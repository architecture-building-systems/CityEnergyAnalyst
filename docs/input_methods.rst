
get_archetypes_properties
-------------------------

The following file is used by scripts: ['data_helper']



.. csv-table:: **inputs/technology/archetypes/construction_properties.xlsx:ARCHITECTURE**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/archetypes/construction_properties.xlsx:HVAC**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/archetypes/construction_properties.xlsx:INDOOR_COMFORT**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/archetypes/construction_properties.xlsx:INTERNAL_LOADS**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/archetypes/construction_properties.xlsx:SUPPLY**
    :header: "Variable", "Description"



get_building_age
----------------

The following file is used by scripts: ['data_helper', 'emissions', 'demand']



.. csv-table:: **inputs/building-properties/age.dbf**
    :header: "Variable", "Description"

     HVAC,Year of last retrofit of HVAC systems (0 if none) - Unit: [-]
     Name,Unique building ID. It must start with a letter. - Unit: [-]
     basement,Year of last retrofit of basement (0 if none) - Unit: [-]
     built,Construction year - Unit: [-]
     envelope,Year of last retrofit of building facades (0 if none) - Unit: [-]
     partitions,Year of last retrofit of internal wall partitions(0 if none) - Unit: [-]
     roof,Year of last retrofit of roof (0 if none) - Unit: [-]
     windows,Year of last retrofit of windows (0 if none) - Unit: [-]


get_building_occupancy
----------------------

The following file is used by scripts: ['data_helper', 'emissions', 'demand']



.. csv-table:: **inputs/building-properties/occupancy.dbf**
    :header: "Variable", "Description"

     COOLROOM,Refrigeration rooms - Unit: [m2]
     FOODSTORE,Food stores - Unit: [m2]
     GYM,Gymnasiums - Unit: [m2]
     HOSPITAL,Hospitals - Unit: [m2]
     HOTEL,Hotels - Unit: [m2]
     INDUSTRIAL,Light industry - Unit: [m2]
     LIBRARY,Libraries - Unit: [m2]
     MULTI_RES,Residential (multiple dwellings) - Unit: [m2]
     Name,Unique building ID. It must start with a letter. - Unit: [-]
     OFFICE,Offices - Unit: [m2]
     PARKING,Parking - Unit: [m2]
     RESTAURANT,Restaurants - Unit: [m2]
     RETAIL,Retail - Unit: [m2]
     SCHOOL,Schools - Unit: [m2]
     SERVERROOM,Data center - Unit: [m2]
     SINGLE_RES,Residential (single dwellings) - Unit: [m2]
     SWIMMING,Swimming halls - Unit: [m2]


get_database_air_conditioning_systems
-------------------------------------

The following file is used by scripts: ['demand']



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:controller**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:cooling**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:dhw**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:heating**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:ventilation**
    :header: "Variable", "Description"



get_database_envelope_systems
-----------------------------

The following file is used by scripts: ['schedule_maker', 'radiation', 'demand']



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:CONSTRUCTION**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:TIGHTNESS**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:ROOF**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:SHADING**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:WALL**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:WINDOW**
    :header: "Variable", "Description"



get_database_lca_buildings
--------------------------

The following file is used by scripts: ['emissions']



.. csv-table:: **inputs/technology/lifecycle/LCA_buildings.xlsx:EMBODIED_EMISSIONS**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/lifecycle/LCA_buildings.xlsx:EMBODIED_ENERGY**
    :header: "Variable", "Description"



get_database_lca_mobility
-------------------------

The following file is used by scripts: ['emissions', 'operation_costs']



.. csv-table:: **inputs/technology/lifecycle/LCA_mobility.xls:MOBILITY**
    :header: "Variable", "Description"



get_database_standard_schedules_use
-----------------------------------

The following file is used by scripts: ['data_helper']



.. csv-table:: **inputs/technology/archetypes/schedules/RESTAURANT.csv**
    :header: "Variable", "Description"



get_database_supply_systems
---------------------------

The following file is used by scripts: ['photovoltaic_thermal', 'decentralized', 'solar_collector', 'thermal_network', 'optimization', 'emissions', 'demand', 'photovoltaic', 'operation_costs']



.. csv-table:: **inputs/technology/systems/supply_systems.xls:BUNDLES**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:Absorption_chiller**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:BH**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:Boiler**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:CCGT**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:CT**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:Chiller**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:DETAILED_ELEC_PRICES**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:FC**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:FEEDSTOCKS**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:Furnace**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:HEX**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:HP**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:PIPING**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:PV**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:PVT**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:Pump**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:SC**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:TES**
    :header: "Variable", "Description"



get_optimization_thermal_network_data_file
------------------------------------------

The following file is used by scripts: ['optimization', 'optimization', 'optimization', 'optimization', 'optimization', 'optimization', 'optimization', 'optimization']



.. csv-table:: **outputs/data/optimization/network/DH_Network_summary_result_0x19b.csv**
    :header: "Variable", "Description"



get_street_network
------------------

The following file is used by scripts: ['optimization', 'network_layout']



.. csv-table:: **inputs/networks/streets.shp**
    :header: "Variable", "Description"

     geometry,TODO - Unit: TODO


get_surroundings_geometry
-------------------------

The following file is used by scripts: ['schedule_maker', 'radiation']



.. csv-table:: **inputs/building-geometry/surroundings.shp**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     floors_ag,Number of floors above ground (incl. ground floor) - Unit: [-]
     geometry,TODO - Unit: TODO
     height_ag,Height above ground (incl. ground floor) - Unit: [m]


get_terrain
-----------

The following file is used by scripts: ['schedule_maker', 'radiation']



.. csv-table:: **inputs/topography/terrain.tif**
    :header: "Variable", "Description"



get_weather
-----------

The following file is used by scripts: ['weather_helper']



.. csv-table:: **../../../../github/cityenergyanalyst/cea/databases/weather/Zug-inducity_1990_2010_TMY.epw**
    :header: "Variable", "Description"



get_zone_geometry
-----------------

The following file is used by scripts: ['schedule_maker', 'photovoltaic_thermal', 'decentralized', 'network_layout', 'radiation', 'demand', 'solar_collector', 'thermal_network', 'optimization', 'shallow_geothermal_potential', 'emissions', 'sewage_potential', 'data_helper', 'photovoltaic']



.. csv-table:: **inputs/building-geometry/zone.shp**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     floors_ag,Number of floors above ground (incl. ground floor) - Unit: [-]
     floors_bg,Number of floors below ground (basement, etc) - Unit: [-]
     geometry,TODO - Unit: TODO
     height_ag,Aggregated height of the walls. - Unit: [m]
     height_bg,Height below ground (basement, etc) - Unit: [m]

