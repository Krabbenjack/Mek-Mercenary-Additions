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
- Fluff text generation for interactions (narrative descriptions)

### ✔ Modular Design
- Each logic component in its own file
- Configurable through JSON
- Trait list fully customizable
- Easily extendable

### ✔ Calendar System
- Full calendar with date navigation
- Date picker dialog (left-click on date)
- Detailed calendar view (right-click on date)
- Event management with recurrence types:
  - Once, Daily, Weekly, Monthly, Yearly
- Event creation, display, and removal
- Birthday tracking for characters
- Dynamic age calculation based on current date
- Age modifiers updated automatically

### ✔ GUI
- **Tabbed interface**:
  - Main view tab (Hauptansicht)
  - Events tab (Ereignisse) for fluff text and narrative logs
- Tree view of all characters grouped by Force/Unit
- Character detail panel with:
  - Name, callsign, age, birthday
  - Profession and unit assignment
  - Personality traits
  - Relationship list (top 10)
- Partner list sorted by social modifier
- Manual and random interaction rolls
- Popup log window (separate window for interaction logs)
- Day progression with date display
- Daily events summary bar

### ✔ MekHQ Import/Export
- **Exporter** (`mekhq_personnel_exporter.py`):
  - Loads `.cpnx` and `.cpnx.gz` campaign files
  - Parses personnel with full data extraction:
    - Names, skills, attributes
    - Personality traits (Aggression, Ambition, Greed, Social, Quirks)
    - Awards, injuries, relationships
  - Parses TO&E structure (Forces hierarchy + Units)
  - Exports to separate JSON files:
    - `personnel_complete.json`
    - `toe_complete.json`
- **Importer** (`data_loading.py`):
  - Loads personnel JSON and converts to Character objects
  - Scales personality traits from index to 0-100 values
  - Applies TO&E structure with UnitAssignment
- **Personality Trait Enums**:
  - AGGRESSION: NONE, TIMID, ASSERTIVE, AGGRESSIVE, BLOODTHIRSTY
  - AMBITION: NONE, ASPIRING, COMPETITIVE, AMBITIOUS, DRIVEN
  - GREED: NONE, GREEDY, AVARICIOUS
  - SOCIAL: NONE, RECLUSIVE, RESERVED, SOCIABLE, GREGARIOUS, VERBOSE
  - QUIRKS: NONE, HONEST, DISHONEST, OPTIMISTIC, PESSIMISTIC, PRAGMATIC, INNOVATIVE, TRADITIONAL, REBELLIOUS, DISCIPLINED

---

## 📁 Project Structure

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
│   │   ├── data_loading.py        # Campaign data loading and import
│   │   ├── interaction_pool.py    # Daily interaction point system
│   │   ├── roll_engine.py         # 2d6 roll mechanics
│   │   ├── social_modifiers.py    # Social modifier calculations
│   │   ├── personality_synergy.py # Trait synergy calculations
│   │   ├── mekhq_personnel_exporter.py  # MekHQ data export tool
│   │   └── merk_calendar/         # Calendar system module
│   │       ├── _init_.py
│   │       ├── calendar_system.py # Event management and calendar logic
│   │       └── widget.py          # Calendar UI widgets
│   │
│   ├── exports/                   # Exported campaign data (JSON)
│   └── images/                    # Image assets
│
├── .github/
│   └── copilot-instructions.md    # Copilot coding guidelines
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Krabbenjack/Mek-Mercenary-Additions.git
cd Mek-Mercenary-Additions
```

### 2. Requirements

- Python 3.x
- tkinter (included in standard Python installation)

No additional dependencies required.

### 3. Launch the GUI

```bash
cd mekhq_social_sim/src
python gui.py
```

---

## 📦 Importing MekHQ Campaign Data

### Step 1: Export from MekHQ
1. Export your `.cpnx` file from MekHQ

### Step 2: Run the Exporter
```bash
cd mekhq_social_sim/src
python mekhq_personnel_exporter.py
```
A file dialog will open to select your `.cpnx` or `.cpnx.gz` file.

Alternatively, specify the path directly:
```bash
python mekhq_personnel_exporter.py path/to/campaign.cpnx -o ../exports
```

### Step 3: Load in GUI
1. Launch `gui.py`
2. Click "Importiere Personal (JSON)" → select `personnel_complete.json`
3. Click "Importiere TO&E (JSON)" → select `toe_complete.json`

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
- Each character receives daily interaction points (default: 3)
- Reset via "Nächster Tag" button in GUI

### **🔹 Calendar System (`merk_calendar/`)**
- EventManager handles event storage and recurrence calculation
- DatePickerDialog for date selection
- DetailedCalendarWindow for monthly view with events
- Integration with main GUI for date display and navigation

---

## 🗺 Roadmap (Planned Features)

### 🔥 1. Weekly Schedules
- Monday–Sunday routines
- Tasks: Training, Maintenance, Free time, Missions
- Influences interaction frequency

### 🔥 2. Advanced Event System
- Random events
- Special interactions
- Conflict triggers, loyalty swings, drama events

### 🔥 3. Export & Analysis Tools
- Relationship history saving
- Graph-based visualization

### 🔥 4. Event Persistence
- Save/load events to JSON or database
- Campaign-wide event history

---

## 📜 License

This project is licensed under the **MIT License**.

---
