from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"


def _load_json(name: str) -> Dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # On any parse error, fall back to empty dict so defaults are used.
        return {}


CORE_CONFIG: Dict[str, Any] = _load_json("core_config.json")
MODIFIERS_CONFIG: Dict[str, Any] = _load_json("modifiers_config.json")
TRAITS_CONFIG: Dict[str, Any] = _load_json("traits_config.json")


def _get(cfg: Dict[str, Any], keys: List[str], default: Any) -> Any:
    cur: Any = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


# --- Core / friendship / interaction ---

def base_interaction_points() -> int:
    return int(_get(CORE_CONFIG, ["base_interaction_points"], 3))


def friendship_step_positive() -> int:
    return int(_get(CORE_CONFIG, ["friendship", "step_positive"], 5))


def friendship_step_negative() -> int:
    return int(_get(CORE_CONFIG, ["friendship", "step_negative"], 5))


def friendship_min() -> int:
    return int(_get(CORE_CONFIG, ["friendship", "min"], -100))


def friendship_max() -> int:
    return int(_get(CORE_CONFIG, ["friendship", "max"], 100))


def base_target() -> int:
    return int(_get(CORE_CONFIG, ["interaction", "base_target"], 7))


def min_target() -> int:
    return int(_get(CORE_CONFIG, ["interaction", "min_target"], 3))


def max_target() -> int:
    return int(_get(CORE_CONFIG, ["interaction", "max_target"], 11))


# --- Social modifiers ---

def unit_same_unit_bonus() -> int:
    return int(_get(MODIFIERS_CONFIG, ["unit", "same_unit_bonus"], 4))


def unit_same_force_bonus() -> int:
    return int(_get(MODIFIERS_CONFIG, ["unit", "same_force_bonus"], 2))


def unit_different_force_type_penalty() -> int:
    return int(_get(MODIFIERS_CONFIG, ["unit", "different_force_type_penalty"], -3))


def profession_same_bonus() -> int:
    return int(_get(MODIFIERS_CONFIG, ["profession", "same_profession_bonus"], 3))


def profession_different_penalty() -> int:
    return int(_get(MODIFIERS_CONFIG, ["profession", "different_profession_penalty"], -2))


def age_child_adult_penalty() -> int:
    return int(_get(MODIFIERS_CONFIG, ["age", "child_adult_penalty"], -8))


def age_teen_adult_penalty() -> int:
    return int(_get(MODIFIERS_CONFIG, ["age", "teen_adult_penalty"], -4))


def age_child_teen_penalty() -> int:
    return int(_get(MODIFIERS_CONFIG, ["age", "child_teen_penalty"], -4))


# --- Traits ---

def trait_names() -> list[str]:
    default = [
        "aggression",
        "greed",
        "courage",
        "honor",
        "gregariousness",
        "loyalty",
        "ambition",
    ]
    names = TRAITS_CONFIG.get("traits")
    if isinstance(names, list) and names:
        return [str(n) for n in names]
    return default
