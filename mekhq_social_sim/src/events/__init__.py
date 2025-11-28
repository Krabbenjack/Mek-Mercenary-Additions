"""
Event management system with persistence.

This package provides:
- EventManager: Manages events with JSON persistence
- EventType: Enum for predefined event types
- RecurrenceType: Enum for event recurrence patterns
- Event dialogs: GUI components for creating/editing/managing events
"""

from .manager import EventManager, Event, EventType, RecurrenceType

__all__ = [
    "EventManager",
    "Event",
    "EventType",
    "RecurrenceType",
]
