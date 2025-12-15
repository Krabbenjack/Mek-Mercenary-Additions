# MekHQ Social Simulator

A modular Python system for simulating social interactions within a MekHQ-inspired military campaign. It models dynamic relationships between characters, including personality synergy, age differences, professions, TO&E (Table of Organization & Equipment) structure, and everyday social encounters.

**Supported MekHQ Version: 5.10+ only**

This version removes backward compatibility with MekHQ 5.7 and older formats to provide clean, consistent support for the MekHQ 5.10 data schema.

---

## 🚀 Features

### Personnel Export
- **Full personnel data extraction** from MekHQ 5.10 campaign files (.cpnx/.cpnx.gz)
- **Personality traits export** with MekHQ 5.10 extended trait indices (0-6 range)
  - Aggression, Ambition, Greed, Social traits
  - Personality quirks
  - Personality descriptions and interview notes
- **AToW (A Time of War) attributes and abilities**
- **Awards, logs, and injuries**
- **Portrait extraction** with category and filename
- **Family relationships** (spouse, children, parents, siblings)

### Campaign Metadata Export (NEW)
- **Campaign date extraction** - Current in-game date from MekHQ campaign
- **Rank system extraction** - Rank system code (SLDF, AFFS, LCAF, etc.)
- **Automatic rank name resolution** - Converts numeric rank IDs to human-readable names
- **One-click import** - Load campaign date and rank system directly from .cpnx files

### TO&E Export (MekHQ 5.10 Schema)
- **Full TO&E extraction** using the MekHQ 5.10 `mothballInfo` schema
- **Units with crew roles**:
  - Driver, Gunner, Commander, Navigator, Tech
  - Vessel crew (multiple personnel)
- **Force hierarchy** with:
  - Force ID, Name, Parent Force
  - `forceType` (Combat, Support, Transport, Security, Salvage)
  - `formationLevel` (Company, Lance, Team, etc.)
  - `preferredRole` (FRONTLINE, etc.) - **new in 5.10**
  - Force commander reference
- **Unit metadata**:
  - Chassis, Model, Type
  - Commander flag, External ID
  - Altitude, Maintenance Multiplier
  - Mothballed status

### GUI Application
- **Tree view** of all characters grouped by Force → Unit
- **Character detail panel** displaying:
  - Basic info (name, callsign, age, birthday, profession)
  - TO&E assignment (unit name, force name, force type)
  - Formation level and preferred role (5.10 fields)
  - Crew role assignment
  - Personality traits (scaled 0-100)
  - Relationships with other characters
- **Portrait display** with automatic path resolution
- **Partner list** sorted by social modifier

### Social Interaction Simulation
- **Random 2d6-based social encounters**
- **Social modifiers** based on:
  - Unit/Force affiliation
  - Profession compatibility
  - Age group similarity
  - Personality trait synergy
- **Friendship & rivalry development** (-100 to +100 scale)
- **Daily interaction point system** with reset
- **Interaction rolls** (random & manual)

### Event & Calendar System
- **Calendar integration** with date picker
- **Event management system**:
  - Predefined event types (Field Training, Simulator Training, Equipment Maintenance)
  - Recurrence patterns (Once, Daily, Monthly, Yearly)
  - Event creation, editing, and deletion via GUI
  - Persistent JSON storage
  - Automatic event count display on calendar

---

## 📁 Project Structure

```
mekhq_social_sim/
├── config/
│   ├── core_config.json           # Base interaction and friendship settings
│   ├── modifiers_config.json      # Social modifier configurations
│   └── traits_config.json         # Personality trait definitions
│
├── src/
│   ├── mekhq_personnel_exporter.py  # MekHQ 5.10 campaign data exporter
│   ├── data_loading.py              # JSON to Character/TO&E importer
│   ├── models.py                    # Character, UnitAssignment data models
│   ├── gui.py                       # Main tkinter GUI application
│   │
│   ├── config_loader.py             # Configuration loading utilities
│   ├── interaction_pool.py          # Daily interaction point system
│   ├── roll_engine.py               # 2d6 roll mechanics
│   ├── social_modifiers.py          # Social modifier calculations
│   ├── personality_synergy.py       # Trait synergy calculations
│   │
│   ├── events/                      # Event system package
│   │   ├── __init__.py
│   │   ├── persistence.py           # JSON save/load for events
│   │   ├── manager.py               # EventManager with refresh hooks
│   │   └── dialogs.py               # GUI dialogs for event management
│   │
│   └── merk_calendar/               # Calendar system package
│       ├── __init__.py
│       ├── calendar_system.py       # Core calendar implementation
│       └── widget.py                # Embeddable calendar widget
│
├── tests/
│   ├── test_exporter.py             # Exporter tests (MekHQ 5.10)
│   ├── test_importer.py             # Importer tests
│   └── test_gui_data.py             # GUI data structure tests
│
├── exports/                         # Default export output directory
└── images/                          # Image assets
```

---

## 🛠 Installation

### Requirements
- Python 3.10+
- tkinter (standard library, for GUI)
- Optional: Pillow (PIL) for portrait image display

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-name/Mek-Mercenary-Additions.git
   cd Mek-Mercenary-Additions
   ```

2. **Install optional dependencies** (for portrait images)
   ```bash
   pip install Pillow
   ```

3. **Run the GUI**
   ```bash
   cd mekhq_social_sim/src
   python gui.py
   ```

---

## 📦 Exporting MekHQ Campaign Data

### Step 1: Export Campaign from MekHQ
1. Open your campaign in MekHQ 5.10+
2. The campaign file is saved as `.cpnx` or `.cpnx.gz`

### Step 2: Run the Exporter
```bash
cd mekhq_social_sim/src
python mekhq_personnel_exporter.py
```

This opens a file dialog to select your campaign file and exports:
- `exports/personnel_complete.json` - Personnel data with traits
- `exports/toe_complete.json` - TO&E structure with units

### Output JSON Structure

#### personnel_complete.json
```json
[
  {
    "id": "uuid",
    "name": {"given": "John", "surname": "Doe", "callsign": "Bulldog", "full_name": "John Doe"},
    "primary_role": "MEKWARRIOR",
    "rank": "12",
    "status": "ACTIVE",
    "birthday": "2961-06-22",
    "personality": {
      "aggression": "ASSERTIVE",
      "aggressionDescriptionIndex": 2,
      "ambition": "AMBITIOUS",
      "ambitionDescriptionIndex": 4,
      "social": "FRIENDLY",
      "socialDescriptionIndex": 5,
      "description": "...",
      "interview_notes": "..."
    },
    "attributes": {"atow_strength": 5, "atow_reflexes": 6},
    "skills": {"Piloting/Mech": 4, "Gunnery/Mech": 3},
    "portrait": {"category": "Male/MekWarrior/", "filename": "MW_M_26.png"},
    "relationships": {"partner": "uuid", "children": ["uuid1", "uuid2"]}
  }
]
```

#### toe_complete.json
```json
{
  "forces": [
    {
      "id": "0",
      "name": "Alpha Company",
      "formation_level": "Company",
      "force_type": 0,
      "preferred_role": "FRONTLINE",
      "force_commander_id": "uuid",
      "units": ["unit-uuid-1", "unit-uuid-2"],
      "sub_forces": [
        {
          "id": "1",
          "name": "Able Lance",
          "formation_level": "Lance",
          "force_type": 0,
          "preferred_role": "FRONTLINE",
          "units": ["unit-uuid-3", "unit-uuid-4"],
          "sub_forces": []
        }
      ]
    }
  ],
  "units": [
    {
      "id": "unit-uuid-1",
      "entity": {"chassis": "Victor", "model": "VTR-9B", "type": "Biped", "commander": "false"},
      "forceId": "1",
      "maintenanceMultiplier": 4,
      "crew": {
        "driverId": "person-uuid-1",
        "gunnerId": "person-uuid-1",
        "techId": "person-uuid-2"
      }
    }
  ]
}
```

---

## 🖥 Using the GUI

### Import Campaign Metadata (NEW)
1. Click **File → Import → Import Campaign Meta (Date & Rank System)**
2. Select your MekHQ campaign file (.cpnx or .cpnx.gz)
3. The campaign date is automatically loaded into the date field (remains editable)
4. The rank system is loaded and personnel ranks are resolved to human-readable names
5. If personnel are already loaded, their rank names will be updated immediately

**Benefits:**
- Sets the correct in-game date for your campaign
- Displays proper rank names (e.g., "Lieutenant", "Captain") instead of numeric IDs
- Ensures rank names match your campaign's rank system (SLDF, AFFS, etc.)

### Import Personnel
1. Click **File → Import → Import Personnel (JSON)**
2. Select `personnel_complete.json`
3. Characters are loaded into the tree view
4. If rank system was previously loaded, rank names are automatically resolved

### Import TO&E
1. First import personnel
2. Click **File → Import → Import TO&E (JSON)**
3. Select `toe_complete.json`
4. Characters are grouped by Force → Unit

### Character Details
- Click a character in the tree view to see details
- Right-click a character for the full detail dialog
- Details include:
  - **Rank** (human-readable name when rank system is loaded)
  - Name, Callsign, Age, Birthday, Profession
  - TO&E Assignment (Unit, Force, Force Type, Formation Level, Preferred Role, Crew Role)
  - Personality Traits (scaled 0-100)
  - Relationships

### Social Interactions
- Select a character and click **"Zufälliger Partner-Wurf"** for random interaction
- Select a partner from the list and click **"Manueller Wurf"** for targeted interaction
- Click **"Nächster Tag"** to reset interaction points

### Calendar & Events
- Click the date display to open the calendar
- Right-click on calendar days to add/manage events
- Events persist between sessions

---

## 📊 Technical Documentation

### Data Flow
```
MekHQ Campaign (.cpnx/.cpnx.gz)
    │
    ▼
mekhq_personnel_exporter.py
    │
    ├── parse_personnel() ──────► personnel_complete.json
    │
    ├── parse_forces() ─────────┐
    │   parse_units() ──────────┤
    │                           ├─► toe_complete.json
    │                           │
    └── parse_campaign_metadata()─► campaign_meta.json
                                    (date + rank system)
    │
    ▼
GUI Application
    │
    ├── load_campaign() ────► Loads personnel with rank resolution
    │
    ├── apply_toe_structure() ─► Assigns units and forces
    │
    └── import_campaign_meta() ─► Sets date and rank system
```

### Rank Resolution System

### TO&E Mapping Logic (MekHQ 5.10)

**Unit → Force Assignment:**
- Units reference forces via `mothballInfo.forceID`
- Forces maintain a list of unit IDs (populated during export)

**Person → Unit Assignment:**
- Persons are assigned to units via `crew` roles in `mothballInfo`:
  - `driverId` → "driver"
  - `gunnerId` → "gunner"
  - `commanderId` → "commander"
  - `navigatorId` → "navigator"
  - `techId` → "tech"
  - `vesselCrewIds[]` → "crew"

### Personality Trait Mapping

MekHQ 5.10 uses extended trait index ranges:

| Trait | Index Range | Example Values |
|-------|-------------|----------------|
| Aggression | 0-5 | NONE, TIMID, ASSERTIVE, AGGRESSIVE, BLOODTHIRSTY, DETERMINED |
| Ambition | 0-5 | NONE, ASPIRING, GOAL_ORIENTED, COMPETITIVE, AMBITIOUS, DRIVEN |
| Greed | 0-6 | NONE, GENEROUS, HOARDING, PROFITABLE, FRAUDULENT, MERCENARY, LUSTFUL |
| Social | 0-6 | NONE, AUTHENTIC, DISINGENUOUS, RESERVED, CONDESCENDING, FRIENDLY, ENCOURAGING |

Out-of-range indices return `UNKNOWN_<index>`.

### Force Type Mapping

| Integer | Name |
|---------|------|
| 0 | Combat |
| 1 | Support |
| 2 | Transport |
| 3 | Security |
| 4 | Salvage |

---

## 🧪 Running Tests

```bash
cd mekhq_social_sim
python -m unittest discover -s tests -v
```

Tests cover:
- Exporter: Campaign loading, personnel/forces/units parsing, JSON export
- Importer: Character loading, TO&E application, crew role mapping
- GUI data: Model classes, tree view grouping, detail display

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 🔄 Migration from MekHQ 5.7

If you have JSON files exported from MekHQ 5.7 or older:
1. Re-export your campaign using MekHQ 5.10+
2. Use the updated exporter to generate new JSON files
3. Import the new JSON files into the GUI

Legacy fields like `unit_id` and `force_id` on personnel are no longer used. All TO&E information comes from the `mothballInfo` structure in units.
