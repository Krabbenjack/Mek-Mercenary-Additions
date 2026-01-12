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
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import re
import logging

from events.participant_resolver import get_participant_resolver

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
        
        # TODO: Check relationship requirements (relationship_exists, authority_present)
        # This will be implemented in Phase 3
        
        return len(errors) == 0, errors
    
    def select_participants(self, event_id: int, characters: Dict[str, Any]) -> List[str]:
        """
        Select participants for an event based on injector rules.
        
        Uses resolver maps for role, filter, and age group resolution.
        
        Args:
            event_id: Event ID to select participants for
            characters: Dictionary of Character objects keyed by ID
            
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
        
        # TODO: Apply relationship_context constraints (required_relation, etc.)
        # This will be implemented in Phase 3
        
        # Select based on type
        if selection_type == "single_person":
            return candidate_ids[:1] if candidate_ids else []
        
        elif selection_type == "multiple_persons":
            count = primary_selection.get("count", 1)
            min_count = primary_selection.get("min", count)
            max_count = primary_selection.get("max", count)
            
            # Return up to max_count participants
            return candidate_ids[:min(len(candidate_ids), max_count)]
        
        elif selection_type == "pair":
            # For pair selection, need at least 2 candidates
            if len(candidate_ids) < 2:
                logger.warning(
                    f"[PARTICIPANT_SELECTOR] Event {event_id} requires pair selection "
                    f"but only {len(candidate_ids)} candidate(s) found"
                )
                return []
            
            # Return first 2 candidates (can be enhanced later for pair_constraints)
            return candidate_ids[:2]
        
        return []


# Global singleton instance
_selector_instance: Optional[ParticipantSelector] = None


def get_participant_selector() -> ParticipantSelector:
    """Get the global ParticipantSelector singleton instance."""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = ParticipantSelector()
    return _selector_instance
