
PVT_metadata_results
--------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/B001_PVT_sensors.csv**
    :header: "Variable", "Description"



PVT_results
-----------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/B001_PVT.csv**
    :header: "Variable", "Description"



PVT_total_buildings
-------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/PVT_total_buildings.csv**
    :header: "Variable", "Description"



PVT_totals
----------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/solar/PVT_total.csv**
    :header: "Variable", "Description"



PV_metadata_results
-------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/B001_PV_sensors.csv**
    :header: "Variable", "Description"



PV_results
----------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/B001_PV.csv**
    :header: "Variable", "Description"



PV_total_buildings
------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/PV_total_buildings.csv**
    :header: "Variable", "Description"



PV_totals
---------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/solar/PV_total.csv**
    :header: "Variable", "Description"



SC_metadata_results
-------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/B001_SC_ET_sensors.csv**
    :header: "Variable", "Description"



SC_results
----------

The following file is used by scripts: ['decentralized']



.. csv-table:: **outputs/data/potentials/solar/B001_SC_ET.csv**
    :header: "Variable", "Description"



SC_total_buildings
------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/SC_ET_total_buildings.csv**
    :header: "Variable", "Description"



SC_totals
---------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/solar/SC_FP_total.csv**
    :header: "Variable", "Description"



get_building_air_conditioning
-----------------------------

The following file is used by scripts: ['demand']



.. csv-table:: **inputs/building-properties/air_conditioning_systems.dbf**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     cool_ends,End of the cooling season - use 00|00 when there is none - Unit: [DD|MM]
     cool_starts,Start of the cooling season - use 00|00 when there is none - Unit: [DD|MM]
     heat_ends,End of the heating season - use 00|00 when there is none - Unit: [DD|MM]
     heat_starts,Start of the heating season - use 00|00 when there is none - Unit: [DD|MM]
     type_cs,Type of cooling supply system - Unit: [code]
     type_ctrl,Type of heating and cooling control systems (relates to values in Default Database HVAC Properties) - Unit: [code]
     type_dhw,Type of hot water supply system - Unit: [code]
     type_hs,Type of heating supply system - Unit: [code]
     type_vent,Type of ventilation strategy (relates to values in Default Database HVAC Properties) - Unit: [code]


get_building_architecture
-------------------------

The following file is used by scripts: ['schedule_maker', 'radiation', 'emissions', 'demand']



.. csv-table:: **inputs/building-properties/architecture.dbf**
    :header: "Variable", "Description"

     Es,Fraction of gross floor area with electrical demands. - Unit: [m2/m2]
     Hs_ag,Fraction of above ground gross floor area air-conditioned. - Unit: [m2/m2]
     Hs_bg,Fraction of below ground gross floor area air-conditioned. - Unit: [m2/m2]
     Name,Unique building ID. It must start with a letter. - Unit: [-]
     Ns,Fraction of net gross floor area. - Unit: [m2/m2]
     type_cons,Type of construction. It relates to the contents of the default database of Envelope Properties: construction - Unit: [code]
     type_leak,Leakage level. It relates to the contents of the default database of Envelope Properties: leakage - Unit: [code]
     type_roof,Roof construction type (relates to values in Default Database Construction Properties) - Unit: [-]
     type_shade,Shading system type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_wall,Wall construction type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_win,Window type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     void_deck,Number of floors (from the ground up) with an open envelope (default = 0) - Unit: [-]
     wwr_east,Window to wall ratio in in facades facing east - Unit: [m2/m2]
     wwr_north,Window to wall ratio in in facades facing north - Unit: [m2/m2]
     wwr_south,Window to wall ratio in in facades facing south - Unit: [m2/m2]
     wwr_west,Window to wall ratio in in facades facing west - Unit: [m2/m2]


get_building_comfort
--------------------

The following file is used by scripts: ['schedule_maker', 'demand']



.. csv-table:: **inputs/building-properties/indoor_comfort.dbf**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     RH_max_pc,Upper bound of relative humidity - Unit: [%]
     RH_min_pc,Lower_bound of relative humidity - Unit: [%]
     Tcs_set_C,Setpoint temperature for cooling system - Unit: [C]
     Tcs_setb_C,Setback point of temperature for cooling system - Unit: [C]
     Ths_set_C,Setpoint temperature for heating system - Unit: [C]
     Ths_setb_C,Setback point of temperature for heating system - Unit: [C]
     Ve_lpspax,Indoor quality requirements of indoor ventilation per person - Unit: [l/s]


get_building_internal
---------------------

The following file is used by scripts: ['schedule_maker', 'demand']



.. csv-table:: **inputs/building-properties/internal_loads.dbf**
    :header: "Variable", "Description"

     Ea_Wm2,Peak specific electrical load due to computers and devices - Unit: [W/m2]
     Ed_Wm2,Peak specific electrical load due to servers/data centres - Unit: [W/m2]
     El_Wm2,Peak specific electrical load due to artificial lighting - Unit: [W/m2]
     Epro_Wm2,Peak specific electrical load due to industrial processes - Unit: [W/m2]
     Name,Unique building ID. It must start with a letter. - Unit: [-]
     Occ_m2pax,Occupancy density - Unit: [m2/pax]
     Qcpro_Wm2,Peak specific process cooling load - Unit: [W/m2]
     Qcre_Wm2,Peak specific cooling load due to refrigeration (cooling rooms) - Unit: [W/m2]
     Qhpro_Wm2,Peak specific process heating load - Unit: [W/m2]
     Qs_Wpax,Peak sensible heat load of people - Unit: [W/pax]
     Vw_lpdpax,Peak specific fresh water consumption (includes cold and hot water) - Unit: [lpd]
     Vww_lpdpax,Peak specific daily hot water consumption - Unit: [lpd]
     X_ghpax,Moisture released by occupancy at peak conditions - Unit: [gh/kg/p]


get_building_supply
-------------------

The following file is used by scripts: ['demand', 'decentralized', 'emissions', 'operation_costs']



.. csv-table:: **inputs/building-properties/supply_systems.dbf**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     type_cs,Type of cooling supply system - Unit: [code]
     type_dhw,Type of hot water supply system - Unit: [code]
     type_el,Type of electrical supply system - Unit: [code]
     type_hs,Type of heating supply system - Unit: [code]


get_building_weekly_schedules
-----------------------------

The following file is used by scripts: ['schedule_maker', 'demand']



.. csv-table:: **inputs/building-properties/schedules/B001.csv**
    :header: "Variable", "Description"



get_costs_operation_file
------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/costs/operation_costs.csv**
    :header: "Variable", "Description"

     Aocc_m2,TODO - Unit: TODO
     COAL_hs_cost_m2yr,TODO - Unit: TODO
     COAL_hs_cost_yr,Operation costs of coal due to space heating - Unit: $USD(2015)/yr
     COAL_ww_cost_m2yr,TODO - Unit: TODO
     COAL_ww_cost_yr,Operation costs of coal due to hotwater - Unit: $USD(2015)/yr
     DC_cdata_cost_m2yr,TODO - Unit: TODO
     DC_cdata_cost_yr,Operation costs due to space heating - Unit: $USD(2015)/yr
     DC_cre_cost_m2yr,TODO - Unit: TODO
     DC_cre_cost_yr,Operation costs due to hotwater - Unit: $USD(2015)/yr
     DC_cs_cost_m2yr,TODO - Unit: TODO
     DC_cs_cost_yr,Operation costs due to space cooling - Unit: $USD(2015)/yr
     DH_hs_cost_m2yr,TODO - Unit: TODO
     DH_hs_cost_yr,Operation costs due to space heating - Unit: $USD(2015)/yr
     DH_ww_cost_m2yr,TODO - Unit: TODO
     DH_ww_cost_yr,Operation costs due to hotwater - Unit: $USD(2015)/yr
     GRID_cost_m2yr,Electricity supply from the grid - Unit: $USD(2015)/m2.yr
     GRID_cost_yr,Electricity supply from the grid - Unit: $USD(2015)/yr
     NG_hs_cost_m2yr,TODO - Unit: TODO
     NG_hs_cost_yr,Operation costs of NG due to space heating - Unit: $USD(2015)/yr
     NG_ww_cost_m2yr,TODO - Unit: TODO
     NG_ww_cost_yr,Operation costs of NG due to hotwater - Unit: $USD(2015)/yr
     Name,Unique building ID. It must start with a letter. - Unit: [-]
     OIL_hs_cost_m2yr,TODO - Unit: TODO
     OIL_hs_cost_yr,Operation costs of oil due to space heating - Unit: $USD(2015)/yr
     OIL_ww_cost_m2yr,TODO - Unit: TODO
     OIL_ww_cost_yr,Operation costs of oil due to hotwater - Unit: $USD(2015)/yr
     PV_cost_m2yr,Electricity supply from PV - Unit: $USD(2015)/yr
     PV_cost_yr,Electricity supply from PV - Unit: $USD(2015)/yr
     SOLAR_hs_cost_m2yr,TODO - Unit: TODO
     SOLAR_hs_cost_yr,Operation costs due to solar collectors for hotwater - Unit: $USD(2015)/yr
     SOLAR_ww_cost_m2yr,TODO - Unit: TODO
     SOLAR_ww_cost_yr,Operation costs due to solar collectors for space heating - Unit: $USD(2015)/yr
     WOOD_hs_cost_m2yr,TODO - Unit: TODO
     WOOD_hs_cost_yr,Operation costs of wood due to space heating - Unit: $USD(2015)/yr
     WOOD_ww_cost_m2yr,TODO - Unit: TODO
     WOOD_ww_cost_yr,Operation costs of wood due to hotwater - Unit: $USD(2015)/yr


get_demand_results_file
-----------------------

The following file is used by scripts: ['decentralized', 'optimization', 'thermal_network', 'sewage_potential']



.. csv-table:: **outputs/data/demand/B001.csv**
    :header: "Variable", "Description"



get_geothermal_potential
------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/Shallow_geothermal_potential.csv**
    :header: "Variable", "Description"



get_lca_embodied
----------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/emissions/Total_LCA_embodied.csv**
    :header: "Variable", "Description"



get_lca_mobility
----------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/emissions/Total_LCA_mobility.csv**
    :header: "Variable", "Description"



get_lca_operation
-----------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/emissions/Total_LCA_operation.csv**
    :header: "Variable", "Description"



get_multi_criteria_analysis
---------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/multicriteria/gen_2_multi_criteria_analysis.csv**
    :header: "Variable", "Description"



get_network_energy_pumping_requirements_file
--------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__plant_pumping_load_kW.csv**
    :header: "Variable", "Description"



get_network_layout_edges_shapefile
----------------------------------

The following file is used by scripts: ['thermal_network']



.. csv-table:: **outputs/data/thermal-network/DH/edges.shp**
    :header: "Variable", "Description"



get_network_layout_nodes_shapefile
----------------------------------

The following file is used by scripts: ['thermal_network']



.. csv-table:: **outputs/data/thermal-network/DH/nodes.shp**
    :header: "Variable", "Description"



get_network_linear_pressure_drop_edges
--------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__linear_pressure_drop_edges_Paperm.csv**
    :header: "Variable", "Description"



get_network_linear_thermal_loss_edges_file
------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__linear_thermal_loss_edges_Wperm.csv**
    :header: "Variable", "Description"



get_network_pressure_at_nodes
-----------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__pressure_at_nodes_Pa.csv**
    :header: "Variable", "Description"



get_network_temperature_plant
-----------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__temperature_plant_K.csv**
    :header: "Variable", "Description"



get_network_temperature_return_nodes_file
-----------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__temperature_return_nodes_K.csv**
    :header: "Variable", "Description"



get_network_temperature_supply_nodes_file
-----------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__temperature_supply_nodes_K.csv**
    :header: "Variable", "Description"



get_network_thermal_loss_edges_file
-----------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__thermal_loss_edges_kW.csv**
    :header: "Variable", "Description"



get_network_total_pressure_drop_file
------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/thermal-network/DH__plant_pumping_pressure_loss_Pa.csv**
    :header: "Variable", "Description"



get_network_total_thermal_loss_file
-----------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/thermal-network/DH__total_thermal_loss_edges_kW.csv**
    :header: "Variable", "Description"



get_optimization_checkpoint
---------------------------

The following file is used by scripts: []



get_optimization_connected_cooling_capacity
-------------------------------------------

The following file is used by scripts: []



get_optimization_connected_electricity_capacity
-----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_0_connected_electrical_capacity.csv**
    :header: "Variable", "Description"



get_optimization_connected_heating_capacity
-------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_0/ind_2_connected_heating_capacity.csv**
    :header: "Variable", "Description"



get_optimization_decentralized_folder_building_result_heating
-------------------------------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/decentralized/DiscOp_B001_result_heating.csv**
    :header: "Variable", "Description"



get_optimization_decentralized_folder_building_result_heating_activation
------------------------------------------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/decentralized/DiscOp_B001_result_heating_activation.csv**
    :header: "Variable", "Description"



get_optimization_disconnected_cooling_capacity
----------------------------------------------

The following file is used by scripts: []



get_optimization_disconnected_heating_capacity
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_0/ind_1_disconnected_heating_capacity.csv**
    :header: "Variable", "Description"



get_optimization_generation_connected_performance
-------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/gen_1_connected_performance.csv**
    :header: "Variable", "Description"



get_optimization_generation_disconnected_performance
----------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/gen_2_disconnected_performance.csv**
    :header: "Variable", "Description"



get_optimization_generation_total_performance
---------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/gen_2_total_performance.csv**
    :header: "Variable", "Description"



get_optimization_generation_total_performance_halloffame
--------------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/gen_1_total_performance_halloffame.csv**
    :header: "Variable", "Description"



get_optimization_generation_total_performance_pareto
----------------------------------------------------

The following file is used by scripts: ['multi_criteria_analysis']



.. csv-table:: **outputs/data/optimization/slave/gen_2/gen_2_total_performance_pareto.csv**
    :header: "Variable", "Description"



get_optimization_individuals_in_generation
------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/generation_2_individuals.csv**
    :header: "Variable", "Description"



get_optimization_network_results_summary
----------------------------------------

The following file is used by scripts: ['optimization', 'optimization', 'optimization', 'optimization', 'optimization', 'optimization', 'optimization', 'optimization']



.. csv-table:: **outputs/data/optimization/network/DH_Network_summary_result_0x1be.csv**
    :header: "Variable", "Description"



get_optimization_slave_building_connectivity
--------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_1_building_connectivity.csv**
    :header: "Variable", "Description"



get_optimization_slave_connected_performance
--------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_2_buildings_connected_performance.csv**
    :header: "Variable", "Description"



get_optimization_slave_cooling_activation_pattern
-------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_2_Cooling_Activation_Pattern.csv**
    :header: "Variable", "Description"



get_optimization_slave_disconnected_performance
-----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_0_buildings_disconnected_performance.csv**
    :header: "Variable", "Description"



get_optimization_slave_electricity_activation_pattern
-----------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_1_Electricity_Activation_Pattern.csv**
    :header: "Variable", "Description"



get_optimization_slave_electricity_requirements_data
----------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_1_Electricity_Requirements_Pattern.csv**
    :header: "Variable", "Description"



get_optimization_slave_heating_activation_pattern
-------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_0_Heating_Activation_Pattern.csv**
    :header: "Variable", "Description"



get_optimization_slave_total_performance
----------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_0/ind_2_total_performance.csv**
    :header: "Variable", "Description"



get_optimization_substations_results_file
-----------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/substations/110011011DH_B001_result.csv**
    :header: "Variable", "Description"



get_optimization_substations_total_file
---------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/substations/Total_DH_111111111.csv**
    :header: "Variable", "Description"



get_radiation_building
----------------------

The following file is used by scripts: ['photovoltaic_thermal', 'solar_collector', 'photovoltaic', 'demand']



.. csv-table:: **outputs/data/solar-radiation/B001_radiation.csv**
    :header: "Variable", "Description"



get_radiation_building_sensors
------------------------------

The following file is used by scripts: ['photovoltaic_thermal', 'solar_collector', 'photovoltaic', 'demand']



.. csv-table:: **outputs/data/solar-radiation/B001_insolation_Whm2.json**
    :header: "Variable", "Description"



get_radiation_materials
-----------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/solar-radiation/buidling_materials.csv**
    :header: "Variable", "Description"



get_radiation_metadata
----------------------

The following file is used by scripts: ['photovoltaic_thermal', 'solar_collector', 'photovoltaic', 'demand']



.. csv-table:: **outputs/data/solar-radiation/B001_geometry.csv**
    :header: "Variable", "Description"



get_schedule_model_file
-----------------------

The following file is used by scripts: ['demand']



.. csv-table:: **outputs/data/occupancy/B001.csv**
    :header: "Variable", "Description"



get_sewage_heat_potential
-------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/Sewage_heat_potential.csv**
    :header: "Variable", "Description"



get_thermal_demand_csv_file
---------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__thermal_demand_per_building_W.csv**
    :header: "Variable", "Description"



get_thermal_network_edge_list_file
----------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/thermal-network/DH__metadata_edges.csv**
    :header: "Variable", "Description"



get_thermal_network_layout_massflow_edges_file
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__massflow_edges_kgs.csv**
    :header: "Variable", "Description"



get_thermal_network_layout_massflow_nodes_file
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__massflow_nodes_kgs.csv**
    :header: "Variable", "Description"



get_thermal_network_node_types_csv_file
---------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__metadata_nodes.csv**
    :header: "Variable", "Description"



get_thermal_network_plant_heat_requirement_file
-----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__plant_thermal_load_kW.csv**
    :header: "Variable", "Description"



get_thermal_network_pressure_losses_edges_file
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__pressure_losses_edges_kW.csv**
    :header: "Variable", "Description"



get_thermal_network_substation_ploss_file
-----------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__pumping_load_due_to_substations_kW.csv**
    :header: "Variable", "Description"



get_thermal_network_velocity_edges_file
---------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__velocity_edges_mpers.csv**
    :header: "Variable", "Description"



get_total_demand
----------------

The following file is used by scripts: ['optimization', 'network_layout', 'sewage_potential', 'decentralized', 'operation_costs', 'thermal_network', 'emissions']



.. csv-table:: **outputs/data/demand/Total_demand.csv**
    :header: "Variable", "Description"



get_water_body_potential
------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/Water_body_potential.csv**
    :header: "Variable", "Description"



get_weather_file
----------------

The following file is used by scripts: ['schedule_maker', 'photovoltaic_thermal', 'decentralized', 'solar_collector', 'radiation', 'thermal_network', 'optimization', 'shallow_geothermal_potential', 'demand', 'photovoltaic']



.. csv-table:: **inputs/weather/weather.epw**
    :header: "Variable", "Description"


