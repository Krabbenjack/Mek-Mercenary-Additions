"""
MekHQ 5.10 GUI Tests

Lightweight tests for gui.py components.
"""
import sys
import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

# Import models for testing (GUI requires tkinter which may not be available)
from models import Character, UnitAssignment, PortraitInfo

# Import exporter and data loading for creating test data
from mekhq_personnel_exporter import (
    load_cpnx,
    parse_personnel,
    parse_forces,
    parse_units,
    export_personnel_to_json,
    export_toe_to_json,
)
from data_loading import load_campaign


# Path to test campaign file
SAMPLE_CAMPAIGN = Path(__file__).parent.parent.parent / "Helix Tactical Unit.cpnx.gz"


class TestCharacterModel(unittest.TestCase):
    """Test Character model with MekHQ 5.10 fields."""

    def test_character_creation(self):
        """Test creating a Character object."""
        char = Character(
            id="test-id",
            name="Test Name",
            callsign="TestCall",
            age=30,
            profession="MEKWARRIOR",
        )
        self.assertEqual(char.id, "test-id")
        self.assertEqual(char.name, "Test Name")
        self.assertEqual(char.callsign, "TestCall")
        self.assertEqual(char.age, 30)
        self.assertEqual(char.profession, "MEKWARRIOR")

    def test_character_label_with_callsign(self):
        """Test character label uses callsign when available."""
        char = Character(
            id="test-id",
            name="John Doe",
            callsign="Bulldog",
            age=30,
            profession="MEKWARRIOR",
        )
        self.assertEqual(char.label(), "Bulldog (MEKWARRIOR)")

    def test_character_label_without_callsign(self):
        """Test character label uses name when no callsign."""
        char = Character(
            id="test-id",
            name="John Doe",
            callsign=None,
            age=30,
            profession="MEKWARRIOR",
        )
        self.assertEqual(char.label(), "John Doe (MEKWARRIOR)")

    def test_character_age_group(self):
        """Test character age group classification."""
        # Child
        char_child = Character(id="1", name="Child", callsign=None, age=10, profession=None)
        self.assertEqual(char_child.age_group, "child")

        # Teen
        char_teen = Character(id="2", name="Teen", callsign=None, age=18, profession=None)
        self.assertEqual(char_teen.age_group, "teen")

        # Adult
        char_adult = Character(id="3", name="Adult", callsign=None, age=35, profession=None)
        self.assertEqual(char_adult.age_group, "adult")

        # Senior
        char_senior = Character(id="4", name="Senior", callsign=None, age=65, profession=None)
        self.assertEqual(char_senior.age_group, "senior")


class TestUnitAssignment(unittest.TestCase):
    """Test UnitAssignment model with MekHQ 5.10 fields."""

    def test_unit_assignment_basic(self):
        """Test creating a basic UnitAssignment."""
        unit = UnitAssignment(
            force_name="Alpha Lance",
            unit_name="Victor VTR-9B",
            force_type="Combat",
        )
        self.assertEqual(unit.force_name, "Alpha Lance")
        self.assertEqual(unit.unit_name, "Victor VTR-9B")
        self.assertEqual(unit.force_type, "Combat")

    def test_unit_assignment_with_5_10_fields(self):
        """Test UnitAssignment with MekHQ 5.10 specific fields."""
        unit = UnitAssignment(
            force_name="Able Lance",
            unit_name="Shadow Hawk SHD-2D",
            force_type="Combat",
            formation_level="Lance",
            preferred_role="FRONTLINE",
            crew_role="gunner",
        )
        self.assertEqual(unit.formation_level, "Lance")
        self.assertEqual(unit.preferred_role, "FRONTLINE")
        self.assertEqual(unit.crew_role, "gunner")

    def test_unit_assignment_optional_fields_default_none(self):
        """Test optional fields default to None."""
        unit = UnitAssignment(
            force_name="Test Force",
            unit_name="Test Unit",
            force_type="Support",
        )
        self.assertIsNone(unit.formation_level)
        self.assertIsNone(unit.preferred_role)
        self.assertIsNone(unit.crew_role)


class TestPortraitInfo(unittest.TestCase):
    """Test PortraitInfo model."""

    def test_portrait_info_creation(self):
        """Test creating PortraitInfo."""
        portrait = PortraitInfo(
            category="Male/MekWarrior/",
            filename="MW_M_26.png",
        )
        self.assertEqual(portrait.category, "Male/MekWarrior/")
        self.assertEqual(portrait.filename, "MW_M_26.png")

    def test_portrait_info_defaults(self):
        """Test PortraitInfo default values."""
        portrait = PortraitInfo()
        self.assertIsNone(portrait.category)
        self.assertIsNone(portrait.filename)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestTreeViewData(unittest.TestCase):
    """Test data preparation for tree view display."""

    @classmethod
    def setUpClass(cls):
        """Create test data from sample campaign."""
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.personnel_path = os.path.join(cls.tmpdir.name, "personnel_complete.json")
        cls.toe_path = os.path.join(cls.tmpdir.name, "toe_complete.json")

        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        export_personnel_to_json(personnel, cls.personnel_path)
        export_toe_to_json(forces, units, cls.toe_path)

        cls.characters = load_campaign(cls.personnel_path, cls.toe_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_characters_grouped_by_force(self):
        """Test characters can be grouped by force name."""
        forces = {}
        no_toe = []

        for char in self.characters.values():
            if char.unit is None:
                no_toe.append(char)
            else:
                force_name = char.unit.force_name
                if force_name not in forces:
                    forces[force_name] = []
                forces[force_name].append(char)

        # Should have some forces
        self.assertGreater(len(forces), 0)

        # Should have characters without TO&E
        self.assertGreater(len(no_toe), 0)

    def test_characters_grouped_by_unit(self):
        """Test characters can be grouped by unit name within forces."""
        forces = {}

        for char in self.characters.values():
            if char.unit is None:
                continue

            force_name = char.unit.force_name
            unit_name = char.unit.unit_name

            if force_name not in forces:
                forces[force_name] = {}

            if unit_name not in forces[force_name]:
                forces[force_name][unit_name] = []

            forces[force_name][unit_name].append(char)

        # Should have nested structure
        self.assertGreater(len(forces), 0)
        for force_name, units in forces.items():
            self.assertGreater(len(units), 0)


@unittest.skipUnless(SAMPLE_CAMPAIGN.exists(), "Sample campaign file not found")
class TestCharacterDetails(unittest.TestCase):
    """Test character detail display data."""

    @classmethod
    def setUpClass(cls):
        """Create test data from sample campaign."""
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.personnel_path = os.path.join(cls.tmpdir.name, "personnel_complete.json")
        cls.toe_path = os.path.join(cls.tmpdir.name, "toe_complete.json")

        root = load_cpnx(str(SAMPLE_CAMPAIGN))
        personnel = parse_personnel(root)
        forces = parse_forces(root)
        units = parse_units(root)

        export_personnel_to_json(personnel, cls.personnel_path)
        export_toe_to_json(forces, units, cls.toe_path)

        cls.characters = load_campaign(cls.personnel_path, cls.toe_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_character_details_fields(self):
        """Test character has all required detail fields."""
        char = next(iter(self.characters.values()))

        # Basic fields should always be present
        self.assertIsNotNone(char.id)
        self.assertIsNotNone(char.name)
        self.assertIsNotNone(char.age)

    def test_character_with_toe_has_unit_details(self):
        """Test character with TO&E has unit detail fields."""
        # Find a character with unit assignment
        char_with_unit = None
        for char in self.characters.values():
            if char.unit:
                char_with_unit = char
                break

        self.assertIsNotNone(char_with_unit, "No character with unit found")

        # Unit fields for display
        self.assertIsNotNone(char_with_unit.unit.unit_name)
        self.assertIsNotNone(char_with_unit.unit.force_name)
        self.assertIsNotNone(char_with_unit.unit.force_type)

    def test_no_crash_on_missing_fields(self):
        """Test handling of missing/None fields doesn't crash."""
        # Create character with minimal data
        char = Character(
            id="minimal",
            name="Minimal Character",
            callsign=None,
            age=0,
            profession=None,
        )

        # These should not crash
        _ = char.label()
        _ = char.age_group

        # Unit is None by default
        self.assertIsNone(char.unit)
        self.assertIsNone(char.birthday)
        self.assertIsNone(char.portrait)


if __name__ == "__main__":
    unittest.main()
