:orphan:

Script Data Flow
================
This section aims to clarify the files used (inputs) or created (outputs) by each script, along with the methods used
to access this data.

TO DO: run trace for all scripts.


multi_criteria_analysis
-----------------------
.. graphviz::

    digraph multi_criteria_analysis {
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
        label="optimization/slave/gen_2";
        get_optimization_generation_total_performance_pareto[label="gen_2_total_performance_pareto.csv"];
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/multicriteria";
        get_multi_criteria_analysis[label="gen_2_multi_criteria_analysis.csv"];
    }
    get_optimization_generation_total_performance_pareto -> "multi_criteria_analysis"[label="(get_optimization_generation_total_performance_pareto)"];
    "multi_criteria_analysis" -> get_multi_criteria_analysis[label="(get_multi_criteria_analysis)"];
    }

photovoltaic
------------
.. graphviz::

    digraph photovoltaic {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        PV_metadata_results[label="B001_PV_sensors.csv"];
        PV_results[label="B001_PV.csv"];
        PV_total_buildings[label="PV_total_buildings.csv"];
        PV_totals[label="PV_total.csv"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_conversion_systems[label="CONVERSION.xls"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        get_radiation_building[label="{building}_radiation.csv"];
        get_radiation_building_sensors[label="B001_insolation_Whm2.json"];
        get_radiation_metadata[label="B001_geometry.csv"];
    }
    get_database_conversion_systems -> "photovoltaic"[label="(get_database_conversion_systems)"];
    get_radiation_building -> "photovoltaic"[label="(get_radiation_building)"];
    get_radiation_building_sensors -> "photovoltaic"[label="(get_radiation_building_sensors)"];
    get_radiation_metadata -> "photovoltaic"[label="(get_radiation_metadata)"];
    get_weather_file -> "photovoltaic"[label="(get_weather_file)"];
    get_zone_geometry -> "photovoltaic"[label="(get_zone_geometry)"];
    "photovoltaic" -> PV_metadata_results[label="(PV_metadata_results)"];
    "photovoltaic" -> PV_results[label="(PV_results)"];
    "photovoltaic" -> PV_total_buildings[label="(PV_total_buildings)"];
    "photovoltaic" -> PV_totals[label="(PV_totals)"];
    }

decentralized
-------------
.. graphviz::

    digraph decentralized {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/decentralized";
        get_optimization_decentralized_folder_building_cooling_activation[label="{building}_{configuration}_cooling_activation.csv"];
        get_optimization_decentralized_folder_building_result_heating[label="DiscOp_B001_result_heating.csv"];
        get_optimization_decentralized_folder_building_result_heating_activation[label="DiscOp_B001_result_heating_activation.csv"];
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        get_optimization_substations_results_file[label="110011011DH_B001_result.csv"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        SC_results[label="B001_SC_ET.csv"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_supply[label="supply_systems.dbf"];
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_conversion_systems[label="CONVERSION.xls"];
        get_database_feedstocks[label="FEEDSTOCKS.xls"];
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_demand_results_file[label="B001.csv"];
        get_total_demand[label="Total_demand.csv"];
    }
    SC_results -> "decentralized"[label="(SC_results)"];
    get_building_supply -> "decentralized"[label="(get_building_supply)"];
    get_database_conversion_systems -> "decentralized"[label="(get_database_conversion_systems)"];
    get_database_feedstocks -> "decentralized"[label="(get_database_feedstocks)"];
    get_demand_results_file -> "decentralized"[label="(get_demand_results_file)"];
    get_total_demand -> "decentralized"[label="(get_total_demand)"];
    get_weather_file -> "decentralized"[label="(get_weather_file)"];
    get_zone_geometry -> "decentralized"[label="(get_zone_geometry)"];
    "decentralized" -> get_optimization_decentralized_folder_building_cooling_activation[label="(get_optimization_decentralized_folder_building_cooling_activation)"];
    "decentralized" -> get_optimization_decentralized_folder_building_result_heating[label="(get_optimization_decentralized_folder_building_result_heating)"];
    "decentralized" -> get_optimization_decentralized_folder_building_result_heating_activation[label="(get_optimization_decentralized_folder_building_result_heating_activation)"];
    "decentralized" -> get_optimization_substations_results_file[label="(get_optimization_substations_results_file)"];
    }

solar_collector
---------------
.. graphviz::

    digraph solar_collector {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        SC_metadata_results[label="B001_SC_ET_sensors.csv"];
        SC_results[label="B001_SC_ET.csv"];
        SC_total_buildings[label="SC_ET_total_buildings.csv"];
        SC_totals[label="SC_FP_total.csv"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_conversion_systems[label="CONVERSION.xls"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        get_radiation_building[label="{building}_radiation.csv"];
        get_radiation_building_sensors[label="B001_insolation_Whm2.json"];
        get_radiation_metadata[label="B001_geometry.csv"];
    }
    get_database_conversion_systems -> "solar_collector"[label="(get_database_conversion_systems)"];
    get_radiation_building -> "solar_collector"[label="(get_radiation_building)"];
    get_radiation_building_sensors -> "solar_collector"[label="(get_radiation_building_sensors)"];
    get_radiation_metadata -> "solar_collector"[label="(get_radiation_metadata)"];
    get_weather_file -> "solar_collector"[label="(get_weather_file)"];
    get_zone_geometry -> "solar_collector"[label="(get_zone_geometry)"];
    "solar_collector" -> SC_metadata_results[label="(SC_metadata_results)"];
    "solar_collector" -> SC_results[label="(SC_results)"];
    "solar_collector" -> SC_total_buildings[label="(SC_total_buildings)"];
    "solar_collector" -> SC_totals[label="(SC_totals)"];
    }

zone_helper
-----------
.. graphviz::

    digraph zone_helper {
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
        label="inputs/building-geometry";
        get_site_polygon[label="site.shp"];
    }
    get_site_polygon -> "zone_helper"[label="(get_site_polygon)"];
    }

archetypes_mapper
-----------------
.. graphviz::

    digraph archetypes_mapper {
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
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_typology[label="typology.dbf"];
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_air_conditioning[label="air_conditioning_systems.dbf"];
        get_building_architecture[label="architecture.dbf"];
        get_building_comfort[label="indoor_comfort.dbf"];
        get_building_internal[label="internal_loads.dbf"];
        get_building_supply[label="supply_systems.dbf"];
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties/schedules";
        get_building_weekly_schedules[label="B001.csv"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/archetypes";
        get_database_construction_standards[label="CONSTRUCTION_STANDARDS.xlsx"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/schedules";
        get_database_standard_schedules_use[label="RESTAURANT.csv"];
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/use_types";
        get_database_use_types_properties[label="USE_TYPE_PROPERTIES.xlsx"];
    }
    get_building_typology -> "archetypes_mapper"[label="(get_building_typology)"];
    get_database_construction_standards -> "archetypes_mapper"[label="(get_database_construction_standards)"];
    get_database_standard_schedules_use -> "archetypes_mapper"[label="(get_database_standard_schedules_use)"];
    get_database_use_types_properties -> "archetypes_mapper"[label="(get_database_use_types_properties)"];
    get_zone_geometry -> "archetypes_mapper"[label="(get_zone_geometry)"];
    "archetypes_mapper" -> get_building_air_conditioning[label="(get_building_air_conditioning)"];
    "archetypes_mapper" -> get_building_architecture[label="(get_building_architecture)"];
    "archetypes_mapper" -> get_building_comfort[label="(get_building_comfort)"];
    "archetypes_mapper" -> get_building_internal[label="(get_building_internal)"];
    "archetypes_mapper" -> get_building_supply[label="(get_building_supply)"];
    "archetypes_mapper" -> get_building_weekly_schedules[label="(get_building_weekly_schedules)"];
    }

sewage_potential
----------------
.. graphviz::

    digraph sewage_potential {
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
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_demand_results_file[label="B001.csv"];
        get_total_demand[label="Total_demand.csv"];
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/potentials";
        get_sewage_heat_potential[label="Sewage_heat_potential.csv"];
    }
    get_demand_results_file -> "sewage_potential"[label="(get_demand_results_file)"];
    get_total_demand -> "sewage_potential"[label="(get_total_demand)"];
    get_zone_geometry -> "sewage_potential"[label="(get_zone_geometry)"];
    "sewage_potential" -> get_sewage_heat_potential[label="(get_sewage_heat_potential)"];
    }

photovoltaic_thermal
--------------------
.. graphviz::

    digraph photovoltaic_thermal {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        PVT_metadata_results[label="B001_PVT_sensors.csv"];
        PVT_results[label="B001_PVT.csv"];
        PVT_total_buildings[label="PVT_total_buildings.csv"];
        PVT_totals[label="PVT_total.csv"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_conversion_systems[label="CONVERSION.xls"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        get_radiation_building[label="{building}_radiation.csv"];
        get_radiation_building_sensors[label="B001_insolation_Whm2.json"];
        get_radiation_metadata[label="B001_geometry.csv"];
    }
    get_database_conversion_systems -> "photovoltaic_thermal"[label="(get_database_conversion_systems)"];
    get_radiation_building -> "photovoltaic_thermal"[label="(get_radiation_building)"];
    get_radiation_building_sensors -> "photovoltaic_thermal"[label="(get_radiation_building_sensors)"];
    get_radiation_metadata -> "photovoltaic_thermal"[label="(get_radiation_metadata)"];
    get_weather_file -> "photovoltaic_thermal"[label="(get_weather_file)"];
    get_zone_geometry -> "photovoltaic_thermal"[label="(get_zone_geometry)"];
    "photovoltaic_thermal" -> PVT_metadata_results[label="(PVT_metadata_results)"];
    "photovoltaic_thermal" -> PVT_results[label="(PVT_results)"];
    "photovoltaic_thermal" -> PVT_total_buildings[label="(PVT_total_buildings)"];
    "photovoltaic_thermal" -> PVT_totals[label="(PVT_totals)"];
    }

radiation
---------
.. graphviz::

    digraph radiation {
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
        label="inputs/building-geometry";
        get_surroundings_geometry[label="surroundings.shp"];
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_architecture[label="architecture.dbf"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/assemblies";
        get_database_envelope_systems[label="ENVELOPE.xls"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/topography";
        get_terrain[label="terrain.tif"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        get_radiation_building[label="{building}_radiation.csv"];
        get_radiation_building_sensors[label="B001_insolation_Whm2.json"];
        get_radiation_materials[label="buidling_materials.csv"];
        get_radiation_metadata[label="B001_geometry.csv"];
    }
    get_building_architecture -> "radiation"[label="(get_building_architecture)"];
    get_database_envelope_systems -> "radiation"[label="(get_database_envelope_systems)"];
    get_surroundings_geometry -> "radiation"[label="(get_surroundings_geometry)"];
    get_terrain -> "radiation"[label="(get_terrain)"];
    get_weather_file -> "radiation"[label="(get_weather_file)"];
    get_zone_geometry -> "radiation"[label="(get_zone_geometry)"];
    "radiation" -> get_radiation_building[label="(get_radiation_building)"];
    "radiation" -> get_radiation_building_sensors[label="(get_radiation_building_sensors)"];
    "radiation" -> get_radiation_materials[label="(get_radiation_materials)"];
    "radiation" -> get_radiation_metadata[label="(get_radiation_metadata)"];
    }

water_body_potential
--------------------
.. graphviz::

    digraph water_body_potential {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/potentials";
        get_water_body_potential[label="Water_body_potential.csv"];
    }
    "water_body_potential" -> get_water_body_potential[label="(get_water_body_potential)"];
    }

decentrlized
------------
.. graphviz::

    digraph decentrlized {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/decentralized";
        get_optimization_decentralized_folder_building_result_cooling[label="{building}_{configuration}_cooling.csv"];
    }
    "decentrlized" -> get_optimization_decentralized_folder_building_result_cooling[label="(get_optimization_decentralized_folder_building_result_cooling)"];
    }

thermal_network
---------------
.. graphviz::

    digraph thermal_network {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        get_optimization_substations_results_file[label="110011011DH_B001_result.csv"];
        get_optimization_substations_total_file[label="Total_DH_111111111.csv"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/thermal-network/DH";
        get_network_layout_edges_shapefile[label="edges.shp"];
        get_network_layout_nodes_shapefile[label="nodes.shp"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_distribution_systems[label="DISTRIBUTION.xls"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_demand_results_file[label="B001.csv"];
        get_total_demand[label="Total_demand.csv"];
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/thermal-network";
        get_nominal_edge_mass_flow_csv_file[label="Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv"];
        get_nominal_node_mass_flow_csv_file[label="Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv"];
        get_thermal_network_edge_node_matrix_file[label="{network_type}__EdgeNode.csv"];
    }
    subgraph cluster_6_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/thermal-network";
        get_network_energy_pumping_requirements_file[label="DH__plant_pumping_load_kW.csv"];
        get_network_linear_pressure_drop_edges[label="DH__linear_pressure_drop_edges_Paperm.csv"];
        get_network_linear_thermal_loss_edges_file[label="DH__linear_thermal_loss_edges_Wperm.csv"];
        get_network_pressure_at_nodes[label="DH__pressure_at_nodes_Pa.csv"];
        get_network_temperature_plant[label="DH__temperature_plant_K.csv"];
        get_network_temperature_return_nodes_file[label="DH__temperature_return_nodes_K.csv"];
        get_network_temperature_supply_nodes_file[label="DH__temperature_supply_nodes_K.csv"];
        get_network_thermal_loss_edges_file[label="DH__thermal_loss_edges_kW.csv"];
        get_network_total_pressure_drop_file[label="DH__plant_pumping_pressure_loss_Pa.csv"];
        get_network_total_thermal_loss_file[label="DH__total_thermal_loss_edges_kW.csv"];
        get_thermal_demand_csv_file[label="DH__thermal_demand_per_building_W.csv"];
        get_thermal_network_edge_list_file[label="DH__metadata_edges.csv"];
        get_thermal_network_layout_massflow_edges_file[label="DH__massflow_edges_kgs.csv"];
        get_thermal_network_layout_massflow_nodes_file[label="DH__massflow_nodes_kgs.csv"];
        get_thermal_network_node_types_csv_file[label="DH__metadata_nodes.csv"];
        get_thermal_network_plant_heat_requirement_file[label="DH__plant_thermal_load_kW.csv"];
        get_thermal_network_pressure_losses_edges_file[label="DH__pressure_losses_edges_kW.csv"];
        get_thermal_network_substation_ploss_file[label="DH__pumping_load_due_to_substations_kW.csv"];
        get_thermal_network_velocity_edges_file[label="DH__velocity_edges_mpers.csv"];
    }
    get_database_distribution_systems -> "thermal_network"[label="(get_database_distribution_systems)"];
    get_demand_results_file -> "thermal_network"[label="(get_demand_results_file)"];
    get_network_layout_edges_shapefile -> "thermal_network"[label="(get_network_layout_edges_shapefile)"];
    get_network_layout_nodes_shapefile -> "thermal_network"[label="(get_network_layout_nodes_shapefile)"];
    get_nominal_edge_mass_flow_csv_file -> "thermal_network"[label="(get_nominal_edge_mass_flow_csv_file)"];
    get_nominal_node_mass_flow_csv_file -> "thermal_network"[label="(get_nominal_node_mass_flow_csv_file)"];
    get_thermal_network_edge_node_matrix_file -> "thermal_network"[label="(get_thermal_network_edge_node_matrix_file)"];
    get_total_demand -> "thermal_network"[label="(get_total_demand)"];
    get_weather_file -> "thermal_network"[label="(get_weather_file)"];
    get_zone_geometry -> "thermal_network"[label="(get_zone_geometry)"];
    "thermal_network" -> get_network_energy_pumping_requirements_file[label="(get_network_energy_pumping_requirements_file)"];
    "thermal_network" -> get_network_linear_pressure_drop_edges[label="(get_network_linear_pressure_drop_edges)"];
    "thermal_network" -> get_network_linear_thermal_loss_edges_file[label="(get_network_linear_thermal_loss_edges_file)"];
    "thermal_network" -> get_network_pressure_at_nodes[label="(get_network_pressure_at_nodes)"];
    "thermal_network" -> get_network_temperature_plant[label="(get_network_temperature_plant)"];
    "thermal_network" -> get_network_temperature_return_nodes_file[label="(get_network_temperature_return_nodes_file)"];
    "thermal_network" -> get_network_temperature_supply_nodes_file[label="(get_network_temperature_supply_nodes_file)"];
    "thermal_network" -> get_network_thermal_loss_edges_file[label="(get_network_thermal_loss_edges_file)"];
    "thermal_network" -> get_network_total_pressure_drop_file[label="(get_network_total_pressure_drop_file)"];
    "thermal_network" -> get_network_total_thermal_loss_file[label="(get_network_total_thermal_loss_file)"];
    "thermal_network" -> get_optimization_substations_results_file[label="(get_optimization_substations_results_file)"];
    "thermal_network" -> get_optimization_substations_total_file[label="(get_optimization_substations_total_file)"];
    "thermal_network" -> get_thermal_demand_csv_file[label="(get_thermal_demand_csv_file)"];
    "thermal_network" -> get_thermal_network_edge_list_file[label="(get_thermal_network_edge_list_file)"];
    "thermal_network" -> get_thermal_network_layout_massflow_edges_file[label="(get_thermal_network_layout_massflow_edges_file)"];
    "thermal_network" -> get_thermal_network_layout_massflow_nodes_file[label="(get_thermal_network_layout_massflow_nodes_file)"];
    "thermal_network" -> get_thermal_network_node_types_csv_file[label="(get_thermal_network_node_types_csv_file)"];
    "thermal_network" -> get_thermal_network_plant_heat_requirement_file[label="(get_thermal_network_plant_heat_requirement_file)"];
    "thermal_network" -> get_thermal_network_pressure_losses_edges_file[label="(get_thermal_network_pressure_losses_edges_file)"];
    "thermal_network" -> get_thermal_network_substation_ploss_file[label="(get_thermal_network_substation_ploss_file)"];
    "thermal_network" -> get_thermal_network_velocity_edges_file[label="(get_thermal_network_velocity_edges_file)"];
    }

demand
------
.. graphviz::

    digraph demand {
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
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_air_conditioning[label="air_conditioning_systems.dbf"];
        get_building_architecture[label="architecture.dbf"];
        get_building_comfort[label="indoor_comfort.dbf"];
        get_building_internal[label="internal_loads.dbf"];
        get_building_supply[label="supply_systems.dbf"];
        get_building_typology[label="typology.dbf"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties/schedules";
        get_building_weekly_schedules[label="B001.csv"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/assemblies";
        get_database_air_conditioning_systems[label="HVAC.xls"];
        get_database_envelope_systems[label="ENVELOPE.xls"];
        get_database_supply_assemblies[label="SUPPLY.xls"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_demand_results_file[label="B001.csv"];
        get_total_demand[label="Total_demand.csv"];
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/occupancy";
        get_schedule_model_file[label="B001.csv"];
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/solar-radiation";
        get_radiation_building[label="{building}_radiation.csv"];
        get_radiation_building_sensors[label="B001_insolation_Whm2.json"];
        get_radiation_metadata[label="B001_geometry.csv"];
    }
    get_building_air_conditioning -> "demand"[label="(get_building_air_conditioning)"];
    get_building_architecture -> "demand"[label="(get_building_architecture)"];
    get_building_comfort -> "demand"[label="(get_building_comfort)"];
    get_building_internal -> "demand"[label="(get_building_internal)"];
    get_building_supply -> "demand"[label="(get_building_supply)"];
    get_building_typology -> "demand"[label="(get_building_typology)"];
    get_building_weekly_schedules -> "demand"[label="(get_building_weekly_schedules)"];
    get_database_air_conditioning_systems -> "demand"[label="(get_database_air_conditioning_systems)"];
    get_database_envelope_systems -> "demand"[label="(get_database_envelope_systems)"];
    get_database_supply_assemblies -> "demand"[label="(get_database_supply_assemblies)"];
    get_radiation_building -> "demand"[label="(get_radiation_building)"];
    get_radiation_building_sensors -> "demand"[label="(get_radiation_building_sensors)"];
    get_radiation_metadata -> "demand"[label="(get_radiation_metadata)"];
    get_schedule_model_file -> "demand"[label="(get_schedule_model_file)"];
    get_weather_file -> "demand"[label="(get_weather_file)"];
    get_zone_geometry -> "demand"[label="(get_zone_geometry)"];
    "demand" -> get_demand_results_file[label="(get_demand_results_file)"];
    "demand" -> get_total_demand[label="(get_total_demand)"];
    }

database_helper
----------------
.. graphviz::

    digraph database_helper {
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
    "database_helper"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/technology/archetypes";
        get_database_construction_standards[label="CONSTRUCTION_STANDARDS.xlsx"];
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/technology/assemblies";
        get_database_air_conditioning_systems[label="HVAC.xls"];
        get_database_envelope_systems[label="ENVELOPE.xls"];
        get_database_supply_assemblies[label="SUPPLY.xls"];
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_conversion_systems[label="CONVERSION.xls"];
        get_database_distribution_systems[label="DISTRIBUTION.xls"];
        get_database_feedstocks[label="FEEDSTOCKS.xls"];
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/schedules";
        get_database_standard_schedules_use[label="RESTAURANT.csv"];
    }
    subgraph cluster_4_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="technology/archetypes/use_types";
        get_database_use_types_properties[label="USE_TYPE_PROPERTIES.xlsx"];
    }
    "database_helper" -> get_database_air_conditioning_systems[label="(get_database_air_conditioning_systems)"];
    "database_helper" -> get_database_construction_standards[label="(get_database_construction_standards)"];
    "database_helper" -> get_database_conversion_systems[label="(get_database_conversion_systems)"];
    "database_helper" -> get_database_distribution_systems[label="(get_database_distribution_systems)"];
    "database_helper" -> get_database_envelope_systems[label="(get_database_envelope_systems)"];
    "database_helper" -> get_database_feedstocks[label="(get_database_feedstocks)"];
    "database_helper" -> get_database_standard_schedules_use[label="(get_database_standard_schedules_use)"];
    "database_helper" -> get_database_supply_assemblies[label="(get_database_supply_assemblies)"];
    "database_helper" -> get_database_use_types_properties[label="(get_database_use_types_properties)"];
    }

schedule_maker
--------------
.. graphviz::

    digraph schedule_maker {
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
        label="inputs/building-geometry";
        get_surroundings_geometry[label="surroundings.shp"];
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_architecture[label="architecture.dbf"];
        get_building_comfort[label="indoor_comfort.dbf"];
        get_building_internal[label="internal_loads.dbf"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties/schedules";
        get_building_weekly_schedules[label="B001.csv"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/assemblies";
        get_database_envelope_systems[label="ENVELOPE.xls"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/topography";
        get_terrain[label="terrain.tif"];
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_6_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/occupancy";
        get_schedule_model_file[label="B001.csv"];
    }
    get_building_architecture -> "schedule_maker"[label="(get_building_architecture)"];
    get_building_comfort -> "schedule_maker"[label="(get_building_comfort)"];
    get_building_internal -> "schedule_maker"[label="(get_building_internal)"];
    get_building_weekly_schedules -> "schedule_maker"[label="(get_building_weekly_schedules)"];
    get_database_envelope_systems -> "schedule_maker"[label="(get_database_envelope_systems)"];
    get_surroundings_geometry -> "schedule_maker"[label="(get_surroundings_geometry)"];
    get_terrain -> "schedule_maker"[label="(get_terrain)"];
    get_weather_file -> "schedule_maker"[label="(get_weather_file)"];
    get_zone_geometry -> "schedule_maker"[label="(get_zone_geometry)"];
    "schedule_maker" -> get_schedule_model_file[label="(get_schedule_model_file)"];
    }

system_costs
------------
.. graphviz::

    digraph system_costs {
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
        label="inputs/building-properties";
        get_building_supply[label="supply_systems.dbf"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/assemblies";
        get_database_supply_assemblies[label="SUPPLY.xls"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_feedstocks[label="FEEDSTOCKS.xls"];
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/costs";
        get_costs_operation_file[label="operation_costs.csv"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_total_demand[label="Total_demand.csv"];
    }
    get_building_supply -> "system_costs"[label="(get_building_supply)"];
    get_database_feedstocks -> "system_costs"[label="(get_database_feedstocks)"];
    get_database_supply_assemblies -> "system_costs"[label="(get_database_supply_assemblies)"];
    get_total_demand -> "system_costs"[label="(get_total_demand)"];
    "system_costs" -> get_costs_operation_file[label="(get_costs_operation_file)"];
    }

network_layout
--------------
.. graphviz::

    digraph network_layout {
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
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/thermal-network/DH";
        get_network_layout_edges_shapefile[label="edges.shp"];
        get_network_layout_nodes_shapefile[label="nodes.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/networks";
        get_street_network[label="streets.shp"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_total_demand[label="Total_demand.csv"];
    }
    get_street_network -> "network_layout"[label="(get_street_network)"];
    get_total_demand -> "network_layout"[label="(get_total_demand)"];
    get_zone_geometry -> "network_layout"[label="(get_zone_geometry)"];
    "network_layout" -> get_network_layout_edges_shapefile[label="(get_network_layout_edges_shapefile)"];
    "network_layout" -> get_network_layout_nodes_shapefile[label="(get_network_layout_nodes_shapefile)"];
    }

weather_helper
--------------
.. graphviz::

    digraph weather_helper {
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
        label="databases/weather";
        get_weather[label="Zug-inducity_1990_2010_TMY.epw"];
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    get_weather -> "weather_helper"[label="(get_weather)"];
    "weather_helper" -> get_weather_file[label="(get_weather_file)"];
    }

data_migrator
-----------------
.. graphviz::

    digraph data_migrator {
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
    "data_migrator"[style=filled, color=white, fillcolor="#3FC0C2", shape=note, fontsize=20, fontname=arial];
    subgraph cluster_0_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_typology[label="typology.dbf"];
    }
    "data_migrator" -> get_building_typology[label="(get_building_typology)"];
    }

optimization
------------
.. graphviz::

    digraph optimization {
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
        label="data/optimization/decentralized";
        get_optimization_decentralized_folder_building_cooling_activation[label="{building}_{configuration}_cooling_activation.csv"];
        get_optimization_decentralized_folder_building_result_cooling[label="{building}_{configuration}_cooling.csv"];
        get_optimization_decentralized_folder_building_result_heating[label="DiscOp_B001_result_heating.csv"];
        get_optimization_decentralized_folder_building_result_heating_activation[label="DiscOp_B001_result_heating_activation.csv"];
    }
    subgraph cluster_1_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/master";
        get_optimization_checkpoint[label="CheckPoint_1"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/network";
        get_optimization_network_results_summary[label="DH_Network_summary_result_0x1be.csv"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        get_optimization_substations_results_file[label="110011011DH_B001_result.csv"];
    }
    subgraph cluster_3_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="data/optimization/substations";
        get_optimization_substations_total_file[label="Total_DH_111111111.csv"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="data/potentials/solar";
        PVT_totals[label="PVT_total.csv"];
        PV_totals[label="PV_total.csv"];
        SC_totals[label="SC_FP_total.csv"];
    }
    subgraph cluster_5_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_6_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/networks";
        get_street_network[label="streets.shp"];
    }
    subgraph cluster_7_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_conversion_systems[label="CONVERSION.xls"];
        get_database_distribution_systems[label="DISTRIBUTION.xls"];
        get_database_feedstocks[label="FEEDSTOCKS.xls"];
    }
    subgraph cluster_8_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_9_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="optimization/slave/gen_0";
        get_optimization_building_scale_heating_capacity[label="ind_1_building_scale_heating_capacity.csv"];
        get_optimization_district_scale_heating_capacity[label="ind_2_district_scale_heating_capacity.csv"];
        get_optimization_slave_total_performance[label="ind_2_total_performance.csv"];
    }
    subgraph cluster_10_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="optimization/slave/gen_1";
        get_optimization_building_scale_cooling_capacity[label="ind_0_building_scale_cooling_capacity.csv"];
        get_optimization_district_scale_cooling_capacity[label="ind_1_district_scale_cooling_capacity.csv"];
        get_optimization_generation_district_scale_performance[label="gen_1_district_scale_performance.csv"];
        get_optimization_slave_cooling_activation_pattern[label="ind_2_Cooling_Activation_Pattern.csv"];
        get_optimization_slave_district_scale_performance[label="ind_2_buildings_district_scale_performance.csv"];
        get_optimization_slave_electricity_activation_pattern[label="ind_1_Electricity_Activation_Pattern.csv"];
        get_optimization_slave_electricity_requirements_data[label="ind_1_Electricity_Requirements_Pattern.csv"];
    }
    subgraph cluster_11_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="optimization/slave/gen_2";
        get_optimization_district_scale_electricity_capacity[label="ind_0_district_scale_electrical_capacity.csv"];
        get_optimization_generation_building_scale_performance[label="gen_2_building_scale_performance.csv"];
        get_optimization_generation_total_performance[label="gen_2_total_performance.csv"];
        get_optimization_generation_total_performance_pareto[label="gen_2_total_performance_pareto.csv"];
        get_optimization_individuals_in_generation[label="generation_2_individuals.csv"];
        get_optimization_slave_building_connectivity[label="ind_1_building_connectivity.csv"];
        get_optimization_slave_building_scale_performance[label="ind_0_buildings_building_scale_performance.csv"];
        get_optimization_slave_heating_activation_pattern[label="ind_0_Heating_Activation_Pattern.csv"];
    }
    subgraph cluster_12_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_demand_results_file[label="B001.csv"];
        get_total_demand[label="Total_demand.csv"];
    }
    subgraph cluster_13_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/potentials";
        get_geothermal_potential[label="Shallow_geothermal_potential.csv"];
        get_sewage_heat_potential[label="Sewage_heat_potential.csv"];
        get_water_body_potential[label="Water_body_potential.csv"];
    }
    subgraph cluster_14_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/thermal-network";
        get_network_total_pressure_drop_file[label="DH__plant_pumping_pressure_loss_Pa.csv"];
        get_network_total_thermal_loss_file[label="DH__total_thermal_loss_edges_kW.csv"];
        get_thermal_network_edge_list_file[label="DH__metadata_edges.csv"];
    }
    PVT_totals -> "optimization"[label="(PVT_totals)"];
    PV_totals -> "optimization"[label="(PV_totals)"];
    SC_totals -> "optimization"[label="(SC_totals)"];
    get_database_conversion_systems -> "optimization"[label="(get_database_conversion_systems)"];
    get_database_distribution_systems -> "optimization"[label="(get_database_distribution_systems)"];
    get_database_feedstocks -> "optimization"[label="(get_database_feedstocks)"];
    get_demand_results_file -> "optimization"[label="(get_demand_results_file)"];
    get_geothermal_potential -> "optimization"[label="(get_geothermal_potential)"];
    get_network_total_pressure_drop_file -> "optimization"[label="(get_network_total_pressure_drop_file)"];
    get_network_total_thermal_loss_file -> "optimization"[label="(get_network_total_thermal_loss_file)"];
    get_optimization_decentralized_folder_building_cooling_activation -> "optimization"[label="(get_optimization_decentralized_folder_building_cooling_activation)"];
    get_optimization_decentralized_folder_building_result_cooling -> "optimization"[label="(get_optimization_decentralized_folder_building_result_cooling)"];
    get_optimization_decentralized_folder_building_result_heating -> "optimization"[label="(get_optimization_decentralized_folder_building_result_heating)"];
    get_optimization_decentralized_folder_building_result_heating_activation -> "optimization"[label="(get_optimization_decentralized_folder_building_result_heating_activation)"];
    get_optimization_network_results_summary -> "optimization"[label="(get_optimization_network_results_summary)"];
    get_optimization_substations_results_file -> "optimization"[label="(get_optimization_substations_results_file)"];
    get_sewage_heat_potential -> "optimization"[label="(get_sewage_heat_potential)"];
    get_street_network -> "optimization"[label="(get_street_network)"];
    get_thermal_network_edge_list_file -> "optimization"[label="(get_thermal_network_edge_list_file)"];
    get_total_demand -> "optimization"[label="(get_total_demand)"];
    get_water_body_potential -> "optimization"[label="(get_water_body_potential)"];
    get_weather_file -> "optimization"[label="(get_weather_file)"];
    get_zone_geometry -> "optimization"[label="(get_zone_geometry)"];
    "optimization" -> get_optimization_building_scale_cooling_capacity[label="(get_optimization_building_scale_cooling_capacity)"];
    "optimization" -> get_optimization_building_scale_heating_capacity[label="(get_optimization_building_scale_heating_capacity)"];
    "optimization" -> get_optimization_checkpoint[label="(get_optimization_checkpoint)"];
    "optimization" -> get_optimization_district_scale_cooling_capacity[label="(get_optimization_district_scale_cooling_capacity)"];
    "optimization" -> get_optimization_district_scale_electricity_capacity[label="(get_optimization_district_scale_electricity_capacity)"];
    "optimization" -> get_optimization_district_scale_heating_capacity[label="(get_optimization_district_scale_heating_capacity)"];
    "optimization" -> get_optimization_generation_building_scale_performance[label="(get_optimization_generation_building_scale_performance)"];
    "optimization" -> get_optimization_generation_district_scale_performance[label="(get_optimization_generation_district_scale_performance)"];
    "optimization" -> get_optimization_generation_total_performance[label="(get_optimization_generation_total_performance)"];
    "optimization" -> get_optimization_generation_total_performance_pareto[label="(get_optimization_generation_total_performance_pareto)"];
    "optimization" -> get_optimization_individuals_in_generation[label="(get_optimization_individuals_in_generation)"];
    "optimization" -> get_optimization_slave_building_connectivity[label="(get_optimization_slave_building_connectivity)"];
    "optimization" -> get_optimization_slave_building_scale_performance[label="(get_optimization_slave_building_scale_performance)"];
    "optimization" -> get_optimization_slave_cooling_activation_pattern[label="(get_optimization_slave_cooling_activation_pattern)"];
    "optimization" -> get_optimization_slave_district_scale_performance[label="(get_optimization_slave_district_scale_performance)"];
    "optimization" -> get_optimization_slave_electricity_activation_pattern[label="(get_optimization_slave_electricity_activation_pattern)"];
    "optimization" -> get_optimization_slave_electricity_requirements_data[label="(get_optimization_slave_electricity_requirements_data)"];
    "optimization" -> get_optimization_slave_heating_activation_pattern[label="(get_optimization_slave_heating_activation_pattern)"];
    "optimization" -> get_optimization_slave_total_performance[label="(get_optimization_slave_total_performance)"];
    "optimization" -> get_optimization_substations_total_file[label="(get_optimization_substations_total_file)"];
    }

shallow_geothermal_potential
----------------------------
.. graphviz::

    digraph shallow_geothermal_potential {
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
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/weather";
        get_weather_file[label="weather.epw"];
    }
    subgraph cluster_2_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/potentials";
        get_geothermal_potential[label="Shallow_geothermal_potential.csv"];
    }
    get_weather_file -> "shallow_geothermal_potential"[label="(get_weather_file)"];
    get_zone_geometry -> "shallow_geothermal_potential"[label="(get_zone_geometry)"];
    "shallow_geothermal_potential" -> get_geothermal_potential[label="(get_geothermal_potential)"];
    }

emissions
---------
.. graphviz::

    digraph emissions {
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
        label="inputs/building-geometry";
        get_zone_geometry[label="zone.shp"];
    }
    subgraph cluster_1_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/building-properties";
        get_building_architecture[label="architecture.dbf"];
        get_building_supply[label="supply_systems.dbf"];
        get_building_typology[label="typology.dbf"];
    }
    subgraph cluster_2_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/assemblies";
        get_database_supply_assemblies[label="SUPPLY.xls"];
    }
    subgraph cluster_3_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="inputs/technology/components";
        get_database_feedstocks[label="FEEDSTOCKS.xls"];
    }
    subgraph cluster_4_in {
        style = filled;
        color = "#E1F2F2";
        fontsize = 20;
        rank=same;
        label="outputs/data/demand";
        get_total_demand[label="Total_demand.csv"];
    }
    subgraph cluster_5_out {
        style = filled;
        color = "#aadcdd";
        fontsize = 20;
        rank=same;
        label="outputs/data/emissions";
        get_lca_embodied[label="Total_LCA_embodied.csv"];
        get_lca_mobility[label="Total_LCA_mobility.csv"];
        get_lca_operation[label="Total_LCA_operation.csv"];
    }
    get_building_architecture -> "emissions"[label="(get_building_architecture)"];
    get_building_supply -> "emissions"[label="(get_building_supply)"];
    get_building_typology -> "emissions"[label="(get_building_typology)"];
    get_database_feedstocks -> "emissions"[label="(get_database_feedstocks)"];
    get_database_supply_assemblies -> "emissions"[label="(get_database_supply_assemblies)"];
    get_total_demand -> "emissions"[label="(get_total_demand)"];
    get_zone_geometry -> "emissions"[label="(get_zone_geometry)"];
    "emissions" -> get_lca_embodied[label="(get_lca_embodied)"];
    "emissions" -> get_lca_mobility[label="(get_lca_mobility)"];
    "emissions" -> get_lca_operation[label="(get_lca_operation)"];
    }
