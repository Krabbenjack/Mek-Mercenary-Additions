"""
Event management system with persistence and headless event mechanics.

This package provides:
- EventManager: Manages events with JSON persistence (legacy UI-coupled system)
- EventType: Enum for predefined event types
- RecurrenceType: Enum for event recurrence patterns
- Event dialogs: GUI components for creating/editing/managing events

Phase 1 Headless Event Mechanics (NO UI):
- AxisRegistry: Core axis system for persistent state
- EventInjector: Layer 1 - Event selection and participant selection
- InteractionSelector: Layer 2 - Interaction selection with modifiers
- InteractionResolver: Layer 3 - Mechanical resolution via skill checks
- OutcomeApplier: Layer 4 - Applies outcomes and modifies axes
- EventSystemOrchestrator: Convenience wrapper for full event cycle
"""

from .manager import EventManager, Event, EventType, RecurrenceType

# Phase 1 Headless Event Mechanics
from .axis_system import AxisRegistry, AxisDefinition, AxisState
from .injector import EventInjector, EventInstance
from .interaction_selector import InteractionSelector, SelectedInteraction
from .resolver import InteractionResolver, ResolutionResult, StageResult
from .outcome_applier import OutcomeApplier, AppliedOutcome
from .orchestrator import EventSystemOrchestrator

__all__ = [
    # Legacy UI-coupled system
    "EventManager",
    "Event",
    "EventType",
    "RecurrenceType",
    
    # Phase 1 Headless Event Mechanics
    "AxisRegistry",
    "AxisDefinition",
    "AxisState",
    "EventInjector",
    "EventInstance",
    "InteractionSelector",
    "SelectedInteraction",
    "InteractionResolver",
    "ResolutionResult",
    "StageResult",
    "OutcomeApplier",
    "AppliedOutcome",
    "EventSystemOrchestrator",
]
