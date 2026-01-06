"""
Headless tests for Phase 1 Event Mechanics System

Tests the complete event cycle:
1. Event Injection
2. Interaction Selection
3. Interaction Resolution
4. Outcome Application
5. Axis State Persistence

NO UI DEPENDENCIES - runs completely headlessly.
"""

import sys
import unittest
from pathlib import Path
from dataclasses import dataclass

# Add src to path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import event system components
from events.axis_system import AxisRegistry, AxisDefinition, AxisState
from events.injector import EventInjector, EventInstance
from events.interaction_selector import InteractionSelector, SelectedInteraction
from events.resolver import InteractionResolver, ResolutionResult
from events.outcome_applier import OutcomeApplier, AppliedOutcome
from events.orchestrator import EventSystemOrchestrator


# Mock Character for testing
@dataclass
class MockCharacter:
    id: str
    name: str
    age: int
    skills: dict
    attributes: dict
    profession: str = "TEST"


class TestAxisSystem(unittest.TestCase):
    """Test the Axis Registry (Core Layer)"""
    
    def test_axis_registry_initialization(self):
        """Test that axis registry initializes with expected axes"""
        registry = AxisRegistry()
        
        # Check that expected axes are defined
        self.assertTrue(registry.has_axis('friendship'))
        self.assertTrue(registry.has_axis('respect'))
        self.assertTrue(registry.has_axis('romance'))
        self.assertTrue(registry.has_axis('confidence'))
        self.assertTrue(registry.has_axis('reputation'))
    
    def test_relationship_axis_operations(self):
        """Test getting and modifying relationship axes"""
        registry = AxisRegistry()
        
        # Get initial state
        state = registry.get_relationship_axis('char1', 'char2', 'friendship')
        self.assertEqual(state.value, 0)
        
        # Modify axis
        registry.modify_relationship_axis('char1', 'char2', 'friendship', 10)
        state = registry.get_relationship_axis('char1', 'char2', 'friendship')
        self.assertEqual(state.value, 10)
        
        # Verify symmetric access
        state2 = registry.get_relationship_axis('char2', 'char1', 'friendship')
        self.assertEqual(state2.value, 10)
    
    def test_character_axis_operations(self):
        """Test getting and modifying character axes"""
        registry = AxisRegistry()
        
        # Get initial state
        state = registry.get_character_axis('char1', 'confidence')
        self.assertEqual(state.value, 0)
        
        # Modify axis
        registry.modify_character_axis('char1', 'confidence', 5)
        state = registry.get_character_axis('char1', 'confidence')
        self.assertEqual(state.value, 5)
    
    def test_axis_clamping(self):
        """Test that axis values are clamped to valid range"""
        registry = AxisRegistry()
        
        # Set friendship beyond max
        registry.set_relationship_axis_value('char1', 'char2', 'friendship', 200)
        state = registry.get_relationship_axis('char1', 'char2', 'friendship')
        self.assertEqual(state.value, 100)  # Should be clamped to max
        
        # Set friendship below min
        registry.set_relationship_axis_value('char1', 'char2', 'friendship', -200)
        state = registry.get_relationship_axis('char1', 'char2', 'friendship')
        self.assertEqual(state.value, -100)  # Should be clamped to min
    
    def test_axis_persistence(self):
        """Test that axis states can be saved and loaded"""
        import tempfile
        
        registry = AxisRegistry()
        
        # Set some values
        registry.modify_relationship_axis('char1', 'char2', 'friendship', 25)
        registry.modify_character_axis('char1', 'confidence', 10)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)
        
        registry.save_to_file(temp_path)
        
        # Create new registry and load
        registry2 = AxisRegistry()
        registry2.load_from_file(temp_path)
        
        # Verify values match
        state1 = registry2.get_relationship_axis('char1', 'char2', 'friendship')
        self.assertEqual(state1.value, 25)
        
        state2 = registry2.get_character_axis('char1', 'confidence')
        self.assertEqual(state2.value, 10)
        
        # Cleanup
        temp_path.unlink()


class TestEventInjector(unittest.TestCase):
    """Test Event Injector (Layer 1)"""
    
    def setUp(self):
        """Create test characters"""
        self.characters = [
            MockCharacter('char1', 'Alice', 25, {}, {'CHA': 7}),
            MockCharacter('char2', 'Bob', 30, {}, {'CHA': 6}),
            MockCharacter('char3', 'Charlie', 28, {}, {'CHA': 8}),
        ]
    
    def test_injector_initialization(self):
        """Test that injector loads event definitions"""
        injector = EventInjector()
        
        # Should have loaded some events
        self.assertGreater(len(injector.events), 0)
        self.assertGreater(len(injector.injector_rules), 0)
    
    def test_get_available_events(self):
        """Test getting available events"""
        injector = EventInjector()
        
        available = injector.get_available_events(self.characters)
        
        # Should have some available events
        self.assertGreater(len(available), 0)
        
        # All should be valid event IDs
        for event_id in available:
            self.assertIn(event_id, injector.injector_rules)
    
    def test_inject_event(self):
        """Test injecting an event"""
        injector = EventInjector()
        
        # Get first available event
        available = injector.get_available_events(self.characters)
        if available:
            event_id = available[0]
            
            # Inject event
            event_instance = injector.inject_event(event_id, self.characters)
            
            # Should produce valid event instance
            self.assertIsNotNone(event_instance)
            self.assertEqual(event_instance.event_id, event_id)
            self.assertGreater(len(event_instance.primary_participants), 0)


class TestInteractionSelector(unittest.TestCase):
    """Test Interaction Selector (Layer 2)"""
    
    def test_selector_initialization(self):
        """Test that selector loads interaction definitions"""
        selector = InteractionSelector()
        
        # Should have loaded interactions
        self.assertGreater(len(selector.interactions), 0)
    
    def test_get_interactions_by_domain(self):
        """Test filtering interactions by domain"""
        selector = InteractionSelector()
        
        social = selector.get_interactions_by_domain('social')
        self.assertGreater(len(social), 0)
        
        # All should be social domain
        for interaction in social:
            self.assertEqual(interaction.domain, 'social')
    
    def test_select_interaction(self):
        """Test selecting an interaction"""
        selector = InteractionSelector()
        
        # Create mock participants
        participant_ids = ['char1', 'char2']
        
        # Select interaction
        selected = selector.select_interaction(
            domain='social',
            participant_ids=participant_ids,
            environment='FOB',
            tone='informal'
        )
        
        if selected:
            self.assertIsNotNone(selected)
            self.assertIn(selected.domain, ['social', 'operational'])
            self.assertEqual(selected.participants, participant_ids)


class TestInteractionResolver(unittest.TestCase):
    """Test Interaction Resolver (Layer 3)"""
    
    def setUp(self):
        """Create test characters"""
        self.characters = [
            MockCharacter('char1', 'Alice', 25, {'Negotiation': 3}, {'CHA': 7}),
            MockCharacter('char2', 'Bob', 30, {'Leadership': 2}, {'CHA': 6}),
        ]
    
    def test_resolver_initialization(self):
        """Test that resolver loads resolution rules"""
        resolver = InteractionResolver()
        
        # Should have loaded resolution profiles and rules
        self.assertGreater(len(resolver.resolution_profiles), 0)
        self.assertGreater(len(resolver.interaction_resolutions), 0)
    
    def test_resolve_interaction(self):
        """Test resolving an interaction"""
        from events.interaction_selector import SelectedInteraction
        
        resolver = InteractionResolver()
        
        # Create mock selected interaction
        selected = SelectedInteraction(
            interaction_name='casual_talk',
            domain='social',
            roll_type='group_mutual',
            participants=['char1', 'char2'],
            modifiers={}
        )
        
        # Resolve
        result = resolver.resolve_interaction(selected, self.characters)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.interaction_name, 'casual_talk')
        self.assertIn(result.get_outcome_tier(), ['on_failure', 'on_success', 'on_great_success'])


class TestOutcomeApplier(unittest.TestCase):
    """Test Outcome Applier (Layer 4)"""
    
    def setUp(self):
        """Create test characters and axis registry"""
        self.characters = [
            MockCharacter('char1', 'Alice', 25, {'Negotiation': 3}, {'CHA': 7}),
            MockCharacter('char2', 'Bob', 30, {'Leadership': 2}, {'CHA': 6}),
        ]
        self.registry = AxisRegistry()
    
    def test_applier_initialization(self):
        """Test that applier loads outcome definitions"""
        applier = OutcomeApplier(self.registry)
        
        # Should have loaded outcomes
        self.assertGreater(len(applier.social_outcomes), 0)
        self.assertGreater(len(applier.operational_outcomes), 0)
    
    def test_apply_outcome(self):
        """Test applying an outcome"""
        from events.resolver import ResolutionResult, StageResult
        from rules.skill_roll import SkillRollResult
        
        applier = OutcomeApplier(self.registry)
        
        # Create mock resolution result (success)
        roll_result = SkillRollResult(
            roll=10,
            total=12,
            target_number=8,
            success=True,
            margin=4,
            fumble=False,
            stunning_success=False
        )
        
        stage_result = StageResult(
            stage_id='conversation_flow',
            success=True,
            margin=4,
            roll_result=roll_result
        )
        
        resolution = ResolutionResult(
            interaction_name='casual_talk',
            domain='social',
            stages=[stage_result],
            overall_success=True,
            participants=['char1', 'char2']
        )
        
        # Get initial values
        initial_friendship = self.registry.get_relationship_axis('char1', 'char2', 'friendship').value
        
        # Apply outcome
        applied = applier.apply_outcome(resolution, self.characters)
        
        self.assertIsNotNone(applied)
        
        # Check that friendship was modified (casual_talk on success gives +1 friendship)
        final_friendship = self.registry.get_relationship_axis('char1', 'char2', 'friendship').value
        self.assertNotEqual(initial_friendship, final_friendship)


class TestFullEventCycle(unittest.TestCase):
    """Test complete event cycle through all layers"""
    
    def setUp(self):
        """Create test characters"""
        self.characters = [
            MockCharacter('char1', 'Alice', 25, {'Negotiation': 3, 'Leadership': 2}, {'CHA': 7, 'INT': 6}),
            MockCharacter('char2', 'Bob', 30, {'Leadership': 2, 'Negotiation': 1}, {'CHA': 6, 'INT': 7}),
            MockCharacter('char3', 'Charlie', 28, {'Negotiation': 2}, {'CHA': 8, 'INT': 5}),
        ]
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes all layers"""
        orchestrator = EventSystemOrchestrator()
        
        self.assertIsNotNone(orchestrator.axis_registry)
        self.assertIsNotNone(orchestrator.injector)
        self.assertIsNotNone(orchestrator.interaction_selector)
        self.assertIsNotNone(orchestrator.resolver)
        self.assertIsNotNone(orchestrator.outcome_applier)
    
    def test_full_event_cycle(self):
        """Test running a complete event cycle"""
        orchestrator = EventSystemOrchestrator()
        
        # Get available events
        available = orchestrator.injector.get_available_events(self.characters)
        self.assertGreater(len(available), 0)
        
        # Run event cycle
        event_id = available[0]
        results = orchestrator.run_event_cycle(
            event_id,
            self.characters,
            domain='social',
            environment='FOB',
            tone='informal'
        )
        
        # Check results
        self.assertIsNotNone(results)
        
        # If successful, should have all layer outputs
        if results['success']:
            self.assertIsNotNone(results['event_instance'])
            self.assertIsNotNone(results['selected_interaction'])
            self.assertIsNotNone(results['resolution_result'])
            self.assertIsNotNone(results['applied_outcome'])
    
    def test_state_persistence(self):
        """Test that state persists across cycles"""
        import tempfile
        
        orchestrator = EventSystemOrchestrator()
        
        # Run several event cycles
        for _ in range(3):
            results = orchestrator.inject_random_event(
                self.characters,
                domain='social',
                tone='informal'
            )
        
        # Get current state
        state1 = orchestrator.get_state_dict()
        
        # Save state
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)
        
        orchestrator.save_state(temp_path)
        
        # Create new orchestrator and load state
        orchestrator2 = EventSystemOrchestrator()
        orchestrator2.load_state(temp_path)
        
        # Get loaded state
        state2 = orchestrator2.get_state_dict()
        
        # States should match
        self.assertEqual(state1, state2)
        
        # Cleanup
        temp_path.unlink()
    
    def test_no_ui_imports(self):
        """Verify that no UI modules are imported"""
        import sys
        
        # Check that tkinter is not in loaded modules
        ui_modules = [name for name in sys.modules.keys() if 'tkinter' in name.lower() or 'gui' in name.lower()]
        
        # Filter out only modules from our package
        our_ui_modules = [name for name in ui_modules if 'mekhq_social_sim' in name]
        
        # Should not have imported any of our UI modules
        self.assertEqual(len(our_ui_modules), 0, f"UI modules detected: {our_ui_modules}")


if __name__ == '__main__':
    unittest.main()
