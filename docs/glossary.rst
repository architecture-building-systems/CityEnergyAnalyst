Glossary
========
Zone Geometry
-------------
**Description**: This database consists of a shapefile storing the geometry of buildings in the zone of analysis. This database is useful to calculate the geometry and position of buildings, and as such, it is a key element in all CEA.

**Format/Naming**: Shape file / zone.shp

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_geometry/zone.shp

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                      | Valid Values |
+==========================+=========+======+==================================================+==============+
| Name                     | string  | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_ag                | float   | [m]  | Building total height above ground               | {0.1?.n}     |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_bg                | float   | [m]  | Building total height below ground               | {1?.n}       |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_ag                 | integer | [-]  | Number of building floors above ground           | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_bg                 | integer | [-]  | Number of building floors below  ground          | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------+--------------+

Zone Occupancy
--------------
**Description**: This database consists of a .dbf file storing shares of occupancy types in buildings in the zone of analysis. This database is useful to determine hourly patterns of occupancy of buildings in the area. CEA covers >15 different types of occupancy. Mix-use buildings are represented by different shares

**Format/Naming**: dataBase / occupancy.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/age.dbf

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                                            | Valid Values |
+==========================+========+=========+========================================================================+==============+
| Name                     | string | [-]     | Unique building ID. It must start with a letter.                       | -            |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| HOTEL                    | float  | [m2/m2] | Share (fraction of gross floor area) of hospitality area               | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| COOLROOM                 | float  | [m2/m2] | Share (fraction of gross floor area) of coolrooms                      | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| PARKING                  | float  | [m2/m2] | Share (fraction of gross floor area) of parking area                   | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SCHOOL                   | float  | [m2/m2] | Share (fraction of gross floor area) of school                         | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| OFFICE                   | float  | [m2/m2] | Share (fraction of gross floor area) of office space                   | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| GYM                      | float  | [m2/m2] | Share (fraction of gross floor area) of of gym space                   | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| HOSPITAL                 | float  | [m2/m2] | Share (fraction of gross floor area) of hospital area                  | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| INDUSTRIAL               | float  | [m2/m2] | Share (fraction of gross floor area) of industrial area                | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| RETAIL                   | float  | [m2/m2] | Share (fraction of gross floor area) of retail area                    | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| RESTAURANT               | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SINGLE_RES               | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| MULTI-RES                | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SERVERROOM               | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SWIMMING                 | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| FOODSTORE                | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| LIBRARY                  | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0?.1}     |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+

District Geometry
-----------------
**Description**: This database consists of a shapefile storing the geometry of buildings in the surroundings of the zone of analysis. This database is useful to calculate the radiation reflected from surrounding buildings into the zone of analysis.

**Format/Naming**: shapefile / district.shp

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_geometry/district.shp

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                      | Valid Values |
+==========================+=========+======+==================================================+==============+
| Name                     | string  | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_ag                | float   | [m]  | Building total height above ground               | {0.1?.n}     |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_bg                | float   | [m]  | Building total height below ground               | {1?.n}       |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_ag                 | integer | [-]  | Number of building floors above ground           | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_bg                 | integer | [-]  | Number of building floors below  ground          | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------+--------------+

Zone Weather
------------
**Description**: This database consists of a .epw file storing hourly data about the weather conditions of the zone of interest. This data is useful to estimate solar radiation on site, and the conditions of temperature and humidity of the air, as such, it is a key element of CEA.

**Format/Naming**: eplus file / zurich.epw

**Location (example)**: ..cea/databases/CH/weather/zurich.epw

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| <location>.epw           |      | [-]  |             |              |
+--------------------------+------+------+-------------+--------------+

Zone Supply
-----------
**Description**: This database consists of a .dbf file storing the type of heating, cooling and electrical supply systems of buildings in  the zone of analysis. This database is useful to calculate the emissions due to operation of buildings and their underlying infrastructure. 

**Format/Naming**: dataBase / supply_systems.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/age.dbf

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+------+---------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                                                                 | Valid Values |
+==========================+=========+======+=============================================================================================+==============+
| Name                     | string  | [-]  | Unique building ID. It must start with a letter.                                            | alphanumeric |
+--------------------------+---------+------+---------------------------------------------------------------------------------------------+--------------+
| type_el                  | string  | [-]  | Type of electrical supply system (relates to inputs in Default Database LCA_infrastructure) | {T0?.Tn}     |
+--------------------------+---------+------+---------------------------------------------------------------------------------------------+--------------+
| type_cs                  | string  | [-]  | Type of cooling supply system (relates to values  in Default Database LCA_infrastructure)   | {T0?.Tn}     |
+--------------------------+---------+------+---------------------------------------------------------------------------------------------+--------------+
| type_hs                  | string  | [-]  | Type of heating supply system (relates to values  in Default Database LCA_infrastructure)   | {T0?.Tn}     |
+--------------------------+---------+------+---------------------------------------------------------------------------------------------+--------------+
| type_dhw                 | integer | [-]  | Type of hot water supply system (relates to values in Default Database LCA_infrastructure)  | {T0?.Tn}     |
+--------------------------+---------+------+---------------------------------------------------------------------------------------------+--------------+

Zone Age
--------
**Description**: This database consists of a .dbf file storing the age of construction and years of renovation of different architectural components in buildings in the zone of analysis. This database is useful to estimate embodied and grey energy and emissions due to the construction and retrofit of buildings.

**Format/Naming**: dataBase / age.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/age.dbf

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                                  | Valid Values |
+==========================+=========+======+==============================================================+==============+
| Name                     | string  | [-]  | Unique building ID. It must start with a letter.             | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| built                    | integer | [-]  | Construction year                                            | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| roof                     | integer | [-]  | Year of last retrofit of roof (0 if none)                    | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| windows                  | integer | [-]  | Year of last retrofit of windows (0 if none)                 | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| partitions               | integer | [-]  | Year of last retrofit of internal wall partitions(0 if none) | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| HVAC                     | integer | [-]  | Year of last retrofit of HVAC systems  (0 if none)           | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| envelope                 | integer | [-]  | Year of last retrofit of building facades (0 if none)        | {0?.n}       |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+

District Terrain
----------------
**Description**: This database consists in a raster image with cells of 5m X 5m of resolution storing the elevation of the terrain in m. This database is useful to calculate the solar radiation reflected to buildings. 

**Format/Naming**: shapefile / district.tiff

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/terrain/terrain.tiff

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| terrain.tiff             | [-]  | [-]  | [-]         | [-]          |
+--------------------------+------+------+-------------+--------------+

Zone Architecture
-----------------
**Description**: This database consists of a .dbf file storing architectural properties of buildings in the zone of analysis. This database is useful to calculate the thermal properties of the building envelope and occupancy density, and as such, it is a key element in all CEA.

**Format/Naming**: dataBase / architecture.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/architecture.dbf

**Primary Interdependencies**: Secondary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit          | Description                                                                             | Valid Values |
+==========================+========+===============+=========================================================================================+==============+
| Name                     | string | [-]           | Unique building ID. It must start with a letter.                                        | -            |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| void_deck                | float  | [floor/floor] | Share of floors with an open envelope (default = 0)                                     | {0.0….1}     |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| Hs                       | float  | [m2/m2]       | Fraction of gross floor area air-conditioned.                                           | {0.0….1}     |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| wwr_x                    | float  | [m2/m2]       | Average window-to-wall area ratio in the cardinal direction x                           | {0.0….1}     |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| n50                      | float  | [1/h]         | Air exchanges per hour at a pressure of 50 Pa.                                          | {0.0….10}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_roof                | string | [-]           | Roof construction type (relates to values in Default Database Construction Properties)  | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_wall                | float  | [m2/m2]       | Wall construction type  (relates to values in Default Database Construction Properties) | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_win                 | float  | [m2/m2]       | Window type  (relates to values in Default Database Construction Properties)            | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_shade               | float  | [m2/m2]       | Shading system type  (relates to values in Default Database Construction Properties)    | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+

Internal Loads
--------------
**Description**: This database consists of a .dbf file storing internal thermal loads in buildings in the zone of analysis. This database is useful to calculate the heat released inside the building due to the use of appliances, people moving etc, as such, it is a key element of CEA

**Format/Naming**: dataBase / internal_loads.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/internal_loads.dbf

**Primary Interdependencies**: Secondary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit      | Description                                                         | Valid Values |
+==========================+========+===========+=====================================================================+==============+
| Name                     | string | [-]       | Unique building ID. It must start with a letter.                    | -            |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Qs_Wp                    | float  | [W/p]     | Sensible heat released by occupancy at peak conditions              | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| X_ghp                    | float  | [gh/kg/p] | Moisture released by occupancy at peak conditions                   | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ea_Wm2                   | float  | [W/m2]    | Peak specific electrical  load due to computers and devices         | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| El_Wm2                   | float  | [W/m2]    | Peak specific electrical  load due to artificial lighting           | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Epro_Wm2                 | string | [W/m2]    | Peak specific electrical load due to industrial processes           | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ere_Wm2                  | float  | [W/m2]    | Peak specific electrical load due to refrigeration                  | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ed_Wm2                   | float  | [W/m2]    | Peak specific electrical load due to servers/data centres           | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Vww_lpd                  | float  | [lpd]     | Peak specific daily hot water consumption                           | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Vw_lpd                   | float  | [lpd]     | Peak specific fresh water consumption (includes cold and hot water) | {0.0….n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+

Zone Indoor Comfort
-------------------
**Description**: This database consists of a .dbf file storing thresholds of thermal comfort necessary for buildings in the zone of analysis. This database is useful to set the upper and lower limits for heating or cooling a building, as such, it is a key element of CEA.

**Format/Naming**: dataBase / indoor_comfort.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/internal_loads.dbf

**Primary Interdependencies**: Secondary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                      | Valid Values |
+==========================+========+=======+==================================================+==============+
| Name                     | string | [-]   | Unique building ID. It must start with a letter. | -            |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ths_set_C                | float  | [C]   | Setpoint temperature for heating  system         | {0.0….n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ths_setb_C               | float  | [C]   | Setback point of temperature for heating system  | {0.0….n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Tcs_set_C                | float  | [C]   | Setpoint temperature for cooling system          | {0.0….n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Tcs_setb_C               | float  | [C]   | Setback point of temperature for cooling system  | {0.0….n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ve_lps                   | float  | [l/s] | IQ requirements of indoor ventilation per person | {0.0….n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+

Zone HVAC
---------
**Description**: This database consists of a .dbf file storing information of HVAC systems in buildings. This database is useful to know which type of technical system the building is using. Depending on the system, the energy demand of the building can be supplied in different ways.

**Format/Naming**: dataBase / technical_systems.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/technical_systems.dbf

**Primary Interdependencies**: Secondary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                                                                          | Valid Values |
+==========================+========+=========+======================================================================================================+==============+
| Name                     | string | [-]     | Unique building ID. It must start with a letter.                                                     | -            |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_cs                  | string | [-]     | Type of cooling system  (relates to values in Default Database HVAC Properties)                      | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_hs                  | string | [m2/m2] | Type of heating system  (relates to values in Default Database HVAC Properties)                      | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_dhw                 | string | [m2/m2] | Type of hot water system  (relates to values in Default Database HVAC Properties)                    | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_ctrl                | string | [m2/m2] | Type of heating and cooling control systems  (relates to values in Default Database HVAC Properties) | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_vent                | string | [m2/m2] | Type of ventilation strategy (relates to values in Default Database HVAC Properties)                 | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+

Construction Properties
-----------------------
**Description**: This database stores building properties of the Swiss building stock. This database  is useful to retrieve properties of buildings based on their construction year and age. 

**Format/Naming**: excel file / construction.xlsx

**Location (example)**: .../CH/archetypes/construction_properties.xlsx

**Primary Interdependencies**: None

**Secondary Interdependencies**: Receives data from the primary input databases of ?age? and ?occupancy?. Serves to produce all secondary input databases.


+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Column names /parameters | Type   | Unit | Description                                                                                                         | Valid Values                    |
+==========================+========+======+=====================================================================================================================+=================================+
| Name                     | string | [-]  | Unique building ID. It must start with a letter.                                                                    | alphanumeric                    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| building_use             | string | [-]  | Building use. It relates to the uses stored in the input database of  Zone_occupancy                                | Those stored in  Zone_occupancy |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| year_start               | int    | [yr] | Lower  limit of year interval where the building properties apply                                                   | {0...n}                         |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| year_end                 | int    | [yr] | Upper limit of year interval where the building properties apply                                                    | {0...n}                         |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| standard                 | string | [-]  | Letter representing whereas the field represent construction properties of a building as built ?C? or renovated ?R? | {?C? , ?R?}                     |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Hs                       | float  | [-]  | Fraction of heated space in building archetype                                                                      | {0.0...1}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| win_wall                 | float  | [-]  | Window to wall ratio in building archetype                                                                          | {0.0...1}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| type_cons                | string | [-]  | Type of construction. It relates to the contents of the default database of Envelope Properties: construction       | {T1...Tn}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| type_leak                | string | [-]  | Leakage level. It relates to the contents of the default database of Envelope Properties: leakage                   | {T1...Tn}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| type_win                 | string | [-]  | Window type. It relates to the contents of the default database of Envelope Properties: windows                     | {T1...Tn}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| type_roof                | string | [-]  | Roof construction. It relates to the contents of the default database of Envelope Properties: roof                  | {T1...Tn}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| type_wall                | string | [-]  | Wall construction. It relates to the contents of the default database of Envelope Properties: walll                 | {T1...Tn}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+
| type_shade               | string | [-]  | Shading system type. It relates to the contents of the default database of Envelope Properties: shade               | {T1...Tn}                       |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+---------------------------------+

Occupancy Schedules
-------------------
**Description**: This database in Excel stores information of schedules of occupancy, and use of hot water, lighting and other electrical appliances. Every tab in this excel file corresponds to a type of occupancy. This database is useful to calculate the demand of energy in buildings.

**Format/Naming**: excel file / occupancy_schedule.xlsx

**Location (example)**: .../CH/archetypes/occupancy_schedules.xlsx

**Primary Interdependencies**: Relates detailed data to the primary input database of Zone occupancy.

**Secondary Interdependencies**: None

+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                            | Valid Values |
+==========================+========+=======+========================================================+==============+
| Name                     | string | [-]   | Unique building ID. It must start with a letter.       | alphanumeric |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Weekday_1                | float  | [p/p] | Probability of maximum occupancy per hour in a weekday | {0.0?.1}     |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Saturday_1               | float  | [p/p] | Probability of maximum occupancy per hour on Saturday  | {0.0?.1}     |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Sunday_1                 | float  | [p/p] | Probability of maximum occupancy per hour on Sunday    | {0.0?.1}     |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+

System Controls
---------------
**Description**: This database in Excel stores information used to define the cooling and heating seasons for a given scenario.

**Format/Naming**: excel file / systems_controls.xlsx

**Location (example)**: .../CH/archetypes/systems_controls.xlsx

**Primary Interdependencies**: 

**Secondary Interdependencies**: Note: the heating and cooling seasons need to be non-overlapping and comprise the entire year.

+--------------------------+---------+------+----------------------------------------------------+---------------+
| Column names /parameters | Type    | Unit | Description                                        | Valid Values  |
+==========================+=========+======+====================================================+===============+
| has-heating-season       | Boolean | [-]  | Defines whether the scenario has a heating season. | {TRUE, FALSE} |
+--------------------------+---------+------+----------------------------------------------------+---------------+
| heating-season-start     | date    | [-]  | Day on which the heating season starts             | mm-dd         |
+--------------------------+---------+------+----------------------------------------------------+---------------+
| heating-season-end       | date    | [-]  | Last day of the heating season                     | mm-dd         |
+--------------------------+---------+------+----------------------------------------------------+---------------+
| has-cooling-season       | Boolean | [-]  | Defines whether the scenario has a cooling season. | {TRUE, FALSE} |
+--------------------------+---------+------+----------------------------------------------------+---------------+
| cooling-season-start     | date    | [-]  | Day on which the cooling season starts             | mm-dd         |
+--------------------------+---------+------+----------------------------------------------------+---------------+
| cooling-season-end       | date    | [-]  | Last day of the cooling season                     | mm-dd         |
+--------------------------+---------+------+----------------------------------------------------+---------------+

LCA Buildings: Embodies_Energy
------------------------------
**Description**: This database stores information for the Life Cycle Analysis of buildings due to their construction and dismantling. This database is useful to calculate the embodied emissions and grey energy of buildings.

**Format/Naming**: excel file / LCA_buidlings.xlsx

**Location (example)**: .../CH/lifecycle/LCA_buildings.xlsx

**Primary Interdependencies**: Relates detailed data to the primary input database of ‘age’ and ‘occupancy’

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
|                          |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

LCA Infrastructure
------------------
**Description**: This database stores information for the Life Cycle Analysis of energy infrastructure in buildings and districts. This database is useful to calculate the emissions and primary energy per unit of energy consumed in the area.

**Format/Naming**: excel file / LCA_infrastructure.xlsx

**Location (example)**: .../CH/lifecycle/LCA_infrastructure.xlsx

**Primary Interdependencies**: Relates detailed data to the primary input database of ‘supply_systems’

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
|                          |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

Emission Systems
----------------
**Description**: This database stores information of HVAC systems in buildings. This database is useful to calculate the performance of different HVAC systems and control systems in buildings.

**Format/Naming**: excel file / emission_systems.xlsx

**Location (example)**: .../systems/emission_systems.xlsx

**Primary Interdependencies**: Relates to the primary input database of Zone HVAC

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
|                          |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

Envelope Systems: Construction
------------------------------
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xlsx

**Location (example)**: .../systems/envelope_systems.xlsx

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: None

+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                                                              | Valid Values |
+==========================+========+=========+==========================================================================================+==============+
| description              | string | [-]     | Description of component                                                                 | -            |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]     | Unique ID of component in the construction category                                      | {T1..Tn}     |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+
| Cm_Af                    | float  | [J/Km2] | Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790. | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+

Envelope Systems: Leakage
-------------------------
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xlsx

**Location (example)**: .../systems/envelope_systems.xlsx

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: None

+--------------------------+--------+-------+------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                          | Valid Values |
+==========================+========+=======+======================================================+==============+
| description              | string | [-]   | Description of component                             | -            |
+--------------------------+--------+-------+------------------------------------------------------+--------------+
| code                     | string | [-]   | Unique ID of component in the leakage category       | {T1..Tn}     |
+--------------------------+--------+-------+------------------------------------------------------+--------------+
| n50                      | float  | [1/h] | Air exchanges due to leakage at a pressure of 50 Pa. | {0.0...n}    |
+--------------------------+--------+-------+------------------------------------------------------+--------------+

Envelope Systems: Window
------------------------
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xlsx

**Location (example)**: .../systems/envelope_systems.xlsx

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: None

+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                      | Valid Values |
+==========================+========+======+==================================================================================================+==============+
| description              | string | [-]  | Description of component                                                                         | -            |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]  | Unique ID of component in the window category                                                    | {T1..Tn}     |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| G_win                    | float  | [-]  | Solar heat gain coefficient. Defined according to ISO 13790.                                     | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| e_win                    | float  | [-]  | Emissivity of external surface. Defined according to ISO 13790.                                  | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| U_win                    | float  | [-]  | Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. | {0.1...n}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| rth_win                  | float  | [-]  | Reflectance in the Red spectrum.  Defined according Radiance. (long-wave)                        | {0....1}     |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| gtn_win                  | float  | [-]  | Reflectance in the Green spectrum.  Defined according Radiance. (medium-wave)                    | {0....1}     |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| btn_win                  | float  | [-]  | Reflectance in the Blue spectrum.  Defined according Radiance. (Short-wave)                      | {0....1}     |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+

Envelope Systems: Roof
----------------------
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xlsx

**Location (example)**: .../systems/envelope_systems.xlsx

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: 

+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                      | Valid Values |
+==========================+========+======+==================================================================================================+==============+
| description              | string | [-]  | Description of component                                                                         | -            |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]  | Unique ID of component in the window category                                                    | {T1..Tn}     |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| a_roof                   | float  | [-]  | Solar absorption coefficient. Defined according to ISO 13790.                                    | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| e_win                    | float  | [-]  | Emissivity of external surface. Defined according to ISO 13790.                                  | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| U_roof                   | float  | [-]  | Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. | {0.1...n}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| r_roof                   | float  | [-]  | Reflectance in the Red spectrum.  Defined according Radiance. (long-wave)                        | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| g_roof                   | float  | [-]  | Reflectance in the Green spectrum.  Defined according Radiance. (medium-wave)                    | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| b_roof                   | float  | [-]  | Reflectance in the Blue spectrum.  Defined according Radiance. (Short-wave)                      | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| spec_roof                | float  | [-]  | Specularity.  Defined according Radiance.                                                        | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| rough_roof               | float  | [-]  | roughness.  Defined according Radiance.                                                          | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+

Envelope Systems
----------------
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xlsx

**Location (example)**: .../systems/envelope_systems.xlsx

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: 

+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                      | Valid Values |
+==========================+========+======+==================================================================================================+==============+
| description              | string | [-]  | Description of component                                                                         | -            |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]  | Unique ID of component in the window category                                                    | {T1..Tn}     |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| a_wall                   | float  | [-]  | Solar absorption coefficient. Defined according to ISO 13790.                                    | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| e_wall                   | float  | [-]  | Emissivity of external surface. Defined according to ISO 13790.                                  | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| U_wall                   | float  | [-]  | Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. | {0.1...n}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| r_wall                   | float  | [-]  | Reflectance in the Red spectrum.  Defined according Radiance. (long-wave)                        | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| g_wall                   | float  | [-]  | Reflectance in the Green spectrum.  Defined according Radiance. (medium-wave)                    | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| b_wall                   | float  | [-]  | Reflectance in the Blue spectrum.  Defined according Radiance. (Short-wave)                      | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| spec_wall                | float  | [-]  | Specularity.  Defined according Radiance.                                                        | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| rough_wall               | float  | [-]  | roughness.  Defined according Radiance.                                                          | {0.0....1}   |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+

Envelope Systems: Shading
-------------------------
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xlsx

**Location (example)**: .../systems/envelope_systems.xlsx

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: 

+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                        | Valid Values |
+==========================+========+======+====================================================================================+==============+
| description              | string | [-]  | Description of component                                                           | -            |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]  | Unique ID of component in the window category                                      | {T1..Tn}     |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+
| rf_sh                    | float  | [-]  | Shading coefficient when shading device is active. Defined according to ISO 13790. | {0.0...1}    |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+

Uncertainty Distributions
-------------------------
**Description**: This database stores information of probability density functions of several input parameters of the CEA tool. This database is useful to perform a sensitivity analysis of input parameters and to calibrate to measured data.

**Format/Naming**: excel file / uncertainty_distributions.xlsx

**Location (example)**: .../cea/databases/uncertainty/uncertainty_distributions.xlsx

**Primary Interdependencies**: Relates detailed data to the secondary input database of ‘architecture’ through the contents of the default database of  ‘envelope_systems’. It also relates detailed data to the secondary input databases of ‘internal_loads and indoor_comfort’ 

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
|                          |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

