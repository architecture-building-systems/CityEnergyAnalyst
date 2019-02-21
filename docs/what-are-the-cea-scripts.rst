What are the CEA Scripts?
=========================
CEA relies on a number of scripts which may share dependencies.
This section aims to clarify the files created or used by each script, along with the methods used
to access this data. All script requests for reading or writing data are routed through the inputlocator's specific 'get_methods',
which join the current working path with that of the desired input/output file.
Scripts can be run via the command line interface (cli) by calling: ``cea script-name``.

Core
----
Currently, the CEA operates using a core set of scripts whose outputs are necessary for the function of most
other scripts. They should be run in the following order:

    #.   ``data-helper`` : creates secondary input databases from the default within cea/databases
         (only needs to be run once for each scenario).
    #.   ``radiation-daysim`` : creates the solar insolation data for each building using daysim.
    #.   ``demand`` : creates a demand approximation for each building.

.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap = false, fontname=arial];
        "data-helper"[shape=note, style=filled, color=white, fillcolor="#3FC0C2", fontname=arial, fontsize=20];
        "demand"[shape=note, style=filled, color=white, fillcolor="#3FC0C2", fontname=arial, fontsize=20];
        "radiation-daysim"[shape=note, style=filled, color=white, fillcolor="#3FC0C2", fontname=arial, fontsize=20];
        node [shape=box, style=filled, fillcolor="#E1F2F2", fontname=arial, fontsize=15, fixedsize=true, width=3.75]
        "databases/CH/archetypes" -> "data-helper"
        "inputs/building-properties" -> "data-helper"
        "databases/CH/archetypes" -> "demand"
        "inputs/building-properties" -> "demand"
        "databases/CH/lifecycle" -> "demand"
        "outputs/data/solar-radiation" -> "demand"
        "databases/CH/systems" -> "demand"
        "cea/databases/weather" -> "demand"
        "inputs/building-geometry" -> "demand"
        "inputs/building-properties" -> "radiation-daysim"
        "databases/CH/systems" -> "radiation-daysim"
        "inputs/topography" -> "radiation-daysim"
        "cea/databases/weather" -> "radiation-daysim"
        "inputs/building-geometry" -> "radiation-daysim"
        "data-helper" -> "inputs/building-properties"
        "demand" -> "outputs/data/demand"
        "radiation-daysim" -> "outputs/data/solar-radiation"
        {rank=same "databases/CH/lifecycle" "databases/CH/archetypes" "inputs/building-geometry" "databases/CH/systems" "inputs/topography" "cea/databases/weather" "inputs/building-properties"}
    }


data-helper
-----------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=2.8];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "data-helper"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/archetypes";
            "construction_properties.xlsx"
            "occupancy_schedules.xlsx"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-properties";
            "age.dbf"
            "occupancy.dbf"
        }
        subgraph cluster_1_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="inputs/building-properties";
            "architecture.dbf"
            "indoor_comfort.dbf"
            "technical_systems.dbf"
            "internal_loads.dbf"
            "restrictions.dbf"
            "supply_systems.dbf"
        }
        "construction_properties.xlsx" -> "data-helper"[label="(get_archetypes_properties)"]
        "occupancy_schedules.xlsx" -> "data-helper"[label="(get_archetypes_schedules)"]
        "age.dbf" -> "data-helper"[label="(get_building_age)"]
        "occupancy.dbf" -> "data-helper"[label="(get_building_occupancy)"]
        "data-helper" -> "architecture.dbf"[label="(get_building_architecture)"]
        "data-helper" -> "indoor_comfort.dbf"[label="(get_building_comfort)"]
        "data-helper" -> "technical_systems.dbf"[label="(get_building_hvac)"]
        "data-helper" -> "internal_loads.dbf"[label="(get_building_internal)"]
        "data-helper" -> "restrictions.dbf"[label="(get_building_restrictions)"]
        "data-helper" -> "supply_systems.dbf"[label="(get_building_supply)"]
    }

thermal-network-matrix
----------------------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5.085];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "thermal-network-matrix"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="cea/databases/weather";
            "Zug.epw"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/systems";
            "supply_systems.xls"
            "thermal_networks.xls"
        }
        subgraph cluster_2_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/networks/DH";
            "nodes.shp"
        }
        subgraph cluster_2_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="inputs/networks/DH";
            "edges.shp"
        }
        subgraph cluster_3_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="outputs/data/demand";
            "{BUILDING}.csv"
        }
        subgraph cluster_4_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="outputs/data/optimization/network/layout";
            "Nominal_EdgeMassFlow_at_design_DH__kgpers.csv"
            "DH__Nodes.csv"
            "Nominal_NodeMassFlow_at_design_DH__kgpers.csv"
            "DH__Edges.csv"
            "DH__EdgeNode.csv"
            "DH__MassFlow_kgs.csv"
            "DH__Plant_heat_requirement_kW.csv"
            "DH__ploss_System_edges_kW.csv"
            "DH__P_DeltaP_Pa.csv"
            "DH__P_DeltaP_kW.csv"
            "DH__qloss_System_kW.csv"
            "DH__T_Return_K.csv"
            "DH__T_Supply_K.csv"
            "DH__Nodes.csv"
            "DH__ploss_Substations_kW.csv"
            "DH__substaion_HEX_cost_USD.csv"
            "Aggregated_Demand_DH__Wh.csv"
        }
        "{BUILDING}.csv" -> "thermal-network-matrix"[label="(get_demand_results_file)"]
        "nodes.shp" -> "thermal-network-matrix"[label="(get_network_layout_nodes_shapefile)"]
        "supply_systems.xls" -> "thermal-network-matrix"[label="(get_supply_systems)"]
        "thermal_networks.xls" -> "thermal-network-matrix"[label="(get_thermal_networks)"]
        "Zug.epw" -> "thermal-network-matrix"[label="(get_weather)"]
        "thermal-network-matrix" -> "Nominal_EdgeMassFlow_at_design_DH__kgpers.csv"[label="(get_edge_mass_flow_csv_file)"]
        "thermal-network-matrix" -> "edges.shp"[label="(get_network_layout_edges_shapefile)"]
        "thermal-network-matrix" -> "DH__Nodes.csv"[label="(get_network_node_types_csv_file)"]
        "thermal-network-matrix" -> "Nominal_NodeMassFlow_at_design_DH__kgpers.csv"[label="(get_node_mass_flow_csv_file)"]
        "thermal-network-matrix" -> "DH__Edges.csv"[label="(get_optimization_network_edge_list_file)"]
        "thermal-network-matrix" -> "DH__EdgeNode.csv"[label="(get_optimization_network_edge_node_matrix_file)"]
        "thermal-network-matrix" -> "DH__MassFlow_kgs.csv"[label="(get_optimization_network_layout_massflow_file)"]
        "thermal-network-matrix" -> "DH__Plant_heat_requirement_kW.csv"[label="(get_optimization_network_layout_plant_heat_requirement_file)"]
        "thermal-network-matrix" -> "DH__ploss_System_edges_kW.csv"[label="(get_optimization_network_layout_ploss_system_edges_file)"]
        "thermal-network-matrix" -> "DH__P_DeltaP_Pa.csv"[label="(get_optimization_network_layout_pressure_drop_file)"]
        "thermal-network-matrix" -> "DH__P_DeltaP_kW.csv"[label="(get_optimization_network_layout_pressure_drop_kw_file)"]
        "thermal-network-matrix" -> "DH__qloss_System_kW.csv"[label="(get_optimization_network_layout_qloss_system_file)"]
        "thermal-network-matrix" -> "DH__T_Return_K.csv"[label="(get_optimization_network_layout_return_temperature_file)"]
        "thermal-network-matrix" -> "DH__T_Supply_K.csv"[label="(get_optimization_network_layout_supply_temperature_file)"]
        "thermal-network-matrix" -> "DH__Nodes.csv"[label="(get_optimization_network_node_list_file)"]
        "thermal-network-matrix" -> "DH__ploss_Substations_kW.csv"[label="(get_optimization_network_substation_ploss_file)"]
        "thermal-network-matrix" -> "DH__substaion_HEX_cost_USD.csv"[label="(get_substation_HEX_cost)"]
        "thermal-network-matrix" -> "Aggregated_Demand_DH__Wh.csv"[label="(get_thermal_demand_csv_file)"]
    }

solar-collector
---------------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=3.503];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "solar-collector"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="cea/databases/weather";
            "Zug.epw"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/systems";
            "supply_systems.xls"
        }
        subgraph cluster_2_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-geometry";
            "zone.shp"
        }
        subgraph cluster_3_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="outputs/data/potentials/solar";
            "{BUILDING}_SC_FP_sensors.csv"
            "{BUILDING}_SC_FP.csv"
            "SC_FP_total_buildings.csv"
            "SC_FP_total.csv"
        }
        subgraph cluster_4_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="outputs/data/solar-radiation";
            "{BUILDING}_insolation_Whm2.json"
            "{BUILDING}_geometry.csv"
        }
        "{BUILDING}_insolation_Whm2.json" -> "solar-collector"[label="(get_radiation_building)"]
        "{BUILDING}_geometry.csv" -> "solar-collector"[label="(get_radiation_metadata)"]
        "supply_systems.xls" -> "solar-collector"[label="(get_supply_systems)"]
        "Zug.epw" -> "solar-collector"[label="(get_weather)"]
        "zone.shp" -> "solar-collector"[label="(get_zone_geometry)"]
        "solar-collector" -> "{BUILDING}_SC_FP_sensors.csv"[label="(SC_metadata_results)"]
        "solar-collector" -> "{BUILDING}_SC_FP.csv"[label="(SC_results)"]
        "solar-collector" -> "SC_FP_total_buildings.csv"[label="(SC_total_buildings)"]
        "solar-collector" -> "SC_FP_total.csv"[label="(SC_totals)"]
    }

photovoltaic-thermal
--------------------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=3.503];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "photovoltaic-thermal"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="cea/databases/weather";
            "Zug.epw"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/systems";
            "supply_systems.xls"
        }
        subgraph cluster_2_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-geometry";
            "zone.shp"
        }
        subgraph cluster_3_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="outputs/data/potentials/solar";
            "{BUILDING}_PVT_sensors.csv"
            "{BUILDING}_PVT.csv"
            "PVT_total_buildings.csv"
            "PVT_total.csv"
        }
        subgraph cluster_4_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="outputs/data/solar-radiation";
            "{BUILDING}_insolation_Whm2.json"
            "{BUILDING}_geometry.csv"
        }
        "{BUILDING}_insolation_Whm2.json" -> "photovoltaic-thermal"[label="(get_radiation_building)"]
        "{BUILDING}_geometry.csv" -> "photovoltaic-thermal"[label="(get_radiation_metadata)"]
        "supply_systems.xls" -> "photovoltaic-thermal"[label="(get_supply_systems)"]
        "Zug.epw" -> "photovoltaic-thermal"[label="(get_weather)"]
        "zone.shp" -> "photovoltaic-thermal"[label="(get_zone_geometry)"]
        "photovoltaic-thermal" -> "{BUILDING}_PVT_sensors.csv"[label="(PVT_metadata_results)"]
        "photovoltaic-thermal" -> "{BUILDING}_PVT.csv"[label="(PVT_results)"]
        "photovoltaic-thermal" -> "PVT_total_buildings.csv"[label="(PVT_total_buildings)"]
        "photovoltaic-thermal" -> "PVT_total.csv"[label="(PVT_totals)"]
    }

photovoltaic
------------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=3.503];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "photovoltaic"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="cea/databases/weather";
            "Zug.epw"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/systems";
            "supply_systems.xls"
        }
        subgraph cluster_2_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-geometry";
            "zone.shp"
        }
        subgraph cluster_3_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="outputs/data/potentials/solar";
            "{BUILDING}_PV_sensors.csv"
            "{BUILDING}_PV.csv"
            "PV_total_buildings.csv"
            "PV_total.csv"
        }
        subgraph cluster_4_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="outputs/data/solar-radiation";
            "{BUILDING}_insolation_Whm2.json"
            "{BUILDING}_geometry.csv"
        }
        "{BUILDING}_insolation_Whm2.json" -> "photovoltaic"[label="(get_radiation_building)"]
        "{BUILDING}_geometry.csv" -> "photovoltaic"[label="(get_radiation_metadata)"]
        "supply_systems.xls" -> "photovoltaic"[label="(get_supply_systems)"]
        "Zug.epw" -> "photovoltaic"[label="(get_weather)"]
        "zone.shp" -> "photovoltaic"[label="(get_zone_geometry)"]
        "photovoltaic" -> "{BUILDING}_PV_sensors.csv"[label="(PV_metadata_results)"]
        "photovoltaic" -> "{BUILDING}_PV.csv"[label="(PV_results)"]
        "photovoltaic" -> "PV_total_buildings.csv"[label="(PV_total_buildings)"]
        "photovoltaic" -> "PV_total.csv"[label="(PV_totals)"]
    }

radiation-daysim
----------------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=3.503];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "radiation-daysim"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="cea/databases/weather";
            "Zug.epw"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/systems";
            "envelope_systems.xls"
        }
        subgraph cluster_2_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-geometry";
            "district.shp"
            "zone.shp"
        }
        subgraph cluster_3_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-properties";
            "architecture.dbf"
        }
        subgraph cluster_4_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/topography";
            "terrain.tif"
        }
        subgraph cluster_5_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="outputs/data/solar-radiation";
            "{BUILDING}_insolation_Whm2.json"
            "{BUILDING}_geometry.csv"
        }
        "architecture.dbf" -> "radiation-daysim"[label="(get_building_architecture)"]
        "district.shp" -> "radiation-daysim"[label="(get_district_geometry)"]
        "envelope_systems.xls" -> "radiation-daysim"[label="(get_envelope_systems)"]
        "terrain.tif" -> "radiation-daysim"[label="(get_terrain)"]
        "Zug.epw" -> "radiation-daysim"[label="(get_weather)"]
        "zone.shp" -> "radiation-daysim"[label="(get_zone_geometry)"]
        "radiation-daysim" -> "{BUILDING}_insolation_Whm2.json"[label="(get_radiation_building)"]
        "radiation-daysim" -> "{BUILDING}_geometry.csv"[label="(get_radiation_metadata)"]
    }

demand
------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=3.503];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "demand"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="cea/databases/weather";
            "Zug.epw"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/archetypes";
            "construction_properties.xlsx"
            "occupancy_schedules.xlsx"
            "system_controls.xlsx"
        }
        subgraph cluster_2_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/lifecycle";
            "LCA_infrastructure.xlsx"
        }
        subgraph cluster_3_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/systems";
            "envelope_systems.xls"
            "emission_systems.xls"
        }
        subgraph cluster_4_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-geometry";
            "zone.shp"
        }
        subgraph cluster_5_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-properties";
            "age.dbf"
            "architecture.dbf"
            "indoor_comfort.dbf"
            "technical_systems.dbf"
            "internal_loads.dbf"
            "occupancy.dbf"
            "supply_systems.dbf"
        }
        subgraph cluster_6_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="outputs/data/demand";
            "{BUILDING}.csv"
            "Total_demand.csv"
        }
        subgraph cluster_7_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="outputs/data/solar-radiation";
            "{BUILDING}_insolation_Whm2.json"
            "{BUILDING}_geometry.csv"
        }
        "construction_properties.xlsx" -> "demand"[label="(get_archetypes_properties)"]
        "occupancy_schedules.xlsx" -> "demand"[label="(get_archetypes_schedules)"]
        "system_controls.xlsx" -> "demand"[label="(get_archetypes_system_controls)"]
        "age.dbf" -> "demand"[label="(get_building_age)"]
        "architecture.dbf" -> "demand"[label="(get_building_architecture)"]
        "indoor_comfort.dbf" -> "demand"[label="(get_building_comfort)"]
        "technical_systems.dbf" -> "demand"[label="(get_building_hvac)"]
        "internal_loads.dbf" -> "demand"[label="(get_building_internal)"]
        "occupancy.dbf" -> "demand"[label="(get_building_occupancy)"]
        "supply_systems.dbf" -> "demand"[label="(get_building_supply)"]
        "envelope_systems.xls" -> "demand"[label="(get_envelope_systems)"]
        "LCA_infrastructure.xlsx" -> "demand"[label="(get_life_cycle_inventory_supply_systems)"]
        "{BUILDING}_insolation_Whm2.json" -> "demand"[label="(get_radiation_building)"]
        "{BUILDING}_geometry.csv" -> "demand"[label="(get_radiation_metadata)"]
        "emission_systems.xls" -> "demand"[label="(get_technical_emission_systems)"]
        "Zug.epw" -> "demand"[label="(get_weather)"]
        "zone.shp" -> "demand"[label="(get_zone_geometry)"]
        "demand" -> "{BUILDING}.csv"[label="(get_demand_results_file)"]
        "demand" -> "Total_demand.csv"[label="(get_total_demand)"]
    }

emissions
---------
.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        graph [overlap=false, fontname=arial];
        node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=3.5];
        edge [fontname=arial, fontsize = 15]
        newrank=true
        subgraph cluster_legend {
        fontsize=25
        style=invis
        "process"[style=filled, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname="arial"]
        "inputs" [style=filled, shape=folder, color=white, fillcolor="#E1F2F2", fontsize=20]
        "outputs"[style=filled, shape=folder, color=white, fillcolor="#aadcdd", fontsize=20]
        "inputs"->"process"[style=invis]
        "process"->"outputs"[style=invis]
        }
        "emissions"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
        subgraph cluster_0_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/benchmarks";
            "benchmark_2000W.xls"
        }
        subgraph cluster_1_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="databases/CH/lifecycle";
            "LCA_buildings.xlsx"
            "LCA_infrastructure.xlsx"
        }
        subgraph cluster_2_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-geometry";
            "zone.shp"
        }
        subgraph cluster_3_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="inputs/building-properties";
            "age.dbf"
            "architecture.dbf"
            "occupancy.dbf"
            "supply_systems.dbf"
        }
        subgraph cluster_4_in {
            style = filled;
            color = "#E1F2F2";
            fontsize = 20;
            rank=same;
            label="outputs/data/demand";
            "Total_demand.csv"
        }
        subgraph cluster_5_out {
            style = filled;
            color = "#aadcdd";
            fontsize = 20;
            rank=same;
            label="outputs/data/emissions";
            "Total_LCA_embodied.csv"
            "Total_LCA_mobility.csv"
            "Total_LCA_operation.csv"
        }
        "age.dbf" -> "emissions"[label="(get_building_age)"]
        "architecture.dbf" -> "emissions"[label="(get_building_architecture)"]
        "occupancy.dbf" -> "emissions"[label="(get_building_occupancy)"]
        "supply_systems.dbf" -> "emissions"[label="(get_building_supply)"]
        "benchmark_2000W.xls" -> "emissions"[label="(get_data_benchmark)"]
        "LCA_buildings.xlsx" -> "emissions"[label="(get_life_cycle_inventory_building_systems)"]
        "LCA_infrastructure.xlsx" -> "emissions"[label="(get_life_cycle_inventory_supply_systems)"]
        "Total_demand.csv" -> "emissions"[label="(get_total_demand)"]
        "zone.shp" -> "emissions"[label="(get_zone_geometry)"]
        "emissions" -> "Total_LCA_embodied.csv"[label="(get_lca_embodied)"]
        "emissions" -> "Total_LCA_mobility.csv"[label="(get_lca_mobility)"]
        "emissions" -> "Total_LCA_operation.csv"[label="(get_lca_operation)"]
    }
