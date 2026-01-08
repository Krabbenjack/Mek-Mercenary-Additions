"""
Participant Selector - Logic for selecting event participants based on injector rules.

This module handles:
1. Loading injector rules for events
2. Checking event availability (required roles/counts)
3. Selecting participants that match the criteria
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import re


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
                    event_id = int(event_id_str)
                    self.injector_rules[event_id] = rule
            
            except Exception as e:
                print(f"[ERROR] Failed to load {rules_file}: {e}")
    
    def get_injector_rule(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get the injector rule for a specific event ID."""
        return self.injector_rules.get(event_id)
    
    def check_availability(self, event_id: int, characters: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Check if an event can be executed with the current character roster.
        
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
            # Normalize role name for comparison (handle MECHWARRIOR/MEKWARRIOR)
            matching_chars = [
                char for char in characters.values()
                if char.profession and self._normalize_role(char.profession) == self._normalize_role(required_role)
            ]
            
            if len(matching_chars) < min_count:
                errors.append(f"Requires {min_count} {required_role}(s), found {len(matching_chars)}")
        
        # Check any_person requirement
        if requires.get("any_person") and not characters:
            errors.append("Requires at least one person")
        
        return len(errors) == 0, errors
    
    def _normalize_role(self, role: str) -> str:
        """
        Normalize role names for comparison.
        
        Handles variations like MECHWARRIOR vs MEKWARRIOR.
        MekHQ uses MEKWARRIOR as the canonical form.
        """
        # Convert to uppercase and handle common variations
        role = role.upper().strip()
        
        # MECHWARRIOR and MEKWARRIOR are the same, normalize to MEKWARRIOR (MekHQ standard)
        if role in ("MECHWARRIOR", "MEKWARRIOR", "MW"):
            return "MEKWARRIOR"
        
        return role
    
    def select_participants(self, event_id: int, characters: Dict[str, Any]) -> List[str]:
        """
        Select participants for an event based on injector rules.
        
        Args:
            event_id: Event ID to select participants for
            characters: Dictionary of Character objects keyed by ID
            
        Returns:
            List of character IDs selected as participants
        """
        rule = self.get_injector_rule(event_id)
        if not rule:
            return []
        
        primary_selection = rule.get("primary_selection", {})
        selection_type = primary_selection.get("type")
        
        if selection_type == "none":
            return []
        
        required_role = primary_selection.get("role")
        if not required_role:
            return []
        
        # Get all characters matching the required role
        matching_chars = [
            char_id for char_id, char in characters.items()
            if char.profession and self._normalize_role(char.profession) == self._normalize_role(required_role)
        ]
        
        # Select based on type
        if selection_type == "single_person":
            return matching_chars[:1] if matching_chars else []
        
        elif selection_type == "multiple_persons":
            count = primary_selection.get("count", 1)
            min_count = primary_selection.get("min", count)
            max_count = primary_selection.get("max", count)
            
            # Return up to count participants
            return matching_chars[:min(len(matching_chars), max_count)]
        
        return []


# Global singleton instance
_selector_instance: Optional[ParticipantSelector] = None


def get_participant_selector() -> ParticipantSelector:
    """Get the global ParticipantSelector singleton instance."""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = ParticipantSelector()
    return _selector_instance
