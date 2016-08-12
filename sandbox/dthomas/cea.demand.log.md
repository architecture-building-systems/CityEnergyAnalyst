# Table of contents
- [run_as_script](#run_as_script)
   - [demand_calculation](#demand_calculation)
      - [get_temperatures](#get_temperatures)
         - [schedule_maker](#schedule_maker)
            - [read_schedules](#read_schedules)
         - [thermal_loads_all_buildings](#thermal_loads_all_buildings)
            - [calc_thermal_loads](#calc_thermal_loads)
               - [calc_occ](#calc_occ)
                  - [calc_occ_schedule](#calc_occ_schedule)
               - [calc_Eint](#calc_eint)
                  - [calc_Ea_El_Edata_Eref_schedule](#calc_ea_el_edata_eref_schedule)
                  - [calc_Eprof_schedule](#calc_eprof_schedule)
                  - [calc_Eaf](#calc_eaf)
                  - [calc_Elf](#calc_elf)
                  - [calc_Edataf](#calc_edataf)
                  - [calc_Eref](#calc_eref)
                  - [calc_Eprof](#calc_eprof)
               - [calc_Qgain_sen](#calc_qgain_sen)
                  - [calc_I_sol](#calc_i_sol)
               - [calc_Qgain_lat](#calc_qgain_lat)
               - [get_properties_natural_ventilation](#get_properties_natural_ventilation)
                  - [calc_qv_delta_p_ref](#calc_qv_delta_p_ref)
                  - [get_building_geometry_ventilation](#get_building_geometry_ventilation)
                  - [calc_coeff_lea_zone](#calc_coeff_lea_zone)
                  - [allocate_default_leakage_paths](#allocate_default_leakage_paths)
                  - [lookup_coeff_wind_pressure](#lookup_coeff_wind_pressure)
                  - [calc_coeff_vent_zone](#calc_coeff_vent_zone)
                  - [allocate_default_ventilation_openings](#allocate_default_ventilation_openings)
               - [calc_thermal_load_mechanical_and_natural_ventilation_timestep](#calc_thermal_load_mechanical_and_natural_ventilation_timestep)
                  - [calc_T_em_ls](#calc_t_em_ls)
                  - [calc_Qhs_Qcs_sys_max](#calc_qhs_qcs_sys_max)
                  - [calc_h_ve_adj](#calc_h_ve_adj)
                  - [calc_Htr](#calc_htr)
                  - [calc_Qhs_Qcs](#calc_qhs_qcs)
               - [calc_thermal_load_hvac_timestep](#calc_thermal_load_hvac_timestep)
                  - [calc_hex](#calc_hex)
                     - [calc_w](#calc_w)
                  - [calc_hvac](#calc_hvac)
                     - [calc_h](#calc_h)
                     - [calc_w3_cooling_case](#calc_w3_cooling_case)
                        - [calc_Qhs_Qcs_dis_ls](#calc_qhs_qcs_dis_ls)
               - [calc_temperatures_emission_systems](#calc_temperatures_emission_systems)
               - [calc_Qwwf](#calc_qwwf)
                  - [calc_Qww_schedule](#calc_qww_schedule)
                     - [calc_mww](#calc_mww)
                     - [calc_Qww](#calc_qww)
                     - [calc_Qww_dis_ls_r](#calc_qww_dis_ls_r)
                        - [calc_disls](#calc_disls)
                     - [calc_Qww_dis_ls_nr](#calc_qww_dis_ls_nr)
                  - [calc_Qww_st_ls](#calc_qww_st_ls)
               - [calc_Eauxf](#calc_eauxf)
                  - [calc_Eauxf_ww](#calc_eauxf_ww)
                  - [calc_Eauxf_hs_dis](#calc_eauxf_hs_dis)
                  - [calc_Eauxf_cs_dis](#calc_eauxf_cs_dis)
                  - [calc_Eauxf_ve](#calc_eauxf_ve)
               - [calc_E_totals](#calc_e_totals)
               - [results_to_csv](#results_to_csv)
                  - [calc_Eauxf_fw](#calc_eauxf_fw)
                     - [calc_w3_heating_case](#calc_w3_heating_case)
         - [write_totals_csv](#write_totals_csv)

# allocate_default_leakage_paths
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **coeff_lea_zone** `['float64']`: *2130.2643780536373*
- **area_facade_zone** `['float64']`: *1237.0067791693345*
- **area_roof_zone** `['float64']`: *402.0814169172408*
- **height_zone** `['float64']`: *12.0*


### Output
- `['tuple']`: (array([ 401.92338084,  401.92338084,  401.92338084,  401.92338084,
        522.57085469]), array([  3.,   3.,   9.,   9.,  12.]), array([ 0.,  1.,  0.,  1.,  2.]))

### Docstring template

```
PARAMETERS
----------

:param coeff_lea_zone:
:type coeff_lea_zone: float64

:param area_facade_zone:
:type area_facade_zone: float64

:param area_roof_zone:
:type area_roof_zone: float64

:param height_zone:
:type height_zone: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# allocate_default_ventilation_openings
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **coeff_vent_zone** `['float']`: *0.0*
- **height_zone** `['float64']`: *12.0*


### Output
- `['tuple']`: (array([ 0.,  0.,  0.,  0.]), array([ 3.,  3.,  9.,  9.]), array([ 0.,  1.,  0.,  1.]))

### Docstring template

```
PARAMETERS
----------

:param coeff_vent_zone:
:type coeff_vent_zone: float

:param height_zone:
:type height_zone: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_E_totals
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **Aef** `['float64']`: *2171.2396513531003*
- **Ealf** `['ndarray']`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Eauxf** `['ndarray']`: *array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796])*
- **Edataf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['tuple']`: (array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096]), 39777.110412788796, 90.946385247798304, 2.0123670800422278, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0)

### Docstring template

```
PARAMETERS
----------

:param Aef:
:type Aef: float64

:param Ealf:
:type Ealf: ndarray

:param Eauxf:
:type Eauxf: ndarray

:param Edataf:
:type Edataf: ndarray

:param Eprof:
:type Eprof: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Ea_El_Edata_Eref_schedule
- number of invocations: 1
- max duration: 0.512 s
- avg duration: 0.512 s
- min duration: 0.512 s
- total duration: 0.512 s

### Input
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 1.0, u'GYM': 0.0, u'HOTEL': 0.0, u'PFloor': 1.0, u'PARKING': 0.0, u'MULTI_RES': 0.0, u'RETAIL': 0.0, u'HOSPITAL': 0.0}*


### Output
- `['ndarray']`: array([ 0.08,  0.08,  0.08, ...,  0.06,  0.06,  0.06])

### Docstring template

```
PARAMETERS
----------

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: dict

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eaf
- number of invocations: 1
- max duration: 0.044 s
- avg duration: 0.044 s
- min duration: 0.044 s
- total duration: 0.044 s

### Input
- **schedule** `['ndarray']`: *array([ 0.08,  0.08,  0.08, ...,  0.06,  0.06,  0.06])*
- **Ea_Wm2** `['float64']`: *7.0*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['ndarray']`: array([ 1215.89420476,  1215.89420476,  1215.89420476, ...,   911.92065357,
         911.92065357,   911.92065357])

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: ndarray

:param Ea_Wm2:
:type Ea_Wm2: float64

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eauxf
- number of invocations: 1
- max duration: 0.292 s
- avg duration: 0.292 s
- min duration: 0.292 s
- total duration: 0.292 s

### Input
- **Af** `['float64']`: *2171.2396513531003*
- **Ll** `['float64']`: *32.648092418099999*
- **Lw** `['float64']`: *16.008581384100001*
- **Mww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-281104.46918348083*
- **Qhsf** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        93991.5268617 ,  94591.45409877,  95210.96830999])*
- **Qhsf_0** `['float64']`: *296485.76361481688*
- **Qww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf** `['ndarray']`: *array([  9.73533082,   9.75835448,   9.78142295, ...,  11.14941905,
        11.16687292,  11.18431081])*
- **Qwwf_0** `['float64']`: *5419.7627526345404*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re** `['ndarray']`: *array([ 0,  0,  0, ..., 32, 32, 32])*
- **Ths_sup** `['ndarray']`: *array([ 0,  0,  0, ..., 39, 39, 39])*
- **Vw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Year** `['int64']`: *1993*
- **fforma** `['float64']`: *0.76931348014904022*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C972E10>*
- **nf_ag** `['float64']`: *4.0*
- **nfp** `['float64']`: *1.0*
- **qv_req** `['ndarray']`: *array([ 1.16944851,  1.16944851,  1.16944851, ...,  1.16944851,
        1.16944851,  1.16944851])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **Ehs_lat_aux** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['tuple']`: (array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796]), array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]))

### Docstring template

```
PARAMETERS
----------

:param Af:
:type Af: float64

:param Ll:
:type Ll: float64

:param Lw:
:type Lw: float64

:param Mww:
:type Mww: ndarray

:param Qcsf:
:type Qcsf: ndarray

:param Qcsf_0:
:type Qcsf_0: float64

:param Qhsf:
:type Qhsf: ndarray

:param Qhsf_0:
:type Qhsf_0: float64

:param Qww:
:type Qww: ndarray

:param Qwwf:
:type Qwwf: ndarray

:param Qwwf_0:
:type Qwwf_0: float64

:param Tcs_re:
:type Tcs_re: ndarray

:param Tcs_sup:
:type Tcs_sup: ndarray

:param Ths_re:
:type Ths_re: ndarray

:param Ths_sup:
:type Ths_sup: ndarray

:param Vw:
:type Vw: ndarray

:param Year:
:type Year: int64

:param fforma:
:type fforma: float64

:param gv:
:type gv: GlobalVariables

:param nf_ag:
:type nf_ag: float64

:param nfp:
:type nfp: float64

:param qv_req:
:type qv_req: ndarray

:param sys_e_cooling:
:type sys_e_cooling: unicode

:param sys_e_heating:
:type sys_e_heating: unicode

:param Ehs_lat_aux:
:type Ehs_lat_aux: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Eauxf_cs_dis
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **Qcsf** `['float64']`: *-0*
- **Qcsf0** `['float64']`: *-281104.46918348083*
- **Imax** `['float64']`: *88.705510978710478*
- **deltaP_des** `['float64']`: *11.531716427232364*
- **b** `['float64']`: *1.2*
- **ts** `['int32']`: *0*
- **tr** `['int32']`: *0*
- **cpw** `['float64']`: *4.1840000000000002*


### Output
- `['float']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param Qcsf:
:type Qcsf: float64

:param Qcsf0:
:type Qcsf0: float64

:param Imax:
:type Imax: float64

:param deltaP_des:
:type deltaP_des: float64

:param b:
:type b: float64

:param ts:
:type ts: int32

:param tr:
:type tr: int32

:param cpw:
:type cpw: float64

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# calc_Eauxf_fw
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **freshw** `['ndarray']`: *array([ 0.00874946,  0.00437473,  0.00109368, ...,  0.0369118 ,
        0.02050655,  0.01558498])*
- **nf** `['float64']`: *7.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C2CC4B0>*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param freshw:
:type freshw: ndarray

:param nf:
:type nf: float64

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eauxf_hs_dis
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **Qhsf** `['float64']`: *0.0*
- **Qhsf0** `['float64']`: *296485.76361481688*
- **Imax** `['float64']`: *88.705510978710478*
- **deltaP_des** `['float64']`: *11.531716427232364*
- **b** `['float64']`: *1.2*
- **ts** `['int32']`: *0*
- **tr** `['int32']`: *0*
- **cpw** `['float64']`: *4.1840000000000002*


### Output
- `['float']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param Qhsf:
:type Qhsf: float64

:param Qhsf0:
:type Qhsf0: float64

:param Imax:
:type Imax: float64

:param deltaP_des:
:type deltaP_des: float64

:param b:
:type b: float64

:param ts:
:type ts: int32

:param tr:
:type tr: int32

:param cpw:
:type cpw: float64

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# calc_Eauxf_ve
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Qhsf** `['float64']`: *0.0*
- **Qcsf** `['float64']`: *-0*
- **P_ve** `['float64']`: *0.55000000000000004*
- **qve** `['float64']`: *1.1694485063119631*
- **SystemH** `['unicode_']`: *u'T1'*
- **SystemC** `['unicode_']`: *u'T3'*


### Output
- `['float']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param Qhsf:
:type Qhsf: float64

:param Qcsf:
:type Qcsf: float64

:param P_ve:
:type P_ve: float64

:param qve:
:type qve: float64

:param SystemH:
:type SystemH: unicode_

:param SystemC:
:type SystemC: unicode_

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# calc_Eauxf_ww
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **Qww** `['float64']`: *0.0*
- **Qwwf** `['float64']`: *9.7353308233326086*
- **Qwwf0** `['float64']`: *5419.7627526345404*
- **Imax** `['float64']`: *88.705510978710478*
- **deltaP_des** `['float64']`: *11.531716427232364*
- **b** `['float64']`: *1.2*
- **qV_des** `['float64']`: *0.0*


### Output
- `['float']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param Qww:
:type Qww: float64

:param Qwwf:
:type Qwwf: float64

:param Qwwf0:
:type Qwwf0: float64

:param Imax:
:type Imax: float64

:param deltaP_des:
:type deltaP_des: float64

:param b:
:type b: float64

:param qV_des:
:type qV_des: float64

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# calc_Edataf
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

### Input
- **schedule** `['ndarray']`: *array([ 0.08,  0.08,  0.08, ...,  0.06,  0.06,  0.06])*
- **Ed_Wm2** `['float64']`: *0.0*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: ndarray

:param Ed_Wm2:
:type Ed_Wm2: float64

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eint
- number of invocations: 1
- max duration: 1.907 s
- avg duration: 1.907 s
- min duration: 1.907 s
- total duration: 1.907 s

### Input
- **tsd** `['dict']`: *{'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Tww_re': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Tm': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Qcs_sen_incl_em_ls': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_re_cs'*
- **prop_internal_loads** `['dict']`: *{u'El_Wm2': 15.9, u'Qs_Wp': 70.0, u'Ed_Wm2': 0.0, u'Ea_Wm2': 7.0, u'Ere_Wm2': 0.0, u'Epro_Wm2': 0.0, u'Vww_lpd': 10.0, u'Vw_lpd': 20.0, u'X_ghp': 80.0}*
- **Af** `['float64']`: *2171.2396513531003*
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 1.0, u'GYM': 0.0, u'HOTEL': 0.0, u'PFloor': 1.0, u'PARKING': 0.0, u'MULTI_RES': 0.0, u'RETAIL': 0.0, u'HOSPITAL': 0.0}*


### Output
- `['dict']`: {'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Tww_re': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ealf': array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096]), 'Tm': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), '

### Docstring template

```
PARAMETERS
----------

:param tsd:
:type tsd: dict

:param prop_internal_loads:
:type prop_internal_loads: dict

:param Af:
:type Af: float64

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: dict

RETURNS
-------

:returns:
:rtype: dict

```

[TOC](#table-of-contents)
---

# calc_Elf
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **schedule** `['ndarray']`: *array([ 0.08,  0.08,  0.08, ...,  0.06,  0.06,  0.06])*
- **El_Wm2** `['float64']`: *15.9*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['ndarray']`: array([ 2761.81683652,  2761.81683652,  2761.81683652, ...,  2071.36262739,
        2071.36262739,  2071.36262739])

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: ndarray

:param El_Wm2:
:type El_Wm2: float64

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eprof
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **schedule** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Epro_Wm2** `['float64']`: *0.0*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: ndarray

:param Epro_Wm2:
:type Epro_Wm2: float64

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eprof_schedule
- number of invocations: 1
- max duration: 0.531 s
- avg duration: 0.531 s
- min duration: 0.531 s
- total duration: 0.531 s

### Input
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 1.0, u'GYM': 0.0, u'HOTEL': 0.0, u'PFloor': 1.0, u'PARKING': 0.0, u'MULTI_RES': 0.0, u'RETAIL': 0.0, u'HOSPITAL': 0.0}*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: dict

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eref
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **schedule** `['ndarray']`: *array([ 0.08,  0.08,  0.08, ...,  0.06,  0.06,  0.06])*
- **Ere_Wm2** `['float64']`: *0.0*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: ndarray

:param Ere_Wm2:
:type Ere_Wm2: float64

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Htr
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Hve** `['float64']`: *1414.5649132349504*
- **Htr_is** `['float64']`: *15748.652178585824*
- **Htr_ms** `['float64']`: *63226.498647402281*
- **Htr_w** `['float64']`: *1403.3742289273969*


### Output
- `['tuple']`: (1297.9787346036153, 2701.3529635310124, 2590.6666958115343)

### Docstring template

```
PARAMETERS
----------

:param Hve:
:type Hve: float64

:param Htr_is:
:type Htr_is: float64

:param Htr_ms:
:type Htr_ms: float64

:param Htr_w:
:type Htr_w: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_I_sol
- number of invocations: 1
- max duration: 0.079 s
- avg duration: 0.079 s
- min duration: 0.079 s
- total duration: 0.079 s

### Input
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x0C2C0830>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0CA6BB10>*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param bpr:
:type bpr: BuildingPropertiesRow

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Qgain_lat
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **people** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **X_ghp** `['float64']`: *80.0*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param people:
:type people: ndarray

:param X_ghp:
:type X_ghp: float64

:param sys_e_cooling:
:type sys_e_cooling: unicode

:param sys_e_heating:
:type sys_e_heating: unicode

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Qgain_sen
- number of invocations: 1
- max duration: 0.205 s
- avg duration: 0.205 s
- min duration: 0.205 s
- total duration: 0.205 s

### Input
- **people** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qs_Wp** `['float64']`: *70.0*
- **Eal_nove** `['ndarray']`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcdata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **tsd** `['dict']`: *{'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Elf': array([ 2761.81683652,  2761.81683652,  2761.81683652, ...,  2071.36262739,
        2071.36262739,  2071.36262739]), 'Ealf': array([ 3977.71104128,  3977.71104128,  3977.711*
- **Am** `['float64']`: *6947.9668843299214*
- **Atot** `['float64']`: *4564.8267184306733*
- **Htr_w** `['float64']`: *1403.3742289273969*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x0C204F70>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BEF75F0>*


### Output
- `['dict']`: {'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Elf': array([ 2761.81683652,  2761.81683652,  2761.81683652, ...,  2071.36262739,
        2071.36262739,  2071.36262739]), 'I_st': array([-994.95409443, -994.95409443, -994.954094

### Docstring template

```
PARAMETERS
----------

:param people:
:type people: ndarray

:param Qs_Wp:
:type Qs_Wp: float64

:param Eal_nove:
:type Eal_nove: ndarray

:param Eprof:
:type Eprof: ndarray

:param Qcdata:
:type Qcdata: ndarray

:param Qcrefri:
:type Qcrefri: ndarray

:param tsd:
:type tsd: dict

:param Am:
:type Am: float64

:param Atot:
:type Atot: float64

:param Htr_w:
:type Htr_w: float64

:param bpr:
:type bpr: BuildingPropertiesRow

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: dict

```

[TOC](#table-of-contents)
---

# calc_Qhs_Qcs
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

### Input
- **SystemH** `['unicode']`: *u'T1'*
- **SystemC** `['unicode']`: *u'T3'*
- **tm_t0** `['int']`: *16*
- **te_t** `['float64']`: *8.8000000000000007*
- **tintH_set** `['float64']`: *12.0*
- **tintC_set** `['int32']`: *50*
- **Htr_em** `['float64']`: *582.9963349687813*
- **Htr_ms** `['float64']`: *63226.498647402281*
- **Htr_is** `['float64']`: *15748.652178585824*
- **Htr_1** `['float64']`: *1297.9787346036153*
- **Htr_2** `['float64']`: *2701.3529635310124*
- **Htr_3** `['float64']`: *2590.6666958115343*
- **I_st** `['float64']`: *-994.95409442637424*
- **Hve** `['float64']`: *1414.5649132349504*
- **Htr_w** `['float64']`: *1403.3742289273969*
- **I_ia** `['float64']`: *1789.9699685754963*
- **I_m** `['float64']`: *2724.4521715126953*
- **Cm** `['float64']`: *651371895.40593004*
- **Af** `['float64']`: *2171.2396513531003*
- **Losses** `['bool']`: *False*
- **tHset_corr** `['float']`: *2.65*
- **tCset_corr** `['float']`: *-2.0*
- **IC_max** `['float64']`: *-1085619.8256765502*
- **IH_max** `['float64']`: *1085619.8256765502*
- **Flag** `['bool_']`: *False*


### Output
- `['tuple']`: (15.946568617146644, 15.202170683665049, 0, 0, 0, 15.520531773681475, 31273.645775067431)

### Docstring template

```
PARAMETERS
----------

:param SystemH:
:type SystemH: unicode

:param SystemC:
:type SystemC: unicode

:param tm_t0:
:type tm_t0: int

:param te_t:
:type te_t: float64

:param tintH_set:
:type tintH_set: float64

:param tintC_set:
:type tintC_set: int32

:param Htr_em:
:type Htr_em: float64

:param Htr_ms:
:type Htr_ms: float64

:param Htr_is:
:type Htr_is: float64

:param Htr_1:
:type Htr_1: float64

:param Htr_2:
:type Htr_2: float64

:param Htr_3:
:type Htr_3: float64

:param I_st:
:type I_st: float64

:param Hve:
:type Hve: float64

:param Htr_w:
:type Htr_w: float64

:param I_ia:
:type I_ia: float64

:param I_m:
:type I_m: float64

:param Cm:
:type Cm: float64

:param Af:
:type Af: float64

:param Losses:
:type Losses: bool

:param tHset_corr:
:type tHset_corr: float

:param tCset_corr:
:type tCset_corr: float

:param IC_max:
:type IC_max: float64

:param IH_max:
:type IH_max: float64

:param Flag:
:type Flag: bool_

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Qhs_Qcs_dis_ls
- number of invocations: 1
- max duration: 0.04 s
- avg duration: 0.04 s
- min duration: 0.04 s
- total duration: 0.04 s

### Input
- **tair** `['float64']`: *15.202170683665049*
- **text** `['float64']`: *8.8000000000000007*
- **Qhs** `['float64']`: *0.0*
- **Qcs** `['float64']`: *0.0*
- **tsh** `['int64']`: *90*
- **trh** `['int64']`: *70*
- **tsc** `['int64']`: *7*
- **trc** `['int64']`: *15*
- **Qhs_max** `['float64']`: *294916.76361481688*
- **Qcs_max** `['float64']`: *-152740.15924554263*
- **D** `['int32']`: *20*
- **Y** `['float64']`: *0.29999999999999999*
- **SystemH** `['unicode_']`: *u'T1'*
- **SystemC** `['unicode_']`: *u'T3'*
- **Bf** `['float64']`: *0.69999999999999996*
- **Lv** `['float64']`: *67.916762127496582*


### Output
- `['tuple']`: (0, 0)

### Docstring template

```
PARAMETERS
----------

:param tair:
:type tair: float64

:param text:
:type text: float64

:param Qhs:
:type Qhs: float64

:param Qcs:
:type Qcs: float64

:param tsh:
:type tsh: int64

:param trh:
:type trh: int64

:param tsc:
:type tsc: int64

:param trc:
:type trc: int64

:param Qhs_max:
:type Qhs_max: float64

:param Qcs_max:
:type Qcs_max: float64

:param D:
:type D: int32

:param Y:
:type Y: float64

:param SystemH:
:type SystemH: unicode_

:param SystemC:
:type SystemC: unicode_

:param Bf:
:type Bf: float64

:param Lv:
:type Lv: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Qhs_Qcs_sys_max
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **Af** `['float64']`: *2171.2396513531003*
- **prop_HVAC** `['dict']`: *{u'Qcsmax_Wm2': 500, u'dTcs0_C': 8, u'type_ctrl': u'T1', u'type_cs': u'T3', u'dThs0_C': 20, u'Qhsmax_Wm2': 500, u'Tscs0_C': 7, u'type_hs': u'T1', u'Tsww0_C': 60, u'Qwwmax_Wm2': 500, u'dTww0_C': 50, u'Tshs0_C': 90, u'type_dhw': u'T1'}*


### Output
- `['tuple']`: (-1085619.8256765502, 1085619.8256765502)

### Docstring template

```
PARAMETERS
----------

:param Af:
:type Af: float64

:param prop_HVAC:
:type prop_HVAC: dict

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Qww
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **mww** `['float64']`: *0.0*
- **Tww_sup_0** `['int64']`: *60*
- **Tww_re** `['float64']`: *10.0*
- **Cpw** `['float64']`: *4.1840000000000002*


### Output
- `['float64']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param mww:
:type mww: float64

:param Tww_sup_0:
:type Tww_sup_0: int64

:param Tww_re:
:type Tww_re: float64

:param Cpw:
:type Cpw: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_Qww_dis_ls_nr
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **tair** `['float64']`: *15.202170683665049*
- **Qww** `['float64']`: *0.0*
- **Lvww_dis** `['float64']`: *50.246706155723558*
- **Lvww_c** `['float64']`: *55.259252908257515*
- **Y** `['float64']`: *0.29999999999999999*
- **Qww_0** `['float64']`: *2998.114341223164*
- **V** `['float64']`: *81.45987041393002*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **Bf** `['float64']`: *0.69999999999999996*
- **te** `['float64']`: *8.8000000000000007*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0D0092F0>*


### Output
- `['float64']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param tair:
:type tair: float64

:param Qww:
:type Qww: float64

:param Lvww_dis:
:type Lvww_dis: float64

:param Lvww_c:
:type Lvww_c: float64

:param Y:
:type Y: float64

:param Qww_0:
:type Qww_0: float64

:param V:
:type V: float64

:param Flowtap:
:type Flowtap: float64

:param twws:
:type twws: int64

:param Cpw:
:type Cpw: float64

:param Pwater:
:type Pwater: int32

:param Bf:
:type Bf: float64

:param te:
:type te: float64

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_Qww_dis_ls_r
- number of invocations: 1
- max duration: 0.086 s
- avg duration: 0.086 s
- min duration: 0.086 s
- total duration: 0.086 s

### Input
- **Tair** `['float64']`: *15.202170683665049*
- **Qww** `['float64']`: *0.0*
- **lsww_dis** `['float64']`: *183.34912611426176*
- **lcww_dis** `['float64']`: *72.543326121114177*
- **Y** `['float64']`: *0.40000000000000002*
- **Qww_0** `['float64']`: *2998.114341223164*
- **V** `['float64']`: *81.45987041393002*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0559B870>*


### Output
- `['float64']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param Tair:
:type Tair: float64

:param Qww:
:type Qww: float64

:param lsww_dis:
:type lsww_dis: float64

:param lcww_dis:
:type lcww_dis: float64

:param Y:
:type Y: float64

:param Qww_0:
:type Qww_0: float64

:param V:
:type V: float64

:param Flowtap:
:type Flowtap: float64

:param twws:
:type twws: int64

:param Cpw:
:type Cpw: float64

:param Pwater:
:type Pwater: int32

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_Qww_schedule
- number of invocations: 1
- max duration: 0.481 s
- avg duration: 0.481 s
- min duration: 0.481 s
- total duration: 0.481 s

### Input
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 1.0, u'GYM': 0.0, u'HOTEL': 0.0, u'PFloor': 1.0, u'PARKING': 0.0, u'MULTI_RES': 0.0, u'RETAIL': 0.0, u'HOSPITAL': 0.0}*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: dict

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Qww_st_ls
- number of invocations: 1
- max duration: 0.389 s
- avg duration: 0.389 s
- min duration: 0.389 s
- total duration: 0.389 s

### Input
- **Vww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Tww_setpoint** `['int']`: *60*
- **Ta** `['ndarray']`: *array([ 15.20217068,  15.13002744,  15.05677264, ...,  12.        ,
        12.        ,  12.        ])*
- **Bf** `['float']`: *0.7*
- **Pwater** `['int']`: *998*
- **Cpw** `['float']`: *4.184*
- **Qww_dis_ls_r** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qww_dis_ls_nr** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **U_dhwtank** `['float']`: *0.225*
- **AR** `['float']`: *3.3*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C12D390>*
- **T_ext** `['ndarray']`: *array([ 8.8,  8.6,  8.4, ..., -0.3, -0.5, -0.7])*
- **Qww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['tuple']`: (array([  9.73533082,   9.75835448,   9.78142295, ...,  11.14941905,
        11.16687292,  11.18431081]), array([ 59.95490068,  59.9096947 ,  59.86438185, ...,  59.77568316,
        59.72395215,  59.67214037]))

### Docstring template

```
PARAMETERS
----------

:param Vww:
:type Vww: ndarray

:param Tww_setpoint:
:type Tww_setpoint: int

:param Ta:
:type Ta: ndarray

:param Bf:
:type Bf: float

:param Pwater:
:type Pwater: int

:param Cpw:
:type Cpw: float

:param Qww_dis_ls_r:
:type Qww_dis_ls_r: ndarray

:param Qww_dis_ls_nr:
:type Qww_dis_ls_nr: ndarray

:param U_dhwtank:
:type U_dhwtank: float

:param AR:
:type AR: float

:param gv:
:type gv: GlobalVariables

:param T_ext:
:type T_ext: ndarray

:param Qww:
:type Qww: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Qwwf
- number of invocations: 1
- max duration: 1.803 s
- avg duration: 1.803 s
- min duration: 1.803 s
- total duration: 1.803 s

### Input
- **Af** `['float64']`: *2171.2396513531003*
- **Lcww_dis** `['float64']`: *72.543326121114177*
- **Lsww_dis** `['float64']`: *183.34912611426176*
- **Lvww_c** `['float64']`: *55.259252908257515*
- **Lvww_dis** `['float64']`: *50.246706155723558*
- **T_ext** `['ndarray']`: *array([ 8.8,  8.6,  8.4, ..., -0.3, -0.5, -0.7])*
- **Ta** `['ndarray']`: *array([ 15.20217068,  15.13002744,  15.05677264, ...,  12.        ,
        12.        ,  12.        ])*
- **Tww_re** `['ndarray']`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_sup_0** `['int64']`: *60*
- **Y** `['list']`: *[0.3, 0.4, 0.4]*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C2B0410>*
- **Vww_lpd** `['float64']`: *10.0*
- **Vw_lpd** `['float64']`: *10.0*
- **Occ_m2p** `['float64']`: *14.0*
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 1.0, u'GYM': 0.0, u'HOTEL': 0.0, u'PFloor': 1.0, u'PARKING': 0.0, u'MULTI_RES': 0.0, u'RETAIL': 0.0, u'HOSPITAL': 0.0}*


### Output
- `['tuple']`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([  9.73533082,   9.75835448,   9.78142295, ...,  11.14941905,
        11.16687292,  11.18431081]), array([  9.73533082,   9.75835448,   9.78142295, ...,  11.14941905,
        11.16687292,  11.18431081]), 5419.7627526345404, array([ 59.95490068,  59.9096947 ,  59.86438185, ...,  59.77568316,
        59.72395215,  59.67214037]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0., 

### Docstring template

```
PARAMETERS
----------

:param Af:
:type Af: float64

:param Lcww_dis:
:type Lcww_dis: float64

:param Lsww_dis:
:type Lsww_dis: float64

:param Lvww_c:
:type Lvww_c: float64

:param Lvww_dis:
:type Lvww_dis: float64

:param T_ext:
:type T_ext: ndarray

:param Ta:
:type Ta: ndarray

:param Tww_re:
:type Tww_re: ndarray

:param Tww_sup_0:
:type Tww_sup_0: int64

:param Y:
:type Y: list

:param gv:
:type gv: GlobalVariables

:param Vww_lpd:
:type Vww_lpd: float64

:param Vw_lpd:
:type Vw_lpd: float64

:param Occ_m2p:
:type Occ_m2p: float64

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: dict

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_T_em_ls
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **SystemH** `['unicode']`: *u'T1'*
- **SystemC** `['unicode']`: *u'T3'*
- **sys_e_ctrl** `['unicode']`: *u'T1'*


### Output
- `['tuple']`: (2.65, -2.0)

### Docstring template

```
PARAMETERS
----------

:param SystemH:
:type SystemH: unicode

:param SystemC:
:type SystemC: unicode

:param sys_e_ctrl:
:type sys_e_ctrl: unicode

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_coeff_lea_zone
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **qv_delta_p_lea_ref** `['float64']`: *28949.862018041335*


### Output
- `['float64']`: 2130.2643780536373

### Docstring template

```
PARAMETERS
----------

:param qv_delta_p_lea_ref:
:type qv_delta_p_lea_ref: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_coeff_vent_zone
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **area_vent_zone** `['int']`: *0*


### Output
- `['float']`: 0.0

### Docstring template

```
PARAMETERS
----------

:param area_vent_zone:
:type area_vent_zone: int

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# calc_disls
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **tamb** `['float64']`: *15.202170683665049*
- **hotw** `['float64']`: *0.0*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **V** `['float64']`: *81.45987041393002*
- **twws** `['int64']`: *60*
- **Lsww_dis** `['float64']`: *183.34912611426176*
- **p** `['int32']`: *998*
- **cpw** `['float64']`: *4.1840000000000002*
- **Y** `['float64']`: *0.40000000000000002*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C2B01F0>*


### Output
- `['int']`: 0

### Docstring template

```
PARAMETERS
----------

:param tamb:
:type tamb: float64

:param hotw:
:type hotw: float64

:param Flowtap:
:type Flowtap: float64

:param V:
:type V: float64

:param twws:
:type twws: int64

:param Lsww_dis:
:type Lsww_dis: float64

:param p:
:type p: int32

:param cpw:
:type cpw: float64

:param Y:
:type Y: float64

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: int

```

[TOC](#table-of-contents)
---

# calc_h
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **t** `['int32']`: *24*
- **w** `['float64']`: *0.0090625183347139426*


### Output
- `['float64']`: 47.207559164780534

### Docstring template

```
PARAMETERS
----------

:param t:
:type t: int32

:param w:
:type w: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_h_ve_adj
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **q_m_mech** `['float64']`: *1.4033382075743557*
- **q_m_nat** `['int']`: *0*
- **temp_ext** `['float64']`: *8.8000000000000007*
- **temp_sup** `['float64']`: *8.8000000000000007*
- **temp_zone_set** `['int']`: *21*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C2B0710>*


### Output
- `['float64']`: 1414.5649132349504

### Docstring template

```
PARAMETERS
----------

:param q_m_mech:
:type q_m_mech: float64

:param q_m_nat:
:type q_m_nat: int

:param temp_ext:
:type temp_ext: float64

:param temp_sup:
:type temp_sup: float64

:param temp_zone_set:
:type temp_zone_set: int

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_hex
- number of invocations: 1
- max duration: 0.099 s
- avg duration: 0.099 s
- min duration: 0.099 s
- total duration: 0.099 s

### Input
- **rel_humidity_ext** `['int64']`: *73*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C12D710>*
- **temp_ext** `['float64']`: *8.1999999999999993*
- **temp_zone_prev** `['float64']`: *18.759995042815788*
- **timestep** `['int']`: *3217*


### Output
- `['tuple']`: (8.1999999999999993, 0.0049493200522193461)

### Docstring template

```
PARAMETERS
----------

:param rel_humidity_ext:
:type rel_humidity_ext: int64

:param gv:
:type gv: GlobalVariables

:param temp_ext:
:type temp_ext: float64

:param temp_zone_prev:
:type temp_zone_prev: float64

:param timestep:
:type timestep: int

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_hvac
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **rhum_1** `['int64']`: *73*
- **temp_1** `['float64']`: *8.1999999999999993*
- **temp_zone_set** `['float64']`: *18.639283464540256*
- **qv_req** `['float64']`: *1.1694485063119631*
- **qe_sen** `['int']`: *0*
- **temp_5_prev** `['float64']`: *18.759995042815788*
- **wint** `['float64']`: *0.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C967510>*
- **timestep** `['int']`: *3217*


### Output
- `['tuple']`: (0, 0, 0, 0, 0, 0, 0, nan, nan, 8.1999999999999993, 8.1999999999999993, 0, 0, 18.639283464540256)

### Docstring template

```
PARAMETERS
----------

:param rhum_1:
:type rhum_1: int64

:param temp_1:
:type temp_1: float64

:param temp_zone_set:
:type temp_zone_set: float64

:param qv_req:
:type qv_req: float64

:param qe_sen:
:type qe_sen: int

:param temp_5_prev:
:type temp_5_prev: float64

:param wint:
:type wint: float64

:param gv:
:type gv: GlobalVariables

:param timestep:
:type timestep: int

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_mww
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **schedule** `['float64']`: *0.0*
- **Vww_lpd** `['float64']`: *10.0*
- **Occ_m2p** `['float64']`: *14.0*
- **Af** `['float64']`: *2171.2396513531003*
- **Pwater** `['int32']`: *998*


### Output
- `['tuple']`: (0.0, 0.0)

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: float64

:param Vww_lpd:
:type Vww_lpd: float64

:param Occ_m2p:
:type Occ_m2p: float64

:param Af:
:type Af: float64

:param Pwater:
:type Pwater: int32

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_occ
- number of invocations: 1
- max duration: 1.042 s
- avg duration: 1.042 s
- min duration: 1.042 s
- total duration: 1.042 s

### Input
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 1.0, u'GYM': 0.0, u'HOTEL': 0.0, u'PFloor': 1.0, u'PARKING': 0.0, u'MULTI_RES': 0.0, u'RETAIL': 0.0, u'HOSPITAL': 0.0}*
- **Occ_m2p** `['float64']`: *14.0*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: dict

:param Occ_m2p:
:type Occ_m2p: float64

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_occ_schedule
- number of invocations: 1
- max duration: 0.508 s
- avg duration: 0.508 s
- min duration: 0.508 s
- total duration: 0.508 s

### Input
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 1.0, u'GYM': 0.0, u'HOTEL': 0.0, u'PFloor': 1.0, u'PARKING': 0.0, u'MULTI_RES': 0.0, u'RETAIL': 0.0, u'HOSPITAL': 0.0}*


### Output
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: dict

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_qv_delta_p_ref
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **n_delta_p_ref** `['int64']`: *6*
- **vol_building** `['float64']`: *4824.9770030068894*


### Output
- `['float64']`: 28949.862018041335

### Docstring template

```
PARAMETERS
----------

:param n_delta_p_ref:
:type n_delta_p_ref: int64

:param vol_building:
:type vol_building: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_temperatures_emission_systems
- number of invocations: 1
- max duration: 0.602 s
- avg duration: 0.602 s
- min duration: 0.602 s
- total duration: 0.602 s

### Input
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-281104.46918348083*
- **Qhsf** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        93991.5268617 ,  94591.45409877,  95210.96830999])*
- **Qhsf_0** `['float64']`: *296485.76361481688*
- **Ta** `['ndarray']`: *array([ 15.20217068,  15.13002744,  15.05677264, ...,  12.        ,
        12.        ,  12.        ])*
- **Ta_re_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_re_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Tcs_re_0** `['int64']`: *15*
- **Tcs_sup_0** `['int64']`: *7*
- **Ths_re_0** `['int64']`: *70*
- **Ths_sup_0** `['int64']`: *90*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0564ABF0>*
- **ma_sup_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **ma_sup_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **ta_hs_set** `['ndarray']`: *array([ 12.,  12.,  12., ...,  12.,  12.,  12.])*


### Output
- `['tuple']`: (array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]), array([ 0,  0,  0, ..., 32, 32, 32]), array([ 0,  0,  0, ..., 39, 39, 39]), array([0, 0, 0, ..., 0, 0, 0]), array([ 0,  0,  0, ..., 14, 14, 14]))

### Docstring template

```
PARAMETERS
----------

:param Qcsf:
:type Qcsf: ndarray

:param Qcsf_0:
:type Qcsf_0: float64

:param Qhsf:
:type Qhsf: ndarray

:param Qhsf_0:
:type Qhsf_0: float64

:param Ta:
:type Ta: ndarray

:param Ta_re_cs:
:type Ta_re_cs: ndarray

:param Ta_re_hs:
:type Ta_re_hs: ndarray

:param Ta_sup_cs:
:type Ta_sup_cs: ndarray

:param Ta_sup_hs:
:type Ta_sup_hs: ndarray

:param Tcs_re_0:
:type Tcs_re_0: int64

:param Tcs_sup_0:
:type Tcs_sup_0: int64

:param Ths_re_0:
:type Ths_re_0: int64

:param Ths_sup_0:
:type Ths_sup_0: int64

:param gv:
:type gv: GlobalVariables

:param ma_sup_cs:
:type ma_sup_cs: ndarray

:param ma_sup_hs:
:type ma_sup_hs: ndarray

:param sys_e_cooling:
:type sys_e_cooling: unicode

:param sys_e_heating:
:type sys_e_heating: unicode

:param ta_hs_set:
:type ta_hs_set: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_thermal_load_hvac_timestep
- number of invocations: 1
- max duration: 0.294 s
- avg duration: 0.294 s
- min duration: 0.294 s
- total duration: 0.294 s

### Input
- **t** `['int']`: *3217*
- **tsd** `['dict']`: *{'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 31273.64577507,  30638.91316891,  30004.18056276, ...,
            0.        ,      0.        ,      0.        ]), 've': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 15.52053177,  15.45631268,  15.39091312, ...,   0.        ,
         0.        ,   0.        ]), 'Elf': array([ 2761.81683652,  2761.8168*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x0C9672D0>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0CA6BB10>*


### Output
- `['dict']`: {'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 31273.64577507,  30638.91316891,  30004.18056276, ...,
            0.        ,      0.        ,      0.        ]), 've': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 15.52053177,  15.45631268,  15.39091312, ...,   0.        ,
         0.        ,   0.        ]), 'Elf': array([ 2761.81683652,  2761.8168

### Docstring template

```
PARAMETERS
----------

:param t:
:type t: int

:param tsd:
:type tsd: dict

:param bpr:
:type bpr: BuildingPropertiesRow

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: dict

```

[TOC](#table-of-contents)
---

# calc_thermal_load_mechanical_and_natural_ventilation_timestep
- number of invocations: 1
- max duration: 0.374 s
- avg duration: 0.374 s
- min duration: 0.374 s
- total duration: 0.374 s

### Input
- **t** `['int']`: *0*
- **tsd** `['dict']`: *{'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Elf': array([ 2761.81683652,  2761.81683652,  2761.81683652, ...,  2071.36262739,
        2071.36262739,  2071.36262739]), 'I_st': array([-994.95409443, -994.95409443, -994.954094*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x0C9D83F0>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C12AD70>*


### Output
- `['dict']`: {'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 31273.64577507,      0.        ,      0.        , ...,
            0.        ,      0.        ,      0.        ]), 've': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 15.52053177,   0.        ,   0.        , ...,   0.        ,
         0.        ,   0.        ]), 'Elf': array([ 2761.81683652,  2761.8168

### Docstring template

```
PARAMETERS
----------

:param t:
:type t: int

:param tsd:
:type tsd: dict

:param bpr:
:type bpr: BuildingPropertiesRow

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: dict

```

[TOC](#table-of-contents)
---

# calc_thermal_loads
- number of invocations: 1
- max duration: 10.009 s
- avg duration: 10.009 s
- min duration: 10.009 s
- total duration: 10.009 s

### Input
- **building_name** `['str']`: *'B153767'*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x0C22D330>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **usage_schedules** `['dict']`: *{'list_uses': [u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL'], 'schedules': [([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4,*
- **date** `['DatetimeIndex']`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C2B01F0>*
- **results_folder** `['str']`: *'c:\\reference-case\\baseline\\outputs\\data\\demand'*
- **temporary_folder** `['str']`: *'c:\\users\\darthoma\\appdata\\local\\temp'*

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
- `['NoneType']`: None

### Docstring template

```
PARAMETERS
----------

:param building_name:
:type building_name: str

:param bpr:
:type bpr: BuildingPropertiesRow

:param weather_data:
:type weather_data: DataFrame

:param usage_schedules:
:type usage_schedules: dict

:param date:
:type date: DatetimeIndex

:param gv:
:type gv: GlobalVariables

:param results_folder:
:type results_folder: str

:param temporary_folder:
:type temporary_folder: str

RETURNS
-------

:returns:
:rtype: NoneType

```

[TOC](#table-of-contents)
---

# calc_w
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **t** `['float64']`: *8.1999999999999993*
- **RH** `['int64']`: *73*


### Output
- `['float64']`: 0.0049493200522193461

### Docstring template

```
PARAMETERS
----------

:param t:
:type t: float64

:param RH:
:type RH: int64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_w3_cooling_case
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **t5** `['int32']`: *24*
- **w2** `['float64']`: *0.0090625183347139426*
- **t3** `['int']`: *16*
- **w5** `['float64']`: *0.0094873786628507113*


### Output
- `['float64']`: 0.0090625183347139426

### Docstring template

```
PARAMETERS
----------

:param t5:
:type t5: int32

:param w2:
:type w2: float64

:param t3:
:type t3: int

:param w5:
:type w5: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_w3_heating_case
- number of invocations: 1
- max duration: 0.041 s
- avg duration: 0.041 s
- min duration: 0.041 s
- total duration: 0.041 s

### Input
- **t5** `['float64']`: *20.0*
- **w2** `['float64']`: *0.0041699403233700994*
- **w5** `['float64']`: *0.0045258958486444414*
- **t3** `['int']`: *36*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0CFFB590>*


### Output
- `['float64']`: 0.0041699403233700994

### Docstring template

```
PARAMETERS
----------

:param t5:
:type t5: float64

:param w2:
:type w2: float64

:param w5:
:type w5: float64

:param t3:
:type t3: int

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# demand_calculation
- number of invocations: 1
- max duration: 812.509 s
- avg duration: 812.509 s
- min duration: 812.509 s
- total duration: 812.509 s

### Input
- **locator** `['InputLocator']`: *<cea.inputlocator.InputLocator object at 0x0C135370>*
- **weather_path** `['str']`: *'C:\\Users\\darthoma\\Documents\\GitHub\\CEAforArcGIS\\cea\\databases\\CH\\Weather\\Zurich.epw'*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C135370>*


### Output
- `['NoneType']`: None

### Docstring template

```
PARAMETERS
----------

:param locator:
:type locator: InputLocator

:param weather_path:
:type weather_path: str

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: NoneType

INPUT / OUTPUT FILES
--------------------

- get_radiation: c:\reference-case\baseline\outputs\data\solar-radiation\radiation.csv
- get_surface_properties: c:\reference-case\baseline\outputs\data\solar-radiation\properties_surfaces.csv
- get_building_geometry: c:\reference-case\baseline\inputs\building-geometry\zone.shp
- get_building_hvac: c:\reference-case\baseline\inputs\building-properties\technical_systems.shp
- get_building_thermal: c:\reference-case\baseline\inputs\building-properties\thermal_properties.shp
- get_building_occupancy: c:\reference-case\baseline\inputs\building-properties\occupancy.shp
- get_building_architecture: c:\reference-case\baseline\inputs\building-properties\architecture.shp
- get_building_age: c:\reference-case\baseline\inputs\building-properties\age.shp
- get_building_comfort: c:\reference-case\baseline\inputs\building-properties\indoor_comfort.shp
- get_building_internal: c:\reference-case\baseline\inputs\building-properties\internal_loads.shp
```

[TOC](#table-of-contents)
---

# get_building_geometry_ventilation
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **gdf_building_geometry** `['dict']`: *{'perimeter': 103.08389826411121, u'Blength': 32.648092418099999, u'height_bg': 6.0, u'floors_bg': 2.0, u'height_ag': 12.0, u'floors_ag': 4.0, u'Bwidth': 16.008581384100001, 'footprint': 402.0814169172408}*


### Output
- `['tuple']`: (1237.0067791693345, 402.0814169172408, 12.0, 0)

### Docstring template

```
PARAMETERS
----------

:param gdf_building_geometry:
:type gdf_building_geometry: dict

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# get_properties_natural_ventilation
- number of invocations: 1
- max duration: 0.428 s
- avg duration: 0.428 s
- min duration: 0.428 s
- total duration: 0.428 s

### Input
- **gdf_geometry_building** `['dict']`: *{'perimeter': 103.08389826411121, u'Blength': 32.648092418099999, u'height_bg': 6.0, u'floors_bg': 2.0, u'height_ag': 12.0, u'floors_ag': 4.0, u'Bwidth': 16.008581384100001, 'footprint': 402.0814169172408}*
- **gdf_architecture_building** `['dict']`: *{u'Occ_m2p': 14.0, u'f_cros': 0, u'n50': 6, u'win_op': 0.5, u'win_wall': 0.40000000000000002, u'type_shade': u'T1'}*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C135890>*


### Output
- `['dict']`: {'coeff_wind_pressure_path_vent': array([ 0.05, -0.05,  0.05, -0.05]), 'coeff_vent_path': array([ 0.,  0.,  0.,  0.]), 'height_vent_path': array([ 3.,  3.,  9.,  9.]), 'coeff_lea_path': array([ 401.92338084,  401.92338084,  401.92338084,  401.92338084,
        522.57085469]), 'factor_cros': 0, 'height_lea_path': array([  3.,   3.,   9.,   9.,  12.]), 'coeff_wind_pressure_path_lea': array([ 0.05, -0.05,  0.05, -0.05,  0.  ])}

### Docstring template

```
PARAMETERS
----------

:param gdf_geometry_building:
:type gdf_geometry_building: dict

:param gdf_architecture_building:
:type gdf_architecture_building: dict

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: dict

```

[TOC](#table-of-contents)
---

# get_temperatures
- number of invocations: 1
- max duration: 0.181 s
- avg duration: 0.181 s
- min duration: 0.181 s
- total duration: 0.181 s

### Input
- **locator** `['LocatorDecorator']`: *???*
- **prop_HVAC** `['GeoDataFrame']`: *(1482, 5)*

#### prop_HVAC:
```
              Name type_cs type_ctrl type_dhw type_hs
count         1482    1482      1482     1482    1482
unique        1482       2         3        2       5
top     B302034519      T0        T1       T1      T1
freq             1     988      1377     1403    1368

[4 rows x 5 columns]
```

### Output
- `['DataFrame']`: (1482, 14)

### Docstring template

```
PARAMETERS
----------

:param locator:
:type locator: LocatorDecorator

:param prop_HVAC:
:type prop_HVAC: GeoDataFrame

RETURNS
-------

:returns:
:rtype: DataFrame

INPUT / OUTPUT FILES
--------------------

- get_technical_emission_systems: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Systems\emission_systems.xls
- get_technical_emission_systems: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Systems\emission_systems.xls
- get_technical_emission_systems: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Systems\emission_systems.xls
```

[TOC](#table-of-contents)
---

# lookup_coeff_wind_pressure
- number of invocations: 1
- max duration: 0.041 s
- avg duration: 0.041 s
- min duration: 0.041 s
- total duration: 0.041 s

### Input
- **height_path** `['ndarray']`: *array([  3.,   3.,   9.,   9.,  12.])*
- **class_shielding** `['int']`: *2*
- **orientation_path** `['ndarray']`: *array([ 0.,  1.,  0.,  1.,  2.])*
- **slope_roof** `['int']`: *0*
- **factor_cros** `['int64']`: *0*


### Output
- `['ndarray']`: array([ 0.05, -0.05,  0.05, -0.05,  0.  ])

### Docstring template

```
PARAMETERS
----------

:param height_path:
:type height_path: ndarray

:param class_shielding:
:type class_shielding: int

:param orientation_path:
:type orientation_path: ndarray

:param slope_roof:
:type slope_roof: int

:param factor_cros:
:type factor_cros: int64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# read_schedules
- number of invocations: 1
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **use** `['unicode']`: *u'GYM'*
- **x** `['DataFrame']`: *(24, 41)*

#### x:
```
Index([nan, u'Weekday_1', u'Saturday_1', u'Sunday_1', nan, nan, nan, u'Weekday_2', u'Saturday_2', u'Sunday_2', nan, nan, nan, u'Weekday_3', u'Saturday_3', u'Sunday_3', nan, nan, nan, u'month', nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan], dtype='object')
```

### Output
- `['tuple']`: ([array([0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.8, 1.0, 1.0, 0.8, 0.0, 0.8,
       1.0, 1.0, 0.8, 0.5, 0.8, 0.8, 0.8, 0.5, 0.5, 0.0], dtype=object), array([0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.8, 1.0, 1.0, 0.8, 0.0, 0.8,
       1.0, 1.0, 0.8, 0.5, 0.8, 0.8, 0.8, 0.5, 0.5, 0.0], dtype=object), array([0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.8, 1.0, 1.0, 0.8, 0.0, 0.8,
       1.0, 1.0, 0.8, 0.5, 0.8, 0.8, 0.8, 0.5, 0.5, 0.0], dtype=object)], [array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.5, 0.8, 

### Docstring template

```
PARAMETERS
----------

:param use:
:type use: unicode

:param x:
:type x: DataFrame

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# results_to_csv
- number of invocations: 1
- max duration: 0.217 s
- avg duration: 0.217 s
- min duration: 0.217 s
- total duration: 0.217 s

### Input
- **GFA_m2** `['float64']`: *2412.4885015034447*
- **Af** `['float64']`: *2171.2396513531003*
- **Ealf** `['ndarray']`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Ealf_0** `['float64']`: *39777.110412788796*
- **Ealf_tot** `['float64']`: *90.946385247798304*
- **Eauxf** `['ndarray']`: *array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796])*
- **Eauxf_tot** `['float64']`: *2.0123670800422278*
- **Edata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Edata_tot** `['float64']`: *0.0*
- **Epro** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Epro_tot** `['float64']`: *0.0*
- **Name** `['str']`: *'B153767'*
- **Occupancy** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Occupants** `['float64']`: *124.0*
- **Qcdata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcs** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-281104.46918348083*
- **Qhs** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        57273.71555088,  57869.64278795,  58484.15699917])*
- **Qhsf** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        93991.5268617 ,  94591.45409877,  95210.96830999])*
- **Qhsf_0** `['float64']`: *296485.76361481688*
- **Qww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qww_ls_st** `['ndarray']`: *array([  9.73533082,   9.75835448,   9.78142295, ...,  11.14941905,
        11.16687292,  11.18431081])*
- **Qwwf** `['ndarray']`: *array([  9.73533082,   9.75835448,   9.78142295, ...,  11.14941905,
        11.16687292,  11.18431081])*
- **Qwwf_0** `['float64']`: *5419.7627526345404*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_re_0** `['int64']`: *15*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup_0** `['int64']`: *7*
- **Ths_re** `['ndarray']`: *array([ 0,  0,  0, ..., 32, 32, 32])*
- **Ths_re_0** `['int64']`: *70*
- **Ths_sup** `['ndarray']`: *array([ 0,  0,  0, ..., 39, 39, 39])*
- **Ths_sup_0** `['int64']`: *90*
- **Tww_re** `['ndarray']`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_st** `['ndarray']`: *array([ 59.95490068,  59.9096947 ,  59.86438185, ...,  59.77568316,
        59.72395215,  59.67214037])*
- **Tww_sup_0** `['int64']`: *60*
- **Waterconsumption** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **locationFinal** `['str']`: *'c:\\reference-case\\baseline\\outputs\\data\\demand'*
- **mcpcs** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcphs** `['ndarray']`: *array([ 0,  0,  0, ..., 14, 14, 14])*
- **mcpww** `['ndarray']`: *array([ 0.1948824 ,  0.19552022,  0.19616052, ...,  0.22399329,
        0.22457734,  0.22516265])*
- **path_temporary_folder** `['str']`: *'c:\\users\\darthoma\\appdata\\local\\temp'*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **waterpeak** `['float64']`: *0.05169618217507381*
- **date** `['DatetimeIndex']`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*


### Output
- `['NoneType']`: None

### Docstring template

```
PARAMETERS
----------

:param GFA_m2:
:type GFA_m2: float64

:param Af:
:type Af: float64

:param Ealf:
:type Ealf: ndarray

:param Ealf_0:
:type Ealf_0: float64

:param Ealf_tot:
:type Ealf_tot: float64

:param Eauxf:
:type Eauxf: ndarray

:param Eauxf_tot:
:type Eauxf_tot: float64

:param Edata:
:type Edata: ndarray

:param Edata_tot:
:type Edata_tot: float64

:param Epro:
:type Epro: ndarray

:param Epro_tot:
:type Epro_tot: float64

:param Name:
:type Name: str

:param Occupancy:
:type Occupancy: ndarray

:param Occupants:
:type Occupants: float64

:param Qcdata:
:type Qcdata: ndarray

:param Qcrefri:
:type Qcrefri: ndarray

:param Qcs:
:type Qcs: ndarray

:param Qcsf:
:type Qcsf: ndarray

:param Qcsf_0:
:type Qcsf_0: float64

:param Qhs:
:type Qhs: ndarray

:param Qhsf:
:type Qhsf: ndarray

:param Qhsf_0:
:type Qhsf_0: float64

:param Qww:
:type Qww: ndarray

:param Qww_ls_st:
:type Qww_ls_st: ndarray

:param Qwwf:
:type Qwwf: ndarray

:param Qwwf_0:
:type Qwwf_0: float64

:param Tcs_re:
:type Tcs_re: ndarray

:param Tcs_re_0:
:type Tcs_re_0: int64

:param Tcs_sup:
:type Tcs_sup: ndarray

:param Tcs_sup_0:
:type Tcs_sup_0: int64

:param Ths_re:
:type Ths_re: ndarray

:param Ths_re_0:
:type Ths_re_0: int64

:param Ths_sup:
:type Ths_sup: ndarray

:param Ths_sup_0:
:type Ths_sup_0: int64

:param Tww_re:
:type Tww_re: ndarray

:param Tww_st:
:type Tww_st: ndarray

:param Tww_sup_0:
:type Tww_sup_0: int64

:param Waterconsumption:
:type Waterconsumption: ndarray

:param locationFinal:
:type locationFinal: str

:param mcpcs:
:type mcpcs: ndarray

:param mcphs:
:type mcphs: ndarray

:param mcpww:
:type mcpww: ndarray

:param path_temporary_folder:
:type path_temporary_folder: str

:param sys_e_cooling:
:type sys_e_cooling: unicode

:param sys_e_heating:
:type sys_e_heating: unicode

:param waterpeak:
:type waterpeak: float64

:param date:
:type date: DatetimeIndex

RETURNS
-------

:returns:
:rtype: NoneType

```

[TOC](#table-of-contents)
---

# run_as_script
- number of invocations: 1
- max duration: 812.603 s
- avg duration: 812.603 s
- min duration: 812.603 s
- total duration: 812.603 s

### Input


### Output
- `['NoneType']`: None

### Docstring template

```
PARAMETERS
----------

RETURNS
-------

:returns:
:rtype: NoneType

```

[TOC](#table-of-contents)
---

# schedule_maker
- number of invocations: 1
- max duration: 1.846 s
- avg duration: 1.846 s
- min duration: 1.846 s
- total duration: 1.846 s

### Input
- **date** `['DatetimeIndex']`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*
- **locator** `['LocatorDecorator']`: *???*
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*


### Output
- `['list']`: [([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000

### Docstring template

```
PARAMETERS
----------

:param date:
:type date: DatetimeIndex

:param locator:
:type locator: LocatorDecorator

:param list_uses:
:type list_uses: list

RETURNS
-------

:returns:
:rtype: list

INPUT / OUTPUT FILES
--------------------

- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\databases\CH\Archetypes\Archetypes_schedules.xlsx
```

[TOC](#table-of-contents)
---

# thermal_loads_all_buildings
- number of invocations: 1
- max duration: 795.96 s
- avg duration: 795.96 s
- min duration: 795.96 s
- total duration: 795.96 s

### Input
- **building_properties** `['BuildingProperties']`: *<cea.demand.thermal_loads.BuildingProperties object at 0x0C97C870>*
- **date** `['DatetimeIndex']`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C2296B0>*
- **locator** `['LocatorDecorator']`: *???*
- **num_buildings** `['int']`: *274*
- **usage_schedules** `['dict']`: *{'list_uses': [u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL'], 'schedules': [([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4,*
- **weather_data** `['DataFrame']`: *(8760, 3)*

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
- `['NoneType']`: None

### Docstring template

```
PARAMETERS
----------

:param building_properties:
:type building_properties: BuildingProperties

:param date:
:type date: DatetimeIndex

:param gv:
:type gv: GlobalVariables

:param locator:
:type locator: LocatorDecorator

:param num_buildings:
:type num_buildings: int

:param usage_schedules:
:type usage_schedules: dict

:param weather_data:
:type weather_data: DataFrame

RETURNS
-------

:returns:
:rtype: NoneType

INPUT / OUTPUT FILES
--------------------

- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: c:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
```

[TOC](#table-of-contents)
---

# write_totals_csv
- number of invocations: 1
- max duration: 10.489 s
- avg duration: 10.489 s
- min duration: 10.489 s
- total duration: 10.489 s

### Input
- **building_properties** `['BuildingProperties']`: *<cea.demand.thermal_loads.BuildingProperties object at 0x0559B870>*
- **locator** `['LocatorDecorator']`: *???*


### Output
- `['NoneType']`: None

### Docstring template

```
PARAMETERS
----------

:param building_properties:
:type building_properties: BuildingProperties

:param locator:
:type locator: LocatorDecorator

RETURNS
-------

:returns:
:rtype: NoneType

INPUT / OUTPUT FILES
--------------------

- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153767T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B9001534T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B3169241T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153737T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006714T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006719T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153759T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153735T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006695T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153748T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153747T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368544T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153746T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153745T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153734T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153700T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006694T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153749T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153750T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153724T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153725T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153723T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153721T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153692T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153744T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153693T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153691T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368514T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153718T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153697T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153696T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153695T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153694T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153729T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049558T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153719T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153728T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153722T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006646T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007056aT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006839T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049656T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153742T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153715T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368562T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153716T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368593T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153753T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153743T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153717T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368599T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302023067T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007075T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153731T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153730T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153727T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153752T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153751T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153738T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153741T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153740T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153739T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372539T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153733T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153732T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153726T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007704T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007086T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007093T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007412T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007413T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368754T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153701T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006827T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006683T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302023104T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049659T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007081T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007701T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007744T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007064T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302023054T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153766T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B3169932T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007073T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007089T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302023103T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006713T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049650T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049632T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007063T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007868T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155054T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2367127T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007317T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007331T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049821T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B11515811T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007876T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007487T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007719T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007720T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007320T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302024340T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140556T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B3169408T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140567T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155061T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049800T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007726T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007697T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007700T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302061510T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B3169552T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372281T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140560T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140564T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140559T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B3169526T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040175T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140562T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140561T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B3169989T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040203T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155060T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372564T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007163T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007529T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040205T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B9011127T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040207T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140577T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140571T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372467T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040197T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040204T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140570T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140568T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372562T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140557T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040335T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140558T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140580T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140581T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040296T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140582T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040295T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140576T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B9011691T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040263T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140575T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372547T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140574T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140573T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372522T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302049837T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007878T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155194T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007873T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155193T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007721T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007385T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007869T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2367084T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007864T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007184T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155053T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007454T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007387T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007714T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007724T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007710T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007712T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007383T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2367115T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007715T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302023178T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007585T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2367248T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155128T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155084T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B9083954T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2367087T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155082T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155068T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155069T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155083T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155080T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2367183T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155067T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155073T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155072T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155071T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B3169251T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155066T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155065T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368214T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302008404T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155989T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007685T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007199T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155992T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155990T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155991T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368215T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372508T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140578T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140583T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372478T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040303T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040308T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040311T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040224T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040222T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040315T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372472T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140584T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140585T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140586T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372458T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040194T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040269T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040217T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040213T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040272T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372475T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140588T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040229T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040249T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140590T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140589T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140591T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2368754aT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B153690T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007056T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006716T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302022981T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006812T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006718T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006717T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302020948T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007057T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302020839T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007087T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302020840T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007068T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302024358T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040176T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040285T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302019757T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007894T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040323T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040195T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302019572T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302007201T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B155192T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302022730T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302022729T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040218T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302020916T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302020945T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302019271T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302022767T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302021376T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302024464T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302022768T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302019954T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302006890T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302034111T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B9011701T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302021637T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302020123T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302021377T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302024465T.csv
- get_total_demand: c:\reference-case\baseline\outputs\data\demand\Total_demand.csv
```

[TOC](#table-of-contents)
---

