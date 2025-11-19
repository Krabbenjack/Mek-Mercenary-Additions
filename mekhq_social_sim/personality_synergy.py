from __future__ import annotations
from typing import Dict, Tuple

from models import Character
import config_loader as cfg


TRAITS = cfg.trait_names()


def _trait_value(char: Character, trait: str) -> int | None:
    value = char.traits.get(trait)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def trait_synergy_modifier(a: Character, b: Character) -> Tuple[int, Dict[str, str]]:
    """Compute a generic personality synergy modifier between two characters.

    This implementation is intentionally generic so that the trait list can
    be configured via traits_config.json. The idea:

    - For each trait we look at the absolute difference in values (0–100).
    - Very similar values (delta <= 10) give a small bonus.
    - Moderate similarity (delta <= 25) gives a tiny bonus.
    - Large differences (delta >= 50) give a malus.

    You can later replace this function with something more detailed if needed.
    """
    total = 0
    breakdown: Dict[str, str] = {}

    for trait in TRAITS:
        va = _trait_value(a, trait)
        vb = _trait_value(b, trait)
        key = f"trait:{trait}"

        if va is None or vb is None:
            breakdown[key] = "no data (0)"
            continue

        delta = abs(va - vb)
        mod = 0
        reason = ""

        if delta <= 10:
            mod = 2
            reason = "very similar"
        elif delta <= 25:
            mod = 1
            reason = "somewhat similar"
        elif delta >= 50:
            mod = -2
            reason = "very different"
        else:
            mod = 0
            reason = "neutral difference"

        total += mod
        breakdown[key] = f"{reason} (Δ={delta}, {mod:+d})"

    return total, breakdown
