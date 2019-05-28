
get_archetypes_properties
-------------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    construction_properties.xlsx:ARCHITECTURE,Es,TODO,TODO,TODO,TODO
    construction_properties.xlsx:ARCHITECTURE,Hs,Fraction of heated space in building archetype,[-],float,{0.0...1}
    construction_properties.xlsx:ARCHITECTURE,Ns,TODO,TODO,TODO,TODO
    construction_properties.xlsx:ARCHITECTURE,building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    construction_properties.xlsx:ARCHITECTURE,standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
    construction_properties.xlsx:ARCHITECTURE,type_cons,Type of construction. It relates to the contents of the default database of Envelope Properties: construction,[code],string,{T1...Tn}
    construction_properties.xlsx:ARCHITECTURE,type_leak,Leakage level. It relates to the contents of the default database of Envelope Properties: leakage,[code],string,{T1...Tn}
    construction_properties.xlsx:ARCHITECTURE,type_roof,Roof construction. It relates to the contents of the default database of Envelope Properties: roof,[code],string,{T1...Tn}
    construction_properties.xlsx:ARCHITECTURE,type_shade,Shading system type. It relates to the contents of the default database of Envelope Properties: shade,[code],string,{T1...Tn}
    construction_properties.xlsx:ARCHITECTURE,type_wall,Wall construction. It relates to the contents of the default database of Envelope Properties: walll,[code],string,{T1...Tn}
    construction_properties.xlsx:ARCHITECTURE,type_win,Window type. It relates to the contents of the default database of Envelope Properties: windows,[code],string,{T1...Tn}
    construction_properties.xlsx:ARCHITECTURE,void_deck,Share of floors with an open envelope (default = 0),[floor/floor],float,{0.0...1}
    construction_properties.xlsx:ARCHITECTURE,wwr_east,Window to wall ratio in building archetype,[-],float,{0.0...1}
    construction_properties.xlsx:ARCHITECTURE,wwr_north,Window to wall ratio in building archetype,[-],float,{0.0...1}
    construction_properties.xlsx:ARCHITECTURE,wwr_south,Window to wall ratio in building archetype,[-],float,{0.0...1}
    construction_properties.xlsx:ARCHITECTURE,wwr_west,Window to wall ratio in building archetype,[-],float,{0.0...1}
    construction_properties.xlsx:ARCHITECTURE,year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
    construction_properties.xlsx:ARCHITECTURE,year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}
    construction_properties.xlsx:HVAC,building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,[-]
    construction_properties.xlsx:HVAC,standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
    construction_properties.xlsx:HVAC,type_cs,Type of cooling supply system,[code],string,{T0...Tn}
    construction_properties.xlsx:HVAC,type_ctrl,Type of control system,[code],string,{T0...Tn}
    construction_properties.xlsx:HVAC,type_dhw,Type of hot water supply system,[code],string,{T0...Tn}
    construction_properties.xlsx:HVAC,type_hs,Type of heating supply system,[code],string,{T0...Tn}
    construction_properties.xlsx:HVAC,type_vent,Type of ventilation system,[code],string,{T0...Tn}
    construction_properties.xlsx:HVAC,year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
    construction_properties.xlsx:HVAC,year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}
    construction_properties.xlsx:INDOOR_COMFORT,Code,Unique code for the material of the pipe.,[-],string,[-]
    construction_properties.xlsx:INDOOR_COMFORT,Tcs_set_C,Setpoint temperature for cooling system,[C],float,{0.0...n}
    construction_properties.xlsx:INDOOR_COMFORT,Tcs_setb_C,Setback point of temperature for cooling system,[C],float,{0.0...n}
    construction_properties.xlsx:INDOOR_COMFORT,Ths_set_C,Setpoint temperature for heating system,[C],float,{0.0...n}
    construction_properties.xlsx:INDOOR_COMFORT,Ths_setb_C,Setback point of temperature for heating system,[C],float,{0.0...n}
    construction_properties.xlsx:INDOOR_COMFORT,Ve_lps,Indoor quality requirements of indoor ventilation per person,[l/s],float,{0.0...n}
    construction_properties.xlsx:INDOOR_COMFORT,rhum_max_pc,TODO,TODO,TODO,TODO
    construction_properties.xlsx:INDOOR_COMFORT,rhum_min_pc,TODO,TODO,TODO,TODO
    construction_properties.xlsx:INTERNAL_LOADS,Code,Unique code for the material of the pipe.,[-],string,[-]
    construction_properties.xlsx:INTERNAL_LOADS,Ea_Wm2,Peak specific electrical load due to computers and devices,[W/m2],float,{0.0...n}
    construction_properties.xlsx:INTERNAL_LOADS,Ed_Wm2,Peak specific electrical load due to servers/data centres,[W/m2],float,{0.0...n}
    construction_properties.xlsx:INTERNAL_LOADS,El_Wm2,Peak specific electrical load due to artificial lighting,[W/m2],float,{0.0...n}
    construction_properties.xlsx:INTERNAL_LOADS,Epro_Wm2,Peak specific electrical load due to industrial processes,[W/m2],string,{0.0...n}
    construction_properties.xlsx:INTERNAL_LOADS,Qcre_Wm2,TODO,TODO,TODO,TODO
    construction_properties.xlsx:INTERNAL_LOADS,Qhpro_Wm2,Peak specific due to process heat,[W/m2],float,{0.0...n}
    construction_properties.xlsx:INTERNAL_LOADS,Qs_Wp,TODO,TODO,TODO,TODO
    construction_properties.xlsx:INTERNAL_LOADS,Vw_lpd,Peak specific fresh water consumption (includes cold and hot water),[lpd],float,{0.0...n}
    construction_properties.xlsx:INTERNAL_LOADS,Vww_lpd,Peak specific daily hot water consumption,[lpd],float,{0.0...n}
    construction_properties.xlsx:INTERNAL_LOADS,X_ghp,Moisture released by occupancy at peak conditions,[gh/kg/p],float,{0.0...n}
    construction_properties.xlsx:SUPPLY,building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    construction_properties.xlsx:SUPPLY,standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
    construction_properties.xlsx:SUPPLY,type_cs,Type of cooling supply system,[code],string,{T0...Tn}
    construction_properties.xlsx:SUPPLY,type_dhw,Type of hot water supply system,[code],string,{T0...Tn}
    construction_properties.xlsx:SUPPLY,type_el,Type of electrical supply system,[code],string,{T0...Tn}
    construction_properties.xlsx:SUPPLY,type_hs,Type of heating supply system,[code],string,{T0...Tn}
    construction_properties.xlsx:SUPPLY,year_end,Upper limit of year interval where the building properties apply,[yr],int,{0...n}
    construction_properties.xlsx:SUPPLY,year_start,Lower limit of year interval where the building properties apply,[yr],int,{0...n}

get_archetypes_schedules
------------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    occupancy_schedules.xlsx:COOLROOM,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:COOLROOM,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:COOLROOM,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:FOODSTORE,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:FOODSTORE,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:GYM,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:GYM,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Saturday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:HOSPITAL,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Sunday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:HOSPITAL,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOSPITAL,Weekday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:HOSPITAL,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:HOSPITAL,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:HOTEL,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:HOTEL,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Saturday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:INDUSTRIAL,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Sunday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:INDUSTRIAL,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:INDUSTRIAL,Weekday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:INDUSTRIAL,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:INDUSTRIAL,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Saturday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:LAB,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Sunday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:LAB,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LAB,Weekday_4,TODO,TODO,TODO,TODO
    occupancy_schedules.xlsx:LAB,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:LAB,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:LIBRARY,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:LIBRARY,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MULTI_RES,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:MULTI_RES,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:MUSEUM,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:MUSEUM,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:OFFICE,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:OFFICE,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:PARKING,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:PARKING,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RESTAURANT,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:RESTAURANT,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:RETAIL,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:RETAIL,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SCHOOL,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:SCHOOL,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SERVERROOM,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:SERVERROOM,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SINGLE_RES,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:SINGLE_RES,month,Probability of use for the month,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],float,{0.0...1}
    occupancy_schedules.xlsx:SWIMMING,density,m2 per person,[m2/p],float,{0.0...n}
    occupancy_schedules.xlsx:SWIMMING,month,Probability of use for the month,[p/p],float,{0.0...1}

get_archetypes_system_controls
------------------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    system_controls.xlsx:heating_cooling,cooling-season-end,Last day of the cooling season,[-],date,mm-dd
    system_controls.xlsx:heating_cooling,cooling-season-start,Day on which the cooling season starts,[-],date,mm-dd
    system_controls.xlsx:heating_cooling,has-cooling-season,Defines whether the scenario has a cooling season.,[-],Boolean,{TRUE/FALSE}
    system_controls.xlsx:heating_cooling,has-heating-season,Defines whether the scenario has a heating season.,[-],Boolean,{TRUE/FALSE}
    system_controls.xlsx:heating_cooling,heating-season-end,Last day of the heating season,[-],date,mm-dd
    system_controls.xlsx:heating_cooling,heating-season-start,Day on which the heating season starts,[-],date,mm-dd

get_building_age
----------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    age.dbf,HVAC,Year of last retrofit of HVAC systems (0 if none),[-],int,{0...n}
    age.dbf,Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
    age.dbf,basement,Year of last retrofit of basement (0 if none),[-],int,{0...n}
    age.dbf,built,Construction year,[-],int,{0...n}
    age.dbf,envelope,Year of last retrofit of building facades (0 if none),[-],int,{0...n}
    age.dbf,partitions,Year of last retrofit of internal wall partitions(0 if none),[-],int,{0...n}
    age.dbf,roof,Year of last retrofit of roof (0 if none),[-],int,{0...n}
    age.dbf,windows,Year of last retrofit of windows (0 if none),[-],int,{0...n}

get_building_occupancy
----------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    occupancy.dbf,COOLROOM,Refrigeration rooms,m2,float,{0.0...1}
    occupancy.dbf,FOODSTORE,Food stores,m2,float,{0.0...1}
    occupancy.dbf,GYM,Gymnasiums,m2,float,{0.0...1}
    occupancy.dbf,HOSPITAL,Hospitals,m2,float,{0.0...1}
    occupancy.dbf,HOTEL,Hotels,m2,float,{0.0...1}
    occupancy.dbf,INDUSTRIAL,Light industry,m2,float,{0.0...1}
    occupancy.dbf,LIBRARY,Libraries,m2,float,{0.0...1}
    occupancy.dbf,MULTI_RES,Residential (multiple dwellings),m2,TODO,TODO
    occupancy.dbf,Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
    occupancy.dbf,OFFICE,Offices,m2,float,{0.0...1}
    occupancy.dbf,PARKING,Parking,m2,float,{0.0...1}
    occupancy.dbf,RESTAURANT,Restaurants,m2,float,{0.0...1}
    occupancy.dbf,RETAIL,Retail,m2,float,{0.0...1}
    occupancy.dbf,SCHOOL,Schools,m2,float,{0.0...1}
    occupancy.dbf,SERVERROOM,Data center,m2,float,{0.0...1}
    occupancy.dbf,SINGLE_RES,Residential (single dwellings),m2,float,{0.0...1}
    occupancy.dbf,SWIMMING,Swimming halls,m2,float,{0.0...1}

get_data_benchmark
------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    benchmark_2000W.xls:EMBODIED,CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,CO2_today,Present CO2 production,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,Description,Describes the source of the benchmark standards.,[-],string,[-]
    benchmark_2000W.xls:EMBODIED,NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,PEN_today,Present primary energy demand,[-],float,{0.0...n}
    benchmark_2000W.xls:EMBODIED,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    benchmark_2000W.xls:MOBILITY,CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,CO2_today,Present CO2 production,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,Description,Describes the source of the benchmark standards.,[-],string,[-]
    benchmark_2000W.xls:MOBILITY,NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,PEN_today,Present primary energy demand,[-],float,{0.0...n}
    benchmark_2000W.xls:MOBILITY,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    benchmark_2000W.xls:OPERATION,CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,CO2_today,Present CO2 production,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,Description,Describes the source of the benchmark standards.,[-],string,[-]
    benchmark_2000W.xls:OPERATION,NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,PEN_today,Present primary energy demand,[-],float,{0.0...n}
    benchmark_2000W.xls:OPERATION,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    benchmark_2000W.xls:TOTAL,CO2_target_new,Target CO2 production for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,CO2_today,Present CO2 production,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,Description,Describes the source of the benchmark standards.,[-],string,[-]
    benchmark_2000W.xls:TOTAL,NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,NRE_today,Present non-renewable energy consumption,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,PEN_target_new,Target primary energy demand for newly constructed buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,PEN_today,Present primary energy demand,[-],float,{0.0...n}
    benchmark_2000W.xls:TOTAL,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy

get_district_geometry
---------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    district.shp,Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
    district.shp,floors_ag,TODO,TODO,TODO,TODO
    district.shp,floors_bg,TODO,TODO,TODO,TODO
    district.shp,geometry,TODO,TODO,TODO,TODO
    district.shp,height_ag,Aggregated height of the walls.,[m],float,{0.0...n}
    district.shp,height_bg,TODO,TODO,TODO,TODO

get_envelope_systems
--------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    envelope_systems.xls:CONSTRUCTION,Cm_Af,Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790.,[J/Km2],float,{0.0...1}
    envelope_systems.xls:CONSTRUCTION,Description,Describes the source of the benchmark standards.,[-],string,[-]
    envelope_systems.xls:CONSTRUCTION,code,Unique ID of component in the construction category,[-],string,{T1..Tn}
    envelope_systems.xls:LEAKAGE,Description,Describes the source of the benchmark standards.,[-],string,[-]
    envelope_systems.xls:LEAKAGE,code,Unique ID of component in the leakage category,[-],string,{T1..Tn}
    envelope_systems.xls:LEAKAGE,n50,Air exchanges due to leakage at a pressure of 50 Pa.,[1/h],float,{0.0...n}
    envelope_systems.xls:ROOF,Description,Describes the source of the benchmark standards.,[-],string,[-]
    envelope_systems.xls:ROOF,U_roof,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.1...n}
    envelope_systems.xls:ROOF,a_roof,Solar absorption coefficient. Defined according to ISO 13790.,[-],float,{0.0...1}
    envelope_systems.xls:ROOF,code,Unique ID of component in the window category,[-],string,{T1..Tn}
    envelope_systems.xls:ROOF,e_roof,Emissivity of external surface. Defined according to ISO 13790.,[-],float,{0.0...1}
    envelope_systems.xls:ROOF,r_roof,Reflectance in the Red spectrum. Defined according Radiance. (long-wave),[-],float,{0.0...1}
    envelope_systems.xls:SHADING,Description,Describes the source of the benchmark standards.,[-],string,[-]
    envelope_systems.xls:SHADING,code,Unique ID of component in the window category,[-],string,{T1...Tn}
    envelope_systems.xls:SHADING,rf_sh,Shading coefficient when shading device is active. Defined according to ISO 13790.,[-],float,{0.0...1}
    envelope_systems.xls:WALL,Description,Describes the source of the benchmark standards.,[-],string,[-]
    envelope_systems.xls:WALL,U_base,Thermal transmittance of basement including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.0...1}
    envelope_systems.xls:WALL,U_wall,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.1...n}
    envelope_systems.xls:WALL,a_wall,Solar absorption coefficient. Defined according to ISO 13790.,[-],float,{0.0...1}
    envelope_systems.xls:WALL,code,Unique ID of component in the window category,[-],string,{T1..Tn}
    envelope_systems.xls:WALL,e_wall,Emissivity of external surface. Defined according to ISO 13790.,[-],float,{0.0...1}
    envelope_systems.xls:WALL,r_wall,Reflectance in the Red spectrum. Defined according Radiance. (long-wave),[-],float,{0.0...1}
    envelope_systems.xls:WINDOW,Description,Describes the source of the benchmark standards.,[-],string,[-]
    envelope_systems.xls:WINDOW,G_win,Solar heat gain coefficient. Defined according to ISO 13790.,[-],float,{0.0...1}
    envelope_systems.xls:WINDOW,U_win,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],float,{0.1...n}
    envelope_systems.xls:WINDOW,code,Unique ID of component in the window category,[-],string,{T1..Tn}
    envelope_systems.xls:WINDOW,e_win,Emissivity of external surface. Defined according to ISO 13790.,[-],float,{0.0...1}

get_life_cycle_inventory_building_systems
-----------------------------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Excavation,Typical embodied CO2 equivalent emissions for site excavation.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Floor_g,Typical embodied CO2 equivalent emissions of the ground floor.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Floor_int,Typical embodied CO2 equivalent emissions of the interior floor.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Roof,Typical embodied CO2 equivalent emissions of the roof.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Services,Typical embodied CO2 equivalent emissions of the building services.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Wall_ext_ag,Typical embodied CO2 equivalent emissions of the exterior above ground walls.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Wall_ext_bg,Typical embodied CO2 equivalent emissions of the exterior below ground walls.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Wall_int_nosup,nan,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Wall_int_sup,nan,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,Win_ext,Typical embodied CO2 equivalent emissions of the external glazing.,[kgCO2],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,year_end,Upper limit of year interval where the building properties apply,[-],int,{0...n}
    LCA_buildings.xlsx:EMBODIED_EMISSIONS,year_start,Lower limit of year interval where the building properties apply,[-],int,{0...n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Excavation,Typical embodied energy for site excavation.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Floor_g,Typical embodied energy of the ground floor.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Floor_int,Typical embodied energy of the interior floor.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Roof,Typical embodied energy of the roof.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Services,Typical embodied energy of the building services.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Wall_ext_ag,Typical embodied energy of the exterior above ground walls.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Wall_ext_bg,Typical embodied energy of the exterior below ground walls.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Wall_int_nosup,nan,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Wall_int_sup,nan,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,Win_ext,Typical embodied energy of the external glazing.,[GJ],float,{0.0....n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    LCA_buildings.xlsx:EMBODIED_ENERGY,standard,Letter representing whereas the field represent construction properties of a building as newly constructed (C) or renovated (R),[-],string,{C or R}
    LCA_buildings.xlsx:EMBODIED_ENERGY,year_end,Upper limit of year interval where the building properties apply,[-],int,{0...n}
    LCA_buildings.xlsx:EMBODIED_ENERGY,year_start,Lower limit of year interval where the building properties apply,[-],int,{0...n}

get_life_cycle_inventory_supply_systems
---------------------------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    LCA_infrastructure.xlsx:COOLING,Description,Describes the source of the benchmark standards.,[-],string,[-]
    LCA_infrastructure.xlsx:COOLING,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    LCA_infrastructure.xlsx:COOLING,eff_cs,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:COOLING,reference,nan,[-],string,[-]
    LCA_infrastructure.xlsx:COOLING,scale_cs,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:COOLING,source_cs,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:DHW,Description,Describes the source of the benchmark standards.,[-],string,[-]
    LCA_infrastructure.xlsx:DHW,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    LCA_infrastructure.xlsx:DHW,eff_dhw,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:DHW,reference,nan,[-],string,[-]
    LCA_infrastructure.xlsx:DHW,scale_dhw,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:DHW,source_dhw,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:ELECTRICITY,Description,Describes the source of the benchmark standards.,[-],string,[-]
    LCA_infrastructure.xlsx:ELECTRICITY,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    LCA_infrastructure.xlsx:ELECTRICITY,eff_el,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:ELECTRICITY,reference,nan,[-],string,[-]
    LCA_infrastructure.xlsx:ELECTRICITY,scale_el,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:ELECTRICITY,source_el,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:HEATING,Description,Describes the source of the benchmark standards.,[-],string,[-]
    LCA_infrastructure.xlsx:HEATING,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    LCA_infrastructure.xlsx:HEATING,eff_hs,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:HEATING,reference,nan,[-],string,[-]
    LCA_infrastructure.xlsx:HEATING,scale_hs,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:HEATING,source_hs,TODO,TODO,TODO,TODO
    LCA_infrastructure.xlsx:RESOURCES,CO2,Refers to the equivalent CO2 required to run the heating or cooling system.,[kg/kWh],float,{0.0....n}
    LCA_infrastructure.xlsx:RESOURCES,Description,Description of the heating and cooling network (related to the code). E.g. heatpump -soil/water,[-],string,[-]
    LCA_infrastructure.xlsx:RESOURCES,PEN,Refers to the amount of primary energy needed (PEN) to run the heating or cooling system.,[kWh/kWh],float,{0.0....n}
    LCA_infrastructure.xlsx:RESOURCES,code,Unique ID of component of the heating and cooling network,[-],string,{T1..Tn}
    LCA_infrastructure.xlsx:RESOURCES,costs_kWh,Refers to the financial costs required to run the heating or cooling system.,[$/kWh],float,{0.0....n}
    LCA_infrastructure.xlsx:RESOURCES,reference,nan,[-],string,[-]

get_street_network
------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    streets.shp,FID,TODO,TODO,TODO,TODO
    streets.shp,geometry,TODO,TODO,TODO,TODO

get_supply_systems
------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    supply_systems.xls:Absorption_chiller,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:Absorption_chiller,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,a,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,a_e,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,a_g,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,b,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,c,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:Absorption_chiller,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,d,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,e,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,e_e,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,e_g,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,el_W,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,m_cw,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,m_hw,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,r_e,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,r_g,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,s_e,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,s_g,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,type,TODO,TODO,TODO,TODO
    supply_systems.xls:Absorption_chiller,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:BH,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,a,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,b,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,c,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:BH,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,d,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,e,TODO,TODO,TODO,TODO
    supply_systems.xls:BH,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:Boiler,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,a,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,b,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,c,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:Boiler,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,d,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,e,TODO,TODO,TODO,TODO
    supply_systems.xls:Boiler,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:CCGT,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,a,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,b,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,c,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:CCGT,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,d,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,e,TODO,TODO,TODO,TODO
    supply_systems.xls:CCGT,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:CT,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,a,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,b,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,c,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:CT,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,d,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,e,TODO,TODO,TODO,TODO
    supply_systems.xls:CT,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:Chiller,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,a,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,b,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,c,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:Chiller,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,d,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,e,TODO,TODO,TODO,TODO
    supply_systems.xls:Chiller,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:FC, Assumptions,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:FC,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,a,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,b,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,c,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:FC,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,d,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,e,TODO,TODO,TODO,TODO
    supply_systems.xls:FC,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:Furnace,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,a,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,b,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,c,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:Furnace,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,d,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,e,TODO,TODO,TODO,TODO
    supply_systems.xls:Furnace,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,Currency,Defines the unit of currency used to create the cost estimations (year specific). E.g. USD-2015.,[-],string,[-]
    supply_systems.xls:HEX,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:HEX,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,a,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,a_p,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,b,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,b_p,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,c,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,c_p,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:HEX,d,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,d_p,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,e,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,e_p,TODO,TODO,TODO,TODO
    supply_systems.xls:HEX,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:HP,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,a,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,b,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,c,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:HP,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,d,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,e,TODO,TODO,TODO,TODO
    supply_systems.xls:HP,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:PV,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_Bref,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_a0,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_a1,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_a2,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_a3,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_a4,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_n,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_noct,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,PV_th,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,a,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,b,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,c,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:PV,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,d,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,e,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,misc_losses,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,module_length_m,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,type,TODO,TODO,TODO,TODO
    supply_systems.xls:PV,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:PVT,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,a,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,b,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,c,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:PVT,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,d,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,e,TODO,TODO,TODO,TODO
    supply_systems.xls:PVT,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:Piping,Currency ,TODO,TODO,TODO,TODO
    supply_systems.xls:Piping,Description,Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter.,[DN#],string,alphanumeric
    supply_systems.xls:Piping,Diameter_max,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.,[-],float,{0.0....n}
    supply_systems.xls:Piping,Diameter_min,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.,[-],float,{0.0....n}
    supply_systems.xls:Piping,Investment,Typical cost of investment for a given pipe diameter.,[$/m],float,{0.0....n}
    supply_systems.xls:Piping,Unit,Defines the unit of measurement for the diameter values.,[mm],string,[-]
    supply_systems.xls:Piping,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:Pricing,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:Pricing,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:Pricing,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:Pricing,value,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:Pump,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,a,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,b,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,c,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:Pump,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,d,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,e,TODO,TODO,TODO,TODO
    supply_systems.xls:Pump,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,C_eff,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,Cp_fluid,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:SC,IAM_d,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,a,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,aperture_area_ratio,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,b,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,c,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,c1,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,c2,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:SC,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,d,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,dP1,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,dP2,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,dP3,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,dP4,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,e,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,mB0_r,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,mB_max_r,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,mB_min_r,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,module_area_m2,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,module_length_m,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,n0,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,t_max,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,type,TODO,TODO,TODO,TODO
    supply_systems.xls:SC,unit,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,Description,Describes the source of the benchmark standards.,[-],string,[-]
    supply_systems.xls:TES,IR_%,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,LT_yr,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,O&M_%,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,a,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,assumption,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,b,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,c,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,cap_max,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,cap_min,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    supply_systems.xls:TES,currency,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,d,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,e,TODO,TODO,TODO,TODO
    supply_systems.xls:TES,unit ,TODO,TODO,TODO,TODO

get_technical_emission_systems
------------------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    emission_systems.xls:controller,Description,Describes the source of the benchmark standards.,[-],string,[-]
    emission_systems.xls:controller,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    emission_systems.xls:controller,dT_Qcs,TODO,TODO,TODO,TODO
    emission_systems.xls:controller,dT_Qhs,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,Description,Describes the source of the benchmark standards.,[-],string,[-]
    emission_systems.xls:cooling,Qcsmax_Wm2,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,Tc_sup_air_ahu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,Tc_sup_air_aru_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,Tscs0_ahu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,Tscs0_aru_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,Tscs0_scu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    emission_systems.xls:cooling,dTcs0_ahu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,dTcs0_aru_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,dTcs0_scu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:cooling,dTcs_C,TODO,TODO,TODO,TODO
    emission_systems.xls:dhw,Description,Description of the typical supply and return temperatures related to HVAC: hot water and sanitation.,[-],string,[-]
    emission_systems.xls:dhw,Qwwmax_Wm2,Maximum heat flow permitted by the distribution system per m2 of the exchange interface (e.g. floor/radiator heating area).,[W/m2],float,{0.0....n}
    emission_systems.xls:dhw,Tsww0_C,Typical supply water temperature.,[C],float,{0.0....n}
    emission_systems.xls:dhw,code,Unique ID of component of the typical supply and return temperature bins.,[-],string,{T1..Tn}
    emission_systems.xls:heating,Description,Describes the source of the benchmark standards.,[-],string,[-]
    emission_systems.xls:heating,Qhsmax_Wm2,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,Th_sup_air_ahu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,Th_sup_air_aru_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,Tshs0_ahu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,Tshs0_aru_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,Tshs0_shu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    emission_systems.xls:heating,dThs0_ahu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,dThs0_aru_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,dThs0_shu_C,TODO,TODO,TODO,TODO
    emission_systems.xls:heating,dThs_C,TODO,TODO,TODO,TODO
    emission_systems.xls:ventilation,Description,Describes the source of the benchmark standards.,[-],string,[-]
    emission_systems.xls:ventilation,ECONOMIZER,TODO,TODO,TODO,TODO
    emission_systems.xls:ventilation,HEAT_REC,TODO,TODO,TODO,TODO
    emission_systems.xls:ventilation,MECH_VENT,TODO,TODO,TODO,TODO
    emission_systems.xls:ventilation,NIGHT_FLSH,TODO,TODO,TODO,TODO
    emission_systems.xls:ventilation,WIN_VENT,TODO,TODO,TODO,TODO
    emission_systems.xls:ventilation,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy

get_terrain
-----------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"


get_thermal_networks
--------------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    thermal_networks.xls:MATERIAL PROPERTIES,Cp_JkgK,Heat capacity of transmission fluid.,[J/kgK],float,{0.0...n}
    thermal_networks.xls:MATERIAL PROPERTIES,code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],string,Those stored in Zone_occupancy
    thermal_networks.xls:MATERIAL PROPERTIES,lambda_WmK,Thermal conductivity,[W/mK],float,{0.0...n}
    thermal_networks.xls:MATERIAL PROPERTIES,material,TODO,TODO,TODO,TODO
    thermal_networks.xls:MATERIAL PROPERTIES,rho_kgm3,Density of transmission fluid.,[kg/m3],float,{0.0...n}
    thermal_networks.xls:PIPING CATALOG,D_ext_m,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.,[m],float,{0.0...n}
    thermal_networks.xls:PIPING CATALOG,D_ins_m,Defines the pipe insulation diameter for the nominal diameter (DN) bin.,[m],float,{0.0...n}
    thermal_networks.xls:PIPING CATALOG,D_int_m,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.,[m],float,{0.0...n}
    thermal_networks.xls:PIPING CATALOG,Pipe_DN,Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter.,[DN#],string,alphanumeric
    thermal_networks.xls:PIPING CATALOG,Vdot_max_m3s,Maximum volume flow rate for the nominal diameter (DN) bin.,[m3/s],float,{0.0...n}
    thermal_networks.xls:PIPING CATALOG,Vdot_min_m3s,Minimum volume flow rate for the nominal diameter (DN) bin.,[m3/s],float,{0.0...n}

get_weather
-----------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    Singapore.epw,EPW file variables,TODO,TODO,TODO,TODO

get_zone_geometry
-----------------
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"

    zone.shp,Name,Unique building ID. It must start with a letter.,[-],string,alphanumeric
    zone.shp,floors_ag,TODO,TODO,TODO,TODO
    zone.shp,floors_bg,TODO,TODO,TODO,TODO
    zone.shp,geometry,TODO,TODO,TODO,TODO
    zone.shp,height_ag,Aggregated height of the walls.,[m],float,{0.0...n}
    zone.shp,height_bg,TODO,TODO,TODO,TODO
