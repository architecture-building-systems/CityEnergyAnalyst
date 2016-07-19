# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 7.Network layout
# 
# The objective of this script is to determine the potential of connecting different zones in terms of the next criteria:
#     
#     
#     - Diversity factor effects.
#     - Length of piping, number of substations, CO2 reduced if so.

# <codecell>

import arcpy
import pandas as pd
import numpy as np
arcpy.env.workspace = 'c:\ArcGIS\Network.gdb'
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")
arcpy.CheckOutExtension("Network")
import os, sys
from pyGDsandbox.dataIO import df2dbf, dbf2df 
from arcpy import Result
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import ESMFunctions as ESM

# <markdowncell>

# ###VARIABLES

# <codecell>

#list of inputs
Zone_of_study = 3
Scenarios = ['SQ','BAU','UC','CAMP','HEB'] #List of scenarios to evaluate the potentials
locationFinal = r'C:\ArcGIS\ESMdata\DataFinal\NET'

# <codecell>

#locations
Database = r'C:\ArcGIS\Network.gdb'
temporal = r'c:\ArcGIS\Network.gdb\temp' #location of temptemporal2ral files inside the database
temporal2 = r'c:\ArcGIS\temp' #location of temptemporal2ral files inside the database
epanet = r'c:\ArcGIS\temp\EPANET' #location of files for epanet modeling

# <markdowncell>

# ###Functions

# <markdowncell>

# ###Process

# <markdowncell>

# ###This first part creates the base network form pedestrian, streets and traintracks. It adds the distribution lines to every building. For this it is necesssaru the location points of the buildings with their heating, cooling loads and a binary variable to despict plants.

# <codecell>

#CREATE THE BASE NETWORK TO FIND OPTIMAL ROUTES
Scenario = Scenarios[0]
#import the locattion of the roads = pedestrian + streets + traintracks+exsitng networks
Allroads = Database+'\\'+Scenario+'\\'+Scenario+'Allroads'
#import location of points with information of buildings (Qh, Qc and Af, Plant =1 for those buildings that could be one
# and a field called ID == OBJECTID)
buidingsheat = Database+'\\'+Scenario+'\\'+Scenario+'heatingcost'
# Calculate the basenetwork for heating costumers
output = Database+'\\'+Scenario+'\\'+Scenario+'heatingnet'
basenetwork(Allroads,output,buidingsheat,temporal,"District heating")
# Calculate the basenetwork for cooling costumers
buidingscool = Database+'\\'+Scenario+'\\'+Scenario+'coolingcost'
output = Database+'\\'+Scenario+'\\'+Scenario+'coolingnet'
basenetwork(Allroads,output,buidingscool,temporal,NetworkType="District cooling")

# <markdowncell>

# ###In a second part we create optimal routes. we run the close facility in arcgis as the problem single source - multiple destination based on a central plant. then we run the geometric tracing to find the closest route withn a series of closest routes among all other costumers. then we run the minimum spanning tree.

# <codecell>

# Inputs
Scenario = Scenarios[0]
Boundaries_Zones = Database+'\\'+'Boundaries'+'\\'+'Zones'
heatingcostumers = Database+'\\'+Scenario+'\\'+Scenario+'heatingcost'
coolingcostumers = Database+'\\'+Scenario+'\\'+Scenario+'coolingcost'
NetwrokDatasetDH = Database+'\\'+Scenario+'\\'+Scenario+'HeatingNET'
NetwrokDatasetDC = Database+'\\'+Scenario+'\\'+Scenario+'CoolingNET'
OutputDH = Database+'\\'+Scenario+'\\'+Scenario+'HeatingFacilityClust'
OutputDC = Database+'\\'+Scenario+'\\'+Scenario+'coolingFacilityClust'
geomNetwrokDatasetDH = Database+'\\'+Scenario+'\\'+Scenario+'HeatingGEOM'
geomNetwrokDatasetDC = Database+'\\'+Scenario+'\\'+Scenario+'CoolingGEOM'
namedatasetDH = Scenario+'HeatingGEOM'
namedatasetDC = Scenario+'CoolingGEOM'
heatingnet = "SQheatingnet_1"
coolingnet = "SQcoolingnet_1"
OutputDHGEOM = Database+'\\'+Scenario+'\\'+Scenario+'HeatingGEOMClust'
OutputDCGEOM = Database+'\\'+Scenario+'\\'+Scenario+'coolingGEOMClust'
Kheating =  0.65 #correaltion values of geom of sample network
Kcooling =  0.72 #correaltion values of geom of sample network

#Import List of Cityquarters and Count them for iteration
OutTable = 'Boundaries_CQ.dbf'
arcpy.TableToTable_conversion(Boundaries_Zones, temporal2, OutTable)
List_Boundaries_CQ = dbf2df(temporal2+'\\'+OutTable)
Counter = List_Boundaries_CQ.ID.count()

# <codecell>

#create empty dataframe with lengths
reload(ESM)
Lenghts = pd.DataFrame(columns=['Zone','F_Method_Qh','F_Method_Qc','G_Method_Qh','G_Method_Qc','C_Method_Qh','C_Method_Qc','MST_Method_Qh','MST_Method_Qc'],index=range(Counter))

for Zone in range(7,Counter):
    Valuezone = Zone+1 # set the value or name of the City quarter
    Lenghts.loc[Zone,'Zone']= Valuezone
    #for heating costumers
    nameS = "Heatingstops"
    nameA = "Heatinganchors"
    result0 = ESM.AnchorsStops(heatingcostumers, nameS,nameA,temporal,temporal2,Boundaries_Zones,"Qh",Valuezone)
    Anchor = result0[0];Stop = result0[1]; Flagcontinue = result0[2];b =result0[3];a =result0[4]
    if Flagcontinue == 0:
        # for one to multiple
        Lenghts.loc[Zone,'C_Method_Qh'] = ESM.Networkcorrelation(a,b,Kheating)
        result = ESM.Facilitynetworkanalysis(NetwrokDatasetDH,Anchor,Stop,Valuezone,temporal,Flag="heat")
        results = result[0]
        Lenghts.loc[Zone,'F_Method_Qh']= result[1]
        # for Multiple to multiple
        geoms = ESM.Geometricalnetworkanalysis(geomNetwrokDatasetDH,Stop,heatingnet,Valuezone,"heat",namedatasetDH,temporal)
        geom = geoms[0]
        Lenghts.loc[Zone,'G_Method_Qh']= geoms[1]        
        # for MST
        edges = ESM.calc_edges(Stop,NetwrokDatasetDH,temporal2,temporal)
        Nodes = ESM.calc_nodes(Stop,temporal2)
        edgelist = ESM.calc_MST(Nodes,edges)
        MSTs = ESM.calc_MSTnetwork(NetwrokDatasetDH,Stop,edgelist,temporal,temporal2,Zone,"heat")
        MST = MSTs[0]
        Lenghts.loc[Zone,'MST_Method_Qh'] = MSTs[1]
        #creating joint files
        if Zone == 0:
            resultFinal = results
            geomFinal = geom
            MSTFinal = MST
        else:
            arcpy.Append_management(results,resultFinal)
            arcpy.Append_management(geom,geomFinal)
            arcpy.Append_management(MST,MSTFinal)
    else:
        Lenghts.loc[Zone,'F_Method_Qh']= 0
        Lenghts.loc[Zone,'G_Method_Qh']= 0
        Lenghts.loc[Zone,'C_Method_Qh']= 0
        Lenghts.loc[Zone,'MST_Method_Qh']= 0
    #for cooling costumers
    nameS = "coolinggstops"
    nameA = "coolinganchors"
    result1 = ESM.AnchorsStops(coolingcostumers, nameS,nameA,temporal,temporal2,Boundaries_Zones,"Qc",Valuezone)
    Anchor = result1[0];Stop = result1[1]; Flagcontinue = result1[2];b =result1[3];a =result1[4]
    if Flagcontinue == 0:
        Lenghts.loc[Zone,'C_Method_Qc'] = ESM.Networkcorrelation(a,b,Kcooling)
        result2 = ESM.Facilitynetworkanalysis(NetwrokDatasetDC,Anchor,Stop,Valuezone,temporal,Flag="cool")
        results2 = result2[0]
        Lenghts.loc[Zone,'F_Method_Qc']= result2[1]
        geoms2 = ESM.Geometricalnetworkanalysis(geomNetwrokDatasetDC,Stop,coolingnet,Valuezone,"cool",namedatasetDC,temporal)
        geom2 = geoms2[0]
        Lenghts.loc[Zone,'G_Method_Qc']= geoms2[1]
        # for MST
        edges2 = ESM.calc_edges(Stop,NetwrokDatasetDC,temporal2,temporal)
        Nodes2 = ESM.calc_nodes(Stop,temporal2)
        edgelist2 = ESM.calc_MST(Nodes2,edges2)
        MSTs2 = ESM.calc_MSTnetwork(NetwrokDatasetDC,Stop,edgelist2,temporal,temporal2,Zone,"cool")
        MST2 = MSTs2[0]
        Lenghts.loc[Zone,'MST_Method_Qc'] = MSTs2[1]        
        #creating joint files        
        
        if Zone == 0:
            resultFinal2 = results2
            geomFinal2 = geom2
            MSTFinal2 = MST2
        else:
            arcpy.Append_management(results2,resultFinal2)
            arcpy.Append_management(geom2,geomFinal2)
            arcpy.Append_management(MST2,MSTFinal2)
    else:        
        Lenghts.loc[Zone,'F_Method_Qc']= 0
        Lenghts.loc[Zone,'G_Method_Qc']= 0
        Lenghts.loc[Zone,'C_Method_Qc']= 0
        Lenghts.loc[Zone,'MST_Method_Qc']= 0
        
    print "Finished"+str(Valuezone)
#Lenghts.to_excel(locationFinal+'\\'+Scenario+'\\'+"NetworksLength.xls",sheet_name='Values')
arcpy.Delete_management("in_memory")

# <markdowncell>

# ###In A third part all the files are created in order to be modeled in EPANET

# <codecell>

# import file with lenghts and ID of zones
Zonesfile = pd.ExcelFile(locationFinal+'\\'+Scenario+'\\'+"NetworksLength.xls")
Zones = pd.ExcelFile.parse(Zonesfile, 'Values')
for zone in range (Zones.ID.count()):
    
    if Zones.loc[zone,'F_Method_Qh'] > 0:
    
        #for heating costumers
        pump = temporal+ "pump"+str(zone+1)
        anchor = temporal+'\\'+"Heatinganchors"+str(zone+1)
        stops = temporal+'\\'+"Heatingstops"+str(zone+1)
        network = temporal+'\\'+"MSTheat"+str(zone)
        Calc_prepareEPANET(stops,pump,anchor, network, "MST", "H", zone, 40)
        network = temporal+'\\'+"GEOM"+str(zone+1)+"heat"
        Calc_prepareEPANET(stops,pump,anchor, network, "SPMO", "H", zone, 40)
        network = temporal+'\\'+"ROUTE"+str(zone)+"heat"
        Calc_prepareEPANET(stops,pump,anchor, network, "SPSO", "H", zone, 40)
    
    if Zones.loc[zone,'F_Method_Qc'] > 0:
    
        #for cooling costumers
        pump = temporal+ "pump"+str(zone+1)
        anchor = temporal+'\\'+"coolingstops"+str(zone+1)
        stops = temporal+'\\'+"coolinganchors"+str(zone+1)
        network = temporal+'\\'+"MSTcool"+str(zone)
        Calc_prepareEPANET(stops,pump,anchor, network, "MST", "C", zone, 8)
        network = temporal+'\\'+"GEOM"+str(zone+1)+"cool"
        Calc_prepareEPANET(stops,pump,anchor, network, "SPMO", "C", zone, 8)
        network = temporal+'\\'+"ROUTE"+str(zone)+"cool"
        Calc_prepareEPANET(stops,pump,anchor, network, "SPSO", "C", zone, 8)

    

# <codecell>

arcpy.Delete_management("in_memory")

# <codecell>


