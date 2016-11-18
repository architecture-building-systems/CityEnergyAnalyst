# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 7.Network layout

# <codecell>

import arcpy
import pandas as pd
arcpy.env.workspace = 'c:\Arcgis\Network.gdb'
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
Zone_of_study = 4
Scenarios = ['HEB'] #List of scenarios to evaluate the potentials
locationFinal = r'C:\Arcgis\ESMdata\DataFinal\NET'

# <codecell>

#locations
Database = r'C:\Arcgis\Network.gdb'
temporal = r'c:\Arcgis\Network.gdb\temp' #location of temptemporal2ral files inside the database
temporal2 = r'c:\Arcgis\temp' #location of temptemporal2ral files inside the database

# <headingcell level=3>

# PROCESS

# <codecell>

Scenario = Scenarios[0]

# <codecell>

Boundaries_Zones = Database+'\\'+'Boundaries'+'\\'+'Zones'

# <headingcell level=3>

# Calculate basenetowrks heating and cooling cases

# <codecell>

#import the locattion of the roads = pedestrian + streets + traintracks+exsitng networks
Allroads = Database+'\\'+Scenario+'\\'+Scenario+'Allroads'
#import location of points with information of buildings (flow in lps = (m_Qh0, m_Qc0), Plant = 1, Sinks (can be 0) for those buildings that could be one
# and a field called ID == OBJECTID)
buildings_area = Database+'\\'+Scenario+'\\'+Scenario+'AREA'
buildingscool = Database+'\\'+Scenario+'\\'+Scenario+'coolingcost' #buildings with cooling load (peak period)
buildingsheat = Database+'\\'+Scenario+'\\'+Scenario+'heatingcost' #buildings with heating load (Peak period)

# <codecell>

# calculate heating costumers
arcpy.Select_analysis(buildings_area,buildingsheat, "m_Qh0>0 OR Plant = 1") # routine
#calculate cooling costumers
arcpy.Select_analysis(buildings_area,buildingscool, "m_Qc0>0 OR Plant = 1") # routine

# <codecell>

# Calculate the basenetwork for heating costumers
output = Database+'\\'+Scenario+'\\'+Scenario+'heatingnet'
ESM.basenetwork(Allroads,output,buildingsheat,temporal,temporal2,"District heating",Database)

# <codecell>

# Calculate the basenetwork for cooling costumers
output = Database+'\\'+Scenario+'\\'+Scenario+'coolingnet'
ESM.basenetwork(Allroads,output,buildingscool,temporal,temporal2,"District cooling",Database)

# <headingcell level=5>

# Create network dataset in arcgis (ONly manual untill now) add a cost called segments, with a constant value 1 from-to and 2 to -from. calculate turns

# <headingcell level=4>

# Calculate for the heating case MST

# <codecell>

network = Database+'\\'+Scenario+'\\'+Scenario+'heatingND'
junctions = Database+'\\'+Scenario+'\\'+Scenario+'heatingND_Junctions'
flowname = "m_Qh0"
networkH = "DH"
# create edges for the whole networx, adjacent and not adjacent points
all_edges_a, all_edges_na = ESM.calc_edges(junctions,network,temporal2,calc_nodes = False) # [origin, destination, lenght]

# <codecell>

reload(ESM)
# Extract buildings from the zone and identify if there are more than 2 buildings
buildings, Flagcontinue = ESM.Calc_select_buildings(Zone_of_study, buildingsheat, Boundaries_Zones, temporal)
if Flagcontinue == True: 
    # Create nodes of the whole network and for buildings
    all_nodes, nodes_buildings = ESM.calc_allnodes(junctions,buildings,temporal, temporal2,flowname) #  [origin, source, sink, flow , Xcoordinate, ycoordinate ]
    # Create possible conections between buildings
    connections = [(a,b) for a in list(nodes_buildings["node"]) for b in list(nodes_buildings["node"])]
    # Create list of connections including length
    s2 = set(connections)
    edges = [t for t in all_edges_na if (t[0],t[1]) in s2]
    # calculate graph with values directly for EPANET
    ESM.Calc_MST_graph(edges, all_edges_a, all_nodes, temporal2, temporal, buildings, locationFinal, Scenario, Zone_of_study,networkH)
    arcpy.Delete_management("in_memory")

# <codecell>

# Now for all zones except the zone of interest only running scenario SQ above
# Extract buildings from the zone and identify if there are more than 2 buildings
network = Database+'\\'+Scenario+'\\'+Scenario+'heatingND'
junctions = Database+'\\'+Scenario+'\\'+Scenario+'heatingND_Junctions'
flowname = "m_Qh0"
networkC = "DH"
zones = range(1,Zone_of_study)
zones.extend(range(Zone_of_study+1, 22))
for zone in zones:  
    buildings, Flagcontinue = ESM.Calc_select_buildings(zone, buildingsheat, Boundaries_Zones, temporal)
    if Flagcontinue == True: 
        # Create nodes of the whole network and for buildings
        all_nodes, nodes_buildings = ESM.calc_allnodes(junctions,buildings,temporal, temporal2,flowname) #  [origin, source, sink, flow , Xcoordinate, ycoordinate ]
        # Create possible conections between buildings
        connections = [(a,b) for a in list(nodes_buildings["node"]) for b in list(nodes_buildings["node"])]
        # Create list of connections including length
        s2 = set(connections)
        edges = [t for t in all_edges_na if (t[0],t[1]) in s2]
        # calculate graph with values directly for EPANET
        ESM.Calc_MST_graph(edges, all_edges_a, all_nodes, temporal2, temporal, buildings, locationFinal, "Surroundings", zone,networkH)
        arcpy.Delete_management("in_memory")

# <headingcell level=4>

# Calculate for the cooling case MST

# <codecell>

network = Database+'\\'+Scenario+'\\'+Scenario+'coolingND'
junctions = Database+'\\'+Scenario+'\\'+Scenario+'coolingND_Junctions'
flowname = "m_Qc0"
networkC = "DC"
# create edges for the whole networx, adjacent and not adjacent points
all_edges_a, all_edges_na = ESM.calc_edges(junctions,network,temporal2,calc_nodes = False) # [origin, destination, lenght]

# <codecell>

# Extract buildings from the zone and identify if there are more than 2 buildings
buildings, Flagcontinue = ESM.Calc_select_buildings(Zone_of_study, buildingscool, Boundaries_Zones, temporal)
if Flagcontinue == True: 
    # Create nodes of the whole network and for buildings
    all_nodes, nodes_buildings = ESM.calc_allnodes(junctions,buildings,temporal, temporal2,flowname) #  [origin, source, sink, flow , Xcoordinate, ycoordinate ]
    # Create possible conections between buildings
    connections = [(a,b) for a in list(nodes_buildings["node"]) for b in list(nodes_buildings["node"])]
    # Create list of connections including length
    s2 = set(connections)
    edges = [t for t in all_edges_na if (t[0],t[1]) in s2]
    # calculate graph with values directly for EPANET
    ESM.Calc_MST_graph(edges, all_edges_a, all_nodes, temporal2, temporal, buildings, locationFinal, Scenario, Zone_of_study,networkC)
    arcpy.Delete_management("in_memory")

# <codecell>

# Now for all zones except the zone of interest only running scenario SQ above
# Extract buildings from the zone and identify if there are more than 2 buildings
network = Database+'\\'+Scenario+'\\'+Scenario+'coolingND'
junctions = Database+'\\'+Scenario+'\\'+Scenario+'coolingND_Junctions'
flowname = "m_Qc0"
networkC = "DC"
Scenario = "Surroundings"
zones = range(1,Zone_of_study)
zones.extend(range(Zone_of_study+1, 22))
for zone in zones:  
    buildings, Flagcontinue = ESM.Calc_select_buildings(zone, buildingscool, Boundaries_Zones, temporal)
    if Flagcontinue == True: 
        # Create nodes of the whole network and for buildings
        all_nodes, nodes_buildings = ESM.calc_allnodes(junctions,buildings,temporal, temporal2,flowname) #  [origin, source, sink, flow , Xcoordinate, ycoordinate ]
        # Create possible conections between buildings
        connections = [(a,b) for a in list(nodes_buildings["node"]) for b in list(nodes_buildings["node"])]
        # Create list of connections including length
        s2 = set(connections)
        edges = [t for t in all_edges_na if (t[0],t[1]) in s2]
        # calculate graph with values directly for EPANET
        ESM.Calc_MST_graph(edges, all_edges_a, all_nodes, temporal2, temporal, buildings, locationFinal, Scenario, zone,networkC)
        arcpy.Delete_management("in_memory")

# <headingcell level=6>

# Go to Qgis and make the first run in EPANET. this will give the directions of the flow

# <headingcell level=6>

# Calculate order of files for the optimazation routine

# <codecell>

Zone_of_study = 4
networkH = "DH"
pipes_DH = locationFinal+'\\'+Scenario+'\\'+'Zone_'+str(Zone_of_study)+'MST_'+networkH+'.shp'
ESM.Calc_orderFlowPipes(pipes_DH,networkH,locationFinal,Scenario)
source_DH = locationFinal+'\\'+Scenario+'\\'+'Zone_'+str(Zone_of_study)+'source_'+networkH+'.shp'
sinks_DH = locationFinal+'\\'+Scenario+'\\'+'Zone_'+str(Zone_of_study)+'sink_'+networkH+'.shp'
ESM.Calc_orderNodes(sinks_DH,source_DH,buildingsheat,temporal2,networkH,locationFinal,Scenario)

# <codecell>

# for the pipes, only run once.
networkC = "DC"
pipes_DC = locationFinal+'\\'+Scenario+'\\'+'Zone_'+str(Zone_of_study)+'MST_'+networkC+'.shp'
ESM.Calc_orderFlowPipes(pipes_DC,networkC,locationFinal,Scenario)
source_DC = locationFinal+'\\'+Scenario+'\\'+'Zone_'+str(Zone_of_study)+'source_'+networkC+'.shp'
sinks_DC = locationFinal+'\\'+Scenario+'\\'+'Zone_'+str(Zone_of_study)+'sink_'+networkC+'.shp'
ESM.Calc_orderNodes(sinks_DC,source_DC,buildingscool,temporal2,networkC,locationFinal,Scenario)

