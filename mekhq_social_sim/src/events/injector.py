"""
Event Injector - Layer 1

Responsible for:
- Loading event definitions and injector selection rules
- Evaluating availability constraints
- Selecting events based on context
- Selecting primary participants
- Selecting derived participants

Does NOT:
- Perform skill checks
- Apply outcomes
- Change any state

All selection is deterministic and rule-based.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import random


@dataclass
class EventInstance:
    """
    A concrete event instance with selected participants.
    This is the output of the Event Injector.
    """
    event_id: int
    event_category: str
    primary_participants: List[str]  # character IDs
    derived_participants: List[str] = field(default_factory=list)  # character IDs
    context: Dict[str, Any] = field(default_factory=dict)


class EventInjector:
    """
    Event Injector - selects events and participants based on rules.
    
    Loads:
    - eventlist.json (event catalogue)
    - injector_selection_rules_*.json (selection rules)
    - age_groups.json (age filtering)
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the event injector.
        
        Args:
            config_dir: Path to config/events directory. If None, uses default location.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config" / "events"
        
        self.config_dir = config_dir
        self.events: Dict[int, Dict[str, Any]] = {}  # event_id -> event_data
        self.injector_rules: Dict[int, Dict[str, Any]] = {}  # event_id -> selection_rules
        self.age_groups: Dict[str, Dict[str, Any]] = {}
        
        self._load_event_list()
        self._load_injector_rules()
        self._load_age_groups()
    
    def _load_json_with_comments(self, filepath: Path) -> Dict[str, Any]:
        """Load JSON file, stripping C-style comments"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Remove single-line comments
            lines = []
            for line in content.split('\n'):
                comment_pos = line.find('//')
                if comment_pos >= 0:
                    line = line[:comment_pos]
                lines.append(line)
            
            clean_content = '\n'.join(lines)
            
            # Remove C-style comment blocks
            while '/*' in clean_content:
                start = clean_content.find('/*')
                end = clean_content.find('*/', start)
                if end >= 0:
                    clean_content = clean_content[:start] + clean_content[end+2:]
                else:
                    break
            
            return json.loads(clean_content)
    
    def _load_event_list(self):
        """Load event definitions from eventlist.json"""
        filepath = self.config_dir / "eventlist.json"
        if not filepath.exists():
            return
        
        data = self._load_json_with_comments(filepath)
        
        # Parse nested event structure
        text_event_type = data.get('TextEventType', {})
        for category_name, events in text_event_type.items():
            if isinstance(events, dict):
                for event_name, event_id in events.items():
                    if isinstance(event_id, int):
                        self.events[event_id] = {
                            'id': event_id,
                            'name': event_name,
                            'category': category_name
                        }
    
    def _load_injector_rules(self):
        """Load all injector selection rules from injector_rules/*.json"""
        rules_dir = self.config_dir / "injector_rules"
        if not rules_dir.exists():
            return
        
        for rules_file in rules_dir.glob("injector_selection_rules_*.json"):
            data = self._load_json_with_comments(rules_file)
            
            # Extract rules for each event ID
            for event_id_str, rules in data.items():
                if event_id_str.startswith('_') or event_id_str == 'meta':
                    continue  # Skip metadata
                
                try:
                    event_id = int(event_id_str)
                    self.injector_rules[event_id] = rules
                except (ValueError, TypeError):
                    continue
    
    def _load_age_groups(self):
        """Load age group definitions from age_groups.json"""
        filepath = self.config_dir / "meta" / "age_groups.json"
        if not filepath.exists():
            return
        
        data = self._load_json_with_comments(filepath)
        self.age_groups = data.get('age_groups', {})
    
    def get_age_group(self, age: int) -> Optional[str]:
        """Determine the age group for a given age"""
        for group_name, group_data in self.age_groups.items():
            min_age = group_data.get('min_age', 0)
            max_age = group_data.get('max_age')
            
            if max_age is None:
                # Open-ended (e.g., ADULT)
                if age >= min_age:
                    return group_name
            else:
                if min_age <= age <= max_age:
                    return group_name
        
        return None
    
    def check_availability(self, event_id: int, characters: List[Any]) -> bool:
        """
        Check if an event is available given the current character pool.
        
        Args:
            event_id: Event ID to check
            characters: List of Character objects
            
        Returns:
            True if event can be injected, False otherwise
        """
        if event_id not in self.injector_rules:
            return False
        
        rules = self.injector_rules[event_id]
        availability = rules.get('availability', {})
        requires = availability.get('requires', {})
        
        # Check minimum character count
        min_count = requires.get('min_count', 1)
        if len(characters) < min_count:
            return False
        
        # Check if we need any person
        any_person = requires.get('any_person', False)
        if any_person and len(characters) > 0:
            return True
        
        # Add more availability checks here as needed
        # (e.g., specific age groups, professions, etc.)
        
        return True
    
    def select_primary_participants(
        self,
        event_id: int,
        characters: List[Any],
        filters: Optional[List[str]] = None
    ) -> List[str]:
        """
        Select primary participants for an event.
        
        Args:
            event_id: Event ID
            characters: List of Character objects
            filters: Optional list of filter strings (e.g., ["present", "alive"])
            
        Returns:
            List of character IDs
        """
        if event_id not in self.injector_rules:
            return []
        
        rules = self.injector_rules[event_id]
        primary_selection = rules.get('primary_selection', {})
        
        selection_type = primary_selection.get('type', 'single_person')
        min_count = primary_selection.get('min', 1)
        max_count = primary_selection.get('max', 1)
        rule_filters = primary_selection.get('filters', [])
        
        # Combine filters
        all_filters = set(rule_filters)
        if filters:
            all_filters.update(filters)
        
        # Apply filters to character pool
        filtered_chars = self._apply_filters(characters, list(all_filters))
        
        if not filtered_chars:
            return []
        
        # Select based on type
        if selection_type == 'single_person':
            # Select one random character
            selected = random.choice(filtered_chars)
            return [selected.id]
        
        elif selection_type == 'pair':
            # Select two distinct characters
            if len(filtered_chars) < 2:
                return []
            
            pair = random.sample(filtered_chars, 2)
            return [char.id for char in pair]
        
        elif selection_type == 'multiple_persons':
            # Select multiple characters
            count = random.randint(min_count, min(max_count or len(filtered_chars), len(filtered_chars)))
            selected = random.sample(filtered_chars, count)
            return [char.id for char in selected]
        
        return []
    
    def select_derived_participants(
        self,
        event_id: int,
        primary_participant_ids: List[str],
        characters: List[Any]
    ) -> List[str]:
        """
        Select derived participants based on primary participants.
        
        Args:
            event_id: Event ID
            primary_participant_ids: IDs of primary participants
            characters: Full list of Character objects
            
        Returns:
            List of derived participant character IDs
        """
        if event_id not in self.injector_rules:
            return []
        
        rules = self.injector_rules[event_id]
        derived_rules = rules.get('derived_participants', [])
        
        if not derived_rules:
            return []
        
        # For now, return empty list
        # Future implementation can add more sophisticated derived selection logic
        return []
    
    def _apply_filters(self, characters: List[Any], filters: List[str]) -> List[Any]:
        """
        Apply filters to character list.
        
        Supported filters:
        - "present": Character is present (not traveling, etc.)
        - "alive": Character is alive
        - "adult": Character is adult age
        """
        filtered = characters
        
        for filter_name in filters:
            if filter_name == "present":
                # Assume all characters are present for now
                # Future: check character status
                pass
            
            elif filter_name == "alive":
                # Assume all characters are alive for now
                # Future: check character status
                pass
            
            elif filter_name == "adult":
                # Filter by age
                filtered = [c for c in filtered if c.age >= 18]
        
        return filtered
    
    def inject_event(self, event_id: int, characters: List[Any]) -> Optional[EventInstance]:
        """
        Inject an event, selecting participants.
        
        This is the main entry point for the Event Injector.
        
        Args:
            event_id: Event ID to inject
            characters: List of Character objects
            
        Returns:
            EventInstance if successful, None if event cannot be injected
        """
        # Check availability
        if not self.check_availability(event_id, characters):
            return None
        
        # Select primary participants
        primary_ids = self.select_primary_participants(event_id, characters)
        if not primary_ids:
            return None
        
        # Select derived participants
        derived_ids = self.select_derived_participants(event_id, primary_ids, characters)
        
        # Get event data
        event_data = self.events.get(event_id, {})
        
        return EventInstance(
            event_id=event_id,
            event_category=event_data.get('category', 'UNKNOWN'),
            primary_participants=primary_ids,
            derived_participants=derived_ids,
            context={}
        )
    
    def get_available_events(self, characters: List[Any]) -> List[int]:
        """
        Get list of all events that can be injected given the character pool.
        
        Args:
            characters: List of Character objects
            
        Returns:
            List of event IDs that are available
        """
        available = []
        for event_id in self.injector_rules.keys():
            if self.check_availability(event_id, characters):
                available.append(event_id)
        
        return available
