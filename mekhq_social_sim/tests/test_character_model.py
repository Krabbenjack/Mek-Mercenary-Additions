"""
Test the extended Character model with new fields.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).resolve().parents[2] / "mekhq_social_sim" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import unittest
from models import Character, UnitAssignment
from datetime import date


class TestExtendedCharacterModel(unittest.TestCase):
    """Test cases for the extended Character model."""

    def test_character_with_all_fields(self):
        """Test creating a character with all new fields."""
        char = Character(
            id="test-001",
            name="Test Pilot",
            callsign="Ace",
            age=32,
            profession="MEKWARRIOR",
            secondary_profession="TECH",
            attributes={"STR": 7, "DEX": 8, "INT": 9},
            skills={"Gunnery": 3, "Piloting": 4, "Tech/Mek": 5},
            abilities={"Natural Aptitude/Gunnery": "Bonus to gunnery rolls"},
        )
        
        self.assertEqual(char.secondary_profession, "TECH")
        self.assertEqual(char.attributes["STR"], 7)
        self.assertEqual(char.skills["Gunnery"], 3)
        self.assertEqual(len(char.abilities), 1)
        self.assertIn("Natural Aptitude/Gunnery", char.abilities)

    def test_character_with_missing_optional_fields(self):
        """Test creating a character with missing optional fields."""
        char = Character(
            id="test-002",
            name="Basic Pilot",
            callsign=None,
            age=25,
            profession="MEKWARRIOR",
        )
        
        self.assertIsNone(char.secondary_profession)
        self.assertEqual(len(char.attributes), 0)
        self.assertEqual(len(char.skills), 0)
        self.assertEqual(len(char.abilities), 0)

    def test_character_empty_collections(self):
        """Test that empty collections are properly initialized."""
        char = Character(
            id="test-003",
            name="Empty Char",
            callsign="Empty",
            age=20,
            profession="TECH",
        )
        
        self.assertIsInstance(char.attributes, dict)
        self.assertIsInstance(char.skills, dict)
        self.assertIsInstance(char.abilities, dict)
        self.assertIsInstance(char.traits, dict)
        self.assertIsInstance(char.quirks, list)

    def test_skill_attribute_mapping(self):
        """Test skill-to-attribute mapping functionality."""
        from skill_attribute_mapping import get_skill_attributes, format_skill_support
        
        # Test exact match
        attrs = get_skill_attributes("Gunnery/Mek")
        self.assertEqual(attrs, ["DEX", "RFL"])
        
        # Test formatted output
        support = format_skill_support("Gunnery/Mek")
        self.assertIn("DEX", support)
        self.assertIn("RFL", support)
        
        # Test unknown skill
        attrs = get_skill_attributes("Unknown Skill")
        self.assertEqual(attrs, [])
        
        support = format_skill_support("Unknown Skill")
        self.assertEqual(support, "")

    def test_character_label_with_professions(self):
        """Test character label generation."""
        char1 = Character(
            id="test-004",
            name="John Doe",
            callsign="Duke",
            age=30,
            profession="MEKWARRIOR",
        )
        
        # Label should use callsign and profession
        self.assertEqual(char1.label(), "Duke (MEKWARRIOR)")
        
        char2 = Character(
            id="test-005",
            name="Jane Smith",
            callsign=None,
            age=28,
            profession="TECH",
        )
        
        # Label should use name when no callsign
        self.assertEqual(char2.label(), "Jane Smith (TECH)")


if __name__ == "__main__":
    unittest.main()
