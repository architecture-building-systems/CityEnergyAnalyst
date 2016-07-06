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
