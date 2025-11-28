# Event System GUI Features - Visual Guide

## Overview
This document describes the GUI enhancements made to the calendar and event system.

## Main Application Window

### Date Display (Top Bar)
```
┌─────────────────────────────────────────────────────────┐
│ Friday, 22.11.2025  [Nächster Tag]  [Import Buttons...] │
│                                                          │
│ Events today: Field Training (Infantry), Simulator...   │
└─────────────────────────────────────────────────────────┘
```

**Interactions:**
- **Left-click** on date: Opens date picker dialog
- **Right-click** on date: Opens detailed calendar view

---

## Detailed Calendar View

### Month Calendar Grid
```
┌─────────────────────────────────────────────────────────┐
│        << Previous    November 2025    Next >>          │
├─────────────────────────────────────────────────────────┤
│ Mon   Tue   Wed   Thu   Fri   Sat   Sun                │
├─────────────────────────────────────────────────────────┤
│                             1     2                      │
│  3     4     5     6     7     8     9                  │
│ 10    11    12    13    14    15    16                  │
│                               (2)                        │
│ 17    18    19    20    21    22    23                  │
│                         (1)                              │
│ 24    25    26    27    28    29    30                  │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Days with events show count in parentheses: `15\n(2 events)`
- Days with events are highlighted in **light blue**
- **Left-click** on a day: Selects the day and updates event list below
- **Right-click** on a day: Opens context menu

### Context Menu (Right-Click on Day)
```
┌────────────────┐
│ Add Event      │
│ Manage Events  │
└────────────────┘
```

---

## Event Creation Dialog

### Add Event Dialog
```
┌─────────────────────────────────────────────────────┐
│              Create Event                           │
├─────────────────────────────────────────────────────┤
│  Date: Friday, 15.11.2025                          │
│                                                     │
│  Event Type:                                        │
│  ┌─────────────────────────────────────────────┐  │
│  │ Field Training (Infantry)            ▼     │  │
│  └─────────────────────────────────────────────┘  │
│  Options:                                          │
│    - Field Training (Infantry)                    │
│    - Simulator Training (MekWarrior)              │
│    - Equipment Maintenance (Tech)                 │
│                                                     │
│  Recurrence:                                        │
│  ┌─────────────────────────────────────────────┐  │
│  │ Once                                  ▼     │  │
│  └─────────────────────────────────────────────┘  │
│  Options:                                          │
│    - Once                                          │
│    - Daily                                         │
│    - Monthly                                       │
│    - Yearly                                        │
│                                                     │
│         [Create]          [Cancel]                 │
└─────────────────────────────────────────────────────┘
```

**Key Changes from Legacy:**
- ❌ No free-text entry field
- ✅ Dropdown for event type (restricted to 3 types)
- ✅ Dropdown for recurrence (restricted to 4 patterns)
- ❌ No "Weekly" option

---

## Event Edit Dialog

### Edit Event Dialog
```
┌─────────────────────────────────────────────────────┐
│              Edit Event                             │
├─────────────────────────────────────────────────────┤
│  Editing Event ID: 15                              │
│  Date: Friday, 15.11.2025                          │
│                                                     │
│  Event Type:                                        │
│  ┌─────────────────────────────────────────────┐  │
│  │ Simulator Training (MekWarrior)      ▼     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  Recurrence:                                        │
│  ┌─────────────────────────────────────────────┐  │
│  │ Monthly                               ▼     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│          [Save]           [Cancel]                 │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Shows event ID for reference
- Pre-filled with current values
- Date is read-only (shown but not editable)
- Same dropdown restrictions as creation

---

## Manage Events Dialog

### Manage Events for a Day
```
┌─────────────────────────────────────────────────────┐
│         Manage Events                               │
├─────────────────────────────────────────────────────┤
│  Events for: Friday, 15.11.2025                    │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Field Training (Infantry) (once) [ID: 15]    │ │
│  │ Simulator Training (MekWarrior) (daily) [...] │ │
│  │                                                │ │
│  │                                                │ │
│  │                                                │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│      [Edit]         [Delete]        [Close]        │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Lists all events for the selected day
- Shows event type, recurrence, and ID
- **Edit**: Opens edit dialog with pre-filled values
- **Delete**: Shows confirmation dialog, then removes event
- Events are sorted and displayed clearly

**Delete Confirmation:**
```
┌─────────────────────────────────────────┐
│        Confirm Delete                   │
├─────────────────────────────────────────┤
│  Are you sure you want to delete this  │
│  event?                                 │
│                                         │
│  Field Training (Infantry)              │
│  (once)                                 │
│                                         │
│      [Yes]            [No]              │
└─────────────────────────────────────────┘
```

---

## Event Display in Main Window

### Events on Current Day Panel
```
┌─────────────────────────────────────────────────────────┐
│          Events on current day                          │
├─────────────────────────────────────────────────────────┤
│ - Field Training (Infantry) (once)                     │
│   The unit performs field training exercises.          │
│                                                          │
│ - Simulator Training (MekWarrior) (daily)               │
│   The unit performs simulator training focusing on     │
│   tactics and coordination.                             │
│                                                          │
│ - Equipment Maintenance (Tech) (monthly)                │
│   The mechs undergo scheduled maintenance and repairs.  │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Shows all events for the currently selected date
- Includes event type and recurrence pattern
- Displays descriptive text based on event type
- Updates automatically when date changes

---

## Calendar Day Display

### Day Button States

**Normal Day (No Events):**
```
┌──────┐
│  15  │
└──────┘
```

**Day with Events:**
```
┌──────────┐
│    15    │
│(2 events)│  [Light Blue Background]
└──────────┘
```

**Features:**
- Event count shown in parentheses
- Light blue background highlights days with events
- Right-click shows context menu
- Left-click selects the day

---

## Workflow Examples

### Creating a New Event

1. Open calendar view (right-click date display)
2. Right-click on desired day → Select "Add Event"
3. Select event type from dropdown (e.g., "Field Training (Infantry)")
4. Select recurrence from dropdown (e.g., "Monthly")
5. Click "Create"
6. Event appears on calendar with count
7. Event is automatically saved to JSON

### Editing an Existing Event

1. Open calendar view
2. Right-click on day with events → Select "Manage Events"
3. Select event from list
4. Click "Edit"
5. Change event type or recurrence
6. Click "Save"
7. Changes are automatically persisted

### Deleting an Event

1. Open calendar view
2. Right-click on day with events → Select "Manage Events"
3. Select event from list
4. Click "Delete"
5. Confirm deletion
6. Event is removed and changes saved

---

## Technical Details

### Event Types (Dropdown Options)
1. Field Training (Infantry)
2. Simulator Training (MekWarrior)
3. Equipment Maintenance (Tech)

### Recurrence Patterns (Dropdown Options)
1. Once
2. Daily
3. Monthly
4. Yearly

### Persistence
- Events stored in: `~/.mekhq_social_sim/events.json`
- Format: JSON with automatic save on changes
- Loads automatically on application start

---

## Integration with Existing Features

### Compatibility
- ✅ Works with existing character management
- ✅ Works with daily interaction system
- ✅ Works with TO&E structure
- ✅ All previous calendar features preserved
- ✅ Backward compatible with legacy event system

### New Features Don't Break
- Date picker still works (left-click)
- Next day button still works
- Character age calculation still works
- All existing event displays still work

---

## Benefits of the New System

1. **Type Safety**: Predefined event types prevent typos and inconsistencies
2. **User-Friendly**: Dropdown selections are easier than free-text entry
3. **Persistent**: Events survive application restarts
4. **Maintainable**: Modular code structure in src/events/
5. **Extensible**: Easy to add new event types or features
6. **Reliable**: Comprehensive test coverage ensures stability
7. **Professional**: Clean, modern GUI with consistent behavior
