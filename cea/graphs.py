# -*- coding: utf-8 -*-
"""
===========================
graphs algorithm
===========================
J. Fonseca  script development          18.09.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox

"""
from __future__ import division
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import os
import pandas as pd
import numpy as np
import arcpy

class GraphsDemandTool(object):

    def __init__(self):
        self.label = 'Demand Graphs'
        self.description = 'Calculate Graphs of the Demand'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_buildings = arcpy.Parameter(
            displayName="Buildings file",
            name="path_buildings",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_buildings.filter.list = ['shp']
        path_results_demand = arcpy.Parameter(
            displayName="Demand Folder Path",
            name="path_results_demand",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        path_results = arcpy.Parameter(
            displayName="Graphs Demand Results Folder Path",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")        
        return [path_buildings, path_results_demand,
                path_results]

    def execute(self, parameters, messages):
        graphs_demand(path_buildings=parameters[0].valueAsText,
                    path_results_demand=parameters[1].valueAsText,
                    path_results = parameters[2].valueAsText,
                    analysis_fields = ["Ealf", "Qhsf","Qwwf", "Qcsf"])

def graphs_demand(path_buildings, path_results_demand, path_results, analysis_fields):
    """
    algorithm to print graphs in PDF concerning the dynamics of each annd all buildings

    Parameters
    ----------
    path_buildings : string
        path to buildings file buildings.shp

    Returns
    -------
    Graphs of each building and total: .Pdf
        heat map file per variable of interest n.
    """
    # get name of files to map
    #names = []
    time = pd.date_range('1/1/2015', freq='H', periods=8760)
    color_palette = ['grey','r','y','c']
    with arcpy.da.SearchCursor(path_buildings,"Name") as cursor:
        for row in cursor:
            name = row[0]
            pathfile = path_results_demand+'\\'+name+".csv"
            if os.path.exists(pathfile):
                df = pd.read_csv(pathfile,usecols=analysis_fields)
                df.index = time 
                fig, (ax1, ax2, ax3, ax4) = plt.subplots(4,figsize=(12,16))#,dpi=4200)
                fig.text(0.07, 0.5, 'Demand [kWh]', va='center', rotation='vertical')
        
                df.plot(ax = ax1, y=analysis_fields,title='Year', color=color_palette, label=analysis_fields,legend=False)
                df[408:576].plot(ax = ax2, y=analysis_fields,title='Winter', legend=False, color=color_palette, label=analysis_fields)
                df[3096:3264].plot(ax = ax3, y=analysis_fields,title='Spring & Fall', legend=False, color=color_palette, label=analysis_fields)
                df[4102:4270].plot(ax = ax4, y=analysis_fields, title='Summer', legend=False, color=color_palette, label=analysis_fields)
                
                ax4.legend(bbox_to_anchor=(0, -0.4, 1, 0.102), loc=0, ncol=4, mode="expand", borderaxespad=0,fontsize=15)
                fig.subplots_adjust(hspace=0.7)
                
                plt.savefig(path_results+'\\'+name+".pdf")
		plt.clf()
                plt.close()
                message = 'Graph Building ' + str(name)+ ' complete'
                arcpy.AddMessage(message)
	   

def test_graph_demand():
    analysis_fields = ["Ealf", "Qhsf","Qwwf", "Qcsf"]
    path_buildings = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\101_input files\feature classes'+'\\'+'buildings.shp'  # noqa
    path_results_demand = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\demand'  # noqa
    path_results = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\graphs_demand'
    graphs_demand(path_buildings, path_results_demand, path_results, analysis_fields)

if __name__ == '__main__':
    test_graph_demand()

