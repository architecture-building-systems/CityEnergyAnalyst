# Heat Rejection (Anthropogenic Heat)

## Main API

- `calculate_heat_rejection_for_whatif(whatif_name, locator) → (buildings_df, components_df)` — Calculate heat rejection for one what-if scenario
- `main(config)` — Entry point in `main.py`, iterates over `config.what_ifs.what_if_name`

## Architecture

**Data sources (sole source of truth)**:
1. `configuration.json` → per-building supply configs (carrier, efficiency, component, scale)
2. `final_energy_buildings.csv` → metadata (GFA, coords, scale, case, case_description)
3. `B####.csv` hourly files → per-service carrier flows
4. Plant hourly files → thermal load and carrier flows for district plants

No SupplySystem, no optimization-new framework, no 4-case connectivity logic.
Scale is read directly from `configuration.json`.

## Technology Functions

### Building-scale

| Service | Carrier | Heat rejection |
|---|---|---|
| hs / ww | FUEL | `losses = fuel_kWh − demand_kWh` (boiler exhaust) |
| hs / ww | GRID (HP) | 0 (absorbs ambient heat) |
| hs / ww | DH | 0 (attributed to plant) |
| cs | GRID (chiller) | `q_cond = Qcs_sys_kWh + Qcs_sys_GRID_kWh` → CT if tertiary_component |
| cs | DC | 0 (attributed to plant) |
| hs_booster / ww_booster | FUEL | `losses = col_kWh × (1 − η)` |
| hs_booster / ww_booster | GRID | 0 (electric booster) |

Fuel carriers are resolved dynamically from ``ENERGY_CARRIERS.csv``
(every row with ``type == 'combustible'``) via
``cea.technologies.energy_carriers.combustible_carriers(locator)``.
The electricity carrier (typically ``GRID``) is likewise resolved via
``electricity_carrier(locator)`` so users who renamed their electricity
feedstock still route correctly.

### Cooling tower

```python
from cea.technologies.cooling_tower import calc_CT_const

q_cond = Qcs_sys_kWh + Qcs_sys_GRID_kWh
ct_aux_power = float(COOLING_TOWERS.csv row for tertiary_component['aux_power'])
_, q_anth = calc_CT_const(q_cond, ct_aux_power)  # q_anth = q_cond × (1 + aux_power)
```

If no `tertiary_component`: `q_anth = q_cond` (condenser heat direct to atmosphere).

### Plant-scale

| Plant | Carrier | Heat rejection |
|---|---|---|
| DH | FUEL | `fuel_col_kWh − thermal_load_kWh` |
| DH | GRID (HP) | 0 |
| DC | GRID (chiller) | `q_cond = thermal_load_kWh + plant_primary_DC_GRID_kWh + plant_tertiary_DC_GRID_kWh` → CT |

## Key Patterns

### DO: Read per-service carrier columns from hourly file

```python
df = pd.read_csv(locator.get_final_energy_building_file(building, whatif_name))
# For fuel heating: losses = Qhs_sys_NATURALGAS_kWh - Qhs_sys_kWh
# For grid cooling: q_cond = Qcs_sys_kWh + Qcs_sys_GRID_kWh
```

### DO: CT aux_power from tertiary_component

```python
ct_code = supply_cfg['space_cooling']['tertiary_component']  # e.g. 'CT1'
ct_aux_power = float(COOLING_TOWERS_df[COOLING_TOWERS_df['code'] == ct_code]['aux_power'])
```

### DON'T: Use SupplySystem / optimization-new framework

The SupplySystem objects are not used — final-energy already computed all carrier flows.

## Output Files

```
outputs/data/analysis/{whatif_name}/heat/
├── heat_rejection_buildings.csv   # One row per building/plant
├── heat_rejection_components.csv  # One row per service per building
└── {name}.csv                     # Hourly heat_rejection_kW (8760 rows)
```

**heat_rejection_buildings.csv** columns: `name, type, GFA_m2, x_coord, y_coord, scale, case, case_description, heat_rejection_annual_MWh, peak_heat_rejection_kW, whatif_name`

**heat_rejection_components.csv** columns: `name, service, scale, assembly_code, component_code, carrier, peak_heat_rejection_kW, heat_rejection_annual_MWh`

## Visualisation (Bar Chart & Map Layer)

### Bar chart (`plot-heat-rejection` script)

- Config: `[plots-heat-rejection]` with `what-if-name` (WhatIfNameMultiChoiceParameter, mode=final_energy)
- `a_data_loader.py:_export_heat_rejection_to_plots_folder()` — bypasses `result_summary.py`:
  - Building annual view: reads `heat_rejection_buildings.csv`, converts `heat_rejection_annual_MWh × 1000 → heat_rejection_kWh`, adds `period='annually'`
  - District time-series: sums entity hourly files, aggregates via `exec_aggregate_time_period()`
- The `execute_summary()` method in `csv_pointer` dispatches to this function (same pattern as `final-energy`)

### Map layer (`AnthropogenicHeatMapLayer`)

- `expected_parameters()` includes `whatif_name` (`selector="choice"`, `options_generator="_get_whatif_names"`)
- `_get_whatif_names()` scans `outputs/data/analysis/*/heat/heat_rejection_buildings.csv`
- `generate_data()` reads from `locator.get_heat_rejection_whatif_buildings_file(whatif_name)` and `locator.get_heat_rejection_whatif_building_file(name, whatif_name)`

## Related Files

- `heat_rejection.py` — All calculation functions
- `main.py` — Entry point
- `cea/analysis/final_energy/` — Must run first to produce inputs
- `cea/analysis/costs/AGENTS.md` — Reference for parallel architecture
- `cea/technologies/cooling_tower.py` — `calc_CT_const(q_hot, eff_rating)`
- `cea/visualisation/a_data_loader.py` — Bar chart export bypass
- `cea/interfaces/dashboard/map_layers/life_cycle_analysis/layers.py` — `AnthropogenicHeatMapLayer`
