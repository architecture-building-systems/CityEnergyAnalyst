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

`FUEL_CARRIERS = {'NATURALGAS', 'OIL', 'COAL', 'WOOD'}`

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
| DC | GRID (chiller) | `q_cond = thermal_load_kWh + plant_cooling_GRID_kWh` → CT |

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

## Related Files

- `heat_rejection.py` — All calculation functions
- `main.py` — Entry point
- `cea/analysis/final_energy/` — Must run first to produce inputs
- `cea/analysis/costs/AGENTS.md` — Reference for parallel architecture
- `cea/technologies/cooling_tower.py` — `calc_CT_const(q_hot, eff_rating)`
- `cea/technologies/boiler.py` — `calc_boiler_const(Q_load, efficiency)`
