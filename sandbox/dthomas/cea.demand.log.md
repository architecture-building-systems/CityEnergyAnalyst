# Table of contents
- [AmFunction](#amfunction)

- [CalcThermalLoads](#calcthermalloads)

- [Calc_Im_tot](#calc-im-tot)

- [Calc_Rf_sh](#calc-rf-sh)

- [Calc_Tm](#calc-tm)

- [Calc_form](#calc-form)

- [CmFunction](#cmfunction)

- [calc_Ccoil2](#calc-ccoil2)

- [calc_Eaux_cs_dis](#calc-eaux-cs-dis)

- [calc_Eaux_fw](#calc-eaux-fw)

- [calc_Eaux_hs_dis](#calc-eaux-hs-dis)

- [calc_Eaux_ve](#calc-eaux-ve)

- [calc_Eaux_ww](#calc-eaux-ww)

- [calc_HVAC](#calc-hvac)

- [calc_Hcoil2](#calc-hcoil2)

- [calc_Htr](#calc-htr)

- [calc_Qdis_ls](#calc-qdis-ls)

- [calc_Qem_ls](#calc-qem-ls)

- [calc_Qww_ls_nr](#calc-qww-ls-nr)

- [calc_Qww_ls_r](#calc-qww-ls-r)

- [calc_RAD](#calc-rad)

- [calc_TABSH](#calc-tabsh)

- [calc_TL](#calc-tl)

- [calc_capacity_heating_cooling_system](#calc-capacity-heating-cooling-system)

- [calc_comp_heat_gains_sensible](#calc-comp-heat-gains-sensible)

- [calc_dhw_heating_demand](#calc-dhw-heating-demand)

- [calc_disls](#calc-disls)

- [calc_gl](#calc-gl)

- [calc_h](#calc-h)

- [calc_heat_gains_internal_latent](#calc-heat-gains-internal-latent)

- [calc_heat_gains_internal_sensible](#calc-heat-gains-internal-sensible)

- [calc_heat_gains_solar](#calc-heat-gains-solar)

- [calc_loads_electrical](#calc-loads-electrical)

- [calc_mixed_schedule](#calc-mixed-schedule)

- [calc_pumping_systems_aux_loads](#calc-pumping-systems-aux-loads)

- [calc_qv_req](#calc-qv-req)

- [calc_temperatures_emission_systems](#calc-temperatures-emission-systems)

- [calc_w](#calc-w)

- [calc_w3_cooling_case](#calc-w3-cooling-case)

- [calc_w3_heating_case](#calc-w3-heating-case)

- [calculate_pipe_transmittance_values](#calculate-pipe-transmittance-values)

- [demand_calculation](#demand-calculation)

- [get_internal_comfort](#get-internal-comfort)

- [get_internal_loads](#get-internal-loads)

- [get_occupancy](#get-occupancy)

- [get_prop_RC_model](#get-prop-rc-model)

- [get_properties_building_envelope](#get-properties-building-envelope)

- [get_properties_building_systems](#get-properties-building-systems)

- [get_temperatures](#get-temperatures)

- [results_to_csv](#results-to-csv)

- [test_demand](#test-demand)


# AmFunction
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **x** `["<type 'unicode'>"]`: *u'T3'*


### Output
- `["<type 'float'>"]`: 3.2

[TOC](#table-of-contents)
---

# CalcThermalLoads
- number of invocations: 1
- max duration: 7.836 s
- avg duration: 7.836 s
- min duration: 7.836 s
- total duration: 7.836 s

### Input
- **Name** `["<type 'str'>"]`: *'B153767'*
- **prop_occupancy** `["<class 'pandas.core.series.Series'>"]`: *GYM           0
HOSPITAL      0
HOTEL         0
IN*
- **prop_architecture** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
type_shade     T1
win_wall      *
- **prop_geometry** `["<class 'pandas.core.series.Series'>"]`: *Blength       32.648092
Bwidth        16.008581
fl*
- **prop_HVAC** `["<class 'pandas.core.series.Series'>"]`: *type_hs        T1
type_cs        T3
type_dhw      *
- **prop_RC_model** `["<class 'pandas.core.series.Series'>"]`: *Awall_all    1.131753e+03
Atot         4.564827e+0*
- **prop_comfort** `["<class 'pandas.core.series.Series'>"]`: *Tcs_set_C     24
Tcs_setb_C    28
Ths_set_C     22*
- **prop_internal_loads** `["<class 'pandas.core.series.Series'>"]`: *Ea_Wm2       7.0
Ed_Wm2       0.0
El_Wm2      15.9*
- **prop_age** `["<class 'pandas.core.series.Series'>"]`: *HVAC             0
basement         0
built       *
- **Solar** `["<class 'pandas.core.series.Series'>"]`: *T1     0.000000e+00
T2     0.000000e+00
T3     0.0*
- **locationFinal** `["<type 'str'>"]`: *'C:\\reference-case\\baseline\\2-results\\2-demand*
- **schedules** `["<type 'list'>"]`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **T_ext** `["<type 'numpy.ndarray'>"]`: *array([ 8.8,  8.6,  8.4, ..., -0.3, -0.5, -0.7])*
- **RH_ext** `["<type 'numpy.ndarray'>"]`: *array([65, 66, 64, ..., 88, 89, 86], dtype=int64)*
- **path_temporary_folder** `["<type 'str'>"]`: *'c:\\users\\darthoma\\appdata\\local\\temp'*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x1E3926F*
- **date** `["<class 'pandas.tseries.index.DatetimeIndex'>"]`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016*
- **list_uses** `["<type 'list'>"]`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'M*


### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

# Calc_Im_tot
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **I_m** `["<type 'numpy.float64'>"]`: *2724.4521715126948*
- **Htr_em** `["<type 'numpy.float64'>"]`: *582.9963349687813*
- **te_t** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **Htr_3** `["<type 'numpy.float64'>"]`: *1774.7161808217863*
- **I_st** `["<type 'numpy.float64'>"]`: *-994.95409442637401*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **Htr_1** `["<type 'numpy.float64'>"]`: *422.59542894663815*
- **I_ia** `["<type 'numpy.float64'>"]`: *1789.9699685754961*
- **IHC_nd** `["<type 'int'>"]`: *0*
- **Hve** `["<type 'numpy.float64'>"]`: *434.24793027062015*
- **Htr_2** `["<type 'numpy.float64'>"]`: *1825.969657874035*


### Output
- `["<type 'numpy.float64'>"]`: 24198.339335931298

[TOC](#table-of-contents)
---

# Calc_Rf_sh
- number of invocations: 1
- max duration: 0.043 s
- avg duration: 0.043 s
- min duration: 0.043 s
- total duration: 0.043 s

### Input
- **ShadingType** `["<type 'unicode'>"]`: *u'T1'*


### Output
- `["<type 'numpy.float64'>"]`: 0.080000000000000002

[TOC](#table-of-contents)
---

# Calc_Tm
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **Htr_3** `["<type 'numpy.float64'>"]`: *1774.7161808217863*
- **Htr_1** `["<type 'numpy.float64'>"]`: *422.59542894663815*
- **tm_t0** `["<type 'int'>"]`: *16*
- **Cm** `["<type 'numpy.float64'>"]`: *651371895.40593004*
- **Htr_em** `["<type 'numpy.float64'>"]`: *582.9963349687813*
- **Im_tot** `["<type 'numpy.float64'>"]`: *24198.339335931298*
- **Htr_ms** `["<type 'numpy.float64'>"]`: *63226.498647402281*
- **I_st** `["<type 'numpy.float64'>"]`: *-994.95409442637401*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **te_t** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **I_ia** `["<type 'numpy.float64'>"]`: *1789.9699685754961*
- **IHC_nd** `["<type 'int'>"]`: *0*
- **Hve** `["<type 'numpy.float64'>"]`: *434.24793027062015*
- **Htr_is** `["<type 'numpy.float64'>"]`: *15748.652178585824*


### Output
- `["<type 'tuple'>"]`: (15.96286680328714, 15.773293778561444, 15.6967828

[TOC](#table-of-contents)
---

# Calc_form
- number of invocations: 1
- max duration: 0.041 s
- avg duration: 0.041 s
- min duration: 0.041 s
- total duration: 0.041 s

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
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **x** `["<type 'unicode'>"]`: *u'T3'*


### Output
- `["<type 'int'>"]`: 300000

[TOC](#table-of-contents)
---

# calc_Ccoil2
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **Qc** `["<type 'numpy.float64'>"]`: *-0*
- **tasup** `["<type 'numpy.float64'>"]`: *273.0*
- **tare** `["<type 'numpy.float64'>"]`: *273.0*
- **Qc0** `["<type 'numpy.float64'>"]`: *-204653.58618871804*
- **tare_0** `["<type 'numpy.float64'>"]`: *298.76745199999999*
- **tasup_0** `["<type 'numpy.float64'>"]`: *288.5*
- **tsc0** `["<type 'numpy.int64'>"]`: *280*
- **trc0** `["<type 'numpy.int64'>"]`: *288*
- **wr** `["<type 'numpy.float64'>"]`: *0.0*
- **ws** `["<type 'numpy.float64'>"]`: *0.0*
- **ma0** `["<type 'numpy.float64'>"]`: *293.3384533787829*
- **ma** `["<type 'numpy.float64'>"]`: *0.0*
- **Cpa** `["<type 'numpy.float64'>"]`: *1.008*
- **LMRT0** `["<type 'numpy.float64'>"]`: *5.0389200206867066*
- **UA0** `["<type 'numpy.float64'>"]`: *-40614.573231671922*
- **mCw0** `["<type 'numpy.float64'>"]`: *25581.698273589755*
- **Qcsf** `["<type 'numpy.float64'>"]`: *-0*


### Output
- `["<type 'tuple'>"]`: (0, 0, 0)

[TOC](#table-of-contents)
---

# calc_Eaux_cs_dis
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **Qcsf** `["<type 'numpy.float64'>"]`: *-0*
- **Qcsf0** `["<type 'numpy.float64'>"]`: *-204653.58618871804*
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
- max duration: 0.041 s
- avg duration: 0.041 s
- min duration: 0.041 s
- total duration: 0.041 s

### Input
- **freshw** `["<type 'numpy.ndarray'>"]`: *array([ 0.05684067,  0.02842034,  0.00710508, ...,*
- **nf** `["<type 'numpy.float64'>"]`: *7.0*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x1E399A7*


### Output
- `["<type 'numpy.ndarray'>"]`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

[TOC](#table-of-contents)
---

# calc_Eaux_hs_dis
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **Qhsf** `["<type 'numpy.float64'>"]`: *0.0*
- **Qhsf0** `["<type 'numpy.float64'>"]`: *238040.53751762083*
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
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **Qhsf** `["<type 'numpy.float64'>"]`: *0.0*
- **Qcsf** `["<type 'numpy.float64'>"]`: *-0*
- **P_ve** `["<type 'numpy.float64'>"]`: *0.55000000000000004*
- **qve** `["<type 'numpy.float64'>"]`: *0.36187327522551677*
- **SystemH** `["<type 'numpy.unicode_'>"]`: *u'T1'*
- **SystemC** `["<type 'numpy.unicode_'>"]`: *u'T3'*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*


### Output
- `["<type 'float'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_Eaux_ww
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **Qww** `["<type 'numpy.float64'>"]`: *0.0*
- **Qwwf** `["<type 'numpy.float64'>"]`: *0.0*
- **Qwwf0** `["<type 'numpy.float64'>"]`: *7817.979206290941*
- **Imax** `["<type 'numpy.float64'>"]`: *88.705510978710478*
- **deltaP_des** `["<type 'numpy.float64'>"]`: *11.531716427232364*
- **b** `["<type 'numpy.float64'>"]`: *1.2*
- **qV_des** `["<type 'numpy.float64'>"]`: *0.0*


### Output
- `["<type 'float'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_HVAC
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **SystemH** `["<type 'unicode'>"]`: *u'T1'*
- **SystemC** `["<type 'unicode'>"]`: *u'T3'*
- **people** `["<type 'numpy.float64'>"]`: *0.0*
- **RH1** `["<type 'numpy.int64'>"]`: *65*
- **t1** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **tair** `["<type 'numpy.float64'>"]`: *15.696782868056831*
- **qv_req** `["<type 'numpy.float64'>"]`: *0.36187327522551677*
- **Flag** `["<type 'bool'>"]`: *False*
- **Qsen** `["<type 'numpy.float64'>"]`: *0.0*
- **t5_1** `["<type 'int'>"]`: *21*
- **wint** `["<type 'numpy.float64'>"]`: *0.0*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x20200E5*


### Output
- `["<type 'tuple'>"]`: (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16.6967828

[TOC](#table-of-contents)
---

# calc_Hcoil2
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **Qh** `["<type 'numpy.float64'>"]`: *0.0*
- **tasup** `["<type 'numpy.float64'>"]`: *273.0*
- **tare** `["<type 'numpy.float64'>"]`: *273.0*
- **Qh0** `["<type 'numpy.float64'>"]`: *2973.6572196073485*
- **tare_0** `["<type 'numpy.float64'>"]`: *287.33851664000002*
- **tasup_0** `["<type 'numpy.float64'>"]`: *302.5*
- **tsh0** `["<type 'numpy.int64'>"]`: *313*
- **trh0** `["<type 'numpy.int64'>"]`: *293*
- **wr** `["<type 'numpy.float64'>"]`: *0.0*
- **ws** `["<type 'numpy.float64'>"]`: *0.0*
- **ma0** `["<type 'numpy.float64'>"]`: *0.2508454338729228*
- **ma** `["<type 'numpy.float64'>"]`: *0.0*
- **Cpa** `["<type 'numpy.float64'>"]`: *1.008*
- **LMRT0** `["<type 'numpy.complex128'>"]`: *(3.2181823632629567-10.174322742210903j)*
- **UA0** `["<type 'numpy.complex128'>"]`: *(84.038584693840235+265.68900918555283j)*
- **mCw0** `["<type 'numpy.float64'>"]`: *148.68286098036742*
- **Qhsf** `["<type 'numpy.float64'>"]`: *0.0*


### Output
- `["<type 'tuple'>"]`: (0, 0, 0)

[TOC](#table-of-contents)
---

# calc_Htr
- number of invocations: 1
- max duration: 0.046 s
- avg duration: 0.046 s
- min duration: 0.046 s
- total duration: 0.046 s

### Input
- **Hve** `["<type 'numpy.float64'>"]`: *434.24793027062015*
- **Htr_is** `["<type 'numpy.float64'>"]`: *15748.652178585824*
- **Htr_ms** `["<type 'numpy.float64'>"]`: *63226.498647402281*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*


### Output
- `["<type 'tuple'>"]`: (422.59542894663815, 1825.969657874035, 1774.71618

[TOC](#table-of-contents)
---

# calc_Qdis_ls
- number of invocations: 1
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **tair** `["<type 'numpy.float64'>"]`: *15.696782868056831*
- **text** `["<type 'numpy.float64'>"]`: *8.8000000000000007*
- **Qhs** `["<type 'numpy.float64'>"]`: *0.0*
- **Qcs** `["<type 'numpy.float64'>"]`: *0.0*
- **tsh** `["<type 'numpy.int64'>"]`: *90*
- **trh** `["<type 'numpy.int64'>"]`: *70*
- **tsc** `["<type 'numpy.int64'>"]`: *7*
- **trc** `["<type 'numpy.int64'>"]`: *15*
- **Qhs_max** `["<type 'numpy.float64'>"]`: *236471.53751762083*
- **Qcs_max** `["<type 'numpy.float64'>"]`: *-204339.58618871804*
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

# calc_Qem_ls
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **SystemH** `["<type 'unicode'>"]`: *u'T1'*
- **SystemC** `["<type 'unicode'>"]`: *u'T3'*


### Output
- `["<type 'list'>"]`: [1.7, -1]

[TOC](#table-of-contents)
---

# calc_Qww_ls_nr
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

### Input
- **tair** `["<type 'numpy.float64'>"]`: *15.696782868056831*
- **Qww** `["<type 'numpy.float64'>"]`: *0.0*
- **Lvww_dis** `["<type 'numpy.float64'>"]`: *50.246706155723558*
- **Lvww_c** `["<type 'numpy.float64'>"]`: *55.259252908257515*
- **Y** `["<type 'numpy.float64'>"]`: *0.29999999999999999*
- **Qww_0** `["<type 'numpy.float64'>"]`: *5988.854757997784*
- **V** `["<type 'numpy.float64'>"]`: *81.45987041393002*
- **Flowtap** `["<type 'numpy.float64'>"]`: *0.035999999999999997*
- **twws** `["<type 'numpy.int64'>"]`: *60*
- **Cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*
- **Pwater** `["<type 'numpy.int32'>"]`: *998*
- **Bf** `["<type 'numpy.float64'>"]`: *0.69999999999999996*
- **te** `["<type 'numpy.float64'>"]`: *8.8000000000000007*


### Output
- `["<type 'numpy.float64'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_Qww_ls_r
- number of invocations: 1
- max duration: 0.093 s
- avg duration: 0.093 s
- min duration: 0.093 s
- total duration: 0.093 s

### Input
- **Tair** `["<type 'numpy.float64'>"]`: *15.696782868056831*
- **Qww** `["<type 'numpy.float64'>"]`: *0.0*
- **lsww_dis** `["<type 'numpy.float64'>"]`: *183.34912611426176*
- **lcww_dis** `["<type 'numpy.float64'>"]`: *72.543326121114177*
- **Y** `["<type 'numpy.float64'>"]`: *0.40000000000000002*
- **Qww_0** `["<type 'numpy.float64'>"]`: *5988.854757997784*
- **V** `["<type 'numpy.float64'>"]`: *81.45987041393002*
- **Flowtap** `["<type 'numpy.float64'>"]`: *0.035999999999999997*
- **twws** `["<type 'numpy.int64'>"]`: *60*
- **Cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*
- **Pwater** `["<type 'numpy.int32'>"]`: *998*


### Output
- `["<type 'numpy.float64'>"]`: 0.0

[TOC](#table-of-contents)
---

# calc_RAD
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **Qh** `["<type 'numpy.float64'>"]`: *0.0*
- **tair** `["<type 'numpy.float64'>"]`: *15.696782868056831*
- **Qh0** `["<type 'numpy.float64'>"]`: *238040.53751762083*
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
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **Qh** `["<type 'numpy.float64'>"]`: *104794.32592430274*
- **tair** `["<type 'numpy.float64'>"]`: *22.0*
- **Qh0** `["<type 'numpy.float64'>"]`: *125220.41121154878*
- **tair0** `["<type 'numpy.float64'>"]`: *22.0*
- **tsh0** `["<type 'numpy.int64'>"]`: *40*
- **trh0** `["<type 'numpy.int64'>"]`: *35*
- **nh** `["<type 'numpy.float64'>"]`: *0.20000000000000001*


### Output
- `["<type 'tuple'>"]`: (37.448100582343471, 33.263705845479763, 25.044082

[TOC](#table-of-contents)
---

# calc_TL
- number of invocations: 1
- max duration: 0.164 s
- avg duration: 0.164 s
- min duration: 0.164 s
- total duration: 0.164 s

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
- **Htr_1** `["<type 'numpy.float64'>"]`: *422.59542894663815*
- **Htr_2** `["<type 'numpy.float64'>"]`: *1825.969657874035*
- **Htr_3** `["<type 'numpy.float64'>"]`: *1774.7161808217863*
- **I_st** `["<type 'numpy.float64'>"]`: *-994.95409442637401*
- **Hve** `["<type 'numpy.float64'>"]`: *434.24793027062015*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **I_ia** `["<type 'numpy.float64'>"]`: *1789.9699685754961*
- **I_m** `["<type 'numpy.float64'>"]`: *2724.4521715126948*
- **Cm** `["<type 'numpy.float64'>"]`: *651371895.40593004*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Losses** `["<type 'bool'>"]`: *False*
- **tHset_corr** `["<type 'float'>"]`: *1.7*
- **tCset_corr** `["<type 'int'>"]`: *-1*
- **IC_max** `["<type 'numpy.float64'>"]`: *-1085619.8256765502*
- **IH_max** `["<type 'numpy.float64'>"]`: *1085619.8256765502*
- **Flag** `["<type 'bool'>"]`: *False*


### Output
- `["<type 'tuple'>"]`: (15.96286680328714, 15.696782868056831, 0, 0, 0, 1

[TOC](#table-of-contents)
---

# calc_capacity_heating_cooling_system
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **prop_HVAC** `["<class 'pandas.core.series.Series'>"]`: *type_hs        T1
type_cs        T3
type_dhw      *


### Output
- `["<type 'tuple'>"]`: (-1085619.8256765502, 1085619.8256765502)

[TOC](#table-of-contents)
---

# calc_comp_heat_gains_sensible
- number of invocations: 1
- max duration: 0.08 s
- avg duration: 0.08 s
- min duration: 0.08 s
- total duration: 0.08 s

### Input
- **Am** `["<type 'numpy.float64'>"]`: *6947.9668843299214*
- **Atot** `["<type 'numpy.float64'>"]`: *4564.8267184306733*
- **Htr_w** `["<type 'numpy.float64'>"]`: *1403.3742289273969*
- **I_int_sen** `["<type 'numpy.ndarray'>"]`: *array([ 3579.93993715,  3579.93993715,  3579.93993*
- **I_sol** `["<class 'pandas.core.series.Series'>"]`: *T1     0.000000e+00
T2     0.000000e+00
T3     0.0*


### Output
- `["<type 'tuple'>"]`: (array([ 1789.96996858,  1789.96996858,  1789.9699

[TOC](#table-of-contents)
---

# calc_dhw_heating_demand
- number of invocations: 1
- max duration: 0.85 s
- avg duration: 0.85 s
- min duration: 0.85 s
- total duration: 0.85 s

### Input
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Lcww_dis** `["<type 'numpy.float64'>"]`: *72.543326121114177*
- **Lsww_dis** `["<type 'numpy.float64'>"]`: *183.34912611426176*
- **Lvww_c** `["<type 'numpy.float64'>"]`: *55.259252908257515*
- **Lvww_dis** `["<type 'numpy.float64'>"]`: *50.246706155723558*
- **T_ext** `["<type 'numpy.ndarray'>"]`: *array([ 8.8,  8.6,  8.4, ..., -0.3, -0.5, -0.7])*
- **Ta** `["<type 'numpy.ndarray'>"]`: *array([ 15.69678287,  15.64983331,  15.60189303, .*
- **Tww_re** `["<type 'numpy.ndarray'>"]`: *array([ 20.,  20.,  20., ...,  20.,  20.,  20.])*
- **Tww_sup_0** `["<type 'numpy.int64'>"]`: *60*
- **Y** `["<type 'list'>"]`: *[0.3, 0.4, 0.4]*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x1E394AD*
- **vw** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **vww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `["<type 'tuple'>"]`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array

[TOC](#table-of-contents)
---

# calc_disls
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **tamb** `["<type 'numpy.float64'>"]`: *15.696782868056831*
- **hotw** `["<type 'numpy.float64'>"]`: *0.0*
- **Flowtap** `["<type 'numpy.float64'>"]`: *0.035999999999999997*
- **V** `["<type 'numpy.float64'>"]`: *81.45987041393002*
- **twws** `["<type 'numpy.int64'>"]`: *60*
- **Lsww_dis** `["<type 'numpy.float64'>"]`: *183.34912611426176*
- **p** `["<type 'numpy.int32'>"]`: *998*
- **cpw** `["<type 'numpy.float64'>"]`: *4.1840000000000002*
- **Y** `["<type 'numpy.float64'>"]`: *0.40000000000000002*


### Output
- `["<type 'int'>"]`: 0

[TOC](#table-of-contents)
---

# calc_gl
- number of invocations: 1
- max duration: 0.038 s
- avg duration: 0.038 s
- min duration: 0.038 s
- total duration: 0.038 s

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
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **t** `["<type 'numpy.float64'>"]`: *23.0*
- **w** `["<type 'numpy.float64'>"]`: *0.0041699403233700994*


### Output
- `["<type 'numpy.float64'>"]`: 33.740492623233642

[TOC](#table-of-contents)
---

# calc_heat_gains_internal_latent
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

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
- max duration: 0.041 s
- avg duration: 0.041 s
- min duration: 0.041 s
- total duration: 0.041 s

### Input
- **people** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qs_Wp** `["<type 'numpy.float64'>"]`: *70.0*
- **Eal_nove** `["<type 'numpy.ndarray'>"]`: *array([ 3977.71104128,  3977.71104128,  3977.71104*
- **Eprof** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcdata** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `["<type 'numpy.ndarray'>"]`: array([ 3579.93993715,  3579.93993715,  3579.93993

[TOC](#table-of-contents)
---

# calc_heat_gains_solar
- number of invocations: 1
- max duration: 0.234 s
- avg duration: 0.234 s
- min duration: 0.234 s
- total duration: 0.234 s

### Input
- **Aw** `["<type 'numpy.float64'>"]`: *452.70136417012804*
- **Awall_all** `["<type 'numpy.float64'>"]`: *1131.75341042532*
- **Sh_typ** `["<type 'unicode'>"]`: *u'T1'*
- **Solar** `["<class 'pandas.core.series.Series'>"]`: *T1     0.000000e+00
T2     0.000000e+00
T3     0.0*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x1E8F347*


### Output
- `["<class 'pandas.core.series.Series'>"]`: T1     0.000000e+00
T2     0.000000e+00
T3     0.0

[TOC](#table-of-contents)
---

# calc_loads_electrical
- number of invocations: 1
- max duration: 0.038 s
- avg duration: 0.038 s
- min duration: 0.038 s
- total duration: 0.038 s

### Input
- **Aef** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Eal_nove** `["<type 'numpy.ndarray'>"]`: *array([ 3977.71104128,  3977.71104128,  3977.71104*
- **Eauxf** `["<type 'numpy.ndarray'>"]`: *array([  0.        ,   0.        ,   0.        , .*
- **Edataf** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eprof** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `["<type 'tuple'>"]`: (array([ 8636563.93444973,  8636563.93444973,  863

[TOC](#table-of-contents)
---

# calc_mixed_schedule
- number of invocations: 1
- max duration: 0.754 s
- avg duration: 0.754 s
- min duration: 0.754 s
- total duration: 0.754 s

### Input
- **list_uses** `["<type 'list'>"]`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'M*
- **schedules** `["<type 'list'>"]`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `["<class 'pandas.core.series.Series'>"]`: *GYM           0
HOSPITAL      0
HOTEL         0
IN*


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
- max duration: 0.315 s
- avg duration: 0.315 s
- min duration: 0.315 s
- total duration: 0.315 s

### Input
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Ll** `["<type 'numpy.float64'>"]`: *32.648092418099999*
- **Lw** `["<type 'numpy.float64'>"]`: *16.008581384100001*
- **Mww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcsf** `["<type 'numpy.ndarray'>"]`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `["<type 'numpy.float64'>"]`: *-204653.58618871804*
- **Qhsf** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.  *
- **Qhsf_0** `["<type 'numpy.float64'>"]`: *238040.53751762083*
- **Qww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `["<type 'numpy.float64'>"]`: *7817.979206290941*
- **Tcs_re** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 24, 24, 24])*
- **Ths_sup** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 27, 27, 28])*
- **Vw** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Year** `["<type 'numpy.int64'>"]`: *1993*
- **fforma** `["<type 'numpy.float64'>"]`: *0.76931348014904022*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2025F7B*
- **nf_ag** `["<type 'numpy.float64'>"]`: *4.0*
- **nfp** `["<type 'numpy.float64'>"]`: *1.0*
- **qv_req** `["<type 'numpy.ndarray'>"]`: *array([ 0.36187328,  0.36187328,  0.36187328, ...,*
- **sys_e_cooling** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_heating** `["<type 'unicode'>"]`: *u'T1'*


### Output
- `["<type 'tuple'>"]`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array

[TOC](#table-of-contents)
---

# calc_qv_req
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **ve** `["<type 'numpy.float64'>"]`: *0.0*
- **people** `["<type 'numpy.float64'>"]`: *0.0*
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2025FB1*
- **hour_day** `["<type 'numpy.int32'>"]`: *0*
- **hour_year** `["<type 'numpy.int32'>"]`: *0*
- **limit_inf_season** `["<type 'numpy.int32'>"]`: *3217*
- **limit_sup_season** `["<type 'numpy.int32'>"]`: *6192*


### Output
- `["<type 'numpy.float64'>"]`: 0.36187327522551677

[TOC](#table-of-contents)
---

# calc_temperatures_emission_systems
- number of invocations: 1
- max duration: 1.057 s
- avg duration: 1.057 s
- min duration: 1.057 s
- total duration: 1.057 s

### Input
- **Qcsf** `["<type 'numpy.ndarray'>"]`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `["<type 'numpy.float64'>"]`: *-204653.58618871804*
- **Qhsf** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.  *
- **Qhsf_0** `["<type 'numpy.float64'>"]`: *238040.53751762083*
- **Ta** `["<type 'numpy.ndarray'>"]`: *array([ 15.69678287,  15.64983331,  15.60189303, .*
- **Ta_re_cs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_re_hs** `["<type 'numpy.ndarray'>"]`: *array([ 0.        ,  0.        ,  0.        , ...,*
- **Ta_sup_cs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_hs** `["<type 'numpy.ndarray'>"]`: *array([  0. ,   0. ,   0. , ...,  29.5,  29.5,  29*
- **Tcs_re_0** `["<type 'numpy.int64'>"]`: *15*
- **Tcs_sup_0** `["<type 'numpy.int64'>"]`: *7*
- **Ths_re_0** `["<type 'numpy.int64'>"]`: *70*
- **Ths_sup_0** `["<type 'numpy.int64'>"]`: *90*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2025F07*
- **ma_sup_cs** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **ma_sup_hs** `["<type 'numpy.ndarray'>"]`: *array([ 0.        ,  0.        ,  0.        , ...,*
- **sys_e_cooling** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_heating** `["<type 'unicode'>"]`: *u'T1'*
- **ta_hs_set** `["<type 'numpy.ndarray'>"]`: *array([ 12.,  12.,  12., ...,  12.,  12.,  12.])*
- **w_re** `["<type 'numpy.ndarray'>"]`: *array([ 0.        ,  0.        ,  0.        , ...,*
- **w_sup** `["<type 'numpy.ndarray'>"]`: *array([ 0.        ,  0.        ,  0.        , ...,*


### Output
- `["<type 'tuple'>"]`: (array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, .

[TOC](#table-of-contents)
---

# calc_w
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **t** `["<type 'numpy.float64'>"]`: *8.0999999999999996*
- **RH** `["<type 'numpy.int64'>"]`: *62*


### Output
- `["<type 'numpy.float64'>"]`: 0.0041699403233700994

[TOC](#table-of-contents)
---

# calc_w3_cooling_case
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **w2** `["<type 'numpy.float64'>"]`: *0.0063353710010796305*
- **t3** `["<type 'int'>"]`: *16*
- **w5** `["<type 'numpy.float64'>"]`: *0.0071562131687267936*
- **liminf** `["<type 'float'>"]`: *0.005636886384620951*
- **limsup** `["<type 'float'>"]`: *0.013314133298988883*
- **m** `["<type 'numpy.float64'>"]`: *2.0153421629692034*
- **lvapor** `["<type 'int'>"]`: *2257*


### Output
- `["<type 'tuple'>"]`: (0.0063353710010796305, 0, 0)

[TOC](#table-of-contents)
---

# calc_w3_heating_case
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

### Input
- **t5** `["<type 'numpy.float64'>"]`: *23.0*
- **w2** `["<type 'numpy.float64'>"]`: *0.0041699403233700994*
- **w5** `["<type 'numpy.float64'>"]`: *0.0042029928046326687*
- **t3** `["<type 'int'>"]`: *30*
- **t5_1** `["<type 'numpy.float64'>"]`: *16.434122635221094*
- **m** `["<type 'numpy.float64'>"]`: *16.683344854513354*
- **lvapor** `["<type 'int'>"]`: *2257*
- **liminf** `["<type 'float'>"]`: *0.005238573137613202*
- **limsup** `["<type 'float'>"]`: *0.012362611394129815*


### Output
- `["<type 'tuple'>"]`: (0.0052055206563506326, 38994.062200986169, 0)

[TOC](#table-of-contents)
---

# calculate_pipe_transmittance_values
- number of invocations: 1
- max duration: 0.05 s
- avg duration: 0.05 s
- min duration: 0.05 s
- total duration: 0.05 s

### Input
- **year** `["<type 'numpy.int64'>"]`: *1993*
- **Retrofit** `["<type 'numpy.int64'>"]`: *0*


### Output
- `["<type 'list'>"]`: [0.3, 0.4, 0.4]

[TOC](#table-of-contents)
---

# demand_calculation
- number of invocations: 1
- max duration: 979.283 s
- avg duration: 979.283 s
- min duration: 979.283 s
- total duration: 979.283 s

### Input
- **locator** `["<class 'cea.inputlocator.InputLocator'>"]`: *<cea.inputlocator.InputLocator object at 0x2025F9B*
- **weather_path** `["<type 'str'>"]`: *'C:\\Users\\darthoma\\Documents\\GitHub\\CEAforArc*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x2025F9B*


### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

# get_internal_comfort
- number of invocations: 1
- max duration: 0.059 s
- avg duration: 0.059 s
- min duration: 0.059 s
- total duration: 0.059 s

### Input
- **people** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **prop_comfort** `["<class 'pandas.core.series.Series'>"]`: *Tcs_set_C     24
Tcs_setb_C    28
Ths_set_C     22*
- **limit_inf_season** `["<type 'int'>"]`: *3217*
- **limit_sup_season** `["<type 'int'>"]`: *6192*
- **hour_year** `["<type 'numpy.ndarray'>"]`: *array([ 0,  1,  2, ..., 21, 22, 23])*


### Output
- `["<type 'tuple'>"]`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array

[TOC](#table-of-contents)
---

# get_internal_loads
- number of invocations: 1
- max duration: 0.039 s
- avg duration: 0.039 s
- min duration: 0.039 s
- total duration: 0.039 s

### Input
- **mixed_schedule** `["<class 'pandas.core.frame.DataFrame'>"]`: *(8760, 4)*
- **prop_internal_loads** `["<class 'pandas.core.series.Series'>"]`: *Ea_Wm2       7.0
Ed_Wm2       0.0
El_Wm2      15.9*
- **prop_architecture** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
type_shade     T1
win_wall      *
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
- `["<type 'tuple'>"]`: (array([ 3977.71104128,  3977.71104128,  3977.7110

[TOC](#table-of-contents)
---

# get_occupancy
- number of invocations: 1
- max duration: 0.038 s
- avg duration: 0.038 s
- min duration: 0.038 s
- total duration: 0.038 s

### Input
- **mixed_schedule** `["<class 'pandas.core.frame.DataFrame'>"]`: *(8760, 4)*
- **prop_architecture** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
type_shade     T1
win_wall      *
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
- max duration: 0.27 s
- avg duration: 0.27 s
- min duration: 0.27 s
- total duration: 0.27 s

### Input
- **uses** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 9)*
- **architecture** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 3)*
- **thermal** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 7)*
- **geometry** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 8)*
- **HVAC** `["<class 'pandas.core.frame.DataFrame'>"]`: *(1482, 13)*
- **rf** `["<class 'pandas.core.frame.DataFrame'>"]`: *(2140, 5)*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x1097DD3*

#### HVAC:
```
           Tshs0_C      dThs0_C   Qhsmax_Wm2      Tscs0_C      dTcs0_C  \
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000   
mean     88.245614    19.679487   494.264507     2.597841     2.968961   
std       9.943751     2.130572    49.822428     3.382873     3.866141   
min       0.000000     0.000000     0.000000     0.000000     0.000000   
25%      90.000000    20.000000   500.000000     0.000000     0.000000   
50%      90.000000    20.000000   500.000000     0.000000     0.000000   
75%      90.000000    20.000000   500.000000     7.000000     8.000000   
max      90.000000    20.000000   500.000000     7.000000     8.000000   

        Qcsmax_Wm2      Tsww0_C      dTww0_C   Qwwmax_Wm2  
count  1482.000000  1482.000000  1482.000000  1482.000000  
mean    185.560054    59.595142    39.730094   496.626181  
std     241.633795     4.913642     3.275761    40.947018  
min       0.000000     0.000000     0.000000     0.000000  
25%       0.000000    60.000000    40.000000   500.000000  
50%       0.000000    60.000000    40.000000   500.000000  
75%     500.000000    60.000000    40.000000   500.000000  
max     500.000000    60.000000    40.000000   500.000000  

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
- `["<class 'pandas.core.frame.DataFrame'>"]`: (274, 14)
```
          Awall_all           Atot           Aw             Am            Aef  \
count    274.000000     274.000000   274.000000     274.000000     274.000000   
mean    1229.167375    6788.584880   341.214719   10262.859246    3990.484436   
std     1614.734960   15317.136196   461.975223   27230.133256   10670.567419   
min       26.326689      35.854865     6.095712       0.000000       4.287679   
25%      336.506101    1235.762736    85.964162    1182.449634     449.853115   
50%      713.470323    2348.721099   171.734138    2588.168154    1014.216986   
75%     1362.915079    5790.761600   405.955475    7334.245516    2933.698206   
max    12466.623953  181691.565146  3317.350336  329540.768090  131816.307236   

                  Af            Cm         Htr_is        Htr_em  \
count     274.000000  2.740000e+02     274.000000    274.000000   
mean     3988.470653  7.143507e+08   23420.617836   1234.781696   
std     10671.305464  1.893164e+09   52844.119875   2573.653149   
min         0.000000  0.000000e+00     123.699285     -0.000000   
25%       449.853115  8.010539e+07    4263.381439    160.312351   
50%      1014.216986  1.719449e+08    8103.087793    281.381072   
75%      2933.698206  5.755465e+08   19978.127521    835.058050   
max    131816.307236  2.174969e+10  626835.899755  20330.043380   

               Htr_ms        Htr_op           Hg            HD        Htr_w  
count      274.000000    274.000000   274.000000    274.000000   274.000000  
mean     93392.019136   1208.373440   529.902047    678.471393   660.495818  
std     247794.212631   2513.090338  1127.811143   1602.225219  1097.681033  
min          0.000000     10.086766     2.075740      7.720315     7.924426  
25%      10760.291670    162.342105    54.265664     97.633223   123.732742  
50%      23552.330203    280.892472    94.493504    172.924079   261.920127  
75%      66741.634197    816.542270   366.717077    411.857669   593.145962  
max    2998820.989622  19924.663212  9154.270129  13660.091141  9038.302366  

[8 rows x 14 columns]
```

[TOC](#table-of-contents)
---

# get_properties_building_envelope
- number of invocations: 1
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **prop_RC_model** `["<class 'pandas.core.series.Series'>"]`: *Awall_all    1.131753e+03
Atot         4.564827e+0*
- **prop_age** `["<class 'pandas.core.series.Series'>"]`: *HVAC             0
basement         0
built       *
- **prop_architecture** `["<class 'pandas.core.series.Series'>"]`: *Occ_m2p        14
type_shade     T1
win_wall      *
- **prop_geometry** `["<class 'pandas.core.series.Series'>"]`: *Blength       32.648092
Bwidth        16.008581
fl*
- **prop_occupancy** `["<class 'pandas.core.series.Series'>"]`: *GYM           0
HOSPITAL      0
HOTEL         0
IN*


### Output
- `["<type 'tuple'>"]`: (6947.9668843299214, 4564.8267184306733, 452.70136

[TOC](#table-of-contents)
---

# get_properties_building_systems
- number of invocations: 1
- max duration: 0.18 s
- avg duration: 0.18 s
- min duration: 0.18 s
- total duration: 0.18 s

### Input
- **Ll** `["<type 'numpy.float64'>"]`: *32.648092418099999*
- **Lw** `["<type 'numpy.float64'>"]`: *16.008581384100001*
- **Retrofit** `["<type 'numpy.int64'>"]`: *0*
- **Year** `["<type 'numpy.int64'>"]`: *1993*
- **footprint** `["<type 'numpy.float64'>"]`: *402.0814169172408*
- **gv** `["<class 'cea.globalvar.GlobalVariables'>"]`: *<cea.globalvar.GlobalVariables object at 0x1E39167*
- **nf_ag** `["<type 'numpy.float64'>"]`: *4.0*
- **nfp** `["<type 'numpy.float64'>"]`: *1.0*
- **prop_HVAC** `["<class 'pandas.core.series.Series'>"]`: *type_hs        T1
type_cs        T3
type_dhw      *


### Output
- `["<type 'tuple'>"]`: (72.543326121114177, 183.34912611426176, 67.916762

[TOC](#table-of-contents)
---

# get_temperatures
- number of invocations: 1
- max duration: 0.098 s
- avg duration: 0.098 s
- min duration: 0.098 s
- total duration: 0.098 s

### Input
- **locator** `["<class 'cea.inputlocator.InputLocator'>"]`: *<cea.inputlocator.InputLocator object at 0x1E39FF7*
- **prop_HVAC** `["<class 'geopandas.geodataframe.GeoDataFrame'>"]`: *(1482, 5)*


### Output
- `["<class 'pandas.core.frame.DataFrame'>"]`: (1482, 14)
```
           Tshs0_C      dThs0_C   Qhsmax_Wm2      Tscs0_C      dTcs0_C  \
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000   
mean     88.245614    19.679487   494.264507     2.597841     2.968961   
std       9.943751     2.130572    49.822428     3.382873     3.866141   
min       0.000000     0.000000     0.000000     0.000000     0.000000   
25%      90.000000    20.000000   500.000000     0.000000     0.000000   
50%      90.000000    20.000000   500.000000     0.000000     0.000000   
75%      90.000000    20.000000   500.000000     7.000000     8.000000   
max      90.000000    20.000000   500.000000     7.000000     8.000000   

        Qcsmax_Wm2      Tsww0_C      dTww0_C   Qwwmax_Wm2  
count  1482.000000  1482.000000  1482.000000  1482.000000  
mean    185.560054    59.595142    39.730094   496.626181  
std     241.633795     4.913642     3.275761    40.947018  
min       0.000000     0.000000     0.000000     0.000000  
25%       0.000000    60.000000    40.000000   500.000000  
50%       0.000000    60.000000    40.000000   500.000000  
75%     500.000000    60.000000    40.000000   500.000000  
max     500.000000    60.000000    40.000000   500.000000  

[8 rows x 9 columns]
```

[TOC](#table-of-contents)
---

# results_to_csv
- number of invocations: 1
- max duration: 0.257 s
- avg duration: 0.257 s
- min duration: 0.257 s
- total duration: 0.257 s

### Input
- **Af** `["<type 'numpy.float64'>"]`: *2171.2396513531003*
- **Ealf** `["<type 'numpy.ndarray'>"]`: *array([ 8636563.93444973,  8636563.93444973,  8636*
- **Ealf_0** `["<type 'numpy.float64'>"]`: *86365639.344497323*
- **Ealf_tot** `["<type 'numpy.float64'>"]`: *197466.39779724294*
- **Eauxf** `["<type 'numpy.ndarray'>"]`: *array([  0.        ,   0.        ,   0.        , .*
- **Eauxf_tot** `["<type 'numpy.float64'>"]`: *5.2523332200346564*
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
- **Qcsf_0** `["<type 'numpy.float64'>"]`: *-204653.58618871804*
- **Qhs_sen** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.  *
- **Qhsf** `["<type 'numpy.ndarray'>"]`: *array([     0.        ,      0.        ,      0.  *
- **Qhsf_0** `["<type 'numpy.float64'>"]`: *238040.53751762083*
- **Qww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qww_ls_st** `["<type 'numpy.ndarray'>"]`: *array([ 16.27469621,  16.31423479,  16.35384389, .*
- **Qwwf** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `["<type 'numpy.float64'>"]`: *7817.979206290941*
- **Tcs_re** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_re_0** `["<type 'numpy.int64'>"]`: *15*
- **Tcs_sup** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup_0** `["<type 'numpy.int64'>"]`: *7*
- **Ths_re** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 24, 24, 24])*
- **Ths_re_0** `["<type 'numpy.int64'>"]`: *70*
- **Ths_sup** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 27, 27, 28])*
- **Ths_sup_0** `["<type 'numpy.int64'>"]`: *90*
- **Tww_re** `["<type 'numpy.ndarray'>"]`: *array([ 20.,  20.,  20., ...,  20.,  20.,  20.])*
- **Tww_st** `["<type 'numpy.ndarray'>"]`: *array([ 59.96527642,  59.93046849,  59.89557604, .*
- **Tww_sup_0** `["<type 'numpy.int64'>"]`: *60*
- **Waterconsumption** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **locationFinal** `["<type 'str'>"]`: *'C:\\reference-case\\baseline\\2-results\\2-demand*
- **mcpcs** `["<type 'numpy.ndarray'>"]`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcphs** `["<type 'numpy.ndarray'>"]`: *array([ 0,  0,  0, ..., 11, 11, 11])*
- **mcpww** `["<type 'numpy.ndarray'>"]`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **path_temporary_folder** `["<type 'str'>"]`: *'c:\\users\\darthoma\\appdata\\local\\temp'*
- **sys_e_cooling** `["<type 'unicode'>"]`: *u'T3'*
- **sys_e_heating** `["<type 'unicode'>"]`: *u'T1'*
- **waterpeak** `["<type 'numpy.float64'>"]`: *0.33673440168628083*
- **date** `["<class 'pandas.tseries.index.DatetimeIndex'>"]`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016*


### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

# test_demand
- number of invocations: 1
- max duration: 979.379 s
- avg duration: 979.379 s
- min duration: 979.379 s
- total duration: 979.379 s

### Input


### Output
- `["<type 'NoneType'>"]`: None

[TOC](#table-of-contents)
---

