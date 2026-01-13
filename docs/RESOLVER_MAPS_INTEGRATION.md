# Resolver Maps Integration - Complete Implementation

## Overview

This document describes the complete implementation of resolver maps integration into the Mek-Mercenary-Additions event system. The integration ensures that event participant selection never fails silently due to unknown DSL tokens, and all abstract role/filter/relationship tokens are resolved deterministically.

## Architecture

### Three-Layer Resolution System

```
┌─────────────────────────────────────────────────────────────┐
│                    Participant Selector                      │
│  (Orchestrates selection using both resolvers)              │
└───────────────┬─────────────────────────┬───────────────────┘
                │                         │
        ┌───────▼────────┐        ┌──────▼──────────┐
        │  Participant   │        │  Relationship   │
        │   Resolver     │        │    Resolver     │
        └───────┬────────┘        └──────┬──────────┘
                │                         │
        ┌───────▼─────────────────────────▼───────────┐
        │          Resolver Bundle                     │
        │  (Loads and caches all resolver maps)       │
        └──────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   ┌────▼────┐   ┌─────▼─────┐  ┌─────▼────────┐
   │Participant│  │Relationship│ │Age Groups   │
   │ Map       │  │  Map       │ │  JSON       │
   └───────────┘  └────────────┘ └──────────────┘
```

### File Structure

```
mekhq_social_sim/
├── config/events/meta/
│   ├── participant_resolution_map.json    # Role/filter/person_set definitions
│   ├── relationship_resolution_map.json   # Relationship DSL definitions
│   └── age_groups.json                    # Age group ranges
│
└── src/events/
    ├── resolver_bundle.py                 # Central loader for all maps
    ├── participant_resolver.py            # Role/filter/age resolution
    ├── relationship_resolver.py           # Relationship DSL resolution
    └── participant_selector.py            # Updated to use resolvers
```

## Components

### 1. ResolverBundle (`resolver_bundle.py`)

**Purpose**: Central access point for all resolver configurations.

**Key Features**:
- Loads all three resolver JSON files on initialization
- Implements include resolution for age_groups reference
- Provides type-safe accessor methods
- Singleton pattern for efficient reuse

**API**:
```python
bundle = get_resolver_bundle()

# Participant map accessors
roles = bundle.get_role_mapping("HR")  # ["ADMINISTRATOR_HR"]
filter_def = bundle.get_filter_definition("present")
age_group_def = bundle.get_age_group_definition("EARLY_TEEN")

# Relationship map accessors
predicate = bundle.get_pair_predicate("RELATIONSHIP_ACTIVE_WITH_EACH_OTHER")
derived = bundle.get_derived_relation("HR_REPRESENTATIVE")

# Policy accessors
policy = bundle.get_unknown_role_policy()  # "warn_and_fail"
```

### 2. ParticipantResolver (`participant_resolver.py`)

**Purpose**: Resolves participant selection constraints (roles, filters, age groups).

**Key Features**:
- Maps abstract roles to concrete profession values
- Evaluates filter predicates against character fields
- Checks age group membership
- Logs warnings for unknown tokens with event context

**API**:
```python
resolver = get_participant_resolver()

# Role resolution
concrete_roles = resolver.resolve_role("HR", event_id=2002)
matches = resolver.character_matches_role(character, "TECHNICIAN")
char_ids = resolver.filter_characters_by_role(characters, "MEKWARRIOR")

# Filter resolution
passes = resolver.apply_filter(character, "present", event_id=2001)
char_ids = resolver.filter_characters_by_filters(characters, ["present", "alive"])

# Age group resolution
group = resolver.get_character_age_group(character)  # "EARLY_TEEN"
in_group = resolver.character_in_age_group(character, "TEEN")
char_ids = resolver.filter_characters_by_age_group(characters, "LATE_TEEN")
```

### 3. RelationshipResolver (`relationship_resolver.py`)

**Purpose**: Resolves relationship DSL tokens (predicates, requirements, derived participants).

**Key Features**:
- Evaluates pair predicates (has_flag, not, and, or)
- Checks availability requirements (relationship_exists, authority_present)
- Resolves derived participants (role_group_pick, person_set, composite)
- Handles unsupported relations gracefully with logging

**API**:
```python
resolver = get_relationship_resolver()

# Pair predicate evaluation
satisfied = resolver.evaluate_pair_predicate(
    char_a_id, char_b_id, "RELATIONSHIP_ACTIVE_WITH_EACH_OTHER", event_id=3211
)

# Availability checks
has_rel = resolver.check_relationship_exists(characters, event_id=3221)
has_auth = resolver.check_authority_present(characters, event_id=3212)

# Derived participant resolution
derived_def = {"relation": "HR_REPRESENTATIVE"}
char_ids = resolver.resolve_derived_participant(
    derived_def, primary_char_id, characters, event_id=2002
)
```

### 4. ParticipantSelector (Updated)

**Purpose**: Orchestrates event participant selection using both resolvers.

**Key Changes**:
- Integrated ParticipantResolver for role/filter/age resolution
- Integrated RelationshipResolver for relationship constraints
- Added support for relationship_context in pair selection
- Added get_derived_participants() method for derived participant resolution
- Removed old _normalize_role() method (now handled by resolver)

**Enhanced API**:
```python
selector = get_participant_selector()

# Availability check (uses both resolvers)
available, errors = selector.check_availability(event_id, characters)

# Primary participant selection (uses participant resolver)
participants = selector.select_participants(event_id, characters)

# Derived participant selection (uses relationship resolver)
derived = selector.get_derived_participants(event_id, participants, characters)
```

## Resolution Flows

### Role Resolution Flow

```
Event Rule: { "role": "HR" }
    ↓
ParticipantResolver.resolve_role("HR")
    ↓
ResolverBundle.get_role_mapping("HR")
    ↓
participant_resolution_map.json: "HR": ["ADMINISTRATOR_HR"]
    ↓
Filter characters where profession == "ADMINISTRATOR_HR"
    ↓
Return: [char_id_1, char_id_2, ...]
```

### Filter Resolution Flow

```
Event Rule: { "filters": ["present"] }
    ↓
ParticipantResolver.apply_filter(character, "present")
    ↓
ResolverBundle.get_filter_definition("present")
    ↓
Definition: { "type": "status_in", "field": "status", "values": ["ACTIVE"] }
    ↓
Check: character.status in ["ACTIVE"]
    ↓
Return: True/False
```

### Relationship Predicate Flow

```
Event Rule: { "required_relation": "RELATIONSHIP_ACTIVE_WITH_EACH_OTHER" }
    ↓
RelationshipResolver.evaluate_pair_predicate(char_a, char_b, predicate)
    ↓
ResolverBundle.get_pair_predicate("RELATIONSHIP_ACTIVE_WITH_EACH_OTHER")
    ↓
Definition: { "type": "has_flag", "flag": "RELATIONSHIP_ACTIVE_WITH_EACH_OTHER" }
    ↓
RelationshipStateQuery.has_flag(char_a, char_b, flag)
    ↓
Return: True/False
```

## Non-Silent Failure Policy

### Implementation

All resolvers follow a strict **warn_and_fail** policy for unknown tokens:

1. **Unknown Token Detected** → Log warning with event context
2. **Return Safe Default** → Empty list / False (not crash)
3. **Propagate Failure** → Let availability check or selection fail deterministically

### Logging Format

```
[PARTICIPANT_RESOLVER] Unknown role 'UNKNOWN_ROLE' for event 2002. 
Policy: warn_and_fail. No role mapping found in participant_resolution_map.

[RELATIONSHIP_RESOLVER] Unsupported derived relation 'SUPERVISOR_OF' for event 1006.
Reason: Requires org/hierarchy model. Training 1006 references this.
```

### Benefits

- **No Silent Failures**: Every unmapped token is logged
- **Clear Context**: Event ID and token name in every message
- **Predictable Behavior**: Always returns empty/False, never crashes
- **Easy Debugging**: Search logs for [PARTICIPANT_RESOLVER] or [RELATIONSHIP_RESOLVER]

## Supported DSL Features

### Participant Resolution

| Feature | Status | Example |
|---------|--------|---------|
| Abstract Roles | ✅ Full | `"role": "HR"` → `["ADMINISTRATOR_HR"]` |
| Role Exclusion | ✅ Full | `"exclude_roles": ["HR"]` |
| Status Filters | ✅ Full | `"filters": ["present"]` → `status == "ACTIVE"` |
| Filter Aliases | ✅ Full | `"alive"` → alias of `"present"` |
| Age Groups | ✅ Full | `"age_group": "EARLY_TEEN"` → age 10-13 |
| Person Sets | ✅ Full | `"any_person"` → filters: ["present"] |

### Relationship Resolution

| Feature | Status | Example |
|---------|--------|---------|
| has_flag | ✅ Full | Check for `RELATIONSHIP_ACTIVE_WITH_EACH_OTHER` |
| has_any_flag | ✅ Full | Check for multiple flags (OR logic) |
| not | ✅ Full | Negate predicate result |
| and | ✅ Full | Combine predicates (AND logic) |
| or | ✅ Full | Combine predicates (OR logic) |
| relationship_exists | ✅ Full | Check if any relationship record exists |
| authority_present | ✅ Partial | Checks family/guardian/mentor roles |
| role_group_pick | ✅ Full | `HR_REPRESENTATIVE` → pick HR role |
| person_set | ✅ Full | `ALL_PRESENT_PERSONS` → delegate to participant resolver |
| composite_first_supported | ✅ Partial | Try multiple relation types in order |

### Unsupported (Logged Gracefully)

| Feature | Status | Reason |
|---------|--------|--------|
| SUPERVISOR_OF | ⚠️ Unsupported | Requires org/hierarchy model |
| UNIT_OF | ⚠️ Unsupported | Requires unit membership graph |
| COMMAND_SUPERVISOR_OF | ⚠️ Unsupported | Requires org/hierarchy model |
| org_supervisor_of_primary | ⚠️ Unsupported | Requires org/hierarchy model |

## Testing Results

### Unit Tests (Automated)

```bash
# Run from project root
cd mekhq_social_sim/src
python3 test_resolver_integration.py
```

**Results**: ALL TESTS PASSED ✅

- ✅ Event 2001 (Personnel Meeting): 6 participants selected
- ✅ Event 2002 (HR Intervention): HR detection + derived participant
- ✅ Event 1001 (Mech Simulator Training): 4 MekWarriors selected
- ✅ Event 3201 (Youth): Age group filtering working
- ✅ Event 3221 (Relationship): Requirement checking working
- ✅ Unknown token handling: All warnings logged

### Regression Tests

```bash
# Run from project root
python3 -m unittest discover -s mekhq_social_sim/tests -p "test_*.py"
```

**Results**: 50+ tests passing, 0 failures ✅

## Integration Points

### How GUI Uses the System

```python
# In gui.py or event dialogs
from events.participant_selector import get_participant_selector

selector = get_participant_selector()

# Check if event can run
available, errors = selector.check_availability(event_id, characters)
if not available:
    show_error_dialog(errors)
    return

# Select participants
primary = selector.select_participants(event_id, characters)
derived = selector.get_derived_participants(event_id, primary, characters)

# Execute event with primary + derived participants
all_participants = primary + derived
execute_event(event_id, all_participants)
```

### Adding New Events

1. **Add injector rule** to `config/events/injector_rules/*.json`
2. **Use abstract roles** from `participant_resolution_map.json`
3. **Use filters** like "present" and "alive"
4. **Use age groups** from `age_groups.json`
5. **Use relationship predicates** from `relationship_resolution_map.json`
6. **Test availability** with `check_availability()`
7. **Test selection** with `select_participants()` and `get_derived_participants()`

### Adding New Roles/Filters

1. **Update** `config/events/meta/participant_resolution_map.json`
2. **Add mapping** to roles or filters section
3. **Restart application** (resolver loads on init)
4. **Verify** with test script

## Best Practices

### For Event Designers

1. ✅ **DO** use abstract roles (HR, TECHNICIAN) instead of concrete ones
2. ✅ **DO** use "present" filter for standard availability checks
3. ✅ **DO** use age_groups.json names for youth events
4. ✅ **DO** test events with check_availability() before finalizing
5. ❌ **DON'T** invent new role names without adding to resolver map
6. ❌ **DON'T** use concrete profession values in rules
7. ❌ **DON'T** duplicate age group definitions

### For Developers

1. ✅ **DO** check logs for [PARTICIPANT_RESOLVER] / [RELATIONSHIP_RESOLVER] warnings
2. ✅ **DO** add new abstract roles to participant map before using
3. ✅ **DO** mark unsupported features with "unsupported" type in maps
4. ✅ **DO** provide clear "reason" field for unsupported features
5. ❌ **DON'T** silently ignore unknown tokens
6. ❌ **DON'T** throw exceptions for unknown tokens (log and return empty)
7. ❌ **DON'T** bypass resolvers for new event types

## Future Enhancements

### Phase 2 Candidates

- [ ] Unit membership graph (for UNIT_OF derived relation)
- [ ] Org hierarchy model (for SUPERVISOR_OF / COMMAND_SUPERVISOR_OF)
- [ ] More sophisticated pair selection (e.g., romantic compatibility scoring)
- [ ] Advanced age group queries (age ranges, multiple groups)

### Nice-to-Have

- [ ] Resolver map hot-reload (without restarting application)
- [ ] Resolver map validation tool (check for inconsistencies)
- [ ] Performance optimization (caching resolved results per event)
- [ ] Debug mode with verbose logging

## Troubleshooting

### Problem: Event not available when it should be

**Solution**: Check logs for [PARTICIPANT_RESOLVER] warnings. Likely cause: unmapped role or filter.

### Problem: No participants selected

**Solution**: Verify that:
1. Characters have `status == "ACTIVE"` (for "present" filter)
2. Characters have matching `profession` values
3. Age group definitions match character ages

### Problem: Derived participants empty

**Solution**: Check logs for [RELATIONSHIP_RESOLVER] warnings. If relation is "unsupported", feature not yet implemented.

### Problem: Unknown token not logging

**Solution**: Verify:
1. Event ID is passed to resolver methods
2. Python logging is configured (use `logging.basicConfig(level=logging.WARNING)`)

## Conclusion

The resolver maps integration provides a robust, extensible, and fail-safe system for event participant selection. All abstract tokens are resolved deterministically, and unknown tokens never cause silent failures. The system is ready for production use and future expansion.

## Contact

For questions or issues with the resolver system:
- Check logs first ([PARTICIPANT_RESOLVER] / [RELATIONSHIP_RESOLVER] messages)
- Review this document
- Examine the resolver JSON files in `config/events/meta/`
- Run the test script to verify your setup
