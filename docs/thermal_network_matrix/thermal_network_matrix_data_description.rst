Data description for thermal_network_matrix.py
==============================================

.. contents::


This document describes the main variables used in the :py:mod:`cea.technologies.thermal_network.thermal_network_matrix`
module.

The order of presentation follows the order of creating when running the script.

ThermalNetwork.buildings_demands
--------------------------------

:type: dictionary containing a DataFrame for each building

Description of each Dataframe:

:shape:   (8760, 25)
:Columns: - Name
          - Ef_kWh
          - Qhsf_kWh
          - Qwwf_kWh
          - Qcsf_kWh
          - Qcsf_lat_kWh
          - Qcdataf_kWh
          - Qcref_kWh
          - mcphsf_kWperC
          - mcpcsf_kWperC
          - mcpwwf_kWperC
          - Twwf_sup_C
          - Twwf_re_C
          - Thsf_sup_C
          - Thsf_re_C
          - Tcsf_sup_C
          - Tcsf_re_C
          - Tcdataf_re_C
          - Tcdataf_sup_C
          - Tcref_re_C
          - Tcref_sup_C
          - Q_substation_heating
          - Q_substation_cooling
          - T_sup_target_DH
          - T_sup_target_DC
:Index: Time steps 0-8759
:created by: - ThermalNetwork _init_ (empty)
             - substation_matrix.determine_building_supply_temperatures
:passed to:  - substation_matrix.substation_HEX_design_main     (creating substations_HEX_specs)
             - read_properties_from_buildings (creating t_target_supply_C)
             - initial_diameter_guess
             - substation_return_model_main
             - hourly_thermal_calculation


ThermalNetwork.substations_HEX_specs
------------------------------------

:type: DataFrame
:shape: (len(building_names), 6)
:Columns:    - HEX_area_SH
             - HEX_area_DHW
             - HEX_area_SC
             - HEX_UA_SH
             - HEX_UA_DHW
             - HEX_UA_SC
:Index: building_names

:created by: - ThermalNetwork _init_ (empty)
             - substation_matrix.substation_HEX_design_main
:passed to:  - network_parameters (dictionary)
             - initial_diameter_guess
             - hourly_mass_flow_calculation
             - substation_return_model_main
             - hourly_thermal_calculation


ThermalNetwork.t_target_supply_C
--------------------------------

:type: DataFrame
:shape: (8760, len(building_names))
:Columns: building_names
:Index: Timesteps 0-8759

:created by:  - ThermalNetwork _init_ (empty)
              - read_properties_from_buildings
:passed to:   - write_substation_temperatures_to_nodes_df (creating t_target_supply_df),
              - calc_max_edge_flowrate,
              - initial_diameter_guess,
              - hourly_mass_flow_calculation

T_substation_supply_K
---------------------
:type: DataFrame
:shape: (1, len(building_names))
:Columns: building_names
:Index: ['T_supply']

:created by: - hourly_mass_flow_calculation
             - write_nodes_values_to_substations
:passed to:  - substation_return_model_main


ThermalNetwork.t_target_supply_df
---------------------------------
:type: DataFrame
:shape: (8760, number_of_nodes)
:Columns: All Nodes ([NODE0, ...])
:Index: Timesteps 0-8759

:created by:  - ThermalNetwork _init_ (empty)
              - write_substation_temperatures_to_nodes_df
:passed to:


ThermalNetwork.all_nodes_df
---------------------------
:type: DataFrame
:shape: (number_of_nodes, 2)
:Columns: - Type
          - Building
:Index: All Nodes ([NODE0, ...])

:created by:  - ThermalNetwork _init_ (empty)
              - get_thermal_network_from_shapefile
:passed to:   - write_substation_temperatures_to_nodes_df (creating t_target_supply_df)
              - network_parameters (dictionary)
              - initial_diameter_guess
              - hourly_mass_flow_calculation (creating required_flow_rate_df)
              - substation_return_model_main
              - calc_mass_flow_edges
              - hourly_thermal_calculation


ThermalNetwork.edge_df
-----------------------
:type: GeoDataFrame
:shape:  - initially: (number_of_edges, 7),
         - later: (number_of_edges, 15),
            - merge with ThermalNetwork.pipe_properties in thermal_network_main to store data and output together in one file

:Columns: - initially:

            - type_mat
            - pipe_DN
            - geometry
            - coordinates
            - pipe length
            - start node
            - end node

          - later:

            - type_mat
            - pipe_DN_x
            - geometry
            - coordinates
            - pipe length
            - start node
            - end node
            - pipe_DN_y
            - D_ext_m
            - D_int_m
            - D_ins_m
            - Vdot_min_m3s
            - Vdot_max_m3s
            - mdot_min_kgs
            - mdot_max_kgs
:Index: All Edges ([PIPE0, ...])

:created by: - ThermalNetwork _init_
             - get_thermal_network_from_shapefile
:passed to:  - network_parameters (dictionary)
             - initial_diameter_guess
             - hourly_mass_flow_calculation
             - substation_return_model_main
             - hourly_thermal_calculation


ThermalNetwork.edge_node_df
----------------------------
:type: DataFrame
:shape: (number_of_nodes, number_of_edges)
:Columns: All Edges ([PIPE0, ...])
:Index: All Nodes ([NODE0, ...])

:created by: - ThermalNetwork _init_ (empty)
             - get_thermal_network_from_shapefile
:passed to:  - network_parameters (dictionary)
             - initial_diameter_guess
             - hourly_mass_flow_calculation
             - substation_return_model_main
             - calc_mass_flow_edges
             - hourly_thermal_calculation


ThermalNetwork.edge_mass_flow_df
--------------------------------
:type: DataFrame
:shape: (8760, number_of_edges)
:Columns: All Edges ([PIPE0, PIPE1, ..., PIPEn])
:Index: Timesteps 0-8759

:created by: - ThermalNetwork _init_ (empty)
             - calc_max_edge_flowrate
             - load_max_edge_flowrate_from_previous_run (read from csv)
:passed to:  - network_parameters (dictionary)
             - hourly_mass_flow_calculation
             - hourly_thermal_calculation


ThermalNetwork.node_mass_flow_df
--------------------------------
:type: DataFrame
:shape: (8760, number_of_nodes)
:Columns: All Edges ([NODE0, NODE1, ..., NODEn])
:Index: Timesteps 0-8759

:created by: - ThermalNetwork _init_ (empty)
             - calc_max_edge_flowrate
:passed to: hourly_mass_flow_calculation


T_return_all
------------
:type: DataFrame
:shape: (1, len(building_names))
:Columns: building_names
:Index: 0

:created by: hourly_mass_flow_calculation
:passed to:



mdot_all
--------
:type: DataFrame
:shape: (1, len(building_names))
:Columns: building_names
:Index: 0

:created by: hourly_mass_flow_calculation
:passed to: write_substation_values_to_nodes_df (creating required_flow_rate_df)


required_flow_rate_df
---------------------
:type: DataFrame
:shape: (1, number_of_nodes)
:Columns: All Nodes ([NODE0, ...])
:Index: 0

:created by: write_substation_values_to_nodes_df
:passed to: calc_mass_flow_edges



max_edge_mass_flow_df
---------------------
:type: DataFrame
:shape: (1, number_of_edges)
:Columns: All Edges ([PIPE0, ...])
:Index: 0

:created by: calc_max_edge_flowrate
:passed to: max_edge_mass_flow_df_kgs (rename when exiting calc_max_edge_flowrate function)



ThermalNetwork.pipe_properties
------------------------------
:type: DataFrame
:shape: (8, number_of_edges)
:Columns: All Edges ([PIPE0, ...])
:Index:      - pipe_DN
             - D_ext_m
             - D_int_m
             - D_ins_m
             - Vdot_min_m3s
             - Vdot_max_m3s
             - mdot_min_kgs
             - mdot_max_kgs

:created by: - ThermalNetwork _init_ (empty)
             - calc_max_edge_flowrate
:passed to:  - network_parameters (dictionary)
             - merged into edge_df
             - hourly_thermal_calculation


Description of DataFrames and Lists written to csv by the thermal_network_matrix.py file
========================================================================================

sorted in order of creation in the script

csv_outputs['T_supply_nodes']
-----------------------------

:type: DataFrame
:shape: (8760, number_of_nodes),
:Columns: All Nodes ([NODE0, ...])
:Index: Timesteps 0-8759


csv_outputs['T_return_nodes']
-----------------------------

:type: DataFrame
:shape: (8760, number_of_nodes),
:Columns: All Nodes ([NODE0, ...])
:Index: Timesteps 0-8759


csv_outputs['q_loss_supply_edges']
----------------------------------

:type: DataFrame
:shape: (8760, number_of_edges),
:Columns: All Edges ([PIPE0, ...])
:Index: Timesteps 0-8759


csv_outputs['plant_heat_requirement']
-------------------------------------

:type: DataFrame
:shape: (8760, number_of_plants),
:Columns: Plant Buildings
:Index: Timesteps 0-8759


csv_outputs['pressure_nodes_supply']
------------------------------------

:type: DataFrame
:shape: (8760, number_of_nodes),
:Columns: All Nodes ([NODE0, ...])
:Index: Timesteps 0-8759


csv_outputs['pressure_nodes_return']
------------------------------------

:type: DataFrame
:shape: (8760, number_of_nodes),
:Columns: All Nodes ([NODE0, ...])
:Index: Timesteps 0-8759


csv_outputs['pressure_loss_system_Pa']
--------------------------------------

:type: DataFrame
:shape: (8760, 3),
:Columns: - pressure_loss_supply_Pa
          - pressure_loss_return_Pa
          - pressure_loss_total_Pa
:Index: Timesteps 0-8759


csv_outputs['pressure_loss_system_kW']
--------------------------------------

:type: DataFrame
:shape: (8760, 3),
:Columns: - pressure_loss_supply_kW
          - pressure_loss_return_kW
          - pressure_loss_total_kW
:Index: Timesteps 0-8759


csv_outputs['pressure_loss_supply_kW']
--------------------------------------

:type: DataFrame
:shape: (8760, number_of_edges),
:Columns: All Edges ([PIPE0, ...])
:Index: Timesteps 0-8759


csv_outputs['q_loss_system']
----------------------------

:type: DataFrame
:shape: (8760, 3),
:Columns: 0
:Index: Timesteps 0-8759


csv_outputs['edge_mass_flows']
------------------------------

:type: DataFrame
:shape: (8760, number_of_edges),
:Columns: All Edges ([PIPE0, ...])
:Index: Timesteps 0-8759
