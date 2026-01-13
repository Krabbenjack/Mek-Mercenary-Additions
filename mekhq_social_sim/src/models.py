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

    # Rank from JSON (numeric ID)
    rank: Optional[str] = None
    
    # Rank name (human-readable, resolved from rank system)
    rank_name: Optional[str] = None
    
    # Personality quirks (list of quirk keys)
    quirks: List[str] = field(default_factory=list)
    
    # Secondary profession (new for character sheet UI)
    secondary_profession: Optional[str] = None
    
    # Attributes (e.g., STR, BOD, RFL, DEX, INT, WIL, CHA, EDG)
    attributes: Dict[str, int] = field(default_factory=dict)
    
    # Skills (skill name -> level)
    skills: Dict[str, int] = field(default_factory=dict)
    
    # Special Abilities / SPAs (name -> description)
    abilities: Dict[str, str] = field(default_factory=dict)
    
    # Status field from MekHQ (e.g., "ACTIVE", "CAMP_FOLLOWER", etc.)
    status: Optional[str] = None
    
    # Event-driven character state (Phase 3)
    # These values are modified by event outcomes and displayed read-only in UI
    xp: int = 0  # Experience points (numeric, no upper limit)
    confidence: int = 50  # Operational confidence (0-100)
    fatigue: int = 0  # Fatigue level (0-100)
    reputation_pool: int = 50  # Social reputation (0-100)

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
