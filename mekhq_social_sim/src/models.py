from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, List

import config_loader as cfg
from datetime import date


@dataclass
class UnitAssignment:
    """TO&E assignment information for a character (MekHQ 5.10)."""
    force_name: str
    unit_name: str
    force_type: str  # e.g. "Combat", "Support", "Transport", "Security", "Salvage"
    formation_level: Optional[str] = None  # e.g. "Company", "Lance", "Team"
    preferred_role: Optional[str] = None   # e.g. "FRONTLINE" (new in 5.10)
    crew_role: Optional[str] = None        # e.g. "driver", "gunner", "tech", "crew"


@dataclass
class PortraitInfo:
    """Portrait information from MekHQ JSON export."""
    category: Optional[str] = None
    filename: Optional[str] = None


@dataclass
class Character:
    id: str
    name: str
    callsign: Optional[str]
    age: int
    profession: Optional[str]
    traits: Dict[str, int] = field(default_factory=dict)
    friendship: Dict[str, int] = field(default_factory=dict)
    daily_interaction_points: int = 0
    unit: Optional[UnitAssignment] = None

    # NEW: store birthday (optional). JSON uses yyyy-mm-dd.
    birthday: Optional[date] = None

    # Portrait info from JSON
    portrait: Optional[PortraitInfo] = None

    # Rank from JSON
    rank: Optional[str] = None
    
    # Personality quirks (list of quirk keys)
    quirks: List[str] = field(default_factory=list)

    def label(self) -> str:
        """Short label for GUI/logs."""
        base = self.callsign or self.name
        if self.profession:
            return f"{base} ({self.profession})"
        return base

    @property
    def age_group(self) -> str:
        """Return a coarse age group for social modifiers."""
        if self.age < 16:
            return "child"
        if self.age < 21:
            return "teen"
        if self.age < 60:
            return "adult"
        return "senior"


# Configurable defaults for relationship development.
FRIENDSHIP_STEP = cfg.friendship_step_positive()
RIVALRY_STEP = cfg.friendship_step_negative()
FRIENDSHIP_MIN = cfg.friendship_min()
FRIENDSHIP_MAX = cfg.friendship_max()


def clamp_friendship(value: int) -> int:
    """Clamp friendship/rivalry scores into the allowed range."""
    return max(FRIENDSHIP_MIN, min(FRIENDSHIP_MAX, value))
