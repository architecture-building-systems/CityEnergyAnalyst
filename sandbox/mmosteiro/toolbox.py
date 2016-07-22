"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.
"""
import os
import tempfile

import arcpy

import inputlocator
from cea import globalvar

reload(inputlocator)


def add_message(msg, **kwargs):
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    arcpy.AddMessage(msg % kwargs)
    log_file = os.path.join(tempfile.gettempdir(), 'cea.log')
    with open(log_file, 'a') as log:
        log.write(msg % kwargs)

class GraphsBenchmarkTool(object):
    def __init__(self):
        self.label = 'Benchmark graphs'
        self.description = 'Create benchmark plots of scenarios in a folder'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenarios = arcpy.Parameter(
            displayName="Path to the scenarios to plot",
            name="scenarios",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        output_file = arcpy.Parameter(
            displayName="Path to output PDF",
            name="output_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        output_file.filter.list = ['pdf']
        return [scenarios, output_file]

    def execute(self, parameters, messages):
        scenarios = parameters[0].valueAsText.split(';')
        output_file = parameters[1].valueAsText

        arcpy.AddMessage(scenarios)

        import cea.analysis.benchmark
        reload(cea.analysis.benchmark)
        locator_list = [inputlocator.InputLocator(scenario) for scenario in scenarios]
        cea.analysis.benchmark.benchmark(locator_list = locator_list, output_file = output_file)
        return

class MobilityTool(object):

    def __init__(self):
        self.label = 'Emissions Mobility'
        self.description = 'Calculate emissions and primary energy due to mobility'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return scenario_path

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        from sandbox.mmosteiro.mobility import lca_mobility

        scenario_path = parameters[0].valueAsText
        gv = globalvar.GlobalVariables()
        gv.log = add_message
        locator = inputlocator.InputLocator(scenario_path=scenario_path)
        lca_mobility(locator=locator, gv=gv)

