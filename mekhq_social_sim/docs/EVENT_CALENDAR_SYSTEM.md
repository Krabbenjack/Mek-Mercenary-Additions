# Event System Documentation

## Overview

The Event System provides a comprehensive way to schedule and track unit activities with recurring patterns. Events are persistently stored in JSON format and integrate seamlessly with the calendar GUI.

## Architecture

### Components

1. **`src/events/persistence.py`**: Handles JSON serialization and deserialization
   - `Event`: Data class representing an event
   - `EventType`: Enum defining predefined event types
   - `RecurrenceType`: Enum defining recurrence patterns
   - `save_events()`: Save events to JSON file
   - `load_events()`: Load events from JSON file

2. **`src/events/manager.py`**: Business logic for event management
   - `EventManager`: Main class for managing events
   - Provides CRUD operations (Create, Read, Update, Delete)
   - Implements recurrence calculation logic
   - Supports refresh callbacks for UI integration

3. **`src/events/dialogs.py`**: GUI components
   - `EventCreationDialog`: Create new events
   - `EventEditDialog`: Edit existing events
   - `ManageEventsDialog`: List, edit, and delete events for a specific day

## Event Types

The system supports three predefined event types:

1. **Field Training (Infantry)**: Ground troop training exercises
2. **Simulator Training (MekWarrior)**: BattleMech simulation sessions
3. **Equipment Maintenance (Tech)**: Regular maintenance schedules

These types are enforced through the `EventType` enum and presented as dropdown selections in the GUI.

## Recurrence Patterns

Events can recur according to the following patterns:

- **Once**: Event occurs only on the selected date
- **Daily**: Event repeats every day from the start date
- **Monthly**: Event repeats on the same day of each month (e.g., 15th of every month)
- **Yearly**: Event repeats on the same date each year (e.g., January 15th every year)

**Note**: The WEEKLY recurrence pattern from the legacy system has been removed to simplify the interface as per requirements.

## Usage

### From Code

```python
from events import EventManager, EventType, RecurrenceType
from datetime import date

# Create an event manager (uses default storage path)
manager = EventManager()

# Or specify a custom path
manager = EventManager(storage_path="/path/to/events.json")

# Add an event
event = manager.add_event(
    event_type=EventType.FIELD_TRAINING,
    start_date=date(2025, 1, 15),
    recurrence_type=RecurrenceType.MONTHLY
)

# Query events for a specific date
events = manager.get_events_for_date(date(2025, 2, 15))

# Update an event
manager.update_event(
    event_id=event.id,
    event_type=EventType.SIMULATOR_TRAINING,
    start_date=date(2025, 1, 15),
    recurrence_type=RecurrenceType.YEARLY
)

# Delete an event
manager.remove_event(event.id)

# Register a refresh callback (called when events change)
def on_events_changed():
    print("Events have been updated!")

manager.add_refresh_callback(on_events_changed)
```

### From GUI

1. **Open Calendar**: 
   - Left-click on the date display in the main GUI to open the date picker
   - Right-click on the date display to open the detailed calendar view

2. **Add Event**:
   - In the detailed calendar view, right-click on any day button
   - Select "Add Event" from the context menu
   - Choose the event type from the dropdown
   - Select the recurrence pattern
   - Click "Create"

3. **Manage Events**:
   - Right-click on a day button
   - Select "Manage Events" from the context menu
   - See all events for that day
   - Click "Edit" to modify an event
   - Click "Delete" to remove an event (with confirmation)

4. **View Events**:
   - Days with events show a count in parentheses (e.g., "15\n(2 events)")
   - Days with events are highlighted in light blue
   - Events for the selected day appear in the bottom panel

## Persistence

Events are automatically saved to `~/.mekhq_social_sim/events.json` whenever changes are made. The JSON format is:

```json
{
  "events": [
    {
      "id": 1,
      "event_type": "Field Training (Infantry)",
      "start_date": "2025-01-15",
      "recurrence_type": "monthly"
    }
  ]
}
```

## Integration with Main GUI

The event system is integrated into `src/gui.py`:

- The date display at the top shows the current date
- Left-click opens the date picker
- Right-click opens the detailed calendar view
- Events for the current date are shown in the "Events on current day" panel
- The "Events today" label shows a summary of today's events

## Backward Compatibility

The system maintains backward compatibility with the legacy calendar system:

- If the new events package is not available, the system falls back to the legacy implementation
- The `DetailedCalendarWindow` in `calendar_system.py` supports both old and new EventManager APIs
- Legacy code can continue to use the old text-based event creation

## Extensibility

The system is designed to be extensible:

1. **Adding Event Types**: Modify the `EventType` enum in `persistence.py`
2. **Custom Recurrence**: Extend `_event_occurs_on_date()` in `manager.py`
3. **Additional Fields**: Add fields to the `Event` class and update serialization methods
4. **UI Enhancements**: Create new dialog classes in `dialogs.py`

## Testing

Run the test suite:

```bash
python3 /tmp/test_events.py
```

This validates:
- Event creation with all types and recurrence patterns
- JSON persistence (save/load)
- EventManager CRUD operations
- Recurrence calculation logic
- Refresh callback functionality

## Error Handling

The system handles errors gracefully:

- Invalid JSON files: Returns empty list and prints error
- Missing storage file: Creates new file on first save
- Invalid event data: Skips malformed entries
- Callback failures: Catches exceptions and continues

## Best Practices

1. **Always use the EventManager**: Don't create Event objects directly unless you have a specific reason
2. **Check return values**: Update and delete operations return boolean success indicators
3. **Register callbacks wisely**: Only register callbacks that need to respond to changes
4. **Use enums**: Always use `EventType` and `RecurrenceType` enums instead of raw strings
5. **Handle None gracefully**: `get_event_by_id()` returns None if not found

## Future Enhancements

Possible improvements for future versions:

- Event categories and tags
- Event duration (start time, end time)
- Event priorities
- Conflict detection
- Export to iCalendar format
- Integration with weekly schedules
- Event templates
- Bulk operations
- Search and filter capabilities
