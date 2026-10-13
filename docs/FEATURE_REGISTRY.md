# Feature Registry — Mek-Mercenary-Additions

Status: initial inventory, 2026-10-13. **Presence in code is not proof of working runtime behavior.** This registry tracks the current `main` branch, not speculative features. Update after every tested merge.

## Status legend
- **Present / unverified**: implementation exists on main, regression tests or GUI acceptance not yet verified.
- **Partial**: implementation exists but an essential behavior is missing.
- **Branch only**: implementation exists in an unmerged PR.
- **Planned**: no verified implementation on main.
- **Verified**: automated tests and user acceptance passed on current main.

| ID | Feature | Main status | Sources / code | Acceptance / known gap |
| --- | --- | --- | --- | --- |
| CAL-001 | Event catalogue from JSON | Present / unverified | `config/events/eventlist.json`, `src/events/persistence.py` | Dynamic EventType entries correspond to event IDs; calendar dropdown works |
| CAL-002 | Calendar CRUD and recurrence | Present / unverified | `src/events/manager.py`, `src/events/dialogs.py`; `mekhq_social_sim/docs/EVENT_CALENDAR_SYSTEM.md` | Create/edit/delete, persistence, recurrence, refresh work |
| UI-001 | Character detail sheet | Present / unverified | `src/gui.py`; `mekhq_social_sim/docs/CHARACTER_SHEET_DOCUMENTATION.md` | Import/display, accordion, attributes/skills/portraits |
| UI-002 | Main GUI and calendar integration | Present / unverified | `src/gui.py`; `docs/UI_PHASE3_COMPLETE.md` | Manual start and calendar flows function |
| PART-001 | Participant selection and resolver maps | Partial | `src/events/participant_selector.py`, `participant_resolver.py`, `relationship_resolver.py`; merged PRs #34/#35 | Availability, primary/derived, deterministic date behavior, editable selection |
| PART-002 | Pass selected participants into execution | Partial | `src/events/dialogs.py`, `injector.py`; old PR #27 | Currently selected IDs are not passed into `execute_event()` |
| EVT-001 | Injector execution pipeline | Partial | `src/events/injector.py` | Current implementation validates and logs placeholder; TODOs remain for selection, interactions, checks, outcomes, triggers |
| EVT-002 | Event Resolve Window | Branch only | PRs #36/#37, `src/events/dialogs.py` on feature branch | Opens after participant confirmation, displays metadata/participants/checks; preserve calendar |
| EVT-003 | Headless interaction and mechanical resolution | Branch only | PR #23; `docs/EVENT_SYSTEM.md` | JSON interaction choice, tone/environment, existing skill-roll integration; must adapt to current architecture |
| EVT-004 | Declarative outcome application | Branch only | PR #23; `config/events/outcomes/` | Outcome JSON is source of effects, no hardcoded event logic |
| REL-001 | Relationship engine and trigger intake | Present / unverified | `src/relationship_engine.py`; merged PR #24 | Relationship engine owns state; explicit triggers, read-only query API |
| REL-002 | Relationship UI | Present / unverified | merged PR #21; `docs/RELATIONSHIP_SYSTEM_UI.md` | Show friendship/romance/respect and flags via runtime provider |
| STA-001 | Base / Session / Effective state contract | Planned / needs inventory | `docs/EVENT_SYSTEM.md` plus design decisions | Base read-only MekHQ export; Session persisted changes; Effective=Base+Session; single relationship-state authority |
| PLAY-001 | Event Playback narrative | Planned | Project design; PR #36 only placeholder | Top resolution checks/rolls/modifiers/results; bottom prose/narrative, no redundant interpretation layer |
| OBS-001 | Event execution log / Social Director | Partial | `src/events/injector.py`, merged PR #25 | Must log actual participants, checks, effects and outcomes rather than placeholder success |

## Maintenance rules
1. Keep requirements in `docs/FEATURE_TODO.md`, implementation evidence here.
2. Never mark **Verified** from a PR description alone. Check code, automated tests and user GUI acceptance.
3. Link feature IDs in PRs and commits, and update both documents with every merge.
4. Prefer current `main` code and authoritative JSON/config over old implementation summaries. Historical docs can be stale (e.g. calendar docs still describe three event types).
5. Do not create a second selection engine or relationship state master without an explicit architecture decision.
