What are the CEA Scripts?
=========================
CEA relies on a number of scripts which may share dependencies.
This section aims to clarify the databases created or used by each script, along with the methods used
to access this data. Scripts can be run via the command line interface (cli) by calling: ``cea script-name``.

Core
----
Currently, the CEA operates using a core set of scripts whose outputs are necessary for the function of
other scripts. They should be run in the following order:

    #.   ``data-helper`` : creates secondary input databases from the default within cea/databases
         (only needs to be run once for each scenario).
    #.   ``radiation-daysim`` : creates the solar insolation data for each building using daysim.
    #.   ``demand`` : creates a demand approximation for each building.

.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        node [shape=box, style=filled, fillcolor=peachpuff]
        graph [overlap = false];
        "data-helper"[style=filled, fillcolor=darkorange];
        "demand"[style=filled, fillcolor=darkorange];
        "radiation-daysim"[style=filled, fillcolor=darkorange];
        "databases/CH/archetypes" -> "data-helper"
        "inputs/building-properties" -> "data-helper"
        "databases/CH/archetypes" -> "demand"
        "inputs/building-properties" -> "demand"
        "databases/CH/systems" -> "demand"
        "databases/CH/lifecycle" -> "demand"
        "outputs/data/solar-radiation" -> "demand"
        "databases/CH/systems" -> "demand"
        "../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather" -> "demand"
        "inputs/building-geometry" -> "demand"
        "inputs/building-properties" -> "radiation-daysim"
        "inputs/building-geometry" -> "radiation-daysim"
        "databases/CH/systems" -> "radiation-daysim"
        "inputs/topography" -> "radiation-daysim"
        "../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather" -> "radiation-daysim"
        "inputs/building-geometry" -> "radiation-daysim"
        "data-helper" -> "inputs/building-properties"
        "demand" -> "outputs/data/demand"
        "radiation-daysim" -> "outputs/data/solar-radiation"
        }


data-helper
-----------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "data-helper"[style=filled, fillcolor=darkorange];
    "construction_properties.xlsx" -> "data-helper"[label="get_archetypes_properties"]
    "occupancy_schedules.xlsx" -> "data-helper"[label="get_archetypes_schedules"]
    "age.dbf" -> "data-helper"[label="get_building_age"]
    "occupancy.dbf" -> "data-helper"[label="get_building_occupancy"]
    "data-helper" -> "architecture.dbf"[label="get_building_architecture"]
    "data-helper" -> "indoor_comfort.dbf"[label="get_building_comfort"]
    "data-helper" -> "technical_systems.dbf"[label="get_building_hvac"]
    "data-helper" -> "internal_loads.dbf"[label="get_building_internal"]
    "data-helper" -> "restrictions.dbf"[label="get_building_restrictions"]
    "data-helper" -> "supply_systems.dbf"[label="get_building_supply"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="databases/CH/archetypes";
    "construction_properties.xlsx"[style=filled, color=white]
    "occupancy_schedules.xlsx"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="inputs/building-properties";
    "age.dbf"[style=filled, color=white]
    "occupancy.dbf"[style=filled, color=white]
    "architecture.dbf"[style=filled, color=white]
    "indoor_comfort.dbf"[style=filled, color=white]
    "technical_systems.dbf"[style=filled, color=white]
    "internal_loads.dbf"[style=filled, color=white]
    "restrictions.dbf"[style=filled, color=white]
    "supply_systems.dbf"[style=filled, color=white]
    }
    }

thermal-network-matrix
----------------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "thermal-network-matrix"[style=filled, fillcolor=darkorange];
    "thermal-network-matrix" -> "Aggregated_Demand_DH__Wh.csv"[label="get_thermal_demand_csv_file"]
    "thermal-network-matrix" -> "DH__Plant_heat_requirement_kW.csv"[label="get_optimization_network_layout_plant_heat_requirement_file"]
    "thermal-network-matrix" -> "DH__MassFlow_kgs.csv"[label="get_optimization_network_layout_massflow_file"]
    "thermal-network-matrix" -> "DH__Edges.csv"[label="get_optimization_network_edge_list_file"]
    "thermal-network-matrix" -> "DH__P_DeltaP_kW.csv"[label="get_optimization_network_layout_pressure_drop_kw_file"]
    "thermal-network-matrix" -> "DH__substaion_HEX_cost_USD.csv"[label="get_substation_HEX_cost"]
    "thermal-network-matrix" -> "DH__P_DeltaP_Pa.csv"[label="get_optimization_network_layout_pressure_drop_file"]
    "thermal-network-matrix" -> "DH__Nodes.csv"[label="get_optimization_network_node_list_file"]
    "thermal-network-matrix" -> "DH__ploss_System_edges_kW.csv"[label="get_optimization_network_layout_ploss_system_edges_file"]
    "thermal-network-matrix" -> "DH__T_Supply_K.csv"[label="get_optimization_network_layout_supply_temperature_file"]
    "thermal-network-matrix" -> "DH__qloss_System_kW.csv"[label="get_optimization_network_layout_qloss_system_file"]
    "thermal-network-matrix" -> "DH__T_Return_K.csv"[label="get_optimization_network_layout_return_temperature_file"]
    "thermal-network-matrix" -> "DH__EdgeNode.csv"[label="get_optimization_network_edge_node_matrix_file"]
    "thermal-network-matrix" -> "DH__ploss_Substations_kW.csv"[label="get_optimization_network_substation_ploss_file"]
    "thermal-network-matrix" -> "Nominal_EdgeMassFlow_at_design_DH__kgpers.csv"[label="get_edge_mass_flow_csv_file"]
    "thermal-network-matrix" -> "Nominal_NodeMassFlow_at_design_DH__kgpers.csv"[label="get_node_mass_flow_csv_file"]

    "{BUILDING}.csv" -> "thermal-network-matrix"[label="get_demand_results_file"]

    "thermal-network-matrix" -> "edges.shp"[label="get_network_layout_edges_shapefile"]
    "nodes.shp" -> "thermal-network-matrix"[label="get_network_layout_nodes_shapefile"]

    "Zug.epw" -> "thermal-network-matrix"[label="get_weather"]

    "supply_systems.xls" -> "thermal-network-matrix"[label="get_supply_systems"]
    "thermal_networks.xls" -> "thermal-network-matrix"[label="get_thermal_networks"]

    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
	label="outputs/data/optimization/network/layout/"
	"Aggregated_Demand_DH__Wh.csv"[style=filled, color=white]
	"DH__Plant_heat_requirement_kW.csv"[style=filled, color=white]
	"DH__MassFlow_kgs.csv"[style=filled, color=white]
	"DH__Edges.csv"[style=filled, color=white]
	"DH__EdgeNode.csv"[style=filled, color=white]
	"DH__P_DeltaP_kW.csv"[style=filled, color=white]
	"DH__substaion_HEX_cost_USD.csv"[style=filled, color=white]
	"DH__P_DeltaP_Pa.csv"[style=filled, color=white]
	"DH__Nodes.csv"[style=filled, color=white]
	"DH__ploss_System_edges_kW.csv"[style=filled, color=white]
	"DH__T_Supply_K.csv"[style=filled, color=white]
	"DH__qloss_System_kW.csv"[style=filled, color=white]
	"DH__T_Return_K.csv"[style=filled, color=white]
	"DH__ploss_Substations_kW.csv"[style=filled, color=white]
	"Nominal_EdgeMassFlow_at_design_DH__kgpers.csv"[style=filled, color=white]
	"Nominal_NodeMassFlow_at_design_DH__kgpers.csv"[style=filled, color=white]
	}

    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
	label="outputs/data/demand/"
	"{BUILDING}.csv"[style=filled, color=white]
	}

    subgraph cluster_2 {
        style = filled;
        color = peachpuff;
	label="inputs/networks/DH/"
	"edges.shp"[style=filled, color=white]
	"nodes.shp"[style=filled, color=white]
	}

    subgraph cluster_3 {
        style = filled;
        color = peachpuff;
	label="../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather/"
	"Zug.epw"[style=filled, color=white]
	}

    subgraph cluster_4 {
        style = filled;
        color = peachpuff;
	label="databases/CH/systems/"
	"supply_systems.xls"[style=filled, color=white]
	"thermal_networks.xls"[style=filled, color=white]
	}
	}


solar-collector
---------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "solar-collector"[style=filled, fillcolor=darkorange];
    "{BUILDING}_insolation_Whm2.json" -> "solar-collector"[label="get_radiation_building"]
    "{BUILDING}_geometry.csv" -> "solar-collector"[label="get_radiation_metadata"]
    "supply_systems.xls" -> "solar-collector"[label="get_supply_systems"]
    "Zug.epw" -> "solar-collector"[label="get_weather"]
    "zone.shp" -> "solar-collector"[label="get_zone_geometry"]
    "solar-collector" -> "{BUILDING}_SC_FP_sensors.csv"[label="SC_metadata_results"]
    "solar-collector" -> "{BUILDING}_SC_FP.csv"[label="SC_results"]
    "solar-collector" -> "SC_FP_total_buildings.csv"[label="SC_total_buildings"]
    "solar-collector" -> "SC_FP_total.csv"[label="SC_totals"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather";
    "Zug.epw"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="databases/CH/systems";
    "supply_systems.xls"[style=filled, color=white]
    }
    subgraph cluster_2 {
        style = filled;
        color = peachpuff;
        label="inputs/building-geometry";
    "zone.shp"[style=filled, color=white]
    }
    subgraph cluster_3 {
        style = filled;
        color = peachpuff;
        label="outputs/data/potentials/solar";
    "{BUILDING}_SC_FP_sensors.csv"[style=filled, color=white]
    "{BUILDING}_SC_FP.csv"[style=filled, color=white]
    "SC_FP_total_buildings.csv"[style=filled, color=white]
    "SC_FP_total.csv"[style=filled, color=white]
    }
    subgraph cluster_4 {
        style = filled;
        color = peachpuff;
        label="outputs/data/solar-radiation";
    "{BUILDING}_insolation_Whm2.json"[style=filled, color=white]
    "{BUILDING}_geometry.csv"[style=filled, color=white]
    }
    }

photovoltaic-thermal
--------------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "photovoltaic-thermal"[style=filled, fillcolor=darkorange];
    "{BUILDING}_insolation_Whm2.json" -> "photovoltaic-thermal"[label="get_radiation_building"]
    "{BUILDING}_geometry.csv" -> "photovoltaic-thermal"[label="get_radiation_metadata"]
    "supply_systems.xls" -> "photovoltaic-thermal"[label="get_supply_systems"]
    "Zug.epw" -> "photovoltaic-thermal"[label="get_weather"]
    "zone.shp" -> "photovoltaic-thermal"[label="get_zone_geometry"]
    "photovoltaic-thermal" -> "{BUILDING}_PVT_sensors.csv"[label="PVT_metadata_results"]
    "photovoltaic-thermal" -> "{BUILDING}_PVT.csv"[label="PVT_results"]
    "photovoltaic-thermal" -> "PVT_total_buildings.csv"[label="PVT_total_buildings"]
    "photovoltaic-thermal" -> "PVT_total.csv"[label="PVT_totals"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather";
    "Zug.epw"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="databases/CH/systems";
    "supply_systems.xls"[style=filled, color=white]
    }
    subgraph cluster_2 {
        style = filled;
        color = peachpuff;
        label="inputs/building-geometry";
    "zone.shp"[style=filled, color=white]
    }
    subgraph cluster_3 {
        style = filled;
        color = peachpuff;
        label="outputs/data/potentials/solar";
    "{BUILDING}_PVT_sensors.csv"[style=filled, color=white]
    "{BUILDING}_PVT.csv"[style=filled, color=white]
    "PVT_total_buildings.csv"[style=filled, color=white]
    "PVT_total.csv"[style=filled, color=white]
    }
    subgraph cluster_4 {
        style = filled;
        color = peachpuff;
        label="outputs/data/solar-radiation";
    "{BUILDING}_insolation_Whm2.json"[style=filled, color=white]
    "{BUILDING}_geometry.csv"[style=filled, color=white]
    }
    }

lake-potential
--------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "lake-potential"[style=filled, fillcolor=darkorange];
    "lake-potential" -> "Lake_potential.csv"[label="get_lake_potential"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="outputs/data/potentials";
    "Lake_potential.csv"[style=filled, color=white]
    }
    }

photovoltaic
------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "photovoltaic"[style=filled, fillcolor=darkorange];
    "{BUILDING}_insolation_Whm2.json" -> "photovoltaic"[label="get_radiation_building"]
    "{BUILDING}_geometry.csv" -> "photovoltaic"[label="get_radiation_metadata"]
    "supply_systems.xls" -> "photovoltaic"[label="get_supply_systems"]
    "Zug.epw" -> "photovoltaic"[label="get_weather"]
    "zone.shp" -> "photovoltaic"[label="get_zone_geometry"]
    "photovoltaic" -> "{BUILDING}_PV_sensors.csv"[label="PV_metadata_results"]
    "photovoltaic" -> "{BUILDING}_PV.csv"[label="PV_results"]
    "photovoltaic" -> "PV_total_buildings.csv"[label="PV_total_buildings"]
    "photovoltaic" -> "PV_total.csv"[label="PV_totals"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather";
    "Zug.epw"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="databases/CH/systems";
    "supply_systems.xls"[style=filled, color=white]
    }
    subgraph cluster_2 {
        style = filled;
        color = peachpuff;
        label="inputs/building-geometry";
    "zone.shp"[style=filled, color=white]
    }
    subgraph cluster_3 {
        style = filled;
        color = peachpuff;
        label="outputs/data/potentials/solar";
    "{BUILDING}_PV_sensors.csv"[style=filled, color=white]
    "{BUILDING}_PV.csv"[style=filled, color=white]
    "PV_total_buildings.csv"[style=filled, color=white]
    "PV_total.csv"[style=filled, color=white]
    }
    subgraph cluster_4 {
        style = filled;
        color = peachpuff;
        label="outputs/data/solar-radiation";
    "{BUILDING}_insolation_Whm2.json"[style=filled, color=white]
    "{BUILDING}_geometry.csv"[style=filled, color=white]
    }
    }

sewage-potential
----------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "sewage-potential"[style=filled, fillcolor=darkorange];
    "{BUILDING}.csv" -> "sewage-potential"[label="get_demand_results_file"]
    "Total_demand.csv" -> "sewage-potential"[label="get_total_demand"]
    "sewage-potential" -> "SWP.csv"[label="get_sewage_heat_potential"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="outputs/data/demand";
    "{BUILDING}.csv"[style=filled, color=white]
    "Total_demand.csv"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="outputs/data/potentials";
    "SWP.csv"[style=filled, color=white]
    }
    }

radiation-daysim
----------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "radiation-daysim"[style=filled, fillcolor=darkorange];
    "architecture.dbf" -> "radiation-daysim"[label="get_building_architecture"]
    "district.shp" -> "radiation-daysim"[label="get_district_geometry"]
    "envelope_systems.xls" -> "radiation-daysim"[label="get_envelope_systems"]
    "terrain.tif" -> "radiation-daysim"[label="get_terrain"]
    "Zug.epw" -> "radiation-daysim"[label="get_weather"]
    "zone.shp" -> "radiation-daysim"[label="get_zone_geometry"]
    "radiation-daysim" -> "{BUILDING}_insolation_Whm2.json"[label="get_radiation_building"]
    "radiation-daysim" -> "{BUILDING}_geometry.csv"[label="get_radiation_metadata"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather";
    "Zug.epw"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="databases/CH/systems";
    "envelope_systems.xls"[style=filled, color=white]
    }
    subgraph cluster_2 {
        style = filled;
        color = peachpuff;
        label="inputs/building-geometry";
    "district.shp"[style=filled, color=white]
    "zone.shp"[style=filled, color=white]
    }
    subgraph cluster_3 {
        style = filled;
        color = peachpuff;
        label="inputs/building-properties";
    "architecture.dbf"[style=filled, color=white]
    }
    subgraph cluster_4 {
        style = filled;
        color = peachpuff;
        label="inputs/topography";
    "terrain.tif"[style=filled, color=white]
    }
    subgraph cluster_5 {
        style = filled;
        color = peachpuff;
        label="outputs/data/solar-radiation";
    "{BUILDING}_insolation_Whm2.json"[style=filled, color=white]
    "{BUILDING}_geometry.csv"[style=filled, color=white]
    }
    }

demand
------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "demand"[style=filled, fillcolor=darkorange];
    "construction_properties.xlsx" -> "demand"[label="get_archetypes_properties"]
    "occupancy_schedules.xlsx" -> "demand"[label="get_archetypes_schedules"]
    "system_controls.xlsx" -> "demand"[label="get_archetypes_system_controls"]
    "age.dbf" -> "demand"[label="get_building_age"]
    "architecture.dbf" -> "demand"[label="get_building_architecture"]
    "indoor_comfort.dbf" -> "demand"[label="get_building_comfort"]
    "technical_systems.dbf" -> "demand"[label="get_building_hvac"]
    "internal_loads.dbf" -> "demand"[label="get_building_internal"]
    "occupancy.dbf" -> "demand"[label="get_building_occupancy"]
    "supply_systems.dbf" -> "demand"[label="get_building_supply"]
    "envelope_systems.xls" -> "demand"[label="get_envelope_systems"]
    "LCA_infrastructure.xlsx" -> "demand"[label="get_life_cycle_inventory_supply_systems"]
    "{BUILDING}_insolation_Whm2.json" -> "demand"[label="get_radiation_building"]
    "{BUILDING}_geometry.csv" -> "demand"[label="get_radiation_metadata"]
    "emission_systems.xls" -> "demand"[label="get_technical_emission_systems"]
    "Zug.epw" -> "demand"[label="get_weather"]
    "zone.shp" -> "demand"[label="get_zone_geometry"]
    "demand" -> "{BUILDING}.csv"[label="get_demand_results_file"]
    "demand" -> "Total_demand.csv"[label="get_total_demand"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather";
    "Zug.epw"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="databases/CH/archetypes";
    "construction_properties.xlsx"[style=filled, color=white]
    "occupancy_schedules.xlsx"[style=filled, color=white]
    "system_controls.xlsx"[style=filled, color=white]
    }
    subgraph cluster_2 {
        style = filled;
        color = peachpuff;
        label="databases/CH/lifecycle";
    "LCA_infrastructure.xlsx"[style=filled, color=white]
    }
    subgraph cluster_3 {
        style = filled;
        color = peachpuff;
        label="databases/CH/systems";
    "envelope_systems.xls"[style=filled, color=white]
    "emission_systems.xls"[style=filled, color=white]
    }
    subgraph cluster_4 {
        style = filled;
        color = peachpuff;
        label="inputs/building-geometry";
    "zone.shp"[style=filled, color=white]
    }
    subgraph cluster_5 {
        style = filled;
        color = peachpuff;
        label="inputs/building-properties";
    "age.dbf"[style=filled, color=white]
    "architecture.dbf"[style=filled, color=white]
    "indoor_comfort.dbf"[style=filled, color=white]
    "technical_systems.dbf"[style=filled, color=white]
    "internal_loads.dbf"[style=filled, color=white]
    "occupancy.dbf"[style=filled, color=white]
    "supply_systems.dbf"[style=filled, color=white]
    }
    subgraph cluster_6 {
        style = filled;
        color = peachpuff;
        label="outputs/data/demand";
    "{BUILDING}.csv"[style=filled, color=white]
    "Total_demand.csv"[style=filled, color=white]
    }
    subgraph cluster_7 {
        style = filled;
        color = peachpuff;
        label="outputs/data/solar-radiation";
    "{BUILDING}_insolation_Whm2.json"[style=filled, color=white]
    "{BUILDING}_geometry.csv"[style=filled, color=white]
    }
    }

network-layout
--------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "network-layout"[style=filled, fillcolor=darkorange];
    "streets.shp" -> "network-layout"[label="get_street_network"]
    "zone.shp" -> "network-layout"[label="get_zone_geometry"]
    "Total_demand.csv" -> "network-layout"[label="get_total_demand"]

    subgraph cluster_0 {
    style = filled;
    color = peachpuff;
    label="inputs/networks/";
    "streets.shp"[style=filled, color=white]
    }

    subgraph cluster_1 {
    style = filled;
    color = peachpuff;
    label="inputs/building-geometry/";
    "zone.shp"[style=filled, color=white]
    }

    subgraph cluster_2 {
    style = filled;
    color = peachpuff;
    label="outputs/data/demand/";
    "Total_demand.csv"[style=filled, color=white]
    }
    }


emissions
---------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    node [shape=box];
    graph [overlap = false];
    "emissions"[style=filled, fillcolor=darkorange];
    "age.dbf" -> "emissions"[label="get_building_age"]
    "architecture.dbf" -> "emissions"[label="get_building_architecture"]
    "occupancy.dbf" -> "emissions"[label="get_building_occupancy"]
    "supply_systems.dbf" -> "emissions"[label="get_building_supply"]
    "benchmark_2000W.xls" -> "emissions"[label="get_data_benchmark"]
    "LCA_buildings.xlsx" -> "emissions"[label="get_life_cycle_inventory_building_systems"]
    "LCA_infrastructure.xlsx" -> "emissions"[label="get_life_cycle_inventory_supply_systems"]
    "Total_demand.csv" -> "emissions"[label="get_total_demand"]
    "zone.shp" -> "emissions"[label="get_zone_geometry"]
    "emissions" -> "Total_LCA_embodied.csv"[label="get_lca_embodied"]
    "emissions" -> "Total_LCA_mobility.csv"[label="get_lca_mobility"]
    "emissions" -> "Total_LCA_operation.csv"[label="get_lca_operation"]
    subgraph cluster_0 {
        style = filled;
        color = peachpuff;
        label="databases/CH/benchmarks";
    "benchmark_2000W.xls"[style=filled, color=white]
    }
    subgraph cluster_1 {
        style = filled;
        color = peachpuff;
        label="databases/CH/lifecycle";
    "LCA_buildings.xlsx"[style=filled, color=white]
    "LCA_infrastructure.xlsx"[style=filled, color=white]
    }
    subgraph cluster_2 {
        style = filled;
        color = peachpuff;
        label="inputs/building-geometry";
    "zone.shp"[style=filled, color=white]
    }
    subgraph cluster_3 {
        style = filled;
        color = peachpuff;
        label="inputs/building-properties";
    "age.dbf"[style=filled, color=white]
    "architecture.dbf"[style=filled, color=white]
    "occupancy.dbf"[style=filled, color=white]
    "supply_systems.dbf"[style=filled, color=white]
    }
    subgraph cluster_4 {
        style = filled;
        color = peachpuff;
        label="outputs/data/demand";
    "Total_demand.csv"[style=filled, color=white]
    }
    subgraph cluster_5 {
        style = filled;
        color = peachpuff;
        label="outputs/data/emissions";
    "Total_LCA_embodied.csv"[style=filled, color=white]
    "Total_LCA_mobility.csv"[style=filled, color=white]
    "Total_LCA_operation.csv"[style=filled, color=white]
    }
    }
