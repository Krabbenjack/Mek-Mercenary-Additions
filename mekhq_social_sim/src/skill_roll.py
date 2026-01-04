# skill_roll.py
# A Time of War–style skill & attribute resolution
# Designed for event-based systems (Mek-Mercenary-Additions)
# -----------------------------------------------------------

from dataclasses import dataclass
import random
from typing import Optional


# -----------------------------------------------------------
# Result Object
# -----------------------------------------------------------

@dataclass(frozen=True)
class SkillRollResult:
    roll: int
    total: int
    target_number: int
    success: bool
    margin: int
    fumble: bool = False
    stunning_success: bool = False
    notes: Optional[str] = None


# -----------------------------------------------------------
# Dice Helpers
# -----------------------------------------------------------

def roll_2d6() -> int:
    return random.randint(1, 6) + random.randint(1, 6)


def explode_d6(max_total: int = 30, current: int = 12) -> int:
    total = current
    while total < max_total:
        die = random.randint(1, 6)
        total += die
        if die < 6:
            break
    return total


# -----------------------------------------------------------
# Core Resolver
# -----------------------------------------------------------

def resolve_skill_check(
    *,
    target_number: int,

    # trained skill
    trained: bool = True,
    skill_level: int = 0,
    attribute_link_mod: int = 0,

    # untrained / attribute check
    attribute_score: int = 0,

    # modifiers
    difficulty_mod: int = 0,
    situational_mod: int = 0,

    # edge usage
    edge_pre: int = 0,     # +2 per point, before roll
    edge_post: int = 0,    # +1 per point, after roll

    # deterministic testing / scripted events
    fixed_roll: Optional[int] = None,
) -> SkillRollResult:
    """
    Resolves a single AToW-style skill or attribute check.

    Rules enforced:
    - 2D6 core roll
    - Natural 2 = fumble (automatic failure)
    - Natural 12 = stunning success (exploding)
    - Edge (pre): +2 per point before modifiers
    - Edge (post): +1 per point after modifiers
    """

    # -------------------------------------------------------
    # Roll dice
    # -------------------------------------------------------

    base_roll = fixed_roll if fixed_roll is not None else roll_2d6()

    # -------------------------------------------------------
    # FUMBLE
    # -------------------------------------------------------

    if base_roll == 2:
        return SkillRollResult(
            roll=base_roll,
            total=base_roll,
            target_number=target_number,
            success=False,
            margin=target_number - base_roll,
            fumble=True,
            stunning_success=False,
            notes="FUMBLE: natural 2"
        )

    # -------------------------------------------------------
    # STUNNING SUCCESS
    # -------------------------------------------------------

    stunning = False
    roll_value = base_roll

    if base_roll == 12:
        roll_value = explode_d6()
        stunning = True

    # -------------------------------------------------------
    # Apply modifiers
    # -------------------------------------------------------

    total = roll_value

    # Edge before roll
    if edge_pre > 0:
        total += edge_pre * 2

    # Skill vs Attribute
    if trained:
        total += skill_level
        total += attribute_link_mod
    else:
        total += attribute_score

    # Situational
    total += difficulty_mod
    total += situational_mod

    # Edge after roll
    if edge_post > 0:
        total += edge_post

    # -------------------------------------------------------
    # Outcome
    # -------------------------------------------------------

    success = total >= target_number
    margin = total - target_number

    return SkillRollResult(
        roll=roll_value,
        total=total,
        target_number=target_number,
        success=success,
        margin=margin,
        fumble=False,
        stunning_success=stunning,
        notes="STUNNING SUCCESS" if stunning else None
    )


# -----------------------------------------------------------
# Convenience Wrapper for Difficulty Labels
# -----------------------------------------------------------

DIFFICULTY_MODIFIERS = {
    "very_easy": 3,
    "easy": 1,
    "average": 0,
    "hard": -1,
    "very_hard": -3,
    "extreme": -5,
}


def resolve_with_difficulty_label(**kwargs) -> SkillRollResult:
    difficulty = kwargs.pop("difficulty", "average")
    kwargs["difficulty_mod"] = DIFFICULTY_MODIFIERS.get(difficulty, 0)
    return resolve_skill_check(**kwargs)
