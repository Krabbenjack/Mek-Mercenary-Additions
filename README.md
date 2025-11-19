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

## 📁 Project Structure

```
/
├── config/
│   ├── core_config.json
│   ├── modifiers_config.json
│   └── traits_config.json
│
├── data_loading.py
├── models.py
├── interaction_pool.py
├── roll_engine.py
├── social_modifiers.py
├── personality_synergy.py
├── config_loader.py
├── gui.py
├── mekhq_personnel_exporter.py
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
