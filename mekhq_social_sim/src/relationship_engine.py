"""
Relationship Engine Core

This module is the MASTER of relationship state management. It processes triggers
from the trigger intake adapter and applies relationship rules to update axes,
sentiments, flags, and states.

CRITICAL DESIGN RULES:
- This module OWNS all relationship state mutations
- Only processes EXPLICIT triggers (never infers)
- Applies rules from relationship_*.json files
- Never modifies event system state
- Never performs event selection or weighting

Architecture:
    Trigger Intake → Relationship Engine → State Update
                           ↓
                    Rule Application (axes, sentiments, flags)
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import sys


class RelationshipState:
    """
    Represents the complete state of a relationship between two characters.
    """
    
    def __init__(self, char_a_id: str, char_b_id: str):
        """
        Initialize a relationship state.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
        """
        # Canonicalize IDs for bidirectional relationships
        self.participants = tuple(sorted([char_a_id, char_b_id]))
        
        # Axes (numeric values)
        self.axes: Dict[str, int] = {
            "friendship": 0,
            "respect": 0,
            "romance": 0
        }
        
        # Sentiments (name -> strength)
        self.sentiments: Dict[str, int] = {}
        
        # Flags (name -> expiry_day or None)
        self.flags: Dict[str, Optional[int]] = {}
        
        # Roles (e.g., "family", "spouse")
        self.roles: List[str] = []
        
        # Metadata
        self.last_interaction_day: Optional[int] = None
        self.relationship_id: str = f"{self.participants[0]}_{self.participants[1]}"
    
    def get_axis(self, axis_name: str) -> int:
        """Get the value of an axis."""
        return self.axes.get(axis_name, 0)
    
    def set_axis(self, axis_name: str, value: int) -> None:
        """Set the value of an axis (with bounds checking)."""
        # Default bounds: -100 to 100
        min_val = -100
        max_val = 100
        
        clamped_value = max(min_val, min(max_val, value))
        self.axes[axis_name] = clamped_value
    
    def modify_axis(self, axis_name: str, delta: int) -> None:
        """Modify an axis by a delta value."""
        current = self.get_axis(axis_name)
        self.set_axis(axis_name, current + delta)
    
    def has_sentiment(self, sentiment_name: str) -> bool:
        """Check if a sentiment is active."""
        return sentiment_name in self.sentiments and self.sentiments[sentiment_name] > 0
    
    def get_sentiment_strength(self, sentiment_name: str) -> int:
        """Get the strength of a sentiment."""
        return self.sentiments.get(sentiment_name, 0)
    
    def set_sentiment(self, sentiment_name: str, strength: int) -> None:
        """Set a sentiment with a specific strength."""
        if strength <= 0:
            # Remove sentiment if strength is 0 or negative
            self.sentiments.pop(sentiment_name, None)
        else:
            self.sentiments[sentiment_name] = strength
    
    def modify_sentiment(self, sentiment_name: str, delta: int) -> None:
        """Modify a sentiment strength by a delta."""
        current = self.get_sentiment_strength(sentiment_name)
        new_strength = current + delta
        self.set_sentiment(sentiment_name, new_strength)
    
    def has_flag(self, flag_name: str) -> bool:
        """Check if a flag is active."""
        return flag_name in self.flags
    
    def set_flag(self, flag_name: str, expiry_day: Optional[int] = None) -> None:
        """Set a flag (optionally with expiry)."""
        self.flags[flag_name] = expiry_day
    
    def remove_flag(self, flag_name: str) -> None:
        """Remove a flag."""
        self.flags.pop(flag_name, None)
    
    def has_role(self, role_name: str) -> bool:
        """Check if a role is assigned."""
        return role_name in self.roles
    
    def add_role(self, role_name: str) -> None:
        """Add a role."""
        if role_name not in self.roles:
            self.roles.append(role_name)
    
    def remove_role(self, role_name: str) -> None:
        """Remove a role."""
        if role_name in self.roles:
            self.roles.remove(role_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "relationship_id": self.relationship_id,
            "participants": list(self.participants),
            "axes": self.axes.copy(),
            "sentiments": self.sentiments.copy(),
            "flags": self.flags.copy(),
            "roles": self.roles.copy(),
            "last_interaction_day": self.last_interaction_day
        }


class RelationshipEngine:
    """
    Core relationship engine that processes triggers and applies relationship rules.
    
    This is the MASTER of relationship state. It owns all state mutations.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the relationship engine.
        
        Args:
            config_dir: Path to config/relations directory. If None, uses default.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config" / "relations"
        
        self.config_dir = config_dir
        self.relationships: Dict[str, RelationshipState] = {}
        self.current_day: int = 0
        
        # Load configuration files
        self.axes_rules: Dict[str, Any] = {}
        self.sentiment_rules: Dict[str, Any] = {}
        self.flag_rules: Dict[str, Any] = {}
        self.acceptance_rules: Dict[str, Any] = {}
        
        self._load_configuration()
    
    def _load_json_with_comments(self, filepath: Path) -> Dict[str, Any]:
        """Load JSON file, stripping comments."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Remove line comments
                lines = content.split('\n')
                clean_lines = []
                for line in lines:
                    if line.strip().startswith('//'):
                        continue
                    if '//' in line:
                        line = line[:line.index('//')]
                    clean_lines.append(line)
                clean_content = '\n'.join(clean_lines)
                
                # Remove block comments
                while '/*' in clean_content:
                    start = clean_content.index('/*')
                    end = clean_content.index('*/', start) + 2
                    clean_content = clean_content[:start] + clean_content[end:]
                
                return json.loads(clean_content)
        except FileNotFoundError:
            print(f"[WARNING] Configuration file not found: {filepath}", file=sys.stderr)
            return {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in {filepath}: {e}", file=sys.stderr)
            return {}
    
    def _load_configuration(self) -> None:
        """Load all relationship configuration files."""
        self.axes_rules = self._load_json_with_comments(
            self.config_dir / "relationship_axes_rules.json"
        )
        self.sentiment_rules = self._load_json_with_comments(
            self.config_dir / "relationship_sentiment_rules.json"
        )
        self.flag_rules = self._load_json_with_comments(
            self.config_dir / "relationship_flags_rules.json"
        )
        self.acceptance_rules = self._load_json_with_comments(
            self.config_dir / "relationship_acceptance_rules.json"
        )
        
        print(f"[INFO] Relationship engine loaded configuration", file=sys.stderr)
    
    def get_or_create_relationship(self, char_a_id: str, char_b_id: str) -> RelationshipState:
        """
        Get or create a relationship state.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            
        Returns:
            RelationshipState for the pair
        """
        # Create canonical key
        key = "_".join(sorted([char_a_id, char_b_id]))
        
        if key not in self.relationships:
            self.relationships[key] = RelationshipState(char_a_id, char_b_id)
        
        return self.relationships[key]
    
    def process_trigger(self, trigger_name: str, payload: Dict[str, Any]) -> None:
        """
        Process a trigger and apply relationship rules.
        
        This is the main entry point for trigger processing.
        
        Args:
            trigger_name: Name of the trigger (e.g., "ROMANTIC_REJECTION")
            payload: Trigger payload dictionary
        """
        print(f"[DEBUG] Processing trigger: {trigger_name}", file=sys.stderr)
        
        # Route to appropriate handler
        if trigger_name == "TIME_SKIP":
            self._handle_time_skip(payload)
        elif trigger_name == "ROMANTIC_REJECTION":
            self._handle_romantic_rejection(payload)
        elif trigger_name == "ROMANTIC_ACCEPTANCE":
            self._handle_romantic_acceptance(payload)
        elif trigger_name == "APOLOGY_ACCEPTED":
            self._handle_apology_accepted(payload)
        elif trigger_name == "BETRAYAL_EVENT":
            self._handle_betrayal_event(payload)
        elif trigger_name == "HEROIC_ACTION":
            self._handle_heroic_action(payload)
        else:
            print(f"[WARNING] No handler for trigger: {trigger_name}", file=sys.stderr)
    
    def _handle_time_skip(self, payload: Dict[str, Any]) -> None:
        """Handle TIME_SKIP trigger (decay processing)."""
        days_skipped = payload["days_skipped"]
        self.current_day += days_skipped
        
        print(f"[DEBUG] Time skip: {days_skipped} days (now day {self.current_day})", file=sys.stderr)
        
        # Process decay for all relationships
        # (Simplified - would apply axes_rules decay logic here)
        for rel_state in self.relationships.values():
            # Process flag expiries
            expired_flags = []
            for flag_name, expiry_day in list(rel_state.flags.items()):
                if expiry_day is not None and self.current_day >= expiry_day:
                    expired_flags.append(flag_name)
            
            for flag_name in expired_flags:
                rel_state.remove_flag(flag_name)
                print(f"[DEBUG] Flag '{flag_name}' expired for {rel_state.relationship_id}", file=sys.stderr)
    
    def _handle_romantic_rejection(self, payload: Dict[str, Any]) -> None:
        """Handle ROMANTIC_REJECTION trigger."""
        initiator_id = payload["initiator"]
        target_id = payload["target"]
        
        rel = self.get_or_create_relationship(initiator_id, target_id)
        
        # Apply sentiment: HURT (based on sentiment_rules.json)
        # Base strength = 2, can be modified by traits
        rel.set_sentiment("HURT", 2)
        
        # Apply flag: JEALOUS (temporary, 7 days)
        rel.set_flag("JEALOUS", self.current_day + 7)
        
        # Modify romance axis (negative impact)
        rel.modify_axis("romance", -5)
        
        print(f"[DEBUG] Romantic rejection: {initiator_id} → {target_id}", file=sys.stderr)
    
    def _handle_romantic_acceptance(self, payload: Dict[str, Any]) -> None:
        """Handle ROMANTIC_ACCEPTANCE trigger."""
        initiator_id = payload["initiator"]
        target_id = payload["target"]
        
        rel = self.get_or_create_relationship(initiator_id, target_id)
        
        # Boost romance axis
        rel.modify_axis("romance", 10)
        
        # Remove negative sentiments (if any)
        if rel.has_sentiment("HURT"):
            rel.modify_sentiment("HURT", -1)
        
        print(f"[DEBUG] Romantic acceptance: {initiator_id} ↔ {target_id}", file=sys.stderr)
    
    def _handle_apology_accepted(self, payload: Dict[str, Any]) -> None:
        """Handle APOLOGY_ACCEPTED trigger."""
        initiator_id = payload["initiator"]
        target_id = payload["target"]
        
        rel = self.get_or_create_relationship(initiator_id, target_id)
        
        # Remove CONFLICT_ACTIVE flag
        rel.remove_flag("CONFLICT_ACTIVE")
        
        # Reduce HURT sentiment
        if rel.has_sentiment("HURT"):
            rel.modify_sentiment("HURT", -2)
        
        print(f"[DEBUG] Apology accepted: {initiator_id} → {target_id}", file=sys.stderr)
    
    def _handle_betrayal_event(self, payload: Dict[str, Any]) -> None:
        """Handle BETRAYAL_EVENT trigger."""
        initiator_id = payload["initiator"]
        target_id = payload["target"]
        severity = payload["severity"]
        
        rel = self.get_or_create_relationship(initiator_id, target_id)
        
        # Apply BETRAYED sentiment with severity-based strength
        strength = min(5, 2 + severity)
        rel.set_sentiment("BETRAYED", strength)
        
        # Severe negative impact on friendship and respect
        rel.modify_axis("friendship", -20)
        rel.modify_axis("respect", -15)
        rel.modify_axis("romance", -30)
        
        print(f"[DEBUG] Betrayal event: {initiator_id} betrayed {target_id} (severity {severity})", file=sys.stderr)
    
    def _handle_heroic_action(self, payload: Dict[str, Any]) -> None:
        """Handle HEROIC_ACTION trigger (mutual respect effects)."""
        actor_id = payload["actor"]
        witnesses = payload["witnesses"]
        
        print(f"[DEBUG] Heroic action by {actor_id}, witnessed by {len(witnesses)} characters", file=sys.stderr)
        
        # Apply respect boost to all witnesses
        for witness_id in witnesses:
            if witness_id == actor_id:
                continue
            
            rel = self.get_or_create_relationship(actor_id, witness_id)
            rel.modify_axis("respect", 5)
    
    def get_relationship_state(self, char_a_id: str, char_b_id: str) -> Optional[RelationshipState]:
        """
        Get the current state of a relationship (read-only access).
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            
        Returns:
            RelationshipState or None if relationship doesn't exist
        """
        key = "_".join(sorted([char_a_id, char_b_id]))
        return self.relationships.get(key)
    
    def get_all_relationships(self) -> List[RelationshipState]:
        """Get all relationship states (for serialization/display)."""
        return list(self.relationships.values())


# Global singleton instance
_global_relationship_engine: Optional[RelationshipEngine] = None


def get_relationship_engine() -> RelationshipEngine:
    """
    Get the global relationship engine instance.
    
    Returns:
        RelationshipEngine instance
    """
    global _global_relationship_engine
    if _global_relationship_engine is None:
        _global_relationship_engine = RelationshipEngine()
    return _global_relationship_engine


def initialize_relationship_engine(config_dir: Optional[Path] = None) -> RelationshipEngine:
    """
    Initialize the global relationship engine with a specific config directory.
    
    Args:
        config_dir: Path to config/relations directory
        
    Returns:
        Initialized RelationshipEngine instance
    """
    global _global_relationship_engine
    _global_relationship_engine = RelationshipEngine(config_dir)
    return _global_relationship_engine
