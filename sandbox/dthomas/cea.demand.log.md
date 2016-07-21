# Table of contents
- [test_demand](#test_demand)
   - [demand_calculation](#demand_calculation)
      - [get_temperatures](#get_temperatures)
      - [get_prop_RC_model](#get_prop_rc_model)
         - [lookup_effective_mass_area_factor](#lookup_effective_mass_area_factor)
         - [lookup_specific_heat_capacity](#lookup_specific_heat_capacity)
      - [create_windows](#create_windows)
         - [calc_thermal_loads_new_ventilation](#calc_thermal_loads_new_ventilation)
            - [calc_occ_schedule](#calc_occ_schedule)
            - [calc_Qint](#calc_Qint)
            - [calc_occ](#calc_occ)
            - [get_internal_comfort](#get_internal_comfort)
            - [get_properties_building_envelope](#get_properties_building_envelope)
            - [get_properties_building_systems](#get_properties_building_systems)
               - [calculate_pipe_transmittance_values](#calculate_pipe_transmittance_values)
               - [Calc_form](#calc_form)
                  - [calc_qv_req](#calc_qv_req)
            - [calc_I_sol](#calc_I_sol)
               - [Calc_Rf_sh](#calc_rf_sh)
                  - [calc_gl](#calc_gl)
            - [calc_Qint_sen](#calc_Qint_sen)
            - [calc_comp_heat_gains_sensible](#calc_comp_heat_gains_sensible)
            - [calc_Qint_lat](#calc_Qint_lat)
            - [calc_Qhs_Qcs_sys_max](#calc_Qhs_Qcs_sys_max)
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
               - [calc_Qhs_Qcs](#calc_tl)
                  - [Calc_Im_tot](#calc_im_tot)
                  - [Calc_Tm](#calc_tm)
            - [calc_thermal_load_hvac_timestep](#calc_thermal_load_hvac_timestep)
               - [calc_hex](#calc_hex)
                  - [calc_w](#calc_w)
               - [calc_hvac](#calc_hvac)
                  - [calc_h](#calc_h)
                  - [calc_w3_cooling_case](#calc_w3_cooling_case)
                     - [calc_Qhs_Qcs_dis_ls](#calc_qdis_ls)
            - [calc_temperatures_emission_systems](#calc_temperatures_emission_systems)
               - [calc_RAD](#calc_rad)
               - [calc_Ccoil2](#calc_ccoil2)
            - [calc_dhw_heating_demand](#calc_dhw_heating_demand)
               - [calc_Qww_ls_r](#calc_qww_ls_r)
                  - [calc_disls](#calc_disls)
               - [calc_Qww_ls_nr](#calc_qww_ls_nr)
            - [calc_pumping_systems_aux_loads](#calc_pumping_systems_aux_loads)
               - [calc_Eauxf_ww](#calc_eaux_ww)
               - [calc_Eauxf_hs_dis](#calc_eaux_hs_dis)
               - [calc_Eauxf_cs_dis](#calc_eaux_cs_dis)
                  - [calc_Eauxf_fw](#calc_eaux_fw)
               - [calc_Eauxf_ve](#calc_eaux_ve)
            - [calc_loads_electrical](#calc_loads_electrical)
            - [results_to_csv](#results_to_csv)

# Calc_Im_tot
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **I_m** `['float64']`: *79762.919602934169*
- **Htr_em** `['float64']`: *4708.7054243215807*
- **te_t** `['float64']`: *8.8000000000000007*
- **Htr_3** `['float64']`: *14625.726582316747*
- **I_st** `['float64']`: *-33997.131577193883*
- **Htr_w** `['float64']`: *3194.4897685939245*
- **Htr_1** `['float64']`: *11601.839189961052*
- **I_ia** `['float64']`: *45966.658539909738*
- **IHC_nd** `['int']`: *0*
- **Hve** `['float64']`: *12108.73617821176*
- **Htr_2** `['float64']`: *14796.328958554977*


### Output
- `['float64']`: 259835.36548415307

### Docstring template

```
PARAMETERS
----------

:param I_m:
:type I_m: float64

:param Htr_em:
:type Htr_em: float64

:param te_t:
:type te_t: float64

:param Htr_3:
:type Htr_3: float64

:param I_st:
:type I_st: float64

:param Htr_w:
:type Htr_w: float64

:param Htr_1:
:type Htr_1: float64

:param I_ia:
:type I_ia: float64

:param IHC_nd:
:type IHC_nd: int

:param Hve:
:type Hve: float64

:param Htr_2:
:type Htr_2: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# Calc_Rf_sh
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **ShadingType** `['unicode']`: *u'T1'*


### Output
- `['float64']`: 0.080000000000000002

### Docstring template

```
PARAMETERS
----------

:param ShadingType:
:type ShadingType: unicode

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# Calc_Tm
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **Htr_3** `['float64']`: *14625.726582316747*
- **Htr_1** `['float64']`: *11601.839189961052*
- **tm_t0** `['int']`: *16*
- **Cm** `['float64']`: *9200022633.5336075*
- **Htr_em** `['float64']`: *4708.7054243215807*
- **Im_tot** `['float64']`: *259835.36548415307*
- **Htr_ms** `['float64']`: *1268487.9691690276*
- **I_st** `['float64']`: *-33997.131577193883*
- **Htr_w** `['float64']`: *3194.4897685939245*
- **te_t** `['float64']`: *8.8000000000000007*
- **I_ia** `['float64']`: *45966.658539909738*
- **IHC_nd** `['int']`: *0*
- **Hve** `['float64']`: *12108.73617821176*
- **Htr_is** `['float64']`: *277144.29793335864*


### Output
- `['tuple']`: (15.990348708538315, 15.915271425714591, 15.776326345626217, 15.872198450887193)

### Docstring template

```
PARAMETERS
----------

:param Htr_3:
:type Htr_3: float64

:param Htr_1:
:type Htr_1: float64

:param tm_t0:
:type tm_t0: int

:param Cm:
:type Cm: float64

:param Htr_em:
:type Htr_em: float64

:param Im_tot:
:type Im_tot: float64

:param Htr_ms:
:type Htr_ms: float64

:param I_st:
:type I_st: float64

:param Htr_w:
:type Htr_w: float64

:param te_t:
:type te_t: float64

:param I_ia:
:type I_ia: float64

:param IHC_nd:
:type IHC_nd: int

:param Hve:
:type Hve: float64

:param Htr_is:
:type Htr_is: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# Calc_form
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **Lw** `['float64']`: *75.297589090599999*
- **Ll** `['float64']`: *149.94902371500001*
- **footprint** `['float64']`: *7744.1267959037104*


### Output
- `['float64']`: 0.68587937213939387

### Docstring template

```
PARAMETERS
----------

:param Lw:
:type Lw: float64

:param Ll:
:type Ll: float64

:param footprint:
:type footprint: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# allocate_default_leakage_paths
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **coeff_lea_zone** `['float64']`: *20514.548494838626*
- **area_facade_zone** `['float64']`: *8123.2973337619205*
- **area_roof_zone** `['float64']`: *7744.1267959037104*
- **height_zone** `['float64']`: *18.0*


### Output
- `['tuple']`: (array([  2625.59593368,   2625.59593368,   2625.59593368,   2625.59593368,
        10012.16476011]), array([  4.5,   4.5,  13.5,  13.5,  18. ]), array([ 0.,  1.,  0.,  1.,  2.]))

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
- **height_zone** `['float64']`: *18.0*


### Output
- `['tuple']`: (array([ 0.,  0.,  0.,  0.]), array([  4.5,   4.5,  13.5,  13.5]), array([ 0.,  1.,  0.,  1.]))

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

# calc_Ccoil2
- number of invocations: 1
- max duration: 0.039 s
- avg duration: 0.039 s
- min duration: 0.039 s
- total duration: 0.039 s

### Input
- **Qc** `['float64']`: *-0*
- **tasup** `['float64']`: *273.0*
- **tare** `['float64']`: *273.0*
- **Qc0** `['float64']`: *-6904323.8309259824*
- **tare_0** `['float64']`: *299.69999999999999*
- **tasup_0** `['float64']`: *288.5*
- **tsc0** `['int64']`: *280*
- **trc0** `['int64']`: *288*
- **wr** `['float64']`: *0.0*
- **ws** `['float64']`: *0.0*
- **ma0** `['float64']`: *698.11904308609815*
- **ma** `['float64']`: *0.0*
- **Cpa** `['float64']`: *1.008*
- **LMRT0** `['float64']`: *5.2262449377670945*
- **UA0** `['float64']`: *-1321086.9205598016*
- **mCw0** `['float64']`: *863040.47886574781*
- **Qcsf** `['float64']`: *-0*


### Output
- `['tuple']`: (0, 0, 0)

### Docstring template

```
PARAMETERS
----------

:param Qc:
:type Qc: float64

:param tasup:
:type tasup: float64

:param tare:
:type tare: float64

:param Qc0:
:type Qc0: float64

:param tare_0:
:type tare_0: float64

:param tasup_0:
:type tasup_0: float64

:param tsc0:
:type tsc0: int64

:param trc0:
:type trc0: int64

:param wr:
:type wr: float64

:param ws:
:type ws: float64

:param ma0:
:type ma0: float64

:param ma:
:type ma: float64

:param Cpa:
:type Cpa: float64

:param LMRT0:
:type LMRT0: float64

:param UA0:
:type UA0: float64

:param mCw0:
:type mCw0: float64

:param Qcsf:
:type Qcsf: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Eauxf_cs_dis
- number of invocations: 1
- max duration: 0.042 s
- avg duration: 0.042 s
- min duration: 0.042 s
- total duration: 0.042 s

### Input
- **Qcsf** `['float64']`: *-0*
- **Qcsf0** `['float64']`: *-6904323.8309259824*
- **Imax** `['float64']`: *283.40236374748633*
- **deltaP_des** `['float64']`: *36.842307287173227*
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
- max duration: 0.043 s
- avg duration: 0.043 s
- min duration: 0.043 s
- total duration: 0.043 s

### Input
- **freshw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **nf** `['float64']`: *6.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x056503D0>*


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
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **Qhsf** `['float64']`: *0.0*
- **Qhsf0** `['float64']`: *2904139.1739979726*
- **Imax** `['float64']`: *283.40236374748633*
- **deltaP_des** `['float64']`: *36.842307287173227*
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
- max duration: 0.046 s
- avg duration: 0.046 s
- min duration: 0.046 s
- total duration: 0.046 s

### Input
- **Qhsf** `['float64']`: *0.0*
- **Qcsf** `['float64']`: *-0*
- **P_ve** `['float64']`: *0.55000000000000004*
- **qve** `['float64']`: *10.010529247860251*
- **SystemH** `['unicode_']`: *u'T1'*
- **SystemC** `['unicode_']`: *u'T3'*
- **Af** `['float64']`: *55757.712930506714*


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

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# calc_Eauxf_ww
- number of invocations: 1
- max duration: 0.04 s
- avg duration: 0.04 s
- min duration: 0.04 s
- total duration: 0.04 s

### Input
- **Qww** `['float64']`: *0.0*
- **Qwwf** `['float64']`: *0.0*
- **Qwwf0** `['float64']`: *4302122.6581722982*
- **Imax** `['float64']`: *283.40236374748633*
- **deltaP_des** `['float64']`: *36.842307287173227*
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

# calc_Htr
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **Hve** `['float64']`: *12108.73617821176*
- **Htr_is** `['float64']`: *277144.29793335864*
- **Htr_ms** `['float64']`: *1268487.9691690276*
- **Htr_w** `['float64']`: *3194.4897685939245*


### Output
- `['tuple']`: (11601.839189961052, 14796.328958554977, 14625.726582316747)

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

# calc_Qhs_Qcs_dis_ls
- number of invocations: 1
- max duration: 0.033 s
- avg duration: 0.033 s
- min duration: 0.033 s
- total duration: 0.033 s

### Input
- **tair** `['float64']`: *15.776326345626217*
- **text** `['float64']`: *8.8000000000000007*
- **Qhs** `['float64']`: *0.0*
- **Qcs** `['float64']`: *0.0*
- **tsh** `['int64']`: *90*
- **trh** `['int64']`: *70*
- **tsc** `['int64']`: *7*
- **trc** `['int64']`: *15*
- **Qhs_max** `['float64']`: *2897029.1739979726*
- **Qcs_max** `['float64']`: *-3882983.136141208*
- **D** `['int32']`: *20*
- **Y** `['float64']`: *0.20000000000000001*
- **SystemH** `['unicode_']`: *u'T1'*
- **SystemC** `['unicode_']`: *u'T3'*
- **Bf** `['float64']`: *0.69999999999999996*
- **Lv** `['float64']`: *461.49328157682544*


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

# calc_Qww_ls_nr
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **tair** `['float64']`: *15.776326345626217*
- **Qww** `['float64']`: *0.0*
- **Lvww_dis** `['float64']`: *586.85486698254124*
- **Lvww_c** `['float64']`: *302.49546942591496*
- **Y** `['float64']`: *0.20000000000000001*
- **Qww_0** `['float64']`: *4292895.6648421632*
- **V** `['float64']`: *2353.3874187719634*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **Bf** `['float64']`: *0.69999999999999996*
- **te** `['float64']`: *8.8000000000000007*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0553A3B0>*


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

# calc_Qww_ls_r
- number of invocations: 1
- max duration: 0.099 s
- avg duration: 0.099 s
- min duration: 0.099 s
- total duration: 0.099 s

### Input
- **Tair** `['float64']`: *15.776326345626217*
- **Qww** `['float64']`: *0.0*
- **lsww_dis** `['float64']`: *5296.9827283981376*
- **lcww_dis** `['float64']`: *233.81493873483373*
- **Y** `['float64']`: *0.29999999999999999*
- **Qww_0** `['float64']`: *4292895.6648421632*
- **V** `['float64']`: *2353.3874187719634*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0564C470>*


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

# calc_RAD
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **Qh** `['float64']`: *0.0*
- **tair** `['float64']`: *15.776326345626217*
- **Qh0** `['float64']`: *2904139.1739979726*
- **tair0** `['float64']`: *22.0*
- **tsh0** `['int64']`: *90*
- **trh0** `['int64']`: *70*
- **nh** `['float64']`: *0.29999999999999999*


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
:type tsh0: int64

:param trh0:
:type trh0: int64

:param nh:
:type nh: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Qhs_Qcs
- number of invocations: 1
- max duration: 0.146 s
- avg duration: 0.146 s
- min duration: 0.146 s
- total duration: 0.146 s

### Input
- **SystemH** `['unicode']`: *u'T1'*
- **SystemC** `['unicode']`: *u'T3'*
- **tm_t0** `['int']`: *16*
- **te_t** `['float64']`: *8.8000000000000007*
- **tintH_set** `['float64']`: *12.0*
- **tintC_set** `['int32']`: *50*
- **Htr_em** `['float64']`: *4708.7054243215807*
- **Htr_ms** `['float64']`: *1268487.9691690276*
- **Htr_is** `['float64']`: *277144.29793335864*
- **Htr_1** `['float64']`: *11601.839189961052*
- **Htr_2** `['float64']`: *14796.328958554977*
- **Htr_3** `['float64']`: *14625.726582316747*
- **I_st** `['float64']`: *-33997.131577193883*
- **Hve** `['float64']`: *12108.73617821176*
- **Htr_w** `['float64']`: *3194.4897685939245*
- **I_ia** `['float64']`: *45966.658539909738*
- **I_m** `['float64']`: *79762.919602934169*
- **Cm** `['float64']`: *9200022633.5336075*
- **Af** `['float64']`: *55757.712930506714*
- **Losses** `['bool']`: *False*
- **tHset_corr** `['float']`: *2.65*
- **tCset_corr** `['float']`: *-2.0*
- **IC_max** `['float64']`: *-27878856.465253357*
- **IH_max** `['float64']`: *27878856.465253357*
- **Flag** `['bool_']`: *False*


### Output
- `['tuple']`: (15.990348708538315, 15.776326345626217, 0, 0, 0, 15.872198450887193, 259835.36548415307)

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

# calc_Qhs_Qcs_sys_max
- number of invocations: 1
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

### Input
- **Af** `['float64']`: *55757.712930506714*
- **prop_HVAC** `['Series']`: *type_hs        T1
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
Name: B140577, dtype: object*


### Output
- `['tuple']`: (-27878856.465253357, 27878856.465253357)

### Docstring template

```
PARAMETERS
----------

:param Af:
:type Af: float64

:param prop_HVAC:
:type prop_HVAC: Series

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
- **qv_delta_p_lea_ref** `['float64']`: *278788.56465253356*


### Output
- `['float64']`: 20514.548494838626

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

# calc_comp_heat_gains_sensible
- number of invocations: 1
- max duration: 0.061 s
- avg duration: 0.061 s
- min duration: 0.061 s
- total duration: 0.061 s

### Input
- **Am** `['float64']`: *139394.28232626678*
- **Atot** `['float64']`: *80331.680560393797*
- **Htr_w** `['float64']`: *3194.4897685939245*
- **I_int_sen** `['ndarray']`: *array([ 91933.31707982,  91933.31707982,  91933.31707982, ...,
        68949.98780986,  68949.98780986,  68949.98780986])*
- **I_sol** `['Series']`: *T1         0.000000
T2         0.000000
T3         0.000000
T4         0.000000
T5         0.000000
T6         0.000000
T7         0.000000
T8       598.701915
T9      7497.095839
T10    19081.608777
T11    23639.153501
T12    14762.169418
T13     2986.138953
T14       13.374632
T15        0.000000
...
T8746    14001.022334
T8747    17210.649913
T8748    10077.431663
T8749     1683.731590
T8750        1.763559
T8751        0.000000
T8752        0.000000
T8753        0.000000
T8754        0.00000*


### Output
- `['tuple']`: (array([ 45966.65853991,  45966.65853991,  45966.65853991, ...,
        34474.99390493,  34474.99390493,  34474.99390493]), T1      79762.919603
T2      79762.919603
T3      79762.919603
T4      79762.919603
T5      79762.919603
T6      79762.919603
T7      79762.919603
T8     199265.804220
T9     409463.049689
T10    787317.648510
T11    833927.133101
T12    499471.807999
T13    242109.643659
T14    435178.117395
T15    792907.664641
...
T8746    589949.994055
T8747    624545.257429
T8748    37

### Docstring template

```
PARAMETERS
----------

:param Am:
:type Am: float64

:param Atot:
:type Atot: float64

:param Htr_w:
:type Htr_w: float64

:param I_int_sen:
:type I_int_sen: ndarray

:param I_sol:
:type I_sol: Series

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_dhw_heating_demand
- number of invocations: 1
- max duration: 0.7 s
- avg duration: 0.7 s
- min duration: 0.7 s
- total duration: 0.7 s

### Input
- **Af** `['float64']`: *55757.712930506714*
- **Lcww_dis** `['float64']`: *233.81493873483373*
- **Lsww_dis** `['float64']`: *5296.9827283981376*
- **Lvww_c** `['float64']`: *302.49546942591496*
- **Lvww_dis** `['float64']`: *586.85486698254124*
- **T_ext** `['ndarray']`: *array([ 8.8,  8.6,  8.4, ..., -0.3, -0.5, -0.7])*
- **Ta** `['ndarray']`: *array([ 15.77632635,  15.75592442,  15.73484567, ...,  16.78319779,
        16.7204114 ,  16.65710792])*
- **Tww_re** `['ndarray']`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_sup_0** `['int64']`: *60*
- **Y** `['list']`: *[0.2, 0.3, 0.3]*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0564C170>*
- **vw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **vww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['tuple']`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 1232.4372647 ,  1236.00437222,  1239.57628598, ...,  1384.34886103,
        1388.22274974,  1392.10021718]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 4302122.6581722982, array([ 59.99601267,  59.9920138 ,  59.98800338, ...,  59.98057898,
        59.97608763,  59.97158374]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0., 

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

:param vw:
:type vw: ndarray

:param vww:
:type vww: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_disls
- number of invocations: 1
- max duration: 0.041 s
- avg duration: 0.041 s
- min duration: 0.041 s
- total duration: 0.041 s

### Input
- **tamb** `['float64']`: *15.776326345626217*
- **hotw** `['float64']`: *0.0*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **V** `['float64']`: *2353.3874187719634*
- **twws** `['int64']`: *60*
- **Lsww_dis** `['float64']`: *5296.9827283981376*
- **p** `['int32']`: *998*
- **cpw** `['float64']`: *4.1840000000000002*
- **Y** `['float64']`: *0.29999999999999999*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BBCB330>*


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

# calc_gl
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **radiation** `['float64']`: *0.0*
- **g_gl** `['float64']`: *0.67500000000000004*
- **Rf_sh** `['float64']`: *0.080000000000000002*


### Output
- `['float64']`: 0.67500000000000004

### Docstring template

```
PARAMETERS
----------

:param radiation:
:type radiation: float64

:param g_gl:
:type g_gl: float64

:param Rf_sh:
:type Rf_sh: float64

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
- **t** `['int32']`: *24*
- **w** `['float64']`: *0.0057424260468282732*


### Output
- `['float64']`: 38.757393077345448

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
- **q_m_mech** `['float64']`: *12.012635097432302*
- **q_m_nat** `['int']`: *0*
- **temp_ext** `['float64']`: *8.8000000000000007*
- **temp_sup** `['float64']`: *8.8000000000000007*
- **temp_zone_set** `['int']`: *21*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BBCBB50>*


### Output
- `['float64']`: 12108.73617821176

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

# calc_Qint_lat
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

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

# calc_Qint_sen
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

### Input
- **people** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qs_Wp** `['float64']`: *70.0*
- **Eal_nove** `['ndarray']`: *array([ 102148.13008869,  102148.13008869,  102148.13008869, ...,
         76611.09756652,   76611.09756652,   76611.09756652])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcdata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['ndarray']`: array([ 91933.31707982,  91933.31707982,  91933.31707982, ...,
        68949.98780986,  68949.98780986,  68949.98780986])

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

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# calc_I_sol
- number of invocations: 1
- max duration: 0.196 s
- avg duration: 0.196 s
- min duration: 0.196 s
- total duration: 0.196 s

### Input
- **Aw** `['float64']`: *2457.2998219953265*
- **Awall_all** `['float64']`: *7926.7736193397632*
- **Sh_typ** `['unicode']`: *u'T1'*
- **Solar** `['Series']`: *T1          0.00
T2          0.00
T3          0.00
T4          0.00
T5          0.00
T6          0.00
T7          0.00
T8       4087.40
T9      51183.45
T10    130272.12
T11    161386.95
T12    100782.86
T13     20386.68
T14        91.31
T15         0.00
...
T8746     95586.43
T8747    117498.89
T8748     68799.67
T8749     11495.01
T8750        12.04
T8751         0.00
T8752         0.00
T8753         0.00
T8754         0.00
T8755         0.00
T8756         0.00
T8757         0.00
T8758        *
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05644570>*


### Output
- `['Series']`: T1         0.000000
T2         0.000000
T3         0.000000
T4         0.000000
T5         0.000000
T6         0.000000
T7         0.000000
T8       598.701915
T9      7497.095839
T10    19081.608777
T11    23639.153501
T12    14762.169418
T13     2986.138953
T14       13.374632
T15        0.000000
...
T8746    14001.022334
T8747    17210.649913
T8748    10077.431663
T8749     1683.731590
T8750        1.763559
T8751        0.000000
T8752        0.000000
T8753        0.000000
T8754        0.00000

### Docstring template

```
PARAMETERS
----------

:param Aw:
:type Aw: float64

:param Awall_all:
:type Awall_all: float64

:param Sh_typ:
:type Sh_typ: unicode

:param Solar:
:type Solar: Series

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: Series

```

[TOC](#table-of-contents)
---

# calc_hex
- number of invocations: 1
- max duration: 0.094 s
- avg duration: 0.094 s
- min duration: 0.094 s
- total duration: 0.094 s

### Input
- **rel_humidity_ext** `['int64']`: *73*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BBCBD50>*
- **qv_mech** `['float64']`: *10.010529247860251*
- **timestep** `['int']`: *3217*
- **temp_ext** `['float64']`: *8.1999999999999993*
- **qv_mech_dim** `['int']`: *0*
- **temp_zone_prev** `['float64']`: *23.207931924118423*


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

:param qv_mech:
:type qv_mech: float64

:param timestep:
:type timestep: int

:param temp_ext:
:type temp_ext: float64

:param qv_mech_dim:
:type qv_mech_dim: int

:param temp_zone_prev:
:type temp_zone_prev: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_hvac
- number of invocations: 1
- max duration: 0.03 s
- avg duration: 0.03 s
- min duration: 0.03 s
- total duration: 0.03 s

### Input
- **rhum_1** `['int64']`: *73*
- **temp_1** `['float64']`: *8.1999999999999993*
- **temp_zone_set** `['float64']`: *23.148449002889645*
- **qv_req** `['float64']`: *10.010529247860251*
- **qe_sen** `['int']`: *0*
- **temp_5_prev** `['float64']`: *23.207931924118423*
- **wint** `['float64']`: *0.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05654590>*
- **timestep** `['int']`: *3217*


### Output
- `['tuple']`: (0, 0, 0, 0, 0, 0, 0, nan, nan, 8.1999999999999993, 8.1999999999999993, 0, 0, 23.148449002889645)

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

# calc_loads_electrical
- number of invocations: 1
- max duration: 0.039 s
- avg duration: 0.039 s
- min duration: 0.039 s
- total duration: 0.039 s

### Input
- **Aef** `['float64']`: *55757.712930506714*
- **Ealf** `['ndarray']`: *array([ 102148.13008869,  102148.13008869,  102148.13008869, ...,
         76611.09756652,   76611.09756652,   76611.09756652])*
- **Eauxf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Edataf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['tuple']`: (array([ 102148.13008869,  102148.13008869,  102148.13008869, ...,
         76611.09756652,   76611.09756652,   76611.09756652]), 1021481.3008868831, 2335.5148463479386, 51.28295419225833, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0, array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), 0.0)

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

# calc_occ_schedule
- number of invocations: 1
- max duration: 0.545 s
- avg duration: 0.545 s
- min duration: 0.545 s
- total duration: 0.545 s

### Input
- **list_uses** `['list']`: *[u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL']*
- **schedules** `['list']`: *[([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.64000*
- **building_uses** `['Series']`: *GYM           0
HOSPITAL      0
HOTEL         0
INDUSTRIAL    0
MULTI_RES     0
OFFICE        1
PARKING       0
PFloor        1
RETAIL        0
Name: B140577, dtype: float64*


### Output
- `['DataFrame']`: (8760, 4)

### Docstring template

```
PARAMETERS
----------

:param list_uses:
:type list_uses: list

:param schedules:
:type schedules: list

:param building_uses:
:type building_uses: Series

RETURNS
-------

:returns:
:rtype: DataFrame

```

[TOC](#table-of-contents)
---

# calc_pumping_systems_aux_loads
- number of invocations: 1
- max duration: 0.452 s
- avg duration: 0.452 s
- min duration: 0.452 s
- total duration: 0.452 s

### Input
- **Af** `['float64']`: *55757.712930506714*
- **Ll** `['float64']`: *149.94902371500001*
- **Lw** `['float64']`: *75.297589090599999*
- **Mww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-6904323.8309259824*
- **Qhsf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qhsf_0** `['float64']`: *2904139.1739979726*
- **Qww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `['float64']`: *4302122.6581722982*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Vw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Year** `['int64']`: *1914*
- **fforma** `['float64']`: *0.68587937213939387*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BBE38F0>*
- **nf_ag** `['float64']`: *6.0*
- **nfp** `['float64']`: *1.0*
- **qv_req** `['ndarray']`: *array([ 10.01052925,  10.01052925,  10.01052925, ...,  10.01052925,
        10.01052925,  10.01052925])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*


### Output
- `['tuple']`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]))

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

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_qv_delta_p_ref
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **n_delta_p_ref** `['int64']`: *2*
- **vol_building** `['float64']`: *139394.28232626678*


### Output
- `['float64']`: 278788.56465253356

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

# calc_qv_req
- number of invocations: 1
- max duration: 0.034 s
- avg duration: 0.034 s
- min duration: 0.034 s
- total duration: 0.034 s

### Input
- **ve** `['float64']`: *0.0*
- **people** `['float64']`: *0.0*
- **Af** `['float64']`: *55757.712930506714*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0D0C50D0>*
- **hour_day** `['int32']`: *0*
- **hour_year** `['int32']`: *0*
- **n50** `['int64']`: *2*


### Output
- `['float64']`: 10.010529247860251

### Docstring template

```
PARAMETERS
----------

:param ve:
:type ve: float64

:param people:
:type people: float64

:param Af:
:type Af: float64

:param gv:
:type gv: GlobalVariables

:param hour_day:
:type hour_day: int32

:param hour_year:
:type hour_year: int32

:param n50:
:type n50: int64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calc_tHC_corr
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

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

# calc_temperatures_emission_systems
- number of invocations: 1
- max duration: 0.403 s
- avg duration: 0.403 s
- min duration: 0.403 s
- total duration: 0.403 s

### Input
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-6904323.8309259824*
- **Qhsf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qhsf_0** `['float64']`: *2904139.1739979726*
- **Ta** `['ndarray']`: *array([ 15.77632635,  15.75592442,  15.73484567, ...,  16.78319779,
        16.7204114 ,  16.65710792])*
- **Ta_re_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_re_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Ta_sup_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Tcs_re_0** `['int64']`: *15*
- **Tcs_sup_0** `['int64']`: *7*
- **Ths_re_0** `['int64']`: *70*
- **Ths_sup_0** `['int64']`: *90*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0D0C5730>*
- **ma_sup_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **ma_sup_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **ta_hs_set** `['ndarray']`: *array([ 12.,  12.,  12., ...,  12.,  12.,  12.])*
- **w_re** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **w_sup** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['tuple']`: (array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]), array([0, 0, 0, ..., 0, 0, 0]))

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

:param w_re:
:type w_re: ndarray

:param w_sup:
:type w_sup: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_thermal_load_hvac_timestep
- number of invocations: 1
- max duration: 0.25 s
- avg duration: 0.25 s
- min duration: 0.25 s
- total duration: 0.25 s

### Input
- **t** `['int']`: *3217*
- **thermal_loads_input** `['ThermalLoadsInput']`: *<cea.thermal_loads.ThermalLoadsInput object at 0x0BBE31D0>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **state_prev** `['dict']`: *{'temp_air_prev': 23.207931924118423, 'temp_m_prev': 23.897810477201745}*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0563E4B0>*

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
- `['tuple']`: (23.851764106477361, 23.148449002889645, 0, 0, 0, 23.513266047229571, 225811.61532373607, 0, 0, 0, 0, 0, 12.012635097432302, 0, 0, 0, 0, 0, 0, nan, nan, 8.1999999999999993, 8.1999999999999993, 0, 0)

### Docstring template

```
PARAMETERS
----------

:param t:
:type t: int

:param thermal_loads_input:
:type thermal_loads_input: ThermalLoadsInput

:param weather_data:
:type weather_data: DataFrame

:param state_prev:
:type state_prev: dict

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_thermal_load_mechanical_and_natural_ventilation_timestep
- number of invocations: 1
- max duration: 0.348 s
- avg duration: 0.348 s
- min duration: 0.348 s
- total duration: 0.348 s

### Input
- **t** `['int']`: *0*
- **thermal_loads_input** `['ThermalLoadsInput']`: *<cea.thermal_loads.ThermalLoadsInput object at 0x05654850>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **state_prev** `['dict']`: *{'temp_air_prev': 21, 'temp_m_prev': 16}*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0564B1F0>*

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
- `['tuple']`: (15.990348708538315, 15.776326345626217, 0, 0, 0, 15.872198450887193, 259835.36548415307, 12.012635097432302, 0, 0, 0, 0)

### Docstring template

```
PARAMETERS
----------

:param t:
:type t: int

:param thermal_loads_input:
:type thermal_loads_input: ThermalLoadsInput

:param weather_data:
:type weather_data: DataFrame

:param state_prev:
:type state_prev: dict

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_thermal_loads_new_ventilation
- number of invocations: 1
- max duration: 8.492 s
- avg duration: 8.492 s
- min duration: 8.492 s
- total duration: 8.492 s

### Input
- **Name** `['str']`: *'B140577'*
- **bpr** `['BuildingPropertiesRow']`: *<cea.demand.BuildingPropertiesRow object at 0x0D0B3230>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **usage_schedules** `['dict']`: *{'list_uses': [u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL'], 'schedules': [([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4,*
- **date** `['DatetimeIndex']`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05644570>*
- **results_folder** `['str']`: *'C:\\reference-case\\baseline\\outputs\\data\\demand'*
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

:param Name:
:type Name: str

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
- max duration: 0.032 s
- avg duration: 0.032 s
- min duration: 0.032 s
- total duration: 0.032 s

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
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **t5** `['int32']`: *24*
- **w2** `['float64']`: *0.0057424260468282732*
- **t3** `['float64']`: *15.6*
- **w5** `['float64']`: *0.0062009902000392655*


### Output
- `['float64']`: 0.0057424260468282732

### Docstring template

```
PARAMETERS
----------

:param t5:
:type t5: int32

:param w2:
:type w2: float64

:param t3:
:type t3: float64

:param w5:
:type w5: float64

RETURNS
-------

:returns:
:rtype: float64

```

[TOC](#table-of-contents)
---

# calculate_pipe_transmittance_values
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **year** `['int64']`: *1914*
- **Retrofit** `['int64']`: *1969*


### Output
- `['list']`: [0.2, 0.3, 0.3]

### Docstring template

```
PARAMETERS
----------

:param year:
:type year: int64

:param Retrofit:
:type Retrofit: int64

RETURNS
-------

:returns:
:rtype: list

```

[TOC](#table-of-contents)
---

# create_windows
- number of invocations: 1
- max duration: 0.831 s
- avg duration: 0.831 s
- min duration: 0.831 s
- total duration: 0.831 s

### Input
- **df_prop_surfaces** `['DataFrame']`: *(2140, 6)*
- **gdf_building_architecture** `['GeoDataFrame']`: *(1482, 6)*

#### df_prop_surfaces:
```
        Freeheight  FactorShade    height_ag   Shape_Leng        Awall
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
#### gdf_building_architecture:
```
           Occ_m2p       f_cros          n50       win_op     win_wall
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000
mean     28.795209     0.620783     2.563428     0.745344     0.235283
std      14.443868     0.485356     1.303021     0.194858     0.062597
min       0.000000     0.000000     2.000000     0.500000     0.100000
25%      14.000000     0.000000     2.000000     0.500000     0.210000
50%      40.000000     1.000000     2.000000     0.900000     0.210000
75%      40.000000     1.000000     2.000000     0.900000     0.310000
max      40.000000     1.000000     6.000000     0.900000     0.400000

[8 rows x 5 columns]
```

### Output
- `['DataFrame']`: (8749, 6)

### Docstring template

```
PARAMETERS
----------

:param df_prop_surfaces:
:type df_prop_surfaces: DataFrame

:param gdf_building_architecture:
:type gdf_building_architecture: GeoDataFrame

RETURNS
-------

:returns:
:rtype: DataFrame

```

[TOC](#table-of-contents)
---

# demand_calculation
- number of invocations: 1
- max duration: 48.288 s
- avg duration: 48.288 s
- min duration: 48.288 s
- total duration: 48.288 s

### Input
- **locator** `['InputLocator']`: *<cea.inputlocator.InputLocator object at 0x056550F0>*
- **weather_path** `['str']`: *'C:\\Users\\darthoma\\Documents\\GitHub\\CEAforArcGIS\\cea\\db\\CH\\Weather\\Zurich.epw'*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x056550F0>*


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

- get_radiation: C:\reference-case\baseline\outputs\data\solar-radiation\radiation.csv
- get_surface_properties: C:\reference-case\baseline\outputs\data\solar-radiation\properties_surfaces.csv
- get_building_geometry: C:\reference-case\baseline\inputs\building-geometry\zone.shp
- get_building_hvac: C:\reference-case\baseline\inputs\building-properties\technical_systems.shp
- get_building_thermal: C:\reference-case\baseline\inputs\building-properties\thermal_properties.shp
- get_building_occupancy: C:\reference-case\baseline\inputs\building-properties\occupancy.shp
- get_building_architecture: C:\reference-case\baseline\inputs\building-properties\architecture.shp
- get_building_age: C:\reference-case\baseline\inputs\building-properties\age.shp
- get_building_comfort: C:\reference-case\baseline\inputs\building-properties\indoor_comfort.shp
- get_building_internal: C:\reference-case\baseline\inputs\building-properties\internal_loads.shp
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_archetypes_schedules: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Archetypes\Archetypes_schedules.xlsx
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140577T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140571T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372467T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040197T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040204T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140570T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B2372562T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140557T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B302040335T.csv
- get_temporary_file: c:\users\darthoma\appdata\local\temp\B140558T.csv
- get_total_demand: C:\reference-case\baseline\outputs\data\demand\Total_demand.csv
```

[TOC](#table-of-contents)
---

# get_building_geometry_ventilation
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **gdf_building_geometry** `['Series']`: *Blength       149.949024
Bwidth         75.297589
floors_ag       6.000000
floors_bg       2.000000
height_ag      18.000000
height_bg       6.000000
footprint    7744.126796
perimeter     451.294296
Name: B140577, dtype: float64*


### Output
- `['tuple']`: (8123.2973337619205, 7744.1267959037104, 18.0, 0)

### Docstring template

```
PARAMETERS
----------

:param gdf_building_geometry:
:type gdf_building_geometry: Series

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# get_internal_comfort
- number of invocations: 1
- max duration: 0.037 s
- avg duration: 0.037 s
- min duration: 0.037 s
- total duration: 0.037 s

### Input
- **people** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **prop_comfort** `['Series']`: *Tcs_set_C     24
Tcs_setb_C    28
Ths_set_C     22
Ths_setb_C    12
Ve_lps        10
Name: B140577, dtype: float64*
- **limit_inf_season** `['int']`: *3217*
- **limit_sup_season** `['int']`: *6192*
- **weekday** `['ndarray']`: *array([4, 4, 4, ..., 4, 4, 4])*


### Output
- `['tuple']`: (array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 12.,  12.,  12., ...,  12.,  12.,  12.]), array([50, 50, 50, ..., 50, 50, 50]))

### Docstring template

```
PARAMETERS
----------

:param people:
:type people: ndarray

:param prop_comfort:
:type prop_comfort: Series

:param limit_inf_season:
:type limit_inf_season: int

:param limit_sup_season:
:type limit_sup_season: int

:param weekday:
:type weekday: ndarray

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_Qint
- number of invocations: 1
- max duration: 0.04 s
- avg duration: 0.04 s
- min duration: 0.04 s
- total duration: 0.04 s

### Input
- **mixed_schedule** `['DataFrame']`: *(8760, 4)*
- **prop_internal_loads** `['Series']`: *Ea_Wm2       7.0
Ed_Wm2       0.0
El_Wm2      15.9
Epro_Wm2     0.0
Ere_Wm2      0.0
Qs_Wp       70.0
Vw_lpd      20.0
Vww_lpd     10.0
X_ghp       80.0
Name: B140577, dtype: float64*
- **prop_architecture** `['Series']`: *Occ_m2p         14
f_cros           0
n50              2
type_shade      T1
win_op         0.5
win_wall      0.31
Name: B140577, dtype: object*
- **Af** `['float64']`: *55757.712930506714*

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
- `['tuple']`: (array([ 102148.13008869,  102148.13008869,  102148.13008869, ...,
         76611.09756652,   76611.09756652,   76611.09756652]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]), array([ 0.,  0.,  0., ...,  0.,  0.,  0.]))

### Docstring template

```
PARAMETERS
----------

:param mixed_schedule:
:type mixed_schedule: DataFrame

:param prop_internal_loads:
:type prop_internal_loads: Series

:param prop_architecture:
:type prop_architecture: Series

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# calc_occ
- number of invocations: 1
- max duration: 0.039 s
- avg duration: 0.039 s
- min duration: 0.039 s
- total duration: 0.039 s

### Input
- **mixed_schedule** `['DataFrame']`: *(8760, 4)*
- **prop_architecture** `['Series']`: *Occ_m2p         14
f_cros           0
n50              2
type_shade      T1
win_op         0.5
win_wall      0.31
Name: B140577, dtype: object*
- **Af** `['float64']`: *55757.712930506714*

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
- `['ndarray']`: array([ 0.,  0.,  0., ...,  0.,  0.,  0.])

### Docstring template

```
PARAMETERS
----------

:param mixed_schedule:
:type mixed_schedule: DataFrame

:param prop_architecture:
:type prop_architecture: Series

:param Af:
:type Af: float64

RETURNS
-------

:returns:
:rtype: ndarray

```

[TOC](#table-of-contents)
---

# get_prop_RC_model
- number of invocations: 1
- max duration: 0.225 s
- avg duration: 0.225 s
- min duration: 0.225 s
- total duration: 0.225 s

### Input
- **occupancy** `['GeoDataFrame']`: *(1482, 9)*
- **architecture** `['GeoDataFrame']`: *(1482, 6)*
- **thermal_properties** `['GeoDataFrame']`: *(1482, 7)*
- **geometry** `['GeoDataFrame']`: *(10, 8)*
- **hvac_temperatures** `['DataFrame']`: *(1482, 13)*
- **surface_properties** `['DataFrame']`: *(2140, 5)*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0563EBB0>*

#### occupancy:
```
               GYM     HOSPITAL        HOTEL   INDUSTRIAL    MULTI_RES  \
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000   
mean      0.000675     0.023617     0.027665     0.018219     0.613360   
std       0.025976     0.151903     0.164067     0.133786     0.487144   
min       0.000000     0.000000     0.000000     0.000000     0.000000   
25%       0.000000     0.000000     0.000000     0.000000     0.000000   
50%       0.000000     0.000000     0.000000     0.000000     1.000000   
75%       0.000000     0.000000     0.000000     0.000000     1.000000   
max       1.000000     1.000000     1.000000     1.000000     1.000000   

            OFFICE      PARKING  PFloor       RETAIL  
count  1482.000000  1482.000000    1482  1482.000000  
mean      0.256410     0.053306       1     0.006748  
std       0.436798     0.224719       0     0.081894  
min       0.000000     0.000000       1     0.000000  
25%       0.000000     0.000000       1     0.000000  
50%       0.000000     0.000000       1     0.000000  
75%       1.000000     0.000000       1     0.000000  
max       1.000000     1.000000       1     1.000000  

[8 rows x 9 columns]
```
#### architecture:
```
           Occ_m2p       f_cros          n50       win_op     win_wall
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000
mean     28.795209     0.620783     2.563428     0.745344     0.235283
std      14.443868     0.485356     1.303021     0.194858     0.062597
min       0.000000     0.000000     2.000000     0.500000     0.100000
25%      14.000000     0.000000     2.000000     0.500000     0.210000
50%      40.000000     1.000000     2.000000     0.900000     0.210000
75%      40.000000     1.000000     2.000000     0.900000     0.310000
max      40.000000     1.000000     6.000000     0.900000     0.400000

[8 rows x 5 columns]
```
#### thermal_properties:
```
                Es           Hs       U_base       U_roof       U_wall  \
count  1482.000000  1482.000000  1482.000000  1482.000000  1482.000000   
mean      0.850931     0.802955     0.437179     0.239170     0.263060   
std       0.038972     0.194194     0.458709     0.114598     0.227806   
min       0.820000     0.000000     0.280000     0.200000     0.200000   
25%       0.820000     0.820000     0.280000     0.200000     0.200000   
50%       0.820000     0.820000     0.280000     0.200000     0.200000   
75%       0.900000     0.900000     0.280000     0.200000     0.200000   
max       0.900000     0.900000     2.320000     1.000000     3.700000   

             U_win  
count  1482.000000  
mean      1.510391  
std       0.527412  
min       1.300000  
25%       1.300000  
50%       1.300000  
75%       1.300000  
max       4.300000  

[8 rows x 6 columns]
```
#### geometry:
```
          Blength     Bwidth  floors_ag  floors_bg  height_ag  height_bg  \
count   10.000000  10.000000  10.000000  10.000000  10.000000         10   
mean    34.907450  20.058049   3.500000   1.000000  10.500000          3   
std     41.070339  19.954174   1.433721   0.666667   4.301163          2   
min      7.035817   5.825479   1.000000   0.000000   3.000000          0   
25%     19.280715  11.565315   3.000000   1.000000   9.000000          3   
50%     24.260381  14.735675   3.500000   1.000000  10.500000          3   
75%     28.229976  16.441090   4.000000   1.000000  12.000000          3   
max    149.949024  75.297589   6.000000   2.000000  18.000000          6   

         footprint   perimeter  
count    10.000000   10.000000  
mean   1027.959244  110.830454  
std    2364.124064  121.634991  
min      40.413039   25.560532  
25%     205.954253   66.205409  
50%     292.598585   79.569010  
75%     454.350296   93.861137  
max    7744.126796  451.294296  

[8 rows x 8 columns]
```
#### hvac_temperatures:
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
#### surface_properties:
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
- `['DataFrame']`: (10, 15)

### Docstring template

```
PARAMETERS
----------

:param occupancy:
:type occupancy: GeoDataFrame

:param architecture:
:type architecture: GeoDataFrame

:param thermal_properties:
:type thermal_properties: GeoDataFrame

:param geometry:
:type geometry: GeoDataFrame

:param hvac_temperatures:
:type hvac_temperatures: DataFrame

:param surface_properties:
:type surface_properties: DataFrame

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: DataFrame

```

[TOC](#table-of-contents)
---

# get_properties_building_envelope
- number of invocations: 1
- max duration: 0.031 s
- avg duration: 0.031 s
- min duration: 0.031 s
- total duration: 0.031 s

### Input
- **prop_RC_model** `['Series']`: *Awall_all    7.926774e+03
Atot         8.033168e+04
Aw           2.457300e+03
Am           1.393943e+05
Aef          5.575771e+04
Af           5.575771e+04
Cm           9.200023e+09
Htr_is       2.771443e+05
Htr_em       4.708705e+03
Htr_ms       1.268488e+06
Htr_op       4.691291e+03
Hg           2.048571e+03
HD           2.642720e+03
Htr_w        3.194490e+03
GFA_m2       6.195301e+04
Name: B140577, dtype: float64*
- **prop_age** `['Series']`: *HVAC          1969
basement      1969
built         1914
envelope      1969
partitions    1969
roof          1969
windows       1969
Name: B140577, dtype: int64*
- **prop_architecture** `['Series']`: *Occ_m2p         14
f_cros           0
n50              2
type_shade      T1
win_op         0.5
win_wall      0.31
Name: B140577, dtype: object*
- **prop_geometry** `['Series']`: *Blength       149.949024
Bwidth         75.297589
floors_ag       6.000000
floors_bg       2.000000
height_ag      18.000000
height_bg       6.000000
footprint    7744.126796
perimeter     451.294296
Name: B140577, dtype: float64*
- **prop_occupancy** `['Series']`: *GYM           0
HOSPITAL      0
HOTEL         0
INDUSTRIAL    0
MULTI_RES     0
OFFICE        1
PARKING       0
PFloor        1
RETAIL        0
Name: B140577, dtype: float64*


### Output
- `['tuple']`: (139394.28232626678, 80331.680560393797, 2457.2998219953265, 7926.7736193397632, 9200022633.5336075, 149.94902371500001, 75.297589090599999, 1969, u'T1', 1914, 7744.1267959037104, 6.0, 2.0, 1.0)

### Docstring template

```
PARAMETERS
----------

:param prop_RC_model:
:type prop_RC_model: Series

:param prop_age:
:type prop_age: Series

:param prop_architecture:
:type prop_architecture: Series

:param prop_geometry:
:type prop_geometry: Series

:param prop_occupancy:
:type prop_occupancy: Series

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# get_properties_building_systems
- number of invocations: 1
- max duration: 0.142 s
- avg duration: 0.142 s
- min duration: 0.142 s
- total duration: 0.142 s

### Input
- **Ll** `['float64']`: *149.94902371500001*
- **Lw** `['float64']`: *75.297589090599999*
- **Retrofit** `['int64']`: *1969*
- **Year** `['int64']`: *1914*
- **footprint** `['float64']`: *7744.1267959037104*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x056533F0>*
- **nf_ag** `['float64']`: *6.0*
- **nfp** `['float64']`: *1.0*
- **nf_bg** `['float64']`: *2.0*
- **prop_HVAC** `['Series']`: *type_hs        T1
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
Name: B140577, dtype: object*


### Output
- `['tuple']`: (233.81493873483373, 5296.9827283981376, 461.49328157682544, 302.49546942591496, 586.85486698254124, 15, 7, 70, 90, 10, 60, [0.2, 0.3, 0.3], 0.68587937213939387)

### Docstring template

```
PARAMETERS
----------

:param Ll:
:type Ll: float64

:param Lw:
:type Lw: float64

:param Retrofit:
:type Retrofit: int64

:param Year:
:type Year: int64

:param footprint:
:type footprint: float64

:param gv:
:type gv: GlobalVariables

:param nf_ag:
:type nf_ag: float64

:param nfp:
:type nfp: float64

:param nf_bg:
:type nf_bg: float64

:param prop_HVAC:
:type prop_HVAC: Series

RETURNS
-------

:returns:
:rtype: tuple

```

[TOC](#table-of-contents)
---

# get_properties_natural_ventilation
- number of invocations: 1
- max duration: 0.426 s
- avg duration: 0.426 s
- min duration: 0.426 s
- total duration: 0.426 s

### Input
- **gdf_geometry_building** `['Series']`: *Blength       149.949024
Bwidth         75.297589
floors_ag       6.000000
floors_bg       2.000000
height_ag      18.000000
height_bg       6.000000
footprint    7744.126796
perimeter     451.294296
Name: B140577, dtype: float64*
- **gdf_architecture_building** `['Series']`: *Occ_m2p         14
f_cros           0
n50              2
type_shade      T1
win_op         0.5
win_wall      0.31
Name: B140577, dtype: object*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05653410>*


### Output
- `['dict']`: {'coeff_wind_pressure_path_vent': array([ 0.05, -0.05,  0.05, -0.05]), 'coeff_vent_path': array([ 0.,  0.,  0.,  0.]), 'height_vent_path': array([  4.5,   4.5,  13.5,  13.5]), 'coeff_lea_path': array([  2625.59593368,   2625.59593368,   2625.59593368,   2625.59593368,
        10012.16476011]), 'factor_cros': 0, 'height_lea_path': array([  4.5,   4.5,  13.5,  13.5,  18. ]), 'coeff_wind_pressure_path_lea': array([ 0.05, -0.05,  0.05, -0.05,  0.  ])}

### Docstring template

```
PARAMETERS
----------

:param gdf_geometry_building:
:type gdf_geometry_building: Series

:param gdf_architecture_building:
:type gdf_architecture_building: Series

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

- get_technical_emission_systems: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Systems\emission_systems.xls
- get_technical_emission_systems: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Systems\emission_systems.xls
- get_technical_emission_systems: C:\Users\darthoma\Documents\GitHub\CEAforArcGIS\cea\db\CH\Systems\emission_systems.xls
```

[TOC](#table-of-contents)
---

# lookup_coeff_wind_pressure
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **height_path** `['ndarray']`: *array([  4.5,   4.5,  13.5,  13.5,  18. ])*
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

# lookup_effective_mass_area_factor
- number of invocations: 1
- max duration: 0.028 s
- avg duration: 0.028 s
- min duration: 0.028 s
- total duration: 0.028 s

### Input
- **th_mass** `['unicode']`: *u'T2'*


### Output
- `['float']`: 2.5

### Docstring template

```
PARAMETERS
----------

:param th_mass:
:type th_mass: unicode

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# lookup_specific_heat_capacity
- number of invocations: 1
- max duration: 0.029 s
- avg duration: 0.029 s
- min duration: 0.029 s
- total duration: 0.029 s

### Input
- **th_mass** `['unicode']`: *u'T2'*


### Output
- `['float']`: 165000.0

### Docstring template

```
PARAMETERS
----------

:param th_mass:
:type th_mass: unicode

RETURNS
-------

:returns:
:rtype: float

```

[TOC](#table-of-contents)
---

# results_to_csv
- number of invocations: 1
- max duration: 0.229 s
- avg duration: 0.229 s
- min duration: 0.229 s
- total duration: 0.229 s

### Input
- **GFA_m2** `['float64']`: *61953.014367229684*
- **Af** `['float64']`: *55757.712930506714*
- **Ealf** `['ndarray']`: *array([ 102148.13008869,  102148.13008869,  102148.13008869, ...,
         76611.09756652,   76611.09756652,   76611.09756652])*
- **Ealf_0** `['float64']`: *1021481.3008868831*
- **Ealf_tot** `['float64']`: *2335.5148463479386*
- **Eauxf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eauxf_tot** `['float64']`: *51.28295419225833*
- **Edata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Edata_tot** `['float64']`: *0.0*
- **Epro** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Epro_tot** `['float64']`: *0.0*
- **Name** `['str']`: *'B140577'*
- **Occupancy** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Occupants** `['float64']`: *3186.0*
- **Qcdata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcs** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf** `['ndarray']`: *array([-0., -0., -0., ..., -0., -0., -0.])*
- **Qcsf_0** `['float64']`: *-6904323.8309259824*
- **Qhs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qhsf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qhsf_0** `['float64']`: *2904139.1739979726*
- **Qww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qww_ls_st** `['ndarray']`: *array([ 1232.4372647 ,  1236.00437222,  1239.57628598, ...,  1384.34886103,
        1388.22274974,  1392.10021718])*
- **Qwwf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `['float64']`: *4302122.6581722982*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_re_0** `['int64']`: *15*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup_0** `['int64']`: *7*
- **Ths_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re_0** `['int64']`: *70*
- **Ths_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_sup_0** `['int64']`: *90*
- **Tww_re** `['ndarray']`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_st** `['ndarray']`: *array([ 59.99601267,  59.9920138 ,  59.98800338, ...,  59.98057898,
        59.97608763,  59.97158374])*
- **Tww_sup_0** `['int64']`: *60*
- **Waterconsumption** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **locationFinal** `['str']`: *'C:\\reference-case\\baseline\\outputs\\data\\demand'*
- **mcpcs** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcphs** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcpww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **path_temporary_folder** `['str']`: *'c:\\users\\darthoma\\appdata\\local\\temp'*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **waterpeak** `['float64']`: *222.06589651719963*
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

# test_demand
- number of invocations: 1
- max duration: 48.38 s
- avg duration: 48.38 s
- min duration: 48.38 s
- total duration: 48.38 s

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

