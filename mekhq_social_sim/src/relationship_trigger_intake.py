"""
Relationship Trigger Intake Adapter

This module provides a minimal adapter that receives triggers from external systems
(Event System, Interaction System, etc.) and validates them against the authoritative
relationship_triggers.json registry.

CRITICAL DESIGN RULES:
- No logic execution: only validation and forwarding
- No fallbacks: unknown triggers must error
- No interpretation: payloads are validated but not modified
- No implicit emission: all triggers must be explicit

This adapter is the ONLY allowed entry point for triggers into the relationship system.
"""

from typing import Dict, Any, Optional, List, Callable
import json
from pathlib import Path
import sys


class TriggerValidationError(Exception):
    """Raised when a trigger fails validation against the registry."""
    pass


class TriggerIntakeAdapter:
    """
    Validates and forwards triggers to the relationship engine.
    
    This adapter acts as a gatekeeper, ensuring that only valid, well-formed
    triggers reach the relationship system.
    """
    
    def __init__(self, trigger_registry_path: Optional[Path] = None):
        """
        Initialize the trigger intake adapter.
        
        Args:
            trigger_registry_path: Path to relationship_triggers.json.
                                  If None, uses default location.
        """
        if trigger_registry_path is None:
            # Default to config/relations/relationship_triggers.json
            trigger_registry_path = (
                Path(__file__).parent.parent / "config" / "relations" / "relationship_triggers.json"
            )
        
        self.trigger_registry_path = trigger_registry_path
        self.trigger_registry: Dict[str, Any] = {}
        self.handlers: List[Callable[[str, Dict[str, Any]], None]] = []
        
        self._load_trigger_registry()
    
    def _load_trigger_registry(self) -> None:
        """Load and validate the trigger registry from JSON."""
        try:
            with open(self.trigger_registry_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Remove JSON comments (lines starting with //)
                lines = content.split('\n')
                clean_lines = []
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('//'):
                        continue
                    # Remove inline comments
                    if '//' in line:
                        line = line[:line.index('//')]
                    clean_lines.append(line)
                clean_content = '\n'.join(clean_lines)
                
                # Remove /* */ style comments
                while '/*' in clean_content:
                    start = clean_content.index('/*')
                    end = clean_content.index('*/', start) + 2
                    clean_content = clean_content[:start] + clean_content[end:]
                
                self.trigger_registry = json.loads(clean_content)
            
            # Validate registry structure
            if "_domain" not in self.trigger_registry or self.trigger_registry["_domain"] != "relationship":
                raise ValueError("Invalid trigger registry: _domain must be 'relationship'")
            
            if "triggers" not in self.trigger_registry:
                raise ValueError("Invalid trigger registry: missing 'triggers' section")
            
            print(f"[INFO] Loaded {len(self.trigger_registry['triggers'])} trigger definitions", file=sys.stderr)
            
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Trigger registry not found at {self.trigger_registry_path}. "
                "Cannot initialize relationship trigger system."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in trigger registry: {e}")
    
    def register_handler(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Register a handler to receive validated triggers.
        
        Args:
            handler: Callable that accepts (trigger_name, payload) and processes the trigger
        """
        if handler not in self.handlers:
            self.handlers.append(handler)
    
    def unregister_handler(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """Remove a previously registered handler."""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def validate_trigger(self, trigger_name: str, payload: Dict[str, Any]) -> None:
        """
        Validate a trigger against the registry.
        
        Args:
            trigger_name: Name of the trigger (e.g., "ROMANTIC_REJECTION")
            payload: Dictionary containing trigger data
            
        Raises:
            TriggerValidationError: If trigger is invalid or unknown
        """
        # Check if trigger exists in registry
        triggers = self.trigger_registry.get("triggers", {})
        if trigger_name not in triggers:
            raise TriggerValidationError(
                f"Unknown trigger: '{trigger_name}'. "
                f"All triggers must be registered in relationship_triggers.json"
            )
        
        trigger_def = triggers[trigger_name]
        
        # Validate payload schema
        expected_schema = trigger_def.get("payload_schema", {})
        if not expected_schema:
            raise TriggerValidationError(
                f"Trigger '{trigger_name}' has no payload_schema defined. "
                "All triggers must have an explicit schema."
            )
        
        # Check for required fields
        for field_name, field_type in expected_schema.items():
            if field_name not in payload:
                raise TriggerValidationError(
                    f"Trigger '{trigger_name}' missing required field '{field_name}' "
                    f"(expected type: {field_type})"
                )
            
            # Basic type validation
            value = payload[field_name]
            if field_type == "integer" and not isinstance(value, int):
                raise TriggerValidationError(
                    f"Trigger '{trigger_name}' field '{field_name}' must be integer, got {type(value).__name__}"
                )
            elif field_type == "string" and not isinstance(value, str):
                raise TriggerValidationError(
                    f"Trigger '{trigger_name}' field '{field_name}' must be string, got {type(value).__name__}"
                )
            elif field_type == "character_id" and not isinstance(value, str):
                raise TriggerValidationError(
                    f"Trigger '{trigger_name}' field '{field_name}' must be character_id (string), "
                    f"got {type(value).__name__}"
                )
            elif field_type == "character_id[]" and not isinstance(value, list):
                raise TriggerValidationError(
                    f"Trigger '{trigger_name}' field '{field_name}' must be array of character_id, "
                    f"got {type(value).__name__}"
                )
    
    def emit_trigger(self, trigger_name: str, payload: Dict[str, Any], source: str) -> None:
        """
        Validate and emit a trigger to registered handlers.
        
        Args:
            trigger_name: Name of the trigger (e.g., "ROMANTIC_REJECTION")
            payload: Dictionary containing trigger data
            source: Source system identifier (must match registry's allowed sources)
            
        Raises:
            TriggerValidationError: If trigger is invalid
        """
        # Validate the trigger
        self.validate_trigger(trigger_name, payload)
        
        # Validate source
        trigger_def = self.trigger_registry["triggers"][trigger_name]
        expected_source = trigger_def.get("source", "")
        agent_constraints = self.trigger_registry.get("agent_constraints", {})
        allowed_sources = agent_constraints.get("may_emit_triggers", [])
        
        if source not in allowed_sources:
            raise TriggerValidationError(
                f"Source '{source}' is not authorized to emit triggers. "
                f"Allowed sources: {', '.join(allowed_sources)}"
            )
        
        # Forward to all registered handlers
        for handler in self.handlers:
            try:
                handler(trigger_name, payload)
            except Exception as e:
                print(
                    f"[ERROR] Handler {handler.__name__} failed to process trigger '{trigger_name}': {e}",
                    file=sys.stderr
                )
                # Continue processing other handlers
    
    def get_trigger_info(self, trigger_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific trigger.
        
        Args:
            trigger_name: Name of the trigger
            
        Returns:
            Dictionary with trigger definition, or None if not found
        """
        triggers = self.trigger_registry.get("triggers", {})
        return triggers.get(trigger_name)
    
    def list_available_triggers(self) -> List[str]:
        """
        Get a list of all available trigger names.
        
        Returns:
            List of trigger names
        """
        return list(self.trigger_registry.get("triggers", {}).keys())


# Global singleton instance (can be initialized later)
_global_trigger_intake: Optional[TriggerIntakeAdapter] = None


def get_trigger_intake() -> TriggerIntakeAdapter:
    """
    Get the global trigger intake adapter instance.
    
    Returns:
        TriggerIntakeAdapter instance
    """
    global _global_trigger_intake
    if _global_trigger_intake is None:
        _global_trigger_intake = TriggerIntakeAdapter()
    return _global_trigger_intake


def initialize_trigger_intake(registry_path: Optional[Path] = None) -> TriggerIntakeAdapter:
    """
    Initialize the global trigger intake adapter with a specific registry path.
    
    Args:
        registry_path: Path to relationship_triggers.json
        
    Returns:
        Initialized TriggerIntakeAdapter instance
    """
    global _global_trigger_intake
    _global_trigger_intake = TriggerIntakeAdapter(registry_path)
    return _global_trigger_intake
