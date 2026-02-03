# Final Energy Calculation - Implementation Plan

**Date Created:** 2026-02-02
**Last Updated:** 2026-02-02 (finalized design decisions)
**Purpose:** Design plan for new final-energy module using optimization-new equations
**Target Output Format:** Similar to hourly_operational_emission.py
**Status:** ✅ Design finalized, ready for implementation

---

## 1. Overview

### Goal
Calculate final energy (energy by carrier) for buildings using the same component-based efficiency models from optimization-new, outputting hourly timeseries in the same shape as emissions output.

### Key Differences from Old Approach
| Aspect | Old (ASSEMBLIES) | New (Final Energy) |
|--------|-----------------|------------------------|
| **Efficiency** | Single annual average | Component-specific constant COP/efficiency from COMPONENTS database |
| **Calculation** | Simple division: `E = Q / η` | **Same:** Simple division `E = Q / η` (hourly) |
| **Temporal** | Annual totals only | Hourly profiles (8760 rows) |
| **What-if** | Not supported | Support what-if scenarios with parameter overrides |

**Note:** We use constant efficiency (not part-load curves) to match CEA database approach.

---

## 2. Core Equations (from optimization-new)

### Building-Scale Systems

**Boiler** (`cea/technologies/boiler.py`):
```python
Q_fuel_Wh = Q_load_Wh / thermal_efficiency
# Example: 100 kWh heating ÷ 0.85 efficiency = 117.6 kWh natural gas
```

**Heat Pump** (`cea/technologies/heatpumps.py`):
```python
P_elec_Wh = Q_load_Wh / COP
Q_ambient_Wh = Q_load_Wh - P_elec_Wh
# Example: 100 kWh heating ÷ 3.0 COP = 33.3 kWh electricity + 66.7 kWh ambient
```

**Vapor Compression Chiller** (`cea/technologies/chiller_vapor_compression.py`):
```python
P_elec_Wh = Q_cool_Wh / COP
Q_waste_heat_Wh = Q_cool_Wh + P_elec_Wh
# Example: 100 kWh cooling ÷ 2.5 COP = 40 kWh electricity
```

**Absorption Chiller** (`cea/technologies/chiller_absorption.py`):
```python
Q_heat_in_Wh = Q_cool_Wh / COP
P_elec_aux_Wh = Q_cool_Wh * aux_power_share
# Example: 100 kWh cooling ÷ 0.7 COP = 142.9 kWh heat + 5 kWh electricity
```

### District Systems

**Network connectivity determines supply type**:
- **Connected buildings**: Read from thermal-network simulation results
- **Not connected**: Fall back to building-scale calculations

```python
if building in network_connected_buildings[service]:
    # District supply: read from network substation results
    DH_hs_kWh = network_results[building]['QH_sys_kWh']
else:
    # Building-scale supply: calculate from components
    if component_code == 'BO1':
        NG_hs_kWh = Qhs_sys_kWh / component_efficiency
```

---

## 3. Output Format (Match hourly_operational_emission.py)

### File Structure

**Path:** `outputs/data/final-energy/{what-if-name}/{building}.csv`

**Index:** `hour` (0-8759)

**Columns:**

```
hour,date,Qhs_sys_NATURALGAS_kWh,Qhs_sys_OIL_kWh,Qhs_sys_COAL_kWh,Qhs_sys_WOOD_kWh,Qhs_sys_GRID_kWh,Qhs_sys_SOLAR_kWh,Qhs_sys_DH_kWh,Qhs_sys_NONE_kWh,
Qww_sys_NATURALGAS_kWh,Qww_sys_OIL_kWh,Qww_sys_COAL_kWh,Qww_sys_WOOD_kWh,Qww_sys_GRID_kWh,Qww_sys_SOLAR_kWh,Qww_sys_DH_kWh,Qww_sys_NONE_kWh,
Qcs_sys_GRID_kWh,Qcs_sys_DC_kWh,Qcs_sys_NONE_kWh,
E_sys_GRID_kWh,E_sys_NONE_kWh
```

**Column naming pattern:** `{service}_{carrier}_kWh`
- **service**: `Qhs_sys` (heating), `Qww_sys` (DHW), `Qcs_sys` (cooling), `E_sys` (electricity)
- **carrier**: `NATURALGAS`, `OIL`, `COAL`, `WOOD`, `GRID`, `SOLAR`, `DH` (district heating), `DC` (district cooling), `NONE`

**Example row:**
```
hour,date,Qhs_sys_NATURALGAS_kWh,Qhs_sys_GRID_kWh,...,E_sys_GRID_kWh
0,01/01/2020 01:00,15.3,0.0,...,8.5
1,01/01/2020 02:00,14.8,0.0,...,7.2
...
8759,31/12/2020 24:00,12.1,0.0,...,9.3
```

---

## 4. Configuration Parameters

From `cea/default.config` [final-energy] section:

```ini
[final-energy]
what-if-name =
what-if-name.type = NetworkLayoutNameParameter
what-if-name.nullable = true
what-if-name.help = Name of what-if analysis (sub)scenario.

overwrite-supply-settings = false
overwrite-supply-settings.type = BooleanParameter
overwrite-supply-settings.help = Controls supply system selection mode. When False (default), CEA uses supply systems from Building Properties/Supply and validates consistency with network connectivity (errors on mismatches). When True, CEA uses supply-type parameters and automatically selects building-scale or district-scale assemblies based on network connectivity, enabling what-if scenario analysis without modifying supply.csv.

network-name =
network-name.type = NetworkLayoutChoiceParameter
network-name.nullable = true
network-name.help = Select an existing network layout to calculate the delivered energy.

network-type = DH, DC
network-type.type = MultiChoiceParameter
network-type.choices = DH, DC
network-type.help = Type(s) of district network to calculate costs for

supply-type-cs =
supply-type-cs.type = DistrictSupplyTypeParameter
supply-type-cs.supply-category = SUPPLY_COOLING
supply-type-cs.help = Cooling supply system type(s). Select 2 assemblies: one building-scale (for standalone buildings) and one district-scale (for district-connected buildings).

supply-type-hs =
supply-type-hs.type = DistrictSupplyTypeParameter
supply-type-hs.supply-category = SUPPLY_HEATING
supply-type-hs.help = Heating supply system type(s)...

supply-type-dhw =
supply-type-dhw.type = DistrictSupplyTypeParameter
supply-type-dhw.supply-category = SUPPLY_HOTWATER
supply-type-dhw.help = Domestic hot water supply system type(s)...

hs-booster-type =
hs-booster-type.type = DistrictSupplyTypeParameter
hs-booster-type.supply-category = SUPPLY_HEATING
hs-booster-type.scale = BUILDING
hs-booster-type.help = Space heating booster system type (building-scale only)
hs-booster-type.nullable = true

dhw-booster-type =
dhw-booster-type.type = DistrictSupplyTypeParameter
dhw-booster-type.supply-category = SUPPLY_HOTWATER
dhw-booster-type.scale = BUILDING
dhw-booster-type.help = Domestic hot water booster system type (building-scale only)
dhw-booster-type.nullable = true
```

### Booster Parameter Behavior

**Key attribute:** `.scale = BUILDING`

This attribute filters the dropdown to **only show building-scale assemblies**:
- ✅ Shows: `SUPPLY_HOTWATER_AS1 (building)`, `SUPPLY_HOTWATER_AS3 (building)`, etc.
- ❌ Hides: `SUPPLY_HOTWATER_AS9 (district)`, `SUPPLY_HOTWATER_AS10 (district)`, etc.

**Why building-scale only?**
Booster systems are **local equipment** that supplement district supply when network temperature is insufficient. They are never district-scale.

**Technical implementation:**
The `DistrictSupplyTypeParameter` class respects the `.scale` attribute:
1. `_choices` property filters by scale (line 1497-1500 in config.py)
2. `decode()` method filters saved values to match scale (line 1715-1718)
3. `get()` method does NOT auto-add missing scale when scale_filter is set (line 1750)

---

## 5. Calculation Workflow

### Mode 1: overwrite-supply-settings = False (Production/Validation)

**Authority:** supply.csv + network connectivity validation

```python
def calculate_final_energy_production_mode(config, locator, building_name):
    # 1. Read supply.csv
    supply_df = pd.read_csv(locator.get_building_supply())
    supply_row = supply_df[supply_df['Name'] == building_name].iloc[0]

    # 2. Load network connectivity (if network-name specified)
    if config.final_energy.network_name:
        dc_nodes = load_network_nodes('DC', config.final_energy.network_name)
        dh_nodes = load_network_nodes('DH', config.final_energy.network_name)
    else:
        dc_nodes, dh_nodes = [], []

    # 3. Validate consistency
    for service in ['hs', 'cs', 'dhw']:
        scale = supply_row[f'scale_{service}']
        is_connected = (service == 'hs' and building_name in dh_nodes) or \
                      (service == 'cs' and building_name in dc_nodes)

        if scale == 'DISTRICT' and not is_connected:
            raise ValueError(f"Building {building_name} has district {service} in supply.csv but not connected to network")

        if scale == 'BUILDING' and is_connected:
            raise ValueError(f"Building {building_name} has building-scale {service} but is connected to network")

    # 4. Calculate final energy using supply.csv assemblies
    final_energy = calculate_from_assemblies(supply_row, demand_profile)

    return final_energy
```

### Mode 2: overwrite-supply-settings = True (What-If)

**Authority:** Network connectivity + supply-type-* parameters

```python
def calculate_final_energy_whatif_mode(config, locator, building_name):
    # 1. Load network connectivity (determines building vs district)
    if config.final_energy.network_name:
        dc_nodes = load_network_nodes('DC', config.final_energy.network_name)
        dh_nodes = load_network_nodes('DH', config.final_energy.network_name)
    else:
        dc_nodes, dh_nodes = [], []

    # 2. Select assemblies based on connectivity
    assemblies = {}

    # Heating
    if building_name in dh_nodes:
        assemblies['hs'] = get_district_assembly(config.final_energy.supply_type_hs)
    else:
        assemblies['hs'] = get_building_assembly(config.final_energy.supply_type_hs)

    # Cooling
    if building_name in dc_nodes:
        assemblies['cs'] = get_district_assembly(config.final_energy.supply_type_cs)
    else:
        assemblies['cs'] = get_building_assembly(config.final_energy.supply_type_cs)

    # DHW (never district-scale)
    assemblies['dhw'] = get_building_assembly(config.final_energy.supply_type_dhw)

    # 3. Calculate final energy using selected assemblies
    final_energy = calculate_from_assemblies_whatif(assemblies, demand_profile)

    return final_energy
```

---

## 6. Component-to-Carrier Mapping

### Strategy: Read from COMPONENTS database

Each component has a `feedstock` field that determines the energy carrier:

```python
# Load COMPONENTS database
boilers_db = pd.read_csv(locator.get_database_components_conversion_boilers())
component_row = boilers_db[boilers_db['code'] == 'BO1'].iloc[0]

# Map feedstock to carrier column
FEEDSTOCK_TO_CARRIER = {
    'NATURALGAS': 'NATURALGAS',
    'OIL': 'OIL',
    'COAL': 'COAL',
    'WOOD': 'WOOD',
    'GRID': 'GRID',
    'SOLAR': 'SOLAR',
    # District systems
    'NONE': 'NONE',  # No system
}

carrier = FEEDSTOCK_TO_CARRIER[component_row['feedstock']]  # e.g., 'NATURALGAS'
column_name = f"Qhs_sys_{carrier}_kWh"  # e.g., 'Qhs_sys_NATURALGAS_kWh'
```

### Handling District Systems

```python
if assembly_row['scale'] == 'DISTRICT':
    if service == 'hs' or service == 'dhw':
        carrier = 'DH'  # District heating
    elif service == 'cs':
        carrier = 'DC'  # District cooling

    # Read from network substation results
    network_file = locator.get_optimization_substations_total_file(network_name)
    df = pd.read_csv(network_file)
    final_energy[f"Q{service}_sys_DH_kWh"] = df[f'{building_name}_QH_kWh']
```

---

## 7. File Storage Structure

### Directory Layout

```
outputs/data/final-energy/
├── baseline/                    # Default: overwrite-supply-settings=false
│   ├── B1001.csv               # Building results
│   ├── B1002.csv
│   └── ...
├── whatif-hp-only/             # What-if scenario 1
│   ├── B1001.csv
│   ├── B1002.csv
│   └── ...
└── whatif-boiler-backup/       # What-if scenario 2
    ├── B1001.csv
    ├── B1002.csv
    └── ...
```

### Naming Convention

**Production mode** (`overwrite-supply-settings = false`):
- `what-if-name = ""` (blank) → `outputs/data/final-energy/baseline/{building}.csv`

**What-if mode** (`overwrite-supply-settings = true`):
- `what-if-name = "hp-only"` → `outputs/data/final-energy/whatif-hp-only/{building}.csv`
- `what-if-name = "boiler-backup"` → `outputs/data/final-energy/whatif-boiler-backup/{building}.csv`

### InputLocator Method

```python
def get_final_energy_building(self, building_name: str, what_if_name: str = None) -> str:
    """
    Get path to final energy results for a building.

    :param building_name: Building identifier
    :param what_if_name: What-if scenario name (None for baseline)
    :return: Path to CSV file
    """
    if what_if_name:
        subdir = f"whatif-{what_if_name}"
    else:
        subdir = "baseline"

    return os.path.join(
        self.get_final_energy_folder(),
        subdir,
        f"{building_name}.csv"
    )

def get_final_energy_folder(self) -> str:
    """Get final-energy output directory"""
    return os.path.join(self.scenario, 'outputs', 'data', 'final-energy')
```

---

## 8. Implementation Steps

### Phase 1: Core Calculation Engine

**File:** `cea/analysis/final_energy/calculation.py`

```python
def calculate_building_final_energy(
    locator,
    building_name: str,
    supply_assemblies: dict,  # {service: assembly_code}
    network_name: str = None,
    network_connected_buildings: dict = None,  # {service: [buildings]}
) -> pd.DataFrame:
    """
    Calculate hourly final energy for a building using optimization-new component models.

    :param locator: InputLocator
    :param building_name: Building identifier
    :param supply_assemblies: Dictionary mapping service to assembly code
        Example: {'hs': 'SUPPLY_HEATING_AS3', 'cs': 'SUPPLY_COOLING_AS1', 'dhw': 'SUPPLY_HOTWATER_AS1'}
    :param network_name: Network layout name (optional)
    :param network_connected_buildings: Dict of service -> list of connected buildings
    :return: DataFrame with 8760 rows and columns: hour, date, {service}_{carrier}_kWh
    """

    # 1. Load demand profile
    demand_df = pd.read_csv(locator.get_demand_results_file(building_name))

    # 2. Initialize output dataframe (8760 rows)
    final_energy_df = create_output_dataframe(demand_df)

    # 3. Process each service
    for service in ['hs', 'cs', 'dhw', 'el']:
        # Check if district-connected
        is_district = (
            network_connected_buildings and
            service in network_connected_buildings and
            building_name in network_connected_buildings[service]
        )

        if is_district:
            # District system: read from network results
            carrier = 'DH' if service in ['hs', 'dhw'] else 'DC'
            final_energy_df = add_district_energy(
                final_energy_df, service, carrier,
                building_name, network_name, locator
            )
        else:
            # Building-scale: calculate from components
            assembly_code = supply_assemblies[service]
            final_energy_df = calculate_service_final_energy(
                final_energy_df, service, assembly_code,
                demand_df, locator
            )

    return final_energy_df
```

### Phase 2: Production Mode (supply.csv validation)

**File:** `cea/analysis/final_energy/production_mode.py`

```python
def calculate_final_energy_production(config, locator):
    """
    Production mode: Use supply.csv with strict validation.
    Errors on inconsistencies between supply.csv and network connectivity.
    """
    # Load supply.csv
    supply_df = pd.read_csv(locator.get_building_supply())

    # Load network connectivity
    network_name = config.final_energy.network_name
    if network_name:
        dc_connected, dh_connected = load_network_connectivity(locator, network_name)
    else:
        dc_connected, dh_connected = [], []

    # Process each building
    for building in locator.get_zone_building_names():
        supply_row = supply_df[supply_df['Name'] == building].iloc[0]

        # Validate consistency
        validate_supply_vs_network(building, supply_row, dc_connected, dh_connected)

        # Extract assemblies from supply.csv
        assemblies = {
            'hs': supply_row['supply_type_hs'],
            'cs': supply_row['supply_type_cs'],
            'dhw': supply_row['supply_type_dhw'],
            'el': supply_row['supply_type_el'],
        }

        # Calculate
        result = calculate_building_final_energy(
            locator, building, assemblies,
            network_name, {'hs': dh_connected, 'cs': dc_connected}
        )

        # Save to baseline folder
        output_path = locator.get_final_energy_building(building, what_if_name=None)
        result.to_csv(output_path, index=False)
```

### Phase 3: What-If Mode

**File:** `cea/analysis/final_energy/whatif_mode.py`

```python
def calculate_final_energy_whatif(config, locator):
    """
    What-if mode: Use supply-type-* parameters with automatic scale selection.
    Network connectivity determines building vs district scale.
    """
    # Load network connectivity
    network_name = config.final_energy.network_name
    if network_name:
        dc_connected, dh_connected = load_network_connectivity(locator, network_name)
    else:
        dc_connected, dh_connected = [], []

    # Process each building
    for building in locator.get_zone_building_names():
        # Select assemblies based on connectivity
        assemblies = {}

        # Heating
        if building in dh_connected:
            assemblies['hs'] = get_district_assembly(config.final_energy.supply_type_hs)
        else:
            assemblies['hs'] = get_building_assembly(config.final_energy.supply_type_hs)

        # Cooling
        if building in dc_connected:
            assemblies['cs'] = get_district_assembly(config.final_energy.supply_type_cs)
        else:
            assemblies['cs'] = get_building_assembly(config.final_energy.supply_type_cs)

        # DHW (always building-scale)
        assemblies['dhw'] = get_building_assembly(config.final_energy.supply_type_dhw)

        # Electricity (always building-scale)
        assemblies['el'] = 'SUPPLY_ELECTRICITY_AS0'  # Grid supply

        # Calculate
        result = calculate_building_final_energy(
            locator, building, assemblies,
            network_name, {'hs': dh_connected, 'cs': dc_connected}
        )

        # Save to what-if folder
        what_if_name = config.final_energy.what_if_name
        output_path = locator.get_final_energy_building(building, what_if_name)
        result.to_csv(output_path, index=False)
```

### Phase 4: Main Entry Point

**File:** `cea/analysis/final_energy/main.py`

```python
def main(config):
    """
    Final energy calculation entry point.
    Routes to production or what-if mode based on overwrite-supply-settings.
    """
    locator = cea.inputlocator.InputLocator(config.scenario)

    # Validate database has required component columns
    # validate_supply_database_for_final_energy(locator)

    if config.final_energy.overwrite_supply_settings:
        # What-if mode
        print("Running final energy calculation in what-if mode...")
        print(f"  What-if scenario: {config.final_energy.what_if_name or '(default)'}")
        calculate_final_energy_whatif(config, locator)
    else:
        # Production mode
        print("Running final energy calculation in production mode...")
        print("  Using supply.csv with network validation")
        calculate_final_energy_production(config, locator)

    print("Final energy calculation complete!")
```

---

## 9. Testing Strategy

### Unit Tests

**Test building-scale calculations:**
```python
def test_boiler_efficiency():
    # Given: 100 kWh heating demand, BO1 (gas boiler, η=0.85)
    demand = 100.0
    component_code = 'BO1'

    # When: Calculate final energy
    result = calculate_service_final_energy('hs', component_code, demand)

    # Then: NG consumption = 100 / 0.85 = 117.65 kWh
    assert result['Qhs_sys_NATURALGAS_kWh'] == pytest.approx(117.65, rel=0.01)
    assert result['Qhs_sys_GRID_kWh'] == 0.0
```

**Test heat pump:**
```python
def test_heat_pump_cop():
    # Given: 100 kWh heating demand, HP3 (COP=3.0)
    demand = 100.0
    component_code = 'HP3'

    # When: Calculate final energy
    result = calculate_service_final_energy('hs', component_code, demand)

    # Then: Electricity consumption = 100 / 3.0 = 33.33 kWh
    assert result['Qhs_sys_GRID_kWh'] == pytest.approx(33.33, rel=0.01)
    assert result['Qhs_sys_NATURALGAS_kWh'] == 0.0
```

### Integration Tests

**Test production mode validation:**
```python
def test_production_mode_validates_mismatch():
    # Given: Building has district heating in supply.csv but not in network
    # When: Run production mode
    # Then: Should raise ValueError
    with pytest.raises(ValueError, match="has district hs in supply.csv but not connected"):
        calculate_final_energy_production(config, locator)
```

**Test what-if mode auto-selection:**
```python
def test_whatif_mode_selects_district_for_connected():
    # Given: Building connected to DC network
    # When: Run what-if mode
    # Then: Should use district-scale assembly from supply-type-cs
    result = calculate_final_energy_whatif(config, locator)
    assert 'Qcs_sys_DC_kWh' in result.columns
    assert result['Qcs_sys_DC_kWh'].sum() > 0
```

---

## 10. Implementation Decisions (Finalized)

### ✅ Decision 1: Constant Efficiency (NOT Part-Load Curves)
**Decision:** Use constant efficiency from COMPONENTS database
**Rationale:** Matches CEA database design, simpler implementation
**Workflow:**
```python
# Step 1: Load assembly → get primary component code
assembly_row['primary_components']  # e.g., 'BO1'

# Step 2: Load component → get efficiency and feedstock
component_row['min_thermal_eff']  # e.g., 0.85
component_row['feedstock']  # e.g., 'NATURALGAS'

# Step 3: Calculate hourly (simple division)
for hour in range(8760):
    fuel_kWh[hour] = demand_kWh[hour] / efficiency
```

### ✅ Decision 2: District Systems - Require Thermal-Network Results
**Decision:** Always require thermal-network simulation as prerequisite
**Rationale:** District systems need accurate network flow data
**Implementation:**
```python
if building in network_connected_buildings['DH']:
    # Must have thermal-network results
    network_file = locator.get_thermal_network_substation_file(network_name, building)
    if not os.path.exists(network_file):
        raise ValueError(
            f"Building {building} connected to district network '{network_name}' "
            f"but thermal-network results not found. "
            f"Please run: cea thermal-network --network-name {network_name}"
        )
    # Read actual district consumption
    df = pd.read_csv(network_file)
    DH_hs_kWh = df['Qhs_dh_W'] / 1000  # Convert W to kWh
```

### ✅ Decision 3: Booster Systems - Separate from Base DHW
**Decision:** Booster systems calculated separately with dedicated parameters
**Parameters:**
- `hs-booster-type` (space heating booster, building-scale only)
- `dhw-booster-type` (hot water booster, building-scale only)

**Data Source:** `thermal-network/{network}/booster/DH/substation/DH_booster_substation_{building}.csv`

**Calculation:**
```python
# Read booster substation file
booster_df = pd.read_csv(locator.get_thermal_network_booster_substation(network, building))

# District heating energy (base)
DH_hs_kWh = (booster_df['Qhs_dh_W'] + booster_df['Qww_dh_W']) / 1000

# Booster energy (supplement)
booster_demand_kWh = (booster_df['Qhs_booster_W'] + booster_df['Qww_booster_W']) / 1000

# Apply booster component efficiency
booster_component = load_component(config.final_energy.dhw_booster_type)
booster_fuel_kWh = booster_demand_kWh / booster_component['min_thermal_eff']

# Output to appropriate carrier column
final_energy['Qhs_sys_DH_kWh'] = DH_hs_kWh  # District
final_energy[f'Qww_sys_{booster_feedstock}_kWh'] = booster_fuel_kWh  # Booster fuel
```

### ✅ Decision 4: Solar Thermal - Skip for Phase 1
**Decision:** Not implemented in Phase 1
**Rationale:** Complex calculation, low priority
**Future:** Can add in Phase 2 by reading from solar-collector script results

### ✅ Decision 5: Multiple Components - Use Primary Only
**Decision:** Only use `primary_components` from ASSEMBLIES
**Rationale:** Simplifies Phase 1, covers 95% of use cases
**Ignored:**
- `secondary_components` (e.g., backup boilers, pumps)
- `tertiary_components` (e.g., cooling towers, heat rejection)

**Future:** Phase 2 can add secondary/tertiary handling for complex systems (CHP, etc.)

---

## 11. Summary

### Advantages of This Approach
✅ **Reuses optimization-new equations** - Same component database and efficiency models
✅ **Constant efficiency** - Matches CEA database design, simple and fast
✅ **Supports what-if scenarios** - Test different supply assemblies without modifying supply.csv
✅ **Matches emissions output format** - Easy integration with LCA module
✅ **Hourly resolution** - Enables time-dependent analysis
✅ **Network connectivity aware** - Respects physical constraints
✅ **Booster systems supported** - Handles district + booster correctly

### Design Decisions (Finalized 2026-02-02)
1. ✅ **Constant efficiency** - Use COMPONENTS database `min_thermal_eff`, no part-load curves
2. ✅ **District systems** - Require thermal-network simulation results as prerequisite
3. ✅ **Booster systems** - Separate hs-booster-type and dhw-booster-type parameters (building-scale only)
4. ✅ **Solar thermal** - Skip for Phase 1
5. ✅ **Multiple components** - Use only primary_components for Phase 1

### Implementation Phases

**Phase 1: Core Calculation Engine** (Priority: HIGH)
- [ ] Create `cea/analysis/final_energy/calculation.py`
- [ ] Implement `calculate_building_final_energy()` function
- [ ] Support constant efficiency calculation (hourly loop)
- [ ] Handle building-scale assemblies → components → feedstock mapping
- [ ] Handle district-scale systems (read from thermal-network)
- [ ] Handle booster systems (read from booster substation files)
- [ ] Generate output CSV with 8760 rows + carrier columns

**Phase 2: Production Mode** (Priority: HIGH)
- [ ] Create `cea/analysis/final_energy/production_mode.py`
- [ ] Implement strict validation (supply.csv vs network connectivity)
- [ ] Raise clear errors on mismatches
- [ ] Save to `baseline/` folder

**Phase 3: What-If Mode** (Priority: HIGH)
- [ ] Create `cea/analysis/final_energy/whatif_mode.py`
- [ ] Implement supply-type-* parameter usage
- [ ] Auto-select building/district scale based on connectivity
- [ ] Save to `whatif-{name}/` folder

**Phase 4: Testing & Documentation** (Priority: MEDIUM)
- [ ] Unit tests for efficiency calculations
- [ ] Integration tests for production/what-if modes
- [ ] Test booster system calculations
- [ ] User guide for what-if scenarios

**Phase 5: Future Enhancements** (Priority: LOW)
- [ ] Part-load efficiency curves (if needed)
- [ ] Solar thermal calculation
- [ ] Secondary/tertiary component handling
- [ ] CHP and complex system support

### Next Steps
1. ✅ **Plan finalized** - All design decisions made
2. **Start Phase 1** - Core calculation engine
3. **Test with real scenarios** - Use booster data from `/Users/zshi/Library/CloudStorage/Dropbox/CEA2/batch_gh/_ZRH_ copy/`
4. **Iterate based on results** - Refine as needed

---

**END OF IMPLEMENTATION PLAN**
