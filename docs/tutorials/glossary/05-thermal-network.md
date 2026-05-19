# Thermal Network Design

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **25**

---

## Files

- [`get_network_energy_pumping_requirements_file`](#get_network_energy_pumping_requirements_file)
- [`get_network_layout_edges_shapefile`](#get_network_layout_edges_shapefile)
- [`get_network_layout_nodes_shapefile`](#get_network_layout_nodes_shapefile)
- [`get_network_linear_pressure_drop_edges`](#get_network_linear_pressure_drop_edges)
- [`get_network_linear_thermal_loss_edges_file`](#get_network_linear_thermal_loss_edges_file)
- [`get_network_pressure_at_nodes`](#get_network_pressure_at_nodes)
- [`get_network_temperature_plant`](#get_network_temperature_plant)
- [`get_network_temperature_return_nodes_file`](#get_network_temperature_return_nodes_file)
- [`get_network_temperature_supply_nodes_file`](#get_network_temperature_supply_nodes_file)
- [`get_network_thermal_loss_edges_file`](#get_network_thermal_loss_edges_file)
- [`get_network_total_pressure_drop_file`](#get_network_total_pressure_drop_file)
- [`get_network_total_thermal_loss_file`](#get_network_total_thermal_loss_file)
- [`get_nominal_edge_mass_flow_csv_file`](#get_nominal_edge_mass_flow_csv_file)
- [`get_nominal_node_mass_flow_csv_file`](#get_nominal_node_mass_flow_csv_file)
- [`get_thermal_demand_csv_file`](#get_thermal_demand_csv_file)
- [`get_thermal_network_edge_list_file`](#get_thermal_network_edge_list_file)
- [`get_thermal_network_edge_node_matrix_file`](#get_thermal_network_edge_node_matrix_file)
- [`get_thermal_network_layout_massflow_edges_file`](#get_thermal_network_layout_massflow_edges_file)
- [`get_thermal_network_layout_massflow_nodes_file`](#get_thermal_network_layout_massflow_nodes_file)
- [`get_thermal_network_node_types_csv_file`](#get_thermal_network_node_types_csv_file)
- [`get_thermal_network_plant_heat_requirement_file`](#get_thermal_network_plant_heat_requirement_file)
- [`get_thermal_network_pressure_losses_edges_file`](#get_thermal_network_pressure_losses_edges_file)
- [`get_thermal_network_substation_ploss_file`](#get_thermal_network_substation_ploss_file)
- [`get_thermal_network_substation_results_file`](#get_thermal_network_substation_results_file)
- [`get_thermal_network_velocity_edges_file`](#get_thermal_network_velocity_edges_file)

---

### `get_network_energy_pumping_requirements_file`

- **Path**: `outputs/data/thermal-network/DH__plant_pumping_load_kW.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `pressure_loss_return_kW` | pumping electricity required to overcome pressure losses in the return network | float | `[kWh]` | {0.0...n} |
| `pressure_loss_substations_kW` | pumping electricity required to overcome pressure losses in the substations | float | `[kWh]` | {0.0...n} |
| `pressure_loss_supply_kW` | pumping electricity required to overcome pressure losses in the supply network | float | `[kWh]` | {0.0...n} |
| `pressure_loss_total_kW` | pumping electricity required to overcome pressure losses in the entire network | float | `[kWh]` | {0.0...n} |

---

### `get_network_layout_edges_shapefile`

- **Path**: `outputs/data/thermal-network/DH/edges.shp`
- **File type**: `shp`
- **Created by**: `network_layout`
- **Used by**: `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `geometry` | Geometry | LineString | `NA` |  |
| `length_m` | length of this edge | float | `[m]` | {0.0...n} |
| `name` | Unique network pipe ID. | string | `NA` | alphanumeric |
| `pipe_DN` | Classifies nominal pipe diameters (DN) into typical bins. | string | `NA` | alphanumeric |
| `type_mat` | Material type | string | `NA` | alphanumeric |

---

### `get_network_layout_nodes_shapefile`

- **Path**: `outputs/data/thermal-network/DH/nodes.shp`
- **File type**: `shp`
- **Created by**: `network_layout`
- **Used by**: `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Building` | Unique building ID. e.g. "B01" | string | `NA` | alphanumeric |
| `geometry` | Geometry | Point | `NA` |  |
| `name` | Unique node ID. e.g. "NODE1" | string | `NA` | alphanumeric |
| `Type` | Type of node. | string | `NA` | {PLANT, CONSUMER, NONE} |

---

### `get_network_linear_pressure_drop_edges`

- **Path**: `outputs/data/thermal-network/DH__linear_pressure_drop_edges_Paperm.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `PIPE0` | linear pressure drop in this pipe section | float | `[Pa/m]` | {0.0...n} |

---

### `get_network_linear_thermal_loss_edges_file`

- **Path**: `outputs/data/thermal-network/DH__linear_thermal_loss_edges_Wperm.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `PIPE0` | linear thermal losses in this pipe section | float | `[Wh/m]` | {0.0...n} |

---

### `get_network_pressure_at_nodes`

- **Path**: `outputs/data/thermal-network/DH__pressure_at_nodes_Pa.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `NODE0` | pressure at this node | float | `[Pa]` | {0.0...n} |

---

### `get_network_temperature_plant`

- **Path**: `outputs/data/thermal-network/DH__temperature_plant_K.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `temperature_return_K` | Plant return temperature at each time step | float | `[C]` | {0.0...n} |
| `temperature_supply_K` | Plant supply temperature at each time step | float | `[C]` | {0.0...n} |

---

### `get_network_temperature_return_nodes_file`

- **Path**: `outputs/data/thermal-network/DH__temperature_return_nodes_K.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `NODE0` | Return temperature at node NODE0 (outlet temperature of NODE0) at each time step | float | `[C]` | {0.0...n} |

---

### `get_network_temperature_supply_nodes_file`

- **Path**: `outputs/data/thermal-network/DH__temperature_supply_nodes_K.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `NODE0` | Supply temperature at node NODE0 (inlet temperature of NODE0) at each time step | float | `[C]` | {0.0...n} |

---

### `get_network_thermal_loss_edges_file`

- **Path**: `outputs/data/thermal-network/DH__thermal_loss_edges_kW.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `PIPE0` | Thermal losses along pipe PIPE0 at each time step | float | `[kWh]` | {0.0...n} |

---

### `get_network_total_pressure_drop_file`

- **Path**: `outputs/data/thermal-network/DH__plant_pumping_pressure_loss_Pa.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `pressure_loss_return_Pa` | Pressure losses in the return network at each time step | float | `[Pa]` | {0.0...n} |
| `pressure_loss_substations_Pa` | Pressure losses in all substations at each time step | float | `[Pa]` | {0.0...n} |
| `pressure_loss_supply_Pa` | Pressure losses in the supply network at each time step | float | `[Pa]` | {0.0...n} |
| `pressure_loss_total_Pa` | Total pressure losses in the entire thermal network at each time step | float | `[Pa]` | {0.0...n} |

---

### `get_network_total_thermal_loss_file`

- **Path**: `outputs/data/thermal-network/DH__total_thermal_loss_edges_kW.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `thermal_loss_return_kW` | Thermal losses in the supply network at each time step | float | `[kWh]` | {0.0...n} |
| `thermal_loss_supply_kW` | Thermal losses in the return network at each time step | float | `[kWh]` | {0.0...n} |
| `thermal_loss_total_kW` | Thermal losses in the entire thermal network at each time step | float | `[kWh]` | {0.0...n} |

---

### `get_nominal_edge_mass_flow_csv_file`

- **Path**: `outputs/data/thermal-network/Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `PIPE0` | Mass flow rate in pipe PIPE0 at design operating conditions | float | `[kg/s]` | {0.0...n} |

---

### `get_nominal_node_mass_flow_csv_file`

- **Path**: `outputs/data/thermal-network/Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `NODE0` | Mass flow rate in node NODE0 at design operating conditions | float | `[kg/s]` | {0.0...n} |

---

### `get_thermal_demand_csv_file`

- **Path**: `outputs/data/thermal-network/DH__thermal_demand_per_building_W.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `B01` | Thermal demand for building B01 at each simulation time step | float | `[Wh]` | {0.0...n} |

---

### `get_thermal_network_edge_list_file`

- **Path**: `outputs/data/thermal-network/DH__metadata_edges.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `D_int_m` | Internal pipe diameter for the nominal diameter | float | `[m]` | {0.0...n} |
| `length_m` | Length of each pipe in the network | float | `[m]` | {0.0...n} |
| `name` | Unique network pipe ID. | string | `NA` | alphanumeric |
| `pipe_DN` | Nominal pipe diameter (e.g. DN100 refers to pipes of approx. 100 mm in diameter) | int | `[-]` | {0...n} |
| `type_mat` | Material of the pipes | string | `NA` | alphanumeric |

---

### `get_thermal_network_edge_node_matrix_file`

- **Path**: `outputs/data/thermal-network/{network_type}__EdgeNode.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `NODE` | Names of the nodes in the network | string | `NA` | alphanumeric |
| `PIPE0` | Indicates the direction of flow of PIPE0 with respect to each node NODEn: if equal to PIPE0 and NODEn are not connected / if equal to 1 PIPE0 enters NODEn / if equal to -1 PIPE0 leaves NODEn | int | `[-]` | {-1, 0, 1} |

---

### `get_thermal_network_layout_massflow_edges_file`

- **Path**: `outputs/data/thermal-network/DH__massflow_edges_kgs.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `PIPE0` | Mass flow rate in pipe PIPE0 at each time step | float | `[kg/s]` | {0.0...n} |

---

### `get_thermal_network_layout_massflow_nodes_file`

- **Path**: `outputs/data/thermal-network/DH__massflow_nodes_kgs.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `NODE0` | Mass flow rate in node NODE0 at each time step | float | `[kg/s]` | {0.0...n} |

---

### `get_thermal_network_node_types_csv_file`

- **Path**: `outputs/data/thermal-network/DH__metadata_nodes.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Building` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `name` | Unique network node ID. | string | `NA` | alphanumeric |
| `Type` | Type of node: "PLANT" / "CONSUMER" / "NONE" (if it is neither) | string | `NA` | alphanumeric |

---

### `get_thermal_network_plant_heat_requirement_file`

- **Path**: `outputs/data/thermal-network/DH__plant_thermal_load_kW.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `thermal_load_kW` | Thermal load supplied by the plant at each time step | float | `[kWh]` | {0.0...n} |

---

### `get_thermal_network_pressure_losses_edges_file`

- **Path**: `outputs/data/thermal-network/DH__pressure_losses_edges_kW.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `PIPE0` | Pressure losses at pipe PIPE0 at each time step | float | `[kWh]` | {0.0...n} |

---

### `get_thermal_network_substation_ploss_file`

- **Path**: `outputs/data/thermal-network/DH__pumping_load_due_to_substations_kW.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `B01` | Pumping load at building substation B01 for each timestep | float | `[kWh]` | {0.0...n} |

---

### `get_thermal_network_substation_results_file`

- **Path**: `outputs/data/thermal-network/DH/ww_only/DH_ww_only_substation_B001.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `date` | Date and time in hourly intervals | date | `NA` | YYYY-MM-DD |
| `HEX_cdata_area_m2` | Heat exchanger area for data center cooling (DC only) | float | `[m2]` | {0.0...n} |
| `HEX_cre_area_m2` | Heat exchanger area for refrigeration (DC only) | float | `[m2]` | {0.0...n} |
| `HEX_cs_area_m2` | Heat exchanger area for space cooling (DC only) | float | `[m2]` | {0.0...n} |
| `HEX_hs_area_m2` | Heat exchanger area for space heating (DH only) | float | `[m2]` | {0.0...n} |
| `HEX_ww_area_m2` | Heat exchanger area for domestic hot water (DH only) | float | `[m2]` | {0.0...n} |
| `mdot_DC_result_kgpers` | Substation flow rate on the DC side (DC only) | float | `[kg/s]` | {0.0...n} |
| `mdot_DH_result_kgpers` | Substation flow rate on the DH side (DH only) | float | `[kg/s]` | {0.0...n} |
| `Qcdata_dc_W` | Cooling from district cooling for data center (DC only) | float | `[W]` | {0.0...n} |
| `Qcre_dc_W` | Cooling from district cooling for refrigeration (DC only) | float | `[W]` | {0.0...n} |
| `Qcs_dc_W` | Cooling from district cooling for space cooling (DC only) | float | `[W]` | {0.0...n} |
| `Qhs_booster_W` | Heat from local booster for space heating (DH only, zero when district heating temperature is sufficient) | float | `[W]` | {0.0...n} |
| `Qhs_dh_W` | Heat from district heating for space heating (DH only, may be less than total if booster is used) | float | `[W]` | {0.0...n} |
| `Qww_booster_W` | Heat from local booster for domestic hot water (DH only, zero when district heating temperature is sufficient) | float | `[W]` | {0.0...n} |
| `Qww_dh_W` | Heat from district heating for domestic hot water (DH only, may be less than total if booster is used) | float | `[W]` | {0.0...n} |
| `T_return_DC_result_C` | Substation return temperature of the district cooling network (DC only) | float | `[C]` | {-273.15...n} |
| `T_return_DH_result_C` | Substation return temperature of the district heating network (DH only) | float | `[C]` | {-273.15...n} |
| `T_supply_DC_result_C` | Substation supply temperature of the district cooling network (DC only) | float | `[C]` | {-273.15...n} |
| `T_supply_DH_result_C` | Substation supply temperature of the district heating network (DH only) | float | `[C]` | {-273.15...n} |
| `T_target_dhw_C` | Building-side target supply temperature for domestic hot water (from HVAC assembly, non-zero only when booster is active) | float | `[C]` | {0.0...n} |
| `T_target_hs_C` | Building-side target supply temperature for space heating (from HVAC assembly, non-zero only when booster is active) | float | `[C]` | {0.0...n} |

---

### `get_thermal_network_velocity_edges_file`

- **Path**: `outputs/data/thermal-network/DH__velocity_edges_mpers.csv`
- **File type**: `csv`
- **Created by**: `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `PIPE0` | Flow velocity of heating/cooling medium in pipe PIPE0 | float | `[m/s]` | {0.0...n} |

---

[← Energy Demand Forecasting](04-demand-forecasting.md) | [Glossary index](index.md) | [Life Cycle Analysis (BETA) →](06-life-cycle-analysis.md)
