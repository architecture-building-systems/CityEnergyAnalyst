:orphan:

Script Data Flow
================
This section aims to clarify the files used (inputs) or created (outputs) by each script, along with the methods used
to access this data.

TO DO: run trace for all scripts.


sewage-potential
----------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
    "sewage-potential"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        "B001.csv"
        "Total_demand.csv"
    }
    subgraph cluster_10_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/potentials";
        "SWP.csv"
    }
    "construction_properties.xlsx" -> "sewage-potential"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "sewage-potential"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "sewage-potential"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "sewage-potential"[label="(get_building_age)"]
    "occupancy.dbf" -> "sewage-potential"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "sewage-potential"[label="(get_data_benchmark)"]
    "B001.csv" -> "sewage-potential"[label="(get_demand_results_file)"]
    "district.shp" -> "sewage-potential"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "sewage-potential"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "sewage-potential"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "sewage-potential"[label="(get_life_cycle_inventory_supply_systems)"]
    "streets.shp" -> "sewage-potential"[label="(get_street_network)"]
    "supply_systems.xls" -> "sewage-potential"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "sewage-potential"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "sewage-potential"[label="(get_terrain)"]
    "thermal_networks.xls" -> "sewage-potential"[label="(get_thermal_networks)"]
    "Total_demand.csv" -> "sewage-potential"[label="(get_total_demand)"]
    "Singapore.epw" -> "sewage-potential"[label="(get_weather)"]
    "zone.shp" -> "sewage-potential"[label="(get_zone_geometry)"]
    "sewage-potential" -> "SWP.csv"[label="(get_sewage_heat_potential)"]
    }

data-helper
-----------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "architecture.dbf"
        "indoor_comfort.dbf"
        "technical_systems.dbf"
        "internal_loads.dbf"
        "restrictions.dbf"
        "supply_systems.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    "construction_properties.xlsx" -> "data-helper"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "data-helper"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "data-helper"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "data-helper"[label="(get_building_age)"]
    "occupancy.dbf" -> "data-helper"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "data-helper"[label="(get_data_benchmark)"]
    "district.shp" -> "data-helper"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "data-helper"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "data-helper"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "data-helper"[label="(get_life_cycle_inventory_supply_systems)"]
    "streets.shp" -> "data-helper"[label="(get_street_network)"]
    "supply_systems.xls" -> "data-helper"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "data-helper"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "data-helper"[label="(get_terrain)"]
    "thermal_networks.xls" -> "data-helper"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "data-helper"[label="(get_weather)"]
    "zone.shp" -> "data-helper"[label="(get_zone_geometry)"]
    "data-helper" -> "architecture.dbf"[label="(get_building_architecture)"]
    "data-helper" -> "indoor_comfort.dbf"[label="(get_building_comfort)"]
    "data-helper" -> "technical_systems.dbf"[label="(get_building_hvac)"]
    "data-helper" -> "internal_loads.dbf"[label="(get_building_internal)"]
    "data-helper" -> "restrictions.dbf"[label="(get_building_restrictions)"]
    "data-helper" -> "supply_systems.dbf"[label="(get_building_supply)"]
    }

network-layout
--------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
    "network-layout"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/networks/DC";
        "edges.shp"
        "nodes.shp"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        "Total_demand.csv"
    }
    "construction_properties.xlsx" -> "network-layout"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "network-layout"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "network-layout"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "network-layout"[label="(get_building_age)"]
    "occupancy.dbf" -> "network-layout"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "network-layout"[label="(get_data_benchmark)"]
    "district.shp" -> "network-layout"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "network-layout"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "network-layout"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "network-layout"[label="(get_life_cycle_inventory_supply_systems)"]
    "streets.shp" -> "network-layout"[label="(get_street_network)"]
    "supply_systems.xls" -> "network-layout"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "network-layout"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "network-layout"[label="(get_terrain)"]
    "thermal_networks.xls" -> "network-layout"[label="(get_thermal_networks)"]
    "Total_demand.csv" -> "network-layout"[label="(get_total_demand)"]
    "Singapore.epw" -> "network-layout"[label="(get_weather)"]
    "zone.shp" -> "network-layout"[label="(get_zone_geometry)"]
    "network-layout" -> "edges.shp"[label="(get_network_layout_edges_shapefile)"]
    "network-layout" -> "nodes.shp"[label="(get_network_layout_nodes_shapefile)"]
    }

operation-costs
---------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
    "operation-costs"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
        "supply_systems.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/costs";
        "operation_costs.csv"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        "Total_demand.csv"
    }
    "construction_properties.xlsx" -> "operation-costs"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "operation-costs"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "operation-costs"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "operation-costs"[label="(get_building_age)"]
    "occupancy.dbf" -> "operation-costs"[label="(get_building_occupancy)"]
    "supply_systems.dbf" -> "operation-costs"[label="(get_building_supply)"]
    "benchmark_2000W.xls" -> "operation-costs"[label="(get_data_benchmark)"]
    "district.shp" -> "operation-costs"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "operation-costs"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "operation-costs"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "operation-costs"[label="(get_life_cycle_inventory_supply_systems)"]
    "streets.shp" -> "operation-costs"[label="(get_street_network)"]
    "supply_systems.xls" -> "operation-costs"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "operation-costs"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "operation-costs"[label="(get_terrain)"]
    "thermal_networks.xls" -> "operation-costs"[label="(get_thermal_networks)"]
    "Total_demand.csv" -> "operation-costs"[label="(get_total_demand)"]
    "Singapore.epw" -> "operation-costs"[label="(get_weather)"]
    "zone.shp" -> "operation-costs"[label="(get_zone_geometry)"]
    "operation-costs" -> "operation_costs.csv"[label="(get_costs_operation_file)"]
    }

solar-collector
---------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        "B001_SC_ET_sensors.csv"
        "B001_SC_ET.csv"
        "SC_ET_total_buildings.csv"
        "SC_ET_total.csv"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    "construction_properties.xlsx" -> "solar-collector"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "solar-collector"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "solar-collector"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "solar-collector"[label="(get_building_age)"]
    "occupancy.dbf" -> "solar-collector"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "solar-collector"[label="(get_data_benchmark)"]
    "district.shp" -> "solar-collector"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "solar-collector"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "solar-collector"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "solar-collector"[label="(get_life_cycle_inventory_supply_systems)"]
    "B001_insolation_Whm2.json" -> "solar-collector"[label="(get_radiation_building)"]
    "B001_geometry.csv" -> "solar-collector"[label="(get_radiation_metadata)"]
    "streets.shp" -> "solar-collector"[label="(get_street_network)"]
    "supply_systems.xls" -> "solar-collector"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "solar-collector"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "solar-collector"[label="(get_terrain)"]
    "thermal_networks.xls" -> "solar-collector"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "solar-collector"[label="(get_weather)"]
    "zone.shp" -> "solar-collector"[label="(get_zone_geometry)"]
    "solar-collector" -> "B001_SC_ET_sensors.csv"[label="(SC_metadata_results)"]
    "solar-collector" -> "B001_SC_ET.csv"[label="(SC_results)"]
    "solar-collector" -> "SC_ET_total_buildings.csv"[label="(SC_total_buildings)"]
    "solar-collector" -> "SC_ET_total.csv"[label="(SC_totals)"]
    }

lake-potential
--------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
    "lake-potential"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/potentials";
        "Lake_potential.csv"
    }
    "construction_properties.xlsx" -> "lake-potential"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "lake-potential"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "lake-potential"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "lake-potential"[label="(get_building_age)"]
    "occupancy.dbf" -> "lake-potential"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "lake-potential"[label="(get_data_benchmark)"]
    "district.shp" -> "lake-potential"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "lake-potential"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "lake-potential"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "lake-potential"[label="(get_life_cycle_inventory_supply_systems)"]
    "streets.shp" -> "lake-potential"[label="(get_street_network)"]
    "supply_systems.xls" -> "lake-potential"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "lake-potential"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "lake-potential"[label="(get_terrain)"]
    "thermal_networks.xls" -> "lake-potential"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "lake-potential"[label="(get_weather)"]
    "zone.shp" -> "lake-potential"[label="(get_zone_geometry)"]
    "lake-potential" -> "Lake_potential.csv"[label="(get_lake_potential)"]
    }

thermal-network
---------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
    "thermal-network"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/networks/DC";
        "nodes.shp"
    }
    subgraph cluster_9_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/networks/DC";
        "edges.shp"
    }
    subgraph cluster_10_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="optimization/network/layout";
        "Nominal_EdgeMassFlow_at_design_DH__kgpers.csv"
        "DH__Nodes.csv"
        "Nominal_NodeMassFlow_at_design_DH__kgpers.csv"
        "DH__Edges.csv"
        "DH__EdgeNode.csv"
        "DH__MassFlow_kgs.csv"
        "DH__Plant_heat_requirement_kW.csv"
        "DH__ploss_System_edges_kW.csv"
        "DH__P_DeltaP_Pa.csv"
        "DH__qloss_System_kW.csv"
        "DH__T_Return_K.csv"
        "DH__T_Supply_K.csv"
        "DH__Nodes.csv"
        "DH__ploss_Substations_kW.csv"
        "Aggregated_Demand_DH__Wh.csv"
    }
    subgraph cluster_11_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        "B001.csv"
    }
    "construction_properties.xlsx" -> "thermal-network"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "thermal-network"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "thermal-network"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "thermal-network"[label="(get_building_age)"]
    "occupancy.dbf" -> "thermal-network"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "thermal-network"[label="(get_data_benchmark)"]
    "B001.csv" -> "thermal-network"[label="(get_demand_results_file)"]
    "district.shp" -> "thermal-network"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "thermal-network"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "thermal-network"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "thermal-network"[label="(get_life_cycle_inventory_supply_systems)"]
    "nodes.shp" -> "thermal-network"[label="(get_network_layout_nodes_shapefile)"]
    "streets.shp" -> "thermal-network"[label="(get_street_network)"]
    "supply_systems.xls" -> "thermal-network"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "thermal-network"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "thermal-network"[label="(get_terrain)"]
    "thermal_networks.xls" -> "thermal-network"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "thermal-network"[label="(get_weather)"]
    "zone.shp" -> "thermal-network"[label="(get_zone_geometry)"]
    "thermal-network" -> "Nominal_EdgeMassFlow_at_design_DH__kgpers.csv"[label="(get_edge_mass_flow_csv_file)"]
    "thermal-network" -> "edges.shp"[label="(get_network_layout_edges_shapefile)"]
    "thermal-network" -> "DH__Nodes.csv"[label="(get_network_node_types_csv_file)"]
    "thermal-network" -> "Nominal_NodeMassFlow_at_design_DH__kgpers.csv"[label="(get_node_mass_flow_csv_file)"]
    "thermal-network" -> "DH__Edges.csv"[label="(get_optimization_network_edge_list_file)"]
    "thermal-network" -> "DH__EdgeNode.csv"[label="(get_optimization_network_edge_node_matrix_file)"]
    "thermal-network" -> "DH__MassFlow_kgs.csv"[label="(get_optimization_network_layout_massflow_file)"]
    "thermal-network" -> "DH__Plant_heat_requirement_kW.csv"[label="(get_optimization_network_layout_plant_heat_requirement_file)"]
    "thermal-network" -> "DH__ploss_System_edges_kW.csv"[label="(get_optimization_network_layout_ploss_system_edges_file)"]
    "thermal-network" -> "DH__P_DeltaP_Pa.csv"[label="(get_optimization_network_layout_pressure_drop_file)"]
    "thermal-network" -> "DH__qloss_System_kW.csv"[label="(get_optimization_network_layout_qloss_system_file)"]
    "thermal-network" -> "DH__T_Return_K.csv"[label="(get_optimization_network_layout_return_temperature_file)"]
    "thermal-network" -> "DH__T_Supply_K.csv"[label="(get_optimization_network_layout_supply_temperature_file)"]
    "thermal-network" -> "DH__Nodes.csv"[label="(get_optimization_network_node_list_file)"]
    "thermal-network" -> "DH__ploss_Substations_kW.csv"[label="(get_optimization_network_substation_ploss_file)"]
    "thermal-network" -> "Aggregated_Demand_DH__Wh.csv"[label="(get_thermal_demand_csv_file)"]
    }

photovoltaic-thermal
--------------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        "B001_PVT_sensors.csv"
        "B001_PVT.csv"
        "PVT_total_buildings.csv"
        "PVT_total.csv"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    "construction_properties.xlsx" -> "photovoltaic-thermal"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "photovoltaic-thermal"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "photovoltaic-thermal"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "photovoltaic-thermal"[label="(get_building_age)"]
    "occupancy.dbf" -> "photovoltaic-thermal"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "photovoltaic-thermal"[label="(get_data_benchmark)"]
    "district.shp" -> "photovoltaic-thermal"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "photovoltaic-thermal"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "photovoltaic-thermal"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "photovoltaic-thermal"[label="(get_life_cycle_inventory_supply_systems)"]
    "B001_insolation_Whm2.json" -> "photovoltaic-thermal"[label="(get_radiation_building)"]
    "B001_geometry.csv" -> "photovoltaic-thermal"[label="(get_radiation_metadata)"]
    "streets.shp" -> "photovoltaic-thermal"[label="(get_street_network)"]
    "supply_systems.xls" -> "photovoltaic-thermal"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "photovoltaic-thermal"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "photovoltaic-thermal"[label="(get_terrain)"]
    "thermal_networks.xls" -> "photovoltaic-thermal"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "photovoltaic-thermal"[label="(get_weather)"]
    "zone.shp" -> "photovoltaic-thermal"[label="(get_zone_geometry)"]
    "photovoltaic-thermal" -> "B001_PVT_sensors.csv"[label="(PVT_metadata_results)"]
    "photovoltaic-thermal" -> "B001_PVT.csv"[label="(PVT_results)"]
    "photovoltaic-thermal" -> "PVT_total_buildings.csv"[label="(PVT_total_buildings)"]
    "photovoltaic-thermal" -> "PVT_total.csv"[label="(PVT_totals)"]
    }

emissions
---------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "architecture.dbf"
        "occupancy.dbf"
        "supply_systems.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        "Total_demand.csv"
    }
    subgraph cluster_10_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/emissions";
        "Total_LCA_embodied.csv"
        "Total_LCA_mobility.csv"
        "Total_LCA_operation.csv"
    }
    "construction_properties.xlsx" -> "emissions"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "emissions"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "emissions"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "emissions"[label="(get_building_age)"]
    "architecture.dbf" -> "emissions"[label="(get_building_architecture)"]
    "occupancy.dbf" -> "emissions"[label="(get_building_occupancy)"]
    "supply_systems.dbf" -> "emissions"[label="(get_building_supply)"]
    "benchmark_2000W.xls" -> "emissions"[label="(get_data_benchmark)"]
    "district.shp" -> "emissions"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "emissions"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "emissions"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "emissions"[label="(get_life_cycle_inventory_supply_systems)"]
    "streets.shp" -> "emissions"[label="(get_street_network)"]
    "supply_systems.xls" -> "emissions"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "emissions"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "emissions"[label="(get_terrain)"]
    "thermal_networks.xls" -> "emissions"[label="(get_thermal_networks)"]
    "Total_demand.csv" -> "emissions"[label="(get_total_demand)"]
    "Singapore.epw" -> "emissions"[label="(get_weather)"]
    "zone.shp" -> "emissions"[label="(get_zone_geometry)"]
    "emissions" -> "Total_LCA_embodied.csv"[label="(get_lca_embodied)"]
    "emissions" -> "Total_LCA_mobility.csv"[label="(get_lca_mobility)"]
    "emissions" -> "Total_LCA_operation.csv"[label="(get_lca_operation)"]
    }

demand
------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "architecture.dbf"
        "indoor_comfort.dbf"
        "technical_systems.dbf"
        "internal_loads.dbf"
        "occupancy.dbf"
        "supply_systems.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        "B001.csv"
        "Total_demand.csv"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
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
    "benchmark_2000W.xls" -> "demand"[label="(get_data_benchmark)"]
    "district.shp" -> "demand"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "demand"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "demand"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "demand"[label="(get_life_cycle_inventory_supply_systems)"]
    "B001_insolation_Whm2.json" -> "demand"[label="(get_radiation_building)"]
    "B001_geometry.csv" -> "demand"[label="(get_radiation_metadata)"]
    "streets.shp" -> "demand"[label="(get_street_network)"]
    "supply_systems.xls" -> "demand"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "demand"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "demand"[label="(get_terrain)"]
    "thermal_networks.xls" -> "demand"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "demand"[label="(get_weather)"]
    "zone.shp" -> "demand"[label="(get_zone_geometry)"]
    "demand" -> "B001.csv"[label="(get_demand_results_file)"]
    "demand" -> "Total_demand.csv"[label="(get_total_demand)"]
    }

radiation-daysim
----------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "architecture.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_9_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    "construction_properties.xlsx" -> "radiation-daysim"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "radiation-daysim"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "radiation-daysim"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "radiation-daysim"[label="(get_building_age)"]
    "architecture.dbf" -> "radiation-daysim"[label="(get_building_architecture)"]
    "occupancy.dbf" -> "radiation-daysim"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "radiation-daysim"[label="(get_data_benchmark)"]
    "district.shp" -> "radiation-daysim"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "radiation-daysim"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "radiation-daysim"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "radiation-daysim"[label="(get_life_cycle_inventory_supply_systems)"]
    "streets.shp" -> "radiation-daysim"[label="(get_street_network)"]
    "supply_systems.xls" -> "radiation-daysim"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "radiation-daysim"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "radiation-daysim"[label="(get_terrain)"]
    "thermal_networks.xls" -> "radiation-daysim"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "radiation-daysim"[label="(get_weather)"]
    "zone.shp" -> "radiation-daysim"[label="(get_zone_geometry)"]
    "radiation-daysim" -> "B001_insolation_Whm2.json"[label="(get_radiation_building)"]
    "radiation-daysim" -> "B001_geometry.csv"[label="(get_radiation_metadata)"]
    }

photovoltaic
------------
.. graphviz::

    digraph trace_inputlocator {
    rankdir="LR";
    graph [overlap=false, fontname=arial];
    node [shape=box, style=filled, color=white, fontsize=15, fontname=arial, fixedsize=true, width=5];
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
        label="WTP_CBD_h/inputs/building-geometry";
        "district.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/building-properties";
        "age.dbf"
        "occupancy.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="WTP_CBD_h/inputs/topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="cea/databases/weather";
        "Singapore.epw"
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        "B001_PV_sensors.csv"
        "B001_PV.csv"
        "PV_total_buildings.csv"
        "PV_total.csv"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/archetypes";
        "construction_properties.xlsx"
        "occupancy_schedules.xlsx"
        "system_controls.xlsx"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/CH/systems";
        "envelope_systems.xls"
        "supply_systems.xls"
        "emission_systems.xls"
        "thermal_networks.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/benchmarks";
        "benchmark_2000W.xls"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="databases/SG/lifecycle";
        "LCA_buildings.xlsx"
        "LCA_infrastructure.xlsx"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    "construction_properties.xlsx" -> "photovoltaic"[label="(get_archetypes_properties)"]
    "occupancy_schedules.xlsx" -> "photovoltaic"[label="(get_archetypes_schedules)"]
    "system_controls.xlsx" -> "photovoltaic"[label="(get_archetypes_system_controls)"]
    "age.dbf" -> "photovoltaic"[label="(get_building_age)"]
    "occupancy.dbf" -> "photovoltaic"[label="(get_building_occupancy)"]
    "benchmark_2000W.xls" -> "photovoltaic"[label="(get_data_benchmark)"]
    "district.shp" -> "photovoltaic"[label="(get_district_geometry)"]
    "envelope_systems.xls" -> "photovoltaic"[label="(get_envelope_systems)"]
    "LCA_buildings.xlsx" -> "photovoltaic"[label="(get_life_cycle_inventory_building_systems)"]
    "LCA_infrastructure.xlsx" -> "photovoltaic"[label="(get_life_cycle_inventory_supply_systems)"]
    "B001_insolation_Whm2.json" -> "photovoltaic"[label="(get_radiation_building)"]
    "B001_geometry.csv" -> "photovoltaic"[label="(get_radiation_metadata)"]
    "streets.shp" -> "photovoltaic"[label="(get_street_network)"]
    "supply_systems.xls" -> "photovoltaic"[label="(get_supply_systems)"]
    "emission_systems.xls" -> "photovoltaic"[label="(get_technical_emission_systems)"]
    "terrain.tif" -> "photovoltaic"[label="(get_terrain)"]
    "thermal_networks.xls" -> "photovoltaic"[label="(get_thermal_networks)"]
    "Singapore.epw" -> "photovoltaic"[label="(get_weather)"]
    "zone.shp" -> "photovoltaic"[label="(get_zone_geometry)"]
    "photovoltaic" -> "B001_PV_sensors.csv"[label="(PV_metadata_results)"]
    "photovoltaic" -> "B001_PV.csv"[label="(PV_results)"]
    "photovoltaic" -> "PV_total_buildings.csv"[label="(PV_total_buildings)"]
    "photovoltaic" -> "PV_total.csv"[label="(PV_totals)"]
    }
