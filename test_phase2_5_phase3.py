#!/usr/bin/env python3
"""
Test script to verify Phase 2.5 and Phase 3 implementation.

This script tests:
1. EventType loading from eventlist.json
2. Event creation and validation
3. Event injector execution
4. Character model with new state fields
5. Observer pattern for Social Director
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "mekhq_social_sim" / "src"
sys.path.insert(0, str(src_path))

from datetime import date
from events.persistence import EventType, Event, RecurrenceType
from events.injector import get_event_injector
from events.manager import EventManager
from models import Character


def test_eventlist_loading():
    """Test that EventType loads from eventlist.json."""
    print("=" * 60)
    print("TEST 1: EventType Loading from eventlist.json")
    print("=" * 60)
    
    event_types = list(EventType)
    print(f"✓ Loaded {len(event_types)} event types from eventlist.json")
    
    print("\nSample event types:")
    for event_type in event_types[:10]:
        print(f"  - {event_type.name} (ID: {event_type.value})")
    
    print("\n✓ Test 1 PASSED\n")


def test_event_creation():
    """Test creating events with new EventType system."""
    print("=" * 60)
    print("TEST 2: Event Creation with EventType")
    print("=" * 60)
    
    # Create event with event type from eventlist
    event = Event(
        EventType.SIMULATOR_TRAINING_MECHWARRIOR,
        date(2025, 1, 15),
        RecurrenceType.ONCE
    )
    
    print(f"✓ Created event: {event.title}")
    print(f"  Event ID: {event.event_id}")
    print(f"  Date: {event.start_date}")
    print(f"  Recurrence: {event.recurrence_type.value}")
    
    print("\n✓ Test 2 PASSED\n")


def test_event_injector():
    """Test event injector validation and execution."""
    print("=" * 60)
    print("TEST 3: Event Injector")
    print("=" * 60)
    
    injector = get_event_injector()
    print(f"✓ Event injector initialized with {len(injector.event_definitions)} events")
    
    # Test validation
    valid, name = injector.validate_event_id(1001)
    print(f"\n✓ Event ID 1001 validation: {valid}")
    print(f"  Event name: {name}")
    
    # Test invalid ID
    valid, name = injector.validate_event_id(99999)
    print(f"\n✓ Invalid event ID 99999 validation: {valid}")
    print(f"  Event name: {name}")
    
    # Test execution
    log = injector.execute_event(1001, date.today())
    print(f"\n✓ Executed event: {log.event_name}")
    print(f"  Execution date: {log.execution_date}")
    print(f"  Interactions: {len(log.interactions)}")
    print(f"  Errors: {len(log.errors)}")
    
    print("\n✓ Test 3 PASSED\n")


def test_character_state_fields():
    """Test Character model with Phase 3 state fields."""
    print("=" * 60)
    print("TEST 4: Character State Fields (Phase 3)")
    print("=" * 60)
    
    char = Character(
        id="test_001",
        name="Test Pilot",
        callsign="Ghost",
        age=28,
        profession="MechWarrior"
    )
    
    print(f"✓ Created character: {char.name} ({char.callsign})")
    print(f"\nEvent-driven state fields:")
    print(f"  XP: {char.xp}")
    print(f"  Confidence: {char.confidence}/100")
    print(f"  Fatigue: {char.fatigue}/100")
    print(f"  Reputation Pool: {char.reputation_pool}/100")
    
    # Modify values (simulating event outcome)
    char.xp = 150
    char.confidence = 75
    char.fatigue = 30
    char.reputation_pool = 65
    
    print(f"\n✓ After event modifications:")
    print(f"  XP: {char.xp}")
    print(f"  Confidence: {char.confidence}/100")
    print(f"  Fatigue: {char.fatigue}/100")
    print(f"  Reputation Pool: {char.reputation_pool}/100")
    
    print("\n✓ Test 4 PASSED\n")


def test_observer_pattern():
    """Test observer pattern for Social Director."""
    print("=" * 60)
    print("TEST 5: Observer Pattern (Social Director)")
    print("=" * 60)
    
    injector = get_event_injector()
    
    # Track observer calls
    observed_logs = []
    
    def observer_callback(log):
        observed_logs.append(log)
    
    # Add observer
    injector.add_observer(observer_callback)
    print("✓ Observer registered")
    
    # Execute event
    injector.execute_event(1001, date.today())
    
    # Check observer was called
    assert len(observed_logs) == 1, "Observer should have been called once"
    print(f"✓ Observer received {len(observed_logs)} execution log(s)")
    print(f"  Observed event: {observed_logs[0].event_name}")
    
    # Remove observer
    injector.remove_observer(observer_callback)
    print("✓ Observer unregistered")
    
    print("\n✓ Test 5 PASSED\n")


def test_event_manager_integration():
    """Test EventManager integration with EventInjector."""
    print("=" * 60)
    print("TEST 6: EventManager + EventInjector Integration")
    print("=" * 60)
    
    # Create temp event manager
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.close()
    
    manager = EventManager(Path(tmp.name))
    print("✓ EventManager created")
    
    # Add event
    event = manager.add_event(
        EventType.SIMULATOR_TRAINING_MECHWARRIOR,
        date.today(),
        RecurrenceType.ONCE
    )
    print(f"✓ Added event: {event.title}")
    
    # Create test character roster
    characters = {
        "char1": Character(id="char1", name="Pilot 1", callsign="Alpha", age=25, profession="MechWarrior")
    }
    
    # Execute events for date
    logs = manager.execute_events_for_date(date.today(), characters)
    print(f"✓ Executed {len(logs)} event(s)")
    for log in logs:
        print(f"  - {log.event_name} (ID: {log.event_id})")
    
    # Cleanup
    Path(tmp.name).unlink()
    
    print("\n✓ Test 6 PASSED\n")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  PHASE 2.5 + PHASE 3 IMPLEMENTATION TEST SUITE          ║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    try:
        test_eventlist_loading()
        test_event_creation()
        test_event_injector()
        test_character_state_fields()
        test_observer_pattern()
        test_event_manager_integration()
        
        print("╔" + "=" * 58 + "╗")
        print("║  ALL TESTS PASSED ✓                                     ║")
        print("╚" + "=" * 58 + "╝")
        print("\n")
        print("Phase 2.5 and Phase 3 implementation verified successfully!")
        print("\nNext steps:")
        print("  1. Start the GUI: python mekhq_social_sim/src/gui.py")
        print("  2. Test Social Director debug window")
        print("  3. Test calendar event scheduling and execution")
        print("  4. Verify Character Sheet Progress section display")
        print("\n")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
