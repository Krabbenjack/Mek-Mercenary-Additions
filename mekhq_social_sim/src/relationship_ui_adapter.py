"""
relationship_ui_adapter.py

Adapter module to bridge the UI with the relationship runtime provider.
This module provides a clean interface for the GUI to access relationship data
without directly depending on the runtime implementation details.

IMPORTANT:
- This module NEVER reads rule JSON files
- This module NEVER computes relationship values
- This module ONLY queries the runtime provider
- All relationship data comes from serialize_relationship_runtime()
"""

from typing import Dict, List, Any, Optional
from datetime import date
from pathlib import Path
import sys

# Add runtime directory to path
runtime_path = Path(__file__).resolve().parents[1] / "runtime"
if str(runtime_path) not in sys.path:
    sys.path.insert(0, str(runtime_path))


class RelationshipRuntimeAdapter:
    """
    Adapter for accessing relationship runtime data in the UI.
    Provides a clean interface that hides implementation details.
    """
    
    def __init__(self, current_date: date, campaign_start_date: date):
        """
        Initialize the adapter.
        
        Args:
            current_date: Current campaign date
            campaign_start_date: Campaign start date
        """
        self.current_date = current_date
        self.campaign_start_date = campaign_start_date
        self._runtime_data: Optional[Dict[str, Any]] = None
        
    def _get_runtime_data(self) -> Dict[str, Any]:
        """
        Get runtime data from the relationship runtime provider.
        
        For now, this returns mock data since the runtime provider
        has placeholder implementations. When the backend is fully
        implemented, this will call the actual runtime provider.
        """
        if self._runtime_data is not None:
            return self._runtime_data
            
        # Try to import and use the real runtime provider
        try:
            import relationship_runtime_provider as provider
            
            # Check if the provider has real implementations
            # For now, we'll catch NotImplementedError and use mock data
            try:
                self._runtime_data = provider.serialize_relationship_runtime()
            except NotImplementedError:
                # Provider not fully implemented yet, use mock data
                self._runtime_data = self._get_mock_runtime_data()
        except ImportError:
            # Provider module not available, use mock data
            self._runtime_data = self._get_mock_runtime_data()
            
        return self._runtime_data
    
    def _get_mock_runtime_data(self) -> Dict[str, Any]:
        """
        Generate mock runtime data for testing the UI.
        This simulates what serialize_relationship_runtime() will return.
        """
        campaign_day = (self.current_date - self.campaign_start_date).days
        
        return {
            "_domain": "relationship",
            "_type": "runtime_snapshot",
            "_authoritative": True,
            
            "meta": {
                "current_campaign_day": campaign_day,
                "generated_on_day": campaign_day,
                "time_source": "campaign_calendar"
            },
            
            "relationships": []
        }
    
    def get_relationships_for_character(self, character_id: str) -> List[Dict[str, Any]]:
        """
        Get all relationships involving a specific character.
        
        Args:
            character_id: The character's ID
            
        Returns:
            List of relationship dictionaries involving this character
        """
        runtime_data = self._get_runtime_data()
        relationships = []
        
        for rel in runtime_data.get("relationships", []):
            participants = rel.get("participants", {})
            if participants.get("a") == character_id or participants.get("b") == character_id:
                relationships.append(rel)
                
        return relationships
    
    def get_relationship_between(self, char_a_id: str, char_b_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the relationship between two specific characters.
        
        Args:
            char_a_id: First character's ID
            char_b_id: Second character's ID
            
        Returns:
            Relationship dictionary if it exists, None otherwise
        """
        runtime_data = self._get_runtime_data()
        
        for rel in runtime_data.get("relationships", []):
            participants = rel.get("participants", {})
            a = participants.get("a")
            b = participants.get("b")
            
            if (a == char_a_id and b == char_b_id) or (a == char_b_id and b == char_a_id):
                return rel
                
        return None
    
    def has_any_relationships(self, character_id: str) -> bool:
        """
        Check if a character has any relationships.
        
        Args:
            character_id: The character's ID
            
        Returns:
            True if the character has any relationships, False otherwise
        """
        return len(self.get_relationships_for_character(character_id)) > 0
    
    def get_other_character_id(self, relationship: Dict[str, Any], character_id: str) -> str:
        """
        Given a relationship and a character ID, get the ID of the other character.
        
        Args:
            relationship: Relationship dictionary
            character_id: ID of one character in the relationship
            
        Returns:
            ID of the other character in the relationship
        """
        participants = relationship.get("participants", {})
        a = participants.get("a", "")
        b = participants.get("b", "")
        
        if a == character_id:
            return b
        elif b == character_id:
            return a
        else:
            return ""
    
    def format_axis_value(self, value: int, axis_name: str = "") -> str:
        """
        Format an axis value for display.
        
        Args:
            value: Numeric axis value
            axis_name: Name of the axis (optional)
            
        Returns:
            Formatted string
        """
        if value > 0:
            return f"+{value}"
        else:
            return str(value)
    
    def get_axis_label_color(self, value: int) -> str:
        """
        Get a color for displaying an axis value.
        
        Args:
            value: Numeric axis value
            
        Returns:
            Color hex code
        """
        if value > 50:
            return "#2E7D32"  # Dark green
        elif value > 20:
            return "#66BB6A"  # Light green
        elif value > -20:
            return "#757575"  # Gray
        elif value > -50:
            return "#EF5350"  # Light red
        else:
            return "#C62828"  # Dark red
