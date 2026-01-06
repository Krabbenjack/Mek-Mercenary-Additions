"""
Event System Orchestrator

Ties all layers together for headless execution:
1. Event Injector (Layer 1)
2. Interaction Selector (Layer 2)
3. Interaction Resolver (Layer 3)
4. Outcome Applier (Layer 4)

This is a convenience wrapper for running the full event cycle.
It maintains strict layer separation and ensures no shortcuts are taken.
"""

from __future__ import annotations
from typing import List, Optional, Any, Dict
from pathlib import Path

from .axis_system import AxisRegistry
from .injector import EventInjector, EventInstance
from .interaction_selector import InteractionSelector, SelectedInteraction
from .resolver import InteractionResolver, ResolutionResult
from .outcome_applier import OutcomeApplier, AppliedOutcome


class EventSystemOrchestrator:
    """
    Orchestrates the full event cycle through all layers.
    
    Ensures:
    - Proper layer separation
    - No shortcuts or cross-layer violations
    - All state changes via Outcome Applier only
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the event system orchestrator.
        
        Args:
            config_dir: Path to config/events directory. If None, uses default location.
        """
        # Initialize core systems
        self.axis_registry = AxisRegistry()
        
        # Initialize layer components
        self.injector = EventInjector(config_dir)
        self.interaction_selector = InteractionSelector(config_dir)
        self.resolver = InteractionResolver(config_dir)
        self.outcome_applier = OutcomeApplier(self.axis_registry, config_dir)
    
    def run_event_cycle(
        self,
        event_id: int,
        characters: List[Any],
        domain: str = "social",
        environment: Optional[str] = None,
        tone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a complete event cycle through all layers.
        
        Args:
            event_id: Event ID to inject
            characters: List of Character objects
            domain: Interaction domain ("social" or "operational")
            environment: Optional environment context
            tone: Optional tone context
            
        Returns:
            Dictionary containing results from each layer
        """
        results = {
            'success': False,
            'event_instance': None,
            'selected_interaction': None,
            'resolution_result': None,
            'applied_outcome': None,
            'error': None
        }
        
        try:
            # Layer 1: Event Injection
            event_instance = self.injector.inject_event(event_id, characters)
            if not event_instance:
                results['error'] = 'Event injection failed'
                return results
            
            results['event_instance'] = event_instance
            
            # Layer 2: Interaction Selection
            selected_interaction = self.interaction_selector.select_interaction_for_event(
                event_instance,
                domain=domain,
                environment=environment,
                tone=tone
            )
            if not selected_interaction:
                results['error'] = 'Interaction selection failed'
                return results
            
            results['selected_interaction'] = selected_interaction
            
            # Get participant Character objects
            participant_chars = [
                c for c in characters
                if c.id in selected_interaction.participants
            ]
            
            # Layer 3: Interaction Resolution
            resolution_result = self.resolver.resolve_interaction(
                selected_interaction,
                participant_chars
            )
            results['resolution_result'] = resolution_result
            
            # Layer 4: Outcome Application
            applied_outcome = self.outcome_applier.apply_outcome(
                resolution_result,
                participant_chars
            )
            results['applied_outcome'] = applied_outcome
            
            results['success'] = True
            
        except Exception as e:
            results['error'] = f'Exception: {str(e)}'
        
        return results
    
    def inject_random_event(
        self,
        characters: List[Any],
        domain: str = "social",
        environment: Optional[str] = None,
        tone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inject and execute a random available event.
        
        Args:
            characters: List of Character objects
            domain: Interaction domain ("social" or "operational")
            environment: Optional environment context
            tone: Optional tone context
            
        Returns:
            Dictionary containing results from each layer
        """
        import random
        
        # Get available events
        available_events = self.injector.get_available_events(characters)
        if not available_events:
            return {
                'success': False,
                'error': 'No available events'
            }
        
        # Select random event
        event_id = random.choice(available_events)
        
        # Run full cycle
        return self.run_event_cycle(
            event_id,
            characters,
            domain=domain,
            environment=environment,
            tone=tone
        )
    
    def get_axis_state(self, char1_id: str, char2_id: str, axis_name: str) -> int:
        """Get current relationship axis value"""
        return self.axis_registry.get_relationship_axis(char1_id, char2_id, axis_name).value
    
    def get_character_axis_state(self, char_id: str, axis_name: str) -> int:
        """Get current character axis value"""
        return self.axis_registry.get_character_axis(char_id, axis_name).value
    
    def save_state(self, filepath: Path):
        """Save all axis states to file"""
        self.axis_registry.save_to_file(filepath)
    
    def load_state(self, filepath: Path):
        """Load axis states from file"""
        self.axis_registry.load_from_file(filepath)
    
    def get_state_dict(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return self.axis_registry.to_dict()
