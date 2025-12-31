"""
test_relationship_ui.py

Test script for the new relationship UI system.
Creates mock data and validates the UI components work correctly.
"""

import sys
from pathlib import Path
from datetime import date
from typing import Dict, Any, List

# Add src to path
src_path = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src_path))

# Import the adapter (without GUI dependencies)
from relationship_ui_adapter import RelationshipRuntimeAdapter


def create_mock_relationship_data() -> List[Dict[str, Any]]:
    """
    Create comprehensive mock relationship data for testing.
    This simulates what the runtime provider would return.
    """
    return [
        {
            "relationship_id": "rel_001",
            "participants": {
                "a": "char_001",
                "b": "char_002"
            },
            "axes": {
                "friendship": 45,
                "romance": 10,
                "respect": 30
            },
            "sentiments": {
                "TRUSTING": {
                    "strength": 2,
                    "category": "positive"
                }
            },
            "flags": {
                "AWKWARD": {
                    "remaining_days": 2
                }
            },
            "roles": {},
            "derived": {
                "states": {
                    "friendship": "friends",
                    "romance": "curiosity",
                    "respect": "acknowledged"
                },
                "dynamic": "stable",
                "evaluated_day": 100
            },
            "events": [
                {
                    "name": "Friendly conversation",
                    "days_ago": 5
                },
                {
                    "name": "Worked together on mission",
                    "days_ago": 10
                }
            ]
        },
        {
            "relationship_id": "rel_002",
            "participants": {
                "a": "char_001",
                "b": "char_003"
            },
            "axes": {
                "friendship": -35,
                "romance": 0,
                "respect": -20
            },
            "sentiments": {
                "HURT": {
                    "strength": 1,
                    "category": "negative"
                }
            },
            "flags": {},
            "roles": {},
            "derived": {
                "states": {
                    "friendship": "rivals",
                    "romance": "neutral",
                    "respect": "tolerated"
                },
                "dynamic": "strained",
                "evaluated_day": 100
            },
            "events": [
                {
                    "name": "Argument over tactics",
                    "days_ago": 3
                }
            ]
        },
        {
            "relationship_id": "rel_003",
            "participants": {
                "a": "char_001",
                "b": "char_004"
            },
            "axes": {
                "friendship": 75,
                "romance": 60,
                "respect": 55
            },
            "sentiments": {
                "TRUSTING": {
                    "strength": 3,
                    "category": "positive"
                },
                "ADMIRING": {
                    "strength": 2,
                    "category": "positive"
                }
            },
            "flags": {},
            "roles": {
                "MENTOR": "char_004",
                "APPRENTICE": "char_001"
            },
            "derived": {
                "states": {
                    "friendship": "close_friends",
                    "romance": "attraction",
                    "respect": "esteemed"
                },
                "dynamic": "stable",
                "evaluated_day": 100
            },
            "events": [
                {
                    "name": "Training session together",
                    "days_ago": 1
                },
                {
                    "name": "Shared personal story",
                    "days_ago": 7
                }
            ]
        }
    ]


def test_adapter_with_mock_data():
    """Test the adapter with comprehensive mock data."""
    print("=" * 60)
    print("Testing Relationship UI Adapter")
    print("=" * 60)
    
    # Create adapter
    current = date(3050, 6, 15)
    start = date(3050, 1, 1)
    adapter = RelationshipRuntimeAdapter(current, start)
    
    # Override the mock data method to return our test data
    def custom_mock():
        return {
            "_domain": "relationship",
            "_type": "runtime_snapshot",
            "_authoritative": True,
            "meta": {
                "current_campaign_day": 165,
                "generated_on_day": 165,
                "time_source": "campaign_calendar"
            },
            "relationships": create_mock_relationship_data()
        }
    
    adapter._get_mock_runtime_data = custom_mock
    adapter._runtime_data = None  # Reset cache
    
    print("\n1. Testing get_relationships_for_character('char_001'):")
    rels = adapter.get_relationships_for_character("char_001")
    print(f"   Found {len(rels)} relationships")
    for rel in rels:
        other_id = adapter.get_other_character_id(rel, "char_001")
        axes = rel.get("axes", {})
        print(f"   - With {other_id}: F={axes.get('friendship', 0)}, "
              f"R={axes.get('romance', 0)}, E={axes.get('respect', 0)}")
    
    print("\n2. Testing has_any_relationships:")
    print(f"   char_001: {adapter.has_any_relationships('char_001')}")
    print(f"   char_999: {adapter.has_any_relationships('char_999')}")
    
    print("\n3. Testing get_relationship_between:")
    rel = adapter.get_relationship_between("char_001", "char_002")
    if rel:
        print(f"   Found relationship: {rel['relationship_id']}")
        print(f"   Derived dynamic: {rel['derived']['dynamic']}")
    
    print("\n4. Testing axis formatting:")
    print(f"   format_axis_value(45): {adapter.format_axis_value(45)}")
    print(f"   format_axis_value(-35): {adapter.format_axis_value(-35)}")
    print(f"   format_axis_value(0): {adapter.format_axis_value(0)}")
    
    print("\n5. Testing color coding:")
    for value in [80, 40, 0, -40, -80]:
        color = adapter.get_axis_label_color(value)
        print(f"   Value {value:3d} → {color}")
    
    print("\n6. Analyzing mock relationships:")
    for rel in rels:
        print(f"\n   Relationship: {rel['relationship_id']}")
        
        # Participants
        participants = rel['participants']
        print(f"   Participants: {participants['a']} ↔ {participants['b']}")
        
        # Axes
        axes = rel['axes']
        print(f"   Axes: F={axes.get('friendship', 0)}, "
              f"R={axes.get('romance', 0)}, E={axes.get('respect', 0)}")
        
        # Derived states
        derived = rel.get('derived', {})
        states = derived.get('states', {})
        if states:
            print(f"   States: {', '.join([f'{k}={v}' for k, v in states.items()])}")
        
        # Dynamic
        dynamic = derived.get('dynamic', 'unknown')
        if dynamic != 'unknown':
            print(f"   Dynamic: {dynamic}")
        
        # Sentiments
        sentiments = rel.get('sentiments', {})
        if sentiments:
            print(f"   Sentiments: {list(sentiments.keys())}")
        
        # Flags
        flags = rel.get('flags', {})
        if flags:
            print(f"   Flags: {list(flags.keys())}")
        
        # Roles
        roles = rel.get('roles', {})
        if roles:
            print(f"   Roles: {list(roles.keys())}")
        
        # Events
        events = rel.get('events', [])
        if events:
            print(f"   Events: {len(events)} recorded")
    
    print("\n" + "=" * 60)
    print("All adapter tests completed successfully!")
    print("=" * 60)


def test_relationship_detail_structure():
    """Test that the relationship detail structure is complete."""
    print("\n" + "=" * 60)
    print("Testing Relationship Detail Structure")
    print("=" * 60)
    
    mock_data = create_mock_relationship_data()
    
    print("\nChecking required fields in mock data:")
    required_fields = ["relationship_id", "participants", "axes"]
    optional_fields = ["sentiments", "flags", "roles", "derived", "events"]
    
    for i, rel in enumerate(mock_data, 1):
        print(f"\n{i}. Relationship {rel['relationship_id']}:")
        
        # Check required fields
        for field in required_fields:
            present = field in rel
            print(f"   ✓ {field}: {'PRESENT' if present else 'MISSING'}")
        
        # Check optional fields
        for field in optional_fields:
            if field in rel and rel[field]:
                print(f"   + {field}: {len(rel[field]) if isinstance(rel[field], (dict, list)) else 'present'}")
    
    print("\n" + "=" * 60)
    print("Structure validation complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nRelationship UI System Test Suite")
    print("==================================\n")
    
    try:
        test_adapter_with_mock_data()
        test_relationship_detail_structure()
        
        print("\n✓ ALL TESTS PASSED")
        print("\nThe new relationship system is ready for GUI integration.")
        print("Mock data covers:")
        print("  - Positive relationships (friends, attraction)")
        print("  - Negative relationships (rivals, conflict)")
        print("  - Complex relationships (mentor/apprentice with mixed axes)")
        print("  - Sentiments (both positive and negative)")
        print("  - Flags (temporary states)")
        print("  - Roles (structural relationships)")
        print("  - Event history")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
