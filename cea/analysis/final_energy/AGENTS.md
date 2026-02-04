# Final Energy Module - Agent Guide

## Quick Reference

**Purpose**: Convert building energy demand to final energy consumption by carrier type. Supports both building-scale and district-scale systems with what-if scenario analysis.

**Main API**:
- `main(config)` - Entry point, orchestrates calculation workflow
- `calculate_building_final_energy(building, locator, config) → DataFrame` - Calculate one building
- `calculate_plant_final_energy(network_name, network_type, plant_name, locator, config) → DataFrame` - Calculate district plant
- `load_supply_configuration(building, locator, config) → Dict` - Load supply system config (production or what-if mode)
- `validate_district_assembly_consistency(building_configs) → None` - Validate all district buildings use same assembly
- `aggregate_buildings_summary(building_dfs, plant_dfs, locator) → DataFrame` - Create annual summary
- `create_final_energy_breakdown(building_dfs, plant_dfs, building_configs, locator, config) → DataFrame` - Create detailed breakdown

## Key Patterns

### ✅ DO: What-If Mode Assembly Selection (Override Logic)

```python
# User provides both building and district assemblies:
supply_type_hs = ['SUPPLY_HEATING_AS3 (building)', 'SUPPLY_HEATING_AS9 (district)']

# For each building:
# 1. Read supply.csv to get configured scale
# 2. Check network connectivity (substation file exists)
# 3. Apply override logic:

# supply.csv=DISTRICT + no connection → use building (fallback)
if configured == 'DISTRICT' and not is_connected:
    use_assembly = building_assembly  # AS3

# supply.csv=DISTRICT + has connection → use district (keep)
if configured == 'DISTRICT' and is_connected:
    use_assembly = district_assembly  # AS9

# supply.csv=BUILDING + no connection → use building (keep)
if configured == 'BUILDING' and not is_connected:
    use_assembly = building_assembly  # AS3

# supply.csv=BUILDING + has connection → use district (upgrade)
if configured == 'BUILDING' and is_connected:
    use_assembly = district_assembly  # AS9

# 4. Validate: All district buildings must use same assembly type
validate_district_assembly_consistency(building_configs)
```

## Key Patterns (continued)

### ✅ DO: Use constant efficiency from COMPONENTS

```python
# Load component to get efficiency
component_info = load_component_info('BO1', locator)
carrier = component_info['carrier']  # 'NATURALGAS'
efficiency = component_info['efficiency']  # 0.82

# Apply efficiency
final_energy_kWh = demand_kWh / efficiency
```

### ✅ DO: Read district consumption from thermal-network

```python
# For district systems, read actual consumption
if scale == 'DISTRICT':
    dh_data = load_district_heating_data(building, network_name, locator)
    final_energy['Qhs_sys_DH_kWh'] = dh_data['DH_hs_kWh']
```

### ✅ DO: Handle missing network files gracefully

```python
try:
    booster_data = load_booster_data(building, network_name, 'hs', locator)
    # Process booster data
except FileNotFoundError:
    # Building not connected to network or network not calculated
    pass
```

### ❌ DON'T: Use part-load curves or variable efficiency

```python
# ❌ WRONG - No part-load curves
efficiency = calculate_partload_efficiency(load_ratio)

# ✅ CORRECT - Use constant efficiency from COMPONENTS
efficiency = component_info['efficiency']
```

### ❌ DON'T: Calculate district energy with efficiency

```python
# ❌ WRONG - Don't apply efficiency to district consumption
final_energy = district_consumption / efficiency

# ✅ CORRECT - Use consumption directly (efficiency at plant)
final_energy = district_consumption
```

## Data Flow

```
1. Load supply configuration
   supply.csv OR config params → ASSEMBLIES → COMPONENTS → efficiency + carrier

2. Calculate building-scale systems
   demand / efficiency → final_energy_by_carrier

3. Load district-scale systems
   thermal-network substation files → actual_consumption

4. Aggregate and export
   individual files + summary + breakdown + JSON config
```

## Important Database Workflow

```python
# Assembly → Component → Feedstock
assembly_df = supply_db.heating  # From Supply.from_locator()
assembly = assembly_df.loc['SUPPLY_HEATING_AS3']
component_code = assembly['primary_components']  # 'BO1'

# Component has efficiency and fuel
component_file = locator.get_db4_components_conversion_conversion_technology_csv('BOILERS')
component_df = pd.read_csv(component_file)
component = component_df[component_df['code'] == component_code].iloc[0]
efficiency = component['min_eff_rating']  # 0.82
fuel_code = component['fuel_code']  # 'Cgas'
carrier = map_fuel_code_to_carrier(fuel_code)  # 'NATURALGAS'
```

## Output Structure

```
outputs/data/final-energy/{whatif-name}/
├── B####.csv               # Individual buildings (8760 rows)
├── final_energy_buildings.csv  # Annual summary (1 row/building)
├── final_energy.csv        # Detailed breakdown (multiple rows/building)
└── supply_configuration.json    # Configuration used
```

### ✅ DO: District Plant Calculation

```python
# Plant final energy calculated from thermal-network results
plant_load_df = pd.read_csv(f'{network_folder}/DH_{network_name}_plant_thermal_load_kW.csv')
pumping_df = pd.read_csv(f'{network_folder}/DH_{network_name}_plant_pumping_load_kW.csv')

# Apply plant efficiency (default: gas boiler 0.85 for DH, electric chiller COP 3.0 for DC)
fuel_kWh = plant_load_df['thermal_load_kW'] / 0.85
pumping_kWh = pumping_df.iloc[:, 0]

# Output includes:
# - plant_heating_NATURALGAS_kWh (or plant_cooling_GRID_kWh)
# - plant_pumping_GRID_kWh
# - Metadata: scale, plant_name, network_name, network_type
```

### ✅ DO: Booster Systems (Requires Thermal-Network)

```python
# Boosters are read from substation files (not calculated from scratch)
substation_df = pd.read_csv(f'{network_folder}/DH/substation/DH_{network}_substation_{building}.csv')

# Extract booster columns
Qhs_booster_W = substation_df['Qhs_booster_W']  # Space heating booster
Qww_booster_W = substation_df['Qww_booster_W']  # Hot water booster

# Apply booster efficiency from config (what-if) or default (production)
booster_fuel_kWh = booster_demand_kWh / efficiency

# Note: Boosters require thermal-network to have been run first
```

## Common Issues

**Issue**: "Multiple district heating assembly types detected"
→ What-if mode validation failed - all district buildings must use same assembly
→ Solution: Provide only one district assembly in supply-type-hs (e.g., only AS9, not AS9+AS10)

**Issue**: "District substation file not found"
→ Building has district assembly but thermal-network not run for this network
→ Solution: Run `cea thermal-network --network-name xxx` first

**Issue**: "Component {code} not found"
→ Check ASSEMBLIES primary_components references valid COMPONENTS codes

**Issue**: Wrong efficiency values
→ Boilers use `min_eff_rating`, heat pumps use `min_eff_rating_seasonal`
→ Check component file structure for correct column name

**Issue**: What-if mode not working as expected
→ Check that you've provided both building AND district assemblies for the same service
→ Example: `['SUPPLY_HEATING_AS3 (building)', 'SUPPLY_HEATING_AS9 (district)']`
→ The code uses override logic based on supply.csv + network connectivity

## Config Parameters

**What-if mode**:
- Assembly codes in config include scale labels: `"SUPPLY_HEATING_AS3 (building)"`
- Strip labels before database lookup: `assembly_code.split(' (')[0]`

**Production mode**:
- Read from `supply.csv` with `building_supply['supply_type_hs']`
- No scale labels in CSV, use raw codes

## Implementation Status

**✅ Completed Features:**
- Building-scale final energy calculation (gas boilers, heat pumps, chillers)
- District heating/cooling (reads from thermal-network substation files)
- Booster systems (space heating + hot water)
- District plant final energy calculation (heating plant + pumping)
- What-if mode with assembly override logic
- Validation: all district buildings use same assembly
- Aggregation: buildings + plants in summary and breakdown files

**Prerequisites:**
- **Demand calculation**: `cea demand` must run first
- **Thermal-network** (for district systems): `cea thermal-network --network-name xxx` must run before final-energy
- **supply.csv**: Must be populated with building supply configurations (production mode only)

**Limitations:**
- Plant equipment type currently uses defaults (gas boiler for DH, electric chiller for DC)
- Booster calculation requires pre-existing thermal-network results (cannot synthesize standalone)
- Solar thermal not yet implemented

## Testing

```python
# Test what-if mode with override logic
config.final_energy.overwrite_supply_settings = True
config.final_energy.network_name = 'xxx'
config.final_energy.supply_type_hs = ['SUPPLY_HEATING_AS3', 'SUPPLY_HEATING_AS9']

# Buildings will be assigned AS3 (building) or AS9 (district) based on:
# 1. Their configured scale in supply.csv
# 2. Actual network connectivity (substation file exists)

# Test single building calculation
building = 'B1000'
final_energy_df = calculate_building_final_energy(building, locator, config)
print(final_energy_df[['Qhs_sys_kWh', 'Qhs_sys_NATURALGAS_kWh']].sum())

# Verify efficiency
demand = final_energy_df['Qhs_sys_kWh'].sum()
final = final_energy_df['Qhs_sys_NATURALGAS_kWh'].sum()
efficiency = demand / final  # Should match component efficiency

# Test validation
building_configs = {...}  # Dict of building -> supply_config
validate_district_assembly_consistency(building_configs)  # Should not raise if consistent
```

## Related Files

- `main.py` - Entry point, workflow orchestration
- `calculation.py` - Core calculation logic
- `BACKEND_PLAN.md` - File schemas, CSV structures
- `IMPLEMENTATION_PLAN.md` - Design decisions, approach
- `cea/databases/AGENTS.md` - Database structure (ASSEMBLIES vs COMPONENTS)
