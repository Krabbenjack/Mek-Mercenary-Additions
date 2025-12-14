#!/usr/bin/env python3
"""
Test script for the new trait synergy engine.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "mekhq_social_sim" / "src"
sys.path.insert(0, str(src_path))

from data_loading import load_campaign
from trait_synergy_engine import calculate_synergy, get_character_traits_as_enums

def test_synergy():
    """Test the synergy engine with real campaign data."""
    
    # Load campaign data
    personnel_path = Path(__file__).parent / "mekhq_social_sim" / "exports" / "personnel_complete.json"
    toe_path = Path(__file__).parent / "mekhq_social_sim" / "exports" / "toe_complete.json"
    
    print("Loading campaign data...")
    characters = load_campaign(personnel_path, toe_path)
    
    print(f"Loaded {len(characters)} characters\n")
    
    # Get first two characters with traits
    chars_with_traits = [c for c in characters.values() if c.traits]
    
    if len(chars_with_traits) < 2:
        print("Not enough characters with traits to test!")
        return
    
    char_a = chars_with_traits[0]
    char_b = chars_with_traits[1]
    
    print(f"Testing synergy between:")
    print(f"  Character A: {char_a.name}")
    traits_a = get_character_traits_as_enums(char_a)
    for category, enum_str in sorted(traits_a.items()):
        print(f"    {category}: {enum_str}")
    if char_a.quirks:
        print(f"    Quirks: {', '.join(char_a.quirks)}")
    
    print(f"\n  Character B: {char_b.name}")
    traits_b = get_character_traits_as_enums(char_b)
    for category, enum_str in sorted(traits_b.items()):
        print(f"    {category}: {enum_str}")
    if char_b.quirks:
        print(f"    Quirks: {', '.join(char_b.quirks)}")
    
    print("\nCalculating synergy...")
    total_mod, breakdown = calculate_synergy(char_a, char_b)
    
    print(f"\nTotal Modifier: {total_mod:+d}")
    print("\nBreakdown:")
    for key, desc in breakdown.items():
        print(f"  {key}: {desc}")
    
    print("\n✅ Synergy engine test completed successfully!")

if __name__ == "__main__":
    test_synergy()
