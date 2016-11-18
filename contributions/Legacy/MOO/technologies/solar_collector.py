"""
==================================================
solar collectors
==================================================

"""


from __future__ import division
import numpy as np
import pandas as pd
from math import *
import re
from cea.utilities import epwreader
from cea.utilities import solar_equations


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


"""
============================
SC heat generation
============================

"""

def calc_SC(locator, sensors_data, radiation, latitude, longitude, year, gv, weather_path):

    # weather data
    weather_data = epwreader.epw_reader(weather_path)

    # solar properties
    g, Sz, Az, ha, trr_mean, worst_sh, worst_Az = solar_equations.calc_sun_properties(latitude, longitude, weather_data, gv)

    # read radiation file
    hourly_data = pd.read_csv(radiation)

    # get only datapoints with production beyond min_production
    Max_Isol = hourly_data.total.max()
    Min_Isol = Max_Isol * gv.min_production  # 80% of the local average maximum in the area
    sensors_data_clean = sensors_data[sensors_data["total"] > Min_Isol]
    radiation_clean =radiation.loc[radiation['sensor_id'].isin(sensors_data_clean.sensor_id)]

    # Calculate the heights of all buildings for length of vertical pipes
    height = locator.get_total_demand().height.sum()

    # calculate optimal angle and tilt for panels
    optimal_angle_and_tilt(sensors_data, latitude, worst_sh, worst_Az, trr_mean, gv.grid_side,
                           gv.module_lenght_SC, gv.angle_north, Min_Isol, Max_Isol)

    Number_groups, hourlydata_groups, number_points, prop_observers = calc_groups(radiation_clean, sensors_data_clean)

    result, Final = SC_generation(gv.type_SCpanel, hourlydata_groups, prop_observers, number_points, g, Sz, Az, ha, latitude,
                                  gv.Tin, height)

    Final.to_csv(locator.solar_collectors_result(), index=True, float_format='%.2f')
    return


def SC_generation(type_SCpanel, group_radiation, prop_observers, number_points, weather_data, g, Sz, Az, ha, latitude, Tin, height):

    # get properties of the panel to evaluate
    n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Aratio, Apanel, dP1,dP2,dP3,dP4 = calc_properties_SC(type_SCpanel)
    Area_a = Aratio*Apanel
    listgroups = number_points.count() #counter from the vector with number of points
    listresults = [None]* listgroups
    listresults_perarea = [None]* listgroups
    listareasgroups = [None]* listgroups
    Sum_mcp = np.zeros(8760)
    Sum_qout = np.zeros(8760)
    Sum_Eaux = np.zeros(8760)
    Sum_qloss = np.zeros(8760)
    Tin_array = np.zeros(8760)+ Tin
    Sum_Area_m = (prop_observers['area_netpv']*number_points).sum()
    lv = 2 # grid lenght module length
    Le = (2*lv*number_points.sum())/(Sum_Area_m*Aratio)
    Li = 2*height/(Sum_Area_m*Aratio)
    Leq = Li+Le # in m/m2
    if type_SCpanel ==2: # for vaccum tubes
        Nseg = 100 # default number of subsdivisions for the calculation
    else:
        Nseg = 10 # default number of subsdivisions for the calculation

    for group in range(listgroups):
        teta_z = prop_observers.loc[group,'aspect'] #azimuth of paneles of group
        Area_group = prop_observers.loc[group,'area_netpv']*number_points[group]
        tilt_angle = prop_observers.loc[group,'slope'] #tilt angle of panels
        radiation = pd.DataFrame({'I_sol':group_radiation[group]}) #choose vector with all values of Isol
        radiation['I_diffuse'] = weather_data.ratio_diffhout*radiation.I_sol #calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']  #direct radaition

        #calculate angle modifiers,
        IAM_b = calc_anglemodifierSC(Az, g, ha, teta_z, tilt_angle, type_SCpanel,
                                     latitude, Sz) #direct angle modifier

        listresults[group] = Calc_SC_module2(radiation,tilt_angle, IAM_b, radiation.I_direct,
                                             radiation.I_diffuse,weather_data.drybulb_C,
                                             n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Area_a,
                                             dP1,dP2,dP3,dP4, Tin, Leq, Le,Nseg)

        K = Area_group/Apanel
        listresults[group][5] = listresults[group][5]*K
        listresults[group][0] = listresults[group][0]*K
        listresults[group][1] = listresults[group][1]*K
        listresults[group][2] = listresults[group][2]*K

        listareasgroups[group] = Area_group

    for group in range(listgroups):
        mcp_array = listresults[group][5]
        qloss_array = listresults[group][0]
        qout_array = listresults[group][1]
        Eaux_array = listresults[group][2]
        Sum_qout = Sum_qout + qout_array
        Sum_Eaux = Sum_Eaux + Eaux_array
        Sum_qloss = Sum_qloss + qloss_array
        Sum_mcp = Sum_mcp + mcp_array

    Tout_group = (Sum_qout/Sum_mcp) + Tin  # in C

    Final = pd.DataFrame({'Qsc_Kw':Sum_qout,'Tscs':Tin_array,'Tscr':Tout_group, 'mcp_kW/C': Sum_mcp,'Eaux_kW': Sum_Eaux,
                          'Qsc_l_KWH': Sum_qloss, 'Area':sum(listareasgroups)},index = range(8760))

    return listresults, Final


def calc_groups(Clean_hourly, observers_fin):

    # calculate number of optima groups as number of optimal combiantions.
    groups_ob = Clean_hourly.groupby(['CATB', 'CATGB', 'CATteta_z'])
    hourlydata_groups = groups_ob.mean().reset_index()
    hourlydata_groups = pd.DataFrame(hourlydata_groups)
    Number_pointsgroup = groups_ob.size().reset_index()
    number_points = Number_pointsgroup[0]

    groups_ob = observers_fin.groupby(['CATB', 'CATGB', 'CATteta_z'])
    prop_observers = groups_ob.mean().reset_index()
    prop_observers = pd.DataFrame(prop_observers)
    Number_groups = groups_ob.size().count()

    hourlydata_groups = hourlydata_groups.drop({'ID', 'GB', 'grid_code', 'pointid', 'array_s', 'area_netpv', 'aspect',
                                                'slope', 'CATB', 'CATGB', 'CATteta_z'}, axis=1).transpose().reindex(
        axis=1)  # vector with radiation points of group
    hourlydata_groups['newindex'] = hourlydata_groups.index
    hourlydata_groups['newindex'] = hourlydata_groups.newindex.apply(lambda x: re.findall('\d+', x))
    hourlydata_groups.index = range(8760)
    for hour in range(8760):
        hourlydata_groups.loc[hour, 'newindex'] = int(hourlydata_groups.loc[hour, 'newindex'][0])

    hourlydata_groups.set_index('newindex', inplace=True)
    hourlydata_groups.sort_index(inplace=True)
    hourlydata_groups.index = range(8760)

    return Number_groups, hourlydata_groups, number_points, prop_observers


def Calc_SC_module2(radiation,tilt_angle, IAM_b_vector, I_direct_vector, I_diffuse_vector,Te_vector, n0,c1,c2, mB0_r,
                    mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Area_a, dP1,dP2,dP3,dP4, Tin, Leq, Le, Nseg):

    #panel to store the results per flow
    #method with no condensaiton gains, no wind or long-wave dependency, sky factor set to zero.
    # calculate radiation part
    #local variables
    Cpwg = 3680#J/kgK  water grlycol  specific heat
    maxmsc = mB_max_r*Area_a/3600
    #Do the calculation of every time step for every possible flow condition
    #get states where highly performing values are obtained.
    mopt = 0 #para iniciar
    temperature_out =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    temperature_in =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    supply_out =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    supply_losses =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    Auxiliary =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    temperature_m =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    specific_flows = [np.zeros(8760), (np.zeros(8760)+mB0_r)*Area_a/3600, (np.zeros(8760)+mB_max_r)*Area_a/3600,
                      (np.zeros(8760)+mB_min_r)*Area_a/3600, np.zeros(8760),np.zeros(8760)] # in kg/s
    specific_pressurelosses = [np.zeros(8760),(np.zeros(8760)+dP2)*Area_a,(np.zeros(8760)+dP3)*Area_a,
                               (np.zeros(8760)+dP4)*Area_a,np.zeros(8760),np.zeros(8760)] # in Pa
    supply_out_pre = np.zeros(8760)
    supply_out_total = np.zeros(8760)
    mcp = np.zeros(8760)

	#calculate net radiant heat (absorbed)
    tilt = radians(tilt_angle)
    qrad_vector = np.vectorize(calc_qrad)(n0, IAM_b_vector, I_direct_vector, IAM_d, I_diffuse_vector,
                                          tilt) # in W/m2 is a mean of the group
    counter = 0
    Flag = False
    Flag2 = False
    for flow in range(6):
        Mo = 1
        TIME0 = 0
        DELT = 1 #timestep 1 hour
        delts = DELT*3600 #convert time step in seconds
        Tfl = np.zeros([3, 1]) #create vector
        DT = np.zeros([3, 1])
        Tabs= np.zeros([3, 1])
        STORED = np.zeros([600, 1])
        TflA = np.zeros([600, 1])
        TflB = np.zeros([600, 1])
        TabsB = np.zeros([600, 1])
        TabsA = np.zeros([600, 1])
        qgainSeg = np.zeros([100, 1])
        for time in range(8760):
            Mfl = specific_flows[flow][time]
            if time < TIME0+DELT/2:
                for Iseg in range(101, 501): #400 points with the data
                    STORED[Iseg] = Tin
            else:
                for Iseg in range(1, Nseg): #400 points with the data
                    STORED[100+Iseg] = STORED[200+Iseg]
                    STORED[300+Iseg] = STORED[400+Iseg]

            #calculate stability criteria
            if Mfl > 0:
                stabcrit = Mfl*Cpwg*Nseg*(DELT*3600)/(C_eff*Area_a)
                if stabcrit <= 0.5:
                    print 'ERROR'+ str(stabcrit)+ ' '+str(Area_a)+' ' + str(Mfl)
            Te = Te_vector[time]
            qrad = qrad_vector[time]
            Tfl[1] = 0 #mean absorber temp
            Tabs[1] = 0 #mean absorber initial tempr
            for Iseg in range(1,Nseg+1):
                Tfl[1] = Tfl[1]+STORED[100+Iseg]/Nseg
                Tabs[1] = Tabs[1]+STORED[300+Iseg]/Nseg
            #first guess for DeatT
            if Mfl > 0:
                Tout = Tin+(qrad-(c1+0.5)*(Tin-Te))/(Mfl*Cpwg/Area_a)
                Tfl[2] = (Tin+Tout)/2
            else:
                Tout = Te+qrad/(c1+0.5)
                Tfl[2] = Tout #fluid temperature same as output
            DT[1] = Tfl[2] - Te

            #calculate qgain with the guess

            qgain = calc_qgain(Tfl,Tabs,qrad,DT, Tin, Tout, Area_a, c1, c2, Mfl, delts,Cpwg, C_eff,Te)

            Aseg= Area_a/Nseg
            for Iseg in range(1,Nseg+1):
                TflA[Iseg] = STORED[100+Iseg]
                TabsA[Iseg] = STORED[300+Iseg]
                if Iseg >1:
                    TinSeg = ToutSeg
                else:
                    TinSeg = Tin
                if Mfl > 0 and Mo ==1:
                    ToutSeg=((Mfl*Cpwg*(TinSeg+273))/Aseg-(C_eff*(TinSeg+273))/(2*delts)+qgain+
                             (C_eff*(TflA[Iseg]+273)/delts))/(Mfl*Cpwg/Aseg+C_eff/(2*delts))
                    ToutSeg = ToutSeg-273
                    TflB[Iseg] = (TinSeg+ToutSeg)/2
                else:
                    Tfl[1] = TflA[Iseg]
                    Tabs[1] = TabsA[Iseg]
                    qgain = calc_qgain(Tfl,Tabs,qrad, DT, TinSeg, Tout, Aseg, c1, c2, Mfl, delts,Cpwg, C_eff,Te)
                    ToutSeg = Tout
                    if Mfl > 0:
                        TflB[Iseg] = (TinSeg+ToutSeg)/2
                        ToutSeg = TflA[Iseg] + (qgain*delts)/C_eff
                    else:
                        TflB[Iseg] = ToutSeg
                    TflB[Iseg] = ToutSeg
                    qfluid = (ToutSeg-TinSeg)*Mfl*Cpwg/Aseg
                    qmtherm = (TflB[Iseg]-TflA[Iseg])*C_eff/delts
                    qbal = qgain-qfluid-qmtherm
                    if abs(qbal) > 1:
                        time = time
                qgainSeg[Iseg] = qgain #in W/m2
            #the resulting energy output
            qout = Mfl*Cpwg*(ToutSeg-Tin)
            Tabs[2] = 0
            #storage of the mean temperature
            for Iseg in range(1,Nseg+1):
                STORED[200+Iseg] = TflB[Iseg]
                STORED[400+Iseg] = TabsB[Iseg]
                Tabs[2] = Tabs[2]+TabsB[Iseg]/Nseg

            #outputs
            temperature_out[flow][time]= ToutSeg
            temperature_in[flow][time] = Tin
            supply_out[flow][time]  = qout/1000 #in kW
            temperature_m[flow][time] = (Tin+ToutSeg)/2 #Mean absorber temperature at present

            qgain = 0
            TavgB = 0
            TavgA = 0
            for Iseg in range(1,Nseg+1):
                qgain = qgain +qgainSeg*Aseg # W
                TavgA = TavgA+TflA[Iseg]/Nseg
                TavgB = TavgB+TflB[Iseg]/Nseg

            #OUT[9] = qgain/Area_a # in W/m2
            qmtherm = (TavgB-TavgA)*C_eff*Area_a/delts
            qbal = qgain-qmtherm-qout

            #OUT[11] = qmtherm
            #OUT[12] = qbal
        if flow < 4:
            Auxiliary[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow],
                                                         Leq, Area_a) #in kW
        if flow == 3:
            q1 = supply_out[0]
            q2 = supply_out[1]
            q3 = supply_out[2]
            q4 = supply_out[3]
            E1 = Auxiliary[0]
            E2 = Auxiliary[1]
            E3 = Auxiliary[2]
            E4 = Auxiliary[3]
            specific_flows[4], specific_pressurelosses[4] = SelectminimumenergySc(q1,q2,q3,q4,E1,E2,E3,E4, 0,
                                                                                  mB0_r, mB_max_r,mB_min_r,0,
                                                                                  dP2,dP3,dP4, Area_a)
        if flow == 4:
            Auxiliary[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow],
                                                         Leq, Area_a) #in kW
            dp5 = specific_pressurelosses[flow]
            q5 = supply_out[flow]
            m5 = specific_flows[flow]
            ##poits where load is negative
            specific_flows[5], specific_pressurelosses[5] = Selectminimumenergy2(m5,q5,dp5)
        if flow == 5:
            supply_losses[flow] = np.vectorize(Calc_qloss_net)(specific_flows[flow],Le,Area_a,temperature_m[flow],
                                                               Te_vector, maxmsc)
            supply_out_pre = supply_out[flow].copy() + supply_losses[flow].copy()
            Auxiliary[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow],
                                                         Leq, Area_a) # in kW
            supply_out_total= supply_out + 0.5*Auxiliary[flow] - supply_losses[flow]
            mcp = specific_flows[flow]*(Cpwg/1000) # mcp in kW/c

    result = [supply_losses[5], supply_out_total[5], Auxiliary[5], temperature_out[flow], temperature_in[flow], mcp]
    return result


def calc_qrad(n0, IAM_b, I_direct, IAM_d, I_diffuse, tilt):
    qrad = n0 * IAM_b * I_direct + n0 * IAM_d * I_diffuse * (1 + cos(tilt)) / 2
    return qrad


def calc_qgain(Tfl, Tabs, qrad, DT, TinSub, Tout, Aseg, c1, c2, Mfl, delts, Cpwg, C_eff, Te):
    xgain = 1
    xgainmax = 100
    exit = False
    while exit == False:
        qgain = qrad - c1 * (DT[1]) - c2 * abs(DT[1]) * DT[1]
        if Mfl > 0:
            Tout = ((Mfl * Cpwg * TinSub) / Aseg - (C_eff * TinSub) / (2 * delts) + qgain + (
                C_eff * Tfl[1]) / delts) / (Mfl * Cpwg / Aseg + C_eff / (2 * delts))
            Tfl[2] = (TinSub + Tout) / 2
            DT[2] = Tfl[2] - Te
            qdiff = Mfl / Aseg * Cpwg * 2 * (DT[2] - DT[1])
        else:
            Tout = Tfl[1] + (qgain * delts) / C_eff
            Tfl[2] = Tout
            DT[2] = Tfl[2] - Te
            qdiff = 5 * (DT[2] - DT[1])
        if abs(qdiff < 0.1):
            DT[1] = DT[2]
            exit = True
        else:
            if xgain > 40:
                DT[1] = (DT[1] + DT[2]) / 2
                if xgain == xgainmax:
                    exit = True
            else:
                DT[1] = DT[2]
    qout = Mfl * Cpwg * (Tout - TinSub) / Aseg
    qmtherm = (Tfl[2] - Tfl[1]) * C_eff / delts
    qbal = qgain - qout - qmtherm
    if abs(qbal) > 1:
        qbal = qbal
    return qgain


def Calc_qloss_net(Mfl, Le, Area_a, Tm, Te, maxmsc):
    qloss = 0.217 * Le * Area_a * (Tm - Te) * (Mfl / maxmsc) / 1000
    return qloss  # in kW


def calc_anglemodifierSC(Az_vector, g_vector, ha_vector, teta_z, tilt_angle, type_SCpanel, latitude, Sz_vector):

    def calc_Teta_L(Az, teta_z, tilt, Sz):
        # calculate incident angles longitudinal and trasnversally of the solar collector
        teta_la = tan(Sz) * cos(teta_z - Az)
        teta_l = degrees(abs(atan(teta_la) - tilt))  # longitudinal incidence angle
        if teta_l < 0:
            teta_l = min(89, abs(teta_T))
        if teta_l >= 90:
            teta_l = 89.999
        return teta_l  # in degrees

    def calc_Teta_T(Az, Sz, teta_z):  # Az is the solar azimuth
        # calculate incident angles transversal
        teta_ta = sin(Sz) * sin(abs(teta_z - Az))
        teta_T = degrees(atan(teta_ta / cos(teta_ta)))  # transversal angle modifier
        if teta_T < 0:
            teta_T = min(89, abs(teta_T))
        if teta_T >= 90:
            teta_T = 89.999
        return teta_T

    def calc_maxtetaL(teta_L):
        if teta_L < 0:
            teta_L = min(89, abs(teta_L))
        if teta_L >= 90:
            teta_L = 89.999
        return teta_L

    def Calc_IAMb(teta_l, teta_T, type_SCpanel):
        if type_SCpanel == 1:  # # Flat plate collector   SOLEX blu SFP, 2012
            IAM_b = -0.00000002127039627042 * teta_l ** 4 + 0.00000143550893550934 * teta_l ** 3 - 0.00008493589743580050 * teta_l ** 2 + 0.00041588966590833100 * teta_l + 0.99930069929920900000
        if type_SCpanel == 2:  # # evacuated tube   Zewotherm SOL ZX-30 SFP, 2012
            IAML = -0.00000003365384615386 * teta_l ** 4 + 0.00000268745143745027 * teta_l ** 3 - 0.00010196678321666700 * teta_l ** 2 + 0.00088830613832779900 * teta_l + 0.99793706293541500000
            IAMT = 0.000000002794872 * teta_T ** 5 - 0.000000534731935 * teta_T ** 4 + 0.000027381118880 * teta_T ** 3 - 0.000326340326281 * teta_T ** 2 + 0.002973799531468 * teta_T + 1.000713286764210
            IAM_b = IAMT * IAML  # overall incidence angle modifier for beam radiation
        return IAM_b

    #convert to radians
    teta_z = radians(teta_z)
    tilt = radians(tilt_angle)

    #Az_vector = np.radians(Az_vector)
    g_vector = np.radians(g_vector)
    ha_vector = np.radians(ha_vector)
    lat = radians(latitude)
    Sz_vector = np.radians(Sz_vector)
    Az_vector = np.radians(Az_vector)
    Incidence_vector = np.vectorize(Calc_incidenteangleB)(g_vector, lat, ha_vector, tilt, teta_z) # incident angle in radians

    #calculate incident angles
    if type_SCpanel == 1:#
        Teta_L = np.degrees(Incidence_vector)
        Teta_T = 0 #not necessary
        Teta_L = np.vectorize(calc_maxtetaL)(Teta_L)
    if type_SCpanel == 2:#
        Teta_L = np.vectorize(calc_Teta_L)(Az_vector, teta_z, tilt, Sz_vector) # in degrees
        Teta_T = np.vectorize(calc_Teta_T)(Az_vector, Sz_vector, teta_z,Incidence_vector) # in degrees

    #calculate incident angle modifier
    IAM_b_vector = np.vectorize(Calc_IAMb)(Teta_L,Teta_T, type_SCpanel)

    return  IAM_b_vector


def Calc_incidenteangleB(g, lat, ha, tilt, teta_z):
    # calculate incident angle beam radiation
    part1 = sin(lat) * sin(g) * cos(tilt) - cos(lat) * sin(g) * sin(tilt) * cos(teta_z)
    part2 = cos(lat) * cos(g) * cos(ha) * cos(tilt) + sin(lat) * cos(g) * cos(ha) * sin(tilt) * cos(teta_z)
    part3 = cos(g) * sin(ha) * sin(tilt) * sin(teta_z)
    teta_B = acos(part1 + part2 + part3)
    return teta_B  # in radains

"""
============================
properties of module
============================

"""

def calc_properties_SC(type_SCpanel):
    if type_SCpanel == 1:#     # Flat plate collector   SOLEX blu SFP, 2012
        n0 = 0.775 # zero loss efficeincy
        c1 = 3.91 #W/m2K
        c2 = 0.0081 #W/m2K2
        #specific mass flow rates
        mB0_r = 57.98 # # in kg/h/m2   of aperture area
        mB_max_r = 86.97 # in kg/h/m2   of aperture area
        mB_min_r = 28.99 # in kg/h/m2   of aperture area
        C_eff = 8000  #thermal capacitance of module J/m2K
        t_max = 192 # stagnation temperature in C
        IAM_d = 0.87 #diffuse incident angle considered at 50 degrees
        Aratio = 0.888# the aperture/gross area ratio
        Apanel = 2.023 #m2
        dP1 = 0
        dP2 = 170/(Aratio*Apanel)
        dP3 = 270/(Aratio*Apanel)
        dP4 = 80/(Aratio*Apanel)
    if type_SCpanel == 2:#     # evacuated tube   Zewotherm SOL ZX-30 SFP, 2012
        n0 = 0.721
        c1 = 0.89 #W/m2K
        c2 = 0.0199 #W/m2K2

        #specific mass flow rates
        mB0_r = 88.2  # in kg/h/m2   of aperture area
        mB_max_r = 147.12 # in kg/h/m2
        mB_min_r = 33.10 # in kg/h/m2
        C_eff = 38000  #thermal capacitance of module anf fluid for Brine J/m2K
        t_max = 196 # stagnation temperature in C
        IAM_d = 0.91 #diffuse incident angle considered at 50 degrees
        Aratio = 0.655 # the aperture/gross area ratio
        Apanel = 4.322 #m2
        dP1 = 0        # in Pa per m2
        dP2 = 8000/(Aratio*Apanel)     # in Pa per m2
        dP3 = 22000/(Aratio*Apanel)    # in Pa per m2
        dP4 = 2000/(Aratio*Apanel)     #in Pa per m2
        #Fluids Cp [kJ/kgK] Density [kg/m3] Used for
        #Water-glyucol 33%  3.68            1044 Collector Loop
        #Water 4.19             998 Secondary collector loop, store, loops for auxiliary

    return n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Aratio, Apanel,dP1,dP2,dP3,dP4


"""
============================
auxiliary electricity solar collectort
============================

"""

def calc_Eaux_SC(qV_des, Dp_collector, Leq, Aa):
    Ro = 1000  # kg/m3
    dpl = 200 # pressure losses per length of pipe according to solar districts
    Fcr = 1.3 # factor losses of accessories
    Dp_friction = dpl*Leq*Aa*Fcr#HANZENWILIAMSN PA/M
    Eaux = (qV_des/Ro)*(Dp_collector+Dp_friction)/0.6/10 #energy necesary in kW from pumps
    return Eaux # energy spent in kWh


"""
============================
minimization of Eaux
============================

"""

def SelectminimumenergySc(q1,q2,q3,q4,E1,E2,E3,E4,m1,m2,m3,m4,dP1,dP2,dP3,dP4,Area_a):
    mopt = np.empty(8760)
    dpopt = np.empty(8760)
    const = Area_a/3600
    ms =  [m1*const,m2*const,m3*const,m4*const]  #float points
    dps = [dP1*Area_a,dP2*Area_a,dP3*Area_a,dP4*Area_a] #float points
    balances =  [q1-E1*2,q2-E2*2,q3-E3*2,q4-E4*2]#vectors #quality of electricity is twice as expensive
    for time in range(8760):
        balances2 = [balances[0][time],balances[1][time],balances[2][time],balances[3][time]]
        maxenergy = np.max(balances2)
        ix_maxenergy = np.where(balances2==maxenergy)
        mopt[time] = ms[ix_maxenergy[0][0]]
        dpopt[time] = dps[ix_maxenergy[0][0]]
    return mopt, dpopt


def Selectminimumenergy2(m, q, dp):
    for time in range(8760):
        if q[time] <= 0:
            m[time] = 0
            dp[time] = 0
    return m, dp


"""
============================
optimal angle and tilt
============================

"""

def optimal_angle_and_tilt(observers_all, latitude, worst_sh, worst_Az, transmittivity,
                           grid_side, module_lenght, angle_north, Min_Isol, Max_Isol):

    def Calc_optimal_angle(teta_z, latitude, transmissivity):
        if transmissivity <= 0.15:
            gKt = 0.977
        elif 0.15 < transmissivity <= 0.7:
            gKt = 1.237 - 1.361 * transmissivity
        else:
            gKt = 0.273
        Tad = 0.98
        Tar = 0.97
        Pg = 0.2  # ground reflectance of 0.2
        l = radians(latitude)
        a = radians(teta_z)  # this is surface azimuth
        b = atan((cos(a) * tan(l)) * (1 / (1 + ((Tad * gKt - Tar * Pg) / (2 * (1 - gKt))))))
        return degrees(b)

    def Calc_optimal_spacing(Sh, Az, tilt_angle, module_lenght):
        h = module_lenght * sin(radians(tilt_angle))
        D1 = h / tan(radians(Sh))
        D = max(D1 * cos(radians(180 - Az)), D1 * cos(radians(Az - 180)))
        return D

    def Calc_categoriesroof(teta_z, B, GB, Max_Isol):
        if -122.5 < teta_z <= -67:
            CATteta_z = 1
        elif -67 < teta_z <= -22.5:
            CATteta_z = 3
        elif -22.5 < teta_z <= 22.5:
            CATteta_z = 5
        elif 22.5 < teta_z <= 67:
            CATteta_z = 4
        elif 67 <= teta_z <= 122.5:
            CATteta_z = 2

        if 0 < B <= 5:
            CATB = 1  # flat roof
        elif 5 < B <= 15:
            CATB = 2  # tilted 25 degrees
        elif 15 < B <= 25:
            CATB = 3  # tilted 25 degrees
        elif 25 < B <= 40:
            CATB = 4  # tilted 25 degrees
        elif 40 < B <= 60:
            CATB = 5  # tilted 25 degrees
        elif B > 60:
            CATB = 6  # tilted 25 degrees

        GB_percent = GB / Max_Isol
        if 0 < GB_percent <= 0.25:
            CATGB = 1  # flat roof
        elif 0.25 < GB_percent <= 0.50:
            CATGB = 2
        elif 0.50 < GB_percent <= 0.75:
            CATGB = 3
        elif 0.75 < GB_percent <= 0.90:
            CATGB = 4
        elif 0.90 < GB_percent <= 1:
            CATGB = 5

        return CATB, CATGB, CATteta_z

    # calculate values for flat roofs Slope < 5 degrees.
    optimal_angle_flat = Calc_optimal_angle(0, latitude, transmittivity)
    optimal_spacing_flat = Calc_optimal_spacing(worst_sh, worst_Az, optimal_angle_flat, module_lenght)
    arcpy.AddField_management(observers_all, "array_s", "DOUBLE")
    arcpy.AddField_management(observers_all, "area_netpv", "DOUBLE")
    arcpy.AddField_management(observers_all, "CATB", "SHORT")
    arcpy.AddField_management(observers_all, "CATGB", "SHORT")
    arcpy.AddField_management(observers_all, "CATteta_z", "SHORT")
    fields = ('aspect', 'slope', 'GB', "array_s", "area_netpv", "CATB", "CATGB", "CATteta_z")
    # go inside the database and perform the changes
    with arcpy.da.UpdateCursor(observers_all, fields) as cursor:
        for row in cursor:
            aspect = row[0]
            slope = row[1]
            if slope > 5:  # no t a flat roof.
                B = slope
                array_s = 0
                if 180 <= aspect < 360:  # convert the aspect of arcgis to azimuth
                    teta_z = aspect - 180
                elif 0 < aspect < 180:
                    teta_z = aspect - 180  # negative in the east band
                elif aspect == 0 or aspect == 360:
                    teta_z = 180
                if -angle_north <= teta_z <= angle_north and row[2] > Min_Isol:
                    row[0] = teta_z
                    row[1] = B
                    row[3] = array_s
                    row[4] = (grid_side - array_s) / cos(radians(abs(B))) * grid_side
                    row[5], row[6], row[7] = Calc_categoriesroof(teta_z, B, row[2], Max_Isol)
                    cursor.updateRow(row)
                else:
                    cursor.deleteRow()
            else:
                teta_z = 0  # flat surface, all panels will be oriented towards south # optimal angle in degrees
                B = optimal_angle_flat
                array_s = optimal_spacing_flat
                if row[2] > Min_Isol:
                    row[0] = teta_z
                    row[1] = B
                    row[3] = array_s
                    row[4] = (grid_side - array_s) / cos(radians(abs(B))) * grid_side
                    row[5], row[6], row[7] = Calc_categoriesroof(teta_z, B, row[2], Max_Isol)
                    cursor.updateRow(row)
                else:
                    cursor.deleteRow()

"""
============================
investment and maintenance costs
============================

"""

def calc_Cinv_SC(Area):
    """
    Lifetime 35 years
    """
    InvCa = 2050 * Area /35 # [CHF/y]

    return InvCa


"""
============================
test
============================

"""

def test_solar_collector():
    import cea.inputlocator
    locator = cea.inputlocator.InputLocator(r'C:\reference-case\baseline')
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    weather_path = locator.get_default_weather()
    radiation = locator.get_radiation()
    gv = cea.globalvar.GlobalVariables()

    calc_SC(locator=locator, radiation = radiation, latitude=46.95240555555556, longitude=7.439583333333333, year=2014, gv=gv,
                             weather_path=weather_path)


if __name__ == '__main__':
    test_solar_collector()

