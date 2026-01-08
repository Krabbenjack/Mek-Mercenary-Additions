"""
Event Participant Selection Engine

Loads and interprets selection rules from JSON configuration files.
Resolves participants for events based on:
- availability (can the event occur?)
- primary_selection (who is the main participant?)
- derived_participants (who else is involved based on relations?)

Supports selection types:
- single_person
- pair
- multiple_persons
- none

Applies basic filters:
- role (profession)
- age_group
- alive
- present
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import re
import random


class SelectionEngine:
    """
    Deterministic participant selection engine for events.
    
    Loads rules from JSON files and resolves participants based on event ID.
    """
    
    def __init__(self, config_dir: Optional[Path] = None, random_seed: Optional[int] = None):
        """
        Initialize the selection engine.
        
        Args:
            config_dir: Path to config/events/injector_rules directory. If None, uses default.
            random_seed: Optional seed for random number generator (for testing/deterministic behavior)
        """
        if config_dir is None:
            # Use resolve() to get absolute path and handle symlinks/nested paths
            module_dir = Path(__file__).resolve().parent
            self.config_dir = module_dir.parent.parent / "config" / "events" / "injector_rules"
        else:
            self.config_dir = Path(config_dir)
        
        # Cache for loaded rules
        self._rules_cache: Dict[str, Dict[str, Any]] = {}
        
        # Random number generator (can be seeded for deterministic behavior)
        self._rng = random.Random(random_seed)
        
        # Load all selection rule files
        self._load_all_rules()
    
    def _strip_json_comments(self, json_str: str) -> str:
        """Remove C-style comments from JSON string."""
        json_str = re.sub(r'//.*', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        return json_str
    
    def _load_all_rules(self) -> None:
        """Load all selection rule JSON files into cache."""
        rule_files = [
            "injector_selection_rules_social.json",
            "injector_selection_rules_children_and_youth.json",
            "injector_selection_rules_training.json",
            "injector_selection_rules_youth_social.json",
            "injector_selection_rules_administration.json",
        ]
        
        for filename in rule_files:
            filepath = self.config_dir / filename
            if not filepath.exists():
                print(f"[WARNING] Selection rules file not found: {filepath}")
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    json_content = f.read()
                
                clean_json = self._strip_json_comments(json_content)
                data = json.loads(clean_json)
                
                # Extract rules (skip meta key)
                for event_id_str, rules in data.items():
                    if event_id_str == "meta":
                        continue
                    
                    # Store rules indexed by event ID
                    self._rules_cache[event_id_str] = rules
                
                print(f"[INFO] Loaded selection rules from {filename}")
            
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}: {e}")
    
    def get_rules(self, event_id: int) -> Optional[Dict[str, Any]]:
        """
        Get selection rules for a specific event ID.
        
        Args:
            event_id: Event ID to look up
            
        Returns:
            Rules dictionary or None if not found
        """
        return self._rules_cache.get(str(event_id))
    
    def resolve(self, event_id: int, characters: Dict[str, Any]) -> Dict[str, List[Any]]:
        """
        Resolve participants for an event.
        
        Args:
            event_id: Event ID from eventlist.json
            characters: Dictionary of Character objects keyed by character ID
            
        Returns:
            Dictionary with:
                "primary": List[Character] - primary participants
                "derived": List[Character] - derived participants
                "all": List[Character] - all participants combined
        """
        rules = self.get_rules(event_id)
        
        if not rules:
            print(f"[WARNING] No selection rules found for event ID {event_id}")
            return {"primary": [], "derived": [], "all": []}
        
        # Check availability
        if not self._check_availability(rules.get("availability", {}), characters):
            print(f"[INFO] Event {event_id} not available (availability check failed)")
            return {"primary": [], "derived": [], "all": []}
        
        # Select primary participants
        primary_selection = rules.get("primary_selection", {})
        primary = self._select_primary(primary_selection, characters)
        
        # Select derived participants
        derived_rules = rules.get("derived_participants", [])
        derived = self._select_derived(derived_rules, primary, characters)
        
        # Combine all participants (ensure no duplicates)
        all_participants = list(primary)
        for char in derived:
            if char not in all_participants:
                all_participants.append(char)
        
        print(f"[INFO] Event {event_id} resolved: {len(primary)} primary, {len(derived)} derived, {len(all_participants)} total")
        
        return {
            "primary": primary,
            "derived": derived,
            "all": all_participants
        }
    
    def _check_availability(self, availability: Dict[str, Any], characters: Dict[str, Any]) -> bool:
        """
        Check if an event is available based on availability requirements.
        
        Args:
            availability: Availability rules from JSON
            characters: Character roster
            
        Returns:
            True if event can occur, False otherwise
        """
        requires = availability.get("requires", {})
        
        # Check for any_person requirement
        if requires.get("any_person"):
            min_count = requires.get("min_count", 1)
            available = self._filter_characters(characters.values(), ["alive", "present"])
            return len(available) >= min_count
        
        # Check for role requirement
        if "role" in requires:
            role = requires["role"]
            min_count = requires.get("min_count", 1)
            available = self._filter_by_role(characters.values(), role)
            available = self._filter_characters(available, ["alive", "present"])
            return len(available) >= min_count
        
        # Check for age_group requirement
        if "age_group" in requires:
            age_group = requires["age_group"]
            min_count = requires.get("min_count", 1)
            available = self._filter_by_age_group(characters.values(), age_group)
            available = self._filter_characters(available, ["alive", "present"])
            return len(available) >= min_count
        
        # Default: available if any characters exist
        return len(characters) > 0
    
    def _select_primary(self, primary_selection: Dict[str, Any], characters: Dict[str, Any]) -> List[Any]:
        """
        Select primary participants based on selection rules.
        
        Args:
            primary_selection: Primary selection rules from JSON
            characters: Character roster
            
        Returns:
            List of Character objects
        """
        selection_type = primary_selection.get("type", "none")
        
        if selection_type == "none":
            return []
        
        # Apply filters
        filters = primary_selection.get("filters", [])
        candidates = self._filter_characters(characters.values(), filters)
        
        # Apply role filter if specified
        if "role" in primary_selection:
            role = primary_selection["role"]
            candidates = self._filter_by_role(candidates, role)
        
        # Apply age_group filter if specified
        if "age_group" in primary_selection:
            age_group = primary_selection["age_group"]
            candidates = self._filter_by_age_group(candidates, age_group)
        
        # Apply exclude_roles if specified
        if "exclude_roles" in primary_selection:
            exclude_roles = primary_selection["exclude_roles"]
            candidates = [c for c in candidates if not self._matches_any_role(c, exclude_roles)]
        
        if not candidates:
            return []
        
        # Select based on type
        if selection_type == "single_person":
            count = primary_selection.get("count", 1)
            return self._rng.sample(candidates, min(count, len(candidates)))
        
        elif selection_type == "pair":
            if len(candidates) < 2:
                return []
            return self._rng.sample(candidates, 2)
        
        elif selection_type == "multiple_persons":
            min_count = primary_selection.get("min", 1)
            max_count = primary_selection.get("max", len(candidates))
            count = primary_selection.get("count")
            
            if count is not None:
                # Fixed count
                actual_count = min(count, len(candidates))
            else:
                # Random count between min and max
                actual_count = self._rng.randint(min_count, min(max_count, len(candidates)))
            
            return self._rng.sample(candidates, actual_count)
        
        return []
    
    def _select_derived(self, derived_rules: List[Dict[str, Any]], primary: List[Any], 
                       characters: Dict[str, Any]) -> List[Any]:
        """
        Select derived participants based on relations to primary participants.
        
        Args:
            derived_rules: List of derived participant rules
            primary: List of primary participants
            characters: Character roster
            
        Returns:
            List of Character objects
        """
        derived = []
        
        for rule in derived_rules:
            relation = rule.get("relation")
            source = rule.get("source", "primary")
            optional = rule.get("optional", False)
            filters = rule.get("filters", [])
            
            # Handle special case: ALL_PRESENT_PERSONS
            if relation == "ALL_PRESENT_PERSONS":
                candidates = self._filter_characters(characters.values(), ["alive", "present"])
                derived.extend(candidates)
                continue
            
            # For now, we don't have relationship data, so we'll just log and skip
            if relation and source == "primary":
                print(f"[INFO] Derived relation '{relation}' from primary - not yet implemented")
                if not optional:
                    print(f"[WARNING] Required derived relation '{relation}' could not be resolved")
        
        return derived
    
    def _filter_characters(self, characters: List[Any], filters: List[str]) -> List[Any]:
        """
        Apply basic filters to character list.
        
        Args:
            characters: List of Character objects
            filters: List of filter names (e.g., "alive", "present")
            
        Returns:
            Filtered list of Character objects
        """
        result = list(characters)
        
        for filter_name in filters:
            if filter_name == "alive":
                # Assume all characters are alive (no death tracking in Phase 2.5)
                pass
            elif filter_name == "present":
                # Assume all characters are present (no deployment tracking in Phase 2.5)
                pass
        
        return result
    
    def _filter_by_role(self, characters: List[Any], role: str) -> List[Any]:
        """
        Filter characters by role/profession.
        
        Args:
            characters: List of Character objects
            role: Role name or special role identifier
            
        Returns:
            Filtered list of Character objects
        """
        # Handle special role identifiers
        if role == "MECHWARRIOR":
            return [c for c in characters if c.profession and "mechwarrior" in c.profession.lower()]
        elif role == "TECHNICIAN":
            return [c for c in characters if c.profession and "tech" in c.profession.lower()]
        elif role == "INFANTRY_SOLDIER":
            return [c for c in characters if c.profession and "infantry" in c.profession.lower()]
        elif role == "COMMAND_OR_SUPERVISOR":
            # Check for command roles in profession or rank
            return [c for c in characters if (
                (c.profession and any(cmd in c.profession.lower() for cmd in ["command", "officer", "captain", "commander", "leader"])) or
                (c.rank_name and any(cmd in c.rank_name.lower() for cmd in ["command", "officer", "captain", "commander", "leader"]))
            )]
        else:
            # Generic role match against profession
            return [c for c in characters if c.profession and role.lower() in c.profession.lower()]
    
    def _filter_by_age_group(self, characters: List[Any], age_group: str) -> List[Any]:
        """
        Filter characters by age group.
        
        Args:
            characters: List of Character objects
            age_group: Age group identifier (e.g., "TODDLER", "CHILD", "TEEN", "ADULT")
            
        Returns:
            Filtered list of Character objects
        """
        age_ranges = {
            "TODDLER": (0, 3),
            "CHILD": (4, 12),
            "TEEN": (13, 19),
            "YOUNG_ADULT": (20, 29),
            "ADULT": (30, 59),
            "SENIOR": (60, 999),
        }
        
        if age_group not in age_ranges:
            print(f"[WARNING] Unknown age group: {age_group}")
            return []
        
        min_age, max_age = age_ranges[age_group]
        return [c for c in characters if min_age <= c.age <= max_age]
    
    def _matches_any_role(self, character: Any, roles: List[str]) -> bool:
        """
        Check if a character matches any of the given roles.
        
        Args:
            character: Character object
            roles: List of role identifiers
            
        Returns:
            True if character matches any role, False otherwise
        """
        for role in roles:
            matches = self._filter_by_role([character], role)
            if matches:
                return True
        return False


# Global singleton instance
_selection_engine_instance: Optional[SelectionEngine] = None


def get_selection_engine() -> SelectionEngine:
    """Get the global SelectionEngine singleton instance."""
    global _selection_engine_instance
    if _selection_engine_instance is None:
        _selection_engine_instance = SelectionEngine()
    return _selection_engine_instance
