# UI Testing Guide

## Overview

This document provides comprehensive testing procedures for all UI features in the MekHQ Social Sim application, including the Main UI redesign, Inspector panel, Calendar integration, and Campaign metadata import/export.

## Testing Categories

1. **Main UI Redesign Testing** - 4-region inspector-style layout
2. **Inspector Panel Testing** - Context-sensitive display system
3. **Calendar Integration Testing** - Phase 3 event system
4. **Campaign Metadata Testing** - Import/export and rank resolution
5. **Portrait System Testing** - Scaling and variant support

## 1. Main UI Redesign Testing

### Architecture Changes

**Removed**: Notebook/tab-based interface (Hauptansicht and Ereignisse tabs)
**Added**: 4-region inspector-style layout
**Removed**: Direct social interaction UI (manual/random roll buttons, partner selection)
**Added**: Event-based architecture with debug-only Social Director access

### New Layout Structure

```
┌──────────────────────────────────────────────┐
│ Top Bar (fixed ~36px)                        │
├───────────────┬─────────────────────────────┤
│ Left Pane     │ Right Pane (Inspector)       │
│ (Navigation)  │                               │
├───────────────┴─────────────────────────────┤
│ Bottom Pane (System Feed)                     │
└──────────────────────────────────────────────┘
```

### Region Testing

#### Top Bar Tests
- [ ] Fixed height: 36px
- [ ] Campaign Day displays correctly
- [ ] Date label shows current date in format "Monday, 01.01.2026"
- [ ] Left-click on date opens DatePickerDialog
- [ ] Right-click on date opens DetailedCalendarWindow
- [ ] "Next Day" button is present and enabled
- [ ] Top bar height is fixed (doesn't grow with window)
- [ ] No social or gameplay actions present

#### Left Navigation Pane Tests
- [ ] Width: ~20-25% (weight=1 in PanedWindow)
- [ ] TreeView is visible
- [ ] "Personnel" root node exists
- [ ] "No TO&E" child node exists
- [ ] TreeView has vertical scrollbar
- [ ] No horizontal scrollbar appears
- [ ] Tree structure shows:
  - Personnel (root)
    - Force Name
      - Unit Name
        - Character entries
    - No TO&E (for unassigned personnel)

#### Right Inspector Panel Tests

**Initial State (No Selection)**:
- [ ] Context header shows "CAMPAIGN"
- [ ] Primary block shows:
  - [ ] Campaign Day number
  - [ ] Current date
  - [ ] Characters loaded count
- [ ] Secondary block is empty
- [ ] Utility strip shows "Social Director (Debug)" button

**Character Selected**:
- [ ] Context header changes to "CHARACTER · [Name]"
- [ ] Primary block shows:
  - [ ] Small portrait (max 96×96px) on left
  - [ ] Character name (bold, larger)
  - [ ] Rank (if available)
  - [ ] Unit assignment or "No assignment"
  - [ ] "Details…" button
- [ ] Secondary block shows:
  - [ ] Profession (primary/secondary)
  - [ ] Age and age group
  - [ ] Interaction points
- [ ] No scrolling on inspector itself
- [ ] Content doesn't exceed reasonable height

**Inspector Interactions**:
- [ ] Clicking "Details…" opens CharacterDetailDialog
- [ ] CharacterDetailDialog displays correctly with all sections
- [ ] Clicking "Social Director (Debug)" shows placeholder messagebox

#### Bottom System Feed Tests
- [ ] Feed is visible at bottom
- [ ] "System Feed" label is present
- [ ] Text area is read-only (cannot type)
- [ ] Has vertical scrollbar
- [ ] Height is approximately 15-20% of window
- [ ] Background matches dark theme
- [ ] Day advancement messages appear
- [ ] Event notifications appear
- [ ] System status messages appear

### Startup & Initialization Tests
- [ ] Application starts without errors
- [ ] Dark military theme is applied (dark backgrounds, light text)
- [ ] Window opens at 1200×800px
- [ ] All four regions are visible
- [ ] No AttributeError on startup
- [ ] Inspector renders correctly

### Data Import & Display Tests

#### Personnel Import
- [ ] File > Import > Import Personnel (JSON) works
- [ ] After import, tree populates with characters
- [ ] "No TO&E" node contains all characters initially
- [ ] Character count updates in Campaign context

#### TO&E Import
- [ ] File > Import > Import TO&E (JSON) works
- [ ] After import, tree reorganizes by Force/Unit hierarchy
- [ ] Characters move from "No TO&E" to appropriate units
- [ ] Force and unit nodes are collapsible

#### Campaign Metadata Import
- [ ] File > Import > Import Campaign Meta works
- [ ] Date updates to campaign date
- [ ] Rank names resolve correctly

### Tree Navigation Tests
- [ ] Clicking character in tree selects it
- [ ] Inspector updates to show character context
- [ ] Right-clicking character opens CharacterDetailDialog
- [ ] Right-clicking Force/Unit nodes does nothing (expected)
- [ ] Tree nodes expand/collapse correctly

### Day Advancement Tests
- [ ] "Next Day" button advances campaign day
- [ ] System feed logs "--- Day [N] ---"
- [ ] System feed logs "Interaction points reset."
- [ ] If events exist for date, they appear in feed
- [ ] Selected character's inspector view updates (points reset)
- [ ] Date advances by one day

### Window Resizing Tests
- [ ] Window can be resized
- [ ] Top bar maintains fixed height
- [ ] Bottom feed maintains reasonable proportion
- [ ] Left/right pane split is adjustable via PanedWindow
- [ ] Inspector content doesn't break with small window
- [ ] No horizontal scrollbars appear unexpectedly

### Portrait Display Tests
- [ ] If PIL available and portrait exists:
  - [ ] Portrait displays in inspector (96×96 max)
  - [ ] Aspect ratio is maintained
  - [ ] No distortion or cropping
- [ ] If portrait missing:
  - [ ] "No portrait" message shows
  - [ ] No errors or crashes
- [ ] If PIL not available:
  - [ ] "No PIL" message shows
  - [ ] No errors or crashes

### Theme & Visual Hierarchy Tests
- [ ] Dark backgrounds throughout
- [ ] Light text on dark background (good contrast)
- [ ] Context header is visually distinct (muted, bold)
- [ ] Primary block has slightly elevated appearance
- [ ] Secondary block is visually subordinate
- [ ] Utility strip is de-emphasized
- [ ] Debug button looks tool-like, not like gameplay

### Menu Bar Tests
- [ ] File menu exists
- [ ] Export submenu has "Export Campaign Data" option
- [ ] Import submenu has three options:
  - [ ] Import Campaign Meta
  - [ ] Import Personnel (JSON)
  - [ ] Import TO&E (JSON)
- [ ] "Set External Portrait Folder..." option exists
- [ ] Exit option works

### Error Handling Tests
- [ ] Importing invalid JSON shows error dialog
- [ ] Selecting non-character tree node doesn't crash
- [ ] Missing portrait doesn't crash
- [ ] No characters loaded state is handled gracefully

## 2. Inspector Initialization Testing

### Problem Previously Identified
AttributeError on startup when `secondary_container` was accessed before creation.

### Build Order Validation
- [ ] All containers built BEFORE initial context display
- [ ] `_build_primary_block` is structure-only (no show methods)
- [ ] `_build_secondary_block` is structure-only (no clear methods)
- [ ] Utility Strip present and unconditional
- [ ] 'Social Director (Debug)' button exists

### Inspector Behavior Tests
- [ ] Selecting character in tree updates Inspector
- [ ] Context header changes correctly
- [ ] Primary block shows character info
- [ ] Secondary block shows supplementary info
- [ ] No container-related errors during switching

### Utility Strip Tests
- [ ] "Social Director (Debug)" button visible at bottom
- [ ] Button present regardless of selection
- [ ] Clicking button shows placeholder message (doesn't crash)

### Regression Checks
- [ ] Right-click character opens CharacterDetailDialog
- [ ] CharacterDetailDialog works unchanged
- [ ] Bottom feed still logs messages
- [ ] Window resizing doesn't break Inspector

## 3. Calendar Integration Testing (Phase 3)

### Calendar Access Tests
- [ ] Left-click date label opens DatePickerDialog
- [ ] Right-click date label opens DetailedCalendarWindow
- [ ] No explicit Calendar button visible
- [ ] No CalendarWidget embedded in top bar
- [ ] Single access point is intuitive and functional

### Event Creation Dialog Tests
- [ ] Right-click calendar date → "Add Event" opens EventCreationDialog
- [ ] Event Type dropdown shows human-readable names (not IDs)
- [ ] All 56 events from eventlist.json are available
- [ ] Event names are clear and understandable (e.g., "SIMULATOR_TRAINING_MECHWARRIOR")
- [ ] Creating event works correctly
- [ ] Recurrence options work (Once, Daily, Monthly, Yearly)

### Today's Events Panel Tests
- [ ] Panel is visible below top bar
- [ ] "📅 Today's Events" label is present
- [ ] Scheduled events for current date are displayed
- [ ] Each event shows: name, ID, recurrence
- [ ] "Start Event" button is present for each event
- [ ] "No events scheduled for today" shows when no events
- [ ] "No event system available" shows when system unavailable

### Event Execution Tests
- [ ] Clicking "Start Event" triggers event execution
- [ ] Event results appear in System Feed
- [ ] Participant names are logged
- [ ] Success/error status is clear
- [ ] No crashes or errors

### Date Change Tests
- [ ] Using Date Picker updates Today's Events panel
- [ ] Using "Next Day" button updates Today's Events panel
- [ ] Panel content reflects events for newly selected date
- [ ] Panel auto-refreshes correctly

### Layout Integration Tests
- [ ] Today's Events panel fits naturally in layout
- [ ] Top bar is cleaner and less cluttered
- [ ] No layout issues or overlaps
- [ ] Window resizing works correctly

## 4. Campaign Metadata Testing

### Export Tests (GUI Method)

**Step 1: Launch GUI**
```bash
cd mekhq_social_sim/src
python gui.py
```

**Step 2: Export via Menu**
- [ ] Click **File → Export → Export Campaign Data from .cpnx...**
- [ ] Select your .cpnx or .cpnx.gz file
- [ ] Observe success dialog

**Expected Result**:
- [ ] Three files created in `mekhq_social_sim/exports/`:
  - [ ] `personnel_complete.json`
  - [ ] `toe_complete.json`
  - [ ] `campaign_meta.json`
- [ ] Success message shows: personnel count, units count, date, rank system

### Export Tests (CLI Method)
```bash
cd mekhq_social_sim/src
python mekhq_personnel_exporter.py "path/to/campaign.cpnx" -o ../exports
```

**Expected Result**:
- [ ] Three files created in `exports/`
- [ ] `campaign_meta.json` contains campaign_date and rank_system

### Rank Resolution Tests (CLI)
```bash
cd mekhq_social_sim/src
python3 -c "
from rank_resolver import get_rank_resolver

resolver = get_rank_resolver()
resolver.set_rank_system('SLDF')

print('Rank 33 (Lieutenant):', resolver.resolve_rank_name(33))
print('Rank 34 (Captain):', resolver.resolve_rank_name(34))
print('Rank 21 (Warrant Officer):', resolver.resolve_rank_name(21))
"
```

**Expected Output**:
- [ ] ✅ Loaded 19 rank systems
- [ ] ✅ Active rank system set to: Star League Defense Force (SLDF)
- [ ] Rank 33: Lieutenant
- [ ] Rank 34: Captain
- [ ] Rank 21: Warrant Officer

### Personnel Loading Tests
```bash
cd mekhq_social_sim/src
python3 -c "
from data_loading import load_campaign
from rank_resolver import get_rank_resolver

resolver = get_rank_resolver()
resolver.set_rank_system('SLDF')

chars = load_campaign('../exports/personnel_complete.json')
print(f'Loaded {len(chars)} characters')

for i, (cid, char) in enumerate(list(chars.items())[:5]):
    if char.rank:
        print(f'  {char.name}: rank_id={char.rank}, rank_name={char.rank_name}')
"
```

**Expected**:
- [ ] Characters load successfully
- [ ] Rank names are resolved (e.g., "Lieutenant" instead of "33")

### GUI Integration Tests

**Step 1: Export Campaign Data**
- [ ] File → Export → Export Campaign Data from .cpnx...
- [ ] Files created in `mekhq_social_sim/exports/`
- [ ] Success dialog shows export summary
- [ ] Log window shows export progress

**Step 2: Import Campaign Metadata**
- [ ] File → Import → Import Campaign Meta (Date & Rank System)
- [ ] Select your .cpnx or .cpnx.gz file
- [ ] Success message shows campaign date and rank system loaded
- [ ] Date field updates to campaign date
- [ ] Date field remains editable

**Step 3: Import Personnel**
- [ ] File → Import → Import Personnel (JSON)
- [ ] Select `personnel_complete.json`
- [ ] Characters load into tree view
- [ ] Rank names appear in character details (not numeric IDs)

**Step 4: Verify Rank Display**
- [ ] Click on various characters in tree view
- [ ] Check character details panel
- [ ] Right-click character → view detail dialog
- [ ] Rank displays as NAME (e.g., "Lieutenant"), not number (e.g., "33")

### Fallback Behavior Tests

**Unknown Rank System**:
- [ ] Import campaign with rank system not in config
- [ ] Expected: Shows "Rank 33 (UNKNOWN_SYSTEM)" or similar

**Missing Rank System**:
- [ ] Load personnel without setting rank system first
- [ ] Expected: Shows "Rank 33" or "No Rank"

**Invalid Rank ID**:
- [ ] Character with rank ID 999 (not in system)
- [ ] Expected: Shows "Unknown Rank 999 (SLDF)" or similar

## 5. Portrait System Testing

### Portrait Bounded Scaling Tests

**Tall Portrait (400x900 _cas variant)**:
- [ ] Scales to fit height limit (300px max)
- [ ] Preserves aspect ratio
- [ ] No cropping or distortion

**Square Portrait (512x512)**:
- [ ] Scales to 220x220 (fills width limit)
- [ ] Aspect ratio maintained

**Wide Portrait (900x400)**:
- [ ] Scales to fit width limit (220px max)
- [ ] Aspect ratio maintained

**Small Portrait (100x150)**:
- [ ] Remains 100x150 (no upscaling)
- [ ] Not enlarged beyond original size

### Portrait Variant Tests

**Main Character Window**:
- [ ] Shows default portrait (e.g., MW_F_4.png)
- [ ] Uses PortraitHelper.load_portrait_image()
- [ ] Max size 250x250

**Character Detail Dialog**:
- [ ] Prefers casual variant (e.g., MW_F_4_cas.png)
- [ ] Falls back to default if casual not found
- [ ] Uses bounded scaling (max 220x300)
- [ ] Preserves aspect ratio

### Portrait Search Flow Tests

**Priority Order**:
1. [ ] Module: images/portraits/ searched first
2. [ ] External: (if configured) searched second

**Extension Priority**:
- [ ] Original extension tried first
- [ ] Then .png, .jpg, .jpeg, .gif, .bmp in order

**Category Subdirectory Support**:
- [ ] Portraits in Male/ subdirectory load correctly
- [ ] Portraits in Female/ subdirectory load correctly
- [ ] Category is read from character's portrait metadata

## 6. Regression Testing

### Must Not Break

- [ ] **Existing Personnel Import** - Works without campaign metadata
- [ ] **TO&E Import** - Still functions correctly
- [ ] **Portrait Display** - No changes to portrait handling
- [ ] **Character Details** - All existing fields still visible
- [ ] **Social Interactions** - Synergy engine unaffected
- [ ] **Calendar System** - Event management unchanged
- [ ] **Day Advancement** - Still works correctly

## 7. Automated Testing

### TO&E Import Test Script

```bash
cd /path/to/Mek-Mercenary-Additions
python3 test_toe_import.py
```

**Expected Output**:
```
============================================================
TO&E IMPORT TEST
============================================================

This test verifies that TO&E import is working correctly.
Make sure you have exported campaign data first!

1. Loading personnel...
   ✅ Loaded XX characters

2. Applying TO&E structure...
   ✅ Characters with units: XX/XX

3. Building tree structure...
   ✅ Forces found: X
   ✅ Personnel without TO&E: XX

4. Tree structure:
   Personal (root)
   ├── [Your Force Names]
   │   ├── [Your Unit Names] (X personnel)
   │   └── ...
   └── Ohne TO&E (XX personnel without assignments)

✅ TO&E IMPORT TEST PASSED
```

This test verifies:
- [ ] Personnel loading works correctly
- [ ] TO&E structure is properly applied
- [ ] Characters are assigned to correct forces and units
- [ ] Tree structure is built correctly for GUI display

## Test Data

Use existing test files:
- `mekhq_social_sim/exports/personnel_complete.json`
- `mekhq_social_sim/exports/toe_complete.json`
- `mekhq_social_sim/exports/campaign_meta.json`

## Recommended Test Flow

1. **Start application**
2. **Import campaign metadata** (sets date and rank system)
3. **Import personnel** (loads characters)
4. **Import TO&E** (organizes characters)
5. **Select various characters** and verify inspector display
6. **Right-click to open detail dialogs**
7. **Advance day** and verify feed updates
8. **Resize window** and verify layout stability
9. **Test calendar interaction** (left-click date, right-click date)
10. **Add events** via calendar
11. **Verify Today's Events panel** shows events
12. **Execute events** via Start Event buttons
13. **Change dates** and verify panel updates

## Success Criteria

The UI testing is successful if:
1. ✅ Application starts without exceptions
2. ✅ All four regions are present and functional
3. ✅ Inspector displays context-appropriate information
4. ✅ No gameplay actions are in Main UI
5. ✅ Dark theme is applied throughout
6. ✅ Character detail dialogs still work
7. ✅ Data import/export still works
8. ✅ Layout is stable during resize
9. ✅ Code is clean and maintainable
10. ✅ No regressions in existing features
11. ✅ Calendar integration works as designed
12. ✅ Today's Events panel functions correctly
13. ✅ Event creation uses eventlist.json
14. ✅ Rank names display correctly
15. ✅ Portrait scaling works as expected

## Known Limitations

1. **No GUI Testing in CI**: This environment doesn't have tkinter, so automated GUI tests are not possible
2. **Social Director**: Not yet implemented - shows placeholder message
3. **Unit Context**: Not yet implemented in inspector (only Campaign and Character contexts)
4. **Event Details**: Events show in feed as single-line entries, not detailed descriptions

## Performance Benchmarks

### Expected Performance
- Export campaign metadata: < 1 second
- Load 19 rank systems: < 0.1 second (one-time)
- Resolve 100 character ranks: < 0.01 second
- Total personnel load (100 chars): < 0.1 second

### Performance Test
```bash
cd mekhq_social_sim/src
python3 -c "
import time
from data_loading import load_campaign
from rank_resolver import get_rank_resolver

resolver = get_rank_resolver()
resolver.set_rank_system('SLDF')

start = time.time()
chars = load_campaign('../exports/personnel_complete.json')
elapsed = time.time() - start

print(f'Loaded {len(chars)} characters in {elapsed:.3f}s')
"
```

## Notes for Developer Testing

### Visual Inspection Points
- **Calm & Operational**: UI should feel inspector-like, not game-like
- **Clear Hierarchy**: Context header > Primary > Secondary > Utility
- **No Clutter**: Only essential information in inspector
- **Professional**: Dark military aesthetic, not flashy or colorful
- **Functional**: Everything has a clear purpose

### Common Issues to Watch For
- Container initialization order errors
- Portrait scaling distortion
- Missing rank name resolution
- Event dropdown showing IDs instead of names
- Today's Events panel not updating
- Inspector not switching contexts correctly
- System Feed not logging events
- Calendar access not working

## Conclusion

This testing guide provides comprehensive coverage of all UI features. Manual testing is required since the application uses tkinter which is not available in CI environments. Follow the checklists systematically to ensure all features work correctly and no regressions have been introduced.
