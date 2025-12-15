"""
Unit tests for portrait loading and variant resolution.
"""
import unittest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add src to path
repo_root = Path(__file__).resolve().parents[2]
src_path = repo_root / "mekhq_social_sim" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from models import Character, PortraitInfo


class TestPortraitVariantResolution(unittest.TestCase):
    """Test portrait variant resolution logic."""
    
    def test_extract_base_and_extension(self):
        """Test extracting base name and extension from filename."""
        # Import here to avoid tkinter import issues in CI
        try:
            from gui import PortraitHelper
        except ModuleNotFoundError:
            self.skipTest("tkinter not available")
        
        # Test normal filename
        base, ext = PortraitHelper._extract_base_and_extension("MW_F_4.png")
        self.assertEqual(base, "MW_F_4")
        self.assertEqual(ext, ".png")
        
        # Test filename with _cas suffix
        base, ext = PortraitHelper._extract_base_and_extension("MW_F_4_cas.png")
        self.assertEqual(base, "MW_F_4_cas")
        self.assertEqual(ext, ".png")
        
        # Test different extension
        base, ext = PortraitHelper._extract_base_and_extension("portrait.jpg")
        self.assertEqual(base, "portrait")
        self.assertEqual(ext, ".jpg")
    
    def test_portrait_config_initialization(self):
        """Test PortraitConfig can be initialized without errors."""
        try:
            from gui import PortraitConfig
        except ModuleNotFoundError:
            self.skipTest("tkinter not available")
        
        config = PortraitConfig()
        # Initially should be None (no config file)
        self.assertIsNone(config.external_portrait_root)
        
    def test_portrait_config_search_paths(self):
        """Test search paths include module folder."""
        try:
            from gui import PortraitConfig, PORTRAIT_BASE_PATH
        except ModuleNotFoundError:
            self.skipTest("tkinter not available")
        
        config = PortraitConfig()
        paths = config.get_search_paths()
        
        # Should always include module portrait folder
        self.assertIn(PORTRAIT_BASE_PATH, paths)
        self.assertGreaterEqual(len(paths), 1)
    
    def test_portrait_config_save_and_load(self):
        """Test saving and loading external portrait folder."""
        try:
            from gui import PortraitConfig
        except ModuleNotFoundError:
            self.skipTest("tkinter not available")
        
        with TemporaryDirectory() as temp_dir:
            config = PortraitConfig()
            external_path = Path(temp_dir)
            
            # Save config
            config.save_config(external_path)
            
            # Verify it's set
            self.assertEqual(config.external_portrait_root, external_path)
            
            # Search paths should now include external folder
            paths = config.get_search_paths()
            self.assertIn(external_path, paths)


class TestPortraitCharacterIntegration(unittest.TestCase):
    """Test portrait integration with Character model."""
    
    def test_character_with_portrait_info(self):
        """Test character can have portrait info."""
        portrait = PortraitInfo(category="Male", filename="MW_F_4.png")
        char = Character(
            id="test-1",
            name="Test Pilot",
            callsign="Test",
            age=30,
            profession="MechWarrior",
            portrait=portrait
        )
        
        self.assertIsNotNone(char.portrait)
        self.assertEqual(char.portrait.category, "Male")
        self.assertEqual(char.portrait.filename, "MW_F_4.png")
    
    def test_character_without_portrait_info(self):
        """Test character can exist without portrait info."""
        char = Character(
            id="test-2",
            name="Test Tech",
            callsign=None,
            age=25,
            profession="Technician"
        )
        
        self.assertIsNone(char.portrait)


if __name__ == '__main__':
    unittest.main()
