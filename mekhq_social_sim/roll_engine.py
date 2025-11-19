from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Dict, Optional
import random

from models import Character, clamp_friendship, FRIENDSHIP_STEP, RIVALRY_STEP
from interaction_pool import has_points, consume_point
from social_modifiers import combined_social_modifier
import config_loader as cfg


@dataclass
class InteractionResult:
    actor: Character
    partner: Character
    total_modifier: int
    target: int
    roll: int
    success: bool
    new_friendship: int
    breakdown: Dict[str, str]
    log_lines: List[str]


def find_potential_partners(actor: Character, characters: Iterable[Character]) -> List[Character]:
    """Return a list of all potential partners.

    This is intentionally very open; you can later add filters here.
    """
    partners: List[Character] = []
    for c in characters:
        if c.id == actor.id:
            continue
        partners.append(c)
    return partners


def _pick_partner_weighted(
    actor: Character, partners: List[Character]
) -> tuple[Character, int, Dict[str, str]]:
    """Pick a partner randomly, weighted by the combined social modifier."""
    weights: List[float] = []
    mods: List[int] = []
    breakdowns: List[Dict[str, str]] = []

    for p in partners:
        mod, breakdown = combined_social_modifier(actor, p)
        weight = max(1.0, 10.0 + float(mod))  # basic weight + mod, never < 1
        weights.append(weight)
        mods.append(mod)
        breakdowns.append(breakdown)

    total_weight = sum(weights)
    r = random.uniform(0, total_weight)
    acc = 0.0
    for partner, w, mod, br in zip(partners, weights, mods, breakdowns):
        acc += w
        if r <= acc:
            return partner, mod, br

    # Fallback
    return partners[-1], mods[-1], breakdowns[-1]


def _perform_interaction_roll(
    actor: Character,
    partner: Character,
    total_mod: int,
    breakdown: Dict[str, str]
) -> InteractionResult:
    """Perform the actual dice roll and update friendship."""
    base_target = cfg.base_target()
    min_t = cfg.min_target()
    max_t = cfg.max_target()

    target = base_target - (total_mod // 2)
    target = max(min_t, min(max_t, target))

    roll = random.randint(1, 6) + random.randint(1, 6)
    success = roll >= target

    delta = FRIENDSHIP_STEP if success else -RIVALRY_STEP
    old_val = actor.friendship.get(partner.id, 0)
    new_val = clamp_friendship(old_val + delta)

    actor.friendship[partner.id] = new_val
    partner.friendship[actor.id] = new_val

    consume_point(actor)

    log_lines: List[str] = []
    log_lines.append(
        f"{actor.label()} interagiert mit {partner.label()} (Gesamtmodifikator: {total_mod:+d})."
    )
    log_lines.append(
        f"Wurf: {roll} gegen Ziel {target} → {'Erfolg' if success else 'Misserfolg'}"
    )
    log_lines.append(
        f"Freundschaft {actor.label()}–{partner.label()}: {old_val} → {new_val} ({delta:+d})."
    )
    log_lines.append("Details der Modifikatoren:")
    for key, text in breakdown.items():
        log_lines.append(f" - {key}: {text}")

    return InteractionResult(
        actor=actor,
        partner=partner,
        total_modifier=total_mod,
        target=target,
        roll=roll,
        success=success,
        new_friendship=new_val,
        breakdown=breakdown,
        log_lines=log_lines,
    )


def perform_random_interaction(
    actor: Character,
    characters: Iterable[Character],
) -> Optional[InteractionResult]:
    """Perform a random social interaction.

    - Choose a partner (weighted by social modifier)
    - Roll 2d6 vs. a target modified by the social situation
    - Adjust friendship
    - Consume one interaction point
    """

    if not has_points(actor):
        return None

    partners = find_potential_partners(actor, characters)
    if not partners:
        return None

    partner, total_mod, breakdown = _pick_partner_weighted(actor, partners)
    
    return _perform_interaction_roll(actor, partner, total_mod, breakdown)


def perform_manual_interaction(
    actor: Character,
    partner: Character,
) -> Optional[InteractionResult]:
    """Perform a manual social interaction with a specific partner.

    - Use the specified partner
    - Roll 2d6 vs. a target modified by the social situation
    - Adjust friendship
    - Consume one interaction point
    """

    if not has_points(actor):
        return None

    total_mod, breakdown = combined_social_modifier(actor, partner)
    
    return _perform_interaction_roll(actor, partner, total_mod, breakdown)
