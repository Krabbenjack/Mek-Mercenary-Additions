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
