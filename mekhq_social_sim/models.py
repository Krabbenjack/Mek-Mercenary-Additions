from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

import config_loader as cfg


@dataclass
class UnitAssignment:
    force_name: str
    unit_name: str
    force_type: str  # e.g. "Combat", "Support", "Convoy", "Security"


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
