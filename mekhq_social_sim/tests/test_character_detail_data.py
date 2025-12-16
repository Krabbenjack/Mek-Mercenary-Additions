"""
Integration test simulating CharacterDetailDialog initialization with various character states.
This test validates that the UI can be instantiated without crashes for different data scenarios.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).resolve().parents[2] / "mekhq_social_sim" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import unittest
from datetime import date
from models import Character, UnitAssignment, PortraitInfo


class TestCharacterDetailDialogDataHandling(unittest.TestCase):
    """
    Test that CharacterDetailDialog can handle various character configurations.
    
    These tests validate data handling logic without requiring a GUI environment.
    They simulate the data processing that would occur in the UI.
    """

    def setUp(self):
        """Set up test data."""
        self.current_date = date(2990, 1, 1)

    def test_character_with_full_data(self):
        """Test character with all possible fields populated."""
        char = Character(
            id="full-char",
            name="Complete Warrior",
            callsign="Complete",
            age=35,
            profession="MEKWARRIOR",
            secondary_profession="TECH",
            traits={
                "Aggression": "Aggression:AGGRESSIVE",
                "Ambition": "Ambition:AMBITIOUS",
                "Social": "Social:SOCIABLE",
            },
            friendship={
                "friend-1": 50,
                "friend-2": -30,
                "friend-3": 0,
            },
            daily_interaction_points=10,
            unit=UnitAssignment(
                force_name="Alpha Company",
                unit_name="Alpha Lance",
                force_type="Combat",
                formation_level="Lance",
                preferred_role="FRONTLINE",
                crew_role="pilot",
            ),
            birthday=date(2955, 5, 15),
            portrait=PortraitInfo(category="Male/Mek", filename="MW_M_1.png"),
            rank="5",
            rank_name="Lieutenant",
            quirks=["TECH_SAVVY", "BRAVE", "STUBBORN"],
            attributes={"STR": 7, "DEX": 8, "INT": 9, "WIL": 6, "CHA": 5, "EDG": 4},
            skills={"Gunnery/Mek": 3, "Piloting/Mek": 4, "Tech/Mek": 5},
            abilities={"Natural Aptitude/Gunnery": "Bonus", "Combat Reflexes": "Init bonus"},
        )
        
        # Validate all fields are accessible
        self.assertEqual(char.name, "Complete Warrior")
        self.assertEqual(char.secondary_profession, "TECH")
        self.assertEqual(len(char.attributes), 6)
        self.assertEqual(len(char.skills), 3)
        self.assertEqual(len(char.abilities), 2)
        self.assertEqual(len(char.quirks), 3)
        self.assertIsNotNone(char.unit)
        self.assertIsNotNone(char.portrait)

    def test_character_with_minimal_data(self):
        """Test character with only required fields."""
        char = Character(
            id="minimal-char",
            name="Minimal Pilot",
            callsign=None,
            age=20,
            profession=None,
        )
        
        # Validate optional fields have safe defaults
        self.assertIsNone(char.secondary_profession)
        self.assertEqual(len(char.attributes), 0)
        self.assertEqual(len(char.skills), 0)
        self.assertEqual(len(char.abilities), 0)
        self.assertEqual(len(char.quirks), 0)
        self.assertEqual(len(char.friendship), 0)
        self.assertIsNone(char.unit)
        self.assertIsNone(char.portrait)

    def test_character_with_partial_data(self):
        """Test character with some fields populated, others missing."""
        char = Character(
            id="partial-char",
            name="Partial Pilot",
            callsign="Partial",
            age=28,
            profession="TECH",
            # Has skills but no attributes
            skills={"Tech/Mek": 7, "Computer": 5},
            # Has quirks but no abilities
            quirks=["TECH_SAVVY"],
            # No unit, no portrait
        )
        
        self.assertEqual(len(char.skills), 2)
        self.assertEqual(len(char.attributes), 0)
        self.assertEqual(len(char.quirks), 1)
        self.assertEqual(len(char.abilities), 0)
        self.assertIsNone(char.unit)

    def test_character_with_unknown_profession(self):
        """Test character with custom/unknown profession strings."""
        char = Character(
            id="custom-prof",
            name="Custom Role",
            callsign="Custom",
            age=30,
            profession="Mek_Range_Instructor",  # Custom profession
            secondary_profession="Firing Range instructor",  # Custom secondary
        )
        
        # Should accept any string without crashing
        self.assertEqual(char.profession, "Mek_Range_Instructor")
        self.assertEqual(char.secondary_profession, "Firing Range instructor")
        # Label should include profession
        self.assertIn("Mek_Range_Instructor", char.label())

    def test_character_with_unknown_skills(self):
        """Test character with skills not in the mapping."""
        char = Character(
            id="unknown-skills",
            name="Unique Skills",
            callsign="Unique",
            age=25,
            profession="HACKER",
            skills={
                "Hacking": 8,  # Not in standard mapping
                "Custom Skill": 5,  # Made up
                "Gunnery/Mek": 3,  # Standard skill
            },
        )
        
        self.assertEqual(len(char.skills), 3)
        # All skills should be stored regardless of mapping
        self.assertEqual(char.skills["Hacking"], 8)
        self.assertEqual(char.skills["Custom Skill"], 5)

    def test_character_age_groups(self):
        """Test age group property for different ages."""
        # Child
        child = Character(id="1", name="Child", callsign=None, age=10, profession=None)
        self.assertEqual(child.age_group, "child")
        
        # Teen
        teen = Character(id="2", name="Teen", callsign=None, age=18, profession=None)
        self.assertEqual(teen.age_group, "teen")
        
        # Adult
        adult = Character(id="3", name="Adult", callsign=None, age=35, profession=None)
        self.assertEqual(adult.age_group, "adult")
        
        # Senior
        senior = Character(id="4", name="Senior", callsign=None, age=65, profession=None)
        self.assertEqual(senior.age_group, "senior")

    def test_skill_attribute_mapping_edge_cases(self):
        """Test skill-to-attribute mapping with various inputs."""
        from skill_attribute_mapping import get_skill_attributes, format_skill_support
        
        # Standard skill
        attrs = get_skill_attributes("Gunnery/Mek")
        self.assertGreater(len(attrs), 0)
        
        # Case insensitive
        attrs_lower = get_skill_attributes("gunnery/mek")
        self.assertEqual(attrs, attrs_lower)
        
        # Unknown skill
        unknown = get_skill_attributes("Completely Made Up Skill")
        self.assertEqual(unknown, [])
        
        # Format with unknown skill returns empty string
        formatted = format_skill_support("Unknown")
        self.assertEqual(formatted, "")

    def test_friendship_values_sorting(self):
        """Test that friendship values can be sorted correctly."""
        char = Character(
            id="social-char",
            name="Social Butterfly",
            callsign="Social",
            age=28,
            profession="LIAISON",
            friendship={
                "enemy-1": -50,
                "friend-1": 75,
                "neutral-1": 0,
                "friend-2": 40,
                "enemy-2": -20,
            },
        )
        
        # Sort by value (descending)
        sorted_rels = sorted(char.friendship.items(), key=lambda x: -x[1])
        
        # Verify sorting
        self.assertEqual(sorted_rels[0][1], 75)  # Highest friend
        self.assertEqual(sorted_rels[-1][1], -50)  # Worst enemy
        
        # Filter allies (positive)
        allies = [k for k, v in char.friendship.items() if v > 0]
        self.assertEqual(len(allies), 2)
        
        # Filter rivals (negative)
        rivals = [k for k, v in char.friendship.items() if v < 0]
        self.assertEqual(len(rivals), 2)

    def test_top_skills_extraction(self):
        """Test extracting top N skills for overview section."""
        char = Character(
            id="skilled-char",
            name="Skilled Warrior",
            callsign="Skilled",
            age=40,
            profession="VETERAN_MEKWARRIOR",
            skills={
                "Gunnery/Mek": 8,
                "Piloting/Mek": 7,
                "Tactics": 6,
                "Leadership": 5,
                "Tech/Mek": 4,
                "Small Arms": 3,
                "Medtech": 2,
            },
        )
        
        # Get top 5 skills
        top_5 = sorted(char.skills.items(), key=lambda x: -x[1])[:5]
        
        self.assertEqual(len(top_5), 5)
        self.assertEqual(top_5[0][0], "Gunnery/Mek")
        self.assertEqual(top_5[0][1], 8)
        self.assertEqual(top_5[4][0], "Tech/Mek")
        self.assertEqual(top_5[4][1], 4)


if __name__ == "__main__":
    unittest.main()
