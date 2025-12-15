# Campaign Metadata Import - Testing Guide

## Overview
This feature allows one-click import of campaign metadata (date and rank system) from MekHQ .cpnx files, with automatic resolution of numeric rank IDs to human-readable names.

## Files Modified
1. `mekhq_social_sim/src/mekhq_personnel_exporter.py` - Added campaign metadata extraction
2. `mekhq_social_sim/src/rank_resolver.py` - NEW: Rank name resolution system
3. `mekhq_social_sim/src/models.py` - Added `rank_name` field to Character
4. `mekhq_social_sim/src/data_loading.py` - Integrated rank resolution
5. `mekhq_social_sim/src/gui.py` - Added import menu and display updates
6. `README.md` - Updated documentation

## How to Test

### 1. Export Campaign Metadata
```bash
cd mekhq_social_sim/src
python mekhq_personnel_exporter.py "path/to/campaign.cpnx" -o ../exports
```

**Expected Result:**
- Three files created in `exports/`:
  - `personnel_complete.json`
  - `toe_complete.json`
  - `campaign_meta.json` (NEW)

**Verify campaign_meta.json contains:**
```json
{
  "campaign_date": "YYYY-MM-DD",
  "rank_system": "SLDF"
}
```

### 2. Test Rank Resolution (CLI)
```bash
cd mekhq_social_sim/src
python3 -c "
from rank_resolver import get_rank_resolver

resolver = get_rank_resolver()
resolver.set_rank_system('SLDF')

# Test various ranks
print('Rank 33 (Lieutenant):', resolver.resolve_rank_name(33))
print('Rank 34 (Captain):', resolver.resolve_rank_name(34))
print('Rank 21 (Warrant Officer):', resolver.resolve_rank_name(21))
"
```

**Expected Output:**
```
✅ Loaded 19 rank systems
✅ Active rank system set to: Star League Defense Force (SLDF)
Rank 33 (Lieutenant): Lieutenant
Rank 34 (Captain): Captain
Rank 21 (Warrant Officer): Warrant Officer
```

### 3. Test Personnel Loading with Rank Names
```bash
cd mekhq_social_sim/src
python3 -c "
from data_loading import load_campaign
from rank_resolver import get_rank_resolver

resolver = get_rank_resolver()
resolver.set_rank_system('SLDF')

chars = load_campaign('../exports/personnel_complete.json')
print(f'Loaded {len(chars)} characters')

# Show first 5 with ranks
for i, (cid, char) in enumerate(list(chars.items())[:5]):
    if char.rank:
        print(f'  {char.name}: rank_id={char.rank}, rank_name={char.rank_name}')
"
```

**Expected Output:**
- Characters load successfully
- Rank names are resolved (e.g., "Lieutenant" instead of "33")

### 4. Test GUI Integration (Requires Display)

**Step 1: Launch GUI**
```bash
cd mekhq_social_sim/src
python gui.py
```

**Step 2: Import Campaign Metadata**
1. Click **File → Import → Import Campaign Meta (Date & Rank System)**
2. Select your .cpnx or .cpnx.gz file
3. Observe success message with:
   - Campaign date loaded
   - Rank system loaded

**Expected Behavior:**
- Date field updates to campaign date
- Date field remains editable (you can still change it)
- If personnel already loaded, ranks update immediately

**Step 3: Import Personnel**
1. Click **File → Import → Import Personnel (JSON)**
2. Select `personnel_complete.json`

**Expected Behavior:**
- Characters load into tree view
- Rank names appear in character details (not numeric IDs)

**Step 4: Verify Rank Display**
1. Click on various characters in tree view
2. Check character details panel
3. Right-click character → view detail dialog

**Expected Display:**
```
Name: John Doe
Callsign: Bulldog
Rank: Lieutenant       ← Should show NAME, not "33"
Age: 32 (adult)
...
```

### 5. Test Fallback Behavior

**Test Unknown Rank System:**
- Import campaign with rank system not in config
- Expected: Shows "Rank 33 (UNKNOWN_SYSTEM)" or similar

**Test Missing Rank System:**
- Load personnel without setting rank system first
- Expected: Shows "Rank 33" or "No Rank"

**Test Invalid Rank ID:**
- Character with rank ID 999 (not in system)
- Expected: Shows "Unknown Rank 999 (SLDF)" or similar

## Regression Testing

### Must Not Break:
1. **Existing Personnel Import** - Works without campaign metadata
2. **TO&E Import** - Still functions correctly
3. **Portrait Display** - No changes to portrait handling
4. **Character Details** - All existing fields still visible
5. **Social Interactions** - Synergy engine unaffected
6. **Calendar System** - Event management unchanged
7. **Day Advancement** - Still works correctly

## Performance Benchmarks

### Expected Performance:
- Export campaign metadata: < 1 second
- Load 19 rank systems: < 0.1 second (one-time)
- Resolve 100 character ranks: < 0.01 second
- Total personnel load (100 chars): < 0.1 second

### Performance Test:
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

## Security Validation

✅ **CodeQL Check Passed**: No security alerts
✅ **No External Dependencies**: Uses only standard library + existing dependencies
✅ **Input Validation**: All XML/JSON parsing has error handling
✅ **No Code Execution**: Only data loading, no eval() or exec()

## Known Limitations

1. **Rank System Requirement**: Some campaigns may not have a rank system set
   - Fallback: Shows "Rank X" if system not available
   
2. **MekHQ 5.10 Only**: Only works with MekHQ 5.10+ campaign files
   - Earlier versions have different XML structure

3. **GUI Testing**: Requires X11/display environment
   - Syntax validation completed
   - Manual GUI testing required in appropriate environment

## Success Criteria

✅ All automated tests pass
✅ No security vulnerabilities
✅ Performance within acceptable ranges
✅ Documentation complete and accurate
✅ Code review feedback addressed
✅ Backwards compatibility maintained

**Status**: Ready for manual GUI testing in display environment
