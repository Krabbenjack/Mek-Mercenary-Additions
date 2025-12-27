"""
Test data loading with extended character fields.
"""
import sys
from pathlib import Path
import json
import tempfile
import os

# Add src to path
src_path = Path(__file__).resolve().parents[2] / "mekhq_social_sim" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import unittest
from data_loading import load_personnel


class TestExtendedDataLoading(unittest.TestCase):
    """Test cases for loading extended character data."""

    def test_load_personnel_with_extended_fields(self):
        """Test loading personnel with attributes, skills, and abilities."""
        # Create a temporary JSON file with test data
        test_data = [
            {
                "id": "char-001",
                "name": {
                    "full_name": "John Doe",
                    "callsign": "Duke"
                },
                "age": 32,
                "birthday": "2990-05-15",
                "primary_role": "MEKWARRIOR",
                "secondary_role": "TECH",
                "rank": 5,
                "personality": {
                    "aggression": "AGGRESSIVE",
                    "aggressionDescriptionIndex": 3,
                    "ambition": "AMBITIOUS",
                    "ambitionDescriptionIndex": 4,
                    "greed": "NONE",
                    "greedDescriptionIndex": 0,
                    "social": "SOCIABLE",
                    "socialDescriptionIndex": 4,
                    "quirks": ["TECH_SAVVY", "BRAVE"]
                },
                "attributes": {
                    "STR": 7,
                    "DEX": 8,
                    "INT": 9,
                    "WIL": 6,
                    "CHA": 5,
                    "EDG": 4
                },
                "skills": {
                    "Gunnery/Mek": 3,
                    "Piloting/Mek": 4,
                    "Tech/Mek": 5,
                    "Tactics": 2
                },
                "abilities": {
                    "Natural Aptitude/Gunnery": "Bonus to gunnery rolls",
                    "Combat Reflexes": "Bonus to initiative"
                },
                "portrait": {
                    "category": "Male/Mek",
                    "filename": "MW_M_1.png"
                }
            },
            {
                "id": "char-002",
                "name": {
                    "full_name": "Jane Smith",
                },
                "age": 28,
                "primary_role": "TECH",
                "personality": {},
                # No secondary_role, attributes, skills, or abilities
            }
        ]

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            # Load the data
            characters = load_personnel(temp_path)

            # Verify we loaded 2 characters
            self.assertEqual(len(characters), 2)

            # Check char-001 (with all fields)
            char1 = characters.get("char-001")
            self.assertIsNotNone(char1)
            self.assertEqual(char1.name, "John Doe")
            self.assertEqual(char1.callsign, "Duke")
            self.assertEqual(char1.age, 32)
            self.assertEqual(char1.profession, "MEKWARRIOR")
            self.assertEqual(char1.secondary_profession, "TECH")
            
            # Check attributes
            self.assertEqual(len(char1.attributes), 6)
            self.assertEqual(char1.attributes["STR"], 7)
            self.assertEqual(char1.attributes["DEX"], 8)
            self.assertEqual(char1.attributes["INT"], 9)
            
            # Check skills
            self.assertEqual(len(char1.skills), 4)
            self.assertEqual(char1.skills["Gunnery/Mek"], 3)
            self.assertEqual(char1.skills["Piloting/Mek"], 4)
            self.assertEqual(char1.skills["Tech/Mek"], 5)
            
            # Check abilities
            self.assertEqual(len(char1.abilities), 2)
            self.assertIn("Natural Aptitude/Gunnery", char1.abilities)
            self.assertIn("Combat Reflexes", char1.abilities)
            
            # Check quirks
            self.assertEqual(len(char1.quirks), 2)
            self.assertIn("TECH_SAVVY", char1.quirks)
            self.assertIn("BRAVE", char1.quirks)

            # Check char-002 (missing optional fields)
            char2 = characters.get("char-002")
            self.assertIsNotNone(char2)
            self.assertEqual(char2.name, "Jane Smith")
            self.assertIsNone(char2.callsign)
            self.assertEqual(char2.profession, "TECH")
            self.assertIsNone(char2.secondary_profession)
            
            # Check empty collections
            self.assertEqual(len(char2.attributes), 0)
            self.assertEqual(len(char2.skills), 0)
            self.assertEqual(len(char2.abilities), 0)

        finally:
            # Clean up temp file
            os.unlink(temp_path)

    def test_load_personnel_with_null_values(self):
        """Test loading personnel with null values in new fields."""
        test_data = [
            {
                "id": "char-003",
                "name": {"full_name": "Null Test"},
                "age": 25,
                "primary_role": "MEKWARRIOR",
                "secondary_role": None,
                "attributes": None,
                "skills": None,
                "abilities": None,
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            characters = load_personnel(temp_path)
            char = characters.get("char-003")
            
            self.assertIsNotNone(char)
            self.assertIsNone(char.secondary_profession)
            self.assertEqual(len(char.attributes), 0)
            self.assertEqual(len(char.skills), 0)
            self.assertEqual(len(char.abilities), 0)

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
