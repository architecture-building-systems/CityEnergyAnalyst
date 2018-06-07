Primary Input Databases
-----------------------
Zone Geometry
^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of buildings in the zone of analysis. This database is useful to calculate the geometry and position of buildings, and as such, it is a key element in all CEA.

**Format/Naming**: shapefile / zone.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-geometry/zone.shp`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                      | Valid Values |
+==========================+=========+======+==================================================+==============+
| Name                     | string  | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_ag                | float   | [m]  | Building total height above ground               | {0.1...n}    |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_bg                | float   | [m]  | Building total height below ground               | {1.0...n}    |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_ag                 | integer | [-]  | Number of building floors above ground           | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_bg                 | integer | [-]  | Number of building floors below  ground          | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+

District Geometry
^^^^^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of buildings in the surroundings of the zone of analysis. This database is useful to calculate the radiation reflected from surrounding buildings into the zone of analysis.

**Format/Naming**: shapefile / district.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-geometry/zone.shp`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                      | Valid Values |
+==========================+=========+======+==================================================+==============+
| Name                     | string  | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_ag                | float   | [m]  | Building total height above ground               | {0.1...n}    |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Height_bg                | float   | [m]  | Building total height below ground               | {1.0...n}    |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_ag                 | integer | [-]  | Number of building floors above ground           | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| Floor_bg                 | integer | [-]  | Number of building floors below  ground          | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+

Building Metering
^^^^^^^^^^^^^^^^^
**Description**: 

**Format/Naming**: csv / B01.csv

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-geometry/zone.shp`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Column names /parameters | Type    | Unit            | Description                                                                                         | Valid Values        |
+==========================+=========+=================+=====================================================================================================+=====================+
| DATE                     | date    | [smalldatetime] | Time stamp for each day of the year ascending in hour intervals.                                    | YYYY-MM-DD hh:mm:ss |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Name                     | string  | [-]             | Unique building ID. It must start with a letter.                                                    | alphanumeric        |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| occ_pax                  | integer | [# of people]   | Describes the occupancy in terms of pax, an estimate number of people, for a given hour time stamp. | {0...n}             |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| QHf_kWh                  | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| QCf_kWh                  | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Ef_kWh                   | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qhsf_kWh                 | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qhs_kWh                  | float   | [kWh]           | Sensible heat load of the heating system                                                            | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qhs_lat_kWh              | float   | [kWh]           | Latent heat load of the heating system                                                              | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qhprof_kWh               | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qwwf_kWh                 | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qww_kWh                  | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qcsf_kWh                 | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qcs_kWh                  | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qcs_lat_kWh              | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qcref_kWh                | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Qcdataf_kWh              | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Ealf_kWh                 | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Eauxf_kWh                | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Ecaf_kWh                 | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Edataf_kWh               | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Eprof_kWh                | float   | [kWh]           |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Tshs_C                   | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Trhs_C                   | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Tscs_C                   | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Trcs_C                   | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Tsww_C                   | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Trww_C                   | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Tsref_C                  | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Trref_C                  | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Tsdata_C                 | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Trdata_C                 | float   | [C]             |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| Vw_m3                    | float   | [m3]            |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| mcphs_kWC                |         | [kW]            |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| mcpww_kWC                |         | [kW]            |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| mcpcs_kWC                |         | [kW]            |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| mcpref_kWC               |         | [kW]            |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+
| mcpdata_kWC              |         | [kW]            |                                                                                                     | {0.0?.n}            |
+--------------------------+---------+-----------------+-----------------------------------------------------------------------------------------------------+---------------------+

Zone Age
^^^^^^^^
**Description**: This database consists of a .dbf file storing the age of construction and years of renovation of different architectural components in buildings in the zone of analysis. This database is useful to estimate embodied and grey energy and emissions due to the construction and retrofit of buildings.

**Format/Naming**: dataBase / age.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/age.dbf`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                      | Valid Values |
+==========================+========+======+==================================================+==============+
| Name                     | string | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+--------+------+--------------------------------------------------+--------------+

Zone Architecture
^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing architectural properties of buildings in the zone of analysis. This database is useful to calculate the thermal properties of the building envelope and occupancy density, and as such, it is a key element in all CEA.

**Format/Naming**: dataBase / architecture.dbf

**Location (example)**: ``  ..cea/examples/reference-case-open/baseline/inputs/building_properties/architecture.dbf`` 

**Primary Interdependencies**: Secondary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit          | Description                                                                             | Valid Values |
+==========================+========+===============+=========================================================================================+==============+
| Name                     | string | [-]           | Unique building ID. It must start with a letter.                                        | alphanumeric |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| void_deck                | float  | [floor/floor] | Share of floors with an open envelope (default = 0)                                     | {0.0?.1}     |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| Hs                       | float  | [m2/m2]       | Fraction of gross floor area air-conditioned.                                           | {0.0?.1}     |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| wwr_x                    | float  | [m2/m2]       | Average window-to-wall area ratio in the cardinal direction x                           | {0.0?.1}     |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| n50                      | float  | [1/h]         | Air exchanges per hour at a pressure of 50 Pa.                                          | {0.0?.10}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_roof                | string | [-]           | Roof construction type (relates to values in Default Database Construction Properties)  | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_wall                | float  | [m2/m2]       | Wall construction type ÿ(relates to values in Default Database Construction Properties) | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_win                 | float  | [m2/m2]       | Window type ÿ(relates to values in Default Database Construction Properties)            | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+
| type_shade               | float  | [m2/m2]       | Shading system type ÿ(relates to values in Default Database Construction Properties)    | {T1...Tn}    |
+--------------------------+--------+---------------+-----------------------------------------------------------------------------------------+--------------+

Zone Indoor Comfort
^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing thresholds of thermal comfort necessary for buildings in the zone of analysis. This database is useful to set the upper and lower limits for heating or cooling a building, as such, it is a key element of CEA.

**Format/Naming**: dataBase / indoor_comfort.dbf

**Location (example)**:  `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/internal_loads.dbf``

**Primary Interdependencies**: Secondary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                      | Valid Values |
+==========================+========+=======+==================================================+==============+
| Name                     | string | [-]   | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ths_set_C                | float  | [C]   | Setpoint temperature for heating ÿsystem         | {0.0?.n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ths_setb_C               | float  | [C]   | Setback point of temperature for heating system  | {0.0?.n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Tcs_set_C                | float  | [C]   | Setpoint temperature for cooling system          | {0.0?.n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Tcs_setb_C               | float  | [C]   | Setback point of temperature for cooling system  | {0.0?.n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ve_lps                   | float  | [l/s] | IQ requirements of indoor ventilation per person | {0.0?.n}     |
+--------------------------+--------+-------+--------------------------------------------------+--------------+

Internal Loads
^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing internal thermal loads in buildings in the zone of analysis. This database is useful to calculate the heat released inside the building due to the use of appliances, people moving etc, as such, it is a key element of CEA

**Format/Naming**: dataBase / internal_loads.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/internal_loads.dbf`` 

**Primary Interdependencies**: Secondary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit      | Description                                                         | Valid Values |
+==========================+========+===========+=====================================================================+==============+
| Name                     | string | [-]       | Unique building ID. It must start with a letter.                    | alphanumeric |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Qs_Wp                    | float  | [W/p]     | Sensible heat released by occupancy at peak conditions              | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| X_ghp                    | float  | [gh/kg/p] | Moisture released by occupancy at peak conditions                   | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ea_Wm2                   | float  | [W/m2]    | Peak specific electrical ÿload due to computers and devices         | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| El_Wm2                   | float  | [W/m2]    | Peak specific electrical ÿload due to artificial lighting           | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Epro_Wm2                 | string | [W/m2]    | Peak specific electrical load due to industrial processes           | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ere_Wm2                  | float  | [W/m2]    | Peak specific electrical load due to refrigeration                  | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ed_Wm2                   | float  | [W/m2]    | Peak specific electrical load due to servers/data centres           | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Vww_lpd                  | float  | [lpd]     | Peak specific daily hot water consumption                           | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Vw_lpd                   | float  | [lpd]     | Peak specific fresh water consumption (includes cold and hot water) | {0.0?.n}     |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+

Zone Occupancy
^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing shares of occupancy types in buildings in the zone of analysis. This database is useful to determine hourly patterns of occupancy of buildings in the area. CEA covers >15 different types of occupancy. Mix-use buildings are represented by different shares

**Format/Naming**: dataBase / occupancy.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/age.dbf`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                                            | Valid Values |
+==========================+========+=========+========================================================================+==============+
| Name                     | string | [-]     | Unique building ID. It must start with a letter.                       | -            |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| HOTEL                    | float  | [m2/m2] | Share (fraction of gross floor area) of hospitality area               | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| COOLROOM                 | float  | [m2/m2] | Share (fraction of gross floor area) of coolrooms                      | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| PARKING                  | float  | [m2/m2] | Share (fraction of gross floor area) of parking area                   | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SCHOOL                   | float  | [m2/m2] | Share (fraction of gross floor area) of school                         | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| OFFICE                   | float  | [m2/m2] | Share (fraction of gross floor area) of office space                   | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| GYM                      | float  | [m2/m2] | Share (fraction of gross floor area) of of gym space                   | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| HOSPITAL                 | float  | [m2/m2] | Share (fraction of gross floor area) of hospital area                  | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| INDUSTRIAL               | float  | [m2/m2] | Share (fraction of gross floor area) of industrial area                | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| RETAIL                   | float  | [m2/m2] | Share (fraction of gross floor area) of retail area                    | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| RESTAURANT               | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SINGLE_RES               | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| MULTI-RES                | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SERVERROOM               | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| SWIMMING                 | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| FOODSTORE                | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+
| LIBRARY                  | float  | [m2/m2] | Share (fraction of gross floor area) of this occupancy in the building | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------+--------------+

Restrictions
^^^^^^^^^^^^
**Description**: 

**Format/Naming**: dataBase / restrictions.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-properties/restrictions.dbf`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+---------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                      | Valid Values |
+==========================+=========+======+==================================================+==============+
| NAME                     | string  | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| SOLAR                    | integer | [-]  |                                                  | {0?n}        |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| GEOTHERMAL               | integer | [-]  |                                                  | {0?n}        |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| WATERBODY                | integer | [-]  |                                                  | {0?n}        |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| NATURALGAS               | integer | [-]  |                                                  | {0?n}        |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| BIOGAS                   | integer | [-]  |                                                  | {0?n}        |
+--------------------------+---------+------+--------------------------------------------------+--------------+

Secondary Input Database
------------------------
Supply Systems
^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing the type of heating, cooling and electrical supply systems of buildings in ÿthe zone of analysis. This database is useful to calculate the emissions due to operation of buildings and their underlying infrastructure. 

**Format/Naming**: dataBase / supply_systems.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-properties/supply_systems.dbf`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+--------+------+---------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                 | Valid Values |
+==========================+========+======+=============================================================================================+==============+
| Name                     | string | [-]  | Unique building ID. It must start with a letter.                                            | alphanumeric |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------+--------------+
| type_cs                  | string | [-]  | Type of cooling supply system (relates to values  in Default Database LCA_infrastructure)   | {T0...Tn}    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------+--------------+
| type_hs                  | string | [-]  | Type of heating supply system (relates to values  in Default Database LCA_infrastructure)   | {T0...Tn}    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------+--------------+
| type_dhw                 | string | [-]  | Type of hot water supply system (relates to values in Default Database LCA_infrastructure)  | {T0...Tn}    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------+--------------+
| type_el                  | string | [-]  | Type of electrical supply system (relates to inputs in Default Database LCA_infrastructure) | {T0...Tn}    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------+--------------+

Zone HVAC
^^^^^^^^^
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
| type_cs                  | string | [-]     | Type of cooling system ÿ(relates to values in Default Database HVAC Properties)                      | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_hs                  | string | [m2/m2] | Type of heating system ÿ(relates to values in Default Database HVAC Properties)                      | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_dhw                 | string | [m2/m2] | Type of hot water system ÿ(relates to values in Default Database HVAC Properties)                    | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_ctrl                | string | [m2/m2] | Type of heating and cooling control systems ÿ(relates to values in Default Database HVAC Properties) | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+
| type_vent                | string | [m2/m2] | Type of ventilation strategy (relates to values in Default Database HVAC Properties)                 | {T1...Tn}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------------------+--------------+

District Cooling Network
^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of cooling networks in the surroundings of the zone of analysis. This database is useful to calculate ???

**Format/Naming**: Shapefile / edges.shp, nodes.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/networks/DC/edges.shp ``  and `` ..cea/examples/reference-case-open/baseline/inputs/networks/DC/nodes.shp ``

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| ??                       | ??   | ??   | ??          |              |
+--------------------------+------+------+-------------+--------------+

District Heating Network
^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of heating networks in the surroundings of the zone of analysis. This database is useful to calculate ???

**Format/Naming**: Shapefile / edges.shp, nodes.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/networks/DH/edges.shp ``  and `` ..cea/examples/reference-case-open/baseline/inputs/networks/DH/nodes.shp ``

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| ??                       | ??   | ??   | ??          |              |
+--------------------------+------+------+-------------+--------------+

District Topography
^^^^^^^^^^^^^^^^^^^
**Description**: This database consists in a raster image with cells of 5m X 5m of resolution storing the elevation of the topography in m. This database is useful to calculate the solar radiation reflected to buildings. 

**Format/Naming**: shapefile / district.tiff

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/topography/terrain.tiff `` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| terrain.tiff             | [-]  | [-]  | [-]         | [-]          |
+--------------------------+------+------+-------------+--------------+

Zone Weather
^^^^^^^^^^^^
**Description**: This database consists of a .epw file storing hourly data about the weather conditions of the zone of interest. This data is useful to estimate solar radiation on site, and the conditions of temperature and humidity of the air, as such, it is a key element of CEA.

**Format/Naming**: eplus file / zurich.epw

**Location (example)**: `` ..cea/databases/CH/weather/zurich.epw`` 

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| <location>.epw           |      | [-]  | [-]         | [-]          |
+--------------------------+------+------+-------------+--------------+

Construction Properties
^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores building properties of the Swiss building stock. This database  is useful to retrieve properties of buildings based on their construction year and age. 

**Format/Naming**: excel file / construction.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/construction_properties.xlsx `` 

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
^^^^^^^^^^^^^^^^^^^
**Description**: This database in Excel stores information of schedules of occupancy, and use of hot water, lighting and other electrical appliances. Every tab in this excel file corresponds to a type of occupancy. This database is useful to calculate the demand of energy in buildings.

**Format/Naming**: excel file / occupancy_schedule.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/occupancy_schedules.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of Zone occupancy.

**Secondary Interdependencies**: None

+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                            | Valid Values |
+==========================+========+=======+========================================================+==============+
| Name                     | string | [-]   | Unique building ID. It must start with a letter.       | alphanumeric |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Weekday_1                | float  | [p/p] | Probability of maximum occupancy per hour in a weekday | {0.0...1}    |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Saturday_1               | float  | [p/p] | Probability of maximum occupancy per hour on Saturday  | {0.0...1}    |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+
| Sunday_1                 | float  | [p/p] | Probability of maximum occupancy per hour on Sunday    | {0.0...1}    |
+--------------------------+--------+-------+--------------------------------------------------------+--------------+

System Controls
^^^^^^^^^^^^^^^
**Description**: This database in Excel stores information used to define the cooling and heating seasons for a given scenario.

**Format/Naming**: excel file / systems_controls.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/systems_controls.xlsx ``

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

Benchmarks
^^^^^^^^^^
**Description**: This database in Excel stores information used to define the characteristics of a benchmark from which comparisons are made considering the modelled performance.

**Format/Naming**: excel file / benchmark_2000W.xlsx

**Location (example)**: `` cea/databases/CH/benchmarks/benchmark_2000W.xlsx ``

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+------+---------------------------------------------------------+---------------+
| Column names /parameters | Type   | Unit | Description                                             | Valid Values  |
+==========================+========+======+=========================================================+===============+
| code                     | string | [-]  | Defines the function of a particular building typology. | [e.g. OFFICE] |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| NRE_today                | float  | [-]  | Net real emissions                                      | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| CO2_today                | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| PEN_today                | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| NRE_target_retrofit      | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| CO2_target_retrofit      | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| PEN_target_retrofit      | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| NRE_target_new           | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| CO2_target_new           | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| PEN_target_new           | float  | [-]  |                                                         | {0.0?.n}      |
+--------------------------+--------+------+---------------------------------------------------------+---------------+
| Description              |        | [-]  | Describes the source of the benchmark standards.        | [-]           |
+--------------------------+--------+------+---------------------------------------------------------+---------------+

Supply Costs
^^^^^^^^^^^^
**Description**: This database contains the schedule for various conduits, relating pipe nominal diameter (DN) to investment cost. This is helful for approximating the costs of hydraulic networks.

**Format/Naming**: excel file / supply_systems.xls

**Location (example)**: `` cea/databases/CH/economics/supply_systems.xls ``

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+------+-------------+--------------+
| Column names /parameters | Type   | Unit | Description | Valid Values |
+==========================+========+======+=============+==============+
| Description              | string | [-]  |             |              |
+--------------------------+--------+------+-------------+--------------+
| Diameter_max             | float  | [-]  |             |              |
+--------------------------+--------+------+-------------+--------------+
| Diameter_min             | float  | [-]  |             |              |
+--------------------------+--------+------+-------------+--------------+
| Unit                     | string | [-]  |             |              |
+--------------------------+--------+------+-------------+--------------+
| Investment               | float  | [-]  |             |              |
+--------------------------+--------+------+-------------+--------------+
| Currency                 | string | [-]  |             |              |
+--------------------------+--------+------+-------------+--------------+

LCA Buildings: EMBODIED_ENERGY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information for the Life Cycle Analysis of buildings due to their construction and dismantling. This database is useful to calculate the embodied emissions and grey energy of buildings.

**Format/Naming**: excel file / LCA_buidlings.xlsx

**Location (example)**: `` cea/databases/CH/lifecycle/LCA_buildings.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of ?age? and ?occupancy?

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| building_use             |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| year_start               |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| year_end                 |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| standard                 |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_ext_ag              |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_ext_bg              |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Floor_int                |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_int_sup             |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_int_nosup           |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Roof                     |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Floor_g                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Services                 |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Win_ext                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Excavation               |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

LCA Buildings: EMBODIED_EMISSIONS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information for the Life Cycle Analysis of buildings due to their construction and dismantling. This database is useful to calculate the embodied emissions and grey energy of buildings.

**Format/Naming**: excel file / LCA_buidlings.xlsx

**Location (example)**: `` cea/databases/CH/lifecycle/LCA_buildings.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of ?age? and ?occupancy?

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| building_use             |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| year_start               |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| year_end                 |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| standard                 |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_ext_ag              |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_ext_bg              |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Floor_int                |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_int_sup             |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Wall_int_nosup           |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Roof                     |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Floor_g                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Services                 |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Win_ext                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Excavation               |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

LCA Infrastructure
^^^^^^^^^^^^^^^^^^
**Description**: This database stores information for the Life Cycle Analysis of energy infrastructure in buildings and districts. This database is useful to calculate the emissions and primary energy per unit of energy consumed in the area.

**Format/Naming**: excel file / LCA_infrastructure.xlsx

**Location (example)**: `` cea/databases/CH/lifecycle/LCA_infrastructure.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of ?supply_systems?

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| Description              |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| code                     |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| PEN                      |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| CO2                      |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| costs_kWh                |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

Emission Systems
^^^^^^^^^^^^^^^^
**Description**: This database stores information of HVAC systems in buildings. This database is useful to calculate the performance of different HVAC systems and control systems in buildings.

**Format/Naming**: excel file / emission_systems.xlsx

**Location (example)**: `` cea/databases/systems/emission_systems.xls`` 

**Primary Interdependencies**: Relates to the primary input database of Zone HVAC

**Secondary Interdependencies**: None

+--------------------------+--------+-------+-------------+--------------+
| Column names /parameters | Type   | Unit  | Description | Valid Values |
+==========================+========+=======+=============+==============+
| Description              | string | [-]   |             | [-]          |
+--------------------------+--------+-------+-------------+--------------+
| code                     | string | [-]   |             | {T0...Tn}    |
+--------------------------+--------+-------+-------------+--------------+
| Tsww0_C                  | float  | [C]   |             | {0.0?.n}     |
+--------------------------+--------+-------+-------------+--------------+
| Qwwmax_Wm2               | float  | [Wm2] |             | {0.0?.n}     |
+--------------------------+--------+-------+-------------+--------------+

Envelope Systems: Construction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xls

**Location (example)**: `` cea/databases/systems/envelope_systems.xlsx`` 

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: None

+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                                                              | Valid Values |
+==========================+========+=========+==========================================================================================+==============+
| description              | string | [-]     | Description of component                                                                 | [-]          |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]     | Unique ID of component in the construction category                                      | {T1..Tn}     |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+
| Cm_Af                    | float  | [J/Km2] | Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790. | {0.0...1}    |
+--------------------------+--------+---------+------------------------------------------------------------------------------------------+--------------+

Envelope Systems: Leakage
^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xls

**Location (example)**: `` cea/databases/systems/envelope_systems.xlsx`` 

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: None

+--------------------------+--------+-------+------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                          | Valid Values |
+==========================+========+=======+======================================================+==============+
| description              | string | [-]   | Description of component                             | [-]          |
+--------------------------+--------+-------+------------------------------------------------------+--------------+
| code                     | string | [-]   | Unique ID of component in the leakage category       | {T1..Tn}     |
+--------------------------+--------+-------+------------------------------------------------------+--------------+
| n50                      | float  | [1/h] | Air exchanges due to leakage at a pressure of 50 Pa. | {0.0...n}    |
+--------------------------+--------+-------+------------------------------------------------------+--------------+

Envelope Systems: Window
^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xls

**Location (example)**: `` cea/databases/systems/envelope_systems.xlsx`` 

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: None

+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                      | Valid Values |
+==========================+========+======+==================================================================================================+==============+
| description              | string | [-]  | Description of component                                                                         | [-]          |
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
^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xls

**Location (example)**: `` cea/databases/systems/envelope_systems.xlsx`` 

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: 

+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                      | Valid Values |
+==========================+========+======+==================================================================================================+==============+
| description              | string | [-]  | Description of component                                                                         | [-]          |
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
^^^^^^^^^^^^^^^^
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xls

**Location (example)**: `` cea/databases/systems/envelope_systems.xlsx`` 

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: 

+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                      | Valid Values |
+==========================+========+======+==================================================================================================+==============+
| description              | string | [-]  | Description of component                                                                         | [-]          |
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
^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information with detailed properties of components of the building envelope. This database is useful to calculate the thermal demand of energy in buildings.

**Format/Naming**: excel file / envelope_systems.xls

**Location (example)**: `` cea/databases/systems/envelope_systems.xlsx`` 

**Primary Interdependencies**: Relates to the primary input database of Zone architecture

**Secondary Interdependencies**: 

+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                        | Valid Values |
+==========================+========+======+====================================================================================+==============+
| description              | string | [-]  | Description of component                                                           | [-]          |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]  | Unique ID of component in the window category                                      | {T1..Tn}     |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+
| rf_sh                    | float  | [-]  | Shading coefficient when shading device is active. Defined according to ISO 13790. | {0.0...1}    |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+

Thermal Networks
^^^^^^^^^^^^^^^^
**Description**: 

**Format/Naming**: excel file / thermal_networks.xls

**Location (example)**: `` cea/databases/systems/thermal_networks.xls`` 

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| Pipe_DN                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| D_ext_m                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| D_int_m                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| D_ins_m                  |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Vdot_min_m3s             |      |      |             |              |
+--------------------------+------+------+-------------+--------------+
| Vdot_max_m3s             |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

Uncertainty Distributions
^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information of probability density functions of several input parameters of the CEA tool. This database is useful to perform a sensitivity analysis of input parameters and to calibrate to measured data.

**Format/Naming**: excel file / uncertainty_distributions.xlsx

**Location (example)**: .../cea/databases/uncertainty/uncertainty_distributions.xlsx

**Primary Interdependencies**: Relates detailed data to the secondary input database of ?architecture? through the contents of the default database of ÿ?envelope_systems?. It also relates detailed data to the secondary input databases of ?internal_loads and indoor_comfort? 

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| name                     |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

