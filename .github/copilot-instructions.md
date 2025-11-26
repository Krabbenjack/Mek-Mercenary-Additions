# Mek-Mercenary-Additions — Copilot Instructions

## Project Overview

Mek-Mercenary-Additions is a modular Python system for simulating social interactions within a MekHQ-inspired military campaign. It models dynamic relationships between characters, including personality synergy, age differences, professions, TO&E (Table of Organization & Equipment) structure, and everyday social encounters.

The project includes:
- A configurable interaction engine with 2d6-based social encounters
- A graphical user interface (tkinter) for character management and interaction simulation
- Import tools for real MekHQ campaign files (.cpnx format)
- A calendar system with event management

### Directory Structure

```
Mek-Mercenary-Additions/
├── mekhq_social_sim/
│   ├── config/                    # JSON configuration files
│   │   ├── core_config.json       # Base interaction and friendship settings
│   │   ├── modifiers_config.json  # Social modifier configurations
│   │   └── traits_config.json     # Personality trait definitions
│   │
│   ├── src/                       # Python source code
│   │   ├── gui.py                 # Main tkinter GUI application
│   │   ├── models.py              # Character and UnitAssignment data models
│   │   ├── config_loader.py       # Configuration loading utilities
│   │   ├── data_loading.py        # Campaign data loading
│   │   ├── interaction_pool.py    # Daily interaction point system
│   │   ├── roll_engine.py         # 2d6 roll mechanics
│   │   ├── social_modifiers.py    # Social modifier calculations
│   │   ├── personality_synergy.py # Trait synergy calculations
│   │   ├── mekhq_personnel_exporter.py  # MekHQ data export tool
│   │   └── merk_calendar/         # Calendar system module
│   │       ├── _init_.py
│   │       ├── calendar_system.py
│   │       └── widget.py
│   │
│   ├── exports/                   # Exported campaign data
│   └── images/                    # Image assets
│
├── README.md
├── LICENSE
└── .gitignore
```

## Tech Stack & Dependencies

- **Language**: Python 3.x
- **GUI Framework**: tkinter (standard library)
- **Data Format**: JSON for configuration and data files

### Running the Application

1. Ensure Python 3.x is installed
2. Navigate to the `mekhq_social_sim/src` directory
3. Run the GUI: `python gui.py`

### Importing MekHQ Data

1. Export your `.cpnx` file from MekHQ
2. Run the exporter:
   ```bash
   python mekhq_personnel_exporter.py path/to/campaign.cpnx -o exports
   ```
3. Load the exported JSON files in the GUI

## Coding & Style Guidelines

- Use consistent 4-space indentation (Python standard)
- Follow PEP 8 naming conventions
- Use type hints for function parameters and return values (already used in the codebase)
- Use dataclasses for data models (see `models.py`)
- Keep imports organized: standard library first, then local modules
- Write docstrings for public functions and classes
- Comments should be in English for code, though UI text may be in German

### Configuration Files

When modifying config/data files (JSON):
- Preserve the existing structure and formatting
- Do not reorder or remove unrelated fields unless necessary
- Ensure values are valid JSON types

### Key Concepts

- **Friendship Scale**: −100 to +100, with configurable step values
- **Interaction Points**: Daily allocation per character, reset on day advance
- **Social Modifiers**: Combine TO&E hierarchy, professions, age groups, and personality traits
- **Trait Synergy**: Bonus/penalty based on similarity of character traits

### MekHQ Data Export/Import Functions

The project provides comprehensive functionality for extracting data from MekHQ campaign files (.cpnx) and importing them into the GUI.

#### Export Functions (`mekhq_personnel_exporter.py`)

| Function | Description |
|----------|-------------|
| `load_cpnx(path)` | Loads a MekHQ campaign file (.cpnx or .cpnx.gz), returns XML root element |
| `parse_personnel(root)` | Extracts all personnel data (name, skills, attributes, personality traits, awards, injuries, relationships) |
| `parse_forces(root)` | Extracts TO&E force hierarchy with sub-forces and unit references |
| `parse_units(root)` | Extracts all units with entity data, crew IDs (driverId, gunnerId, etc.), and force assignments |
| `export_personnel_to_json(data, path)` | Exports personnel data to `personnel_complete.json` |
| `export_toe_to_json(forces, units, path)` | Exports TO&E structure to `toe_complete.json` |

**Personality Trait Enums**: The exporter converts MekHQ trait indices to human-readable names:
- `AGGRESSION_TRAITS`: NONE, TIMID, ASSERTIVE, AGGRESSIVE, BLOODTHIRSTY
- `AMBITION_TRAITS`: NONE, ASPIRING, COMPETITIVE, AMBITIOUS, DRIVEN
- `GREED_TRAITS`: NONE, GREEDY, AVARICIOUS
- `SOCIAL_TRAITS`: NONE, RECLUSIVE, RESERVED, SOCIABLE, GREGARIOUS, VERBOSE

#### Import Functions (`data_loading.py`)

| Function | Description |
|----------|-------------|
| `load_personnel(path)` | Loads `personnel_complete.json` and converts entries to `Character` objects with scaled personality traits (0-100) |
| `apply_toe_structure(path, characters)` | Applies TO&E from `toe_complete.json` to existing `Character` objects, assigning `UnitAssignment` |
| `load_campaign(personnel_path, toe_path)` | Convenience function that loads personnel and optionally applies TO&E |

#### GUI Import Handlers (`gui.py`)

| Method | Description |
|--------|-------------|
| `_import_personnel()` | Opens file dialog to select `personnel_complete.json`, loads characters, resets interaction pools, updates tree view |
| `_import_toe()` | Opens file dialog to select `toe_complete.json`, applies TO&E structure to loaded characters, refreshes tree view |

**Data Flow**:
1. User exports `.cpnx` from MekHQ
2. `mekhq_personnel_exporter.py` parses XML and generates `personnel_complete.json` + `toe_complete.json`
3. GUI loads personnel via `_import_personnel()` → `load_campaign()` → `load_personnel()`
4. GUI applies TO&E via `_import_toe()` → `apply_toe_structure()`

## Testing & Validation

- After code or config changes, verify that the GUI loads correctly
- Ensure no runtime errors or crashes when:
  - Loading personnel JSON files
  - Applying TO&E structure
  - Performing random/manual interactions
  - Advancing days
- If changes affect social modifiers or balancing, ensure values are within reasonable bounds

## What Copilot Should Do & What to Avoid

### ✅ Allowed / Recommended Tasks

- Implement new features as described in issues or TODOs
- Fix bugs in social simulation logic or GUI
- Add new configuration options while preserving existing structure
- Improve code readability and maintainability
- Add type hints to existing code
- Update or add documentation and comments
- Refactor code to reduce duplication

### ⚠️ Not Recommended / Sensitive Tasks

- Large-scale refactoring of the GUI layout or core simulation engine
- Changing the friendship/interaction point formulas without clear requirements
- Modifying the MekHQ import/export logic (requires MekHQ compatibility testing)
- Removing or significantly altering existing configuration options
- Changes that would break backwards compatibility with existing exported data

## Communication & Collaboration Guidelines

- When assigning tasks, provide clear, well-scoped descriptions with acceptance criteria
- Use PR comments to provide feedback on code changes
- For larger or risky changes, request manual review before merging
- Copilot is best suited for incremental changes, routine enhancements, bug fixes, and documentation
