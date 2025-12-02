# mekhq_personnel_exporter.py
"""
MekHQ 5.10 Personnel + TO&E Exporter

Extracts personnel data and TO&E structure from MekHQ 5.10 campaign files
(.cpnx/.cpnx.gz) and exports them as JSON.

Supports ONLY MekHQ 5.10 schema - no backward compatibility with older versions.

Output files:
- personnel_complete.json  → Personnel data with traits
- toe_complete.json        → Forces hierarchy + Units with crew roles from mothballInfo

Key MekHQ 5.10 changes:
- TO&E info (forceID, crew roles) is stored exclusively in <mothballInfo>
- Forces include preferredRole field
- Personality trait indices can go up to 5 for social traits
"""

import os
import gzip
import json
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List

# Optional tkinter import (only needed for GUI file dialog)
try:
    from tkinter import Tk, filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    Tk = None
    filedialog = None


# ============================================================
# PERSONALITY TRAIT ENUMS (MekHQ 5.10)
# ============================================================

# MekHQ 5.10 uses indices 0-4 for aggression
AGGRESSION_TRAITS = [
    "NONE",           # 0
    "TIMID",          # 1
    "ASSERTIVE",      # 2
    "AGGRESSIVE",     # 3
    "BLOODTHIRSTY",   # 4
    "DETERMINED"      # 5 (new in 5.10)
]

# MekHQ 5.10 uses indices 0-5 for ambition
AMBITION_TRAITS = [
    "NONE",           # 0
    "ASPIRING",       # 1
    "GOAL_ORIENTED",  # 2 (renamed in 5.10)
    "COMPETITIVE",    # 3
    "AMBITIOUS",      # 4
    "DRIVEN"          # 5
]

# MekHQ 5.10 uses indices 0-5 for greed
GREED_TRAITS = [
    "NONE",           # 0
    "GENEROUS",       # 1
    "HOARDING",       # 2
    "PROFITABLE",     # 3
    "FRAUDULENT",     # 4
    "MERCENARY",      # 5
    "LUSTFUL"         # 6 (extended)
]

# MekHQ 5.10 uses indices 0-5 for social
SOCIAL_TRAITS = [
    "NONE",           # 0
    "AUTHENTIC",      # 1
    "DISINGENUOUS",   # 2
    "RESERVED",       # 3
    "CONDESCENDING",  # 4
    "FRIENDLY",       # 5
    "ENCOURAGING"     # 6 (extended)
]

# Personality Quirks - Extended list for MekHQ 5.10
PERSONALITY_QUIRK_TRAITS = [
    "NONE",           # 0
    "HONEST",         # 1
    "DISHONEST",      # 2
    "OPTIMISTIC",     # 3
    "PESSIMISTIC",    # 4
    "PRAGMATIC",      # 5
    "INNOVATIVE",     # 6
    "TRADITIONAL",    # 7
    "REBELLIOUS",     # 8
    "DISCIPLINED"     # 9
]


def get_trait_name(trait_list: List[str], index: Optional[int]) -> Optional[str]:
    """
    Convert a trait index to its enum name.
    Returns UNKNOWN_<index> if index is out of range for the trait list.
    """
    if index is None:
        return None

    try:
        idx = int(index)
        if 0 <= idx < len(trait_list):
            return trait_list[idx]
        # Return UNKNOWN_<index> for out-of-range indices
        return f"UNKNOWN_{idx}"
    except (ValueError, TypeError):
        pass

    return None


# ============================================================
# LOADER
# ============================================================

def load_cpnx(path: str) -> ET.Element:
    """Load a MekHQ campaign file (.cpnx or .cpnx.gz)"""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    # GZIP or regular XML?
    if path.endswith(".gz"):
        with gzip.open(path, "rb") as f:
            raw_data = f.read()
    else:
        with open(path, "rb") as f:
            raw_data = f.read()

    try:
        root = ET.fromstring(raw_data)
    except ET.ParseError as e:
        raise ValueError(f"Not a valid MekHQ XML structure: {e}")

    return root


# ============================================================
# PARSER HELPER FUNCTIONS
# ============================================================

def safe_int(value: Any) -> Optional[int]:
    """Safe integer conversion"""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> Optional[float]:
    """Safe float conversion"""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_bool(value: Any) -> Optional[bool]:
    """Safe boolean conversion"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return None


def get_text(elem: ET.Element, *tags: str) -> Optional[str]:
    """Search for text in multiple possible tag names"""
    for tag in tags:
        val = elem.findtext(tag)
        if val:
            return val
    return None


# ============================================================
# PERSONNEL PARSER
# ============================================================

def parse_name(person: ET.Element) -> Dict[str, Optional[str]]:
    """Extract names in all possible formats"""
    name_data = {
        "given": None,
        "surname": None,
        "callsign": None,
        "full_name": None
    }

    # Direct tags (MekHQ 5.10 format)
    name_data["given"] = get_text(person, "givenName", "firstName")
    name_data["surname"] = get_text(person, "surname", "lastName", "familyName")
    name_data["callsign"] = get_text(person, "callsign", "nickname")

    # <name> block (legacy format)
    name_elem = person.find("name")
    if name_elem is not None:
        if not name_data["given"]:
            name_data["given"] = get_text(name_elem, "firstName", "given", "givenName")
        if not name_data["surname"]:
            name_data["surname"] = get_text(name_elem, "lastName", "surname", "family")
        # If <name> contains direct text
        if name_elem.text and not (name_data["given"] or name_data["surname"]):
            name_data["full_name"] = name_elem.text

    # Build full name
    if not name_data["full_name"]:
        parts = [name_data["given"], name_data["surname"]]
        name_data["full_name"] = " ".join(p for p in parts if p) or None

    return name_data


def parse_attributes(person: ET.Element) -> Dict[str, int]:
    """Extract attributes (classic + AToW)"""
    attributes = {}

    # Classic attributes
    attr_elem = person.find("attributes") or person.find("attributesMap")
    if attr_elem is not None:
        for attr in attr_elem.findall("attribute"):
            name = get_text(attr, "name") or attr.get("name")
            value = get_text(attr, "value") or attr.get("value")
            if name and value:
                attributes[name] = safe_int(value)

    # AToW Attributes (A Time of War)
    atow_elem = person.find("atowAttributes")
    if atow_elem is not None:
        for child in atow_elem:
            val = safe_int(child.text)
            if val is not None:
                attributes[f"atow_{child.tag}"] = val

    # Direct attribute tags (sometimes single)
    for attr_name in ["STR", "BOD", "RFL", "DEX", "INT", "WIL", "CHA", "EDG"]:
        val = person.findtext(attr_name)
        if val and attr_name not in attributes:
            attributes[attr_name] = safe_int(val)

    return attributes


def parse_skills(person: ET.Element) -> Dict[str, int]:
    """Extract skills in all formats"""
    skills = {}

    # Format 1: Direct <skill> tags
    for skill in person.findall("skill"):
        s_type = get_text(skill, "type", "name", "skillType")
        s_level = get_text(skill, "level", "value")
        if s_type and s_level:
            skills[s_type] = safe_int(s_level)

    # Format 2: <skills> container
    skills_elem = person.find("skills") or person.find("skillMap")
    if skills_elem is not None:
        for skill in skills_elem.findall("skill"):
            s_type = get_text(skill, "type", "name")
            s_level = get_text(skill, "level", "value")
            if s_type and s_level:
                skills[s_type] = safe_int(s_level)

        # Format 3: <entry> tags (Map structure)
        for entry in skills_elem.findall("entry"):
            key = entry.get("key") or get_text(entry, "name", "key")
            value = entry.get("value") or get_text(entry, "level", "value")
            if key and value:
                skills[key] = safe_int(value)

    return skills


def parse_abilities(person: ET.Element) -> Dict[str, str]:
    """Extract Special Abilities (SPAs)"""
    abilities = {}

    abilities_elem = person.find("abilities") or person.find("specialAbilities")
    if abilities_elem is not None:
        for ab in abilities_elem.findall("ability"):
            name = get_text(ab, "name") or ab.get("name")
            desc = get_text(ab, "description", "desc") or ab.get("description", "")
            if name:
                abilities[name] = desc

    return abilities


def parse_personality(person: ET.Element) -> Dict[str, Any]:
    """
    Extract personality traits including enum names.
    Handles MekHQ 5.10 extended trait indices (up to 5-6 for some traits).
    """
    personality: Dict[str, Any] = {}

    # --- READ TRAIT INDICES ---
    aggression_idx = safe_int(person.findtext("aggressionDescriptionIndex"))
    ambition_idx = safe_int(person.findtext("ambitionDescriptionIndex"))
    greed_idx = safe_int(person.findtext("greedDescriptionIndex"))
    social_idx = safe_int(person.findtext("socialDescriptionIndex"))
    quirk_idx = safe_int(person.findtext("personalityQuirkDescriptionIndex"))

    # --- GENERATE ENUM NAMES FROM INDICES ---
    personality["aggression"] = get_trait_name(AGGRESSION_TRAITS, aggression_idx)
    personality["ambition"] = get_trait_name(AMBITION_TRAITS, ambition_idx)
    personality["greed"] = get_trait_name(GREED_TRAITS, greed_idx)
    personality["social"] = get_trait_name(SOCIAL_TRAITS, social_idx)
    personality["personalityQuirk"] = get_trait_name(PERSONALITY_QUIRK_TRAITS, quirk_idx)

    # --- ALSO STORE INDICES THEMSELVES ---
    if aggression_idx is not None:
        personality["aggressionDescriptionIndex"] = aggression_idx
    if ambition_idx is not None:
        personality["ambitionDescriptionIndex"] = ambition_idx
    if greed_idx is not None:
        personality["greedDescriptionIndex"] = greed_idx
    if social_idx is not None:
        personality["socialDescriptionIndex"] = social_idx
    if quirk_idx is not None:
        personality["personalityQuirkDescriptionIndex"] = quirk_idx

    # --- ADDITIONAL PERSONALITY DATA ---
    description = person.findtext("personalityDescription")
    if description:
        personality["description"] = description

    interview_notes = person.findtext("personalityInterviewNotes")
    if interview_notes:
        personality["interview_notes"] = interview_notes

    # Traits (alternative structure - if present)
    traits_elem = person.find("personality") or person.find("personalityTraits") or person.find("traits")
    if traits_elem is not None:
        traits: Dict[str, Any] = {}
        for trait in traits_elem.findall("trait"):
            name = get_text(trait, "name") or trait.get("name") or trait.text
            value = get_text(trait, "value") or trait.get("value", "True")
            if name:
                traits[name] = value
        if traits:
            personality["traits"] = traits

    return personality if personality else {}


def parse_awards(person: ET.Element) -> List[Dict[str, str]]:
    """Extract awards"""
    awards: List[Dict[str, str]] = []

    awards_elem = person.find("awards")
    if awards_elem is not None:
        for award in awards_elem.findall("award"):
            awards.append({
                "name": award.findtext("name"),
                "date": award.findtext("date"),
                "set": award.findtext("set")
            })

    return awards


def parse_logs(person: ET.Element) -> Dict[str, List[Dict[str, str]]]:
    """Extract personnel and assignment logs"""
    logs = {"personnel": [], "assignments": []}

    # Personnel Log
    pers_log = person.find("personnelLog")
    if pers_log is not None:
        for entry in pers_log.findall("logEntry"):
            logs["personnel"].append({
                "date": entry.findtext("date"),
                "description": entry.findtext("desc"),
                "type": entry.findtext("type")
            })

    # Assignment Log
    assign_log = person.find("assignmentLog") or person.find("missionLog")
    if assign_log is not None:
        for entry in assign_log.findall("logEntry"):
            logs["assignments"].append({
                "date": entry.findtext("date"),
                "description": entry.findtext("desc"),
                "type": entry.findtext("type")
            })

    return logs


def parse_injuries(person: ET.Element) -> List[Dict[str, Any]]:
    """Extract injuries"""
    injuries: List[Dict[str, Any]] = []

    injuries_elem = person.find("injuries")
    if injuries_elem is not None:
        for injury in injuries_elem.findall("injury"):
            injuries.append({
                "type": injury.findtext("type"),
                "location": injury.findtext("location"),
                "severity": safe_int(injury.findtext("severity")),
                "permanent": safe_bool(injury.findtext("permanent")),
                "hits": safe_int(injury.findtext("hits"))
            })

    return injuries


def parse_portrait(person: ET.Element) -> Dict[str, str]:
    """Extract portrait information"""
    portrait: Dict[str, str] = {}

    portrait_elem = person.find("portrait")
    if portrait_elem is not None:
        for child in portrait_elem:
            portrait[child.tag] = child.text

    return portrait


def parse_relationships(person: ET.Element) -> Dict[str, Any]:
    """Extract relationships (family, partner)"""
    relationships: Dict[str, Any] = {
        "partner": None,
        "children": [],
        "parents": [],
        "siblings": []
    }

    # MekHQ 5.10: Relationships in <genealogy>
    genealogy = person.find("genealogy")
    if genealogy is not None:
        family = genealogy.find("family")
        if family is not None:
            for rel in family.findall("relationship"):
                rel_type = rel.findtext("type")
                person_id = rel.findtext("personId")
                if rel_type and person_id:
                    if rel_type == "SPOUSE" or rel_type == "PARTNER":
                        relationships["partner"] = person_id
                    elif rel_type == "CHILD":
                        relationships["children"].append(person_id)
                    elif rel_type == "PARENT":
                        relationships["parents"].append(person_id)
                    elif rel_type == "SIBLING":
                        relationships["siblings"].append(person_id)

    # Legacy format: <relationships> block
    rel_elem = person.find("relationships")
    if rel_elem is not None:
        # Partner
        partner = rel_elem.find("partner") or rel_elem.find("spouse")
        if partner is not None:
            relationships["partner"] = partner.get("id")

        # Children
        for child in rel_elem.findall(".//child"):
            relationships["children"].append(child.get("id"))

        # Parents
        for parent in rel_elem.findall(".//parent"):
            relationships["parents"].append(parent.get("id"))

        # Siblings
        for sibling in rel_elem.findall(".//sibling"):
            relationships["siblings"].append(sibling.get("id"))

    return relationships


def parse_personnel(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Main function: Extract ALL personnel data from a MekHQ campaign (5.10 schema).

    Note: MekHQ 5.10 does NOT store forceId/unitId directly on personnel.
    Unit/force assignment must be resolved via units.mothballInfo crew roles.
    """
    personnel_elem = root.find("personnel")
    if personnel_elem is None:
        print("⚠️  Warning: No <personnel> section found.")
        return []

    personnel: List[Dict[str, Any]] = []

    for person in personnel_elem.findall("person"):
        # Basic data
        person_data: Dict[str, Any] = {
            "id": person.get("id"),
            "type": person.get("type"),
            "name": parse_name(person),

            # Roles & Status
            "primary_role": get_text(person, "primaryRole", "role"),
            "secondary_role": get_text(person, "secondaryRole"),
            "rank": person.findtext("rank"),
            "status": person.findtext("status"),

            # Faction
            "faction": person.findtext("faction"),
            "origin_faction": person.findtext("originFaction"),

            # Experience
            "xp": safe_int(person.findtext("xp")),
            "total_xp": safe_int(get_text(person, "totalXPEarnings", "totalXP")),
            "kills": safe_int(person.findtext("kills")),

            # Personal Data
            "gender": person.findtext("gender"),
            "birthday": person.findtext("birthday"),
            "age": safe_int(person.findtext("age")),
            "date_of_death": person.findtext("dateOfDeath"),

            # Finances & Loyalty
            "salary": safe_int(person.findtext("salary")),
            "total_earnings": safe_int(person.findtext("totalEarnings")),
            "loyalty": safe_int(person.findtext("loyalty")),

            # Important Dates
            "recruitment_date": person.findtext("recruitment"),
            "joined_campaign": person.findtext("joinedCampaign"),
            "last_rank_change": person.findtext("lastRankChangeDate"),
            "retirement_date": person.findtext("retirementDate"),

            # Complex Data
            "attributes": parse_attributes(person),
            "skills": parse_skills(person),
            "abilities": parse_abilities(person),
            "personality": parse_personality(person),
            "awards": parse_awards(person),
            "logs": parse_logs(person),
            "injuries": parse_injuries(person),
            "portrait": parse_portrait(person),
            "relationships": parse_relationships(person),

            # Flags
            "commander": safe_bool(person.findtext("commander")),
            "founder": safe_bool(person.findtext("founder")),
            "immortal": safe_bool(person.findtext("immortal")),
            "clan_personnel": safe_bool(person.findtext("clanPersonnel")),
            "dependent": safe_bool(person.findtext("dependent")),
            "prisoner": safe_bool(person.findtext("prisoner")),
            "bondsman": safe_bool(person.findtext("bondsman")),
        }

        personnel.append(person_data)

    return personnel


# ============================================================
# TO&E PARSER (FORCES & UNITS)
# ============================================================

def parse_units(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Extract all units from <units> section (MekHQ 5.10 schema).

    In 5.10, TO&E assignment and crew roles are ONLY in <mothballInfo>.
    Entity attributes include chassis, model, type, commander, externalId, altitude.

    Returns list of unit dictionaries containing:
    - id: Unit UUID
    - campaign_type: Unit type from XML attribute
    - entity: Full entity metadata (chassis, model, type, commander, externalId, altitude)
    - maintenanceMultiplier: Maintenance cost multiplier
    - forceId: Force assignment (from mothballInfo.forceID)
    - crew: Dictionary of crew roles (driver, gunner, commander, navigator, tech, vesselCrew)
    - extras: Any additional leaf tags
    """
    units_root = root.find("units")
    if units_root is None:
        print("⚠️  Warning: No <units> section found.")
        return []

    units_data: List[Dict[str, Any]] = []

    for unit in units_root.findall("unit"):
        u_id = unit.get("id")
        u_type = unit.get("type")

        data: Dict[str, Any] = {
            "id": u_id,
            "campaign_type": u_type,
        }

        # Entity block: contains chassis, model, type, etc. as attributes
        entity = unit.find("entity")
        if entity is not None:
            entity_data = dict(entity.attrib)
            data["entity"] = entity_data

        # Maintenance multiplier (direct tag)
        maint_mult = unit.findtext("maintenanceMultiplier")
        if maint_mult is not None:
            data["maintenanceMultiplier"] = safe_int(maint_mult)

        # MekHQ 5.10: All TO&E info is in <mothballInfo>
        mothball_info = unit.find("mothballInfo")
        if mothball_info is not None:
            # Force assignment
            force_id = mothball_info.findtext("forceID")
            if force_id is not None:
                data["forceId"] = force_id

            # Crew roles from mothballInfo
            crew: Dict[str, Any] = {}

            driver_id = mothball_info.findtext("driverId")
            if driver_id:
                crew["driverId"] = driver_id

            gunner_id = mothball_info.findtext("gunnerId")
            if gunner_id:
                crew["gunnerId"] = gunner_id

            commander_id = mothball_info.findtext("commanderId")
            if commander_id:
                crew["commanderId"] = commander_id

            navigator_id = mothball_info.findtext("navigatorId")
            if navigator_id:
                crew["navigatorId"] = navigator_id

            tech_id = mothball_info.findtext("techId")
            if tech_id:
                crew["techId"] = tech_id

            # Vessel crew (multiple IDs possible)
            vessel_crew_ids = []
            for vc in mothball_info.findall("vesselCrewId"):
                if vc.text:
                    vessel_crew_ids.append(vc.text)
            if vessel_crew_ids:
                crew["vesselCrewIds"] = vessel_crew_ids

            if crew:
                data["crew"] = crew

        # Extract any other leaf tags as extras (excluding already processed)
        processed_tags = {
            "entity", "maintenanceMultiplier", "mothballInfo",
            "mothballed", "site", "transportId"
        }
        extras: Dict[str, Any] = {}
        for child in unit:
            if child.tag in processed_tags:
                continue
            if len(list(child)) == 0 and child.text and child.text.strip():
                extras[child.tag] = child.text.strip()

        # Include site and transportId if present
        site = unit.findtext("site")
        if site:
            data["site"] = site

        transport_id = unit.findtext("transportId")
        if transport_id:
            data["transportId"] = transport_id

        # Store mothballed status
        mothballed = unit.findtext("mothballed")
        if mothballed:
            data["mothballed"] = safe_bool(mothballed)

        if extras:
            data["extras"] = extras

        units_data.append(data)

    return units_data


def parse_forces(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Extract the complete Forces/TO&E hierarchy (MekHQ 5.10 schema).

    MekHQ 5.10 forces include:
    - id, name
    - formationLevel (e.g., "Company", "Lance", "Team")
    - forceType (integer: 0=Combat, 1=Support, 2=Transport, 3=Security, 4=Salvage)
    - forceCommanderID (UUID of commander person)
    - preferredRole (new in 5.10: e.g., "FRONTLINE")
    - subForces (recursive)

    NOTE: In 5.10, units are NOT listed under forces - they reference forces
    via mothballInfo.forceID. The units list is populated during export by
    matching units to forces.

    Returns list of root forces, each with:
    {
      "id": "0",
      "name": "Helix Tactical Unit",
      "formation_level": "Company",
      "force_type": 0,
      "force_commander_id": "uuid",
      "preferred_role": "FRONTLINE",
      "parent_id": None or ID,
      "units": [],  # Will be populated during export
      "sub_forces": [...]
    }
    """
    forces_root = root.find("forces")
    if forces_root is None:
        print("⚠️  Warning: No <forces> section found.")
        return []

    def _parse_force(elem: ET.Element, parent_id: Optional[str] = None) -> Dict[str, Any]:
        fid = elem.get("id")
        data: Dict[str, Any] = {
            "id": fid,
            "name": elem.findtext("name"),
            "formation_level": elem.findtext("formationLevel"),
            "force_type": safe_int(elem.findtext("forceType")),
            "force_commander_id": elem.findtext("forceCommanderID"),
            "preferred_role": elem.findtext("preferredRole"),  # New in 5.10
            "parent_id": parent_id,
            "units": [],  # Will be populated from unit.mothballInfo.forceID
            "sub_forces": [],
        }

        # Sub-forces (recursive)
        sub_elem = elem.find("subForces")
        if sub_elem is not None:
            for sf in sub_elem.findall("force"):
                data["sub_forces"].append(_parse_force(sf, parent_id=fid))

        return data

    forest: List[Dict[str, Any]] = []
    for top in forces_root.findall("force"):
        forest.append(_parse_force(top, parent_id=None))

    return forest


def count_forces_recursive(forces: List[Dict[str, Any]]) -> int:
    """Helper function: count all forces including sub-forces"""
    total = 0
    for f in forces:
        total += 1
        total += count_forces_recursive(f.get("sub_forces", []))
    return total


# ============================================================
# EXPORT
# ============================================================

def export_personnel_to_json(
    personnel_data: List[Dict[str, Any]],
    output_path: str = "exports/personnel_complete.json",
) -> str:
    """Export personnel data as JSON"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(personnel_data, f, indent=2, ensure_ascii=False)

    return output_path


def export_toe_to_json(
    forces_data: List[Dict[str, Any]],
    units_data: List[Dict[str, Any]],
    output_path: str = "exports/toe_complete.json",
) -> str:
    """
    Export the TO&E structure (Forces + Units) as JSON.

    MekHQ 5.10: Units are assigned to forces via mothballInfo.forceID.
    This function populates the force.units lists from unit forceId values.

    Structure:
    {
      "forces": [...],
      "units":  [...]
    }
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Build force ID mapping for quick lookup
    force_id_map: Dict[str, Dict[str, Any]] = {}

    def _map_forces(force_list: List[Dict[str, Any]]) -> None:
        for force in force_list:
            fid = str(force.get("id", ""))
            if fid:
                force_id_map[fid] = force
            _map_forces(force.get("sub_forces", []))

    _map_forces(forces_data)

    # Populate force units lists from unit forceId (from mothballInfo)
    for unit in units_data:
        force_id = str(unit.get("forceId", ""))
        if force_id and force_id in force_id_map:
            force_id_map[force_id]["units"].append(unit.get("id"))

    payload = {
        "forces": forces_data,
        "units": units_data,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return output_path


def print_summary(personnel_data: List[Dict[str, Any]]):
    """Print a summary of exported personnel data"""
    print(f"\n{'='*60}")
    print(f"📊 PERSONNEL EXPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total Personnel: {len(personnel_data)}")

    if personnel_data:
        # Count people with various data
        with_skills = sum(1 for p in personnel_data if p.get("skills"))
        with_attributes = sum(1 for p in personnel_data if p.get("attributes"))
        with_abilities = sum(1 for p in personnel_data if p.get("abilities"))
        with_personality = sum(1 for p in personnel_data if p.get("personality"))
        commanders = sum(1 for p in personnel_data if p.get("commander"))

        print(f"\n✓ With Skills:       {with_skills}")
        print(f"✓ With Attributes:   {with_attributes}")
        print(f"✓ With Abilities:    {with_abilities}")
        print(f"✓ With Personality:  {with_personality}")
        print(f"✓ Commanders:        {commanders}")

        # Personality Traits Statistics
        trait_counts = {
            "aggression": 0,
            "ambition": 0,
            "greed": 0,
            "social": 0,
            "personalityQuirk": 0,
        }

        for p in personnel_data:
            pers = p.get("personality", {})
            for trait in trait_counts.keys():
                if pers.get(trait):
                    trait_counts[trait] += 1

        print(f"\n📋 Personality Traits:")
        print(f"   Aggression:  {trait_counts['aggression']}")
        print(f"   Ambition:    {trait_counts['ambition']}")
        print(f"   Greed:       {trait_counts['greed']}")
        print(f"   Social:      {trait_counts['social']}")
        print(f"   Quirk:       {trait_counts['personalityQuirk']}")

        # Show example person
        example = personnel_data[0]
        print(f"\n📋 Example Person:")
        print(f"   Name: {example['name'].get('full_name', 'N/A')}")
        print(f"   Rank: {example.get('rank', 'N/A')}")
        print(f"   XP:   {example.get('xp', 'N/A')}")
        print(f"   Skills: {len(example.get('skills', {}))}")
        print(f"   Attributes: {len(example.get('attributes', {}))}")

        # Personality traits of example
        example_pers = example.get("personality", {})
        if example_pers:
            print(f"   Personality:")
            for trait in [
                "aggression",
                "ambition",
                "greed",
                "social",
                "personalityQuirk",
            ]:
                val = example_pers.get(trait)
                if val:
                    print(f"      {trait}: {val}")

    print(f"{'='*60}\n")


# ============================================================
# MAIN
# ============================================================

def main():
    """Main program with file dialog"""
    print("\n" + "="*60)
    print("🎮 MekHQ 5.10 Personnel + TO&E Exporter")
    print("    (with Personality Trait Enums)")
    print("="*60 + "\n")

    # Check if tkinter is available
    if not TKINTER_AVAILABLE:
        print("❌ tkinter not available. Run with a file path argument instead:")
        print("   python mekhq_personnel_exporter.py <path_to_campaign.cpnx>")
        return

    # File dialog
    Tk().withdraw()
    file_path = filedialog.askopenfilename(
        title="Select a MekHQ Campaign File",
        filetypes=[
            ("MekHQ Campaigns", "*.cpnx *.cpnx.gz"),
            ("All Files", "*.*"),
        ],
    )

    if not file_path:
        print("❌ No file selected. Aborting.")
        return

    print(f"📂 Loading campaign: {os.path.basename(file_path)}")

    try:
        # Load
        root = load_cpnx(file_path)
        print("✅ Campaign loaded successfully")

        # --- PERSONNEL ---
        print("📊 Extracting personnel data...")
        personnel_data = parse_personnel(root)

        if not personnel_data:
            print("⚠️  No personnel data found!")

        # --- TO&E (FORCES & UNITS) ---
        print("📊 Extracting TO&E (Forces & Units from mothballInfo)...")
        forces_data = parse_forces(root)
        units_data = parse_units(root)

        # --- EXPORT ---
        print("💾 Exporting JSON...")

        personnel_output_path = export_personnel_to_json(personnel_data)
        toe_output_path = export_toe_to_json(forces_data, units_data)

        # --- SUMMARY ---
        print_summary(personnel_data)

        total_forces = count_forces_recursive(forces_data)
        units_with_force = sum(1 for u in units_data if u.get("forceId"))
        units_with_crew = sum(1 for u in units_data if u.get("crew"))

        print(f"\n{'='*60}")
        print("📊 TO&E SUMMARY (MekHQ 5.10)")
        print(f"{'='*60}")
        print(f"Root Forces: {len(forces_data)}")
        print(f"Total Forces (incl. sub-forces): {total_forces}")
        print(f"Units: {len(units_data)}")
        print(f"Units with Force Assignment: {units_with_force}")
        print(f"Units with Crew Data: {units_with_crew}")
        print(f"{'='*60}\n")

        print("✅ Export completed successfully!")
        print(f"📄 Personnel file saved: {personnel_output_path}")
        print(f"📄 TO&E file saved:      {toe_output_path}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
