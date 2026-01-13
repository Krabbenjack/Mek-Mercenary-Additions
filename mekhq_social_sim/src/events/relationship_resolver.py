"""
Relationship Resolver - Logic for resolving relationship DSL in event rules.

This module provides resolution for:
- Pair predicates (RELATIONSHIP_ACTIVE_WITH_EACH_OTHER, MARRIED_WITH_EACH_OTHER, etc.)
- Availability requirements (relationship_exists, authority_present)
- Derived participants (HR_REPRESENTATIVE, AUTHORITY_OVER, etc.)
"""

from typing import Dict, List, Optional, Any, Set
import logging

from events.resolver_bundle import get_resolver_bundle
from relationship_state_query import get_state_query

# Configure logging
logger = logging.getLogger(__name__)


class RelationshipResolver:
    """
    Resolves relationship DSL constraints using resolver maps.
    
    This class handles the translation of relationship tokens into concrete
    queries against the relationship system.
    """
    
    def __init__(self):
        """Initialize the relationship resolver."""
        self.bundle = get_resolver_bundle()
        self.state_query = get_state_query()
    
    # -------------------------------------------------------------------------
    # Pair Predicate Resolution
    # -------------------------------------------------------------------------
    
    def evaluate_pair_predicate(
        self, 
        char_a_id: str, 
        char_b_id: str, 
        predicate_name: str,
        event_id: Optional[int] = None
    ) -> bool:
        """
        Evaluate a pair predicate for two characters.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            predicate_name: Predicate name (e.g., "RELATIONSHIP_ACTIVE_WITH_EACH_OTHER")
            event_id: Optional event ID for logging context
            
        Returns:
            True if the predicate is satisfied, False otherwise
        """
        predicate_def = self.bundle.get_pair_predicate(predicate_name)
        
        if predicate_def is None:
            policy = self.bundle.get_unknown_required_relation_policy()
            context = f" for event {event_id}" if event_id else ""
            logger.warning(
                f"[RELATIONSHIP_RESOLVER] Unknown pair predicate '{predicate_name}'{context}. "
                f"Policy: {policy}. No predicate definition found in relationship_resolution_map."
            )
            return False
        
        predicate_type = predicate_def.get("type")
        
        if predicate_type == "has_flag":
            # Check if relationship has a specific flag
            flag = predicate_def.get("flag")
            if not flag:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] Predicate '{predicate_name}' is missing 'flag' field"
                )
                return False
            
            return self.state_query.has_flag(char_a_id, char_b_id, flag)
        
        elif predicate_type == "has_any_flag":
            # Check if relationship has any of the specified flags
            flags = predicate_def.get("flags", [])
            for flag in flags:
                if self.state_query.has_flag(char_a_id, char_b_id, flag):
                    return True
            return False
        
        elif predicate_type == "not":
            # Negate the result of a sub-expression
            expr = predicate_def.get("expr", {})
            sub_result = self._evaluate_expression(char_a_id, char_b_id, expr, event_id)
            return not sub_result
        
        elif predicate_type == "and":
            # All sub-expressions must be true
            all_exprs = predicate_def.get("all", [])
            for expr in all_exprs:
                if not self._evaluate_expression(char_a_id, char_b_id, expr, event_id):
                    return False
            return True
        
        elif predicate_type == "or":
            # At least one sub-expression must be true
            any_exprs = predicate_def.get("any", [])
            for expr in any_exprs:
                if self._evaluate_expression(char_a_id, char_b_id, expr, event_id):
                    return True
            return False
        
        else:
            logger.warning(
                f"[RELATIONSHIP_RESOLVER] Unknown predicate type '{predicate_type}' "
                f"for predicate '{predicate_name}'"
            )
            return False
    
    def _evaluate_expression(
        self, 
        char_a_id: str, 
        char_b_id: str, 
        expr: Dict[str, Any],
        event_id: Optional[int] = None
    ) -> bool:
        """
        Evaluate a relationship expression.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            expr: Expression definition
            event_id: Optional event ID for logging context
            
        Returns:
            True if the expression is satisfied, False otherwise
        """
        expr_type = expr.get("type")
        
        if expr_type == "relationship_exists":
            return self.state_query.relationship_exists(char_a_id, char_b_id)
        
        elif expr_type == "has_flag":
            flag = expr.get("flag")
            if not flag:
                return False
            return self.state_query.has_flag(char_a_id, char_b_id, flag)
        
        elif expr_type == "has_any_flag":
            flags = expr.get("flags", [])
            for flag in flags:
                if self.state_query.has_flag(char_a_id, char_b_id, flag):
                    return True
            return False
        
        elif expr_type == "not":
            sub_expr = expr.get("expr", {})
            return not self._evaluate_expression(char_a_id, char_b_id, sub_expr, event_id)
        
        elif expr_type == "and":
            all_exprs = expr.get("all", [])
            for sub_expr in all_exprs:
                if not self._evaluate_expression(char_a_id, char_b_id, sub_expr, event_id):
                    return False
            return True
        
        elif expr_type == "or":
            any_exprs = expr.get("any", [])
            for sub_expr in any_exprs:
                if self._evaluate_expression(char_a_id, char_b_id, sub_expr, event_id):
                    return True
            return False
        
        else:
            logger.warning(
                f"[RELATIONSHIP_RESOLVER] Unknown expression type '{expr_type}'"
            )
            return False
    
    # -------------------------------------------------------------------------
    # Availability Requirements Resolution
    # -------------------------------------------------------------------------
    
    def check_relationship_exists(
        self, 
        characters: Dict[str, Any],
        event_id: Optional[int] = None
    ) -> bool:
        """
        Check if at least one relationship exists in the roster.
        
        Used for availability.requires.relationship_exists.
        
        Args:
            characters: Dictionary of Character objects keyed by ID
            event_id: Optional event ID for logging context
            
        Returns:
            True if at least one relationship exists, False otherwise
        """
        char_ids = list(characters.keys())
        
        # Check all pairs
        for i, char_a_id in enumerate(char_ids):
            for char_b_id in char_ids[i+1:]:
                if self.state_query.relationship_exists(char_a_id, char_b_id):
                    return True
        
        return False
    
    def check_authority_present(
        self, 
        characters: Dict[str, Any],
        event_id: Optional[int] = None
    ) -> bool:
        """
        Check if any authority relationship exists in the roster.
        
        Used for availability.requires.authority_present.
        Authority is defined as AUTHORITY_OVER derived relation.
        
        Args:
            characters: Dictionary of Character objects keyed by ID
            event_id: Optional event ID for logging context
            
        Returns:
            True if at least one authority relationship exists, False otherwise
        """
        # Get the AUTHORITY_OVER definition
        authority_def = self.bundle.get_derived_relation("AUTHORITY_OVER")
        
        if authority_def is None:
            logger.warning(
                f"[RELATIONSHIP_RESOLVER] No definition for AUTHORITY_OVER derived relation"
            )
            return False
        
        # For Phase 1: Check if any parent/guardian/mentor role exists
        # This is a simplified implementation
        char_ids = list(characters.keys())
        
        for i, char_a_id in enumerate(char_ids):
            for char_b_id in char_ids[i+1:]:
                # Check for family roles (parent/guardian/mentor)
                if self.state_query.has_role(char_a_id, char_b_id, "family"):
                    return True
                if self.state_query.has_role(char_a_id, char_b_id, "guardian"):
                    return True
                if self.state_query.has_role(char_a_id, char_b_id, "mentor"):
                    return True
        
        return False
    
    # -------------------------------------------------------------------------
    # Derived Participants Resolution
    # -------------------------------------------------------------------------
    
    def resolve_derived_participant(
        self,
        derived_def: Dict[str, Any],
        primary_char_id: Optional[str],
        characters: Dict[str, Any],
        event_id: Optional[int] = None
    ) -> List[str]:
        """
        Resolve a derived participant definition to character IDs.
        
        Args:
            derived_def: Derived participant definition from injector rule
            primary_char_id: ID of primary selected character (if applicable)
            characters: Dictionary of all Character objects keyed by ID
            event_id: Optional event ID for logging context
            
        Returns:
            List of character IDs matching the derived relation
        """
        relation_name = derived_def.get("relation")
        if not relation_name:
            logger.warning(
                f"[RELATIONSHIP_RESOLVER] Derived participant missing 'relation' field"
            )
            return []
        
        relation_def = self.bundle.get_derived_relation(relation_name)
        
        if relation_def is None:
            policy = self.bundle.get_unknown_derived_relation_policy()
            context = f" for event {event_id}" if event_id else ""
            logger.warning(
                f"[RELATIONSHIP_RESOLVER] Unknown derived relation '{relation_name}'{context}. "
                f"Policy: {policy}. No relation definition found in relationship_resolution_map."
            )
            return []
        
        relation_type = relation_def.get("type")
        
        if relation_type == "unsupported":
            if self.bundle.should_warn_on_unsupported():
                reason = relation_def.get("reason", "No reason provided")
                context = f" for event {event_id}" if event_id else ""
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] Unsupported derived relation '{relation_name}'{context}. "
                    f"Reason: {reason}"
                )
            return []
        
        elif relation_type == "person_set":
            # Delegate to participant resolver
            person_set_name = relation_def.get("person_set")
            if not person_set_name:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] Derived relation '{relation_name}' "
                    f"is a person_set but missing 'person_set' field"
                )
                return []
            
            # Import here to avoid circular dependency
            from events.participant_resolver import get_participant_resolver
            resolver = get_participant_resolver()
            
            person_set_def = resolver.bundle.get_person_set_definition(person_set_name)
            if person_set_def:
                filters = person_set_def.get("filters", [])
                return resolver.filter_characters_by_filters(characters, filters, event_id)
            else:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] Person set '{person_set_name}' not found"
                )
                return []
        
        elif relation_type == "role_group_pick":
            # Pick one or more characters from a role group
            from events.participant_resolver import get_participant_resolver
            resolver = get_participant_resolver()
            
            role = relation_def.get("role")
            pick = relation_def.get("pick", "one")
            
            if not role:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] Derived relation '{relation_name}' "
                    f"is a role_group_pick but missing 'role' field"
                )
                return []
            
            matching_ids = resolver.filter_characters_by_role(characters, role, event_id)
            
            if pick == "one":
                return matching_ids[:1]
            elif pick == "all":
                return matching_ids
            else:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] Unknown pick value '{pick}' for relation '{relation_name}'"
                )
                return matching_ids[:1]
        
        elif relation_type == "composite_first_supported":
            # Try multiple relation types in order, return first that has results
            order = relation_def.get("order", [])
            
            for sub_def in order:
                sub_type = sub_def.get("type")
                
                # For now, we only support basic family role checks
                if sub_type == "family_parent_of_primary":
                    if primary_char_id:
                        # Find characters with "family" role to primary
                        for char_id in characters.keys():
                            if char_id != primary_char_id:
                                if self.state_query.has_role(char_id, primary_char_id, "family"):
                                    return [char_id]
                
                elif sub_type == "family_guardian_of_primary":
                    if primary_char_id:
                        # Find characters with "guardian" role to primary
                        for char_id in characters.keys():
                            if char_id != primary_char_id:
                                if self.state_query.has_role(char_id, primary_char_id, "guardian"):
                                    return [char_id]
                
                elif sub_type == "mentor_of_primary":
                    if primary_char_id:
                        # Find characters with "mentor" role to primary
                        for char_id in characters.keys():
                            if char_id != primary_char_id:
                                if self.state_query.has_role(char_id, primary_char_id, "mentor"):
                                    return [char_id]
                
                elif sub_type == "org_supervisor_of_primary":
                    # Not supported yet - requires org hierarchy
                    if self.bundle.should_warn_on_unsupported():
                        logger.warning(
                            f"[RELATIONSHIP_RESOLVER] org_supervisor_of_primary not supported yet "
                            f"for relation '{relation_name}'"
                        )
            
            # No supported sub-type found results
            return []
        
        # DIRECT IMPLEMENTATION: Handle UNIT_OF and ALL_PRESENT_PERSONS
        # These are not in resolver maps but implemented directly based on character data
        
        elif relation_name == "UNIT_OF":
            # Get all members of the primary character's unit
            if not primary_char_id:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] UNIT_OF requires primary character but none provided"
                )
                return []
            
            primary_char = characters.get(primary_char_id)
            if not primary_char:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] Primary character {primary_char_id} not found"
                )
                return []
            
            # Check if character has a unit assignment
            if not hasattr(primary_char, 'unit') or primary_char.unit is None:
                logger.info(
                    f"[RELATIONSHIP_RESOLVER] Character {primary_char_id} has no unit assignment"
                )
                return []
            
            # Get the unit name from primary character
            primary_unit_name = primary_char.unit.unit_name
            
            # Check what should be included
            include = derived_def.get("include", "ALL_MEMBERS")
            
            if include == "ALL_MEMBERS":
                # Find all characters in the same unit
                unit_members = []
                for char_id, char in characters.items():
                    if hasattr(char, 'unit') and char.unit is not None:
                        if char.unit.unit_name == primary_unit_name:
                            # Don't include the primary character again
                            if char_id != primary_char_id:
                                unit_members.append(char_id)
                
                logger.info(
                    f"[RELATIONSHIP_RESOLVER] UNIT_OF for {primary_char_id}: "
                    f"found {len(unit_members)} unit members in '{primary_unit_name}'"
                )
                return unit_members
            else:
                logger.warning(
                    f"[RELATIONSHIP_RESOLVER] UNIT_OF include type '{include}' not supported"
                )
                return []
        
        elif relation_name == "ALL_PRESENT_PERSONS":
            # Get all characters with "present" status (ACTIVE)
            from events.participant_resolver import get_participant_resolver
            resolver = get_participant_resolver()
            
            # Use the "present" filter from participant resolver
            present_chars = resolver.filter_characters_by_filters(
                characters, ["present"], event_id
            )
            
            logger.info(
                f"[RELATIONSHIP_RESOLVER] ALL_PRESENT_PERSONS: found {len(present_chars)} present characters"
            )
            return present_chars
        
        else:
            logger.warning(
                f"[RELATIONSHIP_RESOLVER] Unknown relation type '{relation_type}' "
                f"for relation '{relation_name}'"
            )
            return []


# Global singleton instance
_relationship_resolver: Optional[RelationshipResolver] = None


def get_relationship_resolver() -> RelationshipResolver:
    """Get the global RelationshipResolver singleton instance."""
    global _relationship_resolver
    if _relationship_resolver is None:
        _relationship_resolver = RelationshipResolver()
    return _relationship_resolver
