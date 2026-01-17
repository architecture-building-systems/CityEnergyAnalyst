# CEA Thermal Network Implementation - Comprehensive Analysis

## Executive Summary

The CEA thermal network implementation is organized into two main phases:

1. **Network Layout Generation** (`cea/technologies/network_layout/`) - Creates network topology (nodes/edges)
2. **Thermal Network Simulation** (`cea/technologies/thermal_network/`) - Simulates heat flow and properties

Key architectural decision: **Building selection happens at layout generation time**, not at simulation time. The layout phase determines which buildings are in the network via configuration parameters, and the thermal simulation phase only simulates buildings already in the layout.

---

## Part 1: Main Entry Points & Call Flow

### Entry Point 1: Network Layout Generation
**Script**: `cea/technologies/network_layout/main.py::main()`

**Call Path**:
```
main(config)
  ├─ Check if user-provided network (edges.shp/nodes.shp/geojson)
  │   └─ process_user_defined_network()
  │       ├─ load_user_defined_network()
  │       ├─ auto_create_plant_nodes() (if no PLANT nodes exist)
  │       └─ Save DC/DH nodes to layout folders
  │
  └─ Auto-generate layout via Steiner tree
      └─ auto_layout_network(config, network_layout, locator)
          ├─ Determine buildings to connect (see Part 3)
          ├─ calc_building_centroids() - Extract building locations
          ├─ calc_connectivity_network_with_geometry() - Build street graph
          ├─ calc_steiner_spanning_tree() - Optimize network
          ├─ add_plant_close_to_anchor() - Create PLANT nodes
          └─ Save network to shapefile
```

**Configuration Read**:
- `config.network_layout.network_name` - Network identifier
- `config.network_layout.include_services` - List of services (DH/DC)
- `config.network_layout.overwrite_supply_settings` - Use connected-buildings or supply.csv
- `config.network_layout.connected_buildings` - What-if list of buildings
- `config.network_layout.consider_only_buildings_with_demand` - Filter by demand
- `config.network_layout.connection_candidates` - k-nearest optimization
- `config.network_layout.cooling_plant_building` - Plant anchors for DC
- `config.network_layout.heating_plant_building` - Plant anchors for DH
- `config.network_layout.itemised_dh_services` - DH service priority order

### Entry Point 2: Thermal Network Simulation
**Script**: `cea/technologies/thermal_network/thermal_network.py::main()`

**Call Path**:
```
main(config)
  ├─ Read config.thermal_network.network_name
  ├─ Read config.thermal_network.network_type (list: DH, DC, or both)
  ├─ Read config.thermal_network.network_model ('simplified' or 'detailed')
  │
  └─ For each network type in network_types:
      ├─ if simplified:
      │   └─ thermal_network_simplified()
      │       ├─ get_thermal_network_from_shapefile() - Load layout
      │       ├─ Simulate heat transfer
      │       └─ Save results (CSV + shapefile)
      │
      └─ if detailed:
          └─ ThermalNetwork(locator, network_name, config)
              └─ get_thermal_network_from_shapefile()
                  ├─ Load layout from DH/DC nodes folder
                  ├─ Extract PLANT node type to get service config
                  ├─ Create edge-node incidence matrix
                  └─ Calculate initial mass flows
```

**Configuration Read**:
- `config.thermal_network.network_name` - Must match layout network name
- `config.thermal_network.network_type` - DH, DC, or both
- `config.thermal_network.network_model` - 'simplified' or 'detailed'
- Other thermal params (temperature control, plant temp, etc.)

---

## Part 2: Configuration Parameters

### 2A. Building Selection Parameters

**All parameters in**: `cea/default.config` section `[network-layout]`

| Parameter | Type | Default | Usage | Read From |
|-----------|------|---------|-------|-----------|
| `overwrite-supply-settings` | Boolean | true | Switch between supply.csv and connected-buildings | Line 1614 |
| `connected-buildings` | BuildingsParameter | (blank) | What-if list of connected buildings | Line 1623-1625 |
| `consider-only-buildings-with-demand` | Boolean | true | Filter by demand > 0 | Line 1680-1682 |
| `itemised-dh-services` | MultiChoiceParameter | [space_heating, domestic_hot_water] | DH service priority order | Line 1618-1621 |
| `heating-plant-building` | StringParameter | (blank) | Anchor building(s) for DH plant placement | Line 1632-1635 |
| `cooling-plant-building` | StringParameter | (blank) | Anchor building(s) for DC plant placement | Line 1627-1630 |

### 2B. Network Layout Parameters

| Parameter | Type | Default | Usage | Read From |
|-----------|------|---------|-------|-----------|
| `network-name` | StringParameter | (required) | Unique identifier for layout variant | Line 549-550 |
| `network-type` | ChoiceParameter | DH | Network type to simulate | Line 1275-1277 |
| `include-services` | MultiChoiceParameter | [DH, DC] | Which networks to generate | (network_layout config) |
| `connection-candidates` | IntegerParameter | 3 | k-nearest for Kou optimization | (network_layout config) |
| `snap-tolerance` | IntegerParameter | (blank=0.5m) | Snap near-miss endpoints | (network_layout config) |
| `number-of-components` | IntegerParameter | (blank) | Expected disconnected components (validation) | (network_layout config) |

### 2C. Thermal Network Parameters

**All parameters in**: `cea/default.config` section `[thermal-network]`

| Parameter | Type | Default | Read In |
|-----------|------|---------|---------|
| `network-name` | NetworkLayoutChoiceParameter | (required) | thermal_network.py line 3458 |
| `network-type` | MultiChoiceParameter | [DH, DC] | thermal_network.py line 3479 |
| `network-model` | ChoiceParameter | simplified | thermal_network.py line 3454 |
| `temperature-control` | ChoiceParameter | VT | Plant supply temp control |
| `plant-supply-temperature` | IntegerParameter | 80 | Supply temp in CT mode |

---

## Part 3: Building Selection Logic

### 3A. Selection Decision Tree

```
if overwrite_supply_settings = True:
    # What-if scenario mode
    if connected_buildings is explicitly set (non-empty):
        buildings_list = connected_buildings
        mode = "User-specified what-if list"
    else:
        buildings_list = all_buildings_in_zone
        mode = "All zone buildings (blank = all)"
else:
    # Standard mode: read from supply.csv
    buildings_list = get_buildings_from_supply_csv(locator, network_type)
    mode = "Building Properties/Supply settings"
    
    # WARN if connected_buildings was set
    if connected_buildings is not empty:
        print("⚠ connected-buildings ignored (overwrite-supply-settings=False)")
```

**Location**: `/cea/technologies/network_layout/main.py` lines 636-727

### 3B. get_buildings_from_supply_csv() Implementation

**Location**: `/cea/technologies/network_layout/main.py` lines 149-174

**Logic**:
1. Read supply.csv
2. Read assemblies database (supply_heating or supply_cooling)
3. Map supply system codes to scale (DISTRICT vs BUILDING)
4. Filter rows where scale='DISTRICT'
5. Return list of building names

**Example**:
```csv
# supply.csv
name,supply_type_hs,supply_type_cs
B001,DHN,ahu
B002,DHN,DC
B003,BUILDING,ahu
```
After mapping with assemblies:
```
DHN → DISTRICT (in DH assemblies)
DC → DISTRICT (in DC assemblies)
BUILDING → BUILDING
```
Result: Buildings B001, B002 are in DH network; B001, B002 in DC network

### 3C. get_buildings_with_demand() Implementation

**Location**: `/cea/technologies/network_layout/main.py` lines 177-218

**Logic**:
1. Read total_demand.csv
2. Filter rows where QH_sys_MWhyr > 0 (for DH) or QC_sys_MWhyr > 0 (for DC)
3. Return building names with non-zero demand

**Applied When**: `consider_only_buildings_with_demand=True`

### 3D. Building Selection in Plant Node Creation

**Location**: `/cea/technologies/network_layout/main.py` lines 221-548

Plant buildings can be **ANY building in zone**, not just connected buildings:
- Used as anchors for PLANT node placement
- Can be specified via config (`heating-plant-building`, `cooling-plant-building`)
- If not specified, auto-select building with highest demand

---

## Part 4: Network Layout Generation

### 4A. Auto-Generated Layout (Steiner Tree)

**Function**: `auto_layout_network()` lines 628-1020

**Workflow**:

```
1. Determine connected buildings (see Part 3)
   ├─ Read supply.csv OR use connected-buildings parameter
   └─ Apply demand filter if enabled

2. Load street network
   └─ gpd.read_file(locator.get_street_network())

3. For each network type (DC, DH):
   ├─ Extract building centroids
   │   └─ calc_building_centroids(zone_df, buildings_list, plant_buildings, consider_demand_filter, network_type)
   │
   ├─ Build connectivity graph
   │   └─ calc_connectivity_network_with_geometry(streets_gdf, buildings_gdf, connection_candidates=k)
   │       └─ Returns NetworkX graph with normalized coordinates
   │
   ├─ Optimize with Steiner tree
   │   └─ calc_steiner_spanning_tree(graph, method='kou' or 'mehlhorn', connection_candidates=k)
   │       └─ Returns optimal edges and nodes for this network type
   │
   ├─ Create PLANT node
   │   └─ add_plant_close_to_anchor(anchor_building, nodes, edges, ...)
   │       ├─ Create separate PLANT node near anchor building
   │       ├─ Mark with type='PLANT_DH' or 'PLANT_DC' temporarily
   │       └─ Encodes service configuration in type (e.g., 'PLANT_hs_ww')
   │
   └─ Save network-specific nodes to DH/DC folder

4. Combine all edges and save to layout.shp
```

### 4B. User-Defined Layout Processing

**Function**: `process_user_defined_network()` lines 1082-1363

**Input Options**:
- Edges shapefile (layout.shp) - Required
- Nodes shapefile - Optional (can auto-convert from nodes column in edges)
- GeoJSON - Optional alternative format

**Workflow**:

```
1. Load user-provided network from shapefile/GeoJSON
   └─ load_user_defined_network(config, locator, edges_shp, nodes_shp, geojson_path)
       └─ Returns GeoDataFrames for nodes and edges

2. Validate building names exist in zone
   └─ All network buildings must exist in zone.shp

3. Determine connected buildings
   └─ Same logic as auto-generated (supply.csv vs connected-buildings)

4. Validate network connectivity
   └─ validate_network_covers_district_buildings()
       └─ All specified buildings must have nodes in network

5. Auto-create missing PLANT nodes (if none exist)
   └─ auto_create_plant_nodes(nodes, edges, zone_gdf, plant_building_names, network_type)
       ├─ If PLANT nodes already exist: Use them as-is
       ├─ If user specified plant buildings: Create PLANT at each one
       └─ Otherwise: Create PLANT at building with highest demand

6. Separate nodes for DC and DH
   └─ PLANT → PLANT_DC (for DC) or PLANT_DH (for DH)
   └─ Save to DC/DH folders

7. Save combined edges to layout.shp
```

### 4C. Node Type Conversion (User-Defined Input)

**Function**: `convert_simplified_nodes_to_full_format()` lines 32-115

Converts simplified user format to CEA full format:

| Simplified Type | Full Type | Building |
|-----------------|-----------|----------|
| Building name (e.g., "B001") | CONSUMER | B001 |
| "NONE" | NONE | NONE |
| "PLANT" | PLANT | NONE |
| "PLANT_DC" | PLANT_DC | NONE |
| "PLANT_DH" | PLANT_DH | NONE |
| Empty/NaN | NONE | NONE |

---

## Part 5: Supply.csv Integration

### 5A. supply.csv Schema

**Location**: `cea/inputlocator.py` line 905 → `scenario/inputs/building-properties/supply.csv`

**Columns**:
- `name` - Building identifier
- `supply_type_hs` - Heating supply system code (e.g., "DHN", "BUILDING", etc.)
- `supply_type_cs` - Cooling supply system code (e.g., "DHN", "BUILDING", etc.)
- Other columns (not used by thermal network)

**Example**:
```csv
name,supply_type_hs,supply_type_cs
B001,DHN,DHN
B002,BUILDING,DHN
B003,BUILDING,BUILDING
```

### 5B. Assemblies Database Mapping

**Location**: 
- DH assemblies: `locator.get_database_assemblies_supply_heating()` → `cea/databases/assemblies_supply_heating.csv`
- DC assemblies: `locator.get_database_assemblies_supply_cooling()` → `cea/databases/assemblies_supply_cooling.csv`

**Schema**:
| code | scale | ... |
|------|-------|-----|
| DHN | DISTRICT | ... |
| BUILDING | BUILDING | ... |
| Individual system codes | BUILDING | ... |

### 5C. Current Implementation of overwrite-supply-settings

**Status**: PARTIALLY IMPLEMENTED

**Working**:
- ✅ Switch between supply.csv and connected-buildings parameter
- ✅ If overwrite=True and connected-buildings is blank, uses all zone buildings
- ✅ If overwrite=True and connected-buildings has values, uses those values
- ✅ If overwrite=False, reads supply.csv and validates buildings exist

**Missing**:
- ❌ Does NOT read supply_type_hs and supply_type_cs columns to filter specific services
- ❌ Currently reads supply.csv only to get the building list, ignores service types
- ❌ No per-building service specification

**Code Location**: `/cea/technologies/network_layout/main.py` lines 149-174

---

## Part 6: Service Configuration (DHW/Space Heating)

### 6A. itemised-dh-services Parameter

**Definition** (default.config lines 1618-1621):
```
itemised-dh-services = space_heating, domestic_hot_water

Choices:
- space_heating
- domestic_hot_water

Order matters:
[space_heating, domestic_hot_water] = network at space heating temp (e.g., 35°C for LTDH)
                                      DHW uses booster if needed
                                      
[domestic_hot_water, space_heating] = network at max(60°C, space heating temp)
                                      ensures DHW always served
                                      accommodates both low-temp and high-temp systems
```

### 6B. Plant Node Type Encoding

**Location**: `/cea/technologies/network_layout/plant_node_operations.py`

**Service Encoding in Plant Type**:
```python
PLANT_hs_ww    = space_heating first, DHW second (network at ~35°C)
PLANT_ww_hs    = DHW first, space heating second (network at ~60°C)
PLANT_hs       = space_heating only
PLANT_ww       = DHW only
PLANT           = legacy (defaults to hs_ww)
```

**Functions**:
- `get_plant_type_from_services(itemised_dh_services, network_type)` - Generates type from config
- `get_services_from_plant_type(plant_type)` - Extracts services from type string

### 6C. Booster Logic

**Location**: `/cea/technologies/building_heating_booster.py`

**When Booster Activates**:
```python
If T_dh_supply < T_target:
    DH pre-heats from return temp to (T_dh_supply - 5K approach temp)
    Booster tops up from DH outlet to target temp
else:
    DH heats to target temp directly
```

**Used In**:
- Simplified thermal network: `simplified_thermal_network.py` lines 534+ 
- For both space heating and DHW loads
- Calculates booster heat, DH return temp, HEX area

### 6D. Service Configuration in Thermal Simulation

**Location**: `/cea/technologies/thermal_network/thermal_network.py` lines 242-262

**Workflow**:
1. Thermal network simulation loads network layout
2. Reads PLANT node type from nodes.shp
3. Extracts service configuration via `get_services_from_plant_type()`
4. If legacy PLANT type: Use default behavior (both services)
5. If modern type (e.g., PLANT_hs_ww): Use specified service order
6. Stores in `self.itemised_dh_services` attribute
7. Passes to substation matrix and booster calculations

---

## Part 7: Building Selection Flow - Complete Example

### Example Scenario: 10 Buildings, Decide Which Get DH

**Buildings**:
```
B001: supply_type_hs=DHN,  QH_sys=50 MWh/yr  ✓ has demand
B002: supply_type_hs=DHN,  QH_sys=0 MWh/yr   ✓ in supply.csv
B003: supply_type_hs=BUILDING, QH_sys=30    ✗ building-scale
B004: supply_type_hs=DHN,  QH_sys=20        ✓ has demand  
B005: supply_type_hs=DHN,  QH_sys=0         ✓ in supply.csv
B006-B010: supply_type_hs=BUILDING          ✗ building-scale
```

### Scenario A: overwrite-supply-settings=False (Standard Mode)

**Step 1**: Read supply.csv
```
→ Buildings with DHN: [B001, B002, B004, B005]
```

**Step 2**: Apply consider-only-buildings-with-demand filter
```
→ Buildings with >0 demand: [B001, B004]
→ Final: [B001, B004]
```

**Result**: Network connects B001 and B004

### Scenario B: overwrite-supply-settings=True, connected-buildings=blank

**Step 1**: Use all zone buildings
```
→ All buildings: [B001-B010]
```

**Step 2**: Apply consider-only-buildings-with-demand filter  
```
→ Buildings with >0 demand: [B001, B003, B004]
→ Final: [B001, B003, B004]
```

**Result**: Network connects B001, B003, B004

### Scenario C: overwrite-supply-settings=True, connected-buildings=[B001, B002, B005]

**Step 1**: Use connected-buildings
```
→ User-specified: [B001, B002, B005]
```

**Step 2**: Apply consider-only-buildings-with-demand filter
```
→ Buildings with >0 demand: [B001]
→ Final: [B001]
```

**Result**: Network connects only B001 (B002 and B005 have no demand, so excluded)

---

## Part 8: Plant Node Creation

### 8A. Anchor Building Selection

**Location**: `/cea/technologies/network_layout/main.py` lines 787-813

**Logic**:
```python
if plant_building parameter is specified:
    plant_buildings = parse_comma_separated_input(plant_building)
    validate_each_building_exists_in_zone()
    # Can be ANY building in zone, not just connected buildings
else:
    # Auto-select: building with highest demand
    plant_buildings = [building_with_max_demand(connected_buildings)]
```

**Cap**: Maximum 3 plant buildings per network type

### 8B. Plant Node Placement

**Location**: `/cea/technologies/network_layout/plant_node_operations.py::add_plant_close_to_anchor()`

**Steps**:
1. Find anchor building in network nodes
2. Find closest NONE node (junction)
3. Create new PLANT node offset by (1, 1) meters from junction
4. Create edge connecting PLANT to junction
5. All coordinates normalized to 6 decimal places
6. PLANT node marked with service configuration (PLANT_hs_ww, etc.)

**Result**: Separate PLANT node, not the building node itself

---

## Part 9: Network Layout Files Structure

### Output File Organization

**Network Layout Phase Outputs**:
```
scenario/outputs/
└─ thermal_networks/
   └─ {network_name}/          # User-specified network name (e.g., "baseline-2025")
      ├─ DH/                   # District heating (created if DH in include-services)
      │  ├─ nodes.shp          # DH-specific nodes (has PLANT, CONSUMER for DH)
      │  ├─ nodes.dbf
      │  ├─ nodes.shx
      │  └─ ...
      ├─ DC/                   # District cooling (created if DC in include-services)
      │  ├─ nodes.shp
      │  └─ ...
      └─ layout.shp            # Combined edges for all networks (DH + DC)
```

### Node Shapefile Columns

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| name | String | NODE0, NODE1, PLANT001 | Unique node identifier |
| type | String | CONSUMER, NONE, PLANT | Node role in network |
| building | String | B001, NONE | Building name or "NONE" |
| geometry | Point | (x, y) | Coordinate in projected CRS |

### Edge Shapefile Columns

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| name | String | PIPE0, PIPE1 | Unique pipe identifier |
| geometry | LineString | [(x1,y1), (x2,y2)] | Pipe route |
| weight | Float | 150.5 | Length in meters |
| pipe_DN | Integer | 150 | Nominal diameter (mm) |
| type_mat | String | T1 | Pipe material type |

---

## Part 10: Service Temperature Implications

### Temperature Selection by Service Configuration

**Space Heating First** (itemised-dh-services=[space_heating, domestic_hot_water]):
- Network supply temp: Set for space heating (e.g., 35°C for LTDH, 50°C for mid-temp)
- DHW handling: Local booster elevates supply to 60°C for DHW systems
- Plant type: `PLANT_hs_ww`
- Use case: Low-temperature district heating networks
- Tradeoff: Booster cost for DHW vs. network efficiency

**DHW First** (itemised-dh-services=[domestic_hot_water, space_heating]):
- Network supply temp: Set for DHW (60°C minimum)
- Space heating handling: Direct supply from network
- Plant type: `PLANT_ww_hs`
- Use case: High-demand DHW areas or mixed heating systems
- Tradeoff: Higher network losses for space heating vs. no booster

**Space Heating Only** (itemised-dh-services=[space_heating]):
- Network supply temp: For space heating only
- DHW: Provided by building-level systems (boiler, heat pump, etc.)
- Plant type: `PLANT_hs`
- No thermal network for DHW

**DHW Only** (itemised-dh-services=[domestic_hot_water]):
- Network supply temp: For DHW only (60°C)
- Space heating: Provided by building-level systems
- Plant type: `PLANT_ww`
- No thermal network for space heating

---

## Part 11: Key Data Dependencies

### Minimum Required Files for Network Layout Generation

1. **zone.shp** - Building geometry (footprints)
   - Columns: name, geometry
   - Used for: Building centroid extraction

2. **street_network.shp** - Street network
   - Columns: geometry (LineString)
   - Used for: Connectivity potential graph

3. **supply.csv** - Building supply systems (if overwrite-supply-settings=False)
   - Columns: name, supply_type_hs, supply_type_cs
   - Used for: Building selection (via assembly mapping)

4. **Assemblies databases** - Assembly definitions
   - Files: assemblies_supply_heating.csv, assemblies_supply_cooling.csv
   - Used for: Map supply codes to DISTRICT/BUILDING scale

5. **total_demand.csv** - Building heating/cooling demands (if consider-only-buildings-with-demand=True)
   - Columns: name, QH_sys_MWhyr, QC_sys_MWhyr
   - Used for: Filter buildings by demand, select plant anchors

### Minimum Required Files for Thermal Network Simulation

1. **DH/nodes.shp** or **DC/nodes.shp** - Network nodes
   - Created by network layout phase
   - Used for: Node list, plant type, building mapping

2. **layout.shp** - Network edges
   - Created by network layout phase
   - Used for: Pipe connectivity, routing

3. **Demand results** - Building-level hourly demands
   - Location: `scenario/outputs/demand/`
   - Used for: Heating/cooling loads at each building

4. **Weather file** - Weather data
   - Used for: Ground temperature, ambient conditions

---

## Part 12: Critical Data Flow Points

### Point 1: Building Selection Determination (Network Layout Phase)

```
Config Parameters:
  - overwrite_supply_settings (True/False)
  - connected_buildings (List or blank)
  - consider_only_buildings_with_demand (True/False)
  
  ↓
  
Determination in main.py::auto_layout_network() lines 653-773:
  - If overwrite=True:
      - If connected_buildings non-empty: use as list
      - If connected_buildings blank: use all zone buildings
  - If overwrite=False:
      - Read supply.csv
      - Map codes to scale via assemblies
      - Use buildings with scale=DISTRICT
      
  ↓
  
Apply demand filter (if enabled):
  - Read total_demand.csv
  - Keep only buildings with QH_sys > 0 (DH) or QC_sys > 0 (DC)
  
  ↓
  
Output: list_district_scale_buildings
```

### Point 2: Plant Node Type Creation (Network Layout Phase)

```
Config Parameters:
  - itemised_dh_services (e.g., [space_heating, domestic_hot_water])
  - heating_plant_building or cooling_plant_building
  
  ↓
  
Plant node type determination in plant_node_operations.py::
  get_plant_type_from_services(itemised_dh_services, network_type)
  
  ↓
  
Result: PLANT type string (e.g., PLANT_hs_ww, PLANT_ww_hs, PLANT)
  - Stored in nodes.shp type column
  - Used by thermal simulation to determine service config
```

### Point 3: Service Configuration Reading (Thermal Simulation Phase)

```
Network nodes.shp with PLANT type (e.g., PLANT_hs_ww)
  ↓
  
Read by thermal_network.py::get_thermal_network_from_shapefile() lines 241-262
  
  ↓
  
Extract via plant_node_operations.py::get_services_from_plant_type()
  - Decodes 'PLANT_hs_ww' → ['space_heating', 'domestic_hot_water']
  
  ↓
  
Store in ThermalNetwork.itemised_dh_services
  
  ↓
  
Pass to:
  - calculate_minimum_network_temperature() - Determines supply temp
  - booster calculations - Determines if booster needed
  - substation matrix - Determines HEX design
```

---

## Part 13: Refactoring Considerations

### Current Limitations

1. **Supply.csv underutilized**
   - Currently only extracts building list
   - Ignores service type columns (supply_type_hs, supply_type_cs)
   - No per-building service configuration

2. **Service configuration is global**
   - Single itemised_dh_services applies to all buildings
   - No per-building override (e.g., "B001 needs DHW, B002 doesn't")

3. **Plant placement is after network generation**
   - PLANT nodes created as post-processing
   - Cannot influence Steiner tree algorithm
   - Limited to simple anchor-based placement

4. **Demand filtering is separate from building selection**
   - Can result in disconnected networks if buildings have no demand
   - Consider-only-buildings-with-demand sometimes needs overriding

### Suggested Refactoring Goals

1. **Phase 1: Enhance supply.csv usage**
   - Read supply_type_hs and supply_type_cs columns
   - Allow per-building service specification
   - Store in nodes.shp attributes for later reference

2. **Phase 2: Separate DHW and space heating networks**
   - Generate separate networks per service
   - Allow different plant locations per service
   - Independent routing optimization

3. **Phase 3: Pre-placement plant influence**
   - Include PLANT locations in Steiner tree algorithm
   - Ensure optimal plant-to-building distances
   - Support multi-plant topologies

4. **Phase 4: Building-level service configuration**
   - Allow supply.csv to specify per-building services
   - Buildings can be connected to subset of services
   - More flexible what-if scenarios

---

## Part 14: Key Files Reference

### Main Scripts
- `/cea/technologies/network_layout/main.py` - Network layout generation entry point
- `/cea/technologies/thermal_network/thermal_network.py` - Thermal network simulation entry point
- `/cea/technologies/thermal_network/simplified_thermal_network.py` - Simplified thermal model

### Building Selection
- `/cea/technologies/network_layout/main.py::auto_layout_network()` - Main selection logic
- `/cea/technologies/network_layout/main.py::get_buildings_from_supply_csv()` - Supply.csv reading
- `/cea/technologies/network_layout/main.py::get_buildings_with_demand()` - Demand filtering

### Network Generation
- `/cea/technologies/network_layout/connectivity_potential.py` - Street network graph
- `/cea/technologies/network_layout/steiner_spanning_tree.py` - Steiner tree optimization
- `/cea/technologies/network_layout/substations_location.py` - Building centroid calculation

### Plant Node Management
- `/cea/technologies/network_layout/plant_node_operations.py` - Plant creation and service encoding
- `/cea/technologies/building_heating_booster.py` - Booster logic for DHW

### Service Configuration
- `/cea/technologies/thermal_network/thermal_network.py::get_thermal_network_from_shapefile()` - Service reading
- `/cea/technologies/thermal_network/simplified_thermal_network.py::calculate_minimum_network_temperature()` - Service-based temp calc

### Configuration
- `/cea/default.config` - All configuration parameters
- `/cea/inputlocator.py` - File path resolution

### Databases
- `/cea/databases/assemblies_supply_heating.csv` - DH system scale mapping
- `/cea/databases/assemblies_supply_cooling.csv` - DC system scale mapping

---

## Summary

The CEA thermal network system implements a two-phase architecture:

1. **Layout Phase** determines which buildings are connected based on configuration parameters, supply.csv, and demand filtering
2. **Simulation Phase** simulates heat flow in the pre-determined network, using service configuration encoded in PLANT node types

The refactoring toward separating DHW and space heating services should focus on:
- Enhanced supply.csv utilization for per-building service specification
- Separate network generation per service
- Service-aware plant placement
- Building-level configuration in nodes.shp

All building selection happens at layout generation time, making it critical to have the configuration parameters correctly set before running the network layout script.
