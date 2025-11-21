from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from datetime import datetime, date

from models import Character, UnitAssignment


def _parse_iso_date(date_str: str) -> date | None:
    """Parse yyyy-mm-dd (ISO) date string to datetime.date, return None on failure."""
    if not date_str:
        return None
    try:
        # expected format in JSON: yyyy-mm-dd
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        # fallback to generic ISO parse
        try:
            return datetime.fromisoformat(date_str).date()
        except Exception:
            return None


def load_personnel(personnel_path: str | Path) -> Dict[str, Character]:
    """Load personnel_complete.json and convert to Character objects.

    Expected JSON structure from mekhq_personnel_exporter.py:
    [
      {
        "id": "123",
        "name": {
          "full_name": "John Doe",
          "callsign": "Bulldog"
        },
        "age": 32,
        "birthday": "1990-05-12",
        "primary_role": "MechWarrior",
        "personality": {
          "aggression": "AGGRESSIVE",
          "aggressionDescriptionIndex": 3,
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

        # Name-Struktur aus dem Exporter
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

        # Personality traits extrahieren und in 0-100 Werte konvertieren
        traits = {}
        personality = entry.get("personality", {})

        if isinstance(personality, dict):
            # Trait-Index-Werte (0-4 oder 0-5) in 0-100 skalieren
            trait_mappings = {
                "aggressionDescriptionIndex": ("aggression", 4),  # 0-4 -> 0-100
                "ambitionDescriptionIndex": ("ambition", 4),
                "greedDescriptionIndex": ("greed", 2),  # 0-2 -> 0-100
                "socialDescriptionIndex": ("gregariousness", 5),  # 0-5 -> 0-100
            }

            for index_key, (trait_name, max_val) in trait_mappings.items():
                index_val = personality.get(index_key)
                if index_val is not None:
                    try:
                        # Skaliere von 0-max_val auf 0-100
                        scaled_value = int((int(index_val) / max_val) * 100)
                        traits[trait_name] = scaled_value
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

        # Fallback: Wenn alte "traits" Struktur vorhanden
        if not traits and "traits" in entry:
            old_traits = entry.get("traits", {})
            if isinstance(old_traits, dict):
                traits = {k: int(v) for k, v in old_traits.items() if v is not None}

        char = Character(
            id=cid,
            name=name,
            callsign=callsign,
            age=age,
            profession=profession,
            traits=traits,
            birthday=birthday,
        )
        characters[cid] = char

    return characters


def apply_toe_structure(toe_path: str | Path, characters: Dict[str, Character]) -> None:
    """Apply TO&E structure from toe_complete.json to Character objects.

    Expected JSON structure from mekhq_personnel_exporter.py:
    {
      "forces": [
        {
          "id": "0",
          "name": "Alpha Regiment",
          "force_type": 0,
          "units": ["unit-uuid-1", ...],
          "sub_forces": [...]
        }
      ],
      "units": [
        {
          "id": "unit-uuid-1",
          "forceId": "0",
          "driverId": "person-uuid",
          "gunnerId": "person-uuid",
          ...
        }
      ]
    }
    """
    path = Path(toe_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    forces = data.get("forces", [])
    units = data.get("units", [])

    # Erstelle Mapping: Force-ID -> Force-Info
    force_map = {}

    def _flatten_forces(force_list, parent_name=None, parent_type=None):
        for force in force_list:
            fid = str(force.get("id"))
            fname = force.get("name", "Unknown Force")
            ftype_num = force.get("force_type", 0)

            # Force-Type als String
            force_type_names = {
                0: "Combat",
                1: "Support",
                2: "Transport",
                3: "Civilian"
            }
            ftype = force_type_names.get(ftype_num, "Unknown")

            force_map[fid] = {
                "name": fname,
                "type": ftype
            }

            # Rekursiv Sub-Forces verarbeiten
            sub_forces = force.get("sub_forces", [])
            if sub_forces:
                _flatten_forces(sub_forces, fname, ftype)

    _flatten_forces(forces)

    # Erstelle Mapping: Unit-ID -> Force-Info
    unit_to_force = {}
    for unit in units:
        uid = str(unit.get("id"))
        fid = str(unit.get("forceId", ""))
        if fid and fid in force_map:
            unit_to_force[uid] = force_map[fid]

    # Erstelle Mapping: Person-ID -> Unit-ID
    person_to_unit = {}
    for unit in units:
        uid = str(unit.get("id"))

        # Verschiedene Crew-Positionen
        crew_ids = []
        for key in ["driverId", "gunnerId", "commanderId", "navigatorId", "techId"]:
            cid = unit.get(key)
            if cid:
                crew_ids.append(str(cid))

        for cid in crew_ids:
            person_to_unit[cid] = uid

    # Wende TO&E auf Charaktere an
    for cid, char in characters.items():
        uid = person_to_unit.get(cid)
        if uid and uid in unit_to_force:
            force_info = unit_to_force[uid]
            char.unit = UnitAssignment(
                force_name=force_info["name"],
                unit_name=f"Unit {uid[:8]}",  # Gekürzte Unit-ID als Name
                force_type=force_info["type"]
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
