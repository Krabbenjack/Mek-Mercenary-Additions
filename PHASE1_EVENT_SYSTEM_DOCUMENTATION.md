# Phase 1 Event Mechanics System - Documentation

## Overview

Phase 1 implements a fully functional, headless event mechanics system that:
- Injects events based on context
- Selects participants
- Selects interactions with environmental/tonal modifiers
- Resolves interactions via existing skill checks
- Applies outcomes to persistent character/relationship axes
- **Runs completely without UI** - all modules are UI-independent

## Architecture

The system follows a strict **layered architecture** as defined in `docs/EVENT_SYSTEM.md`:

```
┌─────────────────────────────────────────────┐
│           Axis Registry (Core)              │
│  Persistent state for all axes              │
│  - Friendship, Respect, Romance             │
│  - Confidence, Reputation                   │
└─────────────────────────────────────────────┘
                    ▲
                    │ (state changes only)
                    │
┌─────────────────────────────────────────────┐
│      Layer 4: Outcome Applier               │
│  Applies declared effects only              │
│  - axis_delta, set_flags, emit_triggers     │
│  - xp, fatigue, confidence, reputation      │
└─────────────────────────────────────────────┘
                    ▲
┌─────────────────────────────────────────────┐
│      Layer 3: Interaction Resolver          │
│  Mechanical resolution via skill checks     │
│  Uses existing rules/skill_roll.py          │
│  Produces: ResolutionResult                 │
└─────────────────────────────────────────────┘
                    ▲
┌─────────────────────────────────────────────┐
│      Layer 2: Interaction Selector          │
│  Selects interactions with modifiers        │
│  - Environment weights                      │
│  - Tone weights                             │
│  Produces: SelectedInteraction              │
└─────────────────────────────────────────────┘
                    ▲
┌─────────────────────────────────────────────┐
│      Layer 1: Event Injector                │
│  Selects events and participants            │
│  Produces: EventInstance                    │
└─────────────────────────────────────────────┘
```

## Components

### Core: Axis Registry (`events/axis_system.py`)

**Purpose:** Central registry for all character and relationship axes.

**Features:**
- Loads axis definitions from `config/relations/relationship_axes_rules.json`
- Manages per-character axes: confidence, reputation
- Manages per-relationship axes: friendship, respect, romance
- Automatic value clamping to defined ranges
- State persistence (save/load to JSON)
- No UI coupling, no hardcoded behavior

**Usage:**
```python
from events import AxisRegistry

registry = AxisRegistry()

# Get/modify relationship axis
registry.modify_relationship_axis('char1', 'char2', 'friendship', +5)
value = registry.get_relationship_axis('char1', 'char2', 'friendship').value

# Get/modify character axis
registry.modify_character_axis('char1', 'confidence', +10)
value = registry.get_character_axis('char1', 'confidence').value

# Persistence
registry.save_to_file(Path('state.json'))
registry.load_from_file(Path('state.json'))
```

### Layer 1: Event Injector (`events/injector.py`)

**Purpose:** Selects events and participants based on availability rules.

**Loads:**
- `config/events/eventlist.json` - Event catalog
- `config/events/injector_rules/injector_selection_rules_*.json` - Selection rules
- `config/events/meta/age_groups.json` - Age filtering

**Features:**
- Availability checking
- Primary participant selection (single, pair, multiple)
- Derived participant selection
- Age-based filtering

**Does NOT:**
- Perform skill checks
- Apply outcomes
- Change state

**Usage:**
```python
from events import EventInjector

injector = EventInjector()

# Get available events
available = injector.get_available_events(characters)

# Inject specific event
event_instance = injector.inject_event(event_id=3001, characters=characters)
```

### Layer 2: Interaction Selector (`events/interaction_selector.py`)

**Purpose:** Selects interactions with context-based modifiers.

**Loads:**
- `config/events/context/interactions_social.json`
- `config/events/context/interactions_operational.json`
- `config/events/context/event_environment_list.json`
- `config/events/context/interactions_Tones.json`

**Features:**
- Domain filtering (social/operational)
- Environment modifiers (weight, difficulty, outcome scaling)
- Tone modifiers (weight, difficulty, escalation)
- Weighted random selection

**Does NOT:**
- Perform mechanical resolution
- Apply outcomes

**Usage:**
```python
from events import InteractionSelector

selector = InteractionSelector()

# Select interaction
selected = selector.select_interaction(
    domain='social',
    participant_ids=['char1', 'char2'],
    environment='FOB',
    tone='informal'
)
```

### Layer 3: Interaction Resolver (`events/resolver.py`)

**Purpose:** Executes mechanical resolution using skill checks.

**Loads:**
- `config/events/resolution/interaction_resolution_social.json`
- `config/events/resolution/interaction_resolution_operational.json`

**Uses:**
- `rules/skill_roll.py` - Existing A Time of War skill check system

**Features:**
- Stage-based resolution
- Skill checks with attribute fallbacks
- Margin of success tracking
- Fumble and stunning success detection

**Does NOT:**
- Apply outcomes
- Change state

**Usage:**
```python
from events import InteractionResolver

resolver = InteractionResolver()

# Resolve interaction
resolution_result = resolver.resolve_interaction(
    selected_interaction,
    characters
)

# Check outcome
if resolution_result.overall_success:
    tier = resolution_result.get_outcome_tier()  # "on_success", "on_great_success", or "on_failure"
```

### Layer 4: Outcome Applier (`events/outcome_applier.py`)

**Purpose:** Applies declared effects from outcome definitions.

**Loads:**
- `config/events/outcomes/social_outcomes.json`
- `config/events/outcomes/operational_outcomes.json`

**Features:**
- Applies **ONLY** declared effects:
  - `axis_delta` - Modifies relationship/character axes
  - `xp_delta` - Awards experience points (pooled)
  - `fatigue_delta` - Modifies fatigue
  - `confidence_delta` - Modifies confidence axis
  - `reputation_pool_delta` - Modifies reputation
  - `set_flags` - Sets flags on axes
  - `emit_triggers` - Emits triggers for later processing

**Does NOT:**
- Have knowledge of events
- Have knowledge of UI
- Have knowledge of interactions
- Infer or create effects not in config

**Usage:**
```python
from events import OutcomeApplier

applier = OutcomeApplier(axis_registry)

# Apply outcome based on resolution
applied = applier.apply_outcome(resolution_result, participants)

# Check what was applied
print(applied.effects_applied)
print(applied.triggers_emitted)
```

### Orchestrator (`events/orchestrator.py`)

**Purpose:** Ties all layers together for convenient execution.

**Features:**
- Single entry point for full event cycle
- Maintains strict layer separation
- State persistence helpers

**Usage:**
```python
from events import EventSystemOrchestrator

orchestrator = EventSystemOrchestrator()

# Run complete event cycle
results = orchestrator.run_event_cycle(
    event_id=3001,
    characters=characters,
    domain='social',
    environment='FOB',
    tone='informal'
)

# Run random event
results = orchestrator.inject_random_event(
    characters,
    domain='social',
    environment='SIMULATION',
    tone='cheerful'
)

# Access axis states
friendship = orchestrator.get_axis_state('char1', 'char2', 'friendship')
confidence = orchestrator.get_character_axis_state('char1', 'confidence')

# Persistence
orchestrator.save_state(Path('state.json'))
orchestrator.load_state(Path('state.json'))
```

## Running Tests

### Unit Tests
```bash
cd mekhq_social_sim
python tests/test_event_system_headless.py
```

All 19 tests should pass:
- ✅ Axis Registry operations
- ✅ Event injection
- ✅ Interaction selection
- ✅ Resolution mechanics
- ✅ Outcome application
- ✅ State persistence
- ✅ No UI dependencies

### Integration Test
```bash
cd mekhq_social_sim
python tests/integration_test_event_system.py
```

This runs a complete demonstration showing:
- Full event cycles
- Relationship tracking
- State persistence
- Layer separation

## Configuration Files

All configuration files are in `mekhq_social_sim/config/events/`:

```
config/events/
├── eventlist.json                    # Event catalog
├── meta/
│   └── age_groups.json              # Age group definitions
├── injector_rules/
│   ├── injector_selection_rules_social.json
│   ├── injector_selection_rules_training.json
│   ├── injector_selection_rules_administration.json
│   ├── injector_selection_rules_youth_social.json
│   └── injector_selection_rules_children_and_youth.json
├── context/
│   ├── interactions_social.json      # Social interaction definitions
│   ├── interactions_operational.json # Operational interaction definitions
│   ├── event_environment_list.json   # Environment modifiers
│   └── interactions_Tones.json       # Tone modifiers
├── resolution/
│   ├── interaction_resolution_social.json      # Social resolution rules
│   └── interaction_resolution_operational.json # Operational resolution rules
└── outcomes/
    ├── social_outcomes.json          # Social outcome effects
    └── operational_outcomes.json     # Operational outcome effects
```

## Design Principles

1. **Single Source of Truth:** All rules in JSON, no game logic in config
2. **Layered Architecture:** Each layer answers one question only, no shortcuts
3. **No UI Coupling:** All modules are UI-independent
4. **Declarative Effects:** Outcomes declare effects explicitly, no inference
5. **State Isolation:** Only Outcome Applier modifies state
6. **Existing Systems:** Uses existing skill check system, doesn't reinvent
7. **Deterministic:** Same inputs = same outputs (modulo randomness)
8. **Testable:** All components testable without UI

## Phase 2 Readiness

The system is designed to support Phase 2 (UI integration) without refactoring:

- ✅ All state is externalized (AxisRegistry)
- ✅ All modules are UI-independent
- ✅ State can be queried without side effects
- ✅ State changes are tracked and observable
- ✅ No assumptions about how results will be displayed

## Known Limitations

1. **Group Checks:** Currently uses first participant for resolution; full group mechanics to be implemented
2. **Opposed Checks:** Basic implementation; advanced opposition mechanics to be expanded
3. **Derived Participants:** Framework exists but logic needs expansion
4. **Trigger Processing:** Triggers are emitted but not yet processed (future feature)

## Next Steps (Phase 1.5+)

1. Expand group and opposed check mechanics
2. Implement trigger processing system
3. Add more sophisticated derived participant logic
4. Create UI integration layer (Phase 2)
5. Add event scheduling and time-based injection
6. Implement relationship state machine integration

## Verification

To verify Phase 1 is complete:

```bash
# Run all tests
cd mekhq_social_sim
python tests/test_event_system_headless.py   # Should pass 19/19
python tests/test_character_model.py          # Should pass 5/5 (existing)
python tests/test_extended_data_loading.py    # Should pass 2/2 (existing)

# Run integration test
python tests/integration_test_event_system.py  # Should complete successfully

# Verify no UI imports
grep -r "import tkinter" src/events/  # Should return nothing
grep -r "import gui" src/events/      # Should return nothing
```

✅ **Phase 1 is complete and ready for Phase 2.**
