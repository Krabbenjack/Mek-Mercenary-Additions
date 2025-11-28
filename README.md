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
- Calendar integration with date picker and detailed month view
- Event management system with:
  - Right-click context menu on calendar days
  - Event creation with predefined types (Field Training, Simulator Training, Equipment Maintenance)
  - Event recurrence patterns (Once, Daily, Monthly, Yearly)
  - Event editing and deletion
  - Persistent storage (JSON)
  - Automatic event count display on calendar

### ✔ MekHQ Import
- `mekhq_personnel_exporter.py`  
- Extracts:
  - Personnel  
  - Traits  
  - TO&E  

---

## 📁 Project Structure

```
/
├── config/
│   ├── core_config.json
│   ├── modifiers_config.json
│   └── traits_config.json
│
├── src/
│   ├── events/                  # Event system package
│   │   ├── __init__.py
│   │   ├── persistence.py       # JSON save/load for events
│   │   ├── manager.py           # EventManager with refresh hooks
│   │   └── dialogs.py           # GUI dialogs for event management
│   │
│   ├── merk_calendar/           # Calendar system package
│   │   ├── __init__.py
│   │   ├── calendar_system.py   # Core calendar implementation
│   │   └── widget.py            # Embeddable calendar widget
│   │
│   ├── data_loading.py
│   ├── models.py
│   ├── interaction_pool.py
│   ├── roll_engine.py
│   ├── social_modifiers.py
│   ├── personality_synergy.py
│   ├── config_loader.py
│   ├── gui.py
│   └── mekhq_personnel_exporter.py
│
├── README.md
└── requirements.txt  (optional)
```

> Tip: You can move the Python files into a `src/` directory later if you prefer.

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
python gui.py
```

---

## 📅 Using the Event System

The event system allows you to schedule and track unit activities with recurrence patterns.

### Adding Events

1. **From the Main GUI**: Click on the date display (top bar) with right-click to open the calendar view
2. **In the Calendar View**: Right-click on any day to see the context menu:
   - **Add Event**: Create a new event for that day
   - **Manage Events**: View, edit, or delete existing events

### Event Types

Three predefined event types are available:
- **Field Training (Infantry)**: Ground troop training exercises
- **Simulator Training (MekWarrior)**: BattleMech simulation sessions
- **Equipment Maintenance (Tech)**: Regular maintenance schedules

### Recurrence Patterns

Events can repeat automatically:
- **Once**: Event occurs only on the selected date
- **Daily**: Event repeats every day from the start date
- **Monthly**: Event repeats on the same day of each month
- **Yearly**: Event repeats on the same date each year

### Event Storage

Events are automatically saved to `~/.mekhq_social_sim/events.json` and persist between sessions.

---

## 📦 Importing MekHQ Campaign Data

1. Export your `.cpnx` file from MekHQ  
2. Run the exporter:

```
python mekhq_personnel_exporter.py path/to/campaign.cpnx -o exports
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
### **🔹 Event System (`src/events/`)**
- **EventManager**: Centralized event management with JSON persistence
- **Event Types**: Predefined activities (Field Training, Simulator Training, Equipment Maintenance)
- **Recurrence**: Flexible patterns (Once, Daily, Monthly, Yearly)
- **Persistence**: Automatic save/load to JSON
- **Refresh Hooks**: UI components can register callbacks for automatic updates


---

## 🗺 Roadmap (Planned Features)

### ✅ 1. Calendar System (COMPLETED)
- ✓ Birthdays for characters  
- ✓ Automatic aging system  
- ✓ GUI date display  
- ✓ Age modifiers updated dynamically
- ✓ Event system with persistence (JSON storage)
- ✓ Predefined event types (Field Training, Simulator Training, Equipment Maintenance)
- ✓ Event recurrence (Once, Daily, Monthly, Yearly)
- ✓ Right-click context menu on calendar days
- ✓ Event creation, editing, and deletion through GUI dialogs
- ✓ Automatic event count display on calendar days

### 🔥 2. Weekly Schedules
- Monday–Sunday routines  
- Tasks: Training, Maintenance, Free time, Missions  
- Influences interaction frequency

### 🔥 3. Event System Extensions
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
