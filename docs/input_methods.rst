
get_optimization_thermal_network_data_file
------------------------------------------

path: ``outputs/data/optimization/network/DH_Network_summary_result_0x19b.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``DATE``, "TODO"
    ``mcpdata_netw_total_kWperC``, "TODO"
    ``mdot_DH_netw_total_kgpers``, "TODO"
    ``Q_DH_losses_W``, "TODO"
    ``Q_DHNf_W``, "TODO"
    ``Qcdata_netw_total_kWh``, "TODO"
    ``T_DHNf_re_K``, "TODO"
    ``T_DHNf_sup_K``, "TODO"
    


get_site_polygon
----------------

path: ``inputs\building-geometry\site.shp``

The following file is used by these scripts: ``zone_helper``


.. csv-table::
    :header: "Variable", "Description"

    ``FID``, "TODO"
    ``geometry``, "TODO"
    


get_street_network
------------------

path: ``inputs/networks/streets.shp``

The following file is used by these scripts: ``network_layout``, ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``geometry``, "Geometry"
    ``Id``, "Unique building ID. It must start with a letter."
    


get_surroundings_geometry
-------------------------

path: ``inputs/building-geometry/surroundings.shp``

The following file is used by these scripts: ``radiation``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``floors_ag``, "Number of floors above ground (incl. ground floor)"
    ``floors_bg``, "Number of floors below ground (basement, etc)"
    ``geometry``, "Geometry"
    ``height_ag``, "Height above ground (incl. ground floor)"
    ``height_bg``, "Height below ground (basement, etc)"
    ``Name``, "Unique building ID. It must start with a letter."
    


get_terrain
-----------

path: ``inputs/topography/terrain.tif``

The following file is used by these scripts: ``radiation``, ``schedule_maker``


.. csv-table::
    :header: "Variable", "Description"

    ``raster_value``, "TODO"
    


get_weather
-----------

path: ``databases/weather/Zug-inducity_1990_2010_TMY.epw``

The following file is used by these scripts: ``weather_helper``


.. csv-table::
    :header: "Variable", "Description"

    ``aerosol_opt_thousandths (index = 29)``, "TODO"
    ``Albedo (index = 32)``, "Albedo"
    ``atmos_Pa (index = 9)``, "Atmospheric pressure"
    ``ceiling_hgt_m (index = 25)``, "TODO"
    ``datasource (index = 5)``, "Source of data"
    ``day (index = 2)``, "TODO"
    ``days_last_snow (index = 31)``, "Days since last snow"
    ``dewpoint_C (index = 7)``, "TODO"
    ``difhorillum_lux (index = 18)``, "TODO"
    ``difhorrad_Whm2 (index = 15)``, "TODO"
    ``dirnorillum_lux (index = 17)``, "TODO"
    ``dirnorrad_Whm2 (index = 14)``, "TODO"
    ``drybulb_C (index = 6)``, "TODO"
    ``extdirrad_Whm2 (index = 11)``, "TODO"
    ``exthorrad_Whm2 (index = 10)``, "TODO"
    ``glohorillum_lux (index = 16)``, "TODO"
    ``glohorrad_Whm2 (index = 13)``, "TODO"
    ``horirsky_Whm2 (index = 12)``, "TODO"
    ``hour (index = 3)``, "TODO"
    ``liq_precip_depth_mm (index = 33)``, "TODO"
    ``liq_precip_rate_Hour (index = 34)``, "TODO"
    ``minute (index = 4)``, "TODO"
    ``month (index = 1)``, "TODO"
    ``opaqskycvr_tenths (index = 23)``, "TODO"
    ``precip_wtr_mm (index = 28)``, "TODO"
    ``presweathcodes (index = 27)``, "TODO"
    ``presweathobs (index = 26)``, "TODO"
    ``relhum_percent (index = 8)``, "TODO"
    ``snowdepth_cm (index = 30)``, "TODO"
    ``totskycvr_tenths (index = 22)``, "TODO"
    ``visibility_km (index = 24)``, "TODO"
    ``winddir_deg (index = 20)``, "TODO"
    ``windspd_ms (index = 21)``, "TODO"
    ``year (index = 0)``, "TODO"
    ``zenlum_lux (index = 19)``, "TODO"
    


get_zone_geometry
-----------------

path: ``inputs/building-geometry/zone.shp``

The following file is used by these scripts: ``archetypes_mapper``, ``decentralized``, ``demand``, ``emissions``, ``network_layout``, ``optimization``, ``photovoltaic``, ``photovoltaic_thermal``, ``radiation``, ``schedule_maker``, ``sewage_potential``, ``shallow_geothermal_potential``, ``solar_collector``, ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``floors_ag``, "Number of floors above ground (incl. ground floor)"
    ``floors_bg``, "Number of floors below ground (basement, etc)"
    ``geometry``, "Geometry"
    ``height_ag``, " Height above ground (incl. ground floor)"
    ``height_bg``, "Height below ground (basement, etc)"
    ``Name``, "Unique building ID. It must start with a letter."
    

