"""
Relationship State Query Interface

This module provides READ-ONLY access to relationship state for the Event System.
The Event System uses this to:
- Gate interactions (e.g., suppress flirt if state is awkward)
- Weight interaction probabilities (e.g., reduce bonding if CONFLICT_ACTIVE)
- Make context-aware decisions

CRITICAL DESIGN RULES:
- NEVER mutates relationship state
- NEVER emits triggers
- NEVER implements acceptance logic
- ONLY provides read access to existing state
- Event System remains MASTER of event selection

This is the ONLY allowed backward flow: Relationship → Event (read-only)
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sys

from relationship_engine import RelationshipEngine, RelationshipState, get_relationship_engine


class RelationshipStateQuery:
    """
    Provides read-only access to relationship state for external systems.
    
    This class is designed to be used by the Event System to query relationship
    state for gating and weighting purposes.
    """
    
    def __init__(self, engine: Optional[RelationshipEngine] = None):
        """
        Initialize the state query interface.
        
        Args:
            engine: RelationshipEngine instance. If None, uses global instance.
        """
        self.engine = engine if engine is not None else get_relationship_engine()
    
    # -------------------------------------------------------------------------
    # Basic State Queries
    # -------------------------------------------------------------------------
    
    def get_axis_value(self, char_a_id: str, char_b_id: str, axis_name: str) -> int:
        """
        Get the value of a relationship axis.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            axis_name: Name of axis (e.g., "friendship", "romance", "respect")
            
        Returns:
            Axis value (integer), or 0 if relationship doesn't exist
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return 0
        return rel.get_axis(axis_name)
    
    def has_flag(self, char_a_id: str, char_b_id: str, flag_name: str) -> bool:
        """
        Check if a relationship has a specific flag.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            flag_name: Name of flag (e.g., "CONFLICT_ACTIVE", "ESTRANGED")
            
        Returns:
            True if flag is active, False otherwise
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return False
        return rel.has_flag(flag_name)
    
    def has_sentiment(self, char_a_id: str, char_b_id: str, sentiment_name: str) -> bool:
        """
        Check if a relationship has a specific sentiment.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            sentiment_name: Name of sentiment (e.g., "HURT", "BETRAYED")
            
        Returns:
            True if sentiment is active, False otherwise
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return False
        return rel.has_sentiment(sentiment_name)
    
    def get_sentiment_strength(self, char_a_id: str, char_b_id: str, sentiment_name: str) -> int:
        """
        Get the strength of a sentiment.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            sentiment_name: Name of sentiment
            
        Returns:
            Sentiment strength (integer), or 0 if not present
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return 0
        return rel.get_sentiment_strength(sentiment_name)
    
    def has_role(self, char_a_id: str, char_b_id: str, role_name: str) -> bool:
        """
        Check if a relationship has a specific role.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            role_name: Name of role (e.g., "family", "spouse")
            
        Returns:
            True if role is assigned, False otherwise
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return False
        return rel.has_role(role_name)
    
    # -------------------------------------------------------------------------
    # Interaction Gating Queries
    # -------------------------------------------------------------------------
    
    def should_suppress_romantic_interaction(self, char_a_id: str, char_b_id: str) -> bool:
        """
        Check if romantic interactions should be suppressed.
        
        Common reasons to suppress:
        - CONFLICT_ACTIVE flag
        - ESTRANGED flag
        - BETRAYED sentiment with high strength
        - Romance axis is deeply negative
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            
        Returns:
            True if romantic interactions should be suppressed
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return False
        
        # Check for blocking flags
        if rel.has_flag("CONFLICT_ACTIVE") or rel.has_flag("ESTRANGED"):
            return True
        
        # Check for strong negative sentiment
        if rel.get_sentiment_strength("BETRAYED") >= 3:
            return True
        
        # Check for deeply negative romance
        if rel.get_axis("romance") <= -30:
            return True
        
        return False
    
    def should_suppress_friendly_interaction(self, char_a_id: str, char_b_id: str) -> bool:
        """
        Check if friendly interactions should be suppressed.
        
        Common reasons to suppress:
        - ESTRANGED flag
        - Very negative friendship
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            
        Returns:
            True if friendly interactions should be suppressed
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return False
        
        if rel.has_flag("ESTRANGED"):
            return True
        
        if rel.get_axis("friendship") <= -50:
            return True
        
        return False
    
    def is_relationship_awkward(self, char_a_id: str, char_b_id: str) -> bool:
        """
        Check if a relationship is in an awkward state.
        
        Awkward states might include:
        - Recent romantic rejection (HURT + JEALOUS)
        - Unresolved conflict
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            
        Returns:
            True if relationship is awkward
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return False
        
        # Recent romantic rejection
        if rel.has_sentiment("HURT") and rel.has_flag("JEALOUS"):
            return True
        
        # Active conflict
        if rel.has_flag("CONFLICT_ACTIVE"):
            return True
        
        return False
    
    # -------------------------------------------------------------------------
    # Interaction Weighting Queries
    # -------------------------------------------------------------------------
    
    def get_interaction_weight_modifier(
        self, 
        char_a_id: str, 
        char_b_id: str, 
        interaction_type: str
    ) -> float:
        """
        Get a weight modifier for interaction selection.
        
        This is used by the Event System to adjust interaction probabilities
        based on relationship state.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            interaction_type: Type of interaction (e.g., "romantic", "friendly", "professional")
            
        Returns:
            Multiplier for interaction weight (0.0 to 2.0)
            - 1.0 = neutral (no change)
            - <1.0 = reduced probability
            - >1.0 = increased probability
            - 0.0 = completely suppress
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        
        if interaction_type == "romantic":
            if self.should_suppress_romantic_interaction(char_a_id, char_b_id):
                return 0.0
            
            if rel is None:
                return 0.5  # Reduced for unknown relationships
            
            romance = rel.get_axis("romance")
            if romance > 30:
                return 1.5  # Increase probability for high romance
            elif romance > 10:
                return 1.2
            elif romance < -10:
                return 0.3  # Reduce but don't eliminate
            else:
                return 1.0
        
        elif interaction_type == "friendly":
            if self.should_suppress_friendly_interaction(char_a_id, char_b_id):
                return 0.0
            
            if rel is None:
                return 1.0  # Neutral for unknown relationships
            
            friendship = rel.get_axis("friendship")
            if friendship > 30:
                return 1.3
            elif friendship < -30:
                return 0.5
            else:
                return 1.0
        
        elif interaction_type == "professional":
            if rel is None:
                return 1.0
            
            respect = rel.get_axis("respect")
            if respect > 30:
                return 1.2
            elif respect < -30:
                return 0.7
            else:
                return 1.0
        
        # Default: no modification
        return 1.0
    
    def get_bonding_weight_modifier(self, char_a_id: str, char_b_id: str) -> float:
        """
        Get a weight modifier for bonding interactions (team building, etc.).
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            
        Returns:
            Multiplier for bonding interaction weight
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return 1.0
        
        # Reduce bonding opportunities if conflict is active
        if rel.has_flag("CONFLICT_ACTIVE"):
            return 0.3
        
        # Reduce if friendship is negative
        friendship = rel.get_axis("friendship")
        if friendship < -20:
            return 0.5
        elif friendship > 30:
            return 1.2  # Already bonded, maintain it
        
        return 1.0
    
    # -------------------------------------------------------------------------
    # Bulk Queries
    # -------------------------------------------------------------------------
    
    def get_relationship_summary(self, char_a_id: str, char_b_id: str) -> Dict[str, Any]:
        """
        Get a summary of relationship state.
        
        Args:
            char_a_id: ID of first character
            char_b_id: ID of second character
            
        Returns:
            Dictionary with relationship summary, or empty dict if no relationship
        """
        rel = self.engine.get_relationship_state(char_a_id, char_b_id)
        if rel is None:
            return {}
        
        return {
            "axes": rel.axes.copy(),
            "sentiments": rel.sentiments.copy(),
            "flags": list(rel.flags.keys()),
            "roles": rel.roles.copy(),
            "is_awkward": self.is_relationship_awkward(char_a_id, char_b_id),
            "suppress_romantic": self.should_suppress_romantic_interaction(char_a_id, char_b_id),
            "suppress_friendly": self.should_suppress_friendly_interaction(char_a_id, char_b_id)
        }
    
    def get_all_relationships_for_character(self, char_id: str) -> List[Dict[str, Any]]:
        """
        Get all relationships involving a specific character.
        
        Args:
            char_id: ID of character
            
        Returns:
            List of relationship summaries
        """
        results = []
        for rel in self.engine.get_all_relationships():
            if char_id in rel.participants:
                other_id = rel.participants[0] if rel.participants[1] == char_id else rel.participants[1]
                summary = self.get_relationship_summary(char_id, other_id)
                summary["other_character_id"] = other_id
                results.append(summary)
        
        return results


# Global singleton instance
_global_state_query: Optional[RelationshipStateQuery] = None


def get_state_query() -> RelationshipStateQuery:
    """
    Get the global relationship state query instance.
    
    Returns:
        RelationshipStateQuery instance
    """
    global _global_state_query
    if _global_state_query is None:
        _global_state_query = RelationshipStateQuery()
    return _global_state_query


def initialize_state_query(engine: Optional[RelationshipEngine] = None) -> RelationshipStateQuery:
    """
    Initialize the global relationship state query with a specific engine.
    
    Args:
        engine: RelationshipEngine instance
        
    Returns:
        Initialized RelationshipStateQuery instance
    """
    global _global_state_query
    _global_state_query = RelationshipStateQuery(engine)
    return _global_state_query
