"""
Tests for Relationship Engine Core

Verifies that the relationship engine correctly processes triggers and applies
relationship rules to update axes, sentiments, and flags.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from relationship_engine import (
    RelationshipEngine,
    RelationshipState,
    get_relationship_engine,
    initialize_relationship_engine
)


class TestRelationshipState(unittest.TestCase):
    """Test suite for RelationshipState."""
    
    def test_create_relationship_state(self):
        """Test creating a relationship state."""
        rel = RelationshipState("char_001", "char_002")
        
        self.assertEqual(rel.participants, ("char_001", "char_002"))
        self.assertEqual(rel.get_axis("friendship"), 0)
        self.assertEqual(rel.get_axis("respect"), 0)
        self.assertEqual(rel.get_axis("romance"), 0)
    
    def test_canonical_participant_ordering(self):
        """Test that participant IDs are canonically ordered."""
        rel1 = RelationshipState("char_002", "char_001")
        rel2 = RelationshipState("char_001", "char_002")
        
        self.assertEqual(rel1.participants, rel2.participants)
        self.assertEqual(rel1.relationship_id, rel2.relationship_id)
    
    def test_modify_axis(self):
        """Test modifying an axis value."""
        rel = RelationshipState("char_001", "char_002")
        
        rel.modify_axis("friendship", 10)
        self.assertEqual(rel.get_axis("friendship"), 10)
        
        rel.modify_axis("friendship", 5)
        self.assertEqual(rel.get_axis("friendship"), 15)
        
        rel.modify_axis("friendship", -20)
        self.assertEqual(rel.get_axis("friendship"), -5)
    
    def test_axis_bounds_clamping(self):
        """Test that axis values are clamped to valid bounds."""
        rel = RelationshipState("char_001", "char_002")
        
        # Test upper bound
        rel.set_axis("friendship", 150)
        self.assertEqual(rel.get_axis("friendship"), 100)
        
        # Test lower bound
        rel.set_axis("friendship", -150)
        self.assertEqual(rel.get_axis("friendship"), -100)
    
    def test_sentiment_management(self):
        """Test sentiment setting and retrieval."""
        rel = RelationshipState("char_001", "char_002")
        
        self.assertFalse(rel.has_sentiment("HURT"))
        self.assertEqual(rel.get_sentiment_strength("HURT"), 0)
        
        rel.set_sentiment("HURT", 3)
        self.assertTrue(rel.has_sentiment("HURT"))
        self.assertEqual(rel.get_sentiment_strength("HURT"), 3)
        
        rel.modify_sentiment("HURT", -1)
        self.assertEqual(rel.get_sentiment_strength("HURT"), 2)
        
        # Setting to 0 removes the sentiment
        rel.set_sentiment("HURT", 0)
        self.assertFalse(rel.has_sentiment("HURT"))
    
    def test_flag_management(self):
        """Test flag setting and removal."""
        rel = RelationshipState("char_001", "char_002")
        
        self.assertFalse(rel.has_flag("CONFLICT_ACTIVE"))
        
        rel.set_flag("CONFLICT_ACTIVE")
        self.assertTrue(rel.has_flag("CONFLICT_ACTIVE"))
        
        rel.remove_flag("CONFLICT_ACTIVE")
        self.assertFalse(rel.has_flag("CONFLICT_ACTIVE"))
    
    def test_flag_with_expiry(self):
        """Test flag with expiry day."""
        rel = RelationshipState("char_001", "char_002")
        
        rel.set_flag("JEALOUS", 100)
        self.assertTrue(rel.has_flag("JEALOUS"))
        self.assertEqual(rel.flags["JEALOUS"], 100)
    
    def test_role_management(self):
        """Test role assignment and removal."""
        rel = RelationshipState("char_001", "char_002")
        
        self.assertFalse(rel.has_role("family"))
        
        rel.add_role("family")
        self.assertTrue(rel.has_role("family"))
        
        rel.remove_role("family")
        self.assertFalse(rel.has_role("family"))
    
    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        rel = RelationshipState("char_001", "char_002")
        rel.modify_axis("friendship", 20)
        rel.set_sentiment("HURT", 2)
        rel.set_flag("CONFLICT_ACTIVE")
        rel.add_role("colleague")
        
        data = rel.to_dict()
        
        self.assertEqual(data["relationship_id"], "char_001_char_002")
        self.assertEqual(data["axes"]["friendship"], 20)
        self.assertEqual(data["sentiments"]["HURT"], 2)
        self.assertTrue("CONFLICT_ACTIVE" in data["flags"])
        self.assertIn("colleague", data["roles"])


class TestRelationshipEngine(unittest.TestCase):
    """Test suite for RelationshipEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RelationshipEngine()
    
    def test_create_engine(self):
        """Test creating a relationship engine."""
        self.assertIsNotNone(self.engine)
        self.assertEqual(len(self.engine.relationships), 0)
    
    def test_get_or_create_relationship(self):
        """Test getting or creating a relationship."""
        rel = self.engine.get_or_create_relationship("char_001", "char_002")
        
        self.assertIsNotNone(rel)
        self.assertEqual(rel.participants, ("char_001", "char_002"))
        
        # Getting again should return the same instance
        rel2 = self.engine.get_or_create_relationship("char_002", "char_001")
        self.assertIs(rel, rel2)
    
    def test_process_romantic_rejection(self):
        """Test processing ROMANTIC_REJECTION trigger."""
        payload = {
            "initiator": "char_001",
            "target": "char_002",
            "context": "casual_flirt"
        }
        
        self.engine.process_trigger("ROMANTIC_REJECTION", payload)
        
        rel = self.engine.get_relationship_state("char_001", "char_002")
        self.assertIsNotNone(rel)
        
        # Should have HURT sentiment
        self.assertTrue(rel.has_sentiment("HURT"))
        self.assertEqual(rel.get_sentiment_strength("HURT"), 2)
        
        # Should have JEALOUS flag
        self.assertTrue(rel.has_flag("JEALOUS"))
        
        # Romance axis should be reduced
        self.assertLess(rel.get_axis("romance"), 0)
    
    def test_process_romantic_acceptance(self):
        """Test processing ROMANTIC_ACCEPTANCE trigger."""
        payload = {
            "initiator": "char_001",
            "target": "char_002",
            "context": "date"
        }
        
        self.engine.process_trigger("ROMANTIC_ACCEPTANCE", payload)
        
        rel = self.engine.get_relationship_state("char_001", "char_002")
        self.assertIsNotNone(rel)
        
        # Romance axis should be boosted
        self.assertGreater(rel.get_axis("romance"), 0)
    
    def test_process_apology_accepted(self):
        """Test processing APOLOGY_ACCEPTED trigger."""
        # First create a conflict
        rel = self.engine.get_or_create_relationship("char_001", "char_002")
        rel.set_flag("CONFLICT_ACTIVE")
        rel.set_sentiment("HURT", 3)
        
        # Now process apology
        payload = {
            "initiator": "char_001",
            "target": "char_002"
        }
        
        self.engine.process_trigger("APOLOGY_ACCEPTED", payload)
        
        # Conflict flag should be removed
        self.assertFalse(rel.has_flag("CONFLICT_ACTIVE"))
        
        # HURT sentiment should be reduced
        self.assertEqual(rel.get_sentiment_strength("HURT"), 1)
    
    def test_process_betrayal_event(self):
        """Test processing BETRAYAL_EVENT trigger."""
        payload = {
            "initiator": "char_001",
            "target": "char_002",
            "severity": 2
        }
        
        self.engine.process_trigger("BETRAYAL_EVENT", payload)
        
        rel = self.engine.get_relationship_state("char_001", "char_002")
        self.assertIsNotNone(rel)
        
        # Should have BETRAYED sentiment
        self.assertTrue(rel.has_sentiment("BETRAYED"))
        self.assertGreater(rel.get_sentiment_strength("BETRAYED"), 0)
        
        # All axes should be negatively impacted
        self.assertLess(rel.get_axis("friendship"), 0)
        self.assertLess(rel.get_axis("respect"), 0)
        self.assertLess(rel.get_axis("romance"), 0)
    
    def test_process_heroic_action(self):
        """Test processing HEROIC_ACTION trigger."""
        payload = {
            "actor": "char_001",
            "witnesses": ["char_002", "char_003", "char_004"]
        }
        
        self.engine.process_trigger("HEROIC_ACTION", payload)
        
        # All witnesses should have increased respect for the actor
        rel_002 = self.engine.get_relationship_state("char_001", "char_002")
        rel_003 = self.engine.get_relationship_state("char_001", "char_003")
        rel_004 = self.engine.get_relationship_state("char_001", "char_004")
        
        self.assertGreater(rel_002.get_axis("respect"), 0)
        self.assertGreater(rel_003.get_axis("respect"), 0)
        self.assertGreater(rel_004.get_axis("respect"), 0)
    
    def test_process_time_skip(self):
        """Test processing TIME_SKIP trigger."""
        # Set up a relationship with an expiring flag
        rel = self.engine.get_or_create_relationship("char_001", "char_002")
        self.engine.current_day = 100
        rel.set_flag("JEALOUS", 105)
        
        # Time skip to day 106
        payload = {"days_skipped": 6}
        self.engine.process_trigger("TIME_SKIP", payload)
        
        # Current day should be updated
        self.assertEqual(self.engine.current_day, 106)
        
        # Flag should have expired
        self.assertFalse(rel.has_flag("JEALOUS"))
    
    def test_time_skip_does_not_expire_permanent_flags(self):
        """Test that flags without expiry are not removed by time skip."""
        rel = self.engine.get_or_create_relationship("char_001", "char_002")
        self.engine.current_day = 100
        rel.set_flag("ESTRANGED", None)  # No expiry
        
        # Time skip
        payload = {"days_skipped": 50}
        self.engine.process_trigger("TIME_SKIP", payload)
        
        # Flag should still be present
        self.assertTrue(rel.has_flag("ESTRANGED"))
    
    def test_get_all_relationships(self):
        """Test getting all relationships."""
        self.engine.get_or_create_relationship("char_001", "char_002")
        self.engine.get_or_create_relationship("char_003", "char_004")
        self.engine.get_or_create_relationship("char_001", "char_003")
        
        all_rels = self.engine.get_all_relationships()
        self.assertEqual(len(all_rels), 3)


class TestGlobalRelationshipEngine(unittest.TestCase):
    """Test suite for global relationship engine functions."""
    
    def test_get_relationship_engine_creates_singleton(self):
        """Test that get_relationship_engine() creates and returns singleton."""
        engine1 = get_relationship_engine()
        engine2 = get_relationship_engine()
        
        # Should be the same instance
        self.assertIs(engine1, engine2)
    
    def test_initialize_relationship_engine_replaces_global(self):
        """Test that initialize_relationship_engine() replaces the global instance."""
        engine1 = get_relationship_engine()
        engine2 = initialize_relationship_engine()
        engine3 = get_relationship_engine()
        
        # engine2 and engine3 should be the same (new instance)
        self.assertIs(engine2, engine3)
        # But different from engine1
        self.assertIsNot(engine1, engine2)


if __name__ == '__main__':
    unittest.main()
