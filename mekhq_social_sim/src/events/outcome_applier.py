"""
Outcome Applier - Layer 4

Responsible for:
- Loading outcome definitions from social_outcomes.json and operational_outcomes.json
- Applying declared effects ONLY: axis_delta, set_flags, emit_triggers, *_delta
- Modifying axis states via AxisRegistry
- Recording emitted triggers

Does NOT:
- Have knowledge of events
- Have knowledge of UI
- Have knowledge of interactions (only receives resolution results)
- Infer or create effects not declared in outcome data

This is the ONLY layer that modifies state.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .axis_system import AxisRegistry


@dataclass
class AppliedOutcome:
    """Record of an outcome that was applied"""
    interaction_name: str
    stage_id: str
    outcome_tier: str  # "on_failure", "on_success", "on_great_success"
    effects_applied: List[str] = field(default_factory=list)
    triggers_emitted: List[str] = field(default_factory=list)


class OutcomeApplier:
    """
    Outcome Applier - applies declared effects from outcome definitions.
    
    Loads:
    - social_outcomes.json
    - operational_outcomes.json
    
    Modifies:
    - AxisRegistry (ONLY way to change axis values)
    """
    
    def __init__(self, axis_registry: AxisRegistry, config_dir: Optional[Path] = None):
        """
        Initialize the outcome applier.
        
        Args:
            axis_registry: The AxisRegistry to modify
            config_dir: Path to config/events directory. If None, uses default location.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config" / "events"
        
        self.config_dir = config_dir
        self.axis_registry = axis_registry
        self.social_outcomes: Dict[str, Dict[str, Any]] = {}
        self.operational_outcomes: Dict[str, Dict[str, Any]] = {}
        self.emitted_triggers: List[Dict[str, Any]] = []
        
        self._load_outcomes()
    
    def _load_json_with_comments(self, filepath: Path) -> Dict[str, Any]:
        """Load JSON file, stripping C-style comments"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Remove single-line comments
            lines = []
            for line in content.split('\n'):
                comment_pos = line.find('//')
                if comment_pos >= 0:
                    line = line[:comment_pos]
                lines.append(line)
            
            clean_content = '\n'.join(lines)
            
            # Remove C-style comment blocks
            while '/*' in clean_content:
                start = clean_content.find('/*')
                end = clean_content.find('*/', start)
                if end >= 0:
                    clean_content = clean_content[:start] + clean_content[end+2:]
                else:
                    break
            
            return json.loads(clean_content)
    
    def _load_outcomes(self):
        """Load outcome definitions from outcome files"""
        outcomes_dir = self.config_dir / "outcomes"
        
        # Load social outcomes
        social_path = outcomes_dir / "social_outcomes.json"
        if social_path.exists():
            data = self._load_json_with_comments(social_path)
            self.social_outcomes = data.get('interaction_outcomes', {})
        
        # Load operational outcomes
        operational_path = outcomes_dir / "operational_outcomes.json"
        if operational_path.exists():
            data = self._load_json_with_comments(operational_path)
            self.operational_outcomes = data.get('interaction_outcomes', {})
    
    def get_outcome_definition(
        self,
        interaction_name: str,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get outcome definition for an interaction.
        
        Args:
            interaction_name: Name of the interaction
            domain: "social" or "operational"
            
        Returns:
            Outcome definition or None if not found
        """
        if domain == "social":
            return self.social_outcomes.get(interaction_name)
        elif domain == "operational":
            return self.operational_outcomes.get(interaction_name)
        return None
    
    def _apply_axis_deltas(
        self,
        axis_deltas: Dict[str, int],
        participants: List[Any]
    ) -> List[str]:
        """
        Apply axis deltas to participants.
        
        For relationship axes (friendship, respect, romance):
        - Apply between all pairs of participants
        
        For character axes (confidence, reputation):
        - Apply to each participant individually
        
        Args:
            axis_deltas: Dictionary of axis_name -> delta_value
            participants: List of Character objects
            
        Returns:
            List of effect descriptions
        """
        effects = []
        
        for axis_name, delta in axis_deltas.items():
            if delta == 0:
                continue
            
            axis_def = self.axis_registry.get_axis_definition(axis_name)
            if not axis_def:
                continue
            
            # Determine if this is a relationship or character axis
            # Relationship axes: friendship, respect, romance
            # Character axes: confidence, reputation
            
            if axis_name in ['friendship', 'respect', 'romance']:
                # Relationship axis - apply between pairs
                for i, char1 in enumerate(participants):
                    for char2 in participants[i+1:]:
                        old_value = self.axis_registry.get_relationship_axis(
                            char1.id, char2.id, axis_name
                        ).value
                        
                        self.axis_registry.modify_relationship_axis(
                            char1.id, char2.id, axis_name, delta
                        )
                        
                        new_value = self.axis_registry.get_relationship_axis(
                            char1.id, char2.id, axis_name
                        ).value
                        
                        effects.append(
                            f"{axis_name} {char1.id}↔{char2.id}: {old_value} → {new_value} ({delta:+d})"
                        )
            
            elif axis_name in ['confidence', 'reputation']:
                # Character axis - apply to each participant
                for char in participants:
                    old_value = self.axis_registry.get_character_axis(
                        char.id, axis_name
                    ).value
                    
                    self.axis_registry.modify_character_axis(
                        char.id, axis_name, delta
                    )
                    
                    new_value = self.axis_registry.get_character_axis(
                        char.id, axis_name
                    ).value
                    
                    effects.append(
                        f"{axis_name} {char.id}: {old_value} → {new_value} ({delta:+d})"
                    )
        
        return effects
    
    def _apply_character_deltas(
        self,
        outcome_data: Dict[str, Any],
        participants: List[Any]
    ) -> List[str]:
        """
        Apply character-specific deltas (xp, fatigue, confidence, reputation pool).
        
        Args:
            outcome_data: Outcome data for this tier
            participants: List of Character objects
            
        Returns:
            List of effect descriptions
        """
        effects = []
        
        # XP delta
        xp_delta = outcome_data.get('xp_delta', 0)
        if xp_delta != 0:
            for char in participants:
                effects.append(f"XP {char.id}: {xp_delta:+d} (pooled)")
        
        # Fatigue delta
        fatigue_delta = outcome_data.get('fatigue_delta', 0)
        if fatigue_delta != 0:
            for char in participants:
                effects.append(f"Fatigue {char.id}: {fatigue_delta:+d}")
        
        # Confidence delta (handled via axis system)
        confidence_delta = outcome_data.get('confidence_delta', 0)
        if confidence_delta != 0:
            for char in participants:
                old_value = self.axis_registry.get_character_axis(char.id, 'confidence').value
                self.axis_registry.modify_character_axis(char.id, 'confidence', confidence_delta)
                new_value = self.axis_registry.get_character_axis(char.id, 'confidence').value
                effects.append(f"confidence {char.id}: {old_value} → {new_value} ({confidence_delta:+d})")
        
        # Reputation pool delta
        reputation_delta = outcome_data.get('reputation_pool_delta', 0)
        if reputation_delta != 0:
            for char in participants:
                effects.append(f"Reputation pool {char.id}: {reputation_delta:+d}")
        
        return effects
    
    def _set_flags(
        self,
        flags: Dict[str, bool],
        participants: List[Any]
    ) -> List[str]:
        """
        Set flags on relationship axes.
        
        Args:
            flags: Dictionary of flag_name -> bool_value
            participants: List of Character objects
            
        Returns:
            List of effect descriptions
        """
        effects = []
        
        for flag_name, value in flags.items():
            # Flags are typically on relationship axes
            # Apply between all pairs
            for i, char1 in enumerate(participants):
                for char2 in participants[i+1:]:
                    # Assume flags are on friendship axis by default
                    # (could be extended to specify which axis)
                    self.axis_registry.set_flag(
                        char1.id, char2.id, 'friendship', flag_name, value
                    )
                    effects.append(f"Flag {flag_name}={value} on {char1.id}↔{char2.id}")
        
        return effects
    
    def _emit_triggers(
        self,
        triggers: List[str],
        participants: List[Any]
    ) -> List[str]:
        """
        Emit triggers for later processing.
        
        Args:
            triggers: List of trigger names to emit
            participants: List of Character objects
            
        Returns:
            List of effect descriptions
        """
        effects = []
        
        for trigger in triggers:
            trigger_record = {
                'trigger': trigger,
                'participants': [c.id for c in participants]
            }
            self.emitted_triggers.append(trigger_record)
            effects.append(f"Trigger emitted: {trigger}")
        
        return effects
    
    def apply_outcome(
        self,
        resolution_result: Any,
        participants: List[Any]
    ) -> AppliedOutcome:
        """
        Apply outcomes based on resolution result.
        
        This is the main entry point for the Outcome Applier.
        
        Args:
            resolution_result: ResolutionResult from the resolver
            participants: List of Character objects
            
        Returns:
            AppliedOutcome record of what was applied
        """
        interaction_name = resolution_result.interaction_name
        domain = resolution_result.domain
        outcome_tier = resolution_result.get_outcome_tier()
        
        # Get outcome definition
        outcome_def = self.get_outcome_definition(interaction_name, domain)
        
        applied = AppliedOutcome(
            interaction_name=interaction_name,
            stage_id="overall",
            outcome_tier=outcome_tier
        )
        
        if not outcome_def:
            # No outcomes defined - nothing to apply
            return applied
        
        # Apply stage outcomes
        stage_outcomes = outcome_def.get('stage_outcomes', {})
        
        for stage_result in resolution_result.stages:
            stage_id = stage_result.stage_id
            
            if stage_id not in stage_outcomes:
                continue
            
            stage_outcome_data = stage_outcomes[stage_id]
            
            # Determine which tier to use based on this stage's success
            if stage_result.roll_result and stage_result.roll_result.stunning_success:
                tier_data = stage_outcome_data.get('on_great_success', {})
            elif stage_result.success:
                tier_data = stage_outcome_data.get('on_success', {})
            else:
                tier_data = stage_outcome_data.get('on_failure', {})
            
            if not tier_data:
                continue
            
            # Apply axis deltas
            axis_deltas = tier_data.get('axis_delta', {})
            if axis_deltas:
                effects = self._apply_axis_deltas(axis_deltas, participants)
                applied.effects_applied.extend(effects)
            
            # Apply character deltas (xp, fatigue, confidence, reputation)
            char_effects = self._apply_character_deltas(tier_data, participants)
            applied.effects_applied.extend(char_effects)
            
            # Set flags
            flags = tier_data.get('set_flags', {})
            if flags:
                flag_effects = self._set_flags(flags, participants)
                applied.effects_applied.extend(flag_effects)
            
            # Emit triggers
            triggers = tier_data.get('emit_triggers', [])
            if triggers:
                trigger_effects = self._emit_triggers(triggers, participants)
                applied.effects_applied.extend(trigger_effects)
                applied.triggers_emitted.extend(triggers)
        
        return applied
    
    def get_emitted_triggers(self) -> List[Dict[str, Any]]:
        """Get all emitted triggers"""
        return self.emitted_triggers.copy()
    
    def clear_emitted_triggers(self):
        """Clear the emitted triggers list"""
        self.emitted_triggers.clear()
