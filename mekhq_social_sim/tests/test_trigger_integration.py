"""
Integration Test: Trigger Intake → Relationship Engine

This test verifies that triggers flow correctly from the intake adapter
to the relationship engine, ensuring the integration layer works properly.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from relationship_trigger_intake import TriggerIntakeAdapter, TriggerValidationError
from relationship_engine import RelationshipEngine


class TestTriggerIntegration(unittest.TestCase):
    """Test suite for trigger intake → relationship engine integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.intake = TriggerIntakeAdapter()
        self.engine = RelationshipEngine()
        
        # Wire them together
        self.intake.register_handler(self.engine.process_trigger)
    
    def test_romantic_rejection_flow(self):
        """Test complete flow: emit trigger → validate → process → state update."""
        payload = {
            "initiator": "alice",
            "target": "bob",
            "context": "casual_flirt"
        }
        
        # Emit trigger through intake
        self.intake.emit_trigger("ROMANTIC_REJECTION", payload, "interaction_engine")
        
        # Verify state was updated in engine
        rel = self.engine.get_relationship_state("alice", "bob")
        self.assertIsNotNone(rel)
        self.assertTrue(rel.has_sentiment("HURT"))
        self.assertTrue(rel.has_flag("JEALOUS"))
        self.assertLess(rel.get_axis("romance"), 0)
    
    def test_romantic_acceptance_flow(self):
        """Test romantic acceptance flow."""
        payload = {
            "initiator": "alice",
            "target": "bob",
            "context": "date"
        }
        
        self.intake.emit_trigger("ROMANTIC_ACCEPTANCE", payload, "interaction_engine")
        
        rel = self.engine.get_relationship_state("alice", "bob")
        self.assertIsNotNone(rel)
        self.assertGreater(rel.get_axis("romance"), 0)
    
    def test_apology_accepted_flow(self):
        """Test apology accepted flow."""
        # Set up initial conflict state
        rel = self.engine.get_or_create_relationship("alice", "bob")
        rel.set_flag("CONFLICT_ACTIVE")
        rel.set_sentiment("HURT", 3)
        
        # Emit apology trigger
        payload = {
            "initiator": "alice",
            "target": "bob"
        }
        
        self.intake.emit_trigger("APOLOGY_ACCEPTED", payload, "scripted_event")
        
        # Verify conflict resolved
        self.assertFalse(rel.has_flag("CONFLICT_ACTIVE"))
        self.assertEqual(rel.get_sentiment_strength("HURT"), 1)
    
    def test_betrayal_event_flow(self):
        """Test betrayal event flow."""
        payload = {
            "initiator": "alice",
            "target": "bob",
            "severity": 3
        }
        
        self.intake.emit_trigger("BETRAYAL_EVENT", payload, "scripted_event")
        
        rel = self.engine.get_relationship_state("alice", "bob")
        self.assertIsNotNone(rel)
        self.assertTrue(rel.has_sentiment("BETRAYED"))
        self.assertLess(rel.get_axis("friendship"), 0)
    
    def test_heroic_action_flow(self):
        """Test heroic action flow (multi-character effect)."""
        payload = {
            "actor": "alice",
            "witnesses": ["bob", "charlie", "david"]
        }
        
        self.intake.emit_trigger("HEROIC_ACTION", payload, "mission_event")
        
        # All witnesses should have increased respect
        for witness in ["bob", "charlie", "david"]:
            rel = self.engine.get_relationship_state("alice", witness)
            self.assertIsNotNone(rel)
            self.assertGreater(rel.get_axis("respect"), 0)
    
    def test_time_skip_flow(self):
        """Test time skip flow."""
        # Set up relationship with expiring flag
        rel = self.engine.get_or_create_relationship("alice", "bob")
        self.engine.current_day = 100
        rel.set_flag("JEALOUS", 105)
        
        # Emit time skip
        payload = {"days_skipped": 10}
        self.intake.emit_trigger("TIME_SKIP", payload, "campaign_time_system")
        
        # Verify time advanced and flag expired
        self.assertEqual(self.engine.current_day, 110)
        self.assertFalse(rel.has_flag("JEALOUS"))
    
    def test_invalid_trigger_rejected(self):
        """Test that invalid triggers are rejected at intake."""
        payload = {
            "initiator": "alice",
            # Missing required fields
        }
        
        with self.assertRaises(TriggerValidationError):
            self.intake.emit_trigger("ROMANTIC_REJECTION", payload, "interaction_engine")
        
        # Verify no state was created (trigger was blocked)
        rel = self.engine.get_relationship_state("alice", "bob")
        self.assertIsNone(rel)
    
    def test_unauthorized_source_rejected(self):
        """Test that triggers from unauthorized sources are rejected."""
        payload = {
            "initiator": "alice",
            "target": "bob",
            "context": "flirt"
        }
        
        with self.assertRaises(TriggerValidationError):
            self.intake.emit_trigger("ROMANTIC_REJECTION", payload, "unauthorized_system")
        
        # Verify no state was created
        rel = self.engine.get_relationship_state("alice", "bob")
        self.assertIsNone(rel)
    
    def test_sequential_triggers(self):
        """Test processing multiple triggers in sequence."""
        # Start with romantic acceptance
        payload1 = {
            "initiator": "alice",
            "target": "bob",
            "context": "date"
        }
        self.intake.emit_trigger("ROMANTIC_ACCEPTANCE", payload1, "interaction_engine")
        
        rel = self.engine.get_relationship_state("alice", "bob")
        initial_romance = rel.get_axis("romance")
        self.assertGreater(initial_romance, 0)
        
        # Then a rejection
        payload2 = {
            "initiator": "alice",
            "target": "bob",
            "context": "proposal"
        }
        self.intake.emit_trigger("ROMANTIC_REJECTION", payload2, "interaction_engine")
        
        # Romance should be lower now
        final_romance = rel.get_axis("romance")
        self.assertLess(final_romance, initial_romance)
        self.assertTrue(rel.has_sentiment("HURT"))
    
    def test_complex_scenario(self):
        """Test a complex scenario with multiple triggers and characters."""
        # Alice and Bob have romantic interest
        self.intake.emit_trigger(
            "ROMANTIC_ACCEPTANCE",
            {"initiator": "alice", "target": "bob", "context": "date"},
            "interaction_engine"
        )
        
        # Alice performs heroic action witnessed by Bob and Charlie
        self.intake.emit_trigger(
            "HEROIC_ACTION",
            {"actor": "alice", "witnesses": ["bob", "charlie"]},
            "mission_event"
        )
        
        # Bob betrays Alice
        self.intake.emit_trigger(
            "BETRAYAL_EVENT",
            {"initiator": "bob", "target": "alice", "severity": 2},
            "scripted_event"
        )
        
        # Bob apologizes
        self.intake.emit_trigger(
            "APOLOGY_ACCEPTED",
            {"initiator": "bob", "target": "alice"},
            "scripted_event"
        )
        
        # Verify final state
        rel_alice_bob = self.engine.get_relationship_state("alice", "bob")
        self.assertTrue(rel_alice_bob.has_sentiment("BETRAYED"))
        self.assertLess(rel_alice_bob.get_axis("friendship"), 0)
        # Respect is negative overall (betrayal -15, heroic +5 = -10)
        self.assertLess(rel_alice_bob.get_axis("respect"), 0)
        
        # Charlie only witnessed heroic action
        rel_alice_charlie = self.engine.get_relationship_state("alice", "charlie")
        self.assertGreater(rel_alice_charlie.get_axis("respect"), 0)
        self.assertFalse(rel_alice_charlie.has_sentiment("BETRAYED"))


if __name__ == '__main__':
    unittest.main()
