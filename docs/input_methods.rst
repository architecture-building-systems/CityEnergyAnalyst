
get_archetypes_properties
-------------------------

The following file is used by scripts: ['data-helper', 'demand']



.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:ARCHITECTURE**
    :header: "Variable", "Description"

     Es,Fraction of gross floor area with electrical demands. - Unit: [m2/m2]
     Ns,Fraction of net gross floor area. - Unit: [m2/m2]
     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R) - Unit: [-]
     type_cons,Type of construction. It relates to the contents of the default database of Envelope Properties: construction - Unit: [code]
     type_leak,Leakage level. It relates to the contents of the default database of Envelope Properties: leakage - Unit: [code]
     type_roof,Roof construction type (relates to values in Default Database Construction Properties) - Unit: [-]
     type_shade,Shading system type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_wall,Wall construction type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     type_win,Window type (relates to values in Default Database Construction Properties) - Unit: [m2/m2]
     void_deck,Number of floors (from the ground up) with an open envelope (default = 0) - Unit: [-]
     wwr_east,Window to wall ratio in in facades facing east - Unit: [m2/m2]
     wwr_north,Window to wall ratio in in facades facing north - Unit: [m2/m2]
     wwr_south,Window to wall ratio in in facades facing south - Unit: [m2/m2]
     wwr_west,Window to wall ratio in in facades facing west - Unit: [m2/m2]
     year_end,Upper limit of year interval where the building properties apply - Unit: [yr]
     year_start,Lower limit of year interval where the building properties apply - Unit: [yr]


.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:HVAC**
    :header: "Variable", "Description"

     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R) - Unit: [-]
     type_cs,Type of cooling supply system - Unit: [code]
     type_ctrl,Type of heating and cooling control systems (relates to values in Default Database HVAC Properties) - Unit: [code]
     type_dhw,Type of hot water supply system - Unit: [code]
     type_hs,Type of heating supply system - Unit: [code]
     type_vent,Type of ventilation strategy (relates to values in Default Database HVAC Properties) - Unit: [code]
     year_end,Upper limit of year interval where the building properties apply - Unit: [yr]
     year_start,Lower limit of year interval where the building properties apply - Unit: [yr]


.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:INDOOR_COMFORT**
    :header: "Variable", "Description"

     Code,Unique code for the material of the pipe. - Unit: [-]
     RH_max_pc,Upper bound of relative humidity - Unit: [%]
     RH_min_pc,Lower_bound of relative humidity - Unit: [%]
     Tcs_set_C,Setpoint temperature for cooling system - Unit: [C]
     Tcs_setb_C,Setback point of temperature for cooling system - Unit: [C]
     Ths_set_C,Setpoint temperature for heating system - Unit: [C]
     Ths_setb_C,Setback point of temperature for heating system - Unit: [C]
     Ve_lpspax,Indoor quality requirements of indoor ventilation per person - Unit: [l/s]


.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:INTERNAL_LOADS**
    :header: "Variable", "Description"

     Code,Unique code for the material of the pipe. - Unit: [-]
     Ea_Wm2,Peak specific electrical load due to computers and devices - Unit: [W/m2]
     Ed_Wm2,Peak specific electrical load due to servers/data centres - Unit: [W/m2]
     El_Wm2,Peak specific electrical load due to artificial lighting - Unit: [W/m2]
     Epro_Wm2,Peak specific electrical load due to industrial processes - Unit: [W/m2]
     Qcpro_Wm2,Peak specific process cooling load - Unit: [W/m2]
     Qcre_Wm2,Peak specific cooling load due to refrigeration (cooling rooms) - Unit: [W/m2]
     Qhpro_Wm2,Peak specific process heating load - Unit: [W/m2]
     Qs_Wpax,Peak sensible heat load of people - Unit: [W/pax]
     Vw_lpdpax,Peak specific fresh water consumption (includes cold and hot water) - Unit: [lpd]
     Vww_lpdpax,Peak specific daily hot water consumption - Unit: [lpd]
     X_ghpax,Moisture released by occupancy at peak conditions - Unit: [gh/kg/p]


.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:SUPPLY**
    :header: "Variable", "Description"

     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R) - Unit: [-]
     type_cs,Type of cooling supply system - Unit: [code]
     type_dhw,Type of hot water supply system - Unit: [code]
     type_el,Type of electrical supply system - Unit: [code]
     type_hs,Type of heating supply system - Unit: [code]
     year_end,Upper limit of year interval where the building properties apply - Unit: [yr]
     year_start,Lower limit of year interval where the building properties apply - Unit: [yr]


get_archetypes_schedules
------------------------

The following file is used by scripts: ['data-helper', 'demand']



.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:COOLROOM**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:FOODSTORE**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:GYM**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:HOSPITAL**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Saturday_4,TODO - Unit: TODO
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_4,TODO - Unit: TODO
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_4,TODO - Unit: TODO
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:HOTEL**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:INDUSTRIAL**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Saturday_4,TODO - Unit: TODO
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_4,TODO - Unit: TODO
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_4,TODO - Unit: TODO
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:LAB**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Saturday_4,TODO - Unit: TODO
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_4,TODO - Unit: TODO
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_4,TODO - Unit: TODO
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:LIBRARY**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:MULTI_RES**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:MUSEUM**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:OFFICE**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:PARKING**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:RESTAURANT**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:RETAIL**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SCHOOL**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SERVERROOM**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SINGLE_RES**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SWIMMING**
    :header: "Variable", "Description"

     Saturday_1,Probability of maximum occupancy per hour on Saturday - Unit: [p/p]
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Sunday_1,Probability of maximum occupancy per hour on Sunday - Unit: [p/p]
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     Weekday_1,Probability of maximum occupancy per hour in a weekday - Unit: [p/p]
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour - Unit: [p/p]
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour - Unit: [p/p]
     density,m2 per person - Unit: [m2/p]
     month,Probability of use for the month - Unit: [p/p]


get_archetypes_system_controls
------------------------------

The following file is used by scripts: ['demand']



.. csv-table:: **databases/ch/archetypes/system_controls.xlsx:heating_cooling**
    :header: "Variable", "Description"

     cooling-season-end,Last day of the cooling season - Unit: [-]
     cooling-season-start,Day on which the cooling season starts - Unit: [-]
     has-cooling-season,Defines whether the scenario has a cooling season. - Unit: [-]
     has-heating-season,Defines whether the scenario has a heating season. - Unit: [-]
     heating-season-end,Last day of the heating season - Unit: [-]
     heating-season-start,Day on which the heating season starts - Unit: [-]


get_building_age
----------------

The following file is used by scripts: ['data-helper', 'emissions', 'demand']



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

The following file is used by scripts: ['data-helper', 'emissions', 'demand']



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



.. csv-table:: **databases/ch/systems/air_conditioning_systems.xls:controller**
    :header: "Variable", "Description"



.. csv-table:: **databases/ch/systems/air_conditioning_systems.xls:cooling**
    :header: "Variable", "Description"



.. csv-table:: **databases/ch/systems/air_conditioning_systems.xls:dhw**
    :header: "Variable", "Description"



.. csv-table:: **databases/ch/systems/air_conditioning_systems.xls:heating**
    :header: "Variable", "Description"



.. csv-table:: **databases/ch/systems/air_conditioning_systems.xls:ventilation**
    :header: "Variable", "Description"



get_envelope_systems
--------------------

The following file is used by scripts: ['radiation', 'demand']



.. csv-table:: **databases/ch/systems/envelope_systems.xls:CONSTRUCTION**
    :header: "Variable", "Description"

     Cm_Af,Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790. - Unit: [J/Km2]
     Description,Describes the source of the benchmark standards. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]


.. csv-table:: **databases/ch/systems/envelope_systems.xls:LEAKAGE**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     n50,Air exchanges per hour at a pressure of 50 Pa. - Unit: [1/h]


.. csv-table:: **databases/ch/systems/envelope_systems.xls:ROOF**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     U_roof,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. - Unit: [-]
     a_roof,Solar absorption coefficient. Defined according to ISO 13790. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     e_roof,Emissivity of external surface. Defined according to ISO 13790. - Unit: [-]
     r_roof,Reflectance in the Red spectrum. Defined according Radiance. (long-wave) - Unit: [-]


.. csv-table:: **databases/ch/systems/envelope_systems.xls:SHADING**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     rf_sh,Shading coefficient when shading device is active. Defined according to ISO 13790. - Unit: [-]


.. csv-table:: **databases/ch/systems/envelope_systems.xls:WALL**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     U_base,Thermal transmittance of basement including linear losses (+10%). Defined according to ISO 13790. - Unit: [-]
     U_wall,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. - Unit: [-]
     a_wall,Solar absorption coefficient. Defined according to ISO 13790. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     e_wall,Emissivity of external surface. Defined according to ISO 13790. - Unit: [-]
     r_wall,Reflectance in the Red spectrum. Defined according Radiance. (long-wave) - Unit: [-]


.. csv-table:: **databases/ch/systems/envelope_systems.xls:WINDOW**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     G_win,Solar heat gain coefficient. Defined according to ISO 13790. - Unit: [-]
     U_win,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     e_win,Emissivity of external surface. Defined according to ISO 13790. - Unit: [-]


get_life_cycle_inventory_building_systems
-----------------------------------------

The following file is used by scripts: ['emissions']



.. csv-table:: **databases/sg/lifecycle/lca_buildings.xlsx:EMBODIED_EMISSIONS**
    :header: "Variable", "Description"

     Excavation,Typical embodied emissions for site excavation. - Unit: [kg CO2-eq/m2]
     Floor_g,Typical embodied emissions of the ground floor. - Unit: [kg CO2-eq/m2]
     Floor_int,Typical embodied emissions of the interior floor. - Unit: [kg CO2-eq/m2]
     Roof,Typical embodied emissions of the roof. - Unit: [kg CO2-eq/m2]
     Services,Typical embodied emissions of the building services. - Unit: [kg CO2-eq/m2]
     Wall_ext_ag,Typical embodied emissions of the exterior above ground walls. - Unit: [kg CO2-eq/m2]
     Wall_ext_bg,Typical embodied emissions of the exterior below ground walls. - Unit: [kg CO2-eq/m2]
     Wall_int_nosup,Typical embodied emissions of the interior above ground walls. - Unit: [kg CO2-eq/m2]
     Wall_int_sup,Typical embodied emissions of the interior below ground walls. - Unit: [kg CO2-eq/m2]
     Win_ext,Typical embodied emissions of the external glazing. - Unit: [kg CO2-eq/m2]
     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R) - Unit: [-]
     year_end,Upper limit of year interval where the building properties apply - Unit: [yr]
     year_start,Lower limit of year interval where the building properties apply - Unit: [yr]


.. csv-table:: **databases/sg/lifecycle/lca_buildings.xlsx:EMBODIED_ENERGY**
    :header: "Variable", "Description"

     Excavation,Typical embodied energy for site excavation. - Unit: [MJ oil-eq/m2]
     Floor_g,Typical embodied energy of the ground floor. - Unit: [MJ oil-eq/m2]
     Floor_int,Typical embodied energy of the interior floor. - Unit: [MJ oil-eq/m2]
     Roof,Typical embodied energy of the roof. - Unit: [MJ oil-eq/m2]
     Services,Typical embodied energy of the building services. - Unit: [MJ oil-eq/m2]
     Wall_ext_ag,Typical embodied energy of the exterior above ground walls. - Unit: [MJ oil-eq/m2]
     Wall_ext_bg,Typical embodied energy of the exterior below ground walls. - Unit: [MJ oil-eq/m2]
     Wall_int_nosup,nan - Unit: [MJ oil-eq/m2]
     Wall_int_sup,nan - Unit: [MJ oil-eq/m2]
     Win_ext,Typical embodied energy of the external glazing. - Unit: [MJ oil-eq/m2]
     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R) - Unit: [-]
     year_end,Upper limit of year interval where the building properties apply - Unit: [yr]
     year_start,Lower limit of year interval where the building properties apply - Unit: [yr]


get_life_cycle_inventory_supply_systems
---------------------------------------

The following file is used by scripts: ['demand', 'operation-costs', 'emissions']



.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:COOLING**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     eff_cs,TODO - Unit: TODO
     reference,nan - Unit: [-]
     scale_cs,TODO - Unit: TODO
     source_cs,TODO - Unit: TODO


.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:DHW**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     eff_dhw,TODO - Unit: TODO
     reference,nan - Unit: [-]
     scale_dhw,TODO - Unit: TODO
     source_dhw,TODO - Unit: TODO


.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:ELECTRICITY**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     eff_el,TODO - Unit: TODO
     reference,nan - Unit: [-]
     scale_el,TODO - Unit: TODO
     source_el,TODO - Unit: TODO


.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:HEATING**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     eff_hs,TODO - Unit: TODO
     reference,nan - Unit: [-]
     scale_hs,TODO - Unit: TODO
     source_hs,TODO - Unit: TODO


.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:RESOURCES**
    :header: "Variable", "Description"

     CO2,Refers to the equivalent CO2 required to run the heating or cooling system. - Unit: [kg/kWh]
     Description,Describes the source of the benchmark standards. - Unit: [-]
     PEN,Refers to the amount of primary energy needed (PEN) to run the heating or cooling system. - Unit: [kWh/kWh]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     costs_kWh,Refers to the financial costs required to run the heating or cooling system. - Unit: [$/kWh]
     reference,nan - Unit: [-]


get_street_network
------------------

The following file is used by scripts: ['network-layout']



.. csv-table:: **inputs/networks/streets.shp**
    :header: "Variable", "Description"

     FID,TODO - Unit: TODO
     geometry,TODO - Unit: TODO


get_supply_systems
------------------

The following file is used by scripts: ['thermal-network', 'photovoltaic', 'photovoltaic-thermal', 'solar-collector']



.. csv-table:: **databases/ch/systems/supply_systems.xls:Absorption_chiller**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     a_e,TODO - Unit: TODO
     a_g,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     e_e,TODO - Unit: TODO
     e_g,TODO - Unit: TODO
     el_W,TODO - Unit: TODO
     m_cw,TODO - Unit: TODO
     m_hw,TODO - Unit: TODO
     r_e,TODO - Unit: TODO
     r_g,TODO - Unit: TODO
     s_e,TODO - Unit: TODO
     s_g,TODO - Unit: TODO
     type,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:BH**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:Boiler**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:CCGT**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:CT**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:Chiller**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:FC**
    :header: "Variable", "Description"

      Assumptions,TODO - Unit: TODO
     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:Furnace**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:HEX**
    :header: "Variable", "Description"

     Currency,Defines the unit of currency used to create the cost estimations (year specific). E.g. USD-2015. - Unit: [-]
     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     a_p,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     b_p,TODO - Unit: TODO
     c,TODO - Unit: TODO
     c_p,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     d,TODO - Unit: TODO
     d_p,TODO - Unit: TODO
     e,TODO - Unit: TODO
     e_p,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:HP**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:PV**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     PV_Bref,TODO - Unit: TODO
     PV_a0,TODO - Unit: TODO
     PV_a1,TODO - Unit: TODO
     PV_a2,TODO - Unit: TODO
     PV_a3,TODO - Unit: TODO
     PV_a4,TODO - Unit: TODO
     PV_n,TODO - Unit: TODO
     PV_noct,TODO - Unit: TODO
     PV_th,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     misc_losses,TODO - Unit: TODO
     module_length_m,TODO - Unit: TODO
     type,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:PVT**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:Piping**
    :header: "Variable", "Description"

     Currency ,TODO - Unit: TODO
     Description,Describes the source of the benchmark standards. - Unit: [-]
     Diameter_max,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin. - Unit: [-]
     Diameter_min,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin. - Unit: [-]
     Investment,Typical cost of investment for a given pipe diameter. - Unit: [$/m]
     Unit,Defines the unit of measurement for the diameter values. - Unit: [mm]
     assumption,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:Pricing**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     assumption,TODO - Unit: TODO
     currency,TODO - Unit: TODO
     value,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:Pump**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:SC**
    :header: "Variable", "Description"

     C_eff,TODO - Unit: TODO
     Cp_fluid,TODO - Unit: TODO
     Description,Describes the source of the benchmark standards. - Unit: [-]
     IAM_d,TODO - Unit: TODO
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     aperture_area_ratio,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     c1,TODO - Unit: TODO
     c2,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     dP1,TODO - Unit: TODO
     dP2,TODO - Unit: TODO
     dP3,TODO - Unit: TODO
     dP4,TODO - Unit: TODO
     e,TODO - Unit: TODO
     mB0_r,TODO - Unit: TODO
     mB_max_r,TODO - Unit: TODO
     mB_min_r,TODO - Unit: TODO
     module_area_m2,TODO - Unit: TODO
     module_length_m,TODO - Unit: TODO
     n0,TODO - Unit: TODO
     t_max,TODO - Unit: TODO
     type,TODO - Unit: TODO
     unit,TODO - Unit: TODO


.. csv-table:: **databases/ch/systems/supply_systems.xls:TES**
    :header: "Variable", "Description"

     Description,Describes the source of the benchmark standards. - Unit: [-]
     IR_%,TODO - Unit: TODO
     LT_yr,TODO - Unit: TODO
     O&M_%,TODO - Unit: TODO
     a,TODO - Unit: TODO
     assumption,TODO - Unit: TODO
     b,TODO - Unit: TODO
     c,TODO - Unit: TODO
     cap_max,TODO - Unit: TODO
     cap_min,TODO - Unit: TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     currency,TODO - Unit: TODO
     d,TODO - Unit: TODO
     e,TODO - Unit: TODO
     unit ,TODO - Unit: TODO


get_surroundings_geometry
-------------------------

The following file is used by scripts: ['radiation']



.. csv-table:: **inputs/building-geometry/surroundings.shp**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     floors_ag,Number of floors above ground (incl. ground floor) - Unit: [-]
     geometry,TODO - Unit: TODO
     height_ag,Height above ground (incl. ground floor) - Unit: [m]


get_terrain
-----------

The following file is used by scripts: ['radiation']



.. csv-table:: **inputs/topography/terrain.tif**
    :header: "Variable", "Description"

     Mock_variable,TODO - Unit: TODO


get_thermal_networks
--------------------

The following file is used by scripts: ['thermal-network']



.. csv-table:: **databases/ch/systems/thermal_networks.xls:MATERIAL PROPERTIES**
    :header: "Variable", "Description"

     Cp_JkgK,Heat capacity of transmission fluid. - Unit: [J/kgK]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     lambda_WmK,Thermal conductivity - Unit: [W/mK]
     material,TODO - Unit: TODO
     rho_kgm3,Density of transmission fluid. - Unit: [kg/m3]


.. csv-table:: **databases/ch/systems/thermal_networks.xls:PIPING CATALOG**
    :header: "Variable", "Description"

     D_ext_m,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin. - Unit: [m]
     D_ins_m,Defines the pipe insulation diameter for the nominal diameter (DN) bin. - Unit: [m]
     D_int_m,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin. - Unit: [m]
     Pipe_DN,Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter. - Unit: [DN#]
     Vdot_max_m3s,Maximum volume flow rate for the nominal diameter (DN) bin. - Unit: [m3/s]
     Vdot_min_m3s,Minimum volume flow rate for the nominal diameter (DN) bin. - Unit: [m3/s]


get_zone_geometry
-----------------

The following file is used by scripts: ['photovoltaic', 'photovoltaic-thermal', 'emissions', 'network-layout', 'radiation', 'demand', 'solar-collector']



.. csv-table:: **inputs/building-geometry/zone.shp**
    :header: "Variable", "Description"

     Name,Unique building ID. It must start with a letter. - Unit: [-]
     floors_ag,Number of floors above ground (incl. ground floor) - Unit: [-]
     floors_bg,Number of floors below ground (basement, etc) - Unit: [-]
     geometry,TODO - Unit: TODO
     height_ag,Aggregated height of the walls. - Unit: [m]
     height_bg,Height below ground (basement, etc) - Unit: [m]

