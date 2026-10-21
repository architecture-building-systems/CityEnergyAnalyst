# Pathway state status (timeline dot colours) — plan, not started

Status: researched 2026-10-18, **not started**. This is a design plan for a later PR, not a
record of work done. Only the interim fix described at the end exists.

## How it works today

Each state's dot comes from one value, `primary_phase`, computed by
`collect_state_phase_status` (`cea/datamanagement/district_pathways/pathway_status.py`) and
mapped to a fill in the GUI (`STATUS_FILL` in `src/features/pathway/constants.js`):

| Dot | Meaning | Set by |
|---|---|---|
| Grey | Draft (not baked, or only validated) | — |
| Blue | Baked from the pathway log | bake |
| Black | Simulated, results current | Simulate Pathway only |
| Purple | Custom: inputs or database edited inside the state | any save inside the state (`record_custom_state`) |
| Red | Out of date: log changed after the bake (re-bake needed), or a validation error | `has_stale_phase` / validation |

## Problems found

1. **Purple erases everything else.** For a custom state, `collect_state_phase_status` returns
   `custom` for every phase and skips all checks, so it cannot say whether the state has results
   or whether they are current.
2. **Features judge "has results" by different rules.**

   | Feature | Rule |
   |---|---|
   | Canvas pathway picker (`all_simulated` in the overview) | every state black (before the interim fix below) |
   | Emission timeline (`SimulatedPathwayMultiChoiceParameter` in `config.py`) | black or purple, Simulate Pathway run after every custom edit (pathway-wide timestamp; before the interim fix) |
   | Main-view timeline (`all_baked`) | baked, purple or black |

3. **Manual simulation is not recorded.** Only Simulate Pathway calls `record_simulated_state`.
   Running tools by hand inside a state leaves its colour unchanged, and Simulate Pathway re-runs
   it.
4. **A custom state silently ignores later log changes.** Custom bypasses staleness checks and
   bake skips custom states, so a later log change for that year (e.g. a demolition) never
   reaches it, and nothing says so.
5. **Smaller:** the main-view timeline never shows red (it uses `year_phases` only, the pathway
   panel uses `getNodeFill`); `STATUS_ACCENT.changed` (amber) is defined but unused.

## Root cause

A state has two independent facts, which one colour cannot show:

- **Inputs** — Draft, Baked from the log, or Custom (user-edited).
- **Results** — None, Current, or Out of date.

A custom state that was then fully simulated is both: custom, with current results.

## Proposed model

**Fill shows readiness; a ring shows custom.**

| Look | Meaning |
|---|---|
| Grey fill | Draft |
| Blue fill | Inputs ready, no current results |
| Black fill | Results current — ready to analyse |
| Purple ring (on any of the above) | Inputs edited by the user |
| Red | Inputs out of date — log changed since the bake (re-bake) |
| Amber | Results out of date — inputs edited since the last simulation (re-simulate) |

**One backend rule for "results current":** a recorded simulation newer than the last bake and
the last custom edit, with outputs on disk — per state, from the timestamps the status record
already holds (`built_at`, `custom_at`, `simulated_at`); no migration. The canvas picker and the
emission timeline both require it for every state, custom or not; the main-view timeline keeps
requiring inputs ready, and shows red/amber too.

**Manual simulation:** CEA cannot tell from individual tool runs that the whole workflow (~6
steps) ran. Add a **Simulate this State** action that runs the pathway workflow for one year and
records it (a year option on `pathway-simulations` plus a pathway-panel button). Manual tool runs
keep working but do not change the status, so black keeps meaning "the full workflow ran on these
inputs".

**Custom state vs log changes:** when the log changes for a year whose state is custom, show it
red ("pathway log changed since you customised this state"); the user clears and re-bakes, or
keeps their edits.

## Implementation phases

1. Backend status: return inputs and results separately plus the single "results current" rule.
2. Feature gates: the overview's `all_simulated` and `SimulatedPathwayMultiChoiceParameter` use
   that rule (replacing the interim `state_has_results`, below).
3. GUI: fill + ring rendering, red/amber accents, legend — both timelines (main view
   `OverviewCard`, pathway panel) and the canvas picker.
4. Simulate this State (year option + button).
5. Tests for each combination: plain/custom inputs × none/current/out-of-date results.

Size: medium — two backend modules, one config parameter, about five GUI files. Phases 1–3 fix
the feature gating; phase 4 answers manual simulation.

## Interim fix (in place)

Purple states enable the canvas picker and the emission timeline whenever they have outputs on
disk -- no Simulate Pathway run required, since the user may have run the tools inside the
state. Both gates use `state_has_results` (`pathway_status.py`): simulated, or custom with an
`outputs/` folder. It cannot tell whether those outputs reflect the latest edit, or whether the
whole workflow ran -- phase 2 replaces it with the per-state "results current" rule, and phase 4
gives manual runs a way to be recorded. Pinned by `test_custom_states_with_outputs_count_as_simulated`
(`cea/tests/test_pathway_api.py`).
