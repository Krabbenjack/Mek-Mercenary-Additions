# mekhq_personnel_exporter.py
"""
Vollständiger MekHQ Personnel + TO&E Exporter
Extrahiert ALLE Personaldaten und die TO&E-Struktur (Forces & Units)
aus .cpnx/.cpnx.gz Dateien und exportiert sie als JSON.

- personnel_complete.json  → Personen + Traits etc.
- toe_complete.json        → Forces-Baum + Units (Chassis, Crew, forceId ...)
"""

import os
import gzip
import json
import xml.etree.ElementTree as ET
from tkinter import Tk, filedialog
from typing import Optional, Dict, Any, List


# ============================================================
# PERSONALITY TRAIT ENUMS (MekHQ Standard)
# ============================================================

AGGRESSION_TRAITS = [
    "NONE",           # 0
    "TIMID",          # 1
    "ASSERTIVE",      # 2
    "AGGRESSIVE",     # 3
    "BLOODTHIRSTY"    # 4
]

AMBITION_TRAITS = [
    "NONE",           # 0
    "ASPIRING",       # 1
    "COMPETITIVE",    # 2
    "AMBITIOUS",      # 3
    "DRIVEN"          # 4
]

GREED_TRAITS = [
    "NONE",           # 0
    "GREEDY",         # 1
    "AVARICIOUS"      # 2
]

SOCIAL_TRAITS = [
    "NONE",           # 0
    "RECLUSIVE",      # 1
    "RESERVED",       # 2
    "SOCIABLE",       # 3
    "GREGARIOUS",     # 4
    "VERBOSE"         # 5
]

# Personality Quirks - Erweiterte Liste basierend auf MekHQ
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
    Konvertiert einen Trait-Index zu seinem Enum-Namen
    """
    if index is None:
        return None

    try:
        idx = int(index)
        if 0 <= idx < len(trait_list):
            return trait_list[idx]
    except (ValueError, TypeError):
        pass

    return None


# ============================================================
# LOADER
# ============================================================

def load_cpnx(path: str) -> ET.Element:
    """Lädt eine MekHQ-Kampagnendatei (.cpnx oder .cpnx.gz)"""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")

    # GZIP oder normales XML?
    if path.endswith(".gz"):
        with gzip.open(path, "rb") as f:
            raw_data = f.read()
    else:
        with open(path, "rb") as f:
            raw_data = f.read()

    try:
        root = ET.fromstring(raw_data)
    except ET.ParseError as e:
        raise ValueError(f"Keine valide MekHQ-XML-Struktur: {e}")

    return root


# ============================================================
# PARSER HILFSFUNKTIONEN
# ============================================================

def safe_int(value: Any) -> Optional[int]:
    """Sichere Integer-Konvertierung"""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> Optional[float]:
    """Sichere Float-Konvertierung"""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_bool(value: Any) -> Optional[bool]:
    """Sichere Boolean-Konvertierung"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return None


def get_text(elem: ET.Element, *tags: str) -> Optional[str]:
    """Sucht Text in mehreren möglichen Tag-Namen"""
    for tag in tags:
        val = elem.findtext(tag)
        if val:
            return val
    return None


# ============================================================
# PERSONNEL PARSER
# ============================================================

def parse_name(person: ET.Element) -> Dict[str, Optional[str]]:
    """Extrahiert Namen in allen möglichen Formaten"""
    name_data = {
        "given": None,
        "surname": None,
        "callsign": None,
        "full_name": None
    }

    # Direkte Tags (v2 Format)
    name_data["given"] = get_text(person, "givenName", "firstName")
    name_data["surname"] = get_text(person, "surname", "lastName", "familyName")
    name_data["callsign"] = get_text(person, "callsign", "nickname")

    # <name>-Block (v1 Format)
    name_elem = person.find("name")
    if name_elem is not None:
        if not name_data["given"]:
            name_data["given"] = get_text(name_elem, "firstName", "given", "givenName")
        if not name_data["surname"]:
            name_data["surname"] = get_text(name_elem, "lastName", "surname", "family")
        # Falls <name> direkt Text enthält
        if name_elem.text and not (name_data["given"] or name_data["surname"]):
            name_data["full_name"] = name_elem.text

    # Vollständigen Namen zusammensetzen
    if not name_data["full_name"]:
        parts = [name_data["given"], name_data["surname"]]
        name_data["full_name"] = " ".join(p for p in parts if p) or None

    return name_data


def parse_attributes(person: ET.Element) -> Dict[str, int]:
    """Extrahiert Attribute (klassisch + AToW)"""
    attributes = {}

    # Klassische Attribute
    attr_elem = person.find("attributes") or person.find("attributesMap")
    if attr_elem is not None:
        for attr in attr_elem.findall("attribute"):
            name = get_text(attr, "name") or attr.get("name")
            value = get_text(attr, "value") or attr.get("value")
            if name and value:
                attributes[name] = safe_int(value)

    # AToW Attribute (A Time of War)
    atow_elem = person.find("atowAttributes")
    if atow_elem is not None:
        for child in atow_elem:
            val = safe_int(child.text)
            if val is not None:
                attributes[f"atow_{child.tag}"] = val

    # Direkte Attribute-Tags (manchmal einzeln)
    for attr_name in ["STR", "BOD", "RFL", "DEX", "INT", "WIL", "CHA", "EDG"]:
        val = person.findtext(attr_name)
        if val and attr_name not in attributes:
            attributes[attr_name] = safe_int(val)

    return attributes


def parse_skills(person: ET.Element) -> Dict[str, int]:
    """Extrahiert Skills in allen Formaten"""
    skills = {}

    # Format 1: Direkte <skill>-Tags
    for skill in person.findall("skill"):
        s_type = get_text(skill, "type", "name", "skillType")
        s_level = get_text(skill, "level", "value")
        if s_type and s_level:
            skills[s_type] = safe_int(s_level)

    # Format 2: <skills>-Container
    skills_elem = person.find("skills") or person.find("skillMap")
    if skills_elem is not None:
        for skill in skills_elem.findall("skill"):
            s_type = get_text(skill, "type", "name")
            s_level = get_text(skill, "level", "value")
            if s_type and s_level:
                skills[s_type] = safe_int(s_level)

        # Format 3: <entry>-Tags (Map-Struktur)
        for entry in skills_elem.findall("entry"):
            key = entry.get("key") or get_text(entry, "name", "key")
            value = entry.get("value") or get_text(entry, "level", "value")
            if key and value:
                skills[key] = safe_int(value)

    return skills


def parse_abilities(person: ET.Element) -> Dict[str, str]:
    """Extrahiert Special Abilities (SPAs)"""
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
    Extrahiert Persönlichkeitsmerkmale inkl. Enum-Namen
    """
    personality: Dict[str, Any] = {}

    # --- TRAIT-INDIZES AUSLESEN ---
    aggression_idx = safe_int(person.findtext("aggressionDescriptionIndex"))
    ambition_idx = safe_int(person.findtext("ambitionDescriptionIndex"))
    greed_idx = safe_int(person.findtext("greedDescriptionIndex"))
    social_idx = safe_int(person.findtext("socialDescriptionIndex"))
    quirk_idx = safe_int(person.findtext("personalityQuirkDescriptionIndex"))

    # --- ENUM-NAMEN AUS INDIZES GENERIEREN ---
    personality["aggression"] = get_trait_name(AGGRESSION_TRAITS, aggression_idx)
    personality["ambition"] = get_trait_name(AMBITION_TRAITS, ambition_idx)
    personality["greed"] = get_trait_name(GREED_TRAITS, greed_idx)
    personality["social"] = get_trait_name(SOCIAL_TRAITS, social_idx)
    personality["personalityQuirk"] = get_trait_name(PERSONALITY_QUIRK_TRAITS, quirk_idx)

    # --- INDIZES SELBST AUCH SPEICHERN ---
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

    # --- ZUSÄTZLICHE PERSÖNLICHKEITS-DATEN ---
    description = person.findtext("personalityDescription")
    if description:
        personality["description"] = description

    interview_notes = person.findtext("personalityInterviewNotes")
    if interview_notes:
        personality["interview_notes"] = interview_notes

    # Legacy-Felder (alte MekHQ-Versionen)
    legacy_aggression = person.findtext("aggression")
    if legacy_aggression:
        personality["aggression_legacy"] = safe_int(legacy_aggression)

    legacy_greed = person.findtext("greed")
    if legacy_greed:
        personality["greed_legacy"] = safe_int(legacy_greed)

    # Traits (alternative Struktur - falls vorhanden)
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
    """Extrahiert Auszeichnungen"""
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
    """Extrahiert Personnel- und Assignment-Logs"""
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
    """Extrahiert Verletzungen"""
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
    """Extrahiert Portrait-Informationen"""
    portrait: Dict[str, str] = {}

    portrait_elem = person.find("portrait")
    if portrait_elem is not None:
        for child in portrait_elem:
            portrait[child.tag] = child.text

    return portrait


def parse_relationships(person: ET.Element) -> Dict[str, Any]:
    """Extrahiert Beziehungen (Familie, Partner)"""
    relationships: Dict[str, Any] = {
        "partner": None,
        "children": [],
        "parents": [],
        "siblings": []
    }

    rel_elem = person.find("relationships")
    if rel_elem is not None:
        # Partner
        partner = rel_elem.find("partner") or rel_elem.find("spouse")
        if partner is not None:
            relationships["partner"] = partner.get("id")

        # Kinder
        for child in rel_elem.findall(".//child"):
            relationships["children"].append(child.get("id"))

        # Eltern
        for parent in rel_elem.findall(".//parent"):
            relationships["parents"].append(parent.get("id"))

        # Geschwister
        for sibling in rel_elem.findall(".//sibling"):
            relationships["siblings"].append(sibling.get("id"))

    return relationships


def parse_personnel(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Hauptfunktion: Extrahiert ALLE Personaldaten aus einer MekHQ-Kampagne
    """
    personnel_elem = root.find("personnel")
    if personnel_elem is None:
        print("⚠️  Warnung: Kein <personnel>-Abschnitt gefunden.")
        return []

    personnel: List[Dict[str, Any]] = []

    for person in personnel_elem.findall("person"):
        # Basis-Daten
        person_data: Dict[str, Any] = {
            "id": person.get("id"),
            "type": person.get("type"),
            "name": parse_name(person),

            # Rollen & Status
            "primary_role": get_text(person, "primaryRole", "role"),
            "secondary_role": get_text(person, "secondaryRole"),
            "rank": person.findtext("rank"),
            "status": person.findtext("status"),

            # Einheit & Organisation
            "unit_id": person.findtext("unitId"),
            "force_id": person.findtext("forceId"),
            "faction": person.findtext("faction"),
            "origin_faction": person.findtext("originFaction"),

            # Erfahrung
            "xp": safe_int(person.findtext("xp")),
            "total_xp": safe_int(get_text(person, "totalXPEarnings", "totalXP")),
            "kills": safe_int(person.findtext("kills")),

            # Persönliche Daten
            "gender": person.findtext("gender"),
            "birthday": person.findtext("birthday"),
            "age": safe_int(person.findtext("age")),
            "date_of_death": person.findtext("dateOfDeath"),

            # Finanzen & Loyalität
            "salary": safe_int(person.findtext("salary")),
            "total_earnings": safe_int(person.findtext("totalEarnings")),
            "loyalty": safe_int(person.findtext("loyalty")),

            # Wichtige Daten
            "recruitment_date": person.findtext("recruitment"),
            "joined_campaign": person.findtext("joinedCampaign"),
            "last_rank_change": person.findtext("lastRankChangeDate"),
            "retirement_date": person.findtext("retirementDate"),

            # Komplexe Daten
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
    Extrahiert alle Units aus <units>:
    - id, campaign_type
    - entity-Attribute (Chassis, Modell, Typ etc.)
    - Crew-IDs (driverId, gunnerId, commanderId, navigatorId, techId)
    - forceId (Zuordnung zu Force)
    """
    units_root = root.find("units")
    if units_root is None:
        print("⚠️  Warnung: Kein <units>-Abschnitt gefunden.")
        return []

    units_data: List[Dict[str, Any]] = []

    for unit in units_root.findall("unit"):
        u_id = unit.get("id")
        u_type = unit.get("type")

        data: Dict[str, Any] = {
            "id": u_id,
            "campaign_type": u_type,
        }

        # entity-Block: enthält Chassis/Modell/Typ etc. als Attribute
        entity = unit.find("entity")
        if entity is not None:
            data["entity"] = dict(entity.attrib)

        # bekannte einfache Tags
        def _get(tag: str) -> Optional[str]:
            elem = unit.find(tag)
            return elem.text if elem is not None else None

        for tag in [
            "forceId",
            "driverId",
            "gunnerId",
            "commanderId",
            "navigatorId",
            "techId",
            "site",
            "transportId",
        ]:
            val = _get(tag)
            if val is not None:
                key = tag[0].lower() + tag[1:]  # forceId -> forceId (gleicher Name, nur erstes klein)
                data[key] = val

        # alle anderen einfachen Leaf-Tags als "extras"
        extras: Dict[str, Any] = {}
        for child in unit:
            if child.tag in {
                "entity",
                "forceId",
                "driverId",
                "gunnerId",
                "commanderId",
                "navigatorId",
                "techId",
                "site",
                "transportId",
            }:
                continue
            if len(list(child)) == 0 and child.text and child.text.strip():
                extras[child.tag] = child.text.strip()

        if extras:
            data["extras"] = extras

        units_data.append(data)

    return units_data


def parse_forces(root: ET.Element) -> List[Dict[str, Any]]:
    """
    Extrahiert die komplette Forces/TO&E-Hierarchie:

    Rückgabe ist eine Liste von Wurzel-Forces, jede mit:
    {
      "id": "0",
      "name": "Raven's Storm",
      "formation_level": "Regiment/..."
      "force_type": 0,
      "force_commander_id": "uuid der Person",
      "parent_id": None oder ID,
      "units": [ "unit-uuid", ... ],
      "sub_forces": [ ... gleicher Aufbau ... ]
    }
    """
    forces_root = root.find("forces")
    if forces_root is None:
        print("⚠️  Warnung: Kein <forces>-Abschnitt gefunden.")
        return []

    def _parse_force(elem: ET.Element, parent_id: Optional[str] = None) -> Dict[str, Any]:
        fid = elem.get("id")
        data: Dict[str, Any] = {
            "id": fid,
            "name": elem.findtext("name"),
            "formation_level": elem.findtext("formationLevel"),
            "force_type": safe_int(elem.findtext("forceType")),
            "force_commander_id": elem.findtext("forceCommanderID"),
            "parent_id": parent_id,
            "units": [],
            "sub_forces": [],
        }

        # Unit-Referenzen in dieser Force
        units_elem = elem.find("units")
        if units_elem is not None:
            for uref in units_elem.findall("unit"):
                uid = uref.get("id") or (uref.text.strip() if uref.text else None)
                if uid:
                    data["units"].append(uid)

        # Unter-Forces
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
    """Hilfsfunktion: zählt alle Forces inkl. Unter-Forces"""
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
    """Exportiert Personaldaten als JSON"""
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
    Exportiert die TO&E-Struktur (Forces + Units) als JSON.

    Struktur:
    {
      "forces": [...],
      "units":  [...]
    }
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    payload = {
        "forces": forces_data,
        "units": units_data,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return output_path


def print_summary(personnel_data: List[Dict[str, Any]]):
    """Gibt eine Zusammenfassung für das Personal aus"""
    print(f"\n{'='*60}")
    print(f"📊 PERSONNEL EXPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total Personnel: {len(personnel_data)}")

    if personnel_data:
        # Zähle Personen mit verschiedenen Daten
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

        # Personality Traits Statistik
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

        # Beispiel-Person zeigen
        example = personnel_data[0]
        print(f"\n📋 Example Person:")
        print(f"   Name: {example['name'].get('full_name', 'N/A')}")
        print(f"   Rank: {example.get('rank', 'N/A')}")
        print(f"   XP:   {example.get('xp', 'N/A')}")
        print(f"   Skills: {len(example.get('skills', {}))}")
        print(f"   Attributes: {len(example.get('attributes', {}))}")

        # Personality Traits des Beispiels
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
    """Hauptprogramm mit Datei-Dialog"""
    print("\n" + "="*60)
    print("🎮 MekHQ Personnel + TO&E Exporter")
    print("    (inkl. Personality Trait Enums)")
    print("="*60 + "\n")

    # Datei-Dialog
    Tk().withdraw()
    file_path = filedialog.askopenfilename(
        title="Wähle eine MekHQ-Kampagnendatei",
        filetypes=[
            ("MekHQ Kampagnen", "*.cpnx *.cpnx.gz"),
            ("Alle Dateien", "*.*"),
        ],
    )

    if not file_path:
        print("❌ Keine Datei gewählt. Abbruch.")
        return

    print(f"📂 Lade Kampagne: {os.path.basename(file_path)}")

    try:
        # Laden
        root = load_cpnx(file_path)
        print("✅ Kampagne erfolgreich geladen")

        # --- PERSONNEL ---
        print("📊 Extrahiere Personaldaten...")
        personnel_data = parse_personnel(root)

        if not personnel_data:
            print("⚠️  Keine Personaldaten gefunden!")

        # --- TO&E (FORCES & UNITS) ---
        print("📊 Extrahiere TO&E (Forces & Units)...")
        forces_data = parse_forces(root)
        units_data = parse_units(root)

        # --- EXPORT ---
        print("💾 Exportiere JSON...")

        personnel_output_path = export_personnel_to_json(personnel_data)
        toe_output_path = export_toe_to_json(forces_data, units_data)

        # --- ZUSAMMENFASSUNG ---
        print_summary(personnel_data)

        total_forces = count_forces_recursive(forces_data)
        print(f"\n{'='*60}")
        print("📊 TO&E SUMMARY")
        print(f"{'='*60}")
        print(f"Root Forces: {len(forces_data)}")
        print(f"Total Forces (inkl. Unterforces): {total_forces}")
        print(f"Units: {len(units_data)}")
        print(f"{'='*60}\n")

        print("✅ Export erfolgreich abgeschlossen!")
        print(f"📄 Personnel-Datei gespeichert: {personnel_output_path}")
        print(f"📄 TO&E-Datei gespeichert:      {toe_output_path}")

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
