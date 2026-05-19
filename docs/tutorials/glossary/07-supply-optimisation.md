# Energy Supply System Optimisation

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **35**

---

## Files

- [`get_new_optimization_debugging_fitness_tracker_file`](#get_new_optimization_debugging_fitness_tracker_file)
- [`get_new_optimization_debugging_network_tracker_file`](#get_new_optimization_debugging_network_tracker_file)
- [`get_new_optimization_debugging_supply_system_tracker_file`](#get_new_optimization_debugging_supply_system_tracker_file)
- [`get_new_optimization_detailed_network_performance_file`](#get_new_optimization_detailed_network_performance_file)
- [`get_new_optimization_optimal_network_layout_file`](#get_new_optimization_optimal_network_layout_file)
- [`get_new_optimization_optimal_supply_system_file`](#get_new_optimization_optimal_supply_system_file)
- [`get_new_optimization_optimal_supply_systems_summary_file`](#get_new_optimization_optimal_supply_systems_summary_file)
- [`get_new_optimization_supply_systems_annual_breakdown_file`](#get_new_optimization_supply_systems_annual_breakdown_file)
- [`get_new_optimization_supply_systems_detailed_operation_file`](#get_new_optimization_supply_systems_detailed_operation_file)
- [`get_optimization_building_scale_cooling_capacity`](#get_optimization_building_scale_cooling_capacity)
- [`get_optimization_building_scale_heating_capacity`](#get_optimization_building_scale_heating_capacity)
- [`get_optimization_checkpoint`](#get_optimization_checkpoint)
- [`get_optimization_decentralized_folder_building_result_cooling`](#get_optimization_decentralized_folder_building_result_cooling)
- [`get_optimization_decentralized_folder_building_result_cooling_activation`](#get_optimization_decentralized_folder_building_result_cooling_activation)
- [`get_optimization_decentralized_folder_building_result_heating`](#get_optimization_decentralized_folder_building_result_heating)
- [`get_optimization_decentralized_folder_building_result_heating_activation`](#get_optimization_decentralized_folder_building_result_heating_activation)
- [`get_optimization_district_scale_cooling_capacity`](#get_optimization_district_scale_cooling_capacity)
- [`get_optimization_district_scale_electricity_capacity`](#get_optimization_district_scale_electricity_capacity)
- [`get_optimization_district_scale_heating_capacity`](#get_optimization_district_scale_heating_capacity)
- [`get_optimization_generation_building_scale_performance`](#get_optimization_generation_building_scale_performance)
- [`get_optimization_generation_district_scale_performance`](#get_optimization_generation_district_scale_performance)
- [`get_optimization_generation_total_performance`](#get_optimization_generation_total_performance)
- [`get_optimization_generation_total_performance_pareto`](#get_optimization_generation_total_performance_pareto)
- [`get_optimization_individuals_in_generation`](#get_optimization_individuals_in_generation)
- [`get_optimization_network_results_summary`](#get_optimization_network_results_summary)
- [`get_optimization_slave_building_connectivity`](#get_optimization_slave_building_connectivity)
- [`get_optimization_slave_building_scale_performance`](#get_optimization_slave_building_scale_performance)
- [`get_optimization_slave_cooling_activation_pattern`](#get_optimization_slave_cooling_activation_pattern)
- [`get_optimization_slave_district_scale_performance`](#get_optimization_slave_district_scale_performance)
- [`get_optimization_slave_electricity_activation_pattern`](#get_optimization_slave_electricity_activation_pattern)
- [`get_optimization_slave_electricity_requirements_data`](#get_optimization_slave_electricity_requirements_data)
- [`get_optimization_slave_heating_activation_pattern`](#get_optimization_slave_heating_activation_pattern)
- [`get_optimization_slave_total_performance`](#get_optimization_slave_total_performance)
- [`get_optimization_substations_results_file`](#get_optimization_substations_results_file)
- [`get_optimization_substations_total_file`](#get_optimization_substations_total_file)

---

### `get_new_optimization_debugging_fitness_tracker_file`

- **Path**: `outputs/data/optimization_new/debugging/fitness_tracker.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `anthropogenic_heat` | Annual anthropogenic heat emissions from the district energy system | float | `[kWh]` | {0.0...n} |
| `Connectivity` | String codifying the connectivity vector associated to the tested individual | string | `[-]` | alphanumeric |
| `cost` | Annualised cost of the supply systems and networks associated to the tested individual. | float | `[$USD(2015)]` | {0.0...n} |
| `Front` | Order of the non-dominated front that the solution is a part of | int | `[-]` | {0...n} |
| `Generation` | Index of the generation, i.e. iteration of the genetic algorithm | int | `[-]` | {0...n} |
| `GHG_emissions` | Annual green house gas emissions for the operation of the district energy system. | float | `[kg CO2-eq]` | {0.0...n} |
| `Ind_Code` | Unique code for the tested individual (combination of connectivity- and capacity-indicator-vectors) | int | `[-]` | {0...n} |
| `SupSys_Combination` | Index specifying the supply system associated with the tested individual | int | `[-]` | {0...n} |
| `system_energy_demand` | Annual energy demand of the district energy system (all energy carriers combined). | float | `[kWh]` | {0.0...n} |

---

### `get_new_optimization_debugging_network_tracker_file`

- **Path**: `outputs/data/optimization_new/debugging/network_tracker.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `BXXXX` | Marker denoting if building 'BXXXX' is connected to the given network. | string | `[-]` | alphanumeric |
| `Connectivity` | String codifying the connectivity vector associated to the tested individual | string | `[-]` | alphanumeric |
| `Front` | Order of the non-dominated front that the solution is a part of | int | `[-]` | {0...n} |
| `Generation` | Index of the generation, i.e. iteration of the genetic algorithm | int | `[-]` | {0...n} |
| `Ind_Code` | Unique code for the tested individual (combination of connectivity- and capacity-indicator-vectors) | int | `[-]` | {0...n} |
| `Network` | Identifier of the network in the tested district energy system | string | `[-]` | alphanumeric |
| `p_XXX` | Maximum capacity of the primary (i.e. heating/cooling) component 'XXX' in the given network's supply system. | float | `[kW]` | {0.0...n} |
| `s_XXX` | Maximum capacity of the secondary (i.e. supply) component 'XXX' in the given network's supply system. | float | `[kW]` | {0.0...n} |
| `t_XXX` | Maximum capacity of the tertiary (i.e. heat rejection) component 'XXX' in the given network's supply system. | float | `[kW]` | {0.0...n} |

---

### `get_new_optimization_debugging_supply_system_tracker_file`

- **Path**: `outputs/data/optimization_new/debugging/supply_system_tracker.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Connectivity` | String codifying the connectivity vector associated to the tested individual | string | `[-]` | alphanumeric |
| `Generation` | Index of the generation, i.e. iteration of the genetic algorithm | int | `[-]` | {0...n} |
| `Ind_Code` | Unique code for the tested individual (combination of connectivity- and capacity-indicator-vectors) | int | `[-]` | {0...n} |
| `Network` | Identifier of the network in the tested district energy system | string | `[-]` | alphanumeric |
| `p_XXX` | Capacity indicator of the primary (i.e. heating/cooling) component 'XXX' in the given network's supply system. | float | `[-]` | {0.0...1.0} |
| `s_XXX` | Capacity indicator of the secondary (i.e. supply) component 'XXX' in the given network's supply system. | float | `[-]` | {0.0...1.0} |
| `SupSys_Combination` | Index specifying the supply system associated with the tested individual | int | `[-]` | {0...n} |
| `t_XXX` | Capacity indicator of the tertiary (i.e. heat rejection) component 'XXX' in the given network's supply system. | float | `[-]` | {0.0...1.0} |

---

### `get_new_optimization_detailed_network_performance_file`

- **Path**: `outputs/data/optimization_new/DHS_000/Supply_systems_operation_details/network_performance.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Average hourly network losses [kWh]` | Average hourly losses across all pipes of a given network | float | `kWh` | {n...n} |
| `Network cost [USD]` | Total construction cost of a given network | float | `[USD - 2015]` | {0.0...n} |
| `Network length [m]` | Comined length of all pipes in the network | float | `[m]` | {0.0...n} |
| `Std. deviation of hourly network losses [kWh]` | Standard deviation of hourly losses across all pipes of a given network | float | `kWh` | {n...n} |
| `Type` | Type of node (only for Point objects, 'nan' for LineString objects) | string | `NA` | {PLANT, CONSUMER, NONE} |
| `Yearly network losses [kWh]` | Total thermal losses of the network in one year | float | `[kWh]` | {n...n} |

---

### `get_new_optimization_optimal_network_layout_file`

- **Path**: `outputs/data/optimization_new/DHS_000/networks/N0000_layout.geojson`
- **File type**: `geojson`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `building` | Building identifier (only for Point objects that represent a building's connection to the network, 'nan' for LineString objects) | string | `NA` | alphanumeric |
| `D_int_m` | Exact diameter of pipe segment | float | `[m]` | {0.0...n} |
| `end node` | Node (i.e. index of Point corr. object) the pipe segments ends at (only for LineString objects) | string | `NA` | alphanumeric |
| `geometry` | List of Point and LineString objects to describe thermal network pipes, junctions and end-nodes | Point or LineString | `NA` |  |
| `length_m` | Length of pipe segment (only for LineString objects, 'nan' for Point objects) | float | `[m]` | {0.0...n} |
| `pipe_DN` | Nominal diameter of pipe segment (only for LineString objects, 'nan' for Point objects) | float | `[mm]` | {0.0...n} |
| `start node` | Node (i.e. index of Point corr. object) the pipe segments starts from (only for LineString objects) | string | `NA` | alphanumeric |
| `type` | Type of node (only for Point objects, 'nan' for LineString objects) | string | `NA` | {PLANT, CONSUMER, NONE} |
| `type_mat` | Material type code of pipe segment (only for LineString objects, 'nan' for Point objects) | string | `NA` | alphanumeric |

---

### `get_new_optimization_optimal_supply_system_file`

- **Path**: `outputs/data/optimization_new/DHS_000/Supply_systems/N0000_supply_system_structure.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capacity_kW` | Maximum capacity of the component | float | `[kW]` | {0.0...n} |
| `Component_category` | Supply system placement category of the component (primary i.e. cooling/heating-, secondary i.e. supply- or tertiary i.e. heat rejection-components) | string | `NA` | alphanumeric |
| `Component_code` | Code for the exact component-subtype as described in the 'CONVERSION'-database | string | `NA` | alphanumeric |
| `Component_type` | Technical name of the supply system component | string | `NA` | alphanumeric |

---

### `get_new_optimization_optimal_supply_systems_summary_file`

- **Path**: `outputs/data/optimization_new/DHS_000/Supply_systems/Supply_systems_summary.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Cost_USD` | cost of the subsystem, i.e. cost of incoming energy flows + annualised investment cost of components | float | `[USD]` | {0.0...n} |
| `GHG_Emissions_kgCO2` | GHG-emissions of the subsystem | float | `[kg CO2-eq]` | {0.0...n} |
| `Heat_Emissions_kWh` | heat emissions of the subsystem (network or building) | float | `[kWh]` | {0.0...n} |
| `Supply_System` | Identifier of the supply system's consumer, i.e. the subsystem (network or building) | string | `NA` | alphanumeric |
| `System_Energy_Demand_kWh` | system energy demand of the subsystem, i.e. the sum of all incoming energy flows of the system | float | `[kWh]` | {0.0...n} |

---

### `get_new_optimization_supply_systems_annual_breakdown_file`

- **Path**: `outputs/data/optimization_new/DHS_000/Supply_systems_operation_details/N0000_annual_breakdown.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Annual_cost_by_component_USD` | Annualised investment cost of components installed in the network's supply system | float | `[USD]` | {0.0...n} |
| `Annual_energy_carrier_cost_USD` | Yearly cost for a given energy carrier used in the network's supply system | float | `[USD]` | {n...n} |
| `Annual_energy_demand_kWh` | Yearly energy demand for a given energy carrier by the network's supply system | float | `[kWh]` | {n...n} |
| `Annual_GHG_emissions_kgCO2` | Yearly GHG-emissions from the consumption of a given energy carrier used in the network's supply system | float | `[kg CO2-eq]` | {0.0...n} |
| `Annual_heat_rejection_kWh` | Annual quantity of heat of a given type rejected by the network's supply system | float | `[kWh]` | {0.0...n} |

---

### `get_new_optimization_supply_systems_detailed_operation_file`

- **Path**: `outputs/data/optimization_new/DHS_000/Supply_systems_operation_details/N0000_operation.csv`
- **File type**: `csv`
- **Created by**: `optimization_new`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Date` | Time stamp for each day of the year ascending in hour intervals. | date | `NA` | YYYY-MM-DD |
| `GHG_emissions_kgCO2` | Time series of GHG-emissions of the subsystem | float | `[kg CO2-eq]` | {0.0...n} |
| `Heat_rejection_kWh` | Time series of heat emissions of the subsystem (network or building) | float | `[kWh]` | {0.0...n} |
| `System_energy_demand_kWh` | Time series of system energy demand of the subsystem, i.e. incoming energy flows of the system | float | `[kWh]` | {0.0...n} |

---

### `get_optimization_building_scale_cooling_capacity`

- **Path**: `outputs/data/optimization/slave/gen_1/ind_0_building_scale_cooling_capacity.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capacity_ACH_SC_FP_cool_building_scale_W` | Thermal Capacity of Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_ACHHT_FP_cool_building_scale_W` | Thermal Capacity of High-Temperature Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_BaseVCC_AS_cool_building_scale_W` | Thermal Capacity of Base load Vapor Compression Chiller for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_DX_AS_cool_building_scale_W` | Thermal Capacity of Direct Expansion Air-Source for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_VCCHT_AS_cool_building_scale_W` | Thermal Capacity of High-Temperature Vapor Compression Chiller (Air-Source) for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capaticy_ACH_SC_ET_cool_building_scale_W` | Thermal Capacity of Absorption Chiller and Solar Collector (Evacuated Tube)for Decentralized Building | float | `[W]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter | string | `NA` | alphanumeric |

---

### `get_optimization_building_scale_heating_capacity`

- **Path**: `outputs/data/optimization/slave/gen_0/ind_1_building_scale_heating_capacity.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capacity_BaseBoiler_NG_heat_building_scale_W` | Thermal capacity of Base load boiler for Decentralized building | float | `[W]` | {0.0...n} |
| `Capacity_FC_NG_heat_building_scale_W` | Thermal capacity of Fuel Cell for Decentralized building | float | `[W]` | {0.0...n} |
| `Capacity_GS_HP_heat_building_scale_W` | Thermal capacity of ground-source heat pump for Decentralized building | float | `[W]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter | string | `NA` | alphanumeric |

---

### `get_optimization_checkpoint`

- **Path**: `outputs/data/optimization/master/CheckPoint_1`
- **File type**: ``
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `difference_generational_distances` | TODO | TODO | `TODO` |  |
| `generation` | TODO | TODO | `TODO` |  |
| `generational_distances` | TODO | TODO | `TODO` |  |
| `selected_population` | TODO | TODO | `TODO` |  |
| `tested_population` | TODO | TODO | `TODO` |  |

---

### `get_optimization_decentralized_folder_building_result_cooling`

- **Path**: `outputs/data/optimization/decentralized/{building}_{configuration}_cooling.csv`
- **File type**: `csv`
- **Created by**: `decentrlized`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Best configuration` | Index of best configuration simulated | float | `[-]` | {0.0...n} |
| `Capacity_ACH_SC_FP_W` | Thermal Capacity of Absorption Chiller connected to Flat-plate Solar Collector | float | `[W]` | {0.0...n} |
| `Capacity_ACHHT_FP_W` | Thermal Capacity of High Temperature Absorption Chiller connected to Solar Collector (flat Plate) | float | `[W]` | {0.0...n} |
| `Capacity_BaseVCC_AS_W` | Thermal Capacity of Base Vapor compression chiller (air-source) | float | `[W]` | {0.0...n} |
| `Capacity_DX_AS_W` | Thermal Capacity of Direct-Expansion Unit Air-source | float | `[W]` | {0.0...n} |
| `Capacity_VCCHT_AS_W` | Thermal Capacity of High Temperature Vapor compression chiller (air-source) | float | `[W]` | {0.0...n} |
| `Capaticy_ACH_SC_ET_W` | Thermal Capacity of Absorption Chiller connected to Evacuated-Tube Solar Collector | float | `[W]` | {0.0...n} |
| `Capex_a_USD` | Annualized Capital Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_USD` | Total Capital Costs | float | `[USD 2015]` | {0.0...n} |
| `GHG_tonCO2` | Annual Green House Gas Emissions | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `Nominal heating load` | Nominal heat load | float | `[W]` | {0.0...n} |
| `Opex_fixed_USD` | Fixed Annual Operational Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_USD` | Variable Annual Operational Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_USD` | Total Annualized Costs | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_decentralized_folder_building_result_cooling_activation`

- **Path**: `outputs/data/optimization/decentralized/{building}_{configuration}_cooling_activation.csv`
- **File type**: `csv`
- **Created by**: `decentralized`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `E_ACH_req_W` | Electricity requirements of Absorption Chillers | float | `[Wh]` | {0.0...n} |
| `E_BaseVCC_AS_req_W` | Electricity requirements of Vapor Compression Chillers and refrigeration | float | `[Wh]` | {0.0...n} |
| `E_cs_cre_cdata_req_W` | Electricity requirements due to space cooling, servers cooling and refrigeration | float | `[Wh]` | {0.0...n} |
| `E_CT_req_W` | Electricity requirements of Cooling Towers | float | `[Wh]` | {0.0...n} |
| `E_DX_AS_req_W` | Electricity requirements of Air-Source direct expansion chillers | float | `[Wh]` | {0.0...n} |
| `E_SC_ET_req_W` | Electricity requirements of Solar Collectors (evacuated-tubes) | float | `[Wh]` | {0.0...n} |
| `E_SC_FP_req_W` | Electricity requirements of Solar Collectors (flat-plate) | float | `[Wh]` | {0.0...n} |
| `NG_Boiler_req` | Requirements of Natural Gas for Boilers | float | `[Wh]` | {0.0...n} |
| `NG_Burner_req` | Requirements of Natural Gas for Burners | float | `[Wh]` | {0.0...n} |
| `Q_ACH_gen_directload_W` | Thermal energy generated by Absorption chillers | float | `[Wh]` | {0.0...n} |
| `Q_BaseVCC_AS_gen_directload_W` | Thermal energy generated by Air-Source Vapor-compression chillers | float | `[Wh]` | {0.0...n} |
| `Q_Boiler_NG_ACH_W` | Thermal energy generated by Natural gas Boilers to Absorption chillers | float | `[Wh]` | {0.0...n} |
| `Q_Burner_NG_ACH_W` | Thermal energy generated by Natural gas Burners to Absorption chillers | float | `[Wh]` | {0.0...n} |
| `Q_DX_AS_gen_directload_W` | Thermal energy generated by Air-Source direct expansion chillers | float | `[Wh]` | {0.0...n} |
| `Q_SC_ET_ACH_W` | Thermal energy generated by Solar Collectors (evacuated-tubes) to Absorption chillers | float | `[Wh]` | {0.0...n} |
| `Q_SC_FP_ACH_W` | Thermal energy generated by Solar Collectors (flat-plate) to Absorption chillers | float | `[Wh]` | {0.0...n} |

---

### `get_optimization_decentralized_folder_building_result_heating`

- **Path**: `outputs/data/optimization/decentralized/DiscOp_B001_result_heating.csv`
- **File type**: `csv`
- **Created by**: `decentralized`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Best configuration` | Index of best configuration simulated | float | `[-]` | {0.0...n} |
| `Capacity_BaseBoiler_NG_W` | Thermal capacity of Baseload Boiler NG | float | `[-]` | {0.0...n} |
| `Capacity_FC_NG_W` | Thermal Capacity of Fuel Cell NG | float | `[-]` | {0.0...n} |
| `Capacity_GS_HP_W` | Thermal Capacity of Ground Source Heat Pump | float | `[W]` | {0.0...n} |
| `Capex_a_USD` | Annualized Capital Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_USD` | Total Capital Costs | float | `[USD 2015]` | {0.0...n} |
| `GHG_tonCO2` | Annual Green House Gas Emissions | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `Nominal heating load` | Nominal heat load | float | `[W]` | {0.0...n} |
| `Opex_fixed_USD` | Fixed Annual Operational Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_USD` | Variable Annual Operational Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_USD` | Total Annualized Costs | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_decentralized_folder_building_result_heating_activation`

- **Path**: `outputs/data/optimization/decentralized/DiscOp_B001_result_heating_activation.csv`
- **File type**: `csv`
- **Created by**: `decentralized`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `BackupBoiler_Status` | Status of the BackupBoiler (1=on, 0 =off) | int | `[-]` | {0...1} |
| `BG_Boiler_req_W` | Requirements of Bio-gas for Base load Boiler | float | `[Wh]` | {0.0...n} |
| `Boiler_Status` | Status of the Base load Boiler (1=on, 0 =off) | int | `[-]` | {0...1} |
| `E_Fuelcell_gen_export_W` | Electricity generation of fuel cell exported to the grid | float | `[Wh]` | {0.0...n} |
| `E_hs_ww_req_W` | Electricity Requirements for heat pump compressor and auxiliary uses (if required) | float | `[Wh]` | {0.0...n} |
| `Fuelcell_Status` | Status of the fuel cell (1=on, 0 =off) | int | `[-]` | {0...1} |
| `GHP_Status` | Status of the ground-source heat pump (1=on, 0 =off) | int | `[-]` | {0...1} |
| `NG_BackupBoiler_req_W` | Requirements of Natural Gas for Back-up Boiler | float | `[Wh]` | {0.0...n} |
| `NG_Boiler_req_W` | Requirements of Natural Gas for Base load Boiler | float | `[Wh]` | {0.0...n} |
| `NG_FuelCell_req_W` | Requirements of Natural Gas for fuel cell | float | `[Wh]` | {0.0...n} |
| `Q_BackupBoiler_gen_directload_W` | Thermal generation of Back-up Boiler to direct load | float | `[Wh]` | {0.0...n} |
| `Q_Boiler_gen_directload_W` | Thermal generation of Base load Boiler to direct load | float | `[Wh]` | {0.0...n} |
| `Q_Fuelcell_gen_directload_W` | Thermal generation of fuel cell to direct load | float | `[Wh]` | {0.0...n} |
| `Q_GHP_gen_directload_W` | Thermal generation of ground-source heat pump to direct load | float | `[Wh]` | {0.0...n} |

---

### `get_optimization_district_scale_cooling_capacity`

- **Path**: `outputs/data/optimization/slave/gen_1/ind_1_district_scale_cooling_capacity.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capacity_ACH_SC_FP_cool_building_scale_W` | Thermal Capacity of Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_ACHHT_FP_cool_building_scale_W` | Thermal Capacity of High-Temperature Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_BaseVCC_AS_cool_building_scale_W` | Thermal Capacity of Base load Vapor Compression Chiller for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_DX_AS_cool_building_scale_W` | Thermal Capacity of Direct Expansion Air-Source for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capacity_VCCHT_AS_cool_building_scale_W` | Thermal Capacity of High-Temperature Vapor Compression Chiller (Air-Source) for Decentralized Building | float | `[W]` | {0.0...n} |
| `Capaticy_ACH_SC_ET_cool_building_scale_W` | Thermal Capacity of Absorption Chiller and Solar Collector (Evacuated Tube)for Decentralized Building | float | `[W]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter | string | `NA` | alphanumeric |

---

### `get_optimization_district_scale_electricity_capacity`

- **Path**: `outputs/data/optimization/slave/gen_2/ind_0_district_scale_electrical_capacity.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capacity_GRID_el_district_scale_W` | Electrical Capacity Required from the local Grid | float | `[W]` | {0.0...n} |
| `Capacity_PV_el_district_scale_m2` | Area Coverage of PV in central Plant | float | `[m2]` | {0.0...n} |
| `Capacity_PV_el_district_scale_W` | Electrical Capacity of PV in central Plant | float | `[W]` | {0.0...n} |

---

### `get_optimization_district_scale_heating_capacity`

- **Path**: `outputs/data/optimization/slave/gen_0/ind_2_district_scale_heating_capacity.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capacity_BackupBoiler_NG_heat_district_scale_W` | Thermal Capacity of Back-up Boiler - Natural Gas in central plant | float | `[W]` | {0.0...n} |
| `Capacity_BaseBoiler_NG_heat_district_scale_W` | Thermal Capacity of Base Load Boiler - Natural Gas  in central plant | float | `[W]` | {0.0...n} |
| `Capacity_CHP_DB_el_district_scale_W` | Electrical Capacity of CHP Dry-Biomass in central plant | float | `[W]` | {0.0...n} |
| `Capacity_CHP_DB_heat_district_scale_W` | ThermalCapacity of CHP Dry-Biomass in central plant | float | `[W]` | {0.0...n} |
| `Capacity_CHP_NG_el_district_scale_W` | Electrical Capacity of CHP Natural-Gas in central plant | float | `[W]` | {0.0...n} |
| `Capacity_CHP_NG_heat_district_scale_W` | Thermal Capacity of CHP Natural-Gas in central plant | float | `[W]` | {0.0...n} |
| `Capacity_CHP_WB_el_district_scale_W` | Electrical Capacity of CHP Wet-Biomass in central plant | float | `[W]` | {0.0...n} |
| `Capacity_CHP_WB_heat_district_scale_W` | Thermal Capacity of CHP Wet-Biomass in central plant | float | `[W]` | {0.0...n} |
| `Capacity_HP_DS_heat_district_scale_W` | Thermal Capacity of Heat Pump Server-Source in central plant | float | `[W]` | {0.0...n} |
| `Capacity_HP_GS_heat_district_scale_W` | Thermal Capacity of Heat Pump Ground-Source in central plant | float | `[W]` | {0.0...n} |
| `Capacity_HP_SS_heat_district_scale_W` | Thermal Capacity of Heat Pump Sewage-Source in central plant | float | `[W]` | {0.0...n} |
| `Capacity_HP_WS_heat_district_scale_W` | Thermal Capacity of Heat Pump Water-Source in central plant | float | `[W]` | {0.0...n} |
| `Capacity_PeakBoiler_NG_heat_district_scale_W` | Thermal Capacity of Peak Boiler - Natural Gas in central plant | float | `[W]` | {0.0...n} |
| `Capacity_PVT_el_district_scale_W` | Electrical Capacity of PVT Field in central plant | float | `[W]` | {0.0...n} |
| `Capacity_PVT_heat_district_scale_W` | Thermal Capacity of PVT panels in central plant | float | `[W]` | {0.0...n} |
| `Capacity_SC_ET_heat_district_scale_W` | Thermal Capacity of Solar Collectors (Evacuated-tube) in central plant | float | `[W]` | {0.0...n} |
| `Capacity_SC_FP_heat_district_scale_W` | Thermal Capacity of Solar Collectors (Flat-plate) in central plant | float | `[W]` | {0.0...n} |
| `Capacity_SeasonalStorage_WS_heat_district_scale_W` | Thermal Capacity of Seasonal Thermal Storage in central plant | float | `[W]` | {0.0...n} |

---

### `get_optimization_generation_building_scale_performance`

- **Path**: `outputs/data/optimization/slave/gen_2/gen_2_building_scale_performance.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_cooling_building_scale_USD` | Annualized Capital Costs of building-scale systems due to cooling | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_heating_building_scale_USD` | Annualized Capital Costs of building-scale systems due to heating | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_cooling_building_scale_USD` | Total Capital Costs of building-scale systems due to cooling | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_heating_building_scale_USD` | Total Capital Costs of building-scale systems due to heating | float | `[USD 2015]` | {0.0...n} |
| `generation` | No. Generation or Iteration (genetic Algorithm) | int | `[-]` | {0...n} |
| `GHG_cooling_building_scale_tonCO2` | Green House Gas Emissions of building-scale systems due to Cooling | float | `[ton Co2-eq/yr]` | {0.0...n} |
| `GHG_heating_building_scale_tonCO2` | Green House Gas Emissions of building-scale systems due to Heating | float | `[ton Co2-eq/yr]` | {0.0...n} |
| `individual` | No. Individual unique ID | int | `[-]` | {0...n} |
| `individual_name` | Name of  Individual unique ID | string | `NA` | alphanumeric |
| `Opex_fixed_cooling_building_scale_USD` | Fixed Operational Costs of building-scale systems due to cooling | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_heating_building_scale_USD` | Fixed Operational Costs of building-scale systems due to heating | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_cooling_building_scale_USD` | Variable Operational Costs of building-scale systems due to cooling | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_heating_building_scale_USD` | Variable Operational Costs of building-scale systems due to heating | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_generation_district_scale_performance`

- **Path**: `outputs/data/optimization/slave/gen_1/gen_1_district_scale_performance.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_BackupBoiler_NG_district_scale_USD` | Annualized Capital Costs of Back-up Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_BaseBoiler_NG_district_scale_USD` | Annualized Capital Costs of Base Load Boiler Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_CHP_NG_district_scale_USD` | Annualized Capital Costs of CHP Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_DHN_district_scale_USD` | Annualized Capital Costs of District Heating Network | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_Furnace_dry_district_scale_USD` | Annualized Capital Costs of CHP Dry-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_Furnace_wet_district_scale_USD` | Annualized Capital Costs of CHP Wet-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_GHP_district_scale_USD` | Annualized Capital Costs of Ground-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_GRID_district_scale_USD` | Annualized Capital Costs of connection to local electrical grid | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_HP_Lake_district_scale_USD` | Annualized Capital Costs of Lake-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_HP_Server_district_scale_USD` | Annualized Capital Costs of Server-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_HP_Sewage_district_scale_USD` | Annualized Capital Costs of Sewage-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_PeakBoiler_NG_district_scale_USD` | Annualized Capital Costs of Peak Load Boiler Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_PV_district_scale_USD` | Annualized Capital Costs of Photovoltaic Panels in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_PVT_district_scale_USD` | Annualized Capital Costs of PVT Panels in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SC_ET_district_scale_USD` | Annualized Capital Costs of Solar Collectors (evacuated-Tube) in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SC_FP_district_scale_USD` | Annualized Capital Costs of Solar Collectors (Flat-Plate) in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SeasonalStorage_WS_district_scale_USD` | Annualized Capital Costs of Seasonal Thermal Storage in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SubstationsHeating_district_scale_USD` | Annualized Capital Costs of Thermal Substations | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_BackupBoiler_NG_district_scale_USD` | Total Capital Costs of Back-up Boiler Natural Gas in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_BaseBoiler_NG_district_scale_USD` | Total Capital Costs of Base Load Boiler Boiler Natural Gas in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_CHP_NG_district_scale_USD` | Total Capital Costs of CHP Natural Gas in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_DHN_district_scale_USD` | Total Capital Costs of District Heating Network | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_Furnace_dry_district_scale_USD` | Total Capital Costs of CHP Dry-Biomass in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_Furnace_wet_district_scale_USD` | Total Capital Costs of CHP Wet-Biomass in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_GHP_district_scale_USD` | Total Capital Costs of Ground-Source Heat Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_GRID_district_scale_USD` | Total Capital Costs of connection to local electrical grid | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_HP_Lake_district_scale_USD` | Total Capital Costs of Lake-Source Heat Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_HP_Server_district_scale_USD` | Total Capital Costs of Server-Source Heat Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_HP_Sewage_district_scale_USD` | Total Capital Costs of Sewage-Source Heat Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_PeakBoiler_NG_district_scale_USD` | Total Capital Costs of Peak Load Boiler Boiler Natural Gas in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_PV_district_scale_USD` | Total Capital Costs of Photovoltaic Panels in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_PVT_district_scale_USD` | Total Capital Costs of PVT Panels in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SC_ET_district_scale_USD` | Total Capital Costs of Solar Collectors (evacuated-Tube) in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SC_FP_district_scale_USD` | Total Capital Costs of Solar Collectors (Flat-Plate) in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SeasonalStorage_WS_district_scale_USD` | Total Capital Costs of Seasonal Thermal Storage in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SubstationsHeating_district_scale_USD` | Total Capital Costs of Thermal Substations | float | `[USD 2015]` | {0.0...n} |
| `generation` | Number of the Generation or Iteration (Genetic algorithm) | int | `[-]` | {0...n} |
| `GHG_DB_district_scale_tonCO2yr` | Green House Gas Emissions of Dry-Biomass of district-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_GRID_exports_district_scale_tonCO2yr` | Green House Gas Emissions of Exports of Electricity | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_GRID_imports_district_scale_tonCO2yr` | Green House Gas Emissions of Import of Electricity | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_NG_district_scale_tonCO2yr` | Green House Gas Emissions of Natural Gas of district-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_WB_district_scale_tonCO2yr` | Green House Gas Emissions of Wet-Biomass of district-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `individual` | Unique numerical ID of individual | int | `[-]` | {0...n} |
| `individual_name` | Unique alphanumerical ID of individual | string | `NA` | alphanumeric |
| `Opex_fixed_BackupBoiler_NG_district_scale_USD` | Fixed Operation Costs of Back-up Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_BaseBoiler_NG_district_scale_USD` | Fixed Operation Costs of Base Load Boiler Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_CHP_NG_district_scale_USD` | Fixed Operation Costs of CHP Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_DHN_district_scale_USD` | Fixed Operation Costs of District Heating Network | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_Furnace_dry_district_scale_USD` | Fixed Operation Costs of CHP Dry-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_Furnace_wet_district_scale_USD` | Fixed Operation Costs of CHP Wet-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_GHP_district_scale_USD` | Fixed Operation Costs of Ground-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_GRID_district_scale_USD` | Fixed Operation Costs of Electricity in Buildings Connected to Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_HP_Lake_district_scale_USD` | Fixed Operation Costs of Lake-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_HP_Server_district_scale_USD` | Fixed Operation Costs of Server-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_HP_Sewage_district_scale_USD` | Fixed Operation Costs of Sewage-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_PeakBoiler_NG_district_scale_USD` | Fixed Operation Costs of Peak Load Boiler Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_PV_district_scale_USD` | Fixed Operation Costs of Photovoltaic Panels in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_PVT_district_scale_USD` | Fixed Operation Costs of PVT Panels in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SC_ET_district_scale_USD` | Fixed Operation Costs of Solar Collectors (evacuated-Tube) in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SC_FP_district_scale_USD` | Fixed Operation Costs of Solar Collectors (Flat-Plate) in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SeasonalStorage_WS_district_scale_USD` | Fixed Operation Costs of Seasonal Thermal Storage in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SubstationsHeating_district_scale_USD` | Fixed Operation Costs of Thermal Substations | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_DB_district_scale_USD` | Variable Operation Costs due to consumption of Dry-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_GRID_exports_district_scale_USD` | Variable Operation Costs due to electricity exported | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_GRID_imports_district_scale_USD` | Variable Operation Costs due to electricity imported | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_NG_district_scale_USD` | Variable Operation Costs due to consumption of Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_WB_district_scale_USD` | Variable Operation Costs due to consumption of Wet-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_generation_total_performance`

- **Path**: `outputs/data/optimization/slave/gen_2/gen_2_total_performance.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_sys_building_scale_USD` | Annualized Capital Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_sys_district_scale_USD` | Annualized Capital Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_sys_USD` | Annualized Capital Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_sys_building_scale_USD` | Total Capital Costs of building-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_district_scale_USD` | Total Capital Costs of district-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_USD` | Total Capital Costs of district-scale systems and  Decentralized Buildings | float | `[USD 2015]` | {0.0...n} |
| `generation` | No. Generation or Iteration (genetic Algorithm) | int | `[-]` | {0...n} |
| `GHG_sys_building_scale_tonCO2` | Green House Gas Emissions of building-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_district_scale_tonCO2` | Green House Gas Emissions Central Plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_tonCO2` | Green House Gas Emissions of all systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `individual` | No. Individual unique ID | int | `[-]` | {0...n} |
| `individual_name` | Name of  Individual unique ID | string | `NA` | alphanumeric |
| `Opex_a_sys_building_scale_USD` | Operation Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_district_scale_USD` | Operation Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_USD` | Operation Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_building_scale_USD` | Total Anualized Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_district_scale_USD` | Total Anualized Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_USD` | Total Anualized Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_generation_total_performance_pareto`

- **Path**: `outputs/data/optimization/slave/gen_2/gen_2_total_performance_pareto.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: `multi_criteria_analysis`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_sys_building_scale_USD` | Annualized Capital Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_sys_district_scale_USD` | Annualized Capital Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_sys_USD` | Annualized Capital Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_sys_building_scale_USD` | Total Capital Costs of building-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_district_scale_USD` | Total Capital Costs of district-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_USD` | Total Capital Costs of district-scale systems and  Decentralized Buildings | float | `[USD 2015]` | {0.0...n} |
| `generation` | No. Generation or Iteration (genetic Algorithm) | int | `[-]` | {0...n} |
| `GHG_sys_building_scale_tonCO2` | Green House Gas Emissions of building-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_district_scale_tonCO2` | Green House Gas Emissions Central Plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_tonCO2` | Green House Gas Emissions of all systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `individual` | No. Individual unique ID | int | `[-]` | {0...n} |
| `individual_name` | Name of  Individual unique ID | string | `NA` | alphanumeric |
| `Opex_a_sys_building_scale_USD` | Operation Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_district_scale_USD` | Operation Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_USD` | Operation Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_building_scale_USD` | Total Anualized Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_district_scale_USD` | Total Anualized Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_USD` | Total Anualized Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_individuals_in_generation`

- **Path**: `outputs/data/optimization/slave/gen_2/generation_2_individuals.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `B01_DH` | TODO | int | `TODO` | {n...n} |
| `B02_DH` | TODO | int | `TODO` | {n...n} |
| `B03_DH` | TODO | int | `TODO` | {n...n} |
| `B04_DH` | TODO | int | `TODO` | {n...n} |
| `B05_DH` | TODO | int | `TODO` | {n...n} |
| `B06_DH` | TODO | int | `TODO` | {n...n} |
| `B07_DH` | TODO | int | `TODO` | {n...n} |
| `B08_DH` | TODO | int | `TODO` | {n...n} |
| `B09_DH` | TODO | int | `TODO` | {n...n} |
| `DB_Cogen` | TODO | float | `TODO` | {n...n} |
| `DS_HP` | TODO | float | `TODO` | {n...n} |
| `generation` | TODO | int | `TODO` | {n...n} |
| `GS_HP` | TODO | float | `TODO` | {n...n} |
| `individual` | TODO | int | `TODO` | {n...n} |
| `NG_BaseBoiler` | TODO | float | `TODO` | {n...n} |
| `NG_Cogen` | TODO | float | `TODO` | {n...n} |
| `NG_PeakBoiler` | TODO | float | `TODO` | {n...n} |
| `PV` | TODO | float | `TODO` | {n...n} |
| `PVT` | TODO | float | `TODO` | {n...n} |
| `SC_ET` | TODO | float | `TODO` | {n...n} |
| `SC_FP` | TODO | float | `TODO` | {n...n} |
| `SS_HP` | TODO | float | `TODO` | {n...n} |
| `WB_Cogen` | TODO | float | `TODO` | {n...n} |
| `WS_HP` | TODO | float | `TODO` | {n...n} |

---

### `get_optimization_network_results_summary`

- **Path**: `outputs/data/optimization/network/DH_Network_summary_result_0x1be.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `DATE` | Time stamp (hourly) for one year | date | `NA` | YYYY-MM-DD |
| `mcpdata_netw_total_kWperC` | Capacity mass flow rate for server cooling of this network | float | `[kW/C]` | {0.0...n} |
| `mdot_DH_netw_total_kgpers` | Total mass flow rate in this district heating network | float | `[kg/s]` | {0.0...n} |
| `Q_DH_losses_W` | Thermal losses of this district heating network | float | `[Wh]` | {0.0...n} |
| `Q_DHNf_W` | Total thermal demand of district heating network | float | `[Wh]` | {0.0...n} |
| `Qcdata_netw_total_kWh` | Thermal Demand  for server cooling in this network | float | `[kWh]` | {0.0...n} |
| `T_DHNf_re_K` | Average Temperature of return of this district heating network | float | `[K]` | {0.0...n} |
| `T_DHNf_sup_K` | Average Temperature of supply of this district heating network | float | `[K]` | {0.0...n} |

---

### `get_optimization_slave_building_connectivity`

- **Path**: `outputs/data/optimization/slave/gen_2/ind_1_building_connectivity.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `DC_connectivity` | Flag to know if building is connected to District Heating or not | int | `[-]` | {0...1} |
| `DH_connectivity` | Flag to know if building is connected to District Cooling or not | int | `[-]` | {0...1} |
| `name` | Unique building ID. It must start with a letter.) | string | `NA` | alphanumeric |

---

### `get_optimization_slave_building_scale_performance`

- **Path**: `outputs/data/optimization/slave/gen_2/ind_0_buildings_building_scale_performance.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_cooling_building_scale_USD` | Annualized Capital Costs of building-scale systems due to cooling | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_heating_building_scale_USD` | Annualized Capital Costs of building-scale systems due to heating | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_cooling_building_scale_USD` | Total Capital Costs of building-scale systems due to cooling | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_heating_building_scale_USD` | Total Capital Costs of building-scale systems due to heating | float | `[USD 2015]` | {0.0...n} |
| `GHG_cooling_building_scale_tonCO2` | Green House Gas Emissions of building-scale systems due to Cooling | float | `[ton Co2-eq/yr]` | {0.0...n} |
| `GHG_heating_building_scale_tonCO2` | Green House Gas Emissions of building-scale systems due to Heating | float | `[ton Co2-eq/yr]` | {0.0...n} |
| `Opex_fixed_cooling_building_scale_USD` | Fixed Operational Costs of building-scale systems due to cooling | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_heating_building_scale_USD` | Fixed Operational Costs of building-scale systems due to heating | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_cooling_building_scale_USD` | Variable Operational Costs of building-scale systems due to cooling | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_heating_building_scale_USD` | Variable Operational Costs of building-scale systems due to heating | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_slave_cooling_activation_pattern`

- **Path**: `outputs/data/optimization/slave/gen_1/ind_2_Cooling_Activation_Pattern.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capacity_DailyStorage_WS_cool_district_scale_W` | Installed capacity of the short-term thermal storage | float | `[W]` | {0.0...n} |
| `Capex_a_DailyStorage_WS_cool_district_scale_USD` | Annualized capital costs of the short-term thermal storage | float | `[USD-2015/yr]` | {0.0...n} |
| `Capex_total_DailyStorage_WS_cool_district_scale_USD` | Total capital costs of the short-term thermal storage | float | `[USD-2015]` | {0.0...n} |
| `Opex_fixed_DailyStorage_WS_cool_district_scale_USD` | Fixed operational costs of the short-term thermal storage | float | `[USD-2015]` | {0.0...n} |
| `Q_DailyStorage_content_W` | Thermal energy content of the short-term thermal storage | float | `[W]` | {0.0...n} |
| `Q_DailyStorage_gen_directload_W` | Thermal energy supplied from the short-term thermal storage | float | `[W]` | {0.0...n} |

---

### `get_optimization_slave_district_scale_performance`

- **Path**: `outputs/data/optimization/slave/gen_1/ind_2_buildings_district_scale_performance.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_BackupBoiler_NG_district_scale_USD` | Annualized Capital Costs of Back-up Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_BaseBoiler_NG_district_scale_USD` | Annualized Capital Costs of Base load Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_CHP_NG_district_scale_USD` | Annualized Capital Costs of CHP Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_DHN_district_scale_USD` | Annualized Capital Costs of District Heating Network | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_Furnace_dry_district_scale_USD` | Annualized Capital Costs of CHP Dry-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_Furnace_wet_district_scale_USD` | Annualized Capital Costs of CHP Wet-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_GHP_district_scale_USD` | Annualized Capital Costs of Ground-Source Heat-Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_GRID_district_scale_USD` | Annualized Capital Costs of connection to local grid | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_HP_Lake_district_scale_USD` | Annualized Capital Costs of Lake-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_HP_Server_district_scale_USD` | Annualized Capital Costs of Server-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_HP_Sewage_district_scale_USD` | Annualized Capital Costs of Sewage-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_PeakBoiler_NG_district_scale_USD` | Annualized Capital Costs of Peak Boiler in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_PV_district_scale_USD` | Annualized Capital Costs of PV panels | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_PVT_district_scale_USD` | Annualized Capital Costs of PVT panels | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SC_ET_district_scale_USD` | Annualized Capital Costs of Solar collectors (evacuated Tubes) | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SC_FP_district_scale_USD` | Annualized Capital Costs of Solar collectors (Flat-Plate) | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SeasonalStorage_WS_district_scale_USD` | Annualized Capital Costs of Seasonal Thermal Storage in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_SubstationsHeating_district_scale_USD` | Annualized Capital Costs of Heating Substations | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_BackupBoiler_NG_district_scale_USD` | Total Capital Costs of Back-up Boiler Natural Gas in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_BaseBoiler_NG_district_scale_USD` | Total Capital Costs of Base load Boiler Natural Gas in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_CHP_NG_district_scale_USD` | Total Capital Costs of CHP Natural Gas in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_DHN_district_scale_USD` | Total Capital Costs of District Heating Network | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_Furnace_dry_district_scale_USD` | Total Capital Costs of CHP Dry-Biomass in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_Furnace_wet_district_scale_USD` | Total Capital Costs of CHP Wet-Biomass in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_GHP_district_scale_USD` | Total Capital Costs of Ground-Source Heat-Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_GRID_district_scale_USD` | Total Capital Costs of connection to local grid | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_HP_Lake_district_scale_USD` | Total Capital Costs of Lake-Source Heat Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_HP_Server_district_scale_USD` | Total Capital Costs of Server-Source Heat Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_HP_Sewage_district_scale_USD` | Total Capital Costs of Sewage-Source Heat Pump in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_PeakBoiler_NG_district_scale_USD` | Total Capital Costs of Peak Boiler in Central Plant | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_PV_district_scale_USD` | Total Capital Costs of PV panels | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_PVT_district_scale_USD` | Total Capital Costs of PVT panels | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SC_ET_district_scale_USD` | Total Capital Costs of Solar collectors (evacuated Tubes) | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SC_FP_district_scale_USD` | Total Capital Costs of Solar collectors (Flat-Plate) | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SeasonalStorage_WS_district_scale_USD` | Total Capital Costs of Seasonal Thermal Storage | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_SubstationsHeating_district_scale_USD` | Total Capital Costs of Heating Substations | float | `[USD 2015]` | {0.0...n} |
| `GHG_DB_district_scale_tonCO2yr` | Green House Gas Emissions of Dry-Biomass in Central plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_GRID_exports_district_scale_tonCO2yr` | Green House Gas Emissions of  Electricity Exports in Central Plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_GRID_imports_district_scale_tonCO2yr` | Green House Gas Emissions of  Electricity Import in Central Plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_NG_district_scale_tonCO2yr` | Green House Gas Emissions of Natural Gas in Central plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_WB_district_scale_tonCO2yr` | Green House Gas Emissions of Wet-Biomass in Central plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `Opex_fixed_BackupBoiler_NG_district_scale_USD` | Fixed Operation Costs of Back-up Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_BaseBoiler_NG_district_scale_USD` | Fixed Operation Costs of Base load Boiler Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_CHP_NG_district_scale_USD` | Fixed Operation Costs of CHP Natural Gas in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_DHN_district_scale_USD` | Fixed Operation Costs of District Heating Network | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_Furnace_dry_district_scale_USD` | Fixed Operation Costs of CHP Dry-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_Furnace_wet_district_scale_USD` | Fixed Operation Costs of CHP Wet-Biomass in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_GHP_district_scale_USD` | Fixed Operation Costs of Ground-Source Heat-Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_GRID_district_scale_USD` | Fixed Operation Costs of connection to local grid | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_HP_Lake_district_scale_USD` | Fixed Operation Costs of Lake-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_HP_Server_district_scale_USD` | Fixed Operation Costs of Server-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_HP_Sewage_district_scale_USD` | Fixed Operation Costs of Sewage-Source Heat Pump in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_PeakBoiler_NG_district_scale_USD` | Fixed Operation Costs of Peak Boiler in Central Plant | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_PV_district_scale_USD` | Fixed Operation Costs of PV panels | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_PVT_district_scale_USD` | Fixed Operation Costs of PVT panels | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SC_ET_district_scale_USD` | Fixed Operation Costs of Solar collectors (evacuated Tubes) | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SC_FP_district_scale_USD` | Fixed Operation Costs of Solar collectors (Flat-Plate) | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SeasonalStorage_WS_district_scale_USD` | Fixed Operation Costs of Seasonal Thermal Storage | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_fixed_SubstationsHeating_district_scale_USD` | Fixed Operation Costs of Heating Substations | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_DB_district_scale_USD` | Variable Operation Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_GRID_exports_district_scale_USD` | Variable Operation Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_GRID_imports_district_scale_USD` | Variable Operation Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_NG_district_scale_USD` | Variable Operation Costs | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_var_WB_district_scale_USD` | Variable Operation Costs | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_slave_electricity_activation_pattern`

- **Path**: `outputs/data/optimization/slave/gen_1/ind_1_Electricity_Activation_Pattern.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `DATE` | Time stamp (hourly) for one year | date | `NA` | YYYY-MM-DD |
| `E_CHP_gen_directload_W` | Electricity Generated to direct load by CHP Natural Gas | float | `[Wh]` | {0.0...n} |
| `E_CHP_gen_export_W` | Electricity Exported by CHP Natural Gas | float | `[Wh]` | {0.0...n} |
| `E_Furnace_dry_gen_directload_W` | Electricity Generated to direct load by CHP Dry Biomass | float | `[Wh]` | {0.0...n} |
| `E_Furnace_dry_gen_export_W` | Electricity Exported by CHP Dry Biomass | float | `[Wh]` | {0.0...n} |
| `E_Furnace_wet_gen_directload_W` | Electricity Generated to direct load by CHP Wet Biomass | float | `[Wh]` | {0.0...n} |
| `E_Furnace_wet_gen_export_W` | Electricity Exported by CHP Wet Biomass | float | `[Wh]` | {0.0...n} |
| `E_GRID_directload_W` | Electricity Imported from the local grid | float | `[Wh]` | {0.0...n} |
| `E_PV_gen_directload_W` | Electricity Generated to direct load by PV panels | float | `[Wh]` | {0.0...n} |
| `E_PV_gen_export_W` | Electricity Exported by PV panels | float | `[Wh]` | {0.0...n} |
| `E_PVT_gen_directload_W` | Electricity Generated to direct load by PVT panels | float | `[Wh]` | {0.0...n} |
| `E_PVT_gen_export_W` | Electricity Exported by PVT panels | float | `[Wh]` | {0.0...n} |
| `E_Trigen_gen_directload_W` | Electricity Generated to direct load by Trigen CHP Natural Gas | float | `[Wh]` | {0.0...n} |
| `E_Trigen_gen_export_W` | Electricity Exported by Trigen CHP Natural Gas | float | `[Wh]` | {0.0...n} |

---

### `get_optimization_slave_electricity_requirements_data`

- **Path**: `outputs/data/optimization/slave/gen_1/ind_1_Electricity_Requirements_Pattern.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `DATE` | Time stamp (hourly) for one year | date | `NA` | YYYY-MM-DD |
| `E_BackupBoiler_req_W` | Electricity (auxiliary) Required by Back-up Boiler | float | `[Wh]` | {0.0...n} |
| `E_BackupVCC_AS_req_W` | Electricity Required by Back-up Vapor Compression Chiller (Air-Source) | float | `[Wh]` | {0.0...n} |
| `E_BaseBoiler_req_W` | Electricity (auxiliary) Required by Base Load Boiler | float | `[Wh]` | {0.0...n} |
| `E_BaseVCC_AS_req_W` | Electricity Required by Base Load Vapor Compression Chiller (Air-Source) | float | `[Wh]` | {0.0...n} |
| `E_BaseVCC_WS_req_W` | Electricity Required by Base Load Vapor Compression Chiller (Water-Source) | float | `[Wh]` | {0.0...n} |
| `E_cs_cre_cdata_req_building_scale_W` | Electricity Required for space cooling, server cooling and refrigeration of building-scale systems | float | `[Wh]` | {0.0...n} |
| `E_cs_cre_cdata_req_district_scale_W` | Electricity Required for space cooling, server cooling and refrigeration of Buildings Connected to Network | float | `[Wh]` | {0.0...n} |
| `E_DCN_req_W` | Electricity Required for Chilled water Pumping in District Cooling Network | float | `[Wh]` | {0.0...n} |
| `E_DHN_req_W` | Electricity Required for Chilled water Pumping in District Heating Network | float | `[Wh]` | {0.0...n} |
| `E_electricalnetwork_sys_req_W` | Total Electricity Requirements | float | `[Wh]` | {0.0...n} |
| `E_GHP_req_W` | Electricity Required by Ground-Source Heat Pumps | float | `[Wh]` | {0.0...n} |
| `E_HP_Lake_req_W` | Electricity Required by Lake-Source Heat Pumps | float | `[Wh]` | {0.0...n} |
| `E_HP_PVT_req_W` | Electricity Required by Auxiliary Heat Pumps of PVT panels | float | `[Wh]` | {0.0...n} |
| `E_HP_SC_ET_req_W` | Electricity Required by Auxiliary Heat Pumps of Solar collectors (Evacuated tubes) | float | `[Wh]` | {0.0...n} |
| `E_HP_SC_FP_req_W` | Electricity Required by Auxiliary Heat Pumps of Solar collectors (Evacuated Flat Plate) | float | `[Wh]` | {0.0...n} |
| `E_HP_Server_req_W` | Electricity Required by Server-Source Heat Pumps | float | `[Wh]` | {0.0...n} |
| `E_HP_Sew_req_W` | Electricity Required by Sewage-Source Heat Pumps | float | `[Wh]` | {0.0...n} |
| `E_hs_ww_req_building_scale_W` | Electricity Required for space heating and hotwater of building-scale systems | float | `[Wh]` | {0.0...n} |
| `E_hs_ww_req_district_scale_W` | Electricity Required for space heating and hotwater of Buildings Connected to Network | float | `[Wh]` | {0.0...n} |
| `E_PeakBoiler_req_W` | Electricity (auxiliary) Required by Peak-Boiler | float | `[Wh]` | {0.0...n} |
| `E_PeakVCC_AS_req_W` | Electricity Required by Peak Vapor Compression Chiller (Air-Source) | float | `[Wh]` | {0.0...n} |
| `E_PeakVCC_WS_req_W` | Electricity Required by Peak Vapor Compression Chiller (Water-Source) | float | `[Wh]` | {0.0...n} |
| `E_Storage_charging_req_W` | Electricity Required by Auxiliary Heatpumps for charging Seasonal Thermal Storage | float | `[Wh]` | {0.0...n} |
| `E_Storage_discharging_req_W` | Electricity Required by Auxiliary Heatpumps for discharging Seasonal Thermal Storage | float | `[Wh]` | {0.0...n} |
| `Eal_req_W` | Electricity Required for Appliances and Lighting in all Buildings | float | `[Wh]` | {0.0...n} |
| `Eaux_req_W` | Electricity Required for Fans and others in all Buildings | float | `[Wh]` | {0.0...n} |
| `Edata_req_W` | Electricity Required for Servers in all Buildings | float | `[Wh]` | {0.0...n} |
| `Epro_req_W` | Electricity Required for Industrial Processes in all Buildings | float | `[Wh]` | {0.0...n} |

---

### `get_optimization_slave_heating_activation_pattern`

- **Path**: `outputs/data/optimization/slave/gen_2/ind_0_Heating_Activation_Pattern.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `DATE` | Time stamp (hourly) for one year | date | `NA` | YYYY-MM-DD |
| `E_CHP_gen_W` | Electricity Generation by CHP Natural Gas | float | `[Wh]` | {0.0...n} |
| `E_Furnace_dry_gen_W` | Electricity Generation by CHP Dry-Biomass | float | `[Wh]` | {0.0...n} |
| `E_Furnace_wet_gen_W` | Electricity Generation by CHP Wet-Biomass | float | `[Wh]` | {0.0...n} |
| `E_PVT_gen_W` | Electricity Generation by PVT | float | `[Wh]` | {0.0...n} |
| `Q_BackupBoiler_gen_directload_W` | Thermal generation of Back-up Boiler to direct load | float | `[Wh]` | {0.0...n} |
| `Q_BaseBoiler_gen_directload_W` | Thermal generation of Base load Boiler to direct load | float | `[Wh]` | {0.0...n} |
| `Q_CHP_gen_directload_W` | Thermal generation of CHP Natural Gas to direct load | float | `[Wh]` | {0.0...n} |
| `Q_districtheating_sys_req_W` | Thermal requirements of District Heating Network | float | `[Wh]` | {0.0...n} |
| `Q_Furnace_dry_gen_directload_W` | Thermal generation of CHP Dry-Biomass to direct load | float | `[Wh]` | {0.0...n} |
| `Q_Furnace_wet_gen_directload_W` | Thermal generation of CHP Wet-Biomass to direct load | float | `[Wh]` | {0.0...n} |
| `Q_GHP_gen_directload_W` | Thermal generation of ground-source heat pump to direct load | float | `[Wh]` | {0.0...n} |
| `Q_HP_Lake_gen_directload_W` | Thermal generation of Lake-Source Heatpump to direct load | float | `[Wh]` | {0.0...n} |
| `Q_HP_Server_gen_directload_W` | Thermal generation of Server-Source Heatpump to direct load | float | `[Wh]` | {0.0...n} |
| `Q_HP_Server_storage_W` | Thermal generation of Server-Source Heatpump to Seasonal Thermal Storage | float | `[Wh]` | {0.0...n} |
| `Q_HP_Sew_gen_directload_W` | Thermal generation of Sewage-Source Heatpump to direct load | float | `[Wh]` | {0.0...n} |
| `Q_PeakBoiler_gen_directload_W` | Thermal generation of Peak Boiler to direct load | float | `[Wh]` | {0.0...n} |
| `Q_PVT_gen_directload_W` | Thermal generation of PVT  to direct load | float | `[Wh]` | {0.0...n} |
| `Q_PVT_gen_storage_W` | Thermal generation of PVT  to Seasonal Thermal Storage | float | `[Wh]` | {0.0...n} |
| `Q_SC_ET_gen_directload_W` | Thermal generation of Solar Collectors (Evacuated Tubes) to direct load | float | `[Wh]` | {0.0...n} |
| `Q_SC_ET_gen_storage_W` | Thermal generation of Solar Collectors (Evacuated Tubes)  to Seasonal Thermal Storage | float | `[Wh]` | {0.0...n} |
| `Q_SC_FP_gen_directload_W` | Thermal generation of Solar Collectors (Flat Plate) to direct load | float | `[Wh]` | {0.0...n} |
| `Q_SC_FP_gen_storage_W` | Thermal generation of Solar Collectors (Flat Plate)  to Seasonal Thermal Storage | float | `[Wh]` | {0.0...n} |
| `Q_Storage_gen_directload_W` | Discharge from Storage to Direct Load | float | `[Wh]` | {0.0...n} |

---

### `get_optimization_slave_total_performance`

- **Path**: `outputs/data/optimization/slave/gen_0/ind_2_total_performance.csv`
- **File type**: `csv`
- **Created by**: `optimization`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_sys_building_scale_USD` | Annualized Capital Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_sys_district_scale_USD` | Annualized Capital Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_sys_USD` | Annualized Capital Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_total_sys_building_scale_USD` | Total Capital Costs of building-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_district_scale_USD` | Total Capital Costs of district-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_USD` | Total Capital Costs of all systems | float | `[USD 2015]` | {0.0...n} |
| `GHG_sys_building_scale_tonCO2` | Green House Gas Emissions of building-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_district_scale_tonCO2` | Green House Gas Emissions Central Plant | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_tonCO2` | Green House Gas Emissions of all systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `Opex_a_sys_building_scale_USD` | Operation Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_district_scale_USD` | Operation Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_USD` | Operation Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_building_scale_USD` | Total Anualized Costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_district_scale_USD` | Total Anualized Costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_USD` | Total Anualized Costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |

---

### `get_optimization_substations_results_file`

- **Path**: `outputs/data/optimization/substations/110011011DH_B001_result.csv`
- **File type**: `csv`
- **Created by**: `decentralized`, `optimization`, `thermal_network`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `date` | Date and time in hourly intervals | date | `NA` | YYYY-MM-DD |
| `HEX_hs_area_m2` | Heat exchanger area for space heating | float | `[m2]` | {0.0...n} |
| `HEX_ww_area_m2` | Heat exchanger area for domestic hot water | float | `[m2]` | {0.0...n} |
| `mdot_DH_result_kgpers` | Substation flow rate on the DH side. | float | `[kg/s]` | {0.0...n} |
| `Qhs_booster_W` | Heat from local booster for space heating (zero when district heating temperature is sufficient) | float | `[W]` | {0.0...n} |
| `Qhs_dh_W` | Heat from district heating for space heating (may be less than total if booster is used) | float | `[W]` | {0.0...n} |
| `Qww_booster_W` | Heat from local booster for domestic hot water (zero when district heating temperature is sufficient) | float | `[W]` | {0.0...n} |
| `Qww_dh_W` | Heat from district heating for domestic hot water (may be less than total if booster is used) | float | `[W]` | {0.0...n} |
| `T_return_DH_result_C` | Substation return temperature of the district heating network | float | `[C]` | {-273.15...n} |
| `T_supply_DH_result_C` | Substation supply temperature of the district heating network | float | `[C]` | {-273.15...n} |
| `T_target_dhw_C` | Building-side target supply temperature for domestic hot water (from HVAC assembly, non-zero only when booster is active) | float | `[C]` | {0.0...n} |
| `T_target_hs_C` | Building-side target supply temperature for space heating (from HVAC assembly, non-zero only when booster is active) | float | `[C]` | {0.0...n} |

---

### `get_optimization_substations_total_file`

- **Path**: `outputs/data/optimization/substations/Total_DH_111111111.csv`
- **File type**: `csv`
- **Created by**: `optimization`, `thermal_network`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Af_m2` | Conditioned floor area (heated/cooled) | float | `[m2]` | {0.0...n} |
| `Aocc_m2` | Occupied floor area (heated/cooled) | float | `[m2]` | {0.0...n} |
| `Aroof_m2` | Roof area | float | `[m2]` | {0.0...n} |
| `E_sys0_kW` | Nominal end-use electricity demand | float | `[kW]` | {0.0...n} |
| `E_sys_MWhyr` | End-use total electricity consumption (system-level demand), E_sys =  Eve + Ea + El + Edata + Epro + Eaux + Ev | float | `[MWh/yr]` | {0.0...n} |
| `Ea0_kW` | Nominal end-use electricity for appliances | float | `[kW]` | {0.0...n} |
| `Ea_MWhyr` | End-use electricity for appliances | float | `[MWh/yr]` | {0.0...n} |
| `Eal0_kW` | Nominal Total net electricity for all sources and sinks. | float | `[kW]` | {0.0...n} |
| `Eal_MWhyr` | End-use electricity consumption of appliances and lighting, Eal = El_W + Ea_W | float | `[MWh/yr]` | {0.0...n} |
| `Eaux0_kW` | Nominal Auxiliary electricity consumption. | float | `[kW]` | {0.0...n} |
| `Eaux_MWhyr` | End-use auxiliary electricity consumption, Eaux = Eaux_fw + Eaux_ww + Eaux_cs + Eaux_hs + Ehs_lat_aux | float | `[MWh/yr]` | {0.0...n} |
| `Edata0_kW` | Nominal Data centre electricity consumption. | float | `[kW]` | {0.0...n} |
| `Edata_MWhyr` | Electricity consumption for data centers | float | `[MWh/yr]` | {0.0...n} |
| `El0_kW` | Nominal end-use electricity for lights | float | `[kW]` | {0.0...n} |
| `El_MWhyr` | End-use electricity for lights | float | `[MWh/yr]` | {0.0...n} |
| `Epro0_kW` | Nominal Industrial processes electricity consumption. | float | `[kW]` | {0.0...n} |
| `Epro_MWhyr` | Electricity supplied to industrial processes | float | `[MWh/yr]` | {0.0...n} |
| `Ev0_kW` | Nominal end-use electricity for electric vehicles | float | `[kW]` | {0.0...n} |
| `Ev_MWhyr` | End-use electricity for electric vehicles | float | `[MWh/yr]` | {0.0...n} |
| `Eve0_kW` | Nominal end-use electricity for ventilation | float | `[kW]` | {0.0...n} |
| `Eve_MWhyr` | End-use electricity for ventilation | float | `[MWh/yr]` | {0.0...n} |
| `GFA_m2` | Gross floor area | float | `[m2]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `people0` | Nominal occupancy | float | `[people]` | {0.0...n} |
| `QC_sys0_kW` | Nominal Total system cooling demand. | float | `[kW]` | {0.0...n} |
| `QC_sys_MWhyr` | Total system cooling demand, QC_sys = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys | float | `[MWh/yr]` | {0.0...n} |
| `Qcdata0_kW` | Nominal Data centre cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcdata_MWhyr` | Data centre cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcdata_sys0_kW` | Nominal end-use data center cooling demand | float | `[kW]` | {0.0...n} |
| `Qcdata_sys_MWhyr` | End-use data center cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcpro_sys0_kW` | Nominal process cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcpro_sys_MWhyr` | Yearly processes cooling demand. | float | `[MWh/yr]` | {0.0...n} |
| `Qcre0_kW` | Nominal Refrigeration cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcre_MWhyr` | Refrigeration cooling demand for the system | float | `[MWh/yr]` | {0.0...n} |
| `Qcre_sys0_kW` | Nominal refrigeration cooling demand | float | `[kW]` | {0.0...n} |
| `Qcre_sys_MWhyr` | End-use refrigeration demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs0_kW` | Nominal Total cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_dis_ls0_kW` | Nominal Cooling distribution losses. | float | `[kW]` | {0.0...n} |
| `Qcs_dis_ls_MWhyr` | Cooling distribution losses | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_em_ls0_kW` | Nominal Cooling emission losses. | float | `[kW]` | {0.0...n} |
| `Qcs_em_ls_MWhyr` | Cooling emission losses | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_lat_ahu0_kW` | Nominal AHU latent cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_lat_ahu_MWhyr` | AHU latent cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_lat_aru0_kW` | Nominal ARU latent cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_lat_aru_MWhyr` | ARU latent cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_lat_sys0_kW` | Nominal System latent cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_lat_sys_MWhyr` | System latent cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_MWhyr` | Useful energy for space cooling (thermal demand at point of use) | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_ahu0_kW` | Nominal AHU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_ahu_MWhyr` | Sensible cooling demand in AHU | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_aru0_kW` | Nominal ARU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_aru_MWhyr` | ARU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_scu0_kW` | Nominal SCU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_scu_MWhyr` | SCU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_sys0_kW` | Nominal Sensible system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_sys_MWhyr` | Total sensible cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys0_kW` | Nominal end-use space cooling demand | float | `[kW]` | {0.0...n} |
| `Qcs_sys_ahu0_kW` | Nominal AHU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sys_ahu_MWhyr` | AHU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys_aru0_kW` | Nominal ARU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sys_aru_MWhyr` | ARU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys_MWhyr` | End-use space cooling demand (system-level including HVAC losses), Qcs_sys = Qcs_sen_sys + Qcs_lat_sys + Qcs_em_ls + Qcs_dis_ls | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys_scu0_kW` | Nominal SCU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sys_scu_MWhyr` | SCU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `QH_sys0_kW` | Nominal total building heating demand. | float | `[kW]` | {0.0...n} |
| `QH_sys_MWhyr` | Total building heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhpro_sys0_kW` | Nominal process heating demand. | float | `[kW]` | {0.0...n} |
| `Qhpro_sys_MWhyr` | Yearly processes heating demand. | float | `[MWh/yr]` | {0.0...n} |
| `Qhs0_kW` | Nominal space heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_dis_ls0_kW` | Nominal Heating system distribution losses. | float | `[kW]` | {0.0...n} |
| `Qhs_dis_ls_MWhyr` | Heating system distribution losses | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_em_ls0_kW` | Nominal Heating emission losses. | float | `[kW]` | {0.0...n} |
| `Qhs_em_ls_MWhyr` | Heating system emission losses | float | `[MWh/year]` | {0.0...n} |
| `Qhs_lat_ahu0_kW` | Nominal AHU latent heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_lat_ahu_MWhyr` | AHU latent heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_lat_aru0_kW` | Nominal ARU latent heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_lat_aru_MWhyr` | ARU latent heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_lat_sys0_kW` | Nominal System latent heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_lat_sys_MWhyr` | System latent heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_MWhyr` | Total space heating demand. | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_ahu0_kW` | Nominal AHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sen_ahu_MWhyr` | AHU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_aru0_kW` | ARU sensible heating demand | float | `[kW]` | {0.0...n} |
| `Qhs_sen_aru_MWhyr` | ARU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_shu0_kW` | Nominal SHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sen_shu_MWhyr` | SHU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_sys0_kW` | Nominal HVAC systems sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sen_sys_MWhyr` | SHU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys0_kW` | Nominal end-use space heating demand | float | `[kW]` | {0.0...n} |
| `Qhs_sys_ahu0_kW` | Nominal AHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sys_ahu_MWhyr` | AHU system heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys_aru0_kW` | Nominal ARU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sys_aru_MWhyr` | ARU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys_MWhyr` | End-use space heating demand (system-level including HVAC losses), Qhs_sys = Qhs_sen_sys + Qhs_em_ls + Qhs_dis_ls | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys_shu0_kW` | Nominal SHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sys_shu_MWhyr` | SHU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qww0_kW` | Nominal DHW heating demand. | float | `[kW]` | {0.0...n} |
| `Qww_MWhyr` | Useful energy for domestic hot water (thermal demand at taps) | float | `[MWh/yr]` | {0.0...n} |
| `Qww_sys0_kW` | Nominal end-use hotwater demand | float | `[kW]` | {0.0...n} |
| `Qww_sys_MWhyr` | End-use domestic hot water demand (system-level including distribution losses) | float | `[MWh/yr]` | {0.0...n} |

---

[← Life Cycle Analysis (BETA)](06-life-cycle-analysis.md) | [Glossary index](index.md) | [Data Management →](08-data-management.md)
