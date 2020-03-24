:orphan:

Script Data Flow
================
This section aims to clarify the files used (inputs) or created (outputs) by each script, along with the methods used
to access this data.

TO DO: run trace for all scripts.


multi_criteria_analysis
-----------------------
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
    "multi_criteria_analysis"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/multicriteria";
        "gen_2_multi_criteria_analysis.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="optimization/slave/gen_2";
        "gen_2_total_performance_pareto.csv"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "gen_2_total_performance_pareto.csv" -> "multi_criteria_analysis"[label="(get_optimization_generation_total_performance_pareto)"]
    "DH_Network_summary_result_0x19b.csv" -> "multi_criteria_analysis"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "multi_criteria_analysis"[label="(get_site_polygon)"]
    "streets.shp" -> "multi_criteria_analysis"[label="(get_street_network)"]
    "surroundings.shp" -> "multi_criteria_analysis"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "multi_criteria_analysis"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "multi_criteria_analysis"[label="(get_weather)"]
    "zone.shp" -> "multi_criteria_analysis"[label="(get_zone_geometry)"]
    "multi_criteria_analysis" -> "gen_2_multi_criteria_analysis.csv"[label="(get_multi_criteria_analysis)"]
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
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_out {
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
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/solar-radiation";
        "{building}_radiation.csv"
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "CONVERSION.xls"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "CONVERSION.xls" -> "photovoltaic"[label="(get_database_conversion_systems)"]
    "DH_Network_summary_result_0x19b.csv" -> "photovoltaic"[label="(get_optimization_thermal_network_data_file)"]
    "{building}_radiation.csv" -> "photovoltaic"[label="(get_radiation_building)"]
    "B001_insolation_Whm2.json" -> "photovoltaic"[label="(get_radiation_building_sensors)"]
    "B001_geometry.csv" -> "photovoltaic"[label="(get_radiation_metadata)"]
    "site.shp" -> "photovoltaic"[label="(get_site_polygon)"]
    "streets.shp" -> "photovoltaic"[label="(get_street_network)"]
    "surroundings.shp" -> "photovoltaic"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "photovoltaic"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "photovoltaic"[label="(get_weather)"]
    "weather.epw" -> "photovoltaic"[label="(get_weather_file)"]
    "zone.shp" -> "photovoltaic"[label="(get_zone_geometry)"]
    "photovoltaic" -> "B001_PV_sensors.csv"[label="(PV_metadata_results)"]
    "photovoltaic" -> "B001_PV.csv"[label="(PV_results)"]
    "photovoltaic" -> "PV_total_buildings.csv"[label="(PV_total_buildings)"]
    "photovoltaic" -> "PV_total.csv"[label="(PV_totals)"]
    }

decentralized
-------------
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
    "decentralized"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "supply_systems.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "B001.csv"
        "Total_demand.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/decentralized";
        "{building}_{configuration}_cooling_activation.csv"
        "DiscOp_B001_result_heating.csv"
        "DiscOp_B001_result_heating_activation.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        "110011011DH_B001_result.csv"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        "B001_SC_ET.csv"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "CONVERSION.xls"
        "FEEDSTOCKS.xls"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "B001_SC_ET.csv" -> "decentralized"[label="(SC_results)"]
    "supply_systems.dbf" -> "decentralized"[label="(get_building_supply)"]
    "CONVERSION.xls" -> "decentralized"[label="(get_database_conversion_systems)"]
    "FEEDSTOCKS.xls" -> "decentralized"[label="(get_database_feedstocks)"]
    "B001.csv" -> "decentralized"[label="(get_demand_results_file)"]
    "DH_Network_summary_result_0x19b.csv" -> "decentralized"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "decentralized"[label="(get_site_polygon)"]
    "streets.shp" -> "decentralized"[label="(get_street_network)"]
    "surroundings.shp" -> "decentralized"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "decentralized"[label="(get_terrain)"]
    "Total_demand.csv" -> "decentralized"[label="(get_total_demand)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "decentralized"[label="(get_weather)"]
    "weather.epw" -> "decentralized"[label="(get_weather_file)"]
    "zone.shp" -> "decentralized"[label="(get_zone_geometry)"]
    "decentralized" -> "{building}_{configuration}_cooling_activation.csv"[label="(get_optimization_decentralized_folder_building_cooling_activation)"]
    "decentralized" -> "DiscOp_B001_result_heating.csv"[label="(get_optimization_decentralized_folder_building_result_heating)"]
    "decentralized" -> "DiscOp_B001_result_heating_activation.csv"[label="(get_optimization_decentralized_folder_building_result_heating_activation)"]
    "decentralized" -> "110011011DH_B001_result.csv"[label="(get_optimization_substations_results_file)"]
    }

radiation
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
    "radiation"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "architecture.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/solar-radiation";
        "{building}_radiation.csv"
        "B001_insolation_Whm2.json"
        "buidling_materials.csv"
        "B001_geometry.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/assemblies";
        "ENVELOPE.xls"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "architecture.dbf" -> "radiation"[label="(get_building_architecture)"]
    "ENVELOPE.xls" -> "radiation"[label="(get_database_envelope_systems)"]
    "DH_Network_summary_result_0x19b.csv" -> "radiation"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "radiation"[label="(get_site_polygon)"]
    "streets.shp" -> "radiation"[label="(get_street_network)"]
    "surroundings.shp" -> "radiation"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "radiation"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "radiation"[label="(get_weather)"]
    "weather.epw" -> "radiation"[label="(get_weather_file)"]
    "zone.shp" -> "radiation"[label="(get_zone_geometry)"]
    "radiation" -> "{building}_radiation.csv"[label="(get_radiation_building)"]
    "radiation" -> "B001_insolation_Whm2.json"[label="(get_radiation_building_sensors)"]
    "radiation" -> "buidling_materials.csv"[label="(get_radiation_materials)"]
    "radiation" -> "B001_geometry.csv"[label="(get_radiation_metadata)"]
    }

zone_helper
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
    "zone_helper"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "zone_helper"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "zone_helper"[label="(get_site_polygon)"]
    "streets.shp" -> "zone_helper"[label="(get_street_network)"]
    "surroundings.shp" -> "zone_helper"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "zone_helper"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "zone_helper"[label="(get_weather)"]
    "zone.shp" -> "zone_helper"[label="(get_zone_geometry)"]
    }

archetypes_mapper
-----------------
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
    "archetypes_mapper"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "typology.dbf"
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "air_conditioning_systems.dbf"
        "architecture.dbf"
        "indoor_comfort.dbf"
        "internal_loads.dbf"
        "supply_systems.dbf"
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="building-properties/schedules";
        "B001.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/archetypes";
        "CONSTRUCTION_STANDARDS.xlsx"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/schedules";
        "{use}.csv"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/use_types";
        "USE_TYPE_PROPERTIES.xlsx"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "typology.dbf" -> "archetypes_mapper"[label="(get_building_typology)"]
    "CONSTRUCTION_STANDARDS.xlsx" -> "archetypes_mapper"[label="(get_database_construction_standards)"]
    "{use}.csv" -> "archetypes_mapper"[label="(get_database_standard_schedules_use)"]
    "USE_TYPE_PROPERTIES.xlsx" -> "archetypes_mapper"[label="(get_database_use_types_properties)"]
    "DH_Network_summary_result_0x19b.csv" -> "archetypes_mapper"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "archetypes_mapper"[label="(get_site_polygon)"]
    "streets.shp" -> "archetypes_mapper"[label="(get_street_network)"]
    "surroundings.shp" -> "archetypes_mapper"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "archetypes_mapper"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "archetypes_mapper"[label="(get_weather)"]
    "zone.shp" -> "archetypes_mapper"[label="(get_zone_geometry)"]
    "archetypes_mapper" -> "air_conditioning_systems.dbf"[label="(get_building_air_conditioning)"]
    "archetypes_mapper" -> "architecture.dbf"[label="(get_building_architecture)"]
    "archetypes_mapper" -> "indoor_comfort.dbf"[label="(get_building_comfort)"]
    "archetypes_mapper" -> "internal_loads.dbf"[label="(get_building_internal)"]
    "archetypes_mapper" -> "supply_systems.dbf"[label="(get_building_supply)"]
    "archetypes_mapper" -> "B001.csv"[label="(get_building_weekly_schedules)"]
    }

sewage_potential
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
    "sewage_potential"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "B001.csv"
        "Total_demand.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials";
        "Sewage_heat_potential.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "B001.csv" -> "sewage_potential"[label="(get_demand_results_file)"]
    "DH_Network_summary_result_0x19b.csv" -> "sewage_potential"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "sewage_potential"[label="(get_site_polygon)"]
    "streets.shp" -> "sewage_potential"[label="(get_street_network)"]
    "surroundings.shp" -> "sewage_potential"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "sewage_potential"[label="(get_terrain)"]
    "Total_demand.csv" -> "sewage_potential"[label="(get_total_demand)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "sewage_potential"[label="(get_weather)"]
    "zone.shp" -> "sewage_potential"[label="(get_zone_geometry)"]
    "sewage_potential" -> "Sewage_heat_potential.csv"[label="(get_sewage_heat_potential)"]
    }

photovoltaic_thermal
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
    "photovoltaic_thermal"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_out {
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
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/solar-radiation";
        "{building}_radiation.csv"
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "CONVERSION.xls"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "CONVERSION.xls" -> "photovoltaic_thermal"[label="(get_database_conversion_systems)"]
    "DH_Network_summary_result_0x19b.csv" -> "photovoltaic_thermal"[label="(get_optimization_thermal_network_data_file)"]
    "{building}_radiation.csv" -> "photovoltaic_thermal"[label="(get_radiation_building)"]
    "B001_insolation_Whm2.json" -> "photovoltaic_thermal"[label="(get_radiation_building_sensors)"]
    "B001_geometry.csv" -> "photovoltaic_thermal"[label="(get_radiation_metadata)"]
    "site.shp" -> "photovoltaic_thermal"[label="(get_site_polygon)"]
    "streets.shp" -> "photovoltaic_thermal"[label="(get_street_network)"]
    "surroundings.shp" -> "photovoltaic_thermal"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "photovoltaic_thermal"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "photovoltaic_thermal"[label="(get_weather)"]
    "weather.epw" -> "photovoltaic_thermal"[label="(get_weather_file)"]
    "zone.shp" -> "photovoltaic_thermal"[label="(get_zone_geometry)"]
    "photovoltaic_thermal" -> "B001_PVT_sensors.csv"[label="(PVT_metadata_results)"]
    "photovoltaic_thermal" -> "B001_PVT.csv"[label="(PVT_results)"]
    "photovoltaic_thermal" -> "PVT_total_buildings.csv"[label="(PVT_total_buildings)"]
    "photovoltaic_thermal" -> "PVT_total.csv"[label="(PVT_totals)"]
    }

solar_collector
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
    "solar_collector"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        "B001_SC_ET_sensors.csv"
        "B001_SC_ET.csv"
        "SC_ET_total_buildings.csv"
        "SC_FP_total.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/solar-radiation";
        "{building}_radiation.csv"
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "CONVERSION.xls"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "CONVERSION.xls" -> "solar_collector"[label="(get_database_conversion_systems)"]
    "DH_Network_summary_result_0x19b.csv" -> "solar_collector"[label="(get_optimization_thermal_network_data_file)"]
    "{building}_radiation.csv" -> "solar_collector"[label="(get_radiation_building)"]
    "B001_insolation_Whm2.json" -> "solar_collector"[label="(get_radiation_building_sensors)"]
    "B001_geometry.csv" -> "solar_collector"[label="(get_radiation_metadata)"]
    "site.shp" -> "solar_collector"[label="(get_site_polygon)"]
    "streets.shp" -> "solar_collector"[label="(get_street_network)"]
    "surroundings.shp" -> "solar_collector"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "solar_collector"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "solar_collector"[label="(get_weather)"]
    "weather.epw" -> "solar_collector"[label="(get_weather_file)"]
    "zone.shp" -> "solar_collector"[label="(get_zone_geometry)"]
    "solar_collector" -> "B001_SC_ET_sensors.csv"[label="(SC_metadata_results)"]
    "solar_collector" -> "B001_SC_ET.csv"[label="(SC_results)"]
    "solar_collector" -> "SC_ET_total_buildings.csv"[label="(SC_total_buildings)"]
    "solar_collector" -> "SC_FP_total.csv"[label="(SC_totals)"]
    }

water_body_potential
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
    "water_body_potential"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials";
        "Water_body_potential.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "water_body_potential"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "water_body_potential"[label="(get_site_polygon)"]
    "streets.shp" -> "water_body_potential"[label="(get_street_network)"]
    "surroundings.shp" -> "water_body_potential"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "water_body_potential"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "water_body_potential"[label="(get_weather)"]
    "zone.shp" -> "water_body_potential"[label="(get_zone_geometry)"]
    "water_body_potential" -> "Water_body_potential.csv"[label="(get_water_body_potential)"]
    }

decentrlized
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
    "decentrlized"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/decentralized";
        "{building}_{configuration}_cooling.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "decentrlized"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "decentrlized"[label="(get_site_polygon)"]
    "streets.shp" -> "decentrlized"[label="(get_street_network)"]
    "surroundings.shp" -> "decentrlized"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "decentrlized"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "decentrlized"[label="(get_weather)"]
    "zone.shp" -> "decentrlized"[label="(get_zone_geometry)"]
    "decentrlized" -> "{building}_{configuration}_cooling.csv"[label="(get_optimization_decentralized_folder_building_result_cooling)"]
    }

database-migrator
-----------------
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
    "database-migrator"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "typology.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "database-migrator"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "database-migrator"[label="(get_site_polygon)"]
    "streets.shp" -> "database-migrator"[label="(get_street_network)"]
    "surroundings.shp" -> "database-migrator"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "database-migrator"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "database-migrator"[label="(get_weather)"]
    "zone.shp" -> "database-migrator"[label="(get_zone_geometry)"]
    "database-migrator" -> "typology.dbf"[label="(get_building_typology)"]
    }

thermal_network
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
    "thermal_network"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "B001.csv"
        "Total_demand.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        "110011011DH_B001_result.csv"
        "Total_DH_111111111.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/thermal-network";
        "Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv"
        "Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv"
        "{network_type}__EdgeNode.csv"
    }
    subgraph cluster_4_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/thermal-network";
        "DH__plant_pumping_load_kW.csv"
        "DH__linear_pressure_drop_edges_Paperm.csv"
        "DH__linear_thermal_loss_edges_Wperm.csv"
        "DH__pressure_at_nodes_Pa.csv"
        "DH__temperature_plant_K.csv"
        "DH__temperature_return_nodes_K.csv"
        "DH__temperature_supply_nodes_K.csv"
        "DH__thermal_loss_edges_kW.csv"
        "DH__plant_pumping_pressure_loss_Pa.csv"
        "DH__total_thermal_loss_edges_kW.csv"
        "Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv"
        "Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv"
        "DH__thermal_demand_per_building_W.csv"
        "DH__metadata_edges.csv"
        "{network_type}__EdgeNode.csv"
        "DH__massflow_edges_kgs.csv"
        "DH__massflow_nodes_kgs.csv"
        "DH__metadata_nodes.csv"
        "DH__plant_thermal_load_kW.csv"
        "DH__pressure_losses_edges_kW.csv"
        "DH__pumping_load_due_to_substations_kW.csv"
        "DH__velocity_edges_mpers.csv"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/thermal-network/DH";
        "edges.shp"
        "nodes.shp"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "DISTRIBUTION.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "DISTRIBUTION.xls" -> "thermal_network"[label="(get_database_distribution_systems)"]
    "B001.csv" -> "thermal_network"[label="(get_demand_results_file)"]
    "edges.shp" -> "thermal_network"[label="(get_network_layout_edges_shapefile)"]
    "nodes.shp" -> "thermal_network"[label="(get_network_layout_nodes_shapefile)"]
    "Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv" -> "thermal_network"[label="(get_nominal_edge_mass_flow_csv_file)"]
    "Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv" -> "thermal_network"[label="(get_nominal_node_mass_flow_csv_file)"]
    "DH_Network_summary_result_0x19b.csv" -> "thermal_network"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "thermal_network"[label="(get_site_polygon)"]
    "streets.shp" -> "thermal_network"[label="(get_street_network)"]
    "surroundings.shp" -> "thermal_network"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "thermal_network"[label="(get_terrain)"]
    "{network_type}__EdgeNode.csv" -> "thermal_network"[label="(get_thermal_network_edge_node_matrix_file)"]
    "Total_demand.csv" -> "thermal_network"[label="(get_total_demand)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "thermal_network"[label="(get_weather)"]
    "weather.epw" -> "thermal_network"[label="(get_weather_file)"]
    "zone.shp" -> "thermal_network"[label="(get_zone_geometry)"]
    "thermal_network" -> "DH__plant_pumping_load_kW.csv"[label="(get_network_energy_pumping_requirements_file)"]
    "thermal_network" -> "DH__linear_pressure_drop_edges_Paperm.csv"[label="(get_network_linear_pressure_drop_edges)"]
    "thermal_network" -> "DH__linear_thermal_loss_edges_Wperm.csv"[label="(get_network_linear_thermal_loss_edges_file)"]
    "thermal_network" -> "DH__pressure_at_nodes_Pa.csv"[label="(get_network_pressure_at_nodes)"]
    "thermal_network" -> "DH__temperature_plant_K.csv"[label="(get_network_temperature_plant)"]
    "thermal_network" -> "DH__temperature_return_nodes_K.csv"[label="(get_network_temperature_return_nodes_file)"]
    "thermal_network" -> "DH__temperature_supply_nodes_K.csv"[label="(get_network_temperature_supply_nodes_file)"]
    "thermal_network" -> "DH__thermal_loss_edges_kW.csv"[label="(get_network_thermal_loss_edges_file)"]
    "thermal_network" -> "DH__plant_pumping_pressure_loss_Pa.csv"[label="(get_network_total_pressure_drop_file)"]
    "thermal_network" -> "DH__total_thermal_loss_edges_kW.csv"[label="(get_network_total_thermal_loss_file)"]
    "thermal_network" -> "Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv"[label="(get_nominal_edge_mass_flow_csv_file)"]
    "thermal_network" -> "Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv"[label="(get_nominal_node_mass_flow_csv_file)"]
    "thermal_network" -> "110011011DH_B001_result.csv"[label="(get_optimization_substations_results_file)"]
    "thermal_network" -> "Total_DH_111111111.csv"[label="(get_optimization_substations_total_file)"]
    "thermal_network" -> "DH__thermal_demand_per_building_W.csv"[label="(get_thermal_demand_csv_file)"]
    "thermal_network" -> "DH__metadata_edges.csv"[label="(get_thermal_network_edge_list_file)"]
    "thermal_network" -> "{network_type}__EdgeNode.csv"[label="(get_thermal_network_edge_node_matrix_file)"]
    "thermal_network" -> "DH__massflow_edges_kgs.csv"[label="(get_thermal_network_layout_massflow_edges_file)"]
    "thermal_network" -> "DH__massflow_nodes_kgs.csv"[label="(get_thermal_network_layout_massflow_nodes_file)"]
    "thermal_network" -> "DH__metadata_nodes.csv"[label="(get_thermal_network_node_types_csv_file)"]
    "thermal_network" -> "DH__plant_thermal_load_kW.csv"[label="(get_thermal_network_plant_heat_requirement_file)"]
    "thermal_network" -> "DH__pressure_losses_edges_kW.csv"[label="(get_thermal_network_pressure_losses_edges_file)"]
    "thermal_network" -> "DH__pumping_load_due_to_substations_kW.csv"[label="(get_thermal_network_substation_ploss_file)"]
    "thermal_network" -> "DH__velocity_edges_mpers.csv"[label="(get_thermal_network_velocity_edges_file)"]
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
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "air_conditioning_systems.dbf"
        "architecture.dbf"
        "indoor_comfort.dbf"
        "internal_loads.dbf"
        "supply_systems.dbf"
        "typology.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties/schedules";
        "B001.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "B001.csv"
        "Total_demand.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/occupancy";
        "B001.csv"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/solar-radiation";
        "{building}_radiation.csv"
        "B001_insolation_Whm2.json"
        "B001_geometry.csv"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/assemblies";
        "HVAC.xls"
        "ENVELOPE.xls"
        "SUPPLY.xls"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_10_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "air_conditioning_systems.dbf" -> "demand"[label="(get_building_air_conditioning)"]
    "architecture.dbf" -> "demand"[label="(get_building_architecture)"]
    "indoor_comfort.dbf" -> "demand"[label="(get_building_comfort)"]
    "internal_loads.dbf" -> "demand"[label="(get_building_internal)"]
    "supply_systems.dbf" -> "demand"[label="(get_building_supply)"]
    "typology.dbf" -> "demand"[label="(get_building_typology)"]
    "B001.csv" -> "demand"[label="(get_building_weekly_schedules)"]
    "HVAC.xls" -> "demand"[label="(get_database_air_conditioning_systems)"]
    "ENVELOPE.xls" -> "demand"[label="(get_database_envelope_systems)"]
    "SUPPLY.xls" -> "demand"[label="(get_database_supply_assemblies)"]
    "DH_Network_summary_result_0x19b.csv" -> "demand"[label="(get_optimization_thermal_network_data_file)"]
    "{building}_radiation.csv" -> "demand"[label="(get_radiation_building)"]
    "B001_insolation_Whm2.json" -> "demand"[label="(get_radiation_building_sensors)"]
    "B001_geometry.csv" -> "demand"[label="(get_radiation_metadata)"]
    "B001.csv" -> "demand"[label="(get_schedule_model_file)"]
    "site.shp" -> "demand"[label="(get_site_polygon)"]
    "streets.shp" -> "demand"[label="(get_street_network)"]
    "surroundings.shp" -> "demand"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "demand"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "demand"[label="(get_weather)"]
    "weather.epw" -> "demand"[label="(get_weather_file)"]
    "zone.shp" -> "demand"[label="(get_zone_geometry)"]
    "demand" -> "B001.csv"[label="(get_demand_results_file)"]
    "demand" -> "Total_demand.csv"[label="(get_total_demand)"]
    }

data_initializer
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
    "data_initializer"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/schedules";
        "{use}.csv"
    }
    subgraph cluster_4_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/use_types";
        "USE_TYPE_PROPERTIES.xlsx"
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="technology/assemblies";
        "HVAC.xls"
        "ENVELOPE.xls"
        "SUPPLY.xls"
    }
    subgraph cluster_6_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "CONVERSION.xls"
        "DISTRIBUTION.xls"
        "FEEDSTOCKS.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "data_initializer"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "data_initializer"[label="(get_site_polygon)"]
    "streets.shp" -> "data_initializer"[label="(get_street_network)"]
    "surroundings.shp" -> "data_initializer"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "data_initializer"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "data_initializer"[label="(get_weather)"]
    "zone.shp" -> "data_initializer"[label="(get_zone_geometry)"]
    "data_initializer" -> "HVAC.xls"[label="(get_database_air_conditioning_systems)"]
    "data_initializer" -> "CONVERSION.xls"[label="(get_database_conversion_systems)"]
    "data_initializer" -> "DISTRIBUTION.xls"[label="(get_database_distribution_systems)"]
    "data_initializer" -> "ENVELOPE.xls"[label="(get_database_envelope_systems)"]
    "data_initializer" -> "FEEDSTOCKS.xls"[label="(get_database_feedstocks)"]
    "data_initializer" -> "{use}.csv"[label="(get_database_standard_schedules_use)"]
    "data_initializer" -> "SUPPLY.xls"[label="(get_database_supply_assemblies)"]
    "data_initializer" -> "USE_TYPE_PROPERTIES.xlsx"[label="(get_database_use_types_properties)"]
    }

schedule_maker
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
    "schedule_maker"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "architecture.dbf"
        "indoor_comfort.dbf"
        "internal_loads.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties/schedules";
        "B001.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/occupancy";
        "B001.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/assemblies";
        "ENVELOPE.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "architecture.dbf" -> "schedule_maker"[label="(get_building_architecture)"]
    "indoor_comfort.dbf" -> "schedule_maker"[label="(get_building_comfort)"]
    "internal_loads.dbf" -> "schedule_maker"[label="(get_building_internal)"]
    "B001.csv" -> "schedule_maker"[label="(get_building_weekly_schedules)"]
    "ENVELOPE.xls" -> "schedule_maker"[label="(get_database_envelope_systems)"]
    "DH_Network_summary_result_0x19b.csv" -> "schedule_maker"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "schedule_maker"[label="(get_site_polygon)"]
    "streets.shp" -> "schedule_maker"[label="(get_street_network)"]
    "surroundings.shp" -> "schedule_maker"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "schedule_maker"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "schedule_maker"[label="(get_weather)"]
    "weather.epw" -> "schedule_maker"[label="(get_weather_file)"]
    "zone.shp" -> "schedule_maker"[label="(get_zone_geometry)"]
    "schedule_maker" -> "B001.csv"[label="(get_schedule_model_file)"]
    }

system_costs
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
    "system_costs"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "supply_systems.dbf"
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/costs";
        "operation_costs.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "Total_demand.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/assemblies";
        "SUPPLY.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "FEEDSTOCKS.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "supply_systems.dbf" -> "system_costs"[label="(get_building_supply)"]
    "FEEDSTOCKS.xls" -> "system_costs"[label="(get_database_feedstocks)"]
    "SUPPLY.xls" -> "system_costs"[label="(get_database_supply_assemblies)"]
    "DH_Network_summary_result_0x19b.csv" -> "system_costs"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "system_costs"[label="(get_site_polygon)"]
    "streets.shp" -> "system_costs"[label="(get_street_network)"]
    "surroundings.shp" -> "system_costs"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "system_costs"[label="(get_terrain)"]
    "Total_demand.csv" -> "system_costs"[label="(get_total_demand)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "system_costs"[label="(get_weather)"]
    "zone.shp" -> "system_costs"[label="(get_zone_geometry)"]
    "system_costs" -> "operation_costs.csv"[label="(get_costs_operation_file)"]
    }

network_layout
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
    "network_layout"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "Total_demand.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/thermal-network/DH";
        "edges.shp"
        "nodes.shp"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "network_layout"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "network_layout"[label="(get_site_polygon)"]
    "streets.shp" -> "network_layout"[label="(get_street_network)"]
    "surroundings.shp" -> "network_layout"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "network_layout"[label="(get_terrain)"]
    "Total_demand.csv" -> "network_layout"[label="(get_total_demand)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "network_layout"[label="(get_weather)"]
    "zone.shp" -> "network_layout"[label="(get_zone_geometry)"]
    "network_layout" -> "edges.shp"[label="(get_network_layout_edges_shapefile)"]
    "network_layout" -> "nodes.shp"[label="(get_network_layout_nodes_shapefile)"]
    }

weather_helper
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
    "weather_helper"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    subgraph cluster_4_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="weather";
        "weather.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "weather_helper"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "weather_helper"[label="(get_site_polygon)"]
    "streets.shp" -> "weather_helper"[label="(get_street_network)"]
    "surroundings.shp" -> "weather_helper"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "weather_helper"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "weather_helper"[label="(get_weather)"]
    "zone.shp" -> "weather_helper"[label="(get_zone_geometry)"]
    "weather_helper" -> "weather.epw"[label="(get_weather_file)"]
    }

optimization
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
    "optimization"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "B001.csv"
        "Total_demand.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/decentralized";
        "{building}_{configuration}_cooling_activation.csv"
        "{building}_{configuration}_cooling.csv"
        "DiscOp_B001_result_heating.csv"
        "DiscOp_B001_result_heating_activation.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/master";
        "CheckPoint_1"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x1be.csv"
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_4_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x1be.csv"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        "110011011DH_B001_result.csv"
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        "110011011DH_B001_result.csv"
        "Total_DH_111111111.csv"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/potentials";
        "Shallow_geothermal_potential.csv"
        "Sewage_heat_potential.csv"
        "Water_body_potential.csv"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        "PVT_total.csv"
        "PV_total.csv"
        "SC_FP_total.csv"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/thermal-network";
        "DH__plant_pumping_pressure_loss_Pa.csv"
        "DH__total_thermal_loss_edges_kW.csv"
        "DH__metadata_edges.csv"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_10_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="optimization/slave/gen_0";
        "ind_2_connected_heating_capacity.csv"
        "ind_1_disconnected_heating_capacity.csv"
        "ind_2_total_performance.csv"
    }
    subgraph cluster_11_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="optimization/slave/gen_1";
        "ind_1_connected_cooling_capacity.csv"
        "ind_0_disconnected_cooling_capacity.csv"
        "gen_1_connected_performance.csv"
        "gen_1_total_performance_halloffame.csv"
        "ind_2_buildings_connected_performance.csv"
        "ind_2_Cooling_Activation_Pattern.csv"
        "ind_1_Electricity_Activation_Pattern.csv"
        "ind_1_Electricity_Requirements_Pattern.csv"
    }
    subgraph cluster_12_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="optimization/slave/gen_2";
        "ind_0_connected_electrical_capacity.csv"
        "gen_2_disconnected_performance.csv"
        "gen_2_total_performance.csv"
        "gen_2_total_performance_pareto.csv"
        "generation_2_individuals.csv"
        "ind_1_building_connectivity.csv"
        "ind_0_buildings_disconnected_performance.csv"
        "ind_0_Heating_Activation_Pattern.csv"
    }
    subgraph cluster_13_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "CONVERSION.xls"
        "DISTRIBUTION.xls"
        "FEEDSTOCKS.xls"
    }
    subgraph cluster_14_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_15_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "PVT_total.csv" -> "optimization"[label="(PVT_totals)"]
    "PV_total.csv" -> "optimization"[label="(PV_totals)"]
    "SC_FP_total.csv" -> "optimization"[label="(SC_totals)"]
    "CONVERSION.xls" -> "optimization"[label="(get_database_conversion_systems)"]
    "DISTRIBUTION.xls" -> "optimization"[label="(get_database_distribution_systems)"]
    "FEEDSTOCKS.xls" -> "optimization"[label="(get_database_feedstocks)"]
    "B001.csv" -> "optimization"[label="(get_demand_results_file)"]
    "Shallow_geothermal_potential.csv" -> "optimization"[label="(get_geothermal_potential)"]
    "DH__plant_pumping_pressure_loss_Pa.csv" -> "optimization"[label="(get_network_total_pressure_drop_file)"]
    "DH__total_thermal_loss_edges_kW.csv" -> "optimization"[label="(get_network_total_thermal_loss_file)"]
    "{building}_{configuration}_cooling_activation.csv" -> "optimization"[label="(get_optimization_decentralized_folder_building_cooling_activation)"]
    "{building}_{configuration}_cooling.csv" -> "optimization"[label="(get_optimization_decentralized_folder_building_result_cooling)"]
    "DiscOp_B001_result_heating.csv" -> "optimization"[label="(get_optimization_decentralized_folder_building_result_heating)"]
    "DiscOp_B001_result_heating_activation.csv" -> "optimization"[label="(get_optimization_decentralized_folder_building_result_heating_activation)"]
    "DH_Network_summary_result_0x1be.csv" -> "optimization"[label="(get_optimization_network_results_summary)"]
    "110011011DH_B001_result.csv" -> "optimization"[label="(get_optimization_substations_results_file)"]
    "DH_Network_summary_result_0x19b.csv" -> "optimization"[label="(get_optimization_thermal_network_data_file)"]
    "Sewage_heat_potential.csv" -> "optimization"[label="(get_sewage_heat_potential)"]
    "site.shp" -> "optimization"[label="(get_site_polygon)"]
    "streets.shp" -> "optimization"[label="(get_street_network)"]
    "surroundings.shp" -> "optimization"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "optimization"[label="(get_terrain)"]
    "DH__metadata_edges.csv" -> "optimization"[label="(get_thermal_network_edge_list_file)"]
    "Total_demand.csv" -> "optimization"[label="(get_total_demand)"]
    "Water_body_potential.csv" -> "optimization"[label="(get_water_body_potential)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "optimization"[label="(get_weather)"]
    "weather.epw" -> "optimization"[label="(get_weather_file)"]
    "zone.shp" -> "optimization"[label="(get_zone_geometry)"]
    "optimization" -> "CheckPoint_1"[label="(get_optimization_checkpoint)"]
    "optimization" -> "ind_1_connected_cooling_capacity.csv"[label="(get_optimization_connected_cooling_capacity)"]
    "optimization" -> "ind_0_connected_electrical_capacity.csv"[label="(get_optimization_connected_electricity_capacity)"]
    "optimization" -> "ind_2_connected_heating_capacity.csv"[label="(get_optimization_connected_heating_capacity)"]
    "optimization" -> "ind_0_disconnected_cooling_capacity.csv"[label="(get_optimization_disconnected_cooling_capacity)"]
    "optimization" -> "ind_1_disconnected_heating_capacity.csv"[label="(get_optimization_disconnected_heating_capacity)"]
    "optimization" -> "gen_1_connected_performance.csv"[label="(get_optimization_generation_connected_performance)"]
    "optimization" -> "gen_2_disconnected_performance.csv"[label="(get_optimization_generation_disconnected_performance)"]
    "optimization" -> "gen_2_total_performance.csv"[label="(get_optimization_generation_total_performance)"]
    "optimization" -> "gen_1_total_performance_halloffame.csv"[label="(get_optimization_generation_total_performance_halloffame)"]
    "optimization" -> "gen_2_total_performance_pareto.csv"[label="(get_optimization_generation_total_performance_pareto)"]
    "optimization" -> "generation_2_individuals.csv"[label="(get_optimization_individuals_in_generation)"]
    "optimization" -> "DH_Network_summary_result_0x1be.csv"[label="(get_optimization_network_results_summary)"]
    "optimization" -> "ind_1_building_connectivity.csv"[label="(get_optimization_slave_building_connectivity)"]
    "optimization" -> "ind_2_buildings_connected_performance.csv"[label="(get_optimization_slave_connected_performance)"]
    "optimization" -> "ind_2_Cooling_Activation_Pattern.csv"[label="(get_optimization_slave_cooling_activation_pattern)"]
    "optimization" -> "ind_0_buildings_disconnected_performance.csv"[label="(get_optimization_slave_disconnected_performance)"]
    "optimization" -> "ind_1_Electricity_Activation_Pattern.csv"[label="(get_optimization_slave_electricity_activation_pattern)"]
    "optimization" -> "ind_1_Electricity_Requirements_Pattern.csv"[label="(get_optimization_slave_electricity_requirements_data)"]
    "optimization" -> "ind_0_Heating_Activation_Pattern.csv"[label="(get_optimization_slave_heating_activation_pattern)"]
    "optimization" -> "ind_2_total_performance.csv"[label="(get_optimization_slave_total_performance)"]
    "optimization" -> "110011011DH_B001_result.csv"[label="(get_optimization_substations_results_file)"]
    "optimization" -> "Total_DH_111111111.csv"[label="(get_optimization_substations_total_file)"]
    }

shallow_geothermal_potential
----------------------------
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
    "shallow_geothermal_potential"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials";
        "Shallow_geothermal_potential.csv"
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
        "weather.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "shallow_geothermal_potential"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "shallow_geothermal_potential"[label="(get_site_polygon)"]
    "streets.shp" -> "shallow_geothermal_potential"[label="(get_street_network)"]
    "surroundings.shp" -> "shallow_geothermal_potential"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "shallow_geothermal_potential"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "shallow_geothermal_potential"[label="(get_weather)"]
    "weather.epw" -> "shallow_geothermal_potential"[label="(get_weather_file)"]
    "zone.shp" -> "shallow_geothermal_potential"[label="(get_zone_geometry)"]
    "shallow_geothermal_potential" -> "Shallow_geothermal_potential.csv"[label="(get_geothermal_potential)"]
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
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-properties";
        "architecture.dbf"
        "supply_systems.dbf"
        "typology.dbf"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/demand";
        "Total_demand.csv"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/emissions";
        "Total_LCA_embodied.csv"
        "Total_LCA_mobility.csv"
        "Total_LCA_operation.csv"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/assemblies";
        "SUPPLY.xls"
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/components";
        "FEEDSTOCKS.xls"
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_9_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "architecture.dbf" -> "emissions"[label="(get_building_architecture)"]
    "supply_systems.dbf" -> "emissions"[label="(get_building_supply)"]
    "typology.dbf" -> "emissions"[label="(get_building_typology)"]
    "FEEDSTOCKS.xls" -> "emissions"[label="(get_database_feedstocks)"]
    "SUPPLY.xls" -> "emissions"[label="(get_database_supply_assemblies)"]
    "DH_Network_summary_result_0x19b.csv" -> "emissions"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "emissions"[label="(get_site_polygon)"]
    "streets.shp" -> "emissions"[label="(get_street_network)"]
    "surroundings.shp" -> "emissions"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "emissions"[label="(get_terrain)"]
    "Total_demand.csv" -> "emissions"[label="(get_total_demand)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "emissions"[label="(get_weather)"]
    "zone.shp" -> "emissions"[label="(get_zone_geometry)"]
    "emissions" -> "Total_LCA_embodied.csv"[label="(get_lca_embodied)"]
    "emissions" -> "Total_LCA_mobility.csv"[label="(get_lca_mobility)"]
    "emissions" -> "Total_LCA_operation.csv"[label="(get_lca_operation)"]
    }

data-initializer
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
    "data-initializer"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="building-geometry";
        "site.shp"
        "surroundings.shp"
        "zone.shp"
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        "DH_Network_summary_result_0x19b.csv"
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="networks";
        "streets.shp"
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="technology/archetypes";
        "CONSTRUCTION_STANDARDS.xlsx"
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="topography";
        "terrain.tif"
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="weather";
        "Zug-inducity_1990_2010_TMY.epw"
    }
    "DH_Network_summary_result_0x19b.csv" -> "data-initializer"[label="(get_optimization_thermal_network_data_file)"]
    "site.shp" -> "data-initializer"[label="(get_site_polygon)"]
    "streets.shp" -> "data-initializer"[label="(get_street_network)"]
    "surroundings.shp" -> "data-initializer"[label="(get_surroundings_geometry)"]
    "terrain.tif" -> "data-initializer"[label="(get_terrain)"]
    "Zug-inducity_1990_2010_TMY.epw" -> "data-initializer"[label="(get_weather)"]
    "zone.shp" -> "data-initializer"[label="(get_zone_geometry)"]
    "data-initializer" -> "CONSTRUCTION_STANDARDS.xlsx"[label="(get_database_construction_standards)"]
    }
