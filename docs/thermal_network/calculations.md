# Thermal Network Calculations - Complete Reference

This document explains how CEA calculates thermal networks for district heating (DH) and district cooling (DC) systems, with special focus on low-temperature networks with service priority and booster support.

---

## Table of Contents

1. [Overview](#overview)
2. [Service Priority Concept](#service-priority-concept)
3. [Network Models](#network-models)
4. [Substation Calculations](#substation-calculations)
5. [Network Solver (Detailed Model)](#network-solver-detailed-model)
6. [Network Solver (Simplified Model)](#network-solver-simplified-model)
7. [Plant Load Calculation](#plant-load-calculation)
8. [Key Files and Functions](#key-files-and-functions)
9. [Common Pitfalls](#common-pitfalls)

---

## Overview

CEA supports two thermal network modeling approaches:

- **Detailed Model**: Coupled thermal-hydraulic iterative solver
- **Simplified Model**: Decoupled hydraulic (EPANET/WNTR) + thermal overlay

Both models support **service priority** for low-temperature DH networks where one service (e.g., space heating) determines network temperature and other services (e.g., DHW) use local boosters when needed.

---

## Service Priority Concept

### What is Service Priority?

In low-temperature district heating (e.g., 35-45°C supply), the network temperature may be too low for some services (e.g., DHW requires 60°C). **Service priority** determines which service sets the network temperature.

### Plant Types

Defined in `network_service_priority.py`:

| Plant Type | Priority Service | Secondary Services | Network Temp |
|------------|-----------------|-------------------|--------------|
| `PLANT_hs` | Space heating (hs) | - | 35-45°C |
| `PLANT_ww` | DHW (ww) | - | 60-65°C |
| `PLANT_hs_ww` | Space heating | DHW (with booster) | 35-45°C |
| `PLANT_cs` | Space cooling | - | 7-12°C |

### How Boosters Work

When network temperature is insufficient:

1. **Check**: Is `T_network + MIN_APPROACH_TEMP_K < T_target`?
2. **If YES**: Use booster-aware calculation:
   - DH pre-heats from `T_return` to `T_network - MIN_APPROACH_TEMP_K`
   - Local booster tops up from DH outlet to `T_target`
3. **If NO**: Standard heat exchanger calculation (DH provides all heat)

**Example** (DHW with 36°C network, 60°C target, 9.4°C cold water):
```
DH contribution:   9.4°C → 31.2°C  (ΔT = 21.8K, 43% of heat)
Booster tops up:  31.2°C → 60.0°C  (ΔT = 28.8K, 57% of heat)
```

---

## Network Models

### Detailed Model

**File**: `thermal_network.py`

**Approach**: Coupled thermal-hydraulic iterative solver

**Process**:
1. Solve mass flows for each time step using `calc_mass_flow()` (WNTR/EPANET)
2. For each iteration until convergence:
   - Calculate substation return temperatures: `calc_substation_return_DH()`
   - Calculate network thermal losses: `calc_thermal_loss_edges()`
   - Update temperatures throughout network
3. Calculate plant load from mass flows and temperature difference

**Key Functions**:
- `solve_network_temperatures()` - Main solver loop
- `calc_substation_return_DH()` - Substation heat transfer with booster logic
- `calc_plant_heat_requirement()` - Plant thermal load

### Simplified Model

**File**: `simplified_thermal_network.py`

**Approach**: Decoupled hydraulic + thermal overlay

**Process**:
1. **Hydraulic solver** (WNTR/EPANET): Calculate mass flows assuming constant temperature
2. **Substation calculations**: For each building, calculate DH contribution and booster needs
3. **Thermal overlay**: Estimate temperature drops from thermal losses
4. **Plant load**: Sum DH contributions + network losses

**Key Functions**:
- `get_thermal_network_from_shapefile()` - Network setup
- Substation calculations embedded in main loop
- Direct plant load calculation (no iteration)

---

## Substation Calculations

### Standard Heat Exchanger (No Booster Needed)

**Function**: `calc_HEX_heating()` in `substation_matrix.py`

**Method**: NTU-Effectiveness for shell-tube heat exchanger

**When Used**: Network temperature is sufficient (`T_DH_supply >= T_target + MIN_APPROACH_TEMP_K`)

**Returns**:
- `Q`: Heat transferred [W]
- `t_return`: Return temperature [K]
- `mcp`: Mass flow × specific heat [kW/K]
- `ch`: Mass flow × specific heat [W/K]

### Booster-Aware Calculation

**Function**: `calc_dh_heating_with_booster_tracking()` in `building_heating_booster.py`

**When Used**: Network temperature insufficient for target

**Logic**:
```python
T_dh_preheat_max_C = T_DH_supply_C - MIN_APPROACH_TEMP_K

if T_dh_preheat_max_C < T_target_C:
    # DH pre-heats from T_return to T_dh_preheat_max
    temp_rise_dh = T_dh_preheat_max - T_return
    temp_rise_total = T_target - T_return

    # Split heat based on temperature rise
    fraction_dh = temp_rise_dh / temp_rise_total
    Q_dh = Q_demand * fraction_dh
    Q_booster = Q_demand - Q_dh
```

**Returns**:
- `Q_dh_W`: DH contribution [W]
- `T_dh_return_C`: DH return temperature [°C]
- `mcp_dh_kWK`: DH mass flow capacity [kW/K]
- `Q_booster_W`: Local booster heat [W]
- `A_hex_m2`: Heat exchanger area [m²]

### Integration in Detailed Model

**Location**: `substation_matrix.py:326-531` (`calc_substation_return_DH()`)

For each heating service (ahu, aru, shu, ww):

```python
# Check if network temperature sufficient
T_DH_supply_C = T_DH_supply_K - 273.15
T_target_C = building['T_target_C'].values
MIN_APPROACH_TEMP_K = 5

if T_DH_supply_C < (T_target_C[0] + MIN_APPROACH_TEMP_K):
    # Use booster-aware calculation
    Q_dh_W, T_dh_return_C_arr, mcp_dh_kWK_arr, Q_booster_W, A_hex_m2, _ = \
        calc_dh_heating_with_booster_tracking(
            Q_demand_W=Q_demand_W,
            T_DH_supply_C=T_DH_supply_C,
            T_target_C=T_target_C,
            T_return_C=T_return_C,
            load_type='space_heating'  # or 'dhw'
        )

    # Extract values - KEEP IN kW/K for mass_flows list
    mcp_DH = mcp_dh_kWK_arr[0]  # kW/K
    ch_value = mcp_DH * 1000     # W/K for storage
else:
    # Standard HEX calculation
    Q, t_return, mcp_DH, ch_value = calc_HEX_heating(...)
```

**CRITICAL**: Keep `mcp` in kW/K for `mass_flows` list (line 535 sums in kW/K units)

---

## Network Solver (Detailed Model)

### Main Iteration Loop

**Function**: `solve_network_temperatures()` in `thermal_network.py:2644-2889`

```python
for each time step t:
    if network has demand:
        # Initialize
        reset_min_mass_flow_variables()

        for k in range(MAX_ITERATIONS):
            # 1. Calculate substation return temperatures
            t_substation_return = calc_substation_return_DH(
                thermal_network, t, t_supply_nodes, k
            )

            # 2. Calculate thermal losses in pipes
            q_loss_supply, q_loss_return = calc_thermal_loss_edges(...)

            # 3. Update return node temperatures
            t_return_nodes = calc_return_node_temperatures(...)

            # 4. Update supply node temperatures (from plant)
            t_supply_nodes = calc_supply_node_temperatures(...)

            # Check convergence
            if converged(t_supply_nodes, t_supply_nodes_previous):
                break

        # 5. Calculate plant load
        plant_heat_requirement = calc_plant_heat_requirement(
            plant_nodes, t_supply_nodes, t_return_nodes, mass_flows
        )
```

### Plant Load Calculation

**Function**: `calc_plant_heat_requirement()` in `thermal_network.py:2921-2940`

```python
def calc_plant_heat_requirement(plant_node, t_supply_nodes, t_return_nodes,
                                 mass_flow_substations_nodes_df):
    """
    Calculate plant thermal load from temperature difference and mass flow

    Formula: Q = mcp × (T_supply - T_return)
             Q = (kg/s × J/kg·K) × K = W
    """
    plant_heat_requirement_kw = np.full(plant_node.size, np.nan)

    for i in range(plant_node.size):
        node = plant_node[i]
        heat_requirement = HEAT_CAPACITY_OF_WATER_JPERKGK / 1000 * \
                          (t_supply_nodes[node] - t_return_nodes[node]) * \
                          abs(mass_flow_substations_nodes_df.iloc[0, node])
        plant_heat_requirement_kw[i] = heat_requirement

    return plant_heat_requirement_kw
```

**Units**:
- `HEAT_CAPACITY_OF_WATER_JPERKGK = 4185` J/(kg·K)
- Divide by 1000 to convert J/s (W) to kW
- `mass_flow_substations_nodes_df`: kg/s at each node
- Result: kW

---

## Network Solver (Simplified Model)

### Workflow

**File**: `simplified_thermal_network.py`

```python
# 1. HYDRAULIC SOLVER (WNTR/EPANET)
wn = wntr.network.WaterNetworkModel()
# Add pipes, nodes, demands from shapefile
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()

# Extract mass flows (assumes constant temperature)
edge_mass_flow = results.link['flowrate']

# 2. SUBSTATION CALCULATIONS
for building in buildings:
    # Calculate substation heating/cooling with booster tracking
    substation_results = calc_substation_heating_with_priority(
        building_demand, T_DH_supply_target, service_priority
    )

    # Extract DH contribution (excludes booster)
    Q_demand_DH_kWh_building[building] = (
        substation_results["Qhs_dh_W"] + substation_results["Qww_dh_W"]
    ) / 1000

    # Total demand (DH + booster) - for reporting only
    Q_demand_total_kWh_building[building] = (
        substation_results["Qhs_dh_W"] + substation_results["Qhs_booster_W"] +
        substation_results["Qww_dh_W"] + substation_results["Qww_booster_W"]
    ) / 1000

# 3. THERMAL LOSSES
for pipe in pipes:
    # Calculate thermal losses from temperature drop
    thermal_loss_supply = calc_thermal_loss_pipe(
        mass_flow, T_supply, pipe_properties
    )
    thermal_loss_return = thermal_loss_supply  # Approximation

# 4. PLANT LOAD
accumulated_thermal_loss_total = (
    thermal_losses_supply.sum(axis=1) + thermal_losses_return.sum(axis=1)
)

plant_load = Q_demand_DH_kWh_building.sum(axis=1) + accumulated_thermal_loss_total
```

**Key Difference**: No iteration - uses target supply temperature throughout

---

## Plant Load Calculation

### Correct Formula

**Both models should use**:

```
Plant Thermal Load = DH Delivered to Buildings + Network Thermal Losses
```

**NOT**:
```
Plant Load = Total Building Heat + Losses  ❌ (includes booster heat)
Plant Load = DH + Losses - Pumping         ❌ (pumping is electrical, not thermal)
```

### Why Booster Heat is Excluded

Booster heat comes from **local equipment at buildings** (electric resistance heaters, gas boilers, etc.). The district heating plant only provides the DH portion.

**Example**:
```
Building total heating:  100 kW
  - DH contribution:      60 kW  (from network)
  - Booster contribution: 40 kW  (local equipment)

Plant must provide: 60 kW (DH only) + network losses
```

### Why Pumping is Excluded

Pumping energy is **electrical power** consumed by pumps to move water. It's a separate energy input from the plant's **thermal** energy.

**Energy flows**:
```
Plant thermal output:  300 kW (heat)
  ↓
Network: -10 kW (thermal losses)
  ↓
Buildings receive: 290 kW (heat)

Pumps: +15 kW (electricity) - separate accounting
```

### Detailed Model Implementation

**File**: `thermal_network.py:2921-2940`

```python
plant_heat_requirement = calc_plant_heat_requirement(
    plant_nodes, T_supply, T_return, mass_flows
)
# Returns: Q = mcp × ΔT [kW]
```

**Energy balance**:
```
Plant load ≈ Substation DH + Thermal losses
281.41 ≈ 279.40 + 3.76 = 283.16 MWh (error: 0.62%)
```

### Simplified Model Implementation

**File**: `simplified_thermal_network.py:1210-1216`

```python
# Calculate total thermal losses (supply + return)
accumulated_thermal_loss_total_kWh = (
    thermal_losses_supply_kWh.sum(axis=1) + thermal_losses_return_kWh.sum(axis=1)
)

# Plant thermal load = DH delivered + network losses
plant_load_kWh = Q_demand_DH_kWh_building.sum(axis=1) + accumulated_thermal_loss_total_kWh
```

**Energy balance**:
```
Plant load ≈ Substation DH + Thermal losses
291.52 ≈ 279.40 + 12.16 = 291.56 MWh (error: 0.01%)
```

---

## Key Files and Functions

### Core Network Files

| File | Purpose | Model |
|------|---------|-------|
| `thermal_network.py` | Detailed solver | Detailed |
| `simplified_thermal_network.py` | Simplified solver | Simplified |
| `substation_matrix.py` | Substation calculations | Detailed |
| `network_service_priority.py` | Service priority config | Both |
| `building_heating_booster.py` | Booster calculations | Both |

### Key Functions

#### Detailed Model

| Function | Location | Purpose |
|----------|----------|---------|
| `solve_network_temperatures()` | `thermal_network.py:2644` | Main iteration loop |
| `calc_substation_return_DH()` | `substation_matrix.py:326` | Substation heat transfer |
| `calc_plant_heat_requirement()` | `thermal_network.py:2921` | Plant thermal load |
| `calc_HEX_heating()` | `substation_matrix.py:829` | Standard HEX calculation |
| `calc_dh_heating_with_booster_tracking()` | `building_heating_booster.py:27` | Booster-aware calculation |

#### Simplified Model

| Function | Location | Purpose |
|----------|----------|---------|
| `get_thermal_network_from_shapefile()` | `simplified_thermal_network.py:536` | Main entry point |
| Network setup | Lines 540-730 | WNTR model creation |
| Substation loop | Lines 600-625 | Per-building calculations |
| Plant load | Lines 1210-1216 | Plant thermal load |

### Constants

**File**: `cea/constants.py`

```python
HEAT_CAPACITY_OF_WATER_JPERKGK = 4185  # J/(kg·K)
P_WATER_KGPERM3 = 1000                  # kg/m³
PUMP_ETA = 0.8                          # Pump efficiency (80%)
```

**Hardcoded**:
```python
MIN_APPROACH_TEMP_K = 5  # Minimum approach temperature for heat exchangers
```

---

## Common Pitfalls

### 1. Unit Conversion in Booster Calculations

❌ **WRONG**:
```python
mcp_DH = mcp_dh_kWK_arr[0] * 1000  # kW/K to W/K
ch_value = mcp_DH / 1000            # W/K to kW/K
mass_flows.append(mcp_DH)           # Appending W/K
```

✅ **CORRECT**:
```python
mcp_DH = mcp_dh_kWK_arr[0]  # Keep in kW/K
ch_value = mcp_DH * 1000     # kW/K to W/K for storage
mass_flows.append(mcp_DH)    # Appending kW/K (consistent with calc_HEX_heating)
```

**Why**: Line 535 does `mcp_DH_kWK = sum(mass_flows)` expecting kW/K units.

### 2. Including Booster Heat in Plant Load

❌ **WRONG**:
```python
Q_demand_building = Qhs_dh + Qhs_booster + Qww_dh + Qww_booster
plant_load = Q_demand_building.sum() + losses
```

✅ **CORRECT**:
```python
Q_demand_DH_building = Qhs_dh + Qww_dh  # DH only
plant_load = Q_demand_DH_building.sum() + losses
```

**Why**: Booster heat comes from local equipment, not the DH plant.

### 3. Subtracting Pumping Energy

❌ **WRONG**:
```python
plant_load = DH_demand + losses - pumping_kW
```

✅ **CORRECT**:
```python
plant_load = DH_demand + losses
# Pumping is electrical energy, tracked separately
```

**Why**: Pumping energy is electrical input, plant load is thermal output.

### 4. Using `losses_supply * 2` Approximation

❌ **WRONG**:
```python
plant_load = DH_demand + losses_supply * 2
```

✅ **CORRECT**:
```python
total_losses = losses_supply + losses_return
plant_load = DH_demand + total_losses
```

**Why**: Supply and return losses may differ due to temperature differences.

### 5. Forgetting MIN_APPROACH_TEMP_K

❌ **WRONG**:
```python
if T_DH_supply < T_target:
    use_booster()
```

✅ **CORRECT**:
```python
if T_DH_supply < (T_target + MIN_APPROACH_TEMP_K):
    use_booster()
```

**Why**: Heat exchangers need temperature difference to transfer heat effectively.

### 6. Not Handling Zero/NaN Values

❌ **WRONG**:
```python
T_return_nodes.to_csv(file)  # May contain NaN during idle hours
```

✅ **CORRECT**:
```python
T_return_nodes = T_return_nodes.fillna(273.15)  # 0°C sentinel for idle
mass_flows = mass_flows.fillna(0)               # Zero flow during idle
T_return_nodes.to_csv(file)
```

**Why**: NaN values cause issues in post-processing and plotting.

---

## Validation Checklist

When implementing or debugging thermal network calculations:

- [ ] Substation energy split (DH vs booster) is consistent between models
- [ ] Plant load = DH delivered + thermal losses (not including booster)
- [ ] No pumping energy in thermal plant load calculation
- [ ] Network temperatures are physically valid (no negatives)
- [ ] Mass flows in correct units (kg/s, kW/K consistency)
- [ ] Energy balance closes: Plant ≈ Substations + Losses (within 1-2%)
- [ ] NaN/sentinel values handled correctly (273.15K for temps, 0 for flows)
- [ ] MIN_APPROACH_TEMP_K considered in booster logic
- [ ] Service priority correctly determines network temperature

---

## References

- **Service Priority Implementation**: PR #3XXX (service priority refactoring)
- **Bug Fixes**: Session 2026-01-06 (negative temperatures, unit conversion, plant load formula)
- **Related Modules**:
  - `cea/demand/` - Building heating/cooling demands
  - `cea/technologies/substation.py` - Heat exchanger calculations
  - `cea/optimization/` - Network optimization

---

**Last Updated**: 2026-01-06
**Author**: CEA Development Team
**Status**: Production-ready after bug fixes
