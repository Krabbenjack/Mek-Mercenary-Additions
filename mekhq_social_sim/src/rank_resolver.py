"""
Rank Resolution Module

Converts numeric rank IDs to human-readable rank names using MekHQ rank systems.
Supports fallback behavior for unknown ranks or missing rank systems.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Path to rank systems configuration
RANK_SYSTEMS_PATH = Path(__file__).resolve().parents[1] / "config" / "rank_systems.json"


class RankResolver:
    """
    Resolves numeric rank IDs to human-readable rank names.
    
    Loads rank systems from config/rank_systems.json and provides
    lookup functionality with graceful fallbacks.
    """
    
    def __init__(self):
        self.rank_systems: Dict[str, Any] = {}
        self.current_rank_system: Optional[str] = None
        self._load_rank_systems()
    
    def _load_rank_systems(self) -> None:
        """Load rank systems from JSON configuration file."""
        if not RANK_SYSTEMS_PATH.exists():
            print(f"⚠️  Warning: Rank systems file not found at {RANK_SYSTEMS_PATH}")
            return
        
        try:
            with open(RANK_SYSTEMS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rank_systems = data.get('rank_systems', {})
            print(f"✅ Loaded {len(self.rank_systems)} rank systems")
        except Exception as e:
            print(f"⚠️  Warning: Failed to load rank systems: {e}")
    
    def set_rank_system(self, rank_system_code: Optional[str]) -> None:
        """
        Set the active rank system for lookups.
        
        Args:
            rank_system_code: Rank system code (e.g., "SLDF", "AFFS")
        """
        self.current_rank_system = rank_system_code
        if rank_system_code and rank_system_code in self.rank_systems:
            system_name = self.rank_systems[rank_system_code].get('name', rank_system_code)
            print(f"✅ Active rank system set to: {system_name} ({rank_system_code})")
        elif rank_system_code:
            print(f"⚠️  Warning: Unknown rank system '{rank_system_code}' - using fallback")
    
    def resolve_rank_name(
        self,
        rank_id: Optional[int],
        rank_system_code: Optional[str] = None,
        profession_index: int = 0
    ) -> str:
        """
        Convert a numeric rank ID to a human-readable rank name.
        
        Args:
            rank_id: Numeric rank ID from personnel data
            rank_system_code: Optional rank system code (uses current if None)
            profession_index: Index into rankNames array (default 0 for general rank)
        
        Returns:
            Human-readable rank name, or fallback string if not found
        """
        # Use current rank system if not specified
        if rank_system_code is None:
            rank_system_code = self.current_rank_system
        
        # Fallback if no rank system available
        if not rank_system_code:
            if rank_id is not None:
                return f"Rank {rank_id}"
            return "No Rank"
        
        # Fallback if rank ID is None
        if rank_id is None:
            return "No Rank"
        
        # Convert to int safely
        try:
            rank_id = int(rank_id)
        except (ValueError, TypeError):
            return f"Unknown Rank ({rank_id})"
        
        # Look up rank system
        rank_system = self.rank_systems.get(rank_system_code)
        if not rank_system:
            return f"Rank {rank_id} ({rank_system_code})"
        
        # Find rank entry by ID
        ranks = rank_system.get('ranks', [])
        rank_entry = None
        for r in ranks:
            if r.get('id') == rank_id:
                rank_entry = r
                break
        
        if not rank_entry:
            return f"Unknown Rank {rank_id} ({rank_system_code})"
        
        # Get rank names array
        rank_names = rank_entry.get('rankNames', [])
        
        # Get name at profession_index, default to first name if index out of range
        if 0 <= profession_index < len(rank_names):
            name = rank_names[profession_index]
        elif len(rank_names) > 0:
            name = rank_names[0]
        else:
            return f"Rank {rank_id} ({rank_system_code})"
        
        # Check for placeholder names (-, --MW, etc.)
        if not name or name == "-" or name.startswith("--"):
            # Use the first non-placeholder name if available
            for n in rank_names:
                if n and n != "-" and not n.startswith("--"):
                    name = n
                    break
            else:
                # All names are placeholders, show rank ID
                return f"Rank {rank_id}"
        
        return name
    
    def get_rank_system_name(self, rank_system_code: str) -> str:
        """
        Get the full name of a rank system from its code.
        
        Args:
            rank_system_code: Rank system code (e.g., "SLDF")
        
        Returns:
            Full name of the rank system, or the code if not found
        """
        rank_system = self.rank_systems.get(rank_system_code)
        if rank_system:
            return rank_system.get('name', rank_system_code)
        return rank_system_code


# Global rank resolver instance
_rank_resolver: Optional[RankResolver] = None


def get_rank_resolver() -> RankResolver:
    """Get the global rank resolver instance (singleton pattern)."""
    global _rank_resolver
    if _rank_resolver is None:
        _rank_resolver = RankResolver()
    return _rank_resolver


def resolve_rank_name(
    rank_id: Optional[int],
    rank_system_code: Optional[str] = None,
    profession_index: int = 0
) -> str:
    """
    Convenience function to resolve a rank name using the global resolver.
    
    Args:
        rank_id: Numeric rank ID from personnel data
        rank_system_code: Optional rank system code (uses current if None)
        profession_index: Index into rankNames array (default 0)
    
    Returns:
        Human-readable rank name
    """
    resolver = get_rank_resolver()
    return resolver.resolve_rank_name(rank_id, rank_system_code, profession_index)


def set_current_rank_system(rank_system_code: Optional[str]) -> None:
    """
    Set the current rank system for the global resolver.
    
    Args:
        rank_system_code: Rank system code (e.g., "SLDF", "AFFS")
    """
    resolver = get_rank_resolver()
    resolver.set_rank_system(rank_system_code)
