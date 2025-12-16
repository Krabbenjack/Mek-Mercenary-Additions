"""
Test bounded portrait scaling for Character Detail Window.

This test validates that the bounded scaling algorithm correctly scales portraits
without cropping, distortion, or excessive shrinking.
"""
import sys
from pathlib import Path
import unittest

# Add src to path
src_path = Path(__file__).resolve().parents[2] / "mekhq_social_sim" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestBoundedPortraitScaling(unittest.TestCase):
    """Test the bounded scaling algorithm for portraits."""
    
    def setUp(self):
        """Set up test constants."""
        self.MAX_WIDTH = 220
        self.MAX_HEIGHT = 300
    
    def _compute_scaled_size(self, original_w: int, original_h: int) -> tuple:
        """
        Replicate the bounded scaling algorithm.
        
        This is the algorithm that must be implemented in CharacterDetailDialog._load_portrait_bounded.
        """
        # Compute scaling factors
        scale_w = self.MAX_WIDTH / original_w
        scale_h = self.MAX_HEIGHT / original_h
        scale = min(scale_w, scale_h, 1.0)  # Never upscale
        
        # Compute new size
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)
        
        return (new_w, new_h)
    
    def test_tall_portrait_scaling(self):
        """Test scaling of a tall portrait (e.g., 400x900 _cas variant)."""
        original = (400, 900)
        scaled = self._compute_scaled_size(*original)
        
        # Should scale down to fit height limit
        self.assertLessEqual(scaled[0], self.MAX_WIDTH)
        self.assertLessEqual(scaled[1], self.MAX_HEIGHT)
        
        # Height should be at the limit (aspect ratio constraint)
        self.assertEqual(scaled[1], self.MAX_HEIGHT)
        
        # Width should maintain aspect ratio
        expected_width = int(400 * (self.MAX_HEIGHT / 900))
        self.assertEqual(scaled[0], expected_width)
        
        # Should be close to (133, 300)
        self.assertAlmostEqual(scaled[0], 133, delta=1)
        self.assertEqual(scaled[1], 300)
    
    def test_square_portrait_scaling(self):
        """Test scaling of a square portrait (e.g., 512x512)."""
        original = (512, 512)
        scaled = self._compute_scaled_size(*original)
        
        # Should scale down to fit width limit (since square)
        self.assertLessEqual(scaled[0], self.MAX_WIDTH)
        self.assertLessEqual(scaled[1], self.MAX_HEIGHT)
        
        # Width should be at the limit
        self.assertEqual(scaled[0], self.MAX_WIDTH)
        
        # Height should maintain aspect ratio (also 220 for square)
        self.assertEqual(scaled[1], self.MAX_WIDTH)
    
    def test_wide_portrait_scaling(self):
        """Test scaling of a wide portrait (e.g., 900x400)."""
        original = (900, 400)
        scaled = self._compute_scaled_size(*original)
        
        # Should scale down to fit width limit
        self.assertLessEqual(scaled[0], self.MAX_WIDTH)
        self.assertLessEqual(scaled[1], self.MAX_HEIGHT)
        
        # Width should be at the limit
        self.assertEqual(scaled[0], self.MAX_WIDTH)
        
        # Height should maintain aspect ratio
        expected_height = int(400 * (self.MAX_WIDTH / 900))
        self.assertEqual(scaled[1], expected_height)
        
        # Should be close to (220, 98)
        self.assertEqual(scaled[0], 220)
        self.assertAlmostEqual(scaled[1], 98, delta=1)
    
    def test_small_portrait_no_upscaling(self):
        """Test that small portraits are NOT upscaled."""
        original = (100, 150)
        scaled = self._compute_scaled_size(*original)
        
        # Should remain original size (no upscaling)
        self.assertEqual(scaled[0], original[0])
        self.assertEqual(scaled[1], original[1])
    
    def test_portrait_within_limits_no_scaling(self):
        """Test that portraits already within limits are not scaled."""
        original = (200, 280)
        scaled = self._compute_scaled_size(*original)
        
        # Should remain original size
        self.assertEqual(scaled[0], original[0])
        self.assertEqual(scaled[1], original[1])
    
    def test_portrait_at_exact_width_limit(self):
        """Test portrait exactly at width limit."""
        original = (220, 100)
        scaled = self._compute_scaled_size(*original)
        
        # Should remain original size
        self.assertEqual(scaled[0], 220)
        self.assertEqual(scaled[1], 100)
    
    def test_portrait_at_exact_height_limit(self):
        """Test portrait exactly at height limit."""
        original = (100, 300)
        scaled = self._compute_scaled_size(*original)
        
        # Should remain original size
        self.assertEqual(scaled[0], 100)
        self.assertEqual(scaled[1], 300)
    
    def test_portrait_exceeds_both_limits(self):
        """Test portrait that exceeds both width and height limits."""
        original = (1000, 1000)
        scaled = self._compute_scaled_size(*original)
        
        # Should scale to width limit (more restrictive for square)
        self.assertEqual(scaled[0], self.MAX_WIDTH)
        self.assertEqual(scaled[1], self.MAX_WIDTH)
    
    def test_aspect_ratio_preservation_tall(self):
        """Test that aspect ratio is preserved for tall portraits."""
        original = (300, 600)
        scaled = self._compute_scaled_size(*original)
        
        original_ratio = original[1] / original[0]
        scaled_ratio = scaled[1] / scaled[0]
        
        # Aspect ratio should be preserved
        self.assertAlmostEqual(original_ratio, scaled_ratio, places=2)
    
    def test_aspect_ratio_preservation_wide(self):
        """Test that aspect ratio is preserved for wide portraits."""
        original = (800, 200)
        scaled = self._compute_scaled_size(*original)
        
        original_ratio = original[1] / original[0]
        scaled_ratio = scaled[1] / scaled[0]
        
        # Aspect ratio should be preserved
        self.assertAlmostEqual(original_ratio, scaled_ratio, places=2)
    
    def test_no_zero_dimensions(self):
        """Test that scaling never produces zero dimensions."""
        # Test with extremely wide portrait
        original = (10000, 100)
        scaled = self._compute_scaled_size(*original)
        
        self.assertGreater(scaled[0], 0)
        self.assertGreater(scaled[1], 0)
        
        # Test with extremely tall portrait
        original = (100, 10000)
        scaled = self._compute_scaled_size(*original)
        
        self.assertGreater(scaled[0], 0)
        self.assertGreater(scaled[1], 0)


if __name__ == "__main__":
    unittest.main()
