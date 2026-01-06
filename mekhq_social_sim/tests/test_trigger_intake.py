"""
Tests for Relationship Trigger Intake Adapter

Verifies that the trigger intake adapter correctly validates and forwards triggers
according to the relationship_triggers.json registry.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from relationship_trigger_intake import (
    TriggerIntakeAdapter,
    TriggerValidationError,
    get_trigger_intake,
    initialize_trigger_intake
)


class TestTriggerIntakeAdapter(unittest.TestCase):
    """Test suite for TriggerIntakeAdapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize with default path
        self.adapter = TriggerIntakeAdapter()
        self.handler_calls = []
        
        def test_handler(trigger_name: str, payload: dict) -> None:
            self.handler_calls.append((trigger_name, payload))
        
        self.test_handler = test_handler
    
    def test_load_trigger_registry(self):
        """Test that the trigger registry loads successfully."""
        self.assertIsNotNone(self.adapter.trigger_registry)
        self.assertEqual(self.adapter.trigger_registry["_domain"], "relationship")
        self.assertIn("triggers", self.adapter.trigger_registry)
        self.assertGreater(len(self.adapter.trigger_registry["triggers"]), 0)
    
    def test_list_available_triggers(self):
        """Test listing all available trigger names."""
        triggers = self.adapter.list_available_triggers()
        self.assertIsInstance(triggers, list)
        self.assertIn("TIME_SKIP", triggers)
        self.assertIn("ROMANTIC_REJECTION", triggers)
        self.assertIn("ROMANTIC_ACCEPTANCE", triggers)
        self.assertIn("HEROIC_ACTION", triggers)
    
    def test_get_trigger_info(self):
        """Test retrieving information about a specific trigger."""
        info = self.adapter.get_trigger_info("TIME_SKIP")
        self.assertIsNotNone(info)
        self.assertEqual(info["category"], "time")
        self.assertIn("payload_schema", info)
        self.assertIn("days_skipped", info["payload_schema"])
    
    def test_validate_valid_trigger(self):
        """Test validation of a valid trigger passes."""
        # Should not raise
        self.adapter.validate_trigger("TIME_SKIP", {"days_skipped": 10})
    
    def test_validate_unknown_trigger_fails(self):
        """Test that unknown triggers are rejected."""
        with self.assertRaises(TriggerValidationError) as ctx:
            self.adapter.validate_trigger("UNKNOWN_TRIGGER", {})
        
        self.assertIn("Unknown trigger", str(ctx.exception))
        self.assertIn("UNKNOWN_TRIGGER", str(ctx.exception))
    
    def test_validate_missing_required_field_fails(self):
        """Test that triggers with missing required fields are rejected."""
        with self.assertRaises(TriggerValidationError) as ctx:
            self.adapter.validate_trigger("TIME_SKIP", {})
        
        self.assertIn("missing required field", str(ctx.exception))
        self.assertIn("days_skipped", str(ctx.exception))
    
    def test_validate_wrong_field_type_fails(self):
        """Test that triggers with wrong field types are rejected."""
        with self.assertRaises(TriggerValidationError) as ctx:
            self.adapter.validate_trigger("TIME_SKIP", {"days_skipped": "not_an_integer"})
        
        self.assertIn("must be integer", str(ctx.exception))
    
    def test_validate_romantic_rejection_valid(self):
        """Test validation of ROMANTIC_REJECTION with valid payload."""
        payload = {
            "initiator": "char_001",
            "target": "char_002",
            "context": "casual_flirt"
        }
        # Should not raise
        self.adapter.validate_trigger("ROMANTIC_REJECTION", payload)
    
    def test_validate_romantic_rejection_missing_field(self):
        """Test ROMANTIC_REJECTION validation fails when field is missing."""
        payload = {
            "initiator": "char_001",
            # Missing "target" and "context"
        }
        with self.assertRaises(TriggerValidationError) as ctx:
            self.adapter.validate_trigger("ROMANTIC_REJECTION", payload)
        
        self.assertIn("missing required field", str(ctx.exception))
    
    def test_validate_heroic_action_with_array(self):
        """Test validation of HEROIC_ACTION with witnesses array."""
        payload = {
            "actor": "char_001",
            "witnesses": ["char_002", "char_003", "char_004"]
        }
        # Should not raise
        self.adapter.validate_trigger("HEROIC_ACTION", payload)
    
    def test_validate_heroic_action_wrong_type_for_array(self):
        """Test HEROIC_ACTION validation fails when array field is not a list."""
        payload = {
            "actor": "char_001",
            "witnesses": "char_002"  # Should be a list
        }
        with self.assertRaises(TriggerValidationError) as ctx:
            self.adapter.validate_trigger("HEROIC_ACTION", payload)
        
        self.assertIn("must be array", str(ctx.exception))
    
    def test_register_and_emit_trigger(self):
        """Test registering a handler and emitting a trigger."""
        self.adapter.register_handler(self.test_handler)
        
        payload = {"days_skipped": 5}
        self.adapter.emit_trigger("TIME_SKIP", payload, "campaign_time_system")
        
        # Check that handler was called
        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(self.handler_calls[0][0], "TIME_SKIP")
        self.assertEqual(self.handler_calls[0][1], payload)
    
    def test_emit_trigger_with_invalid_source(self):
        """Test that emitting a trigger with unauthorized source fails."""
        payload = {"days_skipped": 5}
        
        with self.assertRaises(TriggerValidationError) as ctx:
            self.adapter.emit_trigger("TIME_SKIP", payload, "unauthorized_source")
        
        self.assertIn("not authorized", str(ctx.exception))
    
    def test_emit_trigger_with_valid_source(self):
        """Test emitting trigger with various valid sources."""
        self.adapter.register_handler(self.test_handler)
        
        # Test campaign_time_system source
        self.adapter.emit_trigger("TIME_SKIP", {"days_skipped": 3}, "campaign_time_system")
        self.assertEqual(len(self.handler_calls), 1)
        
        # Test interaction_engine source
        payload = {
            "initiator": "char_001",
            "target": "char_002",
            "context": "flirt"
        }
        self.adapter.emit_trigger("ROMANTIC_ACCEPTANCE", payload, "interaction_engine")
        self.assertEqual(len(self.handler_calls), 2)
    
    def test_multiple_handlers(self):
        """Test that multiple handlers can be registered."""
        handler_calls_2 = []
        
        def handler_2(trigger_name: str, payload: dict) -> None:
            handler_calls_2.append((trigger_name, payload))
        
        self.adapter.register_handler(self.test_handler)
        self.adapter.register_handler(handler_2)
        
        payload = {"days_skipped": 1}
        self.adapter.emit_trigger("TIME_SKIP", payload, "campaign_time_system")
        
        # Both handlers should have been called
        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(len(handler_calls_2), 1)
    
    def test_unregister_handler(self):
        """Test unregistering a handler."""
        self.adapter.register_handler(self.test_handler)
        self.adapter.unregister_handler(self.test_handler)
        
        payload = {"days_skipped": 1}
        self.adapter.emit_trigger("TIME_SKIP", payload, "campaign_time_system")
        
        # Handler should not have been called
        self.assertEqual(len(self.handler_calls), 0)
    
    def test_handler_exception_does_not_break_emission(self):
        """Test that an exception in one handler doesn't prevent other handlers from running."""
        def failing_handler(trigger_name: str, payload: dict) -> None:
            raise ValueError("Handler failed!")
        
        self.adapter.register_handler(failing_handler)
        self.adapter.register_handler(self.test_handler)
        
        payload = {"days_skipped": 1}
        # Should not raise, despite failing_handler raising an exception
        self.adapter.emit_trigger("TIME_SKIP", payload, "campaign_time_system")
        
        # Second handler should still have been called
        self.assertEqual(len(self.handler_calls), 1)


class TestGlobalTriggerIntake(unittest.TestCase):
    """Test suite for global trigger intake functions."""
    
    def test_get_trigger_intake_creates_singleton(self):
        """Test that get_trigger_intake() creates and returns singleton."""
        intake1 = get_trigger_intake()
        intake2 = get_trigger_intake()
        
        # Should be the same instance
        self.assertIs(intake1, intake2)
    
    def test_initialize_trigger_intake_replaces_global(self):
        """Test that initialize_trigger_intake() replaces the global instance."""
        intake1 = get_trigger_intake()
        intake2 = initialize_trigger_intake()
        intake3 = get_trigger_intake()
        
        # intake2 and intake3 should be the same (new instance)
        self.assertIs(intake2, intake3)
        # But different from intake1
        self.assertIsNot(intake1, intake2)


if __name__ == '__main__':
    unittest.main()
