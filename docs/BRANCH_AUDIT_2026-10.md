# Branch audit — 2026-10-13

Repository: Krabbenjack/Mek-Mercenary-Additions. Baseline: main at 72bd441f60b289f38bbb84232ccbc6a7f4189ec9.

## Already fully contained in main (ahead=0, behind>0)
- copilot/cleanup-calendar-integration
- copilot/combine-markdown-documentation
- copilot/consolidate-documentation-files
- copilot/featurephase2-5-system-activation-ui-integration
- copilot/featurephase2-event-relationship-integration
- copilot/fix-participant-selection-issues
- copilot/integrate-resolver-maps
- copilot/refactor-mechwarrior-to-mekwarrior
- copilot/refactor-ttk-focus-highlighting
- copilot/repair-event-participants-execution-window

These are branch-deletion candidates **after checking open PRs and references**. No branch was deleted.

## Branches requiring review
| Branch | Ahead | Behind | Finding |
| --- | ---: | ---: | --- |
| copilot/add-event-resolve-window-ui | 5 | 6 | EventResolveWindow exists; not on main |
| copilot/fix-calendar-event-integration | 6 | 6 | Also contains EventResolveWindow, with additional changes in dialogs.py |
| copilot/featureevent-participants-execution-window | 7 | 50 | Diverged UI/injector work |
| copilot/implement-headless-event-system | 4 | 75 | Diverged axis/outcome/orchestration code |
| copilot/fix-gui-parent-reference | 1 | 50 | Diverged small fix |
| copilot/fix-derivatives-usability-issues | 1 | 0 | One commit ahead; no changed files in comparison |
| copilot/revert-merge-commit | 1 | 0 | One commit ahead; review revert intention before any merge |

## Confirmed source inspection
- main: events/dialogs.py does **not** define EventResolveWindow.
- copilot/add-event-resolve-window-ui: events/dialogs.py defines EventResolveWindow.
- copilot/fix-calendar-event-integration: events/dialogs.py defines EventResolveWindow and differs from the previous branch in participant-row portrait rendering.
- Both event-window branches modify src/ui_theme.py.
- Calendar-fix branch is a likely successor, **not yet proven safe to merge**.

## Next steps
1. Check open PRs/references before deleting any branch.
2. Review the seven outstanding branches, including relevant code and tests.
3. Port only required changes to a new feature branch based on current main.
4. Run tests; open a PR for user review.
5. Delete stale branches only after confirmation that their contents are no longer needed.

This document is a read-only audit; it does not authorize or perform deletions or merges.
