CEA Scripts
===========
CEA relies on a number of scripts to perform tasks, which may share dependencies.
This section aims to clarify the databases created or used by each script, along with the methods used
to access this data.


data-helper
-----------

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
    
radiation-daysim
----------------

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
    