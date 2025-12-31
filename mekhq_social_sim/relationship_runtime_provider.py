"""
relationship_runtime_provider.py

Single authoritative provider for relationship runtime state.
This module computes relationship runtime data based on campaign time,
stored relationship state, and configured relationship rules.

IMPORTANT:
- This module owns ALL runtime numbers.
- No example values are hardcoded.
- Calendar dates are translated into campaign-relative day counters.
"""

from datetime import date
from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# External dependencies (to be injected / imported from campaign systems)
# ---------------------------------------------------------------------------

def get_current_campaign_date() -> date:
    """
    Must be provided by the campaign calendar system.
    Returns the current in-universe date.
    """
    raise NotImplementedError


def get_campaign_start_date() -> date:
    """
    Must be provided by the campaign meta system.
    Returns the campaign start date.
    """
    raise NotImplementedError


def load_persisted_relationships() -> List[Dict[str, Any]]:
    """
    Loads persisted relationship state from storage.
    This data must already be free of example values.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Core time handling
# ---------------------------------------------------------------------------

def compute_campaign_day() -> int:
    """
    Computes the current campaign day as a relative offset.
    Day 0 == campaign start date.
    """
    current = get_current_campaign_date()
    start = get_campaign_start_date()

    if current < start:
        raise ValueError("Current campaign date is before campaign start date.")

    return (current - start).days


# ---------------------------------------------------------------------------
# Derived evaluation stubs (implemented elsewhere)
# ---------------------------------------------------------------------------

def evaluate_states(relationship: Dict[str, Any]) -> Dict[str, str]:
    """
    Evaluates relationship states (friendship / romance / respect)
    based on axis values and state threshold rules.
    """
    return {}


def evaluate_dynamic(relationship: Dict[str, Any]) -> str:
    """
    Evaluates the current relationship dynamic.
    """
    return "unknown"


# ---------------------------------------------------------------------------
# Runtime builder
# ---------------------------------------------------------------------------

def build_relationship_runtime() -> Dict[str, Any]:
    """
    Builds the complete relationship runtime snapshot.
    This is the ONLY supported way to obtain relationship runtime data.
    """

    campaign_day = compute_campaign_day()
    persisted_relationships = load_persisted_relationships()

    runtime_relationships: List[Dict[str, Any]] = []

    for rel in persisted_relationships:
        runtime_entry = {
            "relationship_id": rel["relationship_id"],
            "participants": rel["participants"],

            # Mutable factual state
            "axes": rel.get("axes", {}),
            "sentiments": rel.get("sentiments", {}),
            "flags": rel.get("flags", {}),
            "roles": rel.get("roles", {}),

            # Derived, non-authoritative data
            "derived": {
                "states": evaluate_states(rel),
                "dynamic": evaluate_dynamic(rel),
                "evaluated_day": campaign_day
            }
        }

        runtime_relationships.append(runtime_entry)

    return {
        "_domain": "relationship",
        "_type": "runtime_snapshot",
        "_authoritative": True,

        "meta": {
            "current_campaign_day": campaign_day,
            "generated_on_day": campaign_day,
            "time_source": "campaign_calendar"
        },

        "relationships": runtime_relationships
    }


# ---------------------------------------------------------------------------
# Serialization helper (optional)
# ---------------------------------------------------------------------------

def serialize_relationship_runtime() -> Dict[str, Any]:
    """
    Public API for UI and external systems.
    Returns a fully computed, safe-to-consume runtime snapshot.
    """
    return build_relationship_runtime()
