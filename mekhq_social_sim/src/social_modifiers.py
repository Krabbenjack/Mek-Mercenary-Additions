from __future__ import annotations
from typing import Tuple, Dict

from models import Character
from trait_synergy_engine import calculate_synergy
import config_loader as cfg


SAME_UNIT_BONUS = cfg.unit_same_unit_bonus()
SAME_FORCE_BONUS = cfg.unit_same_force_bonus()
DIFFERENT_FORCE_TYPE_PENALTY = cfg.unit_different_force_type_penalty()

SAME_PROFESSION_BONUS = cfg.profession_same_bonus()
DIFFERENT_PROFESSION_PENALTY = cfg.profession_different_penalty()

CHILD_ADULT_PENALTY = cfg.age_child_adult_penalty()
TEEN_ADULT_PENALTY = cfg.age_teen_adult_penalty()
CHILD_TEEN_PENALTY = cfg.age_child_teen_penalty()


def _unit_modifier(a: Character, b: Character) -> Tuple[int, str]:
    if a.unit is None or b.unit is None:
        return 0, "no TO&E info"

    if a.unit.unit_name == b.unit.unit_name:
        return SAME_UNIT_BONUS, "same unit in TO&E"
    if a.unit.force_name == b.unit.force_name:
        return SAME_FORCE_BONUS, "same force in TO&E"
    if a.unit.force_type != b.unit.force_type:
        return DIFFERENT_FORCE_TYPE_PENALTY, "different force types in TO&E"

    return 0, "different units, same force type"


def _profession_modifier(a: Character, b: Character) -> Tuple[int, str]:
    if not a.profession or not b.profession:
        return 0, "unknown profession"
    if a.profession == b.profession:
        return SAME_PROFESSION_BONUS, "same profession"
    return DIFFERENT_PROFESSION_PENALTY, "different professions"


def _age_group_modifier(a: Character, b: Character) -> Tuple[int, str]:
    ag_a = a.age_group
    ag_b = b.age_group
    if ag_a == ag_b:
        return 0, "same age group"

    pair = {ag_a, ag_b}
    if pair == {"child", "adult"} or pair == {"child", "senior"}:
        return CHILD_ADULT_PENALTY, "child / adult interaction penalty"
    if pair == {"teen", "adult"}:
        return TEEN_ADULT_PENALTY, "teen / adult interaction penalty"
    if pair == {"child", "teen"}:
        return CHILD_TEEN_PENALTY, "child / teen interaction penalty"

    return 0, "age difference but no special rule"


def combined_social_modifier(a: Character, b: Character) -> Tuple[int, Dict[str, str]]:
    """Combine all social modifiers for characters a and b."""
    total = 0
    breakdown: Dict[str, str] = {}

    umod, uinfo = _unit_modifier(a, b)
    total += umod
    breakdown["unit"] = f"{uinfo} ({umod:+d})"

    pmod, pinfo = _profession_modifier(a, b)
    total += pmod
    breakdown["profession"] = f"{pinfo} ({pmod:+d})"

    amod, ainfo = _age_group_modifier(a, b)
    total += amod
    breakdown["age_group"] = f"{ainfo} ({amod:+d})"

    tmod, tinfo = calculate_synergy(a, b)
    total += tmod

    breakdown["traits_total"] = f"personality synergy total ({tmod:+d})"
    for key, val in tinfo.items():
        breakdown[key] = val

    return total, breakdown
