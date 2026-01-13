"""
Participant Selector - Logic for selecting event participants based on injector rules.

This module handles:
1. Loading injector rules for events
2. Checking event availability (required roles/counts)
3. Selecting participants that match the criteria

Integrates with resolver maps for:
- Abstract role resolution (HR -> ADMINISTRATOR_HR)
- Filter resolution (present -> status ACTIVE)
- Age group resolution (EARLY_TEEN -> age 10-13)
- Relationship resolution (relationship_exists, authority_present, derived participants)
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import re
import logging
import random

from events.participant_resolver import get_participant_resolver
from events.relationship_resolver import get_relationship_resolver

# Configure logging
logger = logging.getLogger(__name__)


class ParticipantSelector:
    """Selects event participants based on injector rules and character roster."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the participant selector.
        
        Args:
            config_dir: Path to config/events directory. If None, uses default.
        """
        if config_dir is None:
            module_dir = Path(__file__).resolve().parent
            self.config_dir = module_dir.parent.parent / "config" / "events" / "injector_rules"
        else:
            self.config_dir = Path(config_dir)
        
        self.injector_rules: Dict[int, Dict[str, Any]] = {}
        self._load_injector_rules()
        
        # Get the participant resolver for role/filter/age resolution
        self.resolver = get_participant_resolver()
        
        # Get the relationship resolver for relationship DSL resolution
        self.relationship_resolver = get_relationship_resolver()
    
    def _strip_json_comments(self, json_str: str) -> str:
        """Remove C-style comments from JSON string."""
        json_str = re.sub(r'//.*', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        return json_str
    
    def _load_injector_rules(self) -> None:
        """Load all injector rules from the config directory."""
        if not self.config_dir.exists():
            print(f"[WARNING] Injector rules directory not found: {self.config_dir}")
            return
        
        for rules_file in self.config_dir.glob("*.json"):
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    json_content = f.read()
                
                clean_json = self._strip_json_comments(json_content)
                rules_data = json.loads(clean_json)
                
                # Rules are keyed by event ID (as strings in JSON)
                for event_id_str, rule in rules_data.items():
                    # Skip non-numeric keys (like "meta")
                    try:
                        event_id = int(event_id_str)
                        self.injector_rules[event_id] = rule
                    except ValueError:
                        # Skip metadata or non-event entries
                        continue
            
            except Exception as e:
                print(f"[ERROR] Failed to load {rules_file}: {e}")
    
    def get_injector_rule(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get the injector rule for a specific event ID."""
        return self.injector_rules.get(event_id)
    
    def check_availability(self, event_id: int, characters: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Check if an event can be executed with the current character roster.
        
        Uses resolver maps for role, filter, and age group resolution.
        
        Args:
            event_id: Event ID to check
            characters: Dictionary of Character objects keyed by ID
            
        Returns:
            Tuple of (is_available, error_messages)
        """
        rule = self.get_injector_rule(event_id)
        if not rule:
            return False, [f"No injector rule found for event {event_id}"]
        
        availability = rule.get("availability", {})
        requires = availability.get("requires", {})
        errors = []
        
        # Check role requirements
        required_role = requires.get("role")
        if required_role:
            min_count = requires.get("min_count", 1)
            
            # Use resolver to get matching characters
            matching_char_ids = self.resolver.filter_characters_by_role(
                characters, required_role, event_id
            )
            
            if len(matching_char_ids) < min_count:
                errors.append(
                    f"Requires {min_count} {required_role}(s), found {len(matching_char_ids)}"
                )
        
        # Check any_person requirement
        # any_person uses the "any_person" person_set which requires "present" filter
        if requires.get("any_person"):
            min_count = requires.get("min_count", 1)
            
            # Get person_set definition
            person_set = self.resolver.bundle.get_person_set_definition("any_person")
            if person_set:
                filters = person_set.get("filters", [])
                # Apply filters to get eligible characters
                matching_char_ids = self.resolver.filter_characters_by_filters(
                    characters, filters, event_id
                )
                
                if len(matching_char_ids) < min_count:
                    errors.append(
                        f"Requires {min_count} person(s), found {len(matching_char_ids)} "
                        f"matching filters {filters}"
                    )
            else:
                # Fallback: just check if we have any characters
                if len(characters) < min_count:
                    errors.append(f"Requires {min_count} person(s), found {len(characters)}")
        
        # Check age_group requirements
        age_group = requires.get("age_group")
        if age_group:
            min_count = requires.get("min_count", 1)
            
            # Use resolver to filter by age group
            matching_char_ids = self.resolver.filter_characters_by_age_group(
                characters, age_group, event_id
            )
            
            if len(matching_char_ids) < min_count:
                errors.append(
                    f"Requires {min_count} {age_group}(s), found {len(matching_char_ids)}"
                )
        
        # Check relationship requirements
        if requires.get("relationship_exists"):
            # Check if at least one relationship exists in the roster
            has_rel = self.relationship_resolver.check_relationship_exists(
                characters, event_id
            )
            if not has_rel:
                errors.append("Requires at least one existing relationship")
        
        if requires.get("authority_present"):
            # Check if any authority relationship exists
            has_authority = self.relationship_resolver.check_authority_present(
                characters, event_id
            )
            if not has_authority:
                errors.append("Requires at least one authority relationship (parent/guardian/mentor)")
        
        return len(errors) == 0, errors
    
    def get_eligible_candidates(self, event_id: int, characters: Dict[str, Any],
                                campaign_date: Optional[Any] = None) -> List[str]:
        """
        Get eligible candidates for an event based on injector rules.
        
        This returns the full candidate pool after applying role/filter/age checks,
        but before min/max/count selection.
        
        Args:
            event_id: Event ID to get candidates for
            characters: Dictionary of Character objects keyed by ID
            campaign_date: Optional campaign date for seed (datetime.date or similar)
            
        Returns:
            List of character IDs eligible as candidates
        """
        rule = self.get_injector_rule(event_id)
        if not rule:
            logger.warning(f"[PARTICIPANT_SELECTOR] No injector rule for event {event_id}")
            return []
        
        primary_selection = rule.get("primary_selection", {})
        selection_type = primary_selection.get("type")
        
        if selection_type == "none":
            return []
        
        # Start with all characters as candidates
        candidate_ids = list(characters.keys())
        
        # Apply role filter if specified
        required_role = primary_selection.get("role")
        if required_role:
            candidate_ids = self.resolver.filter_characters_by_role(
                characters, required_role, event_id
            )
        
        # Apply exclude_roles filter if specified
        exclude_roles = primary_selection.get("exclude_roles", [])
        if exclude_roles:
            for exclude_role in exclude_roles:
                excluded_ids = set(self.resolver.filter_characters_by_role(
                    characters, exclude_role, event_id
                ))
                candidate_ids = [cid for cid in candidate_ids if cid not in excluded_ids]
        
        # Apply filters if specified (e.g., ["present", "alive"])
        filters = primary_selection.get("filters", [])
        if filters:
            # Filter candidate_ids by applying all filters
            filtered_candidates = {cid: characters[cid] for cid in candidate_ids}
            candidate_ids = self.resolver.filter_characters_by_filters(
                filtered_candidates, filters, event_id
            )
        
        # Apply age_group filter if specified
        age_group = primary_selection.get("age_group")
        if age_group:
            # Filter candidates by age group
            filtered_candidates = {cid: characters[cid] for cid in candidate_ids}
            candidate_ids = self.resolver.filter_characters_by_age_group(
                filtered_candidates, age_group, event_id
            )
        
        # Apply relationship_context constraints for pair selection
        relationship_context = primary_selection.get("relationship_context", {})
        if relationship_context and selection_type == "pair":
            required_relation = relationship_context.get("required_relation")
            
            if required_relation:
                # Filter pairs by the required relation predicate
                valid_pairs = []
                for i, char_a_id in enumerate(candidate_ids):
                    for char_b_id in candidate_ids[i+1:]:
                        if self.relationship_resolver.evaluate_pair_predicate(
                            char_a_id, char_b_id, required_relation, event_id
                        ):
                            valid_pairs.append((char_a_id, char_b_id))
                
                if valid_pairs:
                    # For get_eligible_candidates, return all characters that can form pairs
                    # (flattened list of all unique characters in valid pairs)
                    all_pair_chars = set()
                    for char_a, char_b in valid_pairs:
                        all_pair_chars.add(char_a)
                        all_pair_chars.add(char_b)
                    candidate_ids = list(all_pair_chars)
                else:
                    logger.info(
                        f"[PARTICIPANT_SELECTOR] Event {event_id} found no pairs "
                        f"matching required_relation '{required_relation}'"
                    )
                    candidate_ids = []
        
        return candidate_ids
    
    def select_participants(self, event_id: int, characters: Dict[str, Any],
                          campaign_date: Optional[Any] = None) -> List[str]:
        """
        Select participants for an event based on injector rules.
        
        Uses deterministic shuffling based on campaign_date and event_id seed.
        Uses resolver maps for role, filter, and age group resolution.
        
        Args:
            event_id: Event ID to select participants for
            characters: Dictionary of Character objects keyed by ID
            campaign_date: Optional campaign date for deterministic seed (datetime.date or similar)
            
        Returns:
            List of character IDs selected as participants
        """
        rule = self.get_injector_rule(event_id)
        if not rule:
            logger.warning(f"[PARTICIPANT_SELECTOR] No injector rule for event {event_id}")
            return []
        
        primary_selection = rule.get("primary_selection", {})
        selection_type = primary_selection.get("type")
        
        if selection_type == "none":
            return []
        
        # Get eligible candidates using the shared logic
        candidate_ids = self.get_eligible_candidates(event_id, characters, campaign_date)
        
        # Log candidate pool size
        logger.info(
            f"[PARTICIPANT_SELECTOR] Event {event_id}: candidate_count={len(candidate_ids)}"
        )
        
        # Apply deterministic shuffling if campaign_date is provided
        if campaign_date and candidate_ids:
            # Create seed from campaign_date and event_id
            if hasattr(campaign_date, 'toordinal'):
                date_value = campaign_date.toordinal()
            else:
                # Fallback: try to convert to string and hash
                date_value = hash(str(campaign_date))
            
            seed = (date_value, event_id)
            
            # Create local RNG instance and shuffle
            rng = random.Random(seed)
            candidate_ids = candidate_ids.copy()  # Don't modify the original list
            rng.shuffle(candidate_ids)
        
        # Select based on type
        selected_ids = []
        
        if selection_type == "single_person":
            selected_ids = candidate_ids[:1] if candidate_ids else []
        
        elif selection_type == "multiple_persons":
            count = primary_selection.get("count", 1)
            min_count = primary_selection.get("min", count)
            max_count = primary_selection.get("max", count)
            
            # Return up to max_count participants
            selected_ids = candidate_ids[:min(len(candidate_ids), max_count)]
        
        elif selection_type == "pair":
            # For pair selection, need at least 2 candidates
            if len(candidate_ids) < 2:
                logger.warning(
                    f"[PARTICIPANT_SELECTOR] Event {event_id} requires pair selection "
                    f"but only {len(candidate_ids)} candidate(s) found"
                )
                selected_ids = []
            else:
                # Check if we need to validate relationship_context
                relationship_context = primary_selection.get("relationship_context", {})
                if relationship_context:
                    required_relation = relationship_context.get("required_relation")
                    if required_relation:
                        # Find first valid pair from shuffled candidates
                        for i, char_a_id in enumerate(candidate_ids):
                            for char_b_id in candidate_ids[i+1:]:
                                if self.relationship_resolver.evaluate_pair_predicate(
                                    char_a_id, char_b_id, required_relation, event_id
                                ):
                                    selected_ids = [char_a_id, char_b_id]
                                    break
                            if selected_ids:
                                break
                    else:
                        # No required relation, just take first 2
                        selected_ids = candidate_ids[:2]
                else:
                    # No relationship context, just take first 2
                    selected_ids = candidate_ids[:2]
        
        # Log selected participants
        logger.info(
            f"[PARTICIPANT_SELECTOR] Event {event_id}: selected_count={len(selected_ids)}, "
            f"selected_ids={selected_ids}"
        )
        
        return selected_ids
    
    def get_derived_participants(
        self, 
        event_id: int, 
        primary_participants: List[str],
        characters: Dict[str, Any]
    ) -> List[str]:
        """
        Get derived participants for an event.
        
        Args:
            event_id: Event ID
            primary_participants: List of primary participant IDs
            characters: Dictionary of Character objects keyed by ID
            
        Returns:
            List of derived participant IDs
        """
        rule = self.get_injector_rule(event_id)
        if not rule:
            return []
        
        derived_defs = rule.get("derived_participants", [])
        if not derived_defs:
            return []
        
        all_derived = []
        
        for derived_def in derived_defs:
            # Determine the primary character for context
            source = derived_def.get("source", "primary")
            primary_char_id = None
            
            if source == "primary" and primary_participants:
                primary_char_id = primary_participants[0]
            
            # Resolve the derived participant
            derived_ids = self.relationship_resolver.resolve_derived_participant(
                derived_def, primary_char_id, characters, event_id
            )
            
            all_derived.extend(derived_ids)
        
        return all_derived


# Global singleton instance
_selector_instance: Optional[ParticipantSelector] = None


def get_participant_selector() -> ParticipantSelector:
    """Get the global ParticipantSelector singleton instance."""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = ParticipantSelector()
    return _selector_instance
