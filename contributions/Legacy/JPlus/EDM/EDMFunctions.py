# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #ENERGY DEMAND MODEL FUNCTIONS
# - It Includes all the functions for computation of hourly radiation in a centroid of any vertical surface. For the calculation it uses the solar analyst extension included in ArcGIS 10.1.
# - It also includes all the functions related to the estimation of end-uses of energy in buildings and related processes. These functions are part of the analytical and statistical modules for computation of energy dem

# <markdowncell>

# ####MODULES

# <codecell>

from __future__ import division
import arcpy
from arcpy import sa
import ephem
import sys,os
import pandas as pd
import datetime
import jdcal
from math import *
import scipy
import numpy as np
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")

# <markdowncell>

# ##1. RADIATION MODEL

# <markdowncell>

# 1. Calculation of hourly radiation in a day

# <codecell>

def CalcRadiation(day, CQ_name, memoryFeature , Observers, T_G_day, latitude, locationtemp1, aspect_slope, heightoffset):
    # Local Variables
    Latitude = str(latitude)
    skySize = '1800' #max 2400
    dayInterval = '1'
    hourInterval = '1'
    calcDirections = '32'
    zenithDivisions = '1200' #max 1400
    azimuthDivisions = '160'
    diffuseProp =  str(T_G_day.loc[day-1,'diff'])
    transmittivity =  str(T_G_day.loc[day-1,'ttr'])
    heightoffset = str(heightoffset)
    global_radiation = locationtemp1+'\\'+'Day_'+str(day)+'.shp'
    timeConfig =  'WithinDay    '+str(day)+', 0, 24'
    
     #Run the extension of arcgis
    arcpy.gp.PointsSolarRadiation_sa(memoryFeature, Observers, global_radiation, heightoffset,
        Latitude, skySize, timeConfig, dayInterval, hourInterval, "INTERVAL", "1", aspect_slope,
       calcDirections, zenithDivisions, azimuthDivisions, "STANDARD_OVERCAST_SKY",
        diffuseProp, transmittivity, "#", "#", "#")
    
    return arcpy.GetMessages()

# <codecell>

#1. Calculation of hourly radiation in year
def CalcRadiation_year(DEM, Observers, diffuseProp, transmittivity, latitude, Yearlyradiation):
    # Local Variables
    Latitude = str(latitude)
    skySize = '1400' #max 2400
    dayInterval = '14'
    hourInterval = '1'
    calcDirections = '32'
    zenithDivisions = '800' #max 1400
    azimuthDivisions = '160'
    diffuseProp =  str(diffuseProp)
    transmittivity =  str(transmittivity)
    heightoffset = '0'
    timeConfig =  "WholeYear   2014"
    
     #Run the extension of arcgis
    arcpy.gp.PointsSolarRadiation_sa(DEM, Observers, Yearlyradiation, heightoffset,
        Latitude, skySize, timeConfig, dayInterval, hourInterval, "NOINTERVAL", "1", "FROM_DEM",
       calcDirections, zenithDivisions, azimuthDivisions, "STANDARD_OVERCAST_SKY",
        diffuseProp, transmittivity, "#", "#", "#")
    
    return arcpy.GetMessages()

# <codecell>

def Calcfilter_observers(min_Isol,radiation_observers, filtered_observers):
    with arcpy.da.SearchCursor(radiation_observers,["T0"]) as cursor:
        for row in cursor:
            value = 0
            if row[0] > value:
                value = row[0]
    # condition
    Where_clausule =  "T0 >= %.2f" % (value * min_Isol)
    # selection
    arcpy.Select_analysis(radiation_observers,filtered_observers,Where_clausule) # routine

# <codecell>

def Calc_diffuseground_comp(tilt_radians):
    tilt = degrees(tilt_radians)
    teta_ed  = 59.68-0.1388*tilt+0.001497*tilt**2 # angle in degrees
    teta_eG = 90-0.5788*tilt+0.002693*tilt**2 # angle in degrees
    return radians(teta_ed), radians(teta_eG)

# <codecell>

def Calc_Sm_PV(te, I_sol, I_direct, I_diffuse, tilt, lat, teta_z, ha, g, Sz, Az, teta, tetad, tetaeg, areagroup, type_panel,misc_losses,
               n, Pg, K, eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L): #ha is local solar time
    #calcualte ratio of beam radiation on a tilted plane
    # to avoid inconvergence when I_sol = 0
    lim1 = radians(0)
    lim2 = radians(90)
    lim3 = radians(89.999)
    if teta < lim1:
        teta = min(lim3,abs(teta))
    if teta >= lim2:
        teta = lim3
    if Sz < lim1:
        Sz = min(lim3,abs(Sz))
    if Sz >= lim2:
        Sz = lim3
    Rb = cos(teta)/cos(Sz) # teta_z is Zenith angle

    # calculate the specific air mass
    m = 1/cos(Sz)
    M = a0 + a1 * m + a2 * m ** 2 + a3 * m ** 3 + a4 * m ** 4

    #angle refractive  (aproximation accrding to Soteris A.)
    teta_r = asin(sin(teta)/n) # in radians
    Ta_n = exp(-K*L)*(1-((n-1)/(n+1))**2)
    #calculate parameters of anlge modifier #first for the direct radiation
    if teta < 1.5707: # 90 degrees in radians
        part1 = teta_r+teta 
        part2 = teta_r-teta 
        Ta_B = exp((-K*L)/cos(teta_r))*(1-0.5*((sin(part2)**2)/(sin(part1)**2)+(tan(part2)**2)/(tan(part1)**2)))
        kteta_B = Ta_B/Ta_n
    else:
        kteta_B = 0
    
    #angle refractive for diffuse radiation
    teta_r = asin(sin(tetad)/n) # in radians
    part1 = teta_r+tetad
    part2 = teta_r-tetad
    Ta_D = exp((-K*L)/cos(teta_r))*(1-0.5*((sin(part2)**2)/(sin(part1)**2)+(tan(part2)**2)/(tan(part1)**2)))
    kteta_D = Ta_D/Ta_n

    #angle refractive for global radiatoon
    teta_r = asin(sin(tetaeg)/n) # in radians
    part1 = teta_r+tetaeg
    part2 = teta_r-tetaeg
    Ta_eG = exp((-K*L)/cos(teta_r))*(1-0.5*((sin(part2)**2)/(sin(part1)**2)+(tan(part2)**2)/(tan(part1)**2)))
    kteta_eG =  Ta_eG/Ta_n

    #absorbed solar radiation
    S = M*Ta_n*(kteta_B*I_direct*Rb+kteta_D*I_diffuse*(1+cos(tilt))/2+kteta_eG*I_sol*Pg*(1-cos(tilt))/2) # in W
    if S <=0: # when points are 0 and too much losses
        S = 0
    #temperature of cell
    Tcell = te + S*(NOCT-20)/(800)
    
    return S, Tcell

# <codecell>

def Calc_PV_power(S, Tcell, eff_nom, areagroup, Bref,misc_losses):
    P = eff_nom*areagroup*S*(1-Bref*(Tcell-25))*(1-misc_losses)/1000 # Osterwald, 1986) in kWatts
    return P

# <codecell>

# calculate the optimal slopes and modify the observers slope and angle.
def hour_angle(dt, longit, latit=0, elev=0):
    obs = ephem.Observer()
    obs.date = dt.strftime('%Y/%m/%d %H:%M:%S')
    obs.lon = longit
    obs.lat = latit
    obs.elevation = elev
    sun = ephem.Sun()
    sun.compute(obs)
    # get right ascention
    ra = ephem.degrees(sun.g_ra) - 2 * ephem.pi

    # get sidereal time at greenwich (AA ch12)
    jd = ephem.julian_date(dt)
    t = (jd - 2451545.0) / 36525
    theta = 280.46061837 + 360.98564736629 * (jd - 2451545) \
            + .000387933 * t**2 - t**3 / 38710000

    # hour angle (AA ch13)
    ha = (theta + longit - ra * 180 / ephem.pi) % 360
    if ha > 180:
        ha = ha - 360
    return ha

# <codecell>

def Calc_optimal_angle(teta_z,latitude,transmissivity):
    if transmissivity <= 0.15:
        gKt = 0.977
    elif  0.15 < transmissivity <= 0.7:
        gKt = 1.237-1.361*transmissivity
    else:
        gKt = 0.273
    Tad = 0.98
    Tar = 0.97
    Pg = 0.2 # ground reflectance of 0.2
    l = radians(latitude)
    a = radians(teta_z) # this is surface azimuth
    b = atan((cos(a)*tan(l))*(1/(1+((Tad*gKt-Tar*Pg)/(2*(1-gKt))))))
    return degrees(b)

# <codecell>

def Calc_optimal_spacing(teta_z,Sh,tilt_angle,module_lenght):
    h = module_lenght*sin(radians(tilt_angle))
    D1 = h/tan(radians(Sh))
    D  = max(D1*cos(radians(180-teta_z)),D1*cos(radians(teta_z-180)))
    return D

# <codecell>

def optimal_angle_and_tilt(observers_all,latitude,worst_sh, worst_Az, transmittivity, diffuseProp,
                           grid_side, module_lenght,angle_north, Min_Isol, Max_Isol):
    #calculate values for flat roofs Slope < 5 degrees.
    optimal_angle_flat = Calc_optimal_angle(0,latitude,transmittivity)
    optimal_spacing_flat = Calc_optimal_spacing(worst_sh,worst_Az,optimal_angle_flat,module_lenght)
    arcpy.AddField_management(observers_all, "array_s", "DOUBLE")
    arcpy.AddField_management(observers_all, "area_netpv", "DOUBLE")
    arcpy.AddField_management(observers_all, "CATB", "SHORT")
    arcpy.AddField_management(observers_all, "CATGB", "SHORT")
    arcpy.AddField_management(observers_all, "CATteta_z", "SHORT")
    fields = ('aspect','slope','GB',"array_s","area_netpv","CATB","CATGB","CATteta_z")
    # go inside the database and perform the changes
    with arcpy.da.UpdateCursor(observers_all,fields) as cursor:
        for row in cursor:
            aspect = row[0]
            slope = row[1]
            if slope > 5: # no t a flat roof.
                B = slope
                array_s = 0
                if 180 <= aspect < 360:            # convert the aspect of arcgis to azimuth
                    teta_z =   aspect -  180
                elif 0 < aspect < 180:
                    teta_z = aspect - 180 # negative in the east band
                elif aspect == 0 or aspect == 360:
                    teta_z = 180
                if -angle_north <= teta_z <= angle_north  and row[2] > Min_Isol:
                    row[0] = teta_z
                    row[1] = B
                    row[3] = array_s
                    row[4] = (grid_side-array_s)/cos(radians(abs(B)))*grid_side
                    row[5], row[6], row[7] = Calc_categoriesroof(teta_z,B,row[2],Max_Isol)
                    cursor.updateRow(row)
                else:
                    cursor.deleteRow()
            else:
                teta_z = 0 # flat surface, all panels will be oriented towards south # optimal angle in degrees
                B = optimal_angle_flat
                array_s = optimal_spacing_flat
                if row[2] > Min_Isol:
                    row[0] = teta_z
                    row[1] = B
                    row[3] = array_s
                    row[4] = (grid_side-array_s)/cos(radians(abs(B)))*grid_side
                    row[5], row[6], row[7] = Calc_categoriesroof(teta_z,B,row[2],Max_Isol)
                    cursor.updateRow(row)
                else:
                    cursor.deleteRow()

# <codecell>

def Calc_categoriesroof(teta_z,B,GB,Max_Isol):
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


        
    if 0 < B <=5:
        CATB = 1 # flat roof
    elif  5 < B <= 15:
        CATB = 2 #tilted 25 degrees
    elif 15< B <= 25:
        CATB = 3 #tilted 25 degrees
    elif 25< B <= 40:  
        CATB = 4 #tilted 25 degrees
    elif 40< B <= 60:  
        CATB = 5 #tilted 25 degrees
    elif B > 60:  
        CATB = 6 #tilted 25 degrees

    GB_percent =  GB/Max_Isol     
    if 0 < GB_percent <= 0.25:
        CATGB = 1 # flat roof
    elif  0.25 < GB_percent <= 0.50:
        CATGB = 2 
    elif 0.50< GB_percent <= 0.75:
        CATGB = 3 
    elif 0.75< GB_percent <= 0.90:  
        CATGB = 4 
    elif 0.90< GB_percent <= 1:  
        CATGB = 5 
    
    return CATB, CATGB, CATteta_z

# <codecell>

def calc_propertiesPV(type_PVpanel):
    if type_PVpanel == 1:#     # assuming only monocrystalline panels.    
        eff_nom = 0.16 # GTM 2014
        NOCT = 43.5 # Fanney et al.,
        Bref = 0.0035  # Fuentes et al.,Luque and Hegedus, 2003).
        a0 = 0.935823
        a1 = 0.054289
        a2 = -0.008677
        a3 = 0.000527
        a4 = -0.000011
        L = 0.002 # glazing tickness
    if type_PVpanel == 2:#     # polycristalline  
        eff_nom = 0.15 # GTM 2014
        NOCT = 43.9 # Fanney et al.,
        Bref = 0.0044 
        a0 = 0.918093
        a1 = 0.086257
        a2 = -0.024459
        a3 = 0.002816
        a4 = -0.000126
        L = 0.002 # glazing tickness
    if type_PVpanel == 3:#     # amorphous  
        eff_nom = 0.08  # GTM 2014
        NOCT = 38.1 # Fanney et al.,
        Bref = 0.0026
        a0 = 1.10044085
        a1 = -0.06142323
        a2 = -0.00442732
        a3 = 0.000631504
        a4 = -0.000019184
        L = 0.0002 # glazing tickness

    return eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L

# <codecell>

def calc_propertiesSC(type_SCpanel):
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

# <codecell>

def calc_anglemodifierSC(Az_vector, g_vector, ha_vector, teta_z, tilt_angle, type_SCpanel, latitude, Sz_vector):
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

# <codecell>

def calc_SolarZenith(ha,lat,g):
    Szenith = acos(sin(lat)*sin(g)+cos(lat)*cos(g)*cos(ha))
    return Szenith

# <codecell>

def Calc_IAMb(teta_l,teta_T, type_SCpanel):
    if type_SCpanel == 1:#     # Flat plate collector   SOLEX blu SFP, 2012 
        IAM_b = -0.00000002127039627042*teta_l**4 + 0.00000143550893550934*teta_l**3 - 0.00008493589743580050*teta_l**2 + 0.00041588966590833100*teta_l + 0.99930069929920900000
    if type_SCpanel == 2:#     # evacuated tube   Zewotherm SOL ZX-30 SFP, 2012 
        IAML = -0.00000003365384615386*teta_l**4 + 0.00000268745143745027*teta_l**3 - 0.00010196678321666700*teta_l**2 + 0.00088830613832779900*teta_l + 0.99793706293541500000
        IAMT = 0.000000002794872*teta_T**5- 0.000000534731935*teta_T**4 + 0.000027381118880*teta_T**3- 0.000326340326281*teta_T**2 + 0.002973799531468*teta_T + 1.000713286764210
        IAM_b = IAMT*IAML #overall incidence angle modifier for beam radiation
    return IAM_b

# <codecell>

def calc_Teta_L(Az,teta_z,tilt, Sz):
    #calculate incident angles longitudinal and trasnversally of the solar collector
    teta_la = tan(Sz)*cos(teta_z-Az)
    teta_l = degrees(abs(atan(teta_la)-tilt)) # longitudinal incidence angle 
    if teta_l < 0:
        teta_l = min(89,abs(teta_T))
    if teta_l >= 90:
        teta_l = 89.999
    return teta_l # in degrees

# <codecell>

def Calc_incidenteangleB(g, lat, ha, tilt, teta_z):
    #calculate incident angle beam radiation
    part1 = sin(lat)*sin(g)*cos(tilt)-cos(lat)*sin(g)*sin(tilt)*cos(teta_z)
    part2 = cos(lat)*cos(g)*cos(ha)*cos(tilt)+sin(lat)*cos(g)*cos(ha)*sin(tilt)*cos(teta_z)
    part3 = cos(g)*sin(ha)*sin(tilt)*sin(teta_z)
    teta_B = acos(part1+part2+part3)
    return teta_B #in radains

# <codecell>

def calc_Teta_T(Az, Sz, teta_z, teta_B): #Az is the solar azimuth
    #calculate incident angles transversal
    teta_ta = sin(Sz)*sin(abs(teta_z-Az))
    teta_T = degrees(atan(teta_ta/cos(teta_ta))) # transversal angle modifier
    if teta_T < 0:
        teta_T = min(89,abs(teta_T))
    if teta_T >= 90:
        teta_T = 89.999
    return teta_T

# <codecell>

def calc_maxtetaL(teta_L):
    if teta_L < 0:
        teta_L = min(89,abs(teta_L))
    if teta_L >= 90:
        teta_L = 89.999
    return teta_L

# <codecell>

def Calc_incl_angle(x):
    g = 23.45*sin(radians((360/365)*(284+x)))
    return g

# <codecell>

def SC_generation(type_SCpanel, group_radiation, prop_observers, number_points, T_G_hour, latitude, Tin, height):    
    # get properties of the panel to evaluate
    n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Aratio, Apanel, dP1,dP2,dP3,dP4 = calc_propertiesSC(type_SCpanel)
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
        radiation['I_diffuse'] = T_G_hour.ratio_diffhout*radiation.I_sol #calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']  #direct radaition
        
        #calculate angle modifiers              
        T_G_hour['IAM_b']  = calc_anglemodifierSC(T_G_hour.Az,T_G_hour.g,T_G_hour.ha,teta_z,tilt_angle,type_SCpanel,latitude, T_G_hour.Sz) #direct angle modifier
    
        listresults[group] = Calc_SC_module2(radiation,tilt_angle, T_G_hour.IAM_b, radiation.I_direct, radiation.I_diffuse,T_G_hour.te,
                                            n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Area_a, dP1,dP2,dP3,dP4, Tin, Leq, Le,Nseg)
        
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

# <codecell>

def Calc_pv_generation(type_panel, hourly_radiation, Number_groups, number_points, prop_observers, T_G_hour, latitude, misc_losses):
    lat = radians(latitude)
    g_vector = np.radians(T_G_hour.g)
    ha_vector = np.radians(T_G_hour.ha)  
    Sz_vector = np.radians(T_G_hour.Sz)
    Az_vector = np.radians(T_G_hour.Az)
    result = list(range(Number_groups))
    areagroups = list(range(Number_groups))
    Sum_PV = np.zeros(8760)
    
    n = 1.526 #refractive index of galss
    Pg = 0.2 # ground reflectance
    K = 0.4 # extinction coefficien
    eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L  = calc_propertiesPV(type_panel)
    
    for group in range(Number_groups):
        teta_z = prop_observers.loc[group,'aspect'] #azimuth of paneles of group
        areagroup = prop_observers.loc[group,'area_netpv']*number_points[group]
        tilt_angle = prop_observers.loc[group,'slope'] #tilt angle of panels
        radiation = pd.DataFrame({'I_sol':hourly_radiation[group]}) #choose vector with all values of Isol
        radiation['I_diffuse'] = T_G_hour.ratio_diffhout*radiation.I_sol #calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']  #direct radaition
        
        #to radians of properties - solar position and tilt angle
        tilt = radians(tilt_angle) #slope of panel
        teta_z = radians(teta_z) #azimuth of panel
        
        #calculate angles necesary
        teta_vector = np.vectorize(Calc_incidenteangleB)(g_vector, lat, ha_vector, tilt, teta_z)
        teta_ed, teta_eG  = Calc_diffuseground_comp(tilt)
        
        results = np.vectorize(Calc_Sm_PV)(T_G_hour.te,radiation.I_sol, radiation.I_direct, radiation.I_diffuse, tilt, lat, teta_z, ha_vector, g_vector,
                                              Sz_vector, Az_vector, teta_vector, teta_ed, teta_eG, areagroup,type_panel, misc_losses,
                                              n, Pg, K, eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L)
        
        
        result[group] = np.vectorize(Calc_PV_power)(results[0], results[1], eff_nom, areagroup, Bref,misc_losses)
        areagroups[group] = areagroup
        
        Sum_PV = Sum_PV + result[group]
        
    Final = pd.DataFrame({'PV_kWh':Sum_PV,'Area':sum(areagroups)})    
    return result, Final

# <codecell>

def calc_PVT_generation(type_panel, hourly_radiation, Number_groups, number_points, prop_observers, T_G_hour, latitude, misc_losses,
                          type_SCpanel, Tin, height):
    lat = radians(latitude)
    g_vector = np.radians(T_G_hour.g)
    ha_vector = np.radians(T_G_hour.ha)  
    Sz_vector = np.radians(T_G_hour.Sz)
    Az_vector = np.radians(T_G_hour.Az)
    
    # get properties of the panel to evaluate
    n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Aratio, Apanel, dP1,dP2,dP3,dP4 = calc_propertiesSC(type_SCpanel)
    Area_a = Aratio*Apanel
    listresults = list(range(Number_groups))
    listareasgroups = list(range(Number_groups))
    
    Sum_mcp = np.zeros(8760)
    Sum_qout = np.zeros(8760)
    Sum_Eaux = np.zeros(8760)
    Sum_qloss = np.zeros(8760)
    Sum_PV = np.zeros(8760)
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
        
    # get properties of PV panel
    n = 1.526 #refractive index of galss
    Pg = 0.2 # ground reflectance
    K = 0.4 # extinction coefficien
    eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L  = calc_propertiesPV(type_panel)
    
    for group in range(Number_groups):
        teta_z = prop_observers.loc[group,'aspect'] #azimuth of paneles of group
        areagroup = prop_observers.loc[group,'area_netpv']*number_points[group]
        tilt_angle = prop_observers.loc[group,'slope'] #tilt angle of panels
        radiation = pd.DataFrame({'I_sol':hourly_radiation[group]}) #choose vector with all values of Isol
        radiation['I_diffuse'] = T_G_hour.ratio_diffhout*radiation.I_sol #calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']  #direct radaition
        
        #to radians of properties - solar position and tilt angle
        tilt = radians(tilt_angle) #slope of panel
        teta_z = radians(teta_z) #azimuth of panel
        
        #calculate angles necesary
        teta_vector = np.vectorize(Calc_incidenteangleB)(g_vector, lat, ha_vector, tilt, teta_z)
        teta_ed, teta_eG  = Calc_diffuseground_comp(tilt)
        
        results = np.vectorize(Calc_Sm_PV)(T_G_hour.te,radiation.I_sol, radiation.I_direct.copy(), radiation.I_diffuse.copy(), tilt, lat, teta_z, ha_vector, g_vector,
                                              Sz_vector, Az_vector, teta_vector, teta_ed, teta_eG, areagroup,type_panel, misc_losses,
                                              n, Pg, K, eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L)
        
        #calculate angle modifiers              
        T_G_hour['IAM_b']  = calc_anglemodifierSC(T_G_hour.Az,T_G_hour.g,T_G_hour.ha,teta_z,tilt_angle,type_SCpanel,latitude, T_G_hour.Sz)
        
        listresults[group] = Calc_PVT_module(tilt_angle, T_G_hour.IAM_b.copy(), radiation.I_direct.copy(), radiation.I_diffuse.copy(),T_G_hour.te,
                                             n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Area_a, dP1,dP2,dP3,dP4, Tin, Leq, Le,Nseg,
                                             eff_nom,Bref,results[0].copy(), results[1].copy(), misc_losses,areagroup)
    
        Kons = areagroup/Apanel
        Sum_mcp = Sum_mcp + listresults[group][5]*Kons
        Sum_qloss = Sum_qloss + listresults[group][0]*Kons
        Sum_qout = Sum_qout + listresults[group][1]*Kons
        Sum_Eaux = Sum_Eaux + listresults[group][2]*Kons
        Sum_PV = Sum_PV + listresults[group][6]
        listareasgroups[group] = areagroup
        
    Tout_group = (Sum_qout/Sum_mcp) + Tin  # in C
    Final = pd.DataFrame({'Qsc_KWh':Sum_qout,'Tscs':Tin_array,'Tscr':Tout_group, 'mcp_kW/C': Sum_mcp,'Eaux_kWh': Sum_Eaux,
                          'Qsc_l_KWh': Sum_qloss,'PV_kWh':Sum_PV, 'Area':sum(listareasgroups)},index = range(8760))         
    
    return listresults, Final

# <codecell>

def Calc_PVT_module(tilt_angle, IAM_b_vector, I_direct_vector, I_diffuse_vector,Te_vector,
                    n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Area_a, dP1,dP2,dP3,dP4, Tin, Leq, Le, Nseg,
                    eff_nom,Bref,Sm_pv, Tcell_pv,misc_losses,areagroup):
    #panel to store the results per flow
    #method with no condensaiton gains, no wind or long-wave dependency, sky factor set to zero.
    # calculate radiation part
    #local variables
    Cpwg = 3680#J/kgK  water grlycol  specific heat  
    maxmsc = mB_max_r*Area_a/3600
    #Do the calculation of every time step for every possible flow condition
    #get states where highly performing values are obtained.
    mopt = 0 #para iniciar
    Tcell = []
    temperature_out =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    temperature_in =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    supply_out =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    supply_losses =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    Auxiliary =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    temperature_m =[np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760),np.zeros(8760)]
    specific_flows = [np.zeros(8760), (np.zeros(8760)+mB0_r)*Area_a/3600, (np.zeros(8760)+mB_max_r)*Area_a/3600,(np.zeros(8760)+mB_min_r)*Area_a/3600, np.zeros(8760),np.zeros(8760)] # in kg/s
    specific_pressurelosses = [np.zeros(8760),(np.zeros(8760)+dP2)*Area_a,(np.zeros(8760)+dP3)*Area_a,(np.zeros(8760)+dP4)*Area_a,np.zeros(8760),np.zeros(8760)] # in Pa
    supply_out_pre = np.zeros(8760)
    supply_out_total = np.zeros(8760)
    mcp = np.zeros(8760)
    
	#calculate net radiant heat (absorbed)
    tilt = radians(tilt_angle)
    qrad_vector = np.vectorize(calc_qrad)(n0, IAM_b_vector, I_direct_vector, IAM_d, I_diffuse_vector, tilt) # in W/m2 is a mean of the group
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
            c1_pvt = c1 - eff_nom*Bref*Sm_pv[time]
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
                Tout = Tin+(qrad-((c1_pvt)+0.5)*(Tin-Te))/(Mfl*Cpwg/Area_a)
                Tfl[2] = (Tin+Tout)/2
            else:
                Tout = Te+qrad/(c1_pvt+0.5)
                Tfl[2] = Tout #fluid temperature same as output
            DT[1] = Tfl[2] - Te
            
            #calculate qgain with the guess
                              
            qgain = calc_qgain(Tfl,Tabs,qrad,DT, Tin, Tout, Area_a, c1_pvt, c2, Mfl, delts,Cpwg, C_eff,Te)
            
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
                    qgain = calc_qgain(Tfl,Tabs,qrad, DT, TinSeg, Tout, Aseg, c1_pvt, c2, Mfl, delts,Cpwg, C_eff,Te)
                    ToutSeg = Tout
                    if Mfl > 0:
                        TflB[Iseg] = (TinSeg+ToutSeg)/2
                        ToutSeg = TflA[Iseg] + (qgain*Delts)/C_eff
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
            Auxiliary[flow] = np.vectorize(Calc_EauxSC)(specific_flows[flow],specific_pressurelosses[flow], Leq, Area_a) #in kW
        if flow == 3:
            q1 = supply_out[0]
            q2 = supply_out[1]
            q3 = supply_out[2]
            q4 = supply_out[3]
            E1 = Auxiliary[0] 
            E2 = Auxiliary[1] 
            E3 = Auxiliary[2] 
            E4 = Auxiliary[3] 
            specific_flows[4], specific_pressurelosses[4] = SelectminimumenergySc(q1,q2,q3,q4,E1,E2,E3,E4, 0, mB0_r, mB_max_r,mB_min_r,0, dP2,dP3,dP4, Area_a)
        if flow == 4:
            Auxiliary[flow] = np.vectorize(Calc_EauxSC)(specific_flows[flow],specific_pressurelosses[flow], Leq, Area_a) #in kW
            dp5 = specific_pressurelosses[flow]
            q5 = supply_out[flow]
            m5 = specific_flows[flow]
            ##poits where load is negative
            specific_flows[5], specific_pressurelosses[5] = Selectminimumenergy2(m5,q5,dp5)
        if flow == 5:
            supply_losses[flow] = np.vectorize(Calc_qloss_net)(specific_flows[flow],Le,Area_a,temperature_m[flow], Te_vector, maxmsc)
            supply_out_pre = supply_out[flow].copy() + supply_losses[flow].copy()
            Auxiliary[flow] = np.vectorize(Calc_EauxSC)(specific_flows[flow],specific_pressurelosses[flow], Leq, Area_a) # in kW
            supply_out_total = supply_out + 0.5*Auxiliary[flow] - supply_losses[flow]
            mcp = specific_flows[flow]*(Cpwg/1000) # mcp in kW/c
    
    for x in range(8760):
        if supply_out_total[5][x] <= 0: # the dem is zero
            supply_out_total[5][x] = 0
            Auxiliary[5][x] = 0  
            temperature_out[5][x] = 0
            temperature_in[5][x] = 0
        Tcell.append((temperature_out[5][x]+temperature_in[5][x])/2)
        if Tcell[x] == 0:
            Tcell[x] = Tcell_pv[x]
    
    PV_generation = np.vectorize(Calc_PV_power)(Sm_pv, Tcell, eff_nom, areagroup, Bref,misc_losses)
    result = [supply_losses[5], supply_out_total[5], Auxiliary[5], temperature_out[flow], temperature_in[flow], mcp, PV_generation]
    return result

# <codecell>

def Calc_qloss_net(Mfl,Le,Area_a,Tm,Te, maxmsc):
    qloss = 0.217*Le*Area_a*(Tm-Te)*(Mfl/maxmsc)/1000
    return qloss #in kW

# <codecell>

def Selectminimumenergy2(m, q, dp):
    for time in range(8760):
        if q[time] <= 0:
            m[time] = 0
            dp[time] = 0
    return m, dp

# <codecell>

def Calc_EauxSC(qV_des,Dp_collector, Leq, Aa):
    Ro = 1000  # kg/m3
    dpl = 200 # pressure losses per length of pipe according to solar districts
    Fcr = 1.3 # factor losses of accessories
    Dp_friction = dpl*Leq*Aa*Fcr#HANZENWILIAMSN PA/M
    Eaux = (qV_des/Ro)*(Dp_collector+Dp_friction)/0.6/10 #energy necesary in kW from pumps
    return Eaux # energy spent in kWh

# <codecell>

def Calc_SC_module2(radiation,tilt_angle, IAM_b_vector, I_direct_vector, I_diffuse_vector,Te_vector, n0,c1,c2, mB0_r, mB_max_r,mB_min_r,C_eff, t_max, IAM_d, Area_a, dP1,dP2,dP3,dP4, Tin, Leq, Le, Nseg):
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
    specific_flows = [np.zeros(8760), (np.zeros(8760)+mB0_r)*Area_a/3600, (np.zeros(8760)+mB_max_r)*Area_a/3600,(np.zeros(8760)+mB_min_r)*Area_a/3600, np.zeros(8760),np.zeros(8760)] # in kg/s
    specific_pressurelosses = [np.zeros(8760),(np.zeros(8760)+dP2)*Area_a,(np.zeros(8760)+dP3)*Area_a,(np.zeros(8760)+dP4)*Area_a,np.zeros(8760),np.zeros(8760)] # in Pa
    supply_out_pre = np.zeros(8760)
    supply_out_total = np.zeros(8760)
    mcp = np.zeros(8760)

	#calculate net radiant heat (absorbed)
    tilt = radians(tilt_angle)
    qrad_vector = np.vectorize(calc_qrad)(n0, IAM_b_vector, I_direct_vector, IAM_d, I_diffuse_vector, tilt) # in W/m2 is a mean of the group
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
                        ToutSeg = TflA[Iseg] + (qgain*Delts)/C_eff
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
            Auxiliary[flow] = np.vectorize(Calc_EauxSC)(specific_flows[flow],specific_pressurelosses[flow], Leq, Area_a) #in kW
        if flow == 3:
            q1 = supply_out[0]
            q2 = supply_out[1]
            q3 = supply_out[2]
            q4 = supply_out[3]
            E1 = Auxiliary[0] 
            E2 = Auxiliary[1] 
            E3 = Auxiliary[2] 
            E4 = Auxiliary[3] 
            specific_flows[4], specific_pressurelosses[4] = SelectminimumenergySc(q1,q2,q3,q4,E1,E2,E3,E4, 0, mB0_r, mB_max_r,mB_min_r,0, dP2,dP3,dP4, Area_a)
        if flow == 4:
            Auxiliary[flow] = np.vectorize(Calc_EauxSC)(specific_flows[flow],specific_pressurelosses[flow], Leq, Area_a) #in kW
            dp5 = specific_pressurelosses[flow]
            q5 = supply_out[flow]
            m5 = specific_flows[flow]
            ##poits where load is negative
            specific_flows[5], specific_pressurelosses[5] = Selectminimumenergy2(m5,q5,dp5)
        if flow == 5:
            supply_losses[flow] = np.vectorize(Calc_qloss_net)(specific_flows[flow],Le,Area_a,temperature_m[flow], Te_vector, maxmsc)
            supply_out_pre = supply_out[flow].copy() + supply_losses[flow].copy()
            Auxiliary[flow] = np.vectorize(Calc_EauxSC)(specific_flows[flow],specific_pressurelosses[flow], Leq, Area_a) # in kW
            supply_out_total= supply_out + 0.5*Auxiliary[flow] - supply_losses[flow]
            mcp = specific_flows[flow]*(Cpwg/1000) # mcp in kW/c

    result = [supply_losses[5], supply_out_total[5], Auxiliary[5], temperature_out[flow], temperature_in[flow], mcp]
    return result

# <codecell>

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

# <codecell>

def calc_qgain(Tfl,Tabs,qrad,DT, TinSub, Tout, Aseg, c1, c2, Mfl, delts,Cpwg, C_eff,Te):
    xgain = 1
    xgainmax = 100
    exit = False
    while exit == False:
        qgain = qrad - c1*(DT[1])-c2*abs(DT[1])*DT[1]
        if Mfl>0:
            Tout=((Mfl*Cpwg*TinSub)/Aseg - (C_eff*TinSub)/(2*delts) + qgain + (C_eff*Tfl[1])/delts)/(Mfl*Cpwg/Aseg + C_eff/(2*delts))
            Tfl[2]= (TinSub+Tout)/2
            DT[2] = Tfl[2]-Te
            qdiff = Mfl/Aseg*Cpwg*2*(DT[2]-DT[1])
        else:
            Tout = Tfl[1]+(qgain*delts)/C_eff
            Tfl[2] = Tout
            DT[2] = Tfl[2]-Te
            qdiff = 5*(DT[2]-DT[1])
        if abs(qdiff<0.1):
            DT[1]=DT[2]
            exit = True
        else:
            if xgain>40:
                DT[1] = (DT[1]+DT[2])/2
                if xgain == xgainmax:
                    exit = True
            else:
                DT[1]=DT[2] 
    qout = Mfl*Cpwg*(Tout-TinSub)/Aseg
    qmtherm = (Tfl[2]-Tfl[1])*C_eff/delts
    qbal = qgain-qout-qmtherm
    if abs(qbal) > 1:
        qbal = qbal
    return qgain

# <codecell>

def calc_qrad(n0, IAM_b, I_direct, IAM_d, I_diffuse, tilt):
    qrad = n0*IAM_b*I_direct+n0*IAM_d*I_diffuse*(1+cos(tilt))/2
    return qrad

# <markdowncell>

# 1.1 Sub-function to calculate radiation non-sunshinehours

# <codecell>

def calc_radiationday(day, T_G_day, route):
    radiation_sunnyhours = dbf2df(route+'\\'+'Day_'+str(day)+'.dbf')
    #Obtain the number of points modeled to do the iterations
    radiation_sunnyhours['ID'] = 0
    counter = radiation_sunnyhours.ID.count()
    value = counter+1
    radiation_sunnyhours['ID'] = range(1, value)
    
    # Table with empty values with the same range as the points.
    Table = pd.DataFrame.copy(radiation_sunnyhours)
    Names = ['T0','T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12','T13','T14','T15','T16','T17','T18','T19','T20','T21','T22','T23']
    for Name in Names:
        Table[Name]= 0
    #Counter of Columns in the Initial Table
    Counter = radiation_sunnyhours.count(1)
    Value = Counter[0]-1
    #Condition to take into account daysavingtime in Switzerland as the radiation data in ArcGIS is calculated for 2013.    
    if 90 <= day <300: 
        D = 1
    else:
        D = 0 
    # Calculation of Sunrise time
    Sunrise_time = T_G_day.loc[day-1,'sunrise']
    # Calculation of table
    for time in range(Value):
        Hour = int(Sunrise_time)+ int(time)
        Table['T'+str(Hour)] = radiation_sunnyhours['T'+str(time)]
    #rename the table for every T to get in 1 to 8760 hours.
    if day == 1:
        name = 1
    else:
        name = int(day-1)*24+1
    
    Table.rename(columns={'T0':'T'+str(name),'T1':'T'+str(name+1),'T2':'T'+str(name+2),'T3':'T'+str(name+3),'T4':'T'+str(name+4),
                                    'T5':'T'+str(name+5),'T6':'T'+str(name+6),'T7':'T'+str(name+7),'T8':'T'+str(name+8),'T9':'T'+str(name+9),
                                    'T10':'T'+str(name+10),'T11':'T'+str(name+11),'T12':'T'+str(name+12),'T13':'T'+str(name+13),'T14':'T'+str(name+14),
                                    'T15':'T'+str(name+15),'T16':'T'+str(name+16),'T17':'T'+str(name+17),'T18':'T'+str(name+18),'T19':'T'+str(name+19),
                                    'T20':'T'+str(name+20),'T21':'T'+str(name+21),'T22':'T'+str(name+22),'T23':'T'+str(name+23),'ID':'ID'},inplace=True)
    
    return Table

# <codecell>

def calc_sunrise(T_G_day,Yearsimul,timezone,longitude,latitude):
    o = ephem.Observer()
    o.lat = str(latitude)
    o.long = str(longitude)
    s = ephem.Sun()
    for day in range(1,366): # Calculated according to NOAA website  
        o.date = datetime.datetime(Yearsimul, 1, 1) + datetime.timedelta(day-1)
        next_event = o.next_rising(s)
        T_G_day.loc[day-1,'sunrise'] = ephem.localtime(next_event).hour
    return T_G_day

# <markdowncell>

# 2. Burn buildings into DEM

# <codecell>

def Burn(Buildings,DEM,DEMfinal,locationtemp1, locationtemp2, database,  DEM_extent):

    #Create a raster with all the buildings
    Outraster = locationtemp1+'\\'+'AllRaster'
    arcpy.env.extent = DEM_extent #These coordinates are extracted from the environment settings/once the DEM raster is selected directly in ArcGIS,
    arcpy.FeatureToRaster_conversion(Buildings,'height',Outraster,'0.5') #creating raster of the footprints of the buildings
    
    #Clear non values and add all the Buildings to the DEM 
    OutNullRas = sa.IsNull(Outraster) # identify noData Locations
    Output = sa.Con(OutNullRas == 1,0,Outraster)
    RadiationDEM = sa.Raster(DEM) + Output
    RadiationDEM.save(DEMfinal)
    return arcpy.GetMessages()

# <codecell>

def Burn3D(Buildings,DEM,DEMfinal,locationtemp1, locationtemp2, database,  DEM_extent):

    #Create a raster with all the buildings keeping the height
    Outraster = locationtemp1+'\\'+'AllRaster'
    arcpy.env.extent = DEM_extent #These coordinates are extracted from the environment settings/once the DEM raster is selected directly in ArcGIS,
    arcpy.MultipatchToRaster_conversion(Buildings,Outraster,'0.5') #creating raster of the footprints of the buildings
    
    #Clear non values to 0 to make the sumation
    OutNullRas = sa.IsNull(Outraster) # identify noData Locations
    Output = sa.Con(OutNullRas == 1,0,Outraster)
    
    #replace values of the new 
    RadiationDEM = sa.Raster(DEM)
    radiationout = sa.Con(Output > 0, Output, RadiationDEM)
    radiationout.save(DEMfinal)
    return arcpy.GetMessages()

# <markdowncell>

# 3. Calculate Boundaries - Factor Height and Factor Shade

# <codecell>

def CalcBoundaries (Simple_CQ,locationtemp1, locationtemp2, DataFactorsCentroids, DataFactorsBoundaries):
    #local variables
    NearTable = locationtemp1+'\\'+'NearTable.dbf'
    CQLines = locationtemp2+'\\'+'\CQLines'
    CQVertices = locationtemp2+'\\'+'CQVertices'
    CQSegments = locationtemp2+'\\'+'CQSegment'
    CQSegments_centroid = locationtemp2+'\\'+'CQSegmentCentro'
    centroidsTable_name = 'CentroidCQdata.dbf'
    centroidsTable = locationtemp1+'\\'+centroidsTable_name
    Overlaptable = locationtemp1+'\\'+'overlapingTable.csv'
    
    #Create points in the centroid of segment line and table with near features: 
    # indentifying for each segment of line of building A the segment of line of building B in common.  
    arcpy.FeatureToLine_management(Simple_CQ,CQLines)
    arcpy.FeatureVerticesToPoints_management(Simple_CQ,CQVertices,'ALL')
    arcpy.SplitLineAtPoint_management(CQLines,CQVertices,CQSegments,'2 METERS')
    arcpy.FeatureVerticesToPoints_management(CQSegments,CQSegments_centroid,'MID')
    arcpy.GenerateNearTable_analysis(CQSegments_centroid,CQSegments_centroid,NearTable,"1 Meters","NO_LOCATION","NO_ANGLE","CLOSEST","0")
    
    #Import the table with NearMatches
    NearMatches = dbf2df(NearTable)
    
    # Import the table with attributes of the centroids of the Segments
    arcpy.TableToTable_conversion(CQSegments_centroid, locationtemp1, centroidsTable_name)
    DataCentroids = dbf2df(centroidsTable, cols={'Name','height','ORIG_FID'})
    
    # CreateJoin to Assign a Factor to every Centroid of the lines,
    FirstJoin = pd.merge(NearMatches,DataCentroids,left_on='IN_FID', right_on='ORIG_FID')
    SecondaryJoin = pd.merge(FirstJoin,DataCentroids,left_on='NEAR_FID', right_on='ORIG_FID')
    
    # delete matches within the same polygon Name (it can happen that lines are too close one to the other)
    # also delete matches with a distance of more than 20 cm making room for mistakes during the simplicfication of buildings but avoiding deleten boundaries 
    rows = SecondaryJoin.IN_FID.count()
    for row in range(rows):
        if SecondaryJoin.loc[row,'Name_x'] == SecondaryJoin.loc[row,'Name_y'] or SecondaryJoin.loc[row,'NEAR_DIST'] > 0.2:
           SecondaryJoin = SecondaryJoin.drop(row)
    SecondaryJoin.reset_index(inplace=True)
    
    #FactorShade = 0 if the line exist in a building totally covered by another one, and Freeheight is equal to the height of the line 
    # that is not obstructed by the other building
    rows = SecondaryJoin.IN_FID.count()
    SecondaryJoin['FactorShade']=0
    SecondaryJoin['Freeheight']=0
    for row in range(rows):
        if SecondaryJoin.loc[row,'height_x'] <= SecondaryJoin.loc[row,'height_y']:
            SecondaryJoin.loc[row,'FactorShade'] = 0
            SecondaryJoin.loc[row,'Freeheight'] = 0
        elif SecondaryJoin.loc[row,'height_x'] > SecondaryJoin.loc[row,'height_y'] and SecondaryJoin.loc[row,'height_x']-1 <= SecondaryJoin.loc[row,'height_y']:
            SecondaryJoin.loc[row,'FactorShade'] = 0
        else:
            SecondaryJoin.loc[row,'FactorShade'] = 1
            SecondaryJoin.loc[row,'Freeheight'] = abs(SecondaryJoin.loc[row,'height_y']- SecondaryJoin.loc[row,'height_x'])
        
    #Create and export Secondary Join with results, it will be Useful for the function CalcObservers
    SecondaryJoin.to_csv(DataFactorsBoundaries,index=False)
    
    #Update table Datacentroids with the Fields Freeheight and Factor Shade. for those buildings without
    #shading boundaries these factors are equal to 1 and the field 'height' respectively.
    DataCentroids['FactorShade'] = 1
    DataCentroids['Freeheight'] = DataCentroids['height']
    Results = DataCentroids.merge(SecondaryJoin, left_on='ORIG_FID', right_on='ORIG_FID_x', how='outer')
    Results.FactorShade_y.fillna(Results['FactorShade_x'],inplace=True)
    Results.Freeheight_y.fillna(Results['Freeheight_x'],inplace=True)
    Results.rename(columns={'FactorShade_y':'FactorShade','Freeheight_y':'Freeheight'},inplace=True)
    FinalDataCentroids = pd.DataFrame(Results,columns={'ORIG_FID','height','FactorShade','Freeheight'})
            
    FinalDataCentroids.to_csv(DataFactorsCentroids,index=False)
    return arcpy.GetMessages()

# <markdowncell>

# 4. Calculate observation points

# <codecell>

def CalcObservers(Simple_CQ,Observers, DataFactorsBoundaries, locationtemporal2, environment):

    #local variables
    Buffer_CQ = locationtemporal2+'\\'+'BufferCQ'
    temporal_lines = locationtemporal2+'\\'+'lines'
    Points = locationtemporal2+'\\'+'Points'
    AggregatedBuffer = locationtemporal2+'\\'+'BufferAggregated'
    temporal_lines3 = locationtemporal2+'\\'+'lines3'
    Points3 = locationtemporal2+'\\'+'Points3'
    Points3Updated = locationtemporal2+'\\'+'Points3Updated'
    EraseObservers = locationtemporal2+'\\'+'eraseobservers'
    Observers0 = locationtemporal2+'\\'+'observers0'  
    NonoverlappingBuildings = locationtemporal2+'\\'+'Non_overlap'
    templines = locationtemporal2+'\\'+'templines'
    templines2 = locationtemporal2+'\\'+'templines2'
    Buffer_CQ0 = locationtemporal2+'\\'+'Buffer_CQ0'
    Buffer_CQ = locationtemporal2+'\\'+'Buffer_CQ'
    Buffer_CQ1 = locationtemporal2+'\\'+'Buffer_CQ1'
    Simple_CQcopy = locationtemporal2+'\\'+'Simple_CQcopy'
    #First increase the boundaries in 2m of each surface in the community to 
    #analyze- this will avoid that the observers overlap the buildings and Simplify 
    #the community vertices to only create 1 point per surface
    
    arcpy.CopyFeatures_management(Simple_CQ,Simple_CQcopy)
    #Make Square-like buffers
    arcpy.PolygonToLine_management(Simple_CQcopy,templines,"IGNORE_NEIGHBORS")
    arcpy.SplitLine_management(templines,templines2)
    arcpy.Buffer_analysis(templines2,Buffer_CQ0,"0.75 Meters","FULL","FLAT","NONE","#")
    arcpy.Append_management(Simple_CQcopy,Buffer_CQ0,"NO_TEST")
    arcpy.Dissolve_management(Buffer_CQ0,Buffer_CQ1,"Name","#","SINGLE_PART","DISSOLVE_LINES")
    arcpy.SimplifyBuilding_cartography(Buffer_CQ1,Buffer_CQ,simplification_tolerance=8, minimum_area=None)

   #arcpy.Buffer_analysis(Simple_CQ,Buffer_CQ,buffer_distance_or_field=1, line_end_type='FLAT') # buffer with a flat finishing
   #arcpy.Generalize_edit(Buffer_CQ,"2 METERS")
    
    #Transform all polygons of the simplified areas to observation points
    arcpy.SplitLine_management(Buffer_CQ,temporal_lines)
    arcpy.FeatureVerticesToPoints_management(temporal_lines,Points,'MID') # Second the transformation of Lines to a mid point
    
    #Join all the polygons to get extra vertices, make lines and then get points. 
    #these points should be added to the original observation points
    arcpy.AggregatePolygons_cartography(Buffer_CQ,AggregatedBuffer,"0.5 Meters","0 SquareMeters","0 SquareMeters","ORTHOGONAL") # agregate polygons
    arcpy.SplitLine_management(AggregatedBuffer,temporal_lines3) #make lines
    arcpy.FeatureVerticesToPoints_management(temporal_lines3,Points3,'MID')# create extra points
    
    # add information to Points3 about their buildings
    arcpy.SpatialJoin_analysis(Points3,Buffer_CQ,Points3Updated,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST",search_radius="5 METERS")
    arcpy.Erase_analysis(Points3Updated,Points,EraseObservers,"2 Meters")# erase overlaping points
    arcpy.Merge_management([Points,EraseObservers],Observers0)# erase overlaping points
    
    #  Eliminate Observation points above roofs of the highest surfaces(a trick to make the 
    #Import Overlaptable from function CalcBoundaries containing the data about buildings overlaping, eliminate duplicades, chose only those ones no overlaped and reindex
    DataNear = pd.read_csv(DataFactorsBoundaries)
    CleanDataNear = DataNear[DataNear['FactorShade'] == 1]
    CleanDataNear.drop_duplicates(cols='Name_x',inplace=True)
    CleanDataNear.reset_index(inplace=True)
    rows = CleanDataNear.Name_x.count()
    for row in range(rows):
        Field = "Name" # select field where the name exists to iterate
        Value = CleanDataNear.loc[row,'Name_x'] # set the value or name of the City quarter
        Where_clausule =  ''''''+'"'+Field+'"'+"="+"\'"+str(Value)+"\'"+'''''' # strange writing to introduce in ArcGIS
        if row == 0:
            arcpy.MakeFeatureLayer_management(Simple_CQ, 'Simple_lyr')
            arcpy.SelectLayerByAttribute_management('Simple_lyr',"NEW_SELECTION",Where_clausule)
        else:
            arcpy.SelectLayerByAttribute_management('Simple_lyr',"ADD_TO_SELECTION",Where_clausule)
            
        arcpy.CopyFeatures_management('simple_lyr', NonoverlappingBuildings)
        
    arcpy.ErasePoint_edit(Observers0,NonoverlappingBuildings,"INSIDE")
    arcpy.CopyFeatures_management(Observers0,Observers)#copy features to reset the OBJECTID
    with arcpy.da.UpdateCursor(Observers,["OBJECTID","ORIG_FID"]) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
    return arcpy.GetMessages()

# <markdowncell>

# 5. Radiation results to surfaces

# <codecell>

def CalcRadiationSurfaces(Observers, Radiationyearfinal, DataFactorsCentroids, DataradiationLocation,  locationtemp1, locationtemp2):
    # local variables
    CQSegments_centroid = locationtemp2+'\\'+'CQSegmentCentro'
    Outjoin = locationtemp2+'\\'+'Join'
    CQSegments = locationtemp2+'\\'+'CQSegment'
    OutTable = 'CentroidsIDobserv.dbf'
    # Create Join of features Observers and CQ_sementscentroids to 
    # assign Names and IDS of observers (field TARGET_FID) to the centroids of the lines of the buildings,
    # then create a table to import as a Dataframe
    arcpy.SpatialJoin_analysis(CQSegments_centroid,Observers,Outjoin,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST",search_radius="10 METERS")
    arcpy.JoinField_management(Outjoin,'OBJECTID',CQSegments, 'OBJECTID') # add the lenghts of the Lines to the File
    arcpy.TableToTable_conversion(Outjoin, locationtemp1, OutTable)
    
    #ORIG_FID represents the points in the segments of the simplified shape of the building
    #ORIG_FID_1 is the observers ID
    Centroids_ID_observers = dbf2df(locationtemp1+'\\'+OutTable, cols={'Name','height','ORIG_FID','ORIG_FID_1','Shape_Leng'})
    Centroids_ID_observers.rename(columns={'ORIG_FID_1':'ID'},inplace=True)
    
    #Create a Join of the Centroid_ID_observers and Datacentroids in the Second Chapter to get values of surfaces Shaded.
    Datacentroids = pd.read_csv(DataFactorsCentroids)
    DataCentroidsFull = pd.merge(Centroids_ID_observers,Datacentroids,left_on='ORIG_FID',right_on='ORIG_FID')
    
    #Read again the radiation table and merge values with the Centroid_ID_observers under the field ID in Radiationtable and 'ORIG_ID' in Centroids...
    Radiationtable = pd.read_csv(DataradiationLocation,index_col='Unnamed: 0')
    DataRadiation = pd.merge(DataCentroidsFull,Radiationtable, left_on='ID',right_on='ID')
    
    DataRadiation.to_csv(Radiationyearfinal,index=False)
    return arcpy.GetMessages()

# <markdowncell>

# ###ANALYTICAL MODEL

# <markdowncell>

# 1. Estimation of thermal properties and geom of buildings

# <codecell>

def CalcProperties(CQ, CQproperties, RadiationFile,locationtemp1):
    import numpy as np
    #Local Variables
    OutTable = 'CQshape3.dbf'
    
    # Set of estimated constants
    Z = 3 # height of basement for every building in m
    Bf = 0.7 # It calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of  SIA 380/1
    
    # Set of constants according to EN 13790
    his = 3.45 #heat transfer coefficient between air and the surfacein W/(m2K)
    hms = 9.1 # Heat transfer coeddicient between nodes m and s in W/m2K 
    # Set of estimated constants

    #Import RadiationFile and Properties of the shapefiles
    rf = pd.read_csv(RadiationFile)
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    CQShape_properties = dbf2df(locationtemp1+'\\'+OutTable)
    
    #Areas above ground #get the area of each wall in the buildings
    rf['Awall_all'] = rf['Shape_Leng']*rf['Freeheight']*rf['FactorShade'] 
    Awalls0 = pd.pivot_table(rf,rows='Name',values='Awall_all',aggfunc=np.sum); Awalls = pd.DataFrame(Awalls0) #get the area of walls in the whole buildings
    
    Areas = pd.merge(Awalls,CQproperties, left_index=True,right_on='Name')
    Areas['Aw'] = Areas['Awall_all']*Areas['fwindow']*Areas['PFloor'] # Finally get the Area of windows 
    Areas['Aop_sup'] = Areas['Awall_all']*Areas['PFloor']-Areas['Aw'] #....and Opaque areas PFloor represents a factor according to the amount of floors heated
    
    #Areas bellow ground
    AllProperties = pd.merge(Areas,CQShape_properties,on='Name')# Join both properties files (Shape and areas)
    AllProperties['Aop_bel'] = Z*AllProperties['Shape_Leng']+AllProperties['Shape_Area']   # Opague areas in m2 below ground including floor
    AllProperties['Atot'] = AllProperties['Aop_sup']+AllProperties['Shape_Area']+AllProperties['Aop_bel']+AllProperties['Shape_Area']*AllProperties['Floors_y'] # Total area of the building envelope m2, it is considered the roof to be flat
    AllProperties['Af'] = AllProperties['Shape_Area']*AllProperties['Floors_y']*AllProperties['Hs_y']*(1-AllProperties.DEPO)*(1-AllProperties.CR)*(1-AllProperties.SR) # conditioned area - áreas not heated
    AllProperties['Aef'] = AllProperties['Shape_Area']*AllProperties['Floors_y']*AllProperties['Es']# conditioned area only those for electricity
    AllProperties['Am'] = AllProperties.Construction.apply(lambda x:AmFunction(x))*AllProperties['Af'] # Effective mass area in m2

    #Steady-state Thermal transmittance coefficients and Internal heat Capacity
    AllProperties ['Htr_w'] = AllProperties['Aw']*AllProperties['Uwindow']  # Thermal transmission coefficient for windows and glazing. in W/K
    AllProperties ['HD'] = AllProperties['Aop_sup']*AllProperties['Uwall']+AllProperties['Shape_Area']*AllProperties['Uroof']  # Direct Thermal transmission coefficient to the external environment in W/K
    AllProperties ['Hg'] = Bf*AllProperties ['Aop_bel']*AllProperties['Ubasement'] # stady-state Thermal transmission coeffcient to the ground. in W/K
    AllProperties ['Htr_op'] = AllProperties ['Hg']+ AllProperties ['HD']
    AllProperties ['Htr_ms'] = hms*AllProperties ['Am'] # Coupling conduntance 1 in W/K
    AllProperties ['Htr_em'] = 1/(1/AllProperties['Htr_op']-1/ AllProperties['Htr_ms']) # Coupling conduntance 2 in W/K 
    AllProperties ['Htr_is'] = his*AllProperties ['Atot']
    AllProperties['Cm'] = AllProperties.Construction.apply(lambda x:CmFunction(x))*AllProperties['Af'] # Internal heat capacity in J/K
    
    # Year Category of building
    AllProperties['YearCat'] = AllProperties.apply(lambda x: YearCategoryFunction(x['Year_y'], x['Retrofit']), axis=1)
    
    AllProperties.rename(columns={'Hs_y':'Hs','Floors_y':'Floors','PFloor_y':'PFloor','Year_y':'Year','fwindow_y':'fwindow'},inplace=True)
    return AllProperties

# <markdowncell>

# 2. Calculation in areas exposed - elimination of shared boundaries (adiabatic)

# <codecell>

def CalcIncidentRadiation(AllProperties, Radiationyearfinal):

    #Import Radiation table and compute the Irradiation in W in every building's surface
    Radiation_Shading2 = pd.read_csv(Radiationyearfinal)
    Columns = 8761
    Radiation_Shading2['AreaExposed'] = Radiation_Shading2['Shape_Leng']*Radiation_Shading2['FactorShade']*Radiation_Shading2['Freeheight']
    for Column in range(1, Columns):
         #transform all the points of solar radiation into Wh
        Radiation_Shading2['T'+str(Column)] = Radiation_Shading2['T'+str(Column)]*Radiation_Shading2['AreaExposed']
        
    #Do pivot table to sum up the irradiation in every surface to the building 
    #and merge the result with the table allProperties
    PivotTable3 = pd.pivot_table(Radiation_Shading2,rows='Name',margins='Add all row')
    RadiationLoad = pd.DataFrame(PivotTable3)
    Solar = AllProperties.merge(RadiationLoad, left_on='Name',right_index=True)
    
    columns_names = list(range(8760))
    for time in range(len(columns_names)):
        columns_names[time] = 'T'+str(time+1)
        
    Final = Solar[columns_names]

    return Final # total solar radiation in areas exposed to radiation in Watts

# <markdowncell>

# 1.1 Sub-functions of  Thermal mass

# <codecell>

def CmFunction (x): 
    if x == 'Medium':
        return 165000
    elif x == 'Heavy':
        return 300000
    elif x == 'Light':
        return 110000
    else:
        return 165000

# <codecell>

def AmFunction (x): 
    if x == 'Medium':
        return 2.5
    elif x == 'Heavy':
        return 3.2
    elif x == 'Light':
        return 2.5
    else:
        return 2.5

# <markdowncell>

# 1.2. Sub- Function Hourly thermal transmission coefficients

# <codecell>

def calc_Htr(Hve, Htr_is, Htr_ms, Htr_w):
    Htr_1 = 1/(1/Hve+1/Htr_is)
    Htr_2 = Htr_1+Htr_w
    Htr_3 = 1/(1/Htr_2+1/Htr_ms)
    return Htr_1,Htr_2,Htr_3

# <markdowncell>

# 2. Main Calculation of thermal and Electrical loads - No processes

# <codecell>

def calc_Y(year, Retrofit):
    if year >= 1995 or Retrofit > 0:
        Y = [0.2,0.3,0.3]
    elif 1985 <= year < 1995 and Retrofit == 0:
        Y = [0.3,0.4,0.4]
    else:
        Y = [0.4,0.4,0.4] 
    return Y

# <codecell>

def calc_fill_local_Text(T_ext,tH,tC, tmax):
    if tH == 0:
        tH = T_ext
    if tC == 0:
        tC = tmax+1
    return tH, tC

# <codecell>

# Calculate schedule variables
def calc_mixed_schedule(Profiles, Profiles_names, AllProperties, te):  
    
    def calc_average(last, current, share_of_use):
         return last + current * share_of_use
    
    #initialize variables
    ta_hs_set = np.zeros(8760)
    ta_cs_set = np.zeros(8760)
    people = np.zeros(8760)
    ve = np.zeros(8760)
    q_int = np.zeros(8760)
    w_int = np.zeros(8760)
    Eal_nove = np.zeros(8760)
    Eal_ve = np.zeros(8760)
    mww = np.zeros(8760)
    mw = np.zeros(8760)
    
    for num in range(len(Profiles_names)):
        current_share_of_use = AllProperties[Profiles_names[num]]
        ta_hs_set = np.vectorize(calc_average)(ta_hs_set,np.array(Profiles[num].tintH_set),current_share_of_use)
        ta_cs_set = np.vectorize(calc_average)(ta_cs_set,np.array(Profiles[num].tintC_set),current_share_of_use)
        people = np.vectorize(calc_average)(people,np.array(Profiles[num].People),current_share_of_use)
        ve = np.vectorize(calc_average)(ve,np.array(Profiles[num].Ve),current_share_of_use)
        q_int = np.vectorize(calc_average)(q_int,np.array(Profiles[num].I_int),current_share_of_use)
        w_int = np.vectorize(calc_average)(w_int,np.array(Profiles[num].w_int),current_share_of_use)
        Eal_nove = np.vectorize(calc_average)(Eal_nove,np.array(Profiles[num].Ealf_nove),current_share_of_use)
        Eal_ve = np.vectorize(calc_average)(Eal_ve,np.array(Profiles[num].Ealf_ve),current_share_of_use)
        mww = np.vectorize(calc_average)(mww,np.array(Profiles[num].Mww),current_share_of_use)
        mw = np.vectorize(calc_average)(mw,np.array(Profiles[num].Mw),current_share_of_use)
        
    return ta_hs_set,ta_cs_set,people,ve,q_int,Eal_nove,Eal_ve,mww,mw, w_int

# <codecell>

def CalcThermalLoads(k, prop, Solar, locationFinal, Profiles, Profiles_names, T_ext,Seasonhours,T_ext_max,RH_ext, T_ext_min,g_gl,
                     F_f,Bf,D,hf,Pwater,PaCa,Cpw, Flowtap, deltaP_l, fsr,nrec_N,C1,Vmax,Pair,Cpv,Cpa,lvapor,servers ,coolingroom):                 
    Af = prop.Af
    Aef = prop.Aef
    Name = prop.Name
    sys_e_heating = prop.Emission_heating
    sys_e_cooling = prop.Emission_cooling
    if Af > 0:
        #extract properties of building
        # Geometry
        nf = prop.Floors
        nfp = prop.PFloor
        height = prop.height
        Lw = prop.MBG_Width
        Ll = prop.MBG_Length
        Am = prop.Am
        Aw = prop.Aw
        Awall_all = prop.Awall_all
        Atot = Af*4.5
        footprint = prop.Shape_Area
        # construction,renovation etc years of the building
        Year = prop.Year
        Yearcat = prop.YearCat
        Retrofit = prop.Retrofit # year building  renovated or not
        # shading position and types
        Sh_pos = prop.Shading_Po
        Sh_typ = prop.Shading_Ty
        # thermal mass properties
        Cm = prop.Cm

        Y = calc_Y(Year,Retrofit) # linear trasmissivity coefficeitn of piping W/(m.K)
        # nominal temperatures
        Ths_sup_0 = prop.tshs0
        Ths_re_0 = prop.trhs0
        Tcs_sup_0 = prop.tscs0
        Tcs_re_0 = prop.trcs0
        Tww_sup_0 = prop.tsww0

        #3Identification of equivalent lenghts
        fforma = Calc_form(Lw,Ll,footprint) # factor forma comparison real surface and rectangular
        Lv = (2*Ll+0.0325*Ll*Lw+6)*fforma # lenght vertical lines
        Lcww_dis = 2*(Ll+2.5+nf*nfp*hf)*fforma # lenghth hotwater piping circulation circuit
        Lsww_dis = 0.038*Ll*Lw*nf*nfp*hf*fforma # length hotwater piping distribution circuit
        Lvww_c = (2*Ll+0.0125*Ll*Lw)*fforma # lenghth piping heating system circulation circuit
        Lvww_dis = (Ll+0.0625*Ll*Lw)*fforma # lenghth piping heating system distribution circuit

        #calculate schedule and varaibles
        ta_hs_set,ta_cs_set,people,ve,q_int,Eal_nove,Eal_ve,vww,vw,X_int = calc_mixed_schedule(Profiles, Profiles_names,prop, T_ext)
        #2. Transmission coefficients in W/K
        qv_req  = (ve*Af)/3600 # in m3/s
        Hve = (PaCa*qv_req)
        Htr_is = prop.Htr_is
        Htr_ms = prop.Htr_ms
        Htr_w = prop.Htr_w
        Htr_em = prop.Htr_em
        Htr_1,Htr_2, Htr_3 = np.vectorize(calc_Htr)(Hve, Htr_is, Htr_ms, Htr_w)
        
        #3. Heat flows in W
        #. Solar heat gains
        Rf_sh = Calc_Rf_sh(Sh_pos,Sh_typ)  
        solar_specific = np.array(Solar)/Awall_all
        Asol = np.vectorize(calc_gl)(solar_specific,g_gl,Rf_sh)*(1-F_f)*Aw # Calculation of solar efective area per hour in m2
        I_sol = Asol*solar_specific

        #  Sensible heat gains
        I_int_sen = q_int*Af # Internal heat gains

        #  Calculate latent internal loads in terms of added moisture:
        if sys_e_heating == 3 or sys_e_cooling == 3:
            w_int = X_int/(1000*3600)*Af #in kg/kg.s
        else:
            w_int = 0

        #  Components of Sensible heat gains
        I_ia = 0.5*I_int_sen
        I_m = (Am/Atot)*(I_ia+I_sol)
        I_st = (1-(Am/Atot)-(Htr_w/(9.1*Atot)))*(I_ia+I_sol)
        
        #4. Heating and cooling loads
        # factors of Losses due to emission of systems vector hot or cold water for heating and cooling
        tHset_corr, tCset_corr = calc_Qem_ls(sys_e_heating,sys_e_cooling)
        
        # the installed capacities are assumed to be gigantic, it is assumed that the building can  generate heat and cold at anytime
        IC_max = -500*Af
        IH_max = 500*Af 
        # define empty arrrays
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
        # we give a seed high enough to avoid doing a iteration for 2 years.
        if sys_e_heating == 2: #TABS
            tm_t0 = tm_t1 = 22
        else:
            tm_t0 = tm_t1 = 16

        # definition of first temperature to start calculation of air conditioning system
        t5_1 = 21
        # we define limtis of season =
        limit_inf_season = Seasonhours[0]+1
        limit_sup_season = Seasonhours[1]
        for k in range(8760):
            #if it is in the season
            if  limit_inf_season <= k < limit_sup_season:
                #take advantage of this loop to fill the values of cold water
                Flag_season = True
                Tww_re[k] = 14
            else:
                #take advantage of this loop to fill the values of cold water
                Tww_re[k] = 10
                Flag_season = False
            # Calc of Qhs/Qcs - net/useful heating and cooling deamnd in W
            Losses = 0
            Tm[k], Ta[k], Qhs_sen[k], Qcs_sen[k] = calc_TL(sys_e_heating,sys_e_cooling, T_ext_min, T_ext_max, tm_t0,
                                                           T_ext[k], ta_hs_set[k], ta_cs_set[k], Htr_em, Htr_ms, Htr_is, Htr_1[k],
                                                           Htr_2[k], Htr_3[k], I_st[k], Hve[k], Htr_w, I_ia[k], I_m[k], Cm, Af, Losses,
                                                           tHset_corr,tCset_corr,IC_max,IH_max, Flag_season)
            tm_t0 = Tm[k]

            # Calc of Qhs_em_ls/Qcs_em_ls - losses due to emission systems in W
            Losses = 1
            Results1 = calc_TL(sys_e_heating,sys_e_cooling, T_ext_min, T_ext_max, tm_t1, T_ext[k], ta_hs_set[k], ta_cs_set[k],
                               Htr_em, Htr_ms, Htr_is, Htr_1[k],Htr_2[k], Htr_3[k], I_st[k], Hve[k], Htr_w, I_ia[k], I_m[k],
                               Cm, Af, Losses, tHset_corr,tCset_corr,IC_max,IH_max, Flag_season)
            
            

            Qhs_em_ls[k] = Results1[2] - Qhs_sen[k]
            Qcs_em_ls[k] = Results1[3] - Qcs_sen[k]
            if Qcs_em_ls[k] > 0:
                Qcs_em_ls[k] = 0
            if Qhs_em_ls[k] < 0:
                Qhs_em_ls[k] = 0

            tm_t1 = Results1[0]

            # Calculate new sensible loads with HVAC systems incl. recovery.
            if sys_e_heating == 1 or sys_e_heating == 2:
                Qhs_sen_incl_em_ls[k] = Results1[2]
            if sys_e_cooling == 0:    
                Qcs_sen_incl_em_ls[k] = 0
            if sys_e_heating == 3 or sys_e_cooling == 3:
                QHC_sen[k] = Qhs_sen[k] + Qcs_sen[k] + Qhs_em_ls[k] + Qcs_em_ls[k]
                temporal_Qhs, temporal_Qcs, Qhs_lat[k], Qcs_lat[k], Ehs_lat_aux[k], ma_sup_hs[k], ma_sup_cs[k], Ta_sup_hs[k], Ta_sup_cs[k], Ta_re_hs[k], Ta_re_cs[k], w_re[k], w_sup[k], t5[k] =  calc_HVAC(sys_e_heating, sys_e_cooling, people[k],RH_ext[k], T_ext[k],Ta[k], qv_req[k],Flag_season, QHC_sen[k],t5_1, lvapor, w_int[k],nrec_N,C1, Vmax ,Pair, Cpv,Cpa)
                t5_1 = t5[k]
                if sys_e_heating == 3:
                    Qhs_sen_incl_em_ls[k] = temporal_Qhs
                if sys_e_cooling == 3:
                    Qcs_sen_incl_em_ls[k] = temporal_Qcs
        
        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        # erase possible disruptions from dehumidification days
        #Qhs_sen_incl_em_ls[Qhs_sen_incl_em_ls < 0] = 0
        #Qcs_sen_incl_em_ls[Qcs_sen_incl_em_ls > 0] = 0
        Qhs_sen_incl_em_ls_0 = Qhs_sen_incl_em_ls.max()
        Qcs_sen_incl_em_ls_0 = Qcs_sen_incl_em_ls.min()
        Qhs_d_ls, Qcs_d_ls =  np.vectorize(calc_Qdis_ls)(Ta, T_ext, Qhs_sen_incl_em_ls, Qcs_sen_incl_em_ls, Ths_sup_0, Ths_re_0, Tcs_sup_0, Tcs_re_0, Qhs_sen_incl_em_ls_0, Qcs_sen_incl_em_ls_0 ,
                                                         D, Y[0], sys_e_heating, sys_e_cooling, Bf, Lv)         
                
        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        Qhsf = Qhs_sen_incl_em_ls + Qhs_d_ls   # no latent is considered because it is already added as electricity from the adiabatic system.
        Qcsf = Qcs_sen_incl_em_ls + Qcs_d_ls + Qcs_lat
        
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
        
        if sys_e_heating == 1:
            nh = 0.3
            Ths_sup, Ths_re, mcphs = np.vectorize(calc_RAD)(Qhsf,Ta, Qhsf_0, Ta_0, Ths_sup_0, Ths_re_0,nh)

        if sys_e_heating == 2:
            nh = 0.2
            Ths_sup, Ths_re, mcphs = np.vectorize(calc_TABSH)(Qhsf,Ta, Qhsf_0, Ta_0, Ths_sup_0, Ths_re_0,nh)

        if sys_e_heating == 3: 
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
                                                                Cpa, LMRT0, UA0, mCw0, Qhsf)
        if sys_e_cooling == 3: 

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
                                                               tsc0, trc0, w_re, w_sup, ma_sup_0, ma_sup_cs, Cpa,
                                                               LMRT0, UA0, mCw0, Qcsf)  
        #1. Calculate water consumption
        Vww = vww*Af/1000 ## consumption of hot water in m3/hour
        Vw = vw*Af/1000 ## consumption of fresh water in m3/h 
        Mww = Vww*Pwater/3600 # in kg/s
        Mw = Vw*Pwater/3600 # in kg/s
        #2. Calculate water hot dem
        Qww = Mww*Cpw*(Tww_sup_0-Tww_re)*1000 # in W
        #3. losses distribution of domestic hot water recoverable and not recoverable
        Qww_0 = Qww.max()
        Vol_ls = Lsww_dis*(D/1000)**(2/4)*scipy.pi
        Qww_ls_r  = np.vectorize(calc_Qww_ls_r)(Ta, Qww, Lsww_dis, Lcww_dis, Y[1], Qww_0, Vol_ls, Flowtap, Tww_sup_0, Cpw , Pwater)
        Qww_ls_nr  = np.vectorize(calc_Qww_ls_nr)(Ta, Qww, Lvww_dis, Lvww_c, Y[0], Qww_0, Vol_ls, Flowtap, Tww_sup_0, Cpw , Pwater, Bf, T_ext)
    
        
        # Calc requirements of generation systems for hot water - assume losses of 10% due to local storage
        Qwwf = (Qww+Qww_ls_r+Qww_ls_nr)/0.9
        Qwwf_0 = Qwwf.max()    
        
        # clac auxiliary loads of pumping systems
        Eaux_cs = np.zeros(8760)
        Eaux_ve = np.zeros(8760)
        Eaux_fw = np.zeros(8760)
        Eaux_hs = np.zeros(8760)
        Imax = 2*(Ll+Lw/2+hf+(nf*nfp)+10)*fforma
        deltaP_des = Imax*deltaP_l*(1+fsr)
        if Year >= 2000:
            b =1
        else:
            b =1.2
        Eaux_ww = np.vectorize(calc_Eaux_ww)(Qwwf,Qwwf_0,Imax,deltaP_des,b,Mww) 
        if sys_e_heating > 0:
            Eaux_hs = np.vectorize(calc_Eaux_hs_dis)(Qhsf,Qhsf_0,Imax,deltaP_des,b,Ths_sup,Ths_re,Cpw)
        if sys_e_cooling > 0:
            Eaux_cs  = np.vectorize(calc_Eaux_cs_dis)(Qcsf,Qcsf_0,Imax,deltaP_des,b,Tcs_sup,Tcs_re,Cpw)
        if nf > 5: #up to 5th floor no pumping needs
            Eaux_fw = calc_Eaux_fw(Vw,Pwater,nf,hf)
        if sys_e_heating == 3 or sys_e_cooling ==3:
            Eaux_ve = np.vectorize(calc_Eaux_ve)(Qhsf,Qcsf,Eal_ve,sys_e_heating,sys_e_cooling, Af)
            
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
        mcphs =  mcpcs = 0  
        #arrays
        Occupancy = Eauxf = Waterconsumption = np.zeros(8760)
        Qwwf = Qww = Qhs_sen = Qhsf = Qcs_sen = Qcsf = np.zeros(8760)
        Ths_sup = Ths_re = Tcs_re = Tcs_sup = mcphs = mcpcs = Tww_re = np.zeros(8760) # in C 
       
    if Aef > 0:
        # calc appliance and lighting loads
        Ealf = Eal_nove*Aef
        Ealf_0 = Ealf.max()

        # compute totals electrical loads in MWh
        Ealf_tot = Ealf.sum()/1000000
        Eauxf_tot = Eauxf.sum()/1000000
        Ef = Ealf_tot + Eauxf_tot
    else:
        Ealf_tot = Ef = Eauxf_tot =  Ealf_0 = 0 
        Ealf = np.zeros(8760)
        
    # compute totals heating loads loads in MW
    if sys_e_heating != 0:
        Qhsf_tot = Qhsf.sum()/1000000
        Qhs_tot = Qhs_sen.sum()/1000000
        Qwwf_tot = Qwwf.sum()/1000000
        Qww_tot = Qww.sum()/1000000
        Qhf = Qhsf_tot + Qwwf_tot
    else:
        Qhsf_tot = Qhs_tot = Qwwf_tot  = Qww_tot = Qhf = 0

    # compute totals cooling loads in MW
    if sys_e_cooling != 0:
        Qcs_tot = -Qcs_sen.sum()/1000000 
        Qcf = -Qcsf.sum()/1000000
    else:
        Qcs_tot = Qcf = 0
        
    #print series all in kW, mcp in kW/h, cooling loads shown as positive, water consumption m3/h, temperature in Degrees celcious
    DATE = pd.date_range('1/1/2010', periods=8760, freq='H') 
    pd.DataFrame({'DATE':DATE, 'Name':Name,'Ealf':Ealf/1000,'Eauxf':Eauxf/1000,'Qwwf':Qwwf/1000,'Qww':Qww/1000,'Qhs':Qhs_sen/1000,
                  'Qhsf':Qhsf/1000,'Qcs':-Qcs_sen/1000,'Qcsf':-Qcsf/1000,'Occupancy':Occupancy,'totwater':Waterconsumption,
                  'tsh':Ths_sup, 'trh':Ths_re, 'mcphs':mcphs,'tsc':Tcs_sup, 'trc':Tcs_re, 'mcpcs':mcpcs,
                  'tsww':Tww_sup_0,'trww':Tww_re}).to_csv(locationFinal+'\\'+Name+'.csv',index=False, float_format='%.3f')        
    
    
    # print peaks in kW and totals in MWh, temperature peaks in C
    pd.DataFrame({'Name':Name,'Af':Af,'occupants':Occupants,'Qwwf0': Qwwf_0/1000, 'Ealf0': Ealf_0/1000,'Qhsf0':Qhsf_0/1000,
                  'Qcsf0':-Qcsf_0/1000,'Water0':waterpeak,'tsh0':Ths_sup_0, 'trh0':Ths_re_0, 'mcphs0':mcphs.max(),'tsc0':Tcs_sup_0,
                  'trc0':Tcs_re_0, 'mcpcs0':mcpcs.max(),'Qwwf':Qwwf_tot,'Qww':Qww_tot,'Qhsf':Qhsf_tot,'Qhs':Qhs_tot,'Qcsf':Qcf,'Qcs':Qcs_tot,
                  'Ealf':Ealf_tot,'Eauxf':Eauxf_tot,'Qcf':Qcf,'Qhf':Qhf,'Qhf':Qhf, 'tsww0':Tww_sup_0}, index= [0]).to_csv(locationFinal+'\\'+Name+'T.csv',index=False, float_format='%.2f')
    
    return 'Success in  building '+ Name

# <codecell>

def calc_Eaux_ve(Qhsf,Qcsf,ve, SystemH, SystemC, Af):
    if SystemH == 3:
        if Qhsf >0: 
            Eve_aux = ve*Af
        else: 
            Eve_aux = 0
    elif SystemC == 3:
        if Qcsf <0:
            Eve_aux = ve*Af
        else:
            Eve_aux = 0
    else:
        Eve_aux = 0
        
    return Eve_aux

# <codecell>

def calc_Qww_ls_nr(tair,Qww, Lvww_dis, Lvww_c, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater, Bf, te):
    # Calculate tamb in basement according to EN
    tamb = tair - Bf*(tair-te)
    
    # CIRUCLATION LOSSES
    d_circ_ls = (twws-tamb)*Y*(Lvww_c)*(Qww/Qww_0)
    
    # DISTRIBUTION LOSSEs
    d_dis_ls = calc_disls(tamb,Qww,Flowtap,V,twws,Lvww_dis,Pwater,Cpw,Y)
    Qww_d_ls_nr = d_dis_ls + d_circ_ls
    
    return Qww_d_ls_nr 

# <codecell>

def calc_Qww_ls_r(Tair,Qww, lsww_dis, lcww_dis, Y, Qww_0, V, Flowtap, twws, Cpw, Pwater):
    # Calculate tamb in basement according to EN
    tamb = Tair

    # Circulation circuit losses
    circ_ls = (twws-tamb)*Y*lcww_dis*(Qww/Qww_0)

    # Distribtution circuit losses
    dis_ls = calc_disls(tamb,Qww,Flowtap,V,twws,lsww_dis,Pwater,Cpw, Y)

    Qww_d_ls_r = circ_ls + dis_ls
    
    return Qww_d_ls_r

# <codecell>

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

# <codecell>

def calc_Qdis_ls(tair, text, Qhs, Qcs, tsh, trh, tsc,trc, Qhs_max, Qcs_max,D,Y, SystemH,SystemC, Bf, Lv):
    # Calculate tamb in basement according to EN
    tamb = tair - Bf*(tair-text)
    if SystemH != 0 and Qhs > 0:
        Qhs_d_ls = ((tsh + trh)/2-tamb)*(Qhs/Qhs_max)*(Lv*Y) 
    else:
        Qhs_d_ls = 0
    if SystemC != 0 and Qcs < 0:    
        Qcs_d_ls = ((tsc+trc)/2-tamb)*(Qcs/Qcs_max)*(Lv*Y)
    else:
        Qcs_d_ls = 0
        
    return Qhs_d_ls,Qcs_d_ls

# <codecell>

def calc_temperatures(SystemH,SystemC,loads,temps,Occupancy,tsh0,trh0,tsc0,trc0,Af,Floors,Seasonhours,Qc0,Qh0,tairc0,tairh0,cpw,p):
    temps['tsh'] = 0
    temps['trh'] = 0
    temps['tsc'] = 0
    temps['trc'] = 0
    temps['mcphs'] = 0
    temps['mcpcs'] = 0
    Occupancy['qve_eff'] = 0
    if SystemH == 0:
        mwh0 =0  
        
    if SystemC == 0:
        mwc0 =0
    
    if SystemH == 3 and SystemC == 3:
        HVAC = calc_HVAC(SystemH,SystemC,loads.copy(),temps.copy(),Occupancy,tsh0,trh0,Qh0,tsc0,trc0,Qc0,tairc0,tairh0,Af,Seasonhours)
        temps['tsh'] = HVAC[0]['tsh']
        temps['trh'] = HVAC[0]['trh']
        temps['tsc'] = HVAC[0]['tsc']
        temps['trc'] = HVAC[0]['trc']
        Occupancy['qve_eff'] = (HVAC[1]+HVAC[2])/p # in m3/s
        mwh0 = HVAC[3]/1000 #in kW/C#/cpw*3.6 # in kg/h
        mwc0 = HVAC[4]/1000 #in kW/C#/cpw*3.6 # in kg/h
        
    if SystemH == 3 and SystemC != 3:
        HVAC = calc_HVAC(SystemH,SystemC,loads.copy(),temps.copy(),Occupancy,tsh0,trh0,Qh0,tsc0,trc0,Qc0,tairc0,tairh0,Af,Seasonhours)
        temps['tsh'] = HVAC[0]['tsc']
        temps['trh'] = HVAC[0]['trc']
        Occupancy['qve_eff'] = (HVAC[1])/p # in m3/s
        mwh0 = HVAC[3]/1000 #in kW/C#/cpw*3.6 # in kg/h
        mwc0 = HVAC[4]/1000 #in kW/C#/cpw*3.6 # in kg/h
        
    if SystemH == 1:
        n = 0.33
        rad = calc_RAD(loads.copy(),temps.copy(),tsh0,trh0,Qh0,tairh0,n)
        temps['tsh'] = rad[0]['tsh']
        temps['trh'] = rad[0]['trh']
        mwh0 = rad[1]/1000   #/cpw*3.6 # in kg/h
        Occupancy['qve_eff'] = 0
    
    if SystemH == 2:
        fhot = calc_TABSH(loads.copy(),temps.copy(),Qh0,tairh0,tsh0,trh0)
        temps['tsh'] = fhot[0]['tsh']
        temps['trh'] = fhot[0]['trh']  
        mwh0 = fhot[1]/cpw*3.6 # in kg/h
        Occupancy['qve_eff'] = 0   
    
    if SystemC == 4: # it is considered it has a ventilation system to regulate moisture.
        fcool = calc_TABSC(loads.copy(),temps.copy(),Qc0,tairc0,Af)
        temps['tsc'] = fcool[0]['tsc']
        temps['trc'] = fcool[0]['trc']
        mwc0 = fcool[1]/1000 #in kW/C #/cpw*3.6 # in kg/h
        tsc0 = fcool[2]
        trc0 = fcool[4] 
        Occupancy['qve_eff'] = 0
        
    if SystemC == 3 and SystemH != 3:
        HVAC = calc_HVAC(SystemH,SystemC,loads.copy(),temps.copy(),Occupancy,tsh0,trh0,Qh0,tsc0,trc0,Qc0,tairc0,tairh0,Af,Seasonhours)
        temps['tsc'] = HVAC[0]['tsc']
        temps['trc'] = HVAC[0]['trc']
        Occupancy['qve_eff'] = (HVAC[2])/p # in m3/s
        mwc0 = HVAC[4]/1000 #in kW/C#/cpw*3.6 # in kg/h
    
    return  temps['tsh'].copy(),temps['trh'].copy(),temps['tsc'].copy(),temps['trc'].copy(), mwh0, mwc0, tsh0, trh0, tsc0, trc0, Occupancy['qve_eff'].copy()       

# <markdowncell>

# 2.1 Sub-function temperature radiator systems

# <codecell>

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
        min_AT = 10 # Its equal to 10% of the mass flowrate
        trh_min = tair + 5 - 273
        tsh_min = trh_min + min_AT
        AT = (tsh - trh)
        if AT < min_AT:
            if (trh <= trh_min or tsh <= tsh_min):
                trh = trh_min
                tsh = tsh_min
            if  tsh > tsh_min:
                trh = tsh - min_AT
        mCw = Qh/(tsh-trh)/1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return tsh,trh,mCw

# <markdowncell>

# 2.1 Sub-function temperature Floor activated slabs

# <codecell>

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
        result = scipy.optimize.newton(fh, trh0, maxiter=1000,tol=0.1) - 273 
        trh = result.real
        tsh = trh + k2

        # Control system check
        min_AT = 2 # Its equal to 10% of the mass flowrate
        trh_min = tair + 1 - 273
        tsh_min = trh_min + min_AT
        AT = (tsh - trh)
        if AT < min_AT:
            if trh <= trh_min or tsh <= tsh_min:
                trh = trh_min
                tsh = tsh_min
            if tsh > tsh_min:
                trh = tsh - min_AT           
        mCw = Qh/(tsh-trh)/1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return  tsh,trh, mCw

# <markdowncell>

# 2.1 Subfunction temperature and flow TABS Cooling

# <codecell>

def calc_TABSC(tabsc,temps7,Qc0,tair0, Af):
    tair0 = tair0 + 273
    qc0 = Qc0/(Af*0.5)    # 50% of the area available for heat exchange = to size of panels
    tmean_min = dewP = 18
    deltaC_N = 8          # estimated difference of temperature room and panel at nominal conditions
    Sc0 = 2.5             # rise of temperature of supplied water at nominal conditions
    delta_in_des = deltaC_N + Sc0/2
    U0 = qc0/deltaC_N
    
    tsc0 = tair0 - 273 - delta_in_des
    if tsc0 <= dewP:
        tsc0 = dewP - 1
    trc0 = tsc0  + Sc0
    
    tsc0 = tsc0 + 273
    trc0 = trc0 + 273    
    tmean_min = (tsc0+trc0)/2 # for design conditions difference room and cooling medium    
    mCw0 = Qc0/(trc0-tsc0)
    LMRT = (trc0-tsc0)/scipy.log((tsc0-tair0)/(trc0-tair0))
    kC0 = Qc0/(LMRT)
    k1 = 1/mCw0
    def fc(x): 
        Eq = mCw0*k2-kC0*(k2/(scipy.log((x-k2-tair)/(x-tair))))
        return Eq
    rows = 8760
    for row in range(rows):
        if tabsc.loc[row,'Qcsf'] > 0:# in a hotel
            Q = tabsc.loc[row,'Qcsf']
            q = Q/(Af*0.5)
            k2 = Q*k1
            tair = temps7.loc[row,'tair'] + 273
            temps7.loc[row,'trc'] = scipy.optimize.newton(fc, trc0, maxiter=100,tol=0.01) - 273 
            temps7.loc[row,'tsc'] = temps7.loc[row,'trc'] - k2
            
            
    #FLOW CONSIDERING LOSSES Floor slab prototype
    # no significative losses are considered
    tsc0 = (tsc0-273)
    trc0 = (trc0-273)    
    
    return  temps7.copy(), mCw0, mCw0, tsc0, trc0

# <codecell>

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

# <codecell>

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

# <codecell>

def calc_HVAC(SystemH, SystemC, people, RH1, t1, tair, qv_req, Flag, Qsen, t5_1, lvapor, wint, nrec_N,C1, Vmax,Pair, Cpv,Cpa):
    # State No. 5 # indoor air set point
    t5 = tair + 1 # accounding for an increase in temperature
    if Qsen != 0:
        #sensiblea nd latennt loads
        Qsen = Qsen*0.001 # transform in kJ/s
        # Properties of heat recovery and required air incl. Leakage
        qv = qv_req*1.0184     # in m3/s corrected taking into acocunt leakage
        Veff = Vmax*qv/qv_req        #max velocity effective      
        nrec = nrec_N-C1*(Veff-2)   # heat exchanger coefficient

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
        m1 = max(Qsen/((t3-t5)*Cpa),(Pair*qv)) #kg/s # from the point of view of internal loads
        w5 = (wint+w3*m1)/m1

        #room supply moisture content:
        liminf= calc_w(t5,30)
        limsup = calc_w(t5,70)
        if Qsen > 0:  #if heating
            w3, Qhum , Qdhum = calc_w3_heating_case(t5,w2,w5,t3,t5_1,m1,lvapor,liminf,limsup)
        elif Qsen < 0: # if cooling
            w3, Qhum , Qdhum = calc_w3_cooling_case(w2,t3,w5,liminf,limsup,m1,lvapor)

        # State of Supply
        ws = w3
        ts = t3 - 0.5 # minus the expected delta T rise temperature in the ducts

        # the new mass flow rate
        h_t5_w3 =  calc_h(t5,w3)
        h_ts_ws = calc_h(t3,w3)
        m = max(Qsen/((ts-t2)*Cpa),(Pair*qv)) #kg/s # from the point of view of internal loads

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
        Edhum_aux = 0
        ma_hs = ts_hs = tr_hs = ts_cs = tr_cs = ma_cs =  0
    
    return Qhs_sen, Qcs_sen, Qhum, Qdhum, Ehum_aux, ma_hs, ma_cs, ts_hs, ts_cs, tr_hs, tr_cs, w2 , w3, t5

# <codecell>

def calc_Hcoil(Qh, ti, ti_1, Qh0, ti_1_0, ti_0, tsh0, trh0):
    if Qh > 0 and ma >0:
        ti_1_0 = ti_1_0 +273
        ti_0 = ti_0 +273
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        mCw0 = Qh0/(tsh0-trh0)
        LMRT0 = (tsh0-trh0)/scipy.log((tsh0-ti_0)/(trh0-ti_0))
        UA0 = Qh0/LMRT0
        def fh(x): 
            Eq = mCw0*k2-Qh0*(k2/(scipy.log((x+k2-ti)/(x-ti))*LMRT0))
            return Eq

        ti = ti + 273
        ti_1 = ti_1 + 273
        k2 = Qh/mCw0
        trh = scipy.optimize.newton(fh, trh0, maxiter=1000,tol=0.01) - 273
        tsh = trh + k2

        # Control system check
      #  min_AT = 5 # Its equal to 10% of the mass flowrate
      #  trh_min = ti + 2 - 273
      #  tsh_min = trh_min + min_AT
     #   AT = tsh - trh
     #   if AT < min_AT:
      #      if trh <= trh_min or tsh <= tsh_min:
      #          trh = trh_min
      #          tsh = trh_min + min_AT
      #      if tsh > tsh_min:
      #          trh = tsh - min_AT  

        mCw = Qh/(tsh-trh)/1000
    else:
        mCw = 0
        tsh = 0
        trh = 0       
    return tsh, trh, mCw

# <codecell>

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
        result = scipy.optimize.newton(fh, trc0, maxiter=100,tol=0.01) - 273
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

# <codecell>

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
        result = scipy.optimize.newton(fh, trh0, maxiter=100,tol=0.01) - 273 
        trh = result.real
        tsh = trh + k2
        
        # Control system check - close to optimal flow
        min_AT = 10 # Its equal to 10% of the mass flowrate
        tsh_min = tasup + min_AT -273  # to consider coolest source possible
        trh_min = tasup - 273
        if trh < trh_min or tsh < tsh_min:
            trh = trh_min
            tsh = tsh_min
            
        mcphs = Qhsf/(tsh-trh)/1000  
    else:
        tsh = trh =  mcphs =0
    return tsh, trh,  mcphs

# <codecell>

def calc_Ccoil(Qc, ti, ti_1, Qc0, ti_1_0, ti_0, tsc0, trc0):
    Qc = -Qc
    if Qc > 0:
        ti_1_0 = ti_1_0 +273
        ti_0 = ti_0 +273
        tsc0 = tsc0 + 273
        trc0 = trc0 + 273
        mCw0 = Qc0/(trc0-tsc0)
        LMRT0 = (trc0-tsc0)/scipy.log((trc0-ti_0)/(tsc0-ti_0))
        UA0 = Qc0/LMRT0
        def fh(x): 
            Eq = mCw0*k2-UA0*(k2/(scipy.log((x-k2-ti)/(x-ti))))
            return Eq
        
        k2 = Qc/mCw0
        trc = scipy.optimize.newton(fh, tsc0, maxiter=1000,tol=0.01) - 273
        tsc = trc - k2

        # Control system check
        min_AT = 5 # Its equal to 10% of the mass flowrate
        tsc_max = 7 # to consider coolest source possible
        trc_max = 17
        tsc_min = 12
        AT = trc - tsc
        if AT < min_AT:
            if tsc <= tsc_max:
                tsc = tsc_max
                trc = tsc_max + min_AT
            if tsc >= tsc_min:
                tsc = tsc_min
                trc = tsc_min + min_AT
        
        mCw = Qc/(trc-tsc)/1000
    else:
        mCw = 0
        tsc = 0
        trc = 0 
    return tsc, trc, mCw

# <codecell>

def calc_w(t,RH): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    Ps = 610.78*exp(t/(t+238.3)*17.2694)
    Pv = RH/100*Ps
    w = 0.62*Pv/(Pa-Pv)
    return w

# <codecell>

def calc_h(t,w): # enthalpyh of most air in kJ/kg
    if 0 < t < 60:
        h = (1.007*t-0.026)+w*(2501+1.84*t)    
    elif -100 < t <= 0:
        h = (1.005*t)+w*(2501+1.84*t)
   # else:
    #    h = (1.007*t-0.026)+w*(2501+1.84*t) 
    return h

# <codecell>

def calc_t(w,RH): # tempeature in C
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(RH/100*610.78*scipy.exp(x/(x+238.3*17.2694)))-1)-0.62
        return Eq
    result = scipy.optimize.newton(Ps, 19, maxiter=100,tol=0.01)
    t = result.real
    return t

# <codecell>

def calc_RH(w,t): # Moisture content in kg/kg of dry air
    Pa = 100000 #Pa
    def Ps(x): 
        Eq = w*(Pa/(x/100*610.78*scipy.exp(t/(t+238.3*17.2694)))-1)-0.62
        return Eq
    result = scipy.optimize.newton(Ps, 50, maxiter=100,tol=0.01)
    RH = result.real
    return RH

# <codecell>

def Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd,Hve,Htr_2):
    return I_m + Htr_em * te_t + Htr_3*(I_st + Htr_w*te_t + Htr_1*(((I_ia + IHC_nd)/Hve)+ te_t))/Htr_2

# <codecell>

def Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd,Hve,Htr_is):
    tm_t = (tm_t0 *((Cm/3600)-0.5*(Htr_3+ Htr_em))+ Im_tot)/((Cm/3600)+0.5*(Htr_3+Htr_em))
    tm = (tm_t+tm_t0)/2
    ts = (Htr_ms * tm + I_st + Htr_w*te_t + Htr_1*(te_t+(I_ia+IHC_nd)/Hve))/(Htr_ms+Htr_w+Htr_1)
    ta = (Htr_is*ts + Hve*te_t + I_ia + IHC_nd)/(Htr_is+Hve)
    top = 0.31*ta+0.69*ts
    return tm, ts, ta, top

# <markdowncell>

# 2.1. Sub-Function Hourly thermal load

# <codecell>

def calc_TL(SystemH, SystemC, te_min, te_max, tm_t0, te_t, tintH_set, tintC_set, Htr_em, Htr_ms, Htr_is, Htr_1, Htr_2, Htr_3, 
            I_st, Hve, Htr_w, I_ia, I_m, Cm, Af, Losses, tHset_corr,tCset_corr, IC_max,IH_max, Flag):
    # assumptions
    if Losses == 1:
        #Losses due to emission and control of systems
        tintH_set = tintH_set + tHset_corr
        tintC_set = tintC_set + tCset_corr
    if SystemH == 2: #max and minimum temperatures in the thermal mass + 1 above dewpoint18C to avoid condensation
        t_TABS = (22) - ((22) - 19)*(te_t-te_min)/(te_max-te_min)
    else:
        I_TABS = 0
    # Case 1 
    IHC_nd = IH_nd_ac = IC_nd_ac = IHC_nd_un = 0
    Im_tot = Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd,Hve,Htr_2)
    tm, ts, tair0, top0 = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd,Hve,Htr_is)
    if SystemH == 2:
        I_TABS = Af/0.10*(t_TABS-tm)
        Im_tot = Im_tot+I_TABS
        tm, ts, tair0, top0 = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd,Hve,Htr_is)
    if (tintH_set <= tair0) and (tair0<=tintC_set): 
        ta = tair0
        top = top0
        IHC_nd_ac = I_TABS
        IH_nd_ac = 0
        IC_nd_ac = 0
        if IHC_nd_ac > 0:
            if  Flag == True:
                IH_nd_ac = 0
            else:
                IH_nd_ac = I_TABS
        else:
            if Flag == True:
                IC_nd_ac = I_TABS
            else:
                IC_nd_ac = 0
    else:
        if tair0 > tintC_set:
            tair_set = tintC_set
        else:
            tair_set = tintH_set
        # Case 2 
        IHC_nd =  IHC_nd_10 = 10*Af
        Im_tot = Calc_Im_tot(I_m,Htr_em,te_t,Htr_3,I_st,Htr_w,Htr_1,I_ia,IHC_nd_10,Hve,Htr_2)
        tm, ts, tair10, top10 = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd_10,Hve,Htr_is)
        if SystemH == 2:
            I_TABS = Af/0.08*(t_TABS-tm)
            Im_tot = Im_tot + I_TABS
            tm, ts, tair10, top10 = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd_10,Hve,Htr_is)
        IHC_nd_un =  IHC_nd_10*(tair_set - tair0)/(tair10-tair0) + I_TABS
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
            if SystemH ==2:
                I_TABS = Af/0.08*(t_TABS-tm)
                Im_tot = Im_tot+I_TABS
                tm, ts, ta, top = Calc_Tm(Htr_3,Htr_1,tm_t0,Cm,Htr_em,Im_tot,Htr_ms,I_st,Htr_w,te_t,I_ia,IHC_nd_ac,Hve,Htr_is)
            #Results
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
        
    if SystemC == 0:
       IC_nd_ac = 0 
    return tm, ta, IH_nd_ac, IC_nd_ac

# <markdowncell>

# 2.1. Sub-Function Shading Factors of movebale parts

# <codecell>

#It calculates the rediction factor of shading due to type of shading
def Calc_Rf_sh (ShadingPosition,ShadingType):
    #0 for not #1 for Louvres, 2 for Rollo, 3 for Venetian blinds, 4 for Courtain, 5 for Solar control glass
    d ={'Type':[0, 1, 2, 3, 4,5],'ValueIN':[1, 0.2,0.2,0.3,0.77,0.1],'ValueOUT':[1, 0.08,0.08,0.15,0.57,0.1]}
    ValuesRf_Table = pd.DataFrame(d)
    rows = ValuesRf_Table.Type.count()
    for row in range(rows):
        if ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 1: #1 is exterior
            return ValuesRf_Table.loc[row,'ValueOUT']
        elif ShadingType == ValuesRf_Table.loc[row,'Type'] and  ShadingPosition == 0: #0 is intetiror
            return ValuesRf_Table.loc[row,'ValueIN']

# <codecell>

def calc_gl(radiation, g_gl,Rf_sh):
    if radiation > 300: #in w/m2
        return g_gl*Rf_sh
    else:
        return g_gl

# <markdowncell>

# 2.2. Sub-Function equivalent profile of Occupancy

# <markdowncell>

# 2.3 Sub-Function calculation of thermal losses of emission systems differet to air conditioning

# <codecell>

def calc_Qem_ls(SystemH,SystemC):
    tHC_corr = [0,0]
    # values extracted from SIA 2044 - national standard replacing values suggested in EN 15243
    if SystemH == 4 or 1:
        tHC_corr[0] = 0.5 + 1.2
    elif SystemH == 2: 
        tHC_corr[0] = 0 + 1.2
    elif SystemH == 3: # no emission losses but emissions for ventilation
        tHC_corr[0] = 0.5 + 1 #regulation is not taking into account here
    else:
        tHC_corr[0] = 0.5 + 1.2
    
    if SystemC == 4:
        tHC_corr[1] = 0 - 1.2
    elif SystemC == 5: 
        tHC_corr[1] = - 0.4 - 1.2
    elif SystemC == 3: # no emission losses but emissions for ventilation
        tHC_corr[1] = 0 - 1 #regulation is not taking into account here
    else:
        tHC_corr[1] = 0 + - 1.2
        
    return list(tHC_corr)

# <markdowncell>

# 2.1. Sub-Function losses heating system distribution

# <codecell>

#a factor taking into account that Ll and lw are measured from an aproximated rectangular surface
def Calc_form(Lw,Ll,footprint): 
    factor = footprint/(Lw*Ll)
    return factor

# <codecell>

def calc_Eaux_hs_dis(Qhsf,Qhsf0,Imax,deltaP_des,b, ts,tr,cpw):  
    #the power of the pump in Watts 
    if Qhsf > 0 and (ts-tr) != 0:
        fctr = 1.05
        qV_des = Qhsf/((ts-tr)*cpw*1000)
        Phy_des = 0.2278*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        Ppu_dis = Phy_des*feff
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

# <codecell>

def calc_Eaux_cs_dis(Qcsf,Qcsf0,Imax,deltaP_des,b, ts,tr,cpw): 
#refrigerant R-22 1200 kg/m3
    # for Cooling system   
    #the power of the pump in Watts 
    if Qcsf <0 and (ts-tr) != 0:
        fctr = 1.10
        qV_des = Qcsf/((ts-tr)*cpw*1000)
        Phy_des = 0.2778*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*fctr*b
        Ppu_dis = Phy_des*feff
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

# <codecell>

def calc_Eaux_ww(Qwwf,Qwwf0,Imax,deltaP_des,b,qV_des):
    if Qwwf>0:
        # for domestichotwater 
        #the power of the pump in Watts 
        Phy_des = 0.2778*deltaP_des*qV_des
        feff = (1.25*(200/Phy_des)**0.5)*b
        Ppu_dis = Phy_des*feff
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

# <codecell>

def calc_Eaux_fw(freshw, ro,nf,hf):
    Eaux_fw = np.zeros(8760)
    # for domesticFreshwater
    #the power of the pump in Watts Assuming the best performance of the pump of 0.6 and an accumulation tank
    # all the supply of water is done in 5 hours
    hoursop = 5 # assuming around 2000 hour of operation per day. charged from 11 am to 4 pm
    gr = 9.81 # m/s2 gravity
    effi = 0.6 # efficiency of pumps
    equivalentlength = 0.6
    for day in range(1,366):
        balance = 0
        t0 = (day-1)*24
        t24 = day*24
        for hour in range(t0,t24):
            balance = balance + freshw[hour]
        if balance >0 :
            flowday = balance/(3600) #in m3/s
            Energy_hourWh = (hf*(nf-5))/0.6*ro*gr*(flowday/hoursop)/effi
            for t in range(1,hoursop+1):
                time = t0 + 11 + t
                Eaux_fw[t] = Energy_hourWh
    return Eaux_fw

# <markdowncell>

# ##STATISTICAL ENERGY MODEL

# <codecell>

def Querystatistics(CQ, CQ_name, Model, locationtemp1,locationFinal):

    uses = ['ADMIN','SR','INDUS','REST','RESTS','DEPO','COM','MDU','SDU','EDU','CR','HEALTH','SPORT',
            'SWIM','PUBLIC','SUPER','ICE','HOT']
    #Create the table or database of the CQ to generate the values
    OutTable = 'Database.dbf'
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    Database = dbf2df(locationtemp1+'\\'+OutTable)
    
    #THE FIRST PART RELATED TO THE BUILDING PROPERTIES
    
    #Assing main use of the building To assign systems of heating or cooling in a building basis.
    Database['Type'] = Calc_MainUse(Database)
    
    # assign the year of each category and create a new code 
    Database['YearCat'] = Database.apply(lambda x: YearCategoryFunction(x['Year'],x['Retrofit']), axis=1)
    Database['CODE'] = Database.Type + Database.YearCat
    # Create join with the model
    Joineddata = pd.merge(Database, Model, left_on='CODE', right_on='Code')    
    #EXPORT PROPERTIES RELATED TO PROCESEES AND EQUIPMENT
    Counter = Joineddata.Name.count()
    for row in range(Counter):
        if Joineddata.Hs_x[row] <= 0.20 and Joineddata.Es[row]>0:
            Joineddata.Es[row] = Joineddata.Hs_x[row] 
            
    Joineddata.rename(columns={'Hs_x':'Hs'},inplace=True) 
    # EXPORT PROPERTIES
    Joineddata.to_excel(locationFinal+'\\'+CQ_name+'\\'+'Properties.xls',
                        sheet_name='Values',index=False,cols={'Name','tshs0','trhs0','tscs0','trcs0','tsww0','tsice0','trice0','tscp0','trcp0','tshp0','trhp0','Hs','Es','PFloor','Year','fwindow',
                                                              'Floors','Construction','Emission_heating','Emission_cooling','tsdata0','trdata0',
                                                              'Uwall','Uroof','Ubasement','Uwindow','Type'})
    
    Joineddata.to_excel(locationFinal+'\\'+CQ_name+'\\'+'Equipment.xls',
                        sheet_name='Values',index=False,cols={'Name','CRFlag','SRFlag','ICEFlag',
                                                              'E4'})                                                                                                                      
    
    #THE OTHER PART RELATED TO THE ENERGY VALUES'
    DatabaseUnpivoted = pd.melt(Database, id_vars=('Name','Shape_Area','YearCat','Hs','Floors'))
    DatabaseUnpivoted['CODE'] = DatabaseUnpivoted.variable + DatabaseUnpivoted.YearCat
    #Now both Database with the new codification is merged or joined to the values of the Statistical model
    DatabaseModelMerge = pd.merge(DatabaseUnpivoted, Model, left_on='CODE', right_on='Code')
    
    #Now the values are created. as all the intensity values are described in MJ/m2. 
    ##they are transformed into MWh, Heated space is assumed as an overall 90% of the gross area according to the standard SIA, 
    ##unless it is known (Siemens buildings and surroundings, Obtained during visual inspection a report of the area Grafenau)
    counter = DatabaseModelMerge.value.count()
    for r in range (counter):
        if DatabaseModelMerge.loc[r,'Hs_x'] >= 0:
            DatabaseModelMerge.loc[r,'Hs_y'] = DatabaseModelMerge.loc[r,'Hs_x']
            DatabaseModelMerge.loc[r,'Es'] = DatabaseModelMerge.loc[r,'Hs_x']
        
            
    DatabaseModelMerge['Qhsf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qhsf_kWhm2/1000
    DatabaseModelMerge['Qhpf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qhpf_kWhm2/1000
    DatabaseModelMerge['Qwwf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qwwf_kWhm2/1000
    DatabaseModelMerge['Qcsf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcsf_kWhm2/1000
    DatabaseModelMerge['Qcdataf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcdataf_kWhm2/1000
    DatabaseModelMerge['Qcicef'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcicef_kWhm2/1000
    DatabaseModelMerge['Qcpf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.qcpf_kWhm2/1000
    DatabaseModelMerge['Ealf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Es* DatabaseModelMerge.Ealf_kWhm2/1000
    DatabaseModelMerge['Edataf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.Edataf_kWhm2/1000 
    DatabaseModelMerge['Epf'] = DatabaseModelMerge.value * DatabaseModelMerge.Shape_Area * DatabaseModelMerge.Floors * DatabaseModelMerge.Hs_y* DatabaseModelMerge.Epf_kWhm2/1000
    DatabaseModelMerge['Ecaf'] = 0 #compressed air is 0 for all except siemens where data is measured.
    
    # Pivoting the new table and summing rows all in MWh
    Qhsf = pd.pivot_table(DatabaseModelMerge, values='Qhsf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Qhpf = pd.pivot_table(DatabaseModelMerge, values='Qhpf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Qwwf = pd.pivot_table(DatabaseModelMerge, values='Qwwf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Qcsf = pd.pivot_table(DatabaseModelMerge, values='Qcsf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Qcdataf = pd.pivot_table(DatabaseModelMerge, values='Qcdataf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows') 
    Qcicef = pd.pivot_table(DatabaseModelMerge, values='Qcicef', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows') 
    Qcpf = pd.pivot_table(DatabaseModelMerge, values='Qcpf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Ealf = pd.pivot_table(DatabaseModelMerge, values = 'Ealf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Edataf = pd.pivot_table(DatabaseModelMerge, values='Edataf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    Epf = pd.pivot_table(DatabaseModelMerge, values='Epf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')    
    Ecaf = pd.pivot_table(DatabaseModelMerge, values='Ecaf', rows='Name', cols='CODE', aggfunc='sum', margins='add all rows')
    
    Total = pd.DataFrame({'Qhsf': Qhsf['All'],'Qhpf': Qhpf['All'],'Qwwf': Qwwf['All'],'Qcsf': Qcsf['All'],'Qcpf': Qcpf['All'],
                         'Ealf': Ealf['All'],'Epf': Epf['All'],'Edataf': Edataf['All'],'Qcdataf': Qcdataf['All'],
                         'Ecaf': Ecaf['All'],'Qcicef': Qcicef['All'] })
    # reset index
    Total['Name'] = Total.index
    counter = Total.Qhsf.count()
    Total.index = range(counter)
    
    Total.to_csv(locationFinal+'\\'+CQ_name+'\\'+'Loads.csv', index=False)
    
    return Total

# <markdowncell>

# This function estimates the main type of ocupation in the building. as a result those values such as coefficients of trasnmittance, temperatures of operation and type of emission systems are selected in a mayority basis.

# <codecell>

def Calc_MainUse(database):

    uses = ['ADMIN','SR','INDUS','REST','RESTS','DEPO','COM','MDU','SDU','EDU','CR','HEALTH','SPORT',
        'SWIM','PUBLIC','SUPER','ICE','HOT']
    # do this to avoid that the selection of values be vbased on the DEPO. for buildings qih heated spaces
    def Calc_comparison(array_min,array_max):
        if array_max == 'DEPO':
            if array_min != 'DEPO':
                array_max = array_min
        return array_max
    
    databaseclean = database[uses].transpose()
    array_min = np.array(databaseclean[databaseclean[:]>0].idxmin(skipna =True))
    array_max = np.array(databaseclean[databaseclean[:]>0].idxmax(skipna =True))
    Type = np.vectorize(Calc_comparison)(array_min,array_max)
    return Type

# <markdowncell>

# Sub-function: assign As the values in the statistical model are codified according to a secuence of 1, 2, 3, 4 and 5, a function has to be define to codify in the same therms the Database, a new filed (YearCAt) is assigned to the Database

# <codecell>

def YearCategoryFunction(x,y):
    if 0 < x <= 1920:
        #Database['Qh'] = Database.ADMIN.value * Model.
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
    elif  2000 < y <= 2020:
        result = '11'
    elif y > 2020:
        result = '12' 
    
    return result

# <markdowncell>

# Subfunction to calculate average only used in the aggregation proces

# <codecell>

def Calc_series(x,Name,Union,scenario,Ana,total,INDUS,SR,CR,ICE,Capacities,create_datacenter,dacenter_building):
    # Import series from analytical model
    Series = pd.read_csv(Ana+'\\'+Name+'.csv')
    #variables to do the calculation in processes
    E1 = total.loc[x,'E1']; E2 = total.loc[x,'E2']; E3 = total.loc[x,'E3']; E4 = total.loc[x,'E4']
    HP = total.loc[x,'HP']; CP = total.loc[x,'CP']; CA = total.loc[x,'CA']
    SRFlag = total.loc[x,'SRFlag']; CRFlag = total.loc[x,'CRFlag']; ICEFlag = total.loc[x,'ICEFlag']  

    if E1>0 or E2>0 or E3>0: # ALL THREE TYPICAL ELECTRICAL MACHINES
        INDUS['temp'] = INDUS['E1']*E1*Capacities[0]+INDUS['E2']*Capacities[1]+INDUS['E3']*Capacities[2]
        Series['Epf'] = (INDUS['temp']/INDUS.temp.sum())*(total.loc[x,'Epf']*1000)
    elif E4 >0 and E1==0 and E2==0 and E3==0: #OTHER ELECTRICAL EQUIPMENT
        INDUS['temp'] = INDUS['E4']*Capacities[3] #in kWh
        Series['Epf'] = (INDUS['temp']/INDUS.temp.sum())*(total.loc[x,'Epf']*1000)
    else:
        Series['Epf']=0
    
    if CA > 0: # COMPRESSED AIR 
        Series['Ecaf'] = (INDUS['CA']/INDUS.CA.sum())*(total.loc[x,'Ecaf']*1000) 
    else:
        Series['Ecaf'] = 0
    
    if create_datacenter[scenario] == True: #for recovery purposes
        TotalEdata = total.Edataf.sum()
        if total.loc[x,'Name']== dacenter_building[scenario]:  
            Series['Edataf'] = (SR['E1']/SR.E1.sum())*(TotalEdata*1000)
            Series['Qcdataf'] = (SR['Qc']/SR.Qc.sum())*(TotalEdata*0.7*1000)
            Series['tsdata'] = SR.Qc.apply(lambda x: 52.5  if x > 0 else 0)
            Series['trdata'] = SR.Qc.apply(lambda x: 60  if x > 0 else 0)
            total.loc[x,'Edataf'] == TotalEdata
            total.loc[x,'Qcdataf'] == TotalEdata*0.7
            Series['mcpdata'] = Series.Qcdataf/(Series.trdata - Series.tsdata) #in kWh/c
        else: 
            Series['Edataf'] = 0
            Series['Qcdataf'] = 0
            Series['tsdata'] = 0
            Series['trdata'] = 0
            total.loc[x,'Edataf'] == 0
            total.loc[x,'Edataf'] == 0
            Series['mcpdata'] = 0
    else:        
        if SRFlag == 1: # SERVERS  
            tsdata0 = total.loc[x,'tsdata0']
            trdata0 = total.loc[x,'trdata0']
            Series['Edataf'] = (SR['E1']/SR.E1.sum())*(total.loc[x,'Edataf']*1000)
            Series['Qcdataf'] = (SR['Qc']/SR.Qc.sum())*(total.loc[x,'Qcdataf']*1000)
            Series['tsdata'] = Series.Qcdataf.map(lambda x: tsdata0 if x > 0 else 0)
            Series['trdata'] = Series.Qcdataf.map(lambda x: trdata0 if x > 0 else 0)
            Series['mcpdata'] = Series.Qcdataf/(tsdata0 - trdata0) #in kWh/c
        else:
            Series['Qcdataf']= Series['Edataf']= 0
            Series['tsdata'] = 0
            Series['trdata'] = 0
            Series['mcpdata']= 0
    
    if CP > 0: # PROCESS COOLING
        tscp0 = total.loc[x,'tscp0']
        trcp0 = total.loc[x,'trcp0']
        Series['Qcpf'] = (INDUS['CP']/INDUS.CP.sum())*(total.loc[x,'Qcpf']*1000)
        Series['tscp'] = Series.Qcpf.apply(lambda x: tscp0 if x > 0 else 0)
        Series['trcp'] = Series.Qcpf.apply(lambda x: trcp0 if x > 0 else 0)
        Series['mcpcp'] = Series.Qcpf/(tscp0 - trcp0) #in kWh/c
    else:
        Series['Qcpf']=0
        Series['tscp']=0
        Series['trcp']=0
        Series['mcpcp'] = 0
    
    if HP >0: # PROCESS HEATING
        tshp0 = total.loc[x,'tshp0']
        trhp0 = total.loc[x,'trhp0']
        Series['Qhpf'] = (INDUS['HP']/INDUS.HP.sum())*(total.loc[x,'Qhpf']*1000)
        Series['tshp']= Series.Qhpf.apply(lambda x:  tshp0 if x > 0 else 0)
        Series['trhp']= Series.Qhpf.apply(lambda x: trhp0 if x > 0 else 0)
        Series['mcphp'] = Series.Qhpf/(tshp0 - trhp0) #in kWh/c
    else:
        Series['Qhpf']= 0
        Series['tshp']= 0
        Series['trhp']= 0 
        Series['mcphp']=0
        
    if ICEFlag == 1:# ICE HOKEY   
        tsice0 = total.loc[x,'tsice0']
        trice0 = total.loc[x,'trice0']
        Series['Qcicef'] = (ICE['Qc']/ICE.Qc.sum())*(total.loc[x,'Qcicef']*1000)
        Series['tsice'] = Series.Qcicef.apply(lambda x: tsice0 if x > 0 else 0)
        Series['trice']= Series.Qcicef.apply(lambda x: trice0 if x > 0 else 0)
        Series['mcpice'] = Series.Qcicef/(tsice0 - trice0) #in kWh/c
    else:
        Series['Qcicef'] = 0
        Series['tsice'] = 0
        Series['trice'] = 0
        Series['mcpice'] = 0
  
    if CRFlag == 1: # COOLING ROOMS  
        tsice0 = total.loc[x,'tsice0']
        trice0 = total.loc[x,'trice0']
        Series['Qcicef'] = (CR['Qc']/CR.Qc.sum())*(total.loc[x,'Qcicef']*1000)
        Series['tsice'] = Series.Qcicef.apply(lambda a: tsice0 if a > 0 else 0)
        Series['trice'] = Series.Qcicef.apply(lambda a: trice0 if a > 0 else 0)
        Series['mcpice'] = Series.Qcicef/(tsice0 - trice0) #in kWh/c
    else:
        Series['Qcicef']= 0
        Series['tsice'] = 0
        Series['trice'] = 0
        Series['mcpice'] = 0     
    # Calculate for building services total average
    
    Series['Qhs'] = Series['Qhs']/Series['Qhsf'] # obtain the percentage of net/total
    Series['Qcs'] = Series['Qcs']/Series['Qcsf']
    Series['Qww'] = Series['Qww']/Series['Qwwf']
    Series['Qhsf'] = (Series.Qhsf/Union.loc[x,'Qhsf_x'])*(total.loc[x,'Qhsf'])# in kW
    Series['Qwwf'] = (Series.Qwwf/Union.loc[x,'Qwwf_x'])*(total.loc[x,'Qwwf'])
    Series['Qcsf'] = (Series.Qcsf/Union.loc[x,'Qcsf_x'])*(total.loc[x,'Qcsf'])
    Series['Ealf'] = (Series.Ealf/Union.loc[x,'Ealf_x'])*(total.loc[x,'Ealf'])
    Series['Eauxf'] = Series['Eauxf'].copy() #in kW
    Series['Qhs'] = Series['Qhs']*Series['Qhsf'] # attribute then the new fraction
    Series['Qcs'] = Series['Qcs']*Series['Qcsf']
    Series['Qww'] = Series['Qww']*Series['Qwwf']    
    Series.replace([np.inf, -np.inf], np.nan,inplace=True)
    Series.fillna(value=0,inplace=True) # because cooling values or other can be 0
    return Series.copy()

# <codecell>

def Calc_Average(Union,Scenario,Final,Ana,r,Zone_of_study):
    Average = Union.copy()
    if Scenario == 'SQ' and (r) == Zone_of_study:
        Average['Qhs'] = Union.Qhs/Union.Qhsf_x # obtain the percentage of net/total
        Average['Qcs'] = Union.Qcs/Union.Qcsf_x
        Average['Qww'] = Union.Qww/Union.Qwwf_x
        Average['Qhsf'] = (Union.Qhsf_x+Union.Qhsf_y+Union.Qhsf)/3
        Average['Qcsf'] = (Union.Qcsf_x+Union.Qcsf_y+Union.Qcsf)/3
        Average['Qwwf'] = (Union.Qwwf_x+Union.Qwwf_y+Union.Qwwf)/3
        Average['Qhs'] = Average['Qhs']*Average['Qhsf'] # attribute then the new fraction
        Average['Qcs'] = Average['Qcs']*Average['Qcsf']
        Average['Qww'] = Average['Qww']*Average['Qwwf']
        Average['Ealf'] = (Union.Ealf_x+Union.Ealf_y+Union.Ealf)/3  
        Average['Epf'] =  Union.Epf_y
        Average['Qcdataf'] = (Union.Qcdataf_x+Union.Qcdataf_y)/2
        Average['Edataf'] = (Union.Edataf_x+Union.Edataf_y)/2
        Average['Qhpf'] = Union.Qhpf_y
        Average['Qcpf'] = Union.Qcpf_y
        Average['Ecaf'] = Union.Ecaf_y
       # Average['E1'] = Union.E1
       # Average['E2'] = Union.E2
       # Average['E3'] = Union.E3
       # Average['CA'] = Union.CA
       # Average['CP'] = Union.CP
       # Average['HP'] = Union.HP
    else:
        Average['Qhs'] = Union.Qhs/Union.Qhsf_x # obtain the percentage of net/total
        Average['Qcs'] = Union.Qcs/Union.Qcsf_x
        Average['Qww'] = Union.Qww/Union.Qwwf_x
        Average['Qhsf'] = (Union.Qhsf_x+Union.Qhsf_y)/2
        Average['Qcsf'] = (Union.Qcsf_x+Union.Qcsf_y)/2
        Average['Qwwf'] = (Union.Qwwf_x+Union.Qwwf_y)/2
        Average['Ealf'] = (Union.Ealf_x+Union.Ealf_y)/2
        Average['Qhs'] = Average['Qhs']*Average['Qhsf'] # attribute then the new fraction
        Average['Qcs'] = Average['Qcs']*Average['Qcsf']
        Average['Qww'] = Average['Qww']*Average['Qwwf']
        Average['Epf'] = Union.Epf
        Average['Ecaf'] = 0 # no compessed air for any industry if it is unknown statistically
        Average['Qcpf'] = 0 # Union.Qcpf It cannot be assured for all industries
        Average['Qhpf'] = 0 # Union.Qhpf It cannot be assured for all industries
        Average['Qcdataf'] = Union.Qcdataf
        Average['Edataf'] = Union.Edataf
    
    Average['Qhf'] = Average['Qhsf']+Average['Qwwf']+Average['Qhpf']
    Average['Qcf'] = Average['Qcsf']+Average['Qcpf']+Average['Qcdataf']+Average['Qcicef']
    
    #Average['E4'] = Union.E4
    #Average['CRFlag'] = Union.CRFlag
    #Average['ICEFlag'] = Union.ICEFlag
    #Average['SRFlag'] = Union.SRFlag
    #Average['Qcicef'] = Union.Qcicef
    #Average['Water'] = Union.totwater    
    #Average['Af'] = Union.Af
    #Average['Eaux'] = Union.Eaux
    #Average['Occupancy'] = Union.MaxOccupancy
    
    return Average.copy()

# <codecell>

def calc_newmass(i, allproperties, SeriesAVG):  
    Af = allproperties.loc[i,'Af']
    if Af >0:
        # MAIN VARIABLES
        tsww0 = allproperties.loc[i,'tsww0_x']
        trww0 = 10
        #calculate flows
        SeriesAVG.rename(columns={'tsh':'tshs','trh':'trhs','tsc':'tscs','trc':'trcs'},inplace=True)
        SeriesAVG['mcphs'] = SeriesAVG['Qhsf']/(SeriesAVG['tshs']-SeriesAVG['trhs'])
        SeriesAVG['mcpcs'] = SeriesAVG['Qcsf']/(SeriesAVG['trcs']-SeriesAVG['tscs'])
        SeriesAVG['mcpww'] = SeriesAVG['Qwwf']/(SeriesAVG['tsww']-SeriesAVG['trww'])
        SeriesAVG.replace([np.inf, -np.inf], np.nan,inplace=True)
        SeriesAVG.fillna(value=0,inplace=True)
        mwh0 = SeriesAVG['mcphs'].max()
        mwc0 = SeriesAVG['mcpcs'].min()
        tsh0 = allproperties.loc[i,'tsh0']
        trh0 = allproperties.loc[i,'trh0']
        tsc0 = allproperties.loc[i,'tsc0']
        trc0 = allproperties.loc[i,'trc0']
    else:
        SeriesAVG['tsww'] = 0
        SeriesAVG['trww'] = 0
        SeriesAVG['tshs'] = 0
        SeriesAVG['trhs'] = 0
        SeriesAVG['tscs'] = 0
        SeriesAVG['trcs'] = 0
        SeriesAVG['mcphs'] =0
        SeriesAVG['mcpcs'] =0
        SeriesAVG['mcpww'] = 0
        mwh0 = 0 # in kg.h
        mwc0 = 0 # in kg.h
        tsh0 = 0 # in C
        trh0 = 0 # in C
        tsc0 = 0 # in C
        trc0 = 0 # in C  
        tsww0 = 0
    return SeriesAVG.copy(),mwh0,mwc0,tsh0,trh0,tsc0,trc0,tsww0

# <codecell>

def  calc_estimates(Average,EquipmentEst,ValuesEst):
    Variables1 = ['E1','E2','E3','CA','CP','HP']
    for y in Variables1:
        Average[y] = 0 
    Variables2 = ['Epf','Ecaf','Qcpf','Qhpf']
    buildings = Average.Name.count()
    for row in range (buildings):
        Data = EquipmentEst.Name.count()
        Name = Average.loc[row,'Name']
        for r in range(Data):
            Name2 = EquipmentEst.loc[r,'Name']
            if Name == Name2:
                for y in Variables1:
                    Average.loc[row,y] = EquipmentEst.loc[r,y]
        Data2= ValuesEst.Name.count()
        for r in range(Data2):
            Name2 = ValuesEst.loc[r,'Name']
            if Name == Name2:
                for y in Variables2:
                    Average.loc[row,y] = ValuesEst.loc[r,y]
    return Average

# <codecell>


