"""
Axis System - Core Layer

Provides a declarative, persistent axis registry that supports:
- Legacy axes (friendship)
- New social axes (respect, romance)
- Operational axes (confidence, reputation)

Key principles:
- No UI coupling
- No hardcoded axis behavior
- All axis values modified exclusively via Outcome Applier
- Persistent, deterministic state
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
import json
from pathlib import Path


@dataclass
class AxisDefinition:
    """Defines an axis with its configuration from relationship_axes_rules.json"""
    name: str
    min_value: int
    max_value: int
    decay_enabled: bool = False
    gated: bool = False
    special_rules: Dict[str, Any] = field(default_factory=dict)
    
    def clamp(self, value: float) -> int:
        """Clamp a value to this axis's valid range"""
        return max(self.min_value, min(self.max_value, int(value)))


@dataclass
class AxisState:
    """
    Persistent state for an axis.
    Can be per-character (confidence, reputation) or per-relationship (friendship, respect, romance).
    """
    axis_name: str
    value: int = 0
    flags: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AxisRegistry:
    """
    Central, declarative axis registry.
    
    Manages:
    - Axis definitions (loaded from config)
    - Axis state per character/relationship
    - Value clamping and validation
    - State persistence
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the axis registry.
        
        Args:
            config_path: Path to relationship_axes_rules.json. If None, uses default location.
        """
        self.axes: Dict[str, AxisDefinition] = {}
        self.character_axes: Dict[str, Dict[str, AxisState]] = {}  # character_id -> axis_name -> state
        self.relationship_axes: Dict[tuple[str, str], Dict[str, AxisState]] = {}  # (char1_id, char2_id) -> axis_name -> state
        
        if config_path is None:
            # Default path relative to this file
            config_path = Path(__file__).parent.parent.parent / "config" / "relations" / "relationship_axes_rules.json"
        
        self._load_axis_definitions(config_path)
    
    def _load_axis_definitions(self, config_path: Path):
        """Load axis definitions from relationship_axes_rules.json"""
        if not config_path.exists():
            # Define minimal fallback axes if config doesn't exist
            self._define_fallback_axes()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove C-style comment blocks first
            while '/*' in content:
                start = content.find('/*')
                end = content.find('*/', start)
                if end >= 0:
                    content = content[:start] + ' ' + content[end+2:]
                else:
                    break
            
            # Remove single-line comments
            lines = []
            for line in content.split('\n'):
                comment_pos = line.find('//')
                if comment_pos >= 0:
                    line = line[:comment_pos]
                lines.append(line)
            
            clean_content = '\n'.join(lines)
            config = json.loads(clean_content)
        except (json.JSONDecodeError, IOError) as e:
            # Fall back to default axes if loading fails
            self._define_fallback_axes()
            return
        
        # Parse axes from config
        axes_config = config.get('axes', {})
        for axis_name, axis_data in axes_config.items():
            range_data = axis_data.get('range', {})
            decay_data = axis_data.get('decay', {})
            
            self.axes[axis_name] = AxisDefinition(
                name=axis_name,
                min_value=range_data.get('min', -100),
                max_value=range_data.get('max', 100),
                decay_enabled=decay_data.get('enabled', False),
                gated=axis_data.get('gated', False),
                special_rules=axis_data.get('special_rules', {})
            )
        
        # Always add operational axes (confidence, reputation) even if not in config
        # These are part of the event system, not the relationship system
        if 'confidence' not in self.axes:
            self.axes['confidence'] = AxisDefinition(
                name='confidence',
                min_value=-100,
                max_value=100,
                decay_enabled=False
            )
        
        if 'reputation' not in self.axes:
            self.axes['reputation'] = AxisDefinition(
                name='reputation',
                min_value=0,
                max_value=1000,
                decay_enabled=False
            )
    
    def _define_fallback_axes(self):
        """Define minimal fallback axes if config is unavailable"""
        # Legacy friendship axis
        self.axes['friendship'] = AxisDefinition(
            name='friendship',
            min_value=-100,
            max_value=100,
            decay_enabled=False
        )
        
        # New social axes
        self.axes['respect'] = AxisDefinition(
            name='respect',
            min_value=-100,
            max_value=100,
            decay_enabled=False
        )
        
        self.axes['romance'] = AxisDefinition(
            name='romance',
            min_value=-100,
            max_value=100,
            decay_enabled=True,
            gated=True
        )
        
        # Operational axes (per-character)
        self.axes['confidence'] = AxisDefinition(
            name='confidence',
            min_value=-100,
            max_value=100,
            decay_enabled=False
        )
        
        self.axes['reputation'] = AxisDefinition(
            name='reputation',
            min_value=0,
            max_value=1000,
            decay_enabled=False
        )
    
    def has_axis(self, axis_name: str) -> bool:
        """Check if an axis is defined"""
        return axis_name in self.axes
    
    def get_axis_definition(self, axis_name: str) -> Optional[AxisDefinition]:
        """Get the definition for an axis"""
        return self.axes.get(axis_name)
    
    def _normalize_relationship_key(self, char1_id: str, char2_id: str) -> tuple[str, str]:
        """Normalize relationship key to ensure consistent ordering"""
        return tuple(sorted([char1_id, char2_id]))
    
    def get_relationship_axis(self, char1_id: str, char2_id: str, axis_name: str) -> AxisState:
        """
        Get the state of a relationship axis between two characters.
        Creates the state if it doesn't exist.
        """
        if axis_name not in self.axes:
            raise ValueError(f"Unknown axis: {axis_name}")
        
        key = self._normalize_relationship_key(char1_id, char2_id)
        
        if key not in self.relationship_axes:
            self.relationship_axes[key] = {}
        
        if axis_name not in self.relationship_axes[key]:
            self.relationship_axes[key][axis_name] = AxisState(axis_name=axis_name, value=0)
        
        return self.relationship_axes[key][axis_name]
    
    def get_character_axis(self, char_id: str, axis_name: str) -> AxisState:
        """
        Get the state of a character axis (e.g., confidence, reputation).
        Creates the state if it doesn't exist.
        """
        if axis_name not in self.axes:
            raise ValueError(f"Unknown axis: {axis_name}")
        
        if char_id not in self.character_axes:
            self.character_axes[char_id] = {}
        
        if axis_name not in self.character_axes[char_id]:
            self.character_axes[char_id][axis_name] = AxisState(axis_name=axis_name, value=0)
        
        return self.character_axes[char_id][axis_name]
    
    def set_relationship_axis_value(self, char1_id: str, char2_id: str, axis_name: str, value: int):
        """
        Set the value of a relationship axis.
        Value is automatically clamped to valid range.
        """
        axis_def = self.get_axis_definition(axis_name)
        if axis_def is None:
            raise ValueError(f"Unknown axis: {axis_name}")
        
        state = self.get_relationship_axis(char1_id, char2_id, axis_name)
        state.value = axis_def.clamp(value)
    
    def set_character_axis_value(self, char_id: str, axis_name: str, value: int):
        """
        Set the value of a character axis.
        Value is automatically clamped to valid range.
        """
        axis_def = self.get_axis_definition(axis_name)
        if axis_def is None:
            raise ValueError(f"Unknown axis: {axis_name}")
        
        state = self.get_character_axis(char_id, axis_name)
        state.value = axis_def.clamp(value)
    
    def modify_relationship_axis(self, char1_id: str, char2_id: str, axis_name: str, delta: int):
        """
        Modify a relationship axis value by delta.
        This is the primary method used by the Outcome Applier.
        """
        state = self.get_relationship_axis(char1_id, char2_id, axis_name)
        axis_def = self.get_axis_definition(axis_name)
        
        new_value = state.value + delta
        state.value = axis_def.clamp(new_value)
    
    def modify_character_axis(self, char_id: str, axis_name: str, delta: int):
        """
        Modify a character axis value by delta.
        This is the primary method used by the Outcome Applier.
        """
        state = self.get_character_axis(char_id, axis_name)
        axis_def = self.get_axis_definition(axis_name)
        
        new_value = state.value + delta
        state.value = axis_def.clamp(new_value)
    
    def set_flag(self, char1_id: str, char2_id: str, axis_name: str, flag_name: str, value: bool):
        """Set a flag on a relationship axis"""
        state = self.get_relationship_axis(char1_id, char2_id, axis_name)
        state.flags[flag_name] = value
    
    def get_flag(self, char1_id: str, char2_id: str, axis_name: str, flag_name: str) -> bool:
        """Get a flag from a relationship axis"""
        state = self.get_relationship_axis(char1_id, char2_id, axis_name)
        return state.flags.get(flag_name, False)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export all axis states to a dictionary for persistence.
        
        Returns:
            Dictionary containing all character and relationship axis states
        """
        return {
            'character_axes': {
                char_id: {
                    axis_name: {
                        'value': state.value,
                        'flags': state.flags,
                        'metadata': state.metadata
                    }
                    for axis_name, state in axes.items()
                }
                for char_id, axes in self.character_axes.items()
            },
            'relationship_axes': {
                f"{key[0]}:{key[1]}": {
                    axis_name: {
                        'value': state.value,
                        'flags': state.flags,
                        'metadata': state.metadata
                    }
                    for axis_name, state in axes.items()
                }
                for key, axes in self.relationship_axes.items()
            }
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """
        Load all axis states from a dictionary.
        
        Args:
            data: Dictionary containing axis states (from to_dict())
        """
        # Load character axes
        for char_id, axes_data in data.get('character_axes', {}).items():
            for axis_name, state_data in axes_data.items():
                state = self.get_character_axis(char_id, axis_name)
                state.value = state_data['value']
                state.flags = state_data.get('flags', {})
                state.metadata = state_data.get('metadata', {})
        
        # Load relationship axes
        for key_str, axes_data in data.get('relationship_axes', {}).items():
            char1_id, char2_id = key_str.split(':')
            for axis_name, state_data in axes_data.items():
                state = self.get_relationship_axis(char1_id, char2_id, axis_name)
                state.value = state_data['value']
                state.flags = state_data.get('flags', {})
                state.metadata = state_data.get('metadata', {})
    
    def save_to_file(self, filepath: Path):
        """Save axis states to a JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def load_from_file(self, filepath: Path):
        """Load axis states from a JSON file"""
        if not filepath.exists():
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.from_dict(data)
