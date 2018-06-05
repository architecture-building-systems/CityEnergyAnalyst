import os
import subprocess
import tempfile

import cea.config
reload(cea.config)
import cea.inputlocator
import cea.interfaces.arcgis.arcgishelper
reload(cea.interfaces.arcgis.arcgishelper)
from cea.interfaces.arcgis.arcgishelper import *

from cea.interfaces.arcgis.modules import arcpy

class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'Testing the City Energy Analyst'
        self.alias = 'testcea'
        self.tools = [PlotsTool]


class PlotsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots'
        self.label = 'Plots'
        self.description = 'Create plots for single or gorups of buildings'
        self.canRunInBackground = False
        self.category = 'Visualization'

    def updateParameters(self, parameters):
        super(PlotsTool, self).updateParameters(parameters)
        parameters = dict_parameters(parameters)
        scenario = parameters['general:scenario'].valueAsText
        buildings = list_buildings(scenario)
        if set(buildings) != set(parameters['plots:buildings'].filter.list):
            parameters['plots:buildings'].filter.list = buildings
            parameters['plots:buildings'].value = []

        # find subfolders if scenario changes
        config = cea.config.Configuration()
        config.scenario = parameters['general:scenario'].valueAsText
        subfolders = config.sections['plots'].parameters['scenarios'].get_folders()
        if set(subfolders) != set(parameters['plots:scenarios'].filter.list):
            parameters['plots:scenarios'].filter.list = subfolders
            parameters['plots:scenarios'].value = []



