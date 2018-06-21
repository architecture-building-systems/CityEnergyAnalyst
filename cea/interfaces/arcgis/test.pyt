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
        self.tools = [PlotsScenarioComparisonsTool]


class PlotsScenarioComparisonsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots-scenario-comparisons'
        self.label = 'Plots scenario comparisons'
        self.description = 'Plots comparing urban scenarios and supply system configurations'
        self.canRunInBackground = False
        self.category = 'Visualization'

    # find subfolders if scenario changes
    def updateParameters(self, parameters):
        super(PlotsScenarioComparisonsTool, self).updateParameters(parameters)
        parameters = dict_parameters(parameters)
        config = cea.config.Configuration()
        config.scenario = parameters['plots-scenario-comparisons:base-scenario'].valueAsText
        subfolders = config.sections['plots-scenario-comparisons'].parameters['scenarios'].get_folders()

        if set(subfolders) != set(parameters['plots-scenario-comparisons:scenarios'].filter.list):
            parameters['plots-scenario-comparisons:scenarios'].filter.list = subfolders
            parameters['plots-scenario-comparisons:scenarios'].value = []


