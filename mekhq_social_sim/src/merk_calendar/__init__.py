"""
mek_calendar package initializer.

Exports the main public classes from calendar_system so you can import the calendar
functionality as a package:

    from mek_calendar import MainCalendarWindow, EventManager

If you place calendar_system.py in this package (src/mek_calendar/calendar_system.py),
this __init__ makes importing cleaner and encapsulates the package surface.

To install/use in your project layout (recommended):
- Move src/calendar_system.py -> src/mek_calendar/calendar_system.py
- Add this file at src/mek_calendar/__init__.py
- Then you can import with:
    from mek_calendar import MainCalendarWindow, EventManager
"""
from .calendar_system import (
    MainCalendarWindow,
    DetailedCalendarWindow,
    EventManager,
    Event,
    RecurrenceType,
)

__all__ = [
    "MainCalendarWindow",
    "DetailedCalendarWindow",
    "EventManager",
    "Event",
    "RecurrenceType",
]
