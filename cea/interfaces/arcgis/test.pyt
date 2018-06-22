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
        #self.category = 'Visualization'

    def updateParameters(self, parameters):
        super(PlotsScenarioComparisonsTool, self).updateParameters(parameters)
        on_dialog_show = not any([p.hasBeenValidated for p in parameters])
        parameters = dict_parameters(parameters)
        if not on_dialog_show:
            self.update_scenarios(parameters)

    def update_scenarios(self, parameters):
        scenarios_parameter = parameters['plots-scenario-comparisons:scenarios']
        values = []
        for s, g, i in scenarios_parameter.values:
            if not g:
                g = '<none>'
            if not i:
                i = '<none>'
            values.append([s, g, i])
        scenarios_parameter.values = values