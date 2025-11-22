"""
Event persistence layer - JSON storage for events.

Handles loading and saving events to/from JSON files.
"""
import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any
from enum import Enum


class RecurrenceType(Enum):
    """Enum for event recurrence types (restricted to GUI-supported types)."""
    ONCE = "once"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class EventType(Enum):
    """Enum for predefined event types."""
    FIELD_TRAINING = "Field Training (Infantry)"
    SIMULATOR_TRAINING = "Simulator Training (MekWarrior)"
    EQUIPMENT_MAINTENANCE = "Equipment Maintenance (Tech)"


class Event:
    """
    Represents a single event/appointment with predefined type.

    Attributes:
        id: Unique identifier (incrementing counter)
        event_type: EventType enum value
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
        """Get the display title from the event type."""
        return self.event_type.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "start_date": self.start_date.isoformat(),
            "recurrence_type": self.recurrence_type.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary loaded from JSON."""
        event_type = EventType(data["event_type"])
        start_date = datetime.fromisoformat(data["start_date"]).date()
        recurrence_type = RecurrenceType(data["recurrence_type"])
        event_id = data["id"]
        return cls(event_type, start_date, recurrence_type, event_id)

    def __repr__(self):
        return f"Event(id={self.id}, type='{self.event_type.value}', date={self.start_date}, recurrence={self.recurrence_type.value})"


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
        import sys
        print(f"[ERROR] Invalid JSON in {filepath}: {e}", file=sys.stderr)
        return []
    except (KeyError, ValueError) as e:
        import sys
        print(f"[ERROR] Invalid event data in {filepath}: {e}", file=sys.stderr)
        return []
    except (OSError, IOError) as e:
        import sys
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
        import sys
        print(f"[ERROR] Failed to save events to {filepath}: {e}", file=sys.stderr)
        return False
    except (TypeError, ValueError) as e:
        import sys
        print(f"[ERROR] Failed to serialize event data: {e}", file=sys.stderr)
        return False
