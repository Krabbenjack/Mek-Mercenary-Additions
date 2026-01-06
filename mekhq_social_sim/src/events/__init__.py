"""
Event management system with persistence.

This package provides:
- EventManager: Manages events with JSON persistence
- EventType: Enum for predefined event types
- RecurrenceType: Enum for event recurrence patterns
- Event dialogs: GUI components for creating/editing/managing events
- EventInjector: Executes event mechanics when calendar events trigger
"""

from .manager import EventManager, Event, EventType, RecurrenceType
from .injector import EventInjector, EventExecutionLog, get_event_injector

__all__ = [
    "EventManager",
    "Event",
    "EventType",
    "RecurrenceType",
    "EventInjector",
    "EventExecutionLog",
    "get_event_injector",
]
