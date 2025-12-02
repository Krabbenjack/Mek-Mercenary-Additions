"""
MekHQ 5.10 Exporter Tests

Tests for mekhq_personnel_exporter.py with MekHQ 5.10 schema.
"""
import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from mekhq_personnel_exporter import (
    load_cpnx,
    parse_personnel,
    parse_forces,
    parse_units,
    export_personnel_to_json,
    export_toe_to_json,
    get_trait_name,
    AGGRESSION_TRAITS,
    AMBITION_TRAITS,
    GREED_TRAITS,
    SOCIAL_TRAITS,
    PERSONALITY_QUIRK_TRAITS,
)


# Path to test campaign file
SAMPLE_CAMPAIGN = Path(__file__).parent.parent.parent / "Helix Tactical Unit.cpnx.gz"


class TestTraitNameConversion(unittest.TestCase):
    """Test personality trait index to name conversion."""

    def test_aggression_traits(self):
        """Test aggression trait name conversion."""
        self.assertEqual(get_trait_name(AGGRESSION_TRAITS, 0), "NONE")
        self.assertEqual(get_trait_name(AGGRESSION_TRAITS, 2), "ASSERTIVE")
        self.assertEqual(get_trait_name(AGGRESSION_TRAITS, 4), "BLOODTHIRSTY")
        self.assertEqual(get_trait_name(AGGRESSION_TRAITS, 5), "DETERMINED")

    def test_social_traits_extended_range(self):
        """Test social trait name conversion with MekHQ 5.10 extended range."""
        self.assertEqual(get_trait_name(SOCIAL_TRAITS, 0), "NONE")
        self.assertEqual(get_trait_name(SOCIAL_TRAITS, 5), "FRIENDLY")
        self.assertEqual(get_trait_name(SOCIAL_TRAITS, 6), "ENCOURAGING")

    def test_unknown_index(self):
        """Test out-of-range index returns UNKNOWN_<index>."""
        result = get_trait_name(AGGRESSION_TRAITS, 99)
        self.assertEqual(result, "UNKNOWN_99")

    def test_none_index(self):
        """Test None index returns None."""
        result = get_trait_name(AGGRESSION_TRAITS, None)
        self.assertIsNone(result)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestCampaignLoading(unittest.TestCase):
    """Test loading and parsing MekHQ 5.10 campaign files."""

    def test_load_campaign(self):
        """Test loading a .cpnx.gz campaign file."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        self.assertIsNotNone(root)
        self.assertEqual(root.tag, "campaign")

    def test_parse_personnel(self):
        """Test personnel parsing returns valid data."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)

        self.assertIsInstance(personnel, list)
        self.assertGreater(len(personnel), 0)

        # Check first person has required fields
        person = personnel[0]
        self.assertIn("id", person)
        self.assertIn("name", person)
        self.assertIn("personality", person)
        self.assertIn("primary_role", person)

    def test_personality_traits_parsed(self):
        """Test personality traits are correctly parsed."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)

        # Find a person with personality traits
        person_with_traits = None
        for p in personnel:
            pers = p.get("personality", {})
            if pers.get("aggressionDescriptionIndex") is not None:
                person_with_traits = p
                break

        self.assertIsNotNone(person_with_traits, "No person with personality traits found")

        personality = person_with_traits["personality"]
        self.assertIn("aggressionDescriptionIndex", personality)
        self.assertIn("aggression", personality)  # Enum name should be set

    def test_no_legacy_unit_force_ids(self):
        """Test that personnel don't have legacy unit_id/force_id fields."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)

        for person in personnel:
            # MekHQ 5.10 doesn't store these directly on personnel
            self.assertNotIn("unit_id", person)
            self.assertNotIn("force_id", person)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestForcesParsing(unittest.TestCase):
    """Test TO&E forces parsing with MekHQ 5.10 schema."""

    def test_parse_forces(self):
        """Test forces parsing returns valid hierarchy."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)

        self.assertIsInstance(forces, list)
        self.assertGreater(len(forces), 0)

        root_force = forces[0]
        self.assertIn("id", root_force)
        self.assertIn("name", root_force)
        self.assertIn("sub_forces", root_force)

    def test_forces_have_preferred_role(self):
        """Test forces include preferredRole field (new in 5.10)."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)

        root_force = forces[0]
        self.assertIn("preferred_role", root_force)
        # Helix Tactical Unit should have FRONTLINE
        self.assertEqual(root_force["preferred_role"], "FRONTLINE")

    def test_forces_have_formation_level(self):
        """Test forces include formationLevel field."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)

        root_force = forces[0]
        self.assertIn("formation_level", root_force)
        self.assertEqual(root_force["formation_level"], "Company")

    def test_forces_have_force_type(self):
        """Test forces include forceType field."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)

        root_force = forces[0]
        self.assertIn("force_type", root_force)
        self.assertEqual(root_force["force_type"], 0)  # Combat type

    def test_sub_forces_parsed(self):
        """Test sub-forces are correctly parsed."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)

        root_force = forces[0]
        sub_forces = root_force.get("sub_forces", [])
        self.assertGreater(len(sub_forces), 0)

        # Check sub-force has required fields
        sub_force = sub_forces[0]
        self.assertIn("id", sub_force)
        self.assertIn("name", sub_force)
        self.assertIn("preferred_role", sub_force)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestUnitsParsing(unittest.TestCase):
    """Test TO&E units parsing with MekHQ 5.10 schema."""

    def test_parse_units(self):
        """Test units parsing returns valid data."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        units = parse_units(root)

        self.assertIsInstance(units, list)
        self.assertGreater(len(units), 0)

    def test_units_have_entity_metadata(self):
        """Test units include full entity metadata."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        units = parse_units(root)

        # Find a unit with entity data
        unit_with_entity = None
        for u in units:
            if u.get("entity"):
                unit_with_entity = u
                break

        self.assertIsNotNone(unit_with_entity, "No unit with entity data found")

        entity = unit_with_entity["entity"]
        self.assertIn("chassis", entity)
        self.assertIn("model", entity)
        self.assertIn("type", entity)
        self.assertIn("externalId", entity)

    def test_units_have_force_id_from_mothball_info(self):
        """Test units have forceId from mothballInfo (not legacy location)."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        units = parse_units(root)

        units_with_force = [u for u in units if u.get("forceId")]
        self.assertGreater(len(units_with_force), 0)

    def test_units_have_crew_from_mothball_info(self):
        """Test units have crew roles from mothballInfo."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        units = parse_units(root)

        units_with_crew = [u for u in units if u.get("crew")]
        self.assertGreater(len(units_with_crew), 0)

        # Check crew structure
        unit = units_with_crew[0]
        crew = unit["crew"]
        # Should have at least one crew role (plural keys for multiple crew)
        crew_keys = {"driverIds", "gunnerIds", "commanderIds", "navigatorIds", "techIds", "vesselCrewIds"}
        self.assertTrue(any(k in crew for k in crew_keys))

    def test_units_have_maintenance_multiplier(self):
        """Test units include maintenanceMultiplier."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        units = parse_units(root)

        units_with_maint = [u for u in units if u.get("maintenanceMultiplier") is not None]
        self.assertGreater(len(units_with_maint), 0)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestJSONExport(unittest.TestCase):
    """Test JSON export functionality."""

    def test_export_personnel_to_json(self):
        """Test personnel JSON export."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "personnel_complete.json")
            result_path = export_personnel_to_json(personnel, output_path)

            self.assertEqual(result_path, output_path)
            self.assertTrue(os.path.exists(output_path))

            # Verify JSON is valid
            with open(output_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data), len(personnel))

    def test_export_toe_to_json(self):
        """Test TO&E JSON export."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)
        units = parse_units(root)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "toe_complete.json")
            result_path = export_toe_to_json(forces, units, output_path)

            self.assertEqual(result_path, output_path)
            self.assertTrue(os.path.exists(output_path))

            # Verify JSON structure
            with open(output_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("forces", data)
            self.assertIn("units", data)

    def test_units_assigned_to_forces_in_export(self):
        """Test that units are correctly assigned to forces in exported JSON."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)
        units = parse_units(root)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "toe_complete.json")
            export_toe_to_json(forces, units, output_path)

            with open(output_path, encoding="utf-8") as f:
                data = json.load(f)

            # Check that some forces have units populated
            def count_units_in_forces(force_list):
                total = 0
                for f in force_list:
                    total += len(f.get("units", []))
                    total += count_units_in_forces(f.get("sub_forces", []))
                return total

            total_assigned = count_units_in_forces(data["forces"])
            self.assertGreater(total_assigned, 0, "No units assigned to forces")


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestInputFileIntegrity(unittest.TestCase):
    """Test that the exporter does not modify input files."""

    def test_cpnx_file_not_modified(self):
        """Test that exporting does not modify the input .cpnx file."""
        import hashlib

        # Compute hash before
        with open(SAMPLE_CAMPAIGN, 'rb') as f:
            hash_before = hashlib.md5(f.read()).hexdigest()

        # Run full export
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_personnel_to_json(personnel, os.path.join(tmpdir, "personnel.json"))
            export_toe_to_json(forces, units, os.path.join(tmpdir, "toe.json"))

        # Compute hash after
        with open(SAMPLE_CAMPAIGN, 'rb') as f:
            hash_after = hashlib.md5(f.read()).hexdigest()

        self.assertEqual(hash_before, hash_after, "Input .cpnx file was modified!")


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestSecurityBranchMapping(unittest.TestCase):
    """Test that Security branch units and personnel are correctly mapped."""

    def test_security_force_exists(self):
        """Test that Security force (type=3) exists in parsed forces."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        forces = parse_forces(root)

        # Flatten all forces
        all_forces = []
        def flatten(f_list):
            for f in f_list:
                all_forces.append(f)
                flatten(f.get("sub_forces", []))
        flatten(forces)

        security_forces = [f for f in all_forces if f.get("force_type") == 3]
        self.assertGreater(len(security_forces), 0, "No Security force found")

    def test_infantry_unit_has_multiple_crew(self):
        """Test that infantry units (Foot Platoon) have multiple crew members."""
        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        units = parse_units(root)

        # Find Foot Platoon (Security unit)
        foot_platoon = None
        for u in units:
            entity = u.get("entity", {})
            if "Foot Platoon" in entity.get("chassis", ""):
                foot_platoon = u
                break

        self.assertIsNotNone(foot_platoon, "Foot Platoon not found")

        crew = foot_platoon.get("crew", {})
        driver_ids = crew.get("driverIds", [])
        gunner_ids = crew.get("gunnerIds", [])

        # Foot Platoon should have many drivers (infantry)
        self.assertGreater(len(driver_ids), 10, "Infantry unit should have many drivers")
        self.assertGreater(len(gunner_ids), 10, "Infantry unit should have many gunners")


if __name__ == "__main__":
    unittest.main()
