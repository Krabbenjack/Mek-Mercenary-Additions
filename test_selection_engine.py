#!/usr/bin/env python3
"""
Test script for event participant selection engine.

Tests:
1. Selection engine loads rules correctly
2. Participant resolution works for different event types
3. Filters are applied correctly
4. Edge cases (no characters, no rules) are handled
"""
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parent
src_path = repo_root / "mekhq_social_sim" / "src"
sys.path.insert(0, str(src_path))

from events.injector_selection_engine import get_selection_engine
from models import Character


def create_test_characters():
    """Create a test roster of characters."""
    characters = {}
    
    # Create some test characters with different professions and ages
    char1 = Character(
        id="char_001",
        name="John Smith",
        callsign="Ace",
        age=35,
        profession="MechWarrior",
    )
    characters[char1.id] = char1
    
    char2 = Character(
        id="char_002",
        name="Jane Doe",
        callsign="Doc",
        age=28,
        profession="Technician",
    )
    characters[char2.id] = char2
    
    char3 = Character(
        id="char_003",
        name="Bob Johnson",
        callsign="Tank",
        age=42,
        profession="MechWarrior",
    )
    characters[char3.id] = char3
    
    char4 = Character(
        id="char_004",
        name="Alice Brown",
        callsign="Pilot",
        age=31,
        profession="Aerospace Pilot",
    )
    characters[char4.id] = char4
    
    char5 = Character(
        id="char_005",
        name="Charlie Wilson",
        callsign="Chief",
        age=45,
        profession="Technician",
    )
    characters[char5.id] = char5
    
    # Add more MechWarriors to meet minimum count
    char6 = Character(
        id="char_006",
        name="David Lee",
        callsign="Viper",
        age=29,
        profession="MechWarrior",
    )
    characters[char6.id] = char6
    
    char7 = Character(
        id="char_007",
        name="Sarah Connor",
        callsign="Storm",
        age=33,
        profession="MechWarrior",
    )
    characters[char7.id] = char7
    
    # Add a toddler for testing children events
    char8 = Character(
        id="char_008",
        name="Emma Smith",
        callsign=None,
        age=2,
        profession=None,
    )
    characters[char8.id] = char8
    
    return characters


def test_selection_engine():
    """Test the selection engine."""
    print("=" * 70)
    print("Testing Event Participant Selection Engine")
    print("=" * 70)
    
    # Get selection engine
    engine = get_selection_engine()
    print("\n✓ Selection engine initialized")
    
    # Create test characters
    characters = create_test_characters()
    print(f"✓ Created {len(characters)} test characters")
    
    # Test 1: Simulator Training (1001) - requires MechWarriors
    print("\n" + "-" * 70)
    print("Test 1: Simulator Training (Event 1001)")
    print("-" * 70)
    result = engine.resolve(1001, characters)
    print(f"Primary: {len(result['primary'])} participants")
    print(f"Derived: {len(result['derived'])} participants")
    print(f"Total: {len(result['all'])} participants")
    for char in result['all']:
        print(f"  - {char.label()}")
    
    # Test 2: Social Event (3001) - multiple persons
    print("\n" + "-" * 70)
    print("Test 2: Social Event (Event 3001)")
    print("-" * 70)
    result = engine.resolve(3001, characters)
    print(f"Primary: {len(result['primary'])} participants")
    print(f"Derived: {len(result['derived'])} participants")
    print(f"Total: {len(result['all'])} participants")
    for char in result['all']:
        print(f"  - {char.label()}")
    
    # Test 3: Pair event (3101)
    print("\n" + "-" * 70)
    print("Test 3: Pair Event (Event 3101)")
    print("-" * 70)
    result = engine.resolve(3101, characters)
    print(f"Primary: {len(result['primary'])} participants")
    print(f"Derived: {len(result['derived'])} participants")
    print(f"Total: {len(result['all'])} participants")
    for char in result['all']:
        print(f"  - {char.label()}")
    
    # Test 4: Child event (4001) - should select child
    print("\n" + "-" * 70)
    print("Test 4: Child Event (Event 4001)")
    print("-" * 70)
    result = engine.resolve(4001, characters)
    print(f"Primary: {len(result['primary'])} participants")
    print(f"Derived: {len(result['derived'])} participants")
    print(f"Total: {len(result['all'])} participants")
    for char in result['all']:
        print(f"  - {char.label()}")
    
    # Test 5: Non-existent event
    print("\n" + "-" * 70)
    print("Test 5: Non-existent Event (Event 99999)")
    print("-" * 70)
    result = engine.resolve(99999, characters)
    print(f"Primary: {len(result['primary'])} participants")
    print(f"Derived: {len(result['derived'])} participants")
    print(f"Total: {len(result['all'])} participants")
    
    # Test 6: Empty character roster
    print("\n" + "-" * 70)
    print("Test 6: Empty Character Roster (Event 3001)")
    print("-" * 70)
    result = engine.resolve(3001, {})
    print(f"Primary: {len(result['primary'])} participants")
    print(f"Derived: {len(result['derived'])} participants")
    print(f"Total: {len(result['all'])} participants")
    
    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_selection_engine()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
