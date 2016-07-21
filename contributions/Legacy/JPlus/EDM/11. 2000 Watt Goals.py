# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 2000-Watt Society Goals
# 
# This routine calculates the average emissions and primary energy (non renewable) in every sector

# <markdowncell>

# ####MODULES

# <codecell>

from __future__ import division
import arcpy
from arcpy import sa
import sys,os
import pandas as pd
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
arcpy.env.overwriteOutput = True
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM

# <markdowncell>

# ####VARIABLES

# <codecell>

Scenario = 'SQ'
Zone = 'ZONE_3'

# <codecell>

database = r'c:\ArcGIS\EDM.gdb' 
locationgem = r'C:\ArcGIS\EDMdata\DataFinal\GEM'+'\\'+Scenario+'\\'+Zone #GEM is the grey emissions model
locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
locationtemp1 = r'c:\ArcGIS\temp'
locationFinal = r'C:\ArcGIS\EDMdata\DataFinal\2000watt'+'\\'+Scenario+'\\'+Zone #GEM is the grey emissions model

# <codecell>

#GREY EMISSIONS
data = pd.ExcelFile(locationgem+'\\'+'Grey.xls')
grey = pd.ExcelFile.parse(data, 'Values')
energy = pd.read_csv(locationedm+'\\'+'Total.csv')

# <codecell>

#RECOVERY AND EMISSION FACTORS
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,1402.21,0,504.44]#value in MWh of recoverable due tro servers
ri = [0,565.55,0,565.55,0] #value in MWh of recoverable due to processes
fe_Qh = [0.085,0.028,0.026,0.026,0.028] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0366,0.0345,0.0344] #emissions energy factor electricity
fp_Qh = [1.457,0.818,0.681,0.681,0.818] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.63,2.63,2.19,1.98,1.97]#primary energy factor electricity
# for industry primary factors total no processes
fpt_Qh = [1.466,0.892,0.734,0.734,0.892] #primary energy factor heating
fpt_Qc = [17.34,17.34,17.34,17.34,17.34]#primary energy factor cooling
fpt_E = [2.051,3.051,2.53,2.28,2.27]#primary energy factor electricity
# for industry primary factors only heating processes
fe_Qhp = [0.085,0.075,0.075,0.075,0.075]
fp_Qhp = [1.466,1.291,1.291,1.291,1.291]
# this states if there is recovery
if Scenario == 'SQ':
    r = 0 
elif Scenario == 'BAU':
    r = 1
elif Scenario == 'HEB':
    r = 2    
elif Scenario == 'UC':
    r = 3        
elif Scenario == 'CAMP':
    r = 4

# <markdowncell>

# ####PROCESS

# <codecell>

# Create the table or database of the CQ to generate the values
CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
OutTable = 'Database.dbf'
arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
Database0 = dbf2df(locationtemp1+'\\'+OutTable)
Database1 = pd.merge(Database0,energy, on='Name')
Database = pd.merge(Database1,grey, on='Name')

# <markdowncell>

# ####FUNCTIONS

# <codecell>

#CREATE SECTORS
Database['supermarket'] = Database['CR']+Database['SUPER']
Database['retail'] = Database['COM']
Database['restaurant'] = Database['REST']+Database['RESTS']+Database['CR']
Database['other'] = Database['PUBLIC']+Database['SPORT']+Database['SWIM']+Database['HEALTH']+Database['DEPO']+abs(Database['PFloor']-1)
Database['offices'] = Database['ADMIN']+Database['SR']+Database['EDU']
Database['hotel'] = Database['HOT']
Database['dwellings'] = Database['MDU'] + Database['SDU']
Database['industry'] = Database['INDUS']

# <codecell>

#FOR ALL
Database['Areaf'] = Database.Af
Af_tot = Database.Areaf.sum()
Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[r]+ri[r])
Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- rs[r]
E = (Database['Ealf']+Database['Ecaf']+Database['Epf']+Database['Edataf']).sum()
#operation
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = Database['GE'].sum()/Database['Areaf'].sum()
greyemissions = Database['GGHG'].sum()/Database['Areaf'].sum()

#Create dataframe
GT = {'CAT': 'Total','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal = pd.DataFrame(GT,index=[0])

# <codecell>

#FOR dweillings
Database['Areaf'] = Database.Af*Database.dwellings
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['dwellings']).sum()
Database['Qh'] = Database['Qhsf']+Database['Qwwf']+Database['Qhpf']
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum() #recover according to ammount of heat consumed
Qc = (Database['Qcsf']*Database['dwellings']).sum()
Database['Qc'] =Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = (Database['Ealf']*Database['dwellings']).sum()
#operation
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['dwellings']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['dwellings']).sum()/Database['Areaf'].sum()

# Attach to dataframe 
GT = {'CAT': 'dwellings','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

#FOR OFFICES
Database['Areaf'] = Database.Af*Database.offices
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['offices']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = ((Database['Qcsf']+Database['Qcdataf'])*Database['offices']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = ((Database['Ealf']+Database['Edataf'])*Database['offices']).sum()
#operation
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['offices']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['offices']).sum()/Database['Areaf'].sum()

# Attach to dataframe 
GT = {'CAT': 'offices','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

#FOR supermarket
Database['Areaf'] = Database.Af*Database.supermarket
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['supermarket']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = ((Database['Qcsf']+Database['Qcicef'])*Database['supermarket']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = (Database['Ealf']*Database['supermarket']).sum()
#operation
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['supermarket']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['supermarket']).sum()/Database['Areaf'].sum()

# Attach to dataframe 
GT = {'CAT': 'supermarket','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

#FOR hotel
Database['Areaf'] = Database.Af*Database.hotel
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['hotel']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = ((Database['Qcsf'])*Database['hotel']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = (Database['Ealf']*Database['hotel']).sum()
#operation
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['hotel']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['hotel']).sum()/Database['Areaf'].sum()

# Attach to dataframe 
GT = {'CAT': 'hotel','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

#FOR restaurant
Database['Areaf'] = Database.Af*Database.restaurant
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['restaurant']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = ((Database['Qcsf']+Database['Qcicef'])*Database['restaurant']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = (Database['Ealf']*Database['restaurant']).sum()
#operation
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['restaurant']*Database['PFloor']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['restaurant']*Database['PFloor']).sum()/Database['Areaf'].sum()

# Attach to dataframe 
GT = {'CAT': 'restaurant','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

#FOR retail
Database['Areaf'] = Database.Af*Database.retail
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['retail']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = ((Database['Qcsf'])*Database['retail']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = (Database['Ealf']*Database['retail']).sum()
#operation
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['retail']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['retail']).sum()/Database['Areaf'].sum()

# Attach to dataframe 
GT = {'CAT': 'retail','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

#FOR OTHER
Database['Areaf'] = Database['Af']*Database['other']
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['other']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = ((Database['Qcsf'])*Database['other']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = (Database['Ealf']*Database['other']).sum()
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['other']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['other']).sum()/Database['Areaf'].sum()

#Create dataframe
GT = {'CAT': 'other','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

#FOR industry (no processes included)
Database['Areaf'] = Database['Af']*Database['industry']
Af_tot = Database.Areaf.sum()
Qh = ((Database['Qhsf']+Database['Qwwf'])*Database['industry']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = ((Database['Qcsf'])*Database['industry']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = (Database['Ealf']*Database['industry']).sum()
Emissions = (Qh*fe_Qh[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qh[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['industry']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['industry']).sum()/Database['Areaf'].sum()

#Create dataframe
GT = {'CAT': 'Industry_buildings','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)

# <codecell>

print Grandtotal2

# <codecell>

#FOR Processes
Database['Areaf'] = Database['Af']*Database['industry']
Af_tot = Database.Areaf.sum()
Qh = (Database['Qhpf']).sum()
Qh = Qh -(rs[r]+ri[r])*Qh/Database['Qh'].sum()
Qc = (Database['Qcpf']).sum()
Qc = Qc - rs[r]*Qc/Database['Qc'].sum()
E = ((Database['Ecaf']+Database['Epf'])).sum()
Emissions = (Qh*fe_Qhp[r] + Qc*fe_Qc[r] + E*fe_E[r])/Af_tot*3600
Primary = (Qh*fp_Qhp[r] + Qc*fp_Qc[r] + E*fp_E[r])/Af_tot*3600
#construction
greyprimary = (Database['GE']*Database['industry']).sum()/Database['Areaf'].sum()
greyemissions = (Database['GGHG']*Database['industry']).sum()/Database['Areaf'].sum()

#Create dataframe
GT = {'CAT': 'Industry_processes','CO2': Emissions,'Ep': Primary,'GHGE': greyemissions,'GE': greyprimary}
Grandtotal2 = pd.DataFrame(GT,index=[0])
Grandtotal = Grandtotal.append(Grandtotal2)
Grandtotal.fillna(0,inplace=True)
Grandtotal.to_excel(locationFinal+'\\'+'Total.xls')

# <markdowncell>

# ####EMISSIONS OPERATION ALL SCENARIOS SEVERAL INFRASTRUCTURAL CONFIGURATIONS AND BUILDING RETROFIT

# <codecell>

#THIS IS WITH THE NEW TYPE OF SYSTEM
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [1250.4,1356.6,1402.21,0,504.44]#value in MWh of recoverable due tro servers
ri = [295.2,565.55,0,565.55,0] #value in MWh of recoverable due to processes
fe_Qh = [0.028,0.028,0.026,0.026,0.028] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0384,0.0386,0.0366,0.0350,0.0346] #emissions energy factor electricity
fp_Qh = [0.818,0.818,0.681,0.681,0.818] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.346,2.37,2.193,2.011,1.973]#primary energy factor electricity


# list of scenarios
sc = ['SQ', 'BAU', 'HEB', 'UC', 'CAMP']
# list of Cityquarters in each scenario
database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
    Database = pd.read_csv(locationedm+'\\'+'Total.csv')
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH ONLY PV
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.085,0.085,0.085,0.085,0.085] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0384,0.0386,0.0366,0.0350,0.0346] #emissions energy factor electricity

fp_Qh = [1.457,1.457,1.457,1.4571,1.457] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.346,2.37,2.193,2.011,1.973]#primary energy factor electricity

# list of scenarios
sc = ['SQ', 'BAU', 'HEB', 'UC', 'CAMP']
# list of Cityquarters in each scenario
database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
    Database = pd.read_csv(locationedm+'\\'+'Total.csv')
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH THE HEAT RECOVERY OF INDUSTRY
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [295.2,565.55,0,565.55,0] #value in MWh of recoverable due to processes
fe_Qh = [0.085,0.085,0.085,0.085,0.085] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0413,0.0413,0.0413] #emissions energy factor electricity

fp_Qh = [1.457,1.457,1.457,1.4571,1.457] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.635,2.635,2.635,2.635,2.635]#primary energy factor electricity


# list of scenarios
sc = ['SQ', 'BAU', 'HEB', 'UC', 'CAMP']
# list of Cityquarters in each scenario
database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
    Database = pd.read_csv(locationedm+'\\'+'Total.csv')
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH THE HEAT RECOVERY OF SERVERS
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [1250.4,1356.6,1402.21,0,504.44]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.085,0.085,0.085,0.085,0.085] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0413,0.0413,0.0413] #emissions energy factor electricity

fp_Qh = [1.457,1.457,1.457,1.4571,1.457] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.635,2.635,2.635,2.635,2.635]#primary energy factor electricity

# list of scenarios
sc = ['Statusquo', 'BAU2030', 'HEB2030', 'UC2030', 'CAMP2030']
# list of Cityquarters in each scenario
cq = ['CityQuarter_3', 'BAU_2030', 'HEB_2030', 'UC_2030','CAMP_2030']
cq2 = ['CityQuarter_3', 'BAU2030', 'HEB2030', 'UC2030','CAMP2030']
locationClusters = r'c:\ArcGIS\EDM.gdb\Communities' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    CQuarter1 = cq[row]
    CQuarter2 = cq2[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+CQuarter2 #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = locationClusters+'\\'+CQuarter1
    OutTable = 'Database.dbf'
    data = pd.ExcelFile(locationedm+'\\'+'Total.xls')
    energy = pd.ExcelFile.parse(data, 'sheet1')
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    Database0 = dbf2df(locationtemp1+'\\'+OutTable)
    Database = pd.merge(Database0,energy, on='Name')
    
    Database['Af'] = Database['Shape_Area']*Database['Floors']*Database['Hs']
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH THE OLD SYSTEM
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.085,0.085,0.085,0.085,0.085] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0413,0.0413,0.0413] #emissions energy factor electricity

fp_Qh = [1.457,1.457,1.457,1.4571,1.457] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.635,2.635,2.635,2.635,2.635]#primary energy factor electricity

# list of scenarios
sc = ['SQ', 'BAU', 'HEB', 'UC', 'CAMP']
# list of Cityquarters in each scenario
database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
    Database = pd.read_csv(locationedm+'\\'+'Total.csv')
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH THE LAKE-WATER HEATPUMPS
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.028,0.028,0.026,0.026,0.028] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0413,0.0413,0.0413] #emissions energy factor electricity

fp_Qh = [0.818,0.818,0.618,0.618,0.818] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.635,2.635,2.635,2.635,2.635]#primary energy factor electricity

# list of scenarios
sc = ['SQ', 'BAU', 'HEB', 'UC', 'CAMP']
# list of Cityquarters in each scenario
database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
    Database = pd.read_csv(locationedm+'\\'+'Total.csv')
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH THE SOLAR COLLECTORS
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.0268,0.0268,0.0268,0.0268,0.0268] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0413,0.0413,0.0413] #emissions energy factor electricity

fp_Qh = [0.6192,0.6192,0.6192,0.6192,0.6192] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.635,2.635,2.635,2.635,2.635]#primary energy factor electricity

# list of scenarios
sc = ['SQ', 'BAU', 'HEB', 'UC', 'CAMP']
# list of Cityquarters in each scenario
database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = database+'\\'+Scenario+'\\'+Scenario+Zone
    Database = pd.read_csv(locationedm+'\\'+'Total.csv')
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH THE SOLAR COLLECTORS + PV = PVT +Hp for extraction
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [1250.4,1356.6,1402.21,0,504.44]#value in MWh of recoverable due tro servers
ri = [295.2,565.55,0,565.55,0] #value in MWh of recoverable due to processes
fe_Qh = [0.0268,0.0268,0.0268,0.0268,0.0268] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0384,0.0386,0.0366,0.0350,0.0346] #emissions energy factor electricity

fp_Qh = [0.6192,0.6192,0.6192,0.6192,0.6192] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.346,2.37,2.193,2.011,1.973]#primary energy factor electricity


# list of scenarios
sc = ['SQ', 'BAU', 'HEB', 'UC', 'CAMP']
# list of Cityquarters in each scenario
database = r'c:\ArcGIS\EDM.gdb' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+Zone #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    Database = pd.read_csv(locationedm+'\\'+'Total.csv')
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']+Database['Qcicef']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS FOR CHP WITH BIOGAS
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.0318,0.0318,0.0318,0.0318,0.0318] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0303,0.0315,0.0282,0.0277,0.0253] #emissions energy factor electricity

fp_Qh = [0.5368,0.5368,0.5368,0.5368,0.5368] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [1.9189,1.9991,1.7815,1.7451,1.5875]#primary energy factor electricity

# list of scenarios
sc = ['Statusquo', 'BAU2030', 'HEB2030', 'UC2030', 'CAMP2030']
# list of Cityquarters in each scenario
cq = ['CityQuarter_3', 'BAU_2030', 'HEB_2030', 'UC_2030','CAMP_2030']
cq2 = ['CityQuarter_3', 'BAU2030', 'HEB2030', 'UC2030','CAMP2030']
locationClusters = r'c:\ArcGIS\EDM.gdb\Communities' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    CQuarter1 = cq[row]
    CQuarter2 = cq2[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+CQuarter2 #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = locationClusters+'\\'+CQuarter1
    OutTable = 'Database.dbf'
    data = pd.ExcelFile(locationedm+'\\'+'Total.xls')
    energy = pd.ExcelFile.parse(data, 'sheet1')
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    Database0 = dbf2df(locationtemp1+'\\'+OutTable)
    Database = pd.merge(Database0,energy, on='Name')
    
    Database['Af'] = Database['Shape_Area']*Database['Floors']*Database['Hs']
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH THE OLD SYSTEM + summer sHUTDOWN +DECENTRALIZED BOILER
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.075,0.075,0.075,0.075,0.075] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0413,0.0413,0.0413] #emissions energy factor electricity

fp_Qh = [1.291,1.291,1.291,1.291,1.291] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.635,2.635,2.635,2.635,2.635]#primary energy factor electricity

# list of scenarios
sc = ['Statusquo', 'BAU2030', 'HEB2030', 'UC2030', 'CAMP2030']
# list of Cityquarters in each scenario
cq = ['CityQuarter_3', 'BAU_2030', 'HEB_2030', 'UC_2030','CAMP_2030']
cq2 = ['CityQuarter_3', 'BAU2030', 'HEB2030', 'UC2030','CAMP2030']
locationClusters = r'c:\ArcGIS\EDM.gdb\Communities' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    CQuarter1 = cq[row]
    CQuarter2 = cq2[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+CQuarter2 #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = locationClusters+'\\'+CQuarter1
    OutTable = 'Database.dbf'
    data = pd.ExcelFile(locationedm+'\\'+'Total.xls')
    energy = pd.ExcelFile.parse(data, 'sheet1')
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    Database0 = dbf2df(locationtemp1+'\\'+OutTable)
    Database = pd.merge(Database0,energy, on='Name')
    
    Database['Af'] = Database['Shape_Area']*Database['Floors']*Database['Hs']
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>

#THIS IS WITH BIOMASS PELLETS BOILER
# factors organized in Status Quo, BAU,HEB,UC and CAMP
rs = [0,0,0,0,0]#value in MWh of recoverable due tro servers
ri = [0,0,0,0,0] #value in MWh of recoverable due to processes
fe_Qh = [0.014,0.014,0.014,0.014,0.014] #emissions factor heating
fe_Qc = [0.002,0.002,0.002,0.002,0.002] #emissions energy factor cooling
fe_E = [0.0413,0.0413,0.0413,0.0413,0.0413] #emissions energy factor electricity

fp_Qh = [0.227,0.227,0.227,0.227,0.227] #primary energy factor heating
fp_Qc = [0.155,0.155,0.155,0.155,0.155]#primary energy factor cooling
fp_E = [2.635,2.635,2.635,2.635,2.635]#primary energy factor electricity

# list of scenarios
sc = ['Statusquo', 'BAU2030', 'HEB2030', 'UC2030', 'CAMP2030']
# list of Cityquarters in each scenario
cq = ['CityQuarter_3', 'BAU_2030', 'HEB_2030', 'UC_2030','CAMP_2030']
cq2 = ['CityQuarter_3', 'BAU2030', 'HEB2030', 'UC2030','CAMP2030']
locationClusters = r'c:\ArcGIS\EDM.gdb\Communities' #Scenarios or Communities
locationtemp1 = r'c:\ArcGIS\temp'

for row in range(5):
    Scenario = sc[row]
    CQuarter1 = cq[row]
    CQuarter2 = cq2[row]
    locationedm = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario+'\\'+CQuarter2 #EDM is the energy demand model
    # Create the table or database of the CQ to generate the values
    CQ = locationClusters+'\\'+CQuarter1
    OutTable = 'Database.dbf'
    data = pd.ExcelFile(locationedm+'\\'+'Total.xls')
    energy = pd.ExcelFile.parse(data, 'sheet1')
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    Database0 = dbf2df(locationtemp1+'\\'+OutTable)
    Database = pd.merge(Database0,energy, on='Name')
    
    Database['Af'] = Database['Shape_Area']*Database['Floors']*Database['Hs']
    Af_tot = Database.Af.sum()
    Qh = (Database['Qhsf']+Database['Qwwf']+Database['Qhpf']).sum()-(rs[row]+ri[row])
    Qc =(Database['Qcsf']+Database['Qcdataf']+Database['Qcpf']).sum()- (rs[row]/0.8)
    E = (Database['Ealf']+Database['Ecaf']+Database['Edataf']+Database['Epf']).sum()
    Emissions = (Qh*fe_Qh[row] + Qc*fe_Qc[row] + E*fe_E[row])/Af_tot*3600
    Primary = (Qh*fp_Qh[row] + Qc*fp_Qc[row] + E*fp_E[row])/Af_tot*3600

    print  Emissions,Primary

# <codecell>


