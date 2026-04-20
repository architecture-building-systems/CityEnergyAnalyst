# Solar Technology Module — Agent Guide

## Scope
Physics models + database-backed components for three solar technologies:

- **PV** (photovoltaic, electricity only) — `photovoltaic.py`
- **SC** (solar collector, thermal only, flat plate or evacuated tube) — `solar_collector.py`
- **PVT** (PV-thermal hybrid, electricity + thermal) — `photovoltaic_thermal.py`

## THE THREE-NAMESPACE PROBLEM (known issue, see migration plan below)

CEA currently uses **three parallel naming systems** for solar technologies.
Understanding which one each layer uses is essential before editing anything
that touches solar tech codes.

| Layer | PV | PVT | SC |
|---|---|---|---|
| **Database `code` column** | `PV1`, `PV2`, … | `PVT1` | `SC1`, `SC2` |
| **Database `type` column** | (n/a) | (n/a) | `FP`, `ET` |
| **Per-building output file** `potentials/solar/{PV,PVT,SC}/{building}_*.csv` | `B1000_PV1.csv` (DB code) | `B1000_PV1_FP.csv` ({PV code}_{SC type}) | `B1000_FP.csv` (**type, not code**) |
| **Scenario-level file** `potentials/solar/{PV,PVT,SC}_*_total.csv` | `PV_PV1_total.csv` | `PVT_PV1_FP_total.csv` | `SC_FP_total.csv` |
| **Config dropdown tech_code** (what `panels-on-*` stores) | `PV_PV1` | `PVT_PV1_FP` | `SC_FP` |
| **Column prefix in `B####.csv`** | `PV_{facade}_E_kWh` (no panel code) | `PVT_{SC_type}_{facade}_{E,Q}_kWh` | `SC_{SC_type}_{facade}_Q_kWh` |

### Why the divergence exists

- **PV** was built DB-code native from the start. Clean.
- **SC** was built before the `code` column existed; file naming was by collector `type` (FP/ET) and nobody renamed it. The `code` column (SC1, SC2) was added later and is **only used for cost lookups**.
- **PVT** is a compound product (PV panel + SC collector paired into one file). Hybrid naming reflects the two internals: uses `PV_code` (from DB) and `SC_type` (also from DB but the older column).

### The single hardcoded mapping you need to know about

`cea/analysis/costs/solar_costs.py::parse_solar_tech_code` — one function translates
config tech_codes into DB codes. SC is the only one that needs real translation:

```python
# SC_FP -> ('SC', 'FP', 'SC1')   [hardcoded]
# SC_ET -> ('SC', 'ET', 'SC2')   [hardcoded]
db_code = 'SC1' if parts[1] == 'FP' else 'SC2'
```

**This hardcoded line is why you cannot add a 3rd SC product (e.g. `SC3` with
`type=FP`) to the database today — nothing in the pipeline would pick it up.**
PV has no such limit; adding `PV5` to `PHOTOVOLTAIC_PANELS.csv` works today.

## Temporary bridges in place (this PR)

Two small non-breaking bridges were added to reduce user confusion while the
full migration (see below) is pending:

1. **`SolarPanelChoicesMixin` accepts DB-code aliases** (`cea/config.py` around
   the `_try_db_code_alias` method).

   Config files can now set `panels-on-roof` to either form:

   | User writes | Internally normalised to |
   |---|---|
   | `SC_FP` | `SC_FP` (unchanged) |
   | `SC1`  | `SC_FP` (DB lookup: code → type) |
   | `SC_ET` | `SC_ET` (unchanged) |
   | `SC2`  | `SC_ET` (DB lookup) |
   | `PV_PV1` | `PV_PV1` (unchanged) |
   | `PV1`  | `PV_PV1` (prefix rule, no DB needed) |
   | `PVT_PV1_FP` | `PVT_PV1_FP` (unchanged) |
   | `PVT1` | **not aliased** — ambiguous which PV + SC pair was simulated |

   The rest of the pipeline continues to receive the tech_code form. This is
   only a front-door alias, not a true namespace change.

2. **Error messages in `validate_solar_dhw_building`** mention both namespaces
   so users learn the mapping as they hit errors. See `cea/analysis/final_energy/solar_dhw.py`.

## Option A migration plan (future PR)

The target end-state: **database `code` column becomes the single source of
truth for everything**. No hardcoded mapping. File names, column names, and
config values all use DB codes directly.

### What changes in the future PR

| File / subsystem | Change |
|---|---|
| **SC file naming** (`solar_collector.py`, `locator.SC_results` family) | Write `B1000_SC1.csv` / `B1000_SC2.csv` instead of `_FP` / `_ET`. Totals become `SC_SC1_total.csv` etc. |
| **PVT file naming** | Keep compound naming but switch SC part from type to code: `B1000_PV1_SC1.csv` instead of `B1000_PV1_FP.csv`. |
| **Config dropdown** (`SolarPanelChoicesMixin._get_available_solar_technologies`) | Emit DB codes directly (`SC1`, `SC2`, `PV1`, `PVT1`) instead of synthesised tech_codes. Drop the `PV_` / `PVT_` / `SC_` family prefix from config values. |
| **`parse_solar_tech_code`** | Delete. Replace with a direct DB lookup that identifies the family from the `code` alone (all DB codes are unique across the three tables today). |
| **`parse_solar_panel_configuration`** | Consume DB codes directly; no prefix stripping. |
| **`read_solar_generation_file`** | Resolve DB code → family → locator method. |
| **Column names in `B####.csv`** | `SC_FP_walls_north_Q_kWh` → `SC1_walls_north_Q_kWh` (or equivalent DB-native form). **This is a breaking CSV schema change.** |
| **Emissions pipeline** (`cea/analysis/lca/emission_time_dependent.py`) | Regex patterns for `SC_*`, `PVT_*_Q_kWh` columns need updating to match the new prefixes. |
| **Result summary / import-export** (`cea/import_export/result_summary.py`) | Large static column-mapping dict — ~60 lines of mechanical edits. |
| **Temporary bridges** in this PR | Become redundant once DB codes are the canonical form; `_try_db_code_alias` should be flipped to accept **old** tech_codes as deprecated aliases emitting a deprecation warning for one release cycle, then removed. |
| **Migration script** | One-shot tool that renames `potentials/solar/SC/B####_FP.csv` to `B####_SC1.csv` in existing scenarios; ditto for totals, PVT compound names, and any cached intermediates. ~50 lines. |
| **Config compat shim** | At `config.py` load time, translate old `SC_FP` → `SC1` with a one-time warning. Keep for one release; remove after. |

### Scope estimate

- **Optimistic**: 4 days focused work.
- **Realistic**: 6–7 days including CSV schema fallout (emissions, costs, visualisation, exports).
- **With surprise edge cases in `optimization_new` / `what_ifs` / plot tools**: up to 10 days.

### UX concern to resolve before starting Option A

`SC1` / `SC2` are opaque compared to `SC_FP` / `SC_ET`. The dropdown UI should
show descriptive labels (e.g. `"SC1 — flat plate"` / `"SC2 — evacuated tube"`),
reading the `description` column from `SOLAR_COLLECTORS.csv`. The stored config
value stays `SC1` / `SC2`. ~15 lines in the dropdown renderer.

### Acceptance criteria (for reviewers of the future PR)

1. Adding a third SC product to `SOLAR_COLLECTORS.csv` works end-to-end:
   simulation, sizing, costing, emissions, visualisation — no code edits
   required.
2. A scenario authored with the old `SC_FP` / `SC_ET` syntax still runs
   during the compat-shim window; `cea --validate-config` surfaces a one-time
   warning.
3. The migration script runs cleanly on an existing ZRH scenario, producing
   all new-format files without breaking downstream tools.
4. `_try_db_code_alias` (from this PR) is inverted so the **old** tech_codes
   are the deprecated aliases, not the new DB codes.
5. No hardcoded `'SC1'` / `'SC2'` / `'FP'` / `'ET'` string literals remain
   outside of solar-physics module internals.

## Related files

- `cea/technologies/solar/solar_collector.py` — SC physics
- `cea/technologies/solar/photovoltaic.py` — PV physics
- `cea/technologies/solar/photovoltaic_thermal.py` — PVT physics
- `cea/technologies/solar/constants.py` — `T_IN_SC_FP = 60 °C`, `T_IN_SC_ET = 75 °C`, `T_IN_PVT = 35 °C` (operating setpoints)
- `cea/analysis/costs/solar_costs.py` — the hardcoded tech_code → DB code mapping
- `cea/config.py` — `SolarPanelChoicesMixin` (DB-code alias bridge)
- `cea/analysis/final_energy/calculation.py` — `parse_solar_panel_configuration`, `read_solar_generation_file`
- `cea/analysis/final_energy/solar_dhw.py` — SC-primary DHW dispatch (references the three-namespace problem in validator errors)
