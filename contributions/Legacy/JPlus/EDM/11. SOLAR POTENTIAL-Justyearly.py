# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import arcpy 
import pandas as pd

# <codecell>

database = r'c:\ArcGIS\EDM.gdb'  #ArcGIS database
CQ_name = 'UC2030' #Name of the City Quarter to calculate
CQ = database+'\\'+'Scenarios\\'+CQ_name #location of Buildings of the community
context = CQ +'CONTEXT' #location Buildings of all the context
DEM = database+'\\DEM' # DEM of analysis resampled to grid of 1m for more accurracy

# <codecell>

WeatherData = pd.ExcelFile('C:\ArcGIS\EDMdata\Weatherdata\Temp_Design.xls') # Location of temperature data
T_G_hour = pd.ExcelFile.parse(WeatherData, 'Values_hour') # temperature and radiation table
T_G_day = pd.ExcelFile.parse(WeatherData, 'Values_day') # temperature and radiation table

# <codecell>

latitude = 47.1628017306431      #longitude of the city
longitude = 8.31                 #latitude of the city
timezone = 1                     #Timezone of the city
Yearsimul = 2013

# <codecell>

T_G_day['sunrise'] =0 
for day in range(1,365): # Calculated according to NOAA website
    # Calculate Date and Julian day
    Date = datetime.datetime(Yearsimul, 1, 1) + datetime.timedelta(day - 1)
    JuliandDay = sum(jdcal.gcal2jd(Date.year, Date.month, Date.day))
    JulianCentury = (JuliandDay-2451545)/36525
    # Calculate variables for sunrise
    Gmean = np.mod(280.46646+JulianCentury*(36000.76983 + JulianCentury*0.0003032),360)
    Gmeansun = 357.52911+JulianCentury*(35999.05029 - 0.0001537*JulianCentury)
    Orbit = 0.016708634-JulianCentury*(0.000042037+0.0000001267*JulianCentury)
    Suneq_control = np.sin(np.radians(Gmeansun))*(1.914602-JulianCentury*(0.004817+0.000014*JulianCentury))+np.sin(np.radians(2*Gmeansun))*(0.019993-0.000101*JulianCentury)+np.sin(np.radians(3*Gmeansun))*0.000289
    Suntrue_long = Gmean+Suneq_control
    Sunapp_long = Suntrue_long-0.00569-0.00478*np.sin(np.radians(125.04-1934.136*JulianCentury))
    MeanObl = 23+(26+((21.448-JulianCentury*(46.815+JulianCentury*(0.00059-JulianCentury*0.001813))))/60)/60
    OblCorr = MeanObl+0.00256*np.cos(np.radians(125.04-1934.136*JulianCentury))
    SunDeclinationAngle = np.degrees(np.arcsin(np.sin(np.radians(OblCorr))*np.sin(np.radians(Sunapp_long))))
    vary = np.tan(np.radians(OblCorr/2))*np.tan(np.radians(OblCorr/2))
    #Equation of time:
    EOT =4*np.degrees(vary*np.sin(2*np.radians(Gmean))-2*Orbit*np.sin(np.radians(Gmeansun))+4*Orbit*vary*np.sin(np.radians(Gmeansun))*np.cos(2*np.radians(Gmean))-0.5*vary*vary*np.sin(4*np.radians(Gmean))-1.25*Orbit*Orbit*np.sin(2*np.radians(Gmeansun)))
    # aparent sunrise hour
    HA_sunrise = np.degrees(np.arccos(np.cos(np.radians(90.833))/(np.cos(np.radians(latitude))*np.cos(np.radians(SunDeclinationAngle)))-np.tan(np.radians(latitude))*np.tan(np.radians(SunDeclinationAngle))))
    Solar_noon =(720-4*longitude-EOT+timezone*60)/1440
    T_G_day.loc[day,'sunrise'] = (Solar_noon-HA_sunrise*4/1440)*24

# <codecell>


