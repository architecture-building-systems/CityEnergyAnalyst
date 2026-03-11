# Cost Calculations

## Main API

- `calculate_costs_for_whatif(whatif_name, locator) → (buildings_df, components_df)` - Calculate all costs for one what-if scenario
- `main(config)` - Entry point, iterates over `config.what_ifs.what_if_name` list

## Architecture

**Data sources (sole source of truth)**:
1. `configuration.json` → per-building supply configs (component, scale, efficiency, carrier)
2. `final_energy_buildings.csv` → annual summary (carrier MWh, service MWh, peak kW)
3. `B####.csv` hourly files (8760 rows) → per-service peak demand via `.max()`

**No fallback logic. No network topology. No assembly auto-selection.**

## Cost Flow

```
configuration.json + final_energy_buildings.csv + B####.csv
    ↓
Per-service peak (kW) from hourly files
    ↓
capacity_kW = peak_kW / efficiency  [BUILDING-scale only]
    ↓
CAPEX = a + b*Q_W^c + (d + e*Q_W)*ln(Q_W)   [Q in Watts]
    ↓
Capex_a = calc_capex_annualized(CAPEX, IR_%, LT_yr)
Opex_fixed_a = CAPEX × O&M_%
Opex_var_a = carrier_MWh × 1000 × mean(Opex_var_buy_USD2015kWh)
    ↓
TAC = Capex_a + Opex_fixed_a + Opex_var_a
```

## Scale Handling

| Scale | CAPEX | Fixed OPEX | Variable OPEX |
|-------|-------|-----------|---------------|
| BUILDING | From component cost curve | CAPEX × O&M% | carrier_MWh × feedstock_price |
| DISTRICT (building) | 0 | 0 | 0 (at plant level) |
| Plant row | From default component | component cost | carrier_MWh × feedstock_price |

**Plant components** (from `configuration.json['plants']`):
- Derived during final-energy from the DISTRICT-scale supply assembly of connected buildings
- e.g., AS9 → `primary_component=BO1`, carrier=NATURALGAS, efficiency=0.85
- Fallback hardcoded defaults only when `plants` section is absent

## Key Patterns

### DO: Read per-service peaks from hourly files

```python
df = pd.read_csv(locator.get_final_energy_building_file(building, whatif_name))
peak_hs_kW = df['Qhs_sys_kWh'].max()
```

### DO: Capacity sizing

```python
capacity_kW = peak_service_kW / efficiency  # efficiency from configuration.json
```

### DO: CAPEX formula (Q in Watts, log = natural log)

```python
from math import log
Q_W = capacity_kW * 1000.0
InvC = a + b * Q_W**c + (d + e * Q_W) * log(Q_W)
```

### DO: Variable OPEX uses mean of 24 hourly feedstock prices

```python
df = pd.read_csv(locator.get_db4_components_feedstocks_feedstocks_csv('NATURALGAS'))
price = df['Opex_var_buy_USD2015kWh'].mean()  # 24 rows (one per hour of day)
# From carrier annual MWh:
opex_var = carrier_MWh * 1000 * price   # MWh × 1000 kWh/MWh × USD/kWh = USD
# From booster annual kWh (read directly from hourly file):
opex_var = annual_kWh * price           # kWh × USD/kWh = USD  ← NOT /1000
```

### DO: Booster systems (space_heating_booster / hot_water_booster)

```python
# Config keys: space_heating_booster, hot_water_booster
# Peak from hourly file: Qhs_booster_{carrier}_kWh or Qww_booster_{carrier}_kWh
# Annual fuel: sum of that column (in kWh, NOT MWh)
# opex_var_a = annual_kWh * price   # NOT /1000
```

### DO: Plant network_type inference (from case_description)

```python
# case_description is set during final-energy from configuration.json
# 'DH' in case_description → DH plant, 'DC' in case_description → DC plant
```

### DO: Plant pumping — PU1 CAPEX + GRID OPEX

```python
# Peak pumping kW from plant hourly file (pumping_load_kWh column)
# PU1 CAPEX uses peak_pumping_kW (sized on peak network pressure loss)
# GRID OPEX: only when dominant_carrier != 'GRID'
#   - DH plants: NATURALGAS primary → add GRID pumping OPEX separately
#   - DC plants: GRID primary → pumping already bundled into GRID_MWh, OPEX = 0 here
# network_name comes from config_data['metadata']['network_name']
```

### DO: Solar costs from potentials/solar/ folder

```python
# PV: capacity_W = area_PV_m2 × (capacity_Wp / module_area_m2), unit='W'
# SC: capacity = area_SC_m2 directly (unit='m2', cost curve b×area)
# PVT: use full suffix (PV1_FP, PV1_ET) as service label to avoid duplicates
```

### DO: Per-service carrier MWh for OPEX (not aggregate summary column)

```python
# _per_service_peaks_and_booster returns service_mwh dict:
# service_mwh['hs'] = sum(Qhs_sys_*_kWh columns) / 1000  ← only hs carrier MWh
# service_mwh['ww'] = sum(Qww_sys_*_kWh columns) / 1000  ← only ww carrier MWh
# service_mwh['cs'] = sum(Qcs_sys_*_kWh columns) / 1000  ← only cs carrier MWh
# service_mwh['E']  = sum(E_sys_*_kWh columns) / 1000    ← only E carrier MWh
# Use these for opex_var — never use GRID_MWh from summary (includes cooling + E_sys)
```

### DO: Select correct piecewise row for multi-range components

```python
# _get_component_row(code, locator, capacity_W=Q_W) picks the matching cap_min/cap_max row
# PU1 has 4 rows: 500-4000W, 4000-37000W, 37000-375000W, 37000-∞W
# Always pass capacity_W so the correct cost curve segment is used
```

### DO: PVT prefix before PV in COMPONENT_PREFIX_TO_TABLE

```python
# 'PVT' must appear before 'PV' — 'PVT1'.startswith('PV') is True
# HEX must also be registered: 'HEX': 'HEAT_EXCHANGERS'
```

### DON'T: Use part-load curves or variable efficiency

```python
# Component efficiency in configuration.json is constant
# CAPEX cost curve is a,b,c,d,e parameters from COMPONENTS/CONVERSION/*.csv
```

## Database Parameters

**COMPONENTS/CONVERSION/*.csv** (BOILERS, HEAT_PUMPS, VAPOR_COMPRESSION_CHILLERS, etc.):
- `a, b, c, d, e` - Cost curve parameters
- `cap_min, cap_max` - Capacity range in Watts
- `LT_yr` - Lifetime, `IR_%` - Interest rate, `O&M_%` - Annual O&M

**COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/*.csv**:
- `Opex_var_buy_USD2015kWh` - Variable buy price (24 rows)

## Output Files

```
outputs/data/analysis/{whatif_name}/costs/
├── costs_buildings.csv    # One row per building/plant, aggregated totals
└── costs_components.csv   # One row per service per building
```

**costs_components.csv columns**: `name, service, scale, assembly_code, component_code, carrier, peak_service_kW, capacity_kW, Capex_total_USD, Capex_a_USD, Opex_fixed_a_USD, Opex_var_a_USD, TAC_USD`

**costs_buildings.csv columns**: metadata from summary + `Capex_total_USD, Capex_a_USD, Opex_fixed_a_USD, Opex_var_a_USD, TAC_USD, whatif_name`

## Related Files

- `main.py` - Entry point, full implementation
- `equations.py` - `calc_capex_annualized(InvC, IR_%, LT_yr)`
- `cea/analysis/final_energy/` - Must run first to produce inputs
- `cea/databases/AGENTS.md` - Database structure
