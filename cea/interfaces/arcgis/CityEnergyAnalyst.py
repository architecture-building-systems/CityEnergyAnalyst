"""
ArcGIS Toolbox for integrating the CEA with ArcGIS.

ArcGIS starts by creating an instance of Toolbox, which in turn names the tools to include in the interface.

These tools shell out to ``cli.py`` because the ArcGIS python version is old and can't be updated. Therefore
we would decouple the python version used by CEA from the ArcGIS version.

See the script ``install_toolbox.py`` for the mechanics of installing the toolbox into the ArcGIS system.
"""
import os   
import subprocess
import tempfile
import arcpy  # NOTE to developers: this is provided by ArcGIS after doing `cea install-toolbox`

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Martin Mosteiro Romero", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [OperationCostsTool, RetrofitPotentialTool, DemandTool, DataHelperTool, BenchmarkGraphsTool,
                      OperationTool, EmbodiedTool, MobilityTool, PhotovoltaicPannelsTool, SolarCollectorPanelsTool,
                      PhotovoltaicThermalPanelsTool, DemandGraphsTool, ScenarioPlotsTool, RadiationTool,
                      RadiationDaysimTool, HeatmapsTool, DbfToExcelTool, ExcelToDbfTool, ExtractReferenceCaseTool,
                      SensitivityDemandSamplesTool, SensitivityDemandSimulateTool, SensitivityDemandAnalyzeTool,
                      TestTool]


class OperationCostsTool(object):
    def __init__(self):
        self.label = 'Operation Costs'
        self.description = 'Calculate energy costs due to building operation'
        self.category = 'Cost Analysis'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [scenario_path]

    def execute(self, parameters, _):
        scenario_path = parameters[0].valueAsText
        run_cli(scenario_path, 'operation-costs')


class RetrofitPotentialTool(object):
    def __init__(self):
        self.label = 'Building Retrofit Potential'
        self.category = 'Retrofit Analysis'
        self.description = 'Select buildings according to specific criteria for retrofit'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(displayName="Path to the scenario", name="scenario_path", datatype="DEFolder",
                                        parameterType="Required", direction="Input")
        retrofit_target_date = arcpy.Parameter(displayName="Year when the retrofit will take place",
                                               name="retrofit_target_date", datatype="GPLong", parameterType="Required",
                                               direction="Input")
        retrofit_target_date.value = 2020

        keep_partial_matches = arcpy.Parameter(displayName="Keep buildings partially matching the selected criteria",
                                               name="keep_partial_matches",
                                               datatype="GPBoolean", parameterType="Required", direction="Input")
        keep_partial_matches.value = False

        name = arcpy.Parameter(displayName="Name for new scenario", name="name", datatype="String",
                               parameterType="Required", direction="Input")
        name.value = "retrofit_HVAC"

        cb_age_threshold = arcpy.Parameter(displayName="Enable threshold age of HVAC (built / retrofitted)",
                                           name="cb_age_threshold", datatype="GPBoolean", parameterType="Required",
                                           direction="Input", category="age")
        cb_age_threshold.value = False
        cb_age_threshold.enabled = False

        age_threshold = arcpy.Parameter(displayName="threshold age of HVAC (built / retrofitted)", name="age_threshold",
                                        datatype="GPLong", parameterType="Optional", direction="Input", category="age")
        age_threshold.value = 15
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
        eui_heating_threshold.value = 50
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
        eui_hot_water_threshold.value = 50
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
        eui_cooling_threshold.value = 4
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
        eui_electricity_threshold.value = 20
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
        emissions_operation_threshold.value = 30
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
        heating_costs_threshold.value = 2
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
        hot_water_costs_threshold.value = 2
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
        cooling_costs_threshold.value = 2
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
        electricity_costs_threshold.value = 2
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
        heating_losses_threshold.value = 15
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
        hot_water_losses_threshold.value = 15
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
        cooling_losses_threshold.value = 15
        cooling_losses_threshold.enabled = False

        return [scenario_path, retrofit_target_date, keep_partial_matches, name, cb_age_threshold, age_threshold,
                cb_eui_heating_threshold, eui_heating_threshold, cb_eui_hot_water_threshold, eui_hot_water_threshold,
                cb_eui_cooling_threshold, eui_cooling_threshold, cb_eui_electricity_threshold,
                eui_electricity_threshold, cb_emissions_operation_threshold, emissions_operation_threshold,
                cb_heating_costs_threshold, heating_costs_threshold, cb_hot_water_costs_threshold,
                hot_water_costs_threshold, cb_cooling_costs_threshold, cooling_costs_threshold,
                cb_electricity_costs_threshold, electricity_costs_threshold, cb_heating_losses_threshold,
                heating_losses_threshold, cb_hot_water_losses_threshold, hot_water_losses_threshold,
                cb_cooling_losses_threshold, cooling_losses_threshold]

    def updateParameters(self, parameters):
        # only enable fields if scenario_path is set
        for p in parameters[1:]:
            p.enabled = False

        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        # this only get's run if a scenario is chosen
        for p in parameters[1:]:
            p.enabled = True

        parameters = {p.name: p for p in parameters}
        for parameter_name in parameters.keys():
            if parameter_name.startswith('cb_'):
                parameters[parameter_name].setErrorMessage(parameter_name[3:])
                parameters[parameter_name[3:]].enabled = parameters[parameter_name].value

    def execute(self, parameters, _):
        scenario_path, retrofit_target_date, include_only_matches_to_all_criteria, name = parameters[:4]
        scenario_path = scenario_path.valueAsText
        retrofit_target_date = retrofit_target_date.value
        include_only_matches_to_all_criteria = include_only_matches_to_all_criteria.value
        name = name.valueAsText

        args = ['--retrofit-target-date', str(retrofit_target_date), '--name', name]
        if include_only_matches_to_all_criteria:
            args.append('--keep-partial-matches')

        parameters = {p.name: p for p in parameters[4:]}
        for p_name in parameters.keys():
            if p_name.startswith('cb_'):
                checkbox = parameters[p_name]
                parameter = parameters[p_name[3:]]
                if checkbox.value and (parameter.value is not None):
                    args.append('--%s' % parameter.name.replace('_', '-'))
                    args.append(str(parameter.value))

        run_cli(scenario_path, 'retrofit-potential', *args)


class DemandTool(object):
    """integrate the demand script with ArcGIS"""

    def __init__(self):
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.category = 'Dynamic Demand Forecasting'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        weather_name = arcpy.Parameter(
            displayName="Weather file (choose from list or enter full path to .epw file)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names() + ['<choose path from below>']
        weather_name.enabled = False

        weather_path = arcpy.Parameter(
            displayName="Path to .epw file",
            name="weather_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input")
        weather_path.filter.list = ['epw']
        weather_path.enabled = False

        dynamic_infiltration = arcpy.Parameter(
            displayName="Use dynamic infiltration model (slower)",
            name="dynamic_infiltration",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        dynamic_infiltration.enabled = False

        multiprocessing = arcpy.Parameter(
            displayName="Use multiple cores to speed up processing",
            name="multiprocessing",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        multiprocessing.enabled = False

        return [scenario_path, weather_name, weather_path, dynamic_infiltration, multiprocessing]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            for p in parameters[1:]:
                p.enabled = False
            return
        if not os.path.exists(scenario_path):
            for p in parameters[1:]:
                p.enabled = False
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        if not parameters[1].enabled:
            for p in parameters[1:]:
                p.enabled = True
            parameters = {p.name: p for p in parameters}

            parameters['dynamic_infiltration'].value = read_config_boolean(scenario_path, 'demand',
                                                                           'use-dynamic-infiltration-calculation')
            parameters['multiprocessing'].value = read_config_boolean(scenario_path, 'general', 'multiprocessing')

            weather_path = read_config_string(scenario_path, 'general', 'weather')
            if is_builtin_weather_path(weather_path):
                parameters['weather_path'].enabled = False
                parameters['weather_name'].value = builtin_weather_name(weather_path)
            else:
                parameters['weather_name'].value = '<choose path from below>'
                parameters['weather_path'].value = weather_path
        else:
            parameters = {p.name: p for p in parameters}
            parameters['weather_path'].enabled = parameters['weather_name'].value == '<choose path from below>'

    def updateMessages(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        if not os.path.exists(get_radiation(scenario_path)):
            parameters[0].setErrorMessage("No radiation data found for scenario. Run radiation script first.")
        if not os.path.exists(get_surface_properties(scenario_path)):
            parameters[0].setErrorMessage("No radiation data found for scenario. Run radiation script first.")
        return

    def execute(self, parameters, _):
        parameters = {p.name: p for p in parameters}
        scenario_path = parameters['scenario_path'].valueAsText
        weather_name = parameters['weather_name'].valueAsText
        weather_path_param = parameters['weather_path']
        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)
        elif weather_path_param.enabled:
            if os.path.exists(weather_path_param.valueAsText) and weather_path_param.valueAsText.endswith('.epw'):
                weather_path = weather_path_param.valueAsText
        else:
            weather_path = get_weather_path()

        use_dynamic_infiltration_calculation = parameters['dynamic_infiltration'].value
        multiprocessing = parameters['multiprocessing'].value

        # save the configuration to the scenario.config file
        write_config_string(scenario_path, 'general', 'weather', weather_path)
        write_config_boolean(scenario_path, 'demand', 'use-dynamic-infiltration-calculation',
                             use_dynamic_infiltration_calculation)
        write_config_boolean(scenario_path, 'general', 'multiprocessing', multiprocessing)

        # run the demand script
        args = [scenario_path, 'demand', '--weather', weather_path]
        if use_dynamic_infiltration_calculation:
            args.append('--use-dynamic-infiltration-calculation')
        if multiprocessing:
            args.append('--multiprocessing')
        run_cli(*args)


class DataHelperTool(object):
    """
    integrate the cea/demand/preprocessing/properties.py script with ArcGIS.
    """

    def __init__(self):
        self.label = 'Data helper'
        self.description = 'Query characteristics of buildings and systems from statistical data'
        self.category = 'Data Management'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        prop_thermal_flag = arcpy.Parameter(
            displayName="Generate thermal properties",
            name="prop_thermal_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_thermal_flag.value = True
        prop_architecture_flag = arcpy.Parameter(
            displayName="Generate architectural properties",
            name="prop_architecture_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_architecture_flag.value = True
        prop_HVAC_flag = arcpy.Parameter(
            displayName="Generate technical systems properties",
            name="prop_HVAC_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_HVAC_flag.value = True
        prop_comfort_flag = arcpy.Parameter(
            displayName="Generate comfort properties",
            name="prop_comfort_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_comfort_flag.value = True
        prop_internal_loads_flag = arcpy.Parameter(
            displayName="Generate internal loads properties",
            name="prop_internal_loads_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_internal_loads_flag.value = True
        return [scenario_path, prop_thermal_flag, prop_architecture_flag, prop_HVAC_flag, prop_comfort_flag,
                prop_internal_loads_flag]

    def execute(self, parameters, _):
        scenario_path = parameters[0].valueAsText
        flags = {'thermal': parameters[1].value,
                 'architecture': parameters[2].value,
                 'HVAC': parameters[3].value,
                 'comfort': parameters[4].value,
                 'internal-loads': parameters[5].value}
        archetypes = [key for key in flags.keys() if flags[key]]
        run_cli(scenario_path, 'data-helper', '--archetypes', *archetypes)


class BenchmarkGraphsTool(object):
    """Integrates the cea/analysis/benchmark.py tool with ArcGIS"""

    def __init__(self):
        self.label = '2000W Society Benchmark'
        self.description = 'Plot life cycle primary energy demand and emissions compared to an established benchmark'
        self.category = 'Benchmarking'
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
        scenarios = parameters[0].valueAsText
        scenarios = scenarios.replace('"', '')
        scenarios = scenarios.replace("'", '')
        scenarios = scenarios.split(';')
        arcpy.AddMessage(scenarios)
        output_file = parameters[1].valueAsText
        run_cli(None, 'benchmark-graphs', '--output-file', output_file, '--scenarios', *scenarios)
        return


class OperationTool(object):
    def __init__(self):
        self.label = 'LCA Operation'
        self.description = 'Calculate emissions and primary energy due to building operation'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        Qww_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to hot water consumption.",
            name="Qww_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qww_flag.value = True
        Qhs_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to space heating.",
            name="Qhs_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qhs_flag.value = True
        Qcs_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to space cooling.",
            name="Qcs_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcs_flag.value = True
        Qcdata_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to servers cooling.",
            name="Qcdata_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcdata_flag.value = True
        Qcrefri_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to refrigeration.",
            name="Qcrefri_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcrefri_flag.value = True
        Eal_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to appliances and lighting.",
            name="Eal_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Eal_flag.value = True
        Eaux_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to auxiliary electricity.",
            name="Eaux_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Eaux_flag.value = True
        Epro_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to electricity in industrial processes.",
            name="Epro_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Epro_flag.value = True
        Edata_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to electricity consumption in data centers.",
            name="Edata_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Edata_flag.value = True

        return [scenario_path, Qww_flag, Qhs_flag, Qcs_flag, Qcdata_flag, Qcrefri_flag, Eal_flag, Eaux_flag, Epro_flag,
                Edata_flag]

    def execute(self, parameters, _):
        scenario_path = parameters[0].valueAsText
        flags = {
            'Qww': parameters[1].value,
            'Qhs': parameters[2].value,
            'Qcs': parameters[3].value,
            'Qcdata': parameters[4].value,
            'Qcrefri': parameters[5].value,
            'Eal': parameters[6].value,
            'Eaux': parameters[7].value,
            'Epro': parameters[8].value,
            'Edata': parameters[9].value,
        }
        extra_files_to_create = [key for key in flags if flags[key]]
        run_cli(scenario_path, 'emissions', '--extra-files-to-create', *extra_files_to_create)


class EmbodiedTool(object):
    def __init__(self):
        self.label = 'LCA Construction'
        self.description = 'Calculate the emissions and primary energy for building construction and decommissioning'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False

    def getParameterInfo(self):
        yearcalc = arcpy.Parameter(
            displayName="Year to calculate",
            name="yearcalc",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        yearcalc.value = 2014

        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [yearcalc, scenario_path]

    def execute(self, parameters, _):
        year_to_calculate = int(parameters[0].valueAsText)
        scenario_path = parameters[1].valueAsText
        run_cli(scenario_path, 'embodied-energy', '--year-to-calculate', year_to_calculate)


class MobilityTool(object):
    """Integrates the cea/analysis/mobility.py script with ArcGIS."""

    def __init__(self):
        self.label = 'LCA Mobility'
        self.description = 'Calculate emissions and primary energy due to mobility'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [scenario_path]

    def execute(self, parameters, messages):
        scenario_path = parameters[0].valueAsText
        run_cli(scenario_path, 'mobility')


class DemandGraphsTool(object):
    def __init__(self):
        self.label = 'Plots'
        self.description = 'Plot demand time-series data'
        self.category = 'Dynamic Demand Forecasting'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        analysis_fields = arcpy.Parameter(
            displayName="Variables to analyse",
            name="analysis_fields",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        analysis_fields.filter.list = []
        analysis_fields.enabled = False
        multiprocessing = arcpy.Parameter(
            displayName="Use multiple cores to speed up processing",
            name="multiprocessing",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        multiprocessing.enabled = False
        return [scenario_path, analysis_fields, multiprocessing]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        analysis_fields = parameters[1]
        if not analysis_fields.enabled:
            analysis_fields.enabled = True
            fields = _cli_output(scenario_path, 'demand-graphs', '--list-fields').split()
            analysis_fields.filter.list = list(fields)

            multiprocessing = parameters[2]
            multiprocessing.value = read_config_boolean(scenario_path, 'general', 'multiprocessing')
            multiprocessing.enabled = True

    def execute(self, parameters, messages):
        scenario_path = parameters[0].valueAsText
        analysis_fields = parameters[1].valueAsText.split(';')[:4]  # max 4 fields for analysis
        write_config_boolean(scenario_path, 'general', 'multiprocessing', parameters[2].value)
        run_cli(scenario_path, 'demand-graphs', '--analysis-fields', *analysis_fields)


class ScenarioPlotsTool(object):
    def __init__(self):
        self.label = 'Scenario plots'
        self.description = 'Create summary plots of scenarios in a folder'
        self.category = 'Mapping and Visualization'
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
        scenarios = parameters[0].valueAsText
        scenarios = scenarios.replace("'", "")
        scenarios = scenarios.replace('"', '')
        scenarios = scenarios.split(';')
        output_file = parameters[1].valueAsText
        add_message(scenarios)
        run_cli(None, 'scenario-plots', '--output-file', output_file, '--scenarios', *scenarios)


class PhotovoltaicPannelsTool(object):
    def __init__(self):
        self.label = 'Photovoltaic Panels'
        self.description = 'Calculate electricity production from solar photovoltaic technologies'
        self.category = 'Dynamic Supply Systems'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name = arcpy.Parameter(
            displayName="Weather file (use the same one for solar radiation calculation)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names() + ['<choose path from below>']
        weather_name.enabled = False

        weather_path = arcpy.Parameter(
            displayName="Path to .epw file",
            name="weather_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input")
        weather_path.filter.list = ['epw']
        weather_path.enabled = False

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = 2014
        year.enabled = False

        latitude = arcpy.Parameter(
            displayName="Latitude",
            name="latitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        latitude.enabled = False

        longitude = arcpy.Parameter(
            displayName="Longitude",
            name="longitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        longitude.enabled = False

        panel_on_roof = arcpy.Parameter(
            displayName="Consider panels on roofs",
            name="panel_on_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_roof.value = True
        panel_on_roof.enabled = False

        panel_on_wall = arcpy.Parameter(
            displayName="Consider panels on walls",
            name="panel_on_wall",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_wall.value = True
        panel_on_wall.enabled = False

        solar_window_solstice = arcpy.Parameter(
            displayName="Desired hours of production on the winter solstice",
            name="solar_window_solstice",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        solar_window_solstice.value = 4
        solar_window_solstice.enabled = False

        type_PVpanel = arcpy.Parameter(
            displayName="PV technology to use",
            name="type_PVpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_PVpanel.filter.list = ['monocrystalline', 'polycrystalline', 'amorphous']
        type_PVpanel.enabled = False

        min_radiation = arcpy.Parameter(
            displayName="filtering surfaces with low radiation potential (% of the maximum radiation in the area)",
            name="min_radiation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        min_radiation.value = 0.75
        min_radiation.enabled = False

        return [scenario_path, weather_name, weather_path, year, latitude, longitude, panel_on_roof, panel_on_wall,
                solar_window_solstice, type_PVpanel, min_radiation]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        parameters = {p.name: p for p in parameters}
        if not parameters['weather_name'].enabled:
            # user just chose scenario, read in defaults etc.

            radiation_csv = _cli_output(scenario_path, 'locate', 'get_radiation')
            if not os.path.exists(radiation_csv):
                parameters['scenario_path'].setErrorMessage("No radiation file found - please run radiation tool first")
                return

            latitude_parameter = parameters['latitude']
            longitude_parameter = parameters['longitude']

            latitude_value = float(_cli_output(scenario_path, 'latitude'))
            longitude_value = float(_cli_output(scenario_path, 'longitude'))
            if not latitude_parameter.enabled:
                # only overwrite on first try
                latitude_parameter.value = latitude_value

            if not longitude_parameter.enabled:
                # only overwrite on first try
                longitude_parameter.value = longitude_value

            # read values from scenario / or defaults
            parameters['year'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                   '--key', 'date-start')[:4]
            parameters['panel_on_roof'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'panel-on-roof')
            parameters['panel_on_wall'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'panel-on-wall')
            pv_panel_types = {'PV1': 'monocrystalline', 'PV2': 'polycrystalline', 'PV3': 'amorphous'}
            parameters['type_PVpanel'].value = pv_panel_types[
                _cli_output(scenario_path, 'read-config', '--section', 'solar', '--key', 'type-PVpanel')]
            parameters['min_radiation'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'min-radiation')
            parameters['solar_window_solstice'].value = _cli_output(scenario_path, 'read-config', '--section',
                                                                    'solar',
                                                                    '--key', 'solar-window-solstice')

            weather_path = _cli_output(scenario_path, 'read-config', '--section', 'general', '--key', 'weather')
            if is_db_weather(weather_path):
                parameters['weather_name'].value = get_db_weather_name(weather_path)
                parameters['weather_path'].value = ''
            else:
                parameters['weather_name'].value = '<choose path from below>'
                parameters['weather_path'].value = weather_path

            for p in parameters.values():
                p.enabled = True
            parameters['scenario_path'].enabled = False  # user need to re-open dialog to change scenario path...
        parameters['weather_path'].enabled = parameters['weather_name'].value == '<choose path from below>'

    def updateMessages(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        radiation_csv = _cli_output(scenario_path, 'locate', 'get_radiation')
        if not os.path.exists(radiation_csv):
            parameters[0].setErrorMessage("No radiation file found - please run radiation tool first")
            return

    def execute(self, parameters, messages):
        parameters = {p.name: p for p in parameters}
        scenario_path = parameters['scenario_path'].valueAsText
        weather_name = parameters['weather_name'].valueAsText
        weather_path = parameters['weather_path'].valueAsText
        year = parameters['year'].value
        latitude = parameters['latitude'].value
        longitude = parameters['longitude'].value
        panel_on_roof = parameters['panel_on_roof'].value
        panel_on_wall = parameters['panel_on_wall'].value
        solar_window_solstice = parameters['solar_window_solstice'].value
        type_PVpanel = {'monocrystalline': 'PV1',
                        'polycrystalline': 'PV2',
                        'amorphous': 'PV3'}[parameters['type_PVpanel'].value]
        min_radiation = parameters['min_radiation'].value

        date_start = str(year) + '-01-01'

        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)

        add_message('longitude: %s' % longitude)
        add_message('latitude: %s' % latitude)

        run_cli_arguments = [scenario_path, 'photovoltaic',
                             '--latitude', latitude,
                             '--longitude', longitude,
                             '--weather-path', weather_path,
                             '--solar-window-solstice', solar_window_solstice,
                             '--type-PVpanel', type_PVpanel,
                             '--min-radiation', min_radiation,
                             '--date-start', date_start,
                             '--panel-on-roof', 'yes' if panel_on_roof else 'no',
                             '--panel-on-wall', 'yes' if panel_on_wall else 'no']
        run_cli(*run_cli_arguments)
        return


class SolarCollectorPanelsTool(object):
    def __init__(self):
        self.label = 'Solar Collector Panels'
        self.description = 'Calculate heat production from solar collector technologies'
        self.category = 'Dynamic Supply Systems'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name = arcpy.Parameter(
            displayName="Weather file (use the same one for solar radiation calculation)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names() + ['<choose path from below>']
        weather_name.enabled = False

        weather_path = arcpy.Parameter(
            displayName="Path to .epw file",
            name="weather_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input")
        weather_path.filter.list = ['epw']
        weather_path.enabled = False

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = 2014
        year.enabled = False

        latitude = arcpy.Parameter(
            displayName="Latitude",
            name="latitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        latitude.enabled = False

        longitude = arcpy.Parameter(
            displayName="Longitude",
            name="longitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        longitude.enabled = False

        panel_on_roof = arcpy.Parameter(
            displayName="Consider panels on roofs",
            name="panel_on_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_roof.value = True
        panel_on_roof.enabled = False

        panel_on_wall = arcpy.Parameter(
            displayName="Consider panels on walls",
            name="panel_on_wall",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_wall.value = True
        panel_on_wall.enabled = False

        solar_window_solstice = arcpy.Parameter(
            displayName="Desired hours of production on the winter solstice",
            name="solar_window_solstice",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        solar_window_solstice.value = 4
        solar_window_solstice.enabled = False

        type_SCpanel = arcpy.Parameter(
            displayName="Solar collector technology to use",
            name="type_SCpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_SCpanel.filter.list = ['flat plate collectors', 'evacuated tubes']
        type_SCpanel.enabled = False

        min_radiation = arcpy.Parameter(
            displayName="filtering surfaces with low radiation potential (% of the maximum radiation in the area)",
            name="min_radiation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        min_radiation.value = 0.75
        min_radiation.enabled = False

        return [scenario_path, weather_name, weather_path, year, latitude, longitude, panel_on_roof, panel_on_wall,
                solar_window_solstice, type_SCpanel, min_radiation]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        parameters = {p.name: p for p in parameters}
        if not parameters['weather_name'].enabled:
            # user just chose scenario, read in defaults etc.

            radiation_csv = _cli_output(scenario_path, 'locate', 'get_radiation')
            if not os.path.exists(radiation_csv):
                parameters['scenario_path'].setErrorMessage("No radiation file found - please run radiation tool first")
                return

            latitude_parameter = parameters['latitude']
            longitude_parameter = parameters['longitude']

            latitude_value = float(_cli_output(scenario_path, 'latitude'))
            longitude_value = float(_cli_output(scenario_path, 'longitude'))
            if not latitude_parameter.enabled:
                # only overwrite on first try
                latitude_parameter.value = latitude_value

            if not longitude_parameter.enabled:
                # only overwrite on first try
                longitude_parameter.value = longitude_value

            # read values from scenario / or defaults
            parameters['year'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                   '--key', 'date-start')[:4]
            parameters['panel_on_roof'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'panel-on-roof')
            parameters['panel_on_wall'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'panel-on-wall')
            sc_panel_types = {'SC1': 'flat plate collectors', 'SC2': 'evacuated tubes'}
            parameters['type_SCpanel'].value = sc_panel_types[
                _cli_output(scenario_path, 'read-config', '--section', 'solar', '--key', 'type-SCpanel')]
            parameters['min_radiation'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'min-radiation')
            parameters['solar_window_solstice'].value = _cli_output(scenario_path, 'read-config', '--section',
                                                                    'solar',
                                                                    '--key', 'solar-window-solstice')

            weather_path = _cli_output(scenario_path, 'read-config', '--section', 'general', '--key', 'weather')
            if is_db_weather(weather_path):
                parameters['weather_name'].value = get_db_weather_name(weather_path)
                parameters['weather_path'].value = ''
            else:
                parameters['weather_name'].value = '<choose path from below>'
                parameters['weather_path'].value = weather_path

            for p in parameters.values():
                p.enabled = True
            parameters['scenario_path'].enabled = False  # user need to re-open dialog to change scenario path...
        parameters['weather_path'].enabled = parameters['weather_name'].value == '<choose path from below>'

    def updateMessages(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        radiation_csv = _cli_output(scenario_path, 'locate', 'get_radiation')
        if not os.path.exists(radiation_csv):
            parameters[0].setErrorMessage("No radiation file found - please run radiation tool first")
            return

    def execute(self, parameters, messages):
        parameters = {p.name: p for p in parameters}
        scenario_path = parameters['scenario_path'].valueAsText
        weather_name = parameters['weather_name'].valueAsText
        weather_path = parameters['weather_path'].valueAsText
        year = parameters['year'].value
        latitude = parameters['latitude'].value
        longitude = parameters['longitude'].value
        panel_on_roof = parameters['panel_on_roof'].value
        panel_on_wall = parameters['panel_on_wall'].value
        solar_window_solstice = parameters['solar_window_solstice'].value
        type_SCpanel = {'flat plate collectors': 'SC1',
                        'evacuated tubes': 'SC2'}[parameters['type_SCpanel'].value]
        # : flat plat collectors, SC2: evacuated tubes
        min_radiation = parameters['min_radiation'].value

        date_start = str(year) + '-01-01'

        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)

        add_message('longitude: %s' % longitude)
        add_message('latitude: %s' % latitude)

        run_cli_arguments = [scenario_path, 'solar-collector',
                             '--latitude', latitude,
                             '--longitude', longitude,
                             '--weather-path', weather_path,
                             '--solar-window-solstice', solar_window_solstice,
                             '--type-SCpanel', type_SCpanel,
                             '--min-radiation', min_radiation,
                             '--date-start', date_start,
                             '--panel-on-roof', 'yes' if panel_on_roof else 'no',
                             '--panel-on-wall', 'yes' if panel_on_wall else 'no']
        run_cli(*run_cli_arguments)
        return


class PhotovoltaicThermalPanelsTool(object):
    def __init__(self):
        self.label = 'PVT Panels'
        self.description = 'Calculate electricity & heat production from photovoltaic / thermal technologies'
        self.category = 'Dynamic Supply Systems'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name = arcpy.Parameter(
            displayName="Weather file (use the same one for solar radiation calculation)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names() + ['<choose path from below>']
        weather_name.enabled = False

        weather_path = arcpy.Parameter(
            displayName="Path to .epw file",
            name="weather_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input")
        weather_path.filter.list = ['epw']
        weather_path.enabled = False

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = 2014
        year.enabled = False

        latitude = arcpy.Parameter(
            displayName="Latitude",
            name="latitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        latitude.enabled = False

        longitude = arcpy.Parameter(
            displayName="Longitude",
            name="longitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        longitude.enabled = False

        panel_on_roof = arcpy.Parameter(
            displayName="Consider panels on roofs",
            name="panel_on_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_roof.value = True
        panel_on_roof.enabled = False

        panel_on_wall = arcpy.Parameter(
            displayName="Consider panels on walls",
            name="panel_on_wall",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        panel_on_wall.value = True
        panel_on_wall.enabled = False

        solar_window_solstice = arcpy.Parameter(
            displayName="Desired hours of production on the winter solstice",
            name="solar_window_solstice",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        solar_window_solstice.value = 4
        solar_window_solstice.enabled = False

        type_SCpanel = arcpy.Parameter(
            displayName="Solar collector technology to use",
            name="type_SCpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_SCpanel.filter.list = ['flat plate collectors', 'evacuated tubes']
        type_SCpanel.enabled = False

        type_PVpanel = arcpy.Parameter(
            displayName="PV technology to use",
            name="type_PVpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_PVpanel.filter.list = ['monocrystalline', 'polycrystalline', 'amorphous']
        type_PVpanel.enabled = False

        min_radiation = arcpy.Parameter(
            displayName="filtering surfaces with low radiation potential (% of the maximum radiation in the area)",
            name="min_radiation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        min_radiation.value = 0.75
        min_radiation.enabled = False

        return [scenario_path, weather_name, weather_path, year, latitude, longitude, panel_on_roof, panel_on_wall,
                solar_window_solstice, type_PVpanel, type_SCpanel, min_radiation]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        parameters = {p.name: p for p in parameters}
        if not parameters['weather_name'].enabled:
            # user just chose scenario, read in defaults etc.

            radiation_csv = _cli_output(scenario_path, 'locate', 'get_radiation')
            if not os.path.exists(radiation_csv):
                parameters['scenario_path'].setErrorMessage("No radiation file found - please run radiation tool first")
                return

            latitude_parameter = parameters['latitude']
            longitude_parameter = parameters['longitude']

            latitude_value = float(_cli_output(scenario_path, 'latitude'))
            longitude_value = float(_cli_output(scenario_path, 'longitude'))
            if not latitude_parameter.enabled:
                # only overwrite on first try
                latitude_parameter.value = latitude_value

            if not longitude_parameter.enabled:
                # only overwrite on first try
                longitude_parameter.value = longitude_value

            # read values from scenario / or defaults
            parameters['year'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                   '--key', 'date-start')[:4]
            parameters['panel_on_roof'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'panel-on-roof')
            parameters['panel_on_wall'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'panel-on-wall')
            pv_panel_types = {'PV1': 'monocrystalline', 'PV2': 'polycrystalline', 'PV3': 'amorphous'}
            parameters['type_PVpanel'].value = pv_panel_types[
                _cli_output(scenario_path, 'read-config', '--section', 'solar', '--key', 'type-PVpanel')]
            sc_panel_types = {'SC1': 'flat plate collectors', 'SC2': 'evacuated tubes'}
            parameters['type_SCpanel'].value = sc_panel_types[
                _cli_output(scenario_path, 'read-config', '--section', 'solar', '--key', 'type-SCpanel')]
            parameters['min_radiation'].value = _cli_output(scenario_path, 'read-config', '--section', 'solar',
                                                            '--key', 'min-radiation')
            parameters['solar_window_solstice'].value = _cli_output(scenario_path, 'read-config', '--section',
                                                                    'solar',
                                                                    '--key', 'solar-window-solstice')

            weather_path = _cli_output(scenario_path, 'read-config', '--section', 'general', '--key', 'weather')
            if is_db_weather(weather_path):
                parameters['weather_name'].value = get_db_weather_name(weather_path)
                parameters['weather_path'].value = ''
            else:
                parameters['weather_name'].value = '<choose path from below>'
                parameters['weather_path'].value = weather_path

            for p in parameters.values():
                p.enabled = True
            parameters['scenario_path'].enabled = False  # user need to re-open dialog to change scenario path...
        parameters['weather_path'].enabled = parameters['weather_name'].value == '<choose path from below>'

    def updateMessages(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        radiation_csv = _cli_output(scenario_path, 'locate', 'get_radiation')
        if not os.path.exists(radiation_csv):
            parameters[0].setErrorMessage("No radiation file found - please run radiation tool first")
            return

    def execute(self, parameters, messages):
        parameters = {p.name: p for p in parameters}
        scenario_path = parameters['scenario_path'].valueAsText
        weather_name = parameters['weather_name'].valueAsText
        weather_path = parameters['weather_path'].valueAsText
        year = parameters['year'].value
        latitude = parameters['latitude'].value
        longitude = parameters['longitude'].value
        panel_on_roof = parameters['panel_on_roof'].value
        panel_on_wall = parameters['panel_on_wall'].value
        solar_window_solstice = parameters['solar_window_solstice'].value
        type_PVpanel = {'monocrystalline': 'PV1',
                        'polycrystalline': 'PV2',
                        'amorphous': 'PV3'}[parameters['type_PVpanel'].value]
        type_SCpanel = {'flat plate collectors': 'SC1',
                        'evacuated tubes': 'SC2'}[parameters['type_SCpanel'].value]
        min_radiation = parameters['min_radiation'].value

        date_start = str(year) + '-01-01'

        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)

        add_message('longitude: %s' % longitude)
        add_message('latitude: %s' % latitude)

        run_cli_arguments = [scenario_path, 'photovoltaic-thermal',
                             '--latitude', latitude,
                             '--longitude', longitude,
                             '--weather-path', weather_path,
                             '--solar-window-solstice', solar_window_solstice,
                             '--type-PVpanel', type_PVpanel,
                             '--type-SCpanel', type_SCpanel,
                             '--min-radiation', min_radiation,
                             '--date-start', date_start,
                             '--panel-on-roof', 'yes' if panel_on_roof else 'no',
                             '--panel-on-wall', 'yes' if panel_on_wall else 'no']
        run_cli(*run_cli_arguments)
        return


class RadiationDaysimTool(object):
    def __init__(self):
        self.label = 'Urban solar radiation'
        self.description = 'Use Daysim to calculate solar radiation for a scenario'
        self.category = 'Renewable Energy Assessment'
        self.canRunInBackground = False
        self.options = {'rad-n', 'rad-af', 'rad-ab', 'rad-ad', 'rad-as', 'rad-ar', 'rad-aa', 'rad-lr', 'rad-st',
                        'rad-sj',
                        'rad-lw', 'rad-dj', 'rad-ds', 'rad-dr', 'rad-dp', 'sensor-x-dim', 'sensor-y-dim', 'e-terrain',
                        'n-buildings-in-chunk', 'multiprocessing', 'zone-geometry', 'surrounding-geometry',
                        'consider-windows',
                        'consider-floors'}

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name = arcpy.Parameter(
            displayName="Weather file (use the same one for solar radiation calculation)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names() + ['<choose path from below>']
        weather_name.enabled = False

        weather_path = arcpy.Parameter(
            displayName="Path to .epw file",
            name="weather_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input")
        weather_path.filter.list = ['epw']
        weather_path.enabled = False

        rad_n = arcpy.Parameter(displayName="rad-n", category="Daysism radiation simulation parameters", name="rad_n",
                                datatype="Long",
                                parameterType="Required", direction="Input")
        rad_n.enabled = False

        rad_af = arcpy.Parameter(displayName="rad-af", category="Daysism radiation simulation parameters",
                                 name="rad_af", datatype="GPString",
                                 parameterType="Required", direction="Input")
        rad_af.enabled = False

        rad_ab = arcpy.Parameter(displayName="rad-ab", category="Daysism radiation simulation parameters",
                                 name="rad_ab", datatype="Long",
                                 parameterType="Required", direction="Input")
        rad_ab.enabled = False

        rad_ad = arcpy.Parameter(displayName="rad-ad", category="Daysism radiation simulation parameters",
                                 name="rad_ad", datatype="Long",
                                 parameterType="Required", direction="Input")
        rad_ad.enabled = False

        rad_as = arcpy.Parameter(displayName="rad-as", category="Daysism radiation simulation parameters",
                                 name="rad_as", datatype="Long",
                                 parameterType="Required", direction="Input")
        rad_as.enabled = False

        rad_ar = arcpy.Parameter(displayName="rad-ar", category="Daysism radiation simulation parameters",
                                 name="rad_ar", datatype="Long",
                                 parameterType="Required", direction="Input")
        rad_ar.enabled = False

        rad_aa = arcpy.Parameter(displayName="rad-aa", category="Daysism radiation simulation parameters",
                                 name="rad_aa", datatype="GPDouble",
                                 parameterType="Required", direction="Input")
        rad_aa.enabled = False

        rad_lr = arcpy.Parameter(displayName="rad-lr", category="Daysism radiation simulation parameters",
                                 name="rad_lr", datatype="Long",
                                 parameterType="Required", direction="Input")
        rad_lr.enabled = False

        rad_st = arcpy.Parameter(displayName="rad-st", category="Daysism radiation simulation parameters",
                                 name="rad_st", datatype="GPDouble",
                                 parameterType="Required", direction="Input")
        rad_st.enabled = False

        rad_sj = arcpy.Parameter(displayName="rad-sj", category="Daysism radiation simulation parameters",
                                 name="rad_sj", datatype="GPDouble",
                                 parameterType="Required", direction="Input")
        rad_sj.enabled = False

        rad_lw = arcpy.Parameter(displayName="rad-lw", category="Daysism radiation simulation parameters",
                                 name="rad_lw", datatype="GPDouble",
                                 parameterType="Required", direction="Input")
        rad_lw.enabled = False

        rad_dj = arcpy.Parameter(displayName="rad-dj", category="Daysism radiation simulation parameters",
                                 name="rad_dj", datatype="GPDouble",
                                 parameterType="Required", direction="Input")
        rad_dj.enabled = False

        rad_ds = arcpy.Parameter(displayName="rad-ds", category="Daysism radiation simulation parameters",
                                 name="rad_ds", datatype="GPDouble",
                                 parameterType="Required", direction="Input")
        rad_ds.enabled = False

        rad_dr = arcpy.Parameter(displayName="rad-dr", category="Daysism radiation simulation parameters",
                                 name="rad_dr", datatype="Long",
                                 parameterType="Required", direction="Input")
        rad_dr.enabled = False

        rad_dp = arcpy.Parameter(displayName="rad-dp", category="Daysism radiation simulation parameters",
                                 name="rad_dp", datatype="Long",
                                 parameterType="Required", direction="Input")
        rad_dp.enabled = False

        sensor_x_dim = arcpy.Parameter(displayName="X-dim", category="Grid for the sensors", name="sensor_x_dim",
                                       datatype="Long",
                                       parameterType="Required", direction="Input")
        sensor_x_dim.enabled = False

        sensor_y_dim = arcpy.Parameter(displayName="Y-dim", category="Grid for the sensors", name="sensor_y_dim",
                                       datatype="Long",
                                       parameterType="Required", direction="Input")
        sensor_y_dim.enabled = False

        e_terrain = arcpy.Parameter(displayName="e-terrain", category="Terrain parameters", name="e_terrain",
                                    datatype="GPDouble",
                                    parameterType="Required", direction="Input")
        e_terrain.enabled = False

        n_buildings_in_chunk = arcpy.Parameter(displayName="n-buildings-in-chunk", category="Simulation parameters",
                                               name="n_buildings_in_chunk",
                                               datatype="Long", parameterType="Required", direction="Input")
        n_buildings_in_chunk.enabled = False

        multiprocessing = arcpy.Parameter(displayName="multiprocessing", category="Simulation parameters",
                                          name="multiprocessing", datatype="GPBoolean", parameterType="Required",
                                          direction="Input")
        multiprocessing.enabled = False

        zone_geometry = arcpy.Parameter(displayName="zone-geometry", category="Geometry simplification",
                                        name="zone_geometry", datatype="Long",
                                        parameterType="Required", direction="Input")
        zone_geometry.enabled = False

        surrounding_geometry = arcpy.Parameter(displayName="surrounding-geometry", category="Geometry simplification",
                                               name="surrounding_geometry",
                                               datatype="Long", parameterType="Required", direction="Input")
        surrounding_geometry.enabled = False

        consider_windows = arcpy.Parameter(displayName="consider-windows", category="Geometry simplification",
                                           name="consider_windows", datatype="GPBoolean", parameterType="Required",
                                           direction="Input")
        consider_windows.enabled = False

        consider_floors = arcpy.Parameter(displayName="consider-floors", category="Geometry simplification",
                                          name="consider_floors", datatype="GPBoolean", parameterType="Required",
                                          direction="Input")
        consider_floors.enabled = False

        return [scenario_path, weather_name, weather_path, rad_n, rad_af, rad_ab, rad_ad, rad_as, rad_ar, rad_aa,
                rad_lr, rad_st, rad_sj, rad_lw, rad_dj, rad_ds, rad_dr, rad_dp, sensor_x_dim, sensor_y_dim, e_terrain,
                n_buildings_in_chunk, multiprocessing, zone_geometry, surrounding_geometry, consider_windows,
                consider_floors]

    def updateParameters(self, parameters):
        import json

        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        parameters = {p.name: p for p in parameters}
        if not parameters['weather_name'].enabled:
            # user just chose scenario, read in defaults etc.

            # read values from scenario / or defaults
            weather_path = _cli_output(scenario_path, 'read-config', '--section', 'general', '--key', 'weather')
            if is_db_weather(weather_path):
                parameters['weather_name'].value = get_db_weather_name(weather_path)
                parameters['weather_path'].value = ''
            else:
                parameters['weather_name'].value = '<choose path from below>'
                parameters['weather_path'].value = weather_path

            for p in parameters.values():
                p.enabled = True
            parameters['scenario_path'].enabled = False  # user need to re-open dialog to change scenario path...

            # read values for the parameters
            radiation_config = json.loads(
                _cli_output(scenario_path, 'read-config-section', '--section', 'radiation-daysim'))
            parameters['rad_n'].value = radiation_config['rad-n']
            parameters['rad_af'].value = radiation_config['rad-af']
            parameters['rad_ab'].value = radiation_config['rad-ab']
            parameters['rad_ad'].value = radiation_config['rad-ad']
            parameters['rad_as'].value = radiation_config['rad-as']
            parameters['rad_ar'].value = radiation_config['rad-ar']
            parameters['rad_aa'].value = radiation_config['rad-aa']
            parameters['rad_lr'].value = radiation_config['rad-lr']
            parameters['rad_st'].value = radiation_config['rad-st']
            parameters['rad_sj'].value = radiation_config['rad-sj']
            parameters['rad_lw'].value = radiation_config['rad-lw']
            parameters['rad_dj'].value = radiation_config['rad-dj']
            parameters['rad_ds'].value = radiation_config['rad-ds']
            parameters['rad_dr'].value = radiation_config['rad-dr']
            parameters['rad_dp'].value = radiation_config['rad-dp']
            parameters['sensor_x_dim'].value = radiation_config['sensor-x-dim']
            parameters['sensor_y_dim'].value = radiation_config['sensor-y-dim']
            parameters['e_terrain'].value = radiation_config['e-terrain']
            parameters['n_buildings_in_chunk'].value = radiation_config['n-buildings-in-chunk']
            parameters['multiprocessing'].value = parse_boolean(radiation_config['multiprocessing'])
            parameters['zone_geometry'].value = radiation_config['zone-geometry']
            parameters['surrounding_geometry'].value = radiation_config['surrounding-geometry']
            parameters['consider_windows'].value = parse_boolean(radiation_config['consider-windows'])
            parameters['consider_floors'].value = parse_boolean(radiation_config['consider-floors'])

        parameters['weather_path'].enabled = parameters['weather_name'].value == '<choose path from below>'

    def updateMessages(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

    def execute(self, parameters, _):
        parameters = {p.name: p for p in parameters}
        scenario_path = parameters['scenario_path'].valueAsText
        weather_name = parameters['weather_name'].valueAsText
        weather_path = parameters['weather_path'].valueAsText

        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)

        run_cli_arguments = [scenario_path, 'radiation-daysim',
                             '--weather-path', weather_path]
        options = ['rad-n', 'rad-af', 'rad-ab', 'rad-ad', 'rad-as', 'rad-ar', 'rad-aa', 'rad-lr', 'rad-st', 'rad-sj',
                   'rad-lw', 'rad-dj', 'rad-ds', 'rad-dr', 'rad-dp', 'sensor-x-dim', 'sensor-y-dim', 'e-terrain',
                   'n-buildings-in-chunk', 'multiprocessing', 'zone-geometry', 'surrounding-geometry',
                   'consider-windows',
                   'consider-floors']
        for option in options:
            run_cli_arguments.append('--' + option)
            parameter = parameters[option.replace('-', '_')]
            if parameter.dataType == 'Boolean':
                run_cli_arguments.append('yes' if parameter.value else 'no')
            else:
                run_cli_arguments.append(parameter.value)

        run_cli(*run_cli_arguments)
        return


class RadiationTool(object):
    def __init__(self):
        self.label = 'Solar Insolation'
        self.category = 'Renewable Energy Assessment'
        self.description = 'Create radiation file'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name = arcpy.Parameter(
            displayName="Weather file (choose from list or enter full path to .epw file)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names()
        weather_name.enabled = False

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = 2014
        year.enabled = False

        latitude = arcpy.Parameter(
            displayName="Latitude",
            name="latitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        latitude.enabled = False

        longitude = arcpy.Parameter(
            displayName="Longitude",
            name="longitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        longitude.enabled = False

        return [scenario_path, weather_name, year, latitude, longitude]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        weather_parameter = parameters[1]
        year_parameter = parameters[2]
        latitude_parameter = parameters[3]
        longitude_parameter = parameters[4]

        weather_parameter.enabled = True
        year_parameter.enabled = True

        latitude_value = float(_cli_output(scenario_path, 'latitude'))
        longitude_value = float(_cli_output(scenario_path, 'longitude'))
        if not latitude_parameter.enabled:
            # only overwrite on first try
            latitude_parameter.value = latitude_value
            latitude_parameter.enabled = True

        if not longitude_parameter.enabled:
            # only overwrite on first try
            longitude_parameter.value = longitude_value
            longitude_parameter.enabled = True
        return

    def execute(self, parameters, messages):
        scenario_path = parameters[0].valueAsText
        weather_name = parameters[1].valueAsText
        year = parameters[2].value
        latitude = parameters[3].value
        longitude = parameters[4].value

        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = get_weather_path('.')

        # FIXME: use current arcgis databases...
        path_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))

        add_message('longitude: %s' % longitude)
        add_message('latitude: %s' % latitude)

        run_cli(scenario_path, 'radiation', '--arcgis-db', path_arcgis_db, '--latitude', latitude,
                '--longitude', longitude, '--year', year, '--weather-path', weather_path)
        return


def add_message(msg, **kwargs):
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    if len(kwargs):
        msg %= kwargs
    arcpy.AddMessage(msg)
    log_file = os.path.join(tempfile.gettempdir(), 'cea.log')
    with open(log_file, 'a') as log:
        log.write(str(msg))


def get_weather_names():
    """Shell out to cli.py and collect the list of weather files registered with the CEA"""

    def get_weather_names_inner():
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        command = [get_python_exe(), '-u', '-m', 'cea.cli', 'weather-files']
        p = subprocess.Popen(command, stdout=subprocess.PIPE, startupinfo=startupinfo)
        while True:
            line = p.stdout.readline()
            if line == '':
                # end of input
                break
            yield line.rstrip()

    return list(get_weather_names_inner())


def is_db_weather(weather_path):
    """True, if the ``weather_path`` is one of the pre-installed weather files that came with the CEA"""
    weather_name = get_db_weather_name(weather_path)
    if weather_name in get_weather_names():
        # could still be a custom weather file...
        db_weather_path = get_weather_path(weather_name)
        if os.path.dirname(db_weather_path) == os.path.dirname(weather_path):
            return True
    return False


def get_db_weather_name(weather_path):
    weather_name = os.path.splitext(os.path.basename(weather_path))[0]
    return weather_name


def get_weather_path(weather_name='Zug'):
    """Shell out to cli.py and find the path to the weather file"""
    return _cli_output(None, 'weather-path', weather_name)


def get_radiation(scenario_path):
    """Shell out to cli.py and find the path to the ``radiation.csv`` file for the scenario."""
    return _cli_output(scenario_path, 'locate', 'get_radiation')


def get_surface_properties(scenario_path):
    """Shell out to cli.py and find the path to the ``surface_properties.csv`` file for the scenario."""
    return _cli_output(scenario_path, 'locate', 'get_surface_properties')


def get_python_exe():
    """Return the path to the python interpreter that was used to install CEA"""
    try:
        with open(os.path.expanduser('~/cea_python.pth'), 'r') as f:
            python_exe = f.read().strip()
            return python_exe
    except:
        raise AssertionError("Could not find 'cea_python.pth' in home directory.")


def get_environment():
    """Return the system environment to use for the execution - this is based on the location of the python
    interpreter in ``get_python_exe``"""
    root_dir = os.path.dirname(get_python_exe())
    scripts_dir = os.path.join(root_dir, 'Scripts')
    env = os.environ.copy()
    env['PATH'] = ';'.join((root_dir, scripts_dir, os.environ['PATH']))
    return os.environ


def _cli_output(scenario_path=None, *args):
    """Run the CLI in a subprocess without showing windows and return the output as a string, whitespace
    is stripped from the output"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-m', 'cea.cli']
    if scenario_path:
        command.append('--scenario')
        command.append(scenario_path)
    command.extend(args)

    result = subprocess.check_output(command, startupinfo=startupinfo, env=get_environment())
    return result.strip()


def read_config_string(scenario_path, section, key):
    """Read a string value from the configuration file"""
    return _cli_output(scenario_path, 'read-config', '--section', section, '--key', key)


def read_config_boolean(scenario_path, section, key):
    """Read a boolean value from the configuration file"""
    boolean_states = {'0': False,
                      '1': True,
                      'false': False,
                      'no': False,
                      'off': False,
                      'on': True,
                      'true': True,
                      'yes': True}
    value = read_config_string(scenario_path, section, key).lower()
    if value in boolean_states:
        return boolean_states[value]
    else:
        return False


def write_config_string(scenario_path, section, key, value):
    """Write a string value to the configuration file"""
    run_cli(scenario_path, 'write-config', '--section', section, '--key', key, '--value', value)


def write_config_boolean(scenario_path, section, key, value):
    """Write a boolean value to the configuration file"""
    value = 'true' if value else 'false'
    run_cli(scenario_path, 'write-config', '--section', section, '--key', key, '--value', value)


def run_cli(scenario_path=None, *args):
    """Run the CLI in a subprocess without showing windows"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-u', '-m', 'cea.cli']
    if scenario_path:
        command.append('--scenario')
        command.append(scenario_path)
    command.extend(map(str, args))
    add_message(command)
    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=get_environment(), cwd=tempfile.gettempdir())
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        add_message(next_line.rstrip())
    stdout, stderr = process.communicate()
    add_message(stdout)
    add_message(stderr)


def parse_boolean(s):
    """Return True or False, depending on the value of ``s`` as defined by the ConfigParser library."""
    boolean_states = {'0': False,
                      '1': True,
                      'false': False,
                      'no': False,
                      'off': False,
                      'on': True,
                      'true': True,
                      'yes': True}
    if s.lower() in boolean_states:
        return boolean_states[s.lower()]
    return False



class HeatmapsTool(object):
    def __init__(self):
        self.label = 'Heatmaps'
        self.description = 'Generate maps representing hot and cold spots of energy consumption'
        self.category = 'Mapping and Visualization'
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

    def updateParameters(self, parameters):
        # scenario_path
        scenario_path = parameters[0].valueAsText
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        # path_variables
        file_names = [os.path.basename(_cli_output(scenario_path, 'locate', 'get_total_demand'))]
        file_names.extend(
            [f for f in os.listdir(_cli_output(scenario_path, 'locate', 'get_lca_emissions_results_folder'))
             if f.endswith('.csv')])
        path_variables = parameters[1]
        if not path_variables.value or path_variables.value not in file_names:
            path_variables.filter.list = file_names
            path_variables.value = file_names[0]
        # analysis_fields
        analysis_fields = parameters[2]
        if path_variables.value == file_names[0]:
            file_to_analyze = _cli_output(scenario_path, 'locate', 'get_total_demand')
        else:
            file_to_analyze = os.path.join(_cli_output(scenario_path, 'locate', 'get_lca_emissions_results_folder'),
                                           path_variables.value)
        import pandas as pd
        df = pd.read_csv(file_to_analyze)
        fields = df.columns.tolist()
        fields.remove('Name')
        analysis_fields.filter.list = list(fields)
        return

    def execute(self, parameters, _):
        scenario_path = parameters[0].valueAsText
        file_to_analyze = parameters[1].valueAsText
        analysis_fields = parameters[2].valueAsText.split(';')

        if file_to_analyze == os.path.basename(_cli_output(scenario_path, 'locate', 'get_total_demand')):
            file_to_analyze = _cli_output(scenario_path, 'locate', 'get_total_demand')
        else:
            file_to_analyze = os.path.join(_cli_output(scenario_path, 'locate', 'get_lca_emissions_results_folder'),
                                           file_to_analyze)
        run_cli(scenario_path, 'heatmaps', '--file-to-analyze', file_to_analyze, '--analysis-fields', *analysis_fields)

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

        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name = arcpy.Parameter(
            displayName="Weather file (choose from list or enter full path to .epw file)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names()

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

        return [scenario_path, weather_name, samples_folder, simulation_folder, num_simulations, sample_index,
                output_parameters]

    def updateParameters(self, parameters):
        import numpy as np

        # scenario_path
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        elif not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

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
        # scenario_path
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        elif not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

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

        # scenario_path
        scenario_path = parameters[0].valueAsText

        # weather_path
        weather_name = parameters[1].valueAsText
        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = get_weather_path()

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

        run_cli(None, 'sensitivity-demand-simulate', '--scenario-path', scenario_path, '--weather-path', weather_path,
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


class ExcelToDbfTool(object):
    def __init__(self):
        self.label = 'Convert Excel to DBF'
        self.description = 'xls => dbf'
        self.canRunInBackground = False
        self.category = 'Utilities'

    def getParameterInfo(self):
        input_path = arcpy.Parameter(
            displayName="Excel input file path",
            name="input_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        input_path.filter.list = ['xls']
        output_path = arcpy.Parameter(
            displayName="DBF output file path",
            name="output_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        output_path.filter.list = ['dbf']
        return [input_path, output_path]

    def execute(self, parameters, _):
        input_path = parameters[0].valueAsText
        output_path = parameters[1].valueAsText

        run_cli(None, 'excel-to-dbf', '--input-path', input_path, '--output-path', output_path)


class DbfToExcelTool(object):
    def __init__(self):
        self.label = 'Convert DBF to Excel'
        self.description = 'dbf => xls'
        self.canRunInBackground = False
        self.category = 'Utilities'

    def getParameterInfo(self):
        input_path = arcpy.Parameter(
            displayName="DBF input file path",
            name="input_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        input_path.filter.list = ['dbf']
        output_path = arcpy.Parameter(
            displayName="Excel output file path",
            name="output_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        output_path.filter.list = ['xls']

        return [input_path, output_path]

    def execute(self, parameters, _):
        input_path = parameters[0].valueAsText
        output_path = parameters[1].valueAsText

        run_cli(None, 'dbf-to-excel', '--input-path', input_path, '--output-path', output_path)


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
        run_cli(None, 'test')


def is_builtin_weather_path(weather_path):
    """Return True, if the weather path resolves to one of the builtin weather files shipped with the CEA."""
    return os.path.dirname(weather_path) == os.path.dirname(get_weather_path(weather_name='Zug'))

def builtin_weather_name(weather_path):
    """Return the name of the builtin weather file (assumes ``is_builtin_weather_path(weather_path) == True``"""
    return os.path.splitext(os.path.basename(weather_path))[0]
