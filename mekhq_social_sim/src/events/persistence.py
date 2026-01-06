"""
Event persistence layer - JSON storage for events.

Handles loading and saving events to/from JSON files.
Event types are loaded from eventlist.json as the single source of truth.
"""
import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
import sys
import re


class RecurrenceType(Enum):
    """Enum for event recurrence types (restricted to GUI-supported types)."""
    ONCE = "once"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


def _strip_json_comments(json_str: str) -> str:
    """Remove C-style comments from JSON string."""
    # Remove single-line comments (// ...)
    json_str = re.sub(r'//.*', '', json_str)
    # Remove multi-line comments (/* ... */)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    return json_str


def _load_eventlist() -> Dict[int, str]:
    """
    Load event definitions from eventlist.json.
    
    Returns:
        Dict mapping event IDs (int) to event names (str)
    """
    # Find eventlist.json relative to this file
    module_dir = Path(__file__).parent
    config_dir = module_dir.parent.parent / "config" / "events"
    eventlist_path = config_dir / "eventlist.json"
    
    if not eventlist_path.exists():
        print(f"[ERROR] eventlist.json not found at {eventlist_path}", file=sys.stderr)
        return {}
    
    try:
        with open(eventlist_path, 'r', encoding='utf-8') as f:
            json_content = f.read()
        
        # Strip comments before parsing
        clean_json = _strip_json_comments(json_content)
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
        print(f"[ERROR] Failed to load eventlist.json: {e}", file=sys.stderr)
        return {}


def _create_event_type_enum() -> type:
    """
    Dynamically create EventType enum from eventlist.json.
    
    Returns:
        Enum class with all events from eventlist.json
    """
    event_map = _load_eventlist()
    
    if not event_map:
        # Fallback to minimal set if eventlist.json can't be loaded
        print("[WARNING] Using fallback event types", file=sys.stderr)
        return Enum('EventType', {
            'SIMULATOR_TRAINING_MECHWARRIOR': 1001,
            'INFANTRY_FIELD_EXERCISE': 1002,
            'TECHNICAL_MAINTENANCE': 1003,
        })
    
    # Create enum with event_name: event_id pairs
    # event_map is {event_id: event_name}, we need {event_name: event_id}
    enum_dict = {name: event_id for event_id, name in event_map.items()}
    return Enum('EventType', enum_dict)


# Create the EventType enum from eventlist.json
EventType = _create_event_type_enum()


class Event:
    """
    Represents a single event/appointment with predefined type from eventlist.json.

    Attributes:
        id: Unique identifier (incrementing counter)
        event_type: EventType enum value (contains event ID from eventlist.json)
        start_date: datetime.date object
        recurrence_type: RecurrenceType enum
    """

    _counter = 0

    def __init__(self, event_type: EventType, start_date: date, recurrence_type: RecurrenceType, event_id: int = None):
        if event_id is None:
            Event._counter += 1
            self.id = Event._counter
        else:
            self.id = event_id
            Event._counter = max(Event._counter, event_id)
        
        self.event_type = event_type
        self.start_date = start_date
        self.recurrence_type = recurrence_type

    @property
    def title(self) -> str:
        """Get the display title from the event type name."""
        return self.event_type.name

    @property
    def event_id(self) -> int:
        """Get the event ID from eventlist.json."""
        return self.event_type.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_type_id": self.event_type.value,  # Store numeric event ID
            "event_type_name": self.event_type.name,  # Store name for readability
            "start_date": self.start_date.isoformat(),
            "recurrence_type": self.recurrence_type.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary loaded from JSON."""
        # Try new format first (event_type_id), fall back to old format (event_type)
        if "event_type_id" in data:
            event_type_id = data["event_type_id"]
            # Find enum member by value (event ID)
            event_type = EventType(event_type_id)
        else:
            # Old format compatibility - try to parse as string value
            old_event_type = data.get("event_type", "")
            # Try to find by name
            event_type = getattr(EventType, old_event_type.replace(" ", "_").upper(), None)
            if event_type is None:
                # Fall back to first available event type
                event_type = list(EventType)[0]
        
        start_date = datetime.fromisoformat(data["start_date"]).date()
        recurrence_type = RecurrenceType(data["recurrence_type"])
        event_id = data["id"]
        return cls(event_type, start_date, recurrence_type, event_id)

    def __repr__(self):
        return f"Event(id={self.id}, type='{self.event_type.name}' (ID:{self.event_type.value}), date={self.start_date}, recurrence={self.recurrence_type.value})"


def load_events(filepath: Path) -> List[Event]:
    """
    Load events from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of Event objects
    """
    if not filepath.exists():
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        events = [Event.from_dict(event_data) for event_data in data.get("events", [])]
        return events
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {filepath}: {e}", file=sys.stderr)
        return []
    except (KeyError, ValueError) as e:
        print(f"[ERROR] Invalid event data in {filepath}: {e}", file=sys.stderr)
        return []
    except (OSError, IOError) as e:
        print(f"[ERROR] Failed to read {filepath}: {e}", file=sys.stderr)
        return []


def save_events(events: List[Event], filepath: Path) -> bool:
    """
    Save events to JSON file.
    
    Args:
        events: List of Event objects to save
        filepath: Path to JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "events": [event.to_dict() for event in events]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except (OSError, IOError) as e:
        print(f"[ERROR] Failed to save events to {filepath}: {e}", file=sys.stderr)
        return False
    except (TypeError, ValueError) as e:
        print(f"[ERROR] Failed to serialize event data: {e}", file=sys.stderr)
        return False
