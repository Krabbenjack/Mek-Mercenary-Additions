# Feature To-Do and Acceptance Criteria — Mek-Mercenary-Additions

Last reviewed: 2026-10-13. This is the **desired behavior** backlog; `FEATURE_REGISTRY.md` tracks what is actually present on main. Items marked **Design proposal** require user confirmation; they are not claimed as pre-existing decisions.

## Working method
- One small, isolated domino step per feature branch, with focused automated tests and manual GUI test instructions.
- Review existing code, config, documentation and PRs before implementing; do not duplicate established systems.
- After user tests and merges, update `FEATURE_REGISTRY.md` and this backlog.
- No blind merging of divergent branches. Keep `main` working.

## P0 — Repair current event execution contract

### [ ] PART-002 — Selected participant handoff
**Desired:** Manual participant choices in the Event Execution window are the participants actually executed. Preserve Primary vs Derived provenance when available.

**Implementation direction:** Extend existing `EventInjector.execute_event()` to accept explicit participant IDs/objects or a structured participant selection; do not introduce a competing selector. The log must record the final chosen IDs. For no override, use the existing participant selector.

**Acceptance:** Change suggested participants in GUI -> execution log reflects exact final selection; missing/unavailable participants handled clearly; existing calendar/manual flows still work.

### [ ] OBS-001 — Truthful event log
**Desired:** Logs and Social Director display the actual event, date, participant IDs, executed checks and applied effects, not a misleading success banner for a placeholder.

**Acceptance:** Placeholder-only execution is clearly identified as such; later real results are inspectable and reproducible.

## P1 — Resolve Window and UI integration

### [ ] EVT-002 — Port Event Resolve Window from PR #37 selectively
**Desired:** After participant confirmation, open Resolve Window with event name/ID/date, environment and tone, primary/derived participant roster and a scrollable mechanics area; consistent dark theme. Close/cancel should not mutate state.

**Implementation direction:** Use #37 as reference, compare against main, do not blindly merge #36 and #37. Ensure `RESOLVE_THEME` is defined and calendar event creation remains functional.

**Acceptance:** Calendar list and event creation still work; Resolve Window opens, shows correct participants and closes cleanly; no duplicate execution.

### [ ] EVT-003 — Mechanics MVP in Resolve Window
**Desired:** For each event, show at least one real check from the configured interaction resolution: actor, skill, attribute(s), TN, modifiers, dice, success/margin, resulting outcome. No invented check rules.

**Implementation direction:** Reuse existing `rules/skill_roll.py` and JSON resolution definitions; keep UI passive and mechanics in headless code.

**Acceptance:** Repeatable automated check tests; visible and accurate mechanics output; error/unsupported config surfaced, not silently replaced.

## P2 — Headless engine and state authority

### [ ] ARC-001 — State ownership contract
**Desired:** **Base State** = read-only MekHQ export/initial data. **Session State** = persistent event-driven changes (axes/flags etc.). **Effective State** = Base + Session shown everywhere. Relationship state has one authoritative owner.

**Implementation direction:** Audit current `relationship_engine.py` and persistence before adapting #23 `AxisRegistry`. No parallel relationship store or duplicate mutations.

**Acceptance:** Save/reload produces same effective state; source export remains unchanged; UI reads effective values; duplicate event execution is prevented (design proposal: idempotency key).

### [ ] EVT-004 — Context-driven interaction selection
**Desired:** Event -> eligible social/operational interactions from JSON; environment and tone influence weights/modifiers; selection remains separate from checks and outcomes.

**Acceptance:** Eligible interaction is selected under configured conditions; tests cover environment/tone; no hidden meaning inferred from event names.

### [ ] EVT-005 — Stage-based AToW resolution
**Desired:** Resolution JSON controls actor/skill/attributes/TN/modifiers and outcome tiers including margin of success. Existing skill-check module performs rolls.

**Acceptance:** Tests for successful/failed checks, stage flow, missing skills/attributes, and modifier handling.

### [ ] EVT-006 — Declarative outcomes and triggers
**Desired:** `social_outcomes.json` / `operational_outcomes.json` declare axis deltas, flags, triggers and operational changes. Examples discussed: successful flirt romance +5, friendship +2, respect +2; unsuccessful romance +0, friendship +1, respect +1. Margin scaling is a possible future rule, not yet finalized.

**Implementation direction:** Adapt relevant #23 code without a competing axis master; route relationship mutations through established authority.

**Acceptance:** Configured outcome is applied exactly once; persisted effects and emitted triggers match config; no injector-only effects.

## P3 — Event Playback and narrative

### [ ] PLAY-001 — Event Playback two-layer layout
**Desired:** Upper **Resolution Layer** with checks, rolls, modifiers and mechanical results. Lower **Narrative Layer** with natural-language prose describing what happened. Do not add a separate Interpretation Layer; phrases such as “Mutual Interest, positive reception” belong in narrative and should be expanded into richer prose.

**Acceptance:** Same resolved result drives both displays; narrative does not invent effects; scrollable content remains readable.

### [ ] PLAY-002 — Narrative text catalogue (Design proposal)
**Desired:** Data-driven narrative variants keyed to interaction/outcome/tone/environment and, where appropriate, participant relationships.

**Acceptance:** Clear fallback for missing prose, no mechanics duplicated in UI code; review style and coverage with user.

## P4 — Maintenance and cleanup

### [ ] MAINT-001 — Close obsolete PRs after review
PR #28 GUI parent fix (empty), #36 superseded by #37, #39 stale revert (empty), #40 wrong-project UESRPG (empty). PR #27 partially superseded; PR #23 requires architectural adaptation. Do not close or delete without review.

### [ ] MAINT-002 — Safely prune old branches
Ten branches are fully contained in main by commit ancestry. Before deletion check PR references and keep valuable history accessible. Seven other branches need explicit resolution.

### [ ] MAINT-003 — Reconcile documentation
Historical docs may contradict current code (e.g. `EVENT_CALENDAR_SYSTEM.md` describes three event types). Keep `EVENT_SYSTEM.md` architecture and JSON rules authoritative; link updated registry and backlog from project README (design proposal).

## Open decisions (do not assume)
- Final source-of-truth mapping between RelationshipEngine and Session State.
- Exact check/outcome schema coverage across all events and what happens when configuration is missing.
- Whether event re-resolution is allowed and how to reverse effects.
- Narrative variation strategy and how much prose content to author.
- Final GUI layout transition from initial Resolve Window to Event Playback.
