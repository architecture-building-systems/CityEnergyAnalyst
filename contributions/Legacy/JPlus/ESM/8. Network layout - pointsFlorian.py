# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 7.Network layout

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

# <markdowncell>

# ###Functions

# <codecell>

Scenario = Scenarios[0]
network = temporal+'\\'+'temp_ND'
junctions = temporal+'\\'+'temp_ND_Junctions'
buildings = temporal+'\\'+'SQheatingcost_1'

# <codecell>

def calc_edges(junctions,network,temp_folder):
    # create the origin destination matrix for heating and cooling networks
    arcpy.na.MakeODCostMatrixLayer(network,"OD","Length","#","#","segments")
    arcpy.AddLocations_na("OD","Origins",junctions)
    arcpy.AddLocations_na("OD","Destinations",junctions)
    arcpy.Solve_na("OD")
    
    # TRansfor to dataframe and finish
    OD = calc_shptodf("OD"+'\\'+"Lines", temp_folder)
    OD = OD[OD.Total_segm == 1]
    result = pd.DataFrame({"Pipe":range(OD.Total_segm.count()),"NodeA":OD.OriginID, "NodeB":OD.Destinatio, "Length":OD.Total_Leng})
    return result 

# <codecell>

def calc_allnodes(nodes_raw,buildings,temp_folder_DB,temp_folder):
    # create an editable copy of junctions and calculate coordinates POINT_X and POINT_Y:
    allnodes = calc_coordinates(nodes_raw)
    # Create a join with data of Generation Plants available and flows and trasnform to dataframe
    allnodes_join = calc_spatialjoin(buildings,allnodes,temp_folder_DB,temp_folder)
    
    # Select sources and sinks
    matrix = Calc_source_sinks(allnodes_join)
    result = pd.DataFrame({"Node":matrix.TARGET_FID,"Flow_kgs":matrix.Flow, "Sink":matrix.sink, "Source":matrix.Plant,"X_coor":matrix.POINT_X,"Y_coor":matrix.POINT_Y})
    return result 

# <codecell>

def Calc_source_sinks(dataframe):
    # Check if there is a plant or replace with one
    plant_flag = dataframe.Plant.sum()
    if plant_flag < 1:
        index = dataframe[dataframe.Flow == dataframe.Flow.max()].index[0]
        dataframe.loc[index,'Plant'] = 1
    # create sinks
    dataframe['sink'] = 0
    dataframe['sink'][dataframe.Flow > 0] = 1
    return dataframe

# <codecell>

# this function transforms from a layer or feature class to a dataframe
def calc_shptodf(featureclass, temp_folder):
    out_table= 'temptable.dbf'
    arcpy.TableToTable_conversion(featureclass, temp_folder ,out_table)
    result = dbf2df(temporal2+'\\'+out_table)
    return result

# <codecell>

#this function agregates x and y coordinates to a new editable copy of the feature class
def calc_coordinates(featureclass):
    # create copy
    featureclass_copy = "in_memory"+'\\'+"feature_copy"
    arcpy.FeatureClassToFeatureClass_conversion(featureclass,"in_memory","feature_copy")
    # add field with ID and fill acording to 
    arcpy.AddXY_management(featureclass_copy)
    return featureclass_copy

# <codecell>

def calc_spatialjoin(join_feature,target,temp_folder_DB,temp_folder):
    output_join = "in_memory"+'\\'+'out'
    arcpy.SpatialJoin_analysis(target, join_feature, output_join, "JOIN_ONE_TO_ONE")
    result = calc_shptodf(output_join, temp_folder)
    result.fillna(value=0, inplace=True)
    return result 

# <codecell>

edges = calc_edges(junctions,network,temporal2) # [origin, destination, lenght] 
edges.to_csv(r'C:\edges', index=False)

# <codecell>

nodes = calc_allnodes(junctions,buildings,temporal, temporal2) #  [origin, source, sink, flow , Xcoordinate, ycoordinate ]
nodes.to_csv(r'C:\nodes', index=False)

