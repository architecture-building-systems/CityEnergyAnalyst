# Primary Energy Calculation - Migration Reference

**Purpose:** This document captures the logic from the old demand module's primary energy calculations before deletion. Use this as a reference when implementing the new primary-energy module.

**Date Created:** 2026-01-26
**Date Updated:** 2026-01-27 (added backward compatibility validation strategy)
**Original Locations:**
- `cea/demand/thermal_loads.py` (lines 214-319) - calc_Qcs_sys(), calc_Qhs_sys()
- `cea/demand/hotwater_loads.py` (lines 156-234) - calc_Qwwf()
- `cea/demand/electrical_loads.py` (lines 75-127) - calc_Ef()
**Status:** All primary energy calculation functions deleted from demand module

---

## Overview

The old demand module calculated primary energy consumption by applying simple efficiency factors from the ASSEMBLIES database to end-use demand. The new primary-energy module should use COMPONENTS database with more sophisticated efficiency models.

---

## Key Patterns to Preserve

### 1. Scale-based Routing Logic

Primary energy calculation depends on whether the supply system is building-scale or district-scale:

```python
scale_technology = bpr.supply['scale_hs']  # or scale_cs, scale_dhw

if scale_technology == "BUILDING":
    # Calculate from building-scale component efficiency
    # Use COMPONENTS database (BO1, BO2, CH1, etc.)
    primary_energy = calculate_from_components(demand, components)

elif scale_technology == "DISTRICT":
    # Use district network results
    # Read from thermal-network outputs
    primary_energy = get_from_district_network(building, service)

elif scale_technology == "NONE":
    # No heating/cooling system
    primary_energy = 0.0
```

**Why this matters:** Buildings connected to district heating/cooling get energy from the central plant, so their primary energy comes from network-level calculations, not building-level component efficiency.

---

### 2. Service Types

Primary energy must be calculated separately for each service:

| Service | Column Prefix | End-Use Demand | Supply Config | Old Function |
|---------|---------------|----------------|---------------|--------------|
| Heating | `hs` | `Qhs_sys_kWh` | `supply_type_hs` | `calc_Qhs_sys()` |
| Cooling | `cs` | `Qcs_sys_kWh` | `supply_type_cs` | `calc_Qcs_sys()` |
| Hot Water | `dhw` or `ww` | `Qww_sys_kWh` | `supply_type_dhw` | `calc_Qwwf()` |
| Electricity | `el` | `E_sys_kWh` | `supply_type_el` | `calc_Ef()` |

---

### 3. Energy Carrier Mapping

**OLD logic (from ASSEMBLIES `feedstock` field):**

Each supply system type had a `feedstock` field that determined which output column to populate:

#### Heating (`hs`):
| Feedstock | Output Column | Description |
|-----------|---------------|-------------|
| `GRID` | `GRID_hs_kWh` | Electric heating (heat pump, electric resistance) |
| `NATURALGAS` | `NG_hs_kWh` | Natural gas boiler |
| `OIL` | `OIL_hs_kWh` | Oil boiler |
| `COAL` | `COAL_hs_kWh` | Coal furnace |
| `WOOD` | `WOOD_hs_kWh` | Wood/biomass boiler |
| `SOLAR` | `SOLAR_hs_kWh` | Solar thermal (not implemented in old code) |
| District (scale=DISTRICT) | `DH_hs_kWh` | District heating |
| `NONE` | (all zeros) | No heating system |

#### Cooling (`cs`):
| Feedstock | Scale | Output Column | Description |
|-----------|-------|---------------|-------------|
| `GRID` | `BUILDING` | `GRID_cs_kWh` | Electric chiller (building-scale) |
| `GRID` | `DISTRICT` | `DC_cs_kWh` | District cooling |
| `NONE` | - | (all zeros) | No cooling system |

**Note:** Cooling always uses `GRID` as feedstock; the `scale` determines whether it's building chiller or district cooling.

#### Hot Water (`dhw`):
| Feedstock | Output Column | Description |
|-----------|---------------|-------------|
| `GRID` | `GRID_ww_kWh` | Electric water heater |
| `NATURALGAS` | `NG_ww_kWh` | Gas water heater |
| `OIL` | `OIL_ww_kWh` | Oil water heater |
| `COAL` | `COAL_ww_kWh` | Coal water heater |
| `WOOD` | `WOOD_ww_kWh` | Wood water heater |
| `SOLAR` | `SOLAR_ww_kWh` | Solar thermal water heating |
| District (scale=DISTRICT) | `DH_ww_kWh` | District heating for hot water |

**NEW approach (from COMPONENTS database):**

Map component codes to feedstock:
- `BO1` (gas boiler) → `NG_hs_kWh`
- `BO2` (oil boiler) → `OIL_hs_kWh`
- `BO4` (coal boiler) → `COAL_hs_kWh`
- `BO5` (electric boiler) → `GRID_hs_kWh`
- `HP1` (air-source heat pump) → `GRID_hs_kWh`
- `CH1`, `CH2`, `CH3` (chillers) → `GRID_cs_kWh`
- etc.

Each component in COMPONENTS database has a `feedstock` field that specifies its energy source.

---

## Old Calculation Formula

### Building-Scale (Simple Division)

```python
# OLD approach from ASSEMBLIES
efficiency_average_year = bpr.supply['eff_hs']  # Single efficiency value
primary_energy = end_use_demand / efficiency_average_year
```

**Example:**
- End-use demand: `Qhs_sys_kWh = 1000 kWh`
- Efficiency: `eff_hs = 0.9` (90% efficient boiler)
- Primary energy: `NG_hs_kWh = 1000 / 0.9 = 1111.11 kWh`

### District-Scale (Direct Assignment)

```python
# District heating/cooling - no efficiency loss at building level
# The efficiency is handled at the network central plant
DH_hs = Qhs_sys / efficiency_average_year  # Usually efficiency = 1.0 for district
```

**Why:** The building receives hot/cold water from the district network. The conversion efficiency happens at the central plant, not the building.

---

## New Calculation Approach (for primary-energy module)

### Use COMPONENTS Database

Instead of simple division, use component-specific models:

```python
# Load component from COMPONENTS database
component = load_component(supply_components['primary'][0])  # e.g., 'BO1'

# Apply component-specific efficiency model
if component.type == 'BOILER':
    fuel_consumption = demand / component.thermal_efficiency

elif component.type == 'HEAT_PUMP':
    # Heat pumps have COP (coefficient of performance)
    electricity_consumption = demand / component.COP

elif component.type == 'CHILLER':
    electricity_consumption = demand / component.COP

elif component.type == 'CHP':
    # Combined heat and power - produces both heat and electricity
    fuel_consumption = demand / component.thermal_efficiency
    electricity_production = fuel_consumption * component.electrical_efficiency

elif component.type == 'SOLAR_THERMAL':
    # Solar has no fuel consumption, but may have backup
    solar_fraction = calculate_solar_fraction(demand, solar_availability)
    backup_fuel = (demand * (1 - solar_fraction)) / backup_component.efficiency
```

**Advanced:** Could support part-load efficiency curves, temperature-dependent COP, etc.

---

## Old Code Reference

### `calc_Qcs_sys()` - Cooling Primary Energy

**Original location:** `cea/demand/thermal_loads.py:214-243`

**Logic:**
```python
def calc_Qcs_sys(bpr, tsd):
    energy_source = bpr.supply['source_cs']
    scale_technology = bpr.supply['scale_cs']
    efficiency_average_year = bpr.supply['eff_cs']

    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            E_cs = abs(Qcs_sys) / efficiency_average_year
            DC_cs = 0
        elif energy_source == "NONE":
            E_cs = 0
            DC_cs = 0

    elif scale_technology == "DISTRICT":
        if energy_source == "GRID":
            DC_cs = Qcs_sys / efficiency_average_year
            E_cs = 0
        elif energy_source == "NONE":
            DC_cs = 0
            E_cs = 0

    elif scale_technology == "NONE":
        DC_cs = 0
        E_cs = 0
```

**Key insight:** Cooling uses `GRID` as feedstock for both building and district. The `scale` determines output column:
- Building-scale → `GRID_cs_kWh` (electric chiller)
- District-scale → `DC_cs_kWh` (district cooling)

---

### `calc_Qhs_sys()` - Heating Primary Energy

**Original location:** `cea/demand/thermal_loads.py:246-319`

**Logic:**
```python
def calc_Qhs_sys(bpr, tsd):
    energy_source = bpr.supply['source_hs']
    scale_technology = bpr.supply['scale_hs']
    efficiency_average_year = bpr.supply['eff_hs']

    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            E_hs = Qhs_sys / efficiency
            NG_hs = COAL_hs = OIL_hs = WOOD_hs = DH_hs = 0
        elif energy_source == "NATURALGAS":
            NG_hs = Qhs_sys / efficiency
            E_hs = COAL_hs = OIL_hs = WOOD_hs = DH_hs = 0
        elif energy_source == "OIL":
            OIL_hs = Qhs_sys / efficiency
            E_hs = NG_hs = COAL_hs = WOOD_hs = DH_hs = 0
        elif energy_source == "COAL":
            COAL_hs = Qhs_sys / efficiency
            E_hs = NG_hs = OIL_hs = WOOD_hs = DH_hs = 0
        elif energy_source == "WOOD":
            WOOD_hs = Qhs_sys / efficiency
            E_hs = NG_hs = COAL_hs = OIL_hs = DH_hs = 0
        elif energy_source == "NONE":
            E_hs = NG_hs = COAL_hs = OIL_hs = WOOD_hs = DH_hs = 0

    elif scale_technology == "DISTRICT":
        DH_hs = Qhs_sys / efficiency
        E_hs = NG_hs = COAL_hs = OIL_hs = WOOD_hs = 0

    elif scale_technology == "NONE":
        E_hs = NG_hs = COAL_hs = OIL_hs = WOOD_hs = DH_hs = 0
```

**Key insight:** Only ONE fuel type is active at a time; all others set to zero.

---

### `calc_Qwwf()` - Hot Water Primary Energy

**Original location:** `cea/demand/hotwater_loads.py:156-234`

**Logic:**
```python
def calc_Qwwf(bpr, tsd):
    energy_source = bpr.supply['source_dhw']
    scale_technology = bpr.supply['scale_dhw']
    efficiency_average_year = bpr.supply['eff_dhw']

    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            E_ww = Qww_sys / efficiency
            DH_ww = NG_ww = COAL_ww = OIL_ww = WOOD_ww = 0
        elif energy_source == "NATURALGAS":
            NG_ww = Qww_sys / efficiency
            E_ww = DH_ww = COAL_ww = OIL_ww = WOOD_ww = 0
        elif energy_source == "OIL":
            OIL_ww = Qww_sys / efficiency
            E_ww = DH_ww = NG_ww = COAL_ww = WOOD_ww = 0
        elif energy_source == "COAL":
            COAL_ww = Qww_sys / efficiency
            E_ww = DH_ww = NG_ww = OIL_ww = WOOD_ww = 0
        elif energy_source == "WOOD":
            WOOD_ww = Qww_sys / efficiency
            E_ww = DH_ww = NG_ww = COAL_ww = OIL_ww = 0
        elif energy_source == "SOLAR":
            SOLAR_ww = Qww_sys / efficiency
            E_ww = DH_ww = NG_ww = COAL_ww = OIL_ww = WOOD_ww = 0
        elif energy_source == "NONE":
            E_ww = DH_ww = NG_ww = COAL_ww = OIL_ww = WOOD_ww = 0

    elif scale_technology == "DISTRICT":
        DH_ww = Qww_sys / efficiency
        E_ww = NG_ww = COAL_ww = OIL_ww = WOOD_ww = 0

    elif scale_technology == "NONE":
        E_ww = DH_ww = NG_ww = COAL_ww = OIL_ww = WOOD_ww = 0
```

**Key insight:** Identical logic to heating/cooling - simple division by efficiency factor. Note SOLAR energy source is supported for DHW (unlike heating/cooling).

---

### `calc_Ef()` - Electricity Primary Energy

**Original location:** `cea/demand/electrical_loads.py:75-127`

**Logic:**
```python
def calc_Ef(bpr, tsd):
    energy_source = bpr.supply['source_el']
    scale_technology = bpr.supply['scale_el']

    # Sum all end-use electricity demands
    total_el_demand = sum([Eve, Ea, El, Edata, Epro, Eaux, Ev,
                           E_ww, E_cs, E_hs, E_cdata, E_cre])

    if scale_technology == "CITY":
        if energy_source == "GRID":
            # Copy each end-use component to GRID_* equivalent
            GRID = total_el_demand
            GRID_a = Ea
            GRID_l = El
            GRID_v = Ev
            GRID_ve = Eve
            GRID_data = Edata
            GRID_pro = Epro
            GRID_aux = Eaux
            GRID_ww = E_ww
            GRID_cs = E_cs
            GRID_hs = E_hs
            GRID_cdata = E_cdata
            GRID_cre = E_cre

    elif scale_technology == "NONE":
        # All GRID_* fields set to zero
        GRID = GRID_a = GRID_l = ... = 0
```

**Key insight:** Unlike heating/cooling/DHW, electricity has NO efficiency factor - it's a simple 1:1 copy from end-use (E_*) to primary energy (GRID_*). This was just mapping end-use electricity to grid electricity.

**Note:** References to E_ww, E_cs, E_hs, E_cdata, E_cre no longer exist after removal of primary energy fields.

---

## Test Cases for Validation

When implementing the new primary-energy module, verify outputs match these expected values:

### Test 1: Natural Gas Boiler (Building-Scale)
**Input:**
- `Qhs_sys_kWh = 10000 kWh` (annual heating demand)
- `supply_type_hs = SUPPLY_HEATING_AS3` (NG boiler)
- ASSEMBLIES efficiency: `eff_hs = 0.9`

**Expected Output:**
- `NG_hs_kWh = 11111.11 kWh` (10000 / 0.9)
- All other heating columns: `0`

---

### Test 2: Electric Chiller (Building-Scale)
**Input:**
- `Qcs_sys_kWh = 5000 kWh` (annual cooling demand)
- `supply_type_cs = SUPPLY_COOLING_AS1` (electric chiller)
- ASSEMBLIES efficiency (COP): `eff_cs = 3.0`

**Expected Output:**
- `GRID_cs_kWh = 1666.67 kWh` (5000 / 3.0)
- `DC_cs_kWh = 0`

---

### Test 3: District Heating
**Input:**
- `Qhs_sys_kWh = 20000 kWh`
- `supply_type_hs = SUPPLY_HEATING_AS10` (district heating)
- `scale_hs = DISTRICT`
- ASSEMBLIES efficiency: `eff_hs = 1.0` (typically no loss at building level)

**Expected Output:**
- `DH_hs_kWh = 20000 kWh` (20000 / 1.0)
- All other heating columns: `0`

**Note:** In reality, district heating should get actual consumption from thermal-network simulation results.

---

### Test 4: District Cooling
**Input:**
- `Qcs_sys_kWh = 8000 kWh`
- `supply_type_cs = SUPPLY_COOLING_AS5` (district cooling)
- `scale_cs = DISTRICT`
- ASSEMBLIES efficiency: `eff_cs = 1.0`

**Expected Output:**
- `DC_cs_kWh = 8000 kWh`
- `GRID_cs_kWh = 0`

---

### Test 5: Heat Pump (Building-Scale)
**Input:**
- `Qhs_sys_kWh = 15000 kWh`
- `supply_type_hs = SUPPLY_HEATING_AS6` (air-source heat pump)
- ASSEMBLIES efficiency (COP): `eff_hs = 3.5`

**Expected Output:**
- `GRID_hs_kWh = 4285.71 kWh` (15000 / 3.5)
- All fuel columns: `0`
- `DH_hs_kWh = 0`

---

### Test 6: No Heating System
**Input:**
- `Qhs_sys_kWh = 0 kWh`
- `supply_type_hs = SUPPLY_HEATING_AS0` (none)
- `scale_hs = NONE`

**Expected Output:**
- All heating primary energy columns: `0`

---

## Data Flow Comparison

### OLD (demand module):
```
1. Read supply.csv → get supply_type_hs
2. Look up ASSEMBLIES → get feedstock, scale, efficiency
3. Calculate: primary_energy = Qhs_sys / efficiency
4. Write to demand output file
```

### NEW (primary-energy module):
```
1. Read supply.csv → get supply_type_hs
2. Look up ASSEMBLIES → get scale, primary_components
3. If scale == "BUILDING":
   a. Look up COMPONENTS → get component specs (efficiency, COP, curves)
   b. Calculate: primary_energy = component.operate(demand)
4. If scale == "DISTRICT":
   a. Look up thermal-network results
   b. Extract: primary_energy = network_consumption[building]
5. Write to primary-energy output file
```

---

## Output Column Specifications

### All Primary Energy Columns (to be generated)

**Heating:**
- `GRID_hs_kWh` - Electric heating (heat pumps, electric resistance)
- `NG_hs_kWh` - Natural gas heating
- `COAL_hs_kWh` - Coal heating
- `OIL_hs_kWh` - Oil heating
- `WOOD_hs_kWh` - Wood/biomass heating
- `SOLAR_hs_kWh` - Solar thermal heating
- `DH_hs_kWh` - District heating

**Cooling:**
- `GRID_cs_kWh` - Electric cooling (chillers)
- `DC_cs_kWh` - District cooling
- `GRID_cdata_kWh` - Electric cooling for data centers
- `DC_cdata_kWh` - District cooling for data centers
- `GRID_cre_kWh` - Electric cooling for refrigeration
- `DC_cre_kWh` - District cooling for refrigeration

**Hot Water:**
- `GRID_ww_kWh` - Electric water heating
- `NG_ww_kWh` - Natural gas water heating
- `COAL_ww_kWh` - Coal water heating
- `OIL_ww_kWh` - Oil water heating
- `WOOD_ww_kWh` - Wood water heating
- `SOLAR_ww_kWh` - Solar thermal water heating
- `DH_ww_kWh` - District heating for hot water

**Electricity:**
- `GRID_el_kWh` - Grid electricity for appliances, lighting, auxiliary (may just be copy of E_sys_kWh)

**Annual Totals (MWhyr):**
- Add `_MWhyr` suffix for annual total versions of all above columns

---

## Implementation Recommendations

### 1. Start Simple, Then Enhance
- **Phase 1:** Replicate old behavior (simple division by efficiency)
- **Phase 2:** Add component-specific models (COP curves, part-load, etc.)
- **Phase 3:** Integrate with thermal-network results for district systems

### 2. Component Database Structure
Expected structure from COMPONENTS database:
```python
# COMPONENTS/CONVERSION/BOILERS.csv
{
    'code': 'BO1',
    'technology': 'BOILER',
    'feedstock': 'NATURALGAS',
    'thermal_efficiency': 0.92,
    'min_load': 0.3,
    'CAPEX_a_USD': ...,
    'CAPEX_b_USDkW': ...,
    # etc.
}
```

### 3. District System Integration
```python
# Check if thermal-network results exist
network_file = locator.get_optimization_substations_total_file(network_name)
if os.path.exists(network_file):
    # Read actual network consumption
    df = pd.read_csv(network_file)
    DH_hs = df[f'{building}_kW'] * hours_to_kWh
else:
    # Fallback: simple calculation
    DH_hs = Qhs_sys  # Assume no loss at building level
```

### 4. Handle Multiple Components
Some supply systems have primary, secondary, and tertiary components:
```python
# e.g., CHP (primary) + backup boiler (secondary) + heat rejection (tertiary)
primary_fuel = 0
primary_electricity_out = 0
secondary_fuel = 0

for component_code in supply_components['primary']:
    component = load_component(component_code)
    fuel, elec_out = component.operate(demand)
    primary_fuel += fuel
    primary_electricity_out += elec_out

# If primary can't meet demand, use secondary
if demand_unmet > 0:
    for component_code in supply_components['secondary']:
        # ...
```

---

## Migration Checklist

When implementing primary-energy module:

- [ ] Read end-use demand from `outputs/data/demand/{building}.csv`
- [ ] Read supply configuration from `inputs/building-properties/supply.csv`
- [ ] Load ASSEMBLIES database for scale and component references
- [ ] Load COMPONENTS database for efficiency specifications
- [ ] Implement scale-based routing (BUILDING vs DISTRICT)
- [ ] Implement component-to-feedstock mapping
- [ ] Calculate primary energy for heating (hs)
- [ ] Calculate primary energy for cooling (cs)
- [ ] Calculate primary energy for hot water (dhw)
- [ ] Calculate primary energy for electricity (el)
- [ ] Handle district systems (DH/DC) from network results
- [ ] Write output to `outputs/data/primary-energy/{building}.csv`
- [ ] Include all original demand columns in output
- [ ] Validate against test cases (match old behavior)
- [ ] Add annual totals (MWhyr columns)
- [ ] Update schema in `schemas.yml`
- [ ] Add InputLocator methods
- [ ] Register in `scripts.yml`

---

## Backward Compatibility: Database Validation

### Problem

Primary energy calculation requires `primary_components`, `secondary_components`, and `tertiary_components` columns in SUPPLY assemblies (added in v4.0). Users with older databases or custom databases may be missing these columns.

### Strategy: Lazy Validation with Auto-Repair

**Design principles:**
1. **Demand calculation continues working** - Only needs `scale` (already exists)
2. **Primary energy validates on first use** - Check when user runs primary energy feature
3. **Auto-repair + helpful guidance** - Add empty placeholder columns, show clear error

### Implementation Reference

Add this validation function to the primary energy module:

```python
def validate_supply_database_for_primary_energy(locator):
    """
    Validate that SUPPLY assemblies have required columns for primary energy calculation.
    Auto-repairs missing columns with placeholders and provides helpful error messages.

    Called at the start of primary energy calculation to ensure database is ready.

    :param locator: InputLocator object
    :raises ValueError: If required columns are missing (after auto-repair)
    """
    import pandas as pd

    supply_files = {
        'SUPPLY_HEATING': locator.get_database_assemblies_supply_heating(),
        'SUPPLY_COOLING': locator.get_database_assemblies_supply_cooling(),
        'SUPPLY_HOTWATER': locator.get_database_assemblies_supply_hot_water(),
        'SUPPLY_ELECTRICITY': locator.get_database_assemblies_supply_electricity(),
    }

    required_columns = ['primary_components', 'secondary_components', 'tertiary_components']
    issues = {}

    # Check each supply file for missing columns
    for name, filepath in supply_files.items():
        df = pd.read_csv(filepath)
        missing = [col for col in required_columns if col not in df.columns]

        if missing:
            # Auto-repair: Add empty columns with '-' placeholder (CEA convention for "none")
            for col in missing:
                df[col] = '-'
            df.to_csv(filepath, index=False)
            issues[name] = (filepath, missing)

    if issues:
        # Format helpful error message with two solution paths
        error_msg = (
            "⚠️  Primary energy calculation requires component information in SUPPLY assemblies.\n\n"
            "The following files were missing required columns and have been updated with placeholders:\n\n"
        )

        for name, (filepath, missing) in issues.items():
            error_msg += f"  ❌ {name}\n"
            error_msg += f"     File: {filepath}\n"
            error_msg += f"     Missing: {', '.join(missing)}\n"
            error_msg += f"     Status: Empty columns added (values set to '-')\n\n"

        error_msg += (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "To fix this properly, choose one option:\n\n"
            "  Option 1: Using default CEA database (Recommended)\n"
            "  ─────────────────────────────────────────────────\n"
            "  Run Database Helper to reload the default database:\n"
            "    $ cea database-helper --save\n\n"
            "  This will restore the complete database with all component information.\n\n"

            "  Option 2: Using custom database\n"
            "  ────────────────────────────────\n"
            "  Manually fill in the component columns for each supply assembly.\n\n"
            "  Column meanings:\n"
            "    - primary_components:   Main equipment (e.g., 'BO5' for boiler, 'CH2' for chiller)\n"
            "    - secondary_components: Supporting equipment (e.g., pumps, heat exchangers)\n"
            "    - tertiary_components:  Additional equipment (e.g., cooling towers)\n"
            "    - Use '-' for no component\n\n"

            "  Example from default database:\n"
            "    SUPPLY_HOTWATER_AS1: primary='BO2', secondary='-', tertiary='-'\n"
            "    SUPPLY_COOLING_AS2:  primary='CH2', secondary='-', tertiary='CT1'\n\n"

            "  Component codes reference:\n"
            "    - Boilers:       databases/CH/COMPONENTS/CONVERSION/BOILERS.csv\n"
            "    - Chillers:      databases/CH/COMPONENTS/CONVERSION/CHILLERS.csv\n"
            "    - Heat Pumps:    databases/CH/COMPONENTS/CONVERSION/HEATPUMPS.csv\n"
            "    - Cooling Towers: databases/CH/COMPONENTS/CONVERSION/COOLING_TOWERS.csv\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "After fixing, re-run the primary energy calculation.\n"
        )

        raise ValueError(error_msg)


def main(config):
    """Primary energy calculation entry point."""
    locator = InputLocator(config.scenario)

    # Validate database before any calculations
    # This will auto-repair and raise helpful error if components are missing
    validate_supply_database_for_primary_energy(locator)

    # Proceed with primary energy calculations
    # ...
```

### Why This Approach Works

✅ **Non-breaking for demand users** - Validation only triggers when using primary energy feature
✅ **Auto-repair safety net** - Adds placeholder columns to prevent hard crashes
✅ **Clear user guidance** - Two distinct paths based on database origin
✅ **Lazy validation** - Only checks when feature is actually used
✅ **Maintains integrity** - Forces users to provide proper values before calculations run

### Testing

Create test case to verify validation:

```python
def test_validate_supply_database_missing_components(locator, monkeypatch):
    """Test that validation detects and repairs missing component columns."""
    # Remove primary_components column from SUPPLY_HOTWATER.csv
    supply_file = locator.get_database_assemblies_supply_hot_water()
    df = pd.read_csv(supply_file)
    df = df.drop(columns=['primary_components'])
    df.to_csv(supply_file, index=False)

    # Validation should auto-repair and raise informative error
    with pytest.raises(ValueError, match="SUPPLY_HOTWATER.*missing required columns"):
        validate_supply_database_for_primary_energy(locator)

    # Verify column was added with placeholder
    df_repaired = pd.read_csv(supply_file)
    assert 'primary_components' in df_repaired.columns
    assert (df_repaired['primary_components'] == '-').all()
```

### Migration Timeline

**v4.0-beta.6 (Current):**
- Primary energy removed from demand module ✅
- SUPPLY assemblies updated with component columns ✅
- Documentation added ✅

**v4.0-beta.7+ (When primary energy feature is implemented):**
- Add `validate_supply_database_for_primary_energy()` function
- Call validation at start of primary energy calculation
- Add test cases for validation logic

---

## Related Files (for future implementation)

- `cea/optimization_new/component.py` - Reference for component operation models
- `cea/optimization_new/building.py` - Reference for supply system loading
- `cea/technologies/` - Technology-specific calculation functions
- `cea/databases/COMPONENTS/CONVERSION/` - Component specifications

---

**End of Migration Reference**
