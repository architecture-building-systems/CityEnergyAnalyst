# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 7.Network layout

# <codecell>

import arcpy
import pandas as pd
import numpy as np
import networkx as nx
import itertools as it
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

def calc_edges(junctions,network,temp_folder, calc_nodes):
    # create the origin destination matrix for heating and cooling networks
    arcpy.na.MakeODCostMatrixLayer(network,"OD","Length","#","#","segments")
    arcpy.AddLocations_na("OD","Origins",junctions)
    arcpy.AddLocations_na("OD","Destinations",junctions)
    arcpy.Solve_na("OD")
    
    # Transform to dataframe and finish
    OD = calc_shptodf("OD"+'\\'+"Lines", temp_folder)
    OD.reset_index(inplace=True)

    #result taking no taking into account adjacent connections only
    newOD = OD[OD.Total_segm == 1]
    newOD.reset_index(inplace=True)
    result = range(newOD.OriginID.count())
    for x in result:
        result[x] = (newOD.loc[x,'OriginID'],newOD.loc[x,'Destinatio'],{'weight' :newOD.loc[x,'Total_Leng']})
    
    # result taking into account no adjacent entities
    result2 = range(OD.OriginID.count())
    for x in result2:
        result2[x] = (OD.loc[x,'OriginID'],OD.loc[x,'Destinatio'],{'weight' :OD.loc[x,'Total_Leng']})

    return result, result2

# <codecell>

def calc_allnodes(nodes_raw,buildings,temp_folder_DB,temp_folder):
    # create an editable copy of junctions and calculate coordinates POINT_X and POINT_Y:
    allnodes = calc_coordinates(nodes_raw)
    # Create a join with data of Generation Plants available and flows and trasnform to dataframe
    allnodes_join = calc_spatialjoin(buildings,allnodes,temp_folder_DB,temp_folder) 
    allnodes = pd.DataFrame({"Name":allnodes_join.Name,"node":allnodes_join.TARGET_FID,"flow_kgs":allnodes_join.Flow, "sink":allnodes_join.Sink, "source":allnodes_join.Plant,"X_coor":allnodes_join.POINT_X,"Y_coor":allnodes_join.POINT_Y})
    nodes = allnodes[allnodes.Name != ""]
    nodes.reindex(inplace=True)
    return allnodes, nodes

# <codecell>

# This function transforms from a layer or feature class to a dataframe
def calc_shptodf(featureclass, temp_folder):
    out_table= 'temptable.dbf'
    arcpy.TableToTable_conversion(featureclass, temp_folder ,out_table)
    result = dbf2df(temporal2+'\\'+out_table)
    return result

# <codecell>

# This function agregates x and y coordinates to a new editable copy of the feature class
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
    return result

# <codecell>

def calc_MST(edges):
    G = nx.Graph()
    G.add_edges_from(edges)
    mst = nx.minimum_spanning_edges(G,data=False) # a generator of MST edges
    result = list(mst) # make a list of the edges
    return result

# <codecell>

def calc_Short_path(edges_allnodes, edgelist_nodes):
    # calculate connections from every point to point
    G = nx.Graph()
    G.add_edges_from(edges_allnodes)
    counter = 0
    for x in edgelist_nodes:
        edge = nx.dijkstra_path(G,x[0],x[1])
        for i in range(1, len(edge)):
            edge_tuple = (edge[i-1],edge[i])
            if i == 1:
                list_tuples = [edge_tuple]
            else:
                if ((edge[i-1],edge[i]) or (edge[i],edge[i-1])) not in list_tuples:
                    list_tuples.append(edge_tuple)
        if counter == 0:
            result_edges = list_tuples
        else:
            result_edges.extend(list_tuples)
        counter = counter +1
    return result_edges

# <codecell>

def Calc_MST_coordinates(edgesfinal,allnodes,temp_folder):
    X_start= [None]*len(edgesfinal)
    Y_start= [None]*len(edgesfinal)
    X_end= [None]*len(edgesfinal)
    Y_end= [None]*len(edgesfinal)
    start = [x[0] for x in edgesfinal]
    end = [x[1] for x in edgesfinal]
    #for epanet we add J to every row
    NODE1 = ["J"+str(x[0]) for x in edgesfinal]
    NODE2 = ["J"+str(x[0]) for x in edgesfinal]
    for x in range(len(start)):
        index = allnodes[allnodes.node == start[x]].index[0]
        X_start[x] = allnodes.loc[index,"X_coor"]
        Y_start[x] = allnodes.loc[index,"Y_coor"]
        index = allnodes[allnodes.node == end[x]].index[0]
        X_end[x] = allnodes.loc[index,"X_coor"]
        Y_end[x] = allnodes.loc[index,"Y_coor"]
    pd.DataFrame({"X_start":X_start,"Y_start":Y_start,"X_end":X_end,"Y_end":Y_end, "NODE1":NODE1,"NODE2":NODE2}).to_csv(temp_folder+'\\'+'MSTtemp.csv', index=False)
    return temp_folder+'\\'+'MSTtemp.csv'

# <codecell>

def Calc_MST_graph(edges, edges_allnodes, allnodes,temp_folder,temp_folder_DB, coordinates_shp, locationFinal,Scenario, zone):
    
    # calculate edges of the minimum spanning tree
    edges_MST = calc_MST(edges)
    
    # calculate final edgest with the shortest path between connecting nodes of the MST
    edgesfinal = calc_Short_path(edges_allnodes, edges_MST)
    
    #calculate coordinates of points of the MST
    points = Calc_MST_coordinates(edgesfinal,allnodes,temp_folder)
    
    # calculate graph in arcgis of the MST.
    result = locationFinal+'\\'+Scenario+'\\'+"Zone_"+str(zone)+"MST"
    arcpy.XYToLine_management(points,result,"X_start","Y_start","X_end","Y_end","GEODESIC","#",coordinates_shp)
    
    # add fields for EPANET in Pipes
    calc_fields_pipes(result+'.shp')
    return result

# <codecell>

def calc_fields_pipes(pipes):
    arcpy.AddField_management(pipes, "DC_ID", "TEXT")
    arcpy.AddField_management(pipes, "STATUS", "TEXT")
    arcpy.AddField_management(pipes, "ROUGHNESS", "DOUBLE")
    arcpy.AddField_management(pipes, "DIAMETER", "DOUBLE")
    arcpy.AddField_management(pipes, "MINORLOSS", "DOUBLE")
    arcpy.AddField_management(pipes, "LENGTH", "DOUBLE")
    with arcpy.da.UpdateCursor(pipes,["Y_end","DC_ID","STATUS","ROUGHNESS","DIAMETER","LENGHT","SHAPE@LENGTH","MINORLOSS"]) as cursor:
        for row in cursor:
            #row[1] = "PIPE"+str(row[0])
            row[2] = "OPEN"
            row[3] = 0.0015
            row[4] = 80
            row[5] = row[6]
            row[7] = 0
            cursor.updateRow(row)

# <codecell>

def calc_fields_junctions(junctions):
    arcpy.AddField_management(pipes, "DC_ID", "TEXT")
    arcpy.AddField_management(pipes, "DEMAND", "DOUBLE")
    arcpy.AddField_management(pipes, "ELEVATION", "DOUBLE")
    arcpy.AddField_management(pipes, "PATTERN", "DOUBLE")
    arcpy.AddField_management(pipes, "RESULT_DEM", "DOUBLE")

# <codecell>

def Calc_select_buildings(zone, all_buildings,Boundaries_Zones, temp_folder_DB):
    # Selection of single zone
    Where_clausule =  ''''''+'"'+"ID"+'"'+"="+"\'"+str(zone)+"\'"+'''''' # strange writing to introduce in ArcGIS
    Single_zone = "in_memory"+"\\"+"zone"+str(zone) # location of the result of each zone
    arcpy.Select_analysis(Boundaries_Zones,Single_zone,Where_clausule) # routine

    # Selection of all buildings in that zone
    result = 'layer_'+str(zone)
    arcpy.MakeFeatureLayer_management(all_buildings_copy, result) 
    arcpy.SelectLayerByLocation_management(result, 'intersect', Single_zone,selection_type="NEW_SELECTION")
    number = int(arcpy.GetCount_management(result).getOutput(0))
    if number < 2:
        Falgcontinue = False
    else:
        Flagcontinue = True
    return result, Flagcontinue

# <codecell>

def Calc_source_sinks(buildings, locationFinal,Scenario, zone):
    # Check if there is a plant or replace with one
    source = locationFinal+'\\'+Scenario+'\\'+"Zone_"+str(zone)+"source"
    sinks = locationFinal+'\\'+Scenario+'\\'+"Zone_"+str(zone)+"sink"
    sum_array = 0
    cursor = arcpy.da.UpdateCursor(buildings, ("Plant","Flow","Sink"))
    cursor2 = arcpy.da.SearchCursor(buildings, "Flow")
    for row in cursor:
        sum_array = sum_array + row[0]
        if row[1] > 0:
            row[2] = 1
        else:
            row[2] = 0
        cursor.updateRow(row)
    if sum_array != 1:
        for row in cursor:
            if row[1] == max(cursor2):
                row[0] = 1
            else:
                row[0] = 0
            cursor.updateRow(row)
    
    arcpy.Select_analysis(buildings,source,"Plant = 1") # routine
    arcpy.Select_analysis(buildings,sinks,"Sink = 1") # routine
    
    # add fields for EPANET
    
    return source, sinks

# <headingcell level=3>

# PROCESS

# <codecell>

Scenario = Scenarios[0]
network = temporal+'\\'+'temp_ND'
junctions = temporal+'\\'+'temp_ND_Junctions'
all_buildings = temporal+'\\'+'SQheatingcost_1'

# <codecell>

Boundaries_Zones = Database+'\\'+'Boundaries'+'\\'+'Zones'

# <codecell>

# create edges for the whole networx, adjacent and not adjacent points
all_edges_a, all_edges_na = calc_edges(junctions,network,temporal2,calc_nodes = False) # [origin, destination, lenght]

# <codecell>

# create copy of buildings for work
all_buildings_copy = temporal+'\\'+'Buildings_copy'
arcpy.FeatureClassToFeatureClass_conversion(all_buildings, temporal2, 'Buildings_copy')
arcpy.AddField_management(all_buildings_copy,"Sink")

# <codecell>

zone = 4
# Extract buildings from the zone and identify if there are more than 2 buildings
buildings, Flagcontinue = Calc_select_buildings(zone, all_buildings_copy, Boundaries_Zones, temporal)

if Flagcontinue == True: 
    
    # Create files for sinks and sources directly for EPANET
    source, sinks = Calc_source_sinks(buildings, locationFinal, Scenario, zone)
    
    # Create nodes of the whole network and for buildings
    all_nodes, nodes_buildings = calc_allnodes(junctions,buildings,temporal, temporal2) #  [origin, source, sink, flow , Xcoordinate, ycoordinate ]

    # Create possible conections between buildings
    connections = [(a,b) for a in list(nodes_buildings["node"]) for b in list(nodes_buildings["node"])]
    
    # Create list of connections including length
    edges = [t for t in all_edges_na if (t[0],t[1]) in connections]
    
    # calculate graph
    MST = Calc_MST_graph(edges, all_edges_a, all_nodes, temporal2, temporal, buildings, locationFinal, Scenario, zone)
    
    
    arcpy.Delete_management("in_memory")

# <codecell>


