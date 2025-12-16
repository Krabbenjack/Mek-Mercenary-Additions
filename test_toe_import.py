#!/usr/bin/env python3
"""
TO&E Import Test Script

This script tests the complete export/import workflow to verify
that TO&E structure is properly applied and displayed.

Usage:
    python3 test_toe_import.py

Note: Before running this test, export your campaign data using:
    - GUI: File → Export → Export Campaign Data from .cpnx...
    - CLI: python mekhq_personnel_exporter.py <campaign.cpnx> -o exports
"""

from pathlib import Path
import sys
import os

# Add src to path
script_dir = Path(__file__).resolve().parent
src_path = script_dir / "mekhq_social_sim" / "src"
sys.path.insert(0, str(src_path))
os.chdir(str(src_path))

from data_loading import load_campaign, apply_toe_structure
from rank_resolver import get_rank_resolver
from collections import defaultdict

def test_toe_import():
    """Test complete TO&E import workflow"""
    
    print("="*60)
    print("TO&E IMPORT TEST")
    print("="*60)
    print()
    print("This test verifies that TO&E import is working correctly.")
    print("Make sure you have exported campaign data first!")
    print()
    
    # Setup
    script_dir = Path(__file__).resolve().parent
    exports_dir = script_dir / "mekhq_social_sim" / "exports"
    personnel_file = exports_dir / "personnel_complete.json"
    toe_file = exports_dir / "toe_complete.json"
    
    if not personnel_file.exists():
        print("❌ ERROR: personnel_complete.json not found")
        print(f"   Expected at: {personnel_file}")
        print()
        print("Please export your campaign data first:")
        print("  - GUI: File → Export → Export Campaign Data from .cpnx...")
        print("  - CLI: cd mekhq_social_sim/src && python mekhq_personnel_exporter.py <campaign.cpnx> -o ../exports")
        return False
    
    if not toe_file.exists():
        print("❌ ERROR: toe_complete.json not found")
        print(f"   Expected at: {toe_file}")
        print()
        print("Please export your campaign data first:")
        print("  - GUI: File → Export → Export Campaign Data from .cpnx...")
        print("  - CLI: cd mekhq_social_sim/src && python mekhq_personnel_exporter.py <campaign.cpnx> -o ../exports")
        return False
    
    # Verify JSON file structure
    print("\n0. Verifying exported JSON structure...")
    import json
    with open(str(toe_file), 'r') as f:
        toe_data = json.load(f)
    
    root_forces_count = len(toe_data.get('forces', []))
    units_count = len(toe_data.get('units', []))
    
    # Count total forces recursively
    def count_all_forces(forces):
        count = len(forces)
        for force in forces:
            count += count_all_forces(force.get('sub_forces', []))
        return count
    
    total_forces_count = count_all_forces(toe_data.get('forces', []))
    
    print(f"   JSON file contains:")
    print(f"   - Root forces: {root_forces_count}")
    print(f"   - Total forces (including sub-forces): {total_forces_count}")
    print(f"   - Units: {units_count}")
    
    if total_forces_count == 0:
        print("   ❌ ERROR: No forces found in toe_complete.json!")
        return False
    
    # Step 1: Load personnel
    print("\n1. Loading personnel...")
    resolver = get_rank_resolver()
    resolver.set_rank_system('SLDF')
    
    characters = load_campaign(str(personnel_file))
    print(f"   ✅ Loaded {len(characters)} characters")
    
    chars_before = sum(1 for c in characters.values() if c.unit is not None)
    print(f"   Characters with units: {chars_before}")
    
    # Step 2: Apply TO&E
    print("\n2. Applying TO&E structure...")
    apply_toe_structure(str(toe_file), characters)
    
    chars_after = sum(1 for c in characters.values() if c.unit is not None)
    print(f"   ✅ Characters with units: {chars_after}/{len(characters)}")
    
    if chars_after == 0:
        print("   ❌ ERROR: No characters assigned to units!")
        return False
    
    # Step 3: Build tree structure (simulating GUI)
    print("\n3. Building tree structure...")
    forces = defaultdict(lambda: defaultdict(list))
    no_toe = []
    
    for char in characters.values():
        if char.unit is None:
            no_toe.append(char)
        else:
            forces[char.unit.force_name][char.unit.unit_name].append(char)
    
    print(f"   ✅ Forces found: {len(forces)}")
    print(f"   ✅ Personnel without TO&E: {len(no_toe)}")
    
    # Step 4: Display tree structure
    print("\n4. Tree structure:")
    print("   Personal (root)")
    
    for force_name in sorted(forces.keys()):
        units = forces[force_name]
        total_in_force = sum(len(chars) for chars in units.values())
        print(f"   ├── {force_name} ({total_in_force} personnel)")
        
        sorted_units = sorted(units.items())
        for i, (unit_name, chars) in enumerate(sorted_units):
            is_last = (i == len(sorted_units) - 1)
            prefix = "└──" if is_last else "├──"
            print(f"   │   {prefix} {unit_name} ({len(chars)} personnel)")
    
    print(f"   └── Ohne TO&E ({len(no_toe)} personnel)")
    
    # Step 5: Verify specific assignments
    print("\n5. Verifying specific assignments...")
    
    # Find a character we know should have an assignment
    test_chars = []
    for char in characters.values():
        if char.unit and char.unit.force_name == "Able Lance":
            test_chars.append(char)
            if len(test_chars) >= 2:
                break
    
    if test_chars:
        for char in test_chars[:2]:
            print(f"   ✅ {char.name}:")
            print(f"      Force: {char.unit.force_name}")
            print(f"      Unit: {char.unit.unit_name}")
            print(f"      Role: {char.unit.crew_role}")
    else:
        print("   ⚠️  Warning: No characters found in Able Lance")
    
    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Personnel loaded: {len(characters)}")
    print(f"✅ Characters assigned to units: {chars_after}")
    print(f"✅ Forces created: {len(forces)}")
    print(f"✅ Personnel without assignments: {len(no_toe)}")
    
    if chars_after > 0 and len(forces) > 0:
        print("\n✅ TO&E IMPORT TEST PASSED")
        return True
    else:
        print("\n❌ TO&E IMPORT TEST FAILED")
        return False

if __name__ == "__main__":
    success = test_toe_import()
    sys.exit(0 if success else 1)
