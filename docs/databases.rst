
Input Databases
---------------
Primary: Zone Geometry
^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of buildings in the zone of analysis. This database is useful to calculate the geometry and position of buildings, and as such, it is a key element in all CEA.

**Format/Naming**: shapefile / zone.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-geometry/zone.shp`` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

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
| Floor_bg                 | integer | [-]  | Number of building floors below ground           | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+

Primary: District Geometry
^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of buildings in the surroundings of the zone of analysis. This database is useful to calculate the radiation reflected from surrounding buildings into the zone of analysis.

**Format/Naming**: shapefile / district.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-geometry/zone.shp`` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

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
| Floor_bg                 | integer | [-]  | Number of building floors below ground           | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+

Building Metering
^^^^^^^^^^^^^^^^^
**Description**: 

**Format/Naming**: csv / B01.csv

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-geometry/zone.shp`` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Column names /parameters | Type    | Unit            | Description                                                                     | Valid Values        |
+==========================+=========+=================+=================================================================================+=====================+
| DATE                     | date    | [smalldatetime] | Time stamp for each day of the year ascending in hour intervals.                | YYYY-MM-DD hh:mm:ss |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Name                     | string  | [-]             | Unique building ID. It must start with a letter.                                | alphanumeric        |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| occ_pax                  | integer | [# of people]   | Describes the occupancy in terms of pax for a given hour time stamp.            | {0...n}             |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| QHf_kWh                  | float   | [kWh]           | final heating demand Qhsf+Qwwf (hourly-total-peak)                              | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| QCf_kWh                  | float   | [kWh]           | final cooling demand (hourly-total-peak) Qcsf + Qcref + Qcdataf                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Ef_kWh                   | float   | [kWh]           | final electricity demand (hourly-total-peak)                                    | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qhsf_kWh                 | float   | [kWh]           | final space heating demand (hourly-total-peak)                                  | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qhs_kWh                  | float   | [kWh]           | Useful space heating demand (hourly-total-peak)                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qhs_lat_kWh              | float   | [kWh]           | Latent heat load of the heating system                                          | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qhprof_kWh               | float   | [kWh]           |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qwwf_kWh                 | float   | [kWh]           | final heating demand due to domsetic hot water consumption (hourly-total-peak)  | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qww_kWh                  | float   | [kWh]           | useful heating demand due to domestic hot water consumption (hourly-total-peak) | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qcsf_kWh                 | float   | [kWh]           | final space cooling demand (hourly-total-peak)                                  | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qcs_kWh                  | float   | [kWh]           | useful space cooling demand (hourly-total-peak)                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qcs_lat_kWh              | float   | [kWh]           |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qcref_kWh                | float   | [kWh]           | final cooling demand for refrigeration (hourly-total-peak)                      | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Qcdataf_kWh              | float   | [kWh]           | final cooling demand for servers' cooling (hourly-total-peak)                   | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Ealf_kWh                 | float   | [kWh]           | final appliances and lighting demand (hourly-total-peak)                        | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Eauxf_kWh                | float   | [kWh]           | final auxiliary electriciy use (hourly-total-peak)                              | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Ecaf_kWh                 | float   | [kWh]           |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Edataf_kWh               | float   | [kWh]           | final electricty consumption in data centers (houlry-total-peak)                | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Eprof_kWh                | float   | [kWh]           |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Tshs_C                   | float   | [C]             | temperature of supply space heating systems (hourly-peak)                       | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Trhs_C                   | float   | [C]             | temperature of return space heating systems (hourly-peak)                       | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Tscs_C                   | float   | [C]             | temperature of supply space cooling systems (hourly-peak)                       | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Trcs_C                   | float   | [C]             | temperature of return space cooling systems (hourly-peak)                       | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Tsww_C                   | float   | [C]             | temperature of supply domestic hot water systems (hourly-peak)                  | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Trww_C                   | float   | [C]             | temperature of return domestic hot water systems (hourly-peak)                  | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Tsref_C                  | float   | [C]             |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Trref_C                  | float   | [C]             |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Tsdata_C                 | float   | [C]             |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Trdata_C                 | float   | [C]             |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| Vw_m3                    | float   | [m3]            |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| mcphs_kWC                | float   | [kW]            | capacity flow rate of space heating systems (hourly and peak)                   | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| mcpww_kWC                |         | [kW]            | capacity flow rate of domestic hot water systems (hourly and peak)              | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| mcpcs_kWC                |         | [kW]            | capacity flow rate of space cooling systems (hourly and peak)                   | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| mcpref_kWC               |         | [kW]            |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+
| mcpdata_kWC              |         | [kW]            |                                                                                 | {0.0...n}           |
+--------------------------+---------+-----------------+---------------------------------------------------------------------------------+---------------------+

Primary: Zone Age
^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing the age of construction and years of renovation of different architectural components in buildings in the zone of analysis. This database is useful to estimate embodied and grey energy and emissions due to the construction and retrofit of buildings.

**Format/Naming**: dataBase / age.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/age.dbf

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                                  | Valid Values |
+==========================+=========+======+==============================================================+==============+
| Name                     | string  | [-]  | Unique building ID. It must start with a letter.             | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| built                    | integer | [-]  | Construction year                                            | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| roof                     | integer | [-]  | Year of last retrofit of roof (0 if none)                    | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| windows                  | integer | [-]  | Year of last retrofit of windows (0 if none)                 | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| partitions               | integer | [-]  | Year of last retrofit of internal wall partitions(0 if none) | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| HVAC                     | integer | [-]  | Year of last retrofit of HVAC systems (0 if none)            | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| envelope                 | integer | [-]  | Year of last retrofit of building facades (0 if none)        | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
| basement                 | integer | [-]  | Year of last retrofit of basement (0 if none)                | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+
|                          |         |      |                                                              |              |
+--------------------------+---------+------+--------------------------------------------------------------+--------------+

Secondary: Zone Architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing architectural properties of buildings in the zone of analysis. This database is useful to calculate the thermal properties of the building envelope and occupancy density, and as such, it is a key element in all CEA.

**Format/Naming**: dataBase / architecture.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/architecture.dbf`` 

**Primary Interdependencies**: Default Databases

**Secondary Interdependencies**: 

+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit          | Description                                                                            | Valid Values |
+==========================+========+===============+========================================================================================+==============+
| Name                     | string | [-]           | Unique building ID. It must start with a letter.                                       | alphanumeric |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| void_deck                | float  | [floor/floor] | Share of floors with an open envelope (default = 0)                                    | {0.0...1}    |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| Hs                       | float  | [m2/m2]       | Fraction of gross floor area air-conditioned.                                          | {0.0...1}    |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| wwr_x                    | float  | [m2/m2]       | Average window-to-wall area ratio in the cardinal direction x                          | {0.0...1}    |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| n50                      | float  | [1/h]         | Air exchanges per hour at a pressure of 50 Pa.                                         | {0.0...10}   |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| type_roof                | string | [-]           | Roof construction type (relates to values in Default Database Construction Properties) | {T1...Tn}    |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| type_wall                | float  | [m2/m2]       | Wall construction type (relates to values in Default Database Construction Properties) | {T1...Tn}    |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| type_win                 | float  | [m2/m2]       | Window type (relates to values in Default Database Construction Properties)            | {T1...Tn}    |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+
| type_shade               | float  | [m2/m2]       | Shading system type (relates to values in Default Database Construction Properties)    | {T1...Tn}    |
+--------------------------+--------+---------------+----------------------------------------------------------------------------------------+--------------+

Secondary: Zone Indoor Comfort
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing thresholds of thermal comfort necessary for buildings in the zone of analysis. This database is useful to set the upper and lower limits for heating or cooling a building, as such, it is a key element of CEA.

**Format/Naming**: dataBase / indoor_comfort.dbf

**Location (example)**:  `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/internal_loads.dbf``

**Primary Interdependencies**: Default Databases

**Secondary Interdependencies**: 

+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                      | Valid Values |
+==========================+========+=======+==================================================+==============+
| Name                     | string | [-]   | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ths_set_C                | float  | [C]   | Setpoint temperature for heating system          | {0.0...n}    |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ths_setb_C               | float  | [C]   | Setback point of temperature for heating system  | {0.0...n}    |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Tcs_set_C                | float  | [C]   | Setpoint temperature for cooling system          | {0.0...n}    |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Tcs_setb_C               | float  | [C]   | Setback point of temperature for cooling system  | {0.0...n}    |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| Ve_lps                   | float  | [l/s] | IQ requirements of indoor ventilation per person | {0.0...n}    |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| rhum_min_p               |        |       |                                                  |              |
+--------------------------+--------+-------+--------------------------------------------------+--------------+
| rhum_max_p               |        |       |                                                  |              |
+--------------------------+--------+-------+--------------------------------------------------+--------------+

Secondary: Zone Internal Loads
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing internal thermal loads in buildings in the zone of analysis. This database is useful to calculate the heat released inside the building due to the use of appliances, people moving etc, as such, it is a key element of CEA

**Format/Naming**: dataBase / internal_loads.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/internal_loads.dbf`` 

**Primary Interdependencies**: Default Databases

**Secondary Interdependencies**: 

+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit      | Description                                                         | Valid Values |
+==========================+========+===========+=====================================================================+==============+
| Name                     | string | [-]       | Unique building ID. It must start with a letter.                    | alphanumeric |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| X_ghp                    | float  | [gh/kg/p] | Moisture released by occupancy at peak conditions                   | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ea_Wm2                   | float  | [W/m2]    | Peak specific electrical load due to computers and devices          | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| El_Wm2                   | float  | [W/m2]    | Peak specific electrical load due to artificial lighting            | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Epro_Wm2                 | string | [W/m2]    | Peak specific electrical load due to industrial processes           | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ere_Wm2                  | float  | [W/m2]    | Peak specific electrical load due to refrigeration                  | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Ed_Wm2                   | float  | [W/m2]    | Peak specific electrical load due to servers/data centres           | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Vww_lpd                  | float  | [lpd]     | Peak specific daily hot water consumption                           | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Vw_lpd                   | float  | [lpd]     | Peak specific fresh water consumption (includes cold and hot water) | {0.0...n}    |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+
| Qhpro_Wm2                |        |           |                                                                     |              |
+--------------------------+--------+-----------+---------------------------------------------------------------------+--------------+

Primary: Zone Occupancy
^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing shares of occupancy types in buildings in the zone of analysis. This database is useful to determine hourly patterns of occupancy of buildings in the area. CEA covers >15 different types of occupancy. Mix-use buildings are represented by different shares

**Format/Naming**: dataBase / occupancy.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building_properties/age.dbf`` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

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

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

+--------------------------+---------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type    | Unit | Description                                      | Valid Values |
+==========================+=========+======+==================================================+==============+
| NAME                     | string  | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| SOLAR                    | integer | [-]  |                                                  | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| GEOTHERMAL               | integer | [-]  |                                                  | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| WATERBODY                | integer | [-]  |                                                  | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| NATURALGAS               | integer | [-]  |                                                  | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+
| BIOGAS                   | integer | [-]  |                                                  | {0...n}      |
+--------------------------+---------+------+--------------------------------------------------+--------------+

Primary: Supply Systems
^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing the type of heating, cooling and electrical supply systems of buildings in the zone of analysis. This database is useful to calculate the emissions due to operation of buildings and their underlying infrastructure. 

**Format/Naming**: dataBase / supply_systems.dbf

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/building-properties/supply_systems.dbf`` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

+--------------------------+--------+------+--------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                      | Valid Values |
+==========================+========+======+==================================================+==============+
| Name                     | string | [-]  | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+--------+------+--------------------------------------------------+--------------+
| type_cs                  | string | [-]  | Type of cooling supply system                    | {T0...Tn}    |
+--------------------------+--------+------+--------------------------------------------------+--------------+
| type_hs                  | string | [-]  | Type of heating supply system                    | {T0...Tn}    |
+--------------------------+--------+------+--------------------------------------------------+--------------+
| type_dhw                 | string | [-]  | Type of hot water supply system                  | {T0...Tn}    |
+--------------------------+--------+------+--------------------------------------------------+--------------+
| type_el                  | string | [-]  | Type of electrical supply system                 | {T0...Tn}    |
+--------------------------+--------+------+--------------------------------------------------+--------------+

Secondary: Zone HVAC
^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .dbf file storing information of HVAC systems in buildings. This database is useful to know which type of technical system the building is using. Depending on the system, the energy demand of the building can be supplied in different ways.

**Format/Naming**: dataBase / technical_systems.dbf

**Location (example)**: ..cea/examples/reference-case-open/baseline/inputs/building_properties/technical_systems.dbf

**Primary Interdependencies**: Default Databases

**Secondary Interdependencies**: 

+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                                                                         | Valid Values |
+==========================+========+=========+=====================================================================================================+==============+
| Name                     | string | [-]     | Unique building ID. It must start with a letter.                                                    | -            |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------+--------------+
| type_cs                  | string | [-]     | Type of cooling system (relates to values in Default Database HVAC Properties)                      | {T1...Tn}    |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------+--------------+
| type_hs                  | string | [m2/m2] | Type of heating system (relates to values in Default Database HVAC Properties)                      | {T1...Tn}    |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------+--------------+
| type_dhw                 | string | [m2/m2] | Type of hot water system (relates to values in Default Database HVAC Properties)                    | {T1...Tn}    |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------+--------------+
| type_ctrl                | string | [m2/m2] | Type of heating and cooling control systems (relates to values in Default Database HVAC Properties) | {T1...Tn}    |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------+--------------+
| type_vent                | string | [m2/m2] | Type of ventilation strategy (relates to values in Default Database HVAC Properties)                | {T1...Tn}    |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------+--------------+

District Cooling Network
^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of cooling networks in the surroundings of the zone of analysis. This database is useful to calculate ...??

**Format/Naming**: Shapefile / edges.shp, nodes.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/networks/DC/edges.shp `` and `` ..cea/examples/reference-case-open/baseline/inputs/networks/DC/nodes.shp ``

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| edges /nodes             |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

District Heating Network
^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a shapefile storing the geometry of heating networks in the surroundings of the zone of analysis. This database is useful to calculate ...??

**Format/Naming**: Shapefile / edges.shp, nodes.shp

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/networks/DH/edges.shp `` and `` ..cea/examples/reference-case-open/baseline/inputs/networks/DH/nodes.shp ``

**Primary Interdependencies**: Primary Input Database (None)

**Secondary Interdependencies**: 

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| streets/edges/nodes      |      |      |             |              |
+--------------------------+------+------+-------------+--------------+

Primary: District Topography
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists in a raster image with cells of 5m X 5m of resolution storing the elevation of the topography in m. This database is useful to calculate the solar radiation reflected to buildings. 

**Format/Naming**: shapefile / district.tiff

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/inputs/topography/terrain.tiff `` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| terrain.tiff             | [-]  | [-]  | [-]         | [-]          |
+--------------------------+------+------+-------------+--------------+

Primary: Zone Weather
^^^^^^^^^^^^^^^^^^^^^
**Description**: This database consists of a .epw file storing hourly data about the weather conditions of the zone of interest. This data is useful to estimate solar radiation on site, and the conditions of temperature and humidity of the air, as such, it is a key element of CEA.

**Format/Naming**: eplus file / zurich.epw

**Location (example)**: `` ..cea/databases/CH/weather/zurich.epw`` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: None

+--------------------------+------+------+-------------+--------------+
| Column names /parameters | Type | Unit | Description | Valid Values |
+==========================+======+======+=============+==============+
| <location>.epw           | [-]  | [-]  | [-]         | [-]          |
+--------------------------+------+------+-------------+--------------+


Default Databases
-----------------
Construction Properties_Architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores building properties of the Swiss building stock. This database is useful to retrieve properties of buildings based on their construction year and age. 

**Format/Naming**: excel file / construction.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/construction_properties.xlsx `` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: Receives data from the primary input databases of ?age? and ?occupancy?. Serves to produce all secondary input databases.



+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Column names /parameters | Type   | Unit          | Description                                                                                                         | Valid Values                   |
+==========================+========+===============+=====================================================================================================================+================================+
| Name                     | string | [-]           | Unique building ID. It must start with a letter.                                                                    | alphanumeric                   |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| building_use             | string | [-]           | Building use. It relates to the uses stored in the input database of Zone_occupancy                                 | Those stored in Zone_occupancy |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_start               | int    | [yr]          | Lower limit of year interval where the building properties apply                                                    | {0...n}                        |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_end                 | int    | [yr]          | Upper limit of year interval where the building properties apply                                                    | {0...n}                        |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| standard                 | string | [-]           | Letter representing whereas the field represent construction properties of a building as built ?C? or renovated ?R? | {?C? , ?R?}                    |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Hs                       | float  | [-]           | Fraction of heated space in building archetype                                                                      | {0.0...1}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| win_wall                 | float  | [-]           | Window to wall ratio in building archetype                                                                          | {0.0...1}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| wwr_north                | float  | [-]           | Window to wall ratio in building archetype                                                                          | {0.0...1}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| wwr_south                | float  | [-]           | Window to wall ratio in building archetype                                                                          | {0.0...1}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| wwr_east                 | float  | [-]           | Window to wall ratio in building archetype                                                                          | {0.0...1}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| wwr_west                 | float  | [-]           | Window to wall ratio in building archetype                                                                          | {0.0...1}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_cons                | string | [-]           | Type of construction. It relates to the contents of the default database of Envelope Properties: construction       | {T1...Tn}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_leak                | string | [-]           | Leakage level. It relates to the contents of the default database of Envelope Properties: leakage                   | {T1...Tn}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_win                 | string | [-]           | Window type. It relates to the contents of the default database of Envelope Properties: windows                     | {T1...Tn}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_roof                | string | [-]           | Roof construction. It relates to the contents of the default database of Envelope Properties: roof                  | {T1...Tn}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_wall                | string | [-]           | Wall construction. It relates to the contents of the default database of Envelope Properties: walll                 | {T1...Tn}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_shade               | string | [-]           | Shading system type. It relates to the contents of the default database of Envelope Properties: shade               | {T1...Tn}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+
| void_dek                 | float  | [floor/floor] | Share of floors with an open envelope (default = 0)                                                                 | {0.0...1}                      |
+--------------------------+--------+---------------+---------------------------------------------------------------------------------------------------------------------+--------------------------------+

Construction Properties_Supply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores building properties of the Swiss building stock. This database is useful to retrieve properties of buildings based on their construction year and age. 

**Format/Naming**: excel file / construction.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/construction_properties.xlsx `` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: Receives data from the primary input databases of ?age? and ?occupancy?. Serves to produce all secondary input databases.



+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Column names /parameters | Type   | Unit | Description                                                                                                               | Valid Values                   |
+==========================+========+======+===========================================================================================================================+================================+
| building_use             | string | [-]  | Building use. It relates to the uses stored in the input database of Zone_occupancy                                       | Those stored in Zone_occupancy |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_start               | int    | [yr] | Lower limit of year interval where the building properties apply                                                          | {0...n}                        |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_end                 | int    | [yr] | Upper limit of year interval where the building properties apply                                                          | {0...n}                        |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| standard                 | string | [-]  | Letter representing whereas the field represent construction properties of a building as constructed, C, or renovated, R. | {C, R}                         |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_hs                  | string | [-]  | Type of heating supply system                                                                                             | {T0...Tn}                      |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_dhw                 | string | [-]  | Type of hot water supply system                                                                                           | {T0...Tn}                      |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_cs                  | string | [-]  | Type of cooling supply system                                                                                             | {T0...Tn}                      |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| type_el                  | string | [-]  | Type of electrical supply system                                                                                          | {T0...Tn}                      |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------------+--------------------------------+

Construction Properties_HVAC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores building properties of the Swiss building stock. This database is useful to retrieve properties of buildings based on their construction year and age. 

**Format/Naming**: excel file / construction.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/construction_properties.xlsx `` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: Receives data from the primary input databases of ?age? and ?occupancy?. Serves to produce all secondary input databases.



+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit | Description                                                                                                         | Valid Values |
+==========================+========+======+=====================================================================================================================+==============+
| building_use             | string | [-]  | Building use. It relates to the uses stored in the input database of Zone_occupancy                                 |              |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| year_start               | int    | [yr] | Lower limit of year interval where the building properties apply                                                    |              |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| year_end                 | int    | [yr] | Upper limit of year interval where the building properties apply                                                    |              |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| standard                 | string | [-]  | Letter representing whereas the field represent construction properties of a building as built ?C? or renovated ?R? | {C , R}      |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| type_hs                  | string | [-]  | Type of heating supply system                                                                                       | {T0...Tn}    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| type_cs                  | string | [-]  | Type of cooling supply system                                                                                       | {T0...Tn}    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| type_dhw                 | string | [-]  | Type of hot water supply system                                                                                     | {T0...Tn}    |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| type_ctrl                |        |      |                                                                                                                     |              |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+
| type_vent                |        |      |                                                                                                                     |              |
+--------------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+--------------+

Construction Properties_Indoor Comfort
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores building properties of the Swiss building stock. This database is useful to retrieve properties of buildings based on their construction year and age. 

**Format/Naming**: excel file / construction.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/construction_properties.xlsx `` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: Receives data from the primary input databases of ?age? and ?occupancy?. Serves to produce all secondary input databases.



+----------------------------------------------------------------------------+------+------+-------------+--------------+
| Column names /parameters                                                   | Type | Unit | Description | Valid Values |
+============================================================================+======+======+=============+==============+
| Same parameters as Zone Indoor Comfort plus additional Code (for Building) |      |      |             |              |
+----------------------------------------------------------------------------+------+------+-------------+--------------+

Construction Properties_Internal Loads
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores building properties of the Swiss building stock. This database is useful to retrieve properties of buildings based on their construction year and age. 

**Format/Naming**: excel file / construction.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/construction_properties.xlsx `` 

**Primary Interdependencies**: None

**Secondary Interdependencies**: Receives data from the primary input databases of ?age? and ?occupancy?. Serves to produce all secondary input databases.



+-----------------------------------------------------------------------+------+------+-------------+--------------+
| Column names /parameters                                              | Type | Unit | Description | Valid Values |
+=======================================================================+======+======+=============+==============+
| Same parameters as Internal Loads plus additional Code (for Building) |      |      |             |              |
+-----------------------------------------------------------------------+------+------+-------------+--------------+

Occupancy Schedules
^^^^^^^^^^^^^^^^^^^
**Description**: This database in Excel stores information of schedules of occupancy, and use of hot water, lighting and other electrical appliances. Every tab in this excel file corresponds to a type of occupancy. This database is useful to calculate the demand of energy in buildings.

**Format/Naming**: excel file / occupancy_schedule.xlsx

**Location (example)**: `` cea/databases/CH/archetypes/occupancy_schedules.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of Zone occupancy.

**Secondary Interdependencies**: None

+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Column names /parameters   | Type   | Unit   | Description                                                          | Valid Values |
+============================+========+========+======================================================================+==============+
| Name                       | string | [-]    | Unique building ID. It must start with a letter.                     | alphanumeric |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Weekday_1                  | float  | [p/p]  | Probability of maximum occupancy per hour in a weekday               | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Saturday_1                 | float  | [p/p]  | Probability of maximum occupancy per hour on Saturday                | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Sunday_1                   | float  | [p/p]  | Probability of maximum occupancy per hour on Sunday                  | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Weekday_2                  | float  | [p/p]  | Probability of use of lighting and applicances (daily) for each hour | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Saturday_2                 | float  | [p/p]  | Probability of use of lighting and applicances (daily) for each hour | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Sunday_2                   | float  | [p/p]  | Probability of use of lighting and applicances (daily) for each hour | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Weekday_3                  | float  | [p/p]  | Probability of domestic hot water consumption (daily) for each hour  | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Saturday_3                 | float  | [p/p]  | Probability of domestic hot water consumption (daily) for each hour  | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Sunday_3                   | float  | [p/p]  | Probability of domestic hot water consumption (daily) for each hour  | {0.0...1}    |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
|                            |        |        |                                                                      |              |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| probability of use monthly | float  | [-]    |                                                                      |              |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+
| Occupancy density          | float  | [m2/p] | m2 per person                                                        |              |
+----------------------------+--------+--------+----------------------------------------------------------------------+--------------+

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

+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| Column names /parameters | Type   | Unit | Description                                                                         | Valid Values                   |
+==========================+========+======+=====================================================================================+================================+
| code                     | string | [-]  | Building use. It relates to the uses stored in the input database of Zone_occupancy | Those stored in Zone_occupancy |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| NRE_today                | float  | [-]  | Net real emissions???                                                               | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| CO2_today                | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| PEN_today                | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| NRE_target_retrofit      | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| CO2_target_retrofit      | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| PEN_target_retrofit      | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| NRE_target_new           | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| CO2_target_new           | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| PEN_target_new           | float  | [-]  |                                                                                     | {0.0...n}                      |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+
| Description              | string | [-]  | Describes the source of the benchmark standards.                                    | [-]                            |
+--------------------------+--------+------+-------------------------------------------------------------------------------------+--------------------------------+

Supply Systems
^^^^^^^^^^^^^^
**Description**: This database contains the schedule for various conduits, relating pipe nominal diameter (DN) to investment cost. This is helful for approximating the costs of hydraulic networks.

**Format/Naming**: excel file / supply_systems.xls

**Location (example)**: `` cea/databases/CH/economics/supply_systems.xls ``

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                                                                                        | Valid Values |
+==========================+========+=======+====================================================================================================================+==============+
| Description              | string | [DN#] | Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter. | alphanumeric |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Diameter_max             | float  | [-]   | Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.                                     | {0.0....n}   |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Diameter_min             | float  | [-]   | Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.                                     | {0.0....n}   |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Unit                     | string | [mm]  | Defines the unit of measurement for the diameter values.                                                           | [-]          |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Investment               | float  | [$/m] | Typical cost of investment for a given pipe diameter.                                                              | {0.0....n}   |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Currency                 | string | [-]   | Defines the unit of currency used to create the cost estimations (year specific). E.g. USD-2015.                   | [-]          |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+

LCA Buildings: EMBODIED_ENERGY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information for the Life Cycle Analysis of buildings due to their construction and dismantling. This database is useful to calculate the embodied emissions and grey energy of buildings.

**Format/Naming**: excel file / LCA_buidlings.xlsx

**Location (example)**: `` cea/databases/CH/lifecycle/LCA_buildings.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of age and occupancy

**Secondary Interdependencies**: None

+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Column names /parameters | Type   | Unit | Description                                                                                                     | Valid Values                   |
+==========================+========+======+=================================================================================================================+================================+
| building_use             | string | [-]  | Building use. It relates to the uses stored in the input database of Zone_occupancy                             | Those stored in Zone_occupancy |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_start               | int    | [-]  | Lower limit of year interval where the building properties apply                                                | {0...n}                        |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_end                 | int    | [-]  | Upper limit of year interval where the building properties apply                                                | {0...n}                        |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| standard                 | string | [-]  | Letter representing whereas the field represent construction properties of a building as built C or renovated R | {C , R}                        |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_ext_ag              | float  | [GJ] | Typical embodied energy of the exterior above ground walls.                                                     | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_ext_bg              | float  | [GJ] | Typical embodied energy of the exterior below ground walls.                                                     | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Floor_int                | float  | [GJ] | Typical embodied energy of the interior floor.                                                                  | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_int_sup             | float  | [GJ] |                                                                                                                 | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_int_nosup           | float  | [GJ] |                                                                                                                 | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Roof                     | float  | [GJ] | Typical embodied energy of the roof.                                                                            | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Floor_g                  | float  | [GJ] | Typical embodied energy of the ground floor.                                                                    | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Services                 | float  | [GJ] | Typical embodied energy of the building services.                                                               | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Win_ext                  | float  | [GJ] | Typical embodied energy of the external glazing.                                                                | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Excavation               | float  | [GJ] | Typical embodied energy for site excavation.                                                                    | {0.0....n}                     |
+--------------------------+--------+------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+

LCA Buildings: EMBODIED_EMISSIONS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information for the Life Cycle Analysis of buildings due to their construction and dismantling. This database is useful to calculate the embodied emissions and grey energy of buildings.

**Format/Naming**: excel file / LCA_buidlings.xlsx

**Location (example)**: `` cea/databases/CH/lifecycle/LCA_buildings.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of age and occupancy

**Secondary Interdependencies**: None

+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Column names /parameters | Type   | Unit    | Description                                                                                                     | Valid Values                   |
+==========================+========+=========+=================================================================================================================+================================+
| building_use             | string | [-]     | Building use. It relates to the uses stored in the input database of Zone_occupancy                             | Those stored in Zone_occupancy |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_start               | int    | [-]     | Lower limit of year interval where the building properties apply                                                | {0...n}                        |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| year_end                 | int    | [-]     | Upper limit of year interval where the building properties apply                                                | {0...n}                        |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| standard                 | string | [-]     | Letter representing whereas the field represent construction properties of a building as built C or renovated R | {C , R}                        |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_ext_ag              | float  | [kgCO2] | Typical embodied CO2 equivalent emissions of the exterior above ground walls.                                   | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_ext_bg              | float  | [kgCO2] | Typical embodied CO2 equivalent emissions of the exterior below ground walls.                                   | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Floor_int                | float  | [kgCO2] | Typical embodied CO2 equivalent emissions of the interior floor.                                                | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_int_sup             | float  | [kgCO2] |                                                                                                                 | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Wall_int_nosup           | float  | [kgCO2] |                                                                                                                 | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Roof                     | float  | [kgCO2] | Typical embodied CO2 equivalent emissions of the roof.                                                          | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Floor_g                  | float  | [kgCO2] | Typical embodied CO2 equivalent emissions of the ground floor.                                                  | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Services                 | float  | [kgCO2] | Typical embodied CO2 equivalent emissions of the building services.                                             | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Win_ext                  | float  | [kgCO2] | Typical embodied CO2 equivalent emissions of the external glazing.                                              | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+
| Excavation               | float  | [kgCO2] | Typical embodied CO2 equivalent emissions for site excavation.                                                  | {0.0....n}                     |
+--------------------------+--------+---------+-----------------------------------------------------------------------------------------------------------------+--------------------------------+

LCA Infrastructure
^^^^^^^^^^^^^^^^^^
**Description**: This database stores information for the Life Cycle Analysis of energy infrastructure in buildings and districts. This database is useful to calculate the emissions and primary energy per unit of energy consumed in the area.

**Format/Naming**: excel file / LCA_infrastructure.xlsx

**Location (example)**: `` cea/databases/CH/lifecycle/LCA_infrastructure.xlsx`` 

**Primary Interdependencies**: Relates detailed data to the primary input database of supply_systems

**Secondary Interdependencies**: None

+--------------------------+--------+-----------+-------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit      | Description                                                                                     | Valid Values |
+==========================+========+===========+=================================================================================================+==============+
| Description              | string | [-]       | Description of the heating and cooling network (related to the code). E.g. heatpump -soil/water | [-]          |
+--------------------------+--------+-----------+-------------------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]       | Unique ID of component of the heating and cooling network                                       | {T1..Tn}     |
+--------------------------+--------+-----------+-------------------------------------------------------------------------------------------------+--------------+
| PEN                      | float  | [kWh/kWh] | Refers to the amount of primary energy needed (PEN) to run the heating or cooling system.       | {0.0....n}   |
+--------------------------+--------+-----------+-------------------------------------------------------------------------------------------------+--------------+
| CO2                      | float  | [kg/kWh]  | Refers to the equivalent CO2 required to run the heating or cooling system.                     | {0.0....n}   |
+--------------------------+--------+-----------+-------------------------------------------------------------------------------------------------+--------------+
| costs_kWh                | float  | [$/kWh]   | Refers to the financial costs required to run the heating or cooling system.                    | {0.0....n}   |
+--------------------------+--------+-----------+-------------------------------------------------------------------------------------------------+--------------+

Emission Systems
^^^^^^^^^^^^^^^^
**Description**: This database stores information of HVAC systems in buildings. This database is useful to calculate the performance of different HVAC systems and control systems in buildings.

**Format/Naming**: excel file / emission_systems.xlsx

**Location (example)**: `` cea/databases/systems/emission_systems.xls`` 

**Primary Interdependencies**: Relates to the primary input database of Zone HVAC

**Secondary Interdependencies**: None

+--------------------------+--------+--------+-----------------------------------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit   | Description                                                                                                                 | Valid Values |
+==========================+========+========+=============================================================================================================================+==============+
| Description              | string | [-]    | Description of the typical supply and return temperatures related to HVAC, DHW and sanitation.                              | [-]          |
+--------------------------+--------+--------+-----------------------------------------------------------------------------------------------------------------------------+--------------+
| code                     | string | [-]    | Unique ID of component of the typical supply and return temperature bins.                                                   | {T1..Tn}     |
+--------------------------+--------+--------+-----------------------------------------------------------------------------------------------------------------------------+--------------+
| Tsww0_C                  | float  | [C]    | Typical supply water temperature.                                                                                           | {0.0....n}   |
+--------------------------+--------+--------+-----------------------------------------------------------------------------------------------------------------------------+--------------+
| Qwwmax_Wm2               | float  | [W/m2] | Maximum heat flow permitted by the distribution system per m2 of the exchange interface (e.g. floor/radiator heating area). | {0.0....n}   |
+--------------------------+--------+--------+-----------------------------------------------------------------------------------------------------------------------------+--------------+

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
| rth_win                  | float  | [-]  | Reflectance in the Red spectrum. Defined according Radiance. (long-wave)                         | {0...1}      |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| gtn_win                  | float  | [-]  | Reflectance in the Green spectrum. Defined according Radiance. (medium-wave)                     | {0...1}      |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| btn_win                  | float  | [-]  | Reflectance in the Blue spectrum. Defined according Radiance. (Short-wave)                       | {0...1}      |
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
| e_roof                   | float  | [-]  | Emissivity of external surface. Defined according to ISO 13790.                                  | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| U_roof                   | float  | [-]  | Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. | {0.1...n}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| r_roof                   | float  | [-]  | Reflectance in the Red spectrum. Defined according Radiance. (long-wave)                         | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| g_roof                   | float  | [-]  | Reflectance in the Green spectrum. Defined according Radiance. (medium-wave)                     | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| b_roof                   | float  | [-]  | Reflectance in the Blue spectrum. Defined according Radiance. (Short-wave)                       | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| spec_roof                | float  | [-]  | Specularity. Defined according Radiance.                                                         | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| rough_roof               | float  | [-]  | roughness. Defined according Radiance.                                                           | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+

Envelope Systems: Wall
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
| a_wall                   | float  | [-]  | Solar absorption coefficient. Defined according to ISO 13790.                                    | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| e_wall                   | float  | [-]  | Emissivity of external surface. Defined according to ISO 13790.                                  | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| U_wall                   | float  | [-]  | Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. | {0.1...n}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| r_wall                   | float  | [-]  | Reflectance in the Red spectrum. Defined according Radiance. (long-wave)                         | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| U_base                   | float  | [-]  | Thermal transmittance of........                                                                 |              |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| g_wall                   | float  | [-]  | Reflectance in the Green spectrum. Defined according Radiance. (medium-wave)                     | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| b_wall                   | float  | [-]  | Reflectance in the Blue spectrum. Defined according Radiance. (Short-wave)                       | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| spec_wall                | float  | [-]  | Specularity. Defined according Radiance.                                                         | {0.0...1}    |
+--------------------------+--------+------+--------------------------------------------------------------------------------------------------+--------------+
| rough_wall               | float  | [-]  | roughness. Defined according Radiance.                                                           | {0.0...1}    |
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
| code                     | string | [-]  | Unique ID of component in the window category                                      | {T1...Tn}    |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+
| rf_sh                    | float  | [-]  | Shading coefficient when shading device is active. Defined according to ISO 13790. | {0.0...1}    |
+--------------------------+--------+------+------------------------------------------------------------------------------------+--------------+

Thermal Networks_Piping Catalog
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: 

**Format/Naming**: excel file / thermal_networks.xls

**Location (example)**: `` cea/databases/systems/thermal_networks.xls`` 

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit  | Description                                                                                                        | Valid Values |
+==========================+========+=======+====================================================================================================================+==============+
| Pipe_DN                  | string | [DN#] | Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter. | alphanumeric |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| D_ext_m                  | float  | [-]   | Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.                                     | {0.0...n}    |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| D_int_m                  | float  | [-]   | Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.                                     | {0.0...n}    |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| D_ins_m                  | float  |       |                                                                                                                    |              |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Vdot_min_m3s             | float  |       |                                                                                                                    |              |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+
| Vdot_max_m3s             | float  |       |                                                                                                                    |              |
+--------------------------+--------+-------+--------------------------------------------------------------------------------------------------------------------+--------------+

Thermal Networks_Material Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: 

**Format/Naming**: excel file / thermal_networks.xls

**Location (example)**: `` cea/databases/systems/thermal_networks.xls`` 

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+------+----------------------+--------------+
| Column names /parameters | Type   | Unit | Description          | Valid Values |
+==========================+========+======+======================+==============+
| Material                 |        | [-]  | Material             | [-]          |
+--------------------------+--------+------+----------------------+--------------+
| Code                     | string |      |                      |              |
+--------------------------+--------+------+----------------------+--------------+
| lambda_WmK               | float  |      | Thermal conductivity |              |
+--------------------------+--------+------+----------------------+--------------+
| rho_kgm3                 | float  |      |                      |              |
+--------------------------+--------+------+----------------------+--------------+
| Cp_JkgK                  | float  |      | Heat capacity        |              |
+--------------------------+--------+------+----------------------+--------------+

Uncertainty Distributions
^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores information of probability density functions of several input parameters of the CEA tool. This database is useful to perform a sensitivity analysis of input parameters and to calibrate to measured data.

**Format/Naming**: excel file / uncertainty_distributions.xlsx

**Location (example)**: .../cea/databases/uncertainty/uncertainty_distributions.xlsx

**Primary Interdependencies**: Relates detailed data to the secondary input database of architecture through the contents of the default database of envelope_systems. It also relates detailed data to the secondary input databases of internal_loads and indoor_comfort

**Secondary Interdependencies**: None

+--------------------------+------+------+--------------------+--------------+
| Column names /parameters | Type | Unit | Description        | Valid Values |
+==========================+======+======+====================+==============+
| name                     |      |      |                    |              |
+--------------------------+------+------+--------------------+--------------+
| distribution             |      |      |                    |              |
+--------------------------+------+------+--------------------+--------------+
| mu                       |      |      |                    |              |
+--------------------------+------+------+--------------------+--------------+
| stdv                     |      |      | Standard Deviation |              |
+--------------------------+------+------+--------------------+--------------+
| min                      |      |      | Minimum            |              |
+--------------------------+------+------+--------------------+--------------+
| max                      |      |      | Maximum            |              |
+--------------------------+------+------+--------------------+--------------+
| reference                |      |      |                    |              |
+--------------------------+------+------+--------------------+--------------+


Output Databases
----------------
Demand: Zone
^^^^^^^^^^^^
**Description**: These databases store the heating/cooling demand and various operating temperatures for each building in hourly time stamps. Each group of variables is calculated using a specific modules from ``cea\demand`` and is stored within the scenario directory using demand_writer.

**Format/Naming**: csv file / B01.csv

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/outputs/demand/B01.csv`` 

**Primary Interdependencies**: Calculated using the demand modules which get data from the primary input, case specific and system databases.

**Secondary Interdependencies**: Relates to the operating costs for the LCA as well as costs vs CO2 and network optimisations.

+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Column names /parameters | Type   | Unit            | Description                                                                 | Valid Values        |
+==========================+========+=================+=============================================================================+=====================+
| DATE                     | date   | [smalldatetime] | Time stamp for each day of the year ascending in hour intervals.            | YYYY-MM-DD hh:mm:ss |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Name                     | string | [-]             | Unique building ID. It must start with a letter.                            | alphanumeric        |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| people                   | int    | [people]        | Predicted occupancy for each time stamp dependant on the occupancy_schedule | {0...n}             |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| x_int                    | float  | [kg/kg]         | Internal mass fraction of humidity (vapor/dry air)                          | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| QEf_kWh                  | float  | [kWh]           | Final electrical demand for the heating and cooling system??                | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| QHf_kWh                  | float  | [kWh]           | Final heating demand                                                        | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| QCf_kWh                  | float  | [kWh]           | Final cooling demand                                                        | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Ef_kWh                   | float  | [kWh]           | Final electricity demand                                                    | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| E_kWh                    | float  | [kWh]           | Demand for electricity, exclusive of ??                                     | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Egenf_cs_kWh             | float  | [kWh]           | ??                                                                          | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_sen_shu_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_sen_ahu_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_lat_ahu_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_sen_aru_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_lat_aru_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_sen_sys_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_lat_sys_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_em_ls_kWh            | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_dis_ls_kWh           | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhs_kWh                  | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhsf_kWh                 | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhsf_lat_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qwwf_kWh                 | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qww_kWh                  | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhsf_ahu_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhsf_aru_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhsf_shu_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcsf_ahu_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcsf_aru_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcsf_scu_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcdataf_kWh              | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcref_kWh                | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_sen_scu_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_sen_ahu_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_lat_ahu_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_sen_aru_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_lat_aru_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_sen_sys_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_lat_sys_kWh          | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_em_ls_kWh            | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_dis_ls_kWh           | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcsf_kWh                 | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcs_kWh                  | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qcsf_lat_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Qhprof_kWh               | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Edataf_kWh               | float  | [kWh]           | Final electricity consumption in data centers                               | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Ealf_kWh                 | float  | [kWh]           | Final appliances and lighting demand                                        | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eaf_kWh                  | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Elf_kWh                  | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eref_kWh                 | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eauxf_kWh                | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eauxf_ve_kWh             | float  | [kWh]           | Final auxiliary electricity for the ventilation system.                     | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eauxf_hs_kWh             | float  | [kWh]           | Final auxiliary electricity for the heating system.                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eauxf_cs_kWh             | float  | [kWh]           | Final auxiliary electricity for the cooling system.                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eauxf_ww_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eauxf_fw_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Eprof_kWh                | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Ecaf_kWh                 | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Egenf_cs_kWh             | float  | [kWh]           |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_light_kWh     | float  | [kWh]           | Sensible heat gain from lighting                                            | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_app_kWh       | float  | [kWh]           | Sensible heat gain from appliances                                          | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_peop_kWh      | float  | [kWh]           | Sensible heat gain from people                                              | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_data_kWh      | float  | [kWh]           | Sensible heat gain from data centres                                        | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_loss_sen_ref_kWh       | float  | [kWh]           | Sensible heat loss from the refridgeration system                           | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_wall_kWh      | float  | [kWh]           | Sensible heat gain through exterior walls                                   | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_base_kWh      | float  | [kWh]           | Sensible heat gain through the base                                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_roof_kWh      | float  | [kWh]           | Sensible heat gain through the roof                                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_wind_kWh      | float  | [kWh]           | Sensible heat gain through the external windows                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_sen_vent_kWh      | float  | [kWh]           | Sensible heat gain from the ventilation                                     | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Q_gain_lat_peop_kWh      | float  | [kWh]           | Latent heat gain from people                                                | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| I_sol_kWh                | float  | [kWh]           | Total solar insolation                                                      | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| I_rad_kWh                | float  | [kWh]           | Total solar radiation                                                       | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| I_sol_and_I_rad_kWh      | float  | [kWh]           | Combined solar radiation and insolation.                                    | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcpwwf_kWperC            | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcpdataf_kWperC          | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcpref_kWperC            | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcptw_kWperC             | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcpcsf_ahu_kWperC        | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcpcsf_aru_kWperC        | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcpcsf_scu_kWperC        | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcphsf_ahu_kWperC        | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcphsf_aru_kWperC        | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcphsf_shu_kWperC        | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcpcsf_kWperC            | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| mcphsf_kWperC            | float  | [kW/C]          |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| T_int_C                  | float  | [C]             | RC modelled internal temperature for a given building.                      | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| T_ext_C                  | float  | [C]             | Historical external temperature for a given building.                       | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| theta_o_C                | float  | [C]             |                                                                             | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Twwf_sup_C               | float  | [C]             | Supply temperature of the domestic hot water (DHW)                          | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Twwf_re_C                | float  | [C]             | Return temperature of the domestic hot water (DHW)                          | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_sup_aru_C           | float  | [C]             | Heating supply temperature of the air recirculation unit (ARU)              | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_sup_ahu_C           | float  | [C]             | Heating supply temperature of the air handeling unit (AHU)                  | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_sup_shu_C           | float  | [C]             | Heating supply temperature of the sensible heating unit (SHU)               | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_re_aru_C            | float  | [C]             | Heating return temperature of the air recirculation unit (ARU)              | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_re_ahu_C            | float  | [C]             | Heating return temperature of the air handeling unit (AHU)                  | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_re_shu_C            | float  | [C]             | Heating return temperature of the sensible heating unit (SHU)               | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_sup_aru_C           | float  | [C]             | Cooling supply temperature of the air recirculation unit (ARU)              | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_sup_ahu_C           | float  | [C]             | Cooling supply temperature of the air handeling unit (AHU)                  | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_sup_scu_C           | float  | [C]             | Cooling supply temperature of the sensible Cooling unit (SHU)               | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_re_aru_C            | float  | [C]             | Cooling return temperature of the air recirculation unit (ARU)              | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_re_ahu_C            | float  | [C]             | Cooling return temperature of the air handeling unit (AHU)                  | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_re_scu_C            | float  | [C]             | Cooling return temperature of the sensible Cooling unit (SHU)               | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcdataf_sup_C            | float  | [C]             | Cooling supply temperature of the data centre                               | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcdataf_re_C             | float  | [C]             | Cooling return temperature of the data centre                               | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcref_sup_C              | float  | [C]             | Cooling supply temperature of the refridgeration system                     | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcref_re_C               | float  | [C]             | Cooling return temperature of the refridgeration system                     | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_sup_C               | float  | [C]             | Heating supply temperature of TABS heating system??                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Thsf_re_C                | float  | [C]             | Heating return temperature of TABS heating system??                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_sup_C               | float  | [C]             | Cooling supply temperature of TABS heating system??                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+
| Tcsf_re_C                | float  | [C]             | Cooling return temperature of TABS heating system??                         | {0.0...n}           |
+--------------------------+--------+-----------------+-----------------------------------------------------------------------------+---------------------+

Demand: District
^^^^^^^^^^^^^^^^
**Description**: This database stores the gross floor, conditioned floor and roof areas, heating/cooling demand and occupancy of the district (aggregated for each building). Each group of variables is calculated using a specific module from ``cea\demand`` and is stored within the scenario directory using demand_writer.

**Format/Naming**: csv file / B01.csv

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/outputs/demand/B01.csv`` 

**Primary Interdependencies**: Calculated using the demand modules which get data from the primary input, case specific and system databases.

**Secondary Interdependencies**: Relates to the operating costs for the LCA as well as costs vs CO2 and network optimisations.

+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit     | Description                                      | Valid Values |
+==========================+========+==========+==================================================+==============+
| Name                     | string | [-]      | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Af_m2                    | float  | [m2]     | Conditioned floor area (heated/cooled)           | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Aroof_m2                 | float  | [m2]     | Roof area                                        | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| GFA_m2                   | float  | [m2]     | Gross floor area                                 | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| people0                  | int    | [people] | Aggregated occupancy for a given building area.  | {0...n}      |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_ahu_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_dis_ls_MWhyr         | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_lat_ahu_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_sys_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_aru_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_aru0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Ecaf0_kW                 | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| QHf0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_lat_sys_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_cs0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_dis_ls0_kW           | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_lat_sys_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_ahu_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhprof0_kW               | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_em_ls0_kW            | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_hs_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_sys_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eprof0_kW                | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Ealf_MWhyr               | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_lat0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_ahu0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qwwf_MWhyr               | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_aru0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Ecaf_MWhyr               | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_dis_ls0_kW           | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_ahu_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| E0_kW                    | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_scu0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_ahu0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Edataf_MWhyr             | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_lat_ahu0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_em_ls_MWhyr          | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_sys0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Ealf0_kW                 | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_fw_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_lat_aru_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_MWhyr               | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| QCf0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcdataf0_kW              | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_dis_ls_MWhyr         | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| QCf_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_lat_sys0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| QEf0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_sys0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_aru_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_ve0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_lat_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_aru0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_scu_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcref_MWhyr              | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Elf_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_ve_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_em_ls0_kW            | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eref_MWhyr               | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_lat_ahu0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Edataf0_kW               | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhprof_MWhyr             | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_scu_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf0_kW                 | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_lat_aru0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_aru_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_ahu0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_lat0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_hs0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eprof_MWhyr              | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_sen_scu0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Ef_MWhyr                 | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| E_MWhyr                  | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_shu0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_lat_sys0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| QEf_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_lat_aru0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Ef0_kW                   | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_lat_aru_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf0_kW                | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Egenf_cs_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_shu0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_shu_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_MWhyr               | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_aru_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_cs_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eaf0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcref0_kW                | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_ahu_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Elf0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhsf_shu_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_MWhyr              | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_ww_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcs0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qwwf0_kW                 | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_ahu0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qww_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf_lat_MWhyr           | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_sen_aru0_kW          | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcsf0_kW                 | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qcdataf_MWhyr            | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_fw0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eauxf_ww0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_lat_ahu_MWhyr        | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eaf_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| QHf_MWhyr                | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qww0_kW                  | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Egenf_cs0_kW             | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Eref0_kW                 | float  | [kW/yr]  |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+
| Qhs_em_ls_MWhyr          | float  | [MWh/yr] |                                                  | {0.0...n}    |
+--------------------------+--------+----------+--------------------------------------------------+--------------+

Solar Radiation: geometry
^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: 

**Format/Naming**: 

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/outputs/solar-radiation/B01.csv`` 

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| Column names /parameters | Type   | Unit | Description                                      | Valid Values            |
+==========================+========+======+==================================================+=========================+
| AREA_m2                  | float  | [m2] |                                                  | {0.0...n}               |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| BUILDING                 | string | [-]  | Unique building ID. It must start with a letter. | alphanumeric            |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| SURFACE                  | string | [-]  |                                                  | {srf0...srfn}           |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| TYPE                     | string | [-]  |                                                  | {walls, windows, roofs} |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| Xcoor                    | float  | [-]  | Describes the magnitude of the x vector??        | {0.0...n}               |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| Xdir                     | float  | [-]  | Describes direction of the x vector.             | {-1...1}                |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| Ycoor                    | float  | [-]  |                                                  | {0.0...n}               |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| Ydir                     | float  | [-]  | Describes direction of the y vector.             | {-1...1}                |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| Zcoor                    | float  | [-]  |                                                  | {0.0...n}               |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| Zdir                     | int    | [-]  | Describes direction of the Z vector.             | {-1...1}                |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+
| orientation              | string | [-]  |                                                  | {north...}              |
+--------------------------+--------+------+--------------------------------------------------+-------------------------+

Solar Radiation: surface_properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: This database stores the aggregated and averaged geometric properties of the north, east, south and west walls for each building. Therefore, each building has four dedicated rows attibuted each variable listed.

**Format/Naming**: csv file / properties_surfaces.csv

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/outputs/solar-radiation/properties_surfaces.csv`` 

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+---------+-------------------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                                 | Valid Values |
+==========================+========+=========+=============================================================+==============+
| Name                     | string | [-]     | Unique building ID. It must start with a letter.            | alphanumeric |
+--------------------------+--------+---------+-------------------------------------------------------------+--------------+
| Freeheight               | float  | [m]     | Surface height exposed to the sun                           | {0.0...n}    |
+--------------------------+--------+---------+-------------------------------------------------------------+--------------+
| FactorShade              | float  | [ratio] | Defines whether surface is facing the sun (1) or not (0)    | {0.0...1}    |
+--------------------------+--------+---------+-------------------------------------------------------------+--------------+
| height_ag                | float  | [m]     | Aggregated height of the walls.                             | {0.0...n}    |
+--------------------------+--------+---------+-------------------------------------------------------------+--------------+
| Shape_Leng               | float  | [m]     | Surface length                                              | {0.0...n}    |
+--------------------------+--------+---------+-------------------------------------------------------------+--------------+
| Awall_all                | float  | [m2]    | Total aggregated height of the walls, inclusive of windows. | {0.0...n}    |
+--------------------------+--------+---------+-------------------------------------------------------------+--------------+

Solar Radiation: radiation
^^^^^^^^^^^^^^^^^^^^^^^^^^
**Description**: 

**Format/Naming**: 

**Location (example)**: `` ..cea/examples/reference-case-open/baseline/outputs/solar-radiation/radiation.csv`` 

**Primary Interdependencies**: 

**Secondary Interdependencies**: 

+--------------------------+--------+---------+--------------------------------------------------+--------------+
| Column names /parameters | Type   | Unit    | Description                                      | Valid Values |
+==========================+========+=========+==================================================+==============+
| Name                     | string | [-]     | Unique building ID. It must start with a letter. | alphanumeric |
+--------------------------+--------+---------+--------------------------------------------------+--------------+
| T1...T8760               | float  | [Wh/m2] | Solar insolation for each hourly time step.      | {0.01...n}   |
+--------------------------+--------+---------+--------------------------------------------------+--------------+
