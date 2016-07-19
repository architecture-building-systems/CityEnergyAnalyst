# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 5. AGGREGATION OF MODELS + PROCESSES + PEAKS
# ##INTRODUCTION
# 
# The objective of this script is to obtain all the heating, cooling and electricity dem calculated from the modules D-EDM, S-EDM and measured data. during this module the dynamics of processes are added to every building.
# (depending on the cluster)
# 
# the expected output is:
# 
# A file with the specific heating, cooling, electrical dem per building and cluster (Average of results in all the modules)
# A file with normalized dynamic patterns per building and cluster
# - other results area peak capacities in an excelfile
# 
# THIS ROUTINE ALSO CREATES A DATACENTER IF NECESSARY. AS AN OPTION FOR THE URBAN PLAN

# <codecell>

import pandas as pd
import numpy as np
import os, sys
import EDMFunctions as EDM

# <markdowncell>

# ###VARIABLES

# <codecell>

Zone_of_study = 1
Zone_calc = 1
number_of_zones = 1
Scenarios = ['SQ']

# <codecell>

create_datacenter = [False,False,True,False,True] # creates a datacenter in the building selected out of all the loads of the buildings
dacenter_building = ['No','No','ZW12','No','ZW11'] # ZW11 for UC cand ZW12 for HEB scenarios

# <codecell>

locationAna = r'C:\Zernez\EDMdata\DataFinal\DEDM'
locationStat =  r'C:\Zernez\EDMdata\DataFinal\SEDM'
locationMeas =  r'C:\Zernez\EDMdata\Measured'
locationEst =  r'C:\Zernez\EDMdata\Estimated'
locationFinal = r'C:\Zernez\EDMdata\DataFinal\EDM'
locationtemp1 = r'c:\Zernez\temp'

# <codecell>

# Measured Schedules
Schedules = pd.ExcelFile('C:\Zernez\EDMdata\Measured\Zone_1\SchedulesProcess.xls')
INDUS = pd.ExcelFile.parse(Schedules, 'INDUS')
# Capacities ofr equimpemnt E1: solding, E2:wavesolding, E3: lasermarking, E4: other
Capacities = [55,27,5.5,30]#the last value does not in reality matters for the calculation
# Statistical Schedules
Schedules = pd.ExcelFile('C:\Zernez\EDMdata\Statistical\Archetypes_schedules.xls')
SR = pd.ExcelFile.parse(Schedules, 'SR')
ICE = pd.ExcelFile.parse(Schedules, 'ICE')
CR = pd.ExcelFile.parse(Schedules, 'CR')

# <markdowncell>

# ###PROCESS

# <codecell>

reload(EDM)
counter = -1
for x in Scenarios:
    counter = counter + 1
    if x == 'SQ':
        r1= Zone_of_study
        r2= Zone_of_study+1
    else:
        r1= Zone_of_study
        r2 = Zone_of_study+1
    for r in range (r1,r2):
        Zone = 'Zone_'+str(r) 
        if (r) == Zone_of_study:
             Ana = locationAna+'\\'+x+'\\'+Zone
             Stat = locationStat+'\\'+x+'\\'+Zone
             Final =locationFinal+'\\'+x+'\\'+Zone
             DataCQ = pd.ExcelFile(locationStat+'\\'+x+'\\'+Zone+'\\'+'Properties.xls') # Location of the data of the CQ to run    
             CQproperties = pd.ExcelFile.parse(DataCQ, 'Values')
        else:
             Ana = locationAna+'\\'+'Surroundings'+'\\'+Zone
             Stat = locationStat+'\\'+'Surroundings'+'\\'+Zone
             Final =locationFinal+'\\'+'Surroundings'+'\\'+Zone
             DataCQ = pd.ExcelFile(locationStat+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Properties.xls') # Location of the data of the CQ to run
             CQproperties = pd.ExcelFile.parse(DataCQ, 'Values') # properties of buildings, Table with all requierements
        
        if not os.path.exists(Final):
            os.makedirs(Final)
        
        # Import files with total values in MWh of analytical and statistical models
        ValuesAna = pd.read_csv(Ana+'\\'+'Total.csv') # in MWh
        ValuesStat = pd.read_csv(Stat+'\\'+'Loads.csv') #in mWh
        
        ## Create union among both types of values
        if x == 'SQ' and (r) == Zone_of_study: # meaning that only for the SQ and the zone with measured data
            
            # Import measured data of loads and type of equipment
            # Import Estimated data of loads and type of equipment 
            #measured values
            Meas =  pd.ExcelFile(locationMeas+'\\'+Zone+'\\'+'Loads.xls')#
            ValuesMeas = pd.ExcelFile.parse(Meas, 'Values') # in MWh
            Data = pd.ExcelFile(locationMeas+'\\'+Zone+'\\'+'Equipment.xls')
            EquipmentMeas = pd.ExcelFile.parse(Data, 'Values')
            Data = pd.ExcelFile(locationMeas+'\\'+Zone+'\\'+'Properties.xls')
            PropMeas = pd.ExcelFile.parse(Data, 'Values')
            
            # Make union including measured values
            firstunion = pd.merge(ValuesAna,ValuesStat,how='inner',on='Name')
            firstunion.reindex(drop=True,inplace=True)
            Union0 = pd.merge(firstunion,ValuesMeas,how='inner',on='Name')
            Union0.reindex(drop=True,inplace=True)
            Union02 = pd.merge(Union0,EquipmentMeas,how='inner',on='Name')
            Union02.reindex(drop=True,inplace=True)
            Union = pd.merge(Union02,PropMeas,how='inner',on='Name')
            Union.reindex(drop=True,inplace=True)
            
            # Calculate average values 
            Total = EDM.Calc_Average(Union,x,Final,Ana,r,Zone_of_study)


        if x !='SQ' and (r) == Zone_of_study:
            # Import Estimated data of loads and type of equipment 
            #this is form the stat model (flags)
            Data = pd.ExcelFile(Stat+'\\'+'Equipment.xls')
            Equipment = pd.ExcelFile.parse(Data, 'Values')
            #this is from manual estimates
            Data = pd.ExcelFile(locationEst+'\\'+x+'\\'+Zone+'\\'+'Equipment.xls')
            EquipmentEst = pd.ExcelFile.parse(Data, 'Values')
            #this is from manual estimates
            Est = pd.ExcelFile(locationEst+'\\'+x+'\\'+Zone+'\\'+'Loads.xls')
            ValuesEst = pd.ExcelFile.parse(Est, 'Values')
            #this is from stat properties
            sst = pd.ExcelFile(Stat+'\\'+'Properties.xls')
            properties = pd.ExcelFile.parse(sst, 'Values')
            
            # Make union including measured values and estimated ones
            Union0 = pd.merge(ValuesAna,ValuesStat,how='inner',on='Name')
            Union0.reindex(drop=True,inplace=True)
            Union01 = pd.merge(Union0,Equipment,how='inner',on='Name')
            Union01.reindex(drop=True,inplace=True)
            Union = pd.merge(Union01,properties,how='inner',on='Name')
            Union.reindex(drop=True,inplace=True)
            
            
            # Calculate average values incl series and send to tempfolder
            Average = EDM.Calc_Average(Union,x,Final,Ana,r,Zone_of_study)
            
            # Replace values with estimates (if existent) 
            Total = EDM.calc_estimates(Average,EquipmentEst,ValuesEst)

            
        elif x == 'SQ' and (r)!= Zone_of_study:
            # Import type of equipment
            Data = pd.ExcelFile(Stat+'\\'+'Equipment.xls')
            Equipment = pd.ExcelFile.parse(Data, 'Values')
            Data2 = pd.ExcelFile(Stat+'\\'+'Properties.xls')
            properties = pd.ExcelFile.parse(Data2, 'Values')
            
            # Make union without including measured values
            Union0 = pd.merge(ValuesAna,ValuesStat,how='inner',on='Name') 
            Union0.reindex(drop=True,inplace=True)
            Union01 = pd.merge(Union0,Equipment,how='inner',on='Name')
            Union01.reindex(drop=True,inplace=True)
            Union = pd.merge(Union01,properties,how='inner',on='Name')
            Union.reindex(drop=True,inplace=True)
        
            # Calculate average values incl series and send to tempfloder
            Total = EDM.Calc_Average(Union,x,Final,Ana,r,Zone_of_study)
            
            Variables1 = ['E1','E2','E3','CA','CP','HP']
            for y in Variables1:
                Total[y] = 0  
        
        #LIST OF variables
        Variables2 = ['Qhs0','Qcs0','Qww0','E0','Qh0','Qc0']
        for y in Variables2:
            Total[y] = 0

        # Calculate series of all values including temperatures and Peaks
        for row in range (Total.Name.count()):
            Name = Total.loc[row,'Name']
            SeriesAVG = EDM.Calc_series(row,Name,Union,counter,Ana,Total,INDUS,SR,CR,ICE,Capacities,create_datacenter,dacenter_building)
            results = EDM.calc_newmass(row,Total,SeriesAVG)
            FinalSeries = results[0] 
            Total.loc[row,'mcphs0'] = results[1] # in kW/C
            Total.loc[row,'mcpcs0'] = results[2]
            Total.loc[row,'mcpww0'] = FinalSeries.mcpww.max()
            Total.loc[row,'mcpice0'] = FinalSeries.mcpice.min()
            Total.loc[row,'mcpdata0'] = FinalSeries.mcpdata.min()
            Total.loc[row,'mcphp0'] = FinalSeries.mcphp.max()
            Total.loc[row,'mcpcp0'] = FinalSeries.mcpcp.min()
            Total.loc[row,'tshs0'] = results[3]
            Total.loc[row,'trhs0'] = results[4]
            Total.loc[row,'tscs0'] = results[5]
            Total.loc[row,'trcs0'] = results[6]
            Total.loc[row,'tsww0'] = results[7]
            Total.loc[row,'tsdata0'] = FinalSeries.tsdata.max()
            Total.loc[row,'trdata0'] = FinalSeries.trdata.max()
            Total.loc[row,'Qhs0'] = SeriesAVG.Qhsf.max()
            Total.loc[row,'Qcs0'] = SeriesAVG.Qcsf.max()
            Total.loc[row,'Qww0'] = SeriesAVG.Qwwf.max()
            Total.loc[row,'E0'] = (SeriesAVG.Ealf + SeriesAVG.Epf + SeriesAVG.Ecaf + SeriesAVG.Edataf).max()
            Total.loc[row,'Qh0'] = (SeriesAVG.Qhsf + SeriesAVG.Qwwf + SeriesAVG.Qhpf).max()
            Total.loc[row,'Qc0'] = (SeriesAVG.Qcsf + SeriesAVG.Qcicef + SeriesAVG.Qcdataf + SeriesAVG.Qcpf).max()
            FinalSeries['Qhf'] = (SeriesAVG.Qhsf + SeriesAVG.Qwwf + SeriesAVG.Qhpf)
            FinalSeries['Qcf'] = (SeriesAVG.Qcsf + SeriesAVG.Qcicef + SeriesAVG.Qcdataf+ SeriesAVG.Qcpf)
            FinalSeries['Ef'] = (SeriesAVG.Ealf + SeriesAVG.Eauxf+ SeriesAVG.Epf + SeriesAVG.Ecaf + SeriesAVG.Edataf)
            Total.loc[row,'Ef'] = FinalSeries.Ef.sum()/1000
            FinalSeries.to_csv(Final+'\\'+Name+'.csv')
            print 'Complete '+' '+x+' and '+ Zone +' '+ Name
        Total.replace([np.inf, -np.inf], np.nan)
        Total.fillna(value=0,inplace=True)
        Total.to_csv(Final+'\\'+'Total.csv', index=False)
print 'Complete '

# <markdowncell>

# ###Calculation of the load values at every customer when the peak of the zone takes place

# <codecell>

counter = -1
for x in Scenarios:
    counter = counter + 1
    if x == 'SQ':
        r1= 1
        r2= number_of_zones
    else:
        r1= Zone_of_study-1
        r2 =Zone_of_study
    for r in range (r1,r2):
        Zone = 'ZONE_'+str(r+1) 
        if r == Zone_of_study:
             Final =locationFinal+'\\'+x+'\\'+Zone
        else:
             Final =locationFinal+'\\'+'Surroundings'+'\\'+Zone

        # this part reads every file with the loads of the buildings sums them up and extract the peaks
        # no process loads are taking into account because they are assumed to be taken out always as possible form 
        #the district heating
        buildings = pd.read_csv(Final+'\\'+'Total.csv')
        names = buildings.Name.count()
        for row in range(names):
            if row == 0: 
                values = pd.read_csv(Final+'\\'+buildings.loc[row,'Name']+'.csv') #Import all the values from the SeedCluster and sum-them up
                values['Qhsf'] = values['Qhsf'] + values['Qwwf'] + values['Qhpf']
                values['Qcsf'] = values['Qcsf'] + values['Qcicef'] + values['Qcdataf'] + values['Qcpf']
                values['Ealf'] = values['Ealf']+ values['Epf'] + values['Ecaf'] + values['Edataf']
            else:
                newvalues = pd.read_csv(Final+'\\'+buildings.loc[row,'Name']+'.csv')
                values['Qhsf'] = values['Qhsf'] + newvalues['Qhsf'] +  newvalues['Qwwf'] + values['Qhpf']
                values['Qcsf'] = values['Qcsf'] +  newvalues['Qcsf'] +  newvalues['Qcicef'] +  newvalues['Qcdataf'] +  newvalues['Qcpf']
                values['Ealf'] = values['Ealf'] +  newvalues['Ealf']+  newvalues['Epf'] +  newvalues['Ecaf'] +  newvalues['Edataf']
        
        # Get the hour when the peaks happen
        for hour in range(8760):
            if values.loc[hour,'Qhsf'] == values.Qhsf.max():
                hourheat = hour            
            if values.loc[hour,'Qcsf'] == values.Qcsf.max():
                hourcold = hour
            if values.loc[hour,'Ealf'] == values.Ealf.max():
                hourelec = hour
        
        # get the values at those hours
        for row in range(names):
            values = pd.read_csv(Final+'\\'+buildings.loc[row,'Name']+'.csv')
            values['Qhsf'] = values['Qhsf'] + values['Qwwf'] + values['Qhpf']
            values['Qcsf'] = values['Qcsf'] + values['Qcicef'] + values['Qcdataf'] + values['Qcpf']
            values['Ealf'] = values['Ealf']+ values['Epf'] + values['Ecaf'] + values['Edataf']            
            buildings.loc[row,'Qh0'] = values.loc[hourheat,'Qhsf']
            buildings.loc[row,'Qc0'] = values.loc[hourcold,'Qcsf']
            buildings.loc[row,'E0'] = values.loc[hourelec,'Ealf']
        
        buildings[['Name','Qh0','Qc0','E0']].to_csv(Final+'\\'+'Peakzone.csv',index=False)
    print 'Complete '+Zone 

# <codecell>

for x in Scenarios:
    for r in range (20):
        Zone = 'ZONE_'+str(r) 
        if r == Zone_of_study:
            DataCQ = pd.read_csv(locationFinal+'\\'+x+'\\'+Zone+'\\'+'Total.csv') 
            Datapeaks = pd.read_csv(locationFinal+'\\'+x+'\\'+Zone+'\\'+'Peakzone.csv')
        else:
            DataCQ = pd.read_csv(locationFinal+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Total.csv') 
            Datapeaks = pd.read_csv(locationFinal+'\\'+'Surroundings'+'\\'+Zone+'\\'+'Peakzone.csv')
        if r == 0:
            Total_temp = DataCQ
            Total_temp2 = Datapeaks
        else:
            Total_temp = Total_temp.append(DataCQ)
            Total_temp2 = Total_temp2.append(Datapeaks)
        if r == (number_of_zones-1):
            Total_temp.replace([np.inf, -np.inf], np.nan,)
            Total_temp.fillna(value=0,inplace=True)
            Total_temp = Total_temp.reset_index(drop=True)
            Total_temp.to_csv(locationFinal+'\\'+x+'\\'+'Total.csv',index=False)
            
            Total_temp2.replace([np.inf, -np.inf], np.nan,)
            Total_temp2.fillna(value=0,inplace=True)
            Total_temp2 = Total_temp2.reset_index(drop=True)
            Total_temp2.to_csv(locationFinal+'\\'+x+'\\'+'Peaksdistrict.csv',index=False)

# <codecell>


