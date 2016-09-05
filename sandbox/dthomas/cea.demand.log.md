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
               - [calc_thermal_load_hvac_timestep](#calc_thermal_load_hvac_timestep)
                  - [calc_T_em_ls](#calc_t_em_ls)
                  - [calc_Qhs_Qcs_sys_max](#calc_qhs_qcs_sys_max)
                  - [calc_hex](#calc_hex)
                     - [calc_w](#calc_w)
                  - [calc_h_ve_adj](#calc_h_ve_adj)
                  - [calc_Htr](#calc_htr)
                  - [calc_Qhs_Qcs](#calc_qhs_qcs)
                  - [calc_hvac](#calc_hvac)
                     - [calc_h](#calc_h)
                     - [calc_w3_cooling_case](#calc_w3_cooling_case)
               - [calc_thermal_load_mechanical_and_natural_ventilation_timestep](#calc_thermal_load_mechanical_and_natural_ventilation_timestep)
                  - [calc_Qhs_Qcs_dis_ls](#calc_qhs_qcs_dis_ls)
               - [calc_temperatures_emission_systems](#calc_temperatures_emission_systems)
                  - [calc_radiator](#calc_radiator)
                     - [newton](#newton)
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
         - [write_totals_csv](#write_totals_csv)

# allocate_default_leakage_paths
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **coeff_lea_zone** `['float64']`: *7572.0292843945435*
- **area_facade_zone** `['float64']`: *4572.7925135561345*
- **area_roof_zone** `['float64']`: *2638.5217028738552*
- **height_zone** `['float64']`: *19.5*


### Output
- `['tuple']`: (array([ 1200.38171216,  1200.38171216,  1200.38171216,  1200.38171216,
        2770.50243576]), array([  4.875,   4.875,  14.625,  14.625,  19.5  ]), array([ 0.,  1.,  0.,  1.,  2.]))

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
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **coeff_vent_zone** `['float']`: *0.0*
- **height_zone** `['float64']`: *19.5*


### Output
- `['tuple']`: (array([ 0.,  0.,  0.,  0.]), array([  4.875,   4.875,  14.625,  14.625]), array([ 0.,  1.,  0.,  1.]))

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
- max duration: 0.037 s
- avg duration: 0.037 s
- min duration: 0.037 s
- total duration: 0.037 s

### Input
- **Aef** `['float64']`: *14248.017195518818*
- **Ealf** `['ndarray']`: *array([ 45536.66295688,  45536.66295688,  45536.66295688, ...,
        89479.54271027,  75818.5438232 ,  51570.27079866])*
- **Eauxf** `['ndarray']`: *array([  0.        ,   0.        ,   0.        , ...,  65.74432788,
         2.8770457 ,   2.65250507])*
- **Edataf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eaf** `['ndarray']`: *array([ 36132.97160784,  36132.97160784,  36132.97160784, ...,
        71001.2892094 ,  60161.39772705,  40920.59034587])*
- **Elf** `['ndarray']`: *array([  9403.69134904,   9403.69134904,   9403.69134904, ...,
        18478.25350087,  15657.14609616,  10649.68045279])*


### Output
- `['tuple']`: (array([ 45536.66295688,  45536.66295688,  45536.66295688, ...,
        89479.54271027,  75818.5438232 ,  51570.27079866]), 420075.71577720094, 1255.887503351812, 40.055689107389043, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0, 333326.66308228462, 86749.052694916332, 996.536517052627, 259.35098629918525)

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

:param Eaf:
:type Eaf: ndarray

:param Elf:
:type Elf: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Ea_El_Edata_Eref_schedule
- number of invocations: 1
- max duration: 1.126 s
- avg duration: 1.126 s
- min duration: 1.126 s
- total duration: 1.126 s

### Input
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*
- **schedules** `['list']`: *[([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, *
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 0.0, u'RESTAURANT': 0.20000000000000001, u'PFloor': 0.20000000000000001, u'PARKING': 0.80000000000000004, u'SERVERROOM': 0.0}*


### Output
- `['ndarray']`: array([ 0.08  ,  0.08  ,  0.08  , ...,  0.1572,  0.1332,  0.0906])

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
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **schedule** `['ndarray']`: *array([ 0.08  ,  0.08  ,  0.08  , ...,  0.1572,  0.1332,  0.0906])*
- **Ea_Wm2** `['float64']`: *31.699999999999999*
- **Aef** `['float64']`: *14248.017195518818*


### Output
- `['ndarray']`: array([ 36132.97160784,  36132.97160784,  36132.97160784, ...,
        71001.2892094 ,  60161.39772705,  40920.59034587])

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: ndarray

:param Ea_Wm2:
:type Ea_Wm2: float64

:param Aef:
:type Aef: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eauxf
- number of invocations: 1
- max duration: 0.337 s
- avg duration: 0.337 s
- min duration: 0.337 s
- total duration: 0.337 s

### Input
- **Ll** `['float64']`: *87.0*
- **Lw** `['float64']`: *30.0*
- **Mww** `['ndarray']`: *array([ 0.        ,  0.        ,  0.        , ...,  0.31527927,
        0.08521061,  0.07242902])*
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-3824434.2215403998*
- **Qhsf** `['ndarray']`: *array([      0.        ,       0.        ,       0.        , ...,
        345431.70390049,       0.        ,       0.        ])*
- **Qhsf_0** `['float64']`: *3592302.7665316463*
- **Qww** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        65956.42342807,  17826.06038597,  15152.15132807])*
- **Qwwf** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        68481.67061934,  18630.23145399,  15853.22938387])*
- **Qwwf_0** `['float64']`: *128049.69313257416*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re** `['ndarray']`: *array([ 0,  0,  0, ..., 29,  0,  0])*
- **Ths_sup** `['ndarray']`: *array([ 0,  0,  0, ..., 31,  0,  0])*
- **Vw** `['ndarray']`: *array([ 0.        ,  0.        ,  0.        , ...,  2.27455987,
        0.61474591,  0.52253402])*
- **Year** `['int64']`: *2010*
- **fforma** `['float64']`: *1.0109278555072243*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143D28B0>*
- **nf_ag** `['float64']`: *5.0*
- **nfp** `['float64']`: *0.20000000000000001*
- **qv_req** `['ndarray']`: *array([  2.55803726,   2.55803726,   2.55803726, ...,  15.91020361,
         4.30005503,   3.65504678])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **Ehs_lat_aux** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['tuple']`: (array([  0.        ,   0.        ,   0.        , ...,  65.74432788,
         2.8770457 ,   2.65250507]), array([  0.        ,   0.        ,   0.        , ...,  60.21021997,
         0.        ,   0.        ]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.        ,  0.        ,  0.        , ...,  5.5341079 ,
        2.8770457 ,  2.65250507]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]))

### Docstring template

```
PARAMETERS
----------

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
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **Qcsf** `['float64']`: *-0.0*
- **Qcsf0** `['float64']`: *-3824434.2215403998*
- **Imax** `['float64']`: *234.53526247767604*
- **deltaP_des** `['float64']`: *30.489584122097888*
- **b** `['int32']`: *1*
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
:type b: int32

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
- max duration: 0.038 s
- avg duration: 0.038 s
- min duration: 0.038 s
- total duration: 0.038 s

### Input
- **freshw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **nf** `['float64']`: *6.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x140A18D0>*


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
- max duration: 0.039 s
- avg duration: 0.039 s
- min duration: 0.039 s
- total duration: 0.039 s

### Input
- **Qhsf** `['float64']`: *0.0*
- **Qhsf0** `['float64']`: *3592302.7665316463*
- **Imax** `['float64']`: *234.53526247767604*
- **deltaP_des** `['float64']`: *30.489584122097888*
- **b** `['int32']`: *1*
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
:type b: int32

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
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **Qhsf** `['float64']`: *0.0*
- **Qcsf** `['float64']`: *-0.0*
- **P_ve** `['float64']`: *0.55000000000000004*
- **qve** `['float64']`: *2.5580372556112119*
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
- max duration: 0.042 s
- avg duration: 0.042 s
- min duration: 0.042 s
- total duration: 0.042 s

### Input
- **Qww** `['float64']`: *0.0*
- **Qwwf** `['float64']`: *0.0*
- **Qwwf0** `['float64']`: *128049.69313257416*
- **Imax** `['float64']`: *234.53526247767604*
- **deltaP_des** `['float64']`: *30.489584122097888*
- **b** `['int32']`: *1*
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
:type b: int32

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
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **schedule** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ed_Wm2** `['float64']`: *0.0*
- **Aef** `['float64']`: *14248.017195518818*
- **share** `['float64']`: *0.0*


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

:param Aef:
:type Aef: float64

:param share:
:type share: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eint
- number of invocations: 1
- max duration: 3.583 s
- avg duration: 3.583 s
- min duration: 3.583 s
- total duration: 3.583 s

### Input
- **tsd** `['dict']`: *{'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Tww_re': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Tm': array([ nan,  nan,  nan, ...,  nan,  nan,  nan]), 'Qcs_sen_incl_em_ls': array([ 0.,  0.,  0., ...,  0.,*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x140AFF70>*
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*
- **schedules** `['list']`: *[([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, *


### Output
- `['dict']`: {'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Tww_re': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Ealf': array([ 45536.66295688,  45536.66295688,  45536.66295688, ...,
        89479.54271027,  75818.5438232

### Docstring template

```
PARAMETERS
----------

:param tsd:
:type tsd: dict

:param bpr:
:type bpr: BuildingPropertiesRow

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

RETURNS
-------

:returns:
:rtype: dict

```

[TOC](#table-of-contents)
---

# calc_Elf
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **schedule** `['ndarray']`: *array([ 0.08  ,  0.08  ,  0.08  , ...,  0.1572,  0.1332,  0.0906])*
- **El_Wm2** `['float64']`: *8.25*
- **Aef** `['float64']`: *14248.017195518818*


### Output
- `['ndarray']`: array([  9403.69134904,   9403.69134904,   9403.69134904, ...,
        18478.25350087,  15657.14609616,  10649.68045279])

### Docstring template

```
PARAMETERS
----------

:param schedule:
:type schedule: ndarray

:param El_Wm2:
:type El_Wm2: float64

:param Aef:
:type Aef: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_Eprof_schedule
- number of invocations: 1
- max duration: 1.116 s
- avg duration: 1.116 s
- min duration: 1.116 s
- total duration: 1.116 s

### Input
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*
- **schedules** `['list']`: *[([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, *
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 0.0, u'RESTAURANT': 0.20000000000000001, u'PFloor': 0.20000000000000001, u'PARKING': 0.80000000000000004, u'SERVERROOM': 0.0}*


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

# calc_Htr
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **Hve** `['float64']`: *4022.4624237035187*
- **Htr_is** `['float64']`: *69302.623523592818*
- **Htr_ms** `['float64']`: *414902.26073350798*
- **Htr_w** `['float64']`: *297.23151337624876*


### Output
- `['tuple']`: (3801.7984620992102, 4099.0299754754587, 4058.9297487878134)

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
- max duration: 0.111 s
- avg duration: 0.111 s
- min duration: 0.111 s
- total duration: 0.111 s

### Input
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x1432FB30>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x1432FB30>*


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
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **people** `['ndarray']`: *array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539])*
- **X_ghp** `['float64']`: *85.0*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*


### Output
- `['ndarray']`: array([ 0.        ,  0.        ,  0.        , ...,  0.01493667,
        0.00403694,  0.0034314 ])

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
- max duration: 0.255 s
- avg duration: 0.255 s
- min duration: 0.255 s
- total duration: 0.255 s

### Input
- **people** `['ndarray']`: *array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539])*
- **Qs_Wp** `['float64']`: *73.0*
- **Eal_nove** `['ndarray']`: *array([ 45536.66295688,  45536.66295688,  45536.66295688, ...,
        89479.54271027,  75818.5438232 ,  51570.27079866])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcdata** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Qcrefri** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **tsd** `['dict']`: *{'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([     0.        ,      0.        ,      0.        , ...,
        57276.68717357,  15480.18572259,  13158.1578642 ]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Elf': array([  9403.69134904,   9*
- **Am** `['float64']`: *45593.65502566022*
- **Atot** `['float64']`: *20087.716963360235*
- **Htr_w** `['float64']`: *297.23151337624876*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x14DD2BB0>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x1409C8D0>*


### Output
- `['dict']`: {'w_int': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([     0.        ,      0.        ,      0.        , ...,
        57276.68717357,  15480.18572259,  13158.1578642 ]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Elf': array([  9403.69134904,   9

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
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **SystemH** `['unicode']`: *u'T1'*
- **SystemC** `['unicode']`: *u'T3'*
- **tm_t0** `['float64']`: *13.699999999999999*
- **te_t** `['float64']`: *13.699999999999999*
- **tintH_set** `['float64']`: *-30.0*
- **tintC_set** `['int32']`: *28*
- **Htr_em** `['float64']`: *1324.1381230121124*
- **Htr_ms** `['float64']`: *414902.26073350798*
- **Htr_is** `['float64']`: *69302.623523592818*
- **Htr_1** `['float64']`: *3801.7984620992102*
- **Htr_2** `['float64']`: *4099.0299754754587*
- **Htr_3** `['float64']`: *4058.9297487878134*
- **I_st** `['float64']`: *-19538.962465169036*
- **Hve** `['float64']`: *4022.4624237035187*
- **Htr_w** `['float64']`: *297.23151337624876*
- **I_ia** `['float64']`: *15368.623747946371*
- **I_m** `['float64']`: *34882.596696335684*
- **Cm** `['float64']`: *4274405158.6556454*
- **Af** `['float64']`: *14248.017195518818*
- **Losses** `['bool']`: *False*
- **tHset_corr** `['float']`: *1.3499999999999999*
- **tCset_corr** `['float']`: *-0.7*
- **IC_max** `['float64']`: *-7124008.5977594089*
- **IH_max** `['float64']`: *7124008.5977594089*
- **Flag** `['bool_']`: *True*


### Output
- `['tuple']`: (13.725140799625523, 13.910051496030922, 0, 0, 0, 13.765448706927408, 103666.2426068261)

### Docstring template

```
PARAMETERS
----------

:param SystemH:
:type SystemH: unicode

:param SystemC:
:type SystemC: unicode

:param tm_t0:
:type tm_t0: float64

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
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **tair** `['float64']`: *21.498396740500983*
- **text** `['float64']`: *1.1000000000000001*
- **Qhs** `['float64']`: *0.0*
- **Qcs** `['float64']`: *0.0*
- **tsh** `['float64']`: *90.0*
- **trh** `['float64']`: *70.0*
- **tsc** `['int64']`: *7*
- **trc** `['int64']`: *15*
- **Qhs_max** `['float64']`: *3588218.7665316463*
- **Qcs_max** `['float64']`: *-722028.32221596281*
- **D** `['int32']`: *20*
- **Y** `['float64']`: *0.20000000000000001*
- **SystemH** `['unicode_']`: *u'T1'*
- **SystemC** `['unicode_']`: *u'T3'*
- **Bf** `['float64']`: *0.69999999999999996*
- **Lv** `['float64']`: *267.71896933470066*


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
:type tsh: float64

:param trh:
:type trh: float64

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
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Af** `['float64']`: *14248.017195518818*
- **prop_HVAC** `['dict']`: *{u'Qcsmax_Wm2': 500, u'dTcs0_C': 8, u'type_ctrl': u'T2', u'type_cs': u'T3', u'dThs0_C': 20, u'Qhsmax_Wm2': 500, u'Tscs0_C': 7, u'type_hs': u'T1', u'Tsww0_C': 60, u'Qwwmax_Wm2': 500, u'dTww0_C': 50, u'Tshs0_C': 90, u'type_dhw': u'T1'}*


### Output
- `['tuple']`: (-7124008.5977594089, 7124008.5977594089)

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
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

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
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **tair** `['float64']`: *21.498396740500983*
- **Qww** `['float64']`: *0.0*
- **Lvww_dis** `['float64']`: *252.85832985874447*
- **Lvww_c** `['float64']`: *208.88296814418021*
- **Y** `['float64']`: *0.20000000000000001*
- **Qww_0** `['float64']`: *123296.91766959219*
- **V** `['float64']`: *133.63813083451046*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **Bf** `['float64']`: *0.69999999999999996*
- **te** `['float64']`: *1.1000000000000001*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143C4E90>*


### Output
- `['int']`: 0

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
:rtype: int

```

[TOC](#table-of-contents)
---

# calc_Qww_dis_ls_r
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **Tair** `['float64']`: *21.498396740500983*
- **Qww** `['float64']`: *0.0*
- **lsww_dis** `['float64']`: *300.79147412761955*
- **lcww_dis** `['float64']`: *187.0216532688365*
- **Y** `['float64']`: *0.29999999999999999*
- **Qww_0** `['float64']`: *123296.91766959219*
- **V** `['float64']`: *133.63813083451046*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143D2F30>*


### Output
- `['int']`: 0

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
:rtype: int

```

[TOC](#table-of-contents)
---

# calc_Qww_schedule
- number of invocations: 1
- max duration: 1.315 s
- avg duration: 1.315 s
- min duration: 1.315 s
- total duration: 1.315 s

### Input
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*
- **schedules** `['list']`: *[([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, *
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 0.0, u'RESTAURANT': 0.20000000000000001, u'PFloor': 0.20000000000000001, u'PARKING': 0.80000000000000004, u'SERVERROOM': 0.0}*


### Output
- `['ndarray']`: array([ 0.        ,  0.        ,  0.        , ...,  0.01995506,
        0.00539326,  0.00458427])

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
- max duration: 0.284 s
- avg duration: 0.284 s
- min duration: 0.284 s
- total duration: 0.284 s

### Input
- **Vww** `['ndarray']`: *array([ 0.        ,  0.        ,  0.        , ...,  1.13727993,
        0.30737296,  0.26126701])*
- **Tww_setpoint** `['int']`: *60*
- **Ta** `['ndarray']`: *array([ 21.49839674,  21.45330512,  21.40318426, ...,  21.        ,
        21.20261801,  21.24546211])*
- **Bf** `['float']`: *0.7*
- **Pwater** `['int']`: *998*
- **Cpw** `['float']`: *4.184*
- **Qww_dis_ls_r** `['ndarray']`: *array([   0,    0,    0, ..., 1172,  321,  275])*
- **Qww_dis_ls_nr** `['ndarray']`: *array([   0,    0,    0, ..., 1179,  323,  276])*
- **U_dhwtank** `['float']`: *0.225*
- **AR** `['float']`: *3.3*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x142D3C90>*
- **T_ext** `['ndarray']`: *array([ 1.1,  1.1,  1. , ...,  1.4,  1.4,  1.4])*
- **Qww** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        65956.42342807,  17826.06038597,  15152.15132807])*


### Output
- `['tuple']`: (array([ 124.23056187,  124.22946369,  124.39667754, ...,  124.04028432,
        123.91052412,  123.8898852 ]), array([ 59.98600594,  59.972012  ,  59.95799923, ...,  59.98529544,
        59.98938004,  59.99233003]), array([     0.        ,      0.        ,      0.        , ...,
        68481.67061934,  18630.23145399,  15853.22938387]))

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
- max duration: 3.398 s
- avg duration: 3.398 s
- min duration: 3.398 s
- total duration: 3.398 s

### Input
- **Af** `['float64']`: *14248.017195518818*
- **Lcww_dis** `['float64']`: *187.0216532688365*
- **Lsww_dis** `['float64']`: *300.79147412761955*
- **Lvww_c** `['float64']`: *208.88296814418021*
- **Lvww_dis** `['float64']`: *252.85832985874447*
- **T_ext** `['ndarray']`: *array([ 1.1,  1.1,  1. , ...,  1.4,  1.4,  1.4])*
- **Ta** `['ndarray']`: *array([ 21.49839674,  21.45330512,  21.40318426, ...,  21.        ,
        21.20261801,  21.24546211])*
- **Tww_re** `['ndarray']`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_sup_0** `['int64']`: *60*
- **Y** `['list']`: *[0.2, 0.3, 0.3]*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x1432F510>*
- **Vww_lpd** `['float64']`: *8.0*
- **Vw_lpd** `['float64']`: *16.0*
- **Occ_m2p** `['float64']`: *2.0*
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*
- **schedules** `['list']`: *[([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, *
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 0.0, u'RESTAURANT': 0.20000000000000001, u'PFloor': 0.20000000000000001, u'PARKING': 0.80000000000000004, u'SERVERROOM': 0.0}*


### Output
- `['tuple']`: (array([ 0.        ,  0.        ,  0.        , ...,  0.31527927,
        0.08521061,  0.07242902]), array([     0.        ,      0.        ,      0.        , ...,
        65956.42342807,  17826.06038597,  15152.15132807]), array([ 124.23056187,  124.22946369,  124.39667754, ...,  124.04028432,
        123.91052412,  123.8898852 ]), array([     0.        ,      0.        ,      0.        , ...,
        68481.67061934,  18630.23145399,  15853.22938387]), 128049.69313257416, array([ 59.98600594,  5

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
- **sys_e_ctrl** `['unicode']`: *u'T2'*


### Output
- `['tuple']`: (1.3499999999999999, -0.7)

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
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **qv_delta_p_lea_ref** `['float64']`: *102902.34641208035*


### Output
- `['float64']`: 7572.0292843945435

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
- max duration: 0.027 s
- avg duration: 0.027 s
- min duration: 0.027 s
- total duration: 0.027 s

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
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **tamb** `['float']`: *21.0*
- **hotw** `['float']`: *27333.29259181321*
- **Flowtap** `['float']`: *0.036*
- **V** `['float']`: *133.63813083451046*
- **twws** `['long']`: *60L*
- **Lsww_dis** `['float']`: *300.79147412761955*
- **p** `['int']`: *998*
- **cpw** `['float']`: *4.184*
- **Y** `['float']`: *0.3*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x14DA37F0>*


### Output
- `['float64']`: 4.6388364867218721

### Docstring template

```
PARAMETERS
----------

:param tamb:
:type tamb: float

:param hotw:
:type hotw: float

:param Flowtap:
:type Flowtap: float

:param V:
:type V: float

:param twws:
:type twws: long

:param Lsww_dis:
:type Lsww_dis: float

:param p:
:type p: int

:param cpw:
:type cpw: float

:param Y:
:type Y: float

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_h
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **t** `['int32']`: *27*
- **w** `['float64']`: *0.0096304911158184934*


### Output
- `['float64']`: 51.727301079295913

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
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **q_m_mech** `['float64']`: *3.9905381187534905*
- **q_m_nat** `['int']`: *0*
- **temp_ext** `['float64']`: *13.699999999999999*
- **temp_sup** `['float64']`: *13.699999999999999*
- **temp_zone_set** `['float64']`: *13.699999999999999*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143D2830>*


### Output
- `['float64']`: 4022.4624237035187

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
:type temp_zone_set: float64

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
- max duration: 0.085 s
- avg duration: 0.085 s
- min duration: 0.085 s
- total duration: 0.085 s

### Input
- **rel_humidity_ext** `['int64']`: *93*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143D2830>*
- **temp_ext** `['float64']`: *13.699999999999999*
- **temp_zone_prev** `['float64']`: *13.699999999999999*
- **timestep** `['int']`: *5472*


### Output
- `['tuple']`: (13.699999999999999, 0.0091380190832960652)

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
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **rhum_1** `['int64']`: *93*
- **temp_1** `['float64']`: *13.699999999999999*
- **temp_zone_set** `['float']`: *13.910051496030922*
- **qv_req** `['float64']`: *3.3254484322945754*
- **qe_sen** `['int']`: *0*
- **temp_5_prev** `['float64']`: *13.699999999999999*
- **wint** `['float64']`: *0.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x142EA8B0>*
- **timestep** `['int']`: *5472*


### Output
- `['tuple']`: (0, 0, 0, 0, 0, 0, 0, nan, nan, 13.699999999999999, 13.699999999999999, 0, 0, 13.910051496030922)

### Docstring template

```
PARAMETERS
----------

:param rhum_1:
:type rhum_1: int64

:param temp_1:
:type temp_1: float64

:param temp_zone_set:
:type temp_zone_set: float

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
- max duration: 0.054 s
- avg duration: 0.054 s
- min duration: 0.054 s
- total duration: 0.054 s

### Input
- **schedule** `['float64']`: *0.0*
- **Vww_lpd** `['float64']`: *8.0*
- **Occ_m2p** `['float64']`: *2.0*
- **Af** `['float64']`: *14248.017195518818*
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
- max duration: 2.71 s
- avg duration: 2.71 s
- min duration: 2.71 s
- total duration: 2.71 s

### Input
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*
- **schedules** `['list']`: *[([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, *
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x1432FF10>*


### Output
- `['ndarray']`: array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539])

### Docstring template

```
PARAMETERS
----------

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param bpr:
:type bpr: BuildingPropertiesRow

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_occ_schedule
- number of invocations: 1
- max duration: 1.361 s
- avg duration: 1.361 s
- min duration: 1.361 s
- total duration: 1.361 s

### Input
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*
- **schedules** `['list']`: *[([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, *
- **building_uses** `['dict']`: *{u'INDUSTRIAL': 0.0, u'OFFICE': 0.0, u'RESTAURANT': 0.20000000000000001, u'PFloor': 0.20000000000000001, u'PARKING': 0.80000000000000004, u'SERVERROOM': 0.0}*


### Output
- `['ndarray']`: array([ 0.    ,  0.    ,  0.    , ...,  0.0888,  0.024 ,  0.0204])

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
- max duration: 0.026 s
- avg duration: 0.026 s
- min duration: 0.026 s
- total duration: 0.026 s

### Input
- **n_delta_p_ref** `['int64']`: *2*
- **vol_building** `['float64']`: *51451.173206040177*


### Output
- `['float64']`: 102902.34641208035

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

# calc_radiator
- number of invocations: 1
- max duration: 0.035 s
- avg duration: 0.035 s
- min duration: 0.035 s
- total duration: 0.035 s

### Input
- **Qh** `['float64']`: *0.0*
- **tair** `['float64']`: *21.498396740500983*
- **Qh0** `['float64']`: *3592302.7665316463*
- **tair0** `['float64']`: *21.0*
- **tsh0** `['float64']`: *90.0*
- **trh0** `['float64']`: *70.0*


### Output
- `['tuple']`: (0, 0, 0)

### Docstring template

```
PARAMETERS
----------

:param Qh:
:type Qh: float64

:param tair:
:type tair: float64

:param Qh0:
:type Qh0: float64

:param tair0:
:type tair0: float64

:param tsh0:
:type tsh0: float64

:param trh0:
:type trh0: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_temperatures_emission_systems
- number of invocations: 1
- max duration: 0.333 s
- avg duration: 0.333 s
- min duration: 0.333 s
- total duration: 0.333 s

### Input
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-3824434.2215403998*
- **Qhsf** `['ndarray']`: *array([      0.        ,       0.        ,       0.        , ...,
        345431.70390049,       0.        ,       0.        ])*
- **Qhsf_0** `['float64']`: *3592302.7665316463*
- **Ta** `['ndarray']`: *array([ 21.49839674,  21.45330512,  21.40318426, ...,  21.        ,
        21.20261801,  21.24546211])*
- **Ta_re_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_re_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Tcs_re_0** `['int64']`: *15*
- **Tcs_sup_0** `['int64']`: *7*
- **Ths_re_0** `['float']`: *70.0*
- **Ths_sup_0** `['float']`: *90.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143C4E90>*
- **ma_sup_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **ma_sup_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **ta_hs_set** `['ndarray']`: *array([ 12.,  12.,  12., ...,  21.,  21.,  21.])*


### Output
- `['tuple']`: (array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]), array([ 0,  0,  0, ..., 29,  0,  0]), array([ 0,  0,  0, ..., 31,  0,  0]), array([0, 0, 0, ..., 0, 0, 0]), array([     0,      0,      0, ..., 179615,      0,      0]))

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
:type Ths_re_0: float

:param Ths_sup_0:
:type Ths_sup_0: float

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
- max duration: 0.563 s
- avg duration: 0.563 s
- min duration: 0.563 s
- total duration: 0.563 s

### Input
- **t** `['int']`: *5472*
- **tsd** `['dict']`: *{'w_int': array([ 0.        ,  0.        ,  0.        , ...,  0.01493667,
        0.00403694,  0.0034314 ]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([     0.        ,      0.        ,      0.        , ...,
        57276.68717357,  15480.18572259,  13158.1578642 ]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., .*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x143D2450>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x14B5C6B0>*


### Output
- `['dict']`: {'w_int': array([ 0.        ,  0.        ,  0.        , ...,  0.01493667,
        0.00403694,  0.0034314 ]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([     0.        ,      0.        ,      0.        , ...,
        57276.68717357,  15480.18572259,  13158.1578642 ]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., .

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
- max duration: 0.119 s
- avg duration: 0.119 s
- min duration: 0.119 s
- total duration: 0.119 s

### Input
- **t** `['int']`: *6192*
- **tsd** `['dict']`: *{'w_int': array([ 0.        ,  0.        ,  0.        , ...,  0.01493667,
        0.00403694,  0.0034314 ]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([     0.        ,      0.        ,      0.        , ...,
        57276.68717357,  15480.18572259,  13158.1578642 ]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., .*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x143D2450>*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x1432F670>*


### Output
- `['dict']`: {'w_int': array([ 0.        ,  0.        ,  0.        , ...,  0.01493667,
        0.00403694,  0.0034314 ]), 'Im_tot': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 've': array([     0.        ,      0.        ,      0.        , ...,
        57276.68717357,  15480.18572259,  13158.1578642 ]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'Ta_sup_cs': array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 'Top': array([ 0.,  0.,  0., .

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
- max duration: 15.312 s
- avg duration: 15.312 s
- min duration: 15.312 s
- total duration: 15.312 s

### Input
- **building_name** `['str']`: *'Bau A'*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x143C4F10>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **usage_schedules** `['dict']`: *{'list_uses': [u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM'], 'schedules': [([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0*
- **date** `['DatetimeIndex']`: *DatetimeIndex(['2010-01-01 00:00:00', '2010-01-01 01:00:00',
               '2010-01-01 02:00:00', '2010-01-01 03:00:00',
               '2010-01-01 04:00:00', '2010-01-01 05:00:00',
               '2010-01-01 06:00:00', '2010-01-01 07:00:00',
               '2010-01-01 08:00:00', '2010-01-01 09:00:00',
               ...
               '2010-12-31 14:00:00', '2010-12-31 15:00:00',
               '2010-12-31 16:00:00', '2010-12-31 17:00:00',
               '2010-12-31 18:00:00', '2010-12-31 19:0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x142D3C90>*
- **locator** `['LocatorDecorator']`: *???*

#### weather_data:
```
         drybulb_C  relhum_percent   windspd_ms
count  8760.000000     8760.000000  8760.000000
mean     10.150000       73.861644     1.838094
std       8.022269       15.889964     1.847214
min     -10.300000       28.000000     0.000000
25%       3.700000       62.000000     0.500000
50%      10.400000       77.000000     1.300000
75%      16.100000       86.000000     2.500000
max      32.300000      100.000000    15.300000
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

:param locator:
:type locator: LocatorDecorator

RETURNS
-------

:returns:
:rtype: NoneType

INPUT / OUTPUT FILES
--------------------

- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
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
- **t** `['float64']`: *13.699999999999999*
- **RH** `['int64']`: *93*


### Output
- `['float64']`: 0.0091380190832960652

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
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **t5** `['int32']`: *27*
- **w2** `['float64']`: *0.0096304911158184934*
- **t3** `['int']`: *16*
- **w5** `['float64']`: *0.010412833469106675*


### Output
- `['float64']`: 0.0096304911158184934

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

# demand_calculation
- number of invocations: 1
- max duration: 73.876 s
- avg duration: 73.876 s
- min duration: 73.876 s
- total duration: 73.876 s

### Input
- **locator** `['InputLocator']`: *<cea.inputlocator.InputLocator object at 0x143CC990>*
- **weather_path** `['str']`: *'C:\\Users\\darthoma\\Documents\\GitHub\\CEAforArcGIS\\cea\\databases\\CH\\Weather\\Zug-2010.epw'*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143CC990>*


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

- get_radiation: c:\reference-case-zug\baseline\outputs\data\solar-radiation\radiation.csv
- get_surface_properties: c:\reference-case-zug\baseline\outputs\data\solar-radiation\properties_surfaces.csv
- get_building_geometry: c:\reference-case-zug\baseline\inputs\building-geometry\zone.shp
- get_building_hvac: c:\reference-case-zug\baseline\inputs\building-properties\technical_systems.shp
- get_building_thermal: c:\reference-case-zug\baseline\inputs\building-properties\thermal_properties.shp
- get_building_occupancy: c:\reference-case-zug\baseline\inputs\building-properties\occupancy.shp
- get_building_architecture: c:\reference-case-zug\baseline\inputs\building-properties\architecture.shp
- get_building_age: c:\reference-case-zug\baseline\inputs\building-properties\age.shp
- get_building_comfort: c:\reference-case-zug\baseline\inputs\building-properties\indoor_comfort.shp
- get_building_internal: c:\reference-case-zug\baseline\inputs\building-properties\internal_loads.shp
```

[TOC](#table-of-contents)
---

# get_building_geometry_ventilation
- number of invocations: 1
- max duration: 0.024 s
- avg duration: 0.024 s
- min duration: 0.024 s
- total duration: 0.024 s

### Input
- **gdf_building_geometry** `['dict']`: *{'perimeter': 234.50218018236586, u'Blength': 87.0, u'height_bg': 3.0, u'floors_bg': 1.0, u'height_ag': 19.5, u'floors_ag': 5.0, u'Bwidth': 30.0, 'footprint': 2638.5217028738552}*


### Output
- `['tuple']`: (4572.7925135561345, 2638.5217028738552, 19.5, 0)

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
- max duration: 0.403 s
- avg duration: 0.403 s
- min duration: 0.403 s
- total duration: 0.403 s

### Input
- **gdf_geometry_building** `['dict']`: *{'perimeter': 234.50218018236586, u'Blength': 87.0, u'height_bg': 3.0, u'floors_bg': 1.0, u'height_ag': 19.5, u'floors_ag': 5.0, u'Bwidth': 30.0, 'footprint': 2638.5217028738552}*
- **gdf_architecture_building** `['dict']`: *{u'Occ_m2p': 2.0, u'f_cros': 0, u'n50': 2, u'win_op': 0.5, u'win_wall': 0.25, u'type_shade': u'T1'}*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x14B5C650>*


### Output
- `['dict']`: {'coeff_wind_pressure_path_vent': array([ 0.05, -0.05,  0.05, -0.05]), 'coeff_vent_path': array([ 0.,  0.,  0.,  0.]), 'height_vent_path': array([  4.875,   4.875,  14.625,  14.625]), 'coeff_lea_path': array([ 1200.38171216,  1200.38171216,  1200.38171216,  1200.38171216,
        2770.50243576]), 'factor_cros': 0, 'height_lea_path': array([  4.875,   4.875,  14.625,  14.625,  19.5  ]), 'coeff_wind_pressure_path_lea': array([ 0.05, -0.05,  0.05, -0.05,  0.  ])}

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
- max duration: 0.149 s
- avg duration: 0.149 s
- min duration: 0.149 s
- total duration: 0.149 s

### Input
- **locator** `['LocatorDecorator']`: *???*
- **prop_HVAC** `['GeoDataFrame']`: *(24, 5)*

#### prop_HVAC:
```
          Name type_cs type_ctrl type_dhw type_hs
count       24      24        24       24      24
unique      24       1         2        1       2
top     Bau 03      T3        T1       T1      T1
freq         1      24        15       24      16
```

### Output
- `['DataFrame']`: (24, 14)

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
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **height_path** `['ndarray']`: *array([  4.875,   4.875,  14.625,  14.625,  19.5  ])*
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

# newton
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **func** `['builtin_function_or_method']`: *???*
- **x0** `['float']`: *343.0*
- **args** `['tuple']`: *(179615.13832658232, 3.0633147541017403, 3592302.7665316463, 294.0, 58.430633840867486, 0.3)*
- **tol** `['float']`: *0.01*
- **maxiter** `['int']`: *100*


### Output
- `['float']`: 306.32378406013896

### Docstring template

```
PARAMETERS
----------

:param func:
:type func: builtin_function_or_method

:param x0:
:type x0: float

:param args:
:type args: tuple

:param tol:
:type tol: float

:param maxiter:
:type maxiter: int

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# read_schedules
- number of invocations: 1
- max duration: 0.036 s
- avg duration: 0.036 s
- min duration: 0.036 s
- total duration: 0.036 s

### Input
- **use** `['unicode']`: *u'INDUSTRIAL'*
- **x** `['DataFrame']`: *(24, 37)*

#### x:
```
        NaN  Weekday_1  Saturday_1  Sunday_1  NaN  \
count    24       24.0          24        24    0   
unique   24        4.0           1         1    0   
top      24        0.2           0         0  NaN   
freq      1        7.0          24        24  NaN   

                                                      NaN  NaN  Weekday_2  \
count                                                   1   24       24.0   
unique                                                  1   24        4.0   
top     Probability of use of lighting and appliances ...   24        0.2   
freq                                                    1    1        7.0   

        Saturday_2  Sunday_2  ...         NaN  NaN  NaN    NaN  NaN  NaN  \
count         24.0      24.0  ...   24.000000    0    0      1    0    0   
unique         1.0       1.0  ...    1.000000    0    0      1    0    0   
top            0.2       0.2  ...    0.034267  NaN  NaN  month  NaN  NaN   
freq          24.0      24.0  ...   24.000000  NaN  NaN      1  NaN  NaN   

         NaN  NaN  NaN   NaN  
count      1    0    0     1  
unique     1    0    0     1  
top     data  NaN  NaN  data  
freq       1  NaN  NaN     1  

[4 rows x 37 columns]
```

### Output
- `['tuple']`: ([array([0.2, 0.2, 0.2, 0.2, 0.2, 0.5, 0.8, 1.0, 1.0, 0.8, 1.0, 0.5, 0.8,
       1.0, 1.0, 0.8, 0.8, 0.8, 0.5, 0.5, 0.5, 0.5, 0.2, 0.2], dtype=object), array([0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
       0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=object), array([0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
       0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=object)], [array([0.2, 0.2, 0.2, 0.2, 0.2, 0.5, 0.8, 1.0, 1.0, 0.

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
- max duration: 0.424 s
- avg duration: 0.424 s
- min duration: 0.424 s
- total duration: 0.424 s

### Input
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x142CE0B0>*
- **locator** `['LocatorDecorator']`: *???*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.thermal_loads.BuildingPropertiesRow object at 0x068762B0>*
- **tsd** `['dict']`: *{'w_int': array([ 0.        ,  0.        ,  0.        , ...,  0.01493667,
        0.00403694,  0.0034314 ]), 'Im_tot': array([  45137.76324783,   45137.76324783,   44681.97079396, ...,
        318310.72756437,   86958.62143588,   63388.61365678]), 've': array([     0.        ,      0.        ,      0.        , ...,
        57276.68717357,  15480.18572259,  13158.1578642 ]), 'people': array([   0.        ,    0.        ,    0.        , ...,  632.61196348,
        170.97620635,  145.32977539]), 'T*
- **Ealf** `['ndarray']`: *array([ 45536.66295688,  45536.66295688,  45536.66295688, ...,
        89479.54271027,  75818.5438232 ,  51570.27079866])*
- **Ealf_0** `['float64']`: *420075.71577720094*
- **Ealf_tot** `['float64']`: *1255.887503351812*
- **Eauxf** `['ndarray']`: *array([  0.        ,   0.        ,   0.        , ...,  65.74432788,
         2.8770457 ,   2.65250507])*
- **Eauxf_tot** `['float64']`: *40.055689107389043*
- **Edata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Edata_tot** `['float64']`: *0.0*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eprof_tot** `['float64']`: *0.0*
- **building_name** `['str']`: *'Bau A'*
- **Occupancy** `['ndarray']`: *array([   0.,    0.,    0., ...,  632.,  170.,  145.])*
- **Occupants** `['float64']`: *5015.0*
- **Qcdata** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Qcrefri** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Qcs** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-3824434.2215403998*
- **Qhs** `['ndarray']`: *array([      0.        ,       0.        ,       0.        , ...,
        240853.03377428,       0.        ,       0.        ])*
- **Qhsf** `['ndarray']`: *array([      0.        ,       0.        ,       0.        , ...,
        345431.70390049,       0.        ,       0.        ])*
- **Qhsf_0** `['float64']`: *3592302.7665316463*
- **Qww** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        65956.42342807,  17826.06038597,  15152.15132807])*
- **Qwwf** `['ndarray']`: *array([     0.        ,      0.        ,      0.        , ...,
        68481.67061934,  18630.23145399,  15853.22938387])*
- **Qwwf_0** `['float64']`: *128049.69313257416*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re** `['ndarray']`: *array([ 0,  0,  0, ..., 29,  0,  0])*
- **Ths_sup** `['ndarray']`: *array([ 0,  0,  0, ..., 31,  0,  0])*
- **Vw** `['ndarray']`: *array([ 0.        ,  0.        ,  0.        , ...,  2.27455987,
        0.61474591,  0.52253402])*
- **Vww** `['ndarray']`: *array([ 0.        ,  0.        ,  0.        , ...,  1.13727993,
        0.30737296,  0.26126701])*
- **mcpcs** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcphs** `['ndarray']`: *array([     0,      0,      0, ..., 179615,      0,      0])*
- **mcpww** `['ndarray']`: *array([    0.        ,     0.        ,     0.        , ...,  1370.03632807,
         372.68378683,   317.11323267])*
- **date** `['DatetimeIndex']`: *DatetimeIndex(['2010-01-01 00:00:00', '2010-01-01 01:00:00',
               '2010-01-01 02:00:00', '2010-01-01 03:00:00',
               '2010-01-01 04:00:00', '2010-01-01 05:00:00',
               '2010-01-01 06:00:00', '2010-01-01 07:00:00',
               '2010-01-01 08:00:00', '2010-01-01 09:00:00',
               ...
               '2010-12-31 14:00:00', '2010-12-31 15:00:00',
               '2010-12-31 16:00:00', '2010-12-31 17:00:00',
               '2010-12-31 18:00:00', '2010-12-31 19:0*
- **mcpdataf** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcdataf_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcdataf_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcpref** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcref_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcref_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Qhprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ecaf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qhprof_tot** `['int']`: *0*
- **Ecaf_tot** `['int']`: *0*
- **Eaux_hs** `['ndarray']`: *array([  0.        ,   0.        ,   0.        , ...,  60.21021997,
         0.        ,   0.        ])*
- **Eaux_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eaux_ve** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eaux_ww** `['ndarray']`: *array([ 0.        ,  0.        ,  0.        , ...,  5.5341079 ,
        2.8770457 ,  2.65250507])*
- **Eaux_fw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eaf_0** `['float64']`: *333326.66308228462*
- **Elf_0** `['float64']`: *86749.052694916332*
- **Eaf_tot** `['float64']`: *996.536517052627*
- **Elf_tot** `['float64']`: *259.35098629918525*


### Output
- `['NoneType']`: None

### Docstring template

```
PARAMETERS
----------

:param gv:
:type gv: GlobalVariables

:param locator:
:type locator: LocatorDecorator

:param bpr:
:type bpr: BuildingPropertiesRow

:param tsd:
:type tsd: dict

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

:param Eprof:
:type Eprof: ndarray

:param Eprof_tot:
:type Eprof_tot: float64

:param building_name:
:type building_name: str

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

:param Vww:
:type Vww: ndarray

:param mcpcs:
:type mcpcs: ndarray

:param mcphs:
:type mcphs: ndarray

:param mcpww:
:type mcpww: ndarray

:param date:
:type date: DatetimeIndex

:param mcpdataf:
:type mcpdataf: ndarray

:param Tcdataf_re:
:type Tcdataf_re: ndarray

:param Tcdataf_sup:
:type Tcdataf_sup: ndarray

:param mcpref:
:type mcpref: ndarray

:param Tcref_re:
:type Tcref_re: ndarray

:param Tcref_sup:
:type Tcref_sup: ndarray

:param Qhprof:
:type Qhprof: ndarray

:param Ecaf:
:type Ecaf: ndarray

:param Qhprof_tot:
:type Qhprof_tot: int

:param Ecaf_tot:
:type Ecaf_tot: int

:param Eaux_hs:
:type Eaux_hs: ndarray

:param Eaux_cs:
:type Eaux_cs: ndarray

:param Eaux_ve:
:type Eaux_ve: ndarray

:param Eaux_ww:
:type Eaux_ww: ndarray

:param Eaux_fw:
:type Eaux_fw: ndarray

:param Eaf_0:
:type Eaf_0: float64

:param Elf_0:
:type Elf_0: float64

:param Eaf_tot:
:type Eaf_tot: float64

:param Elf_tot:
:type Elf_tot: float64

RETURNS
-------

:returns:
:rtype: NoneType

INPUT / OUTPUT FILES
--------------------

- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau A.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau AT.csv
```

[TOC](#table-of-contents)
---

# run_as_script
- number of invocations: 1
- max duration: 73.98 s
- avg duration: 73.98 s
- min duration: 73.98 s
- total duration: 73.98 s

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
- max duration: 0.735 s
- avg duration: 0.735 s
- min duration: 0.735 s
- total duration: 0.735 s

### Input
- **dates** `['DatetimeIndex']`: *DatetimeIndex(['2010-01-01 00:00:00', '2010-01-01 01:00:00',
               '2010-01-01 02:00:00', '2010-01-01 03:00:00',
               '2010-01-01 04:00:00', '2010-01-01 05:00:00',
               '2010-01-01 06:00:00', '2010-01-01 07:00:00',
               '2010-01-01 08:00:00', '2010-01-01 09:00:00',
               ...
               '2010-12-31 14:00:00', '2010-12-31 15:00:00',
               '2010-12-31 16:00:00', '2010-12-31 17:00:00',
               '2010-12-31 18:00:00', '2010-12-31 19:0*
- **locator** `['LocatorDecorator']`: *???*
- **list_uses** `['list']`: *[u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM']*


### Output
- `['list']`: [([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 

### Docstring template

```
PARAMETERS
----------

:param dates:
:type dates: DatetimeIndex

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
```

[TOC](#table-of-contents)
---

# thermal_loads_all_buildings
- number of invocations: 1
- max duration: 70.157 s
- avg duration: 70.157 s
- min duration: 70.157 s
- total duration: 70.157 s

### Input
- **building_properties** `['BuildingProperties']`: *<cea.demand.thermal_loads.BuildingProperties object at 0x143CCBD0>*
- **date** `['DatetimeIndex']`: *DatetimeIndex(['2010-01-01 00:00:00', '2010-01-01 01:00:00',
               '2010-01-01 02:00:00', '2010-01-01 03:00:00',
               '2010-01-01 04:00:00', '2010-01-01 05:00:00',
               '2010-01-01 06:00:00', '2010-01-01 07:00:00',
               '2010-01-01 08:00:00', '2010-01-01 09:00:00',
               ...
               '2010-12-31 14:00:00', '2010-12-31 15:00:00',
               '2010-12-31 16:00:00', '2010-12-31 17:00:00',
               '2010-12-31 18:00:00', '2010-12-31 19:0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x143CC9F0>*
- **locator** `['LocatorDecorator']`: *???*
- **num_buildings** `['int']`: *24*
- **usage_schedules** `['dict']`: *{'list_uses': [u'INDUSTRIAL', u'OFFICE', u'PARKING', u'RESTAURANT', u'SERVERROOM'], 'schedules': [([0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.16000000000000003, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.8, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.4, 0.4, 0.16000000000000003, 0.16000000000000003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0*
- **weather_data** `['DataFrame']`: *(8760, 3)*

#### weather_data:
```
         drybulb_C  relhum_percent   windspd_ms
count  8760.000000     8760.000000  8760.000000
mean     10.150000       73.861644     1.838094
std       8.022269       15.889964     1.847214
min     -10.300000       28.000000     0.000000
25%       3.700000       62.000000     0.500000
50%      10.400000       77.000000     1.300000
75%      16.100000       86.000000     2.500000
max      32.300000      100.000000    15.300000
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

- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 17.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 17T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 22.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 22T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 19.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 19T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 06.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 06T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 02.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 02T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 05.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 05T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 03.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 03T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 04.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 04T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 16.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 16T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 14.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 14T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 07.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 07T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 17h.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 17hT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 02h.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 02hT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 06h.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 06hT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau 26.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 26T.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau D.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau DT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau E.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau ET.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau F.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau FT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau C.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau CT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau B.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau BT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau I.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau IT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau H.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau HT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
- get_demand_results_file: c:\reference-case-zug\baseline\outputs\data\demand\Bau G.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau GT.csv
- get_demand_results_folder: c:\reference-case-zug\baseline\outputs\data\demand
```

[TOC](#table-of-contents)
---

# write_totals_csv
- number of invocations: 1
- max duration: 0.973 s
- avg duration: 0.973 s
- min duration: 0.973 s
- total duration: 0.973 s

### Input
- **building_properties** `['BuildingProperties']`: *<cea.demand.thermal_loads.BuildingProperties object at 0x067D95B0>*
- **locator** `['LocatorDecorator']`: *???*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x06890530>*


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

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: NoneType

INPUT / OUTPUT FILES
--------------------

- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau AT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 17T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 22T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 19T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 06T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 02T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 05T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 03T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 04T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 16T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 14T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 07T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 17hT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 02hT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 06hT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau 26T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau DT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau ET.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau FT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau CT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau BT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau IT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau HT.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\Bau GT.csv
- get_total_demand: c:\reference-case-zug\baseline\outputs\data\demand\Total_demand.csv
```

[TOC](#table-of-contents)
---

