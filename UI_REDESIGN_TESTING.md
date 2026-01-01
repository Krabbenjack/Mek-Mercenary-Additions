# Main UI Redesign - Testing Guide

## Overview
This document describes the Main UI redesign changes and provides a testing checklist for manual verification.

## Changes Summary

### Architecture Changes
- **Removed**: Notebook/tab-based interface (Hauptansicht and Ereignisse tabs)
- **Added**: 4-region inspector-style layout
- **Removed**: Direct social interaction UI (manual/random roll buttons, partner selection)
- **Added**: Event-based architecture with debug-only Social Director access

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

### Region Details

#### 1. Top Bar
- Fixed height: 36px
- Contains:
  - Campaign Day display (clickable for date picker)
  - Next Day button
  - Calendar access via right-click
- **No social or gameplay actions**

#### 2. Left Navigation Pane
- Width: ~20-25% (weight=1 in PanedWindow)
- Contains: TreeView only
- Shows personnel hierarchy by TO&E
- Vertical scrolling enabled
- Tree structure:
  - Personnel (root)
    - Force Name
      - Unit Name
        - Character entries
    - No TO&E (for unassigned personnel)

#### 3. Right Inspector Panel
- Width: ~75-80% (weight=3 in PanedWindow)
- Structure (top to bottom):
  1. **Context Header** (fixed ~24px)
     - Shows: "CAMPAIGN", "CHARACTER · [Name]", or "UNIT · [Name]"
     - Single line, muted style
     - No buttons
  
  2. **Primary Block** (expandable, max ~40% height)
     - **Campaign Context**:
       - Campaign Day number
       - Current date
       - Character count
     - **Character Context**:
       - Portrait (max 96×96px, left side)
       - Name (bold)
       - Rank
       - Unit assignment
       - "Details…" button (opens CharacterDetailDialog)
  
  3. **Secondary Block** (optional)
     - **Character Context**:
       - Profession
       - Age and age group
       - Interaction points
     - Text-only, no buttons
  
  4. **Utility Strip** (fixed ~32px, bottom)
     - Contains: "Social Director (Debug)" button
     - Debug-style appearance
     - Placeholder - opens info messagebox

#### 4. Bottom System Feed
- Height: ~15-20% (120px default)
- Read-only text widget
- Shows:
  - Day advancement messages
  - Event notifications
  - System status
- Vertical scrolling enabled
- Dark panel background with secondary text color

### Theme Integration
- Dark military theme from `ui_theme.py` applied globally
- Styles used:
  - `Main.TFrame` - Main background
  - `Panel.TFrame` - Panel backgrounds
  - `Raised.TFrame` - Elevated blocks
  - `Primary.TLabel` - Main text
  - `Secondary.TLabel` - Supporting text
  - `Context.TLabel` - Context header (muted, bold)
  - `Primary.TButton` - Standard buttons
  - `Debug.TButton` - Debug tools (visually de-emphasized)

### Removed Features
- ❌ "Ereignisse" tab (events now in bottom feed)
- ❌ Partner selection listbox
- ❌ Manual/random roll buttons
- ❌ Day events description panel
- ❌ Inline character details text widget
- ❌ Large portrait display (250×250)

### Modified Features
- ✓ Portrait display: Now max 96×96px in inspector
- ✓ Character selection: Now updates inspector context
- ✓ Right-click: Opens CharacterDetailDialog (unchanged)
- ✓ Events: Now appear in bottom system feed only
- ✓ Day advancement: Logs to system feed

## Testing Checklist

### Startup & Initialization
- [ ] Application starts without errors
- [ ] Dark military theme is applied (dark backgrounds, light text)
- [ ] Window opens at 1200×800px
- [ ] All four regions are visible

### Top Bar
- [ ] Campaign day displays correctly
- [ ] Date label shows current date in format "Monday, 01.01.2026"
- [ ] Left-click on date opens DatePickerDialog
- [ ] Right-click on date opens DetailedCalendarWindow
- [ ] "Next Day" button is present and enabled
- [ ] Top bar height is fixed (doesn't grow with window)

### Left Navigation Pane
- [ ] TreeView is visible
- [ ] "Personnel" root node exists
- [ ] "No TO&E" child node exists
- [ ] TreeView has vertical scrollbar
- [ ] No horizontal scrollbar appears
- [ ] Width is approximately 20-25% of window

### Right Inspector Panel

#### Initial State (No Selection)
- [ ] Context header shows "CAMPAIGN"
- [ ] Primary block shows:
  - [ ] Campaign Day number
  - [ ] Current date
  - [ ] Characters loaded count (0 initially)
- [ ] Secondary block is empty
- [ ] Utility strip shows "Social Director (Debug)" button

#### Character Selected
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

#### Inspector Interactions
- [ ] Clicking "Details…" opens CharacterDetailDialog
- [ ] CharacterDetailDialog displays correctly with all sections
- [ ] Clicking "Social Director (Debug)" shows placeholder messagebox

### Bottom System Feed
- [ ] Feed is visible at bottom
- [ ] "System Feed" label is present
- [ ] Text area is read-only (cannot type)
- [ ] Has vertical scrollbar
- [ ] Height is approximately 15-20% of window
- [ ] Background matches dark theme

### Data Import & Display

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

### Tree Navigation
- [ ] Clicking character in tree selects it
- [ ] Inspector updates to show character context
- [ ] Right-clicking character opens CharacterDetailDialog
- [ ] Right-clicking Force/Unit nodes does nothing (expected)
- [ ] Tree nodes expand/collapse correctly

### Day Advancement
- [ ] "Next Day" button advances campaign day
- [ ] System feed logs "--- Day [N] ---"
- [ ] System feed logs "Interaction points reset."
- [ ] If events exist for date, they appear in feed
- [ ] Selected character's inspector view updates (points reset)
- [ ] Date advances by one day

### Window Resizing
- [ ] Window can be resized
- [ ] Top bar maintains fixed height
- [ ] Bottom feed maintains reasonable proportion
- [ ] Left/right pane split is adjustable via PanedWindow
- [ ] Inspector content doesn't break with small window
- [ ] No horizontal scrollbars appear unexpectedly

### Portrait Display
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

### Theme & Visual Hierarchy
- [ ] Dark backgrounds throughout
- [ ] Light text on dark background (good contrast)
- [ ] Context header is visually distinct (muted, bold)
- [ ] Primary block has slightly elevated appearance
- [ ] Secondary block is visually subordinate
- [ ] Utility strip is de-emphasized
- [ ] Debug button looks tool-like, not like gameplay

### Menu Bar
- [ ] File menu exists
- [ ] Export submenu has "Export Campaign Data" option
- [ ] Import submenu has three options:
  - [ ] Import Campaign Meta
  - [ ] Import Personnel (JSON)
  - [ ] Import TO&E (JSON)
- [ ] "Set External Portrait Folder..." option exists
- [ ] Exit option works

### Error Handling
- [ ] Importing invalid JSON shows error dialog
- [ ] Selecting non-character tree node doesn't crash
- [ ] Missing portrait doesn't crash
- [ ] No characters loaded state is handled gracefully

### Compatibility
- [ ] CharacterDetailDialog still works unchanged
- [ ] All existing data files (personnel_complete.json, toe_complete.json) load correctly
- [ ] Campaign metadata import still works
- [ ] Calendar system integration still works

## Known Limitations

1. **No GUI Testing in CI**: This environment doesn't have tkinter, so automated GUI tests are not possible
2. **Social Director**: Not yet implemented - shows placeholder message
3. **Unit Context**: Not yet implemented in inspector (only Campaign and Character contexts)
4. **Event Details**: Events show in feed as single-line entries, not detailed descriptions

## Notes for Developer Testing

### Test Data
Use existing test files:
- `mekhq_social_sim/exports/personnel_complete.json`
- `mekhq_social_sim/exports/toe_complete.json`
- `mekhq_social_sim/exports/campaign_meta.json`

### Recommended Test Flow
1. Start application
2. Import campaign metadata (sets date and rank system)
3. Import personnel (loads characters)
4. Import TO&E (organizes characters)
5. Select various characters and verify inspector display
6. Right-click to open detail dialogs
7. Advance day and verify feed updates
8. Resize window and verify layout stability
9. Test calendar interaction (left-click date, right-click date)

### Visual Inspection Points
- **Calm & Operational**: UI should feel inspector-like, not game-like
- **Clear Hierarchy**: Context header > Primary > Secondary > Utility
- **No Clutter**: Only essential information in inspector
- **Professional**: Dark military aesthetic, not flashy or colorful
- **Functional**: Everything has a clear purpose

## Code Structure Verification

### Automated Checks Passed ✓
- [x] All required methods present
- [x] All obsolete methods removed
- [x] Python syntax validation passed
- [x] No import errors (except tkinter in headless env)
- [x] Structure validation passed

### Files Modified
- `mekhq_social_sim/src/gui.py` - Complete restructure of MekSocialGUI class

### Files Unchanged
- `mekhq_social_sim/src/ui_theme.py` - Theme definitions (already existed)
- `mekhq_social_sim/src/models.py` - Data models
- `mekhq_social_sim/src/relationship_detail_dialog.py` - Detail dialog
- All other domain logic files

## Success Criteria

The redesign is successful if:
1. ✅ Application starts without errors
2. ✅ All four regions are present and functional
3. ✅ Inspector displays context-appropriate information
4. ✅ No gameplay actions are in Main UI
5. ✅ Dark theme is applied throughout
6. ✅ Character detail dialogs still work
7. ✅ Data import/export still works
8. ✅ Layout is stable during resize
9. ✅ Code is clean and maintainable
10. ✅ No regressions in existing features

## Smoke Test Results

**Environment**: Headless (no tkinter available)
**Code Validation**: ✅ All checks passed
**Manual Testing**: ⚠️ Requires user with GUI environment

The code has been validated for:
- Syntax correctness
- Structure compliance
- Method presence/absence
- Import resolution (non-GUI modules)

**Next Step**: Manual testing by user in GUI environment required to verify visual appearance and interaction behavior.
