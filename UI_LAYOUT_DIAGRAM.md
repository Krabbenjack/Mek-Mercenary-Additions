# UI Layout - Before and After Phase 3

## BEFORE (Redundant Calendar Access)

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar                                                        │
│ [Date Label] [Next Day] [📅 Calendar Button] [CalendarWidget] │
│  ↓ left-click  ↓ right-click                                  │
│  Date Picker   Calendar Window                                │
└────────────────────────────────────────────────────────────────┘
├────────────────────────────────────────────────────────────────┤
│ Main Content Area (Personnel Tree + Inspector)                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
├────────────────────────────────────────────────────────────────┤
│ System Feed (Log Panel)                                       │
└────────────────────────────────────────────────────────────────┘
```

**Problems**:
- 3 ways to access calendar (confusing!)
- CalendarWidget takes up space but provides no unique value
- Explicit Calendar button duplicates date label functionality
- No visibility of today's events without opening calendar

---

## AFTER (Clean + Today's Events Panel)

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar                                                        │
│ [Date Label (clickable)] [Next Day]                           │
│  ↓ left-click  ↓ right-click                                  │
│  Date Picker   Calendar Window (for planning)                 │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│ 📅 Today's Events                                             │
├────────────────────────────────────────────────────────────────┤
│ • Simulator Training Mekwarrior          [Start Event]       │
│   ID: 1001 | Recurrence: Once                                │
│                                                                │
│ • Personnel Meeting                        [Start Event]       │
│   ID: 2001 | Recurrence: Monthly                             │
└────────────────────────────────────────────────────────────────┘
├────────────────────────────────────────────────────────────────┤
│ Main Content Area (Personnel Tree + Inspector)                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
├────────────────────────────────────────────────────────────────┤
│ System Feed (Log Panel)                                       │
└────────────────────────────────────────────────────────────────┘
```

**Improvements**:
- ✅ Single calendar access point (date label)
- ✅ Cleaner, less cluttered top bar
- ✅ New Today's Events panel shows active events
- ✅ Manual event triggering via "Start Event" button
- ✅ Events visible without opening calendar
- ✅ System feels active and transparent

---

## Event Creation Dialog - Before and After

### BEFORE (Showing Numeric IDs)

```
┌─────────────────────────────────────┐
│ Create Event                        │
├─────────────────────────────────────┤
│ Date: Wednesday, 15.01.2025         │
│                                     │
│ Event Type:                         │
│ [1001                          ▼]   │  ← Hard to understand!
│                                     │
│ Recurrence:                         │
│ [Once                          ▼]   │
│                                     │
│        [Create]  [Cancel]           │
└─────────────────────────────────────┘
```

### AFTER (Showing Event Names)

```
┌─────────────────────────────────────────────────────────┐
│ Create Event                                            │
├─────────────────────────────────────────────────────────┤
│ Date: Wednesday, 15.01.2025                             │
│                                                         │
│ Event Type:                                             │
│ [SIMULATOR_TRAINING_MECHWARRIOR                    ▼]   │  ← Clear!
│                                                         │
│ Recurrence:                                             │
│ [Once                                              ▼]   │
│                                                         │
│        [Create]  [Cancel]                               │
└─────────────────────────────────────────────────────────┘
```

**Dropdown Contents**:
- SIMULATOR_TRAINING_MECHWARRIOR (ID: 1001)
- INFANTRY_FIELD_EXERCISE (ID: 1002)
- TECHNICAL_MAINTENANCE (ID: 1003)
- ... (56 total events from eventlist.json)

---

## Calendar Window Integration

### Calendar remains for PLANNING:
- Right-click date label → Detailed Calendar Window
- Add events for future dates
- Manage scheduled events
- View event recurrence

### Main UI for EXECUTION:
- Today's Events panel shows what's active TODAY
- "Start Event" button triggers event immediately
- Results logged to System Feed
- No need to open calendar for daily operations

---

## User Workflow Examples

### Planning a Training Event
1. Right-click date label → Open Calendar
2. Navigate to desired date
3. Right-click day → "Add Event"
4. Select "SIMULATOR_TRAINING_MECHWARRIOR" from dropdown
5. Select recurrence (Once, Daily, Monthly, Yearly)
6. Click "Create"
7. Event appears on calendar with indicator

### Executing Today's Events
1. Launch application
2. Check "Today's Events" panel
3. See scheduled events with details
4. Click "Start Event" for desired event
5. Event executes → Participants selected → Results logged
6. Check System Feed for execution details

### Changing Date to See Other Events
1. Left-click date label → Date Picker
2. Select new date
3. Today's Events panel auto-updates
4. Shows events for selected date

---

## Design Principles Implemented

| Principle | Implementation |
|-----------|---------------|
| Calendar = Planning | Calendar window for scheduling, right-click access |
| Main UI = Execution | Today's Events panel with Start Event buttons |
| Event System = Single Source | All events from eventlist.json, no free-text |
| Minimize Redundancy | Single calendar access point (date label) |
| Maximize Visibility | Events visible in main UI, no need to open calendar |
| User Control | Manual event triggering via buttons |

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         GUI Layer                           │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Date Label   │  │  Calendar    │  │  Today's Events │ │
│  │  (Controls)   │  │  Window      │  │  Panel          │ │
│  └───────┬───────┘  └──────┬───────┘  └────────┬────────┘ │
└──────────┼──────────────────┼───────────────────┼──────────┘
           │                  │                   │
           ▼                  ▼                   ▼
    ┌──────────────────────────────────────────────────────┐
    │              EventManager (Business Logic)           │
    │  - get_events_for_date()                            │
    │  - add_event()                                      │
    │  - execute_events_for_date()                        │
    └──────────────────┬───────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────┐
    │         EventInjector (Execution Engine)             │
    │  - validate_event_id()                              │
    │  - execute_event()                                  │
    │  - select_participants()                            │
    └──────────────────┬───────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────┐
    │          eventlist.json (Single Source)              │
    │  - SIMULATOR_TRAINING_MECHWARRIOR: 1001             │
    │  - INFANTRY_FIELD_EXERCISE: 1002                    │
    │  - ... (56 total event types)                       │
    └──────────────────────────────────────────────────────┘
```

---

**Summary**: Clean, intuitive UI with visible event system and unified calendar access.
