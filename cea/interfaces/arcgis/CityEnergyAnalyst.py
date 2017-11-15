"""
ArcGIS Toolbox for integrating the CEA with ArcGIS.

ArcGIS starts by creating an instance of Toolbox, which in turn names the tools to include in the interface.

These tools shell out to ``cli.py`` because the ArcGIS python version is old and can't be updated. Therefore
we would decouple the python version used by CEA from the ArcGIS version.

See the script ``install_toolbox.py`` for the mechanics of installing the toolbox into the ArcGIS system.
"""
import os

import arcpy  # NOTE to developers: this is provided by ArcGIS after doing `cea install-toolbox`

import cea.config
import cea.inputlocator
from cea.interfaces.arcgis.arcgishelper import *

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Martin Mosteiro Romero", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# I know this is bad form, but the locator will never really change, so I'm making it global to this file
LOCATOR = cea.inputlocator.InputLocator(None)
CONFIG = cea.config.Configuration(cea.config.DEFAULT_CONFIG)


class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [OperationCostsTool, RetrofitPotentialTool, DemandTool, DataHelperTool, BenchmarkGraphsTool,
                      OperationTool, EmbodiedEnergyTool, MobilityTool, PhotovoltaicPanelsTool, SolarCollectorPanelsTool,
                      PhotovoltaicThermalPanelsTool, DemandGraphsTool, ScenarioPlotsTool, RadiationTool,
                      RadiationDaysimTool, HeatmapsTool, DbfToExcelTool, ExcelToDbfTool, ExtractReferenceCaseTool,
                      SensitivityDemandSamplesTool, SensitivityDemandSimulateTool, SensitivityDemandAnalyzeTool,
                      TestTool]


class OperationCostsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'operation-costs'
        self.label = 'Operation Costs'
        self.description = 'Calculate energy costs due to building operation'
        self.category = 'Cost Analysis'
        self.canRunInBackground = False


class RetrofitPotentialTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'retrofit-potential'
        self.label = 'Building Retrofit Potential'
        self.category = 'Retrofit Analysis'
        self.description = 'Select buildings according to specific criteria for retrofit'
        self.canRunInBackground = False


class DemandTool(CeaTool):
    """integrate the demand script with ArcGIS"""

    def __init__(self):
        self.cea_tool = 'demand'
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.category = 'Dynamic Demand Forecasting'
        self.canRunInBackground = False

class DataHelperTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'data-helper'
        self.label = 'Data helper'
        self.description = 'Query characteristics of buildings and systems from statistical data'
        self.category = 'Data Management'
        self.canRunInBackground = False


class BenchmarkGraphsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'benchmark-graphs'
        self.label = '2000W Society Benchmark'
        self.description = 'Plot life cycle primary energy demand and emissions compared to an established benchmark'
        self.category = 'Benchmarking'
        self.canRunInBackground = False


class OperationTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'emissions'
        self.label = 'LCA Operation'
        self.description = 'Calculate emissions and primary energy due to building operation'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False


class EmbodiedEnergyTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'embodied-energy'
        self.label = 'LCA Construction'
        self.description = 'Calculate the emissions and primary energy for building construction and decommissioning'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False


class MobilityTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'mobility'
        self.label = 'LCA Mobility'
        self.description = 'Calculate emissions and primary energy due to mobility'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False


class DemandGraphsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'demand-graphs'
        self.label = 'Plots'
        self.description = 'Plot demand time-series data'
        self.category = 'Dynamic Demand Forecasting'
        self.canRunInBackground = False


class ScenarioPlotsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'scenario-plots'
        self.label = 'Scenario plots'
        self.description = 'Create summary plots of scenarios in a folder'
        self.category = 'Mapping and Visualization'
        self.canRunInBackground = False


class PhotovoltaicPanelsTool(object):
    def __init__(self):
        self.label = 'Photovoltaic Panels'
        self.description = 'Calculate electricity production from solar photovoltaic technologies'
        self.category = 'Dynamic Supply Systems'
        self.canRunInBackground = False

    def getParameterInfo(self):
        config = cea.config.Configuration()
        scenario = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        scenario.value = config.scenario

        weather_name, weather_path = create_weather_parameters(config)


        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = config.solar.date_start[:4]

        panel_on_roof = arcpy.Parameter(
            displayName="Consider panels on roofs",
            name="panel_on_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_roof.value = config.solar.panel_on_roof

        panel_on_wall = arcpy.Parameter(
            displayName="Consider panels on walls",
            name="panel_on_wall",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_wall.value = config.solar.panel_on_wall

        solar_window_solstice = arcpy.Parameter(
            displayName="Desired hours of production on the winter solstice",
            name="solar_window_solstice",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        solar_window_solstice.value = config.solar.solar_window_solstice

        type_pvpanel = arcpy.Parameter(
            displayName="PV technology to use",
            name="type_pvpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_pvpanel.filter.list = ['monocrystalline', 'polycrystalline', 'amorphous']
        type_pvpanel.value = {'PV1': 'monocrystalline',
                              'PV2': 'polycrystalline',
                              'PV3': 'amorphous'}[config.solar.type_pvpanel]

        min_radiation = arcpy.Parameter(
            displayName="filtering surfaces with low radiation potential (% of the maximum radiation in the area)",
            name="min_radiation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        min_radiation.value = config.solar.min_radiation

        return [scenario, weather_name, weather_path, year, panel_on_roof, panel_on_wall, solar_window_solstice,
                type_pvpanel, min_radiation]

    def updateParameters(self, parameters):
        scenario, parameters = check_senario_exists(parameters)
        check_radiation_exists(parameters, scenario)
        update_weather_parameters(parameters)

    def updateMessages(self, parameters):
        scenario, parameters = check_senario_exists(parameters)
        check_radiation_exists(parameters, scenario)

    def execute(self, parameters, messages):
        scenario, parameters = check_senario_exists(parameters)
        weather_name = parameters['weather_name'].valueAsText
        weather_path_param = parameters['weather_path']
        if weather_name in LOCATOR.get_weather_names():
            weather_path = LOCATOR.get_weather(weather_name)
        elif weather_path_param.enabled:
            if os.path.exists(weather_path_param.valueAsText) and weather_path_param.valueAsText.endswith('.epw'):
                weather_path = weather_path_param.valueAsText
            else:
                weather_path = LOCATOR.get_default_weather()
        else:
            weather_path = LOCATOR.get_default_weather()
        year = parameters['year'].value
        panel_on_roof = parameters['panel_on_roof'].value
        panel_on_wall = parameters['panel_on_wall'].value
        solar_window_solstice = parameters['solar_window_solstice'].value
        type_pvpanel = {'monocrystalline': 'PV1',
                        'polycrystalline': 'PV2',
                        'amorphous': 'PV3'}[parameters['type_pvpanel'].value]
        min_radiation = parameters['min_radiation'].value

        date_start = str(year) + '-01-01'
        run_cli('photovoltaic', scenario=scenario, weather=weather_path,
                solar_window_solstice=solar_window_solstice, type_pvpanel=type_pvpanel, min_radiation=min_radiation,
                date_start=date_start, panel_on_roof=panel_on_roof, panel_on_wall=panel_on_wall)


class SolarCollectorPanelsTool(object):
    def __init__(self):
        self.label = 'Solar Collector Panels'
        self.description = 'Calculate heat production from solar collector technologies'
        self.category = 'Dynamic Supply Systems'
        self.canRunInBackground = False

    def getParameterInfo(self):
        config = cea.config.Configuration()

        scenario = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        scenario.value = config.scenario

        weather_name, weather_path = self.create_weather_parameters(config)

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = config.solar.date_start[:4]

        panel_on_roof = arcpy.Parameter(
            displayName="Consider panels on roofs",
            name="panel_on_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_roof.value = config.solar.panel_on_roof

        panel_on_wall = arcpy.Parameter(
            displayName="Consider panels on walls",
            name="panel_on_wall",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_wall.value = config.solar.panel_on_wall

        solar_window_solstice = arcpy.Parameter(
            displayName="Desired hours of production on the winter solstice",
            name="solar_window_solstice",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        solar_window_solstice.value = config.solar.solar_window_solstice

        type_scpanel = arcpy.Parameter(
            displayName="Solar collector technology to use",
            name="type_scpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_scpanel.filter.list = ['flat plate collectors', 'evacuated tubes']
        type_scpanel.value = {'SC1': 'flat plate collectors',
                              'SC2': 'evacuated tubes'}[config.solar.type_scpanel]

        min_radiation = arcpy.Parameter(
            displayName="filtering surfaces with low radiation potential (% of the maximum radiation in the area)",
            name="min_radiation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        min_radiation.value = config.solar.min_radiation

        return [scenario, weather_name, weather_path, year, panel_on_roof, panel_on_wall, solar_window_solstice,
                type_scpanel, min_radiation]

    def updateParameters(self, parameters):
        scenario, parameters = check_senario_exists(parameters)
        check_radiation_exists(parameters, scenario)
        update_weather_parameters(parameters)

    def updateMessages(self, parameters):
        scenario, parameters = check_senario_exists(parameters)
        check_radiation_exists(parameters, scenario)

    def execute(self, parameters, messages):
        scenario, parameters = check_senario_exists(parameters)
        weather_path = get_weather_path_from_parameters(parameters)
        year = parameters['year'].value
        panel_on_roof = parameters['panel_on_roof'].value
        panel_on_wall = parameters['panel_on_wall'].value
        solar_window_solstice = parameters['solar_window_solstice'].value
        type_scpanel = {'flat plate collectors': 'SC1',
                        'evacuated tubes': 'SC2'}[parameters['type_scpanel'].value]
        min_radiation = parameters['min_radiation'].value

        date_start = str(year) + '-01-01'

        run_cli('solar-collector', scenario=scenario, weather=weather_path,
                solar_window_solstice=solar_window_solstice, type_scpanel=type_scpanel, min_radiation=min_radiation,
                date_start=date_start, panel_on_roof=panel_on_roof, panel_on_wall=panel_on_wall)


class PhotovoltaicThermalPanelsTool(object):
    def __init__(self):
        self.label = 'PVT Panels'
        self.description = 'Calculate electricity & heat production from photovoltaic / thermal technologies'
        self.category = 'Dynamic Supply Systems'
        self.canRunInBackground = False

    def getParameterInfo(self):
        config = cea.config.Configuration()
        scenario = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        scenario.value = config.scenario

        weather_name, weather_path = create_weather_parameters(config)

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = config.solar.date_start[:4]

        panel_on_roof = arcpy.Parameter(
            displayName="Consider panels on roofs",
            name="panel_on_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_roof.value = config.solar.panel_on_roof

        panel_on_wall = arcpy.Parameter(
            displayName="Consider panels on walls",
            name="panel_on_wall",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_wall.value = config.solar.panel_on_wall

        solar_window_solstice = arcpy.Parameter(
            displayName="Desired hours of production on the winter solstice",
            name="solar_window_solstice",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        solar_window_solstice.value = config.solar.solar_window_solstice

        type_scpanel = arcpy.Parameter(
            displayName="Solar collector technology to use",
            name="type_scpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_scpanel.filter.list = ['flat plate collectors', 'evacuated tubes']
        type_scpanel.value = {'SC1': 'flat plate collectors',
                              'SC2': 'evacuated tubes'}[config.solar.type_scpanel]

        type_pvpanel = arcpy.Parameter(
            displayName="PV technology to use",
            name="type_pvpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_pvpanel.filter.list = ['monocrystalline', 'polycrystalline', 'amorphous']
        type_pvpanel.value = {'PV1': 'monocrystalline',
                              'PV2': 'polycrystalline',
                              'PV3': 'amorphous'}[config.solar.type_pvpanel]

        min_radiation = arcpy.Parameter(
            displayName="filtering surfaces with low radiation potential (% of the maximum radiation in the area)",
            name="min_radiation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        min_radiation.value = config.solar.min_radiation

        return [scenario, weather_name, weather_path, year, panel_on_roof, panel_on_wall,
                solar_window_solstice, type_pvpanel, type_scpanel, min_radiation]

    def updateParameters(self, parameters):
        scenario, parameters = check_senario_exists(parameters)
        check_radiation_exists(parameters, scenario)
        update_weather_parameters(parameters)


    def updateMessages(self, parameters):
        scenario, parameters = check_senario_exists(parameters)
        check_radiation_exists(parameters, scenario)

    def execute(self, parameters, messages):
        scenario, parameters = check_senario_exists(parameters)
        weather_name = parameters['weather_name'].valueAsText
        weather_path = parameters['weather_path'].valueAsText
        year = parameters['year'].value
        latitude = parameters['latitude'].value
        longitude = parameters['longitude'].value
        panel_on_roof = parameters['panel_on_roof'].value
        panel_on_wall = parameters['panel_on_wall'].value
        solar_window_solstice = parameters['solar_window_solstice'].value
        type_pvpanel = {'monocrystalline': 'PV1',
                        'polycrystalline': 'PV2',
                        'amorphous': 'PV3'}[parameters['type_pvpanel'].value]
        type_scpanel = {'flat plate collectors': 'SC1',
                        'evacuated tubes': 'SC2'}[parameters['type_scpanel'].value]
        min_radiation = parameters['min_radiation'].value

        date_start = str(year) + '-01-01'

        if weather_name in LOCATOR.get_weather_names():
            weather_path = LOCATOR.get_weather(weather_name)

        run_cli('solar-collector', scenario=scenario, weather=weather_path,
                solar_window_solstice=solar_window_solstice, type_scpanel=type_scpanel, type_pvpanel=type_pvpanel,
                min_radiation=min_radiation, date_start=date_start, panel_on_roof=panel_on_roof,
                panel_on_wall=panel_on_wall)


class RadiationDaysimTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'radiation-daysim'
        self.label = 'Urban solar radiation'
        self.description = 'Use Daysim to calculate solar radiation for a scenario'
        self.category = 'Renewable Energy Assessment'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        if parameter.name == 'buildings':
            return None
        else:
            return parameter_info


class RadiationTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'radiation'
        self.label = 'Solar Insolation'
        self.category = 'Renewable Energy Assessment'
        self.description = 'Create radiation file'
        self.canRunInBackground = False


class HeatmapsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'heatmaps'
        self.label = 'Heatmaps'
        self.description = 'Generate maps representing hot and cold spots of energy consumption'
        self.category = 'Mapping and Visualization'
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
        self.label = 'Create Samples'
        self.category = 'Sensitivity Analysis'
        self.description = 'Create samples for sensitivity analysis'
        self.canRunInBackground = False

class SensitivityDemandSimulateTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'sensitivity-demand-simulate'
        self.label = 'Demand Simulation'
        self.category = 'Sensitivity Analysis'
        self.description = 'Simulate demand for sensitivity analysis samples'
        self.canRunInBackground = False

class SensitivityDemandAnalyzeTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'sensitivity-demand-analyze'
        self.label = 'sensitivity-demand-analyze'
        self.label = 'Run Analysis'
        self.category = 'Sensitivity Analysis'
        self.description = 'Analyze the results in the samples folder and write them out to an Excel file.'
        self.canRunInBackground = False


class ExcelToDbfTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'excel-to-dbf'
        self.label = 'Convert Excel to DBF'
        self.description = 'xls => dbf'
        self.canRunInBackground = False
        self.category = 'Utilities'


class DbfToExcelTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'dbf-to-excel'
        self.label = 'Convert DBF to Excel'
        self.description = 'dbf => xls'
        self.canRunInBackground = False
        self.category = 'Utilities'


class ExtractReferenceCaseTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'extract-reference-case'
        self.label = 'Extract reference case'
        self.description = 'Extract sample reference case to folder'
        self.canRunInBackground = False
        self.category = 'Utilities'

class TestTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'test'
        self.label = 'Test CEA'
        self.description = 'Run some tests on the CEA'
        self.canRunInBackground = False
        self.category = 'Utilities'


