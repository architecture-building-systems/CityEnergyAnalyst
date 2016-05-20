# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ##2. Pinch Anlysis part 1.
# 
# This routine creates composite courves for all the hot and cold streams in every zone in an hourly basis. For starting. we do this with data for the Stauts Quo zone of study

# <codecell>

import pandas as pd
import numpy as np

# <codecell>

#list of inputs
Zone_of_study = 3
Scenarios = ['SQ']#,'BAU','UC','CAMP','HEB'] #List of scenarios to evaluate the potentials
location = r'C:\ArcGIS\EDMdata\DataFinal\EDM'

# <markdowncell>

# ###Functions

# <codecell>

#this function calculates the value of the CP positive hot streams negative cold streams
def calc_CP(CP,typeID):
    if typeID == 'HS':
        return abs(CP)
    else:
        return -abs(CP)

# <codecell>

def Shifted(x):
    if x[0] == 'HS':
        result = x[1]-(dTmin/2)
    else:
        result = x[1]+(dTmin/2)
    return result

# <codecell>

def calc_problemtable(hour,dataraw):
    streams = range(7)   
    #import streams and rename
    streams[0] = dataraw.loc[hour,['NAME','tshs','trhs','mcphs']]
    streams[0]['serviceID'] = 'hs'
    streams[1] = dataraw.loc[hour,['NAME','tsww','trww','mcpww']]
    streams[1]['serviceID'] = 'ww'
    streams[2] = dataraw.loc[hour,['NAME','tshp','trhp','mcphp']]
    streams[2]['serviceID'] = 'hp'
    streams[3] = dataraw.loc[hour,['NAME','tscp','trcp','mcpcp']]
    streams[3]['serviceID'] = 'cp'
    streams[4] = dataraw.loc[hour,['NAME','tscs','trcs','mcpcs']]
    streams[4]['serviceID'] = 'cs'
    streams[5] = dataraw.loc[hour,['NAME','tsice','trice','mcpice']]
    streams[5]['serviceID'] = 'ice'
    streams[6] = dataraw.loc[hour,['NAME','tsdata','trdata','mcpdata']]
    streams[6]['serviceID'] = 'data'
    for stream in range(3):
        streams[stream]['typeID'] = 'CS'
        streams[stream]['hour'] = hour
    for stream in range(3,7):
        streams[stream]['typeID'] = 'HS' 
        streams[stream]['hour'] = hour
    for stream in streams:
        stream.index = ['building','tt','ti','CP','serviceID','typeID','hour']
    
    #create clean data of streams
    data = pd.DataFrame(streams,index =range(7))
    data = data[data.CP !=0] # drop values without flow or CP values
    data['ttS'] = data[['typeID','tt']].apply(Shifted,axis=1) # add shifted temperatures
    data['tiS'] = data[['typeID','ti']].apply(Shifted,axis=1)
    data.reset_index(inplace=True,drop=True)
    
    
    #unmelt table and organize all the shifted temperatures from high to low. and restart index
    table = pd.melt(data,id_vars =['building','CP','typeID','serviceID','hour','tt','ti'],value_name='temp')
    table = table[['temp','hour','building','serviceID']]
    table.sort(column='temp',ascending = False, inplace=True)
    table.reset_index(inplace=True,drop=True)
    
    # here the table will be the final solution table
    temps = len(table)
    streams2 = len(data.CP)
    for row in range(temps-1):
        CPacum = 0
        table.loc[row,'int'] = row + 1
        table.loc[row,'i'] = table.loc[row,'temp']
        table.loc[row,'i+1'] = table.loc[row+1,'temp']
        table.loc[row,'dT'] = table.loc[row,'i'] - table.loc[row,'i+1']
        for stream in range(streams2):
            i = min(data.loc[stream,'tiS'],data.loc[stream,'ttS'])
            i1 = max(data.loc[stream,'tiS'],data.loc[stream,'ttS'])
            if  i <= table.loc[row,'i'] <= i1 and i <= table.loc[row,'i+1'] <= i1:
                CPacum = CPacum + calc_CP(data.loc[stream,'CP'],data.loc[stream,'typeID'])
        table.loc[row,'CPnet'] = CPacum
    for row in range(temps):
        table.loc[row,'dH'] = table.loc[row,'dT']*table.loc[row,'CPnet']
        if row == 0:
            table.loc[row,'dH_a'] = 0
        else:
            table.loc[row,'dH_a'] = table.loc[row-1,'dH_a'] + table.loc[row-1,'dH']

    Qcmin = table['dH_a'][1:].min()
    if Qcmin > 0:
       Qcmin = 0
    for row in range(temps):
        if row == 0:
            table.loc[row,'duty'] = abs(Qcmin)
            table.loc[row,'duty'] = round(table.loc[row,'duty'],2)
        else:
            table.loc[row,'duty'] = table.loc[row-1,'duty'] + table.loc[row-1,'dH']
            table.loc[row,'duty'] = round(table.loc[row,'duty'],2)
   
    return table

# <codecell>

#Determine the Delta min
dTmin = 5
#import all stream temperatures and create a table
zone = "Zone_3"
scenario = "SQ"
totalszone = pd.read_csv(location+'\\'+scenario+'\\'+zone+'\\'+'Total.csv') #import list with totals of the zone
buildings = totalszone.Name.count()
for row in range(9,10): #buildings
    for hour in range(0,2): #8760
        name = totalszone.loc[row,'Name']
        dataraw = pd.read_csv(location+'\\'+scenario+'\\'+zone+'\\'+name+'.csv')
        problemtable = calc_problemtable(hour,dataraw)
        
        # create problem table
        if hour == 0:
           problemtableyear = problemtable
        else:
           problemtableyear = problemtableyear.append(problemtable)

# <codecell>

from mpl_toolkits.mplot3d import Axes3D
import matplotlib
import matplotlib.pyplot as plt
import scipy

fig = plt.figure()
ax = Axes3D(fig)

x = problemtableyear[['hour']]
y = problemtableyear[['temp']]
z = problemtableyear[['duty']]
[x,y] = scipy.meshgrid(x,y)

ax.plot_surface(x,y,z)
plt.show()

# <codecell>

hour

# <codecell>


