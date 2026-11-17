# Final-energy district total: stop counting district heating / cooling twice — plan

Status: researched 2026-11-16; implemented 2026-11-17 (all steps; step 4 takes the Reports total from
`final_energy.csv` and sums only carrier columns across rows, not `TOTAL_MWh` or demand). Also
fixed on the way: plant pumping electricity was read as carrier `DH` / `DC` (the network type)
in `final_energy.csv` instead of `GRID`. Changes final-energy output values; users re-run
final-energy.

## The problem

In a what-if with a thermal network, the same heat is counted twice in the district total:

- **Building rows / files**: heat or cold bought from the network is consumption —
  `Qhs_sys_DH_kWh`, `Qww_sys_DH_kWh`, `Qcs_sys_DC_kWh` (`calculation.py` ~167/228/252) —
  classified as carrier `DH` / `DC` with `is_consumption=True`, so it is inside the building's
  `TOTAL`.
- **Plant rows / files**: the fuel and electricity the plant uses to make that heat or cold
  (`plant_primary_*`, `plant_tertiary_*`, `plant_pumping_*`) are the plant's `TOTAL`
  (`aggregate_buildings_summary`, plant loop) and are added to the district hourly
  `TOTAL_kWh` (`create_hourly_timeseries_aggregation`, plant loop).

Σ over buildings + plants = DH heat delivered + the gas burned to make it. Each building's own
`TOTAL` is right (its final energy includes the DH it buys); only district sums are wrong.

## Who is affected (checked 2026-11-16)

| Reader | Affected? | Why |
|---|---|---|
| KPI `final_energy.total_final_mwh` | **yes** | Σ `TOTAL_MWh` over all rows |
| KPI `final_energy.fossil_share_pct` | **yes** | whole = Σ `TOTAL_MWh` → share too low |
| `final_energy.csv` `TOTAL_kWh` | **yes** | buildings' DH/DC + plant fuel |
| Operational emissions (`emission_time_dependent.py`) | no | `DH`/`DC` are zero-emission carriers; plants carry the fuel |
| Summary export, `plot-final-energy` | no | carrier columns come from `available_carriers` (ENERGY_CARRIERS.csv), which has no DH/DC; no `TOTAL` used — verify in `a_data_loader` export |
| Energy Sankey | no | models plant input vs building delivery explicitly |
| Costs | no | DISTRICT-scale buildings get zero cost rows; plants are costed |
| PV analytics | no | GRID only; DH/DC are not GRID |

Unrelated, found on the way: `api/reports.py::_final_energy_summary` looks for `*_MWhyr`
columns, which `final_energy_buildings.csv` doesn't have (`*_MWh`), so its KPI list is empty.

## Rule

District final energy = energy entering the district boundary. `DH` / `DC` are transfers
inside the district (plant → buildings); the plant's fuel and electricity — including network
losses and pumping — stand in for them. Count DH/DC in a district total **only** for a network
type with no plant results (a plant can fail and be skipped: `main.py` ~360, `✗ ... plant`),
so the heat is never dropped altogether.

## Plan

1. **District hourly total** (`create_hourly_timeseries_aggregation`): do not add building
   `DH` / `DC` consumption to `TOTAL_kWh` when `plant_dfs` has a plant of that network type
   (plant keys are `DH_<name>` / `DC_<name>`). Keep the `DH_kWh` / `DC_kWh` columns — they
   are the delivered heat/cold, useful on their own. Update the docstring and the
   `final_energy.csv` `TOTAL_kWh` description in `cea/schemas.yml` ("energy entering the
   district: building carriers except DH/DC supplied by a plant, plus plant fuel and
   electricity").
2. **Per-row `TOTAL_MWh` unchanged** (`final_energy_buildings.csv`): a building's final energy
   still includes the DH it buys. Say in the schema description that summing it across
   buildings and plants double-counts network heat/cold, and point to `final_energy.csv`.
3. **KPIs read the district file** — `total_final_mwh` and `fossil_share_pct` switch their
   source to `get_final_energy_file` (`TOTAL_kWh`, `NATURALGAS_kWh`, `OIL_kWh`, `COAL_kWh`;
   `aggregate` with `scale: 0.001` for MWh). Same source as the PV analytics cards; no new
   formula node. Update the info notes ("energy entering the district; heat and cold from a
   district network are counted as the plant's fuel and electricity"). The definition hash
   changes, so cached values recompute.
4. **Fix the `reports.py` column suffix** (`_MWhyr` → `_MWh`) — optional, one line; or leave
   to the Reports rework.
5. `cea/analysis/final_energy/AGENTS.md`: one "DO" — district totals count DH/DC only where no
   plant supplies them; never Σ `TOTAL_MWh` across buildings and plants.

## Tests (`cea/tests/test_final_energy_carrier_columns.py`)

- One DH building (`Qhs_sys_DH_kWh` = 10) + one DH plant (`plant_primary_DH_NATURALGAS_kWh`
  = 12, `plant_pumping_DH_GRID_kWh` = 1) → district `TOTAL_kWh` = 13, `DH_kWh` still 10.
- Same building, no plant → `TOTAL_kWh` = 10 (heat kept when the plant is missing).
- DH plant only affects DH: a DC building with no DC plant keeps its DC in the total.
- Building row `TOTAL_MWh` still includes its DH.
- KPI: Total Final Energy and Fossil Fuel Share from a small `final_energy.csv` fixture.

## Check on a real case

A what-if with a DH network (e.g. on `baseline_dh`, on a scratch copy): compare old vs new
Total Final Energy; the drop should be ≈ Σ building DH_MWh. Fossil Fuel Share rises
accordingly.

## Size

Small: about half a day with tests. Users re-run "LCA Part 1: Energy by Carrier" for corrected
totals; until then Total Final Energy reads the old `TOTAL_kWh` (still double-counted), and
cards whose column an older `final_energy.csv` lacks (older files only wrote carriers in use;
now every declared carrier is zero-filled) show "Run LCA Part 1: Energy by Carrier to see
this" — the resolver attaches the tool to a missing-column error. Call it out in the PR.
