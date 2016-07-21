# -*- coding: utf-8 -*-
from __future__ import division
import pandas as pd
import numpy as np
import scipy.optimize as sopt
import scipy
import math
import storagetank_mixed as sto_m



def calc_mainuse(uses_df, uses):
    databaseclean = uses_df[uses].transpose()
    array_min = np.array(
        databaseclean[
            databaseclean[:] > 0].idxmin(
            skipna=True), dtype='S10')
    array_max = np.array(
        databaseclean[
            databaseclean[:] > 0].idxmax(
            skipna=True), dtype='S10')
    mainuse = np.array(map(calc_comparison, array_min, array_max))
    return mainuse


def calc_comparison(array_min, array_max):
    # do this to avoid that the selection of values
    # be based on the DEPO. for buildings qih heated spaces
    if array_max == 'DEPO':
        if array_min != 'DEPO':
            array_max = array_min
    return array_max


def calc_category(x, y):
    if 0 < x <= 1920:
        # Database['Qh'] = Database.ADMIN.value * Model.
        result = '1'
    elif x > 1920 and x <= 1970:
        result = '2'
    elif x > 1970 and x <= 1980:
        result = '3'
    elif x > 1980 and x <= 2000:
        result = '4'
    elif x > 2000 and x <= 2020:
        result = '5'
    elif x > 2020:
        result = '6'

    if 0 < y <= 1920:
        result = '7'
    elif 1920 < y <= 1970:
        result = '8'
    elif 1970 < y <= 1980:
        result = '9'
    elif 1980 < y <= 2000:
        result = '10'
    elif 2000 < y <= 2020:
        result = '11'
    elif y > 2020:
        result = '12'

    return result


def check_temp_file(T_ext,tH,tC, tmax):
    if tH == 0:
        tH = T_ext
    if tC == 0:
        tC = tmax+1
    return tH, tC


def get_prop_RC_model(uses, architecture, thermal, geometry, HVAC, radiation_file, gv):
    rf = radiation_file

    # Areas above ground #get the area of each wall in the buildings
    rf['Awall_all'] = rf['Shape_Leng']*rf['Freeheight']*rf['FactorShade']
    Awalls0 = pd.pivot_table(rf, rows='Name', values='Awall_all', aggfunc=np.sum)
    Awalls = pd.DataFrame(Awalls0) #get the area of walls in the whole buildings
    Areas = pd.merge(Awalls, architecture, left_index=True, right_index=True).merge(uses,left_index=True, right_index=True)
    Areas['Aw'] = Areas['Awall_all']*Areas['win_wall']*Areas['PFloor'] # Finally get the Area of windows
    Areas['Aop_sup'] = Areas['Awall_all']*Areas['PFloor']-Areas['Aw'] # Opaque areas PFloor represents a factor according to the amount of floors heated

    # Areas below ground
    all_prop = Areas.merge(thermal,left_index=True, right_index=True).\
                   merge(geometry,left_index=True,right_index=True).\
                   merge(HVAC,left_index=True,right_index=True)
    all_prop['floors'] = all_prop['floors_bg']+ all_prop['floors_ag']
    all_prop['Aop_bel'] = all_prop['height_bg']*all_prop['perimeter']+all_prop['footprint']   # Opague areas in m2 below ground including floor
    all_prop['Atot'] = Areas['Aw']+all_prop['Aop_sup']+all_prop['footprint']+all_prop['Aop_bel']+all_prop['footprint']*(all_prop['floors']-1) # Total area of the building envelope m2, it is considered the roof to be flat
    all_prop['Af'] = all_prop['footprint']*all_prop['floors']*all_prop['Hs']*(1-all_prop.DEPO)*(1-all_prop.CR)*(1-all_prop.SR) # conditioned area - áreas not heated
    all_prop['Aef'] = all_prop['footprint']*all_prop['floors']*all_prop['Es']# conditioned area only those for electricity
    all_prop['Am'] = all_prop.th_mass.apply(lambda x:AmFunction(x))*all_prop['Af'] # Effective mass area in m2

    # Steady-state Thermal transmittance coefficients and Internal heat Capacity
    all_prop['Htr_w'] = all_prop['Aw']*all_prop['U_win']  # Thermal transmission coefficient for windows and glagv.Zing. in W/K
    all_prop['HD'] = all_prop['Aop_sup']*all_prop['U_wall']+all_prop['footprint']*all_prop['U_roof']  # Direct Thermal transmission coefficient to the external environment in W/K
    all_prop['Hg'] = gv.Bf*all_prop ['Aop_bel']*all_prop['U_base'] # stady-state Thermal transmission coeffcient to the ground. in W/K
    all_prop['Htr_op'] = all_prop ['Hg']+ all_prop ['HD']
    all_prop['Htr_ms'] = gv.hms*all_prop ['Am'] # Coupling conduntance 1 in W/K
    all_prop['Htr_em'] = 1/(1/all_prop['Htr_op']-1/all_prop['Htr_ms']) # Coupling conduntance 2 in W/K
    all_prop['Htr_is'] = gv.his*all_prop ['Atot']
    all_prop['Cm'] = all_prop.th_mass.apply(lambda x:CmFunction(x))*all_prop['Af'] # Internal heat capacity in J/K

    #all_prop.to_csv(r'C:\Users\Jimeno\Desktop\test.csv')
    fields = ['Awall_all', 'Atot', 'Aw', 'Am','Aef','Af','Cm','Htr_is','Htr_em','Htr_ms','Htr_op','Hg','HD','Htr_w']
    result = all_prop[fields]
    return result

def AmFunction (x):
    if x == 'T2':
        return 2.5
    elif x == 'T3':
        return 3.2
    elif x == 'T1':
        return 2.5
    else:
        return 2.5

def CmFunction (x):
    if x == 'T2':
        return 165000
    elif x == 'T3':
        return 300000
    elif x == 'T1':
        return 110000
    else:
        return 165000

def CalcIncidentRadiation(AllProperties, Radiation_Shading2):

    #Import Radiation table and compute the Irradiation in W in every building's surface
    Columns = 8761
    Radiation_Shading2['AreaExposed'] = Radiation_Shading2['Shape_Leng']*Radiation_Shading2['FactorShade']*Radiation_Shading2['Freeheight']
    for Column in range(1, Columns):
         #transform all the points of solar radiation into Wh
        Radiation_Shading2['T'+str(Column)] = Radiation_Shading2['T'+str(Column)]*Radiation_Shading2['AreaExposed']

    #Do pivot table to sum up the irradiation in every surface to the building
    #and merge the result with the table allProperties
    PivotTable3 = pd.pivot_table(Radiation_Shading2, rows='Name', margins='Add all row')
    RadiationLoad = pd.DataFrame(PivotTable3)
    Solar = AllProperties.merge(RadiationLoad, left_index=True,right_index=True)

    columns_names = list(range(8760))
    for time in range(len(columns_names)):
        columns_names[time] = 'T'+str(time+1)

    Final = Solar[columns_names]

    return Final # total solar radiation in areas exposed to radiation in Watts

def calc_Y(year, Retrofit):
    if year >= 1995 or Retrofit > 0:
        Y = [0.2,0.3,0.3]
    elif 1985 <= year < 1995 and Retrofit == 0:
        Y = [0.3,0.4,0.4]
    else:
        Y = [0.4,0.4,0.4]
    return Y

def Calc_form(Lw,Ll,footprint):
    factor = footprint/(Lw*Ll)
    return factor

def Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd,Hve,Htr_is):
    tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
    tm = (tm_t+tm_t0)/2
    ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd)/Hve))/(Htr_ms+Htr_w+Htr_1)
    ta = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
    top = 0.31*ta+0.69*ts
    return tm, ts, ta, top

def calc_mixed_schedule(Profiles, Profiles_names, prop_occupancy):
    # weighted average of schedules
    def calc_average(last, current, share_of_use):
         return last + current*share_of_use

    #initialize variables
    ta_hs_set = np.zeros(8760)
    ta_cs_set = np.zeros(8760)
    people = np.zeros(8760)
    ve = np.zeros(8760)
    q_int = np.zeros(8760)
    w_int = np.zeros(8760)
    Eal = np.zeros(8760)
    E_pro = np.zeros(8760)
    E_data = np.zeros(8760)
    Qc_data = np.zeros(8760)
    Qc_refri = np.zeros(8760)
    mww = np.zeros(8760)
    mw = np.zeros(8760)

    hour = Profiles[0].Hour
    num_profiles = len(Profiles_names)
    for num in range(num_profiles):
        current_share_of_use = prop_occupancy[Profiles_names[num]]
        ta_hs_set = np.vectorize(calc_average)(ta_hs_set,Profiles[num].tintH_set,current_share_of_use)
        ta_cs_set = np.vectorize(calc_average)(ta_cs_set,Profiles[num].tintC_set,current_share_of_use)
        people = np.vectorize(calc_average)(people,Profiles[num].People,current_share_of_use)
        ve = np.vectorize(calc_average)(ve,Profiles[num].Ve,current_share_of_use)
        q_int = np.vectorize(calc_average)(q_int,Profiles[num].I_int,current_share_of_use)
        w_int = np.vectorize(calc_average)(w_int,Profiles[num].w_int,current_share_of_use)
        E_pro = np.vectorize(calc_average)(E_pro,Profiles[num].Epro,current_share_of_use)
        E_data = np.vectorize(calc_average)(E_data,Profiles[num].Edata,current_share_of_use)
        Qc_data = np.vectorize(calc_average)(Qc_data, Profiles[num].Qcdata,current_share_of_use)
        Qc_refri = np.vectorize(calc_average)(Qc_refri,Profiles[num].Qcrefri,current_share_of_use)
        Eal = np.vectorize(calc_average)(Eal,Profiles[num].Ealf_nove,current_share_of_use)
        mww = np.vectorize(calc_average)(mww,Profiles[num].Mww,current_share_of_use)
        mw = np.vectorize(calc_average)(mw,Profiles[num].Mw,current_share_of_use)

    return ta_hs_set,ta_cs_set,people,ve,q_int,Eal,E_pro, E_data, Qc_data,Qc_refri, mww, mw, w_int, hour


def calc_Htr(Hve, Htr_is, Htr_ms, Htr_w):
    Htr_1 = 1/(1/Hve+1/Htr_is)
    Htr_2 = Htr_1+Htr_w
    Htr_3 = 1/(1/Htr_2+1/Htr_ms)
    return Htr_1,Htr_2,Htr_3

def calc_Qem_ls(SystemH,SystemC):
    """model of losses in the emission and control system for space heating and cooling.
    correction factor for the heating and cooling setpoints. extracted from SIA 2044 (replacing EN 15243)"""
    tHC_corr = [0,0]
    # values extracted from SIA 2044 - national standard replacing values suggested in EN 15243
    if SystemH == 'T4' or 'T1':
        tHC_corr[0] = 0.5 + 1.2
    elif SystemH == 'T2':
        tHC_corr[0] = 0 + 1.2
    elif SystemH == 'T3': # no emission losses but emissions for ventilation
        tHC_corr[0] = 0.5 + 1 #regulation is not taking into account here
    else:
        tHC_corr[0] = 0.5 + 1.2

    if SystemC == 'T4':
        tHC_corr[1] = 0 - 1.2
    elif SystemC == 'T5':
        tHC_corr[1] = - 0.4 - 1.2
    elif SystemC == 'T3': # no emission losses but emissions for ventilation
        tHC_corr[1] = 0 - 1 #regulation is not taking into account here
    else:
        tHC_corr[1] = 0 + - 1.2

    return list(tHC_corr)

def Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd,Hve,Htr_2):
    return I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve) + te_t))/Htr_2

def calc_TL(SystemH, SystemC, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1, Htr_2, Htr_3,
            I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,tCset_corr, IC_max,IH_max, Flag):
    # assumptions
    if Losses:
        #Losses due to emission and control of systems
        tintH_set = tintH_set + tHset_corr
        tintC_set = tintC_set + tCset_corr

    # measure if this an uncomfortable hour
    uncomfort = 0
    # Case 0 or 1
    IHC_nd = IC_nd_ac = IH_nd_ac = 0
    Im_tot = Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd,Hve,Htr_2)
    tm, ts, tair_case0, top_case0 = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd,Hve,Htr_is)

    if tintH_set <= tair_case0 <=tintC_set:
        ta = tair_case0
        top = top_case0
        IH_nd_ac
        IH_nd_ac = 0
        IC_nd_ac = 0
    else:
        if tair_case0 > tintC_set:
            tair_set = tintC_set
        else:
            tair_set = tintH_set
        # Case 2
        IHC_nd =  IHC_nd_10 = 10*Af
        Im_tot = Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd_10,Hve,Htr_2)
        tm, ts, tair10, top10 = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd_10,Hve,Htr_is)


        IHC_nd_un =  IHC_nd_10*(tair_set - tair_case0)/(tair10-tair_case0) #- I_TABS
        if  IC_max < IHC_nd_un < IH_max:
            ta = tair_set
            top = 0.31*ta+0.69*ts
            IHC_nd_ac = IHC_nd_un
        else:
            if IHC_nd_un > 0:
                IHC_nd_ac = IH_max
            else:
                IHC_nd_ac = IC_max
            # Case 3 when the maxiFmum power is exceeded
            Im_tot = Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd_ac,Hve,Htr_2)
            tm, ts, ta ,top = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd_ac,Hve,Htr_is)
            uncomfort = 1

        if IHC_nd_un > 0:
            if  Flag == True:
                IH_nd_ac = 0
            else:
                IH_nd_ac = IHC_nd_ac
        else:
            if Flag == True:
                IC_nd_ac = IHC_nd_ac
            else:
                IC_nd_ac = 0

    if SystemC == "T0":
       IC_nd_ac = 0
    if SystemH == "T0":
       IH_nd_ac = 0
    return tm, ta, IH_nd_ac, IC_nd_ac,uncomfort, top, Im_tot

def calc_Qdis_ls(tair, text, Qhs, Qcs, tsh, trh, tsc,trc, Qhs_max, Qcs_max,D,Y, SystemH,SystemC, Bf, Lv):
    """calculates distribution losses based on ISO 15316"""
    # Calculate tamb in basement according to EN
    tamb = tair - Bf*(tair-text)
    if SystemH != 'T0' and Qhs > 0:
        Qhs_d_ls = ((tsh + trh)/2-tamb)*(Qhs/Qhs_max)*(Lv*Y)
    else:
        Qhs_d_ls = 0
    if SystemC != 'T0' and Qcs < 0:
        Qcs_d_ls = ((tsc + trc)/2-tamb)*(Qcs/Qcs_max)*(Lv*Y)
    else:
        Qcs_d_ls = 0

    return Qhs_d_ls,Qcs_d_ls

def calc_RAD(Qh,tair,Qh0,tair0, tsh0,trh0,nh):
    if Qh > 0:
        tair = tair+ 273
        tair0 = tair0 + 273
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        mCw0 = Qh0/(tsh0-trh0)
        #minimum
        LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
        k1 = 1/mCw0
        def fh(x):
            Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tair)/(x-tair))*LMRT))**(nh+1)
            return Eq
        k2 = Qh*k1
        result = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273
        trh = result.real
        tsh = trh + k2

        # Control system check
        #min_AT = 10 # Its equal to 10% of the mass flowrate
        #trh_min = tair + 5 - 273
        #tsh_min = trh_min + min_AT
        #AT = (tsh - trh)
        #if AT < min_AT:
        #    if (trh <= trh_min or tsh <= tsh_min):
        #        trh = trh_min
        ##        tsh = tsh_min
        #    if  tsh > tsh_min:
        #        trh = tsh - min_AT
        mCw = Qh/(tsh-trh)/1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return tsh,trh,mCw

def calc_TABSH(Qh,tair,Qh0,tair0, tsh0,trh0,nh):
    if Qh > 0:
        tair0 = tair0 + 273
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        mCw0 = Qh0/(tsh0-trh0)
        #minimum
        LMRT = (tsh0-trh0)/scipy.log((tsh0-tair0)/(trh0-tair0))
        k1 = 1/mCw0
        def fh(x):
            Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tair)/(x-tair))*LMRT))**(nh+1)
            return Eq
        k2 = Qh*k1
        tair = tair + 273
        result = sopt.newton(fh, trh0, maxiter=1000,tol=0.1) - 273
        trh = result.real
        tsh = trh + k2

        # Control system check
        #min_AT = 2 # Its equal to 10% of the mass flowrate
        #trh_min = tair + 1 - 273
        #tsh_min = trh_min + min_AT
        #AT = (tsh - trh)
        #if AT < min_AT:
        #    if trh <= trh_min or tsh <= tsh_min:
        #        trh = trh_min
        #        tsh = tsh_min
        #    if tsh > tsh_min:
        #        trh = tsh - min_AT
        mCw = Qh/(tsh-trh)/1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return  tsh,trh, mCw

def calc_qv_req(ve,people,Af,gv,hour_day,hour_year,limit_inf_season,limit_sup_season):

    infiltration_occupied = gv.hf*gv.NACH_inf_occ #m3/h.m2
    infiltration_non_occupied = gv.hf*gv.NACH_inf_non_occ #m3/h.m2
    if people >0:
        q_req = (ve+infiltration_occupied)*Af/3600 #m3/s
    else:
        if (21 < hour_day or hour_day < 7) and (limit_inf_season < hour_year <limit_sup_season):
            q_req = (ve*1.3+infiltration_non_occupied)*Af/3600 # free cooling
        else:
            q_req = (ve+infiltration_non_occupied)*Af/3600 #
    return q_req #m3/s

def CalcThermalLoads(Name, prop_occupancy, prop_architecture, prop_thermal, prop_geometry, prop_HVAC, prop_RC_model,
                     prop_age, Solar, locationFinal, Profiles, Profiles_names, T_ext, T_ext_max, RH_ext, T_ext_min,
                     path_temporary_folder,  gv, servers, coolingroom):
    Af = prop_RC_model.Af
    Aef = prop_RC_model.Aef
    sys_e_heating = prop_HVAC.type_hs
    sys_e_cooling = prop_HVAC.type_cs

    if Af > 0:
        #extract properties of building
        # Geometry
        nfp = prop_occupancy.PFloor
        footprint = prop_geometry.footprint
        nf_ag = prop_geometry.floors_ag
        nf_bg = prop_geometry.floors_bg
        Lw = prop_geometry.Bwidth
        Ll = prop_geometry.Blength
        # construction,renovation etc years of the building
        Year = prop_age.built
        Retrofit = prop_age.HVAC # year building  renovated or not
        # shading position and types
        Sh_typ = prop_architecture.type_shade
        # thermal mass properties
        Aw = prop_RC_model.Aw
        Awall_all = prop_RC_model.Awall_all
        Atot = prop_RC_model.Atot
        Cm = prop_RC_model.Cm
        Am = prop_RC_model.Am

        Y = calc_Y(Year,Retrofit) # linear trasmissivity coefficient of piping W/(m.K)
        # nominal temperatures
        Ths_sup_0 = prop_HVAC.tshs0
        Ths_re_0 = prop_HVAC.trhs0
        Tcs_sup_0 = prop_HVAC.tscs0
        Tcs_re_0 = prop_HVAC.trcs0
        Tww_sup_0 = prop_HVAC.tsww0
        Tww_re_0 = prop_HVAC.trww0

        # we define limtis of season.
        limit_inf_season = gv.seasonhours[0]+1
        limit_sup_season = gv.seasonhours[1]

        #Identification of equivalent lenghts
        fforma = Calc_form(Lw,Ll,footprint) # factor form comparison real surface and rectangular
        Lv = (2*Ll+0.0325*Ll*Lw+6)*fforma # lenght vertical lines
        Lcww_dis = 2*(Ll+2.5+nf_ag*nfp*gv.hf)*fforma # lenghtotwater piping circulation circuit
        Lsww_dis = 0.038*Ll*Lw*nf_ag*nfp*gv.hf*fforma # length hotwater piping distribution circuit
        Lvww_c = (2*Ll+0.0125*Ll*Lw)*fforma # lenghth piping heating system circulation circuit
        Lvww_dis = (Ll+0.0625*Ll*Lw)*fforma # lenghth piping heating system distribution circuit

        #calculate schedule and variables
        ta_hs_set,ta_cs_set,people,ve,q_int,Eal_nove,Eprof,Edataf, Qcdataf, Qcrefrif,vww,vw,X_int,hour_day = calc_mixed_schedule(Profiles,
                                                                                                                        Profiles_names,
                                                                                                                        prop_occupancy)
        # data and refrigeration loads
        Qcdata = Qcdataf*Af
        Qcrefri = Qcrefrif*Af

        #2. Transmission coefficients in W/K
        qv_req = np.vectorize(calc_qv_req)(ve,people,Af,gv,hour_day,range(8760),limit_inf_season,limit_sup_season)# in m3/s
        Hve = (gv.PaCa*qv_req)
        Htr_is = prop_RC_model.Htr_is
        Htr_ms = prop_RC_model.Htr_ms
        Htr_w = prop_RC_model.Htr_w
        Htr_em = prop_RC_model.Htr_em
        Htr_1,Htr_2, Htr_3 = np.vectorize(calc_Htr)(Hve, Htr_is, Htr_ms, Htr_w)

        #3. Heat flows in W
        #. Solar heat gains
        Rf_sh = Calc_Rf_sh(Sh_typ)
        solar_specific = Solar/Awall_all #array in W/m2
        Asol = np.vectorize(calc_gl)(solar_specific,gv.g_gl,Rf_sh)*(1-gv.F_f)*Aw # Calculation of solar efective area per hour in m2
        I_sol = Asol*solar_specific #how much are the net solar gains in Wh per hour of the year.

        #  Sensible heat gains
        I_int_sen = q_int*Af # Internal heat gains

        #  Calculate latent internal loads in terms of added moisture:
        if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
            w_int = X_int/(1000*3600)*Af #in kg/kg.s
        else:
            w_int = 0

        #  Components of Sensible heat gains
        I_ia = 0.5*I_int_sen
        I_m = (Am/Atot)*(I_ia+I_sol)
        I_st = (1-(Am/Atot)-(Htr_w/(9.1*Atot)))*(I_ia+I_sol)

        #4. Heating and cooling loads
        # the installed capacities are assumed to be gigantic, it is assumed that the building can  generate heat and cold at anytime
        # this is where the potential task of changing the set-back temperature for H&C can start.....
        if sys_e_heating == 'T2': # i.e., floor heating
            IC_max = -500*Af # typical of HVAC
            IH_max = 115*Af  #100W/m2 in the center and 175W/m2 in edge zones
        else:
            IC_max = -500*Af
            IH_max = 500*Af # typical of radiators and HVAC
        # define empty arrrays
        uncomfort = np.zeros(8760)
        Ta = np.zeros(8760)
        Tm = np.zeros(8760)
        Qhs_sen = np.zeros(8760)
        Qcs_sen = np.zeros(8760)
        Qhs_lat = np.zeros(8760)
        Qcs_lat = np.zeros(8760)
        Qhs_em_ls = np.zeros(8760)
        Qcs_em_ls = np.zeros(8760)
        QHC_sen = np.zeros(8760)
        ma_sup_hs = np.zeros(8760)
        Ta_sup_hs = np.zeros(8760)
        Ta_re_hs = np.zeros(8760)
        ma_sup_cs = np.zeros(8760)
        Ta_sup_cs = np.zeros(8760)
        Ta_re_cs = np.zeros(8760)
        w_sup = np.zeros(8760)
        w_re = np.zeros(8760)
        Ehs_lat_aux = np.zeros(8760)
        Qhs_sen_incl_em_ls = np.zeros(8760)
        Qcs_sen_incl_em_ls = np.zeros(8760)
        t5 = np.zeros(8760)
        Tww_re = np.zeros(8760)
        Top = np.zeros(8760)
        Im_tot = np.zeros(8760)

        # model of losses in the emission and control system for space heating and cooling
        tHset_corr, tCset_corr = calc_Qem_ls(sys_e_heating,sys_e_cooling)

        # we give a seed high enough to avoid doing a iteration for 2 years.
        tm_t0 = tm_t1 = 16
        # end-use demand calculation
        t5_1 = 21# definition of first temperature to start calculation of air conditioning system
        for k in range(8760):
            #if it is in the season
            if  limit_inf_season <= k < limit_sup_season:
                #take advantage of this loop to fill the values of cold water
                Flag_season = True
                Tww_re[k] = 14
            else:
                #take advantage of this loop to fill the values of cold water
                Tww_re[k] = Tww_re_0
                Flag_season = False
            # Calc of Qhs/Qcs - net/useful heating and cooling deamnd in W
            Losses = False # 0 is false and 1 is true
            Tm[k], Ta[k], Qhs_sen[k], Qcs_sen[k], uncomfort[k], Top[k], Im_tot[k] = calc_TL(sys_e_heating,sys_e_cooling, tm_t0,
                                                           T_ext[k], ta_hs_set[k], ta_cs_set[k], Htr_em, Htr_ms, Htr_is, Htr_1[k],
                                                           Htr_2[k], Htr_3[k], I_st[k], Hve[k], Htr_w, I_ia[k], I_m[k], Cm, Af, Losses,
                                                           tHset_corr,tCset_corr,IC_max,IH_max, Flag_season)

            # Calc of Qhs_em_ls/Qcs_em_ls - losses due to emission systems in W
            Losses = True
            Results1 = calc_TL(sys_e_heating,sys_e_cooling, tm_t1, T_ext[k], ta_hs_set[k], ta_cs_set[k],
                               Htr_em, Htr_ms, Htr_is, Htr_1[k],Htr_2[k], Htr_3[k], I_st[k], Hve[k], Htr_w, I_ia[k], I_m[k],
                               Cm, Af, Losses, tHset_corr,tCset_corr,IC_max,IH_max, Flag_season)

            # losses in the emission/control system
            Qhs_em_ls[k] = Results1[2] - Qhs_sen[k]
            Qcs_em_ls[k] = Results1[3] - Qcs_sen[k]
            if Qcs_em_ls[k] > 0:
                Qcs_em_ls[k] = 0
            if Qhs_em_ls[k] < 0:
                Qhs_em_ls[k] = 0

            tm_t0 = Tm[k]
            tm_t1 = Results1[0]

            #calc comfort hours:
            uncomfort[k] = Results1[4]
            Top[k] = Results1[5]
            Im_tot[k] = Results1[6]

            # Calculate new sensible loads with HVAC systems incl. recovery.
            if sys_e_heating == 'T1' or sys_e_heating == 'T2':
                Qhs_sen_incl_em_ls[k] = Results1[2]
            if sys_e_cooling == 'T0':
                Qcs_sen_incl_em_ls[k] = 0
            if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
                QHC_sen[k] = Qhs_sen[k] + Qcs_sen[k] + Qhs_em_ls[k] + Qcs_em_ls[k]
                temporal_Qhs, temporal_Qcs, Qhs_lat[k], Qcs_lat[k], Ehs_lat_aux[k], ma_sup_hs[k], ma_sup_cs[k], Ta_sup_hs[k], Ta_sup_cs[k], Ta_re_hs[k], Ta_re_cs[k], w_re[k], w_sup[k], t5[k] =  calc_HVAC(sys_e_heating, sys_e_cooling,
                                                                                                            people[k],RH_ext[k], T_ext[k],Ta[k],
                                                                                                            qv_req[k],Flag_season, QHC_sen[k],t5_1,
                                                                                                            w_int[k],gv)
                t5_1 = t5[k]
                if sys_e_heating == 'T3':
                    Qhs_sen_incl_em_ls[k] = temporal_Qhs
                if sys_e_cooling == 'T3':
                    Qcs_sen_incl_em_ls[k] = temporal_Qcs

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        # erase possible disruptions from dehumidification days
        #Qhs_sen_incl_em_ls[Qhs_sen_incl_em_ls < 0] = 0
        #Qcs_sen_incl_em_ls[Qcs_sen_incl_em_ls > 0] = 0
        Qhs_sen_incl_em_ls_0 = Qhs_sen_incl_em_ls.max()
        Qcs_sen_incl_em_ls_0 = Qcs_sen_incl_em_ls.min() # cooling loads up to here in negative values
        Qhs_d_ls, Qcs_d_ls =  np.vectorize(calc_Qdis_ls)(Ta, T_ext, Qhs_sen_incl_em_ls, Qcs_sen_incl_em_ls, Ths_sup_0, Ths_re_0, Tcs_sup_0, Tcs_re_0, Qhs_sen_incl_em_ls_0, Qcs_sen_incl_em_ls_0 ,
                                                         gv.D, Y[0], sys_e_heating, sys_e_cooling, gv.Bf, Lv)

        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        Qhsf = Qhs_sen_incl_em_ls + Qhs_d_ls   # no latent is considered because it is already added as electricity from the adiabatic system.
        Qcs = Qcs_sen_incl_em_ls + Qcs_lat
        Qcsf = Qcs + Qcs_d_ls
        Qcsf = -abs(Qcsf)
        Qcs = -abs(Qcs)

        # Calc nomincal temperatures of systems
        Qhsf_0 = Qhsf.max() # in W
        Qcsf_0 = Qcsf.min() # in W negative


        # Cal temperatures of all systems
        Ths_sup = np.zeros(8760) # in C
        Ths_re = np.zeros(8760) # in C
        Tcs_re = np.zeros(8760) # in C
        Tcs_sup = np.zeros(8760) # in C
        mcphs = np.zeros(8760) # in KW/C
        mcpcs = np.zeros(8760) # in KW/C
        Ta_0 = ta_hs_set.max()

        if sys_e_heating == 'T1': #radiators
            nh = 0.3
            Ths_sup, Ths_re, mcphs = np.vectorize(calc_RAD)(Qhsf,Ta, Qhsf_0, Ta_0, Ths_sup_0, Ths_re_0,nh)

        if sys_e_heating == 'T2': #floor heating
            nh = 0.2
            Ths_sup, Ths_re, mcphs = np.vectorize(calc_TABSH)(Qhsf,Ta, Qhsf_0, Ta_0, Ths_sup_0, Ths_re_0,nh)

        if sys_e_heating == 'T3': #air conditioning
            tasup = Ta_sup_hs +273
            tare = Ta_re_hs +273
            index = np.where(Qhsf == Qhsf_0)
            ma_sup_0 = ma_sup_hs[index[0][0]]
            Ta_sup_0 = Ta_sup_hs[index[0][0]] +273
            Ta_re_0 = Ta_re_hs[index[0][0]] + 273
            tsh0 = Ths_sup_0 +273
            trh0 = Ths_re_0 +273
            mCw0 = Qhsf_0/(tsh0-trh0)

            #log mean temperature at nominal conditions
            TD10 = Ta_sup_0 - trh0
            TD20 = Ta_re_0 - tsh0
            LMRT0 = (TD10-TD20)/scipy.log(TD20/TD10)
            UA0 = Qhsf_0/LMRT0

            Ths_sup, Ths_re, mcphs = np.vectorize(calc_Hcoil2)(Qhsf, tasup, tare, Qhsf_0, Ta_re_0, Ta_sup_0,
                                                                tsh0, trh0, w_re, w_sup, ma_sup_0, ma_sup_hs,
                                                                gv.Cpa, LMRT0, UA0, mCw0, Qhsf)
        if sys_e_cooling == 'T3':

            # Initialize temperatures
            tasup = Ta_sup_cs + 273
            tare = Ta_re_cs + 273
            index = np.where(Qcsf == Qcsf_0)
            ma_sup_0 = ma_sup_cs[index[0][0]] + 273
            Ta_sup_0 = Ta_sup_cs[index[0][0]] + 273
            Ta_re_0 = Ta_re_cs[index[0][0]] + 273
            tsc0 = Tcs_sup_0 + 273
            trc0 = Tcs_re_0 + 273
            mCw0 = Qcsf_0/(tsc0 - trc0)

            # log mean temperature at nominal conditions
            TD10 = Ta_sup_0 - trc0
            TD20 = Ta_re_0 - tsc0
            LMRT0 = (TD20-TD10)/scipy.log(TD20/TD10)
            UA0 = Qcsf_0/LMRT0

            # Make loop
            Tcs_sup, Tcs_re, mcpcs = np.vectorize(calc_Ccoil2)(Qcsf, tasup, tare, Qcsf_0, Ta_re_0, Ta_sup_0,
                                                               tsc0, trc0, w_re, w_sup, ma_sup_0, ma_sup_cs, gv.Cpa,
                                                               LMRT0, UA0, mCw0, Qcsf)
        #1. Calculate water consumption
        Vww = vww*Af/1000  ## consumption of hot water in m3/hour
        Vw = vw*Af/1000    ## consumption of fresh water in m3/h = cold water + hot water
        Mww = Vww*gv.Pwater/3600 # in kg/s
        #Mw = Vw*Pwater/3600 # in kg/s
        #2. Calculate hot water demand
        mcpww = Mww*gv.Cpw
        Qww = mcpww*(Tww_sup_0-Tww_re)*1000 # in W
        #3. losses distribution of domestic hot water recoverable and not recoverable
        Qww_0 = Qww.max()
        Vol_ls = Lsww_dis*(gv.D/1000)**(2/4)*math.pi
        Qww_ls_r  = np.vectorize(calc_Qww_ls_r)(Ta, Qww, Lsww_dis, Lcww_dis, Y[1], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0, gv.Cpw , gv.Pwater)
        Qww_ls_nr  = np.vectorize(calc_Qww_ls_nr)(Ta, Qww, Lvww_dis, Lvww_c, Y[0], Qww_0, Vol_ls, gv.Flowtap, Tww_sup_0, gv.Cpw , gv.Pwater, gv.Bf, T_ext)

        # the following part is connected to storage sensible heat loss calculation
        Qww_ls_st = np.zeros(8760)
        Tww_st = np.zeros(8760)
        Qd = np.zeros(8760)
        Qc = np.zeros(8760)
        Tww_st_0 = 60            # dhw tank initial temperature in C, move to global variable
        vww_0 = vww.max()
        V_dhwtank = np.vectorize(sto_m.calc_V_dhwtank)(vww, vww_0)

        #calculate heat loss in dhw tank and temperature change

        for k in range(8760):
            Qww_ls_st[k], Qd[k], Qc[k] = sto_m.calc_Qww_ls_st(Tww_st_0, Ta, gv.Bf, T_ext, V_dhwtank, Qww, Qww_ls_r, Qww_ls_nr)
            Tww_st[k] = sto_m.solve_ode_storage(Tww_st_0, Qww_ls_st[k], Qd[k], Qc[k], gv.Pwater, gv.Cpw, V_dhwtank)
            Tww_st[k] = sto_m.solve_ode_storage(Tww_st_0, Qww_ls_st[k], Qd[k], Qc[k], gv.Pwater, gv.Cpw, V_dhwtank)
            Tww_st_0 = Tww_st[k]


        #def calc_Qww_ls_r(Tair, Qww, lsww_dis, lcww_dis, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater):

        # Calc requirements of generation systems for hot water - assume losses of 10% due to local storage
        Qwwf = Qww+Qww_ls_r+Qww_ls_nr+Qww_ls_st

        Qwwf_0 = Qwwf.max()

        # clac auxiliary loads of pumping systems
        Eaux_cs = np.zeros(8760)
        Eaux_ve = np.zeros(8760)
        Eaux_fw = np.zeros(8760)
        Eaux_hs = np.zeros(8760)
        Imax = 2*(Ll+Lw/2+gv.hf+(nf_ag*nfp)+10)*fforma
        deltaP_des = Imax*gv.deltaP_l*(1+gv.fsr)
        if Year >= 2000:
            b =1
        else:
            b =1.2
        Eaux_ww = np.vectorize(calc_Eaux_ww)(Qwwf,Qwwf_0,Imax,deltaP_des,b,Mww) 
        if sys_e_heating > 0:
            Eaux_hs = np.vectorize(calc_Eaux_hs_dis)(Qhsf,Qhsf_0,Imax,deltaP_des,b,Ths_sup,Ths_re,gv.Cpw)
        if sys_e_cooling > 0:
            Eaux_cs  = np.vectorize(calc_Eaux_cs_dis)(Qcsf,Qcsf_0,Imax,deltaP_des,b,Tcs_sup,Tcs_re,gv.Cpw)
        if nf_ag > 5: #up to 5th floor no pumping needs
            Eaux_fw = calc_Eaux_fw(Vw,nf_ag,gv)
        if sys_e_heating == 'T3' or sys_e_cooling == 'T3':
            Eaux_ve = np.vectorize(calc_Eaux_ve)(Qhsf,Qcsf, gv.Pfan, qv_req,sys_e_heating,sys_e_cooling, Af)

        # Calc total auxiliary loads
        Eauxf = (Eaux_ww + Eaux_fw + Eaux_hs + Eaux_cs + Ehs_lat_aux + Eaux_ve)
    
        # calculate other quantities
        Occupancy = np.floor(people*Af)
        Occupants = Occupancy.max()
        Waterconsumption = Vww+Vw  #volume of water consumed in m3/h
        waterpeak = Waterconsumption.max()
    
    else:
        #scalars
        waterpeak = Occupants = 0
        Qwwf_0 = Ealf_0 = Qhsf_0 = Qcsf_0 = 0
        Ths_sup_0 = Ths_re_0 = Tcs_re_0 = Tcs_sup_0 = Tww_sup_0 = 0
        #arrays
        Occupancy = Eauxf = Waterconsumption = np.zeros(8760)
        Qwwf = Qww = Qhs_sen = Qhsf = Qcs_sen = Qcs = Qcsf = Qcdata = Qcrefri = np.zeros(8760)
        Ths_sup = Ths_re = Tcs_re = Tcs_sup = mcphs = mcpcs = mcpww = Tww_re = uncomfort = np.zeros(8760) # in C 
       
    if Aef > 0:
        # calc appliance and lighting loads
        Ealf = Eal_nove*Aef
        Epro = Eprof*Aef
        Edata = Edataf*Aef
        Ealf_0 = Ealf.max()

        # compute totals electrical loads in MWh
        Ealf_tot = Ealf.sum()/1000000
        Eauxf_tot = Eauxf.sum()/1000000
        Epro_tot = Epro.sum()/1000000
        Edata_tot = Edata.sum()/1000000
    else:
        Ealf_tot = Eauxf_tot =  Ealf_0 = 0
        Epro_tot = Edata_tot = 0
        Ealf = np.zeros(8760)
        Epro = np.zeros(8760)
        Edata = np.zeros(8760)

    # compute totals heating loads loads in MW
    if sys_e_heating != 'T0':
        Qhsf_tot = Qhsf.sum()/1000000
        Qhs_tot = Qhs_sen.sum()/1000000
        Qwwf_tot = Qwwf.sum()/1000000
        Qww_tot = Qww.sum()/1000000
    else:
        Qhsf_tot = Qhs_tot = Qwwf_tot  = Qww_tot = 0

    # compute totals cooling loads in MW
    if sys_e_cooling != 'T0':
        Qcs_tot = -Qcs.sum()/1000000 
        Qcsf_tot = -Qcsf.sum()/1000000
        Qcrefri_tot = Qcrefri.sum()/1000000
        Qcdata_tot = Qcdata.sum()/1000000
    else:
        Qcs_tot = Qcsf_tot = Qcdata_tot = Qcrefri_tot = 'T0'
        
    #print series all in kW, mcp in kW/h, cooling loads shown as positive, water consumption m3/h, temperature in Degrees celcious
    DATE = pd.date_range('1/1/2010', periods=8760, freq='H') 
    pd.DataFrame({'DATE':DATE, 'Name':Name,'Ealf':Ealf/1000,'Eauxf':Eauxf/1000,'Qwwf':Qwwf/1000,'Qww':Qww/1000,'Qhs':Qhs_sen/1000,
                  'Qhsf':Qhsf/1000,'Qcs':-1*Qcs/1000,'Qcsf':-1*Qcsf/1000,'Occupancy':Occupancy,'mw':Waterconsumption,
                  'tsh':Ths_sup, 'trh':Ths_re, 'mcphs':mcphs,'mcpww':mcpww,'tsc':Tcs_sup, 'trc':Tcs_re, 'mcpcs':mcpcs,'Qcdata':Qcdata/1000,
                  'tsww':Tww_sup_0,'trww':Tww_re,'twwst':Tww_st,'Qwwst':Qww_ls_st/1000,'Qd':Qd/1000,'Qc':Qc/1000,'Vtank':V_dhwtank,'Ef':(Ealf+Eauxf+Epro)/1000,'Epro':Epro/1000,'Qcrefri':Qcrefri/1000,'Edata':Edata/1000, 'QHf':(Qwwf+Qhsf)/1000,'QCf':(-1*Qcsf+Qcdata+Qcrefri)/1000,'uncomfortable':uncomfort}).to_csv(locationFinal+'\\'+Name+'.csv',index=False, float_format='%.2f')

    # print peaks in kW and totals in MWh, temperature peaks in C
    totals = pd.DataFrame({'Name':Name,'Af':Af,'occupants':Occupants,'uncomfort': uncomfort.sum()/8760, 'Qwwf0': Qwwf_0/1000, 'Ealf0': Ealf_0/1000,'Qhsf0':Qhsf_0/1000,
                  'Qcsf0':-Qcsf_0/1000,'Water0':waterpeak,'tsh0':Ths_sup_0, 'trh0':Ths_re_0, 'mcphs0':mcphs.max(),'tsc0':Tcs_sup_0,'Qcdata':Qcdata_tot,'Qcrefri':Qcrefri_tot,
                  'trc0':Tcs_re_0, 'mcpcs0':mcpcs.max(),'Qwwf':Qwwf_tot,'Qww':Qww_tot,'Qhsf':Qhsf_tot,'Qhs':Qhs_tot,'Qcsf':Qcsf_tot,'Qcs':Qcs_tot,
                  'Ealf':Ealf_tot,'Eauxf':Eauxf_tot, 'tsww0':Tww_sup_0,'Ef':(Ealf_tot+Eauxf_tot+Epro_tot+Edata_tot),'QHf':(Qwwf_tot+Qhsf_tot),'QCf':(Qcsf_tot+Qcdata_tot+Qcrefri_tot)}, index= [0])
    totals.to_csv(path_temporary_folder+'\\'+Name+'T.csv',index=False, float_format='%.2f')

    return

def calc_HVAC(SystemH, SystemC, people, RH1, t1, tair, qv_req, Flag, Qsen, t5_1, wint,gv):
    # State No. 5 # indoor air set point
    t5 = tair + 1 # accounding for an increase in temperature
    if Qsen != 0:
        #sensiblea nd latennt loads
        Qsen = Qsen*0.001 # transform in kJ/s
        # Properties of heat recovery and required air incl. Leakage
        qv = qv_req*1.0184     # in m3/s corrected taking into acocunt leakage
        Veff = gv.Vmax*qv/qv_req        #max velocity effective      
        nrec = gv.nrec_N-gv.C1*(Veff-2)   # heat exchanger coefficient

        # State No. 1
        w1 = calc_w(t1,RH1) #kg/kg    

        # State No. 2
        t2 = t1 + nrec*(t5_1-t1)
        w2 = min(w1,calc_w(t2,100))

        # State No. 3
        # Assuming thath AHU do not modify the air humidity
        w3 = w2  
        if Qsen > 0:  #if heating
            t3 = 30 # in C
        elif Qsen < 0: # if cooling
            t3 = 16 #in C

        # mass of the system
        h_t5_w3 =  calc_h(t5,w3)
        h_t3_w3 = calc_h(t3,w3)
        m1 = max(Qsen/((t3-t5)*gv.Cpa),(gv.Pair*qv)) #kg/s # from the point of view of internal loads
        w5 = (wint+w3*m1)/m1

        #room supply moisture content:
        liminf= calc_w(t5,30)
        limsup = calc_w(t5,70)
        if Qsen > 0:  #if heating
            w3, Qhum , Qdhum = calc_w3_heating_case(t5,w2,w5,t3,t5_1,m1,gv.lvapor,liminf,limsup)
        elif Qsen < 0: # if cooling
            w3, Qhum , Qdhum = calc_w3_cooling_case(w2,t3,w5,liminf,limsup,m1,gv.lvapor)

        # State of Supply
        ws = w3
        ts = t3 - 0.5 # minus the expected delta T rise temperature in the ducts

        # the new mass flow rate
        h_t5_w3 =  calc_h(t5,w3)
        h_ts_ws = calc_h(t3,ws)
        m = max(Qsen/((ts-t2)*gv.Cpa),(gv.Pair*qv)) #kg/s # from the point of view of internal loads

        # Total loads
        h_t2_w2 = calc_h(t2,w2)
        Qtot = m*(h_t3_w3-h_t2_w2)*1000 # in watts
        
        # Adiabatic humidifier - computation of electrical auxiliary loads
        if Qhum >0:
            Ehum_aux = 15/3600*m # assuming a performance of 15 W por Kg/h of humidified air source: bertagnolo 2012
        else:
            Ehum_aux =0
            
        if Qsen > 0:
            Qhs_sen = Qtot - Qhum
            ma_hs = m
            ts_hs = ts
            tr_hs = t2
            Qcs_sen = 0
            ma_cs = 0
            ts_cs = 0
            tr_cs =  0          
        elif Qsen < 0:
            Qcs_sen = Qtot - Qdhum
            ma_hs = 0
            ts_hs = 0
            tr_hs = 0
            ma_cs = m
            ts_cs = ts
            tr_cs = t2  
            Qhs_sen = 0
    else: 
        Qhum = 0
        Qdhum = 0
        Qtot = 0
        Qhs_sen = 0
        Qcs_sen = 0
        w1 = w2 = w3 = w5 = t2 = t3 = ts = m = 0
        Ehum_aux = 0
        #Edhum_aux = 0
        ma_hs = ts_hs = tr_hs = ts_cs = tr_cs = ma_cs =  0
    
    return Qhs_sen, Qcs_sen, Qhum, Qdhum, Ehum_aux, ma_hs, ma_cs, ts_hs, ts_cs, tr_hs, tr_cs, w2 , w3, t5

def calc_w3_heating_case(t5,w2,w5,t3,t5_1,m,lvapor,liminf,limsup):
    Qhum = 0
    Qdhum = 0
    if w5 < liminf:
        # humidification
        w3 = liminf - w5 + w2
        Qhum = lvapor*m*(w3 - w2)*1000 # in Watts
    elif w5 < limsup and w5  < calc_w(35,70):
        # heating and no dehumidification
        #delta_HVAC = calc_t(w5,70)-t5
        w3 = w2
    elif w5 > limsup:
        # dehumidification
        w3 = max(min(min(calc_w(35,70)-w5+w2,calc_w(t3,100)),limsup-w5+w2),0)
        Qdhum = lvapor*m*(w3 - w2)*1000 # in Watts
    else:
        # no moisture control
        w3 = w2
    return w3, Qhum , Qdhum 

def calc_w3_cooling_case(w2,t3,w5, liminf,limsup,m,lvapor):
    Qhum = 0
    Qdhum = 0
    if w5 > limsup:
        #dehumidification
        w3 = max(min(limsup-w5+w2,calc_w(t3,100)),0)
        Qdhum = lvapor*m*(w3 - w2)*1000 # in Watts
    elif w5 < liminf:
        # humidification
        w3 = liminf-w5+w2
        Qhum = lvapor*m*(w3 - w2)*1000 # in Watts
    else:
        w3 = min(w2,calc_w(t3,100))
    return w3, Qhum , Qdhum

def calc_w(t,RH): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    Ps = 610.78*math.exp(t/(t+238.3)*17.2694)
    Pv = RH/100*Ps
    w = 0.62*Pv/(Pa-Pv)
    return w

def calc_h(t,w): # enthalpyh of most air in kJ/kg
    if 0 < t < 60:
        h = (1.007*t-0.026)+w*(2501+1.84*t)    
    elif -100 < t <= 0:
        h = (1.005*t)+w*(2501+1.84*t)
   # else:
    #    h = (1.007*t-0.026)+w*(2501+1.84*t) 
    return h

def calc_RH(w,t): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(x/100*610.78*scipy.exp(t/(t+238.3*17.2694)))-1)-0.62
        return Eq
    result = sopt.newton(Ps, 50, maxiter=100,tol=0.01)
    RH = result.real
    return RH

def calc_t(w,RH): # tempeature in C
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(RH/100*610.78*scipy.exp(x/(x+238.3*17.2694)))-1)-0.62
        return Eq
    result = sopt.newton(Ps, 19, maxiter=100,tol=0.01)
    t = result.real
    return t

def Calc_Rf_sh (ShadingType):
    # this script assumes shading is always located outside! most of the cases
    #0 for not #1 for Louvres, 2 for Rollo, 3 for Venetian blinds, 4 for Courtain, 5 for Solar control glass
    d ={'Type':['T0', 'T1', 'T2', 'T3', 'T4', 'T5'],'ValueOUT':[1, 0.08,0.08,0.15,0.57,0.1]}
    ValuesRf_Table = pd.DataFrame(d)
    rows = ValuesRf_Table.Type.count()
    for row in range(rows):
        if ShadingType == ValuesRf_Table.loc[row,'Type']:
            return ValuesRf_Table.loc[row,'ValueOUT']

def calc_gl(radiation, g_gl,Rf_sh):
    if radiation > 300: #in w/m2
        return g_gl*Rf_sh
    else:
        return g_gl

def calc_Hcoil2(Qh, tasup, tare, Qh0, tare_0, tasup_0, tsh0, trh0, wr, ws, ma0, ma, Cpa, LMRT0, UA0, mCw0, Qhsf):
    if Qh > 0 and ma >0:
        AUa = UA0*(ma/ma0)**0.77
        NTUc= AUa/(ma*Cpa*1000)
        ec =  1 - scipy.exp(-NTUc)
        tc = (tare-tasup + tasup*ec)/ec #contact temperature of coil
        
        #minimum
        LMRT = (tsh0-trh0)/scipy.log((tsh0-tc)/(trh0-tc))
        k1 = 1/mCw0
        def fh(x): 
            Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-tc)/(x-tc))*LMRT))
            return Eq
        k2 = Qh*k1
        result = sopt.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
        trh = result.real
        tsh = trh + k2
        
        # Control system check - close to optimal flow
        #min_AT = 10 # Its equal to 10% of the mass flowrate
        #tsh_min = tasup + min_AT -273  # to consider coolest source possible
        #trh_min = tasup - 273
        #if trh < trh_min or tsh < tsh_min:
        #    trh = trh_min
        #    tsh = tsh_min
            
        mcphs = Qhsf/(tsh-trh)/1000  
    else:
        tsh = trh =  mcphs =0
    return tsh, trh,  mcphs

def calc_Ccoil2(Qc, tasup, tare, Qc0, tare_0, tasup_0, tsc0, trc0, wr, ws, ma0, ma, Cpa, LMRT0, UA0, mCw0, Qcsf):
    #Water cooling coil for temperature control
    if Qc < 0 and ma >0:
        AUa = UA0*(ma/ma0)**0.77
        NTUc= AUa/(ma*Cpa*1000)
        ec =  1 - scipy.exp(-NTUc)
        tc = (tare-tasup + tasup*ec)/ec  #contact temperature of coil
        
        def fh(x):
            TD1 = tc - (k2 + x)
            TD2 = tc - x
            LMRT = (TD2-TD1)/scipy.log(TD2/TD1)
            Eq = mCw0*k2-Qc0*(LMRT/LMRT0)
            return Eq
        
        k2 = -Qc/mCw0
        result = sopt.newton(fh, trc0, maxiter=100,tol=0.01) - 273
        tsc = result.real
        trc =  tsc + k2 
        
        # Control system check - close to optimal flow
        min_AT = 5 # Its equal to 10% of the mass flowrate
        tsc_min = 7 # to consider coolest source possible
        trc_max = 17
        tsc_max = 12
        AT =  tsc - trc
        if AT < min_AT:
            if tsc < tsc_min:
                tsc = tsc_min
                trc = tsc_min + min_AT
            if tsc > tsc_max:
                tsc = tsc_max
                trc = tsc_max + min_AT
            else:
                trc = tsc + min_AT
        elif tsc > tsc_max or trc > trc_max or tsc < tsc_min:
            trc = trc_max
            tsc = tsc_max
            
        mcpcs = Qcsf/(tsc-trc)/1000
    else:
        tsc = trc = mcpcs = 0
    return tsc, trc, mcpcs 

def calc_Qww_ls_r(Tair,Qww, lsww_dis, lcww_dis, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater):
    # Calculate tamb in basement according to EN
    tamb = Tair

    # Circulation circuit losses
    circ_ls = (twws-tamb)*Y*lcww_dis*(Qww/Qww_0)

    # Distribtution circuit losses
    dis_ls = calc_disls(tamb,Qww,Flowtap,V,twws,lsww_dis,Pwater,Cpw, Y)

    Qww_d_ls_r = circ_ls + dis_ls
    
    return Qww_d_ls_r

def calc_Qww_ls_nr(tair,Qww, Lvww_dis, Lvww_c, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater, Bf, te):
    # Calculate tamb in basement according to EN
    tamb = tair - Bf*(tair-te)
    
    # CIRUCLATION LOSSES
    d_circ_ls = (twws-tamb)*Y*(Lvww_c)*(Qww/Qww_0)
    
    # DISTRIBUTION LOSSEs
    d_dis_ls = calc_disls(tamb,Qww,Flowtap,V,twws,Lvww_dis,Pwater,Cpw,Y)
    Qww_d_ls_nr = d_dis_ls + d_circ_ls
    
    return Qww_d_ls_nr 

def calc_disls(tamb,hotw,Flowtap,V,twws,Lsww_dis,p,cpw, Y):
    if hotw > 0:
        t = 3600/((hotw/1000)/Flowtap)
        if t > 3600: t = 3600
        q = (twws-tamb)*Y
        exponential = scipy.exp(-(q*Lsww_dis*t)/(p*cpw*V*(twws-tamb)*1000))
        tamb = tamb + (twws-tamb)*exponential  
        losses = (twws-tamb)*V*cpw*p/1000*278
    else:
        losses= 0
    return losses

def calc_Eaux_ww(Qwwf,Qwwf0,Imax,deltaP_des,b,qV_des):
    if Qwwf>0:
        # for domestichotwater 
        #the power of the pump in Watts 
        Phy_des = 0.2778*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*b
        #Ppu_dis = Phy_des*feff
        #the power of the pump in Watts 
        if Qwwf/Qwwf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*b
            Eaux_ww = Ppu_dis_hy_i*feff
        else:
            Ppu_dis_hy_i = 0.0367*Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*b
            Eaux_ww = Ppu_dis_hy_i*feff 
    else:
        Eaux_ww = 0
    return Eaux_ww #in #W

def calc_Eaux_hs_dis(Qhsf,Qhsf0,Imax,deltaP_des,b, ts,tr,cpw):  
    #the power of the pump in Watts 
    if Qhsf > 0 and (ts-tr) != 0:
        fctr = 1.05
        qV_des = Qhsf/((ts-tr)*cpw*1000)
        Phy_des = 0.2278*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        #Ppu_dis = Phy_des*feff
        if Qhsf/Qhsf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
            Eaux_hs = Ppu_dis_hy_i*feff
        else:
            Ppu_dis_hy_i = 0.0367*Phy_des
            feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
            Eaux_hs = Ppu_dis_hy_i*feff
    else:
        Eaux_hs = 0
    return Eaux_hs #in #W

def calc_Eaux_cs_dis(Qcsf,Qcsf0,Imax,deltaP_des,b, ts,tr,cpw): 
#refrigerant R-22 1200 kg/m3
    # for Cooling system   
    #the power of the pump in Watts 
    if Qcsf <0 and (ts-tr) != 0:
        fctr = 1.10
        qV_des = Qcsf/((ts-tr)*cpw*1000)
        Phy_des = 0.2778*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        #Ppu_dis = Phy_des*feff
        #the power of the pump in Watts 
        if Qcsf < 0:
            if Qcsf/Qcsf0 > 0.67:
                Ppu_dis_hy_i = Phy_des
                feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                Eaux_cs = Ppu_dis_hy_i*feff
            else:
                Ppu_dis_hy_i = 0.0367*Phy_des
                feff = (1.25*(200/Ppu_dis_hy_i)**0.5)*fctr*b
                Eaux_cs = Ppu_dis_hy_i*feff 
    else:
        Eaux_cs = 0
    return Eaux_cs #in #W

def calc_Eaux_fw(freshw,nf,gv):
    Eaux_fw = np.zeros(8760)
    # for domesticFreshwater
    #the power of the pump in Watts Assuming the best performance of the pump of 0.6 and an accumulation tank
    for day in range(1,366):
        balance = 0
        t0 = (day-1)*24
        t24 = day*24
        for hour in range(t0,t24):
            balance = balance + freshw[hour]
        if balance >0 :
            flowday = balance/(3600) #in m3/s
            Energy_hourWh = (gv.hf*(nf-5))/0.6*gv.Pwater*gv.gr*(flowday/gv.hoursop)/gv.effi
            for t in range(1,gv.hoursop+1):
                time = t0 + 11 + t
                Eaux_fw[time] = Energy_hourWh
    return Eaux_fw

def calc_Eaux_ve(Qhsf,Qcsf,P_ve, qve, SystemH, SystemC, Af):
    if SystemH == 'T3':
        if Qhsf >0: 
            Eve_aux = P_ve*qve*3600
        else: 
            Eve_aux = 0
    elif SystemC == 'T3':
        if Qcsf <0:
            Eve_aux = P_ve*qve*3600
        else:
            Eve_aux = 0
    else:
        Eve_aux = 0
        
    return Eve_aux

