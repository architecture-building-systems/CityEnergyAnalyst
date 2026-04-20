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

## Known limitations & caveats

### 1. `calc_water_temperature` units bug (pre-existing, affects all DHW demand)

`cea/demand/hotwater_loads.py::calc_water_temperature` computes the
annual-cycle damping coefficient using `HOURS_IN_YEAR` (8760) where the
Kusuda/Achenbach 1965 ground-temperature model expects **seconds per year**
(31,536,000). The damping term ends up ~26.8 instead of ~0.45, which
collapses the annual cold-mains curve to a near-constant ~T_ground.

**Observed symptom**: for ZRH the cold-inlet series sits at a flat ~9.4 °C
year-round, where physics expects a 5–18 °C seasonal swing.

**Impact**:

- Affects **all** CEA DHW demand calculations (not just SC-DHW).
- For SC-DHW dispatch the bias is self-consistent: the demand-side
  `Qww_sys_kWh` and the dispatch-side cold-inlet both see the same wrong
  `T_cold`, so the internal energy balance holds. But the real solar
  fraction in temperate climates would likely be ~10 % higher than what
  the model currently reports (lower winter cold-inlet → higher booster
  share; higher summer cold-inlet → smaller `Q_SC_gen` credited per kWh
  delivered; the second effect usually dominates for SC).

**Why not fixed here**: requires a demand-side regression (Swiss + tropical
scenarios) and touches `hotwater_loads.py` which is consumed by every
downstream module. Tracked as a follow-up PR; don't fold into this one.

### 2. Extreme SC oversizing → standing-loss-dominated tank

The dispatch sizes the DHW tank from SC aperture (`TANK_CAPACITY_L_PER_M2 =
50 L/m²`). Real DHW tanks are sized from **daily hot-water consumption**, not
panel area. When `SC_area_m²` is much larger than DHW demand justifies
(e.g. a scenario where SC covers PV+SH+DHW on the same roof and the panels
are chosen to saturate PV sizing), the tank can become absurdly large.

**Observed symptom (ZRH office scenario)**: `B1000` had 713 m² SC on a
3817 m² office building. The resulting 35.7 m³ tank turned over only twice
a day for its 9.7 MWh/yr DHW demand. Of 48 MWh/yr generated:

- ~2.8 MWh delivered as DHW (solar fraction 29 %)
- 0 MWh dumped at `T_MAX` (tank never reached 105 °C because losses bled it)
- ~45 MWh lost to standing losses

**How to spot it**: check `Qww_sys_SOLAR_dumped_kWh` (surplus pressure-
relief dumps) and the implied standing-loss balance
`Q_SC_gen − Qww_sys_SOLAR_kWh − Qww_sys_SOLAR_dumped_kWh`. Standing losses
that rival or exceed the delivered energy are a sizing red flag, not a
dispatch bug.

**Why not "fixed" by changing the tank rule**: sizing by DHW demand
instead of aperture area would also be defensible, but it hides the
oversizing signal. The current rule makes the inefficiency visible in the
output; a future improvement would be to log a warning when
`standing_loss_kWh / Q_SC_gen_kWh > 0.5`.

### 3. Diagnostic column `Qww_sys_SOLAR_dumped_kWh` (and on-the-fly gross)

`Qww_sys_SOLAR_dumped_kWh` is the only SC-DHW diagnostic that's persisted
in `B####.csv` (alongside `Qww_sys_SOLAR_kWh`). It records the hourly
heat that would have pushed the tank above `T_MAX_C` (105 °C) and was
discarded to the pressure-relief valve. It is **not** a delivered
carrier. Internal implementation detail: not in `schemas.yml`, not
exported by `result_summary.py`. Filtered out of:

- `aggregate_buildings_summary` (summary file carrier totals)
- `create_hourly_timeseries_aggregation` (detailed hourly `SOLAR_kWh` column)
- `cea/analysis/lca/emission_time_dependent._calc_operational_emissions_from_fe`
- `cea/analysis/costs/main.py::_per_service_peaks_and_booster` (service MWh)
- `cea/interfaces/dashboard/map_layers/life_cycle_analysis/layers.py`
- `cea/visualisation/special/energy_sankey.py`

If you add a new pipeline that scans `Qww_sys_*_kWh` columns, remember to
skip `*_dumped_kWh`.

**Gross `Q_SC_gen` is recomputed on the fly, not persisted.** The Sankey
needs a source-side width for the SC arc that's larger than the delivered
solar (so the SC1 node visibly narrows from gross to net, just like BO2
narrows 673 → 565 MWh from η loss). Rather than duplicating data already
written by `cea solar-collector` to
`outputs/data/potentials/solar/SC/{name}_{type}.csv`, the Sankey reads
those files directly via the helper
``cea/visualisation/special/energy_sankey._sc_gross_kwh_for_building``,
which delegates to ``solar_dhw.aggregate_sc_thermal_per_surface``.

**Per-surface bookkeeping (correctness fix in this PR).** The `cea
solar-collector` output writes per-surface columns inside each panel-type
file:

```
B1000_FP.csv columns:
  SC_FP_roofs_top_Q_kWh, SC_FP_walls_north_Q_kWh, … walls_south, east, west
  area_SC_m2  ← aggregate across ALL surfaces simulated under SC_FP
  Q_SC_gen_kWh ← aggregate across ALL surfaces simulated under SC_FP
```

The aggregate `Q_SC_gen_kWh` and `area_SC_m2` cover **every surface that
was simulated under that panel type**, not just the ones currently
assigned. A scenario with `roof: SC_ET, wall_north: SC_FP` should pull
*only* the roof column from `B####_ET.csv` and *only* the wall_north
column from `B####_FP.csv`. Summing both files' aggregate columns
double-counts surfaces that aren't actually configured under both
technologies and inflates the SC input by 2–3× (measured 2.4× on the ZRH
test scenario).

`aggregate_sc_thermal_per_surface(building_name, panel_config, locator)`
in `solar_dhw.py` walks the surface→panel-type mapping and sums only the
matching `SC_{type}_{surface}_Q_kWh` and `SC_{type}_{surface}_m2` columns.
Both the dispatch (`aggregate_building_sc_thermal` calls this) and the
Sankey gross helper share this code path, so the source-side and
delivered-side numbers are computed against the same (corrected) input.

Why on-the-fly instead of persisted:

- Avoids writing a diagnostic-only column that no other consumer needs.
- Existing scenarios don't need a `cea final-energy` rerun for the new
  Sankey view — the SC potential files are already on disk.
- Removes filter-exclusion plumbing across emissions / costs / map / LDC
  pipelines.

Trade-off: the Sankey now does an O(buildings × SC-types) read of small
CSVs (~8760 rows × 1–2 panel types per building) per refresh. For typical
scenarios (≤ a few hundred buildings) this is in the tens of MB and well
under a second.

### 4. Future: component-naming for multi-component services

The `_dumped_kWh` suffix and on-the-fly gross lookup are a **bridge**. The cleaner
long-term design is to name carrier (source) and component (sink) columns
separately, so every service-level flow reads `carrier → component → demand`
the same way regardless of whether it's BO1, HP1, or SC1:

| | Current (gross) | Current (net) | Proposed (gross, per-carrier) | Proposed (net, per-component) |
|---|---|---|---|---|
| BO1 DHW | `Qww_sys_NATURALGAS_kWh` = 512 | `Qww_sys_kWh` = 435 | `Qww_in_NATURALGAS_kWh` = 512 | `Qww_out_BO1_kWh` = 435 |
| HP1 SH  | `Qhs_sys_GRID_kWh` = 100       | `Qhs_sys_kWh` = 300 | `Qhs_in_GRID_kWh` = 100       | `Qhs_out_HP1_kWh` = 300       |
| SC1 DHW | (recomputed from SC potentials) = 480 | `Qww_sys_SOLAR_kWh` = 179 | `Qww_in_SOLAR_kWh` = 480       | `Qww_out_SC1_kWh` = 179       |
| BO5 DHW (SC backup) | `Qww_sys_GRID_kWh` (shared w/ E_sys in aggregation, ugh) | — | `Qww_in_GRID_kWh` = 259 | `Qww_out_BO5_kWh` = 256 |

Motivating observation: today `Qww_sys_SOLAR_kWh` is net-delivered,
`Qww_sys_NATURALGAS_kWh` is gross-burned — same syntactic shape, opposite
semantics. The parser can only tell them apart by classifying the middle
token as a carrier vs component, which is fragile. Distinct `in_` / `out_`
prefixes make parsing unambiguous.

**Benefits**:

- No `_gross_kWh` / `_dumped_kWh` / `_delivered_kWh` suffix zoo.
- Multi-component services balance naturally:
  `Qww_out_SC1 + Qww_out_BO5 = Qww_sys_kWh` demand.
- Sankey source = `Qxx_in_CARRIER`, sink = `Qxx_out_COMPONENT`. One rule
  for every component class.
- Losses localise at the component that owns them. No SOLAR-means-two-things
  anomaly.

**Migration scope** (~1 week, similar shape to the solar three-namespace
migration above):

| Touched | What changes |
|---|---|
| `cea/analysis/final_energy/calculation.py` | Write `Qxx_in_*` and `Qxx_out_*`, retire `_gross` / `_dumped` suffixes (keep one round of compat aliasing). |
| `cea/analysis/lca/emission_time_dependent.py` | Carrier detection: look for `Qxx_in_` prefix, not `Qxx_sys_`. Zero-emission check moves to the `in_` column. |
| `cea/analysis/costs/main.py` | Service MWh from `Qxx_in_*` (gross = variable OPEX driver). Peak from `Qxx_out_*` if you want delivered peak, or from demand for load-sizing. |
| `cea/analysis/heat/heat_rejection.py` | Boiler/chiller loss = `Qxx_in_CARRIER - Qxx_out_COMPONENT`, readable directly instead of re-computed from efficiency. |
| `cea/visualisation/special/energy_sankey.py` | Simplifies: `plant_input_kWh` = `Qxx_in_*`, `value_kWh` = `Qxx_out_*`, no special-case branches for SOLAR. |
| `cea/visualisation/special/ldc_component.py` | `col_prefix` lookups change from `Qxx_sys_` to `Qxx_in_` / `Qxx_out_` depending on which side. |
| `cea/import_export/result_summary.py` | Large static column-mapping dict — ~40 lines of mechanical edits. |
| `cea/interfaces/dashboard/map_layers/life_cycle_analysis/layers.py` | `_column_to_carrier` reads from `Qxx_in_` only. |
| Migration script | Rename columns in existing `B####.csv`. ~40 lines. |
| Compat shim | Read old `Qxx_sys_CARRIER_kWh` as either gross (most carriers) or net (SOLAR) based on a small lookup for one release. |

**Subtlety: tertiary components** (e.g. CT1 in chiller assemblies). CT1
does not deliver cooling — it rejects heat — so **no** `Qcs_out_CT1_kWh`.
Its fan electricity stays aggregated in `Qcs_in_GRID_kWh` with the
chiller's input. Document explicitly: the per-component `out_` column
exists only for components that produce useful service energy.

**Until the migration lands**, this PR's on-the-fly gross-from-SC-potential
lookup + the existing `_sys_CARRIER` for SOLAR remain the compromise.

## Related files

- `cea/technologies/solar/solar_collector.py` — SC physics
- `cea/technologies/solar/photovoltaic.py` — PV physics
- `cea/technologies/solar/photovoltaic_thermal.py` — PVT physics
- `cea/technologies/solar/constants.py` — `T_IN_SC_FP = 60 °C`, `T_IN_SC_ET = 75 °C`, `T_IN_PVT = 35 °C` (operating setpoints)
- `cea/analysis/costs/solar_costs.py` — the hardcoded tech_code → DB code mapping
- `cea/config.py` — `SolarPanelChoicesMixin` (DB-code alias bridge)
- `cea/analysis/final_energy/calculation.py` — `parse_solar_panel_configuration`, `read_solar_generation_file`
- `cea/analysis/final_energy/solar_dhw.py` — SC-primary DHW dispatch (references the three-namespace problem in validator errors)
- `cea/demand/hotwater_loads.py::calc_water_temperature` — Kusuda cold-mains model; see caveat #1 above
