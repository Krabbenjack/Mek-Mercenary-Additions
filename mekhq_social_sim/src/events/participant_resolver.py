"""
Participant Resolver - Logic for resolving participant selection rules.

This module provides resolution for:
- Abstract roles to concrete profession values
- Filters (present, alive) to character field checks
- Age groups to character age ranges
"""

from typing import Dict, List, Optional, Any
import logging

from events.resolver_bundle import get_resolver_bundle


# Configure logging
logger = logging.getLogger(__name__)


class ParticipantResolver:
    """
    Resolves participant selection constraints using resolver maps.
    
    This class handles the translation of abstract DSL tokens (roles, filters, age groups)
    into concrete checks against Character objects.
    """
    
    def __init__(self):
        """Initialize the participant resolver."""
        self.bundle = get_resolver_bundle()
    
    # -------------------------------------------------------------------------
    # Role Resolution
    # -------------------------------------------------------------------------
    
    def resolve_role(self, abstract_role: str, event_id: Optional[int] = None) -> List[str]:
        """
        Resolve an abstract role to concrete profession values.
        
        Args:
            abstract_role: Abstract role name (e.g., "HR", "TECHNICIAN")
            event_id: Optional event ID for logging context
            
        Returns:
            List of concrete profession values (e.g., ["ADMINISTRATOR_HR"])
            Empty list if role is unknown (with logging)
        """
        concrete_roles = self.bundle.get_role_mapping(abstract_role)
        
        if not concrete_roles:
            policy = self.bundle.get_unknown_role_policy()
            context = f" for event {event_id}" if event_id else ""
            logger.warning(
                f"[PARTICIPANT_RESOLVER] Unknown role '{abstract_role}'{context}. "
                f"Policy: {policy}. No role mapping found in participant_resolution_map."
            )
        
        return concrete_roles
    
    def character_matches_role(
        self, 
        character: Any, 
        abstract_role: str, 
        event_id: Optional[int] = None
    ) -> bool:
        """
        Check if a character matches an abstract role.
        
        Args:
            character: Character object to check
            abstract_role: Abstract role name
            event_id: Optional event ID for logging context
            
        Returns:
            True if character's profession matches any of the resolved concrete roles
        """
        if not character.profession:
            return False
        
        concrete_roles = self.resolve_role(abstract_role, event_id)
        if not concrete_roles:
            return False
        
        # Normalize both character profession and concrete roles for comparison
        char_profession = character.profession.upper().strip()
        normalized_concrete = [r.upper().strip() for r in concrete_roles]
        
        return char_profession in normalized_concrete
    
    def filter_characters_by_role(
        self, 
        characters: Dict[str, Any], 
        abstract_role: str, 
        event_id: Optional[int] = None
    ) -> List[str]:
        """
        Filter characters by abstract role.
        
        Args:
            characters: Dictionary of Character objects keyed by ID
            abstract_role: Abstract role name
            event_id: Optional event ID for logging context
            
        Returns:
            List of character IDs matching the role
        """
        return [
            char_id for char_id, char in characters.items()
            if self.character_matches_role(char, abstract_role, event_id)
        ]
    
    # -------------------------------------------------------------------------
    # Filter Resolution
    # -------------------------------------------------------------------------
    
    def resolve_filter(self, filter_name: str, event_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Resolve a filter name to its definition.
        
        Args:
            filter_name: Filter name (e.g., "present", "alive")
            event_id: Optional event ID for logging context
            
        Returns:
            Filter definition dict, or None if unknown (with logging)
        """
        filter_def = self.bundle.get_filter_definition(filter_name)
        
        if filter_def is None:
            policy = self.bundle.get_unknown_filter_policy()
            context = f" for event {event_id}" if event_id else ""
            logger.warning(
                f"[PARTICIPANT_RESOLVER] Unknown filter '{filter_name}'{context}. "
                f"Policy: {policy}. No filter mapping found in participant_resolution_map."
            )
        
        return filter_def
    
    def apply_filter(
        self, 
        character: Any, 
        filter_name: str, 
        event_id: Optional[int] = None
    ) -> bool:
        """
        Apply a filter to a character.
        
        Args:
            character: Character object to check
            filter_name: Filter name to apply
            event_id: Optional event ID for logging context
            
        Returns:
            True if character passes the filter, False otherwise
        """
        filter_def = self.resolve_filter(filter_name, event_id)
        
        if filter_def is None:
            # Unknown filter - fail per policy
            return False
        
        filter_type = filter_def.get("type")
        
        if filter_type == "status_in":
            # Check if character's status is in the allowed values
            field = filter_def.get("field", "status")
            allowed_values = filter_def.get("values", [])
            
            # Get the field value from character
            char_value = getattr(character, field, None)
            if char_value is None:
                return False
            
            return char_value.upper() in [v.upper() for v in allowed_values]
        
        elif filter_type == "alias_of":
            # Resolve the alias and apply recursively
            alias = filter_def.get("alias")
            if not alias:
                logger.warning(
                    f"[PARTICIPANT_RESOLVER] Filter '{filter_name}' is an alias but has no target. "
                    f"Treating as failed filter."
                )
                return False
            
            return self.apply_filter(character, alias, event_id)
        
        else:
            logger.warning(
                f"[PARTICIPANT_RESOLVER] Unknown filter type '{filter_type}' for filter '{filter_name}'. "
                f"Treating as failed filter."
            )
            return False
    
    def filter_characters_by_filters(
        self, 
        characters: Dict[str, Any], 
        filters: List[str], 
        event_id: Optional[int] = None
    ) -> List[str]:
        """
        Filter characters by a list of filter names.
        
        All filters must pass (AND logic).
        
        Args:
            characters: Dictionary of Character objects keyed by ID
            filters: List of filter names to apply
            event_id: Optional event ID for logging context
            
        Returns:
            List of character IDs passing all filters
        """
        result = []
        for char_id, char in characters.items():
            passes_all = all(
                self.apply_filter(char, filter_name, event_id)
                for filter_name in filters
            )
            if passes_all:
                result.append(char_id)
        
        return result
    
    # -------------------------------------------------------------------------
    # Age Group Resolution
    # -------------------------------------------------------------------------
    
    def get_character_age_group(self, character: Any) -> Optional[str]:
        """
        Determine which age group a character belongs to.
        
        Returns the first matching age group based on the character's age.
        Age groups are checked in order as defined in age_groups.json.
        
        Args:
            character: Character object with age field
            
        Returns:
            Age group name (e.g., "EARLY_TEEN"), or None if no match
        """
        age = character.age
        
        # Check all age groups
        for group_name, group_def in self.bundle.get_all_age_groups().items():
            min_age = group_def.get("min_age")
            max_age = group_def.get("max_age")
            
            # Check if age falls within range
            if min_age is not None:
                if age < min_age:
                    continue
            
            if max_age is not None:
                if age > max_age:
                    continue
            
            # Age is within range (or max_age is None, meaning no upper limit)
            return group_name
        
        return None
    
    def character_in_age_group(
        self, 
        character: Any, 
        group_name: str, 
        event_id: Optional[int] = None
    ) -> bool:
        """
        Check if a character belongs to a specific age group.
        
        Args:
            character: Character object to check
            group_name: Age group name (e.g., "EARLY_TEEN")
            event_id: Optional event ID for logging context
            
        Returns:
            True if character is in the age group, False otherwise
        """
        group_def = self.bundle.get_age_group_definition(group_name)
        
        if group_def is None:
            logger.warning(
                f"[PARTICIPANT_RESOLVER] Unknown age group '{group_name}' "
                f"{'for event ' + str(event_id) if event_id else ''}. "
                f"No age group definition found in age_groups.json."
            )
            return False
        
        age = character.age
        min_age = group_def.get("min_age")
        max_age = group_def.get("max_age")
        
        # Check age bounds
        if min_age is not None and age < min_age:
            return False
        
        if max_age is not None and age > max_age:
            return False
        
        return True
    
    def filter_characters_by_age_group(
        self, 
        characters: Dict[str, Any], 
        group_name: str, 
        event_id: Optional[int] = None
    ) -> List[str]:
        """
        Filter characters by age group.
        
        Args:
            characters: Dictionary of Character objects keyed by ID
            group_name: Age group name
            event_id: Optional event ID for logging context
            
        Returns:
            List of character IDs in the age group
        """
        return [
            char_id for char_id, char in characters.items()
            if self.character_in_age_group(char, group_name, event_id)
        ]


# Global singleton instance
_participant_resolver: Optional[ParticipantResolver] = None


def get_participant_resolver() -> ParticipantResolver:
    """Get the global ParticipantResolver singleton instance."""
    global _participant_resolver
    if _participant_resolver is None:
        _participant_resolver = ParticipantResolver()
    return _participant_resolver
