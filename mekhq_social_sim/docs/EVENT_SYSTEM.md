MekHQ Social & Operational Event System

Architecture & Data Contract (README)

1. Purpose

This system defines a data-driven event simulation framework for MekHQ that models:

social interactions

operational activities

relationship development

training, combat, and daily life

The system is configuration-first, logic-free in data, and designed to be interpreted by a runtime / agent, not hard-coded.

Its primary goal is to allow events to emerge from context, be resolved mechanically, and apply consequences in a controlled, inspectable way.

2. Core Design Principles
2.1 Single Source of Truth

All rules and definitions live in JSON

No game logic is embedded in config files

Python code only interprets config

2.2 Layered Architecture

The system is explicitly layered.
Each layer answers one question only.

Layer	Question
1	What events exist?
2	Who can participate & what can happen?
3	How is it mechanically resolved?
4	What are the consequences?

No layer skips another.

3. Canonical Flow (High Level)
Time Tick
  → Event Selection (Injector)
    → Interaction Selection
      → Tone & Environment Modifiers
        → Mechanical Resolution (Skill Rolls)
          → Outcomes Applied
            → Relationship / State Update
              → UI Update

4. Folder Structure (Authoritative)
config/
└── events/
    ├── eventlist.json
    ├── event_environment_list.json
    ├── meta/
    │   └── age_groups.json
    ├── injector_rules/
    │   ├── injector_selection_rules_social.json
    │   ├── injector_selection_rules_youth_social.json
    │   ├── injector_selection_rules_children_and_youth.json
    │   ├── injector_selection_rules_training.json
    │   └── injector_selection_rules_administration.json
    ├── context/
    │   ├── Interactions_social.json
    │   ├── Interactions_operational.json
    │   └── Interactions_Tones.json
    ├── resolution/
    │   ├── interaction_resolution_social.json
    │   └── interaction_resolution_operational.json
    └── outcomes/
        ├── social_outcomes.json
        └── operational_outcomes.json

docs/
└── design/
    └── operational_outcomes_explained.json

5. Layer Details
5.1 Layer 1 – Event Catalogue

Files

eventlist.json

event_environment_list.json

Defines

canonical event IDs

event categories

possible environments

Does NOT

select participants

define mechanics

apply effects

5.2 Layer 2 – Context & Selection
5.2.1 Injector Selection Rules

Files

injector_selection_rules_*.json

age_groups.json

Responsible for

who may participate

how many participants

base interaction weights

age / role / context filters

Important

This is where base probabilities live

No skill checks

No outcomes

5.2.2 Interactions

Files

Interactions_social.json

Interactions_operational.json

Defines

interaction types

participant structure (pair / group / opposed)

semantic meaning

5.2.3 Tones

File

Interactions_Tones.json

Role

numeric modifiers only

no abstraction words like “encouraged”

no generation logic

Can modify

interaction weight modifiers (numeric)

escalation likelihood (numeric)

check difficulty (numeric)

outcome multipliers (numeric)

Cannot

create interactions

override injector logic

5.2.4 Environments

File

event_environment_list.json

Role

objective, physical / organizational context

numeric modifiers only

Can modify

interaction weights

check difficulty

fatigue / XP / confidence / reputation scaling

allowed domains

5.3 Layer 3 – Mechanical Resolution

Files

interaction_resolution_social.json

interaction_resolution_operational.json

Defines

resolution stages

skill / attribute mapping

group vs opposed checks

check ordering

Uses

A Time of War dice system

existing skill infrastructure

Does NOT

apply consequences

change state

5.4 Layer 4 – Outcomes
5.4.1 Social Outcomes

File

social_outcomes.json

Can modify

relationship axes:

friendship

respect

romance

reputation pool

flags / triggers

Notes

Romance is treated as a normal relation axis

No implicit effects

No hidden logic

5.4.2 Operational Outcomes

File

operational_outcomes.json

Key Abstractions

Fatigue → delegated to AToW

Performance → implicit via success tier

XP → local pool, commit later

Confidence → new operational axis

Reputation → pool + threshold model

Does NOT

spend XP

advance skills

override parent systems

6. Explicit Non-Goals

This system deliberately does NOT:

hardcode logic in config

define UI behavior

manage persistence directly

replace AToW or MekHQ core mechanics

7. Agent Expectations (Important)

A GitHub / Coding Agent is expected to:

Load and validate all config files

Normalize structures via runtime

Implement:

Event Injector

Interaction Resolver

Outcome Applier

Respect:

numeric modifiers only

layer boundaries

no cross-layer shortcuts

The agent must not invent new mechanics.

8. Guiding Mantra

Events describe possibilities
Interactions describe intent
Resolution describes mechanics
Outcomes describe consequences
Config describes rules
Code interprets, never decides

9. Status

✔ Data complete
✔ Layers complete
✔ No missing files
✔ Ready for agent-assisted implementation
