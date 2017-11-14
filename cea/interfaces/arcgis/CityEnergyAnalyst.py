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


class RetrofitPotentialTool(object):
    def __init__(self):
        self.label = 'Building Retrofit Potential'
        self.category = 'Retrofit Analysis'
        self.description = 'Select buildings according to specific criteria for retrofit'
        self.canRunInBackground = False

    def getParameterInfo(self):
        config = cea.config.Configuration()

        scenario = arcpy.Parameter(displayName="Path to the scenario", name="scenario", datatype="DEFolder",
                                        parameterType="Required", direction="Input")
        scenario.value = config.scenario

        retrofit_target_year = arcpy.Parameter(displayName="Year when the retrofit will take place",
                                               name="retrofit_target_year", datatype="GPLong", parameterType="Required",
                                               direction="Input")
        retrofit_target_year.value = config.retrofit_potential.retrofit_target_year

        keep_partial_matches = arcpy.Parameter(displayName="Keep buildings partially matching the selected criteria",
                                               name="keep_partial_matches",
                                               datatype="GPBoolean", parameterType="Required", direction="Input")
        keep_partial_matches.value = config.retrofit_potential.keep_partial_matches

        name = arcpy.Parameter(displayName="Name for new scenario", name="name", datatype="String",
                               parameterType="Required", direction="Input")
        name.value = config.retrofit_potential.retrofit_scenario_name

        cb_age_threshold = arcpy.Parameter(displayName="Enable threshold age of HVAC (built / retrofitted)",
                                           name="cb_age_threshold", datatype="GPBoolean", parameterType="Required",
                                           direction="Input", category="age")
        cb_age_threshold.value = False
        cb_age_threshold.enabled = False

        age_threshold = arcpy.Parameter(displayName="threshold age of HVAC (built / retrofitted)", name="age_threshold",
                                        datatype="GPLong", parameterType="Optional", direction="Input", category="age")
        age_threshold.value = config.retrofit_potential.age_threshold
        age_threshold.enabled = False

        cb_eui_heating_threshold = arcpy.Parameter(displayName="Enable end use intensity threshold for heating",
                                                   name="cb_eui_heating_threshold", datatype="GPBoolean",
                                                   parameterType="Required", direction="Input",
                                                   category="end use intensity")
        cb_eui_heating_threshold.value = False
        cb_eui_heating_threshold.enabled = True

        eui_heating_threshold = arcpy.Parameter(displayName="End use intensity threshold for heating",
                                                name="eui_heating_threshold", datatype="GPLong",
                                                parameterType="Optional", direction="Input",
                                                category="end use intensity")
        eui_heating_threshold.value = config.retrofit_potential.eui_heating_threshold
        eui_heating_threshold.enabled = False

        cb_eui_hot_water_threshold = arcpy.Parameter(displayName="Enable end use intensity threshold for hot water",
                                                     name="cb_eui_hot_water_threshold", datatype="GPBoolean",
                                                     parameterType="Required", direction="Input",
                                                     category="end use intensity")
        cb_eui_hot_water_threshold.value = False
        cb_eui_hot_water_threshold.enabled = False

        eui_hot_water_threshold = arcpy.Parameter(displayName="End use intensity threshold for hot water",
                                                  name="eui_hot_water_threshold", datatype="GPLong",
                                                  parameterType="Optional", direction="Input",
                                                  category="end use intensity")
        eui_hot_water_threshold.value = config.retrofit_potential.eui_hot_water_threshold
        eui_hot_water_threshold.enabled = False

        cb_eui_cooling_threshold = arcpy.Parameter(displayName="Enable end use intensity threshold for cooling",
                                                   name="cb_eui_cooling_threshold", datatype="GPBoolean",
                                                   parameterType="Required", direction="Input",
                                                   category="end use intensity")
        cb_eui_cooling_threshold.value = False
        cb_eui_cooling_threshold.enabled = False

        eui_cooling_threshold = arcpy.Parameter(displayName="End use intensity threshold for cooling",
                                                name="eui_cooling_threshold", datatype="GPLong",
                                                parameterType="Optional", direction="Input",
                                                category="end use intensity")
        eui_cooling_threshold.value = config.retrofit_potential.eui_cooling_threshold
        eui_cooling_threshold.enabled = False

        cb_eui_electricity_threshold = arcpy.Parameter(displayName="Enable end use intensity threshold for electricity",
                                                       name="cb_eui_electricity_threshold", datatype="GPBoolean",
                                                       parameterType="Required", direction="Input",
                                                       category="end use intensity")
        cb_eui_electricity_threshold.value = False
        cb_eui_electricity_threshold.enabled = False

        eui_electricity_threshold = arcpy.Parameter(displayName="End use intensity threshold for electricity",
                                                    name="eui_electricity_threshold", datatype="GPLong",
                                                    parameterType="Optional", direction="Input",
                                                    category="end use intensity")
        eui_electricity_threshold.value = config.retrofit_potential.eui_electricity_threshold
        eui_electricity_threshold.enabled = False

        cb_emissions_operation_threshold = arcpy.Parameter(
            displayName="Enable threshold for emissions due to operation", name="cb_emissions_operation_threshold",
            datatype="GPBoolean", parameterType="Required", direction="Input", category="emissions")
        cb_emissions_operation_threshold.value = False
        cb_emissions_operation_threshold.enabled = False

        emissions_operation_threshold = arcpy.Parameter(displayName="Threshold for emissions due to operation",
                                                        name="emissions_operation_threshold", datatype="GPLong",
                                                        parameterType="Optional", direction="Input",
                                                        category="emissions")
        emissions_operation_threshold.value = config.retrofit_potential.emissions_operation_threshold
        emissions_operation_threshold.enabled = False

        cb_heating_costs_threshold = arcpy.Parameter(displayName="Enable threshold for heating costs",
                                                     name="cb_heating_costs_threshold", datatype="GPBoolean",
                                                     parameterType="Required", direction="Input",
                                                     category="operation costs")
        cb_heating_costs_threshold.value = False
        cb_heating_costs_threshold.enabled = False

        heating_costs_threshold = arcpy.Parameter(displayName="Threshold for heating costs",
                                                  name="heating_costs_threshold", datatype="GPLong",
                                                  parameterType="Optional", direction="Input",
                                                  category="operation costs")
        heating_costs_threshold.value = config.retrofit_potential.heating_costs_threshold
        heating_costs_threshold.enabled = False

        cb_hot_water_costs_threshold = arcpy.Parameter(displayName="Enable threshold for hot water costs",
                                                       name="cb_hot_water_costs_threshold", datatype="GPBoolean",
                                                       parameterType="Required", direction="Input",
                                                       category="operation costs")
        cb_hot_water_costs_threshold.value = False
        cb_hot_water_costs_threshold.enabled = False

        hot_water_costs_threshold = arcpy.Parameter(displayName="Threshold for hot water costs",
                                                    name="hot_water_costs_threshold", datatype="GPLong",
                                                    parameterType="Optional", direction="Input",
                                                    category="operation costs")
        hot_water_costs_threshold.value = config.retrofit_potential.hot_water_costs_threshold
        hot_water_costs_threshold.enabled = False

        cb_cooling_costs_threshold = arcpy.Parameter(displayName="Enable threshold for cooling costs",
                                                     name="cb_cooling_costs_threshold", datatype="GPBoolean",
                                                     parameterType="Required", direction="Input",
                                                     category="operation costs")
        cb_cooling_costs_threshold.value = False
        cb_cooling_costs_threshold.enabled = False

        cooling_costs_threshold = arcpy.Parameter(displayName="Threshold for cooling costs",
                                                  name="cooling_costs_threshold", datatype="GPLong",
                                                  parameterType="Optional", direction="Input",
                                                  category="operation costs")
        cooling_costs_threshold.value = config.retrofit_potential.cooling_costs_threshold
        cooling_costs_threshold.enabled = False

        cb_electricity_costs_threshold = arcpy.Parameter(displayName="Enable threshold for electricity costs",
                                                         name="cb_electricity_costs_threshold", datatype="GPBoolean",
                                                         parameterType="Required", direction="Input",
                                                         category="operation costs")
        cb_electricity_costs_threshold.value = False
        cb_electricity_costs_threshold.enabled = False

        electricity_costs_threshold = arcpy.Parameter(displayName="Threshold for electricity costs",
                                                      name="electricity_costs_threshold", datatype="GPLong",
                                                      parameterType="Optional", direction="Input",
                                                      category="operation costs")
        electricity_costs_threshold.value = config.retrofit_potential.electricity_costs_threshold
        electricity_costs_threshold.enabled = False

        cb_heating_losses_threshold = arcpy.Parameter(
            displayName="Enable threshold for HVAC system losses from heating",
            name="cb_heating_losses_threshold", datatype="GPBoolean",
            parameterType="Required", direction="Input", category="HVAC system losses")
        cb_heating_losses_threshold.value = False
        cb_heating_losses_threshold.enabled = False

        heating_losses_threshold = arcpy.Parameter(displayName="Threshold for HVAC system losses from heating",
                                                   name="heating_losses_threshold", datatype="GPLong",
                                                   parameterType="Optional", direction="Input",
                                                   category="HVAC system losses")
        heating_losses_threshold.value = config.retrofit_potential.heating_losses_threshold
        heating_losses_threshold.enabled = False

        cb_hot_water_losses_threshold = arcpy.Parameter(
            displayName="Enable threshold for HVAC system losses from hot water", name="cb_hot_water_losses_threshold",
            datatype="GPBoolean", parameterType="Required", direction="Input", category="HVAC system losses")
        cb_hot_water_losses_threshold.value = False
        cb_hot_water_losses_threshold.enabled = False

        hot_water_losses_threshold = arcpy.Parameter(displayName="Threshold for HVAC system losses from hot water",
                                                     name="hot_water_losses_threshold", datatype="GPLong",
                                                     parameterType="Optional", direction="Input",
                                                     category="HVAC system losses")
        hot_water_losses_threshold.value = config.retrofit_potential.hot_water_losses_threshold
        hot_water_losses_threshold.enabled = False

        cb_cooling_losses_threshold = arcpy.Parameter(
            displayName="Enable threshold for HVAC system losses from cooling",
            name="cb_cooling_losses_threshold", datatype="GPBoolean",
            parameterType="Required", direction="Input", category="HVAC system losses")
        cb_cooling_losses_threshold.value = False
        cb_cooling_losses_threshold.enabled = False

        cooling_losses_threshold = arcpy.Parameter(displayName="Threshold for HVAC system losses from cooling",
                                                   name="cooling_losses_threshold", datatype="GPLong",
                                                   parameterType="Optional", direction="Input",
                                                   category="HVAC system losses")
        cooling_losses_threshold.value = config.retrofit_potential.cooling_losses_threshold
        cooling_losses_threshold.enabled = False

        return [scenario, retrofit_target_year, keep_partial_matches, name, cb_age_threshold, age_threshold,
                cb_eui_heating_threshold, eui_heating_threshold, cb_eui_hot_water_threshold, eui_hot_water_threshold,
                cb_eui_cooling_threshold, eui_cooling_threshold, cb_eui_electricity_threshold,
                eui_electricity_threshold, cb_emissions_operation_threshold, emissions_operation_threshold,
                cb_heating_costs_threshold, heating_costs_threshold, cb_hot_water_costs_threshold,
                hot_water_costs_threshold, cb_cooling_costs_threshold, cooling_costs_threshold,
                cb_electricity_costs_threshold, electricity_costs_threshold, cb_heating_losses_threshold,
                heating_losses_threshold, cb_hot_water_losses_threshold, hot_water_losses_threshold,
                cb_cooling_losses_threshold, cooling_losses_threshold]

    def updateParameters(self, parameters):
        scenario, parameters = check_senario_exists(parameters)

        for parameter_name in parameters.keys():
            if parameter_name.startswith('cb_'):
                parameters[parameter_name].setErrorMessage(parameter_name[3:])
                parameters[parameter_name[3:]].enabled = parameters[parameter_name].value

    def execute(self, parameters, _):
        scenario, parameters = check_senario_exists(parameters)
        include_only_matches_to_all_criteria = parameters['include_only_matches_to_all_criteria'].value
        name = parameters['name'].valueAsText
        retrofit_target_year = parameters['retrofit_target_year'].value
        args = {
            'scenario': scenario,
            'retrofit-scenario-name': name,
            'retrofit-target-year': retrofit_target_year,
            'keep-partial-matches': include_only_matches_to_all_criteria,
            'age-threshold': parameters['age_threshold'].value if parameters['cb_age_threshold'].value else None,
            'hot-water-costs-threshold': parameters['hot_water_costs_threshold'].value if parameters['cb_hot_water_costs_threshold'].value else None,
            'emissions-operation-threshold': parameters['emissions_operation_threshold'].value if parameters['cb_emissions_operation_threshold'].value else None,
            'eui-electricity-threshold': parameters['eui_electricity_threshold'].value if parameters['cb_eui_electricity_threshold'].value else None,
            'heating-costs-threshold': parameters['heating_costs_threshold'].value if parameters['cb_heating_costs_threshold'].value else None,
            'eui-hot-water-threshold': parameters['eui_hot_water_threshold'].value if parameters['cb_eui_hot_water_threshold'].value else None,
            'electricity-costs-threshold': parameters['electricity_costs_threshold'].value if parameters['cb_electricity_costs_threshold'].value else None,
            'heating-losses-threshold': parameters['heating_losses_threshold'].value if parameters['cb_heating_losses_threshold'].value else None,
            'cooling-losses-threshold': parameters['cooling_losses_threshold'].value if parameters['cb_cooling_losses_threshold'].value else None,
            'eui-cooling-threshold': parameters['eui_cooling_threshold'].value if parameters['cb_eui_cooling_threshold'].value else None,
            'hot-water-losses-threshold': parameters['hot_water_losses_threshold'].value if parameters['cb_hot_water_losses_threshold'].value else None,
            'eui-heating-threshold': parameters['eui_heating_threshold'].value if parameters['cb_eui_heating_threshold'].value else None,
            'cooling-costs-threshold': parameters['cooling_costs_threshold'].value if parameters['cb_cooling_costs_threshold'].value else None,
        }
        run_cli('retrofit-potential', **args)


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

# Sensitivity Analysis Tools

class SensitivityDemandSamplesTool(object):
    def __init__(self):
        self.label = 'Create Samples'
        self.category = 'Sensitivity Analysis'
        self.description = 'Create samples for sensitivity analysis'
        self.canRunInBackground = False

    def getParameterInfo(self):
        method = arcpy.Parameter(
            displayName="Sampling method",
            name="method",
            datatype="String",
            parameterType="Required",
            direction="Input")
        method.filter.list = ['Morris', 'Sobol']
        method.enabled = True

        num_samples = arcpy.Parameter(
            displayName="Sample size",
            name="num_samples",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        num_samples.value = 1

        variable_groups = arcpy.Parameter(
            displayName="Groups of variables to analyze",
            name="variable_groups",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        variable_groups.filter.list = ['Envelope variables', 'Indoor comfort variables', 'Internal load variables']

        grid_jump = arcpy.Parameter(
            displayName="Grid jump size for Morris method",
            name="grid_jump",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        grid_jump.enabled = False
        grid_jump.value = 2
        grid_jump.parameterDependencies = ['method']

        num_levels = arcpy.Parameter(
            displayName="Number of grid levels for Morris method",
            name="num_levels",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        num_levels.enabled = False
        num_levels.value = 4
        num_levels.parameterDependencies = ['method']

        calc_second_order = arcpy.Parameter(
            displayName="Calculate second-order sensitivities for Sobol method",
            name="calc_second_order",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        calc_second_order.enabled = False
        calc_second_order.value = False
        calc_second_order.parameterDependencies = ['method']

        samples_folder = arcpy.Parameter(
            displayName="Folder in which samples will be saved",
            name="samples_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [method, num_samples, variable_groups, grid_jump, num_levels, calc_second_order, samples_folder]

    def updateParameters(self, parameters):
        # method
        method = parameters[0].valueAsText
        if method not in ['Morris', 'Sobol']:
            parameters[0].setErrorMessage('Invalid method %s' % parameters[0])

        # sampler parameters
        grid_jump = parameters[3]
        num_levels = parameters[4]
        calc_second_order = parameters[5]
        if method == 'Morris':
            grid_jump.enabled = True
            num_levels.enabled = True
            calc_second_order.enabled = False
        elif method == 'Sobol':
            grid_jump.enabled = False
            num_levels.enabled = False
            calc_second_order.enabled = True

        # samples folder
        samples_folder = parameters[6].valueAsText
        if samples_folder is None:
            return
        if not os.path.exists(samples_folder):
            parameters[6].setErrorMessage('Samples folder not found: %s' % samples_folder)
            return

        return

    def execute(self, parameters, _):
        method = parameters[0].valueAsText
        num_samples = int(parameters[1].valueAsText)
        # variable groups
        variables = parameters[2].values
        envelope_flag = False
        indoor_comfort_flag = False
        internal_loads_flag = False
        if 'Envelope variables' in variables:
            envelope_flag = True
        if 'Indoor comfort variables' in variables:
            indoor_comfort_flag = True
        if 'Internal load variables' in variables:
            internal_loads_flag = True

        samples_folder = parameters[6].valueAsText

        if method == 'Morris':
            method = 'morris'
            grid_jump = int(parameters[3].valueAsText)
            num_levels = int(parameters[4].valueAsText)
        elif method == 'Sobol':
            method = 'sobol'
            calc_second_order = parameters[5].value
        else:
            raise

        args = [None, 'sensitivity-demand-samples', '--method', method, '--num-samples', num_samples,
                '--samples-folder', samples_folder, '--envelope-flag', envelope_flag, '--indoor-comfort-flag',
                indoor_comfort_flag, '--internal-loads-flag', internal_loads_flag]

        if method == 'sobol':
            args.append('--calc-second-order')
            args.append(calc_second_order)
        if method == 'morris':
            args.append('--grid-jump')
            args.append(grid_jump)
            args.append('--num-levels')
            args.append(num_levels)

        run_cli(*args)

class SensitivityDemandSimulateTool(object):
    def __init__(self):
        self.label = 'Demand Simulation'
        self.category = 'Sensitivity Analysis'
        self.description = 'Simulate demand for sensitivity analysis samples'
        self.canRunInBackground = False

    def getParameterInfo(self):
        config = cea.config.Configuration()
        scenario = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name, weather_path = create_weather_parameters(config)

        samples_folder = arcpy.Parameter(
            displayName="Folder that contains the samples. The results will also be saved in this folder.",
            name="samples_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        simulation_folder = arcpy.Parameter(
            displayName="Folder to which to copy the scenario folder for simulation",
            name="simulation_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        num_simulations = arcpy.Parameter(
            displayName="Number of simulations to perform",
            name="num_simulations",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        num_simulations.value = 1
        num_simulations.parameterDependencies = ['samples_folder']
        num_simulations.enabled = False

        sample_index = arcpy.Parameter(
            displayName="Sample from which to start simulations",
            name="sample_index",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        sample_index.value = 1
        sample_index.parameterDependencies = ['samples_folder']
        sample_index.enabled = False

        output_parameters = arcpy.Parameter(
            displayName="Output parameters for sensitivity analysis",
            name="output_parameters",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        output_parameters.filter.list = sorted(['QEf_MWhyr', 'QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'Qhsf_MWhyr', 'Qcsf_MWhyr',
                                         'QEf0_kW', 'QHf0_kW', 'QCf0_kW', 'Ef0_kW', 'Qhsf0_kW', 'Qcsf0_kW'])

        return [scenario, weather_name, samples_folder, simulation_folder, num_simulations, sample_index,
                output_parameters]

    def updateParameters(self, parameters):
        import numpy as np
        scenario, parameters = check_senario_exists(parameters)

        # num_simulations, sample_index
        samples_folder = parameters[2].valueAsText
        num_simulations = parameters[4]
        sample_index = parameters[5]
        if samples_folder is None:
            return
        elif not os.path.exists(samples_folder):
            parameters[2].setErrorMessage('Samples folder not found: %s' % samples_folder)
            return
        else:
            samples_file = os.path.join(samples_folder,'samples.npy')
            if not os.path.exists(samples_file):
                parameters[2].setErrorMessage('Samples file not found in %s' % samples_folder)
                return
            else:
                if not num_simulations.enabled:
                    # only overwrite on first try
                    num_simulations.enabled = True
                    num_simulations.value = np.load(os.path.join(samples_folder,'samples.npy')).shape[0]
                    sample_index.enabled = True
                return

    def updateMessages(self, parameters):
        # scenario
        scenario, parameters = check_senario_exists(parameters)

        # samples_folder
        samples_folder = parameters[2].valueAsText
        if samples_folder is None:
            return
        if not os.path.exists(samples_folder):
            parameters[2].setErrorMessage('Samples folder not found: %s' % samples_folder)
            return
        else:
            samples_file = os.path.join(samples_folder, 'samples.npy')
            if not os.path.exists(samples_file):
                parameters[2].setErrorMessage('Samples file not found in %s' % samples_folder)
                return
            return

    def execute(self, parameters, _):
        scenario, parameters = check_senario_exists(parameters)

        # weather_path
        weather_name = parameters[1].valueAsText
        if weather_name in LOCATOR.get_weather_names():
            weather_path = LOCATOR.get_weather(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = LOCATOR.get_weather()

        # samples_folder
        samples_folder = parameters[2].valueAsText

        # simulation_folder
        simulation_folder = parameters[3].valueAsText

        # num_simulations
        num_simulations = int(parameters[4].value)

        # sample_index
        sample_index = int(parameters[5].value) - 1

        # output_parameters
        output_parameters = parameters[6].valueAsText.split(';')

        run_cli(None, 'sensitivity-demand-simulate', '--scenario-path', scenario, '--weather-path', weather_path,
                '--samples-folder', samples_folder, '--simulation-folder', simulation_folder, '--num-simulations',
                num_simulations, '--sample-index', sample_index, '--output-parameters', *output_parameters)

class SensitivityDemandAnalyzeTool(object):
    def __init__(self):
        self.label = 'Run Analysis'
        self.category = 'Sensitivity Analysis'
        self.description = 'Analyze the results in the samples folder and write them out to an Excel file.'
        self.canRunInBackground = False

    def getParameterInfo(self):

        samples_path = arcpy.Parameter(
            displayName="Folder that contains the samples created by the Create Samples tool and the results of the "
                        "Demand Simulation tool.",
            name="samples_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        temporal_scale = arcpy.Parameter(
            displayName="Temporal scale at which to do the analysis",
            name="temporal_scale",
            datatype="String",
            parameterType="Required",
            direction="Input")
        temporal_scale.filter.list = ['Yearly', 'Monthly']
        temporal_scale.enabled = True

        return [samples_path, temporal_scale]

    def updateMessages(self, parameters):
        # samples_path
        samples_path = parameters[0].valueAsText
        if samples_path is None:
            return
        elif not os.path.exists(samples_path):
            parameters[0].setErrorMessage('Samples folder not found: %s' % samples_path)
            return
        else:
            samples_file = os.path.join(samples_path, 'samples.npy')
            if not os.path.exists(samples_file):
                parameters[2].setErrorMessage('Samples file not found in %s' % samples_path)
                return
            return

        # temporal_scale
        temporal_scale = parameters[1].valueAsText
        if temporal_scale is None:
            return
        if not temporal_scale not in ['Yearly', 'Monthly']:
            parameters[1].setErrorMessage('Invalid temporal scale: %s' % temporal_scale)
            return

    def execute(self, parameters, _):

        # samples_path
        samples_path = parameters[0].valueAsText

        # temporal_scale
        temporal_scale = parameters[1].valueAsText
        if temporal_scale == 'Yearly':
            temporal_scale = 'yearly'
        else:
            temporal_scale = 'monthly'

        args = [None, 'sensitivity-demand-analyze', '--samples-path', samples_path, '--temporal-scale', temporal_scale]

        run_cli(*args)


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


class ExtractReferenceCaseTool(object):
    """Extract the built-in reference case to a specified folder"""

    def __init__(self):
        self.label = 'Extract reference case'
        self.description = 'Extract sample reference case to folder'
        self.canRunInBackground = False
        self.category = 'Utilities'

    def getParameterInfo(self):
        output_path = arcpy.Parameter(
            displayName="Extract to folder",
            name="output_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [output_path]

    def execute(self, parameters, _):
        output_path = parameters[0].valueAsText

        run_cli(None, 'extract-reference-case', '--to', output_path)


class TestTool(object):
    """Run `cea test` for the user"""

    def __init__(self):
        self.label = 'Test CEA'
        self.description = 'Run some tests on the CEA'
        self.canRunInBackground = False
        self.category = 'Utilities'

    def getParameterInfo(self):
        return []

    def execute(self,parameters, _):
        add_message('importing cea.config')
        import cea.config
        config = cea.config.Configuration()
        add_message('config.scenario = %s' % config.scenario)
        run_cli('test')


