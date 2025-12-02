"""
MekHQ 5.10 Importer Tests

Tests for data_loading.py with MekHQ 5.10 schema.
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

from data_loading import (
    load_personnel,
    apply_toe_structure,
    load_campaign,
    FORCE_TYPE_NAMES,
    VALID_CREW_ROLES,
)
from models import Character, UnitAssignment

# Import exporter for creating test data
from mekhq_personnel_exporter import (
    load_cpnx,
    parse_personnel,
    parse_forces,
    parse_units,
    export_personnel_to_json,
    export_toe_to_json,
)


# Path to test campaign file
SAMPLE_CAMPAIGN = Path(__file__).parent.parent.parent / "Helix Tactical Unit.cpnx.gz"


class TestForceTypeNames(unittest.TestCase):
    """Test force type name mapping."""

    def test_combat_type(self):
        self.assertEqual(FORCE_TYPE_NAMES[0], "Combat")

    def test_support_type(self):
        self.assertEqual(FORCE_TYPE_NAMES[1], "Support")

    def test_transport_type(self):
        self.assertEqual(FORCE_TYPE_NAMES[2], "Transport")

    def test_security_type(self):
        self.assertEqual(FORCE_TYPE_NAMES[3], "Security")

    def test_salvage_type(self):
        self.assertEqual(FORCE_TYPE_NAMES[4], "Salvage")


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestLoadPersonnel(unittest.TestCase):
    """Test personnel loading from JSON."""

    @classmethod
    def setUpClass(cls):
        """Create test JSON files from sample campaign."""
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.personnel_path = os.path.join(cls.tmpdir.name, "personnel_complete.json")
        cls.toe_path = os.path.join(cls.tmpdir.name, "toe_complete.json")

        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        export_personnel_to_json(personnel, cls.personnel_path)
        export_toe_to_json(forces, units, cls.toe_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_load_personnel_returns_dict(self):
        """Test load_personnel returns a dictionary."""
        characters = load_personnel(self.personnel_path)
        self.assertIsInstance(characters, dict)

    def test_load_personnel_returns_character_objects(self):
        """Test load_personnel returns Character objects."""
        characters = load_personnel(self.personnel_path)
        self.assertGreater(len(characters), 0)

        for cid, char in characters.items():
            self.assertIsInstance(char, Character)
            self.assertEqual(char.id, cid)

    def test_characters_have_name(self):
        """Test characters have name field."""
        characters = load_personnel(self.personnel_path)
        for char in characters.values():
            self.assertIsNotNone(char.name)
            self.assertNotEqual(char.name, "")

    def test_characters_have_profession(self):
        """Test characters have profession from primary_role."""
        characters = load_personnel(self.personnel_path)
        # At least some characters should have professions
        with_profession = [c for c in characters.values() if c.profession]
        self.assertGreater(len(with_profession), 0)

    def test_personality_traits_scaled(self):
        """Test personality traits are scaled to 0-100."""
        characters = load_personnel(self.personnel_path)

        # Find character with traits
        char_with_traits = None
        for char in characters.values():
            if char.traits:
                char_with_traits = char
                break

        self.assertIsNotNone(char_with_traits, "No character with traits found")

        for trait_name, trait_value in char_with_traits.traits.items():
            self.assertGreaterEqual(trait_value, 0)
            self.assertLessEqual(trait_value, 100)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestApplyTOEStructure(unittest.TestCase):
    """Test TO&E structure application to characters."""

    @classmethod
    def setUpClass(cls):
        """Create test JSON files from sample campaign."""
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.personnel_path = os.path.join(cls.tmpdir.name, "personnel_complete.json")
        cls.toe_path = os.path.join(cls.tmpdir.name, "toe_complete.json")

        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        export_personnel_to_json(personnel, cls.personnel_path)
        export_toe_to_json(forces, units, cls.toe_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_apply_toe_assigns_units(self):
        """Test apply_toe_structure assigns units to characters."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        assigned = [c for c in characters.values() if c.unit is not None]
        self.assertGreater(len(assigned), 0)

    def test_unit_assignment_has_force_name(self):
        """Test UnitAssignment has force_name."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        for char in characters.values():
            if char.unit:
                self.assertIsNotNone(char.unit.force_name)
                self.assertNotEqual(char.unit.force_name, "")

    def test_unit_assignment_has_unit_name(self):
        """Test UnitAssignment has unit_name from chassis/model."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        for char in characters.values():
            if char.unit:
                self.assertIsNotNone(char.unit.unit_name)

    def test_unit_assignment_has_force_type(self):
        """Test UnitAssignment has force_type."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        for char in characters.values():
            if char.unit:
                self.assertIsNotNone(char.unit.force_type)

    def test_unit_assignment_has_formation_level(self):
        """Test UnitAssignment has formation_level (MekHQ 5.10)."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        # At least some characters should have formation_level
        with_formation = [c for c in characters.values()
                         if c.unit and c.unit.formation_level]
        self.assertGreater(len(with_formation), 0)

    def test_unit_assignment_has_preferred_role(self):
        """Test UnitAssignment has preferred_role (new in 5.10)."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        # At least some characters should have preferred_role
        with_role = [c for c in characters.values()
                    if c.unit and c.unit.preferred_role]
        self.assertGreater(len(with_role), 0)

    def test_unit_assignment_has_crew_role(self):
        """Test UnitAssignment has crew_role from mothballInfo."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        # All assigned characters should have a crew role
        with_crew_role = [c for c in characters.values()
                         if c.unit and c.unit.crew_role]
        assigned = [c for c in characters.values() if c.unit]

        self.assertGreater(len(with_crew_role), 0)
        # Crew role should be valid
        for char in with_crew_role:
            self.assertIn(char.unit.crew_role, VALID_CREW_ROLES)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestUnassignedCharacters(unittest.TestCase):
    """Test handling of characters without TO&E assignment."""

    @classmethod
    def setUpClass(cls):
        """Create test JSON files from sample campaign."""
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.personnel_path = os.path.join(cls.tmpdir.name, "personnel_complete.json")
        cls.toe_path = os.path.join(cls.tmpdir.name, "toe_complete.json")

        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        export_personnel_to_json(personnel, cls.personnel_path)
        export_toe_to_json(forces, units, cls.toe_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_unassigned_characters_have_no_unit(self):
        """Test characters without TO&E have unit=None."""
        characters = load_personnel(self.personnel_path)
        apply_toe_structure(self.toe_path, characters)

        unassigned = [c for c in characters.values() if c.unit is None]
        self.assertGreater(len(unassigned), 0, "Expected some unassigned characters")

        for char in unassigned:
            self.assertIsNone(char.unit)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestLoadCampaignConvenience(unittest.TestCase):
    """Test load_campaign convenience function."""

    @classmethod
    def setUpClass(cls):
        """Create test JSON files from sample campaign."""
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.personnel_path = os.path.join(cls.tmpdir.name, "personnel_complete.json")
        cls.toe_path = os.path.join(cls.tmpdir.name, "toe_complete.json")

        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        export_personnel_to_json(personnel, cls.personnel_path)
        export_toe_to_json(forces, units, cls.toe_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_load_campaign_without_toe(self):
        """Test load_campaign with only personnel file."""
        characters = load_campaign(self.personnel_path)
        self.assertIsInstance(characters, dict)
        self.assertGreater(len(characters), 0)

        # Without TOE, all characters should have unit=None
        for char in characters.values():
            self.assertIsNone(char.unit)

    def test_load_campaign_with_toe(self):
        """Test load_campaign with both personnel and TOE files."""
        characters = load_campaign(self.personnel_path, self.toe_path)
        self.assertIsInstance(characters, dict)
        self.assertGreater(len(characters), 0)

        # With TOE, some characters should have units
        assigned = [c for c in characters.values() if c.unit is not None]
        self.assertGreater(len(assigned), 0)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestSecurityBranchImport(unittest.TestCase):
    """Test that Security branch personnel are correctly imported."""

    @classmethod
    def setUpClass(cls):
        """Create test JSON files from sample campaign."""
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.personnel_path = os.path.join(cls.tmpdir.name, "personnel_complete.json")
        cls.toe_path = os.path.join(cls.tmpdir.name, "toe_complete.json")

        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        export_personnel_to_json(personnel, cls.personnel_path)
        export_toe_to_json(forces, units, cls.toe_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_security_characters_assigned(self):
        """Test that characters are assigned to Security force."""
        characters = load_campaign(self.personnel_path, self.toe_path)

        security_chars = [c for c in characters.values()
                         if c.unit and c.unit.force_type == "Security"]

        # Infantry platoon should have many characters
        self.assertGreater(len(security_chars), 20,
                          f"Expected >20 Security characters, got {len(security_chars)}")

    def test_security_characters_have_crew_roles(self):
        """Test that Security characters have proper crew roles."""
        characters = load_campaign(self.personnel_path, self.toe_path)

        security_chars = [c for c in characters.values()
                         if c.unit and c.unit.force_type == "Security"]

        for char in security_chars:
            self.assertIsNotNone(char.unit.crew_role,
                                f"Security character {char.name} has no crew role")
            self.assertIn(char.unit.crew_role, VALID_CREW_ROLES)


if __name__ == "__main__":
    unittest.main()
