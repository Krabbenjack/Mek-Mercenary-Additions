# Portrait Bounded Scaling Fix - Implementation Summary

## Issue
Character Detail Window portraits (especially `_cas` variants) were appearing too small due to the use of `Image.thumbnail()` which aggressively shrinks images.

## Solution
Implemented bounded scaling algorithm specifically for Character Detail Window portraits that:
- Preserves aspect ratio
- Scales as large as possible within defined limits
- Never crops or distorts
- Never upscales small images

## Changes Made

### 1. Updated Constants (`gui.py`)
```python
# Old
PORTRAIT_SIZE = (180, 240)

# New
MAX_PORTRAIT_WIDTH = 220
MAX_PORTRAIT_HEIGHT = 300
```

### 2. New Method: `_load_portrait_bounded()`
Implements the required bounded scaling algorithm:
```python
# Load image at original resolution
img = Image.open(path)
w, h = img.size

# Compute scaling factors
scale_w = MAX_PORTRAIT_WIDTH / w
scale_h = MAX_PORTRAIT_HEIGHT / h
scale = min(scale_w, scale_h, 1.0)  # Never upscale

# Compute new size
new_w = int(w * scale)
new_h = int(h * scale)

# Resize using LANCZOS resampling
resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
```

### 3. Updated `_display_portrait()`
Now calls `_load_portrait_bounded()` instead of `PortraitHelper.load_portrait_image()`

## Behavior

### Tall Portrait (400x900 _cas variant)
- Old: Aggressively shrunk to fit in 180x240 box
- New: Scales to 133x300 (fills height, preserves aspect ratio)

### Square Portrait (512x512)
- Old: Shrunk to 180x180
- New: Scales to 220x220 (larger, fills width limit)

### Wide Portrait (900x400)
- Old: Shrunk to 180x80
- New: Scales to 220x98 (larger, fills width limit)

### Small Portrait (100x150)
- Old: Could be upscaled
- New: Remains 100x150 (no upscaling)

## What Was NOT Changed

- Main character window portrait display (still uses `PortraitHelper.load_portrait_image()` with 250x250)
- Portrait file resolution logic
- `_cas` vs default portrait selection
- Any other UI layout or widgets

## Testing

Created comprehensive test suite (`test_bounded_portrait_scaling.py`) with 11 tests:
- ✓ Tall portrait scaling
- ✓ Square portrait scaling
- ✓ Wide portrait scaling
- ✓ No upscaling of small portraits
- ✓ Portraits within limits not scaled
- ✓ Aspect ratio preservation
- ✓ No zero dimensions
- ✓ Edge cases (exact limits, exceeding both limits)

**Total Tests**: 93 (82 original + 11 new)
**Pass Rate**: 100% ✓

## Acceptance Criteria Met

✓ Portrait keeps original aspect ratio
✓ Portrait scaled as large as possible
✓ Portrait never exceeds MAX_PORTRAIT_WIDTH × MAX_PORTRAIT_HEIGHT
✓ No cropping
✓ No distortion
✓ No excessive shrinking
✓ No upscaling of small portraits
✓ Bounded scaling algorithm implemented exactly as specified
✓ Only Character Detail Window modified (main window unchanged)
