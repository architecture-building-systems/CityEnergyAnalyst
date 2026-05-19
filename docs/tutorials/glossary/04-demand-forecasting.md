# Energy Demand Forecasting

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **3**

---

## Files

- [`get_demand_results_file`](#get_demand_results_file)
- [`get_occupancy_model_file`](#get_occupancy_model_file)
- [`get_total_demand`](#get_total_demand)

---

### `get_demand_results_file`

- **Path**: `outputs/data/demand/B001.csv`
- **File type**: `csv`
- **Created by**: `demand`
- **Used by**: `decentralized`, `optimization`, `sewage_potential`, `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `date` | Time stamp for each day of the year ascending in hour intervals. | date | `NA` | YYYY-MM-DD |
| `E_sys_kWh` | End-use total electricity consumption (system-level demand) = Ea + El + Edata + Epro + Eaux + Ev + Eve | float | `[kWh]` | {0.0...n} |
| `Ea_kWh` | End-use electricity for appliances | float | `[kWh]` | {0.0...n} |
| `Eal_kWh` | End-use electricity consumption of appliances and lighting, Eal = El_W + Ea_W | float | `[kWh]` | {0.0...n} |
| `Eaux_kWh` | End-use auxiliary electricity consumption, Eaux = Eaux_fw + Eaux_ww + Eaux_cs + Eaux_hs + Ehs_lat_aux | float | `[kWh]` | {0.0...n} |
| `Edata_kWh` | End-use data centre electricity consumption. | float | `[kWh]` | {0.0...n} |
| `El_kWh` | End-use electricity for lights | float | `[kWh]` | {0.0...n} |
| `Epro_kWh` | End-use electricity consumption for industrial processes. | float | `[kWh]` | {0.0...n} |
| `Ev_kWh` | End-use electricity for electric vehicles | float | `[kWh]` | {0.0...n} |
| `Eve_kWh` | End-use electricity for ventilation | float | `[kWh]` | {0.0...n} |
| `I_rad_kWh` | Radiative heat loss | float | `[kWh]` | {0.0...n} |
| `I_sol_and_I_rad_kWh` | Net radiative heat gain | float | `[kWh]` | {0.0...n} |
| `I_sol_kWh` | Solar heat gain | float | `[kWh]` | {0.0...n} |
| `mcpcdata_sys_kWperC` | Capacity flow rate (mass flow* specific heat capacity) of the chilled water delivered to data centre. | float | `[kW/C]` | {0.0...n} |
| `mcpcre_sys_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to refrigeration. | float | `[kW/C]` | {0.0...n} |
| `mcpcs_sys_ahu_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to air handling units (space cooling). | float | `[kW/C]` | {0.0...n} |
| `mcpcs_sys_aru_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to air recirculation units (space cooling). | float | `[kW/C]` | {0.0...n} |
| `mcpcs_sys_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to space cooling. | float | `[kW/C]` | {0.0...n} |
| `mcpcs_sys_scu_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to sensible cooling units (space cooling). | float | `[kW/C]` | {0.0...n} |
| `mcphs_sys_ahu_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to air handling units (space heating). | float | `[kW/C]` | {0.0...n} |
| `mcphs_sys_aru_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to air recirculation units (space heating). | float | `[kW/C]` | {0.0...n} |
| `mcphs_sys_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to space heating. | float | `[kW/C]` | {0.0...n} |
| `mcphs_sys_shu_kWperC` | Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to sensible heating units (space heating). | float | `[kW/C]` | {0.0...n} |
| `mcptw_kWperC` | Capacity flow rate (mass flow* specific heat capacity) of the fresh water | float | `[kW/C]` | {0.0...n} |
| `mcpww_sys_kWperC` | Capacity flow rate (mass flow* specific heat capacity) of domestic hot water | float | `[kW/C]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `people` | Predicted occupancy: number of people in building | int | `[people]` | {0...n} |
| `Q_gain_lat_peop_kWh` | Latent heat gain from people | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_app_kWh` | Sensible heat gain from appliances | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_base_kWh` | Sensible heat gain from transmission through the base | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_data_kWh` | Sensible heat gain from data centres | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_light_kWh` | Sensible heat gain from lighting | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_peop_kWh` | Sensible heat gain from people | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_pro_kWh` | Sensible heat gain from industrial processes. | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_roof_kWh` | Sensible heat gain from transmission through the roof | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_vent_kWh` | Sensible heat gain from ventilation and infiltration | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_wall_kWh` | Sensible heat gain from transmission through the walls | float | `[kWh]` | {0.0...n} |
| `Q_gain_sen_wind_kWh` | Sensible heat gain from transmission through the windows | float | `[kWh]` | {0.0...n} |
| `Q_loss_sen_ref_kWh` | Sensible heat loss from refrigeration systems | float | `[kWh]` | {0.0...n} |
| `QC_sys_kWh` | Total end-use cooling demand (system-level), QC_sys = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys | float | `[kWh]` | {0.0...n} |
| `Qcdata_kWh` | Data centre space cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcdata_sys_kWh` | End-use data center cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcpro_sys_kWh` | Process cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcre_kWh` | Refrigeration space cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcre_sys_kWh` | End-use refrigeration demand | float | `[kWh]` | {0.0...n} |
| `Qcs_dis_ls_kWh` | Cooling system distribution losses | float | `[kWh]` | {0.0...n} |
| `Qcs_em_ls_kWh` | Cooling system emission losses | float | `[kWh]` | {0.0...n} |
| `Qcs_kWh` | Useful energy for space cooling (thermal demand at point of use) | float | `[kWh]` | {0.0...n} |
| `Qcs_lat_ahu_kWh` | AHU latent cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcs_lat_aru_kWh` | ARU latent cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcs_lat_sys_kWh` | Total latent cooling demand for all systems | float | `[kWh]` | {0.0...n} |
| `Qcs_sen_ahu_kWh` | AHU sensible cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcs_sen_aru_kWh` | ARU sensible cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcs_sen_scu_kWh` | SHU sensible cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcs_sen_sys_kWh` | Total sensible cooling demand for all systems | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_ahu_kWh` | AHU system cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_aru_kWh` | ARU system cooling demand | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_kWh` | End-use space cooling demand (system-level including HVAC losses), Qcs_sys = Qcs_sen_sys + Qcs_lat_sys + Qcs_em_ls + Qcs_dis_ls | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_scu_kWh` | SCU system cooling demand | float | `[kWh]` | {0.0...n} |
| `QH_sys_kWh` | Total end-use heating demand (system-level), QH_sys = Qww_sys + Qhs_sys + Qhpro_sys | float | `[kWh]` | {0.0...n} |
| `Qhpro_sys_kWh` | Process heating demand | float | `[kWh]` | {0.0...n} |
| `Qhs_dis_ls_kWh` | Heating system distribution losses | float | `[kWh]` | {0.0...n} |
| `Qhs_em_ls_kWh` | Heating system emission losses | float | `[kWh]` | {0.0...n} |
| `Qhs_kWh` | Useful energy for space heating (thermal demand at point of use) | float | `[kWh]` | {0.0...n} |
| `Qhs_lat_ahu_kWh` | AHU latent heating demand | float | `[kWh]` | {0.0...n} |
| `Qhs_lat_aru_kWh` | ARU latent heating demand | float | `[kWh]` | {0.0...n} |
| `Qhs_lat_sys_kWh` | Total latent heating demand for all systems | float | `[kWh]` | {0.0...n} |
| `Qhs_sen_ahu_kWh` | AHU sensible heating demand | float | `[kWh]` | {0.0...n} |
| `Qhs_sen_aru_kWh` | ARU sensible heating demand | float | `[kWh]` | {0.0...n} |
| `Qhs_sen_shu_kWh` | SHU sensible heating demand | float | `[kWh]` | {0.0...n} |
| `Qhs_sen_sys_kWh` | Total sensible heating demand | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_ahu_kWh` | Space heating demand in AHU | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_aru_kWh` | Space heating demand in ARU | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_kWh` | End-use space heating demand (system-level including HVAC losses), Qhs_sys = Qhs_sen_sys + Qhs_em_ls + Qhs_dis_ls | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_shu_kWh` | SHU system heating demand | float | `[kWh]` | {0.0...n} |
| `Qww_kWh` | Useful energy for domestic hot water (thermal demand at taps) | float | `[kWh]` | {0.0...n} |
| `Qww_sys_kWh` | End-use domestic hot water demand (system-level including distribution losses) | float | `[kWh]` | {0.0...n} |
| `T_ext_C` | Outdoor temperature | float | `[C]` | {0.0...n} |
| `T_int_C` | Indoor temperature | float | `[C]` | {0.0...n} |
| `Tcdata_sys_re_C` | Cooling supply temperature of the data centre | float | `[C]` | {0.0...n} |
| `Tcdata_sys_sup_C` | Cooling return temperature of the data centre | float | `[C]` | {0.0...n} |
| `Tcre_sys_re_C` | Cooling return temperature of the refrigeration system. | float | `[C]` | {0.0...n} |
| `Tcre_sys_sup_C` | Cooling supply temperature of the refrigeration system. | float | `[C]` | {0.0...n} |
| `Tcs_sys_re_ahu_C` | Return temperature cooling system | float | `[C]` | {0.0...n} |
| `Tcs_sys_re_aru_C` | Return temperature cooling system | float | `[C]` | {0.0...n} |
| `Tcs_sys_re_C` | System cooling return temperature. | float | `[C]` | {0.0...n} |
| `Tcs_sys_re_scu_C` | Return temperature cooling system | float | `[C]` | {0.0...n} |
| `Tcs_sys_sup_ahu_C` | Supply temperature cooling system | float | `[C]` | {0.0...n} |
| `Tcs_sys_sup_aru_C` | Supply temperature cooling system | float | `[C]` | {0.0...n} |
| `Tcs_sys_sup_C` | System cooling supply temperature. | float | `[C]` | {0.0...n} |
| `Tcs_sys_sup_scu_C` | Supply temperature cooling system | float | `[C]` | {0.0...n} |
| `theta_o_C` | Operative temperature in building (RC-model) used for comfort plotting | float | `[C]` | {0.0...n} |
| `Ths_sys_re_ahu_C` | Return temperature heating system | float | `[C]` | {0.0...n} |
| `Ths_sys_re_aru_C` | Return temperature heating system | float | `[C]` | {0.0...n} |
| `Ths_sys_re_C` | Heating system return temperature. | float | `[C]` | {0.0...n} |
| `Ths_sys_re_shu_C` | Return temperature heating system | float | `[C]` | {0.0...n} |
| `Ths_sys_sup_ahu_C` | Supply temperature heating system | float | `[C]` | {0.0...n} |
| `Ths_sys_sup_aru_C` | Supply temperature heating system | float | `[C]` | {0.0...n} |
| `Ths_sys_sup_C` | Heating system supply temperature. | float | `[C]` | {0.0...n} |
| `Ths_sys_sup_shu_C` | Supply temperature heating system | float | `[C]` | {0.0...n} |
| `Tww_sys_re_C` | Return temperature hotwater system | float | `[C]` | {0.0...n} |
| `Tww_sys_sup_C` | Supply temperature hotwater system | float | `[C]` | {0.0...n} |
| `x_int` | Internal mass fraction of humidity (water/dry air) | float | `[kg/kg]` | {0.0...n} |

---

### `get_occupancy_model_file`

- **Path**: `outputs/data/occupancy/B001.csv`
- **File type**: `csv`
- **Created by**: `occupancy`
- **Used by**: `demand`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `DATE` | Time stamp for each day of the year ascending in hourly intervals | date | `NA` | YYYY-MM-DD |
| `Ea_W` | Electrical load due to processes | float | `[Wh]` | {0.0...n} |
| `Ed_W` | Electrical load due to servers/data centers | float | `[Wh]` | {0.0...n} |
| `El_W` | Electrical load due to lighting | float | `[Wh]` | {0.0...n} |
| `Epro_W` | Electrical load due to processes | float | `[Wh]` | {0.0...n} |
| `people_p` | Number of people in the building | float | `[-]` | {0.0...n} |
| `Qcpro_W` | Process cooling load | float | `[Wh]` | {0.0...n} |
| `Qcre_W` | Cooling load due to cool room refrigeration | float | `[Wh]` | {0.0...n} |
| `Qhpro_W` | Process heat load | float | `[Wh]` | {0.0...n} |
| `Qs_W` | Sensible heat load of people | float | `[Wh]` | {0.0...n} |
| `Tcs_set_C` | Set point temperature of space cooling system | string | `[...C]` | alphanumeric |
| `Ths_set_C` | Set point temperature of space heating system | string | `[...C]` | alphanumeric |
| `Ve_lps` | Ventilation rate | float | `[L]` | {0.0...n} |
| `Vw_lph` | Fresh water consumption (includes cold and hot water) | float | `[L]` | {0.0...n} |
| `Vww_lph` | Domestic hot water consumption | float | `[L]` | {0.0...n} |
| `X_gh` | Moisture released by occupants | float | `[g]` | {0.0...n} |

---

### `get_total_demand`

- **Path**: `outputs/data/demand/Total_demand.csv`
- **File type**: `csv`
- **Created by**: `demand`
- **Used by**: `decentralized`, `emissions`, `network_layout`, `system_costs`, `optimization`, `sewage_potential`, `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Af_m2` | Conditioned floor area (heated/cooled) | float | `[m2]` | {0.0...n} |
| `Aocc_m2` | Occupied floor area (heated/cooled) | float | `[m2]` | {0.0...n} |
| `Aroof_m2` | Roof area | float | `[m2]` | {0.0...n} |
| `E_sys0_kW` | Nominal end-use electricity demand | float | `[kW]` | {0.0...n} |
| `E_sys_MWhyr` | End-use total electricity consumption (system-level demand), E_sys =  Eve + Ea + El + Edata + Epro + Eaux + Ev | float | `[MWh/yr]` | {0.0...n} |
| `Ea0_kW` | Nominal end-use electricity for appliances | float | `[kW]` | {0.0...n} |
| `Ea_MWhyr` | End-use electricity for appliances | float | `[MWh/yr]` | {0.0...n} |
| `Eal0_kW` | Nominal Total net electricity for all sources and sinks. | float | `[kW]` | {0.0...n} |
| `Eal_MWhyr` | End-use electricity consumption of appliances and lighting, Eal = El_W + Ea_W | float | `[MWh/yr]` | {0.0...n} |
| `Eaux0_kW` | Nominal Auxiliary electricity consumption. | float | `[kW]` | {0.0...n} |
| `Eaux_MWhyr` | End-use auxiliary electricity consumption, Eaux = Eaux_fw + Eaux_ww + Eaux_cs + Eaux_hs + Ehs_lat_aux | float | `[MWh/yr]` | {0.0...n} |
| `Edata0_kW` | Nominal Data centre electricity consumption. | float | `[kW]` | {0.0...n} |
| `Edata_MWhyr` | Electricity consumption for data centers | float | `[MWh/yr]` | {0.0...n} |
| `El0_kW` | Nominal end-use electricity for lights | float | `[kW]` | {0.0...n} |
| `El_MWhyr` | End-use electricity for lights | float | `[MWh/yr]` | {0.0...n} |
| `Epro0_kW` | Nominal Industrial processes electricity consumption. | float | `[kW]` | {0.0...n} |
| `Epro_MWhyr` | Electricity supplied to industrial processes | float | `[MWh/yr]` | {0.0...n} |
| `Ev0_kW` | Nominal end-use electricity for electric vehicles | float | `[kW]` | {0.0...n} |
| `Ev_MWhyr` | End-use electricity for electric vehicles | float | `[MWh/yr]` | {0.0...n} |
| `Eve0_kW` | Nominal end-use electricity for ventilation | float | `[kW]` | {0.0...n} |
| `Eve_MWhyr` | End-use electricity for ventilation | float | `[MWh/yr]` | {0.0...n} |
| `GFA_m2` | Gross floor area | float | `[m2]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `people0` | Nominal occupancy | int | `[people]` | {0...n} |
| `QC_sys0_kW` | Nominal Total system cooling demand. | float | `[kW]` | {0.0...n} |
| `QC_sys_MWhyr` | Total end-use cooling demand (system-level), QC_sys = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys | float | `[MWh/yr]` | {0.0...n} |
| `Qcdata0_kW` | Nominal Data centre cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcdata_MWhyr` | Data centre cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcdata_sys0_kW` | Nominal end-use data center cooling demand | float | `[kW]` | {0.0...n} |
| `Qcdata_sys_MWhyr` | End-use data center cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcpro_sys0_kW` | Nominal process cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcpro_sys_MWhyr` | Yearly processes cooling demand. | float | `[MWh/yr]` | {0.0...n} |
| `Qcre0_kW` | Nominal Refrigeration cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcre_MWhyr` | Refrigeration cooling demand for the system | float | `[MWh/yr]` | {0.0...n} |
| `Qcre_sys0_kW` | Nominal refrigeration cooling demand | float | `[kW]` | {0.0...n} |
| `Qcre_sys_MWhyr` | End-use refrigeration demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs0_kW` | Nominal Total cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_dis_ls0_kW` | Nominal Cooling distribution losses. | float | `[kW]` | {0.0...n} |
| `Qcs_dis_ls_MWhyr` | Cooling distribution losses | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_em_ls0_kW` | Nominal Cooling emission losses. | float | `[kW]` | {0.0...n} |
| `Qcs_em_ls_MWhyr` | Cooling emission losses | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_lat_ahu0_kW` | Nominal AHU latent cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_lat_ahu_MWhyr` | AHU latent cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_lat_aru0_kW` | Nominal ARU latent cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_lat_aru_MWhyr` | ARU latent cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_lat_sys0_kW` | Nominal System latent cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_lat_sys_MWhyr` | Latent cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_MWhyr` | Useful energy for space cooling (thermal demand at point of use) | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_ahu0_kW` | Nominal AHU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_ahu_MWhyr` | AHU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_aru0_kW` | Nominal ARU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_aru_MWhyr` | ARU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_scu0_kW` | Nominal SCU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_scu_MWhyr` | SCU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sen_sys0_kW` | Nominal Sensible system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sen_sys_MWhyr` | Sensible system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys0_kW` | Nominal end-use space cooling demand | float | `[kW]` | {0.0...n} |
| `Qcs_sys_ahu0_kW` | Nominal AHU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sys_ahu_MWhyr` | AHU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys_aru0_kW` | Nominal ARU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sys_aru_MWhyr` | ARU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys_MWhyr` | End-use space cooling demand (system-level including HVAC losses), Qcs_sys = Qcs_sen_sys + Qcs_lat_sys + Qcs_em_ls + Qcs_dis_ls | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys_scu0_kW` | Nominal SCU system cooling demand. | float | `[kW]` | {0.0...n} |
| `Qcs_sys_scu_MWhyr` | SCU system cooling demand | float | `[MWh/yr]` | {0.0...n} |
| `QH_sys0_kW` | Nominal total building heating demand. | float | `[kW]` | {0.0...n} |
| `QH_sys_MWhyr` | Total end-use heating demand (system-level) | float | `[MWh/yr]` | {0.0...n} |
| `Qhpro_sys0_kW` | Nominal process heating demand. | float | `[kW]` | {0.0...n} |
| `Qhpro_sys_MWhyr` | Yearly processes heating demand. | float | `[MWh/yr]` | {0.0...n} |
| `Qhs0_kW` | Nominal Total heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_dis_ls0_kW` | Nominal Heating system distribution losses. | float | `[kW]` | {0.0...n} |
| `Qhs_dis_ls_MWhyr` | Heating system distribution losses | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_em_ls0_kW` | Nominal Heating emission losses. | float | `[kW]` | {0.0...n} |
| `Qhs_em_ls_MWhyr` | Heating system emission losses | float | `[MWh/year]` | {0.0...n} |
| `Qhs_lat_ahu0_kW` | Nominal AHU latent heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_lat_ahu_MWhyr` | AHU latent heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_lat_aru0_kW` | Nominal ARU latent heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_lat_aru_MWhyr` | ARU latent heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_lat_sys0_kW` | Nominal System latent heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_lat_sys_MWhyr` | System latent heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_MWhyr` | Useful energy for space heating (thermal demand at point of use) | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_ahu0_kW` | Nominal AHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sen_ahu_MWhyr` | Sensible heating demand in AHU | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_aru0_kW` | ARU sensible heating demand | float | `[kW]` | {0.0...n} |
| `Qhs_sen_aru_MWhyr` | ARU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_shu0_kW` | Nominal SHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sen_shu_MWhyr` | SHU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sen_sys0_kW` | Nominal HVAC systems sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sen_sys_MWhyr` | Sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys0_kW` | Nominal end-use space heating demand | float | `[kW]` | {0.0...n} |
| `Qhs_sys_ahu0_kW` | Nominal AHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sys_ahu_MWhyr` | AHU system heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys_aru0_kW` | Nominal ARU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sys_aru_MWhyr` | ARU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys_MWhyr` | End-use space heating demand (system-level including HVAC losses), Qhs_sys = Qhs_sen_sys + Qhs_em_ls + Qhs_dis_ls | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys_shu0_kW` | Nominal SHU sensible heating demand. | float | `[kW]` | {0.0...n} |
| `Qhs_sys_shu_MWhyr` | SHU sensible heating demand | float | `[MWh/yr]` | {0.0...n} |
| `Qww0_kW` | Nominal DHW heating demand. | float | `[kW]` | {0.0...n} |
| `Qww_MWhyr` | Useful energy for domestic hot water (thermal demand at taps) | float | `[MWh/yr]` | {0.0...n} |
| `Qww_sys0_kW` | Nominal end-use hotwater demand | float | `[kW]` | {0.0...n} |
| `Qww_sys_MWhyr` | End-use domestic hot water demand (system-level including distribution losses) | float | `[MWh/yr]` | {0.0...n} |

---

[← Renewable Energy Potential Assessment](03-renewable-energy.md) | [Glossary index](index.md) | [Thermal Network Design →](05-thermal-network.md)
