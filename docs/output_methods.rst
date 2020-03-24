
get_building_typology
---------------------

path: ``inputs/building-properties/typology.dbf``

The following file is used by these scripts: ``archetypes_mapper``, ``demand``, ``emissions``


.. csv-table::
    :header: "Variable", "Description"

    ``3rd_USE``, "TODO"
    ``REFERENCE``, "TODO"
    ``1st_USE``, "TODO"
    ``STANDARD``, "Construction Standard"
    ``3rd_USE_R``, "TODO"
    ``1st_USE_R``, "TODO"
    ``YEAR``, "Construction year"
    ``2nd_USE``, "TODO"
    ``2nd_USE_R``, "TODO"
    ``Name``, "Unique building ID. It must start with a letter."
    


get_network_temperature_plant
-----------------------------

path: ``outputs/data/thermal-network/DH__temperature_plant_K.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``temperature_return_K``, "TODO"
    ``temperature_supply_K``, "TODO"
    


get_optimization_slave_heating_activation_pattern
-------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_0_Heating_Activation_Pattern.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Q_Storage_gen_directload_W``, "TODO"
    ``E_Furnace_wet_gen_W``, "TODO"
    ``Q_HP_Lake_gen_directload_W``, "TODO"
    ``Q_BaseBoiler_gen_directload_W``, "TODO"
    ``Q_SC_ET_gen_storage_W``, "TODO"
    ``Q_SC_ET_gen_directload_W``, "TODO"
    ``Q_Furnace_wet_gen_directload_W``, "TODO"
    ``Q_BackupBoiler_gen_directload_W``, "TODO"
    ``E_PVT_gen_W``, "TODO"
    ``Q_SC_FP_gen_directload_W``, "TODO"
    ``Q_HP_Server_gen_directload_W``, "TODO"
    ``DATE``, "TODO"
    ``Q_HP_Sew_gen_directload_W``, "TODO"
    ``Q_districtheating_sys_req_W``, "TODO"
    ``Q_SC_FP_gen_storage_W``, "TODO"
    ``Q_Furnace_dry_gen_directload_W``, "TODO"
    ``E_Furnace_dry_gen_W``, "TODO"
    ``E_CHP_gen_W``, "TODO"
    ``Q_CHP_gen_directload_W``, "TODO"
    ``Q_GHP_gen_directload_W``, "TODO"
    ``Q_PVT_gen_directload_W``, "TODO"
    ``Q_PeakBoiler_gen_directload_W``, "TODO"
    ``Q_PVT_gen_storage_W``, "TODO"
    ``Q_HP_Server_storage_W``, "TODO"
    


get_thermal_network_plant_heat_requirement_file
-----------------------------------------------

path: ``outputs/data/thermal-network/DH__plant_thermal_load_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NONE``, "TODO"
    


get_network_energy_pumping_requirements_file
--------------------------------------------

path: ``outputs/data/thermal-network/DH__plant_pumping_load_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``pressure_loss_supply_kW``, "TODO"
    ``pressure_loss_return_kW``, "TODO"
    ``pressure_loss_substations_kW``, "TODO"
    ``pressure_loss_total_kW``, "TODO"
    


get_thermal_network_layout_massflow_edges_file
----------------------------------------------

path: ``outputs/data/thermal-network/DH__massflow_edges_kgs.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    


get_sewage_heat_potential
-------------------------

path: ``outputs/data/potentials/Sewage_heat_potential.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``T_out_HP_C``, "TODO"
    ``Ts_C``, "TODO"
    ``T_out_sw_C``, "TODO"
    ``T_in_sw_C``, "TODO"
    ``T_in_HP_C``, "TODO"
    ``mww_zone_kWperC``, "TODO"
    ``Qsw_kW``, "TODO"
    


get_optimization_slave_electricity_activation_pattern
-----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_1_Electricity_Activation_Pattern.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``E_Furnace_dry_gen_export_W``, "TODO"
    ``E_Furnace_dry_gen_directload_W``, "TODO"
    ``E_CHP_gen_directload_W``, "TODO"
    ``E_Furnace_wet_gen_directload_W``, "TODO"
    ``E_GRID_directload_W``, "TODO"
    ``E_PV_gen_directload_W``, "TODO"
    ``E_PVT_gen_directload_W``, "TODO"
    ``E_Trigen_gen_export_W``, "TODO"
    ``E_Furnace_wet_gen_export_W``, "TODO"
    ``E_PV_gen_export_W``, "TODO"
    ``E_PVT_gen_export_W``, "TODO"
    ``DATE``, "TODO"
    ``E_CHP_gen_export_W``, "TODO"
    ``E_Trigen_gen_directload_W``, "TODO"
    


get_demand_results_file
-----------------------

path: ``outputs/data/demand/B001.csv``

The following file is used by these scripts: ``decentralized``, ``optimization``, ``sewage_potential``, ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``Qcs_sys_scu_kWh``, "SCU system cool demand"
    ``COAL_ww_kWh``, "Coal requirement for hotwater supply"
    ``Qhs_lat_aru_kWh``, "ARU latent heat demand"
    ``SOLAR_hs_kWh``, "Solar thermal energy requirement for space heating supply"
    ``Qcdata_sys_kWh``, "End-use data center cooling demand"
    ``Qhpro_sys_kWh``, "Process heat demand"
    ``GRID_data_kWh``, "kWh"
    ``GRID_pro_kWh``, "kWh"
    ``Qhs_sys_kWh``, "End-use space heating demand"
    ``Qcre_sys_kWh``, "End-use refrigeration demand"
    ``Tww_sys_sup_C``, "Supply temperature hotwater system"
    ``E_ww_kWh``, "Hot water system electricity consumption."
    ``mcphs_sys_ahu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to air handling units (space heating)."
    ``Qhs_sen_aru_kWh``, "ARU sensible heat demand"
    ``SOLAR_ww_kWh``, "Solar thermal energy requirement for hotwater supply"
    ``mcpcs_sys_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to space cooling."
    ``Qhs_sys_aru_kWh``, "ARU system heat demand"
    ``E_cre_kWh``, "Refrigeration system electricity consumption."
    ``Ths_sys_sup_ahu_C``, "Supply temperature heating system"
    ``Q_gain_sen_app_kWh``, "Sensible heat gain from appliances"
    ``Ths_sys_sup_aru_C``, "Supply temperature heating system"
    ``GRID_ww_kWh``, "kWh"
    ``Eal_kWh``, "End-use electricity consumption of appliances and lights"
    ``Qhs_em_ls_kWh``, "Heating system emission losses"
    ``DC_cdata_kWh``, "District cooling for data center cooling demand"
    ``GRID_l_kWh``, "kWh"
    ``T_int_C``, "Indoor temperature"
    ``Tcs_sys_sup_scu_C``, "Supply temperature cooling system"
    ``Q_gain_sen_base_kWh``, "Sensible heat gain from transmission through the base"
    ``Ea_kWh``, "TODO"
    ``Qcs_sen_aru_kWh``, "ARU sensible cool demand"
    ``Tcs_sys_re_scu_C``, "Return temperature cooling system"
    ``Qcs_sen_scu_kWh``, "SHU sensible cool demand"
    ``mcphs_sys_aru_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to air recirculation units (space heating)."
    ``mcpcs_sys_scu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to sensible cooling units (space cooling)."
    ``Qcre_kWh``, "Refrigeration space cooling demand"
    ``people``, "Predicted occupancy: number of people in building"
    ``Qcs_sys_ahu_kWh``, "AHU system cool demand"
    ``mcptw_kWperC``, "Capacity flow rate (mass flow* specific heat capaicty) of the fresh water"
    ``Tcs_sys_re_aru_C``, "Return temperature cooling system"
    ``Name``, "Unique building ID. It must start with a letter."
    ``Qhs_kWh``, "Sensible heating system demand"
    ``mcpww_sys_kWperC``, "Capacity flow rate (mass flow* specific heat capaicty) of domestic hot water"
    ``Ths_sys_sup_C``, "Heating system supply temperature."
    ``Tww_sys_re_C``, "Return temperature hotwater system"
    ``GRID_cdata_kWh``, "kWh"
    ``Q_gain_sen_wall_kWh``, "Sensible heat gain from transmission through the walls"
    ``QC_sys_kWh``, "Total cool consumption"
    ``Ths_sys_sup_shu_C``, "Supply temperature heating system"
    ``Tcdata_sys_re_C``, "Cooling supply temperature of the data centre"
    ``DH_ww_kWh``, "Energy requirement by district heating (hotwater supply)"
    ``E_cdata_kWh``, "Data centre cooling specific electricity consumption."
    ``mcpcs_sys_aru_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to air recirculation units (space cooling)."
    ``PV_kWh``, "PV electricity consumption"
    ``WOOD_ww_kWh``, "WOOD requirement for hotwater supply"
    ``Qhs_sys_ahu_kWh``, "AHU system heat demand"
    ``Q_gain_sen_vent_kWh``, "Sensible heat gain from ventilation and infiltration"
    ``Qcs_em_ls_kWh``, "Cooling system emission losses"
    ``I_rad_kWh``, "Radiative heat loss"
    ``Qcdata_kWh``, "Data centre space cooling demand"
    ``DC_cre_kWh``, "District cooling for refrigeration demand"
    ``Q_gain_lat_peop_kWh``, "Latent heat gain from people"
    ``Ths_sys_re_ahu_C``, "Return temperature heating system"
    ``Qhs_lat_sys_kWh``, "Total latent heat demand for all systems"
    ``GRID_cs_kWh``, "kWh"
    ``Qcs_sys_kWh``, "End-use space cooling demand"
    ``Qcs_lat_aru_kWh``, "ARU latent cool demand"
    ``Qhs_lat_ahu_kWh``, "AHU latent heat demand"
    ``E_sys_kWh``, "End-use total electricity system consumption = Ea + El + Edata + Epro + Eaux "
    ``Qcs_sys_aru_kWh``, "ARU system cool demand"
    ``Qhs_sen_shu_kWh``, "SHU sensible heat demand"
    ``COAL_hs_kWh``, "Coal requirement for space heating supply"
    ``Qhs_sys_shu_kWh``, "SHU system heat demand"
    ``Tcs_sys_re_C``, "System cooling return temperature."
    ``Tcs_sys_sup_ahu_C``, "Supply temperature cooling system"
    ``Qhs_dis_ls_kWh``, "Heating system distribution losses"
    ``mcpcre_sys_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to refrigeration."
    ``OIL_ww_kWh``, "OIL requirement for hotwater supply"
    ``x_int``, "Internal mass fraction of humidity (water/dry air)"
    ``Qhs_sen_ahu_kWh``, "AHU sensible heat demand"
    ``Q_gain_sen_data_kWh``, "Sensible heat gain from data centres"
    ``GRID_hs_kWh``, "kWh"
    ``T_ext_C``, "Outdoor temperature"
    ``DC_cs_kWh``, "District cooling for space cooling demand"
    ``Tcre_sys_re_C``, "Cooling return temperature of the refrigeration system."
    ``Qcs_sen_sys_kWh``, "Total sensible cool demand for all systems"
    ``GRID_kWh``, "Grid total requirements of electricity = GRID_a + GRID_l + GRID_v +GRID_data + GRID_pro + GRID_aux + GRID_cdata + GRID_cre + GRID_hs + GRID_ww + GRID_cs"
    ``Qhs_sen_sys_kWh``, "Total sensible heat demand for all systems"
    ``I_sol_and_I_rad_kWh``, "Net radiative heat gain"
    ``Q_gain_sen_pro_kWh``, "Sensible heat gain from industrial processes."
    ``Qcpro_sys_kWh``, "Process cooling demand"
    ``NG_ww_kWh``, "NG requirement for hotwater supply"
    ``E_cs_kWh``, "Cooling system electricity consumption."
    ``Eaux_kWh``, "End-use auxiliary electricity consumption."
    ``NG_hs_kWh``, "NG requirement for space heating supply"
    ``Tcs_sys_sup_aru_C``, "Supply temperature cooling system"
    ``WOOD_hs_kWh``, "WOOD requirement for space heating supply"
    ``Tcdata_sys_sup_C``, "Cooling return temperature of the data centre"
    ``Q_loss_sen_ref_kWh``, "Sensible heat loss from refrigeration systems"
    ``El_kWh``, "TODO"
    ``Qcs_lat_ahu_kWh``, "AHU latent cool demand"
    ``mcpcdata_sys_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the chilled water delivered to data centre."
    ``Ths_sys_re_shu_C``, "Return temperature heating system"
    ``DATE``, "Time stamp for each day of the year ascending in hour intervals."
    ``mcphs_sys_shu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to sensible heating units (space heating)."
    ``Qcs_dis_ls_kWh``, "Cooling system distribution losses"
    ``Q_gain_sen_light_kWh``, "Sensible heat gain from lighting"
    ``mcphs_sys_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to space heating."
    ``Qww_sys_kWh``, "End-use hotwater demand"
    ``GRID_aux_kWh``, "kWh"
    ``Qcs_kWh``, "Specific cool demand"
    ``Qcs_sen_ahu_kWh``, "AHU sensible cool demand"
    ``mcpcs_sys_ahu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to air handling units (space cooling)."
    ``QH_sys_kWh``, "Total heat consumption"
    ``Qcs_lat_sys_kWh``, "Total latent cool demand for all systems"
    ``theta_o_C``, "Operative temperature in building (RC-model) used for comfort plotting"
    ``I_sol_kWh``, "Solar heat gain"
    ``DH_hs_kWh``, "Energy requirement by district heating (space heating supply)"
    ``Tcre_sys_sup_C``, "Cooling supply temperature of the refrigeration system."
    ``Epro_kWh``, "End-use electricity consumption for industrial processes."
    ``GRID_a_kWh``, "kWh"
    ``Tcs_sys_sup_C``, "System cooling supply temperature."
    ``Edata_kWh``, "End-use data centre electricity consumption."
    ``Tcs_sys_re_ahu_C``, "Return temperature cooling system"
    ``Q_gain_sen_wind_kWh``, "Sensible heat gain from transmission through the windows"
    ``OIL_hs_kWh``, "OIL requirement for space heating supply"
    ``Ths_sys_re_C``, "Heating system return temperature."
    ``Qww_kWh``, "DHW specific heat demand"
    ``GRID_cre_kWh``, "kWh"
    ``Ths_sys_re_aru_C``, "Return temperature heating system"
    ``Q_gain_sen_roof_kWh``, "Sensible heat gain from transmission through the roof"
    ``E_hs_kWh``, "Heating system electricity consumption."
    ``Q_gain_sen_peop_kWh``, "Sensible heat gain from people"
    


get_optimization_generation_disconnected_performance
----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/gen_2_disconnected_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PEN_cooling_disconnected_MJoil``, "TODO"
    ``Opex_var_cooling_disconnected_USD``, "TODO"
    ``GHG_cooling_disconnected_tonCO2``, "TODO"
    ``generation``, "TODO"
    ``GHG_heating_disconnected_tonCO2``, "TODO"
    ``individual_name``, "TODO"
    ``Opex_var_heating_disconnected_USD``, "TODO"
    ``Opex_fixed_cooling_disconnected_USD``, "TODO"
    ``Capex_total_cooling_disconnected_USD``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Capex_a_cooling_disconnected_USD``, "TODO"
    ``Capex_total_heating_disconnected_USD``, "TODO"
    ``Capex_a_heating_disconnected_USD``, "TODO"
    ``individual``, "TODO"
    ``PEN_heating_disconnected_MJoil``, "TODO"
    ``Opex_fixed_heating_disconnected_USD``, "TODO"
    


get_building_weekly_schedules
-----------------------------

path: ``inputs/building-properties/schedules/B001.csv``

The following file is used by these scripts: ``demand``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``METADATA``, "TODO"
    ``mixed-schedule``, "TODO"
    


PVT_results
-----------

path: ``outputs/data/potentials/solar/B001_PVT.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Q_PVT_l_kWh``, "Collector heat loss."
    ``Q_PVT_gen_kWh``, "Total heat generated by the collector."
    ``PVT_walls_south_E_kWh``, "Electricity production from photovoltaic-thermal panels on south facades"
    ``Eaux_PVT_kWh``, "Auxiliary electricity consumed by the collector."
    ``PVT_walls_west_Q_kWh``, "Heat production from photovoltaic-thermal panels on west facades"
    ``PVT_roofs_top_Q_kWh``, "Heat production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_east_Q_kWh``, "Heat production from photovoltaic-thermal panels on east facades"
    ``Area_PVT_m2``, "Total area of investigated collector."
    ``radiation_kWh``, "Total radiatiative potential."
    ``PVT_roofs_top_m2``, "Collector surface area on roof tops."
    ``PVT_roofs_top_E_kWh``, "Electricity production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_west_m2``, "West facing wall collector surface area."
    ``T_PVT_sup_C``, "Collector heating supply temperature."
    ``PVT_walls_north_E_kWh``, "Electricity production from photovoltaic-thermal panels on north facades"
    ``T_PVT_re_C``, "Collector heating supply temperature."
    ``E_PVT_gen_kWh``, "Total electricity generated by the collector."
    ``PVT_walls_west_E_kWh``, "Electricity production from photovoltaic-thermal panels on west facades"
    ``PVT_walls_east_E_kWh``, "Electricity production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_south_Q_kWh``, "Heat production from photovoltaic-thermal panels on south facades"
    ``mcp_PVT_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector."
    ``PVT_walls_east_m2``, "Collector surface area on east facades."
    ``Date``, "Date and time in hourly steps."
    ``PVT_walls_north_Q_kWh``, "Heat production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_north_m2``, "Collector surface area on north facades."
    ``PVT_walls_south_m2``, "Collector surface area on south facades."
    


get_thermal_network_layout_massflow_nodes_file
----------------------------------------------

path: ``outputs/data/thermal-network/DH__massflow_nodes_kgs.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "TODO"
    


get_network_total_thermal_loss_file
-----------------------------------

path: ``outputs/data/thermal-network/DH__total_thermal_loss_edges_kW.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``thermal_loss_return_kW``, "TODO"
    ``thermal_loss_supply_kW``, "TODO"
    ``thermal_loss_total_kW``, "TODO"
    


get_lca_embodied
----------------

path: ``outputs/data/emissions/Total_LCA_embodied.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``GHG_sys_embodied_tonCO2``, "Building construction and decomissioning"
    ``GHG_sys_embodied_kgCO2m2``, "Building construction and decomissioning"
    ``GFA_m2``, "Gross floor area"
    ``Name``, "Unique building ID. It must start with a letter."
    


get_optimization_individuals_in_generation
------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/generation_2_individuals.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``B09_DH``, "TODO"
    ``WS_HP``, "TODO"
    ``B06_DH``, "TODO"
    ``NG_PeakBoiler``, "TODO"
    ``NG_BaseBoiler``, "TODO"
    ``B03_DH``, "TODO"
    ``B05_DH``, "TODO"
    ``DB_Cogen``, "TODO"
    ``SS_HP``, "TODO"
    ``B02_DH``, "TODO"
    ``GS_HP``, "TODO"
    ``PV``, "TODO"
    ``NG_Cogen``, "TODO"
    ``B07_DH``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``PVT``, "TODO"
    ``SC_FP``, "TODO"
    ``B08_DH``, "TODO"
    ``B01_DH``, "TODO"
    ``generation``, "TODO"
    ``individual``, "TODO"
    ``B04_DH``, "TODO"
    ``SC_ET``, "TODO"
    ``WB_Cogen``, "TODO"
    ``DS_HP``, "TODO"
    


get_optimization_substations_results_file
-----------------------------------------

path: ``outputs/data/optimization/substations/110011011DH_B001_result.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``mdot_DH_result_kgpers``, "TODO"
    ``Q_heating_W``, "TODO"
    ``A_hex_heating_design_m2``, "TODO"
    ``Q_dhw_W``, "TODO"
    ``A_hex_dhw_design_m2``, "TODO"
    ``T_supply_DH_result_K``, "TODO"
    ``T_return_DH_result_K``, "TODO"
    


get_optimization_disconnected_cooling_capacity
----------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_0_disconnected_cooling_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_DX_AS_cool_disconnected_W``, "TODO"
    ``Name``, "TODO"
    ``Capaticy_ACH_SC_ET_cool_disconnected_W``, "TODO"
    ``Capacity_ACHHT_FP_cool_disconnected_W``, "TODO"
    ``Capacity_VCCHT_AS_cool_disconnected_W``, "TODO"
    ``Capacity_BaseVCC_AS_cool_disconnected_W``, "TODO"
    ``Capacity_ACH_SC_FP_cool_disconnected_W``, "TODO"
    


get_optimization_decentralized_folder_building_cooling_activation
-----------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/{building}_{configuration}_cooling_activation.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``E_cs_cre_cdata_req_W``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``E_DX_AS_req_W``, "TODO"
    ``Q_DX_AS_gen_directload_W``, "TODO"
    


get_database_supply_assemblies
------------------------------

path: ``inputs/technology/assemblies/SUPPLY.xls``

The following file is used by these scripts: ``demand``, ``emissions``, ``system_costs``




.. csv-table:: ``inputs/technology/assemblies/SUPPLY.xls`` Worksheet: ``ELECTRICITY``
    :header: "Variable", "Description"
    ``code``, TODO``Description``, TODO``reference``, TODO``O&M_%``, TODO``LT_yr``, TODO``IR_%``, TODO``CAPEX_USD2015kW``, TODO``efficiency``, TODO``scale``, TODO``feedstock``, TODO



.. csv-table:: ``inputs/technology/assemblies/SUPPLY.xls`` Worksheet: ``HOT_WATER``
    :header: "Variable", "Description"
    ``code``, TODO``Description``, TODO``reference``, TODO``O&M_%``, TODO``LT_yr``, TODO``IR_%``, TODO``CAPEX_USD2015kW``, TODO``efficiency``, TODO``scale``, TODO``feedstock``, TODO



.. csv-table:: ``inputs/technology/assemblies/SUPPLY.xls`` Worksheet: ``COOLING``
    :header: "Variable", "Description"
    ``code``, TODO``Description``, TODO``reference``, TODO``O&M_%``, TODO``LT_yr``, TODO``IR_%``, TODO``CAPEX_USD2015kW``, TODO``efficiency``, TODO``scale``, TODO``feedstock``, TODO



.. csv-table:: ``inputs/technology/assemblies/SUPPLY.xls`` Worksheet: ``HEATING``
    :header: "Variable", "Description"
    ``code``, TODO``Description``, TODO``reference``, TODO``O&M_%``, TODO``LT_yr``, TODO``IR_%``, TODO``CAPEX_USD2015kW``, TODO``efficiency``, TODO``scale``, TODO``feedstock``, TODO




get_nominal_edge_mass_flow_csv_file
-----------------------------------

path: ``outputs/data/thermal-network/Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    ``Unnamed: 0``, "TODO"
    


get_database_use_types_properties
---------------------------------

path: ``inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx``

The following file is used by these scripts: ``archetypes_mapper``




.. csv-table:: ``inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx`` Worksheet: ``INDOOR_COMFORT``
    :header: "Variable", "Description"
    ``RH_max_pc``, TODO``code``, TODO``Tcs_set_C``, TODO``Ths_setb_C``, TODO``Ths_set_C``, TODO``Tcs_setb_C``, TODO``Ve_lpspax``, TODO``RH_min_pc``, TODO



.. csv-table:: ``inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx`` Worksheet: ``INTERNAL_LOADS``
    :header: "Variable", "Description"
    ``El_Wm2``, TODO``code``, TODO``Qhpro_Wm2``, TODO``Occ_m2pax``, TODO``Ed_Wm2``, TODO``Ea_Wm2``, TODO``Qcre_Wm2``, TODO``Ev_kWveh``, TODO``Epro_Wm2``, TODO``X_ghpax``, TODO``Vww_lpdpax``, TODO``Vw_lpdpax``, TODO``Qs_Wpax``, TODO``Qcpro_Wm2``, TODO




get_building_supply
-------------------

path: ``inputs/building-properties/supply_systems.dbf``

The following file is used by these scripts: ``decentralized``, ``demand``, ``emissions``, ``system_costs``


.. csv-table::
    :header: "Variable", "Description"

    ``type_hs``, "Type of heating supply system"
    ``type_el``, "Type of electrical supply system"
    ``Name``, "Unique building ID. It must start with a letter."
    ``type_dhw``, "Type of hot water supply system"
    ``type_cs``, "Type of cooling supply system"
    


get_database_air_conditioning_systems
-------------------------------------

path: ``inputs/technology/assemblies/HVAC.xls``

The following file is used by these scripts: ``demand``




.. csv-table:: ``inputs/technology/assemblies/HVAC.xls`` Worksheet: ``HOT_WATER``
    :header: "Variable", "Description"
    ``Qwwmax_Wm2``, TODO``code``, TODO``Description``, TODO``Tsww0_C``, TODO



.. csv-table:: ``inputs/technology/assemblies/HVAC.xls`` Worksheet: ``CONTROLLER``
    :header: "Variable", "Description"
    ``dT_Qcs``, TODO``dT_Qhs``, TODO``code``, TODO``Description``, TODO



.. csv-table:: ``inputs/technology/assemblies/HVAC.xls`` Worksheet: ``COOLING``
    :header: "Variable", "Description"
    ``Tscs0_scu_C``, TODO``Qcsmax_Wm2``, TODO``code``, TODO``Description``, TODO``dTcs0_aru_C``, TODO``class_cs``, TODO``dTcs0_ahu_C``, TODO``Tc_sup_air_aru_C``, TODO``convection_cs``, TODO``Tscs0_ahu_C``, TODO``Tscs0_aru_C``, TODO``Tc_sup_air_ahu_C``, TODO``dTcs0_scu_C``, TODO``dTcs_C``, TODO



.. csv-table:: ``inputs/technology/assemblies/HVAC.xls`` Worksheet: ``VENTILATION``
    :header: "Variable", "Description"
    ``ECONOMIZER``, TODO``code``, TODO``NIGHT_FLSH``, TODO``Description``, TODO``MECH_VENT``, TODO``WIN_VENT``, TODO``HEAT_REC``, TODO



.. csv-table:: ``inputs/technology/assemblies/HVAC.xls`` Worksheet: ``HEATING``
    :header: "Variable", "Description"
    ``Tshs0_aru_C``, TODO``code``, TODO``Description``, TODO``Tshs0_shu_C``, TODO``Tshs0_ahu_C``, TODO``Qhsmax_Wm2``, TODO``dThs0_aru_C``, TODO``dThs0_ahu_C``, TODO``dThs0_shu_C``, TODO``convection_hs``, TODO``dThs_C``, TODO``class_hs``, TODO``Th_sup_air_aru_C``, TODO``Th_sup_air_ahu_C``, TODO




get_optimization_slave_cooling_activation_pattern
-------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_2_Cooling_Activation_Pattern.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``DATE``, "TODO"
    


get_radiation_materials
-----------------------

path: ``outputs/data/solar-radiation/buidling_materials.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``type_base``, "TODO"
    ``r_wall``, "TODO"
    ``Name``, "TODO"
    ``type_floor``, "TODO"
    ``r_roof``, "TODO"
    ``type_win``, "TODO"
    ``type_roof``, "TODO"
    ``G_win``, "TODO"
    ``type_wall``, "TODO"
    


get_thermal_network_substation_ploss_file
-----------------------------------------

path: ``outputs/data/thermal-network/DH__pumping_load_due_to_substations_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``B01``, "TODO"
    


get_costs_operation_file
------------------------

path: ``outputs/data/costs/operation_costs.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``WOOD_ww_cost_m2yr``, "TODO"
    ``OIL_ww_cost_m2yr``, "TODO"
    ``COAL_ww_cost_yr``, "Operation costs of coal due to hotwater"
    ``Capex_a_sys_connected_USD``, "TODO"
    ``DH_hs_cost_m2yr``, "TODO"
    ``Opex_a_sys_connected_USD``, "TODO"
    ``DC_cre_cost_yr``, "Operation costs due to hotwater"
    ``DC_cs_cost_yr``, "Operation costs due to space cooling"
    ``Aocc_m2``, "TODO"
    ``WOOD_hs_cost_yr``, "Operation costs of wood due to space heating"
    ``COAL_hs_cost_m2yr``, "TODO"
    ``DC_cdata_cost_yr``, "Operation costs due to space heating"
    ``WOOD_ww_cost_yr``, "Operation costs of wood due to hotwater"
    ``PV_cost_yr``, "Electricity supply from PV"
    ``NG_hs_cost_m2yr``, "TODO"
    ``DH_ww_cost_m2yr``, "TODO"
    ``DH_ww_cost_yr``, "Operation costs due to hotwater"
    ``COAL_ww_cost_m2yr``, "TODO"
    ``Capex_a_sys_disconnected_USD``, "TODO"
    ``SOLAR_ww_cost_m2yr``, "TODO"
    ``PV_cost_m2yr``, "Electricity supply from PV"
    ``DC_cdata_cost_m2yr``, "TODO"
    ``GRID_cost_m2yr``, "Electricity supply from the grid"
    ``COAL_hs_cost_yr``, "Operation costs of coal due to space heating"
    ``DC_cre_cost_m2yr``, "TODO"
    ``OIL_hs_cost_m2yr``, "TODO"
    ``OIL_ww_cost_yr``, "Operation costs of oil due to hotwater"
    ``SOLAR_ww_cost_yr``, "Operation costs due to solar collectors for space heating"
    ``Opex_a_sys_disconnected_USD``, "TODO"
    ``NG_ww_cost_m2yr``, "TODO"
    ``DH_hs_cost_yr``, "Operation costs due to space heating"
    ``DC_cs_cost_m2yr``, "TODO"
    ``NG_ww_cost_yr``, "Operation costs of NG due to hotwater"
    ``SOLAR_hs_cost_yr``, "Operation costs due to solar collectors for hotwater"
    ``SOLAR_hs_cost_m2yr``, "TODO"
    ``GRID_cost_yr``, "Electricity supply from the grid"
    ``OIL_hs_cost_yr``, "Operation costs of oil due to space heating"
    ``NG_hs_cost_yr``, "Operation costs of NG due to space heating"
    ``Name``, "Unique building ID. It must start with a letter."
    ``WOOD_hs_cost_m2yr``, "TODO"
    


get_thermal_network_pressure_losses_edges_file
----------------------------------------------

path: ``outputs/data/thermal-network/DH__pressure_losses_edges_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    


get_network_linear_thermal_loss_edges_file
------------------------------------------

path: ``outputs/data/thermal-network/DH__linear_thermal_loss_edges_Wperm.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    


get_optimization_network_results_summary
----------------------------------------

path: ``outputs/data/optimization/network/DH_Network_summary_result_0x1be.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Q_DHNf_W``, "TODO"
    ``T_DHNf_sup_K``, "TODO"
    ``T_DHNf_re_K``, "TODO"
    ``mdot_DH_netw_total_kgpers``, "TODO"
    ``mcpdata_netw_total_kWperC``, "TODO"
    ``Q_DH_losses_W``, "TODO"
    ``DATE``, "TODO"
    ``Qcdata_netw_total_kWh``, "TODO"
    


get_optimization_decentralized_folder_building_result_heating_activation
------------------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/DiscOp_B001_result_heating_activation.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``BackupBoiler_Status``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Boiler_Status``, "TODO"
    ``Q_BackupBoiler_gen_directload_W``, "TODO"
    ``NG_BackupBoiler_req_Wh``, "TODO"
    ``E_hs_ww_req_W``, "TODO"
    ``NG_Boiler_req_Wh``, "TODO"
    ``Q_GHP_gen_directload_W``, "TODO"
    ``GHP_Status``, "TODO"
    ``Q_Boiler_gen_directload_W``, "TODO"
    


get_network_pressure_at_nodes
-----------------------------

path: ``outputs/data/thermal-network/DH__pressure_at_nodes_Pa.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "TODO"
    


PVT_metadata_results
--------------------

path: ``outputs/data/potentials/solar/B001_PVT_sensors.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``surface_azimuth_deg``, "Azimuth angle of the panel surface e.g. south facing = 180 deg"
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``Ycoor``, "Describes the position of the y vector."
    ``area_installed_module_m2``, "The area of the building suface covered by one solar panel"
    ``tilt_deg``, "Tilt angle of roof or walls"
    ``surface``, "Unique surface ID for each building exterior surface."
    ``Xcoor``, "Describes the position of the x vector."
    ``total_rad_Whm2``, "Total radiatiative potential of a given surfaces area."
    ``CATteta_z``, "Category according to the surface azimuth of the panel"
    ``AREA_m2``, "Surface area."
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``Ydir``, "Directional scalar of the y vector."
    ``intersection``, "TODO"
    ``B_deg``, "Tilt angle of the installed solar panels"
    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``CATB``, "Category according to the tilt angle of the panel"
    ``type_orientation``, "Concatenated surface type and orientation."
    ``CATGB``, "Category according to the annual radiation on the panel surface"
    ``Xdir``, "Directional scalar of the x vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    ``array_spacing_m``, "Spacing between solar arrays."
    ``TYPE``, "Surface typology."
    


get_optimization_generation_connected_performance
-------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/gen_1_connected_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_HP_Lake_connected_USD``, "TODO"
    ``Capex_total_Furnace_wet_connected_USD``, "TODO"
    ``Capex_a_SeasonalStorage_WS_connected_USD``, "TODO"
    ``Capex_a_BackupBoiler_NG_connected_USD``, "TODO"
    ``Capex_total_BackupBoiler_NG_connected_USD``, "TODO"
    ``PEN_GRID_imports_connected_MJoilyr``, "TODO"
    ``Capex_a_PV_connected_USD``, "TODO"
    ``Capex_a_BaseBoiler_NG_connected_USD``, "TODO"
    ``Opex_fixed_PV_connected_USD``, "TODO"
    ``Opex_fixed_SC_ET_connected_USD``, "TODO"
    ``Capex_total_SubstationsHeating_connected_USD``, "TODO"
    ``Opex_fixed_SubstationsHeating_connected_USD``, "TODO"
    ``Capex_total_HP_Sewage_connected_USD``, "TODO"
    ``Opex_var_WB_connected_USD``, "TODO"
    ``Opex_fixed_HP_Server_connected_USD``, "TODO"
    ``Capex_total_GRID_connected_USD``, "TODO"
    ``Opex_fixed_BaseBoiler_NG_connected_USD``, "TODO"
    ``Capex_a_HP_Sewage_connected_USD``, "TODO"
    ``Capex_total_BaseBoiler_NG_connected_USD``, "TODO"
    ``Capex_a_Furnace_wet_connected_USD``, "TODO"
    ``Capex_a_SC_ET_connected_USD``, "TODO"
    ``Opex_fixed_DHN_connected_USD``, "TODO"
    ``PEN_WB_connected_MJoilyr``, "TODO"
    ``GHG_GRID_exports_connected_tonCO2yr``, "TODO"
    ``Capex_total_PVT_connected_USD``, "TODO"
    ``Opex_fixed_PVT_connected_USD``, "TODO"
    ``Opex_fixed_GRID_connected_USD``, "TODO"
    ``Opex_var_GRID_imports_connected_USD``, "TODO"
    ``Capex_total_PV_connected_USD``, "TODO"
    ``Capex_a_PeakBoiler_NG_connected_USD``, "TODO"
    ``individual``, "TODO"
    ``Capex_a_PVT_connected_USD``, "TODO"
    ``Capex_a_GHP_connected_USD``, "TODO"
    ``Capex_total_DHN_connected_USD``, "TODO"
    ``Opex_fixed_SeasonalStorage_WS_connected_USD``, "TODO"
    ``generation``, "TODO"
    ``GHG_WB_connected_tonCO2yr``, "TODO"
    ``GHG_GRID_imports_connected_tonCO2yr``, "TODO"
    ``PEN_DB_connected_MJoilyr``, "TODO"
    ``individual_name``, "TODO"
    ``Capex_total_HP_Lake_connected_USD``, "TODO"
    ``Capex_total_SC_FP_connected_USD``, "TODO"
    ``Capex_total_GHP_connected_USD``, "TODO"
    ``Opex_fixed_PeakBoiler_NG_connected_USD``, "TODO"
    ``Opex_fixed_Furnace_wet_connected_USD``, "TODO"
    ``Capex_total_Furnace_dry_connected_USD``, "TODO"
    ``Capex_a_DHN_connected_USD``, "TODO"
    ``Capex_total_CHP_NG_connected_USD``, "TODO"
    ``Opex_fixed_CHP_NG_connected_USD``, "TODO"
    ``Capex_a_SubstationsHeating_connected_USD``, "TODO"
    ``Capex_total_PeakBoiler_NG_connected_USD``, "TODO"
    ``Capex_a_CHP_NG_connected_USD``, "TODO"
    ``Capex_total_SC_ET_connected_USD``, "TODO"
    ``Opex_fixed_GHP_connected_USD``, "TODO"
    ``Opex_fixed_HP_Lake_connected_USD``, "TODO"
    ``Capex_total_HP_Server_connected_USD``, "TODO"
    ``Opex_fixed_BackupBoiler_NG_connected_USD``, "TODO"
    ``Capex_total_SeasonalStorage_WS_connected_USD``, "TODO"
    ``PEN_GRID_exports_connected_MJoilyr``, "TODO"
    ``PEN_NG_connected_MJoilyr``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Opex_fixed_SC_FP_connected_USD``, "TODO"
    ``Opex_var_DB_connected_USD``, "TODO"
    ``Opex_fixed_Furnace_dry_connected_USD``, "TODO"
    ``Capex_a_Furnace_dry_connected_USD``, "TODO"
    ``GHG_DB_connected_tonCO2yr``, "TODO"
    ``Opex_var_NG_connected_USD``, "TODO"
    ``Opex_var_GRID_exports_connected_USD``, "TODO"
    ``Capex_a_HP_Server_connected_USD``, "TODO"
    ``Capex_a_SC_FP_connected_USD``, "TODO"
    ``GHG_NG_connected_tonCO2yr``, "TODO"
    ``Capex_a_GRID_connected_USD``, "TODO"
    ``Opex_fixed_HP_Sewage_connected_USD``, "TODO"
    


PV_totals
---------

path: ``outputs/data/potentials/solar/PV_total.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``PV_walls_west_m2``, "West facing wall collector surface area."
    ``PV_roofs_top_m2``, "Collector surface area on roof tops."
    ``PV_walls_north_E_kWh``, "Electricity production from photovoltaic panels on north facades"
    ``Area_PV_m2``, "Total area of investigated collector."
    ``E_PV_gen_kWh``, "Total electricity generated by the collector."
    ``PV_walls_south_m2``, "Collector surface area on south facades."
    ``PV_walls_east_E_kWh``, "Electricity production from photovoltaic panels on east facades"
    ``PV_walls_east_m2``, "Collector surface area on east facades."
    ``radiation_kWh``, "Total radiatiative potential."
    ``Date``, "Date and time in hourly steps."
    ``PV_walls_south_E_kWh``, "Electricity production from photovoltaic panels on south facades"
    ``PV_roofs_top_E_kWh``, "Electricity production from photovoltaic panels on roof tops"
    ``PV_walls_west_E_kWh``, "Electricity production from photovoltaic panels on west facades"
    ``PV_walls_north_m2``, "Collector surface area on north facades."
    


SC_totals
---------

path: ``outputs/data/potentials/solar/SC_FP_total.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``SC_FP_walls_south_m2``, "TODO"
    ``SC_FP_walls_east_Q_kWh``, "TODO"
    ``T_SC_sup_C``, "TODO"
    ``Q_SC_l_kWh``, "TODO"
    ``Date``, "Date and time in hourly steps."
    ``SC_FP_walls_south_Q_kWh``, "TODO"
    ``Eaux_SC_kWh``, "TODO"
    ``radiation_kWh``, "Total radiatiative potential."
    ``Area_SC_m2``, "TODO"
    ``Q_SC_gen_kWh``, "TODO"
    ``SC_FP_walls_north_m2``, "TODO"
    ``SC_FP_walls_west_m2``, "TODO"
    ``SC_FP_walls_east_m2``, "TODO"
    ``SC_FP_roofs_top_m2``, "TODO"
    ``SC_FP_walls_north_Q_kWh``, "TODO"
    ``mcp_SC_kWperC``, "TODO"
    ``T_SC_re_C``, "TODO"
    ``SC_FP_roofs_top_Q_kWh``, "TODO"
    ``SC_FP_walls_west_Q_kWh``, "TODO"
    


get_network_total_pressure_drop_file
------------------------------------

path: ``outputs/data/thermal-network/DH__plant_pumping_pressure_loss_Pa.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``pressure_loss_substations_Pa``, "TODO"
    ``pressure_loss_return_Pa``, "TODO"
    ``pressure_loss_supply_Pa``, "TODO"
    ``pressure_loss_total_Pa``, "TODO"
    


get_thermal_network_edge_list_file
----------------------------------

path: ``outputs/data/thermal-network/DH__metadata_edges.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``length_m``, "TODO"
    ``D_int_m``, "TODO"
    ``Pipe_DN``, "TODO"
    ``Type_mat``, "TODO"
    


get_optimization_slave_total_performance
----------------------------------------

path: ``outputs/data/optimization/slave/gen_0/ind_2_total_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_total_sys_connected_USD``, "TODO"
    ``PEN_sys_disconnected_MJoil``, "TODO"
    ``GHG_sys_tonCO2``, "TODO"
    ``Capex_total_sys_disconnected_USD``, "TODO"
    ``TAC_sys_USD``, "TODO"
    ``Opex_a_sys_connected_USD``, "TODO"
    ``PEN_sys_connected_MJoil``, "TODO"
    ``Capex_a_sys_USD``, "TODO"
    ``TAC_sys_connected_USD``, "TODO"
    ``GHG_sys_disconnected_tonCO2``, "TODO"
    ``Opex_a_sys_disconnected_USD``, "TODO"
    ``PEN_sys_MJoil``, "TODO"
    ``GHG_sys_connected_tonCO2``, "TODO"
    ``Capex_a_sys_connected_USD``, "TODO"
    ``TAC_sys_disconnected_USD``, "TODO"
    ``Capex_a_sys_disconnected_USD``, "TODO"
    ``Capex_total_sys_USD``, "TODO"
    ``Opex_a_sys_USD``, "TODO"
    


get_optimization_generation_total_performance
---------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/gen_2_total_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``generation``, "TODO"
    ``Capex_total_sys_connected_USD``, "TODO"
    ``PEN_sys_disconnected_MJoil``, "TODO"
    ``GHG_sys_tonCO2``, "TODO"
    ``Capex_a_sys_connected_USD``, "TODO"
    ``TAC_sys_USD``, "TODO"
    ``Opex_a_sys_connected_USD``, "TODO"
    ``individual_name``, "TODO"
    ``individual``, "TODO"
    ``TAC_sys_connected_USD``, "TODO"
    ``GHG_sys_disconnected_tonCO2``, "TODO"
    ``Opex_a_sys_disconnected_USD``, "TODO"
    ``PEN_sys_MJoil``, "TODO"
    ``GHG_sys_connected_tonCO2``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Capex_total_sys_disconnected_USD``, "TODO"
    ``PEN_sys_connected_MJoil``, "TODO"
    ``TAC_sys_disconnected_USD``, "TODO"
    ``Capex_a_sys_USD``, "TODO"
    ``Capex_a_sys_disconnected_USD``, "TODO"
    ``Capex_total_sys_USD``, "TODO"
    ``Opex_a_sys_USD``, "TODO"
    


get_optimization_substations_total_file
---------------------------------------

path: ``outputs/data/optimization/substations/Total_DH_111111111.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``GRID_ww_MWhyr``, "TODO"
    ``Qhs_sen_ahu_MWhyr``, "TODO"
    ``GRID_l0_kW``, "TODO"
    ``Ea_MWhyr``, "TODO"
    ``Qcs_sys_MWhyr``, "TODO"
    ``Qhs_sys_MWhyr``, "TODO"
    ``GRID_pro_MWhyr``, "TODO"
    ``GRID_cre_MWhyr``, "TODO"
    ``OIL_hs0_kW``, "TODO"
    ``Epro_MWhyr``, "TODO"
    ``QH_sys_MWhyr``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Qhs_sen_ahu0_kW``, "TODO"
    ``Qcs0_kW``, "TODO"
    ``WOOD_hs_MWhyr``, "TODO"
    ``Qcs_dis_ls0_kW``, "TODO"
    ``GRID0_kW``, "TODO"
    ``GRID_cs_MWhyr``, "TODO"
    ``GRID_MWhyr``, "TODO"
    ``GRID_data0_kW``, "TODO"
    ``GRID_hs_MWhyr``, "TODO"
    ``Qcdata_MWhyr``, "TODO"
    ``Edata_MWhyr``, "TODO"
    ``Qcs_em_ls_MWhyr``, "TODO"
    ``Qhs_lat_aru_MWhyr``, "TODO"
    ``E_sys_MWhyr``, "TODO"
    ``E_cdata0_kW``, "TODO"
    ``PV_MWhyr``, "TODO"
    ``Qww_sys_MWhyr``, "TODO"
    ``QH_sys0_kW``, "TODO"
    ``E_cre0_kW``, "TODO"
    ``Qcs_lat_sys0_kW``, "TODO"
    ``OIL_ww0_kW``, "TODO"
    ``Eal0_kW``, "TODO"
    ``Qhs_sen_sys0_kW``, "TODO"
    ``DH_hs_MWhyr``, "TODO"
    ``Qcre_sys_MWhyr``, "TODO"
    ``COAL_ww0_kW``, "TODO"
    ``GRID_l_MWhyr``, "TODO"
    ``Qcs_sen_scu_MWhyr``, "TODO"
    ``Af_m2``, "TODO"
    ``DH_ww_MWhyr``, "TODO"
    ``Qhs_dis_ls0_kW``, "TODO"
    ``Qcdata0_kW``, "TODO"
    ``Qhs_lat_sys_MWhyr``, "TODO"
    ``Qcs_sen_aru0_kW``, "TODO"
    ``Qcs_sys_aru0_kW``, "TODO"
    ``Qcs_lat_aru0_kW``, "TODO"
    ``Qcs_sen_scu0_kW``, "TODO"
    ``GRID_aux_MWhyr``, "TODO"
    ``Qcs_lat_ahu0_kW``, "TODO"
    ``Qcre0_kW``, "TODO"
    ``Qhs_lat_sys0_kW``, "TODO"
    ``GRID_cs0_kW``, "TODO"
    ``Aocc_m2``, "TODO"
    ``SOLAR_hs_MWhyr``, "TODO"
    ``GRID_pro0_kW``, "TODO"
    ``COAL_ww_MWhyr``, "TODO"
    ``Qcs_sys_ahu_MWhyr``, "TODO"
    ``Qhs_sys0_kW``, "TODO"
    ``Qcs_sys_scu0_kW``, "TODO"
    ``Aroof_m2``, "TODO"
    ``E_cdata_MWhyr``, "TODO"
    ``DC_cdata_MWhyr``, "TODO"
    ``Qcs_MWhyr``, "TODO"
    ``Qcs_sys_ahu0_kW``, "TODO"
    ``Qhs_sys_ahu_MWhyr``, "TODO"
    ``Qcdata_sys_MWhyr``, "TODO"
    ``OIL_hs_MWhyr``, "TODO"
    ``OIL_ww_MWhyr``, "TODO"
    ``E_cs_MWhyr``, "TODO"
    ``NG_ww_MWhyr``, "TODO"
    ``El_MWhyr``, "TODO"
    ``GRID_cdata0_kW``, "TODO"
    ``GRID_a0_kW``, "TODO"
    ``Qhs_sen_aru0_kW``, "TODO"
    ``Qhs_lat_ahu_MWhyr``, "TODO"
    ``PV0_kW``, "TODO"
    ``Qcs_sys0_kW``, "TODO"
    ``GRID_cre0_kW``, "TODO"
    ``Qcs_lat_ahu_MWhyr``, "TODO"
    ``Eaux0_kW``, "TODO"
    ``DC_cre_MWhyr``, "TODO"
    ``Qhs_sys_aru_MWhyr``, "TODO"
    ``Qcs_em_ls0_kW``, "TODO"
    ``Qcs_dis_ls_MWhyr``, "TODO"
    ``Qhpro_sys_MWhyr``, "TODO"
    ``Epro0_kW``, "TODO"
    ``Qcre_sys0_kW``, "TODO"
    ``Qcs_sen_ahu_MWhyr``, "TODO"
    ``E_sys0_kW``, "TODO"
    ``SOLAR_ww_MWhyr``, "TODO"
    ``Eaux_MWhyr``, "TODO"
    ``SOLAR_hs0_kW``, "TODO"
    ``Qcs_sen_sys_MWhyr``, "TODO"
    ``SOLAR_ww0_kW``, "TODO"
    ``COAL_hs_MWhyr``, "TODO"
    ``E_ww_MWhyr``, "TODO"
    ``Qcs_lat_sys_MWhyr``, "TODO"
    ``Qcs_sen_ahu0_kW``, "TODO"
    ``Qhs_lat_ahu0_kW``, "TODO"
    ``QC_sys_MWhyr``, "TODO"
    ``Qhs_sys_shu0_kW``, "TODO"
    ``Qcs_sen_sys0_kW``, "TODO"
    ``QC_sys0_kW``, "TODO"
    ``Qhs_sen_sys_MWhyr``, "TODO"
    ``Qcpro_sys_MWhyr``, "TODO"
    ``DH_ww0_kW``, "TODO"
    ``E_hs0_kW``, "TODO"
    ``Qhs_sys_aru0_kW``, "TODO"
    ``WOOD_ww0_kW``, "TODO"
    ``E_ww0_kW``, "TODO"
    ``Qww0_kW``, "TODO"
    ``Qhs_dis_ls_MWhyr``, "TODO"
    ``Qhs_lat_aru0_kW``, "TODO"
    ``Qcs_sen_aru_MWhyr``, "TODO"
    ``Qhs_sys_ahu0_kW``, "TODO"
    ``GRID_aux0_kW``, "TODO"
    ``GRID_cdata_MWhyr``, "TODO"
    ``Qww_sys0_kW``, "TODO"
    ``GRID_ww0_kW``, "TODO"
    ``NG_hs0_kW``, "TODO"
    ``NG_hs_MWhyr``, "TODO"
    ``Qcs_sys_scu_MWhyr``, "TODO"
    ``Qhs_sen_aru_MWhyr``, "TODO"
    ``El0_kW``, "TODO"
    ``WOOD_hs0_kW``, "TODO"
    ``E_cre_MWhyr``, "TODO"
    ``NG_ww0_kW``, "TODO"
    ``E_cs0_kW``, "TODO"
    ``DC_cre0_kW``, "TODO"
    ``GFA_m2``, "TODO"
    ``Qhs_sen_shu_MWhyr``, "TODO"
    ``Qhs_sys_shu_MWhyr``, "TODO"
    ``DC_cs_MWhyr``, "TODO"
    ``DC_cs0_kW``, "TODO"
    ``Qcdata_sys0_kW``, "TODO"
    ``Qhs_MWhyr``, "TODO"
    ``WOOD_ww_MWhyr``, "TODO"
    ``Qhpro_sys0_kW``, "TODO"
    ``Qhs_sen_shu0_kW``, "TODO"
    ``Name``, "TODO"
    ``GRID_hs0_kW``, "TODO"
    ``DH_hs0_kW``, "TODO"
    ``Edata0_kW``, "TODO"
    ``Qcs_lat_aru_MWhyr``, "TODO"
    ``DC_cdata0_kW``, "TODO"
    ``Qcre_MWhyr``, "TODO"
    ``Eal_MWhyr``, "TODO"
    ``Qhs_em_ls0_kW``, "TODO"
    ``E_hs_MWhyr``, "TODO"
    ``Qww_MWhyr``, "TODO"
    ``Qcpro_sys0_kW``, "TODO"
    ``Qhs0_kW``, "TODO"
    ``COAL_hs0_kW``, "TODO"
    ``Qcs_sys_aru_MWhyr``, "TODO"
    ``GRID_a_MWhyr``, "TODO"
    ``people0``, "TODO"
    ``GRID_data_MWhyr``, "TODO"
    ``Ea0_kW``, "TODO"
    ``Qhs_em_ls_MWhyr``, "TODO"
    


get_building_internal
---------------------

path: ``inputs/building-properties/internal_loads.dbf``

The following file is used by these scripts: ``demand``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``El_Wm2``, "Peak specific electrical load due to artificial lighting"
    ``Qhpro_Wm2``, "Peak specific process heating load"
    ``Name``, "Unique building ID. It must start with a letter."
    ``Occ_m2pax``, "Occupancy density"
    ``Ed_Wm2``, "Peak specific electrical load due to servers/data centres"
    ``Ea_Wm2``, "Peak specific electrical load due to computers and devices"
    ``Qcre_Wm2``, "Peak specific cooling load due to refrigeration (cooling rooms)"
    ``Epro_Wm2``, "Peak specific electrical load due to industrial processes"
    ``X_ghpax``, "Moisture released by occupancy at peak conditions"
    ``Vww_lpdpax``, "Peak specific daily hot water consumption"
    ``Vw_lpdpax``, "Peak specific fresh water consumption (includes cold and hot water)"
    ``Qs_Wpax``, "Peak sensible heat load of people"
    ``Qcpro_Wm2``, "Peak specific process cooling load"
    


get_optimization_disconnected_heating_capacity
----------------------------------------------

path: ``outputs/data/optimization/slave/gen_0/ind_1_disconnected_heating_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_FC_NG_heat_disconnected_W``, "TODO"
    ``Capacity_BaseBoiler_NG_heat_disconnected_W``, "TODO"
    ``Name``, "TODO"
    ``Capacity_GS_HP_heat_disconnected_W``, "TODO"
    


get_optimization_connected_electricity_capacity
-----------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_0_connected_electrical_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_GRID_el_connected_W``, "TODO"
    ``Capacity_PV_el_connected_m2``, "TODO"
    ``Capacity_PV_el_connected_W``, "TODO"
    


get_schedule_model_file
-----------------------

path: ``outputs/data/occupancy/B001.csv``

The following file is used by these scripts: ``demand``


.. csv-table::
    :header: "Variable", "Description"

    ``Ed_W``, "TODO"
    ``X_gh``, "TODO"
    ``Qcpro_W``, "TODO"
    ``Qs_W``, "TODO"
    ``people_pax``, "TODO"
    ``DATE``, "TODO"
    ``Epro_W``, "TODO"
    ``Vww_lph``, "TODO"
    ``Tcs_set_C``, "TODO"
    ``Ve_lps``, "TODO"
    ``Ths_set_C``, "TODO"
    ``Ea_W``, "TODO"
    ``El_W``, "TODO"
    ``Vw_lph``, "TODO"
    ``Qcre_W``, "TODO"
    ``Qhpro_W``, "TODO"
    


get_database_distribution_systems
---------------------------------

path: ``inputs/technology/components/DISTRIBUTION.xls``

The following file is used by these scripts: ``optimization``, ``thermal_network``




.. csv-table:: ``inputs/technology/components/DISTRIBUTION.xls`` Worksheet: ``THERMAL_GRID``
    :header: "Variable", "Description"
    ``Code``, no such column?``Inv_USD2015perm``, Typical cost of investment for a given pipe diameter.``D_ins_m``, maximum pipe diameter tolerance for the nominal diameter (DN)``D_ext_m``, external pipe diameter tolerance for the nominal diameter (DN)``Pipe_DN``, Nominal pipe diameter``D_int_m``, internal pipe diameter tolerance for the nominal diameter (DN)``Vdot_max_m3s``, maximum volumetric flow rate for the nominal diameter (DN)``Vdot_min_m3s``, minimum volumetric flow rate for the nominal diameter (DN)




get_database_conversion_systems
-------------------------------

path: ``inputs/technology/components/CONVERSION.xls``

The following file is used by these scripts: ``decentralized``, ``optimization``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``




.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``CCGT``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the type of combined-cycle gas turbine``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``PV``
    :header: "Variable", "Description"
    ``code``, identifier of each unique equipment``cap_max``, maximum capacity ``PV_a2``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, x is the relative air mass``PV_a1``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, x is the relative air mass``PV_a0``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, x is the relative air mass``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``module_length_m``, lengh of the PV module``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``PV_a4``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, x is the relative air mass``misc_losses``, losses from cabling, resistances etc...``PV_Bref``, cell maximum power temperature coefficient``PV_a3``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, x is the relative air mass``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``Description``, Describes the source of the benchmark standards.``PV_n``, nominal efficiency``PV_noct``, nominal operating cell temperature``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``assumption``, items made by assumptions in this technology``PV_th``, glazing thickness``type``, redundant



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``PVT``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the type of photovoltaic thermal technology``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``HEX``
    :header: "Variable", "Description"
    ``code``, identifier of each unique equipment``cap_max``, maximum capacity ``a_p``, pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x), where x is the capacity mass flow rate [W/K]   ``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``c_p``, pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x), where x is the capacity mass flow rate [W/K]   ``e_p``, pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x), where x is the capacity mass flow rate [W/K]   ``b_p``, pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x), where x is the capacity mass flow rate [W/K]   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``Description``, Describes the type of heat exchanger``currency``, currency-year information of the investment cost function``d_p``, pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x), where x is the capacity mass flow rate [W/K]   ``IR_%``, interest rate charged on the loan for the capital cost``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``assumption``, items made by assumptions in this technology



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``HP``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the source of the heat pump``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``BH``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the type of borehole heat exchanger``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``CT``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the type of cooling tower``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``Pump``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the source of the benchmark standards.``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``FC``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the type of fuel cell``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, TODO``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``Chiller``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the source of the benchmark standards.``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``Boiler``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the type of boiler``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``SC``
    :header: "Variable", "Description"
    ``code``, identifier of each unique equipment``mB_max_r``, maximum flow rate per aperture area``LT_yr``, lifetime of this technology``module_length_m``, lengh of a solar collector module``currency``, currency-year information of the investment cost function``mB_min_r``, minimum flow rate per aperture area``cap_max``, maximum capacity ``C_eff``, thermal capacity of module ``t_max``, maximum operating temperature``unit``, unit of the min/max capacity``Description``, Describes the type of solar collector``assumption``, items made by assumptions in this technology``type``, type of the solar collector (FP: flate-plate or ET: evacuated-tube)``dP4``, pressure drop at minimum flow rate (mB_min)``dP3``, pressure drop at maximum flow rate (mB_max)``dP2``, pressure drop at nominal flow rate (mB0)``dP1``, pressure drop at zero flow rate``module_area_m2``, module area of a solar collector``cap_min``, minimum capacity``IAM_d``, incident angle modifier for diffuse radiation``c2``, ctemperature difference dependency of the heat loss coefficient``c1``, collector heat loss coefficient at zero temperature difference and wind speed``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``mB0_r``, nominal flow rate per aperture area``IR_%``, interest rate charged on the loan for the capital cost``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``aperture_area_ratio``, ratio of aperture area to panel area``n0``, zero loss efficiency at normal incidence``Cp_fluid``, heat capacity of the heat transfer fluid



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``Furnace``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the type of furnace``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, items made by assumptions in this technology``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``TES``
    :header: "Variable", "Description"
    ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``cap_max``, maximum capacity ``Description``, Describes the source of the benchmark standards.``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``IR_%``, interest rate charged on the loan for the capital cost``currency``, currency-year information of the investment cost function``code``, identifier of each unique equipment``assumption``, TODO``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   



.. csv-table:: ``inputs/technology/components/CONVERSION.xls`` Worksheet: ``Absorption_chiller``
    :header: "Variable", "Description"
    ``code``, identifier of each unique equipment``cap_max``, maximum capacity ``e_e``, parameter in the characteristic equations to calculate the evaporator side ``cap_min``, minimum capacity``LT_yr``, lifetime of this technology``a_g``, parameter in the characteristic equations to calculate the generator side``currency``, currency-year information of the investment cost function``a_e``, parameter in the characteristic equations to calculate the evaporator side ``m_hw``, external flow rate of hot water at the generator``unit``, unit of the min/max capacity``d``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``a``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``c``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``b``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``e``, investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)   ``Description``, Describes the Type of Absorption Chiller``IR_%``, interest rate charged on the loan for the capital cost``O&M_%``, operation and maintanence cost factor (fraction of the investment cost)``m_cw``, external flow rate of cooling water at the condenser and absorber``assumption``, items made by assumptions in this technology``s_e``, parameter in the characteristic equations to calculate the evaporator side ``s_g``, parameter in the characteristic equations to calculate the generator side``e_g``, parameter in the characteristic equations to calculate the generator side``type``, type of absorption chiller (single, double, or triple)``r_e``, parameter in the characteristic equations to calculate the evaporator side ``r_g``, parameter in the characteristic equations to calculate the generator side




get_network_layout_nodes_shapefile
----------------------------------

path: ``outputs/data/thermal-network/DH/nodes.shp``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``Building``, "Unique building ID. It must start with a letter."
    ``geometry``, "Geometry"
    ``Type``, "Weather a Plant or A Customer"
    ``Name``, "Unique building ID. It must start with a letter."
    


get_total_demand
----------------

path: ``outputs/data/demand/Total_demand.csv``

The following file is used by these scripts: ``decentralized``, ``emissions``, ``network_layout``, ``system_costs``, ``optimization``, ``sewage_potential``, ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``GRID_ww_MWhyr``, "TODO"
    ``Qhs_sen_ahu_MWhyr``, "AHU sensible heat demand"
    ``GRID_l0_kW``, "TODO"
    ``Ea_MWhyr``, "TODO"
    ``Qcs_sys_MWhyr``, "End-use space cooling demand"
    ``Qhs_sys_MWhyr``, "End-use space heating demand"
    ``GRID_pro_MWhyr``, "TODO"
    ``GRID_cre_MWhyr``, "TODO"
    ``OIL_hs0_kW``, "Nominal OIL requirement for space heating supply"
    ``Epro_MWhyr``, "Electricity supplied to industrial processes"
    ``QH_sys_MWhyr``, "Total building heating demand"
    ``Qhs_sen_ahu0_kW``, "Nominal AHU sensible heat demand."
    ``Qcs0_kW``, "Nominal Total cooling demand."
    ``WOOD_hs_MWhyr``, "WOOD requirement for space heating supply"
    ``Qcs_dis_ls0_kW``, "Nominal Cool distribution losses."
    ``GRID0_kW``, "Nominal Grid electricity consumption"
    ``GRID_cs_MWhyr``, "TODO"
    ``GRID_MWhyr``, "Grid electricity consumption"
    ``GRID_data0_kW``, "TODO"
    ``GRID_hs_MWhyr``, "TODO"
    ``Qcdata_MWhyr``, "Data centre cooling demand"
    ``Edata_MWhyr``, "Electricity consumption for data centers"
    ``Qcs_em_ls_MWhyr``, "Cool emission losses"
    ``Qhs_lat_aru_MWhyr``, "ARU latent heat demand"
    ``E_sys_MWhyr``, "End-use electricity demand"
    ``E_cdata0_kW``, "Nominal Data centre cooling specific electricity consumption."
    ``PV_MWhyr``, "PV electricity consumption"
    ``Qww_sys_MWhyr``, "End-use hotwater demand"
    ``QH_sys0_kW``, "Nominal total building heating demand."
    ``E_cre0_kW``, "Nominal Refrigeration system electricity consumption."
    ``Qcs_lat_sys0_kW``, "Nominal System latent cool demand."
    ``OIL_ww0_kW``, "Nominal OIL requirement for hotwater supply"
    ``Eal0_kW``, "Nominal Total net electricity for all sources and sinks."
    ``Qhs_sen_sys0_kW``, "Nominal HVAC systems sensible heat demand."
    ``DH_hs_MWhyr``, "Energy requirement by district heating (space heating supply)"
    ``Qcre_sys_MWhyr``, "End-use refrigeration demand"
    ``COAL_ww0_kW``, "Nominal Coal requirement for hotwater supply"
    ``GRID_l_MWhyr``, "TODO"
    ``Qcs_sen_scu_MWhyr``, "SCU system cool demand"
    ``Af_m2``, "Conditioned floor area (heated/cooled)"
    ``DH_ww_MWhyr``, "Energy requirement by district heating (hotwater supply)"
    ``Qhs_dis_ls0_kW``, "Nominal Heating system distribution losses."
    ``Qcdata0_kW``, "Nominal Data centre cooling demand."
    ``Qhs_lat_sys_MWhyr``, "System latent heat demand"
    ``Qcs_sen_aru0_kW``, "Nominal ARU system cool demand."
    ``Qcs_sys_aru0_kW``, "Nominal ARU system cool demand."
    ``Qcs_lat_aru0_kW``, "Nominal ARU latent cool demand."
    ``Qcs_sen_scu0_kW``, "Nominal SCU system cool demand."
    ``GRID_aux_MWhyr``, "TODO"
    ``Qcs_lat_ahu0_kW``, "Nominal AHU latent cool demand."
    ``Qcre0_kW``, "Nominal Refrigeration cooling demand."
    ``Qhs_lat_sys0_kW``, "Nominal System latent heat demand."
    ``GRID_cs0_kW``, "TODO"
    ``Aocc_m2``, "Occupied floor area (heated/cooled)"
    ``SOLAR_hs_MWhyr``, "Solar thermal energy requirement for space heating supply"
    ``GRID_pro0_kW``, "TODO"
    ``COAL_ww_MWhyr``, "Coal requirement for hotwater supply"
    ``Qcs_sys_ahu_MWhyr``, "AHU system cool demand"
    ``Qhs_sys0_kW``, "Nominal end-use space heating demand"
    ``Qcs_sys_scu0_kW``, "Nominal SCU system cool demand."
    ``Aroof_m2``, "Roof area"
    ``E_cdata_MWhyr``, "Electricity consumption due to data center cooling"
    ``DC_cdata_MWhyr``, "District cooling for data center cooling demand"
    ``Qcs_MWhyr``, "Total cool demand"
    ``Qcs_sys_ahu0_kW``, "Nominal AHU system cool demand."
    ``Qhs_sys_ahu_MWhyr``, "AHU system heat demand"
    ``Qcdata_sys_MWhyr``, "End-use data center cooling demand"
    ``OIL_hs_MWhyr``, "OIL requirement for space heating supply"
    ``OIL_ww_MWhyr``, "OIL requirement for hotwater supply"
    ``E_cs_MWhyr``, "Electricity consumption due to space cooling"
    ``NG_ww_MWhyr``, "NG requirement for hotwater supply"
    ``El_MWhyr``, "TODO"
    ``GRID_cdata0_kW``, "TODO"
    ``GRID_a0_kW``, "TODO"
    ``Qhs_sen_aru0_kW``, "ARU sensible heat demand"
    ``Qhs_lat_ahu_MWhyr``, "AHU latent heat demand"
    ``PV0_kW``, "Nominal PV electricity consumption"
    ``Qcs_sys0_kW``, "Nominal end-use space cooling demand"
    ``GRID_cre0_kW``, "TODO"
    ``Qcs_lat_ahu_MWhyr``, "AHU latent cool demand"
    ``Eaux0_kW``, "Nominal Auxiliary electricity consumption."
    ``DC_cre_MWhyr``, "District cooling for refrigeration demand"
    ``Qhs_sys_aru_MWhyr``, "ARU sensible heat demand"
    ``Qcs_em_ls0_kW``, "Nominal Cool emission losses."
    ``Qcs_dis_ls_MWhyr``, "Cool distribution losses"
    ``Qhpro_sys_MWhyr``, "Yearly processes heat demand."
    ``Epro0_kW``, "Nominal Industrial processes electricity consumption."
    ``Qcre_sys0_kW``, " Nominal refrigeration cooling demand"
    ``Qcs_sen_ahu_MWhyr``, "AHU system cool demand"
    ``E_sys0_kW``, "Nominal end-use electricity demand"
    ``SOLAR_ww_MWhyr``, "Solar thermal energy requirement for hotwater supply"
    ``Eaux_MWhyr``, "Electricity consumption due to auxiliary equipment"
    ``SOLAR_hs0_kW``, "Nominal solar thermal energy requirement for space heating supply"
    ``Qcs_sen_sys_MWhyr``, "Sensible system cool demand"
    ``SOLAR_ww0_kW``, "Nominal solar thermal energy requirement for hotwater supply"
    ``COAL_hs_MWhyr``, "Coal requirement for space heating supply"
    ``E_ww_MWhyr``, "Electricity consumption due to hot water"
    ``Qcs_lat_sys_MWhyr``, "System latent cool demand"
    ``Qcs_sen_ahu0_kW``, "Nominal AHU system cool demand."
    ``Qhs_lat_ahu0_kW``, "Nominal AHU latent heat demand."
    ``QC_sys_MWhyr``, "Total system cooling demand"
    ``Qhs_sys_shu0_kW``, "Nominal SHU sensible heat demand."
    ``Qcs_sen_sys0_kW``, "Nominal Sensible system cool demand."
    ``QC_sys0_kW``, "Nominal Total system cooling demand."
    ``Qhs_sen_sys_MWhyr``, "SHU sensible heat demand"
    ``Qcpro_sys_MWhyr``, "Yearly processes cooling demand."
    ``DH_ww0_kW``, "Nominal Energy requirement by district heating (hotwater supply)"
    ``E_hs0_kW``, "Nominal Heating system electricity consumption."
    ``Qhs_sys_aru0_kW``, "Nominal ARU sensible heat demand."
    ``WOOD_ww0_kW``, "Nominal WOOD requirement for hotwater supply"
    ``E_ww0_kW``, "Nominal Domestic hot water electricity consumption."
    ``Qww0_kW``, "Nominal DHW heat demand."
    ``Qhs_dis_ls_MWhyr``, "Heating system distribution losses"
    ``Qhs_lat_aru0_kW``, "Nominal ARU latent heat demand."
    ``Qcs_sen_aru_MWhyr``, "ARU system cool demand"
    ``Qhs_sys_ahu0_kW``, "Nominal AHU sensible heat demand."
    ``GRID_aux0_kW``, "TODO"
    ``GRID_cdata_MWhyr``, "TODO"
    ``Qww_sys0_kW``, "Nominal end-use hotwater demand"
    ``GRID_ww0_kW``, "TODO"
    ``NG_hs0_kW``, "Nominal NG requirement for space heating supply"
    ``NG_hs_MWhyr``, "NG requirement for space heating supply"
    ``Qcs_sys_scu_MWhyr``, "SCU system cool demand"
    ``Qhs_sen_aru_MWhyr``, "ARU sensible heat demand"
    ``El0_kW``, "TODO"
    ``WOOD_hs0_kW``, "Nominal WOOD requirement for space heating supply"
    ``E_cre_MWhyr``, "Electricity consumption due to refrigeration"
    ``NG_ww0_kW``, "Nominal NG requirement for hotwater supply"
    ``E_cs0_kW``, "Nominal Cooling system electricity consumption."
    ``DC_cre0_kW``, "Nominal district cooling for refrigeration demand"
    ``GFA_m2``, "Gross floor area"
    ``Qhs_sen_shu_MWhyr``, "SHU sensible heat demand"
    ``Qhs_sys_shu_MWhyr``, "SHU sensible heat demand"
    ``DC_cs_MWhyr``, "District cooling for space cooling demand"
    ``DC_cs0_kW``, "Nominal district cooling for space cooling demand"
    ``Qcdata_sys0_kW``, "Nominal end-use data center cooling demand"
    ``Qhs_MWhyr``, "Total heating demand"
    ``WOOD_ww_MWhyr``, "WOOD requirement for hotwater supply"
    ``Qhpro_sys0_kW``, "Nominal process heat demand."
    ``Qhs_sen_shu0_kW``, "Nominal SHU sensible heat demand."
    ``Name``, "Unique building ID. It must start with a letter."
    ``GRID_hs0_kW``, "TODO"
    ``DH_hs0_kW``, "Nominal energy requirement by district heating (space heating supply)"
    ``Edata0_kW``, "Nominal Data centre electricity consumption."
    ``Qcs_lat_aru_MWhyr``, "ARU latent cool demand"
    ``DC_cdata0_kW``, "Nominal district cooling for final data center cooling demand"
    ``Qcre_MWhyr``, "Refrigeration cooling demand for the system"
    ``Eal_MWhyr``, "Electricity consumption due to appliances and lighting"
    ``Qhs_em_ls0_kW``, "Nominal Heating emission losses."
    ``E_hs_MWhyr``, "Electricity consumption due to space heating"
    ``Qww_MWhyr``, "DHW heat demand"
    ``Qcpro_sys0_kW``, "Nominal process cooling demand."
    ``Qhs0_kW``, "Nominal Total heating demand."
    ``COAL_hs0_kW``, "Nominal Coal requirement for space heating supply"
    ``Qcs_sys_aru_MWhyr``, "ARU system cool demand"
    ``GRID_a_MWhyr``, "TODO"
    ``people0``, "Nominal occupancy"
    ``GRID_data_MWhyr``, "TODO"
    ``Ea0_kW``, "TODO"
    ``Qhs_em_ls_MWhyr``, "Heating system emission losses"
    


get_lca_mobility
----------------

path: ``outputs/data/emissions/Total_LCA_mobility.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``GHG_sys_mobility_kgCO2m2``, "Commuting"
    ``GHG_sys_mobility_tonCO2``, "Commuting"
    ``GFA_m2``, "Gross floor area"
    ``Name``, "Unique building ID. It must start with a letter."
    


get_network_temperature_supply_nodes_file
-----------------------------------------

path: ``outputs/data/thermal-network/DH__temperature_supply_nodes_K.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "TODO"
    


get_optimization_slave_connected_performance
--------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_2_buildings_connected_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_HP_Lake_connected_USD``, "TODO"
    ``Capex_total_Furnace_wet_connected_USD``, "TODO"
    ``Capex_a_SeasonalStorage_WS_connected_USD``, "TODO"
    ``Capex_a_BackupBoiler_NG_connected_USD``, "TODO"
    ``Capex_total_BackupBoiler_NG_connected_USD``, "TODO"
    ``PEN_GRID_imports_connected_MJoilyr``, "TODO"
    ``Capex_a_PV_connected_USD``, "TODO"
    ``Capex_a_BaseBoiler_NG_connected_USD``, "TODO"
    ``Opex_fixed_PV_connected_USD``, "TODO"
    ``Opex_fixed_SC_ET_connected_USD``, "TODO"
    ``Capex_total_SubstationsHeating_connected_USD``, "TODO"
    ``Opex_fixed_SubstationsHeating_connected_USD``, "TODO"
    ``Capex_total_HP_Sewage_connected_USD``, "TODO"
    ``Opex_var_WB_connected_USD``, "TODO"
    ``Opex_fixed_HP_Server_connected_USD``, "TODO"
    ``Capex_total_GRID_connected_USD``, "TODO"
    ``Opex_fixed_BaseBoiler_NG_connected_USD``, "TODO"
    ``Capex_a_HP_Sewage_connected_USD``, "TODO"
    ``Capex_total_BaseBoiler_NG_connected_USD``, "TODO"
    ``Capex_a_Furnace_wet_connected_USD``, "TODO"
    ``Capex_a_SC_ET_connected_USD``, "TODO"
    ``Opex_fixed_DHN_connected_USD``, "TODO"
    ``PEN_WB_connected_MJoilyr``, "TODO"
    ``GHG_GRID_exports_connected_tonCO2yr``, "TODO"
    ``Capex_total_PVT_connected_USD``, "TODO"
    ``Opex_fixed_PVT_connected_USD``, "TODO"
    ``Opex_fixed_GRID_connected_USD``, "TODO"
    ``Opex_var_GRID_imports_connected_USD``, "TODO"
    ``Capex_total_PV_connected_USD``, "TODO"
    ``Capex_a_PeakBoiler_NG_connected_USD``, "TODO"
    ``Capex_a_PVT_connected_USD``, "TODO"
    ``Capex_a_GHP_connected_USD``, "TODO"
    ``Capex_total_DHN_connected_USD``, "TODO"
    ``Opex_fixed_SeasonalStorage_WS_connected_USD``, "TODO"
    ``GHG_WB_connected_tonCO2yr``, "TODO"
    ``GHG_GRID_imports_connected_tonCO2yr``, "TODO"
    ``PEN_DB_connected_MJoilyr``, "TODO"
    ``Capex_total_HP_Lake_connected_USD``, "TODO"
    ``Capex_total_SC_FP_connected_USD``, "TODO"
    ``Capex_total_GHP_connected_USD``, "TODO"
    ``Opex_fixed_PeakBoiler_NG_connected_USD``, "TODO"
    ``Opex_fixed_Furnace_wet_connected_USD``, "TODO"
    ``Capex_total_Furnace_dry_connected_USD``, "TODO"
    ``Capex_a_DHN_connected_USD``, "TODO"
    ``Capex_total_CHP_NG_connected_USD``, "TODO"
    ``Opex_fixed_CHP_NG_connected_USD``, "TODO"
    ``Capex_a_SubstationsHeating_connected_USD``, "TODO"
    ``Capex_total_PeakBoiler_NG_connected_USD``, "TODO"
    ``Capex_a_CHP_NG_connected_USD``, "TODO"
    ``Capex_total_SC_ET_connected_USD``, "TODO"
    ``Opex_fixed_GHP_connected_USD``, "TODO"
    ``Opex_fixed_HP_Lake_connected_USD``, "TODO"
    ``Capex_total_HP_Server_connected_USD``, "TODO"
    ``Opex_fixed_BackupBoiler_NG_connected_USD``, "TODO"
    ``Capex_total_SeasonalStorage_WS_connected_USD``, "TODO"
    ``PEN_GRID_exports_connected_MJoilyr``, "TODO"
    ``PEN_NG_connected_MJoilyr``, "TODO"
    ``Opex_fixed_SC_FP_connected_USD``, "TODO"
    ``Opex_var_DB_connected_USD``, "TODO"
    ``Opex_fixed_Furnace_dry_connected_USD``, "TODO"
    ``Capex_a_Furnace_dry_connected_USD``, "TODO"
    ``GHG_DB_connected_tonCO2yr``, "TODO"
    ``Opex_var_NG_connected_USD``, "TODO"
    ``Opex_var_GRID_exports_connected_USD``, "TODO"
    ``Capex_a_HP_Server_connected_USD``, "TODO"
    ``Capex_a_SC_FP_connected_USD``, "TODO"
    ``GHG_NG_connected_tonCO2yr``, "TODO"
    ``Capex_a_GRID_connected_USD``, "TODO"
    ``Opex_fixed_HP_Sewage_connected_USD``, "TODO"
    


get_building_air_conditioning
-----------------------------

path: ``inputs/building-properties/air_conditioning_systems.dbf``

The following file is used by these scripts: ``demand``


.. csv-table::
    :header: "Variable", "Description"

    ``heat_ends``, "End of the heating season - use 00|00 when there is none"
    ``Name``, "Unique building ID. It must start with a letter."
    ``type_cs``, "Type of cooling supply system"
    ``cool_starts``, "Start of the cooling season - use 00|00 when there is none"
    ``type_hs``, "Type of heating supply system"
    ``heat_starts``, "Start of the heating season - use 00|00 when there is none"
    ``type_vent``, "Type of ventilation strategy (relates to values in Default Database HVAC Properties)"
    ``cool_ends``, "End of the cooling season - use 00|00 when there is none"
    ``type_dhw``, "Type of hot water supply system"
    ``type_ctrl``, "Type of heating and cooling control systems (relates to values in Default Database HVAC Properties)"
    


PV_metadata_results
-------------------

path: ``outputs/data/potentials/solar/B001_PV_sensors.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``surface_azimuth_deg``, "Azimuth angle of the panel surface e.g. south facing = 180 deg"
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``Ycoor``, "Describes the position of the y vector."
    ``area_installed_module_m2``, "The area of the building suface covered by one solar panel"
    ``tilt_deg``, "Tilt angle of roof or walls"
    ``surface``, "Unique surface ID for each building exterior surface."
    ``Xcoor``, "Describes the position of the x vector."
    ``total_rad_Whm2``, "Total radiatiative potential of a given surfaces area."
    ``CATteta_z``, "Category according to the surface azimuth of the panel"
    ``AREA_m2``, "Surface area."
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``Ydir``, "Directional scalar of the y vector."
    ``intersection``, "TODO"
    ``B_deg``, "Tilt angle of the installed solar panels"
    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``CATB``, "Category according to the tilt angle of the panel"
    ``type_orientation``, "Concatenated surface type and orientation."
    ``CATGB``, "Category according to the annual radiation on the panel surface"
    ``Xdir``, "Directional scalar of the x vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    ``array_spacing_m``, "Spacing between solar arrays."
    ``TYPE``, "Surface typology."
    


get_radiation_metadata
----------------------

path: ``outputs/data/solar-radiation/B001_geometry.csv``

The following file is used by these scripts: ``demand``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``


.. csv-table::
    :header: "Variable", "Description"

    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``Ycoor``, "Describes the position of the y vector."
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``Xdir``, "Directional scalar of the x vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    ``AREA_m2``, "Surface area."
    ``Xcoor``, "Describes the position of the x vector."
    ``Ydir``, "Directional scalar of the y vector."
    ``intersection``, "TODO"
    ``TYPE``, "Surface typology."
    


get_optimization_generation_total_performance_pareto
----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/gen_2_total_performance_pareto.csv``

The following file is used by these scripts: ``multi_criteria_analysis``


.. csv-table::
    :header: "Variable", "Description"

    ``generation``, "TODO"
    ``Capex_total_sys_connected_USD``, "TODO"
    ``PEN_sys_disconnected_MJoil``, "TODO"
    ``GHG_sys_tonCO2``, "TODO"
    ``Capex_a_sys_connected_USD``, "TODO"
    ``TAC_sys_USD``, "TODO"
    ``Opex_a_sys_connected_USD``, "TODO"
    ``individual_name``, "TODO"
    ``individual``, "TODO"
    ``TAC_sys_connected_USD``, "TODO"
    ``GHG_sys_disconnected_tonCO2``, "TODO"
    ``Opex_a_sys_disconnected_USD``, "TODO"
    ``PEN_sys_MJoil``, "TODO"
    ``GHG_sys_connected_tonCO2``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Capex_total_sys_disconnected_USD``, "TODO"
    ``PEN_sys_connected_MJoil``, "TODO"
    ``TAC_sys_disconnected_USD``, "TODO"
    ``Capex_a_sys_USD``, "TODO"
    ``Capex_a_sys_disconnected_USD``, "TODO"
    ``Capex_total_sys_USD``, "TODO"
    ``Opex_a_sys_USD``, "TODO"
    


get_weather_file
----------------

path: ``inputs/weather/weather.epw``

The following file is used by these scripts: ``decentralized``, ``demand``, ``optimization``, ``photovoltaic``, ``photovoltaic_thermal``, ``radiation``, ``schedule_maker``, ``shallow_geothermal_potential``, ``solar_collector``, ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``snowdepth_cm (index = 30)``, "TODO"
    ``windspd_ms (index = 21)``, "TODO"
    ``atmos_Pa (index = 9)``, "TODO"
    ``zenlum_lux (index = 19)``, "TODO"
    ``Albedo (index = 32)``, "TODO"
    ``ceiling_hgt_m (index = 25)``, "TODO"
    ``relhum_percent (index = 8)``, "TODO"
    ``difhorrad_Whm2 (index = 15)``, "TODO"
    ``difhorillum_lux (index = 18)``, "TODO"
    ``presweathobs (index = 26)``, "TODO"
    ``dirnorillum_lux (index = 17)``, "TODO"
    ``days_last_snow (index = 31)``, "TODO"
    ``glohorrad_Whm2 (index = 13)``, "TODO"
    ``precip_wtr_mm (index = 28)``, "TODO"
    ``minute (index = 4)``, "TODO"
    ``liq_precip_depth_mm (index = 33)``, "TODO"
    ``dirnorrad_Whm2 (index = 14)``, "TODO"
    ``exthorrad_Whm2 (index = 10)``, "TODO"
    ``visibility_km (index = 24)``, "TODO"
    ``aerosol_opt_thousandths (index = 29)``, "TODO"
    ``opaqskycvr_tenths (index = 23)``, "TODO"
    ``presweathcodes (index = 27)``, "TODO"
    ``month (index = 1)``, "TODO"
    ``day (index = 2)``, "TODO"
    ``year (index = 0)``, "TODO"
    ``datasource (index = 5)``, "TODO"
    ``winddir_deg (index = 20)``, "TODO"
    ``glohorillum_lux (index = 16)``, "TODO"
    ``drybulb_C (index = 6)``, "TODO"
    ``dewpoint_C (index = 7)``, "TODO"
    ``totskycvr_tenths (index = 22)``, "TODO"
    ``liq_precip_rate_Hour (index = 34)``, "TODO"
    ``horirsky_Whm2 (index = 12)``, "TODO"
    ``hour (index = 3)``, "TODO"
    ``extdirrad_Whm2 (index = 11)``, "TODO"
    


SC_results
----------

path: ``outputs/data/potentials/solar/B001_SC_ET.csv``

The following file is used by these scripts: ``decentralized``


.. csv-table::
    :header: "Variable", "Description"

    ``SC_ET_walls_east_m2``, "TODO"
    ``SC_ET_walls_south_m2``, "TODO"
    ``SC_ET_roofs_top_m2``, "TODO"
    ``Area_SC_m2``, "TODO"
    ``T_SC_sup_C``, "TODO"
    ``SC_ET_walls_west_m2``, "TODO"
    ``Q_SC_l_kWh``, "TODO"
    ``radiation_kWh``, "Total radiatiative potential."
    ``Q_SC_gen_kWh``, "TODO"
    ``SC_ET_walls_west_Q_kWh``, "TODO"
    ``SC_ET_roofs_top_Q_kWh``, "TODO"
    ``SC_ET_walls_south_Q_kWh``, "TODO"
    ``SC_ET_walls_north_m2``, "TODO"
    ``mcp_SC_kWperC``, "TODO"
    ``T_SC_re_C``, "TODO"
    ``SC_ET_walls_east_Q_kWh``, "TODO"
    ``SC_ET_walls_north_Q_kWh``, "TODO"
    ``Date``, "Date and time in hourly steps."
    ``Eaux_SC_kWh``, "TODO"
    


PVT_totals
----------

path: ``outputs/data/potentials/solar/PVT_total.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Q_PVT_l_kWh``, "Collector heat loss."
    ``Q_PVT_gen_kWh``, "Total heat generated by the collector."
    ``PVT_walls_south_E_kWh``, "Electricity production from photovoltaic-thermal panels on south facades"
    ``Eaux_PVT_kWh``, "Auxiliary electricity consumed by the collector."
    ``PVT_walls_west_Q_kWh``, "Heat production from photovoltaic-thermal panels on west facades"
    ``PVT_roofs_top_Q_kWh``, "Heat production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_east_Q_kWh``, "Heat production from photovoltaic-thermal panels on east facades"
    ``Area_PVT_m2``, "Total area of investigated collector."
    ``radiation_kWh``, "Total radiatiative potential."
    ``PVT_roofs_top_m2``, "Collector surface area on roof tops."
    ``PVT_roofs_top_E_kWh``, "Electricity production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_west_m2``, "West facing wall collector surface area."
    ``T_PVT_sup_C``, "Collector heating supply temperature."
    ``PVT_walls_north_E_kWh``, "Electricity production from photovoltaic-thermal panels on north facades"
    ``T_PVT_re_C``, "Collector heating supply temperature."
    ``E_PVT_gen_kWh``, "Total electricity generated by the collector."
    ``PVT_walls_west_E_kWh``, "Electricity production from photovoltaic-thermal panels on west facades"
    ``PVT_walls_east_E_kWh``, "Electricity production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_south_Q_kWh``, "Heat production from photovoltaic-thermal panels on south facades"
    ``mcp_PVT_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector."
    ``PVT_walls_east_m2``, "Collector surface area on east facades."
    ``Date``, "Date and time in hourly steps."
    ``PVT_walls_north_Q_kWh``, "Heat production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_north_m2``, "Collector surface area on north facades."
    ``PVT_walls_south_m2``, "Collector surface area on south facades."
    


get_thermal_demand_csv_file
---------------------------

path: ``outputs/data/thermal-network/DH__thermal_demand_per_building_W.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``B01``, "TODO"
    


get_optimization_slave_electricity_requirements_data
----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_1_Electricity_Requirements_Pattern.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``E_cs_cre_cdata_req_connected_W``, "TODO"
    ``E_BaseVCC_AS_req_W``, "TODO"
    ``E_Storage_discharging_req_W``, "TODO"
    ``E_hs_ww_req_connected_W``, "TODO"
    ``E_DHN_req_W``, "TODO"
    ``E_HP_SC_FP_req_W``, "TODO"
    ``E_Storage_charging_req_W``, "TODO"
    ``E_cs_cre_cdata_req_disconnected_W``, "TODO"
    ``E_HP_Server_req_W``, "TODO"
    ``DATE``, "TODO"
    ``E_BackupBoiler_req_W``, "TODO"
    ``E_HP_Sew_req_W``, "TODO"
    ``E_hs_ww_req_disconnected_W``, "TODO"
    ``E_GHP_req_W``, "TODO"
    ``Eaux_req_W``, "TODO"
    ``E_BaseVCC_WS_req_W``, "TODO"
    ``E_PeakVCC_WS_req_W``, "TODO"
    ``Edata_req_W``, "TODO"
    ``E_PeakVCC_AS_req_W``, "TODO"
    ``E_BaseBoiler_req_W``, "TODO"
    ``E_HP_Lake_req_W``, "TODO"
    ``E_electricalnetwork_sys_req_W``, "TODO"
    ``E_DCN_req_W``, "TODO"
    ``Eal_req_W``, "TODO"
    ``Epro_req_W``, "TODO"
    ``E_HP_PVT_req_W``, "TODO"
    ``E_PeakBoiler_req_W``, "TODO"
    ``E_HP_SC_ET_req_W``, "TODO"
    ``E_BackupVCC_AS_req_W``, "TODO"
    


get_optimization_checkpoint
---------------------------

path: ``outputs/data/optimization/master/CheckPoint_1``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``generation``, "TODO"
    ``difference_generational_distances``, "TODO"
    ``generational_distances``, "TODO"
    ``selected_population``, "TODO"
    ``tested_population``, "TODO"
    


get_database_construction_standards
-----------------------------------

path: ``inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx``

The following file is used by these scripts: ``archetypes_mapper``




.. csv-table:: ``inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx`` Worksheet: ``HVAC_ASSEMBLIES``
    :header: "Variable", "Description"
    ``heat_ends``, End of the heating season - use 00|00 when there is none``type_ctrl``, Type of heating and cooling control systems (relates to values in Default Database HVAC Properties)``type_cs``, Type of cooling supply system``cool_starts``, Start of the cooling season - use 00|00 when there is none``STANDARD``,  Unique ID of Construction Standard``type_hs``, Type of heating supply system``heat_starts``, Start of the heating season - use 00|00 when there is none``type_vent``, Type of ventilation strategy (relates to values in Default Database HVAC Properties)``cool_ends``, End of the cooling season - use 00|00 when there is none``type_dhw``, Type of hot water supply system



.. csv-table:: ``inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx`` Worksheet: ``ENVELOPE_ASSEMBLIES``
    :header: "Variable", "Description"
    ``type_shade``, Shading system type (relates to values in Default Database Construction Properties)``type_part``, Internal partitions construction type (relates to values in Default Database Construction Properties)``Hs_bg``, Fraction of below ground gross floor area air-conditioned ``STANDARD``,  Unique ID of Construction Standard``wwr_north``, Window to wall ratio in in facades facing north``Hs_ag``, Fraction of above ground gross floor area air-conditioned.``Ns``, Fraction of net gross floor area.``type_roof``, Roof construction type (relates to values in Default Database Construction Properties)``type_wall``, External wall construction type (relates to values in Default Database Construction Properties)``type_base``, Basement floor construction type (relates to values in Default Database Construction Properties)``wwr_west``, Window to wall ratio in in facades facing west``type_cons``, Type of construction. It relates to the contents of the default database of Envelope Properties: construction``type_leak``, Tightness level. It relates to the contents of the default database of Envelope Properties: tightness``type_floor``, Internal floor construction type (relates to values in Default Database Construction Properties)``wwr_south``, Window to wall ratio in in facades facing south``wwr_east``, Window to wall ratio in in facades facing east``type_win``, Window type (relates to values in Default Database Construction Properties)``Es``, Fraction of gross floor area with electrical demands.``void_deck``, Number of floors (from the ground up) with an open envelope (default = 0)



.. csv-table:: ``inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx`` Worksheet: ``SUPPLY_ASSEMBLIES``
    :header: "Variable", "Description"
    ``type_el``, Type of electrical supply system``type_hs``, Type of heating supply system``type_cs``, Type of cooling supply system``type_dhw``, Type of hot water supply system``STANDARD``,  Unique ID of Construction Standard



.. csv-table:: ``inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx`` Worksheet: ``STANDARD_DEFINITION``
    :header: "Variable", "Description"
    ``STANDARD``,  Unique ID of Construction Standard``YEAR_START``, Lower limit of year interval where the building properties apply``Description``, Description of the construction standard``YEAR_END``, Upper limit of year interval where the building properties apply




get_building_comfort
--------------------

path: ``inputs/building-properties/indoor_comfort.dbf``

The following file is used by these scripts: ``demand``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``RH_max_pc``, "Upper bound of relative humidity"
    ``Tcs_set_C``, "Setpoint temperature for cooling system"
    ``Name``, "Unique building ID. It must start with a letter."
    ``Ths_setb_C``, "Setback point of temperature for heating system"
    ``Ths_set_C``, "Setpoint temperature for heating system"
    ``Tcs_setb_C``, "Setback point of temperature for cooling system"
    ``Ve_lpspax``, "Indoor quality requirements of indoor ventilation per person"
    ``RH_min_pc``, "Lower_bound of relative humidity"
    


get_water_body_potential
------------------------

path: ``outputs/data/potentials/Water_body_potential.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Ts_C``, "TODO"
    ``QLake_kW``, "TODO"
    


get_optimization_connected_cooling_capacity
-------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_1_connected_cooling_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_DX_AS_cool_disconnected_W``, "TODO"
    ``Name``, "TODO"
    ``Capaticy_ACH_SC_ET_cool_disconnected_W``, "TODO"
    ``Capacity_ACHHT_FP_cool_disconnected_W``, "TODO"
    ``Capacity_VCCHT_AS_cool_disconnected_W``, "TODO"
    ``Capacity_BaseVCC_AS_cool_disconnected_W``, "TODO"
    ``Capacity_ACH_SC_FP_cool_disconnected_W``, "TODO"
    


PV_total_buildings
------------------

path: ``outputs/data/potentials/solar/PV_total_buildings.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PV_walls_west_m2``, "West facing wall collector surface area."
    ``PV_roofs_top_m2``, "Collector surface area on roof tops."
    ``Unnamed: 0``, "TODO"
    ``PV_walls_north_E_kWh``, "Electricity production from photovoltaic panels on north facades"
    ``Area_PV_m2``, "Total area of investigated collector."
    ``E_PV_gen_kWh``, "Total electricity generated by the collector."
    ``PV_walls_south_m2``, "Collector surface area on south facades."
    ``PV_walls_east_E_kWh``, "Electricity production from photovoltaic panels on east facades"
    ``PV_walls_east_m2``, "Collector surface area on east facades."
    ``radiation_kWh``, "Total radiatiative potential."
    ``PV_walls_south_E_kWh``, "Electricity production from photovoltaic panels on south facades"
    ``PV_roofs_top_E_kWh``, "Electricity production from photovoltaic panels on roof tops"
    ``PV_walls_west_E_kWh``, "Electricity production from photovoltaic panels on west facades"
    ``PV_walls_north_m2``, "Collector surface area on north facades."
    


get_optimization_decentralized_folder_building_result_heating
-------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/DiscOp_B001_result_heating.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Unnamed: 0``, "TODO"
    ``Opex_var_USD``, "TODO"
    ``Capacity_FC_NG_W``, "TODO"
    ``Capacity_BaseBoiler_NG_W``, "TODO"
    ``Best configuration``, "TODO"
    ``Capex_total_USD``, "TODO"
    ``Capacity_GS_HP_W``, "TODO"
    ``Opex_fixed_USD``, "TODO"
    ``Nominal heating load``, "TODO"
    ``TAC_USD``, "TODO"
    ``Capex_a_USD``, "TODO"
    ``GHG_tonCO2``, "TODO"
    ``PEN_MJoil``, "TODO"
    


get_multi_criteria_analysis
---------------------------

path: ``outputs/data/multicriteria/gen_2_multi_criteria_analysis.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``TAC_sys_connected_USD``, "TODO"
    ``generation``, "TODO"
    ``Capex_total_sys_connected_USD``, "TODO"
    ``PEN_sys_disconnected_MJoil``, "TODO"
    ``GHG_rank``, "TODO"
    ``GHG_sys_tonCO2``, "TODO"
    ``TAC_sys_USD``, "TODO"
    ``Opex_a_sys_connected_USD``, "TODO"
    ``individual_name``, "TODO"
    ``Capex_a_sys_USD``, "TODO"
    ``GHG_sys_disconnected_tonCO2``, "TODO"
    ``PEN_sys_MJoil``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``normalized_TAC``, "TODO"
    ``normalized_prim``, "TODO"
    ``Capex_total_sys_disconnected_USD``, "TODO"
    ``TAC_sys_disconnected_USD``, "TODO"
    ``Capex_a_sys_disconnected_USD``, "TODO"
    ``TAC_rank``, "TODO"
    ``normalized_emissions``, "TODO"
    ``Capex_total_sys_USD``, "TODO"
    ``normalized_Capex_total``, "TODO"
    ``GHG_sys_connected_tonCO2``, "TODO"
    ``Unnamed: 0.1``, "TODO"
    ``PEN_sys_connected_MJoil``, "TODO"
    ``user_MCDA_rank``, "TODO"
    ``PEN_rank``, "TODO"
    ``normalized_Opex``, "TODO"
    ``Opex_a_sys_disconnected_USD``, "TODO"
    ``user_MCDA``, "TODO"
    ``Capex_a_sys_connected_USD``, "TODO"
    ``individual``, "TODO"
    ``Opex_a_sys_USD``, "TODO"
    


get_network_thermal_loss_edges_file
-----------------------------------

path: ``outputs/data/thermal-network/DH__thermal_loss_edges_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    


get_lca_operation
-----------------

path: ``outputs/data/emissions/Total_LCA_operation.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``COAL_ww_ghg_kgm2``, "Emissions due to operational energy per unit of conditionend floor area of the coal powered domestic hot water system"
    ``COAL_hs_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the coal powererd heating system"
    ``OIL_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for oil powered domestic hot water system"
    ``DC_cre_ghg_ton``, "TODO"
    ``NG_ww_ghg_ton``, "Emissions due to operational energy of the solar powered domestic hot water system"
    ``GHG_sys_tonCO2``, "Energy system operation"
    ``COAL_hs_ghg_ton``, "Emissions due to operational energy of the coal powered heating system"
    ``DH_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district heating powered domestic hot water system"
    ``COAL_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the coal powered domestic hot water system"
    ``DH_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district heating system"
    ``DH_hs_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the district heating system"
    ``NG_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for natural gas powered heating system"
    ``PV_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for PV-System"
    ``WOOD_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the wood powered heating system"
    ``GRID_ghg_ton``, "Emissions due to operational energy of the electrictiy from the grid"
    ``DC_cre_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the dstrict cooling for cooling and refrigeration"
    ``DH_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district heating system"
    ``NG_hs_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the natural gas powered heating system"
    ``SOLAR_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for solar powered domestic hot water system"
    ``SOLAR_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the solar powered heating system"
    ``GRID_nre_pen_GJ``, "Operational primary energy demand (non-renewable) from the grid"
    ``PV_nre_pen_MJm2.1``, "TODO"
    ``PV_nre_pen_GJ.1``, "TODO"
    ``SOLAR_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) of the solar powered heating system"
    ``WOOD_ww_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the wood powered domestic hot water system"
    ``SOLAR_ww_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the solar powered domestic hot water system"
    ``DC_cdata_ghg_ton``, "Emissions due to operational energy of the district cooling for the data center"
    ``SOLAR_ww_ghg_ton``, "Emissions due to operational energy of the solar powered domestic hot water system"
    ``SOLAR_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the solar poweed domestic hot water system"
    ``DC_cs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district cooling system"
    ``COAL_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the coal powered heating system"
    ``DC_cs_ghg_ton``, "Emissions due to operational energy of the district cooling"
    ``OIL_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the oil powered domestic hot water system"
    ``GRID_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) from grid electricity"
    ``WOOD_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the wood powered domestic hot water system"
    ``Name.1``, "TODO"
    ``GRID_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area from grid electricity"
    ``GHG_sys_kgCO2m2``, "Energy system operation"
    ``NG_hs_ghg_ton``, "Emissions due to operational energy of the natural gas powered heating system"
    ``DH_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district heating domestic hot water system"
    ``PV_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area for PV-System"
    ``DC_cdata_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district cooling system of the data center"
    ``DC_cdata_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the dstrict cooling for the data center"
    ``OIL_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for oil powered heating system"
    ``OIL_ww_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the oil powered domestic hot water system"
    ``WOOD_ww_ghg_ton``, "Emissions due to operational energy of the wood powered domestic hot water system"
    ``NG_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for natural gas powered domestic hot water system"
    ``DH_ww_ghg_ton``, "Emissions due to operational energy of the district heating powered domestic hot water system"
    ``DC_cs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district cooling"
    ``PV_ghg_kgm2.1``, "TODO"
    ``OIL_hs_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the oil powered heating system"
    ``SOLAR_hs_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the solar powered heating system"
    ``Name``, "Unique building ID. It must start with a letter."
    ``OIL_ww_ghg_ton``, "Emissions due to operational energy of the oil powered domestic hot water system"
    ``NG_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the natural gas powered domestic hot water system"
    ``GFA_m2``, "Gross floor area"
    ``PV_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) for PV System"
    ``NG_ww_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the gas powered domestic hot water system"
    ``DC_cre_ghg_kgm2``, "TODO"
    ``GFA_m2.1``, "TODO"
    ``OIL_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the oil powered heating system"
    ``DC_cs_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the district cooling"
    ``PV_ghg_ton.1``, "TODO"
    ``DH_ww_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the district heating domestic hot water system"
    ``OIL_hs_ghg_ton``, "Emissions due to operational energy of the oil powered heating system"
    ``WOOD_hs_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the wood powered heating system"
    ``WOOD_hs_ghg_ton``, "Emissions due to operational energy of the wood powered heating system"
    ``SOLAR_hs_ghg_ton``, "Emissions due to operational energy of the solar powered heating system"
    ``DC_cdata_ghg_kgm2``, "Emissions due to operational energy per unit of conditioned floor area of the district cooling for the data center"
    ``COAL_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for coal powered heating system"
    ``COAL_ww_ghg_ton``, "Emissions due to operational energy of the coal powered domestic hot water system"
    ``NG_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the natural gas powered heating system"
    ``DH_hs_ghg_ton``, "Emissions due to operational energy of the district heating system"
    ``WOOD_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for wood powered domestic hot water system"
    ``DC_cre_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district cooling system for cooling and refrigeration"
    ``COAL_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for coal powered domestic hot water system"
    ``PV_ghg_ton``, "Emissions due to operational energy of the PV-System"
    ``WOOD_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for wood powered heating system"
    


get_optimization_connected_heating_capacity
-------------------------------------------

path: ``outputs/data/optimization/slave/gen_0/ind_2_connected_heating_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_HP_DS_heat_connected_W``, "TODO"
    ``Capacity_HP_GS_heat_connected_W``, "TODO"
    ``Capacity_CHP_DB_el_connected_W``, "TODO"
    ``Capacity_PeakBoiler_NG_heat_connected_W``, "TODO"
    ``Capacity_PVT_el_connected_W``, "TODO"
    ``Capacity_CHP_NG_heat_connected_W``, "TODO"
    ``Capacity_BaseBoiler_NG_heat_connected_W``, "TODO"
    ``Capacity_PVT_connected_m2``, "TODO"
    ``Capacity_HP_WS_heat_connected_W``, "TODO"
    ``Capacity_BackupBoiler_NG_heat_connected_W``, "TODO"
    ``Capacity_SC_FP_connected_m2``, "TODO"
    ``Capacity_HP_SS_heat_connected_W``, "TODO"
    ``Capacity_CHP_WB_heat_connected_W``, "TODO"
    ``Capacity_CHP_DB_heat_connected_W``, "TODO"
    ``Capacity_SeasonalStorage_WS_heat_connected_W``, "TODO"
    ``Capacity_SC_ET_heat_connected_W``, "TODO"
    ``Capacity_SeasonalStorage_WS_heat_connected_m3``, "TODO"
    ``Capacity_PVT_heat_connected_W``, "TODO"
    ``Capacity_SC_ET_connected_m2``, "TODO"
    ``Capacity_CHP_NG_el_connected_W``, "TODO"
    ``Capacity_SC_FP_heat_connected_W``, "TODO"
    ``Capacity_CHP_WB_el_connected_W``, "TODO"
    


get_geothermal_potential
------------------------

path: ``outputs/data/potentials/Shallow_geothermal_potential.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Ts_C``, "TODO"
    ``Area_avail_m2``, "TODO"
    ``QGHP_kW``, "TODO"
    


get_optimization_generation_total_performance_halloffame
--------------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/gen_1_total_performance_halloffame.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``generation``, "TODO"
    ``Capex_total_sys_connected_USD``, "TODO"
    ``PEN_sys_disconnected_MJoil``, "TODO"
    ``GHG_sys_tonCO2``, "TODO"
    ``Capex_a_sys_connected_USD``, "TODO"
    ``TAC_sys_USD``, "TODO"
    ``Opex_a_sys_connected_USD``, "TODO"
    ``individual_name``, "TODO"
    ``individual``, "TODO"
    ``TAC_sys_connected_USD``, "TODO"
    ``GHG_sys_disconnected_tonCO2``, "TODO"
    ``Opex_a_sys_disconnected_USD``, "TODO"
    ``PEN_sys_MJoil``, "TODO"
    ``GHG_sys_connected_tonCO2``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Capex_total_sys_disconnected_USD``, "TODO"
    ``PEN_sys_connected_MJoil``, "TODO"
    ``TAC_sys_disconnected_USD``, "TODO"
    ``Capex_a_sys_USD``, "TODO"
    ``Capex_a_sys_disconnected_USD``, "TODO"
    ``Capex_total_sys_USD``, "TODO"
    ``Opex_a_sys_USD``, "TODO"
    


get_database_feedstocks
-----------------------

path: ``inputs/technology/components/FEEDSTOCKS.xls``

The following file is used by these scripts: ``decentralized``, ``emissions``, ``system_costs``, ``optimization``




.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``OIL``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``COAL``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``DRYBIOMASS``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``BIOGAS``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``GRID``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``SOLAR``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``WOOD``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``NATURALGAS``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day



.. csv-table:: ``inputs/technology/components/FEEDSTOCKS.xls`` Worksheet: ``WETBIOMASS``
    :header: "Variable", "Description"
    ``Opex_var_buy_USD2015kWh``, buying price``Opex_var_sell_USD2015kWh``, selling price``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor``reference``, reference``hour``, hour of a 24 hour day




get_database_standard_schedules_use
-----------------------------------

path: ``inputs/technology/archetypes/schedules/RESTAURANT.csv``

The following file is used by these scripts: ``archetypes_mapper``




.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``PROCESSES``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``ELECTROMOBILITY``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``HEATING``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``OCCUPANCY``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``SERVERS``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``WATER``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``MONTHLY_MULTIPLIER``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``COOLING``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``LIGHTING``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``APPLIANCES``
    :header: "Variable", "Description"
    ``1``, TODO``2``, TODO``3``, TODO``4``, TODO``5``, TODO``6``, TODO``7``, TODO``8``, TODO``9``, TODO``10``, TODO``11``, TODO``12``, TODO``13``, TODO``14``, TODO``15``, TODO``16``, TODO``17``, TODO``18``, TODO``19``, TODO``20``, TODO``21``, TODO``22``, TODO``23``, TODO``24``, TODO``DAY``, TODO



.. csv-table:: ``inputs/technology/archetypes/schedules/RESTAURANT.csv`` Worksheet: ``METADATA``
    :header: "Variable", "Description"
    ``metadata``, TODO




get_thermal_network_node_types_csv_file
---------------------------------------

path: ``outputs/data/thermal-network/DH__metadata_nodes.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Building``, "TODO"
    ``Type``, "TODO"
    


get_optimization_slave_building_connectivity
--------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_1_building_connectivity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``DC_connectivity``, "TODO"
    ``DH_connectivity``, "TODO"
    ``Name``, "TODO"
    


get_optimization_decentralized_folder_building_result_cooling
-------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/{building}_{configuration}_cooling.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Capaticy_ACH_SC_ET_W``, "TODO"
    ``Capacity_BaseVCC_AS_W``, "TODO"
    ``Unnamed: 0``, "TODO"
    ``Opex_var_USD``, "TODO"
    ``Capacity_VCCHT_AS_W``, "TODO"
    ``Best configuration``, "TODO"
    ``Capex_total_USD``, "TODO"
    ``Nominal heating load``, "TODO"
    ``Capacity_ACH_SC_FP_W``, "TODO"
    ``Opex_fixed_USD``, "TODO"
    ``TAC_USD``, "TODO"
    ``Capex_a_USD``, "TODO"
    ``Capacity_DX_AS_W``, "TODO"
    ``GHG_tonCO2``, "TODO"
    ``Capacity_ACHHT_FP_W``, "TODO"
    


get_network_linear_pressure_drop_edges
--------------------------------------

path: ``outputs/data/thermal-network/DH__linear_pressure_drop_edges_Paperm.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    


get_network_temperature_return_nodes_file
-----------------------------------------

path: ``outputs/data/thermal-network/DH__temperature_return_nodes_K.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "TODO"
    


get_thermal_network_velocity_edges_file
---------------------------------------

path: ``outputs/data/thermal-network/DH__velocity_edges_mpers.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    


get_building_architecture
-------------------------

path: ``inputs/building-properties/architecture.dbf``

The following file is used by these scripts: ``demand``, ``emissions``, ``radiation``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``type_shade``, "Shading system type (relates to values in Default Database Construction Properties)"
    ``Name``, "Unique building ID. It must start with a letter."
    ``Hs_bg``, "Fraction of below ground gross floor area air-conditioned."
    ``wwr_north``, "Window to wall ratio in in facades facing north"
    ``Hs_ag``, "Fraction of above ground gross floor area air-conditioned."
    ``Ns``, "Fraction of net gross floor area."
    ``type_roof``, "Roof construction type (relates to values in Default Database Construction Properties)"
    ``type_wall``, "External wall construction type (relates to values in Default Database Construction Properties)"
    ``type_base``, "Basement floor construction type (relates to values in Default Database Construction Properties)"
    ``wwr_west``, "Window to wall ratio in in facades facing west"
    ``type_cons``, "Type of construction. It relates to the contents of the default database of Envelope Properties: construction"
    ``type_leak``, "Tightness level. It relates to the contents of the default database of Envelope Properties: tightness"
    ``type_floor``, "Internal floor construction type (relates to values in Default Database Construction Properties)"
    ``wwr_south``, "Window to wall ratio in in facades facing south"
    ``wwr_east``, "Window to wall ratio in in facades facing east"
    ``type_win``, "Window type (relates to values in Default Database Construction Properties)"
    ``Es``, "Fraction of gross floor area with electrical demands."
    ``void_deck``, "Number of floors (from the ground up) with an open envelope (default = 0)"
    


get_radiation_building
----------------------

path: ``outputs/data/solar-radiation/{building}_radiation.csv``

The following file is used by these scripts: ``demand``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``


.. csv-table::
    :header: "Variable", "Description"

    ``windows_south_m2``, "TODO"
    ``walls_south_kW``, "TODO"
    ``windows_east_kW``, "TODO"
    ``walls_north_kW``, "TODO"
    ``walls_east_kW``, "TODO"
    ``roofs_top_m2``, "TODO"
    ``windows_west_kW``, "TODO"
    ``walls_west_m2``, "TODO"
    ``walls_north_m2``, "TODO"
    ``roofs_top_kW``, "TODO"
    ``windows_north_m2``, "TODO"
    ``windows_east_m2``, "TODO"
    ``walls_east_m2``, "TODO"
    ``windows_south_kW``, "TODO"
    ``windows_north_kW``, "TODO"
    ``walls_south_m2``, "TODO"
    ``Date``, "TODO"
    ``windows_west_m2``, "TODO"
    ``walls_west_kW``, "TODO"
    


PV_results
----------

path: ``outputs/data/potentials/solar/B001_PV.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PV_walls_west_m2``, "West facing wall collector surface area."
    ``PV_roofs_top_m2``, "Collector surface area on roof tops."
    ``PV_walls_north_E_kWh``, "Electricity production from photovoltaic panels on north facades"
    ``Area_PV_m2``, "Total area of investigated collector."
    ``E_PV_gen_kWh``, "Total electricity generated by the collector."
    ``PV_walls_south_m2``, "Collector surface area on south facades."
    ``PV_walls_east_E_kWh``, "Electricity production from photovoltaic panels on east facades"
    ``PV_walls_east_m2``, "Collector surface area on east facades."
    ``radiation_kWh``, "Total radiatiative potential."
    ``Date``, "Date and time in hourly steps."
    ``PV_walls_south_E_kWh``, "Electricity production from photovoltaic panels on south facades"
    ``PV_roofs_top_E_kWh``, "Electricity production from photovoltaic panels on roof tops"
    ``PV_walls_west_E_kWh``, "Electricity production from photovoltaic panels on west facades"
    ``PV_walls_north_m2``, "Collector surface area on north facades."
    


get_network_layout_edges_shapefile
----------------------------------

path: ``outputs/data/thermal-network/DH/edges.shp``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``geometry``, "Geometry"
    ``length_m``, "TODO"
    ``Name``, "Unique building ID. It must start with a letter."
    ``Pipe_DN``, "Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter."
    ``Type_mat``, "Material type"
    


get_nominal_node_mass_flow_csv_file
-----------------------------------

path: ``outputs/data/thermal-network/Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "TODO"
    ``Unnamed: 0``, "TODO"
    


get_radiation_building_sensors
------------------------------

path: ``outputs/data/solar-radiation/B001_insolation_Whm2.json``

The following file is used by these scripts: ``demand``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``


.. csv-table::
    :header: "Variable", "Description"

    ``srf0``, "TODO"
    


SC_total_buildings
------------------

path: ``outputs/data/potentials/solar/SC_ET_total_buildings.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``SC_ET_walls_east_m2``, "TODO"
    ``SC_ET_walls_south_m2``, "TODO"
    ``SC_ET_roofs_top_m2``, "TODO"
    ``SC_ET_walls_west_m2``, "TODO"
    ``Q_SC_l_kWh``, "TODO"
    ``radiation_kWh``, "Total radiatiative potential."
    ``Unnamed: 0``, "TODO"
    ``Q_SC_gen_kWh``, "TODO"
    ``SC_ET_walls_west_Q_kWh``, "TODO"
    ``SC_ET_roofs_top_Q_kWh``, "TODO"
    ``SC_ET_walls_south_Q_kWh``, "TODO"
    ``SC_ET_walls_east_Q_kWh``, "TODO"
    ``SC_ET_walls_north_m2``, "TODO"
    ``SC_ET_walls_north_Q_kWh``, "TODO"
    ``Area_SC_m2``, "TODO"
    ``Eaux_SC_kWh``, "TODO"
    


PVT_total_buildings
-------------------

path: ``outputs/data/potentials/solar/PVT_total_buildings.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Q_PVT_l_kWh``, "Collector heat loss."
    ``Name``, "TODO"
    ``Q_PVT_gen_kWh``, "Total heat generated by the collector."
    ``Eaux_PVT_kWh``, "Auxiliary electricity consumed by the collector."
    ``PVT_walls_west_Q_kWh``, "Heat production from photovoltaic-thermal panels on west facades"
    ``PVT_roofs_top_Q_kWh``, "Heat production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_east_Q_kWh``, "Heat production from photovoltaic-thermal panels on east facades"
    ``Area_PVT_m2``, "Total area of investigated collector."
    ``radiation_kWh``, "Total radiatiative potential."
    ``PVT_roofs_top_m2``, "Collector surface area on roof tops."
    ``PVT_roofs_top_E_kWh``, "Electricity production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_west_m2``, "West facing wall collector surface area."
    ``PVT_walls_north_E_kWh``, "Electricity production from photovoltaic-thermal panels on north facades"
    ``E_PVT_gen_kWh``, "Total electricity generated by the collector."
    ``PVT_walls_west_E_kWh``, "Electricity production from photovoltaic-thermal panels on west facades"
    ``PVT_walls_east_E_kWh``, "Electricity production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_south_Q_kWh``, "Heat production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_east_m2``, "Collector surface area on east facades."
    ``PVT_walls_south_E_kWh``, "Electricity production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_north_Q_kWh``, "Heat production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_north_m2``, "Collector surface area on north facades."
    ``PVT_walls_south_m2``, "Collector surface area on south facades."
    


get_thermal_network_edge_node_matrix_file
-----------------------------------------

path: ``outputs/data/thermal-network/{network_type}__EdgeNode.csv``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "TODO"
    ``Unnamed: 0``, "TODO"
    


get_database_envelope_systems
-----------------------------

path: ``inputs/technology/assemblies/ENVELOPE.xls``

The following file is used by these scripts: ``demand``, ``radiation``, ``schedule_maker``




.. csv-table:: ``inputs/technology/assemblies/ENVELOPE.xls`` Worksheet: ``WINDOW``
    :header: "Variable", "Description"
    ``F_F``, Window frame fraction coefficient. Defined according to ISO 13790.``code``, Building use. It relates to the uses stored in the input database of Zone_occupancy``Description``, Describes the source of the benchmark standards.``e_win``, Emissivity of external surface. Defined according to ISO 13790.``G_win``, Solar heat gain coefficient. Defined according to ISO 13790.``GHG_WIN_kgCO2m2``, Embodied emissions per m2 of windows.(entire building life cycle)``U_win``, Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.



.. csv-table:: ``inputs/technology/assemblies/ENVELOPE.xls`` Worksheet: ``CONSTRUCTION``
    :header: "Variable", "Description"
    ``code``, Type of construction``Description``, Describes the Type of construction``Cm_Af``, Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790.



.. csv-table:: ``inputs/technology/assemblies/ENVELOPE.xls`` Worksheet: ``TIGHTNESS``
    :header: "Variable", "Description"
    ``code``, Type of tightness``Description``, Describes the Type of tightness``n50``, Air exchanges per hour at a pressure of 50 Pa.



.. csv-table:: ``inputs/technology/assemblies/ENVELOPE.xls`` Worksheet: ``FLOOR``
    :header: "Variable", "Description"
    ``U_base``, Thermal transmittance of floor including linear losses (+10%). Defined according to ISO 13790.``code``, Type of roof``GHG_FLOOR_kgCO2m2``, Embodied emissions per m2 of roof.(entire building life cycle)``Description``, Describes the Type of roof



.. csv-table:: ``inputs/technology/assemblies/ENVELOPE.xls`` Worksheet: ``WALL``
    :header: "Variable", "Description"
    ``r_wall``, Reflectance in the Red spectrum. Defined according Radiance. (long-wave)``code``, Type of wall``Description``, Describes the Type of wall``a_wall``, Solar absorption coefficient. Defined according to ISO 13790.``U_wall``, Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.``e_wall``, Emissivity of external surface. Defined according to ISO 13790.``GHG_WALL_kgCO2m2``, Embodied emissions per m2 of walls (entire building life cycle)



.. csv-table:: ``inputs/technology/assemblies/ENVELOPE.xls`` Worksheet: ``SHADING``
    :header: "Variable", "Description"
    ``code``, Type of shading``Description``, Describes the source of the benchmark standards.``rf_sh``, Shading coefficient when shading device is active. Defined according to ISO 13790.



.. csv-table:: ``inputs/technology/assemblies/ENVELOPE.xls`` Worksheet: ``ROOF``
    :header: "Variable", "Description"
    ``e_roof``, Emissivity of external surface. Defined according to ISO 13790.``code``, Type of roof``Description``, Describes the Type of roof``GHG_ROOF_kgCO2m2``, Embodied emissions per m2 of roof.(entire building life cycle)``a_roof``, Solar absorption coefficient. Defined according to ISO 13790.``r_roof``, Reflectance in the Red spectrum. Defined according Radiance. (long-wave)``U_roof``, Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.




SC_metadata_results
-------------------

path: ``outputs/data/potentials/solar/B001_SC_ET_sensors.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``surface_azimuth_deg``, "Azimuth angle of the panel surface e.g. south facing = 180 deg"
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``Ycoor``, "Describes the position of the y vector."
    ``area_installed_module_m2``, "The area of the building suface covered by one solar panel"
    ``tilt_deg``, "Tilt angle of roof or walls"
    ``surface``, "Unique surface ID for each building exterior surface."
    ``Xcoor``, "Describes the position of the x vector."
    ``total_rad_Whm2``, "Total radiatiative potential of a given surfaces area."
    ``CATteta_z``, "Category according to the surface azimuth of the panel"
    ``AREA_m2``, "Surface area."
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``Ydir``, "Directional scalar of the y vector."
    ``intersection``, "TODO"
    ``B_deg``, "Tilt angle of the installed solar panels"
    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``CATB``, "Category according to the tilt angle of the panel"
    ``type_orientation``, "Concatenated surface type and orientation."
    ``CATGB``, "Category according to the annual radiation on the panel surface"
    ``Xdir``, "Directional scalar of the x vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    ``array_spacing_m``, "Spacing between solar arrays."
    ``TYPE``, "Surface typology."
    


get_optimization_slave_disconnected_performance
-----------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_0_buildings_disconnected_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PEN_cooling_disconnected_MJoil``, "TODO"
    ``Opex_var_cooling_disconnected_USD``, "TODO"
    ``Capex_total_cooling_disconnected_USD``, "TODO"
    ``Capex_a_cooling_disconnected_USD``, "TODO"
    ``GHG_cooling_disconnected_tonCO2``, "TODO"
    ``Capex_total_heating_disconnected_USD``, "TODO"
    ``Capex_a_heating_disconnected_USD``, "TODO"
    ``GHG_heating_disconnected_tonCO2``, "TODO"
    ``Opex_var_heating_disconnected_USD``, "TODO"
    ``PEN_heating_disconnected_MJoil``, "TODO"
    ``Opex_fixed_heating_disconnected_USD``, "TODO"
    ``Opex_fixed_cooling_disconnected_USD``, "TODO"
    

