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

### Input
- **x** `['unicode']`: *u'T3'*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param x:
:type x: unicode

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# Calc_Im_tot
- number of invocations: 1

### Input
- **I_m** `['float64']`: *2724.4521715126948*
- **Htr_em** `['float64']`: *582.9963349687813*
- **te_t** `['float64']`: *8.8000000000000007*
- **Htr_3** `['float64']`: *2590.6666958115343*
- **I_st** `['float64']`: *-994.95409442637401*
- **Htr_w** `['float64']`: *1403.3742289273969*
- **Htr_1** `['float64']`: *1297.9787346036153*
- **I_ia** `['float64']`: *1789.9699685754961*
- **IHC_nd** `['int']`: *0*
- **Hve** `['float64']`: *1414.5649132349504*
- **Htr_2** `['float64']`: *2701.3529635310124*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# Calc_Rf_sh
- number of invocations: 1

### Input
- **ShadingType** `['unicode']`: *u'T1'*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param ShadingType:
:type ShadingType: unicode

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# Calc_Tm
- number of invocations: 1

### Input
- **Htr_3** `['float64']`: *2590.6666958115343*
- **Htr_1** `['float64']`: *1297.9787346036153*
- **tm_t0** `['int']`: *16*
- **Cm** `['float64']`: *651371895.40593004*
- **Htr_em** `['float64']`: *582.9963349687813*
- **Im_tot** `['float64']`: *31273.645775067431*
- **Htr_ms** `['float64']`: *63226.498647402281*
- **I_st** `['float64']`: *-994.95409442637401*
- **Htr_w** `['float64']`: *1403.3742289273969*
- **te_t** `['float64']`: *8.8000000000000007*
- **I_ia** `['float64']`: *1789.9699685754961*
- **IHC_nd** `['int']`: *0*
- **Hve** `['float64']`: *1414.5649132349504*
- **Htr_is** `['float64']`: *15748.652178585824*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# Calc_form
- number of invocations: 1

### Input
- **Lw** `['float64']`: *16.008581384100001*
- **Ll** `['float64']`: *32.648092418099999*
- **footprint** `['float64']`: *402.0814169172408*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# CmFunction
- number of invocations: 1

### Input
- **x** `['unicode']`: *u'T3'*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param x:
:type x: unicode

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# allocate_default_leakage_paths
- number of invocations: 1

### Input
- **coeff_lea_zone** `['float64']`: *2130.2643780536373*
- **area_facade_zone** `['float64']`: *1237.0067791693345*
- **area_roof_zone** `['float64']`: *402.0814169172408*
- **height_zone** `['float64']`: *12.0*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# allocate_default_ventilation_openings
- number of invocations: 1

### Input
- **coeff_vent_zone** `['float']`: *0.0*
- **height_zone** `['float64']`: *12.0*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Ccoil2
- number of invocations: 1

### Input
- **Qc** `['float64']`: *-0*
- **tasup** `['float64']`: *273.0*
- **tare** `['float64']`: *273.0*
- **Qc0** `['float64']`: *-281104.46918348083*
- **tare_0** `['float64']`: *297.52499999999998*
- **tasup_0** `['float64']`: *288.5*
- **tsc0** `['int64']`: *280*
- **trc0** `['int64']`: *288*
- **wr** `['float64']`: *0.0*
- **ws** `['float64']`: *0.0*
- **ma0** `['float64']`: *289.39212124203419*
- **ma** `['float64']`: *0.0*
- **Cpa** `['float64']`: *1.008*
- **LMRT0** `['float64']`: *4.7866387565955035*
- **UA0** `['float64']`: *-58726.902838896574*
- **mCw0** `['float64']`: *35138.058647935104*
- **Qcsf** `['float64']`: *-0*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Eaux_cs_dis
- number of invocations: 1

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
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Eaux_fw
- number of invocations: 1

### Input
- **freshw** `['ndarray']`: *array([ 0.05684067,  0.02842034,  0.00710508, ...,  0.2397966 ,
        0.13322033,  0.10124745])*
- **nf** `['float64']`: *7.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05602030>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Eaux_hs_dis
- number of invocations: 1

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
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Eaux_ve
- number of invocations: 1

### Input
- **Qhsf** `['float64']`: *0.0*
- **Qcsf** `['float64']`: *-0*
- **P_ve** `['float64']`: *0.55000000000000004*
- **qve** `['float64']`: *1.1694485063119631*
- **SystemH** `['unicode_']`: *u'T1'*
- **SystemC** `['unicode_']`: *u'T3'*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Eaux_ww
- number of invocations: 1

### Input
- **Qww** `['float64']`: *0.0*
- **Qwwf** `['float64']`: *0.0*
- **Qwwf0** `['float64']`: *8928.0324494644647*
- **Imax** `['float64']`: *88.705510978710478*
- **deltaP_des** `['float64']`: *11.531716427232364*
- **b** `['float64']`: *1.2*
- **qV_des** `['float64']`: *0.0*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Hcoil2
- number of invocations: 1

### Input
- **Qh** `['float64']`: *0.0*
- **tasup** `['float64']`: *nan*
- **tare** `['float64']`: *290.94999999999999*
- **Qh0** `['float64']`: *6069.8981795983327*
- **tare_0** `['float64']`: *286.69999999999999*
- **tasup_0** `['float64']`: *309.5*
- **tsh0** `['int64']`: *313*
- **trh0** `['int64']`: *293*
- **wr** `['float64']`: *0.0*
- **ws** `['float64']`: *0.0*
- **ma0** `['float64']`: *0.36707176686581044*
- **ma** `['float64']`: *0.0*
- **Cpa** `['float64']`: *1.008*
- **LMRT0** `['complex128']`: *(1.9781714747962607-13.330104869215896j)*
- **UA0** `['complex128']`: *(66.117721476631871+445.54083011832188j)*
- **mCw0** `['float64']`: *303.49490897991666*
- **Qhsf** `['float64']`: *0.0*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param Qh:
:type Qh: float64

:param tasup:
:type tasup: float64

:param tare:
:type tare: float64

:param Qh0:
:type Qh0: float64

:param tare_0:
:type tare_0: float64

:param tasup_0:
:type tasup_0: float64

:param tsh0:
:type tsh0: int64

:param trh0:
:type trh0: int64

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
:type LMRT0: complex128

:param UA0:
:type UA0: complex128

:param mCw0:
:type mCw0: float64

:param Qhsf:
:type Qhsf: float64

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Htr
- number of invocations: 1

### Input
- **Hve** `['float64']`: *1414.5649132349504*
- **Htr_is** `['float64']`: *15748.652178585824*
- **Htr_ms** `['float64']`: *63226.498647402281*
- **Htr_w** `['float64']`: *1403.3742289273969*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Qdis_ls
- number of invocations: 1

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
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Qww_ls_nr
- number of invocations: 1

### Input
- **tair** `['float64']`: *15.202170683665049*
- **Qww** `['float64']`: *0.0*
- **Lvww_dis** `['float64']`: *50.246706155723558*
- **Lvww_c** `['float64']`: *55.259252908257515*
- **Y** `['float64']`: *0.29999999999999999*
- **Qww_0** `['float64']`: *6509.6247369541134*
- **V** `['float64']`: *81.45987041393002*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **Bf** `['float64']`: *0.69999999999999996*
- **te** `['float64']`: *8.8000000000000007*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C506C10>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_Qww_ls_r
- number of invocations: 1

### Input
- **Tair** `['float64']`: *15.202170683665049*
- **Qww** `['float64']`: *0.0*
- **lsww_dis** `['float64']`: *183.34912611426176*
- **lcww_dis** `['float64']`: *72.543326121114177*
- **Y** `['float64']`: *0.40000000000000002*
- **Qww_0** `['float64']`: *6509.6247369541134*
- **V** `['float64']`: *81.45987041393002*
- **Flowtap** `['float64']`: *0.035999999999999997*
- **twws** `['int64']`: *60*
- **Cpw** `['float64']`: *4.1840000000000002*
- **Pwater** `['int32']`: *998*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C506EB0>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_RAD
- number of invocations: 1

### Input
- **Qh** `['float64']`: *0.0*
- **tair** `['float64']`: *15.202170683665049*
- **Qh0** `['float64']`: *296485.76361481688*
- **tair0** `['float64']`: *22.0*
- **tsh0** `['int64']`: *90*
- **trh0** `['int64']`: *70*
- **nh** `['float64']`: *0.29999999999999999*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_TABSH
- number of invocations: 1

### Input
- **Qh** `['float64']`: *79965.596518869046*
- **tair** `['float64']`: *22.0*
- **Qh0** `['float64']`: *79965.596518869046*
- **tair0** `['float64']`: *22.0*
- **tsh0** `['int64']`: *40*
- **trh0** `['int64']`: *35*
- **nh** `['float64']`: *0.20000000000000001*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_TL
- number of invocations: 1

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
- **I_st** `['float64']`: *-994.95409442637401*
- **Hve** `['float64']`: *1414.5649132349504*
- **Htr_w** `['float64']`: *1403.3742289273969*
- **I_ia** `['float64']`: *1789.9699685754961*
- **I_m** `['float64']`: *2724.4521715126948*
- **Cm** `['float64']`: *651371895.40593004*
- **Af** `['float64']`: *2171.2396513531003*
- **Losses** `['bool']`: *False*
- **tHset_corr** `['float']`: *2.65*
- **tCset_corr** `['float']`: *-2.0*
- **IC_max** `['float64']`: *-1085619.8256765502*
- **IH_max** `['float64']`: *1085619.8256765502*
- **Flag** `['bool_']`: *False*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_capacity_heating_cooling_system
- number of invocations: 1

### Input
- **Af** `['float64']`: *2171.2396513531003*
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
Name: B153767, dtype: object*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_coeff_lea_zone
- number of invocations: 1

### Input
- **qv_delta_p_lea_ref** `['float64']`: *28949.862018041335*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param qv_delta_p_lea_ref:
:type qv_delta_p_lea_ref: float64

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_coeff_vent_zone
- number of invocations: 1

### Input
- **area_vent_zone** `['int']`: *0*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param area_vent_zone:
:type area_vent_zone: int

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_comp_heat_gains_sensible
- number of invocations: 1

### Input
- **Am** `['float64']`: *6947.9668843299214*
- **Atot** `['float64']`: *4564.8267184306733*
- **Htr_w** `['float64']`: *1403.3742289273969*
- **I_int_sen** `['ndarray']`: *array([ 3579.93993715,  3579.93993715,  3579.93993715, ...,  2684.95495286,
        2684.95495286,  2684.95495286])*
- **I_sol** `['Series']`: *T1        0.00000
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
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_dhw_heating_demand
- number of invocations: 1

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
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0C506C30>*
- **vw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **vww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_disls
- number of invocations: 1

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
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BFF3F10>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_gl
- number of invocations: 1

### Input
- **radiation** `['float64']`: *0.0*
- **g_gl** `['float64']`: *0.67500000000000004*
- **Rf_sh** `['float64']`: *0.080000000000000002*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_h
- number of invocations: 1

### Input
- **t** `['int32']`: *24*
- **w** `['float64']`: *0.0090625183347139426*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_h_ve_adj
- number of invocations: 1

### Input
- **q_m_mech** `['float64']`: *1.4033382075743557*
- **q_m_nat** `['int']`: *0*
- **temp_ext** `['float64']`: *8.8000000000000007*
- **temp_sup** `['float64']`: *8.8000000000000007*
- **temp_zone_set** `['int']`: *21*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0D197D30>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_heat_gains_internal_latent
- number of invocations: 1

### Input
- **people** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **X_ghp** `['float64']`: *80.0*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_heat_gains_internal_sensible
- number of invocations: 1

### Input
- **people** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qs_Wp** `['float64']`: *70.0*
- **Eal_nove** `['ndarray']`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcdata** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qcrefri** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_heat_gains_solar
- number of invocations: 1

### Input
- **Aw** `['float64']`: *452.70136417012804*
- **Awall_all** `['float64']`: *1131.75341042532*
- **Sh_typ** `['unicode']`: *u'T1'*
- **Solar** `['Series']`: *T1         0.00
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
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0D178070>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_hex
- number of invocations: 1

### Input
- **rel_humidity_ext** `['int64']`: *73*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0D178430>*
- **qv_mech** `['float64']`: *1.1694485063119631*
- **timestep** `['int']`: *3217*
- **temp_ext** `['float64']`: *8.1999999999999993*
- **qv_mech_dim** `['int']`: *0*
- **temp_zone_prev** `['float64']`: *18.759995042815788*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_hvac
- number of invocations: 1

### Input
- **rhum_1** `['int64']`: *73*
- **temp_1** `['float64']`: *8.1999999999999993*
- **temp_zone_set** `['float64']`: *18.639283464540256*
- **qv_req** `['float64']`: *1.1694485063119631*
- **qe_sen** `['int']`: *0*
- **temp_5_prev** `['float64']`: *18.759995042815788*
- **wint** `['float64']`: *0.0*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BFEE710>*
- **timestep** `['int']`: *3217*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_loads_electrical
- number of invocations: 1

### Input
- **Aef** `['float64']`: *2171.2396513531003*
- **Ealf** `['ndarray']`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Eauxf** `['ndarray']`: *array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796])*
- **Edataf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Eprof** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_mixed_schedule
- number of invocations: 1

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
Name: B153767, dtype: float64*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_pumping_systems_aux_loads
- number of invocations: 1

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
- **Qwwf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `['float64']`: *8928.0324494644647*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Ths_re** `['ndarray']`: *array([ 0,  0,  0, ..., 32, 32, 32])*
- **Ths_sup** `['ndarray']`: *array([ 0,  0,  0, ..., 39, 39, 39])*
- **Vw** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Year** `['int64']`: *1993*
- **fforma** `['float64']`: *0.76931348014904022*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05748F70>*
- **nf_ag** `['float64']`: *4.0*
- **nfp** `['float64']`: *1.0*
- **qv_req** `['ndarray']`: *array([ 1.16944851,  1.16944851,  1.16944851, ...,  1.16944851,
        1.16944851,  1.16944851])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_qv_delta_p_ref
- number of invocations: 1

### Input
- **n_delta_p_ref** `['int64']`: *6*
- **vol_building** `['float64']`: *4824.9770030068894*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_qv_req
- number of invocations: 1

### Input
- **ve** `['float64']`: *0.0*
- **people** `['float64']`: *0.0*
- **Af** `['float64']`: *2171.2396513531003*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05748530>*
- **hour_day** `['int32']`: *0*
- **hour_year** `['int32']`: *0*
- **n50** `['int64']`: *6*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_tHC_corr
- number of invocations: 1

### Input
- **SystemH** `['unicode']`: *u'T1'*
- **SystemC** `['unicode']`: *u'T3'*
- **sys_e_ctrl** `['unicode']`: *u'T1'*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_temperatures_emission_systems
- number of invocations: 1

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
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0D178FB0>*
- **ma_sup_cs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **ma_sup_hs** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **ta_hs_set** `['ndarray']`: *array([ 12.,  12.,  12., ...,  12.,  12.,  12.])*
- **w_re** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **w_sup** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_thermal_load_hvac_timestep
- number of invocations: 1

### Input
- **t** `['int']`: *3217*
- **thermal_loads_input** `['ThermalLoadsInput']`: *<cea.thermal_loads.ThermalLoadsInput object at 0x0D178BB0>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **state_prev** `['dict']`: *{'temp_air_prev': 18.759995042815788, 'temp_m_prev': 20.062727215496661}*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x059D7E90>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_thermal_load_mechanical_and_natural_ventilation_timestep
- number of invocations: 1

### Input
- **t** `['int']`: *0*
- **thermal_loads_input** `['ThermalLoadsInput']`: *<cea.thermal_loads.ThermalLoadsInput object at 0x05748850>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **state_prev** `['dict']`: *{'temp_air_prev': 21, 'temp_m_prev': 16}*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05734510>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_thermal_loads_new_ventilation
- number of invocations: 1

### Input
- **Name** `['str']`: *'B153767'*
- **building_properties** `['BuildingProperties']`: *<cea.demand.BuildingProperties object at 0x0D192BB0>*
- **weather_data** `['DataFrame']`: *(8760, 3)*
- **usage_schedules** `['dict']`: *{'list_uses': [u'GYM', u'HOSPITAL', u'HOTEL', u'INDUSTRIAL', u'MULTI_RES', u'OFFICE', u'PARKING', u'RETAIL'], 'schedules': [([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4, 0.6400000000000001, 0.6400000000000001, 0.6400000000000001, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.0, 0.6400000000000001, 0.8, 0.8, 0.6400000000000001, 0.4,*
- **date** `['DatetimeIndex']`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x05572E10>*
- **locationFinal** `['str']`: *'C:\\reference-case\\baseline\\outputs\\data\\demand'*
- **path_temporary_folder** `['str']`: *'c:\\users\\darthoma\\appdata\\local\\temp'*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param Name:
:type Name: str

:param building_properties:
:type building_properties: BuildingProperties

:param weather_data:
:type weather_data: DataFrame

:param usage_schedules:
:type usage_schedules: dict

:param date:
:type date: DatetimeIndex

:param gv:
:type gv: GlobalVariables

:param locationFinal:
:type locationFinal: str

:param path_temporary_folder:
:type path_temporary_folder: str

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_w
- number of invocations: 1

### Input
- **t** `['float64']`: *8.1999999999999993*
- **RH** `['int64']`: *73*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_w3_cooling_case
- number of invocations: 1

### Input
- **t5** `['int32']`: *24*
- **w2** `['float64']`: *0.0090625183347139426*
- **t3** `['int']`: *16*
- **w5** `['float64']`: *0.0094873786628507113*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calc_w3_heating_case
- number of invocations: 1

### Input
- **t5** `['float64']`: *20.0*
- **w2** `['float64']`: *0.0041699403233700994*
- **w5** `['float64']`: *0.0045258958486444414*
- **t3** `['int']`: *36*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BFE9EB0>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# calculate_pipe_transmittance_values
- number of invocations: 1

### Input
- **year** `['int64']`: *1993*
- **Retrofit** `['int64']`: *0*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# create_windows
- number of invocations: 1

### Input
- **df_prop_surfaces** `['DataFrame']`: *(2140, 6)*
- **gdf_building_architecture** `['GeoDataFrame']`: *(1482, 6)*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# demand_calculation
- number of invocations: 1

### Input
- **locator** `['InputLocator']`: *<cea.inputlocator.InputLocator object at 0x0BFF06B0>*
- **weather_path** `['str']`: *'C:\\Users\\darthoma\\Documents\\GitHub\\CEAforArcGIS\\cea\\db\\CH\\Weather\\Zurich.epw'*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BFF06B0>*


### Output
- `['None']`: ???
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
:rtype: None

INPUT / OUTPUT FILES
--------------------

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
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
- get_demand_results_folder: C:\reference-case\baseline\outputs\data\demand
- get_temporary_folder: c:\users\darthoma\appdata\local\temp
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
- get_total_demand: C:\reference-case\baseline\outputs\data\demand\Total_demand.csv
```

[TOC](#table-of-contents)
---

# get_building_geometry_ventilation
- number of invocations: 1

### Input
- **gdf_building_geometry** `['Series']`: *Blength       32.648092
Bwidth        16.008581
floors_ag      4.000000
floors_bg      2.000000
height_ag     12.000000
height_bg      6.000000
footprint    402.081417
perimeter    103.083898
Name: B153767, dtype: float64*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param gdf_building_geometry:
:type gdf_building_geometry: Series

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# get_internal_comfort
- number of invocations: 1

### Input
- **people** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **prop_comfort** `['Series']`: *Tcs_set_C     24
Tcs_setb_C    28
Ths_set_C     22
Ths_setb_C    12
Ve_lps        10
Name: B153767, dtype: float64*
- **limit_inf_season** `['int']`: *3217*
- **limit_sup_season** `['int']`: *6192*
- **weekday** `['ndarray']`: *array([4, 4, 4, ..., 4, 4, 4])*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# get_internal_loads
- number of invocations: 1

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
Name: B153767, dtype: float64*
- **prop_architecture** `['Series']`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# get_occupancy
- number of invocations: 1

### Input
- **mixed_schedule** `['DataFrame']`: *(8760, 4)*
- **prop_architecture** `['Series']`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **Af** `['float64']`: *2171.2396513531003*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# get_prop_RC_model
- number of invocations: 1

### Input
- **uses** `['GeoDataFrame']`: *(1482, 9)*
- **architecture** `['GeoDataFrame']`: *(1482, 6)*
- **thermal** `['GeoDataFrame']`: *(1482, 7)*
- **geometry** `['GeoDataFrame']`: *(274, 8)*
- **HVAC** `['DataFrame']`: *(1482, 13)*
- **rf** `['DataFrame']`: *(2140, 5)*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x059E5750>*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param uses:
:type uses: GeoDataFrame

:param architecture:
:type architecture: GeoDataFrame

:param thermal:
:type thermal: GeoDataFrame

:param geometry:
:type geometry: GeoDataFrame

:param HVAC:
:type HVAC: DataFrame

:param rf:
:type rf: DataFrame

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

# get_properties_building_envelope
- number of invocations: 1

### Input
- **prop_RC_model** `['Series']`: *Awall_all    1.131753e+03
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
- **prop_age** `['Series']`: *HVAC             0
basement         0
built         1993
envelope         0
partitions       0
roof             0
windows          0
Name: B153767, dtype: int64*
- **prop_architecture** `['Series']`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **prop_geometry** `['Series']`: *Blength       32.648092
Bwidth        16.008581
floors_ag      4.000000
floors_bg      2.000000
height_ag     12.000000
height_bg      6.000000
footprint    402.081417
perimeter    103.083898
Name: B153767, dtype: float64*
- **prop_occupancy** `['Series']`: *GYM           0
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
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# get_properties_building_systems
- number of invocations: 1

### Input
- **Ll** `['float64']`: *32.648092418099999*
- **Lw** `['float64']`: *16.008581384100001*
- **Retrofit** `['int64']`: *0*
- **Year** `['int64']`: *1993*
- **footprint** `['float64']`: *402.0814169172408*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BFE3DF0>*
- **nf_ag** `['float64']`: *4.0*
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
Name: B153767, dtype: object*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# get_properties_natural_ventilation
- number of invocations: 1

### Input
- **gdf_geometry_building** `['Series']`: *Blength       32.648092
Bwidth        16.008581
floors_ag      4.000000
floors_bg      2.000000
height_ag     12.000000
height_bg      6.000000
footprint    402.081417
perimeter    103.083898
Name: B153767, dtype: float64*
- **gdf_architecture_building** `['Series']`: *Occ_m2p        14
f_cros          0
n50             6
type_shade     T1
win_op        0.5
win_wall      0.4
Name: B153767, dtype: object*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x0BFF80F0>*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# get_temperatures
- number of invocations: 1

### Input
- **locator** `['LocatorDecorator']`: *???*
- **prop_HVAC** `['GeoDataFrame']`: *(1482, 5)*


### Output
- `['None']`: ???
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
:rtype: None

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

### Input
- **height_path** `['ndarray']`: *array([  3.,   3.,   9.,   9.,  12.])*
- **class_shielding** `['int']`: *2*
- **orientation_path** `['ndarray']`: *array([ 0.,  1.,  0.,  1.,  2.])*
- **slope_roof** `['int']`: *0*
- **factor_cros** `['int64']`: *0*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# read_building_properties
- number of invocations: 1

### Input
- **locator** `['LocatorDecorator']`: *???*
- **gv** `['GlobalVariables']`: *<cea.globalvar.GlobalVariables object at 0x059E52F0>*


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

:param locator:
:type locator: LocatorDecorator

:param gv:
:type gv: GlobalVariables

RETURNS
-------

:returns:
:rtype: None

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
```

[TOC](#table-of-contents)
---

# results_to_csv
- number of invocations: 1

### Input
- **GFA_m2** `['float64']`: *2412.4885015034447*
- **Af** `['float64']`: *2171.2396513531003*
- **Ealf** `['ndarray']`: *array([ 3977.71104128,  3977.71104128,  3977.71104128, ...,  2983.28328096,
        2983.28328096,  2983.28328096])*
- **Ealf_0** `['float64']`: *39777.110412788796*
- **Ealf_tot** `['float64']`: *90.946385247798304*
- **Eauxf** `['ndarray']`: *array([  0.        ,   0.        ,   0.        , ...,  12.38944692,
        12.42892359,  12.46955796])*
- **Eauxf_tot** `['float64']`: *2.0151953749551139*
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
- **Qww_ls_st** `['ndarray']`: *array([ 16.32384849,  16.36585597,  16.40794422, ...,  18.70794871,
        18.74110195,  18.77423176])*
- **Qwwf** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **Qwwf_0** `['float64']`: *8928.0324494644647*
- **Tcs_re** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_re_0** `['int64']`: *15*
- **Tcs_sup** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **Tcs_sup_0** `['int64']`: *7*
- **Ths_re** `['ndarray']`: *array([ 0,  0,  0, ..., 32, 32, 32])*
- **Ths_re_0** `['int64']`: *70*
- **Ths_sup** `['ndarray']`: *array([ 0,  0,  0, ..., 39, 39, 39])*
- **Ths_sup_0** `['int64']`: *90*
- **Tww_re** `['ndarray']`: *array([ 10.,  10.,  10., ...,  10.,  10.,  10.])*
- **Tww_st** `['ndarray']`: *array([ 59.96517155,  59.93025348,  59.89524561, ...,  59.82668903,
        59.78670315,  59.74664658])*
- **Tww_sup_0** `['int64']`: *60*
- **Waterconsumption** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **locationFinal** `['str']`: *'C:\\reference-case\\baseline\\outputs\\data\\demand'*
- **mcpcs** `['ndarray']`: *array([0, 0, 0, ..., 0, 0, 0])*
- **mcphs** `['ndarray']`: *array([ 0,  0,  0, ..., 14, 14, 14])*
- **mcpww** `['ndarray']`: *array([ 0.,  0.,  0., ...,  0.,  0.,  0.])*
- **path_temporary_folder** `['str']`: *'c:\\users\\darthoma\\appdata\\local\\temp'*
- **sys_e_cooling** `['unicode']`: *u'T3'*
- **sys_e_heating** `['unicode']`: *u'T1'*
- **waterpeak** `['float64']`: *0.33673440168628083*
- **date** `['DatetimeIndex']`: *<class 'pandas.tseries.index.DatetimeIndex'>
[2016-01-01 00:00:00, ..., 2016-12-30 23:00:00]
Length: 8760, Freq: H, Timezone: None*


### Output
- `['None']`: ???
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
:rtype: None

```

[TOC](#table-of-contents)
---

# test_demand
- number of invocations: 1

### Input


### Output
- `['None']`: ???
### Docstring template

```
PARAMETERS
----------

RETURNS
-------

:returns:
:rtype: None

```

[TOC](#table-of-contents)
---

