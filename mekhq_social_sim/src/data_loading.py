"""
MekHQ 5.10 Data Loading Module

Loads personnel and TO&E data from JSON files exported by mekhq_personnel_exporter.py.
Supports ONLY MekHQ 5.10 schema - no backward compatibility with older versions.

Key MekHQ 5.10 changes:
- Crew roles are in units[].crew (from mothballInfo)
- Forces include preferred_role and formation_level
- Units are assigned to forces via mothballInfo.forceID
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, date

from models import Character, UnitAssignment, PortraitInfo


# Force type mapping (MekHQ 5.10)
FORCE_TYPE_NAMES = {
    0: "Combat",
    1: "Support",
    2: "Transport",
    3: "Security",
    4: "Salvage",
}


def _parse_iso_date(date_str: str) -> date | None:
    """Parse yyyy-mm-dd (ISO) date string to datetime.date, return None on failure."""
    if not date_str:
        return None
    try:
        # Expected format in JSON: yyyy-mm-dd
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        # Fallback to generic ISO parse
        try:
            return datetime.fromisoformat(date_str).date()
        except Exception:
            return None


def load_personnel(personnel_path: str | Path) -> Dict[str, Character]:
    """Load personnel_complete.json and convert to Character objects.

    Expected JSON structure from mekhq_personnel_exporter.py (MekHQ 5.10):
    [
      {
        "id": "uuid",
        "name": {
          "full_name": "John Doe",
          "callsign": "Bulldog"
        },
        "age": 32,
        "birthday": "2961-05-12",
        "primary_role": "MEKWARRIOR",
        "personality": {
          "aggression": "AGGRESSIVE",
          "aggressionDescriptionIndex": 3,
          "ambition": "AMBITIOUS",
          "ambitionDescriptionIndex": 4,
          "greed": "PROFITABLE",
          "greedDescriptionIndex": 3,
          "social": "FRIENDLY",
          "socialDescriptionIndex": 5,
          ...
        }
      },
      ...
    ]
    """
    path = Path(personnel_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    characters: Dict[str, Character] = {}
    for entry in data:
        cid = str(entry.get("id"))
        if not cid or cid in characters:
            continue

        # Name structure from exporter
        name_data = entry.get("name", {})
        if isinstance(name_data, dict):
            name = name_data.get("full_name") or "Unknown"
            callsign = name_data.get("callsign")
        else:
            name = str(name_data) if name_data else "Unknown"
            callsign = None

        # Age field from JSON (may be 0 or missing)
        age = int(entry.get("age") or 0)
        profession = entry.get("primary_role") or entry.get("profession")

        # Try parse birthday (JSON uses yyyy-mm-dd)
        birth_str = entry.get("birthday") or entry.get("birthdate") or entry.get("dateOfBirth")
        birthday = _parse_iso_date(birth_str) if birth_str else None

        # Personality traits: scale from 0-N indices to 0-100
        traits = {}
        personality = entry.get("personality", {})

        if isinstance(personality, dict):
            # MekHQ 5.10 trait index ranges (updated)
            trait_mappings = {
                "aggressionDescriptionIndex": ("aggression", 5),   # 0-5 range
                "ambitionDescriptionIndex": ("ambition", 5),       # 0-5 range
                "greedDescriptionIndex": ("greed", 6),             # 0-6 range
                "socialDescriptionIndex": ("gregariousness", 6),   # 0-6 range
            }

            for index_key, (trait_name, max_val) in trait_mappings.items():
                index_val = personality.get(index_key)
                if index_val is not None:
                    try:
                        # Scale from 0-max_val to 0-100
                        scaled_value = int((int(index_val) / max_val) * 100) if max_val > 0 else 0
                        traits[trait_name] = min(100, scaled_value)  # Cap at 100
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

        # Portrait info from JSON
        portrait_data = entry.get("portrait", {})
        portrait = None
        if isinstance(portrait_data, dict) and (portrait_data.get("category") or portrait_data.get("filename")):
            portrait = PortraitInfo(
                category=portrait_data.get("category"),
                filename=portrait_data.get("filename")
            )

        # Rank from JSON
        rank = entry.get("rank")

        char = Character(
            id=cid,
            name=name,
            callsign=callsign,
            age=age,
            profession=profession,
            traits=traits,
            birthday=birthday,
            portrait=portrait,
            rank=rank,
        )
        characters[cid] = char

    return characters


def apply_toe_structure(toe_path: str | Path, characters: Dict[str, Character]) -> None:
    """Apply TO&E structure from toe_complete.json to Character objects.

    MekHQ 5.10 JSON structure:
    {
      "forces": [
        {
          "id": "0",
          "name": "Alpha Regiment",
          "force_type": 0,
          "formation_level": "Company",
          "preferred_role": "FRONTLINE",
          "units": ["unit-uuid-1", ...],
          "sub_forces": [...]
        }
      ],
      "units": [
        {
          "id": "unit-uuid-1",
          "entity": {"chassis": "Victor", "model": "VTR-9B", ...},
          "forceId": "1",
          "maintenanceMultiplier": 4,
          "crew": {
            "driverId": "person-uuid",
            "gunnerId": "person-uuid",
            "techId": "person-uuid",
            "vesselCrewIds": ["person-uuid", ...]
          }
        }
      ]
    }
    """
    path = Path(toe_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    forces = data.get("forces", [])
    units = data.get("units", [])

    # Build force ID -> force info mapping (flatten hierarchy)
    force_map: Dict[str, Dict[str, Any]] = {}

    def _flatten_forces(force_list: List[Dict], parent_name: Optional[str] = None) -> None:
        for force in force_list:
            fid = str(force.get("id", ""))
            fname = force.get("name", "Unknown Force")
            ftype_num = force.get("force_type", 0)
            ftype = FORCE_TYPE_NAMES.get(ftype_num, f"Type_{ftype_num}")

            force_map[fid] = {
                "name": fname,
                "type": ftype,
                "formation_level": force.get("formation_level"),
                "preferred_role": force.get("preferred_role"),
                "force_commander_id": force.get("force_commander_id"),
            }

            # Recursively process sub-forces
            sub_forces = force.get("sub_forces", [])
            if sub_forces:
                _flatten_forces(sub_forces, fname)

    _flatten_forces(forces)

    # Build unit ID -> unit info mapping
    unit_map: Dict[str, Dict[str, Any]] = {}
    for unit in units:
        uid = str(unit.get("id", ""))
        if not uid:
            continue

        entity = unit.get("entity", {})
        unit_map[uid] = {
            "id": uid,
            "force_id": str(unit.get("forceId", "")),
            "chassis": entity.get("chassis", ""),
            "model": entity.get("model", ""),
            "entity_type": entity.get("type", ""),
            "crew": unit.get("crew", {}),
            "maintenance_multiplier": unit.get("maintenanceMultiplier"),
        }

    # Build person ID -> (unit_id, crew_role) mapping
    person_to_unit: Dict[str, Dict[str, Any]] = {}
    for unit in units:
        uid = str(unit.get("id", ""))
        crew = unit.get("crew", {})

        # Map crew roles (MekHQ 5.10 uses mothballInfo)
        # NOTE: Infantry/vehicle units can have MULTIPLE crew per role
        crew_role_map = {
            "driverIds": "driver",
            "gunnerIds": "gunner",
            "commanderIds": "commander",
            "navigatorIds": "navigator",
            "techIds": "tech",
        }

        for crew_key, role_name in crew_role_map.items():
            person_ids = crew.get(crew_key, [])
            if isinstance(person_ids, list):
                for person_id in person_ids:
                    if person_id:
                        person_to_unit[str(person_id)] = {
                            "unit_id": uid,
                            "role": role_name,
                        }

        # Vessel crew (multiple people, same role)
        vessel_crew_ids = crew.get("vesselCrewIds", [])
        for person_id in vessel_crew_ids:
            if person_id:
                person_to_unit[str(person_id)] = {
                    "unit_id": uid,
                    "role": "crew",
                }

    # Apply TO&E to characters
    for cid, char in characters.items():
        assignment = person_to_unit.get(cid)
        if not assignment:
            continue

        uid = assignment["unit_id"]
        unit_info = unit_map.get(uid)
        if not unit_info:
            continue

        force_id = unit_info["force_id"]
        force_info = force_map.get(force_id)
        if not force_info:
            continue

        # Build unit name from entity data
        chassis = unit_info.get("chassis", "")
        model = unit_info.get("model", "")
        if chassis and model:
            unit_name = f"{chassis} {model}"
        elif chassis:
            unit_name = chassis
        else:
            unit_name = f"Unit {uid[:8]}"

        char.unit = UnitAssignment(
            force_name=force_info["name"],
            unit_name=unit_name,
            force_type=force_info["type"],
            formation_level=force_info.get("formation_level"),
            preferred_role=force_info.get("preferred_role"),
            crew_role=assignment.get("role"),
        )


def load_campaign(
    personnel_path: str | Path,
    toe_path: str | Path | None = None,
) -> Dict[str, Character]:
    """Convenience loader: personnel + optional TO&E."""
    characters = load_personnel(personnel_path)
    if toe_path is not None:
        apply_toe_structure(toe_path, characters)
    return characters
