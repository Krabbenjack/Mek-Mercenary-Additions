"""
Event Manager - business logic for managing events with persistence.

Handles event storage, retrieval, recurrence calculation, and provides
refresh hooks for UI integration.
"""
from datetime import date
from pathlib import Path
from typing import List, Callable, Optional

from .persistence import Event, EventType, RecurrenceType, load_events, save_events


class EventManager:
    """
    Business logic for managing events with JSON persistence.
    Handles storage, retrieval, recurrence calculation, and refresh hooks.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize EventManager with optional storage path.
        
        Args:
            storage_path: Path to JSON file for persistence. If None, uses default.
        """
        if storage_path is None:
            storage_path = Path.home() / ".mekhq_social_sim" / "events.json"
        
        self.storage_path = Path(storage_path)
        self.events: List[Event] = []
        self.refresh_callbacks: List[Callable[[], None]] = []
        
        # Load events from storage
        self.load()

    def add_refresh_callback(self, callback: Callable[[], None]):
        """
        Register a callback to be called when events are modified.
        
        Args:
            callback: Function to call when events change
        """
        if callback not in self.refresh_callbacks:
            self.refresh_callbacks.append(callback)

    def remove_refresh_callback(self, callback: Callable[[], None]):
        """Remove a previously registered refresh callback."""
        if callback in self.refresh_callbacks:
            self.refresh_callbacks.remove(callback)

    def _trigger_refresh(self):
        """Call all registered refresh callbacks."""
        for callback in self.refresh_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[ERROR] Refresh callback failed: {e}")

    def add_event(self, event_type: EventType, start_date: date, recurrence_type: RecurrenceType) -> Event:
        """
        Add a new event and save to storage.

        Args:
            event_type: EventType enum value
            start_date: datetime.date object
            recurrence_type: RecurrenceType enum value

        Returns:
            The created Event object
        """
        event = Event(event_type, start_date, recurrence_type)
        self.events.append(event)
        self.save()
        self._trigger_refresh()
        return event

    def update_event(self, event_id: int, event_type: EventType, start_date: date, recurrence_type: RecurrenceType) -> bool:
        """
        Update an existing event.
        
        Args:
            event_id: ID of event to update
            event_type: New event type
            start_date: New start date
            recurrence_type: New recurrence type
            
        Returns:
            True if event was found and updated, False otherwise
        """
        for event in self.events:
            if event.id == event_id:
                event.event_type = event_type
                event.start_date = start_date
                event.recurrence_type = recurrence_type
                self.save()
                self._trigger_refresh()
                return True
        return False

    def remove_event(self, event_id: int) -> bool:
        """
        Remove an event by ID and save to storage.
        
        Args:
            event_id: ID of event to remove
            
        Returns:
            True if event was found and removed, False otherwise
        """
        for i, event in enumerate(self.events):
            if event.id == event_id:
                self.events.pop(i)
                self.save()
                self._trigger_refresh()
                return True
        return False

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """
        Get an event by its ID.
        
        Args:
            event_id: ID of event to retrieve
            
        Returns:
            Event object if found, None otherwise
        """
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def get_events_for_date(self, target_date: date) -> List[Event]:
        """
        Get all events active on a specific date (including recurring ones).

        Args:
            target_date: datetime.date object

        Returns:
            List of Event objects that occur on target_date
        """
        active_events = []
        for event in self.events:
            if self._event_occurs_on_date(event, target_date):
                active_events.append(event)
        return active_events

    def _event_occurs_on_date(self, event: Event, target_date: date) -> bool:
        """
        Check if a specific event occurs on the target date based on recurrence rules.

        Recurrence logic:
        - ONCE: only on start_date
        - DAILY: every day on/after start_date
        - MONTHLY: same day-of-month if day exists
        - YEARLY: same month and day every year on/after start_date
        """
        if target_date < event.start_date:
            return False

        r = event.recurrence_type
        if r == RecurrenceType.ONCE:
            return target_date == event.start_date
        if r == RecurrenceType.DAILY:
            return True
        if r == RecurrenceType.MONTHLY:
            # Occurs if day-of-month matches
            return target_date.day == event.start_date.day and target_date >= event.start_date
        if r == RecurrenceType.YEARLY:
            return (target_date.month == event.start_date.month and
                    target_date.day == event.start_date.day and
                    target_date >= event.start_date)
        return False

    def get_all_events(self) -> List[Event]:
        """Return all stored events (shallow copy)."""
        return self.events.copy()

    def save(self) -> bool:
        """
        Save all events to persistent storage.
        
        Returns:
            True if successful, False otherwise
        """
        return save_events(self.events, self.storage_path)

    def load(self) -> bool:
        """
        Load events from persistent storage.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.events = load_events(self.storage_path)
            self._trigger_refresh()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load events: {e}")
            return False
