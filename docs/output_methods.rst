
PVT_metadata_results
--------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/potentials/solar/B001_PVT_sensors.csv**
    :header: "Variable", "Description"

     intersection,TODO - Unit: TODO


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

     intersection,TODO - Unit: TODO


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

     intersection,TODO - Unit: TODO


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

The following file is used by scripts: ['demand', 'emissions', 'radiation', 'schedule_maker']



.. csv-table:: **inputs/building-properties/architecture.dbf**
    :header: "Variable", "Description"

     Es,Fraction of gross floor area with electrical demands. - Unit: [m2/m2]
     Hs_ag,Fraction of above ground gross floor area air-conditioned. - Unit: [m2/m2]
     Hs_bg,Fraction of below ground gross floor area air-conditioned. - Unit: [m2/m2]
     Name,Unique building ID. It must start with a letter. - Unit: [-]
     Ns,Fraction of net gross floor area. - Unit: [m2/m2]
     type_base,Basement floor construction type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_cons,Type of construction. It relates to the contents of the default database of Envelope Properties: construction - Unit: [code]
     type_floor,Internal floor construction type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_leak,Tightness level. It relates to the contents of the default database of Envelope Properties: tightness - Unit: [code]
     type_roof,Roof construction type (relates to values in Default Database Construction Properties) - Unit: [-]
     type_shade,Shading system type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_wall,External wall construction type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_win,Window type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     void_deck,Number of floors (from the ground up) with an open envelope (default = 0) - Unit: [-]
     wwr_east,Window to wall ratio in in facades facing east - Unit: [m2/m2]
     wwr_north,Window to wall ratio in in facades facing north - Unit: [m2/m2]
     wwr_south,Window to wall ratio in in facades facing south - Unit: [m2/m2]
     wwr_west,Window to wall ratio in in facades facing west - Unit: [m2/m2]


get_building_comfort
--------------------

The following file is used by scripts: ['demand', 'schedule_maker']



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

The following file is used by scripts: ['demand', 'schedule_maker']



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

The following file is used by scripts: ['decentralized', 'demand', 'emissions', 'system_costs']



.. csv-table:: **inputs/building-properties/supply_systems.dbf**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     type_cs,Type of cooling supply system - Unit: [code]
     type_dhw,Type of hot water supply system - Unit: [code]
     type_el,Type of electrical supply system - Unit: [code]
     type_hs,Type of heating supply system - Unit: [code]


get_building_weekly_schedules
-----------------------------

The following file is used by scripts: ['demand', 'schedule_maker']



.. csv-table:: **inputs/building-properties/schedules/B001.csv**
    :header: "Variable", "Description"

     METADATA,TODO - Unit: TODO
     mixed-schedule,TODO - Unit: TODO


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
     Capex_a_sys_connected_USD,TODO - Unit: TODO
     Capex_a_sys_disconnected_USD,TODO - Unit: TODO
     Opex_a_sys_connected_USD,TODO - Unit: TODO
     Opex_a_sys_disconnected_USD,TODO - Unit: TODO


get_demand_results_file
-----------------------

The following file is used by scripts: ['decentralized', 'optimization', 'sewage_potential', 'thermal_network']



.. csv-table:: **outputs/data/demand/B001.csv**
    :header: "Variable", "Description"

     Ea_kWh,TODO - Unit: TODO
     El_kWh,TODO - Unit: TODO


get_geothermal_potential
------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/Shallow_geothermal_potential.csv**
    :header: "Variable", "Description"

     Area_avail_m2,TODO - Unit: TODO
     QGHP_kW,TODO - Unit: TODO
     Ts_C,TODO - Unit: TODO


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

     Capex_a_sys_USD,TODO - Unit: TODO
     Capex_a_sys_connected_USD,TODO - Unit: TODO
     Capex_a_sys_disconnected_USD,TODO - Unit: TODO
     Capex_total_sys_USD,TODO - Unit: TODO
     Capex_total_sys_connected_USD,TODO - Unit: TODO
     Capex_total_sys_disconnected_USD,TODO - Unit: TODO
     GHG_rank,TODO - Unit: TODO
     GHG_sys_connected_tonCO2,TODO - Unit: TODO
     GHG_sys_disconnected_tonCO2,TODO - Unit: TODO
     GHG_sys_tonCO2,TODO - Unit: TODO
     Opex_a_sys_USD,TODO - Unit: TODO
     Opex_a_sys_connected_USD,TODO - Unit: TODO
     Opex_a_sys_disconnected_USD,TODO - Unit: TODO
     PEN_rank,TODO - Unit: TODO
     PEN_sys_MJoil,TODO - Unit: TODO
     PEN_sys_connected_MJoil,TODO - Unit: TODO
     PEN_sys_disconnected_MJoil,TODO - Unit: TODO
     TAC_rank,TODO - Unit: TODO
     TAC_sys_USD,TODO - Unit: TODO
     TAC_sys_connected_USD,TODO - Unit: TODO
     TAC_sys_disconnected_USD,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     Unnamed: 0.1,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     individual,TODO - Unit: TODO
     individual_name,TODO - Unit: TODO
     normalized_Capex_total,TODO - Unit: TODO
     normalized_Opex,TODO - Unit: TODO
     normalized_TAC,TODO - Unit: TODO
     normalized_emissions,TODO - Unit: TODO
     normalized_prim,TODO - Unit: TODO
     user_MCDA,TODO - Unit: TODO
     user_MCDA_rank,TODO - Unit: TODO


get_network_energy_pumping_requirements_file
--------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__plant_pumping_load_kW.csv**
    :header: "Variable", "Description"

     pressure_loss_return_kW,TODO - Unit: TODO
     pressure_loss_substations_kW,TODO - Unit: TODO
     pressure_loss_supply_kW,TODO - Unit: TODO
     pressure_loss_total_kW,TODO - Unit: TODO


get_network_layout_edges_shapefile
----------------------------------

The following file is used by scripts: ['thermal_network']



.. csv-table:: **outputs/data/thermal-network/DH/edges.shp**
    :header: "Variable", "Description"

     length_m,TODO - Unit: TODO


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

     PIPE0,TODO - Unit: TODO


get_network_linear_thermal_loss_edges_file
------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__linear_thermal_loss_edges_Wperm.csv**
    :header: "Variable", "Description"

     PIPE0,TODO - Unit: TODO


get_network_pressure_at_nodes
-----------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__pressure_at_nodes_Pa.csv**
    :header: "Variable", "Description"

     NODE0,TODO - Unit: TODO


get_network_temperature_plant
-----------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__temperature_plant_K.csv**
    :header: "Variable", "Description"

     temperature_return_K,TODO - Unit: TODO
     temperature_supply_K,TODO - Unit: TODO


get_network_temperature_return_nodes_file
-----------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__temperature_return_nodes_K.csv**
    :header: "Variable", "Description"

     NODE0,TODO - Unit: TODO


get_network_temperature_supply_nodes_file
-----------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__temperature_supply_nodes_K.csv**
    :header: "Variable", "Description"

     NODE0,TODO - Unit: TODO


get_network_thermal_loss_edges_file
-----------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__thermal_loss_edges_kW.csv**
    :header: "Variable", "Description"

     PIPE0,TODO - Unit: TODO


get_network_total_pressure_drop_file
------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/thermal-network/DH__plant_pumping_pressure_loss_Pa.csv**
    :header: "Variable", "Description"

     pressure_loss_return_Pa,TODO - Unit: TODO
     pressure_loss_substations_Pa,TODO - Unit: TODO
     pressure_loss_supply_Pa,TODO - Unit: TODO
     pressure_loss_total_Pa,TODO - Unit: TODO


get_network_total_thermal_loss_file
-----------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/thermal-network/DH__total_thermal_loss_edges_kW.csv**
    :header: "Variable", "Description"

     thermal_loss_return_kW,TODO - Unit: TODO
     thermal_loss_supply_kW,TODO - Unit: TODO
     thermal_loss_total_kW,TODO - Unit: TODO


get_optimization_checkpoint
---------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/master/CheckPoint_1**
    :header: "Variable", "Description"

     difference_generational_distances,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     generational_distances,TODO - Unit: TODO
     selected_population,TODO - Unit: TODO
     tested_population,TODO - Unit: TODO


get_optimization_connected_cooling_capacity
-------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_1_connected_cooling_capacity.csv**
    :header: "Variable", "Description"

     Capacity_ACHHT_FP_cool_disconnected_W,TODO - Unit: TODO
     Capacity_ACH_SC_FP_cool_disconnected_W,TODO - Unit: TODO
     Capacity_BaseVCC_AS_cool_disconnected_W,TODO - Unit: TODO
     Capacity_DX_AS_cool_disconnected_W,TODO - Unit: TODO
     Capacity_VCCHT_AS_cool_disconnected_W,TODO - Unit: TODO
     Capaticy_ACH_SC_ET_cool_disconnected_W,TODO - Unit: TODO
     Name,TODO - Unit: TODO


get_optimization_connected_electricity_capacity
-----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_0_connected_electrical_capacity.csv**
    :header: "Variable", "Description"

     Capacity_GRID_el_connected_W,TODO - Unit: TODO
     Capacity_PV_el_connected_W,TODO - Unit: TODO
     Capacity_PV_el_connected_m2,TODO - Unit: TODO


get_optimization_connected_heating_capacity
-------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_0/ind_2_connected_heating_capacity.csv**
    :header: "Variable", "Description"

     Capacity_BackupBoiler_NG_heat_connected_W,TODO - Unit: TODO
     Capacity_BaseBoiler_NG_heat_connected_W,TODO - Unit: TODO
     Capacity_CHP_DB_el_connected_W,TODO - Unit: TODO
     Capacity_CHP_DB_heat_connected_W,TODO - Unit: TODO
     Capacity_CHP_NG_el_connected_W,TODO - Unit: TODO
     Capacity_CHP_NG_heat_connected_W,TODO - Unit: TODO
     Capacity_CHP_WB_el_connected_W,TODO - Unit: TODO
     Capacity_CHP_WB_heat_connected_W,TODO - Unit: TODO
     Capacity_HP_DS_heat_connected_W,TODO - Unit: TODO
     Capacity_HP_GS_heat_connected_W,TODO - Unit: TODO
     Capacity_HP_SS_heat_connected_W,TODO - Unit: TODO
     Capacity_HP_WS_heat_connected_W,TODO - Unit: TODO
     Capacity_PVT_connected_m2,TODO - Unit: TODO
     Capacity_PVT_el_connected_W,TODO - Unit: TODO
     Capacity_PVT_heat_connected_W,TODO - Unit: TODO
     Capacity_PeakBoiler_NG_heat_connected_W,TODO - Unit: TODO
     Capacity_SC_ET_connected_m2,TODO - Unit: TODO
     Capacity_SC_ET_heat_connected_W,TODO - Unit: TODO
     Capacity_SC_FP_connected_m2,TODO - Unit: TODO
     Capacity_SC_FP_heat_connected_W,TODO - Unit: TODO
     Capacity_SeasonalStorage_WS_heat_connected_W,TODO - Unit: TODO
     Capacity_SeasonalStorage_WS_heat_connected_m3,TODO - Unit: TODO


get_optimization_decentralized_folder_building_result_heating
-------------------------------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/decentralized/DiscOp_B001_result_heating.csv**
    :header: "Variable", "Description"

     Best configuration,TODO - Unit: TODO
     Capacity_BaseBoiler_NG_W,TODO - Unit: TODO
     Capacity_FC_NG_W,TODO - Unit: TODO
     Capacity_GS_HP_W,TODO - Unit: TODO
     Capex_a_USD,TODO - Unit: TODO
     Capex_total_USD,TODO - Unit: TODO
     GHG_tonCO2,TODO - Unit: TODO
     Nominal heating load,TODO - Unit: TODO
     Opex_fixed_USD,TODO - Unit: TODO
     Opex_var_USD,TODO - Unit: TODO
     PEN_MJoil,TODO - Unit: TODO
     TAC_USD,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO


get_optimization_decentralized_folder_building_result_heating_activation
------------------------------------------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/decentralized/DiscOp_B001_result_heating_activation.csv**
    :header: "Variable", "Description"

     BackupBoiler_Status,TODO - Unit: TODO
     Boiler_Status,TODO - Unit: TODO
     E_hs_ww_req_W,TODO - Unit: TODO
     GHP_Status,TODO - Unit: TODO
     NG_BackupBoiler_req_Wh,TODO - Unit: TODO
     NG_Boiler_req_Wh,TODO - Unit: TODO
     Q_BackupBoiler_gen_directload_W,TODO - Unit: TODO
     Q_Boiler_gen_directload_W,TODO - Unit: TODO
     Q_GHP_gen_directload_W,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO


get_optimization_disconnected_cooling_capacity
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_0_disconnected_cooling_capacity.csv**
    :header: "Variable", "Description"

     Capacity_ACHHT_FP_cool_disconnected_W,TODO - Unit: TODO
     Capacity_ACH_SC_FP_cool_disconnected_W,TODO - Unit: TODO
     Capacity_BaseVCC_AS_cool_disconnected_W,TODO - Unit: TODO
     Capacity_DX_AS_cool_disconnected_W,TODO - Unit: TODO
     Capacity_VCCHT_AS_cool_disconnected_W,TODO - Unit: TODO
     Capaticy_ACH_SC_ET_cool_disconnected_W,TODO - Unit: TODO
     Name,TODO - Unit: TODO


get_optimization_disconnected_heating_capacity
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_0/ind_1_disconnected_heating_capacity.csv**
    :header: "Variable", "Description"

     Capacity_BaseBoiler_NG_heat_disconnected_W,TODO - Unit: TODO
     Capacity_FC_NG_heat_disconnected_W,TODO - Unit: TODO
     Capacity_GS_HP_heat_disconnected_W,TODO - Unit: TODO
     Name,TODO - Unit: TODO


get_optimization_generation_connected_performance
-------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/gen_1_connected_performance.csv**
    :header: "Variable", "Description"

     Capex_a_BackupBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_a_BaseBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_a_CHP_NG_connected_USD,TODO - Unit: TODO
     Capex_a_DHN_connected_USD,TODO - Unit: TODO
     Capex_a_Furnace_dry_connected_USD,TODO - Unit: TODO
     Capex_a_Furnace_wet_connected_USD,TODO - Unit: TODO
     Capex_a_GHP_connected_USD,TODO - Unit: TODO
     Capex_a_GRID_connected_USD,TODO - Unit: TODO
     Capex_a_HP_Lake_connected_USD,TODO - Unit: TODO
     Capex_a_HP_Server_connected_USD,TODO - Unit: TODO
     Capex_a_HP_Sewage_connected_USD,TODO - Unit: TODO
     Capex_a_PVT_connected_USD,TODO - Unit: TODO
     Capex_a_PV_connected_USD,TODO - Unit: TODO
     Capex_a_PeakBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_a_SC_ET_connected_USD,TODO - Unit: TODO
     Capex_a_SC_FP_connected_USD,TODO - Unit: TODO
     Capex_a_SeasonalStorage_WS_connected_USD,TODO - Unit: TODO
     Capex_a_SubstationsHeating_connected_USD,TODO - Unit: TODO
     Capex_total_BackupBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_total_BaseBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_total_CHP_NG_connected_USD,TODO - Unit: TODO
     Capex_total_DHN_connected_USD,TODO - Unit: TODO
     Capex_total_Furnace_dry_connected_USD,TODO - Unit: TODO
     Capex_total_Furnace_wet_connected_USD,TODO - Unit: TODO
     Capex_total_GHP_connected_USD,TODO - Unit: TODO
     Capex_total_GRID_connected_USD,TODO - Unit: TODO
     Capex_total_HP_Lake_connected_USD,TODO - Unit: TODO
     Capex_total_HP_Server_connected_USD,TODO - Unit: TODO
     Capex_total_HP_Sewage_connected_USD,TODO - Unit: TODO
     Capex_total_PVT_connected_USD,TODO - Unit: TODO
     Capex_total_PV_connected_USD,TODO - Unit: TODO
     Capex_total_PeakBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_total_SC_ET_connected_USD,TODO - Unit: TODO
     Capex_total_SC_FP_connected_USD,TODO - Unit: TODO
     Capex_total_SeasonalStorage_WS_connected_USD,TODO - Unit: TODO
     Capex_total_SubstationsHeating_connected_USD,TODO - Unit: TODO
     GHG_DB_connected_tonCO2yr,TODO - Unit: TODO
     GHG_GRID_exports_connected_tonCO2yr,TODO - Unit: TODO
     GHG_GRID_imports_connected_tonCO2yr,TODO - Unit: TODO
     GHG_NG_connected_tonCO2yr,TODO - Unit: TODO
     GHG_WB_connected_tonCO2yr,TODO - Unit: TODO
     Opex_fixed_BackupBoiler_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_BaseBoiler_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_CHP_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_DHN_connected_USD,TODO - Unit: TODO
     Opex_fixed_Furnace_dry_connected_USD,TODO - Unit: TODO
     Opex_fixed_Furnace_wet_connected_USD,TODO - Unit: TODO
     Opex_fixed_GHP_connected_USD,TODO - Unit: TODO
     Opex_fixed_GRID_connected_USD,TODO - Unit: TODO
     Opex_fixed_HP_Lake_connected_USD,TODO - Unit: TODO
     Opex_fixed_HP_Server_connected_USD,TODO - Unit: TODO
     Opex_fixed_HP_Sewage_connected_USD,TODO - Unit: TODO
     Opex_fixed_PVT_connected_USD,TODO - Unit: TODO
     Opex_fixed_PV_connected_USD,TODO - Unit: TODO
     Opex_fixed_PeakBoiler_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_SC_ET_connected_USD,TODO - Unit: TODO
     Opex_fixed_SC_FP_connected_USD,TODO - Unit: TODO
     Opex_fixed_SeasonalStorage_WS_connected_USD,TODO - Unit: TODO
     Opex_fixed_SubstationsHeating_connected_USD,TODO - Unit: TODO
     Opex_var_DB_connected_USD,TODO - Unit: TODO
     Opex_var_GRID_exports_connected_USD,TODO - Unit: TODO
     Opex_var_GRID_imports_connected_USD,TODO - Unit: TODO
     Opex_var_NG_connected_USD,TODO - Unit: TODO
     Opex_var_WB_connected_USD,TODO - Unit: TODO
     PEN_DB_connected_MJoilyr,TODO - Unit: TODO
     PEN_GRID_exports_connected_MJoilyr,TODO - Unit: TODO
     PEN_GRID_imports_connected_MJoilyr,TODO - Unit: TODO
     PEN_NG_connected_MJoilyr,TODO - Unit: TODO
     PEN_WB_connected_MJoilyr,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     individual,TODO - Unit: TODO
     individual_name,TODO - Unit: TODO


get_optimization_generation_disconnected_performance
----------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/gen_2_disconnected_performance.csv**
    :header: "Variable", "Description"

     Capex_a_cooling_disconnected_USD,TODO - Unit: TODO
     Capex_a_heating_disconnected_USD,TODO - Unit: TODO
     Capex_total_cooling_disconnected_USD,TODO - Unit: TODO
     Capex_total_heating_disconnected_USD,TODO - Unit: TODO
     GHG_cooling_disconnected_tonCO2,TODO - Unit: TODO
     GHG_heating_disconnected_tonCO2,TODO - Unit: TODO
     Opex_fixed_cooling_disconnected_USD,TODO - Unit: TODO
     Opex_fixed_heating_disconnected_USD,TODO - Unit: TODO
     Opex_var_cooling_disconnected_USD,TODO - Unit: TODO
     Opex_var_heating_disconnected_USD,TODO - Unit: TODO
     PEN_cooling_disconnected_MJoil,TODO - Unit: TODO
     PEN_heating_disconnected_MJoil,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     individual,TODO - Unit: TODO
     individual_name,TODO - Unit: TODO


get_optimization_generation_total_performance
---------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/gen_2_total_performance.csv**
    :header: "Variable", "Description"

     Capex_a_sys_USD,TODO - Unit: TODO
     Capex_a_sys_connected_USD,TODO - Unit: TODO
     Capex_a_sys_disconnected_USD,TODO - Unit: TODO
     Capex_total_sys_USD,TODO - Unit: TODO
     Capex_total_sys_connected_USD,TODO - Unit: TODO
     Capex_total_sys_disconnected_USD,TODO - Unit: TODO
     GHG_sys_connected_tonCO2,TODO - Unit: TODO
     GHG_sys_disconnected_tonCO2,TODO - Unit: TODO
     GHG_sys_tonCO2,TODO - Unit: TODO
     Opex_a_sys_USD,TODO - Unit: TODO
     Opex_a_sys_connected_USD,TODO - Unit: TODO
     Opex_a_sys_disconnected_USD,TODO - Unit: TODO
     PEN_sys_MJoil,TODO - Unit: TODO
     PEN_sys_connected_MJoil,TODO - Unit: TODO
     PEN_sys_disconnected_MJoil,TODO - Unit: TODO
     TAC_sys_USD,TODO - Unit: TODO
     TAC_sys_connected_USD,TODO - Unit: TODO
     TAC_sys_disconnected_USD,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     individual,TODO - Unit: TODO
     individual_name,TODO - Unit: TODO


get_optimization_generation_total_performance_halloffame
--------------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/gen_1_total_performance_halloffame.csv**
    :header: "Variable", "Description"

     Capex_a_sys_USD,TODO - Unit: TODO
     Capex_a_sys_connected_USD,TODO - Unit: TODO
     Capex_a_sys_disconnected_USD,TODO - Unit: TODO
     Capex_total_sys_USD,TODO - Unit: TODO
     Capex_total_sys_connected_USD,TODO - Unit: TODO
     Capex_total_sys_disconnected_USD,TODO - Unit: TODO
     GHG_sys_connected_tonCO2,TODO - Unit: TODO
     GHG_sys_disconnected_tonCO2,TODO - Unit: TODO
     GHG_sys_tonCO2,TODO - Unit: TODO
     Opex_a_sys_USD,TODO - Unit: TODO
     Opex_a_sys_connected_USD,TODO - Unit: TODO
     Opex_a_sys_disconnected_USD,TODO - Unit: TODO
     PEN_sys_MJoil,TODO - Unit: TODO
     PEN_sys_connected_MJoil,TODO - Unit: TODO
     PEN_sys_disconnected_MJoil,TODO - Unit: TODO
     TAC_sys_USD,TODO - Unit: TODO
     TAC_sys_connected_USD,TODO - Unit: TODO
     TAC_sys_disconnected_USD,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     individual,TODO - Unit: TODO
     individual_name,TODO - Unit: TODO


get_optimization_generation_total_performance_pareto
----------------------------------------------------

The following file is used by scripts: ['multi_criteria_analysis']



.. csv-table:: **outputs/data/optimization/slave/gen_2/gen_2_total_performance_pareto.csv**
    :header: "Variable", "Description"

     Capex_a_sys_USD,TODO - Unit: TODO
     Capex_a_sys_connected_USD,TODO - Unit: TODO
     Capex_a_sys_disconnected_USD,TODO - Unit: TODO
     Capex_total_sys_USD,TODO - Unit: TODO
     Capex_total_sys_connected_USD,TODO - Unit: TODO
     Capex_total_sys_disconnected_USD,TODO - Unit: TODO
     GHG_sys_connected_tonCO2,TODO - Unit: TODO
     GHG_sys_disconnected_tonCO2,TODO - Unit: TODO
     GHG_sys_tonCO2,TODO - Unit: TODO
     Opex_a_sys_USD,TODO - Unit: TODO
     Opex_a_sys_connected_USD,TODO - Unit: TODO
     Opex_a_sys_disconnected_USD,TODO - Unit: TODO
     PEN_sys_MJoil,TODO - Unit: TODO
     PEN_sys_connected_MJoil,TODO - Unit: TODO
     PEN_sys_disconnected_MJoil,TODO - Unit: TODO
     TAC_sys_USD,TODO - Unit: TODO
     TAC_sys_connected_USD,TODO - Unit: TODO
     TAC_sys_disconnected_USD,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     individual,TODO - Unit: TODO
     individual_name,TODO - Unit: TODO


get_optimization_individuals_in_generation
------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/generation_2_individuals.csv**
    :header: "Variable", "Description"

     DB_Cogen,TODO - Unit: TODO
     DS_HP,TODO - Unit: TODO
     GS_HP,TODO - Unit: TODO
     NG_BaseBoiler,TODO - Unit: TODO
     NG_Cogen,TODO - Unit: TODO
     NG_PeakBoiler,TODO - Unit: TODO
     PV,TODO - Unit: TODO
     PVT,TODO - Unit: TODO
     SC_ET,TODO - Unit: TODO
     SC_FP,TODO - Unit: TODO
     SS_HP,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     WB_Cogen,TODO - Unit: TODO
     WS_HP,TODO - Unit: TODO
     generation,TODO - Unit: TODO
     individual,TODO - Unit: TODO


get_optimization_network_results_summary
----------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/network/DH_Network_summary_result_0x1be.csv**
    :header: "Variable", "Description"

     DATE,TODO - Unit: TODO
     Q_DHNf_W,TODO - Unit: TODO
     Q_DH_losses_W,TODO - Unit: TODO
     Qcdata_netw_total_kWh,TODO - Unit: TODO
     T_DHNf_re_K,TODO - Unit: TODO
     T_DHNf_sup_K,TODO - Unit: TODO
     mcpdata_netw_total_kWperC,TODO - Unit: TODO
     mdot_DH_netw_total_kgpers,TODO - Unit: TODO


get_optimization_slave_building_connectivity
--------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_1_building_connectivity.csv**
    :header: "Variable", "Description"

     DC_connectivity,TODO - Unit: TODO
     DH_connectivity,TODO - Unit: TODO
     Name,TODO - Unit: TODO


get_optimization_slave_connected_performance
--------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_2_buildings_connected_performance.csv**
    :header: "Variable", "Description"

     Capex_a_BackupBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_a_BaseBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_a_CHP_NG_connected_USD,TODO - Unit: TODO
     Capex_a_DHN_connected_USD,TODO - Unit: TODO
     Capex_a_Furnace_dry_connected_USD,TODO - Unit: TODO
     Capex_a_Furnace_wet_connected_USD,TODO - Unit: TODO
     Capex_a_GHP_connected_USD,TODO - Unit: TODO
     Capex_a_GRID_connected_USD,TODO - Unit: TODO
     Capex_a_HP_Lake_connected_USD,TODO - Unit: TODO
     Capex_a_HP_Server_connected_USD,TODO - Unit: TODO
     Capex_a_HP_Sewage_connected_USD,TODO - Unit: TODO
     Capex_a_PVT_connected_USD,TODO - Unit: TODO
     Capex_a_PV_connected_USD,TODO - Unit: TODO
     Capex_a_PeakBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_a_SC_ET_connected_USD,TODO - Unit: TODO
     Capex_a_SC_FP_connected_USD,TODO - Unit: TODO
     Capex_a_SeasonalStorage_WS_connected_USD,TODO - Unit: TODO
     Capex_a_SubstationsHeating_connected_USD,TODO - Unit: TODO
     Capex_total_BackupBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_total_BaseBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_total_CHP_NG_connected_USD,TODO - Unit: TODO
     Capex_total_DHN_connected_USD,TODO - Unit: TODO
     Capex_total_Furnace_dry_connected_USD,TODO - Unit: TODO
     Capex_total_Furnace_wet_connected_USD,TODO - Unit: TODO
     Capex_total_GHP_connected_USD,TODO - Unit: TODO
     Capex_total_GRID_connected_USD,TODO - Unit: TODO
     Capex_total_HP_Lake_connected_USD,TODO - Unit: TODO
     Capex_total_HP_Server_connected_USD,TODO - Unit: TODO
     Capex_total_HP_Sewage_connected_USD,TODO - Unit: TODO
     Capex_total_PVT_connected_USD,TODO - Unit: TODO
     Capex_total_PV_connected_USD,TODO - Unit: TODO
     Capex_total_PeakBoiler_NG_connected_USD,TODO - Unit: TODO
     Capex_total_SC_ET_connected_USD,TODO - Unit: TODO
     Capex_total_SC_FP_connected_USD,TODO - Unit: TODO
     Capex_total_SeasonalStorage_WS_connected_USD,TODO - Unit: TODO
     Capex_total_SubstationsHeating_connected_USD,TODO - Unit: TODO
     GHG_DB_connected_tonCO2yr,TODO - Unit: TODO
     GHG_GRID_exports_connected_tonCO2yr,TODO - Unit: TODO
     GHG_GRID_imports_connected_tonCO2yr,TODO - Unit: TODO
     GHG_NG_connected_tonCO2yr,TODO - Unit: TODO
     GHG_WB_connected_tonCO2yr,TODO - Unit: TODO
     Opex_fixed_BackupBoiler_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_BaseBoiler_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_CHP_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_DHN_connected_USD,TODO - Unit: TODO
     Opex_fixed_Furnace_dry_connected_USD,TODO - Unit: TODO
     Opex_fixed_Furnace_wet_connected_USD,TODO - Unit: TODO
     Opex_fixed_GHP_connected_USD,TODO - Unit: TODO
     Opex_fixed_GRID_connected_USD,TODO - Unit: TODO
     Opex_fixed_HP_Lake_connected_USD,TODO - Unit: TODO
     Opex_fixed_HP_Server_connected_USD,TODO - Unit: TODO
     Opex_fixed_HP_Sewage_connected_USD,TODO - Unit: TODO
     Opex_fixed_PVT_connected_USD,TODO - Unit: TODO
     Opex_fixed_PV_connected_USD,TODO - Unit: TODO
     Opex_fixed_PeakBoiler_NG_connected_USD,TODO - Unit: TODO
     Opex_fixed_SC_ET_connected_USD,TODO - Unit: TODO
     Opex_fixed_SC_FP_connected_USD,TODO - Unit: TODO
     Opex_fixed_SeasonalStorage_WS_connected_USD,TODO - Unit: TODO
     Opex_fixed_SubstationsHeating_connected_USD,TODO - Unit: TODO
     Opex_var_DB_connected_USD,TODO - Unit: TODO
     Opex_var_GRID_exports_connected_USD,TODO - Unit: TODO
     Opex_var_GRID_imports_connected_USD,TODO - Unit: TODO
     Opex_var_NG_connected_USD,TODO - Unit: TODO
     Opex_var_WB_connected_USD,TODO - Unit: TODO
     PEN_DB_connected_MJoilyr,TODO - Unit: TODO
     PEN_GRID_exports_connected_MJoilyr,TODO - Unit: TODO
     PEN_GRID_imports_connected_MJoilyr,TODO - Unit: TODO
     PEN_NG_connected_MJoilyr,TODO - Unit: TODO
     PEN_WB_connected_MJoilyr,TODO - Unit: TODO


get_optimization_slave_cooling_activation_pattern
-------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_2_Cooling_Activation_Pattern.csv**
    :header: "Variable", "Description"

     DATE,TODO - Unit: TODO


get_optimization_slave_disconnected_performance
-----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_0_buildings_disconnected_performance.csv**
    :header: "Variable", "Description"

     Capex_a_cooling_disconnected_USD,TODO - Unit: TODO
     Capex_a_heating_disconnected_USD,TODO - Unit: TODO
     Capex_total_cooling_disconnected_USD,TODO - Unit: TODO
     Capex_total_heating_disconnected_USD,TODO - Unit: TODO
     GHG_cooling_disconnected_tonCO2,TODO - Unit: TODO
     GHG_heating_disconnected_tonCO2,TODO - Unit: TODO
     Opex_fixed_cooling_disconnected_USD,TODO - Unit: TODO
     Opex_fixed_heating_disconnected_USD,TODO - Unit: TODO
     Opex_var_cooling_disconnected_USD,TODO - Unit: TODO
     Opex_var_heating_disconnected_USD,TODO - Unit: TODO
     PEN_cooling_disconnected_MJoil,TODO - Unit: TODO
     PEN_heating_disconnected_MJoil,TODO - Unit: TODO


get_optimization_slave_electricity_activation_pattern
-----------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_1_Electricity_Activation_Pattern.csv**
    :header: "Variable", "Description"

     DATE,TODO - Unit: TODO
     E_CHP_gen_directload_W,TODO - Unit: TODO
     E_CHP_gen_export_W,TODO - Unit: TODO
     E_Furnace_dry_gen_directload_W,TODO - Unit: TODO
     E_Furnace_dry_gen_export_W,TODO - Unit: TODO
     E_Furnace_wet_gen_directload_W,TODO - Unit: TODO
     E_Furnace_wet_gen_export_W,TODO - Unit: TODO
     E_GRID_directload_W,TODO - Unit: TODO
     E_PVT_gen_directload_W,TODO - Unit: TODO
     E_PVT_gen_export_W,TODO - Unit: TODO
     E_PV_gen_directload_W,TODO - Unit: TODO
     E_PV_gen_export_W,TODO - Unit: TODO
     E_Trigen_gen_directload_W,TODO - Unit: TODO
     E_Trigen_gen_export_W,TODO - Unit: TODO


get_optimization_slave_electricity_requirements_data
----------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_1/ind_1_Electricity_Requirements_Pattern.csv**
    :header: "Variable", "Description"

     DATE,TODO - Unit: TODO
     E_BackupBoiler_req_W,TODO - Unit: TODO
     E_BackupVCC_AS_req_W,TODO - Unit: TODO
     E_BaseBoiler_req_W,TODO - Unit: TODO
     E_BaseVCC_AS_req_W,TODO - Unit: TODO
     E_BaseVCC_WS_req_W,TODO - Unit: TODO
     E_DCN_req_W,TODO - Unit: TODO
     E_DHN_req_W,TODO - Unit: TODO
     E_GHP_req_W,TODO - Unit: TODO
     E_HP_Lake_req_W,TODO - Unit: TODO
     E_HP_PVT_req_W,TODO - Unit: TODO
     E_HP_SC_ET_req_W,TODO - Unit: TODO
     E_HP_SC_FP_req_W,TODO - Unit: TODO
     E_HP_Server_req_W,TODO - Unit: TODO
     E_HP_Sew_req_W,TODO - Unit: TODO
     E_PeakBoiler_req_W,TODO - Unit: TODO
     E_PeakVCC_AS_req_W,TODO - Unit: TODO
     E_PeakVCC_WS_req_W,TODO - Unit: TODO
     E_Storage_charging_req_W,TODO - Unit: TODO
     E_Storage_discharging_req_W,TODO - Unit: TODO
     E_cs_cre_cdata_req_connected_W,TODO - Unit: TODO
     E_cs_cre_cdata_req_disconnected_W,TODO - Unit: TODO
     E_electricalnetwork_sys_req_W,TODO - Unit: TODO
     E_hs_ww_req_connected_W,TODO - Unit: TODO
     E_hs_ww_req_disconnected_W,TODO - Unit: TODO
     Eal_req_W,TODO - Unit: TODO
     Eaux_req_W,TODO - Unit: TODO
     Edata_req_W,TODO - Unit: TODO
     Epro_req_W,TODO - Unit: TODO


get_optimization_slave_heating_activation_pattern
-------------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_2/ind_0_Heating_Activation_Pattern.csv**
    :header: "Variable", "Description"

     DATE,TODO - Unit: TODO
     E_CHP_gen_W,TODO - Unit: TODO
     E_Furnace_dry_gen_W,TODO - Unit: TODO
     E_Furnace_wet_gen_W,TODO - Unit: TODO
     E_PVT_gen_W,TODO - Unit: TODO
     Q_BackupBoiler_gen_directload_W,TODO - Unit: TODO
     Q_BaseBoiler_gen_directload_W,TODO - Unit: TODO
     Q_CHP_gen_directload_W,TODO - Unit: TODO
     Q_Furnace_dry_gen_directload_W,TODO - Unit: TODO
     Q_Furnace_wet_gen_directload_W,TODO - Unit: TODO
     Q_GHP_gen_directload_W,TODO - Unit: TODO
     Q_HP_Lake_gen_directload_W,TODO - Unit: TODO
     Q_HP_Server_gen_directload_W,TODO - Unit: TODO
     Q_HP_Server_storage_W,TODO - Unit: TODO
     Q_HP_Sew_gen_directload_W,TODO - Unit: TODO
     Q_PVT_gen_directload_W,TODO - Unit: TODO
     Q_PVT_gen_storage_W,TODO - Unit: TODO
     Q_PeakBoiler_gen_directload_W,TODO - Unit: TODO
     Q_SC_ET_gen_directload_W,TODO - Unit: TODO
     Q_SC_ET_gen_storage_W,TODO - Unit: TODO
     Q_SC_FP_gen_directload_W,TODO - Unit: TODO
     Q_SC_FP_gen_storage_W,TODO - Unit: TODO
     Q_Storage_gen_directload_W,TODO - Unit: TODO
     Q_districtheating_sys_req_W,TODO - Unit: TODO


get_optimization_slave_total_performance
----------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/slave/gen_0/ind_2_total_performance.csv**
    :header: "Variable", "Description"

     Capex_a_sys_USD,TODO - Unit: TODO
     Capex_a_sys_connected_USD,TODO - Unit: TODO
     Capex_a_sys_disconnected_USD,TODO - Unit: TODO
     Capex_total_sys_USD,TODO - Unit: TODO
     Capex_total_sys_connected_USD,TODO - Unit: TODO
     Capex_total_sys_disconnected_USD,TODO - Unit: TODO
     GHG_sys_connected_tonCO2,TODO - Unit: TODO
     GHG_sys_disconnected_tonCO2,TODO - Unit: TODO
     GHG_sys_tonCO2,TODO - Unit: TODO
     Opex_a_sys_USD,TODO - Unit: TODO
     Opex_a_sys_connected_USD,TODO - Unit: TODO
     Opex_a_sys_disconnected_USD,TODO - Unit: TODO
     PEN_sys_MJoil,TODO - Unit: TODO
     PEN_sys_connected_MJoil,TODO - Unit: TODO
     PEN_sys_disconnected_MJoil,TODO - Unit: TODO
     TAC_sys_USD,TODO - Unit: TODO
     TAC_sys_connected_USD,TODO - Unit: TODO
     TAC_sys_disconnected_USD,TODO - Unit: TODO


get_optimization_substations_results_file
-----------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/substations/110011011DH_B001_result.csv**
    :header: "Variable", "Description"

     A_hex_dhw_design_m2,TODO - Unit: TODO
     A_hex_heating_design_m2,TODO - Unit: TODO
     Q_dhw_W,TODO - Unit: TODO
     Q_heating_W,TODO - Unit: TODO
     T_return_DH_result_K,TODO - Unit: TODO
     T_supply_DH_result_K,TODO - Unit: TODO
     mdot_DH_result_kgpers,TODO - Unit: TODO


get_optimization_substations_total_file
---------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/optimization/substations/Total_DH_111111111.csv**
    :header: "Variable", "Description"

     Af_m2,TODO - Unit: TODO
     Aocc_m2,TODO - Unit: TODO
     Aroof_m2,TODO - Unit: TODO
     COAL_hs0_kW,TODO - Unit: TODO
     COAL_hs_MWhyr,TODO - Unit: TODO
     COAL_ww0_kW,TODO - Unit: TODO
     COAL_ww_MWhyr,TODO - Unit: TODO
     DC_cdata0_kW,TODO - Unit: TODO
     DC_cdata_MWhyr,TODO - Unit: TODO
     DC_cre0_kW,TODO - Unit: TODO
     DC_cre_MWhyr,TODO - Unit: TODO
     DC_cs0_kW,TODO - Unit: TODO
     DC_cs_MWhyr,TODO - Unit: TODO
     DH_hs0_kW,TODO - Unit: TODO
     DH_hs_MWhyr,TODO - Unit: TODO
     DH_ww0_kW,TODO - Unit: TODO
     DH_ww_MWhyr,TODO - Unit: TODO
     E_cdata0_kW,TODO - Unit: TODO
     E_cdata_MWhyr,TODO - Unit: TODO
     E_cre0_kW,TODO - Unit: TODO
     E_cre_MWhyr,TODO - Unit: TODO
     E_cs0_kW,TODO - Unit: TODO
     E_cs_MWhyr,TODO - Unit: TODO
     E_hs0_kW,TODO - Unit: TODO
     E_hs_MWhyr,TODO - Unit: TODO
     E_sys0_kW,TODO - Unit: TODO
     E_sys_MWhyr,TODO - Unit: TODO
     E_ww0_kW,TODO - Unit: TODO
     E_ww_MWhyr,TODO - Unit: TODO
     Ea0_kW,TODO - Unit: TODO
     Ea_MWhyr,TODO - Unit: TODO
     Eal0_kW,TODO - Unit: TODO
     Eal_MWhyr,TODO - Unit: TODO
     Eaux0_kW,TODO - Unit: TODO
     Eaux_MWhyr,TODO - Unit: TODO
     Edata0_kW,TODO - Unit: TODO
     Edata_MWhyr,TODO - Unit: TODO
     El0_kW,TODO - Unit: TODO
     El_MWhyr,TODO - Unit: TODO
     Epro0_kW,TODO - Unit: TODO
     Epro_MWhyr,TODO - Unit: TODO
     GFA_m2,TODO - Unit: TODO
     GRID0_kW,TODO - Unit: TODO
     GRID_MWhyr,TODO - Unit: TODO
     GRID_a0_kW,TODO - Unit: TODO
     GRID_a_MWhyr,TODO - Unit: TODO
     GRID_aux0_kW,TODO - Unit: TODO
     GRID_aux_MWhyr,TODO - Unit: TODO
     GRID_cdata0_kW,TODO - Unit: TODO
     GRID_cdata_MWhyr,TODO - Unit: TODO
     GRID_cre0_kW,TODO - Unit: TODO
     GRID_cre_MWhyr,TODO - Unit: TODO
     GRID_cs0_kW,TODO - Unit: TODO
     GRID_cs_MWhyr,TODO - Unit: TODO
     GRID_data0_kW,TODO - Unit: TODO
     GRID_data_MWhyr,TODO - Unit: TODO
     GRID_hs0_kW,TODO - Unit: TODO
     GRID_hs_MWhyr,TODO - Unit: TODO
     GRID_l0_kW,TODO - Unit: TODO
     GRID_l_MWhyr,TODO - Unit: TODO
     GRID_pro0_kW,TODO - Unit: TODO
     GRID_pro_MWhyr,TODO - Unit: TODO
     GRID_ww0_kW,TODO - Unit: TODO
     GRID_ww_MWhyr,TODO - Unit: TODO
     NG_hs0_kW,TODO - Unit: TODO
     NG_hs_MWhyr,TODO - Unit: TODO
     NG_ww0_kW,TODO - Unit: TODO
     NG_ww_MWhyr,TODO - Unit: TODO
     Name,TODO - Unit: TODO
     OIL_hs0_kW,TODO - Unit: TODO
     OIL_hs_MWhyr,TODO - Unit: TODO
     OIL_ww0_kW,TODO - Unit: TODO
     OIL_ww_MWhyr,TODO - Unit: TODO
     PV0_kW,TODO - Unit: TODO
     PV_MWhyr,TODO - Unit: TODO
     QC_sys0_kW,TODO - Unit: TODO
     QC_sys_MWhyr,TODO - Unit: TODO
     QH_sys0_kW,TODO - Unit: TODO
     QH_sys_MWhyr,TODO - Unit: TODO
     Qcdata0_kW,TODO - Unit: TODO
     Qcdata_MWhyr,TODO - Unit: TODO
     Qcdata_sys0_kW,TODO - Unit: TODO
     Qcdata_sys_MWhyr,TODO - Unit: TODO
     Qcpro_sys0_kW,TODO - Unit: TODO
     Qcpro_sys_MWhyr,TODO - Unit: TODO
     Qcre0_kW,TODO - Unit: TODO
     Qcre_MWhyr,TODO - Unit: TODO
     Qcre_sys0_kW,TODO - Unit: TODO
     Qcre_sys_MWhyr,TODO - Unit: TODO
     Qcs0_kW,TODO - Unit: TODO
     Qcs_MWhyr,TODO - Unit: TODO
     Qcs_dis_ls0_kW,TODO - Unit: TODO
     Qcs_dis_ls_MWhyr,TODO - Unit: TODO
     Qcs_em_ls0_kW,TODO - Unit: TODO
     Qcs_em_ls_MWhyr,TODO - Unit: TODO
     Qcs_lat_ahu0_kW,TODO - Unit: TODO
     Qcs_lat_ahu_MWhyr,TODO - Unit: TODO
     Qcs_lat_aru0_kW,TODO - Unit: TODO
     Qcs_lat_aru_MWhyr,TODO - Unit: TODO
     Qcs_lat_sys0_kW,TODO - Unit: TODO
     Qcs_lat_sys_MWhyr,TODO - Unit: TODO
     Qcs_sen_ahu0_kW,TODO - Unit: TODO
     Qcs_sen_ahu_MWhyr,TODO - Unit: TODO
     Qcs_sen_aru0_kW,TODO - Unit: TODO
     Qcs_sen_aru_MWhyr,TODO - Unit: TODO
     Qcs_sen_scu0_kW,TODO - Unit: TODO
     Qcs_sen_scu_MWhyr,TODO - Unit: TODO
     Qcs_sen_sys0_kW,TODO - Unit: TODO
     Qcs_sen_sys_MWhyr,TODO - Unit: TODO
     Qcs_sys0_kW,TODO - Unit: TODO
     Qcs_sys_MWhyr,TODO - Unit: TODO
     Qcs_sys_ahu0_kW,TODO - Unit: TODO
     Qcs_sys_ahu_MWhyr,TODO - Unit: TODO
     Qcs_sys_aru0_kW,TODO - Unit: TODO
     Qcs_sys_aru_MWhyr,TODO - Unit: TODO
     Qcs_sys_scu0_kW,TODO - Unit: TODO
     Qcs_sys_scu_MWhyr,TODO - Unit: TODO
     Qhpro_sys0_kW,TODO - Unit: TODO
     Qhpro_sys_MWhyr,TODO - Unit: TODO
     Qhs0_kW,TODO - Unit: TODO
     Qhs_MWhyr,TODO - Unit: TODO
     Qhs_dis_ls0_kW,TODO - Unit: TODO
     Qhs_dis_ls_MWhyr,TODO - Unit: TODO
     Qhs_em_ls0_kW,TODO - Unit: TODO
     Qhs_em_ls_MWhyr,TODO - Unit: TODO
     Qhs_lat_ahu0_kW,TODO - Unit: TODO
     Qhs_lat_ahu_MWhyr,TODO - Unit: TODO
     Qhs_lat_aru0_kW,TODO - Unit: TODO
     Qhs_lat_aru_MWhyr,TODO - Unit: TODO
     Qhs_lat_sys0_kW,TODO - Unit: TODO
     Qhs_lat_sys_MWhyr,TODO - Unit: TODO
     Qhs_sen_ahu0_kW,TODO - Unit: TODO
     Qhs_sen_ahu_MWhyr,TODO - Unit: TODO
     Qhs_sen_aru0_kW,TODO - Unit: TODO
     Qhs_sen_aru_MWhyr,TODO - Unit: TODO
     Qhs_sen_shu0_kW,TODO - Unit: TODO
     Qhs_sen_shu_MWhyr,TODO - Unit: TODO
     Qhs_sen_sys0_kW,TODO - Unit: TODO
     Qhs_sen_sys_MWhyr,TODO - Unit: TODO
     Qhs_sys0_kW,TODO - Unit: TODO
     Qhs_sys_MWhyr,TODO - Unit: TODO
     Qhs_sys_ahu0_kW,TODO - Unit: TODO
     Qhs_sys_ahu_MWhyr,TODO - Unit: TODO
     Qhs_sys_aru0_kW,TODO - Unit: TODO
     Qhs_sys_aru_MWhyr,TODO - Unit: TODO
     Qhs_sys_shu0_kW,TODO - Unit: TODO
     Qhs_sys_shu_MWhyr,TODO - Unit: TODO
     Qww0_kW,TODO - Unit: TODO
     Qww_MWhyr,TODO - Unit: TODO
     Qww_sys0_kW,TODO - Unit: TODO
     Qww_sys_MWhyr,TODO - Unit: TODO
     SOLAR_hs0_kW,TODO - Unit: TODO
     SOLAR_hs_MWhyr,TODO - Unit: TODO
     SOLAR_ww0_kW,TODO - Unit: TODO
     SOLAR_ww_MWhyr,TODO - Unit: TODO
     Unnamed: 0,TODO - Unit: TODO
     WOOD_hs0_kW,TODO - Unit: TODO
     WOOD_hs_MWhyr,TODO - Unit: TODO
     WOOD_ww0_kW,TODO - Unit: TODO
     WOOD_ww_MWhyr,TODO - Unit: TODO
     people0,TODO - Unit: TODO


get_radiation_building
----------------------

The following file is used by scripts: ['demand', 'photovoltaic', 'photovoltaic_thermal', 'solar_collector']



.. csv-table:: **outputs/data/solar-radiation/B001_radiation.csv**
    :header: "Variable", "Description"

     Date,TODO - Unit: TODO
     roofs_top_kW,TODO - Unit: TODO
     roofs_top_m2,TODO - Unit: TODO
     walls_east_kW,TODO - Unit: TODO
     walls_east_m2,TODO - Unit: TODO
     walls_north_kW,TODO - Unit: TODO
     walls_north_m2,TODO - Unit: TODO
     walls_south_kW,TODO - Unit: TODO
     walls_south_m2,TODO - Unit: TODO
     walls_west_kW,TODO - Unit: TODO
     walls_west_m2,TODO - Unit: TODO
     windows_east_kW,TODO - Unit: TODO
     windows_east_m2,TODO - Unit: TODO
     windows_north_kW,TODO - Unit: TODO
     windows_north_m2,TODO - Unit: TODO
     windows_south_kW,TODO - Unit: TODO
     windows_south_m2,TODO - Unit: TODO
     windows_west_kW,TODO - Unit: TODO
     windows_west_m2,TODO - Unit: TODO


get_radiation_building_sensors
------------------------------

The following file is used by scripts: ['demand', 'photovoltaic', 'photovoltaic_thermal', 'solar_collector']



.. csv-table:: **outputs/data/solar-radiation/B001_insolation_Whm2.json**
    :header: "Variable", "Description"

     srf0,TODO - Unit: TODO


get_radiation_materials
-----------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/solar-radiation/buidling_materials.csv**
    :header: "Variable", "Description"

     G_win,TODO - Unit: TODO
     Name,TODO - Unit: TODO
     r_roof,TODO - Unit: TODO
     r_wall,TODO - Unit: TODO
     type_roof,TODO - Unit: TODO
     type_wall,TODO - Unit: TODO
     type_win,TODO - Unit: TODO


get_radiation_metadata
----------------------

The following file is used by scripts: ['demand', 'photovoltaic', 'photovoltaic_thermal', 'solar_collector']



.. csv-table:: **outputs/data/solar-radiation/B001_geometry.csv**
    :header: "Variable", "Description"

     intersection,TODO - Unit: TODO


get_schedule_model_file
-----------------------

The following file is used by scripts: ['demand']



.. csv-table:: **outputs/data/occupancy/B001.csv**
    :header: "Variable", "Description"

     DATE,TODO - Unit: TODO
     Ea_W,TODO - Unit: TODO
     Ed_W,TODO - Unit: TODO
     El_W,TODO - Unit: TODO
     Epro_W,TODO - Unit: TODO
     Qcpro_W,TODO - Unit: TODO
     Qcre_W,TODO - Unit: TODO
     Qhpro_W,TODO - Unit: TODO
     Qs_W,TODO - Unit: TODO
     Tcs_set_C,TODO - Unit: TODO
     Ths_set_C,TODO - Unit: TODO
     Ve_lps,TODO - Unit: TODO
     Vw_lph,TODO - Unit: TODO
     Vww_lph,TODO - Unit: TODO
     X_gh,TODO - Unit: TODO
     people_pax,TODO - Unit: TODO


get_sewage_heat_potential
-------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/Sewage_heat_potential.csv**
    :header: "Variable", "Description"

     Qsw_kW,TODO - Unit: TODO
     T_in_HP_C,TODO - Unit: TODO
     T_in_sw_C,TODO - Unit: TODO
     T_out_HP_C,TODO - Unit: TODO
     T_out_sw_C,TODO - Unit: TODO
     Ts_C,TODO - Unit: TODO
     mww_zone_kWperC,TODO - Unit: TODO


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

     D_int_m,TODO - Unit: TODO
     Pipe_DN,TODO - Unit: TODO
     Type_mat,TODO - Unit: TODO
     length_m,TODO - Unit: TODO


get_thermal_network_layout_massflow_edges_file
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__massflow_edges_kgs.csv**
    :header: "Variable", "Description"

     PIPE0,TODO - Unit: TODO


get_thermal_network_layout_massflow_nodes_file
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__massflow_nodes_kgs.csv**
    :header: "Variable", "Description"

     NODE0,TODO - Unit: TODO


get_thermal_network_node_types_csv_file
---------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__metadata_nodes.csv**
    :header: "Variable", "Description"

     Building,TODO - Unit: TODO
     Type,TODO - Unit: TODO


get_thermal_network_plant_heat_requirement_file
-----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__plant_thermal_load_kW.csv**
    :header: "Variable", "Description"

     NONE,TODO - Unit: TODO


get_thermal_network_pressure_losses_edges_file
----------------------------------------------

The following file is used by scripts: []



.. csv-table:: **outputs/data/thermal-network/DH__pressure_losses_edges_kW.csv**
    :header: "Variable", "Description"

     PIPE0,TODO - Unit: TODO


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

     PIPE0,TODO - Unit: TODO


get_total_demand
----------------

The following file is used by scripts: ['decentralized', 'emissions', 'network_layout', 'system_costs', 'optimization', 'sewage_potential', 'thermal_network']



.. csv-table:: **outputs/data/demand/Total_demand.csv**
    :header: "Variable", "Description"

     Ea0_kW,TODO - Unit: TODO
     Ea_MWhyr,TODO - Unit: TODO
     El0_kW,TODO - Unit: TODO
     El_MWhyr,TODO - Unit: TODO
     GRID_a0_kW,TODO - Unit: TODO
     GRID_a_MWhyr,TODO - Unit: TODO
     GRID_aux0_kW,TODO - Unit: TODO
     GRID_aux_MWhyr,TODO - Unit: TODO
     GRID_cdata0_kW,TODO - Unit: TODO
     GRID_cdata_MWhyr,TODO - Unit: TODO
     GRID_cre0_kW,TODO - Unit: TODO
     GRID_cre_MWhyr,TODO - Unit: TODO
     GRID_cs0_kW,TODO - Unit: TODO
     GRID_cs_MWhyr,TODO - Unit: TODO
     GRID_data0_kW,TODO - Unit: TODO
     GRID_data_MWhyr,TODO - Unit: TODO
     GRID_hs0_kW,TODO - Unit: TODO
     GRID_hs_MWhyr,TODO - Unit: TODO
     GRID_l0_kW,TODO - Unit: TODO
     GRID_l_MWhyr,TODO - Unit: TODO
     GRID_pro0_kW,TODO - Unit: TODO
     GRID_pro_MWhyr,TODO - Unit: TODO
     GRID_ww0_kW,TODO - Unit: TODO
     GRID_ww_MWhyr,TODO - Unit: TODO


get_water_body_potential
------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/potentials/Water_body_potential.csv**
    :header: "Variable", "Description"

     QLake_kW,TODO - Unit: TODO
     Ts_C,TODO - Unit: TODO


get_weather_file
----------------

The following file is used by scripts: ['decentralized', 'demand', 'optimization', 'photovoltaic', 'photovoltaic_thermal', 'radiation', 'schedule_maker', 'shallow_geothermal_potential', 'solar_collector', 'thermal_network']



.. csv-table:: **inputs/weather/weather.epw**
    :header: "Variable", "Description"


