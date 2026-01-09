# Phase 2 Integration Guide

## Overview

Phase 2 has implemented the Event ↔ Relationship Integration layer, allowing events and interactions to communicate with the relationship system through explicit triggers, and enabling relationship state queries for interaction gating and weighting.

## Architecture Components

### 1. Trigger Intake Adapter (`relationship_trigger_intake.py`)
- **Role**: Validates and forwards triggers from external systems
- **Location**: `mekhq_social_sim/src/relationship_trigger_intake.py`
- **Key Classes**: `TriggerIntakeAdapter`, `TriggerValidationError`
- **Tests**: `mekhq_social_sim/tests/test_trigger_intake.py` (19 tests)

### 2. Relationship Engine (`relationship_engine.py`)
- **Role**: MASTER of relationship state, processes triggers and applies rules
- **Location**: `mekhq_social_sim/src/relationship_engine.py`
- **Key Classes**: `RelationshipEngine`, `RelationshipState`
- **Tests**: `mekhq_social_sim/tests/test_relationship_engine.py` (21 tests)

### 3. State Query Interface (`relationship_state_query.py`)
- **Role**: Provides READ-ONLY access to relationship state for event system
- **Location**: `mekhq_social_sim/src/relationship_state_query.py`
- **Key Classes**: `RelationshipStateQuery`
- **Tests**: `mekhq_social_sim/tests/test_state_query.py` (31 tests)

### 4. Integration Tests
- **Location**: `mekhq_social_sim/tests/test_trigger_integration.py` (10 tests)
- **Purpose**: Verifies trigger flow from intake → engine → state update

## Data Flow

### Forward Flow: Event System → Relationship System

```
Event/Interaction System
    ↓ (emits trigger)
Trigger Intake Adapter
    ↓ (validates)
Relationship Engine
    ↓ (processes trigger)
Relationship State
    ↓ (updates axes, sentiments, flags)
```

### Backward Flow: Relationship System → Event System (Read-Only)

```
Event System
    ↓ (queries state)
State Query Interface
    ↓ (reads)
Relationship Engine
    ↓ (provides state)
Relationship State
```

## How to Emit Triggers

### Basic Pattern

```python
from relationship_trigger_intake import get_trigger_intake

# Get the global intake adapter
intake = get_trigger_intake()

# Emit a trigger with payload
payload = {
    "initiator": "char_001",
    "target": "char_002",
    "context": "casual_flirt"
}

try:
    intake.emit_trigger("ROMANTIC_REJECTION", payload, "interaction_engine")
except TriggerValidationError as e:
    print(f"Trigger validation failed: {e}")
```

### Available Triggers

From `relationship_triggers.json`:

1. **TIME_SKIP** - Campaign time advances
   - Source: `campaign_time_system`
   - Payload: `{"days_skipped": integer}`

2. **LONG_SEPARATION** - Characters separated for prolonged period
   - Source: `relationship_context_evaluator`
   - Payload: `{"days_without_interaction": integer}`

3. **ROMANTIC_REJECTION** - Romantic interaction explicitly rejected
   - Source: `relationship_acceptance_engine`, `interaction_engine`
   - Payload: `{"initiator": character_id, "target": character_id, "context": string}`

4. **ROMANTIC_ACCEPTANCE** - Romantic interaction explicitly accepted
   - Source: `relationship_acceptance_engine`, `interaction_engine`
   - Payload: `{"initiator": character_id, "target": character_id, "context": string}`

5. **APOLOGY_ACCEPTED** - Apology was accepted
   - Source: `scripted_event`, `interaction_engine`
   - Payload: `{"initiator": character_id, "target": character_id}`

6. **BETRAYAL_EVENT** - Severe trust violation
   - Source: `scripted_event`
   - Payload: `{"initiator": character_id, "target": character_id, "severity": integer}`

7. **HEROIC_ACTION** - Heroic action observed by others
   - Source: `mission_event`
   - Payload: `{"actor": character_id, "witnesses": [character_id, ...]}`

## How to Query Relationship State

### Basic Queries

```python
from relationship_state_query import get_state_query

# Get the global query interface
query = get_state_query()

# Check axis values
friendship = query.get_axis_value("char_001", "char_002", "friendship")
romance = query.get_axis_value("char_001", "char_002", "romance")

# Check flags
has_conflict = query.has_flag("char_001", "char_002", "CONFLICT_ACTIVE")

# Check sentiments
is_hurt = query.has_sentiment("char_001", "char_002", "HURT")
hurt_strength = query.get_sentiment_strength("char_001", "char_002", "HURT")
```

### Interaction Gating

```python
# Should romantic interaction be suppressed?
if query.should_suppress_romantic_interaction(actor_id, partner_id):
    # Skip romantic interactions
    pass

# Is relationship in an awkward state?
if query.is_relationship_awkward(actor_id, partner_id):
    # Adjust interaction selection
    pass
```

### Interaction Weighting

```python
# Get weight modifier for interaction type
romantic_weight = query.get_interaction_weight_modifier(
    actor_id, 
    partner_id, 
    "romantic"
)

# Apply to base weight
adjusted_weight = base_weight * romantic_weight

# Get bonding weight modifier
bonding_weight = query.get_bonding_weight_modifier(actor_id, partner_id)
```

### Bulk Queries

```python
# Get full relationship summary
summary = query.get_relationship_summary("char_001", "char_002")
# Returns: {
#     "axes": {"friendship": 30, "romance": 10, "respect": 5},
#     "sentiments": {"HURT": 2},
#     "flags": ["JEALOUS"],
#     "roles": ["colleague"],
#     "is_awkward": True,
#     "suppress_romantic": False,
#     "suppress_friendly": False
# }

# Get all relationships for a character
all_rels = query.get_all_relationships_for_character("char_001")
```

## Integration Example: Updating Existing Interaction System

Here's how the existing `roll_engine.py` could be updated to emit triggers:

```python
# In _perform_interaction_roll function, after friendship update:

def _perform_interaction_roll(
    actor: Character,
    partner: Character,
    total_mod: int,
    breakdown: Dict[str, str]
) -> InteractionResult:
    # ... existing code ...
    
    # NEW: Emit triggers based on interaction outcome
    try:
        from relationship_trigger_intake import get_trigger_intake
        intake = get_trigger_intake()
        
        # Example: If this was a romantic interaction that failed badly
        if is_romantic_interaction and roll <= (target - 4):
            payload = {
                "initiator": actor.id,
                "target": partner.id,
                "context": "interaction_failure"
            }
            intake.emit_trigger("ROMANTIC_REJECTION", payload, "interaction_engine")
        
        # Example: If this was a successful bonding interaction
        if success and interaction_type == "bonding":
            # Could emit a positive trigger here
            pass
    
    except Exception as e:
        # Log but don't break interaction flow
        print(f"[WARNING] Failed to emit trigger: {e}")
    
    return InteractionResult(...)
```

## Integration Example: Using State Queries for Gating

Here's how to add relationship state queries to partner selection:

```python
# In _pick_partner_weighted function:

def _pick_partner_weighted(
    actor: Character, partners: List[Character]
) -> tuple[Character, int, Dict[str, str]]:
    from relationship_state_query import get_state_query
    query = get_state_query()
    
    weights: List[float] = []
    mods: List[int] = []
    breakdowns: List[Dict[str, str]] = []

    for p in partners:
        mod, breakdown = combined_social_modifier(actor, p)
        weight = max(1.0, 10.0 + float(mod))
        
        # NEW: Apply relationship state modifiers
        try:
            # Get interaction weight modifier
            rel_modifier = query.get_interaction_weight_modifier(
                actor.id, 
                p.id, 
                "friendly"  # or determine type based on context
            )
            weight *= rel_modifier
        except Exception as e:
            print(f"[WARNING] Failed to query relationship state: {e}")
        
        weights.append(weight)
        mods.append(mod)
        breakdowns.append(breakdown)

    # ... rest of function ...
```

## Design Principles (CRITICAL)

### ✅ Allowed
- Event system emits explicit triggers
- Relationship system processes triggers
- Event system queries relationship state (read-only)
- Triggers flow through intake adapter

### ❌ Forbidden
- Event system modifying relationship axes directly
- Event system implementing acceptance logic
- Relationship system selecting or weighting events
- Implicit trigger inference
- UI performing relationship logic
- Systems depending on each other's internals

### 🔑 Key Rules
- Systems may **influence** each other
- Systems must **never control** each other
- Influence flows only through:
  - Explicit triggers
  - Declarative rules (JSON)
  - Read-only state access

## Testing Your Integration

### Unit Tests
```bash
# Test trigger intake
python -m unittest mekhq_social_sim.tests.test_trigger_intake

# Test relationship engine
python -m unittest mekhq_social_sim.tests.test_relationship_engine

# Test state queries
python -m unittest mekhq_social_sim.tests.test_state_query

# Test integration
python -m unittest mekhq_social_sim.tests.test_trigger_integration
```

### Full Test Suite
```bash
# Run all tests (should remain passing)
python -m unittest discover -s mekhq_social_sim/tests -p "test_*.py"
```

### Manual Testing
1. Initialize systems:
   ```python
   from relationship_trigger_intake import initialize_trigger_intake
   from relationship_engine import initialize_relationship_engine
   from relationship_state_query import initialize_state_query
   
   intake = initialize_trigger_intake()
   engine = initialize_relationship_engine()
   query = initialize_state_query(engine)
   
   # Wire intake to engine
   intake.register_handler(engine.process_trigger)
   ```

2. Emit test triggers:
   ```python
   intake.emit_trigger(
       "ROMANTIC_ACCEPTANCE",
       {"initiator": "test_001", "target": "test_002", "context": "test"},
       "interaction_engine"
   )
   ```

3. Query state:
   ```python
   romance = query.get_axis_value("test_001", "test_002", "romance")
   print(f"Romance axis: {romance}")
   ```

## Rollback Safety

Each commit in this phase is independently reversible:

1. Commit 1: Trigger intake adapter (self-contained)
2. Commit 2: Relationship engine core (self-contained)
3. Commit 3: State query interface (self-contained)

You can revert to any commit and the system remains functional.

## Next Steps (Future Work)

1. **Update Interaction System**
   - Add trigger emission to `roll_engine.py`
   - Add state queries to partner selection
   - Update interaction outcomes to emit appropriate triggers

2. **Update Calendar System**
   - Emit TIME_SKIP triggers on day advance
   - Track interaction timestamps

3. **UI Updates** (optional, presentation only)
   - Display new relationship state data
   - Show sentiments, flags in relationship detail dialog
   - Maintain read-only enforcement

4. **Event System Integration**
   - Wire event outcomes to trigger emission
   - Use state queries for event selection

## Support & Questions

For questions or issues with Phase 2 integration:
- Review trigger registry: `config/relations/relationship_triggers.json`
- Check test files for usage examples
- All integration is incremental and reversible
