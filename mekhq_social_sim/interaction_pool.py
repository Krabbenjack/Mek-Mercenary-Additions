from __future__ import annotations
from typing import Dict

from models import Character
import config_loader as cfg


BASE_INTERACTION_POINTS: int = cfg.base_interaction_points()


def reset_daily_pools(characters: Dict[str, Character]) -> None:
    """Reset daily interaction points for all characters."""
    for char in characters.values():
        char.daily_interaction_points = BASE_INTERACTION_POINTS


def has_points(char: Character) -> bool:
    return char.daily_interaction_points > 0


def consume_point(char: Character) -> None:
    if char.daily_interaction_points > 0:
        char.daily_interaction_points -= 1
