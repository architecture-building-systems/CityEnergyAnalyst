# List of variables in thermal_loads

Especially since I am refactoring them to one big dataframe...

The main variables introduced is `tsd`, which stands for "time step data".

## calc_thermal_loads_new_ventilation

- `T_ext` -> `tsd['T_ext']`
  - outdoor drybulb temperature
  - from: `weather_data.drybulb_C.values`
  - to: `calc_Qdis_ls:text`
  - to: `calc_dhw_heating_demand:T_ext`
- `rh_ext` -> `tsd['rh_ext']`
  - relative humidity
  - from: `weather_data.relhum_percent.values`
-  mixed_schedule -> `tsd[['occ', 'el', 'pro', 'dhw']]`
  - schedule data (occupancy, electric use, probability of occupancy, domestic hot water use
  - from: `functions.calc_mixed_schedule`
  - to: `functions.get_internal_loads`
  - to: `functions.get_occupancy`
- `Ealf`, `Edataf`,  `Eprof`,  `Eref`,  `Qcrefri`,  `Qcdata`,  `vww`, `vw` -> `tsd[['Ealf', 'Edataf', 'Eprof', 'Eref', 'Qcrefri', 'Qcdata', 'vww', 'vw']]`
  - from: `functions.get_internal_loads:Ealf, Edataf, Eprof, Eref, Qcrefri, Qcdata, vww, vw`
  - to: `calc_heat_gains_internal_sensible:Eal_nove, Eprof, Qcdata, Qcrefri`
  - to: `calc_dhw_heating_demand:vw, vww`
  - to: `calc_loads_electrical:Ealf, Edataf, Eprof`
- `people` -> `tsd['people']`
  - from: `functions.get_occupancy:people`
  - to: `functions.get_internal_comfort:people`
  - to: `calc_qv_req:people`
  - to: `calc_heat_gains_internal_sensible:people`
  - to: `calc_heat_gains_internal_latent:people`
- `ve_schedule,  ta_hs_set,  ta_cs_set` -> `tsd[['ve',  'ta_hs_set',  'ta_cs_set']]`
  - from: `functions.get_internal_comfort:ve, ta_hs_set, ta_cs_set`
  - to: `calc_qv_req:ve`
  - to: `ThermalLoadsInput:temp_hs_set, temp_cs_set`
  - to: `calc_temperatures_emission_systems:ta_hs_set`
