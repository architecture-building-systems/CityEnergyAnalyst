# Pathway re-bake after master-scenario edits — plan, not started

Status: researched 2026-10-18, **not started**. A design plan for a later PR, not a record of work
done. Raised by a teacher training CEA: students fix an error in the master database after
baking, re-bake, and the states keep the old database.

## How bake decides today

`bake_states_from_log()` (`pathway_state.py`) rebuilds a state year only when it is not baked, or
its log hash changed (`source_payload_for_year`: cumulative interventions, building events,
active buildings). It skips custom states (edited inside State mode) always.

Nothing from the master `inputs/` folder is in that hash. A rebuilt state copies the whole master
`inputs/` (database included); a skipped one keeps its old copy. So:

1. **A master edit never reaches existing states.** They show as up to date.
2. **Mixed databases.** A later log edit rebakes that year and every later one with the new
   master; earlier years keep the old one. Results across years stop being comparable, silently.
3. **Custom states can never take a master fix** except by clearing them by hand.

Interim workaround (local installs only): delete every `state_YYYY/` folder **and** `state_status/`
under `outputs/pathways/{pathway}/`, keep `district_pathway_log.yml`, then Bake and Simulate.
Either record alone still reads as baked. Do not use "Clear state" with inputs: it also deletes
that year's log entry.

## Log interventions vs an edited master database

Interventions are changes, not snapshots: construction-type values are written into the
archetype row; envelope edits copy the archetype's *current* master row and overwrite the listed
fields. Only `CONSTRUCTION_TYPES` and the wall/roof/floor/base tables can conflict.

| Conflict | Today |
|---|---|
| Archetype, column, envelope code or field gone from the master | Caught before the bake (`_validate_modification_recipe`), nothing touched |
| Master row switched to direct values; intervention gives partial layers | Fails mid-bake at that year |
| Intervention sets a code (e.g. `supply_type_hs`) the master no longer has | **Not caught** — only the column is checked |
| Intervention and master fix set the same field | Intervention wins from its year on, silently (intended, but unannounced) |

## Design

**One Bake button, not a second "re-bake all".** The gap is that Bake cannot see master edits;
fix that and the only real choice left is what to do with custom states.

- **Bake rebuilds states whose master inputs changed.** No confirmation: a plain baked state is
  regenerable from the log, so nothing user-made is lost (results go stale; Simulate re-runs them).
- **Custom states are the only question.** When the pathway has custom states, Bake asks:
  *Keep their edits* (they won't get master changes) / *Discard edits and rebuild*. No custom
  states → no dialog, as today.
- **Pre-bake check also verifies codes exist**, so the dangling-code case fails early with a clear
  message instead of later in demand.

### Detecting master edits (decided: fingerprint for Bake, marker for the timeline)

Two signals, each sized for where it runs. Designed for both the local tool and the deployed app.

- **Bake — master-inputs fingerprint (authoritative).** A stat walk of master `inputs/` — hash of
  `(relative path, size, mtime_ns)` — recorded per state at bake and compared on the next one. One
  walk per bake run, shared across years; negligible next to the bake itself. Not a content hash
  (the status code dropped folder hashing over cloud-sync drift). Catches every edit, however made.
- **Timeline — "master edited" marker (display only).** A walk per overview request would be
  unbounded I/O in the deployed app (`inputs/` holds a schedule file per building, on network
  storage). Instead, the dashboard's save routes write
  `outputs/pathways/.master_edited.json` (`{"edited_at": ...}`) when the master scenario is
  saved — the mirror of `_mark_state_custom_if_child` (`api/inputs.py`), which marks a state
  custom when the save is inside one. One file covers every pathway (all copy the same master).
  The overview reads it once per request and shows a state red when `edited_at` is newer than its
  `built_at`.
- **Accepted limit:** hand edits on disk and CLI scripts don't write the marker, so they don't turn
  dots red. The next Bake still rebuilds those states, via the fingerprint.

## Work plan

**Backend (CityEnergyAnalyst)**

1. `pathway_status.py`: `master_inputs_fingerprint(locator)`; `record_baked_state` stores it and
   clears `custom`/`custom_at` (a rebuilt custom state is no longer custom).
2. Bake: `bake_states_from_log` rebuilds a non-custom state when its recorded fingerprint differs
   from the current one. Records without a fingerprint (baked before this change) count as fresh,
   so upgrading doesn't rebuild or redden every pathway.
3. Marker: an `InputLocator` method for `.master_edited.json`; a `record_master_edited(locator)`
   helper in `pathway_status.py`. In `api/inputs.py`, extend `_mark_state_custom_if_child` (rename,
   e.g. `_record_save`) so a master-scenario save writes the marker and a state save marks it
   custom — every save route already calls it. Overview / `_collect_bake_phase`: marker newer than
   `built_at` → `changed_after_bake` with `reason: "master"` (log-hash mismatch keeps
   `reason: "log"`); read the marker once per request, not per state.
4. `[bake-pathway-states] custom-states = keep | rebuild` (default `keep`; CLI keeps today's
   behaviour). `bake_states_from_log` honours it. Update `default.config`, regenerate
   `config.pyi`, `scripts.yml` description.
5. `_validate_modification_recipe`: for construction-type fields, check the value exists using
   the `choice.lookup` (locator method + column) already in `schemas.yml`.
6. Tests (`cea/tests/test_pathway_api.py`): master input change → Bake rebuilds non-custom states;
   custom kept by default, rebuilt and un-flagged with `rebuild`; pre-fingerprint record neither
   rebuilt nor red; master save via the API writes the marker, a state save does not; marker newer
   than `built_at` → red with `reason: "master"`; dangling code reported before the bake.
7. `district_pathways/AGENTS.md`: Bake freshness includes the master fingerprint; the timeline uses
   the marker, and why (no per-request folder walk). `dashboard/AGENTS.md` if it lists save-route
   side effects.

**GUI (CityEnergyAnalyst-GUI)**

8. `PathwayPanel.jsx` `handleBakePathway`: if the pathway has custom states, a modal with
   Keep / Discard / Cancel, passing `custom_states`. Count from the overview's phases.
9. Stale tooltip: "Master scenario changed since this bake" vs "Pathway log changed".
10. `bake-states` help tooltip: Bake now picks up master edits; custom states are asked about.

**Out of scope:** warning when an intervention overrides a field changed in the master (last row of the conflict table);
the status redesign in `pathway-state-status-plan.md` (this plan's `reason` field fits into it).

## Size

Small–medium: backend ~1 day including tests (step 3 is a few lines in the existing save hook plus
the overview comparison), GUI ~half a day. About eight files across both repos, plus tests.
