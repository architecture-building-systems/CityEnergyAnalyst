
get_building_air_conditioning
-----------------------------

path: ``inputs/building-properties/air_conditioning_systems.dbf``

The following file is used by these scripts: ``demand``


.. csv-table::
    :header: "Variable", "Description"

    ``cool_ends``, "End of the cooling season - use 00|00 when there is none"
    ``cool_starts``, "Start of the cooling season - use 00|00 when there is none"
    ``heat_ends``, "End of the heating season - use 00|00 when there is none"
    ``heat_starts``, "Start of the heating season - use 00|00 when there is none"
    ``Name``, "Unique building ID. It must start with a letter."
    ``type_cs``, "Type of cooling HVAC assembly (relates to ""code"" in HVAC assemblies)"
    ``type_ctrl``, "Type of heating and cooling control HVAC  assembly (relates to ""code"" in HVAC assemblies)"
    ``type_dhw``, "Type of hot water HVAC assembly (relates to ""code"" in HVAC assemblies)"
    ``type_hs``, "Type of heating HVAC assembly (relates to ""code"" in HVAC assemblies)"
    ``type_vent``, "Type of ventilation HVAC assembly (relates to ""code"" in HVAC assemblies)"
    


get_building_architecture
-------------------------

path: ``inputs/building-properties/architecture.dbf``

The following file is used by these scripts: ``demand``, ``emissions``, ``radiation``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``Es``, "Fraction of gross floor area with electrical demands."
    ``Hs_ag``, "Fraction of above ground gross floor area air-conditioned."
    ``Hs_bg``, "Fraction of below ground gross floor area air-conditioned."
    ``Name``, "Unique building ID. It must start with a letter."
    ``Ns``, "Fraction of net gross floor area."
    ``type_base``, "Basement floor construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_cons``, "Type of construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_floor``, "Internal floor construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_leak``, "Tightness level assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_part``, "Internal partitions construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_roof``, "Roof construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_shade``, "Shading system assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_wall``, "External wall construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_win``, "Window assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``void_deck``, "Number of floors (from the ground up) with an open envelope (default = 0, should be lower than floors_ag.)"
    ``wwr_east``, "Window to wall ratio in in facades facing east"
    ``wwr_north``, "Window to wall ratio in in facades facing north"
    ``wwr_south``, "Window to wall ratio in in facades facing south"
    ``wwr_west``, "Window to wall ratio in in facades facing west"
    


get_building_comfort
--------------------

path: ``inputs/building-properties/indoor_comfort.dbf``

The following file is used by these scripts: ``demand``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``Name``, "Unique building ID. It must start with a letter."
    ``RH_max_pc``, "Upper bound of relative humidity"
    ``RH_min_pc``, "Lower_bound of relative humidity"
    ``Tcs_set_C``, "Setpoint temperature for cooling system"
    ``Tcs_setb_C``, "Setback point of temperature for cooling system"
    ``Ths_set_C``, "Setpoint temperature for heating system"
    ``Ths_setb_C``, "Setback point of temperature for heating system"
    ``Ve_lsp``, "Minimum outdoor air ventilation rate per person for Air Quality"
    


get_building_internal
---------------------

path: ``inputs/building-properties/internal_loads.dbf``

The following file is used by these scripts: ``demand``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``Ea_Wm2``, "Peak specific electrical load due to computers and devices"
    ``Ed_Wm2``, "Peak specific electrical load due to servers/data centres"
    ``El_Wm2``, "Peak specific electrical load due to artificial lighting"
    ``Epro_Wm2``, "Peak specific electrical load due to industrial processes"
    ``Ev_kWveh``, "Peak capacity of electric battery per vehicle"
    ``Name``, "Unique building ID. It must start with a letter."
    ``Occ_m2p``, "Occupancy density"
    ``Qcpro_Wm2``, "Peak specific process cooling load"
    ``Qcre_Wm2``, "Peak specific cooling load due to refrigeration (cooling rooms)"
    ``Qhpro_Wm2``, "Peak specific process heating load"
    ``Qs_Wp``, "Peak sensible heat load of people"
    ``Vw_ldp``, "Peak specific fresh water consumption (includes cold and hot water)"
    ``Vww_ldp``, "Peak specific daily hot water consumption"
    ``X_ghp``, "Moisture released by occupancy at peak conditions"
    


get_building_supply
-------------------

path: ``inputs/building-properties/supply_systems.dbf``

The following file is used by these scripts: ``decentralized``, ``demand``, ``emissions``, ``system_costs``


.. csv-table::
    :header: "Variable", "Description"

    ``Name``, "Unique building ID. It must start with a letter."
    ``type_cs``, "Type of cooling supply assembly (refers to ""code"" in SUPPLY assemblies)"
    ``type_dhw``, "Type of hot water supply assembly (refers to ""code"" in SUPPLY assemblies)"
    ``type_el``, "Type of electrical supply assembly (refers to ""code"" in SUPPLY assemblies)"
    ``type_hs``, "Type of heating supply assembly (refers to ""code"" in SUPPLY assemblies)"
    


get_building_weekly_schedules
-----------------------------

path: ``inputs/building-properties/schedules/B001.csv``

The following file is used by these scripts: ``demand``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``METADATA``, "TODO"
    ``MONTHLY_MULTIPLIER``, "Monthly probabilities of occupancy throughout the year"
    


get_database_air_conditioning_systems
-------------------------------------

path: ``inputs/technology/assemblies/HVAC.xlsx``

The following file is used by these scripts: ``demand``




.. csv-table:: Worksheet: ``CONTROLLER``
    :header: "Variable", "Description"

    ``code``, Unique ID of the controller
    ``Description``, Describes the type of controller
    ``dT_Qcs``, correction temperature of emission losses due to control system of cooling
    ``dT_Qhs``, correction temperature of emission losses due to control system of heating
    



.. csv-table:: Worksheet: ``COOLING``
    :header: "Variable", "Description"

    ``class_cs``, Type or class of the cooling system
    ``code``, Unique ID of the heating system
    ``convection_cs``, Convective part of the power of the heating system in relation to the total power
    ``Description``, Describes the type of cooling system
    ``dTcs0_ahu_C``, Nominal temperature increase on the water side of the air-handling units
    ``dTcs0_aru_C``, Nominal temperature increase on the water side of the air-recirculation units
    ``dTcs0_scu_C``, Nominal temperature increase on the water side of the sensible cooling units
    ``dTcs_C``, Set-point correction for space emission systems
    ``Qcsmax_Wm2``, Maximum heat flow permitted by cooling system per m2 gross floor area 
    ``Tc_sup_air_ahu_C``, Supply air temperature of the air-handling units
    ``Tc_sup_air_aru_C``, Supply air temperature of the air-recirculation units
    ``Tscs0_ahu_C``, Nominal supply temperature of the water side of the air-handling units
    ``Tscs0_aru_C``, Nominal supply temperature of the water side of the air-recirculation units
    ``Tscs0_scu_C``, Nominal supply temperature of the water side of the sensible cooling units
    



.. csv-table:: Worksheet: ``HEATING``
    :header: "Variable", "Description"

    ``class_hs``, Type or class of the heating system
    ``code``, Unique ID of the heating system
    ``convection_hs``, Convective part of the power of the heating system in relation to the total power
    ``Description``, Description
    ``dThs0_ahu_C``, Nominal temperature increase on the water side of the air-handling units
    ``dThs0_aru_C``, Nominal temperature increase on the water side of the air-recirculation units
    ``dThs0_shu_C``, Nominal temperature increase on the water side of the sensible heating units
    ``dThs_C``, correction temperature of emission losses due to type of heating system
    ``Qhsmax_Wm2``, Maximum heat flow permitted by heating system per m2 gross floor area 
    ``Th_sup_air_ahu_C``, Supply air temperature of the air-recirculation units
    ``Th_sup_air_aru_C``, Supply air temperature of the air-handling units
    ``Tshs0_ahu_C``, Nominal supply temperature of the water side of the air-handling units
    ``Tshs0_aru_C``, Nominal supply temperature of the water side of the air-recirculation units
    ``Tshs0_shu_C``, Nominal supply temperature of the water side of the sensible heating units
    



.. csv-table:: Worksheet: ``HOT_WATER``
    :header: "Variable", "Description"

    ``code``, Unique ID of the hot water supply system
    ``Description``, Describes the Type of hot water supply system
    ``Qwwmax_Wm2``, Maximum heat flow permitted by hot water system per m2 gross floor area 
    ``Tsww0_C``, Typical supply water temperature.
    



.. csv-table:: Worksheet: ``VENTILATION``
    :header: "Variable", "Description"

    ``code``, Unique ID of the type of ventilation
    ``Description``, Describes the Type of ventilation
    ``ECONOMIZER``, Boolean, economizer on
    ``HEAT_REC``, Boolean, heat recovery on
    ``MECH_VENT``, Boolean, mechanical ventilation on
    ``NIGHT_FLSH``, Boolean, night flush on
    ``WIN_VENT``, Boolean, window ventilation on
    




get_database_construction_standards
-----------------------------------

path: ``inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx``

The following file is used by these scripts: ``archetypes_mapper``




.. csv-table:: Worksheet: ``ENVELOPE_ASSEMBLIES``
    :header: "Variable", "Description"

    ``Es``, Fraction of gross floor area with electrical demands.
    ``Hs_ag``, Fraction of above ground gross floor area air-conditioned.
    ``Hs_bg``, Fraction of below ground gross floor area air-conditioned 
    ``Ns``, Fraction of net gross floor area.
    ``STANDARD``,  Unique ID of Construction Standard
    ``type_base``, Basement floor construction assembly (relates to "code" in ENVELOPE assemblies)
    ``type_cons``, Type of construction assembly (relates to "code" in ENVELOPE assemblies)
    ``type_floor``, Internal floor construction assembly (relates to "code" in ENVELOPE assemblies)
    ``type_leak``, Tightness level assembly (relates to "code" in ENVELOPE assemblies)
    ``type_part``, Internal partitions construction assembly (relates to "code" in ENVELOPE assemblies)
    ``type_roof``, Roof construction assembly (relates to "code" in ENVELOPE assemblies)
    ``type_shade``, Shading system assembly (relates to "code" in ENVELOPE assemblies)
    ``type_wall``, External wall construction assembly (relates to "code" in ENVELOPE assemblies)
    ``type_win``, Window assembly (relates to "code" in ENVELOPE assemblies)
    ``void_deck``, Number of floors (from the ground up) with an open envelope (default = 0)
    ``wwr_east``, Window to wall ratio in in facades facing east
    ``wwr_north``, Window to wall ratio in in facades facing north
    ``wwr_south``, Window to wall ratio in in facades facing south
    ``wwr_west``, Window to wall ratio in in facades facing west
    



.. csv-table:: Worksheet: ``HVAC_ASSEMBLIES``
    :header: "Variable", "Description"

    ``cool_ends``, End of the cooling season - use 00|00 when there is none
    ``cool_starts``, Start of the cooling season - use 00|00 when there is none
    ``heat_ends``, End of the heating season - use 00|00 when there is none
    ``heat_starts``, Start of the heating season - use 00|00 when there is none
    ``STANDARD``,  Unique ID of Construction Standard
    ``type_cs``, Type of cooling HVAC assembly (relates to "code" in HVAC assemblies)
    ``type_ctrl``, Type of heating and cooling control HVAC  assembly (relates to "code" in HVAC assemblies)
    ``type_dhw``, Type of hot water HVAC assembly (relates to "code" in HVAC assemblies)
    ``type_hs``, Type of heating HVAC assembly (relates to "code" in HVAC assemblies)
    ``type_vent``, Type of ventilation HVAC assembly (relates to "code" in HVAC assemblies)
    



.. csv-table:: Worksheet: ``STANDARD_DEFINITION``
    :header: "Variable", "Description"

    ``Description``, Description of the construction standard
    ``STANDARD``,  Unique ID of Construction Standard
    ``YEAR_END``, Upper limit of year interval where the building properties apply
    ``YEAR_START``, Lower limit of year interval where the building properties apply
    



.. csv-table:: Worksheet: ``SUPPLY_ASSEMBLIES``
    :header: "Variable", "Description"

    ``STANDARD``, Unique ID of Construction Standard
    ``type_cs``, Type of cooling supply assembly (refers to "code" in SUPPLY assemblies)
    ``type_dhw``, Type of hot water supply assembly (refers to "code" in SUPPLY assemblies)
    ``type_el``, Type of electrical supply assembly (refers to "code" in SUPPLY assemblies)
    ``type_hs``, Type of heating supply assembly (refers to "code" in SUPPLY assemblies)
    




get_database_conversion_systems
-------------------------------

path: ``inputs/technology/components/CONVERSION.xlsx``

The following file is used by these scripts: ``decentralized``, ``optimization``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``




.. csv-table:: Worksheet: ``Absorption_chiller``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``a_e``, parameter in the characteristic equations to calculate the evaporator side 
    ``a_g``, parameter in the characteristic equations to calculate the generator side
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``Description``, Describes the Type of Absorption Chiller
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``e_e``, parameter in the characteristic equations to calculate the evaporator side 
    ``e_g``, parameter in the characteristic equations to calculate the generator side
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``m_cw``, external flow rate of cooling water at the condenser and absorber
    ``m_hw``, external flow rate of hot water at the generator
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``r_e``, parameter in the characteristic equations to calculate the evaporator side 
    ``r_g``, parameter in the characteristic equations to calculate the generator side
    ``s_e``, parameter in the characteristic equations to calculate the evaporator side 
    ``s_g``, parameter in the characteristic equations to calculate the generator side
    ``type``, type of absorption chiller 
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``BH``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``Description``, Describes the type of borehole heat exchanger
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``Boiler``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``Description``, Describes the type of boiler
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``CCGT``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``Description``, Describes the type of combined-cycle gas turbine
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``Chiller``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``Description``, Describes the source of the benchmark standards.
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``CT``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``Description``, Describes the type of cooling tower
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``FC``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``Description``, Describes the type of fuel cell
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``Furnace``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``Description``, Describes the type of furnace
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``HEX``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``a_p``, parameter in the pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x),  where x is the capacity mass flow rate [W/K] 
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``b_p``, parameter in the pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x),  where x is the capacity mass flow rate [W/K] 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``c_p``, parameter in the pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x),  where x is the capacity mass flow rate [W/K] 
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``d_p``, parameter in the pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x),  where x is the capacity mass flow rate [W/K] 
    ``Description``, Describes the type of heat exchanger
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x)  
    ``e_p``, parameter in the pressure loss function, f(x) = a_p + b_p*x^c_p + d_p*ln(x) + e_p*x*ln*(x),  where x is the capacity mass flow rate [W/K] 
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``HP``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``Description``, Describes the source of the heat pump
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``Pump``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``Description``, Describes the source of the benchmark standards.
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``PV``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``Description``, Describes the source of the benchmark standards.
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``misc_losses``, losses from cabling, resistances etc...
    ``module_length_m``, length of the PV module
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``PV_a0``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, where  x is the relative air mass
    ``PV_a1``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, where  x is the relative air mass
    ``PV_a2``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, where  x is the relative air mass
    ``PV_a3``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, where  x is the relative air mass
    ``PV_a4``, parameters for air mass modifier, f(x) = a0 + a1*x + a2*x**2  + a3*x**3 + a4*x**4, where  x is the relative air mass
    ``PV_Bref``, cell maximum power temperature coefficient
    ``PV_n``, nominal efficiency
    ``PV_noct``, nominal operating cell temperature
    ``PV_th``, glazing thickness
    ``type``, redundant
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``PVT``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``Description``, Describes the type of photovoltaic thermal technology
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``SC``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``aperture_area_ratio``, ratio of aperture area to panel area
    ``assumption``, items made by assumptions in this technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c1``, collector heat loss coefficient at zero temperature difference and wind speed
    ``c2``, ctemperature difference dependency of the heat loss coefficient
    ``C_eff``, thermal capacity of module 
    ``cap_max``, maximum capacity 
    ``cap_min``, minimum capacity
    ``code``, identifier of each unique equipment
    ``Cp_fluid``, heat capacity of the heat transfer fluid
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``Description``, Describes the type of solar collector
    ``dP1``, pressure drop at zero flow rate
    ``dP2``, pressure drop at nominal flow rate (mB0)
    ``dP3``, pressure drop at maximum flow rate (mB_max)
    ``dP4``, pressure drop at minimum flow rate (mB_min)
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``IAM_d``, incident angle modifier for diffuse radiation
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of this technology
    ``mB0_r``, nominal flow rate per aperture area
    ``mB_max_r``, maximum flow rate per aperture area
    ``mB_min_r``, minimum flow rate per aperture area
    ``module_area_m2``, module area of a solar collector
    ``module_length_m``, length of a solar collector module
    ``n0``, zero loss efficiency at normal incidence
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``t_max``, maximum operating temperature
    ``type``, type of the solar collector (FP: flate-plate or ET: evacuated-tube)
    ``unit``, unit of the min/max capacity
    



.. csv-table:: Worksheet: ``TES``
    :header: "Variable", "Description"

    ``a``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``assumption``, items made by assumptions in this storage technology
    ``b``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``c``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``C_mat_%``, Working fluid replacement cost factor (fraction of the investment cost)
    ``cap_max``, maximum capacity
    ``cap_min``, minimum capacity
    ``code``, Unique code that identifies the thermal energy storage technology
    ``Cp_kJkgK``, heat capacity of working fluid
    ``currency``, currency-year information of the investment cost function, should be unified to USD
    ``d``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``Description``, Describes the thermal energy storage technology
    ``e``, parameter in the investment cost function, f(x) = a + b*x^c + d*ln(x) + e*x*ln*(x), where x is the capacity 
    ``HL_kJkg``, Lantent heat of working fluid at phase change temperature
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_mat_yr``, lifetime of the working fluid of this storage technology
    ``LT_yr``, lifetime of this storage technology
    ``O&M_%``, operation and maintnance cost factor (fraction of the investment cost)
    ``Rho_T_PHCH_kgm3``, Density of working fluid at phase change temperature
    ``T_max_C``, Maximum temperature of working fluid at full discharge
    ``T_min_C``, Minimum temperature of working fluid at full charge
    ``T_PHCH_C``, Phase change temperature of working fluid
    ``type``, code that identifies whether the storage is used for heating or cooling (different properties of the transport media)
    ``unit``, unit which describes the minimum and maximum capacity
    




get_database_distribution_systems
---------------------------------

path: ``inputs/technology/components/DISTRIBUTION.xlsx``

The following file is used by these scripts: ``optimization``, ``thermal_network``




.. csv-table:: Worksheet: ``THERMAL_GRID``
    :header: "Variable", "Description"

    ``code``, pipe ID from the manufacturer
    ``D_ext_m``, external pipe diameter tolerance for the nominal diameter (DN)
    ``D_ins_m``, maximum pipe diameter tolerance for the nominal diameter (DN)
    ``D_int_m``, internal pipe diameter tolerance for the nominal diameter (DN)
    ``Inv_USD2015perm``, Typical cost of investment for a given pipe diameter.
    ``pipe_DN``, Nominal pipe diameter
    ``Vdot_max_m3s``, maximum volumetric flow rate for the nominal diameter (DN)
    ``Vdot_min_m3s``, minimum volumetric flow rate for the nominal diameter (DN)
    




get_database_envelope_systems
-----------------------------

path: ``inputs/technology/assemblies/ENVELOPE.xlsx``

The following file is used by these scripts: ``demand``, ``radiation``, ``schedule_maker``




.. csv-table:: Worksheet: ``CONSTRUCTION``
    :header: "Variable", "Description"

    ``Cm_Af``, Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790.
    ``code``, Type of construction
    ``Description``, Describes the Type of construction
    



.. csv-table:: Worksheet: ``FLOOR``
    :header: "Variable", "Description"

    ``code``, Type of roof
    ``Description``, Describes the Type of roof
    ``GHG_FLOOR_kgCO2m2``, Embodied emissions per m2 of roof.(entire building life cycle)
    ``U_base``, Thermal transmittance of floor including linear losses (+10%). Defined according to ISO 13790.
    



.. csv-table:: Worksheet: ``ROOF``
    :header: "Variable", "Description"

    ``a_roof``, Solar absorption coefficient. Defined according to ISO 13790.
    ``code``, Type of roof
    ``Description``, Describes the Type of roof
    ``e_roof``, Emissivity of external surface. Defined according to ISO 13790.
    ``GHG_ROOF_kgCO2m2``, Embodied emissions per m2 of roof.(entire building life cycle)
    ``r_roof``, Reflectance in the Red spectrum. Defined according Radiance. (long-wave)
    ``U_roof``, Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.
    



.. csv-table:: Worksheet: ``SHADING``
    :header: "Variable", "Description"

    ``code``, Type of shading
    ``Description``, Describes the source of the benchmark standards.
    ``rf_sh``, Shading coefficient when shading device is active. Defined according to ISO 13790.
    



.. csv-table:: Worksheet: ``TIGHTNESS``
    :header: "Variable", "Description"

    ``code``, Type of tightness
    ``Description``, Describes the Type of tightness
    ``n50``, Air exchanges per hour at a pressure of 50 Pa.
    



.. csv-table:: Worksheet: ``WALL``
    :header: "Variable", "Description"

    ``a_wall``, Solar absorption coefficient. Defined according to ISO 13790.
    ``code``, Type of wall
    ``Description``, Describes the Type of wall
    ``e_wall``, Emissivity of external surface. Defined according to ISO 13790.
    ``GHG_WALL_kgCO2m2``, Embodied emissions per m2 of walls (entire building life cycle)
    ``r_wall``, Reflectance in the Red spectrum. Defined according Radiance. (long-wave)
    ``U_wall``, Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.
    



.. csv-table:: Worksheet: ``WINDOW``
    :header: "Variable", "Description"

    ``code``, Window type code to relate to other databases
    ``Description``, Describes the source of the benchmark standards.
    ``e_win``, Emissivity of external surface. Defined according to ISO 13790.
    ``F_F``, Window frame fraction coefficient. Defined according to ISO 13790.
    ``G_win``, Solar heat gain coefficient. Defined according to ISO 13790.
    ``GHG_WIN_kgCO2m2``, Embodied emissions per m2 of windows.(entire building life cycle)
    ``U_win``, Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790.
    




get_database_feedstocks
-----------------------

path: ``inputs/technology/components/FEEDSTOCKS.xlsx``

The following file is used by these scripts: ``decentralized``, ``emissions``, ``system_costs``, ``optimization``




.. csv-table:: Worksheet: ``BIOGAS``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``COAL``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``DRYBIOMASS``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``GRID``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``NATURALGAS``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``OIL``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``SOLAR``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``WETBIOMASS``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    



.. csv-table:: Worksheet: ``WOOD``
    :header: "Variable", "Description"

    ``GHG_kgCO2MJ``, Non-renewable Green House Gas Emissions factor
    ``hour``, hour of a 24 hour day
    ``Opex_var_buy_USD2015kWh``, buying price
    ``Opex_var_sell_USD2015kWh``, selling price
    ``reference``, reference
    




get_database_standard_schedules_use
-----------------------------------

path: ``inputs/technology/archetypes/schedules/RESTAURANT.csv``

The following file is used by these scripts: ``archetypes_mapper``




.. csv-table:: Worksheet: ``APPLIANCES``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``COOLING``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``ELECTROMOBILITY``
    :header: "Variable", "Description"

    ``1``, Average number of electric vehicles in this hour
    ``2``, Average number of electric vehicles in this hour
    ``3``, Average number of electric vehicles in this hour
    ``4``, Average number of electric vehicles in this hour
    ``5``, Average number of electric vehicles in this hour
    ``6``, Average number of electric vehicles in this hour
    ``7``, Average number of electric vehicles in this hour
    ``8``, Average number of electric vehicles in this hour
    ``9``, Average number of electric vehicles in this hour
    ``10``, Average number of electric vehicles in this hour
    ``11``, Average number of electric vehicles in this hour
    ``12``, Average number of electric vehicles in this hour
    ``13``, Average number of electric vehicles in this hour
    ``14``, Average number of electric vehicles in this hour
    ``15``, Average number of electric vehicles in this hour
    ``16``, Average number of electric vehicles in this hour
    ``17``, Average number of electric vehicles in this hour
    ``18``, Average number of electric vehicles in this hour
    ``19``, Average number of electric vehicles in this hour
    ``20``, Average number of electric vehicles in this hour
    ``21``, Average number of electric vehicles in this hour
    ``22``, Average number of electric vehicles in this hour
    ``23``, Average number of electric vehicles in this hour
    ``24``, Average number of electric vehicles in this hour
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``HEATING``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``LIGHTING``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``METADATA``
    :header: "Variable", "Description"

    ``metadata``, 
    



.. csv-table:: Worksheet: ``MONTHLY_MULTIPLIER``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    



.. csv-table:: Worksheet: ``OCCUPANCY``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``PROCESSES``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``SERVERS``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    



.. csv-table:: Worksheet: ``WATER``
    :header: "Variable", "Description"

    ``1``, 
    ``2``, 
    ``3``, 
    ``4``, 
    ``5``, 
    ``6``, 
    ``7``, 
    ``8``, 
    ``9``, 
    ``10``, 
    ``11``, 
    ``12``, 
    ``13``, 
    ``14``, 
    ``15``, 
    ``16``, 
    ``17``, 
    ``18``, 
    ``19``, 
    ``20``, 
    ``21``, 
    ``22``, 
    ``23``, 
    ``24``, 
    ``DAY``, Day of the week (weekday, saturday, or sunday)
    




get_database_supply_assemblies
------------------------------

path: ``inputs/technology/assemblies/SUPPLY.xlsx``

The following file is used by these scripts: ``demand``, ``emissions``, ``system_costs``




.. csv-table:: Worksheet: ``COOLING``
    :header: "Variable", "Description"

    ``CAPEX_USD2015kW``, Capital costs per kW
    ``code``, Code of cooling supply assembly
    ``Description``, description
    ``efficiency``, efficiency of the all in one system
    ``feedstock``, feedstock used by the the all in one system (refers to the FEEDSTOCK database)
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of assembly
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``reference``, reference
    ``scale``, whether the all in one system is used at the building or the district scale
    



.. csv-table:: Worksheet: ``ELECTRICITY``
    :header: "Variable", "Description"

    ``CAPEX_USD2015kW``, Capital costs per kW
    ``code``, Type of all in one system
    ``Description``, Description of Type of all in one system
    ``efficiency``, efficiency of the all in one system
    ``feedstock``, feedstock used by the the all in one system (refers to the FEEDSTOCK database)
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of assembly
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``reference``, Reference of the data
    ``scale``, whether the all in one system is used at the building or the district scale
    



.. csv-table:: Worksheet: ``HEATING``
    :header: "Variable", "Description"

    ``CAPEX_USD2015kW``, Capital costs per kW
    ``code``, Type of all in one system
    ``Description``, Description of Type of all in one system
    ``efficiency``, efficiency of the all in one system
    ``feedstock``, feedstock used by the the all in one system (refers to the FEEDSTOCK database)
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of assembly
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``reference``, Reference of the data
    ``scale``, whether the all in one system is used at the building or the district scale
    



.. csv-table:: Worksheet: ``HOT_WATER``
    :header: "Variable", "Description"

    ``CAPEX_USD2015kW``, Capital costs per kW
    ``code``, Type of all in one system
    ``Description``, Description of Type of all in one system
    ``efficiency``, efficiency of the all in one system
    ``feedstock``, feedstock used by the the all in one system (refers to the FEEDSTOCK database)
    ``IR_%``, interest rate charged on the loan for the capital cost
    ``LT_yr``, lifetime of assembly
    ``O&M_%``, operation and maintenance cost factor (fraction of the investment cost)
    ``reference``, Reference of the data
    ``scale``, whether the all in one system is used at the building or the district scale
    




get_database_use_types_properties
---------------------------------

path: ``inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx``

The following file is used by these scripts: ``archetypes_mapper``




.. csv-table:: Worksheet: ``INDOOR_COMFORT``
    :header: "Variable", "Description"

    ``code``, use type code (refers to building use type)
    ``RH_max_pc``, Upper bound of relative humidity
    ``RH_min_pc``, Lower_bound of relative humidity
    ``Tcs_set_C``, Setpoint temperature for cooling system
    ``Tcs_setb_C``, Setback point of temperature for cooling system
    ``Ths_set_C``, Setpoint temperature for heating system
    ``Ths_setb_C``, Setback point of temperature for heating system
    ``Ve_lsp``, Indoor quality requirements of indoor ventilation per person
    



.. csv-table:: Worksheet: ``INTERNAL_LOADS``
    :header: "Variable", "Description"

    ``code``, use type code (refers to building use type)
    ``Ea_Wm2``, Peak specific electrical load due to computers and devices
    ``Ed_Wm2``, Peak specific electrical load due to servers/data centres
    ``El_Wm2``, Peak specific electrical load due to artificial lighting
    ``Epro_Wm2``, Peak specific electrical load due to industrial processes
    ``Ev_kWveh``, Peak capacity of electrical battery per vehicle
    ``Occ_m2p``, Occupancy density
    ``Qcpro_Wm2``, Peak specific process cooling load
    ``Qcre_Wm2``, Peak specific cooling load due to refrigeration (cooling rooms)
    ``Qhpro_Wm2``, Peak specific process heating load
    ``Qs_Wp``, Peak sensible heat load of people
    ``Vw_ldp``, Peak specific fresh water consumption (includes cold and hot water)
    ``Vww_ldp``, Peak specific daily hot water consumption
    ``X_ghp``, Moisture released by occupancy at peak conditions
    



