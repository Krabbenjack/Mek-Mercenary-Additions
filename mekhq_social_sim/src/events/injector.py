"""
Event Injector - Executes event mechanics when calendar events trigger.

This module is the bridge between the calendar system and the event mechanics system.
When a scheduled event occurs, the injector:
1. Validates the event ID against eventlist.json
2. Selects participants based on injector rules
3. Executes interactions and resolution
4. Applies outcomes
5. Emits triggers to the relationship system
6. Logs execution for debugging (Social Director)
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import date
import json
import re
from pathlib import Path


class EventExecutionLog:
    """Records details of an event execution for debugging/observation."""
    
    def __init__(self, event_id: int, event_name: str, execution_date: date):
        self.event_id = event_id
        self.event_name = event_name
        self.execution_date = execution_date
        self.participants: List[str] = []
        self.interactions: List[Dict[str, Any]] = []
        self.resolution_results: List[Dict[str, Any]] = []
        self.outcomes: List[Dict[str, Any]] = []
        self.triggers_emitted: List[Dict[str, Any]] = []
        self.errors: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "execution_date": self.execution_date.isoformat(),
            "participants": self.participants,
            "interactions": self.interactions,
            "resolution_results": self.resolution_results,
            "outcomes": self.outcomes,
            "triggers_emitted": self.triggers_emitted,
            "errors": self.errors,
        }


class EventInjector:
    """
    Executes event mechanics and manages event execution lifecycle.
    
    This is the main entry point for event execution from the calendar system.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the event injector.
        
        Args:
            config_dir: Path to config/events directory. If None, uses default.
        """
        if config_dir is None:
            # Use resolve() to get absolute path and handle symlinks/nested paths
            module_dir = Path(__file__).resolve().parent
            self.config_dir = module_dir.parent.parent / "config" / "events"
        else:
            self.config_dir = Path(config_dir)
        
        self.event_definitions = self._load_eventlist()
        self.execution_history: List[EventExecutionLog] = []
        
        # Observer callbacks for Social Director
        self._observers: List[callable] = []
    
    def add_observer(self, callback: callable) -> None:
        """
        Add an observer callback for event executions.
        
        Args:
            callback: Function to call with EventExecutionLog after each execution
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: callable) -> None:
        """Remove an observer callback."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, log: EventExecutionLog) -> None:
        """Notify all observers of an event execution."""
        for callback in self._observers:
            try:
                callback(log)
            except Exception as e:
                print(f"[WARNING] Observer callback failed: {e}")
    
    def _strip_json_comments(self, json_str: str) -> str:
        """Remove C-style comments from JSON string."""
        json_str = re.sub(r'//.*', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        return json_str
    
    def _load_eventlist(self) -> Dict[int, str]:
        """Load event definitions from eventlist.json."""
        eventlist_path = self.config_dir / "eventlist.json"
        
        if not eventlist_path.exists():
            print(f"[ERROR] eventlist.json not found at {eventlist_path}")
            return {}
        
        try:
            with open(eventlist_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
            
            clean_json = self._strip_json_comments(json_content)
            data = json.loads(clean_json)
            
            # Extract all event IDs and names
            event_map = {}
            text_event_type = data.get("TextEventType", {})
            
            for category, events in text_event_type.items():
                if isinstance(events, dict):
                    for event_name, event_id in events.items():
                        if isinstance(event_id, int):
                            event_map[event_id] = event_name
            
            return event_map
        
        except Exception as e:
            print(f"[ERROR] Failed to load eventlist.json: {e}")
            return {}
    
    def validate_event_id(self, event_id: int) -> Tuple[bool, Optional[str]]:
        """
        Validate that an event ID exists in eventlist.json.
        
        Args:
            event_id: Event ID to validate
            
        Returns:
            Tuple of (is_valid, event_name)
        """
        event_name = self.event_definitions.get(event_id)
        return (event_name is not None, event_name)
    
    def execute_event(self, event_id: int, execution_date: date, 
                     characters: Optional[Dict[str, Any]] = None,
                     override_participants: Optional[List[Any]] = None) -> EventExecutionLog:
        """
        Execute an event with the given ID.
        
        Args:
            event_id: Event ID from eventlist.json
            execution_date: Date of execution
            characters: Optional character roster for participant selection
            override_participants: Optional list of pre-selected participants (from UI)
            
        Returns:
            EventExecutionLog with execution details
        """
        # Validate event ID
        is_valid, event_name = self.validate_event_id(event_id)
        
        log = EventExecutionLog(event_id, event_name or "UNKNOWN", execution_date)
        
        if not is_valid:
            log.errors.append(f"Invalid event ID: {event_id} not found in eventlist.json")
            self.execution_history.append(log)
            self._notify_observers(log)
            return log
        
        # Select participants
        if override_participants is not None:
            # Use provided participants from execution window
            participants = override_participants
            log.participants = [c.id for c in participants]
            print(f"[INFO] Using {len(participants)} override participants for event {event_id}")
        elif characters:
            # Use selection engine to resolve participants
            from .injector_selection_engine import get_selection_engine
            selection_engine = get_selection_engine()
            result = selection_engine.resolve(event_id, characters)
            participants = result["all"]
            log.participants = [c.id for c in participants]
            print(f"[INFO] Selection engine resolved {len(participants)} participants for event {event_id}")
        else:
            participants = []
            log.participants = []
        
        # Phase 2.5: Minimal execution for observability
        # Full implementation will follow in later phases
        
        # TODO: Select interactions
        # TODO: Resolve interactions (skill checks)
        # TODO: Apply outcomes
        # TODO: Emit triggers
        
        # For now, just log that the event was executed
        log.interactions.append({
            "type": "placeholder",
            "description": f"Event {event_name} (ID:{event_id}) was triggered with {len(participants)} participant(s)"
        })
        
        # Store in history
        self.execution_history.append(log)
        
        # Notify observers (Social Director)
        self._notify_observers(log)
        
        return log
    
    def get_execution_history(self, limit: int = 50) -> List[EventExecutionLog]:
        """
        Get recent execution history.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of EventExecutionLog objects (most recent first)
        """
        return list(reversed(self.execution_history[-limit:]))
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()


# Global singleton instance
_injector_instance: Optional[EventInjector] = None


def get_event_injector() -> EventInjector:
    """Get the global EventInjector singleton instance."""
    global _injector_instance
    if _injector_instance is None:
        _injector_instance = EventInjector()
    return _injector_instance
