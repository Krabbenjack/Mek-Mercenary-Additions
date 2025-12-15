# GUI Menu Bar and Portrait Loading Refactor - Implementation Summary

## Changes Implemented

### Part A: Menu Bar Refactor ✅

**File**: `mekhq_social_sim/src/gui.py`

1. **Added Menu Bar** (`_build_menu_bar` method):
   - Created `File` menu with `Import` submenu
   - Menu items:
     - `Import Personnel (JSON)...` → calls `_import_personnel()`
     - `Import TO&E (JSON)...` → calls `_import_toe()`
     - `Set External Portrait Folder...` → calls `_set_external_portrait_folder()`
     - `Exit` → quits application

2. **Removed Old Import Buttons**:
   - Removed `import_pers_btn` and `import_toe_btn` from top toolbar
   - Kept `NÃ¤chster Tag` button and date label

### Part B: External Portrait Folder + Multi-Root Search ✅

**File**: `mekhq_social_sim/src/gui.py`

1. **Added PortraitConfig Class**:
   - Manages portrait configuration
   - Loads/saves external portrait folder to `config/portrait_config.json`
   - Provides search paths in priority order (module folder first, then external)

2. **Portrait Search Paths**:
   - Default: `mekhq_social_sim/images/portraits/`
   - External: User-configured folder (optional)
   - Both paths searched when resolving portraits

3. **New Menu Action**: `_set_external_portrait_folder()`
   - Opens directory dialog
   - Saves selection to config file
   - Shows confirmation message
   - Immediately refreshes current character display

### Part C: Portrait Variant Suffix Support ✅

**File**: `mekhq_social_sim/src/gui.py`

1. **Updated PortraitHelper Class**:
   - `_extract_base_and_extension()`: Extracts base name and extension
   - `_find_portrait_variant()`: Searches for portrait with variant suffix
   - `resolve_portrait_path()`: Main resolver with `prefer_casual` parameter
   
2. **Variant Resolution Logic**:
   - Supports suffix variants (e.g., `_cas` for casual)
   - Searches all configured roots
   - Tries original extension first, then other supported extensions
   - Supports category subdirectories

3. **Main Panel Portrait** (`_update_portrait`):
   - Uses `prefer_casual=False`
   - Shows default portrait only

4. **Detail Dialog Portrait** (`CharacterDetailDialog._load_portrait`):
   - Uses `prefer_casual=True`
   - Prefers `_cas` variant, falls back to default

5. **Supported Extensions**:
   - `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`

### Part D: Directory Structure ✅

Created directories:
- `mekhq_social_sim/images/portraits/` (with README)

Config file location:
- `mekhq_social_sim/config/portrait_config.json` (created on first use)

## Testing

### Unit Tests ✅
- Created `test_portrait_loading.py` with tests for:
  - Base name and extension extraction
  - PortraitConfig initialization
  - Search paths logic
  - Save/load configuration
  - Character portrait integration

### Test Results
- **66 tests total** (60 existing + 6 new)
- **All tests pass** ✅
- 4 tests skipped (tkinter-dependent, expected in CI)

## Regression Verification

All existing functionality preserved:
- ✅ Import Personnel JSON (now via menu)
- ✅ Import TO&E JSON (now via menu)
- ✅ Tree grouping/selection
- ✅ Character details panel
- ✅ Portrait rendering (enhanced with variants)
- ✅ Manual & random interaction rolls
- ✅ Log popup
- ✅ Event tab behavior
- ✅ All existing tests pass

## Usage Examples

### Setting External Portrait Folder
1. Open app
2. Click `File` → `Import` → `Set External Portrait Folder...`
3. Select folder containing MekHQ portraits
4. Portraits will now be found in both module and external folders

### Portrait Naming
- Default: `MW_F_4.png`
- Casual variant: `MW_F_4_cas.png`

The main panel shows the default, the detail dialog (right-click) shows casual if available.

### Portrait Organization
Portraits can be in:
- Root: `images/portraits/MW_F_4.png`
- Category: `images/portraits/Male/MW_F_4.png`

Both work, category is read from character's portrait metadata.

## Code Quality

- Minimal changes to existing code
- Backward compatible (existing behavior preserved)
- Robust error handling (graceful degradation)
- PIL-optional (works without PIL, shows fallback text)
- Config file optional (works without config file)
- Clean separation of concerns (PortraitConfig class)

## Files Modified

1. `mekhq_social_sim/src/gui.py` (main changes)
   - Added imports: `json`
   - Added classes: `PortraitConfig`
   - Added methods: `_build_menu_bar()`, `_set_external_portrait_folder()`
   - Updated methods: `_build_main_tab()`, `_update_portrait()`, `CharacterDetailDialog._load_portrait()`
   - Updated class: `PortraitHelper` (variant resolution)

## Files Created

1. `mekhq_social_sim/images/portraits/README.md` (documentation)
2. `mekhq_social_sim/tests/test_portrait_loading.py` (tests)

## Configuration File Format

`mekhq_social_sim/config/portrait_config.json`:
```json
{
  "external_portrait_root": "/path/to/external/portraits"
}
```

Created automatically when user sets external portrait folder.
