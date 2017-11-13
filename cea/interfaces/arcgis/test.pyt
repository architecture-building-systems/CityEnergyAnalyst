import os
import subprocess
import tempfile

import cea.config
import cea.inputlocator
from cea.interfaces.arcgis.arcgishelper import *
from cea.interfaces.arcgis.modules import arcpy

class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'Testing the City Energy Analyst'
        self.alias = 'testcea'
        self.tools = [OperationCostsTool]


class OperationCostsTool(object):
    def __init__(self):
        self.label = 'Operation Costs'
        self.description = 'Calculate energy costs due to building operation'
        self.category = 'Cost Analysis'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario = get_parameter_object('general', 'scenario')
        return [scenario]

    def updateParameters(self, parameters):
        scenario_path, parameters = check_senario_exists(parameters)

    def execute(self, parameters, _):
        scenario, parameters = check_senario_exists(parameters)
        run_cli('operation-costs', scenario=scenario)