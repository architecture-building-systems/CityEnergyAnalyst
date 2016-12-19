import os

import arcpy

import cea
import cea.inputlocator
import cea.plots

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class HeatmapsTool(object):
    def __init__(self):
        self.label = 'Heatmaps'
        self.description = 'Create heatmap data layers'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        path_variables = arcpy.Parameter(
            displayName="Choose the file to analyse",
            name="path_variables",
            datatype="String",
            parameterType="Required",
            direction="Input")
        path_variables.filter.list = []
        analysis_fields = arcpy.Parameter(
            displayName="Variables to analyse",
            name="analysis_fields",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        analysis_fields.filter.list = []
        analysis_fields.parameterDependencies = ['path_variables']

        return [scenario_path, path_variables, analysis_fields]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        # scenario_path
        scenario_path = parameters[0].valueAsText
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        # path_variables
        locator = cea.inputlocator.InputLocator(scenario_path)
        file_names = [os.path.basename(locator.get_total_demand())]
        file_names.extend([f for f in os.listdir(locator.get_lca_emissions_results_folder()) if f.endswith('.csv')])
        path_variables = parameters[1]
        if not path_variables.value or path_variables.value not in file_names:
            path_variables.filter.list = file_names
            path_variables.value = file_names[0]
        # analysis_fields
        analysis_fields = parameters[2]
        if path_variables.value == file_names[0]:
            file_to_analyze = locator.get_total_demand()
        else:
            file_to_analyze = os.path.join(locator.get_lca_emissions_results_folder(), path_variables.value)
        import pandas as pd
        df = pd.read_csv(file_to_analyze)
        fields = df.columns.tolist()
        fields.remove('Name')
        analysis_fields.filter.list = list(fields)
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        scenario_path = parameters[0].valueAsText
        file_to_analyze = parameters[1].valueAsText
        analysis_fields = parameters[2].valueAsText.split(';')

        import cea.inputlocator
        locator = cea.inputlocator.InputLocator(scenario_path)
        if file_to_analyze == os.path.basename(locator.get_total_demand()):
            file_to_analyze = locator.get_total_demand()
            path_results = locator.get_heatmaps_demand_folder()
        else:
            file_to_analyze = os.path.join(locator.get_lca_emissions_results_folder(), file_to_analyze)
            path_results = locator.get_heatmaps_emission_folder()
        import cea.plots.heatmaps
        reload(cea.plots.heatmaps)
        cea.plots.heatmaps.heatmaps(locator=locator, analysis_fields=analysis_fields,
                                    path_results=path_results, file_to_analyze=file_to_analyze)
        return