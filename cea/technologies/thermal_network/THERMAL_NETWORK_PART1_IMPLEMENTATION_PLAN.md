# Thermal Network Part 1: Supply.csv Per-Building Service Integration

**Date**: 2025-12-19
**Objective**: Enable per-building service configuration from supply.csv while maintaining backward compatibility
**Status**: Ready for implementation

---

## Executive Summary

### Current Behavior
- `overwrite-supply-settings=false`: Reads building list from supply.csv, but ALL buildings use ALL services from `itemised-dh-services`
- `overwrite-supply-settings=true`: Uses `connected-buildings` parameter, ALL buildings use ALL services

### Desired Behavior
- `overwrite-supply-settings=false`: Reads building list AND per-building service configuration from supply.csv
  - Building A: space_heating only (Qww_dh_W = 0, booster handles DHW)
  - Building B: domestic_hot_water only (Qhs_dh_W = 0, local handles space heating)
  - Building C: both services (Qhs_dh_W > 0, Qww_dh_W > 0)
  - Plant suffix: union of all services (e.g., `_hs_ww` if any building needs either)

### Key Decisions (from user)
1. **Plant suffix order**: Service priority `_hs_ww` (space heating before domestic hot water)
2. **Network architecture**: Single network serves all buildings (buildings use only their configured services)

---

## Architecture Overview

### Two-Phase System (CRITICAL - do not modify)

**Phase 1: Network Layout** (`cea/technologies/network_layout/main.py`)
- Determines which buildings connect
- Generates network topology (nodes + edges)
- Creates PLANT nodes with service encoding (PLANT_hs_ww, PLANT_ww_hs, etc.)
- **Our changes happen here**

**Phase 2: Thermal Simulation** (`cea/technologies/thermal_network/thermal_network.py` + `simplified_thermal_network.py`)
- Reads pre-existing layout from Phase 1
- Simulates heat flow, temperatures, losses
- Calculates substation loads
- **Needs per-building service info from Phase 1**

---

## Implementation Plan

### PART A: Network Layout (Phase 1)

#### File: `cea/technologies/network_layout/main.py`

#### Task 1: Enhance supply.csv reading function

**Current function** (lines 149-174):
```python
def get_buildings_from_supply_csv(locator, network_type):
    # Returns: list of buildings with DISTRICT scale
    return district_buildings
```

**New function** (rename and enhance):
```python
def get_buildings_and_services_from_supply_csv(locator, network_type):
    """
    Read supply.csv and determine per-building service configuration.

    For DH networks, checks both supply_type_hs and supply_type_dhw:
    - If supply_type_hs maps to DISTRICT → building uses space_heating service
    - If supply_type_dhw maps to DISTRICT → building uses domestic_hot_water service
    - Building connects if either service is DISTRICT

    Args:
        locator: InputLocator instance
        network_type: 'DH' or 'DC'

    Returns:
        buildings_list: List of building names with at least one DISTRICT service
        per_building_services: Dict mapping building → set of services
                              Example: {'B001': {'space_heating', 'domestic_hot_water'},
                                       'B002': {'space_heating'},
                                       'B003': {'domestic_hot_water'}}
    """
    supply_df = pd.read_csv(locator.get_building_supply())

    # Read assemblies database for code-to-scale mapping
    if network_type == "DH":
        assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_heating())
    else:  # DC
        assemblies_df = pd.read_csv(locator.get_database_assemblies_supply_cooling())

    # Create mapping: code → scale (DISTRICT or BUILDING)
    scale_mapping = assemblies_df.set_index('code')['scale'].to_dict()

    per_building_services = {}

    for _, row in supply_df.iterrows():
        building_name = row['name']
        building_services = set()

        # Check space heating service (DH only)
        if network_type == "DH" and 'supply_type_hs' in row:
            hs_code = row['supply_type_hs']
            hs_scale = scale_mapping.get(hs_code, None)

            if hs_scale == 'DISTRICT':
                building_services.add('space_heating')

        # Check domestic hot water service (DH only)
        if network_type == "DH" and 'supply_type_dhw' in row:
            dhw_code = row['supply_type_dhw']
            dhw_scale = scale_mapping.get(dhw_code, None)

            if dhw_scale == 'DISTRICT':
                building_services.add('domestic_hot_water')

        # Check cooling service (DC only)
        if network_type == "DC" and 'supply_type_cs' in row:
            cs_code = row['supply_type_cs']
            cs_scale = scale_mapping.get(cs_code, None)

            if cs_scale == 'DISTRICT':
                building_services.add('space_cooling')  # DC service

        # Store building if it uses at least one DISTRICT service
        if building_services:
            per_building_services[building_name] = building_services

    buildings_list = list(per_building_services.keys())

    return buildings_list, per_building_services
```

#### Task 2: Add helper function for network service determination

**New function** (add after get_buildings_and_services_from_supply_csv):
```python
def get_network_services_from_buildings(per_building_services):
    """
    Determine which services the network must provide (union of all building needs).

    Args:
        per_building_services: Dict {building_name: set of services}

    Returns:
        network_services: Set of services needed by at least one building
                         Example: {'space_heating', 'domestic_hot_water'}
    """
    network_services = set()
    for building_services in per_building_services.values():
        network_services.update(building_services)

    return network_services
```

#### Task 3: Add service priority ordering function

**New function** (add after get_network_services_from_buildings):
```python
def apply_service_priority_order(services):
    """
    Apply service priority ordering for plant suffix generation.

    Service Priority (NOT alphabetical):
    1. space_heating (hs) - typically larger load, comes FIRST
    2. domestic_hot_water (ww) - comes SECOND

    This ensures plant suffix is _hs_ww (not _ww_hs) when both services present.

    Args:
        services: Set or list of service names

    Returns:
        List of services in priority order

    Examples:
        {'domestic_hot_water', 'space_heating'} → ['space_heating', 'domestic_hot_water']
        {'domestic_hot_water'} → ['domestic_hot_water']
        {'space_heating'} → ['space_heating']
    """
    # Define priority order (lower index = higher priority)
    priority_order = ['space_heating', 'domestic_hot_water', 'space_cooling']

    # Filter and sort services by priority
    ordered_services = [svc for svc in priority_order if svc in services]

    # Add any unrecognized services at the end (future-proofing)
    for svc in services:
        if svc not in ordered_services:
            ordered_services.append(svc)

    return ordered_services
```

#### Task 4: Update auto_layout_network() function

**Location**: Lines ~700-750 in `auto_layout_network()`

**Current code**:
```python
# Determine buildings to connect
if config.network_layout.overwrite_supply_settings:
    if config.network_layout.connected_buildings:
        buildings = config.network_layout.connected_buildings
    else:
        buildings = zone_df['name'].tolist()
else:
    buildings = get_buildings_from_supply_csv(locator, network_type)

# Apply demand filter
if config.network_layout.consider_only_buildings_with_demand:
    buildings_with_demand = get_buildings_with_demand(locator, network_type)
    buildings = [b for b in buildings if b in buildings_with_demand]
```

**New code**:
```python
# ═══════════════════════════════════════════════════════════════
# STEP 1: Determine buildings and their service requirements
# ═══════════════════════════════════════════════════════════════

if config.network_layout.overwrite_supply_settings:
    # MODE 1: What-if scenario (use connected-buildings parameter)
    print("  ℹ Building selection mode: overwrite-supply-settings=true")

    if config.network_layout.connected_buildings:
        buildings = config.network_layout.connected_buildings
        print(f"    - Using connected-buildings parameter: {len(buildings)} buildings")
    else:
        buildings = zone_df['name'].tolist()
        print(f"    - Using all zone buildings: {len(buildings)} buildings")

    # All buildings use all services (from itemised-dh-services)
    itemised_services = config.network_layout.itemised_dh_services
    if not itemised_services:
        if network_type == 'DH':
            itemised_services = ['space_heating', 'domestic_hot_water']
        else:  # DC
            itemised_services = ['space_cooling']

    # Apply service priority order
    itemised_services_ordered = apply_service_priority_order(itemised_services)

    # All buildings get all services (legacy behavior)
    per_building_services = {b: set(itemised_services_ordered) for b in buildings}
    network_services = set(itemised_services_ordered)

else:
    # MODE 2: Supply.csv mode (read per-building service configuration)
    print("  ℹ Building selection mode: overwrite-supply-settings=false")
    print("    - Reading building list and services from supply.csv")

    # NEW: Get per-building services from supply.csv
    buildings, per_building_services = get_buildings_and_services_from_supply_csv(locator, network_type)

    # Determine network services (union of all building needs)
    network_services = get_network_services_from_buildings(per_building_services)

    print(f"    - Buildings with DISTRICT supply: {len(buildings)}")
    print(f"    - Network services (union): {', '.join(sorted(network_services))}")

    # Log per-building service breakdown
    hs_only = sum(1 for svcs in per_building_services.values()
                  if svcs == {'space_heating'})
    ww_only = sum(1 for svcs in per_building_services.values()
                  if svcs == {'domestic_hot_water'})
    both = sum(1 for svcs in per_building_services.values()
               if {'space_heating', 'domestic_hot_water'}.issubset(svcs))

    if network_type == 'DH':
        print(f"    - Service breakdown: {hs_only} HS-only, {ww_only} DHW-only, {both} both")

# ═══════════════════════════════════════════════════════════════
# STEP 2: Apply demand filter (both modes)
# ═══════════════════════════════════════════════════════════════

if config.network_layout.consider_only_buildings_with_demand:
    print("  ℹ Demand filter: consider-only-buildings-with-demand=true")

    buildings_with_demand = get_buildings_with_demand(locator, network_type)
    buildings_before = len(buildings)
    buildings = [b for b in buildings if b in buildings_with_demand]

    # Update per_building_services to only include filtered buildings
    per_building_services = {b: per_building_services[b] for b in buildings}

    excluded = buildings_before - len(buildings)
    if excluded > 0:
        print(f"    - Excluded {excluded} buildings with zero demand")

print(f"\n  ✓ Final building count: {len(buildings)}")

# ═══════════════════════════════════════════════════════════════
# STEP 3: Generate plant suffix based on network services
# ═══════════════════════════════════════════════════════════════

# Apply service priority order for plant naming
network_services_ordered = apply_service_priority_order(network_services)

# Generate plant type (e.g., PLANT_hs_ww)
# Existing function: get_plant_type_from_services() respects input order
plant_type = get_plant_type_from_services(network_services_ordered, network_type)

print(f"  ✓ Plant type: {plant_type}")
print(f"    - Service priority: {' → '.join(network_services_ordered)}")
```

#### Task 5: Store per-building services in network output

**Location**: After network generation, before saving shapefiles (~line 950)

**Add metadata storage**:
```python
# Store per-building service configuration in metadata file
# This allows Phase 2 (thermal simulation) to know which services each building uses

import json

per_building_services_serializable = {
    building: list(services)  # Convert set to list for JSON
    for building, services in per_building_services.items()
}

metadata_path = os.path.join(
    locator.get_thermal_network_folder(network_type, network_name),
    'building_services.json'
)

with open(metadata_path, 'w') as f:
    json.dump({
        'network_type': network_type,
        'network_name': network_name,
        'plant_type': plant_type,
        'network_services': list(network_services_ordered),
        'per_building_services': per_building_services_serializable,
        'overwrite_supply_settings': config.network_layout.overwrite_supply_settings,
        'timestamp': pd.Timestamp.now().isoformat()
    }, f, indent=2)

print(f"  ✓ Saved per-building service configuration to building_services.json")
```

---

### PART B: Thermal Simulation (Phase 2)

#### File: `cea/technologies/thermal_network/thermal_network.py`

#### Task 6: Read per-building services from layout metadata

**Location**: In `main()` after reading network layout, before calling thermal_network_simplified (~line 200)

**Add**:
```python
# Read per-building service configuration from Phase 1 (network layout)
metadata_path = os.path.join(
    locator.get_thermal_network_folder(network_type, network_name),
    'building_services.json'
)

if os.path.exists(metadata_path):
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    per_building_services = {
        building: set(services)  # Convert list back to set
        for building, services in metadata['per_building_services'].items()
    }

    print(f"  ℹ Loaded per-building service configuration from layout metadata")
    print(f"    - Network services: {', '.join(metadata['network_services'])}")
else:
    # Legacy mode: no metadata file, all buildings use all services
    print(f"  ⚠ Warning: building_services.json not found (legacy layout)")
    print(f"    - Assuming all buildings use all services")

    # Extract services from PLANT node type
    plant_nodes = node_df[node_df['Type'].str.startswith('PLANT', na=False)]
    if not plant_nodes.empty:
        plant_type = plant_nodes.iloc[0]['Type']
        itemised_dh_services, _ = get_services_from_plant_type(plant_type)
    else:
        itemised_dh_services = ['space_heating', 'domestic_hot_water']  # Default

    # All buildings use all services (legacy)
    consumer_nodes = node_df[node_df['Type'] == 'CONSUMER']
    connected_buildings = consumer_nodes['building'].tolist()
    per_building_services = {b: set(itemised_dh_services) for b in connected_buildings}
```

#### File: `cea/technologies/thermal_network/simplified_thermal_network.py`

#### Task 7: Update thermal_network_simplified to accept per_building_services

**Current signature** (~line 469):
```python
def thermal_network_simplified(locator: cea.inputlocator.InputLocator,
                              config: cea.config.Configuration,
                              network_type, network_name):
```

**New signature**:
```python
def thermal_network_simplified(locator: cea.inputlocator.InputLocator,
                              config: cea.config.Configuration,
                              network_type, network_name,
                              per_building_services=None):
    """
    ...
    :param per_building_services: Dict mapping building → set of services
                                  Example: {'B001': {'space_heating', 'domestic_hot_water'},
                                           'B002': {'space_heating'}}
                                  If None, all buildings use all services (legacy behavior)
    """
```

**Pass to substation calls** (~line 540 for DH):
```python
# Existing code
substation.substation_main_heating_thermal_network(locator, total_demand, building_names,
                                                   itemised_dh_services=itemised_dh_services,
                                                   fixed_network_temp_C=fixed_network_temp_C,
                                                   network_type=network_type,
                                                   network_name=network_name)

# NEW: Add per_building_services parameter
substation.substation_main_heating_thermal_network(locator, total_demand, building_names,
                                                   itemised_dh_services=itemised_dh_services,
                                                   per_building_services=per_building_services,  # NEW
                                                   fixed_network_temp_C=fixed_network_temp_C,
                                                   network_type=network_type,
                                                   network_name=network_name)
```

#### File: `cea/technologies/substation.py`

#### Task 8: Update substation functions to filter services per building

**Function 1**: `substation_main_heating_thermal_network()` (line ~201)

**Add parameter**:
```python
def substation_main_heating_thermal_network(locator, total_demand, buildings_name_with_heating,
                                           itemised_dh_services=['space_heating', 'domestic_hot_water'],
                                           per_building_services=None,  # NEW parameter
                                           fixed_network_temp_C=None,
                                           network_type='DH', network_name=''):
```

**Pass to model function**:
```python
for building_name in buildings_name_with_heating:
    building_demand_df = pd.read_csv(locator.get_demand_results_file(building_name))

    # Determine which services THIS specific building uses
    if per_building_services is not None:
        building_services = per_building_services.get(building_name, set(itemised_dh_services))
    else:
        # Legacy: all buildings use all services
        building_services = set(itemised_dh_services)

    # Calculate temperatures...
    # (existing code)

    # Call model with building-specific services
    substation_model_heating_thermal_network(building_name, building_demand_df,
                                            ...,
                                            building_services=building_services,  # NEW
                                            ...)
```

**Function 2**: `substation_model_heating_thermal_network()` (line ~242)

**Add parameter and service filtering**:
```python
def substation_model_heating_thermal_network(name, building, T_DH_supply_C, T_DH_supply_data_C,
                                            Ths_supply_C, Ths_return_C,
                                            Tww_supply_C, Tww_return_C,
                                            hs_configuration, locator,
                                            building_services=None,  # NEW parameter
                                            network_type='DH', network_name=''):
    """
    ...
    :param building_services: Set of services this building uses
                             e.g., {'space_heating'} or {'domestic_hot_water'} or both
                             If None, building uses all services
    """

    # Determine which services to calculate
    if building_services is None:
        building_services = {'space_heating', 'domestic_hot_water'}  # Legacy default

    calculate_space_heating = 'space_heating' in building_services
    calculate_dhw = 'domestic_hot_water' in building_services

    # Extract demands
    Qhs_sys_W = building['Qhs_sys_kWh'].values * 1000
    Qww_sys_W = building['Qww_sys_kWh'].values * 1000

    # Initialize output arrays
    # ... (existing code)

    # ═══════════════════════════════════════════════════════════════
    # SPACE HEATING CALCULATION
    # ═══════════════════════════════════════════════════════════════

    if calculate_space_heating:
        # Existing space heating HEX calculations
        t_DH_return_hs_C, mcp_DH_hs, A_hex_hs = calc_substation_heating(...)
        # ... (existing code)
    else:
        # Building does NOT use DH for space heating
        # Set all space heating DH values to zero
        t_DH_return_hs_C = np.zeros(len(building))
        mcp_DH_hs = np.zeros(len(building))
        A_hex_hs = 0.0
        Qhs_dh_W = np.zeros(len(building))
        Qhs_booster_W = Qhs_sys_W  # All space heating from local booster/system

        print(f"    - {name}: Space heating NOT from DH (supply.csv config)")

    # ═══════════════════════════════════════════════════════════════
    # DOMESTIC HOT WATER CALCULATION
    # ═══════════════════════════════════════════════════════════════

    if calculate_dhw:
        # Existing DHW HEX calculations
        t_DH_return_ww_C, mcp_DH_ww, A_hex_ww = calc_substation_heating(...)
        # ... (existing code)
    else:
        # Building does NOT use DH for DHW
        # Set all DHW DH values to zero
        t_DH_return_ww_C = np.zeros(len(building))
        mcp_DH_ww = np.zeros(len(building))
        A_hex_ww = 0.0
        Qww_dh_W = np.zeros(len(building))
        Qww_booster_W = Qww_sys_W  # All DHW from local booster/system

        print(f"    - {name}: DHW NOT from DH (supply.csv config)")

    # ═══════════════════════════════════════════════════════════════
    # MIXING AND OUTPUT (existing code continues)
    # ═══════════════════════════════════════════════════════════════

    # Mix return temperatures (existing logic works with zeros)
    # ... (existing code)

    # Create output DataFrame (existing code)
    # ... (existing code)
```

---

## Testing Plan

### Test Case 1: overwrite-supply-settings=true (existing behavior)
**Expected**: No change from current behavior
- Uses `connected-buildings` or all zone buildings
- All buildings use all services from `itemised-dh-services`
- Plant suffix from `itemised-dh-services`

### Test Case 2: overwrite-supply-settings=false, all buildings use both services
**Supply.csv**:
```
name,supply_type_hs,supply_type_dhw
B001,DHN,DHN
B002,DHN,DHN
B003,DHN,DHN
```

**Expected**:
- All 3 buildings connect
- `per_building_services = {'B001': {'space_heating', 'domestic_hot_water'}, ...}`
- Plant suffix: `_hs_ww`
- All substation files show both Qhs_dh_W > 0 and Qww_dh_W > 0

### Test Case 3: overwrite-supply-settings=false, mixed services
**Supply.csv**:
```
name,supply_type_hs,supply_type_dhw
B001,DHN,BUILDING
B002,BUILDING,DHN
B003,DHN,DHN
```

**Expected**:
- All 3 buildings connect (each has at least one DISTRICT service)
- `per_building_services`:
  - `B001: {'space_heating'}` (HS from DH, DHW local)
  - `B002: {'domestic_hot_water'}` (DHW from DH, HS local)
  - `B003: {'space_heating', 'domestic_hot_water'}` (both from DH)
- Plant suffix: `_hs_ww` (union includes both)
- Substation outputs:
  - B001: `Qhs_dh_W > 0, Qww_dh_W = 0, Qww_booster_W = Qww_sys_W`
  - B002: `Qhs_dh_W = 0, Qww_dh_W > 0, Qhs_booster_W = Qhs_sys_W`
  - B003: `Qhs_dh_W > 0, Qww_dh_W > 0`

### Test Case 4: overwrite-supply-settings=false, only HS
**Supply.csv**:
```
name,supply_type_hs,supply_type_dhw
B001,DHN,BUILDING
B002,DHN,BUILDING
```

**Expected**:
- Both buildings connect
- `per_building_services = {'B001': {'space_heating'}, 'B002': {'space_heating'}}`
- Plant suffix: `_hs` (only space heating needed)
- All `Qww_dh_W = 0, Qww_booster_W = Qww_sys_W`

### Test Case 5: consider-only-buildings-with-demand=true with mixed services
**Supply.csv** + **Demand**:
```
name,supply_type_hs,supply_type_dhw,QH_sys_MWhyr
B001,DHN,DHN,100
B002,DHN,BUILDING,0  # Zero demand - should be excluded
B003,BUILDING,DHN,50
```

**Expected**:
- Only B001 and B003 connect (B002 excluded due to zero demand)
- `per_building_services = {'B001': {'space_heating', 'domestic_hot_water'}, 'B003': {'domestic_hot_water'}}`
- Plant suffix: `_hs_ww` (union of B001 and B003 needs)

---

## Files Modified Summary

### Phase 1 (Network Layout)
1. **`cea/technologies/network_layout/main.py`**
   - Rename `get_buildings_from_supply_csv()` → `get_buildings_and_services_from_supply_csv()`
   - Add `get_network_services_from_buildings()`
   - Add `apply_service_priority_order()`
   - Update `auto_layout_network()` logic (~50 lines)
   - Add metadata JSON writing

### Phase 2 (Thermal Simulation)
2. **`cea/technologies/thermal_network/thermal_network.py`**
   - Add metadata JSON reading (~30 lines)
   - Pass `per_building_services` to `thermal_network_simplified()`

3. **`cea/technologies/thermal_network/simplified_thermal_network.py`**
   - Add `per_building_services` parameter to signature
   - Pass to substation functions

4. **`cea/technologies/substation.py`**
   - Add `per_building_services` parameter to `substation_main_heating_thermal_network()`
   - Add `building_services` parameter to `substation_model_heating_thermal_network()`
   - Add service filtering logic (~40 lines)

---

## Backward Compatibility

### Existing layouts without building_services.json
- Thermal simulation checks if metadata file exists
- Falls back to legacy mode: all buildings use all services
- Warning printed to console
- No breaking changes

### Existing configs with overwrite-supply-settings=true
- No change in behavior
- All buildings continue to use all services
- Plant suffix from `itemised-dh-services`

---

## Future Enhancements (Not in Part 1)

1. **Separate networks per service** (Part 2)
   - Generate independent DH_hs and DH_ww networks
   - Different plant locations possible
   - More flexible but more complex

2. **GUI/Dashboard integration**
   - Visualize per-building service configuration
   - Edit building_services.json via UI

3. **Validation warnings**
   - Warn if building has DHW demand but no DHW supply configured
   - Suggest enabling DH service for high-demand buildings

4. **Per-building booster configuration**
   - Store booster specs in building_services.json
   - Allow different booster types per building

---

## Implementation Checklist

- [ ] Task 1: Enhance `get_buildings_from_supply_csv()` → `get_buildings_and_services_from_supply_csv()`
- [ ] Task 2: Add `get_network_services_from_buildings()`
- [ ] Task 3: Add `apply_service_priority_order()`
- [ ] Task 4: Update `auto_layout_network()` with new logic
- [ ] Task 5: Add building_services.json metadata writing
- [ ] Task 6: Add metadata reading in thermal_network.py
- [ ] Task 7: Update `thermal_network_simplified()` signature
- [ ] Task 8: Update substation functions with service filtering
- [ ] Test Case 1: Existing behavior unchanged
- [ ] Test Case 2: All buildings both services
- [ ] Test Case 3: Mixed service configuration
- [ ] Test Case 4: Single service (HS only)
- [ ] Test Case 5: Demand filtering with mixed services

---

**Ready for implementation!**
