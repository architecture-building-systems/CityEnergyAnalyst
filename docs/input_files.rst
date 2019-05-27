
get_building_occupancy
----------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    SINGLE_RES,Residential (single dwellings),m2,{0.0...1},float

    HOSPITAL,Hospitals,m2,{0.0...1},float

    GYM,Gymnasiums,m2,{0.0...1},float

    SERVERROOM,Data center,m2,{0.0...1},float

    SWIMMING,Swimming halls,m2,{0.0...1},float

    LIBRARY,Libraries,m2,{0.0...1},float

    RESTAURANT,Restaurants,m2,{0.0...1},float

    COOLROOM,Refrigeration rooms,m2,{0.0...1},float

    SCHOOL,Schools,m2,{0.0...1},float

    RETAIL,Retail,m2,{0.0...1},float

    HOTEL,Hotels,m2,{0.0...1},float

    INDUSTRIAL,Light industry,m2,{0.0...1},float

    PARKING,Parking,m2,{0.0...1},float

    Name,Unique building ID. It must start with a letter.,[-],alphanumeric,string

    OFFICE,Offices,m2,{0.0...1},float

    FOODSTORE,Food stores,m2,{0.0...1},float

    MULTI_RES,Residential (multiple dwellings),m2,TODO,TODO


get_technical_emission_systems
------------------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    Description,Describes the source of the benchmark standards.,[-],[-],string

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    dTcs_C,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    HEAT_REC,TODO,TODO,TODO,TODO

    dThs_C,TODO,TODO,TODO,TODO

    Tc_sup_air_ahu_C,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    Qwwmax_Wm2,Maximum heat flow permitted by the distribution system per m2 of the exchange interface (e.g. floor/radiator heating area).,[W/m2],{0.0....n},float

    Tscs0_aru_C,TODO,TODO,TODO,TODO

    Tshs0_ahu_C,TODO,TODO,TODO,TODO

    Description,Description of the typical supply and return temperatures related to HVAC, hot water and sanitation.,[-],[-],string

    Qhsmax_Wm2,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    MECH_VENT,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    code,Unique ID of component of the typical supply and return temperature bins.,[-],{T1..Tn},string

    dTcs0_ahu_C,TODO,TODO,TODO,TODO

    ECONOMIZER,TODO,TODO,TODO,TODO

    dTcs0_scu_C,TODO,TODO,TODO,TODO

    Qcsmax_Wm2,TODO,TODO,TODO,TODO

    Tshs0_aru_C,TODO,TODO,TODO,TODO

    dT_Qhs,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    Tshs0_shu_C,TODO,TODO,TODO,TODO

    dT_Qcs,TODO,TODO,TODO,TODO

    dTcs0_aru_C,TODO,TODO,TODO,TODO

    Tc_sup_air_aru_C,TODO,TODO,TODO,TODO

    Tscs0_scu_C,TODO,TODO,TODO,TODO

    Th_sup_air_ahu_C,TODO,TODO,TODO,TODO

    NIGHT_FLSH,TODO,TODO,TODO,TODO

    Th_sup_air_aru_C,TODO,TODO,TODO,TODO

    dThs0_aru_C,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    Tscs0_ahu_C,TODO,TODO,TODO,TODO

    dThs0_ahu_C,TODO,TODO,TODO,TODO

    Tsww0_C,Typical supply water temperature.,[C],{0.0....n},float

    WIN_VENT,TODO,TODO,TODO,TODO

    dThs0_shu_C,TODO,TODO,TODO,TODO


get_zone_geometry
-----------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    height_ag,Aggregated height of the walls.,[m],{0.0...n},float

    height_bg,TODO,TODO,TODO,TODO

    floors_ag,TODO,TODO,TODO,TODO

    geometry,TODO,TODO,TODO,TODO

    Name,Unique building ID. It must start with a letter.,[-],alphanumeric,string

    floors_bg,TODO,TODO,TODO,TODO


get_thermal_networks
--------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    Cp_JkgK,Heat capacity of transmission fluid.,[J/kgK],{0.0...n},float

    D_ins_m,Defines the pipe insulation diameter for the nominal diameter (DN) bin.,[m],{0.0...n},float

    D_int_m,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.,[m],{0.0...n},float

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    Vdot_min_m3s,Minimum volume flow rate for the nominal diameter (DN) bin.,[m3/s],{0.0...n},float

    material,TODO,TODO,TODO,TODO

    Pipe_DN,Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter.,[DN#],alphanumeric,string

    lambda_WmK,Thermal conductivity,[W/mK],{0.0...n},float

    D_ext_m,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.,[m],{0.0...n},float

    rho_kgm3,Density of transmission fluid.,[kg/m3],{0.0...n},float

    Vdot_max_m3s,Maximum volume flow rate for the nominal diameter (DN) bin.,[m3/s],{0.0...n},float


get_archetypes_schedules
------------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Sunday_4,TODO,TODO,TODO,TODO

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_4,TODO,TODO,TODO,TODO

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Sunday_4,TODO,TODO,TODO,TODO

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_4,TODO,TODO,TODO,TODO

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    density,m2 per person,[m2/p],{0.0...n},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Saturday_4,TODO,TODO,TODO,TODO

    Weekday_4,TODO,TODO,TODO,TODO

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Weekday_4,TODO,TODO,TODO,TODO

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_4,TODO,TODO,TODO,TODO

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_4,TODO,TODO,TODO,TODO

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Weekday_1,Probability of maximum occupancy per hour in a weekday,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Saturday_1,Probability of maximum occupancy per hour on Saturday,[p/p],{0.0...1},float

    Sunday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    density,m2 per person,[m2/p],{0.0...n},float

    month,Probability of use for the month,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Saturday_2,Probability of use of lighting and applicances (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Weekday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Saturday_3,Probability of domestic hot water consumption (daily) for each hour,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float

    Sunday_1,Probability of maximum occupancy per hour on Sunday,[p/p],{0.0...1},float


get_supply_systems
------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    d,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    c,TODO,TODO,TODO,TODO

    dP2,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    module_area_m2,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    e_p,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    LT_yr,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    Diameter_max,Defines the maximum pipe diameter tolerance for the nominal diameter (DN) bin.,[-],{0.0....n},float

    c,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    mB0_r,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    LT_yr,TODO,TODO,TODO,TODO

    module_length_m,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    a_e,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    unit,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    c_p,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    misc_losses,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    el_W,TODO,TODO,TODO,TODO

    a_p,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    a,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    cap_min,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    IAM_d,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    d,TODO,TODO,TODO,TODO

    type,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    s_e,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    mB_max_r,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    Unit,Defines the unit of measurement for the diameter values.,[mm],[-],string

    Description,Describes the source of the benchmark standards.,[-],[-],string

    assumption,TODO,TODO,TODO,TODO

    Description,Classifies nominal pipe diameters (DN) into typical bins. E.g. DN100 refers to pipes of approx. 100mm in diameter.,[DN#],alphanumeric,string

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    m_hw,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    assumption,TODO,TODO,TODO,TODO

    Cp_fluid,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    c,TODO,TODO,TODO,TODO

    PV_a2,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    m_cw,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    value,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    assumption,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    c2,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    C_eff,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    b_p,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    c1,TODO,TODO,TODO,TODO

    unit ,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    PV_a3,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    e,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    module_length_m,TODO,TODO,TODO,TODO

    PV_n,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    PV_th,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    n0,TODO,TODO,TODO,TODO

    d_p,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    Currency,Defines the unit of currency used to create the cost estimations (year specific). E.g. USD-2015.,[-],[-],string

    PV_Bref,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    unit,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    PV_noct,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    aperture_area_ratio,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    b,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    Investment,Typical cost of investment for a given pipe diameter.,[$/m],{0.0....n},float

    a,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    dP4,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    Diameter_min,Defines the minimum pipe diameter tolerance for the nominal diameter (DN) bin.,[-],{0.0....n},float

    currency,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    a,TODO,TODO,TODO,TODO

    type,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    assumption,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    LT_yr,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    d,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    dP1,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    type,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    PV_a4,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    b,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    e,TODO,TODO,TODO,TODO

    e_g,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    a_g,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    O&M_%,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    e_e,TODO,TODO,TODO,TODO

    t_max,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    s_g,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    c,TODO,TODO,TODO,TODO

    PV_a0,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    unit,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    Currency ,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    unit,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

    PV_a1,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    cap_max,TODO,TODO,TODO,TODO

     Assumptions,TODO,TODO,TODO,TODO

    mB_min_r,TODO,TODO,TODO,TODO

    r_e,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    LT_yr,TODO,TODO,TODO,TODO

    dP3,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    cap_max,TODO,TODO,TODO,TODO

    cap_min,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    c,TODO,TODO,TODO,TODO

    IR_%,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    r_g,TODO,TODO,TODO,TODO

    currency,TODO,TODO,TODO,TODO

    d,TODO,TODO,TODO,TODO

    a,TODO,TODO,TODO,TODO

    b,TODO,TODO,TODO,TODO

    assumption,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    cap_max,TODO,TODO,TODO,TODO


get_archetypes_properties
-------------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    void_deck,Share of floors with an open envelope (default = 0),[floor/floor],{0.0...1},float

    Ve_lps,Indoor quality requirements of indoor ventilation per person,[l/s],{0.0...n},float

    Qcre_Wm2,TODO,TODO,TODO,TODO

    type_el,Type of electrical supply system,[code],{T0...Tn},string

    X_ghp,Moisture released by occupancy at peak conditions,[gh/kg/p],{0.0...n},float

    Qhpro_Wm2,Peak specific due to process heat,[W/m2],{0.0...n},float

    Ths_setb_C,Setback point of temperature for heating system,[C],{0.0...n},float

    Ed_Wm2,Peak specific electrical load due to servers/data centres,[W/m2],{0.0...n},float

    rhum_min_pc,TODO,TODO,TODO,TODO

    year_start,Lower limit of year interval where the building properties apply,[yr],{0...n},int

    building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    year_start,Lower limit of year interval where the building properties apply,[yr],{0...n},int

    rhum_max_pc,TODO,TODO,TODO,TODO

    Code,Unique code for the material of the pipe.,[-],[-],string

    El_Wm2,Peak specific electrical load due to artificial lighting,[W/m2],{0.0...n},float

    standard,Letter representing whereas the field represent construction properties of a building as newly constructed, C, or renovated, R.,[-],{C, R},string

    year_end,Upper limit of year interval where the building properties apply,[yr],{0...n},int

    Tcs_setb_C,Setback point of temperature for cooling system,[C],{0.0...n},float

    year_end,Upper limit of year interval where the building properties apply,[yr],{0...n},int

    type_cs,Type of cooling supply system,[code],{T0...Tn},string

    type_cons,Type of construction. It relates to the contents of the default database of Envelope Properties: construction,[code],{T1...Tn},string

    type_ctrl,Type of control system,[code],{T0...Tn},string

    type_leak,Leakage level. It relates to the contents of the default database of Envelope Properties: leakage,[code],{T1...Tn},string

    wwr_north,Window to wall ratio in building archetype,[-],{0.0...1},float

    building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],[-],string

    wwr_east,Window to wall ratio in building archetype,[-],{0.0...1},float

    Hs,Fraction of heated space in building archetype,[-],{0.0...1},float

    Qs_Wp,TODO,TODO,TODO,TODO

    Tcs_set_C,Setpoint temperature for cooling system,[C],{0.0...n},float

    Ea_Wm2,Peak specific electrical load due to computers and devices,[W/m2],{0.0...n},float

    type_dhw,Type of hot water supply system,[code],{T0...Tn},string

    Code,Unique code for the material of the pipe.,[-],[-],string

    type_dhw,Type of hot water supply system,[code],{T0...Tn},string

    Epro_Wm2,Peak specific electrical load due to industrial processes,[W/m2],{0.0...n},string

    type_wall,Wall construction. It relates to the contents of the default database of Envelope Properties: walll,[code],{T1...Tn},string

    year_start,Lower limit of year interval where the building properties apply,[yr],{0...n},int

    Es,TODO,TODO,TODO,TODO

    type_hs,Type of heating supply system,[code],{T0...Tn},string

    type_cs,Type of cooling supply system,[code],{T0...Tn},string

    building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    type_roof,Roof construction. It relates to the contents of the default database of Envelope Properties: roof,[code],{T1...Tn},string

    type_vent,Type of ventilation system,[code],{T0...Tn},string

    wwr_west,Window to wall ratio in building archetype,[-],{0.0...1},float

    Vww_lpd,Peak specific daily hot water consumption,[lpd],{0.0...n},float

    year_end,Upper limit of year interval where the building properties apply,[yr],{0...n},int

    Vw_lpd,Peak specific fresh water consumption (includes cold and hot water),[lpd],{0.0...n},float

    standard,Letter representing whereas the field represent construction properties of a building as newly constructed, C, or renovated, R.,[-],{C, R},string

    Ns,TODO,TODO,TODO,TODO

    standard,Letter representing whereas the field represent construction properties of a building as newly constructed, C, or renovated, R.,[-],{C , R},string

    wwr_south,Window to wall ratio in building archetype,[-],{0.0...1},float

    Ths_set_C,Setpoint temperature for heating system,[C],{0.0...n},float

    type_win,Window type. It relates to the contents of the default database of Envelope Properties: windows,[code],{T1...Tn},string

    type_hs,Type of heating supply system,[code],{T0...Tn},string

    type_shade,Shading system type. It relates to the contents of the default database of Envelope Properties: shade,[code],{T1...Tn},string


get_street_network
------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    geometry,TODO,TODO,TODO,TODO

    FID,TODO,TODO,TODO,TODO


get_district_geometry
---------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    height_ag,Aggregated height of the walls.,[m],{0.0...n},float

    floors_bg,TODO,TODO,TODO,TODO

    Name,Unique building ID. It must start with a letter.,[-],alphanumeric,string

    height_bg,TODO,TODO,TODO,TODO

    floors_ag,TODO,TODO,TODO,TODO

    geometry,TODO,TODO,TODO,TODO


get_archetypes_system_controls
------------------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    has-cooling-season,Defines whether the scenario has a cooling season.,[-],{TRUE, FALSE},Boolean

    heating-season-end,Last day of the heating season,[-],mm-dd,date

    heating-season-start,Day on which the heating season starts,[-],mm-dd,date

    cooling-season-start,Day on which the cooling season starts,[-],mm-dd,date

    cooling-season-end,Last day of the cooling season,[-],mm-dd,date

    has-heating-season,Defines whether the scenario has a heating season.,[-],{TRUE, FALSE},Boolean


get_data_benchmark
------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],{0.0...n},float

    NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],{0.0...n},float

    PEN_today,Present primary energy demand,[-],{0.0...n},float

    Description,Describes the source of the benchmark standards.,[-],[-],string

    CO2_today,Present CO2 production,[-],{0.0...n},float

    NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],{0.0...n},float

    PEN_today,Present primary energy demand,[-],{0.0...n},float

    NRE_today,Present non-renewable energy consumption,[-],{0.0...n},float

    CO2_target_new,Target CO2 production for newly constructed buildings,[-],{0.0...n},float

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],{0.0...n},float

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    Description,Describes the source of the benchmark standards.,[-],[-],string

    CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],{0.0...n},float

    CO2_today,Present CO2 production,[-],{0.0...n},float

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    CO2_today,Present CO2 production,[-],{0.0...n},float

    NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],{0.0...n},float

    NRE_today,Present non-renewable energy consumption,[-],{0.0...n},float

    CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],{0.0...n},float

    PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],{0.0...n},float

    Description,Describes the source of the benchmark standards.,[-],[-],string

    PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],{0.0...n},float

    PEN_target_new,Target primary energy demand for newly constructed buildings,[-],{0.0...n},float

    NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],{0.0...n},float

    NRE_today,Present non-renewable energy consumption,[-],{0.0...n},float

    PEN_target_new,Target primary energy demand for newly constructed buildings,[-],{0.0...n},float

    Description,Describes the source of the benchmark standards.,[-],[-],string

    NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],{0.0...n},float

    CO2_target_new,Target CO2 production for newly constructed buildings,[-],{0.0...n},float

    NRE_today,Present non-renewable energy consumption,[-],{0.0...n},float

    PEN_today,Present primary energy demand,[-],{0.0...n},float

    PEN_target_retrofit,Target primary energy demand for retrofitted buildings,[-],{0.0...n},float

    CO2_target_new,Target CO2 production for newly constructed buildings,[-],{0.0...n},float

    PEN_today,Present primary energy demand,[-],{0.0...n},float

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],{0.0...n},float

    CO2_today,Present CO2 production,[-],{0.0...n},float

    NRE_target_retrofit,Target non-renewable energy consumption for retrofitted buildings,[-],{0.0...n},float

    PEN_target_new,Target primary energy demand for newly constructed buildings,[-],{0.0...n},float

    PEN_target_new,Target primary energy demand for newly constructed buildings,[-],{0.0...n},float

    CO2_target_retrofit,Target CO2 production for retrofitted buildings,[-],{0.0...n},float

    NRE_target_new,Target non-renewable energy consumption for newly constructed buildings,[-],{0.0...n},float

    CO2_target_new,Target CO2 production for newly constructed buildings,[-],{0.0...n},float


get_building_age
----------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    built,Construction year,[-],{0...n},int

    HVAC,Year of last retrofit of HVAC systems (0 if none),[-],{0...n},int

    windows,Year of last retrofit of windows (0 if none),[-],{0...n},int

    envelope,Year of last retrofit of building facades (0 if none),[-],{0...n},int

    Name,Unique building ID. It must start with a letter.,[-],alphanumeric,string

    roof,Year of last retrofit of roof (0 if none),[-],{0...n},int

    basement,Year of last retrofit of basement (0 if none),[-],{0...n},int

    partitions,Year of last retrofit of internal wall partitions(0 if none),[-],{0...n},int


get_weather
-----------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    EPW file variables,TODO,TODO,TODO,TODO


get_life_cycle_inventory_building_systems
-----------------------------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    Win_ext,Typical embodied CO2 equivalent emissions of the external glazing.,[kgCO2],{0.0....n},float

    Wall_int_nosup,nan,[kgCO2],{0.0....n},float

    year_end,Upper limit of year interval where the building properties apply,[-],{0...n},int

    Wall_ext_bg,Typical embodied CO2 equivalent emissions of the exterior below ground walls.,[kgCO2],{0.0....n},float

    year_end,Upper limit of year interval where the building properties apply,[-],{0...n},int

    year_start,Lower limit of year interval where the building properties apply,[-],{0...n},int

    Floor_g,Typical embodied CO2 equivalent emissions of the ground floor.,[kgCO2],{0.0....n},float

    standard,Letter representing whereas the field represent construction properties of a building as newly constructed, C, or renovated, R.,[-],{C, R},string

    Excavation,Typical embodied CO2 equivalent emissions for site excavation.,[kgCO2],{0.0....n},float

    Wall_ext_ag,Typical embodied CO2 equivalent emissions of the exterior above ground walls.,[kgCO2],{0.0....n},float

    Floor_int,Typical embodied energy of the interior floor.,[GJ],{0.0....n},float

    Wall_ext_bg,Typical embodied energy of the exterior below ground walls.,[GJ],{0.0....n},float

    Roof,Typical embodied CO2 equivalent emissions of the roof.,[kgCO2],{0.0....n},float

    standard,Letter representing whereas the field represent construction properties of a building as newly constructed, C, or renovated, R.,[-],{C, R},string

    building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    Services,Typical embodied CO2 equivalent emissions of the building services.,[kgCO2],{0.0....n},float

    Services,Typical embodied energy of the building services.,[GJ],{0.0....n},float

    Win_ext,Typical embodied energy of the external glazing.,[GJ],{0.0....n},float

    Wall_int_nosup,nan,[GJ],{0.0....n},float

    Wall_int_sup,nan,[GJ],{0.0....n},float

    Floor_int,Typical embodied CO2 equivalent emissions of the interior floor.,[kgCO2],{0.0....n},float

    Wall_ext_ag,Typical embodied energy of the exterior above ground walls.,[GJ],{0.0....n},float

    Floor_g,Typical embodied energy of the ground floor.,[GJ],{0.0....n},float

    Roof,Typical embodied energy of the roof.,[GJ],{0.0....n},float

    building_use,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    Wall_int_sup,nan,[kgCO2],{0.0....n},float

    year_start,Lower limit of year interval where the building properties apply,[-],{0...n},int

    Excavation,Typical embodied energy for site excavation.,[GJ],{0.0....n},float


get_life_cycle_inventory_supply_systems
---------------------------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    eff_dhw,TODO,TODO,TODO,TODO

    source_el,TODO,TODO,TODO,TODO

    scale_hs,TODO,TODO,TODO,TODO

    reference,nan,[-],[-],string

    eff_el,TODO,TODO,TODO,TODO

    reference,nan,[-],[-],string

    scale_dhw,TODO,TODO,TODO,TODO

    reference,nan,[-],[-],string

    code,Unique ID of component of the heating and cooling network,[-],{T1..Tn},string

    Description,Describes the source of the benchmark standards.,[-],[-],string

    CO2,Refers to the equivalent CO2 required to run the heating or cooling system.,[kg/kWh],{0.0....n},float

    reference,nan,[-],[-],string

    scale_cs,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    eff_cs,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    scale_el,TODO,TODO,TODO,TODO

    source_dhw,TODO,TODO,TODO,TODO

    Description,Describes the source of the benchmark standards.,[-],[-],string

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    source_cs,TODO,TODO,TODO,TODO

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    Description,Describes the source of the benchmark standards.,[-],[-],string

    code,Building use. It relates to the uses stored in the input database of Zone_occupancy,[-],Those stored in Zone_occupancy,string

    costs_kWh,Refers to the financial costs required to run the heating or cooling system.,[$/kWh],{0.0....n},float

    PEN,Refers to the amount of primary energy needed (PEN) to run the heating or cooling system.,[kWh/kWh],{0.0....n},float

    reference,nan,[-],[-],string

    eff_hs,TODO,TODO,TODO,TODO

    Description,Description of the heating and cooling network (related to the code). E.g. heatpump -soil/water,[-],[-],string

    source_hs,TODO,TODO,TODO,TODO


get_envelope_systems
--------------------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

    U_base,Thermal transmittance of basement including linear losses (+10%). Defined according to ISO 13790.,[-],{0.0...1},float

    Description,Describes the source of the benchmark standards.,[-],[-],string

    U_roof,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],{0.1...n},float

    Description,Describes the source of the benchmark standards.,[-],[-],string

    G_win,Solar heat gain coefficient. Defined according to ISO 13790.,[-],{0.0...1},float

    e_wall,Emissivity of external surface. Defined according to ISO 13790.,[-],{0.0...1},float

    rf_sh,Shading coefficient when shading device is active. Defined according to ISO 13790.,[-],{0.0...1},float

    code,Unique ID of component in the window category,[-],{T1..Tn},string

    U_win,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],{0.1...n},float

    r_wall,Reflectance in the Red spectrum. Defined according Radiance. (long-wave),[-],{0.0...1},float

    e_roof,Emissivity of external surface. Defined according to ISO 13790.,[-],{0.0...1},float

    code,Unique ID of component in the window category,[-],{T1..Tn},string

    Cm_Af,Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790.,[J/Km2],{0.0...1},float

    code,Unique ID of component in the construction category,[-],{T1..Tn},string

    e_win,Emissivity of external surface. Defined according to ISO 13790.,[-],{0.0...1},float

    a_roof,Solar absorption coefficient. Defined according to ISO 13790.,[-],{0.0...1},float

    Description,Describes the source of the benchmark standards.,[-],[-],string

    code,Unique ID of component in the window category,[-],{T1...Tn},string

    code,Unique ID of component in the leakage category,[-],{T1..Tn},string

    Description,Describes the source of the benchmark standards.,[-],[-],string

    n50,Air exchanges due to leakage at a pressure of 50 Pa.,[1/h],{0.0...n},float

    a_wall,Solar absorption coefficient. Defined according to ISO 13790.,[-],{0.0...1},float

    r_roof,Reflectance in the Red spectrum. Defined according Radiance. (long-wave),[-],{0.0...1},float

    code,Unique ID of component in the window category,[-],{T1..Tn},string

    Description,Describes the source of the benchmark standards.,[-],[-],string

    U_wall,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.,[-],{0.1...n},float

    Description,Describes the source of the benchmark standards.,[-],[-],string


get_terrain
-----------
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"

