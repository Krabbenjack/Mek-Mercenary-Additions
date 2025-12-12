"""
Data-Driven Trait Synergy Engine

Replaces the legacy personality_synergy.py system with a fully JSON-driven
approach based on explicit trait and quirk rules.

This module:
1. Resolves numeric trait indices to Category:KEY format using mekhq_trait_enums.json
2. Maps quirks to QuirkGroups using quirk_group_rules.json
3. Evaluates synergy rules from synergy_*.json files
4. Converts tokens (--,-,0,+,++) to numeric weights
5. Produces total modifier and human-readable breakdown
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json

from models import Character


# Global cache for JSON configuration data
_config_cache: Dict[str, Any] = {}


def _load_json(filename: str) -> Any:
    """Load and cache a JSON configuration file."""
    if filename not in _config_cache:
        config_dir = Path(__file__).parent.parent / "config"
        file_path = config_dir / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            _config_cache[filename] = json.load(f)
    return _config_cache[filename]


def _get_trait_enums() -> Dict[str, List[Dict[str, Any]]]:
    """Load mekhq_trait_enums.json."""
    return _load_json("mekhq_trait_enums.json")


def _get_quirk_enums() -> Dict[str, List[Dict[str, Any]]]:
    """Load mekhq_quirk_enums.json."""
    return _load_json("mekhq_quirk_enums.json")


def _get_quirk_group_rules() -> Dict[str, Any]:
    """Load quirk_group_rules.json."""
    return _load_json("quirk_group_rules.json")


def _get_synergy_scale() -> Dict[str, Any]:
    """Load synergy_scale.json."""
    return _load_json("synergy_scale.json")


def _get_synergy_rules(category: str) -> Dict[str, Any]:
    """Load synergy rules for a trait category (aggression, ambition, greed, social)."""
    filename = f"synergy_{category.lower()}.json"
    return _load_json(filename)


def _get_quirk_synergy_rules() -> Dict[str, Any]:
    """Load synergy_quirk.json."""
    return _load_json("synergy_quirk.json")


def resolve_trait_to_enum(category: str, value: int | str) -> Optional[str]:
    """
    Resolve a trait value to its canonical enum form: Category:KEY
    
    Args:
        category: Trait category (e.g., "Aggression", "Ambition", "Greed", "Social", "Reasoning")
        value: Either a numeric code or a string key
    
    Returns:
        Canonical form "Category:KEY" or None if not found
    """
    trait_enums = _get_trait_enums()
    
    if category not in trait_enums:
        return None
    
    category_traits = trait_enums[category]
    
    # If value is already a string, try to match by key
    if isinstance(value, str):
        for trait_def in category_traits:
            if trait_def.get("key", "").upper() == value.upper():
                return f"{category}:{trait_def['key']}"
        return None
    
    # If value is numeric, match by code
    for trait_def in category_traits:
        if trait_def.get("code") == value:
            return f"{category}:{trait_def['key']}"
    
    return None


def resolve_quirk_groups(quirk_keys: List[str]) -> List[str]:
    """
    Resolve a list of quirk keys to their QuirkGroup assignments.
    
    Args:
        quirk_keys: List of quirk keys (e.g., ["BOOKWORM", "PERFECTIONIST"])
    
    Returns:
        List of QuirkGroup names (e.g., ["QUIET_HOBBY", "NEUROTIC"])
    """
    quirk_group_rules = _get_quirk_group_rules()
    groups = quirk_group_rules.get("groups", [])
    
    assigned_groups = []
    
    for group_def in groups:
        group_name = group_def.get("group")
        match_rules = group_def.get("match", {})
        
        # Check suffix match
        if "suffix" in match_rules:
            suffix = match_rules["suffix"]
            for quirk_key in quirk_keys:
                if quirk_key.endswith(suffix):
                    if group_name not in assigned_groups:
                        assigned_groups.append(group_name)
                    break
        
        # Check any_of match
        if "any_of" in match_rules:
            any_of_list = match_rules["any_of"]
            for quirk_key in quirk_keys:
                if quirk_key in any_of_list:
                    if group_name not in assigned_groups:
                        assigned_groups.append(group_name)
                    break
    
    return assigned_groups


def resolve_quirks_from_character(character: Character) -> Tuple[List[str], List[str]]:
    """
    Resolve character quirks to both quirk keys and quirk groups.
    
    Args:
        character: Character object
    
    Returns:
        Tuple of (quirk_keys, quirk_groups)
    """
    quirk_keys = character.quirks if hasattr(character, 'quirks') else []
    quirk_groups = resolve_quirk_groups(quirk_keys)
    return quirk_keys, quirk_groups


def get_token_weight(token: str) -> int:
    """
    Convert a synergy token to its numeric weight.
    
    Args:
        token: One of "--", "-", "0", "+", "++"
    
    Returns:
        Numeric weight (default 0 for invalid tokens)
    """
    scale = _get_synergy_scale()
    tokens = scale.get("tokens", {})
    defaults = scale.get("defaults", {})
    
    # Get weight from tokens, or use default
    token_info = tokens.get(token, {})
    if isinstance(token_info, dict):
        return token_info.get("weight", 0)
    
    # Fallback to default
    default_token = defaults.get("missing_rule_value", "0")
    default_token_info = tokens.get(default_token, {})
    if isinstance(default_token_info, dict):
        return default_token_info.get("weight", 0)
    
    return 0


def lookup_trait_synergy(trait_a: str, trait_b: str) -> Tuple[int, str]:
    """
    Look up synergy between two traits.
    
    Args:
        trait_a: First trait in Category:KEY format
        trait_b: Second trait in Category:KEY format
    
    Returns:
        Tuple of (weight, description)
    """
    if not trait_a or not trait_b:
        return 0, "missing trait"
    
    # Parse trait_a to get category and key
    if ":" not in trait_a:
        return 0, "invalid trait format"
    
    category_a, key_a = trait_a.split(":", 1)
    
    # Load synergy rules for trait_a's category
    try:
        synergy_rules = _get_synergy_rules(category_a)
    except (FileNotFoundError, KeyError):
        return 0, "no synergy rules for category"
    
    # Look up trait_a's rules
    trait_rules = synergy_rules.get(key_a, {})
    
    # Look up interaction with trait_b
    token = trait_rules.get(trait_b)
    
    if token is None:
        return 0, "no rule"
    
    weight = get_token_weight(token)
    scale = _get_synergy_scale()
    token_info = scale.get("tokens", {}).get(token, {})
    label = token_info.get("label", token)
    
    return weight, f"{label} ({token})"


def lookup_quirk_synergy(quirk_group: str, trait: str) -> Tuple[int, str]:
    """
    Look up synergy between a quirk group and a trait.
    
    Args:
        quirk_group: QuirkGroup name (e.g., "PHOBIA")
        trait: Trait in Category:KEY format
    
    Returns:
        Tuple of (weight, description)
    """
    quirk_rules = _get_quirk_synergy_rules()
    
    # Format quirk group key
    quirk_key = f"QuirkGroup:{quirk_group}"
    
    # Look up quirk group rules
    group_rules = quirk_rules.get(quirk_key, {})
    
    # Look up interaction with trait
    token = group_rules.get(trait)
    
    if token is None:
        return 0, "no rule"
    
    weight = get_token_weight(token)
    scale = _get_synergy_scale()
    token_info = scale.get("tokens", {}).get(token, {})
    label = token_info.get("label", token)
    
    return weight, f"{label} ({token})"


def get_character_traits_as_enums(character: Character) -> Dict[str, str]:
    """
    Get all character traits in Category:KEY enum format.
    
    Args:
        character: Character object with traits dict
    
    Returns:
        Dict mapping category to "Category:KEY" enum string
    """
    trait_enums = {}
    
    # Map old trait names to enum categories
    trait_category_map = {
        "aggression": "Aggression",
        "ambition": "Ambition",
        "greed": "Greed",
        "gregariousness": "Social",
        "social": "Social",
    }
    
    for trait_name, trait_value in character.traits.items():
        category = trait_category_map.get(trait_name.lower())
        if category:
            # Resolve numeric value to enum
            enum_str = resolve_trait_to_enum(category, trait_value)
            if enum_str:
                trait_enums[category] = enum_str
    
    return trait_enums


def calculate_synergy(char_a: Character, char_b: Character) -> Tuple[int, Dict[str, str]]:
    """
    Calculate total personality synergy between two characters using JSON rules.
    
    This is the main entry point that replaces personality_synergy.trait_synergy_modifier().
    
    Args:
        char_a: First character
        char_b: Second character
    
    Returns:
        Tuple of (total_modifier, breakdown_dict)
    """
    total = 0
    breakdown: Dict[str, str] = {}
    
    # Get trait enums for both characters
    traits_a = get_character_traits_as_enums(char_a)
    traits_b = get_character_traits_as_enums(char_b)
    
    # Get quirks for both characters
    quirks_a_keys, quirks_a_groups = resolve_quirks_from_character(char_a)
    quirks_b_keys, quirks_b_groups = resolve_quirks_from_character(char_b)
    
    # Evaluate all trait-to-trait synergies
    for category_a, enum_a in traits_a.items():
        for category_b, enum_b in traits_b.items():
            weight, desc = lookup_trait_synergy(enum_a, enum_b)
            if weight != 0:
                key = f"trait:{enum_a}×{enum_b}"
                breakdown[key] = f"{desc} ({weight:+d})"
                total += weight
    
    # Evaluate quirk group to trait synergies for char_a
    for quirk_group in quirks_a_groups:
        for category_b, enum_b in traits_b.items():
            weight, desc = lookup_quirk_synergy(quirk_group, enum_b)
            if weight != 0:
                key = f"quirk_a:{quirk_group}×{enum_b}"
                breakdown[key] = f"{desc} ({weight:+d})"
                total += weight
    
    # Evaluate quirk group to trait synergies for char_b
    for quirk_group in quirks_b_groups:
        for category_a, enum_a in traits_a.items():
            weight, desc = lookup_quirk_synergy(quirk_group, enum_a)
            if weight != 0:
                key = f"quirk_b:{quirk_group}×{enum_a}"
                breakdown[key] = f"{desc} ({weight:+d})"
                total += weight
    
    # Apply clamping from synergy_scale.json
    scale = _get_synergy_scale()
    aggregation = scale.get("aggregation", {})
    clamp_min = aggregation.get("clamp_min", -10)
    clamp_max = aggregation.get("clamp_max", 10)
    
    clamped_total = max(clamp_min, min(clamp_max, total))
    
    # Add summary line
    if clamped_total != total:
        breakdown["_clamped"] = f"clamped from {total:+d} to {clamped_total:+d}"
    
    # Get descriptive label
    score_to_label = aggregation.get("score_to_label", [])
    label = "Neutral"
    for range_def in score_to_label:
        if range_def["min"] <= clamped_total <= range_def["max"]:
            label = range_def["label"]
            break
    
    breakdown["_summary"] = f"{label} (total: {clamped_total:+d})"
    
    return clamped_total, breakdown
