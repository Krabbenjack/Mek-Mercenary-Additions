# Manual Testing Guide: Event Participants & Execution Window

This document describes how to manually test the new event participant selection and execution window features.

## Prerequisites

1. Python 3.x installed
2. Tkinter available (usually comes with Python)
3. Character roster loaded (use Import Personnel JSON)
4. Calendar system functional

## Test Plan

### Test 1: Basic Event Creation and Execution

**Objective:** Verify that events can be created and started with the execution window.

**Steps:**
1. Launch the application: `cd mekhq_social_sim/src && python gui.py`
2. Import personnel data:
   - Click "Import" menu → "Import Personnel JSON"
   - Select `exports/personnel_complete.json` (if available)
   - Verify characters are loaded in the tree view
3. Open the calendar:
   - Right-click on the date display in the top-right corner
   - Calendar window should open
4. Create an event:
   - Right-click on any day in the calendar
   - Select "Add Event"
   - Choose an event type (e.g., "SIMULATOR_TRAINING_MECHWARRIOR")
   - Choose recurrence type (e.g., "Once")
   - Click "Create"
5. Navigate to the day with the event
   - The event should appear in "Today's Events" panel
6. Click "Start Event" button
   - **Expected:** Event Execution Window opens

### Test 2: Event Execution Window Display

**Objective:** Verify the execution window displays correctly.

**When the execution window opens, verify:**

**Header Section:**
- ✅ Event name is displayed (bold, large font)
- ✅ Event date is displayed (formatted as "Weekday, DD.MM.YYYY")
- ✅ Event ID is displayed (smaller, gray text)

**Character Lists:**
- ✅ Two columns are visible:
  - Left: "Available Characters"
  - Right: "Selected Participants"
- ✅ Both lists have scrollbars
- ✅ Characters in "Available" show: Name (Profession) or just Name
- ✅ Characters in "Selected" show: Name (Profession) or just Name
- ✅ Suggested participants (from selection engine) appear in "Selected" initially

**Buttons:**
- ✅ "Start Event" button is visible (green background)
- ✅ "Cancel" button is visible

### Test 3: Participant Selection Interaction

**Objective:** Verify users can modify participant selection.

**Steps:**
1. Open an event execution window (see Test 1)
2. **Double-click** on a character in "Available Characters"
   - **Expected:** Character moves to "Selected Participants"
   - **Expected:** Character removed from "Available Characters"
3. **Double-click** on a character in "Selected Participants"
   - **Expected:** Character moves back to "Available Characters"
   - **Expected:** Character removed from "Selected Participants"
4. Repeat steps 2-3 multiple times
   - **Expected:** Lists update correctly each time
   - **Expected:** No duplicates appear
   - **Expected:** No characters are lost

### Test 4: Event Execution with Participants

**Objective:** Verify event executes correctly with selected participants.

**Steps:**
1. Open an event execution window
2. Select desired participants (add/remove as needed)
3. Click "Start Event"
   - **Expected:** Window closes
   - **Expected:** Activity feed shows: "Manually started event: [Event Name] (ID:[ID])"
   - **Expected:** Activity feed shows: "✓ Event executed successfully"
   - **Expected:** Activity feed shows: "Participants: [list of character IDs]"

### Test 5: Cancel Event Execution

**Objective:** Verify canceling works correctly.

**Steps:**
1. Open an event execution window
2. Click "Cancel"
   - **Expected:** Window closes
   - **Expected:** NO execution log appears in activity feed
   - **Expected:** Event remains in "Today's Events" panel

### Test 6: Different Event Types

**Objective:** Verify selection engine resolves participants correctly for different event types.

**Test with these event types:**

**A. Training Events (1001-1006)**
- Requires specific roles (MechWarrior, Technician, etc.)
- **Expected:** Only characters with matching profession appear as suggested

**B. Social Events (3001-3143)**
- Multiple participants or pairs
- **Expected:** Multiple characters suggested (3-10 for group events, 2 for pair events)

**C. Children Events (4001-4503)**
- Requires children of specific age groups
- **Expected:** Only children of correct age are suggested
- Note: May show "not available" if no children exist

### Test 7: Edge Cases

**Objective:** Verify edge cases are handled gracefully.

**A. No Characters Available**
1. Start with empty character roster
2. Try to start an event
   - **Expected:** Warning message or empty lists in execution window
   - **Expected:** No crash

**B. No Suggested Participants**
1. Create an event that requires specific roles (e.g., MechWarrior)
2. Ensure no characters have that role
3. Start the event
   - **Expected:** "Selected Participants" list is empty
   - **Expected:** User can still manually add participants from "Available"

**C. Event with No Selection Rules**
1. Create an event with ID that has no selection rules
2. Start the event
   - **Expected:** Selection engine logs warning
   - **Expected:** No suggested participants
   - **Expected:** Execution window still works

### Test 8: Regression Testing

**Objective:** Verify existing functionality still works.

**A. Calendar Operations**
- ✅ Calendar opens via right-click
- ✅ Date picker works (left-click)
- ✅ Events can be created via right-click context menu
- ✅ Events can be edited
- ✅ Events can be deleted
- ✅ Month navigation works (Previous/Next buttons)

**B. Character Management**
- ✅ Character list displays correctly
- ✅ Character details show when selected
- ✅ Character search/filter works
- ✅ Import/Export still works

**C. Existing Event Dialogs**
- ✅ "Add Event" dialog works
- ✅ "Edit Event" dialog works
- ✅ "Manage Events" dialog works

### Test 9: Event Execution Log Verification

**Objective:** Verify execution logs contain correct data.

**Steps:**
1. Execute an event with 3 participants
2. Check the execution log:
   - **Expected:** `event_id` matches the event
   - **Expected:** `execution_date` matches current date
   - **Expected:** `participants` list contains 3 character IDs
   - **Expected:** `errors` list is empty (for valid execution)

### Test 10: Selection Engine Rule Verification

**Objective:** Verify selection engine loads and applies rules correctly.

**Check console output when starting application:**
- ✅ "[INFO] Loaded selection rules from injector_selection_rules_social.json"
- ✅ "[INFO] Loaded selection rules from injector_selection_rules_children_and_youth.json"
- ✅ "[INFO] Loaded selection rules from injector_selection_rules_training.json"
- ✅ "[INFO] Loaded selection rules from injector_selection_rules_youth_social.json"
- ✅ "[INFO] Loaded selection rules from injector_selection_rules_administration.json"

**When starting an event, check console:**
- ✅ "[INFO] Event [ID] resolved: X primary, Y derived, Z total"
- ✅ "[INFO] Using Z override participants for event [ID]"

## Expected Behavior Summary

### ✅ Core Functionality
- Events can be created via calendar
- Events appear in "Today's Events" panel
- Clicking "Start Event" opens execution window
- Execution window displays event metadata
- Suggested participants are pre-selected
- Users can add/remove participants
- Clicking "Start Event" executes event with selected participants
- Execution logs contain participant IDs

### ✅ Selection Engine
- Loads all 5 JSON rule files
- Parses rules for each event ID
- Resolves participants based on:
  - availability checks
  - primary_selection rules
  - derived_participants rules
- Applies filters: role, age_group, alive, present
- Returns structured result with primary, derived, and all participants

### ✅ UI/UX
- Minimal but functional design
- Two-column layout for character selection
- Double-click to add/remove
- Clear visual feedback
- Hint text for user guidance

### ✅ Backward Compatibility
- All existing calendar features work
- All existing event dialogs work
- Character management unaffected
- No existing functionality broken

## Known Limitations (By Design)

- No relationship-based selection (PARENT_OF, etc.) - logged as "not yet implemented"
- No persistence of participant overrides
- No story text or event outcomes
- No skill rolls or resolution
- UI is intentionally plain (no polish)

## Reporting Issues

If any test fails, report:
1. Test number and name
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Console output (if relevant)
6. Screenshot (if UI issue)
