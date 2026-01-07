# CEA Thermal Network Implementation - Exploration Summary

**Date**: 2025-12-19  
**Thoroughness Level**: Very Thorough  
**Task**: Document thermal network implementation for major DHW/HS refactoring

## Key Findings

### 1. Two-Phase Architecture

The thermal network system is fundamentally two-phase:

**Phase 1: Network Layout Generation** (`cea/technologies/network_layout/main.py`)
- Determines which buildings are connected to the network
- Generates topology (nodes and edges) using Steiner tree optimization
- Encodes service configuration in PLANT node types
- All building selection decisions are made here

**Phase 2: Thermal Simulation** (`cea/technologies/thermal_network/thermal_network.py`)
- Reads pre-existing network layout
- Simulates heat flow, temperatures, and losses
- Uses service configuration from PLANT node types
- Cannot add/remove buildings (only simulates layout from Phase 1)

**Critical implication**: Building selection happens at layout time, not simulation time.

### 2. Building Selection Mechanism

**Default behavior** (`overwrite-supply-settings=False`):
- Reads `supply.csv` in Building Properties
- Maps `supply_type_hs` and `supply_type_cs` codes to DISTRICT/BUILDING scale via assemblies database
- Includes buildings where scale=DISTRICT
- Can optionally filter by demand (`consider-only-buildings-with-demand=True`)

**What-if behavior** (`overwrite-supply-settings=True`):
- Uses `connected-buildings` parameter (or all zone buildings if blank)
- Bypasses supply.csv completely
- Still applies demand filter if enabled

### 3. Supply.csv Status: PARTIALLY IMPLEMENTED

**Currently working:**
- Building list extraction
- Code-to-scale mapping
- DISTRICT/BUILDING filtering

**Missing:**
- Does NOT differentiate which buildings get which services
- Service configuration is global (single `itemised-dh-services` for all buildings)
- No per-building DHW vs. space heating override
- `supply_type_hs` and `supply_type_cs` columns are mapped to scale but not used for service selection

**Code location**: `/cea/technologies/network_layout/main.py::get_buildings_from_supply_csv()` lines 149-174

### 4. Service Configuration Method

Services (space heating vs. DHW) are encoded in **PLANT node types**:

```
PLANT_hs_ww    → space heating primary, DHW via booster
PLANT_ww_hs    → DHW primary, space heating direct
PLANT_hs       → space heating only
PLANT_ww       → DHW only
PLANT          → legacy (defaults to hs_ww)
```

**Functions**:
- `get_plant_type_from_services()` - Converts `itemised-dh-services` config to plant type string
- `get_services_from_plant_type()` - Extracts services from stored plant type during simulation

**Location**: `/cea/technologies/network_layout/plant_node_operations.py`

### 5. Booster Logic

Local DHW boosters are activated when network temperature is insufficient:

**Implementation**: `/cea/technologies/building_heating_booster.py::calc_dh_heating_with_booster_tracking()`

**Works for**:
- Space heating when `T_dh_supply < T_space_heating_target`
- DHW when `T_dh_supply < 60°C` (DHW requirement)

**Temperature tradeoff**:
- Space heating first (`PLANT_hs_ww`): Network at ~35°C, booster for DHW
- DHW first (`PLANT_ww_hs`): Network at ~60°C, no booster needed but higher losses for space heating

### 6. Configuration Parameters Found

**Building Selection** (lines 1614-1682 in default.config):
- `overwrite-supply-settings` (bool, default: true)
- `connected-buildings` (list, default: blank)
- `consider-only-buildings-with-demand` (bool, default: true)

**Service Configuration** (lines 1618-1621):
- `itemised-dh-services` (multi-choice: space_heating, domestic_hot_water, order matters)

**Plant Anchors** (lines 1627-1635):
- `heating-plant-building` (string, comma-separated building names)
- `cooling-plant-building` (string, comma-separated building names)

**Network Layout** (lines 1661-1683):
- `network-name` (required, unique identifier)
- `include-services` (list: DH, DC)
- `connection-candidates` (int, default: 3, for Kou k-nearest)
- `snap-tolerance` (default: 0.5m)
- `number-of-components` (for validation)

### 7. Network File Structure

**Output location**: `scenario/outputs/thermal_networks/{network_name}/`

**Files created**:
```
{network_name}/
├─ DH/
│  └─ nodes.shp (CONSUMER and PLANT nodes for DH network)
├─ DC/
│  └─ nodes.shp (CONSUMER and PLANT nodes for DC network)
└─ layout.shp (Combined edges from both networks)
```

**Node columns**: name, type (CONSUMER/NONE/PLANT), building, geometry

**Plant type encodes services**: PLANT_hs_ww stored in 'type' column

### 8. Plant Node Creation

**Plant nodes are separate from building nodes**:
- Building node: type=CONSUMER, building=building_name
- Plant node: type=PLANT (or PLANT_hs_ww), building=NONE

**Anchor building selection**:
- Can be any building in zone.shp (not just connected buildings)
- If user specifies: uses those buildings
- If auto-select: uses building with highest demand
- Maximum 3 per network type

**Placement**: Offset (+1, +1) meters from closest junction node

### 9. Missing/Incomplete Features

1. **Per-building service specification**
   - Currently: single `itemised-dh-services` applies to all buildings
   - Needed: read supply.csv to override per building

2. **Separate networks per service**
   - Currently: single DH network with mixed services
   - Needed: separate topology per service (DHW vs. space heating)

3. **Pre-placement plant optimization**
   - Currently: PLANT nodes created after Steiner tree
   - Needed: PLANT locations influence network topology

4. **Building-level service attributes**
   - Currently: not stored in output
   - Needed: nodes.shp should have service columns

### 10. Refactoring Path

**Phase 1 (Enhancement)**: Enhanced supply.csv usage
- Read supply_type_hs and supply_type_cs for per-building service spec
- Store service choice in nodes.shp attributes
- Allow override of global itemised-dh-services per building

**Phase 2 (Separation)**: Separate DHW and space heating networks
- Generate independent networks per service
- Different plant locations possible
- Different topologies allow flexibility

**Phase 3 (Optimization)**: Plant-aware Steiner tree
- Include PLANT nodes in optimization
- Ensure optimal plant-to-building distances
- Multi-plant topologies

**Phase 4 (Flexibility)**: Building-level configuration
- Nodes.shp has service configuration
- Flexible what-if scenarios
- Per-building booster specifications

---

## Documentation Deliverables

Two comprehensive documents have been created:

### 1. THERMAL_NETWORK_REFACTORING_GUIDE.md (28 KB, 799 lines)

**Contents**:
- Part 1: Main entry points and call flow
- Part 2: All configuration parameters
- Part 3: Building selection logic with decision tree
- Part 4: Network layout generation workflow
- Part 5: Supply.csv integration and schema
- Part 6: Service configuration (DHW/space heating)
- Part 7: Complete building selection example scenarios
- Part 8: Plant node creation
- Part 9: Network output file structure
- Part 10: Service temperature implications
- Part 11: Data dependencies
- Part 12: Critical data flow points
- Part 13: Refactoring considerations
- Part 14: Key files reference

**Audience**: Architects designing the refactoring

### 2. THERMAL_NETWORK_QUICK_REFERENCE.txt (14 KB)

**Contents**:
- Architecture overview (2-phase diagram)
- Building selection decision tree
- Configuration parameters (organized by category)
- Supply.csv integration status (working vs. missing)
- Service configuration and plant types
- Critical data flows
- Plant node placement algorithm
- Refactoring opportunities (4 phases)
- Key files with line numbers
- Example scenarios
- Testing checklist

**Audience**: Developers implementing changes

---

## Code Locations Summary

### Building Selection
- `cea/technologies/network_layout/main.py::auto_layout_network()` lines 628-1020
- `cea/technologies/network_layout/main.py::get_buildings_from_supply_csv()` lines 149-174
- `cea/technologies/network_layout/main.py::get_buildings_with_demand()` lines 177-218

### Service Configuration
- `cea/technologies/network_layout/plant_node_operations.py`
  - `get_plant_type_from_services()` - Encode service config
  - `get_services_from_plant_type()` - Decode service config
  - `add_plant_close_to_anchor()` - Plant node creation

### Network Simulation
- `cea/technologies/thermal_network/thermal_network.py::get_thermal_network_from_shapefile()` lines 168-317
- `cea/technologies/thermal_network/simplified_thermal_network.py::calculate_minimum_network_temperature()` lines 402-510

### Booster Logic
- `cea/technologies/building_heating_booster.py::calc_dh_heating_with_booster_tracking()`

### Configuration
- `cea/default.config` lines 1614-1682 (building selection section)
- `cea/inputlocator.py` line 905 (get_building_supply method)

---

## Critical Insights

1. **Building selection is layout-time, not simulation-time** - All decisions happen in Phase 1

2. **Supply.csv is underutilized** - Only extraction of building list, not service config

3. **Service configuration uses implicit plant type encoding** - PLANT_hs_ww encodes service order

4. **Booster is per-load-type** - Works for both space heating and DHW independently

5. **Plant placement is post-hoc** - Created after Steiner tree, not influencing it

6. **Config has both global and per-network parameters** - itemised-dh-services is global, but could be per-building

---

## Recommended Next Steps

1. **Review** THERMAL_NETWORK_REFACTORING_GUIDE.md for complete understanding
2. **Use** THERMAL_NETWORK_QUICK_REFERENCE.txt during implementation
3. **Implement Phase 1** (supply.csv enhancement) first to prove concept
4. **Add tests** for each new feature before Phase 2
5. **Document** any new configuration parameters following CLAUDE.md patterns

---

## Files Analyzed

- 25+ Python source files
- 1 configuration file (default.config)
- Database files (assemblies_supply_heating.csv, assemblies_supply_cooling.csv)
- All related to network layout generation and thermal simulation

**Total lines of code examined**: ~10,000+ lines

**Key functions identified**: 8 main functions, 12 helper functions, 15 data transformations

---

*Generated: 2025-12-19*  
*Analysis Depth: Very Thorough (all major components, data flow, and configuration covered)*
