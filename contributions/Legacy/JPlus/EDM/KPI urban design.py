# -*- coding: utf-8 -*-
from __future__ import division
from EDMFunctions import YearCategoryFunction,Calc_MainUse
import math
import arcpy
import numpy as np
import pandas as pd
from pyGDsandbox.dataIO import dbf2df 



#list of inputs
Zone_of_study = 4
zone_plot_area = 118797
Scenarios = ['SQ','BAU','CAMP','HEB','UC']

#vectors where to store the results
# characteristics:
MXI = []
# diversity factors
FSI = []
LUM = []
TUM = []

#other usable vector.
N_typ = []

# Groups of uses for the analysis
Residential = ['MDU','SDU']
Working = ['ADMIN','SR', 'INDUS']
Leisure = ['REST','RESTS','DEPO','COM','EDU','CR','HEALTH','SPORT',
            'SWIM','PUBLIC','SUPER','ICE','HOT']
            
for scenario in Scenarios: 
    Database = "C:\Arcgis\EDM.gdb"
    locationtemp1 = r'c:\Arcgis\temp'
    CQ = Database+"\\"+scenario+"\\"+scenario+"Zone_"+str(Zone_of_study)
    
    #Create the table or database of the CQ to generate the values
    OutTable = 'Database.dbf'
    arcpy.TableToTable_conversion(CQ, locationtemp1, OutTable)
    Database = dbf2df(locationtemp1+'\\'+OutTable)
    
    #generate groudn floor area
    Database['GFA'] = Database.Shape_Area*Database.Floors

    # The MXI only measures the fraction of residential area over all other built uses.
    uses = ['MDU','SDU']
    area_per_use = []
    for use in uses:
        area_per_use.append((Database[use]*Database['GFA']))
    MXI.append(np.sum(area_per_use)/Database['GFA'].sum()*100)    
    
    # the FSIM measures the relation of total GFA vs the parcel area or in this case the district area. 
    # finally measures homogeoneyty based on the shanon entropy formula for N number of FSI ranges
    # claculate the plot equivalent area (PEA) per building and then the FSI per building
    all_footprints = Database.Shape_Area.sum()
    Database['PEA'] = Database.Shape_Area*zone_plot_area/all_footprints
    Database['FSI'] = Database['GFA']/Database['PEA']
    
    #calculate ranges
    nranges = 6
    FSI_ranges = [[0,0.5],[0.5,1],[1,1.5],[1.5,2],[2,2.5],[2.5,4]]
    counter = 1
    Database['cat_FSI'] = 0
    Database['num_FSI'] = 1
    buildings = Database['FSI'].count()
    for FSI_range in FSI_ranges:
        for x in range(buildings):
            if FSI_range[0] <= Database.loc[x,'FSI'] < FSI_range[1]:
                Database.loc[x,'cat_FSI'] = counter
        counter = counter +1
    FSI_categories_list = Database.groupby('cat_FSI').sum()
    N_t = nranges
    N_typ.append(N_t)
    tot = FSI_categories_list.num_FSI.sum()
    FSI.append(-sum([(i/tot)*math.log(i/tot) for i in FSI_categories_list.num_FSI])/math.log(N_t))
    
    
    # LUM measures homogeoneyty based on the shanon entropy formula for N number of uses
    residential_use = []
    working_use = []
    Leisure_use = []
    for use in Residential:
        residential_use.append((Database[use]*Database['GFA']))
    for use in Working:
        working_use.append((Database[use]*Database['GFA']))
    for use in Leisure:
        Leisure_use.append((Database[use]*Database['GFA']))  

    r = np.sum(residential_use)
    w = np.sum(working_use)
    l = np.sum(Leisure_use)
    t = r + w +l
    if r/t ==0:
        r = 0.00000000001
    if w/t ==0:
        w = 0.00000000001
    if l/t ==0:
        l = 0.00000000001
    LUM.append(-((r/t*math.log(r/t))+(w/t*math.log(w/t))+(l/t*math.log(l/t)))/math.log(3))
    
    # The TUM measures homogeoneyty based on the shanon entropy formula for N number of typologies
    Database['Type'] = Calc_MainUse(Database)
    Database['YearCat'] = Database.apply(lambda x: YearCategoryFunction(x['Year'],x['Retrofit']), axis=1)
    Database['typology'] = Database.Type + Database.YearCat
    typologies_list = Database.groupby('typology').sum()
    
    N_t = typologies_list.Shape_Area.count()
    N_typ.append(N_t)
    tot = typologies_list.Shape_Area.sum()
    TUM.append(-sum([(i/tot)*math.log(i/tot) for i in typologies_list.Shape_Area])/math.log(17))
print 'done'