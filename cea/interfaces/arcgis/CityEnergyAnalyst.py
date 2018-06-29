"""
ArcGIS Toolbox for integrating the CEA with ArcGIS.

ArcGIS starts by creating an instance of Toolbox, which in turn names the tools to include in the interface.

These tools shell out to ``cli.py`` because the ArcGIS python version is old and can't be updated. Therefore
we would decouple the python version used by CEA from the ArcGIS version.

See the script ``install_toolbox.py`` for the mechanics of installing the toolbox into the ArcGIS system.
"""

import inspect

import cea.config
import cea.inputlocator
import cea.interfaces.arcgis.arcgishelper

reload(cea.interfaces.arcgis.arcgishelper)
from cea.interfaces.arcgis.arcgishelper import *

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Martin Mosteiro Romero", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

arcpy.env.overwriteOutput = True


class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [tool for tool in globals().values()
                      if inspect.isclass(tool) and issubclass(tool, CeaTool) and not tool is CeaTool]


class CreateNewProject(CeaTool):
    def __init__(self):
        self.cea_tool = 'create-new-project'
        self.label = 'New Project'
        self.description = 'Create a new project and scenario based on a zone Shapefile and terrain DEM'
        self.canRunInBackground = False
        self.category = 'Data Management'


# class CopyDefaultDatabases(CeaTool):
#     def __init__(self):
#         self.cea_tool = 'copy-default-databases'
#         self.label = 'Copy Default Databases'
#         self.description = 'Copy default databsases to scenario based on region'
#         self.category = 'Data Management'
#         self.canRunInBackground = False


class DataHelperTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'data-helper'
        self.label = 'Data helper'
        self.description = 'Query characteristics of buildings and systems from statistical data'
        self.category = 'Data Management'
        self.canRunInBackground = False


class DemandTool(CeaTool):
    """integrate the demand script with ArcGIS"""

    def __init__(self):
        self.cea_tool = 'demand'
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.category = 'Demand forecasting'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        """Override this method if you need to use a non-default ArcGIS parameter handling"""
        if parameter.name == 'buildings':
            # ignore this parameter in the ArcGIS interface
            return None
        return parameter_info


class OptimizationTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'optimization'
        self.label = 'Central supply system'
        self.description = 'Run optimization for the given scenario'
        self.category = 'Optimization'
        self.canRunInBackground = False

class Decentralized(CeaTool):
    def __init__(self):
        self.cea_tool = 'decentralized'
        self.label = 'Decentralized supply system'
        self.description = 'Run decentralized building optimization'
        self.category = 'Optimization'
        self.canRunInBackground = False

class OperationTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'emissions'
        self.label = 'District emissions'
        self.description = 'Calculate emissions and primary energy due to building, construction, operation, dismantling and induced mobility'
        self.category = 'Life cycle analysis'
        self.canRunInBackground = False


class OperationCostsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'operation-costs'
        self.label = 'Building operation costs'
        self.description = 'Calculate energy costs due to building operation'
        self.category = 'Cost analysis'
        self.canRunInBackground = False


class RetrofitPotentialTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'retrofit-potential'
        self.label = 'Building Retrofit Potential'
        self.category = 'Retrofit analysis'
        self.description = 'Select buildings according to specific criteria for retrofit'
        self.canRunInBackground = False


class SolarCollectorPanelsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'solar-collector'
        self.label = 'Solar collectors'
        self.description = 'Calculate heat production from solar collector technologies'
        self.category = 'Energy potentials'
        self.canRunInBackground = False


class PhotovoltaicThermalPanelsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'photovoltaic-thermal'
        self.label = 'Photovoltaic-thermal Panels'
        self.description = 'Calculate electricity & heat production from photovoltaic / thermal technologies'
        self.category = 'Energy potentials'
        self.canRunInBackground = False

class LakePotentialTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'lake-potential'
        self.label = 'Lake Potential'
        self.description = 'Calculate the heat extracted from the Lake'
        self.category = 'Energy potentials'
        self.canRunInBackground = False

class PhotovoltaicPanelsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'photovoltaic'
        self.label = 'Photovoltaic panels'
        self.description = 'Calculate electricity production from solar photovoltaic technologies'
        self.category = 'Energy potentials'
        self.canRunInBackground = False


class RadiationDaysimTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'radiation-daysim'
        self.label = 'Solar radiation (Daysim engine)'
        self.description = 'Use Daysim to calculate solar radiation for a scenario'
        self.category = 'Energy potentials'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        if parameter.name == 'buildings':
            return None
        else:
            return parameter_info


class SewageHeatExchanger(CeaTool):
    def __init__(self):
        self.cea_tool = 'sewage-potential'
        self.label = 'Sewage Potential'
        self.description = 'Calculate the heat extracted from the sewage heat exchanger.'
        self.canRunInBackground = False
        self.category = 'Energy potentials'


class ThermalNetworkLayout(CeaTool):
    def __init__(self):
        self.cea_tool = 'network-layout'
        self.label = 'Network layout'
        self.description = 'Create a potential layout of the network with the minimum spanning tree'
        self.canRunInBackground = False
        self.category = 'Thermal networks'


class ThermalNetworkMatrixTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'thermal-network-matrix'
        self.label = 'Thermo-hydraulic network (branched)'
        self.description = 'Solve the thermal hydraulic network'
        self.canRunInBackground = False
        self.category = 'Thermal networks'

class SupplySystemSimulationTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'supply-system-simulation'
        self.label = 'Supply system simulation'
        self.description = 'Simulate the centralized supply system with different technologies'
        self.canRunInBackground = False
        self.category = 'Supply system simulation'

    def updateParameters(self, parameters):
        super(SupplySystemSimulationTool, self).updateParameters(parameters)
        parameters = dict_parameters(parameters)
        scenario = parameters['general:scenario'].valueAsText
        buildings = list_buildings(scenario)
        if set(buildings) != set(parameters['supply-system-simulation:dc-connected-buildings'].filter.list):
            parameters['supply-system-simulation:dc-connected-buildings'].filter.list = buildings
            parameters['supply-system-simulation:dc-connected-buildings'].value = []

class PlotsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots'
        self.label = 'Plots basic'
        self.description = 'Create plots for the default energy system of an urban scenario'
        self.canRunInBackground = False
        self.category = 'Visualization'


class MulticriteriaTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'multi-criteria-analysis'
        self.label = 'Multicriteria analysis'
        self.description = 'Perform multicriteria analysis for results of optimzation of an urban scenario'
        self.canRunInBackground = False
        self.category = 'Analysis'


class PlotsOptimizationTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots-optimization'
        self.label = 'Plots optimization overview'
        self.description = 'Create plots for the results of the optimzation of an urban scenario'
        self.canRunInBackground = False
        self.category = 'Visualization'


class PlotsSupplySystemTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots-supply-system'
        self.label = 'Plots optimization detailed'
        self.description = 'Create plots for a supply system (default or optimal) of an urban scenario'
        self.canRunInBackground = False
        self.category = 'Visualization'


class PlotsScenarioComparisonsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots-scenario-comparisons'
        self.label = 'Plots comparison'
        self.description = 'Plots comparing urban scenarios and supply system configurations'
        self.canRunInBackground = False
        self.category = 'Visualization'


class HeatmapsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'heatmaps'
        self.label = 'Heatmaps'
        self.description = 'Generate maps representing hot and cold spots of energy consumption'
        self.category = 'Visualization'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        if parameter.name == 'file-to-analyze':
            parameter_info.datatype = "String"
            parameter_info.filter.list = []
        elif parameter.name == 'analysis-fields':
            parameter_info.datatype = 'String'
            parameter_info.multiValue = True
            parameter_info.parameterDependencies = ['file-to-analyze']
        return parameter_info

    def updateParameters(self, parameters):
        super(HeatmapsTool, self).updateParameters(parameters)
        parameters = dict_parameters(parameters)
        locator = cea.inputlocator.InputLocator(parameters['general:scenario'].valueAsText)
        file_names = [os.path.basename(locator.get_total_demand())]
        file_names.extend(
            [f for f in os.listdir(locator.get_lca_emissions_results_folder())
             if f.endswith('.csv')])
        file_to_analyze = parameters['heatmaps:file-to-analyze']
        if not file_to_analyze.value or file_to_analyze.value not in file_names:
            file_to_analyze.filter.list = file_names
            file_to_analyze.value = file_names[0]
        # analysis_fields
        analysis_fields = parameters['heatmaps:analysis-fields']
        if file_to_analyze.value == file_names[0]:
            file_path = locator.get_total_demand()
        else:
            file_path = os.path.join(locator.get_lca_emissions_results_folder(),
                                     file_to_analyze.value)
        import pandas as pd
        df = pd.read_csv(file_path)
        fields = df.columns.tolist()
        fields.remove('Name')
        analysis_fields.filter.list = list(fields)

    def execute(self, parameters, _):
        param_dict = dict_parameters(parameters)
        scenario = param_dict['general:scenario'].valueAsText
        file_path = param_dict['heatmaps:file-to-analyze'].valueAsText
        locator = cea.inputlocator.InputLocator(scenario)
        if file_path == os.path.basename(locator.get_total_demand()):
            file_path = locator.get_total_demand()
        else:
            file_path = os.path.join(locator.get_lca_emissions_results_folder(), file_path)
        param_dict['heatmaps:file-to-analyze'].value = file_path
        super(HeatmapsTool, self).execute(parameters, _)


class SensitivityDemandSamplesTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'sensitivity-demand-samples'
        self.label = 'Initializer'
        self.category = 'Sensitivity analysis'
        self.description = 'Create samples for sensitivity analysis'
        self.canRunInBackground = False


class SensitivityDemandSimulateTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'sensitivity-demand-simulate'
        self.label = 'Sampler'
        self.category = 'Sensitivity analysis'
        self.description = 'Simulate demand for sensitivity analysis samples'
        self.canRunInBackground = False


class SensitivityDemandAnalyzeTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'sensitivity-demand-analyze'
        self.label = 'sensitivity-demand-analyze'
        self.label = 'Analysis'
        self.category = 'Sensitivity analysis'
        self.description = 'Analyze the results in the samples folder and write them out to an Excel file.'
        self.canRunInBackground = False


class ExcelToDbfTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'excel-to-dbf'
        self.label = 'Excel to DBF'
        self.description = 'xls => dbf'
        self.canRunInBackground = False
        self.category = 'Utilities'


class DbfToExcelTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'dbf-to-excel'
        self.label = 'DBF to Excel'
        self.description = 'dbf => xls'
        self.canRunInBackground = False
        self.category = 'Utilities'


class TestTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'test'
        self.label = 'Test CEA'
        self.description = 'Run some tests on the CEA'
        self.canRunInBackground = False
        self.category = 'Utilities'
