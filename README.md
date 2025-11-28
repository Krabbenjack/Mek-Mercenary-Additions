# MekHQ Social Simulator (Python 3)

A modular Python system for simulating social interactions within a MekHQ-inspired military campaign.  
Its goal is to model dynamic relationships between characters, including personality synergy, age differences, professions, TO&E structure, and everyday social encounters.

The project includes a configurable interaction engine, a graphical user interface, and import tools for real MekHQ campaign files.

---

## 🧩 Features

### ✔ Interaction Engine
- Random 2d6-based social encounters  
- Social modifiers based on:
  - Unit / Force  
  - Profession  
  - Age group  
  - Personality trait synergy  
- Friendship & rivalry development  
- Daily interaction point system

### ✔ Modular Design
- Each logic component in its own file  
- Configurable through JSON  
- Trait list fully customizable  
- Easily extendable (e.g., calendar system, weekly schedules, events)

### ✔ GUI
- Tree view of all characters grouped by Force/Unit  
- Character detail panel  
- Partner list sorted by social modifier  
- Button to trigger random interactions  
- Log window  
- Day progression & interaction point reset

### ✔ MekHQ Import
- `mekhq_personnel_exporter.py`  
- Extracts:
  - Personnel  
  - Traits  
  - TO&E  

---

## 📋 Newly added functions (auto-detected)

- mekhq_social_sim/src/mekhq_personnel_exporter.py
  - parse_personnel(root: ET.Element) -> List[Dict[str, Any]]: Extract personnel entries from a MekHQ campaign XML root.
  - parse_abilities(person: ET.Element) -> Dict[str, str]: Extract special abilities (SPAs) from a person element.
  - parse_attributes(person): Parse character attributes.
  - parse_skills(person): Parse skill entries.
  - parse_personality(person): Extract personality traits and quirks.
  - parse_awards(person): Extract awards and decorations.
  - parse_logs(person): Extract personal log entries.
  - parse_injuries(person): Extract injury records.
  - parse_portrait(person): Find portrait/portrait path for a person.
  - parse_relationships(person): Extract relationships to other characters.
  - parse_forces(root): Extract Forces structure from campaign file.
  - parse_units(root): Extract Units list from campaign file.
  - count_forces_recursive(forces: List[Dict[str, Any]]) -> int: Helper to count forces including nested sub-forces.
  - export_personnel_to_json(personnel_data: List[Dict[str, Any]], output_path: str = "exports/personnel_complete.json") -> str: Export personnel JSON to disk.
  - export_toe_to_json(forces_data, units_data, output_path: str = "exports/toe_complete.json") -> str: Export TO&E JSON to disk.
  - print_summary(personnel_data): Print a summary of parsed personnel.
  - main(): CLI / GUI entry that orchestrates loading, parsing, and exporting.

- mekhq_social_sim/src/config_loader.py
  - _load_json(name: str) -> Dict[str, Any]: Load JSON config file with safe fallback.
  - _get(cfg: Dict[str, Any], keys: List[str], default: Any) -> Any: Helper to traverse nested config keys.
  - base_interaction_points() -> int: Config accessor for base interaction points.
  - friendship_step_positive() -> int: Config accessor for positive friendship change step.
  - friendship_step_negative() -> int
  - friendship_min() -> int
  - friendship_max() -> int
  - base_target() -> int
  - min_target() -> int
  - max_target() -> int

- mekhq_social_sim/src/social_modifiers.py
  - combined_social_modifier(a: Character, b: Character) -> Tuple[int, Dict[str, str]]: Calculate combined social modifier and breakdown.
  - _unit_modifier(a, b): Internal unit modifier calculation.
  - _profession_modifier(a, b): Internal profession modifier calculation.
  - _age_group_modifier(a, b): Internal age group modifier calculation.
  - trait_synergy_modifier(a, b): Compute personality trait synergy modifier and details.

- mekhq_social_sim/src/gui.py (MekSocialGUI class methods)
  - _import_personnel(self) -> None: GUI handler to import personnel JSON and update UI.
  - _import_toe(self) -> None: GUI handler to import TO&E JSON and apply to characters.
  - _next_day(self) -> None: Advance simulation day, update ages, reset pools.
  - _trigger_manual_roll(self) -> None: Perform a manual interaction roll between selected characters.
  - _trigger_random_roll(self) -> None: Perform a random interaction roll.
  - _generate_fluff(self, result) -> str: Generate narrative fluff text for an interaction result.
  - _describe_event(self, event) -> str: Describe calendar/event entries for UI.

- mekhq_social_sim/src/merk_calendar/__init__.py
  - Re-exports: MainCalendarWindow, DetailedCalendarWindow, EventManager, Event, RecurrenceType (package __all__ entries)

- mekhq_social_sim/src/merk_calendar/widget.py
  - CalendarWidget (tk.Frame subclass) that integrates DatePickerDialog, DetailedCalendarWindow, EventManager.

---

## 📁 Project Structure

```
/
├── mekhq_social_sim/
│   ├── config/
│   │   ├── core_config.json
│   │   ├── modifiers_config.json
│   │   └── traits_config.json
│   │
│   └── src/
│       ├── data_loading.py
│       ├── models.py
│       ├── interaction_pool.py
│       ├── roll_engine.py
│       ├── social_modifiers.py
│       ├── personality_synergy.py
│       ├── config_loader.py
│       ├── gui.py
│       ├── mekhq_personnel_exporter.py
│       └── merk_calendar/
│           ├── __init__.py
│           ├── calendar_system.py
│           └── widget.py
│
├── README.md
└── requirements.txt  (optional)
```

---

## 🚀 Installation

### 1. Clone the Repository

```
git clone https://github.com/<your-name>/<your-repo>.git
cd <your-repo>
```

### 2. Install Optional Dependencies

If you add a `requirements.txt` later:

```
pip install -r requirements.txt
```

### 3. Launch the GUI

```
python mekhq_social_sim/src/gui.py
```

---

## 📦 Importing MekHQ Campaign Data

1. Export your `.cpnx` file from MekHQ  
2. Run the exporter:

```
python mekhq_social_sim/src/mekhq_personnel_exporter.py path/to/campaign.cpnx -o exports
```

3. Load the following in the GUI:
   - `personnel_complete.json`
   - (optional) `toe_complete.json`

---

## 🧠 Technical Core Concepts

### **🔹 Social Modifiers (`social_modifiers.py`)**
Combines TO&E hierarchy, professions, age groups, and personality traits.

### **🔹 Trait Synergy (`personality_synergy.py`)**
Computes a bonus/penalty based on similarity of character traits (configurable).

### **🔹 Relationship System (`models.py`)**
- Friendship scale −100 to +100  
- Variable progression for success/failure  
- Automatic clamping

### **🔹 Interaction Pool (`interaction_pool.py`)**
- Each character receives daily interaction points  
- Reset via “Next Day” button in GUI

---

## 🗺 Roadmap (Planned Features)

### 🔥 1. Calendar System (in progress)
- Birthdays for characters  
- Automatic aging system  
- GUI date display  
- Age modifiers updated dynamically

### 🔥 2. Weekly Schedules
- Monday–Sunday routines  
- Tasks: Training, Maintenance, Free time, Missions  
- Influences interaction frequency

### 🔥 3. Event System
- Random events  
- Special interactions  
- Conflict triggers, loyalty swings, drama events

### 🔥 4. Export & Analysis Tools
- Relationship history saving  
- Graph-based visualization

---

## 📜 License

This project is licensed under the **MIT License**.

---
