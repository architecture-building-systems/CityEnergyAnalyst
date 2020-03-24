
get_surroundings_geometry
-------------------------

The following file is used by these scripts: 


.. csv-table:: ``inputs/building-geometry/surroundings.shp``
    :header: "Variable", "Description"
    geometry, Geometryheight_bg, Height below ground (basement, etc)Name, Unique building ID. It must start with a letter.floors_bg, Number of floors below ground (basement, etc)height_ag, Height above ground (incl. ground floor)floors_ag, Number of floors above ground (incl. ground floor)


get_zone_geometry
-----------------

The following file is used by these scripts: 


.. csv-table:: ``inputs/building-geometry/zone.shp``
    :header: "Variable", "Description"
    geometry, Geometryheight_bg, Height below ground (basement, etc)Name, Unique building ID. It must start with a letter.floors_bg, Number of floors below ground (basement, etc)height_ag,  Height above ground (incl. ground floor)floors_ag, Number of floors above ground (incl. ground floor)


get_terrain
-----------

The following file is used by these scripts: 


.. csv-table:: ``inputs/topography/terrain.tif``
    :header: "Variable", "Description"
    raster_value, TODO


get_street_network
------------------

The following file is used by these scripts: 


.. csv-table:: ``inputs/networks/streets.shp``
    :header: "Variable", "Description"
    geometry, GeometryId, Unique building ID. It must start with a letter.


get_site_polygon
----------------

The following file is used by these scripts: 


.. csv-table:: ``inputs\building-geometry\site.shp``
    :header: "Variable", "Description"
    geometry, TODOFID, TODO


get_optimization_thermal_network_data_file
------------------------------------------

The following file is used by these scripts: 


.. csv-table:: ``outputs/data/optimization/network/DH_Network_summary_result_0x19b.csv``
    :header: "Variable", "Description"
    Q_DHNf_W, TODOT_DHNf_sup_K, TODOT_DHNf_re_K, TODOmdot_DH_netw_total_kgpers, TODOmcpdata_netw_total_kWperC, TODOQ_DH_losses_W, TODODATE, TODOQcdata_netw_total_kWh, TODO


get_weather
-----------

The following file is used by these scripts: 


.. csv-table:: ``databases/weather/Zug-inducity_1990_2010_TMY.epw``
    :header: "Variable", "Description"
    snowdepth_cm (index = 30), TODOwindspd_ms (index = 21), TODOatmos_Pa (index = 9), Atmospheric pressurezenlum_lux (index = 19), TODOAlbedo (index = 32), Albedoceiling_hgt_m (index = 25), TODOrelhum_percent (index = 8), TODOdifhorrad_Whm2 (index = 15), TODOdifhorillum_lux (index = 18), TODOpresweathobs (index = 26), TODOdirnorillum_lux (index = 17), TODOdays_last_snow (index = 31), Days since last snowglohorrad_Whm2 (index = 13), TODOprecip_wtr_mm (index = 28), TODOminute (index = 4), TODOliq_precip_depth_mm (index = 33), TODOdirnorrad_Whm2 (index = 14), TODOexthorrad_Whm2 (index = 10), TODOvisibility_km (index = 24), TODOaerosol_opt_thousandths (index = 29), TODOopaqskycvr_tenths (index = 23), TODOpresweathcodes (index = 27), TODOmonth (index = 1), TODOday (index = 2), TODOyear (index = 0), TODOdatasource (index = 5), Source of datawinddir_deg (index = 20), TODOglohorillum_lux (index = 16), TODOdrybulb_C (index = 6), TODOdewpoint_C (index = 7), TODOtotskycvr_tenths (index = 22), TODOliq_precip_rate_Hour (index = 34), TODOhorirsky_Whm2 (index = 12), TODOhour (index = 3), TODOextdirrad_Whm2 (index = 11), TODO

