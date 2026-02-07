# Heat Rejection (Anthropogenic Heat)

## Main API

**`anthropogenic_heat_main(locator, config) → None`** - Calculate heat rejection from building and district energy systems

**`calculate_standalone_heat_rejection(locator, config, network_types) → dict`** - Calculate building-scale heat rejection for all buildings

**`calculate_network_heat_rejection(locator, config, network_type, network_name, standalone_results) → dict`** - Calculate district network plant heat rejection

**`merge_heat_rejection_results(locator, standalone_results, network_results, is_standalone_only) → dict`** - Merge building and network results using 4-case logic

## Architecture Overview

Heat rejection module mirrors the cost feature's architecture:
- **4-case building connectivity logic** for determining which services are standalone vs district
- **3-level fallback system** for supply system selection
- **Reuses cost module functions** for consistency (supply system creation, DHW fallback)
- **Extracts heat_rejection** from SupplySystem objects instead of costs

## 4-Case Building Connectivity Logic

Mirrors `cea/analysis/costs/AGENTS.md` with same connectivity rules:

### Case 1: Standalone-only OR building not in any network
**Triggers when**:
- `network_name = "(none)"` OR
- Building not found in any network nodes.shp

**Service provision**: All services standalone (cooling, heating, DHW)

**Heat rejection**: Include ALL heat rejection from building-scale systems

**Example**:
```python
# Case 1: All buildings standalone
if is_standalone_only or building_id not in (dc_connected | dh_connected):
    filtered_heat = all_heat_rejection  # Include everything
```

---

### Case 2: Building in BOTH DC+DH networks
**Triggers when**: Building found in both DC/nodes.shp AND DH/nodes.shp

**Service provision**:
- Cooling: District-scale (from DC network)
- Heating: District-scale (from DH network)
- DHW: District-scale (from DH network)

**Heat rejection**: ZERO standalone heat (all services from district)

**Example**:
```python
# Case 2: Both networks - skip building entirely
if is_in_dc and is_in_dh:
    continue  # No standalone services = no building-scale heat
```

**Use case**: Dense urban areas with full district energy coverage

---

### Case 3: Building in DC network only
**Triggers when**: Building in DC/nodes.shp, NOT in DH/nodes.shp

**Service provision**:
- Cooling: District-scale (from DC network)
- Heating: Building-scale (standalone)
- DHW: Building-scale (standalone)

**Heat rejection**: Include only heating/DHW heat (high-temperature services)

**Example**:
```python
# Case 3: DC only - keep only high-temp heat (heating/DHW standalone)
if is_in_dc and not is_in_dh:
    filtered_heat = filter_by_service_temperature(
        heat_data, temp_prefixes=['T100', 'T90', 'T80', 'T60']
    )
```

**Use case**: Cooling-dominant climates, phased district network deployment

---

### Case 4: Building in DH network only
**Triggers when**: Building in DH/nodes.shp, NOT in DC/nodes.shp

**Service provision**:
- Cooling: Building-scale (standalone)
- Heating: District-scale (from DH network)
- DHW: District-scale (from DH network)

**Heat rejection**: Include only cooling heat (low-temperature service)

**Example**:
```python
# Case 4: DH only - keep only low-temp heat (cooling standalone)
if is_in_dh and not is_in_dc:
    filtered_heat = filter_by_service_temperature(
        heat_data, temp_prefixes=['T25', 'T20', 'T15']
    )
```

**Use case**: Heating-dominant climates, existing DH infrastructure

---

## Decision Tree

```
START: Calculate heat rejection for building X

├─ network_name = "(none)" or empty?
│  └─ YES → CASE 1 (all buildings standalone)
│
└─ NO → Check building connectivity:
   ├─ In DC/nodes.shp? → is_in_dc = True/False
   └─ In DH/nodes.shp? → is_in_dh = True/False

   Determine case:
   ├─ is_in_dc=True AND is_in_dh=True → CASE 2
   ├─ is_in_dc=True AND is_in_dh=False → CASE 3
   ├─ is_in_dc=False AND is_in_dh=True → CASE 4
   └─ is_in_dc=False AND is_in_dh=False → CASE 1
```

## Heat Rejection Extraction

### From SupplySystem Objects

```python
# SupplySystem.heat_rejection is a dict
supply_system.heat_rejection = {
    'T25A': pd.Series([0.0, 5.2, ...]),  # Cooling heat (chiller to cooling tower)
    'T100A': pd.Series([10.2, 15.5, ...])  # DHW heat (boiler exhaust)
}

# Keys: Energy carrier codes (temperature + state)
# Values: Hourly heat rejection in kWh (8760 or 8784 values)
```

### Service-Based Filtering

**Current implementation** (transitional):
- Uses temperature prefix matching to identify service type
- `T100, T90, T80, T60` → Heating/DHW (high-temperature)
- `T25, T20, T15` → Cooling (low-temperature)

**Future enhancement**:
- Extract explicit service metadata from SupplySystem
- Add `service_mapping` dict to track carrier-to-service relationships

## Key Patterns

### ✅ DO: Use helper functions for case logic

```python
from cea.analysis.heat.heat_rejection_helpers import determine_building_case, filter_heat_by_case

# Determine connectivity case
case = determine_building_case(
    building_id, dc_connected_buildings, dh_connected_buildings, is_standalone_only
)

# Filter heat based on case
filtered_heat, filtered_systems = filter_heat_by_case(
    heat_data, supply_systems, case
)
```

### ✅ DO: Reuse cost module functions

```python
from cea.analysis.costs.supply_costs import (
    calculate_all_buildings_as_standalone,
    get_dhw_component_fallback,
    filter_supply_code_by_scale
)

# Calculate building-scale systems (reuses entire cost workflow)
building_cost_results = calculate_all_buildings_as_standalone(locator, cost_config)

# Extract heat_rejection instead of costs
for building_id, cost_data in building_cost_results.items():
    supply_system = cost_data.get('supply_system')
    heat_rejection_data = supply_system.heat_rejection
```

### ❌ DON'T: Infer service from temperature alone (fragile)

```python
# Current (transitional) - works but fragile
if 'T100' in carrier:
    service = 'dhw'  # Assumes T100 is always DHW

# Better (future) - explicit service mapping
service = service_mapping.get(carrier, 'unknown')
```

### ❌ DON'T: Duplicate DHW fallback logic

```python
# ❌ DON'T reimplement feedstock-to-boiler mapping
feedstock_to_boiler = {'GRID': 'BO5', 'NATURALGAS': 'BO1'}  # Duplicates cost logic

# ✅ DO reuse helper from cost module
from cea.analysis.costs.supply_costs import get_dhw_component_fallback
component_code = get_dhw_component_fallback(locator, building_id, feedstock)
```

## 3-Level Fallback System

Mirrors `cea/analysis/costs/AGENTS.md` fallback architecture:

### Level 1: Config Fallback (Scale Mismatch)
**When**: Building's supply.csv has DISTRICT-scale code but building is standalone for that service

**Action**: Replace with BUILDING-scale from config

**Example**:
```python
# supply.csv: type_cs = "AS4" (DISTRICT scale)
# Building in Case 4 (DH only) - cooling is standalone
# Config: supply_type_cs = ["AS1 (building)", "AS4 (district)"]
# Result: Use AS1 (building-scale) for standalone cooling
```

**Implementation**: `heat_rejection_helpers.apply_heat_rejection_config_fallback()`

---

### Level 2: Scale Filtering
**When**: Config has multi-select with both BUILDING and DISTRICT scales

**Action**: Filter to appropriate scale based on `is_standalone`

**Example**:
```python
from cea.analysis.costs.supply_costs import filter_supply_code_by_scale

# For standalone cooling (Case 4)
code = filter_supply_code_by_scale(
    locator, config.supply_type_cs, 'SUPPLY_COOLING', is_standalone=True
)  # Returns "AS1" (building-scale)

# For district network
code = filter_supply_code_by_scale(
    locator, config.supply_type_cs, 'SUPPLY_COOLING', is_standalone=False
)  # Returns "AS4" (district-scale)
```

---

### Level 3: Component Fallback

**Level 3A - District Networks**: Use component categories when no DISTRICT-scale assembly

```python
# No DISTRICT-scale cooling assembly found
if not supply_code and config.cooling_components:
    # Use component-based system
    user_component_selection = {
        'primary': ['CH1'],  # From cooling_components
        'tertiary': ['CT1']  # From heat_rejection_components
    }
```

**Level 3B - DHW**: Map feedstock to boiler when SUPPLY_HOTWATER has no components

```python
from cea.analysis.costs.supply_costs import get_dhw_component_fallback

# Feedstock = 'GRID' → BO5 (electric boiler)
# Feedstock = 'NATURALGAS' → BO1 (gas boiler)
component_code = get_dhw_component_fallback(locator, building_id, feedstock)
```

## Output Files

### heat_rejection_buildings.csv
Summary by building/plant:

```csv
name, type, GFA_m2, x_coord, y_coord, heat_rejection_annual_MWh,
peak_heat_rejection_kW, peak_datetime, scale, case, case_description
```

- `case`: 1, 2, 3, or 4 (connectivity case)
- `case_description`: Human-readable ("Standalone", "Both DC+DH", etc.)
- `GFA_m2`: Building floor area (None for plants)

### heat_rejection_components.csv
Component-level breakdown:

```csv
name, type, component_code, component_type, placement,
capacity_kW, heat_rejection_annual_MWh, peak_heat_rejection_kW, scale
```

### heat_rejection_hourly_[building_name].csv
Individual hourly profiles:

```csv
date, heat_rejection_kW
```

One file per building/plant, 8760 hours (non-leap year)

## Common Pitfalls

1. **Case 2 buildings**: Don't forget they have ZERO standalone heat (all from district)
2. **Temperature heuristics**: Current implementation uses temp prefixes - not 100% reliable
3. **DHW system**: Separate from main system, must be created and merged separately
4. **GFA_m2**: Read from zone geometry, not from supply.csv
5. **Leap year**: Always remove Feb 29 to ensure 8760 hours

## Related Files

**Main module**:
- `heat_rejection.py:49-133` - Main orchestration (`anthropogenic_heat_main`)
- `heat_rejection.py:136-226` - Building-scale calculation
- `heat_rejection.py:350-551` - Network-scale calculation
- `heat_rejection.py:627-714` - 4-case merging logic

**Helpers**:
- `heat_rejection_helpers.py` - Case determination and filtering functions

**Reused from costs module**:
- `supply_costs.py:calculate_all_buildings_as_standalone` - Building supply systems
- `supply_costs.py:get_dhw_component_fallback` - DHW feedstock-to-boiler mapping
- `supply_costs.py:filter_supply_code_by_scale` - Scale filtering

**Configuration**:
- `cea/default.config:[anthropogenic-heat]` - Parameters (mirrors system-costs)

**Reference documentation**:
- `cea/analysis/costs/AGENTS.md` - Cost feature architecture (reference for alignment)
