# Table of contents
- [test_demand](#test_demand)
   - [demand_calculation](#demand_calculation)
      - [read_building_properties](#read_building_properties)
         - [get_temperatures](#get_temperatures)
         - [get_prop_RC_model](#get_prop_rc_model)
            - [AmFunction](#amfunction)
            - [CmFunction](#cmfunction)
         - [create_windows](#create_windows)
      - [calc_thermal_loads_new_ventilation](#calc_thermal_loads_new_ventilation)
         - [calc_mixed_schedule](#calc_mixed_schedule)
         - [get_internal_loads](#get_internal_loads)
         - [get_occupancy](#get_occupancy)
         - [get_internal_comfort](#get_internal_comfort)
         - [get_properties_building_envelope](#get_properties_building_envelope)
         - [get_properties_building_systems](#get_properties_building_systems)
            - [calculate_pipe_transmittance_values](#calculate_pipe_transmittance_values)
            - [Calc_form](#calc_form)
               - [calc_qv_req](#calc_qv_req)
         - [calc_heat_gains_solar](#calc_heat_gains_solar)
            - [Calc_Rf_sh](#calc_rf_sh)
               - [calc_gl](#calc_gl)
         - [calc_heat_gains_internal_sensible](#calc_heat_gains_internal_sensible)
         - [calc_comp_heat_gains_sensible](#calc_comp_heat_gains_sensible)
         - [calc_heat_gains_internal_latent](#calc_heat_gains_internal_latent)
         - [calc_capacity_heating_cooling_system](#calc_capacity_heating_cooling_system)
         - [get_properties_natural_ventilation](#get_properties_natural_ventilation)
            - [calc_qv_delta_p_ref](#calc_qv_delta_p_ref)
            - [get_building_geometry_ventilation](#get_building_geometry_ventilation)
            - [calc_coeff_lea_zone](#calc_coeff_lea_zone)
            - [allocate_default_leakage_paths](#allocate_default_leakage_paths)
            - [lookup_coeff_wind_pressure](#lookup_coeff_wind_pressure)
            - [calc_coeff_vent_zone](#calc_coeff_vent_zone)
            - [allocate_default_ventilation_openings](#allocate_default_ventilation_openings)
         - [calc_tHC_corr](#calc_thc_corr)
         - [calc_thermal_load_mechanical_and_natural_ventilation_timestep](#calc_thermal_load_mechanical_and_natural_ventilation_timestep)
            - [calc_h_ve_adj](#calc_h_ve_adj)
            - [calc_Htr](#calc_htr)
            - [calc_TL](#calc_tl)
               - [Calc_Im_tot](#calc_im_tot)
               - [Calc_Tm](#calc_tm)
         - [calc_thermal_load_hvac_timestep](#calc_thermal_load_hvac_timestep)
            - [calc_hex](#calc_hex)
               - [calc_w](#calc_w)
            - [calc_hvac](#calc_hvac)
               - [calc_h](#calc_h)
               - [calc_w3_cooling_case](#calc_w3_cooling_case)
                  - [calc_Qdis_ls](#calc_qdis_ls)
         - [calc_temperatures_emission_systems](#calc_temperatures_emission_systems)
            - [calc_RAD](#calc_rad)
            - [calc_Ccoil2](#calc_ccoil2)
         - [calc_dhw_heating_demand](#calc_dhw_heating_demand)
            - [calc_Qww_ls_r](#calc_qww_ls_r)
               - [calc_disls](#calc_disls)
            - [calc_Qww_ls_nr](#calc_qww_ls_nr)
         - [calc_pumping_systems_aux_loads](#calc_pumping_systems_aux_loads)
            - [calc_Eaux_ww](#calc_eaux_ww)
            - [calc_Eaux_hs_dis](#calc_eaux_hs_dis)
            - [calc_Eaux_cs_dis](#calc_eaux_cs_dis)
            - [calc_Eaux_ve](#calc_eaux_ve)
         - [calc_loads_electrical](#calc_loads_electrical)
         - [results_to_csv](#results_to_csv)
            - [calc_Eaux_fw](#calc_eaux_fw)
               - [calc_w3_heating_case](#calc_w3_heating_case)
                  - [calc_Hcoil2](#calc_hcoil2)
                  - [calc_TABSH](#calc_tabsh)

# AmFunction
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **x** `["<type 'unicode'>"]`: *u'T3'*


### Output
- `["<type 'float'>"]`: 3.2

[TOC](#table-of-contents)
---

# Calc_Im_tot
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **I_m** `["<type 'numpy.float64'>"]`: *2724.4521715126948*
- **Htr_em** `["<type 'numpy.float64'>"]`: *582.9963349687813*
- **te_t** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **Htr_3** `["<type 'numpy.float64'>"]`: *2590.6666958115343*
- **I_st** `["<type 'numpy.float64'>"]`: *-994.95409442637401*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **Htr_1** `["<type 'numpy.float64'>"]`: *1297.9787346036153*
- **I_ia** `["<type 'numpy.float64'>"]`: *1789.9699685754961*
- **IHC_nd** `["<type 'int'>"]`: *0*
- **Hve** `["<type 'numpy.float64'>"]`: *1414.5649132349504*
- **Htr_2** `["<type 'numpy.float64'>"]`: *2701.3529635310124*


### Output
- `["<type 'numpy.float64'>"]`: 31273.645775067431

[TOC](#table-of-contents)
---

# Calc_Rf_sh
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **ShadingType** `["<type 'unicode'>"]`: *u'T1'*


### Output
- `["<type 'numpy.float64'>"]`: 0.080000000000000002

[TOC](#table-of-contents)
---

# Calc_Tm
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **Htr_3** `["<type 'numpy.float64'>"]`: *2590.6666958115343*
- **Htr_1** `["<type 'numpy.float64'>"]`: *1297.9787346036153*
- **tm_t0** `["<type 'int'>"]`: *16*
- **Cm** `["<type 'numpy.float64'>"]`: *651371895.40593004*
- **Htr_em** `["<type 'numpy.float64'>"]`: *582.9963349687813*
- **Im_tot** `["<type 'numpy.float64'>"]`: *31273.645775067431*
- **Htr_ms** `["<type 'numpy.float64'>"]`: *63226.498647402281*
- **I_st** `["<type 'numpy.float64'>"]`: *-994.95409442637401*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **te_t** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **I_ia** `["<type 'numpy.float64'>"]`: *1789.9699685754961*
- **IHC_nd** `["<type 'int'>"]`: *0*
- **Hve** `["<type 'numpy.float64'>"]`: *1414.5649132349504*
- **Htr_is** `["<type 'numpy.float64'>"]`: *15748.652178585824*


### Output
- `["<type 'tuple'>"]`: (15.946568617146644, 15.663563567746825, 15.202170683665049, 15.520531773681475)

[TOC](#table-of-contents)
---

# Calc_form
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Lw** `["<type 'numpy.float64'>"]`: *16.008581384100001*
- **Ll** `["<type 'numpy.float64'>"]`: *32.648092418099999*
- **footprint** `["<type 'numpy.float64'>"]`: *402.0814169172408*


### Output
- `["<type 'numpy.float64'>"]`: 0.76931348014904022

[TOC](#table-of-contents)
---

# CmFunction
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **x** `["<type 'unicode'>"]`: *u'T3'*


### Output
- `["<type 'int'>"]`: 300000

[TOC](#table-of-contents)
---

# allocate_default_leakage_paths
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **coeff_lea_zone** `["<type 'numpy.float64'>"]`: *2130.2643780536373*
- **area_facade_zone** `["<type 'numpy.float64'>"]`: *1237.0067791693345*
- **area_roof_zone** `["<type 'numpy.float64'>"]`: *402.0814169172408*
- **height_zone** `["<type 'numpy.float64'>"]`: *12.0*


### Output
- `["<type 'tuple'>"]`: (array([ 401.92338084,  401.92338084,  401.92338084,  401.92338084,
        522.57085469]), array([  3.,   3.,   9.,   9.,  12.]), array([ 0.,  1.,  0.,  1.,  2.]))

[TOC](#table-of-contents)
---

# allocate_default_ventilation_openings
- number of invocations: 1
- max duration: 0.027 s
- avg duration: 0.027 s
- min duration: 0.027 s
- total duration: 0.027 s

### Input
- **coeff_vent_zone** `["<type 'float'>"]`: *0.0*
- **height_zone** `["<type 'numpy.float64'>"]`: *12.0*


### Output
- `["<type 'tuple'>"]`: (array([ 0.,  0.,  0.,  0.]), array([ 3.,  3.,  9.,  9.]), array([ 0.,  1.,  0.,  1.]))

[TOC](#table-of-contents)
---

# calc_Ccoil2
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **Qc** `["<type 'numpy.float64'>"]`: *-0*
- **tasup** `["<type 'numpy.float64'>"]`: *273.0*
- **tare** `["<type 'numpy.float64'>"]`: *273.0*
- **Qc0** `["<type 'numpy.float64'>"]`: *-281104.46918348083*
- **tare_0** `["<type 'numpy.float64'>"]`: *297.52499999999998*
- **tasup_0** `["<type 'numpy.float64'>"]`: *288.5*
- **tsc0** `["<type 'numpy.int64'>"]`: *280*
- **trc0** `["<type 'numpy.int64'>"]`: *288*
- **wr** `["<type 'numpy.float64'>"]`: *0.0*
- **ws** `["<type 'numpy.float64'>"]`: *0.0*
- **ma0** `["<type 'numpy.float64'>"]`: *289.39212124203419*
- **ma** `["<type 'numpy.float64'>"]`: *0.0*
- **Cpa** `["<type 'numpy.float64'>"]`: *1.008*
- **LMRT0** `["<type 'numpy.float64'>"]`: *4.7866387565955035*
- **UA0** `["<type 'numpy.float64'>"]`: *-58726.902838896574*
- **mCw0** `["<type 'numpy.float64'>"]`: *35138.058647935104*
- **Qcsf** `["<type 'numpy.float64'>"]`: *-0*


### Output
- `["<type 'tuple'>"]`: (0, 0, 0)

[TOC](#table-of-contents)
---

# calc_Eaux_cs_dis
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Qcsf** `["<type 'numpy.float64'>"]`: *-0*
- **Qcsf0** `["<type 'numpy.float64'>"]`: *-281104.46918348083*
- **Imax** `["<type 'numpy.float64'>"]`: *88.705510978710478*
- **deltaP_des** `["<type 'numpy.float64'>"]`: *11.531716427232364*
- **b** `["<type 'numpy.float64'>"]`: *1.2*
- **ts** `["<type 'numpy.int32'>"]`: *0*
- **tr** `["<type 'numpy.int32'>"]`: *0*
- **cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*


### Output
- `["<type 'float'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_Eaux_fw
- number of invocations: 1
- max duration: 0.04 s
- avg duration: 0.04 s
- min duration: 0.04 s
- total duration: 0.04 s

### Input
- **freshw** `["<type 'numpy.ndarray'>"]`: *array([ 0.05684067,  0.02842034,  0.00710508, ...,  0.2397966 ,
        0.13322033,  0.10124745])*
- **nf** `["<type 'numpy.float64'>"]`: *7.0*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E2B8F0>*


### Output
- `["<type 'numpy.ndarray'>"]`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

[TOC](#table-of-contents)
---

# calc_Eaux_hs_dis
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Qhsf** `["<type 'numpy.float64'>"]`: *0.0*
- **Qhsf0** `["<type 'numpy.float64'>"]`: *296485.76361481688*
- **Imax** `["<type 'numpy.float64'>"]`: *88.705510978710478*
- **deltaP_des** `["<type 'numpy.float64'>"]`: *11.531716427232364*
- **b** `["<type 'numpy.float64'>"]`: *1.2*
- **ts** `["<type 'numpy.int32'>"]`: *0*
- **tr** `["<type 'numpy.int32'>"]`: *0*
- **cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*


### Output
- `["<type 'float'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_Eaux_ve
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Qhsf** `["<type 'numpy.float64'>"]`: *0.0*
- **Qcsf** `["<type 'numpy.float64'>"]`: *-0*
- **P_ve** `["<type 'numpy.float64'>"]`: *0.55000000000000004*
- **qve** `["<type 'numpy.float64'>"]`: *1.1694485063119631*
- **SystemH** `["<type 'numpy.unicode_'>"]`: *u'T1'*
- **SystemC** `["<type 'numpy.unicode_'>"]`: *u'T3'*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*


### Output
- `["<type 'float'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_Eaux_ww
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **Qww** `["<type 'numpy.float64'>"]`: *0.0*
- **Qwwf** `["<type 'numpy.float64'>"]`: *0.0*
- **Qwwf0** `["<type 'numpy.float64'>"]`: *8928.0324494644647*
- **Imax** `["<type 'numpy.float64'>"]`: *88.705510978710478*
- **deltaP_des** `["<type 'numpy.float64'>"]`: *11.531716427232364*
- **b** `["<type 'numpy.float64'>"]`: *1.2*
- **qV_des** `["<type 'numpy.float64'>"]`: *0.0*


### Output
- `["<type 'float'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_Hcoil2
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

### Input
- **Qh** `["<type 'numpy.float64'>"]`: *0.0*
- **tasup** `["<type 'numpy.float64'>"]`: *nan*
- **tare** `["<type 'numpy.float64'>"]`: *290.94999999999999*
- **Qh0** `["<type 'numpy.float64'>"]`: *6069.8981795983327*
- **tare_0** `["<type 'numpy.float64'>"]`: *286.69999999999999*
- **tasup_0** `["<type 'numpy.float64'>"]`: *309.5*
- **tsh0** `["<type 'numpy.int64'>"]`: *313*
- **trh0** `["<type 'numpy.int64'>"]`: *293*
- **wr** `["<type 'numpy.float64'>"]`: *0.0*
- **ws** `["<type 'numpy.float64'>"]`: *0.0*
- **ma0** `["<type 'numpy.float64'>"]`: *0.36707176686581044*
- **ma** `["<type 'numpy.float64'>"]`: *0.0*
- **Cpa** `["<type 'numpy.float64'>"]`: *1.008*
- **LMRT0** `["<type 'numpy.complex128'>"]`: *(1.9781714747962607-13.330104869215896j)*
- **UA0** `["<type 'numpy.complex128'>"]`: *(66.117721476631871+445.54083011832188j)*
- **mCw0** `["<type 'numpy.float64'>"]`: *303.49490897991666*
- **Qhsf** `["<type 'numpy.float64'>"]`: *0.0*


### Output
- `["<type 'tuple'>"]`: (0, 0, 0)

[TOC](#table-of-contents)
---

# calc_Htr
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **Hve** `["<type 'numpy.float64'>"]`: *1414.5649132349504*
- **Htr_is** `["<type 'numpy.float64'>"]`: *15748.652178585824*
- **Htr_ms** `["<type 'numpy.float64'>"]`: *63226.498647402281*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*


### Output
- `["<type 'tuple'>"]`: (1297.9787346036153, 2701.3529635310124, 2590.6666958115343)

[TOC](#table-of-contents)
---

# calc_Qdis_ls
- number of invocations: 1
- max duration: 0.037 s
- avg duration: 0.037 s
- min duration: 0.037 s
- total duration: 0.037 s

### Input
- **tair** `["<type 'numpy.float64'>"]`: *15.202170683665049*
- **text** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **Qhs** `["<type 'numpy.float64'>"]`: *0.0*
- **Qcs** `["<type 'numpy.float64'>"]`: *0.0*
- **tsh** `["<type 'numpy.int64'>"]`: *90*
- **trh** `["<type 'numpy.int64'>"]`: *70*
- **tsc** `["<type 'numpy.int64'>"]`: *7*
- **trc** `["<type 'numpy.int64'>"]`: *15*
- **Qhs_max** `["<type 'numpy.float64'>"]`: *294916.76361481688*
- **Qcs_max** `["<type 'numpy.float64'>"]`: *-152740.15924554263*
- **D** `["<type 'numpy.int32'>"]`: *20*
- **Y** `["<type 'numpy.float64'>"]`: *0.29999999999999999*
- **SystemH** `["<type 'numpy.unicode_'>"]`: *u'T1'*
- **SystemC** `["<type 'numpy.unicode_'>"]`: *u'T3'*
- **Bf** `["<type 'numpy.float64'>"]`: *0.69999999999999996*
- **Lv** `["<type 'numpy.float64'>"]`: *67.916762127496582*


### Output
- `["<type 'tuple'>"]`: (0, 0)

[TOC](#table-of-contents)
---

# calc_Qww_ls_nr
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **tair** `["<type 'numpy.float64'>"]`: *15.202170683665049*
- **Qww** `["<type 'numpy.float64'>"]`: *0.0*
- **Lvww_dis** `["<type 'numpy.float64'>"]`: *50.246706155723558*
- **Lvww_c** `["<type 'numpy.float64'>"]`: *55.259252908257515*
- **Y** `["<type 'numpy.float64'>"]`: *0.29999999999999999*
- **Qww_0** `["<type 'numpy.float64'>"]`: *6509.6247369541134*
- **V** `["<type 'numpy.float64'>"]`: *81.45987041393002*
- **Flowtap** `["<type 'numpy.float64'>"]`: *0.035999999999999997*
- **twws** `["<type 'numpy.int64'>"]`: *60*
- **Cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*
- **Pwater** `["<type 'numpy.int32'>"]`: *998*
- **Bf** `["<type 'numpy.float64'>"]`: *0.69999999999999996*
- **te** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E2DFD0>*


### Output
- `["<type 'numpy.float64'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_Qww_ls_r
- number of invocations: 1
- max duration: 0.086 s
- avg duration: 0.086 s
- min duration: 0.086 s
- total duration: 0.086 s

### Input
- **Tair** `["<type 'numpy.float64'>"]`: *15.202170683665049*
- **Qww** `["<type 'numpy.float64'>"]`: *0.0*
- **lsww_dis** `["<type 'numpy.float64'>"]`: *183.34912611426176*
- **lcww_dis** `["<type 'numpy.float64'>"]`: *72.543326121114177*
- **Y** `["<type 'numpy.float64'>"]`: *0.40000000000000002*
- **Qww_0** `["<type 'numpy.float64'>"]`: *6509.6247369541134*
- **V** `["<type 'numpy.float64'>"]`: *81.45987041393002*
- **Flowtap** `["<type 'numpy.float64'>"]`: *0.035999999999999997*
- **twws** `["<type 'numpy.int64'>"]`: *60*
- **Cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*
- **Pwater** `["<type 'numpy.int32'>"]`: *998*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E2D8F0>*


### Output
- `["<type 'numpy.float64'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_RAD
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Qh** `["<type 'numpy.float64'>"]`: *0.0*
- **tair** `["<type 'numpy.float64'>"]`: *15.202170683665049*
- **Qh0** `["<type 'numpy.float64'>"]`: *296485.76361481688*
- **tair0** `["<type 'numpy.float64'>"]`: *22.0*
- **tsh0** `["<type 'numpy.int64'>"]`: *90*
- **trh0** `["<type 'numpy.int64'>"]`: *70*
- **nh** `["<type 'numpy.float64'>"]`: *0.29999999999999999*


### Output
- `["<type 'tuple'>"]`: (0, 0, 0)

[TOC](#table-of-contents)
---

# calc_TABSH
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **Qh** `["<type 'numpy.float64'>"]`: *79965.596518869046*
- **tair** `["<type 'numpy.float64'>"]`: *22.0*
- **Qh0** `["<type 'numpy.float64'>"]`: *79965.596518869046*
- **tair0** `["<type 'numpy.float64'>"]`: *22.0*
- **tsh0** `["<type 'numpy.int64'>"]`: *40*
- **trh0** `["<type 'numpy.int64'>"]`: *35*
- **nh** `["<type 'numpy.float64'>"]`: *0.20000000000000001*


### Output
- `["<type 'tuple'>"]`: (40.0, 35.0, 15.993119303773808)

[TOC](#table-of-contents)
---

# calc_TL
- number of invocations: 1
- max duration: 0.142 s
- avg duration: 0.142 s
- min duration: 0.142 s
- total duration: 0.142 s

### Input
- **SystemH** `["<type 'unicode'>"]`: *u'T1'*
- **SystemC** `["<type 'unicode'>"]`: *u'T3'*
- **tm_t0** `["<type 'int'>"]`: *16*
- **te_t** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **tintH_set** `["<type 'numpy.float64'>"]`: *12.0*
- **tintC_set** `["<type 'numpy.int32'>"]`: *50*
- **Htr_em** `["<type 'numpy.float64'>"]`: *582.9963349687813*
- **Htr_ms** `["<type 'numpy.float64'>"]`: *63226.498647402281*
- **Htr_is** `["<type 'numpy.float64'>"]`: *15748.652178585824*
- **Htr_1** `["<type 'numpy.float64'>"]`: *1297.9787346036153*
- **Htr_2** `["<type 'numpy.float64'>"]`: *2701.3529635310124*
- **Htr_3** `["<type 'numpy.float64'>"]`: *2590.6666958115343*
- **I_st** `["<type 'numpy.float64'>"]`: *-994.95409442637401*
- **Hve** `["<type 'numpy.float64'>"]`: *1414.5649132349504*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **I_ia** `["<type 'numpy.float64'>"]`: *1789.9699685754961*
- **I_m** `["<type 'numpy.float64'>"]`: *2724.4521715126948*
- **Cm** `["<type 'numpy.float64'>"]`: *651371895.40593004*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Losses** `["<type 'bool'>"]`: *False*
- **tHset_corr** `["<type 'float'>"]`: *2.65*
- **tCset_corr** `["<type 'float'>"]`: *-2.0*
- **IC_max** `["<type 'numpy.float64'>"]`: *-1085619.8256765502*
- **IH_max** `["<type 'numpy.float64'>"]`: *1085619.8256765502*
- **Flag** `["<type 'numpy.bool_'>"]`: *False*


### Output
- `["<type 'tuple'>"]`: (15.946568617146644, 15.202170683665049, 0, 0, 0, 15.520531773681475, 31273.645775067431)

[TOC](#table-of-contents)
---

# calc_capacity_heating_cooling_system
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **prop_HVAC** `["<class 'pandas.core.series.Series'>"]`: *type_hs        T1
type_cs        T3
type_dhw       T1
type_ctrl      T1
Tshs0_C        90
dThs0_C        20
Qhsmax_Wm2    500
Tscs0_C         7
dTcs0_C         8
Qcsmax_Wm2    500
Tsww0_C        60
dTww0_C        50
Qwwmax_Wm2    500
Name: B153767, dtype: object*


### Output
- `["<type 'tuple'>"]`: (-1085619.8256765502, 1085619.8256765502)

[TOC](#table-of-contents)
---

# calc_coeff_lea_zone
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **qv_delta_p_lea_ref** `["<type 'numpy.float64'>"]`: *28949.862018041335*


### Output
- `["<type 'numpy.float64'>"]`: 2130.2643780536373

[TOC](#table-of-contents)
---

# calc_coeff_vent_zone
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **area_vent_zone** `["<type 'int'>"]`: *0*


### Output
- `["<type 'float'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_comp_heat_gains_sensible
- number of invocations: 1
- max duration: 0.06 s
- avg duration: 0.06 s
- min duration: 0.06 s
- total duration: 0.06 s

### Input
- **Am** `["<type 'numpy.float64'>"]`: *6947.9668843299214*
- **Atot** `["<type 'numpy.float64'>"]`: *4564.8267184306733*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **I_int_sen** `["<type 'numpy.ndarray'>"]`: *array([ 3579.93993715,  3579.93993715,  3579.93993715, ...,  2684.95495286,
        2684.95495286,  2684.95495286])*
- **I_sol** `["<class 'pandas.core.series.Series'>"]`: *T1        0.00000
T2        0.00000
T3        0.00000
T4        0.00000
T5        0.00000
T6        0.00000
T7        0.00000
T8      108.84888
T9     1445.54571
T10    3498.92676
T11    4367.29482
T12    2713.76406
T13     541.96884
T14       2.54205
T15       0.00000
...
T8746    2564.85852
T8747    3179.24649
T8748    1851.58008
T8749     306.48429
T8750       0.72765
T8751       0.00000
T8752       0.00000
T8753       0.00000
T8754       0.00000
T8755       0.00000
T8756       0.00000
T8757 *


### Output
- `["<type 'tuple'>"]`: (array([ 1789.96996858,  1789.96996858,  1789.96996858, ...,  1342.47747643,
        1342.47747643,  1342.47747643]), T1      2724.452172
T2      2724.452172
T3      2724.452172
T4      2724.452172
T5      2724.452172
T6      2724.452172
T7      2724.452172
T8      6936.487402
T9     15741.840244
T10    31086.938009
T11    33730.559278
T12    20315.967881
T13     8917.632399
T14    14867.401538
T15    27083.248952
...
T8746    23224.889370
T8747    25151.459243
T8748    14957.307018
T8749     65

[TOC](#table-of-contents)
---

# calc_dhw_heating_demand
- number of invocations: 1
- max duration: 0.789 s
- avg duration: 0.789 s
- min duration: 0.789 s
- total duration: 0.789 s

### Input
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Lcww_dis** `["<type 'numpy.float64'>"]`: *72.543326121114177*
- **Lsww_dis** `["<type 'numpy.float64'>"]`: *183.34912611426176*
- **Lvww_c** `["<type 'numpy.float64'>"]`: *55.259252908257515*
- **Lvww_dis** `["<type 'numpy.float64'>"]`: *50.246706155723558*
- **T_ext** `["<type 'numpy.ndarray'>"]`: *array([ 8.8,  8.6,  8.4, ..., -0.3, -0.5, -0.7])*
- **Ta** `["<type 'numpy.ndarray'>"]`: *array([ 15.20217068,  15.13002744,  15.05677264, ...,  12.        ,
        12.        ,  12.        ])*
- **Tww_re** `["<type 'numpy.ndarray'>"]`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_sup_0** `["<type 'numpy.int64'>"]`: *60*
- **Y** `["<type 'list'>"]`: *[0.3, 0.4, 0.4]*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2201C8F0>*
- **vw** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **vww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `["<type 'tuple'>"]`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 16.32384849,  16.36585597,  16.40794422, ...,  18.70794871,
        18.74110195,  18.77423176]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 8928.0324494644647, array([ 59.96517155,  59.93025348,  59.89524561, ...,  59.82668903,
        59.78670315,  59.74664658]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]))

[TOC](#table-of-contents)
---

# calc_disls
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **tamb** `["<type 'numpy.float64'>"]`: *15.202170683665049*
- **hotw** `["<type 'numpy.float64'>"]`: *0.0*
- **Flowtap** `["<type 'numpy.float64'>"]`: *0.035999999999999997*
- **V** `["<type 'numpy.float64'>"]`: *81.45987041393002*
- **twws** `["<type 'numpy.int64'>"]`: *60*
- **Lsww_dis** `["<type 'numpy.float64'>"]`: *183.34912611426176*
- **p** `["<type 'numpy.int32'>"]`: *998*
- **cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*
- **Y** `["<type 'numpy.float64'>"]`: *0.40000000000000002*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2201CA90>*


### Output
- `["<type 'int'>"]`: 0

[TOC](#table-of-contents)
---

# calc_gl
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **radiation** `["<type 'numpy.float64'>"]`: *0.0*
- **g_gl** `["<type 'numpy.float64'>"]`: *0.67500000000000004*
- **Rf_sh** `["<type 'numpy.float64'>"]`: *0.080000000000000002*


### Output
- `["<type 'numpy.float64'>"]`: 0.67500000000000004

[TOC](#table-of-contents)
---

# calc_h
- number of invocations: 1
- max duration: 0.027 s
- avg duration: 0.027 s
- min duration: 0.027 s
- total duration: 0.027 s

### Input
- **t** `["<type 'numpy.int32'>"]`: *24*
- **w** `["<type 'numpy.float64'>"]`: *0.0090625183347139426*


### Output
- `["<type 'numpy.float64'>"]`: 47.207559164780534

[TOC](#table-of-contents)
---

# calc_h_ve_adj
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **q_m_mech** `["<type 'numpy.float64'>"]`: *1.4033382075743557*
- **q_m_nat** `["<type 'int'>"]`: *0*
- **temp_ext** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **temp_sup** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **temp_zone_set** `["<type 'int'>"]`: *21*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2201C6B0>*


### Output
- `["<type 'numpy.float64'>"]`: 1414.5649132349504

[TOC](#table-of-contents)
---

# calc_heat_gains_internal_latent
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **people** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **X_ghp** `["<type 'numpy.float64'>"]`: *80.0*
- **sys_e_cooling** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_heating** `["<type 'unicode'>"]`: *u'T1'*


### Output
- `["<type 'numpy.ndarray'>"]`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

[TOC](#table-of-contents)
---

# calc_heat_gains_internal_sensible
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **people** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qs_Wp** `["<type 'numpy.float64'>"]`: *70.0*
- **Eal_nove** `["<type 'numpy.ndarray'>"]`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Eprof** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcdata** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `["<type 'numpy.ndarray'>"]`: array([ 3579.93993715,  3579.93993715,  3579.93993715, ...,  2684.95495286,
        2684.95495286,  2684.95495286])

[TOC](#table-of-contents)
---

# calc_heat_gains_solar
- number of invocations: 1
- max duration: 0.173 s
- avg duration: 0.173 s
- min duration: 0.173 s
- total duration: 0.173 s

### Input
- **Aw** `["<type 'numpy.float64'>"]`: *452.70136417012804*
- **Awall_all** `["<type 'numpy.float64'>"]`: *1131.75341042532*
- **Sh_typ** `["<type 'unicode'>"]`: *u'T1'*
- **Solar** `["<class 'pandas.core.series.Series'>"]`: *T1         0.00
T2         0.00
T3         0.00
T4         0.00
T5         0.00
T6         0.00
T7         0.00
T8       575.92
T9      7648.39
T10    18512.84
T11    23107.38
T12    14358.54
T13     2867.56
T14       13.45
T15        0.00
...
T8746    13570.68
T8747    16821.41
T8748     9796.72
T8749     1621.61
T8750        3.85
T8751        0.00
T8752        0.00
T8753        0.00
T8754        0.00
T8755        0.00
T8756        0.00
T8757        0.00
T8758        0.00
T8759        0.00
T876*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E377B0>*


### Output
- `["<class 'pandas.core.series.Series'>"]`: T1        0.00000
T2        0.00000
T3        0.00000
T4        0.00000
T5        0.00000
T6        0.00000
T7        0.00000
T8      108.84888
T9     1445.54571
T10    3498.92676
T11    4367.29482
T12    2713.76406
T13     541.96884
T14       2.54205
T15       0.00000
...
T8746    2564.85852
T8747    3179.24649
T8748    1851.58008
T8749     306.48429
T8750       0.72765
T8751       0.00000
T8752       0.00000
T8753       0.00000
T8754       0.00000
T8755       0.00000
T8756       0.00000
T8757 

[TOC](#table-of-contents)
---

# calc_hex
- number of invocations: 1
- max duration: 0.084 s
- avg duration: 0.084 s
- min duration: 0.084 s
- total duration: 0.084 s

### Input
- **rel_humidity_ext** `["<type 'numpy.int64'>"]`: *73*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2201CBD0>*
- **qv_mech** `["<type 'numpy.float64'>"]`: *1.1694485063119631*
- **timestep** `["<type 'int'>"]`: *3217*
- **temp_ext** `["<type 'numpy.float64'>"]`: *8.1999999999999993*
- **qv_mech_dim** `["<type 'int'>"]`: *0*
- **temp_zone_prev** `["<type 'numpy.float64'>"]`: *18.759995042815788*


### Output
- `["<type 'tuple'>"]`: (8.1999999999999993, 0.0049493200522193461)

[TOC](#table-of-contents)
---

# calc_hvac
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **rhum_1** `["<type 'numpy.int64'>"]`: *73*
- **temp_1** `["<type 'numpy.float64'>"]`: *8.1999999999999993*
- **temp_zone_set** `["<type 'numpy.float64'>"]`: *18.639283464540256*
- **qv_req** `["<type 'numpy.float64'>"]`: *1.1694485063119631*
- **qe_sen** `["<type 'int'>"]`: *0*
- **temp_5_prev** `["<type 'numpy.float64'>"]`: *18.759995042815788*
- **wint** `["<type 'numpy.float64'>"]`: *0.0*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x208ECE10>*
- **timestep** `["<type 'int'>"]`: *3217*


### Output
- `["<type 'tuple'>"]`: (0, 0, 0, 0, 0, 0, 0, nan, nan, 8.1999999999999993, 8.1999999999999993, 0, 0, 18.639283464540256)

[TOC](#table-of-contents)
---

# calc_loads_electrical
- number of invocations: 1
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **Aef** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Ealf** `["<type 'numpy.ndarray'>"]`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Eauxf** `["<type 'numpy.ndarray'>"]`: *array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796])*
- **Edataf** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eprof** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `["<type 'tuple'>"]`: (array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096]), 39777.110412788796, 90.946385247798304, 2.0151953749551139, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0)

[TOC](#table-of-contents)
---

# calc_mixed_schedule
- number of invocations: 1
- max duration: 0.56 s
- avg duration: 0.56 s
- min duration: 0.56 s
- total duration: 0.56 s

### Input
- **list_uses** `["<type 'list'>"]`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `["<type 'list'>"]`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `["<class 'pandas.core.series.Series'>"]`: *GYM           0
HOSPITAL      0
HOTEL         0
INDUSTRIAL    0
MULTI_RES     0
OFFICE        1
PARKING       0
PFloor        1
RETAIL        0
Name: B153767, dtype: float64*


### Output
- `["<class 'pandas.core.frame.DataFrame'>"]`: (8760, 4)
```
               dhw           el          occ   pro
count  8760.000000  8760.000000  8760.000000  8760
mean      0.195753     0.208804     0.195753     0
std       0.254020     0.211620     0.254020     0
min       0.000000     0.060000     0.000000     0
25%       0.000000     0.080000     0.000000     0
50%       0.000000     0.100000     0.000000     0
75%       0.400000     0.240000     0.400000     0
max       0.800000     0.800000     0.800000     0

[8 rows x 4 columns]
```

[TOC](#table-of-contents)
---

# calc_pumping_systems_aux_loads
- number of invocations: 1
- max duration: 0.287 s
- avg duration: 0.287 s
- min duration: 0.287 s
- total duration: 0.287 s

### Input
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Ll** `["<type 'numpy.float64'>"]`: *32.648092418099999*
- **Lw** `["<type 'numpy.float64'>"]`: *16.008581384100001*
- **Mww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcsf** `["<type 'numpy.ndarray'>"]`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `["<type 'numpy.float64'>"]`: *-281104.46918348083*
- **Qhsf** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.        , ...,
        93991.5268617 ,  94591.45409877,  95210.96830999])*
- **Qhsf_0** `["<type 'numpy.float64'>"]`: *296485.76361481688*
- **Qww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `["<type 'numpy.float64'>"]`: *8928.0324494644647*
- **Tcs_re** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 32, 32, 32])*
- **Ths_sup** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 39, 39, 39])*
- **Vw** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Year** `["<type 'numpy.int64'>"]`: *1993*
- **fforma** `["<type 'numpy.float64'>"]`: *0.76931348014904022*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E2CE30>*
- **nf_ag** `["<type 'numpy.float64'>"]`: *4.0*
- **nfp** `["<type 'numpy.float64'>"]`: *1.0*
- **qv_req** `["<type 'numpy.ndarray'>"]`: *array([ 1.16944851,  1.16944851,  1.16944851, ...,  1.16944851,
        1.16944851,  1.16944851])*
- **sys_e_cooling** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_heating** `["<type 'unicode'>"]`: *u'T1'*


### Output
- `["<type 'tuple'>"]`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]))

[TOC](#table-of-contents)
---

# calc_qv_delta_p_ref
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **n_delta_p_ref** `["<type 'numpy.int64'>"]`: *6*
- **vol_building** `["<type 'numpy.float64'>"]`: *4824.9770030068894*


### Output
- `["<type 'numpy.float64'>"]`: 28949.862018041335

[TOC](#table-of-contents)
---

# calc_qv_req
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **ve** `["<type 'numpy.float64'>"]`: *0.0*
- **people** `["<type 'numpy.float64'>"]`: *0.0*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E414B0>*
- **hour_day** `["<type 'numpy.int32'>"]`: *0*
- **hour_year** `["<type 'numpy.int32'>"]`: *0*
- **n50** `["<type 'numpy.int64'>"]`: *6*


### Output
- `["<type 'numpy.float64'>"]`: 1.1694485063119631

[TOC](#table-of-contents)
---

# calc_tHC_corr
- number of invocations: 1
- max duration: 0.027 s
- avg duration: 0.027 s
- min duration: 0.027 s
- total duration: 0.027 s

### Input
- **SystemH** `["<type 'unicode'>"]`: *u'T1'*
- **SystemC** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_ctrl** `["<type 'unicode'>"]`: *u'T1'*


### Output
- `["<type 'tuple'>"]`: (2.65, -2.0)

[TOC](#table-of-contents)
---

# calc_temperatures_emission_systems
- number of invocations: 1
- max duration: 0.649 s
- avg duration: 0.649 s
- min duration: 0.649 s
- total duration: 0.649 s

### Input
- **Qcsf** `["<type 'numpy.ndarray'>"]`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `["<type 'numpy.float64'>"]`: *-281104.46918348083*
- **Qhsf** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.        , ...,
        93991.5268617 ,  94591.45409877,  95210.96830999])*
- **Qhsf_0** `["<type 'numpy.float64'>"]`: *296485.76361481688*
- **Ta** `["<type 'numpy.ndarray'>"]`: *array([ 15.20217068,  15.13002744,  15.05677264, ...,  12.        ,
        12.        ,  12.        ])*
- **Ta_re_cs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_re_hs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_cs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_hs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Tcs_re_0** `["<type 'numpy.int64'>"]`: *15*
- **Tcs_sup_0** `["<type 'numpy.int64'>"]`: *7*
- **Ths_re_0** `["<type 'numpy.int64'>"]`: *70*
- **Ths_sup_0** `["<type 'numpy.int64'>"]`: *90*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x218BE9B0>*
- **ma_sup_cs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **ma_sup_hs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **sys_e_cooling** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_heating** `["<type 'unicode'>"]`: *u'T1'*
- **ta_hs_set** `["<type 'numpy.ndarray'>"]`: *array([ 12.,  12.,  12., ...,  12.,  12.,  12.])*
- **w_re** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **w_sup** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `["<type 'tuple'>"]`: (array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]), array([ 0,  0,  0, ..., 32, 32, 32]), array([ 0,  0,  0, ..., 39, 39, 39]), array([0, 0, 0, ..., 0, 0, 0]), array([ 0,  0,  0, ..., 14, 14, 14]))

[TOC](#table-of-contents)
---

# calc_thermal_load_hvac_timestep
- number of invocations: 1
- max duration: 0.234 s
- avg duration: 0.234 s
- min duration: 0.234 s
- total duration: 0.234 s

### Input
- **t** `["<type 'int'>"]`: *3217*
- **thermal_loads_input** `["<class 'cea.thermal_loads.ThermalLoadsInput'>"]`: *<cea.thermal_loads.ThermalLoadsInput object at 0x20E37FD0>*
- **weather_data** `["<class 'pandas.core.frame.DataFrame'>"]`: *(8760, 3)*
- **state_prev** `["<type 'dict'>"]`: *{'temp_air_prev': 18.759995042815788, 'temp_m_prev': 20.062727215496661}*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E37FD0>*

#### weather_data:
```
         drybulb_C  relhum_percent   windspd_ms
count  8760.000000     8760.000000  8760.000000
mean     10.840890       71.675799     1.008390
std       7.885023       16.270003     1.047616
min      -8.900000       25.000000     0.000000
25%       4.800000       60.000000     0.300000
50%      10.700000       74.000000     0.700000
75%      16.900000       84.000000     1.400000
max      32.500000      100.000000     9.400000

[8 rows x 3 columns]
```

### Output
- `["<type 'tuple'>"]`: (19.966467702548133, 18.639283464540256, 0, 0, 0, 19.227457669603439, 28533.095180549077, 0, 0, 0, 0, 0, 1.4033382075743557, 0, 0, 0, 0, 0, 0, nan, nan, 8.1999999999999993, 8.1999999999999993, 0, 0)

[TOC](#table-of-contents)
---

# calc_thermal_load_mechanical_and_natural_ventilation_timestep
- number of invocations: 1
- max duration: 0.349 s
- avg duration: 0.349 s
- min duration: 0.349 s
- total duration: 0.349 s

### Input
- **t** `["<type 'int'>"]`: *0*
- **thermal_loads_input** `["<class 'cea.thermal_loads.ThermalLoadsInput'>"]`: *<cea.thermal_loads.ThermalLoadsInput object at 0x20E3DDB0>*
- **weather_data** `["<class 'pandas.core.frame.DataFrame'>"]`: *(8760, 3)*
- **state_prev** `["<type 'dict'>"]`: *{'temp_air_prev': 21, 'temp_m_prev': 16}*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20E1E110>*

#### weather_data:
```
         drybulb_C  relhum_percent   windspd_ms
count  8760.000000     8760.000000  8760.000000
mean     10.840890       71.675799     1.008390
std       7.885023       16.270003     1.047616
min      -8.900000       25.000000     0.000000
25%       4.800000       60.000000     0.300000
50%      10.700000       74.000000     0.700000
75%      16.900000       84.000000     1.400000
max      32.500000      100.000000     9.400000

[8 rows x 3 columns]
```

### Output
- `["<type 'tuple'>"]`: (15.946568617146644, 15.202170683665049, 0, 0, 0, 15.520531773681475, 31273.645775067431, 1.4033382075743557, 0, 0, 0, 0)

[TOC](#table-of-contents)
---

# calc_thermal_loads_new_ventilation
- number of invocations: 1
- max duration: 8.44 s
- avg duration: 8.44 s
- min duration: 8.44 s
- total duration: 8.44 s

### Input
- **Name** `["<type 'str'>"]`: *'B153767'*
- **building_properties** `["<class 'cea.demand.BuildingProperties'>"]`: *<cea.demand.BuildingProperties object at 0x20102A10>*
- **weather_data** `["<class 'pandas.core.frame.DataFrame'>"]`: *(8760, 3)*
- **usage_schedules** `["<type 'dict'>"]`: *{'list_uses': [u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL'], 'schedules': [([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4,*
- **date** `["<class 'pandas.tseries.index.DatetimeIndex'>"]`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20372550>*
- **locationFinal** `["<type 'str'>"]`: *'C:\\reference-case\\baseline\\outputs\\data\\demand'*
- **path_temporary_folder** `["<type 'str'>"]`: *'c:\\users\\darthoma\\appdata\\local\\temp'*

#### weather_data:
```
         drybulb_C  relhum_percent   windspd_ms
count  8760.000000     8760.000000  8760.000000
mean     10.840890       71.675799     1.008390
std       7.885023       16.270003     1.047616
min      -8.900000       25.000000     0.000000
25%       4.800000       60.000000     0.300000
50%      10.700000       74.000000     0.700000
75%      16.900000       84.000000     1.400000
max      32.500000      100.000000     9.400000

[8 rows x 3 columns]
```

### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

# calc_w
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **t** `["<type 'numpy.float64'>"]`: *8.1999999999999993*
- **RH** `["<type 'numpy.int64'>"]`: *73*


### Output
- `["<type 'numpy.float64'>"]`: 0.0049493200522193461

[TOC](#table-of-contents)
---

# calc_w3_cooling_case
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **t5** `["<type 'numpy.int32'>"]`: *24*
- **w2** `["<type 'numpy.float64'>"]`: *0.0090625183347139426*
- **t3** `["<type 'int'>"]`: *16*
- **w5** `["<type 'numpy.float64'>"]`: *0.0094873786628507113*


### Output
- `["<type 'numpy.float64'>"]`: 0.0090625183347139426

[TOC](#table-of-contents)
---

# calc_w3_heating_case
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **t5** `["<type 'numpy.float64'>"]`: *20.0*
- **w2** `["<type 'numpy.float64'>"]`: *0.0041699403233700994*
- **w5** `["<type 'numpy.float64'>"]`: *0.0045258958486444414*
- **t3** `["<type 'int'>"]`: *36*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x207D4CB0>*


### Output
- `["<type 'numpy.float64'>"]`: 0.0041699403233700994

[TOC](#table-of-contents)
---

# calculate_pipe_transmittance_values
- number of invocations: 1
- max duration: 0.027 s
- avg duration: 0.027 s
- min duration: 0.027 s
- total duration: 0.027 s

### Input
- **year** `["<type 'numpy.int64'>"]`: *1993*
- **Retrofit** `["<type 'numpy.int64'>"]`: *0*


### Output
- `["<type 'list'>"]`: [0.3, 0.4, 0.4]

[TOC](#table-of-contents)
---

# create_windows
- number of invocations: 1
- max duration: 0.978 s
- avg duration: 0.978 s
- min duration: 0.978 s
- total duration: 0.978 s

### Input
- **df_prop_surfaces** `["<class 'pandas.core.frame.DataFrame'>"]`: *(2140, 6)*
- **gdf_building_architecture** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 6)*

#### df_prop_surfaces:
```
        Freeheight  FactorShade    height_ag   Shape_Leng    Awall_all
count  2140.000000  2140.000000  2140.000000  2140.000000  2140.000000
mean     12.264953     0.923832    13.661215    12.078187   157.379374
std       7.315848     0.265329     6.715044    14.908206   259.960388
min       0.000000     0.000000     3.000000     0.000990     0.000000
25%       6.000000     1.000000     9.000000     1.234268     8.513622
50%      15.000000     1.000000    15.000000     9.025269    55.692791
75%      18.000000     1.000000    18.000000    15.838894   203.116772
max      54.000000     1.000000    54.000000   122.214988  2567.501283

[8 rows x 5 columns]
```

### Output
- `["<class 'pandas.core.frame.DataFrame'>"]`: (8749, 6)
```
       angle_window  area_window  height_window_above_ground  \
count          8749  8749.000000                 8749.000000   
mean             90     5.821898                    8.583210   
std               0     7.268579                    6.735171   
min              90     0.000201                    1.500000   
25%              90     0.411601                    4.500000   
50%              90     4.154925                    7.500000   
75%              90     8.068005                   13.500000   
max              90    73.328993                   52.500000   

       height_window_in_zone  orientation_window  
count            8749.000000         8749.000000  
mean                8.583210          133.935307  
std                 6.735171          100.268277  
min                 1.500000            0.000000  
25%                 4.500000            0.000000  
50%                 7.500000           90.000000  
75%                13.500000          180.000000  
max                52.500000          270.000000  

[8 rows x 5 columns]
```

[TOC](#table-of-contents)
---

# demand_calculation
- number of invocations: 1
- max duration: 1077.785 s
- avg duration: 1077.785 s
- min duration: 1077.785 s
- total duration: 1077.785 s

### Input
- **locator** `["<class 'cea.inputlocator.InputLocator'>"]`: *<cea.inputlocator.InputLocator object at 0x2035FF30>*
- **weather_path** `["<type 'str'>"]`: *'C:\\Users\\darthoma\\Documents\\GitHub\\CEAforArcGIS\\cea\\db\\CH\\Weather\\Zurich.epw'*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2035FF30>*


### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

# get_building_geometry_ventilation
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **gdf_building_geometry** `["<class 'pandas.core.series.Series'>"]`: *Blength       32.648092
Bwidth        16.008581
floors_ag      4.000000
floors_bg      2.000000
height_ag     12.000000
height_bg      6.000000
footprint    402.081417
perimeter    103.083898
Name: B153767, dtype: float64*


### Output
- `["<type 'tuple'>"]`: (1237.0067791693345, 402.0814169172408, 12.0, 0)

[TOC](#table-of-contents)
---

# get_internal_comfort
- number of invocations: 1
- max duration: 0.037 s
- avg duration: 0.037 s
- min duration: 0.037 s
- total duration: 0.037 s

### Input
- **people** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **prop_comfort** `["<class 'pandas.core.series.Series'>"]`: *Tcs_set_C     24
Tcs_setb_C    28
Ths_set_C     22
Ths_setb_C    12
Ve_lps        10
Name: B153767, dtype: float64*
- **limit_inf_season** `["<type 'int'>"]`: *3217*
- **limit_sup_season** `["<type 'int'>"]`: *6192*
- **weekday** `["<type 'numpy.ndarray'>"]`: *array([4, 4, 4, ..., 4, 4, 4])*


### Output
- `["<type 'tuple'>"]`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 12.,  12.,  12., ...,  12.,  12.,  12.]), array([50, 50, 50, ..., 50, 50, 50]))

[TOC](#table-of-contents)
---

# get_internal_loads
- number of invocations: 1
- max duration: 0.037 s
- avg duration: 0.037 s
- min duration: 0.037 s
- total duration: 0.037 s

### Input
- **mixed_schedule** `["<class 'pandas.core.frame.DataFrame'>"]`: *(8760, 4)*
- **prop_internal_loads** `["<class 'pandas.core.series.Series'>"]`: *Ea_Wm2       7.0
Ed_Wm2       0.0
El_Wm2      15.9
Epro_Wm2     0.0
Ere_Wm2      0.0
Qs_Wp       70.0
Vw_lpd      20.0
Vww_lpd     10.0
X_ghp       80.0
Name: B153767, dtype: float64*
- **prop_architecture** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*

#### mixed_schedule:
```
               dhw           el          occ   pro
count  8760.000000  8760.000000  8760.000000  8760
mean      0.195753     0.208804     0.195753     0
std       0.254020     0.211620     0.254020     0
min       0.000000     0.060000     0.000000     0
25%       0.000000     0.080000     0.000000     0
50%       0.000000     0.100000     0.000000     0
75%       0.400000     0.240000     0.400000     0
max       0.800000     0.800000     0.800000     0

[8 rows x 4 columns]
```

### Output
- `["<type 'tuple'>"]`: (array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]))

[TOC](#table-of-contents)
---

# get_occupancy
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **mixed_schedule** `["<class 'pandas.core.frame.DataFrame'>"]`: *(8760, 4)*
- **prop_architecture** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*

#### mixed_schedule:
```
               dhw           el          occ   pro
count  8760.000000  8760.000000  8760.000000  8760
mean      0.195753     0.208804     0.195753     0
std       0.254020     0.211620     0.254020     0
min       0.000000     0.060000     0.000000     0
25%       0.000000     0.080000     0.000000     0
50%       0.000000     0.100000     0.000000     0
75%       0.400000     0.240000     0.400000     0
max       0.800000     0.800000     0.800000     0

[8 rows x 4 columns]
```

### Output
- `["<type 'numpy.ndarray'>"]`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

[TOC](#table-of-contents)
---

# get_prop_RC_model
- number of invocations: 1
- max duration: 0.235 s
- avg duration: 0.235 s
- min duration: 0.235 s
- total duration: 0.235 s

### Input
- **uses** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 9)*
- **architecture** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 6)*
- **thermal** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 7)*
- **geometry** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(274, 8)*
- **HVAC** `["<class 'pandas.core.frame.DataFrame'>"]`: *(1482, 13)*
- **rf** `["<class 'pandas.core.frame.DataFrame'>"]`: *(2140, 5)*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x207D06B0>*

#### HVAC:
```
           Tshs0_C      dThs0_C   Qhsmax_Wm2      Tscs0_C      dTcs0_C  \
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000   
mean     84.284750    18.788799   470.985155     2.333333     2.666667   
std      20.977011     4.648400   115.413596     3.300946     3.772509   
min       0.000000     0.000000     0.000000     0.000000     0.000000   
25%      90.000000    20.000000   500.000000     0.000000     0.000000   
50%      90.000000    20.000000   500.000000     0.000000     0.000000   
75%      90.000000    20.000000   500.000000     7.000000     8.000000   
max      90.000000    20.000000   500.000000     7.000000     8.000000   

        Qcsmax_Wm2      Tsww0_C      dTww0_C   Qwwmax_Wm2  
count  1482.000000  1482.000000  1482.000000  1482.000000  
mean    166.666667    56.801619    47.334683   473.346829  
std     235.781822    13.483170    11.235975   112.359747  
min       0.000000     0.000000     0.000000     0.000000  
25%       0.000000    60.000000    50.000000   500.000000  
50%       0.000000    60.000000    50.000000   500.000000  
75%     500.000000    60.000000    50.000000   500.000000  
max     500.000000    60.000000    50.000000   500.000000  

[8 rows x 9 columns]
```
#### rf:
```
        Freeheight  FactorShade    height_ag   Shape_Leng
count  2140.000000  2140.000000  2140.000000  2140.000000
mean     12.264953     0.923832    13.661215    12.078187
std       7.315848     0.265329     6.715044    14.908206
min       0.000000     0.000000     3.000000     0.000990
25%       6.000000     1.000000     9.000000     1.234268
50%      15.000000     1.000000    15.000000     9.025269
75%      18.000000     1.000000    18.000000    15.838894
max      54.000000     1.000000    54.000000   122.214988

[8 rows x 4 columns]
```

### Output
- `["<class 'pandas.core.frame.DataFrame'>"]`: (274, 15)
```
          Awall_all           Atot           Aw             Am            Aef  \
count    274.000000     274.000000   274.000000     274.000000     274.000000   
mean    1229.167375    6788.584879   339.960673   10254.921203    3990.490275   
std     1614.734960   15317.136194   462.836487   27233.091987   10670.565237   
min       26.326689      35.854865     2.632669       0.000000       4.287679   
25%      336.506101    1235.762736    85.964162    1182.449634     449.853115   
50%      713.470323    2348.721099   171.734138    2588.168154    1014.216986   
75%     1362.915079    5790.761600   405.955475    7334.245516    2933.698206   
max    12466.623953  181691.565146  3317.350336  329540.768090  131816.307236   

                  Af            Cm         Htr_is        Htr_em  \
count     274.000000  2.740000e+02     274.000000    274.000000   
mean     3985.452314  7.137771e+08   23420.617832   1232.090555   
std     10672.420367  1.893378e+09   52844.119871   2574.916964   
min         0.000000  0.000000e+00     123.699285     -0.000000   
25%       449.853115  8.010539e+07    4263.381439    160.312351   
50%      1014.216986  1.719449e+08    8103.087793    281.381072   
75%      2933.698206  5.755465e+08   19978.127521    835.058050   
max    131816.307236  2.174969e+10  626835.899755  20330.043440   

               Htr_ms        Htr_op           Hg            HD        Htr_w  \
count      274.000000    274.000000   274.000000    274.000000   274.000000   
mean     93319.782948   1208.714179   529.902047    678.812132   658.011789   
std     247821.137082   2512.933417  1127.811141   1602.087311  1099.072213   
min          0.000000     11.508697     2.075740      9.432957     5.282950   
25%      10760.291670    162.342105    54.265664     97.633223   122.401716   
50%      23552.330203    280.892472    94.493504    172.924079   261.920127   
75%      66741.634197    816.542270   366.717077    411.857669   593.145962   
max    2998820.989622  19924.663269  9154.270129  13660.091136  9038.302366   

              GFA_m2  
count     274.000000  
mean     4460.977496  
std     11850.221764  
min         4.764088  
25%       525.533171  
50%      1174.672642  
75%      3259.664674  
max    146462.563596  

[8 rows x 15 columns]
```

[TOC](#table-of-contents)
---

# get_properties_building_envelope
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **prop_RC_model** `["<class 'pandas.core.series.Series'>"]`: *Awall_all    1.131753e+03
Atot         4.564827e+03
Aw           4.527014e+02
Am           6.947967e+03
Aef          2.171240e+03
Af           2.171240e+03
Cm           6.513719e+08
Htr_is       1.574865e+04
Htr_em       5.829963e+02
Htr_ms       6.322650e+04
Htr_op       5.776698e+02
Hg           2.857637e+02
HD           2.919060e+02
Htr_w        1.403374e+03
GFA_m2       2.412489e+03
Name: B153767, dtype: float64*
- **prop_age** `["<class 'pandas.core.series.Series'>"]`: *HVAC             0
basement         0
built         1993
envelope         0
partitions       0
roof             0
windows          0
Name: B153767, dtype: int64*
- **prop_architecture** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **prop_geometry** `["<class 'pandas.core.series.Series'>"]`: *Blength       32.648092
Bwidth        16.008581
floors_ag      4.000000
floors_bg      2.000000
height_ag     12.000000
height_bg      6.000000
footprint    402.081417
perimeter    103.083898
Name: B153767, dtype: float64*
- **prop_occupancy** `["<class 'pandas.core.series.Series'>"]`: *GYM           0
HOSPITAL      0
HOTEL         0
INDUSTRIAL    0
MULTI_RES     0
OFFICE        1
PARKING       0
PFloor        1
RETAIL        0
Name: B153767, dtype: float64*


### Output
- `["<type 'tuple'>"]`: (6947.9668843299214, 4564.8267184306733, 452.70136417012804, 1131.75341042532, 651371895.40593004, 32.648092418099999, 16.008581384100001, 0, u'T1', 1993, 402.0814169172408, 4.0, 2.0, 1.0)

[TOC](#table-of-contents)
---

# get_properties_building_systems
- number of invocations: 1
- max duration: 0.139 s
- avg duration: 0.139 s
- min duration: 0.139 s
- total duration: 0.139 s

### Input
- **Ll** `["<type 'numpy.float64'>"]`: *32.648092418099999*
- **Lw** `["<type 'numpy.float64'>"]`: *16.008581384100001*
- **Retrofit** `["<type 'numpy.int64'>"]`: *0*
- **Year** `["<type 'numpy.int64'>"]`: *1993*
- **footprint** `["<type 'numpy.float64'>"]`: *402.0814169172408*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20C2D2D0>*
- **nf_ag** `["<type 'numpy.float64'>"]`: *4.0*
- **nfp** `["<type 'numpy.float64'>"]`: *1.0*
- **nf_bg** `["<type 'numpy.float64'>"]`: *2.0*
- **prop_HVAC** `["<class 'pandas.core.series.Series'>"]`: *type_hs        T1
type_cs        T3
type_dhw       T1
type_ctrl      T1
Tshs0_C        90
dThs0_C        20
Qhsmax_Wm2    500
Tscs0_C         7
dTcs0_C         8
Qcsmax_Wm2    500
Tsww0_C        60
dTww0_C        50
Qwwmax_Wm2    500
Name: B153767, dtype: object*


### Output
- `["<type 'tuple'>"]`: (72.543326121114177, 183.34912611426176, 67.916762127496582, 55.259252908257515, 50.246706155723558, 15, 7, 70, 90, 10, 60, [0.3, 0.4, 0.4], 0.76931348014904022)

[TOC](#table-of-contents)
---

# get_properties_natural_ventilation
- number of invocations: 1
- max duration: 0.402 s
- avg duration: 0.402 s
- min duration: 0.402 s
- total duration: 0.402 s

### Input
- **gdf_geometry_building** `["<class 'pandas.core.series.Series'>"]`: *Blength       32.648092
Bwidth        16.008581
floors_ag      4.000000
floors_bg      2.000000
height_ag     12.000000
height_bg      6.000000
footprint    402.081417
perimeter    103.083898
Name: B153767, dtype: float64*
- **gdf_architecture_building** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20C30A50>*


### Output
- `["<type 'dict'>"]`: {'coeff_wind_pressure_path_vent': array([ 0.05, -0.05,  0.05, -0.05]), 'coeff_vent_path': array([ 0.,  0.,  0.,  0.]), 'height_vent_path': array([ 3.,  3.,  9.,  9.]), 'coeff_lea_path': array([ 401.92338084,  401.92338084,  401.92338084,  401.92338084,
        522.57085469]), 'factor_cros': 0, 'height_lea_path': array([  3.,   3.,   9.,   9.,  12.]), 'coeff_wind_pressure_path_lea': array([ 0.05, -0.05,  0.05, -0.05,  0.  ])}

[TOC](#table-of-contents)
---

# get_temperatures
- number of invocations: 1
- max duration: 0.091 s
- avg duration: 0.091 s
- min duration: 0.091 s
- total duration: 0.091 s

### Input
- **locator** `["<class 'cea.inputlocator.InputLocator'>"]`: *<cea.inputlocator.InputLocator object at 0x20C2D070>*
- **prop_HVAC** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 5)*


### Output
- `["<class 'pandas.core.frame.DataFrame'>"]`: (1482, 14)
```
           Tshs0_C      dThs0_C   Qhsmax_Wm2      Tscs0_C      dTcs0_C  \
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000   
mean     84.284750    18.788799   470.985155     2.333333     2.666667   
std      20.977011     4.648400   115.413596     3.300946     3.772509   
min       0.000000     0.000000     0.000000     0.000000     0.000000   
25%      90.000000    20.000000   500.000000     0.000000     0.000000   
50%      90.000000    20.000000   500.000000     0.000000     0.000000   
75%      90.000000    20.000000   500.000000     7.000000     8.000000   
max      90.000000    20.000000   500.000000     7.000000     8.000000   

        Qcsmax_Wm2      Tsww0_C      dTww0_C   Qwwmax_Wm2  
count  1482.000000  1482.000000  1482.000000  1482.000000  
mean    166.666667    56.801619    47.334683   473.346829  
std     235.781822    13.483170    11.235975   112.359747  
min       0.000000     0.000000     0.000000     0.000000  
25%       0.000000    60.000000    50.000000   500.000000  
50%       0.000000    60.000000    50.000000   500.000000  
75%     500.000000    60.000000    50.000000   500.000000  
max     500.000000    60.000000    50.000000   500.000000  

[8 rows x 9 columns]
```

[TOC](#table-of-contents)
---

# lookup_coeff_wind_pressure
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **height_path** `["<type 'numpy.ndarray'>"]`: *array([  3.,   3.,   9.,   9.,  12.])*
- **class_shielding** `["<type 'int'>"]`: *2*
- **orientation_path** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  1.,  0.,  1.,  2.])*
- **slope_roof** `["<type 'int'>"]`: *0*
- **factor_cros** `["<type 'numpy.int64'>"]`: *0*


### Output
- `["<type 'numpy.ndarray'>"]`: array([ 0.05, -0.05,  0.05, -0.05,  0.  ])

[TOC](#table-of-contents)
---

# read_building_properties
- number of invocations: 1
- max duration: 4.346 s
- avg duration: 4.346 s
- min duration: 4.346 s
- total duration: 4.346 s

### Input
- **locator** `["<class 'cea.inputlocator.InputLocator'>"]`: *<cea.inputlocator.InputLocator object at 0x207A8330>*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x207A8330>*


### Output
- `["<class 'cea.demand.BuildingProperties'>"]`: <cea.demand.BuildingProperties object at 0x2035D930>

[TOC](#table-of-contents)
---

# results_to_csv
- number of invocations: 1
- max duration: 0.241 s
- avg duration: 0.241 s
- min duration: 0.241 s
- total duration: 0.241 s

### Input
- **GFA_m2** `["<type 'numpy.float64'>"]`: *2412.4885015034447*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Ealf** `["<type 'numpy.ndarray'>"]`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Ealf_0** `["<type 'numpy.float64'>"]`: *39777.110412788796*
- **Ealf_tot** `["<type 'numpy.float64'>"]`: *90.946385247798304*
- **Eauxf** `["<type 'numpy.ndarray'>"]`: *array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796])*
- **Eauxf_tot** `["<type 'numpy.float64'>"]`: *2.0151953749551139*
- **Edata** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Edata_tot** `["<type 'numpy.float64'>"]`: *0.0*
- **Epro** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Epro_tot** `["<type 'numpy.float64'>"]`: *0.0*
- **Name** `["<type 'str'>"]`: *'B153767'*
- **Occupancy** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Occupants** `["<type 'numpy.float64'>"]`: *124.0*
- **Qcdata** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcs** `["<type 'numpy.ndarray'>"]`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf** `["<type 'numpy.ndarray'>"]`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `["<type 'numpy.float64'>"]`: *-281104.46918348083*
- **Qhs** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.        , ...,
        57273.71555088,  57869.64278795,  58484.15699917])*
- **Qhsf** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.        , ...,
        93991.5268617 ,  94591.45409877,  95210.96830999])*
- **Qhsf_0** `["<type 'numpy.float64'>"]`: *296485.76361481688*
- **Qww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qww_ls_st** `["<type 'numpy.ndarray'>"]`: *array([ 16.32384849,  16.36585597,  16.40794422, ...,  18.70794871,
        18.74110195,  18.77423176])*
- **Qwwf** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `["<type 'numpy.float64'>"]`: *8928.0324494644647*
- **Tcs_re** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_re_0** `["<type 'numpy.int64'>"]`: *15*
- **Tcs_sup** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup_0** `["<type 'numpy.int64'>"]`: *7*
- **Ths_re** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 32, 32, 32])*
- **Ths_re_0** `["<type 'numpy.int64'>"]`: *70*
- **Ths_sup** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 39, 39, 39])*
- **Ths_sup_0** `["<type 'numpy.int64'>"]`: *90*
- **Tww_re** `["<type 'numpy.ndarray'>"]`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_st** `["<type 'numpy.ndarray'>"]`: *array([ 59.96517155,  59.93025348,  59.89524561, ...,  59.82668903,
        59.78670315,  59.74664658])*
- **Tww_sup_0** `["<type 'numpy.int64'>"]`: *60*
- **Waterconsumption** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **locationFinal** `["<type 'str'>"]`: *'C:\\reference-case\\baseline\\outputs\\data\\demand'*
- **mcpcs** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcphs** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 14, 14, 14])*
- **mcpww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **path_temporary_folder** `["<type 'str'>"]`: *'c:\\users\\darthoma\\appdata\\local\\temp'*
- **sys_e_cooling** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_heating** `["<type 'unicode'>"]`: *u'T1'*
- **waterpeak** `["<type 'numpy.float64'>"]`: *0.33673440168628083*
- **date** `["<class 'pandas.tseries.index.DatetimeIndex'>"]`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*


### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

# test_demand
- number of invocations: 1
- max duration: 1077.891 s
- avg duration: 1077.891 s
- min duration: 1077.891 s
- total duration: 1077.891 s

### Input


### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

