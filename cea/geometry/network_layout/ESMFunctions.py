# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import arcpy
import pandas as pd
import numpy as np
import os, sys
sys.path.append("C:\console\sandbox")
from pyGDsandbox.dataIO import df2dbf, dbf2df 
from arcpy import Result
import networkx as nx
import math

# <codecell>

#This Routine creates the route to make the Network analysis
def basenetwork(Allroads,output,buildings,temp,temp2,NetworkType,Database):
    
    #first add distribution network to each building form the roads
    memorybuildings = temp+"\\" + "points"
    Newlines = Database+"\\" + "linesToerase"

    arcpy.FeatureClassToGeodatabase_conversion(buildings,memorybuildings)

    arcpy.Near_analysis(memorybuildings,Allroads,location=True, angle=True)
    arcpy.MakeXYEventLayer_management(memorybuildings,"Near_X","Near_Y","Line_Points_Layer")
    arcpy.FeatureClassToFeatureClass_conversion("Line_Points_Layer",temp,"Line_points")
    arcpy.Append_management(temp+'\\'+"Line_points",memorybuildings,"No_Test")
    arcpy.MakeFeatureLayer_management(memorybuildings,"POINTS_layer")
    arcpy.env.workspace = Database
    arcpy.PointsToLine_management(memorybuildings,Newlines,"ID","#","NO_CLOSE")
    arcpy.Merge_management((Allroads,Newlines),temp+"\\"+"merge") 
    arcpy.FeatureToLine_management(temp+"\\"+"merge",output)#necessary to match vertices

# <codecell>

def AnchorsStops(costumers,namestops,namesanchors,temporal,temporal2,Boundaries_Zones,Field,Value):    
    # list of variables    
    Where_clausule =  ''''''+'"'+"ID"+'"'+"="+"\'"+str(Value)+"\'"+'''''' # strange writing to introduce in ArcGIS
    # selection
    Single_zone = temporal2+"\\"+"zone"+str(Value)+'.shp' # location of the result of each CityQuarter
    arcpy.Select_analysis(Boundaries_Zones,Single_zone,Where_clausule) # routine
    with arcpy.da.SearchCursor(Single_zone,["Shape_Area"]) as cursor:
        for row in cursor:
            Area = row[0]
    # Stops
    arcpy.MakeFeatureLayer_management(costumers, 'layer') 
    arcpy.SelectLayerByLocation_management('layer', 'intersect', Single_zone,selection_type="NEW_SELECTION")
    Stops = namestops+str(Value)
    Stopsroute = temporal+"\\"+Stops
    arcpy.CopyFeatures_management('layer',Stopsroute)
    buildings = int(arcpy.GetCount_management(Stopsroute).getOutput(0))
    Anchor = temporal+"\\"+namesanchors+str(Value)
    if  buildings < 2:
        Flagcontinue = 1
    else:
        Flagcontinue =0
        counter = 0
        with arcpy.da.SearchCursor(Stopsroute,["Plant"]) as cursor:
            for row in cursor:
                if row[0] == str(1):
                    counter = counter + 1
        
        if counter >= 1: #there is a plant as an anchor load
            # list of variables    
            Where_clausule =  ''''''+'"'+"Plant"+'"'+"="+"\'"+str(1)+"\'"+'''''' # strange writing to introduce in ArcGIS
            # selection
            arcpy.Select_analysis(Stopsroute,Anchor,Where_clausule) # routine
        else:
            # Anchorloads
            condition = "(SELECT MAX("+Field+") FROM"+" "+Stops+")"
            Where_clausule =  Field+"="+str(condition)
            arcpy.Select_analysis(Stopsroute,Anchor,Where_clausule) # routine
        
    return  Anchor,Stopsroute,Flagcontinue,buildings,Area#incase no achnor loads then the zone is not analyzed

# <codecell>

def Facilitynetworkanalysis(NetwrokDatasetDH, Anchor ,Stop,Valuezone,temporal,Flag):
    Analysislayer = "Facility"+str(Valuezone)+Flag
    arcpy.MakeClosestFacilityLayer_na(NetwrokDatasetDH,Analysislayer,"Length","TRAVEL_FROM")
    arcpy.AddLocations_na(Analysislayer,"Facilities",Anchor)
    arcpy.AddLocations_na(Analysislayer,"Incidents",Stop)
    arcpy.Solve_na(Analysislayer)
    result0 = "in_memory"+'\\'+"R"+str(Valuezone)+Flag
    result = temporal+'\\'+"ROUTE"+str(Valuezone)+Flag
    arcpy.FeatureToLine_management(Analysislayer+'\\'+"Routes",result0)
    arcpy.Dissolve_management(result0,result)
    with arcpy.da.SearchCursor(result,["Shape_Length"]) as cursor:
        for row in cursor:
            Length = row[0]   
    arcpy.Delete_management("in_memory")
    return result,Length

# <codecell>

def Geometricalnetworkanalysis(geomNetwrokDataset,Stop,netname,Valuezone,Flag,namedataset,temporal):
    junctions = geomNetwrokDataset+"_Junctions"
    NEWLAYER = 'N'+str(Valuezone)+Flag
    arcpy.MakeFeatureLayer_management(junctions,  NEWLAYER) 
    arcpy.SelectLayerByLocation_management(NEWLAYER, 'intersect', Stop,selection_type="NEW_SELECTION")
    FLAGS = "F"+str(Valuezone)+Flag
    arcpy.MakeFeatureLayer_management(NEWLAYER, FLAGS)
    arcpy.TraceGeometricNetwork_management(geomNetwrokDataset,namedataset,FLAGS,"FIND_PATH","#","#","Length","Length")
    result0 = "in_memory"+'\\'+"n"+str(Valuezone)+Flag
    result = temporal+'\\'+"GEOM"+Flag+str(Valuezone)
    arcpy.FeatureToLine_management(namedataset+'\\'+netname,result0)
    arcpy.Dissolve_management(result0,result)
    with arcpy.da.SearchCursor(result,["Shape_Length"]) as cursor:
        for row in cursor:
            Length = row[0]   
    arcpy.Delete_management("in_memory")
    return result,Length

# <codecell>

def Networkcorrelation(a,b,K):
    x = a/b
    L = 2*(b-1)*K*np.sqrt(x)
    return L

# <codecell>

def calc_edges(junctions,network,temp_folder, calc_nodes):
    # create the origin destination matrix for heating and cooling networks
    arcpy.na.MakeODCostMatrixLayer(network,"OD","Length","#","#","segments")
    arcpy.AddLocations_na("OD","Origins",junctions)
    arcpy.AddLocations_na("OD","Destinations",junctions)
    arcpy.Solve_na("OD")
    
    #get results of na (non adjacent) and a (adjacent)
    result_na = []
    result_a = []
    with arcpy.da.SearchCursor("OD"+'\\'+"Lines",['OriginID','DestinationID','Total_Length','Total_segments']) as cursor:
        for row in cursor:
            edge = (row[0],row[1],{'weight' :row[2]})
            result_na.append(edge)
            if row[3] == 1.0:
                result_a.append(edge) 
    return result_a, result_na

# <codecell>

def calc_allnodes(nodes_raw,buildings,temp_folder_DB,temp_folder,flowname):
    # create an editable copy of junctions and calculate coordinates POINT_X and POINT_Y:
    allnodes = calc_coordinates(nodes_raw)
    # Create a join with data of Generation Plants available and flows and trasnform to dataframe
    allnodes_join = calc_spatialjoin(buildings,allnodes,temp_folder_DB,temp_folder) 
    allnodes = pd.DataFrame({"Name":allnodes_join.Name,"node":allnodes_join.TARGET_FID,"flow_kgs":allnodes_join[flowname], "Plant":allnodes_join.Plant,"X_coor":allnodes_join.POINT_X,"Y_coor":allnodes_join.POINT_Y})
    for j in range(allnodes.Name.count()):
        if allnodes.loc[j,"Name"] == "":
            allnodes.loc[j,"Name"] = "NA"
    nodes = allnodes[allnodes.Name != "NA"]
    nodes.reindex(inplace=True)
    return allnodes, nodes

# <codecell>

# This function transforms from a layer or feature class to a dataframe
def calc_shptodf(featureclass, temp_folder):
    out_table= 'temptable.dbf'
    arcpy.TableToTable_conversion(featureclass, temp_folder ,out_table)
    result = dbf2df(temp_folder+'\\'+out_table)
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
    result = sorted(list(mst)) # make a list of the edges
    return result

# <codecell>

def calc_Short_path(edges_allnodes, edgesMST):
    # calculate connections from every point to point
    G = nx.Graph()
    G.add_edges_from(edges_allnodes)
    counter = 0
    for x in edgesMST:
        edge = nx.dijkstra_path(G,x[0],x[1])
        for i in range(1, len(edge)):
            edge_tuple = (edge[i-1],edge[i])
            if counter == 0 and i == 1:
                result_edges = [edge_tuple]
            else:
                if ((edge[i-1],edge[i]) or (edge[i],edge[i-1])) in result_edges:
                    x = 1
                elif ((edge[i-1],edge[i]) and (edge[i],edge[i-1])) not in result_edges:
                    result_edges.append(edge_tuple)                    
        counter = counter +1
    return result_edges

# <codecell>

def Calc_MST_coordinates(edgesfinal,allnodes,temp_folder):
    X_start= [None]*len(edgesfinal)
    Name_start = [None]*len(edgesfinal)
    Name_final = [None]*len(edgesfinal)
    Y_start= [None]*len(edgesfinal)
    X_end= [None]*len(edgesfinal)
    Y_end= [None]*len(edgesfinal)
    start = [x[0] for x in edgesfinal]
    end = [x[1] for x in edgesfinal]
    flow_start = [None]*len(edgesfinal)
    Plant_start = [None]*len(edgesfinal)
    Plant_end = [None]*len(edgesfinal)
    flow_end = [None]*len(edgesfinal)
    # CREATE LINES X AND Y WITH DC_ID OF PIPES FOR EPANET
    PipeID = [None]*len(edgesfinal)
    for x in range(len(start)):
        index = allnodes[allnodes.node == start[x]].index[0]
        Name_start[x] = allnodes.loc[index,"Name"]
        X_start[x] = allnodes.loc[index,"X_coor"]
        Y_start[x] = allnodes.loc[index,"Y_coor"]
        flow_start[x] = allnodes.loc[index,"flow_kgs"]
        Plant_start[x] = allnodes.loc[index,"Plant"]
        index2 = allnodes[allnodes.node == end[x]].index[0]
        Name_final[x] = allnodes.loc[index2,"Name"]
        X_end[x] = allnodes.loc[index2,"X_coor"]
        Y_end[x] = allnodes.loc[index2,"Y_coor"]
        flow_end[x] = allnodes.loc[index2,"flow_kgs"]
        Plant_end[x] = allnodes.loc[index2,"Plant"]
    pd.DataFrame({"X_start":X_start,"Y_start":Y_start,"X_end":X_end,"Y_end":Y_end}).to_csv(temp_folder+'\\'+'MSTtemp.csv', index=False) 

    #CREATE POINTS X AND y WITH DC_ID OD JUNCTIONS FOR EPANET
    start.extend(end)
    Name_start.extend(Name_final)
    X_start.extend(X_end)
    Y_start.extend(Y_end)
    flow_start.extend(flow_end)
    Plant_start.extend(Plant_end)
    Dataframe = pd.DataFrame({"X_coor":X_start,"Y_coor":Y_start,"FID":start,"DEMAND":flow_start, "Plant":Plant_start, "Sink":0})
    Dataframe.drop_duplicates(cols="FID", inplace=True)
    Dataframe.to_csv(temp_folder+'\\'+'MSTtemp2.csv')    
    
    return temp_folder+'\\'+'MSTtemp.csv',temp_folder+'\\'+'MSTtemp2.csv'

# <codecell>

def Calc_MST_graph(edges, edges_allnodes, allnodes,temp_folder,temp_folder_DB, coordinates_shp, locationFinal,Scenario, zone, namenetwork):
    
    # calculate edges of the minimum spanning tree
    edges_MST = calc_MST(edges)
    
    # calculate final edgest with the shortest path between connecting nodes of the MST
    edgesfinal = calc_Short_path(edges_allnodes, edges_MST)
    
    #calculate coordinates of points of the MST
    lines, nodes = Calc_MST_coordinates(edgesfinal,allnodes,temp_folder)
    
    # calculate pipes from the MST
    pipes = locationFinal+'\\'+Scenario+'\\'+"Zone_"+str(zone)+"MST_"+namenetwork
    arcpy.XYToLine_management(lines,pipes,"X_start","Y_start","X_end","Y_end","GEODESIC","#",coordinates_shp)
    
    
    # calculate junctions from the MST
    junctions = temp_folder+"\\"+"Layer_XY"+str(zone)+".shp"
    arcpy.MakeXYEventLayer_management(nodes,"X_coor","Y_coor","Layer"+str(zone),coordinates_shp)
    arcpy.FeatureToPoint_management("Layer"+str(zone), junctions, "CENTROID")
    source, sinks = Calc_source_sinks(junctions, locationFinal,Scenario, zone, namenetwork)

    # add fields for EPANET in Pipes
    calc_fields_pipes(pipes+'.shp')
    
    # add fields for EPANET in sinks
    calc_fields_sinks(sinks+'.shp')
    
    # add fields for EPANET in source
    calc_fields_source(source+'.shp')

# <codecell>

def calc_fields_pipes(pipes):
    arcpy.AddField_management(pipes, "DC_ID", "TEXT")
    arcpy.AddField_management(pipes, "STATUS", "TEXT")
    arcpy.AddField_management(pipes, "ROUGHNESS", "DOUBLE")
    arcpy.AddField_management(pipes, "DIAMETER", "DOUBLE")
    arcpy.AddField_management(pipes, "MINORLOSS", "DOUBLE")
    arcpy.AddField_management(pipes, "LENGTH", "DOUBLE")
    with arcpy.da.UpdateCursor(pipes,["STATUS","ROUGHNESS","DIAMETER","LENGTH","SHAPE@LENGTH","MINORLOSS","DC_ID","FID"]) as cursor:
        for row in cursor:
            row[0] = "OPEN"
            row[1] = 0.0015
            row[2] = 80
            row[3] = row[4]
            row[5] = 0
            row[6] = "PIPE"+str(row[7])
            cursor.updateRow(row)

# <codecell>

def calc_fields_sinks(sinks): 
    arcpy.AddField_management(sinks, "ELEVATION", "DOUBLE")
    arcpy.AddField_management(sinks, "RESULT_DEM", "DOUBLE")
    with arcpy.da.UpdateCursor(sinks,["ELEVATION","DEMAND","RESULT_DEM"]) as cursor:
        for row in cursor:
            row[0] = 0
            row[2] = row[1]
            cursor.updateRow(row)    

# <codecell>

def calc_fields_source(source):
    arcpy.AddField_management(source, "HEAD", "DOUBLE")
    arcpy.AddField_management(source, "ELEVATION", "DOUBLE")
    with arcpy.da.UpdateCursor(source,["HEAD","ELEVATION"]) as cursor:
        for row in cursor:
            row[0] = 500
            row[1] = 0
            cursor.updateRow(row)  

# <codecell>

def Calc_select_buildings(zone, all_buildings,Boundaries_Zones, temp_folder_DB):
    # Selection of single zone
    Where_clausule =  ''''''+'"'+"ID"+'"'+"="+"\'"+str(zone)+"\'"+'''''' # strange writing to introduce in ArcGIS
    Single_zone = "in_memory"+"\\"+"zone"+str(zone) # location of the result of each zone
    arcpy.Select_analysis(Boundaries_Zones,Single_zone,Where_clausule) # routine

    # Selection of all buildings in that zone
    result = 'layer_'+str(zone)
    arcpy.MakeFeatureLayer_management(all_buildings, result) 
    arcpy.SelectLayerByLocation_management(result, 'intersect', Single_zone,selection_type="NEW_SELECTION")
    number = int(arcpy.GetCount_management(result).getOutput(0))
    #arcpy.CopyFeatures_management(result, temp_folder_DB+'\\'+result)
    
    if number < 2:
        Flagcontinue = False
    else:
        Flagcontinue = True
    return result, Flagcontinue

# <codecell>

def Calc_source_sinks(buildings, locationFinal,Scenario, zone,namenetwork):    
    arcpy.AddField_management(buildings, "DC_ID", "TEXT")
    with arcpy.da.UpdateCursor(buildings,["DC_ID","FID"]) as cursor:
        for row in cursor:
            row[0] = "J"+str(row[1])
            cursor.updateRow(row) 
    # Check if there is a plant or replace with one
    source = locationFinal+'\\'+Scenario+'\\'+"Zone_"+str(zone)+"source_"+namenetwork
    sinks = locationFinal+'\\'+Scenario+'\\'+"Zone_"+str(zone)+"sink_"+namenetwork
    sum_array = 0
    cursor = arcpy.da.UpdateCursor(buildings, ("Plant","DEMAND","Sink"))
    cursor2 = arcpy.da.SearchCursor(buildings, "DEMAND")
    for row in cursor:
        sum_array = sum_array + float(row[0])
        if row[1] > 0:
            row[2] = 1
        else:
            row[2] = 0
        cursor.updateRow(row)
    
    if sum_array != '1.0': # no plants then create one a point in the north of the anchor load.
        for row in cursor:
            if row[1] == max(cursor2):
                row[0] = '1.0'
            else:
                row[0] = 0
            cursor.updateRow(row)

    arcpy.Select_analysis(buildings,source, "Plant =  1.0") # routine
    arcpy.Select_analysis(buildings,sinks, "Plant =  0.0") # create sinks (it means junctions and sinks)  
    
    return source, sinks

# <codecell>

def Calc_orderFlowPipes(pipes,network,locationFinal,Scenario):
    LENGTH = []
    DC_ID = []
    NODE1 = []
    NODE2 = []
    with arcpy.da.SearchCursor(pipes,['LENGTH','NODE1','NODE2','RESULT_FLO','DC_ID']) as cursor:
        for row in cursor:
            LENGTH.append(row[0])
            DC_ID.append(row[4])
            if row[3] <0:
                NODE1.append(row[2])
                NODE2.append(row[1])
            else:
                NODE1.append(row[1])
                NODE2.append(row[2])           
    pd.DataFrame({'LENGTH':LENGTH,'NODE1':NODE1,'NODE2':NODE2,'DC_ID':DC_ID}).to_csv(locationFinal+'\\'+Scenario+'\\'+'PipesData_'+network+'.csv', index =False)

# <codecell>

def Calc_orderNodes(sinks,source,buildings,temporal2,network,locationFinal,Scenario):
    arcpy.SpatialJoin_analysis(sinks,buildings,temporal2+'\\'+'tempnodes',"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="INTERSECT")
    Plant = []
    Sink = []
    DC_ID = []
    Name = []
    with arcpy.da.SearchCursor(temporal2+'\\'+'tempnodes.shp',['Plant','Sink','DC_ID','Name']) as cursor:
        for row in cursor:
            Plant.append(row[0])
            Sink.append(row[1])  
            DC_ID.append(row[2])  
            Name.append(row[3]) 
    arcpy.SpatialJoin_analysis(source,buildings,temporal2+'\\'+'tempnodes2',"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="INTERSECT")
    with arcpy.da.SearchCursor(temporal2+'\\'+'tempnodes2.shp',['Plant','Sink','DC_ID','Name']) as cursor:        
        for row in cursor:
           Plant.append(row[0])
           Sink.append(row[1])
           DC_ID.append(row[2])     
           Name.append(row[3])      
    pd.DataFrame({'Plant':Plant,'Sink':Sink,'DC_ID':DC_ID,'Name':Name}).to_csv(locationFinal+'\\'+Scenario+'\\'+'NodesData_'+network+'.csv', index =False)

# <codecell>

def calc_Sewagetemperature(Qwwf,Qww,tsww,trww,totwater,mcpww,cp,SW_ratio):
    if Qwwf > 0:
        Qloss_to_spur = Qwwf - Qww
        t_spur = tsww - Qloss_to_spur/mcpww
        m_DHW = mcpww*SW_ratio # in kWh/c
        m_FW = totwater*SW_ratio*0.5*cp/3.6 # in kWh/c
        mcp_combi = m_DHW+m_FW
        t_combi = (m_DHW*t_spur+m_FW*trww)/mcp_combi
        t_to_sewage = t_combi-t_combi*0.10 #assuming 10% thermal loss throuhg piping
    else:
        t_to_sewage = trww
        mcp_combi = totwater*SW_ratio*0.5*cp/3.6 #in kW/C
    return mcp_combi, t_to_sewage # in lh or kgh and in C

# <codecell>

def calc_sewageheat(mcp,tin,w_HEX,Vf,cp,h0,min_m,L_HEX,tmin,AT_HEX,ATmin):
    mcp_min = min_m*cp # in kW/C
    mcp_max = Vf*w_HEX*0.20*1000*cp# 20 cm is considered as the exchange zone
    A_HEX = w_HEX*L_HEX
    if mcp > mcp_max:
        mcp = mcp_max
    if mcp_min < mcp <= mcp_max:
        mcpa = mcp*1.1 # the flow in the heatpumps slightly above the 
        # B is the sewage, A is the heatpump
        tb1 = tin
        ta1 = tin-((tin-tmin)+ATmin/2)
        alpha = h0*A_HEX*(1/mcpa-1/mcp)
        n = (1-math.exp(-alpha))/(1-mcpa/mcp*math.exp(-alpha))
        tb2 = tb1 + mcpa/mcp*n*(ta1-tb1)
        Q_source= mcp*(tb1-tb2)
        ta2 = ta1 + Q_source/mcpa
        t_source =  (tb2+tb1)
    else:
        tb1 = tin
        tb2 = tin
        ta1 = tin
        ta2 = tin
        Q_source = 0
        t_source =  tin
    return Q_source,t_source, tb2, ta1, ta2

# <codecell>


