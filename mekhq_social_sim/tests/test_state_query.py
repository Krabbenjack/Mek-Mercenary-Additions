"""
Tests for Relationship State Query Interface

Verifies that the state query interface provides read-only access to relationship
state without allowing mutations.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from relationship_engine import RelationshipEngine
from relationship_state_query import RelationshipStateQuery, get_state_query, initialize_state_query


class TestRelationshipStateQuery(unittest.TestCase):
    """Test suite for RelationshipStateQuery."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = RelationshipEngine()
        self.query = RelationshipStateQuery(self.engine)
    
    def test_create_query_interface(self):
        """Test creating a query interface."""
        self.assertIsNotNone(self.query)
        self.assertIs(self.query.engine, self.engine)
    
    def test_get_axis_value(self):
        """Test getting axis values."""
        # Create a relationship with specific axis values
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", 42)
        rel.set_axis("romance", -15)
        
        # Query axis values
        self.assertEqual(self.query.get_axis_value("alice", "bob", "friendship"), 42)
        self.assertEqual(self.query.get_axis_value("alice", "bob", "romance"), -15)
        self.assertEqual(self.query.get_axis_value("alice", "bob", "respect"), 0)
    
    def test_get_axis_value_nonexistent_relationship(self):
        """Test getting axis value for non-existent relationship returns 0."""
        self.assertEqual(self.query.get_axis_value("alice", "bob", "friendship"), 0)
    
    def test_has_flag(self):
        """Test checking for flags."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("CONFLICT_ACTIVE")
        
        self.assertTrue(self.query.has_flag("alice", "bob", "CONFLICT_ACTIVE"))
        self.assertFalse(self.query.has_flag("alice", "bob", "ESTRANGED"))
    
    def test_has_flag_nonexistent_relationship(self):
        """Test checking flag for non-existent relationship returns False."""
        self.assertFalse(self.query.has_flag("alice", "bob", "CONFLICT_ACTIVE"))
    
    def test_has_sentiment(self):
        """Test checking for sentiments."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_sentiment("HURT", 3)
        
        self.assertTrue(self.query.has_sentiment("alice", "bob", "HURT"))
        self.assertFalse(self.query.has_sentiment("alice", "bob", "BETRAYED"))
    
    def test_get_sentiment_strength(self):
        """Test getting sentiment strength."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_sentiment("HURT", 3)
        
        self.assertEqual(self.query.get_sentiment_strength("alice", "bob", "HURT"), 3)
        self.assertEqual(self.query.get_sentiment_strength("alice", "bob", "BETRAYED"), 0)
    
    def test_has_role(self):
        """Test checking for roles."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.add_role("family")
        
        self.assertTrue(self.query.has_role("alice", "bob", "family"))
        self.assertFalse(self.query.has_role("alice", "bob", "spouse"))
    
    def test_should_suppress_romantic_interaction_conflict(self):
        """Test romantic suppression due to conflict."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("CONFLICT_ACTIVE")
        
        self.assertTrue(self.query.should_suppress_romantic_interaction("alice", "bob"))
    
    def test_should_suppress_romantic_interaction_estranged(self):
        """Test romantic suppression due to estrangement."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("ESTRANGED")
        
        self.assertTrue(self.query.should_suppress_romantic_interaction("alice", "bob"))
    
    def test_should_suppress_romantic_interaction_betrayed(self):
        """Test romantic suppression due to betrayal."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_sentiment("BETRAYED", 4)
        
        self.assertTrue(self.query.should_suppress_romantic_interaction("alice", "bob"))
    
    def test_should_suppress_romantic_interaction_negative_romance(self):
        """Test romantic suppression due to deeply negative romance."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("romance", -40)
        
        self.assertTrue(self.query.should_suppress_romantic_interaction("alice", "bob"))
    
    def test_should_not_suppress_romantic_interaction_normal(self):
        """Test that romantic interactions are not suppressed in normal state."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("romance", 20)
        
        self.assertFalse(self.query.should_suppress_romantic_interaction("alice", "bob"))
    
    def test_should_suppress_friendly_interaction(self):
        """Test friendly interaction suppression."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("ESTRANGED")
        
        self.assertTrue(self.query.should_suppress_friendly_interaction("alice", "bob"))
    
    def test_should_suppress_friendly_interaction_negative_friendship(self):
        """Test friendly suppression due to very negative friendship."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", -60)
        
        self.assertTrue(self.query.should_suppress_friendly_interaction("alice", "bob"))
    
    def test_is_relationship_awkward_hurt_and_jealous(self):
        """Test awkward detection with HURT + JEALOUS."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_sentiment("HURT", 2)
        rel.set_flag("JEALOUS")
        
        self.assertTrue(self.query.is_relationship_awkward("alice", "bob"))
    
    def test_is_relationship_awkward_conflict(self):
        """Test awkward detection with active conflict."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("CONFLICT_ACTIVE")
        
        self.assertTrue(self.query.is_relationship_awkward("alice", "bob"))
    
    def test_is_not_awkward_normal(self):
        """Test that normal relationships are not awkward."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", 30)
        
        self.assertFalse(self.query.is_relationship_awkward("alice", "bob"))
    
    def test_get_interaction_weight_modifier_romantic_high(self):
        """Test romantic weight modifier with high romance."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("romance", 40)
        
        modifier = self.query.get_interaction_weight_modifier("alice", "bob", "romantic")
        self.assertGreater(modifier, 1.0)
    
    def test_get_interaction_weight_modifier_romantic_suppressed(self):
        """Test romantic weight modifier when suppressed."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("CONFLICT_ACTIVE")
        
        modifier = self.query.get_interaction_weight_modifier("alice", "bob", "romantic")
        self.assertEqual(modifier, 0.0)
    
    def test_get_interaction_weight_modifier_friendly(self):
        """Test friendly weight modifier."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", 40)
        
        modifier = self.query.get_interaction_weight_modifier("alice", "bob", "friendly")
        self.assertGreater(modifier, 1.0)
    
    def test_get_interaction_weight_modifier_professional(self):
        """Test professional weight modifier."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("respect", 40)
        
        modifier = self.query.get_interaction_weight_modifier("alice", "bob", "professional")
        self.assertGreater(modifier, 1.0)
    
    def test_get_bonding_weight_modifier_conflict(self):
        """Test bonding weight modifier with active conflict."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("CONFLICT_ACTIVE")
        
        modifier = self.query.get_bonding_weight_modifier("alice", "bob")
        self.assertLess(modifier, 1.0)
    
    def test_get_bonding_weight_modifier_negative_friendship(self):
        """Test bonding weight modifier with negative friendship."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", -30)
        
        modifier = self.query.get_bonding_weight_modifier("alice", "bob")
        self.assertLess(modifier, 1.0)
    
    def test_get_bonding_weight_modifier_high_friendship(self):
        """Test bonding weight modifier with high friendship."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", 40)
        
        modifier = self.query.get_bonding_weight_modifier("alice", "bob")
        self.assertGreater(modifier, 1.0)
    
    def test_get_relationship_summary(self):
        """Test getting relationship summary."""
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", 30)
        rel.set_sentiment("HURT", 2)
        rel.set_flag("JEALOUS")
        rel.add_role("colleague")
        
        summary = self.query.get_relationship_summary("alice", "bob")
        
        self.assertEqual(summary["axes"]["friendship"], 30)
        self.assertEqual(summary["sentiments"]["HURT"], 2)
        self.assertIn("JEALOUS", summary["flags"])
        self.assertIn("colleague", summary["roles"])
        self.assertTrue(summary["is_awkward"])
    
    def test_get_relationship_summary_nonexistent(self):
        """Test getting summary for non-existent relationship."""
        summary = self.query.get_relationship_summary("alice", "bob")
        self.assertEqual(summary, {})
    
    def test_get_all_relationships_for_character(self):
        """Test getting all relationships for a character."""
        # Create relationships
        self.engine.get_or_create_relationship("alice", "bob")
        self.engine.get_or_create_relationship("alice", "charlie")
        self.engine.get_or_create_relationship("bob", "charlie")
        
        # Query Alice's relationships
        alice_rels = self.query.get_all_relationships_for_character("alice")
        
        self.assertEqual(len(alice_rels), 2)
        other_ids = [rel["other_character_id"] for rel in alice_rels]
        self.assertIn("bob", other_ids)
        self.assertIn("charlie", other_ids)
    
    def test_read_only_enforcement(self):
        """Test that query interface cannot mutate state (conceptual test)."""
        # This is a conceptual test - the interface doesn't expose mutation methods
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_axis("friendship", 50)
        
        # Query should return the value
        self.assertEqual(self.query.get_axis_value("alice", "bob", "friendship"), 50)
        
        # Query interface has no mutation methods (verified by not having them in the class)
        self.assertFalse(hasattr(self.query, "set_axis"))
        self.assertFalse(hasattr(self.query, "modify_axis"))
        self.assertFalse(hasattr(self.query, "set_sentiment"))
        self.assertFalse(hasattr(self.query, "set_flag"))


class TestGlobalStateQuery(unittest.TestCase):
    """Test suite for global state query functions."""
    
    def test_get_state_query_creates_singleton(self):
        """Test that get_state_query() creates and returns singleton."""
        query1 = get_state_query()
        query2 = get_state_query()
        
        # Should be the same instance
        self.assertIs(query1, query2)
    
    def test_initialize_state_query_replaces_global(self):
        """Test that initialize_state_query() replaces the global instance."""
        engine = RelationshipEngine()
        
        query1 = get_state_query()
        query2 = initialize_state_query(engine)
        query3 = get_state_query()
        
        # query2 and query3 should be the same (new instance)
        self.assertIs(query2, query3)
        # But different from query1
        self.assertIsNot(query1, query2)
        # And should use the provided engine
        self.assertIs(query2.engine, engine)


if __name__ == '__main__':
    unittest.main()
