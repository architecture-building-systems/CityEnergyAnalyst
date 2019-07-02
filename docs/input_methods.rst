
get_archetypes_properties
-------------------------
The following file is used by scripts: ['data-helper', 'demand']


.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:ARCHITECTURE**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Es,TODO,TODO,TODO,TODO
     Hs,Fraction of gross floor area air-conditioned.,[m2/m2],float,{0.0...1}
     Ns,TODO,TODO,TODO,TODO
     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
     type_cons,Type of construction. It relates to the contents of the default database of Envelope Properties: construction,[code],string,{T1...Tn}
     type_leak,Leakage level. It relates to the contents of the default database of Envelope Properties: leakage,[code],string,{T1...Tn}
     type_roof,Roof construction type (relates to values in Default Database Construction Properties),[-],string,{T1...Tn}
     type_shade,Shading system type (relates to values in Default Database Construction Properties),[m2/m2],float,{T1...Tn}
     type_wall,Wall construction type (relates to values in Default Database Construction Properties),[m2/m2],float,{T1...Tn}
     type_win,Window type (relates to values in Default Database Construction Properties),[m2/m2],float,{T1...Tn}
     void_deck,Share of floors with an open envelope (default = 0),[floor/floor],float,{0.0...1}
     wwr_east,Window to wall ratio in in facades facing east,[m2/m2],float,{0.0...1}
     wwr_north,Window to wall ratio in in facades facing north,[m2/m2],float,{0.0...1}
     wwr_south,Window to wall ratio in in facades facing south,[m2/m2],float,{0.0...1}
     wwr_west,Window to wall ratio in in facades facing west,[m2/m2],float,{0.0...1}
     year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
     year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}

.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:HVAC**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
     type_cs,Type of cooling supply system,[code],string,{T0...Tn}
     type_ctrl,Type of heating and cooling control systems (relates to values in Default Database HVAC Properties),[code],string,{T1...Tn}
     type_dhw,Type of hot water supply system,[code],string,{T0...Tn}
     type_hs,Type of heating supply system,[code],string,{T0...Tn}
     type_vent,Type of ventilation strategy (relates to values in Default Database HVAC Properties),[code],string,{T1...Tn}
     year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
     year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}

.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:INDOOR_COMFORT**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Code,Unique code for the material of the pipe.,[-],string,[-]
     Tcs_set_C,Setpoint temperature for cooling system,[C],float,{0.0...n}
     Tcs_setb_C,Setback point of temperature for cooling system,[C],float,{0.0...n}
     Ths_set_C,Setpoint temperature for heating system,[C],float,{0.0...n}
     Ths_setb_C,Setback point of temperature for heating system,[C],float,{0.0...n}
     Ve_lps,Indoor quality requirements of indoor ventilation per person,[l/s],float,{0.0...n}
     rhum_max_pc,TODO,TODO,TODO,TODO
     rhum_min_pc,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:INTERNAL_LOADS**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Code,Unique code for the material of the pipe.,[-],string,[-]
     Ea_Wm2,Peak specific electrical load due to computers and devices,[W/m2],float,{0.0...n}
     Ed_Wm2,Peak specific electrical load due to servers/data centres,[W/m2],float,{0.0...n}
     El_Wm2,Peak specific electrical load due to artificial lighting,[W/m2],float,{0.0...n}
     Epro_Wm2,Peak specific electrical load due to industrial processes,[W/m2],string,{0.0...n}
     Qcre_Wm2,TODO,TODO,TODO,TODO
     Qhpro_Wm2,Peak specific due to process heat,[W/m2],float,{0.0...n}
     Qs_Wp,TODO,TODO,TODO,TODO
     Vw_lpd,Peak specific fresh water consumption (includes cold and hot water),[lpd],float,{0.0...n}
     Vww_lpd,Peak specific daily hot water consumption,[lpd],float,{0.0...n}
     X_ghp,Moisture released by occupancy at peak conditions,[gh/kg/p],float,{0.0...n}

.. csv-table:: **databases/ch/archetypes/construction_properties.xlsx:SUPPLY**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
     type_cs,Type of cooling supply system,[code],string,{T0...Tn}
     type_dhw,Type of hot water supply system,[code],string,{T0...Tn}
     type_el,Type of electrical supply system,[code],string,{T0...Tn}
     type_hs,Type of heating supply system,[code],string,{T0...Tn}
     year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
     year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}


get_archetypes_schedules
------------------------
The following file is used by scripts: ['data-helper', 'demand']


.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:COOLROOM**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:FOODSTORE**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:GYM**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:HOSPITAL**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_4,TODO,TODO,TODO,TODO
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_4,TODO,TODO,TODO,TODO
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_4,TODO,TODO,TODO,TODO
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:HOTEL**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:INDUSTRIAL**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_4,TODO,TODO,TODO,TODO
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_4,TODO,TODO,TODO,TODO
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_4,TODO,TODO,TODO,TODO
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:LAB**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_4,TODO,TODO,TODO,TODO
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_4,TODO,TODO,TODO,TODO
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_4,TODO,TODO,TODO,TODO
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:LIBRARY**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:MULTI_RES**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:MUSEUM**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:OFFICE**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:PARKING**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:RESTAURANT**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:RETAIL**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SCHOOL**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SERVERROOM**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SINGLE_RES**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}

.. csv-table:: **databases/ch/archetypes/occupancy_schedules.xlsx:SWIMMING**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
     Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
     Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
     Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
     Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
     density,m2 per person,[m2/p],float,{0.0...n}
     month,Probability of use for the month,[p/p],float,{0.0...1}


get_archetypes_system_controls
------------------------------
The following file is used by scripts: ['demand']


.. csv-table:: **databases/ch/archetypes/system_controls.xlsx:heating_cooling**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     cooling-season-end,Last day of the cooling season,[-],date,mm-dd
     cooling-season-start,Day on which the cooling season starts,[-],date,mm-dd
     has-cooling-season,Defines whether the scenario has a cooling season.,[-],Boolean,{TRUE/FALSE}
     has-heating-season,Defines whether the scenario has a heating season.,[-],Boolean,{TRUE/FALSE}
     heating-season-end,Last day of the heating season,[-],date,mm-dd
     heating-season-start,Day on which the heating season starts,[-],date,mm-dd


get_building_age
----------------
The following file is used by scripts: ['data-helper', 'emissions', 'demand']


.. csv-table:: **inputs/building-properties/age.dbf**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     HVAC,Year of last retrofit of HVAC systems (0 if none),[-],int,{0...n}
     Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
     basement,Year of last retrofit of basement (0 if none),[-],int,{0...n}
     built,Construction year,[-],int,{0...n}
     envelope,Year of last retrofit of building facades (0 if none),[-],int,{0...n}
     partitions,Year of last retrofit of internal wall partitions(0 if none),[-],int,{0...n}
     roof,Year of last retrofit of roof (0 if none),[-],int,{0...n}
     windows,Year of last retrofit of windows (0 if none),[-],int,{0...n}


get_building_occupancy
----------------------
The following file is used by scripts: ['data-helper', 'emissions', 'demand']


.. csv-table:: **inputs/building-properties/occupancy.dbf**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     COOLROOM,Refrigeration rooms,m2,float,{0.0...1}
     FOODSTORE,Food stores,m2,float,{0.0...1}
     GYM,Gymnasiums,m2,float,{0.0...1}
     HOSPITAL,Hospitals,m2,float,{0.0...1}
     HOTEL,Hotels,m2,float,{0.0...1}
     INDUSTRIAL,Light industry,m2,float,{0.0...1}
     LIBRARY,Libraries,m2,float,{0.0...1}
     MULTI_RES,Residential (multiple dwellings),m2,TODO,TODO
     Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
     OFFICE,Offices,m2,float,{0.0...1}
     PARKING,Parking,m2,float,{0.0...1}
     RESTAURANT,Restaurants,m2,float,{0.0...1}
     RETAIL,Retail,m2,float,{0.0...1}
     SCHOOL,Schools,m2,float,{0.0...1}
     SERVERROOM,Data center,m2,float,{0.0...1}
     SINGLE_RES,Residential (single dwellings),m2,float,{0.0...1}
     SWIMMING,Swimming halls,m2,float,{0.0...1}


get_data_benchmark
------------------
The following file is used by scripts: ['emissions']


.. csv-table:: **databases/sg/benchmarks/benchmark_2000w.xls:EMBODIED**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
     CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
     CO2_today,Present CO2 production,[-],float,{0.0...n}
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
     NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
     NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
     PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
     PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
     PEN_today,Present primary energy demand,[-],float,{0.0...n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy

.. csv-table:: **databases/sg/benchmarks/benchmark_2000w.xls:MOBILITY**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
     CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
     CO2_today,Present CO2 production,[-],float,{0.0...n}
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
     NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
     NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
     PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
     PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
     PEN_today,Present primary energy demand,[-],float,{0.0...n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy

.. csv-table:: **databases/sg/benchmarks/benchmark_2000w.xls:OPERATION**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
     CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
     CO2_today,Present CO2 production,[-],float,{0.0...n}
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
     NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
     NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
     PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
     PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
     PEN_today,Present primary energy demand,[-],float,{0.0...n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy

.. csv-table:: **databases/sg/benchmarks/benchmark_2000w.xls:TOTAL**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
     CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
     CO2_today,Present CO2 production,[-],float,{0.0...n}
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
     NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
     NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
     PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
     PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
     PEN_today,Present primary energy demand,[-],float,{0.0...n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy


get_district_geometry
---------------------
The following file is used by scripts: ['radiation-daysim']


.. csv-table:: **inputs/building-geometry/district.shp**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
     floors_ag,TODO,TODO,TODO,TODO
     floors_bg,TODO,TODO,TODO,TODO
     geometry,TODO,TODO,TODO,TODO
     height_ag,Aggregated height of the walls.,[m],float,{0.0...n}
     height_bg,TODO,TODO,TODO,TODO


get_envelope_systems
--------------------
The following file is used by scripts: ['radiation-daysim', 'demand']


.. csv-table:: **databases/ch/systems/envelope_systems.xls:CONSTRUCTION**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Cm_Af,Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790.,[J/Km2],float,{0.0...1}
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy

.. csv-table:: **databases/ch/systems/envelope_systems.xls:LEAKAGE**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     n50,Air exchanges per hour at a pressure of 50 Pa.,[1/h],float,{0.0...10}

.. csv-table:: **databases/ch/systems/envelope_systems.xls:ROOF**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     U_roof,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.1...n}
     a_roof,Solar absorption coefficient. Defined according to ISO 13790.,[-],float,{0.0...1}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     e_roof,Emissivity of external surface. Defined according to ISO 13790.,[-],float,{0.0...1}
     r_roof,Reflectance in the Red spectrum. Defined according Radiance. (long-wave),[-],float,{0.0...1}

.. csv-table:: **databases/ch/systems/envelope_systems.xls:SHADING**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     rf_sh,Shading coefficient when shading device is active. Defined according to ISO 13790.,[-],float,{0.0...1}

.. csv-table:: **databases/ch/systems/envelope_systems.xls:WALL**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     U_base,Thermal transmittance of basement including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.0...1}
     U_wall,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.1...n}
     a_wall,Solar absorption coefficient. Defined according to ISO 13790.,[-],float,{0.0...1}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     e_wall,Emissivity of external surface. Defined according to ISO 13790.,[-],float,{0.0...1}
     r_wall,Reflectance in the Red spectrum. Defined according Radiance. (long-wave),[-],float,{0.0...1}

.. csv-table:: **databases/ch/systems/envelope_systems.xls:WINDOW**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     G_win,Solar heat gain coefficient. Defined according to ISO 13790.,[-],float,{0.0...1}
     U_win,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.1...n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     e_win,Emissivity of external surface. Defined according to ISO 13790.,[-],float,{0.0...1}


get_life_cycle_inventory_building_systems
-----------------------------------------
The following file is used by scripts: ['emissions']


.. csv-table:: **databases/sg/lifecycle/lca_buildings.xlsx:EMBODIED_EMISSIONS**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Excavation,Typical embodied energy for site excavation.,[GJ],float,{0.0....n}
     Floor_g,Typical embodied energy of the ground floor.,[GJ],float,{0.0....n}
     Floor_int,Typical embodied energy of the interior floor.,[GJ],float,{0.0....n}
     Roof,Typical embodied energy of the roof.,[GJ],float,{0.0....n}
     Services,Typical embodied energy of the building services.,[GJ],float,{0.0....n}
     Wall_ext_ag,Typical embodied energy of the exterior above ground walls.,[GJ],float,{0.0....n}
     Wall_ext_bg,Typical embodied energy of the exterior below ground walls.,[GJ],float,{0.0....n}
     Wall_int_nosup,nan,[GJ],float,{0.0....n}
     Wall_int_sup,nan,[GJ],float,{0.0....n}
     Win_ext,Typical embodied energy of the external glazing.,[GJ],float,{0.0....n}
     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
     year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
     year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}

.. csv-table:: **databases/sg/lifecycle/lca_buildings.xlsx:EMBODIED_ENERGY**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Excavation,Typical embodied energy for site excavation.,[GJ],float,{0.0....n}
     Floor_g,Typical embodied energy of the ground floor.,[GJ],float,{0.0....n}
     Floor_int,Typical embodied energy of the interior floor.,[GJ],float,{0.0....n}
     Roof,Typical embodied energy of the roof.,[GJ],float,{0.0....n}
     Services,Typical embodied energy of the building services.,[GJ],float,{0.0....n}
     Wall_ext_ag,Typical embodied energy of the exterior above ground walls.,[GJ],float,{0.0....n}
     Wall_ext_bg,Typical embodied energy of the exterior below ground walls.,[GJ],float,{0.0....n}
     Wall_int_nosup,nan,[GJ],float,{0.0....n}
     Wall_int_sup,nan,[GJ],float,{0.0....n}
     Win_ext,Typical embodied energy of the external glazing.,[GJ],float,{0.0....n}
     building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
     year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
     year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}


get_life_cycle_inventory_supply_systems
---------------------------------------
The following file is used by scripts: ['demand', 'operation-costs', 'emissions']


.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:COOLING**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     eff_cs,TODO,TODO,TODO,TODO
     reference,nan,[-],string,[-]
     scale_cs,TODO,TODO,TODO,TODO
     source_cs,TODO,TODO,TODO,TODO

.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:DHW**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     eff_dhw,TODO,TODO,TODO,TODO
     reference,nan,[-],string,[-]
     scale_dhw,TODO,TODO,TODO,TODO
     source_dhw,TODO,TODO,TODO,TODO

.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:ELECTRICITY**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     eff_el,TODO,TODO,TODO,TODO
     reference,nan,[-],string,[-]
     scale_el,TODO,TODO,TODO,TODO
     source_el,TODO,TODO,TODO,TODO

.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:HEATING**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     eff_hs,TODO,TODO,TODO,TODO
     reference,nan,[-],string,[-]
     scale_hs,TODO,TODO,TODO,TODO
     source_hs,TODO,TODO,TODO,TODO

.. csv-table:: **databases/sg/lifecycle/lca_infrastructure.xlsx:RESOURCES**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     CO2,Refers to the equivalent CO2 required to run the heating or cooling system.,[kg/kWh],float,{0.0....n}
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     PEN,Refers to the amount of primary energy needed (PEN) to run the heating or cooling system.,[kWh/kWh],float,{0.0....n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     costs_kWh,Refers to the financial costs required to run the heating or cooling system.,[$/kWh],float,{0.0....n}
     reference,nan,[-],string,[-]


get_street_network
------------------
The following file is used by scripts: ['network-layout']


.. csv-table:: **inputs/networks/streets.shp**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     FID,TODO,TODO,TODO,TODO
     geometry,TODO,TODO,TODO,TODO


get_supply_systems
------------------
The following file is used by scripts: ['thermal-network', 'photovoltaic', 'photovoltaic-thermal', 'solar-collector']


.. csv-table:: **databases/ch/systems/supply_systems.xls:Absorption_chiller**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     a_e,TODO,TODO,TODO,TODO
     a_g,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     e_e,TODO,TODO,TODO,TODO
     e_g,TODO,TODO,TODO,TODO
     el_W,TODO,TODO,TODO,TODO
     m_cw,TODO,TODO,TODO,TODO
     m_hw,TODO,TODO,TODO,TODO
     r_e,TODO,TODO,TODO,TODO
     r_g,TODO,TODO,TODO,TODO
     s_e,TODO,TODO,TODO,TODO
     s_g,TODO,TODO,TODO,TODO
     type,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:BH**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:Boiler**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:CCGT**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:CT**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:Chiller**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:FC**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

      Assumptions,TODO,TODO,TODO,TODO
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:Furnace**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:HEX**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Currency,Defines the unit of currency used to create the cost estimations (year specific). E.g. USD-2015.,[-],string,[-]
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     a_p,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     b_p,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     c_p,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     d,TODO,TODO,TODO,TODO
     d_p,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     e_p,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:HP**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:PV**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     PV_Bref,TODO,TODO,TODO,TODO
     PV_a0,TODO,TODO,TODO,TODO
     PV_a1,TODO,TODO,TODO,TODO
     PV_a2,TODO,TODO,TODO,TODO
     PV_a3,TODO,TODO,TODO,TODO
     PV_a4,TODO,TODO,TODO,TODO
     PV_n,TODO,TODO,TODO,TODO
     PV_noct,TODO,TODO,TODO,TODO
     PV_th,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     misc_losses,TODO,TODO,TODO,TODO
     module_length_m,TODO,TODO,TODO,TODO
     type,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:PVT**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:Piping**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Currency ,TODO,TODO,TODO,TODO
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     Diameter_max,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.,[-],float,{0.0....n}
     Diameter_min,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.,[-],float,{0.0....n}
     Investment,Typical cost of investment for a given pipe diameter.,[$/m],float,{0.0....n}
     Unit,Defines the unit of measurement for the diameter values.,[mm],string,[-]
     assumption,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:Pricing**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     assumption,TODO,TODO,TODO,TODO
     currency,TODO,TODO,TODO,TODO
     value,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:Pump**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:SC**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     C_eff,TODO,TODO,TODO,TODO
     Cp_fluid,TODO,TODO,TODO,TODO
     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IAM_d,TODO,TODO,TODO,TODO
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     aperture_area_ratio,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     c1,TODO,TODO,TODO,TODO
     c2,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     dP1,TODO,TODO,TODO,TODO
     dP2,TODO,TODO,TODO,TODO
     dP3,TODO,TODO,TODO,TODO
     dP4,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     mB0_r,TODO,TODO,TODO,TODO
     mB_max_r,TODO,TODO,TODO,TODO
     mB_min_r,TODO,TODO,TODO,TODO
     module_area_m2,TODO,TODO,TODO,TODO
     module_length_m,TODO,TODO,TODO,TODO
     n0,TODO,TODO,TODO,TODO
     t_max,TODO,TODO,TODO,TODO
     type,TODO,TODO,TODO,TODO
     unit,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/supply_systems.xls:TES**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     IR_%,TODO,TODO,TODO,TODO
     LT_yr,TODO,TODO,TODO,TODO
     O&M_%,TODO,TODO,TODO,TODO
     a,TODO,TODO,TODO,TODO
     assumption,TODO,TODO,TODO,TODO
     b,TODO,TODO,TODO,TODO
     c,TODO,TODO,TODO,TODO
     cap_max,TODO,TODO,TODO,TODO
     cap_min,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     currency,TODO,TODO,TODO,TODO
     d,TODO,TODO,TODO,TODO
     e,TODO,TODO,TODO,TODO
     unit ,TODO,TODO,TODO,TODO


get_technical_emission_systems
------------------------------
The following file is used by scripts: ['demand']


.. csv-table:: **databases/ch/systems/emission_systems.xls:controller**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     dT_Qcs,TODO,TODO,TODO,TODO
     dT_Qhs,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/emission_systems.xls:cooling**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     Qcsmax_Wm2,TODO,TODO,TODO,TODO
     Tc_sup_air_ahu_C,TODO,TODO,TODO,TODO
     Tc_sup_air_aru_C,TODO,TODO,TODO,TODO
     Tscs0_ahu_C,TODO,TODO,TODO,TODO
     Tscs0_aru_C,TODO,TODO,TODO,TODO
     Tscs0_scu_C,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     dTcs0_ahu_C,TODO,TODO,TODO,TODO
     dTcs0_aru_C,TODO,TODO,TODO,TODO
     dTcs0_scu_C,TODO,TODO,TODO,TODO
     dTcs_C,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/emission_systems.xls:dhw**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     Qwwmax_Wm2,Maximum heat flow permitted by the distribution system per m2 of the exchange interface (e.g. floor/radiator heating area).,[W/m2],float,{0.0....n}
     Tsww0_C,Typical supply water temperature.,[C],float,{0.0....n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy

.. csv-table:: **databases/ch/systems/emission_systems.xls:heating**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     Qhsmax_Wm2,TODO,TODO,TODO,TODO
     Th_sup_air_ahu_C,TODO,TODO,TODO,TODO
     Th_sup_air_aru_C,TODO,TODO,TODO,TODO
     Tshs0_ahu_C,TODO,TODO,TODO,TODO
     Tshs0_aru_C,TODO,TODO,TODO,TODO
     Tshs0_shu_C,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     dThs0_ahu_C,TODO,TODO,TODO,TODO
     dThs0_aru_C,TODO,TODO,TODO,TODO
     dThs0_shu_C,TODO,TODO,TODO,TODO
     dThs_C,TODO,TODO,TODO,TODO

.. csv-table:: **databases/ch/systems/emission_systems.xls:ventilation**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Description,Describes the source of the benchmark standards.,[-],string,[-]
     ECONOMIZER,TODO,TODO,TODO,TODO
     HEAT_REC,TODO,TODO,TODO,TODO
     MECH_VENT,TODO,TODO,TODO,TODO
     NIGHT_FLSH,TODO,TODO,TODO,TODO
     WIN_VENT,TODO,TODO,TODO,TODO
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy


get_terrain
-----------
The following file is used by scripts: ['radiation-daysim']


.. csv-table:: **inputs/topography/terrain.tif**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Mock_variable,TODO,TODO,TODO,TODO


get_thermal_networks
--------------------
The following file is used by scripts: ['thermal-network']


.. csv-table:: **databases/ch/systems/thermal_networks.xls:MATERIAL PROPERTIES**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Cp_JkgK,Heat capacity of transmission fluid.,[J/kgK],float,{0.0...n}
     code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
     lambda_WmK,Thermal conductivity,[W/mK],float,{0.0...n}
     material,TODO,TODO,TODO,TODO
     rho_kgm3,Density of transmission fluid.,[kg/m3],float,{0.0...n}

.. csv-table:: **databases/ch/systems/thermal_networks.xls:PIPING CATALOG**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     D_ext_m,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.,[m],float,{0.0...n}
     D_ins_m,Defines the pipe insulation diameter for the nominal diameter (DN) bin.,[m],float,{0.0...n}
     D_int_m,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.,[m],float,{0.0...n}
     Pipe_DN,Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter.,[DN#],string,alphanumeric
     Vdot_max_m3s,Maximum volume flow rate for the nominal diameter (DN) bin.,[m3/s],float,{0.0...n}
     Vdot_min_m3s,Minimum volume flow rate for the nominal diameter (DN) bin.,[m3/s],float,{0.0...n}


get_weather
-----------
The following file is used by scripts: ['radiation-daysim', 'photovoltaic', 'photovoltaic-thermal', 'solar-collector', 'demand', 'thermal-network']


.. csv-table:: **c:/users/assistenz/documents/github/cityenergyanalyst/cea/databases/weather/singapore.epw**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     EPW file variables,TODO,TODO,TODO,TODO


get_zone_geometry
-----------------
The following file is used by scripts: ['photovoltaic', 'photovoltaic-thermal', 'emissions', 'network-layout', 'radiation-daysim', 'demand', 'solar-collector']


.. csv-table:: **inputs/building-geometry/zone.shp**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10

     Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
     floors_ag,TODO,TODO,TODO,TODO
     floors_bg,TODO,TODO,TODO,TODO
     geometry,TODO,TODO,TODO,TODO
     height_ag,Aggregated height of the walls.,[m],float,{0.0...n}
     height_bg,TODO,TODO,TODO,TODO

