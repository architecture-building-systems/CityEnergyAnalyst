# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #6. Spatiotemporal Zoning

# <codecell>

import pandas as pd
import os, sys
import arcpy
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("3D")
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM
reload(EDM)

# <markdowncell>

# ###Variables

# <codecell>

Zone_of_study = 3
Zone_calc = 3
number_of_zones = 19
database = r'c:\ArcGIS\EDM.gdb'
Scenarios = ['SQ','BAU','HEB','CAMP','UC']

# <codecell>

locationFinal = r'C:\ArcGIS\EDMdata\DataFinal\EDM'
locationtemp1 = r'c:\ArcGIS\temp'
locationAna = r'C:\ArcGIS\EDMdata\DataFinal\DEDM'

# <markdowncell>

# ###Process

# <markdowncell>

# ####Create spatiotemporal analysis.The timeseries are read, and the peaks of electricity(incl. cooling,ele), thermal cooling and thermal heating are computed. for each one, the date when the peak occurs is added.

# <codecell>

reload(EDM)
for x in Scenarios:
    for r in range (20):
        Zone = 'ZONE_'+str(r) 
        if r == Zone_of_study:
            Data = pd.read_csv(locationFinal+'\\'+x+'\\'+Zone+'\\'+'Total.csv') 
            source = x
            counter = Data.Name.count()
        else:
            Data = pd.read_csv(locationFinal+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Total.csv')
            source = 'Surroundings'
            counter = Data.Name.count()
        for row in range (counter):
            Name = Data.loc[row,'Name']
            Databuilding = pd.read_csv(locationFinal+'\\'+source+'\\'+Zone+'\\'+Name+'.csv')
            Databuilding.fillna(value=0,inplace=True)
            Databuilding['Qh'] = Databuilding['Qhsf']+Databuilding['Qwwf']+Databuilding['Qhpf']
            Databuilding['Qc'] = Databuilding['Qcpf']+Databuilding['Qcsf']+Databuilding['Qcicef']+Databuilding['Qcdataf']
            Databuilding['E'] = Databuilding['Ealf']+Databuilding['Edataf']+Databuilding['Ecaf']+Databuilding['Epf']+Databuilding['Qc']/3                
            NewFrame = pd.DataFrame(Databuilding,columns={'NAME','DATE','Qh','Qc','E'})
            NewFrame['DATE'] = pd.date_range('1/1/2010', periods=8760, freq='H')
            # days where the maximums happen in these dataseries
            newQh = NewFrame[(NewFrame['DATE']>= '2010-12-27') & (NewFrame['DATE']< '2010-12-28')] 
            newE = NewFrame[(NewFrame['DATE']>= '2010-06-28') & (NewFrame['DATE']< '2010-06-29')]
            newQc = NewFrame[(NewFrame['DATE']>= '2010-06-28') & (NewFrame['DATE']< '2010-06-29')]
            #maximums
            newEr = newE[newE['E']== newE['E'].max()]
            newQhr = newQh[newQh['Qh']== newQh['Qh'].max()]
            newQcr = newQc[newQc['Qc']== newQc['Qc'].max()]
            newEr = newEr[:1]
            newQhr = newQhr[:1]
            newQcr = newQcr[:1]
            #create row with data
            TotalE = pd.DataFrame({'E':newEr['E'],'Edate':newEr['DATE'],'NAME':newEr['NAME']})
            TotalQh = pd.DataFrame({'Qh':newQhr['Qh'],'Qhdate':newQhr['DATE'],'NAME':newQhr['NAME']})
            TotalQc = pd.DataFrame({'Qc':newQcr['Qc'],'Qcdate':newQcr['DATE'],'NAME':newQcr['NAME']})
            Total = pd.merge(TotalE,TotalQc,on='NAME')
            Total = pd.merge(Total,TotalQh,on='NAME')
            if (row == 0) & (r == 0):
                totaltemp = Total
            else:
                totaltemp = totaltemp.append(Total)
    totaltemp.reset_index(inplace=True)
    totaltemp.to_csv(locationFinal+'\\'+x+'\\'+'Datespeaks.csv',index=False)
    statzoningdatabase = r'c:\ArcGIS\Statistical zoning.gdb'
    Namedata = x+'_peakdates'
    arcpy.TableToTable_conversion(locationFinal+'\\'+x+'\\'+'Datespeaks.csv',statzoningdatabase,Namedata)
    arcpy.ConvertTimeField_management(statzoningdatabase+'\\'+Namedata,"Edate","'Not Used'","TIME_E0","TEXT","yyyy-MM-dd HH:mm:ss")
    arcpy.ConvertTimeField_management(statzoningdatabase+'\\'+Namedata,"Qhdate","'Not Used'","TIME_Qh0","TEXT","yyyy-MM-dd HH:mm:ss")
    arcpy.ConvertTimeField_management(statzoningdatabase+'\\'+Namedata,"Qcdate","'Not Used'","TIME_Qc0","TEXT","yyyy-MM-dd HH:mm:ss")

# <codecell>


