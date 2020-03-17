
get_database_air_conditioning_systems
-------------------------------------

The following file is used by scripts: ['demand']



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:CONTROLLER**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:COOLING**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:HEATING**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:HOT_WATER**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/air_conditioning_systems.xls:VENTILATION**
    :header: "Variable", "Description"



get_database_conversion_systems
-------------------------------

The following file is used by scripts: ['decentralized', 'optimization', 'photovoltaic', 'photovoltaic_thermal', 'solar_collector']



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



.. csv-table:: **inputs/technology/systems/supply_systems.xls:FC**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:Furnace**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:HEX**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/supply_systems.xls:HP**
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



get_database_distribution_systems
---------------------------------

The following file is used by scripts: ['optimization', 'thermal_network']



.. csv-table:: **inputs/technology/systems/distribution_systems.xls:THERMAL_GRID**
    :header: "Variable", "Description"

     ``Code``,no such column? - Unit: TODO
     ``D_ext_m``,external pipe diameter tolerance for the nominal diameter (DN) - Unit: [m]
     ``D_ins_m``,maximum pipe diameter tolerance for the nominal diameter (DN) - Unit: [m]
     ``D_int_m``,internal pipe diameter tolerance for the nominal diameter (DN) - Unit: [m]
     ``Inv_USD2015perm``,Typical cost of investment for a given pipe diameter. - Unit: [$/m]
     ``Pipe_DN``,Nominal pipe diameter - Unit: [-]
     ``Vdot_max_m3s``,maximum volumetric flow rate for the nominal diameter (DN) - Unit: [m3/s]
     ``Vdot_min_m3s``,minimum volumetric flow rate for the nominal diameter (DN) - Unit: [m3/s]


get_database_envelope_systems
-----------------------------

The following file is used by scripts: ['demand', 'radiation', 'schedule_maker']



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:CONSTRUCTION**
    :header: "Variable", "Description"

     ``Cm_Af``,Internal heat capacity per unit of air conditioned area. Defined according to ISO 13790. - Unit: [J/Km2]
     ``Description``,Describes the Type of construction - Unit: [-]
     ``code``,Type of construction - Unit: [-]


.. csv-table:: **inputs/technology/systems/envelope_systems.xls:FLOOR**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/systems/envelope_systems.xls:ROOF**
    :header: "Variable", "Description"

     ``Description``,Describes the Type of roof - Unit: [-]
     ``code``,Type of roof - Unit: [-]
     ``Description``,Describes the Type of roof - Unit: [-]
     ``GHG_ROOF_kgCO2m2``,Embodied emissions per m2 of roof.(entire building life cycle) - Unit: [kg CO2-eq/m2]
     ``U_roof``,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. - Unit: [-]
     ``a_roof``,Solar absorption coefficient. Defined according to ISO 13790. - Unit: [-]
     ``code``,Type of roof - Unit: [-]
     ``e_roof``,Emissivity of external surface. Defined according to ISO 13790. - Unit: [-]
     ``r_roof``,Reflectance in the Red spectrum. Defined according Radiance. (long-wave) - Unit: [-]


.. csv-table:: **inputs/technology/systems/envelope_systems.xls:SHADING**
    :header: "Variable", "Description"

     ``Description``,Describes the source of the benchmark standards. - Unit: [-]
     ``code``,Type of shading - Unit: [-]
     ``rf_sh``,Shading coefficient when shading device is active. Defined according to ISO 13790. - Unit: [-]


.. csv-table:: **inputs/technology/systems/envelope_systems.xls:TIGHTNESS**
    :header: "Variable", "Description"

     ``Description``,Describes the Type of tightness - Unit: [-]
     ``code``,Type of tightness - Unit: [-]
     ``n50``,Air exchanges per hour at a pressure of 50 Pa. - Unit: [1/h]


.. csv-table:: **inputs/technology/systems/envelope_systems.xls:WALL**
    :header: "Variable", "Description"

     ``Description``,Describes the Type of wall - Unit: [-]
     ``GHG_WALL_kgCO2m2``,Embodied emissions per m2 of walls (entire building life cycle) - Unit: [kg CO2-eq/m2]
     ``U_wall``,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. - Unit: [-]
     ``a_wall``,Solar absorption coefficient. Defined according to ISO 13790. - Unit: [-]
     ``code``,Type of wall - Unit: [-]
     ``e_wall``,Emissivity of external surface. Defined according to ISO 13790. - Unit: [-]
     ``r_wall``,Reflectance in the Red spectrum. Defined according Radiance. (long-wave) - Unit: [-]


.. csv-table:: **inputs/technology/systems/envelope_systems.xls:WINDOW**
    :header: "Variable", "Description"

     ``Description``,Describes the source of the benchmark standards. - Unit: [-]
     ``F_F``,Window frame fraction coefficient. Defined according to ISO 13790. - Unit: [m2-frame/m2-window]
     ``G_win``,Solar heat gain coefficient. Defined according to ISO 13790. - Unit: [-]
     ``U_win``,Thermal transmittance of windows including linear losses (+10%). Defined according to ISO 13790. - Unit: [-]
     ``code``,Building use. It relates to the uses stored in the input database of Zone_occupancy - Unit: [-]
     ``e_win``,Emissivity of external surface. Defined according to ISO 13790. - Unit: [-]


get_database_feedstocks
-----------------------

The following file is used by scripts: ['decentralized', 'emissions', 'system_costs', 'optimization']



.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:BIOGAS**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:COAL**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:DRYBIOMASS**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:GRID**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:NATURALGAS**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:OIL**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:SOLAR**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:WETBIOMASS**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


.. csv-table:: **inputs/technology/feedstocks/feedstocks.xls:WOOD**
    :header: "Variable", "Description"

     ``GHG_kgCO2MJ``,Non-renewable Green House Gas Emissions factor - Unit: [kg CO2-eq/MJ-oil eq]
     ``Opex_var_buy_USD2015kWh``,buying price - Unit: [-]
     ``Opex_var_sell_USD2015kWh``,selling price - Unit: [-]
     ``hour``,hour of a 24 hour day - Unit: [-]
     ``reference``,reference - Unit: [-]


get_database_standard_schedules_use
-----------------------------------

The following file is used by scripts: ['archetypes_mapper']



.. csv-table:: **inputs/technology/archetypes/schedules/RESTAURANT.csv**
    :header: "Variable", "Description"

     ``CH-SIA-2014``,metadata - Unit: [-]
     ``METADATA``,metadata - Unit: [-]
     ``RESTAURANT``,metadata - Unit: [-]


get_database_supply_assemblies
------------------------------

The following file is used by scripts: ['demand', 'emissions', 'system_costs']



.. csv-table:: **inputs/technology/assemblies/supply.xls:COOLING**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/assemblies/supply.xls:ELECTRICITY**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/assemblies/supply.xls:HEATING**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/assemblies/supply.xls:HOT_WATER**
    :header: "Variable", "Description"



get_database_use_types_properties
---------------------------------

The following file is used by scripts: ['archetypes_mapper']



.. csv-table:: **inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx:INDOOR_COMFORT**
    :header: "Variable", "Description"



.. csv-table:: **inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx:INTERNAL_LOADS**
    :header: "Variable", "Description"



get_optimization_thermal_network_data_file
------------------------------------------

The following file is used by scripts: ['optimization']



.. csv-table:: **outputs/data/optimization/network/DH_Network_summary_result_0x19b.csv**
    :header: "Variable", "Description"

     ``DATE``,TODO - Unit: TODO
     ``Q_DHNf_W``,TODO - Unit: TODO
     ``Q_DH_losses_W``,TODO - Unit: TODO
     ``Qcdata_netw_total_kWh``,TODO - Unit: TODO
     ``T_DHNf_re_K``,TODO - Unit: TODO
     ``T_DHNf_sup_K``,TODO - Unit: TODO
     ``mcpdata_netw_total_kWperC``,TODO - Unit: TODO
     ``mdot_DH_netw_total_kgpers``,TODO - Unit: TODO


get_street_network
------------------

The following file is used by scripts: ['network_layout', 'optimization']



.. csv-table:: **inputs/networks/streets.shp**
    :header: "Variable", "Description"

     ``Id``,Unique building ID. It must start with a letter. - Unit: [-]
     ``geometry``,Geometry - Unit: [-]


get_surroundings_geometry
-------------------------

The following file is used by scripts: ['radiation', 'schedule_maker']



.. csv-table:: **inputs/building-geometry/surroundings.shp**
    :header: "Variable", "Description"

     ``Name``,Unique building ID. It must start with a letter. - Unit: [-]
     ``floors_ag``,Number of floors above ground (incl. ground floor) - Unit: [-]
     ``floors_bg``,Number of floors below ground (basement, etc) - Unit: [-]
     ``geometry``,Geometry - Unit: [-]
     ``height_ag``,Height above ground (incl. ground floor) - Unit: [m]
     ``height_bg``,Height below ground (basement, etc) - Unit: [m]


get_terrain
-----------

The following file is used by scripts: ['radiation', 'schedule_maker']



.. csv-table:: **inputs/topography/terrain.tif**
    :header: "Variable", "Description"

     ``raster_value``,TODO - Unit: TODO


get_weather
-----------

The following file is used by scripts: ['weather_helper']



.. csv-table:: **databases/weather/Zug-inducity_1990_2010_TMY.epw**
    :header: "Variable", "Description"



get_zone_geometry
-----------------

The following file is used by scripts: ['archetypes_mapper', 'decentralized', 'demand', 'emissions', 'network_layout', 'optimization', 'photovoltaic', 'photovoltaic_thermal', 'radiation', 'schedule_maker', 'sewage_potential', 'shallow_geothermal_potential', 'solar_collector', 'thermal_network']



.. csv-table:: **inputs/building-geometry/zone.shp**
    :header: "Variable", "Description"

     ``Name``,Unique building ID. It must start with a letter. - Unit: [-]
     ``floors_ag``,Number of floors above ground (incl. ground floor) - Unit: [-]
     ``floors_bg``,Number of floors below ground (basement, etc) - Unit: [-]
     ``geometry``,Geometry - Unit: [-]
     ``height_ag``, Height above ground (incl. ground floor) - Unit: [m]
     ``height_bg``,Height below ground (basement, etc) - Unit: [m]

