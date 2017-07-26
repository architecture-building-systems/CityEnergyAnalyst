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
import arcpy

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
                      OperationTool, EmbodiedTool, MobilityTool,SolarTechnologyTool,
                      DemandGraphsTool, ScenarioPlotsTool, RadiationTool, HeatmapsTool]

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
                                                parameterType="Optional", direction="Input", category="end use intensity")
        eui_heating_threshold.value = 50
        eui_heating_threshold.enabled = False

        cb_eui_hot_water_threshold = arcpy.Parameter(displayName="Enable end use intensity threshold for hot water",
                                                     name="cb_eui_hot_water_threshold", datatype="GPBoolean",
                                                     parameterType="Required", direction="Input", category="end use intensity")
        cb_eui_hot_water_threshold.value = False
        cb_eui_hot_water_threshold.enabled = False

        eui_hot_water_threshold = arcpy.Parameter(displayName="End use intensity threshold for hot water",
                                                  name="eui_hot_water_threshold", datatype="GPLong",
                                                  parameterType="Optional", direction="Input", category="end use intensity")
        eui_hot_water_threshold.value = 50
        eui_hot_water_threshold.enabled = False

        cb_eui_cooling_threshold = arcpy.Parameter(displayName="Enable end use intensity threshold for cooling",
                                                   name="cb_eui_cooling_threshold", datatype="GPBoolean",
                                                   parameterType="Required", direction="Input", category="end use intensity")
        cb_eui_cooling_threshold.value = False
        cb_eui_cooling_threshold.enabled = False

        eui_cooling_threshold = arcpy.Parameter(displayName="End use intensity threshold for cooling",
                                                name="eui_cooling_threshold", datatype="GPLong",
                                                parameterType="Optional", direction="Input", category="end use intensity")
        eui_cooling_threshold.value = 4
        eui_cooling_threshold.enabled = False

        cb_eui_electricity_threshold = arcpy.Parameter(displayName="Enable end use intensity threshold for electricity",
                                                       name="cb_eui_electricity_threshold", datatype="GPBoolean",
                                                       parameterType="Required", direction="Input", category="end use intensity")
        cb_eui_electricity_threshold.value = False
        cb_eui_electricity_threshold.enabled = False

        eui_electricity_threshold = arcpy.Parameter(displayName="End use intensity threshold for electricity",
                                                    name="eui_electricity_threshold", datatype="GPLong",
                                                    parameterType="Optional", direction="Input", category="end use intensity")
        eui_electricity_threshold.value = 20
        eui_electricity_threshold.enabled = False

        cb_emissions_operation_threshold = arcpy.Parameter(
            displayName="Enable threshold for emissions due to operation", name="cb_emissions_operation_threshold",
            datatype="GPBoolean", parameterType="Required", direction="Input", category="emissions")
        cb_emissions_operation_threshold.value = False
        cb_emissions_operation_threshold.enabled = False

        emissions_operation_threshold = arcpy.Parameter(displayName="Threshold for emissions due to operation",
                                                        name="emissions_operation_threshold", datatype="GPLong",
                                                        parameterType="Optional", direction="Input", category="emissions")
        emissions_operation_threshold.value = 30
        emissions_operation_threshold.enabled = False

        cb_heating_costs_threshold = arcpy.Parameter(displayName="Enable threshold for heating costs",
                                                     name="cb_heating_costs_threshold", datatype="GPBoolean",
                                                     parameterType="Required", direction="Input", category="operation costs")
        cb_heating_costs_threshold.value = False
        cb_heating_costs_threshold.enabled = False

        heating_costs_threshold = arcpy.Parameter(displayName="Threshold for heating costs",
                                                  name="heating_costs_threshold", datatype="GPLong",
                                                  parameterType="Optional", direction="Input", category="operation costs")
        heating_costs_threshold.value = 2
        heating_costs_threshold.enabled = False

        cb_hot_water_costs_threshold = arcpy.Parameter(displayName="Enable threshold for hot water costs",
                                                       name="cb_hot_water_costs_threshold", datatype="GPBoolean",
                                                       parameterType="Required", direction="Input", category="operation costs")
        cb_hot_water_costs_threshold.value = False
        cb_hot_water_costs_threshold.enabled = False

        hot_water_costs_threshold = arcpy.Parameter(displayName="Threshold for hot water costs",
                                                    name="hot_water_costs_threshold", datatype="GPLong",
                                                    parameterType="Optional", direction="Input", category="operation costs")
        hot_water_costs_threshold.value = 2
        hot_water_costs_threshold.enabled = False

        cb_cooling_costs_threshold = arcpy.Parameter(displayName="Enable threshold for cooling costs",
                                                     name="cb_cooling_costs_threshold", datatype="GPBoolean",
                                                     parameterType="Required", direction="Input", category="operation costs")
        cb_cooling_costs_threshold.value = False
        cb_cooling_costs_threshold.enabled = False

        cooling_costs_threshold = arcpy.Parameter(displayName="Threshold for cooling costs",
                                                  name="cooling_costs_threshold", datatype="GPLong",
                                                  parameterType="Optional", direction="Input", category="operation costs")
        cooling_costs_threshold.value = 2
        cooling_costs_threshold.enabled = False

        cb_electricity_costs_threshold = arcpy.Parameter(displayName="Enable threshold for electricity costs",
                                                         name="cb_electricity_costs_threshold", datatype="GPBoolean",
                                                         parameterType="Required", direction="Input", category="operation costs")
        cb_electricity_costs_threshold.value = False
        cb_electricity_costs_threshold.enabled = False

        electricity_costs_threshold = arcpy.Parameter(displayName="Threshold for electricity costs",
                                                      name="electricity_costs_threshold", datatype="GPLong",
                                                      parameterType="Optional", direction="Input", category="operation costs")
        electricity_costs_threshold.value = 2
        electricity_costs_threshold.enabled = False

        cb_heating_losses_threshold = arcpy.Parameter(displayName="Enable threshold for HVAC system losses from heating",
                                                      name="cb_heating_losses_threshold", datatype="GPBoolean",
                                                      parameterType="Required", direction="Input", category="HVAC system losses")
        cb_heating_losses_threshold.value = False
        cb_heating_losses_threshold.enabled = False

        heating_losses_threshold = arcpy.Parameter(displayName="Threshold for HVAC system losses from heating",
                                                   name="heating_losses_threshold", datatype="GPLong",
                                                   parameterType="Optional", direction="Input", category="HVAC system losses")
        heating_losses_threshold.value = 15
        heating_losses_threshold.enabled = False

        cb_hot_water_losses_threshold = arcpy.Parameter(
            displayName="Enable threshold for HVAC system losses from hot water", name="cb_hot_water_losses_threshold",
            datatype="GPBoolean", parameterType="Required", direction="Input", category="HVAC system losses")
        cb_hot_water_losses_threshold.value = False
        cb_hot_water_losses_threshold.enabled = False

        hot_water_losses_threshold = arcpy.Parameter(displayName="Threshold for HVAC system losses from hot water",
                                                     name="hot_water_losses_threshold", datatype="GPLong",
                                                     parameterType="Optional", direction="Input", category="HVAC system losses")
        hot_water_losses_threshold.value = 15
        hot_water_losses_threshold.enabled = False

        cb_cooling_losses_threshold = arcpy.Parameter(displayName="Enable threshold for HVAC system losses from cooling",
                                                      name="cb_cooling_losses_threshold", datatype="GPBoolean",
                                                      parameterType="Required", direction="Input", category="HVAC system losses")
        cb_cooling_losses_threshold.value = False
        cb_cooling_losses_threshold.enabled = False

        cooling_losses_threshold = arcpy.Parameter(displayName="Threshold for HVAC system losses from cooling",
                                                   name="cooling_losses_threshold", datatype="GPLong",
                                                   parameterType="Optional", direction="Input", category="HVAC system losses")
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
            displayName="Weather file",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        weather_name.filter.list = get_weather_names() + ['<choose path from below>']

        weather_path = arcpy.Parameter(
            displayName="Path to .epw file",
            name="weather_path",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input")
        weather_path.filter.list = ['epw']

        dynamic_infiltration = arcpy.Parameter(
            displayName="Use dynamic infiltration model (slower)",
            name="dynamic_infiltration",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        return [scenario_path, weather_name, weather_path, dynamic_infiltration]

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
            previous_run = ConfigurationStore().read(scenario_path, 'demand')
            if previous_run:
                for key in previous_run.keys():
                    p = parameters[key]
                    p.value = previous_run[key]
            parameters['weather_path'].enabled = parameters['weather_name'].value == '<choose path from below>'
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

        args = [scenario_path, 'demand', '--weather', weather_path]
        if use_dynamic_infiltration_calculation:
            args.append('--use-dynamic-infiltration-calculation')
        run_cli(*args)
        ConfigurationStore().write(scenario_path,
                                   'demand', {'weather_name': weather_name,
                                              'weather_path': weather_path,
                                              'dynamic_infiltration': use_dynamic_infiltration_calculation})


class DataHelperTool(object):
    """
    integrate the cea/demand/preprocessing/properties.py script with ArcGIS.
    """

    def __init__(self):
        # map from CLI flag names to the parameter names used in the ArcGIS interface
        self.flag_mapping = {'thermal': 'prop_thermal_flag', 'architecture': 'prop_architecture_flag',
                             'HVAC': 'prop_HVAC_flag', 'comfort': 'prop_comfort_flag',
                             'internal-loads': 'prop_internal_loads_flag'}
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
        prop_thermal_flag.enabled = False
        prop_architecture_flag = arcpy.Parameter(
            displayName="Generate architectural properties",
            name="prop_architecture_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_architecture_flag.enabled = False
        prop_HVAC_flag = arcpy.Parameter(
            displayName="Generate technical systems properties",
            name="prop_HVAC_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_HVAC_flag.enabled = False
        prop_comfort_flag = arcpy.Parameter(
            displayName="Generate comfort properties",
            name="prop_comfort_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_comfort_flag.enabled = False
        prop_internal_loads_flag = arcpy.Parameter(
            displayName="Generate internal loads properties",
            name="prop_internal_loads_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_internal_loads_flag.enabled = False
        return [scenario_path, prop_thermal_flag, prop_architecture_flag, prop_HVAC_flag, prop_comfort_flag,
                prop_internal_loads_flag]

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

        # first time only (for a new scenario_path)
        if not parameters[1].enabled:
            for p in parameters[1:]:
                p.enabled = True
            parameters = {p.name: p for p in parameters}
            flags = ConfigurationStore().read(scenario_path, 'data-helper')
            if flags:
                for key in flags.keys():
                    if key in self.flag_mapping:
                        p = parameters[self.flag_mapping[key]]
                        p.value = flags[key]

    def execute(self, parameters, _):
        scenario_path = parameters[0].valueAsText
        flags = {'thermal': parameters[1].value,
                 'architecture': parameters[2].value,
                 'HVAC': parameters[3].value,
                 'comfort': parameters[4].value,
                 'internal-loads': parameters[5].value}

        ConfigurationStore().write(scenario_path, 'data-helper', flags)

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
        Qhs_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to space heating.",
            name="Qhs_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcs_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to space cooling.",
            name="Qcs_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcdata_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to servers cooling.",
            name="Qcdata_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcrefri_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to refrigeration.",
            name="Qcrefri_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Eal_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to appliances and lighting.",
            name="Eal_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Eaux_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to auxiliary electricity.",
            name="Eaux_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Epro_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to electricity in industrial processes.",
            name="Epro_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Edata_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to electricity consumption in data centers.",
            name="Edata_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        return [scenario_path, Qww_flag, Qhs_flag, Qcs_flag, Qcdata_flag, Qcrefri_flag, Eal_flag, Eaux_flag, Epro_flag,
                Edata_flag]

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
            previous_run = ConfigurationStore().read(scenario_path, 'emissions')
            if previous_run:
                for key in previous_run.keys():
                    p = parameters[key + '_flag']
                    p.value = previous_run[key]


    def execute(self, parameters, _):
        parameters = {p.name: p for p in parameters}
        scenario_path = parameters['scenario_path'].valueAsText
        flags = {key.split('_')[0]: parameter.value for key, parameter in parameters.items()
                 if not key == 'scenario_path'}
        extra_files_to_create = [key for key in flags if flags[key]]
        run_cli(scenario_path, 'emissions', '--extra-files-to-create', *extra_files_to_create)
        ConfigurationStore().write(scenario_path, 'emissions', flags)


class EmbodiedTool(object):
    def __init__(self):
        self.label = 'LCA Construction'
        self.description = 'Calculate the emissions and primary energy for building construction and decommissioning'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        yearcalc = arcpy.Parameter(
            displayName="Year to calculate",
            name="yearcalc",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        return [scenario_path, yearcalc]

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
            previous_run = ConfigurationStore().read(scenario_path, 'embodied-energy')
            if previous_run:
                    parameters['yearcalc'].value = previous_run['yearcalc']

    def execute(self, parameters, _):
        parameters = {p.name: p for p in parameters}
        scenario_path = parameters['scenario_path'].valueAsText
        year_to_calculate = parameters['yearcalc'].value
        run_cli(scenario_path, 'embodied-energy', '--year-to-calculate', year_to_calculate)
        ConfigurationStore().write(scenario_path, 'embodied-energy', {'yearcalc': year_to_calculate})


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
        return [scenario_path, analysis_fields]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        analysis_fields = parameters[1]
        if scenario_path is None:
            analysis_fields.enabled = False
            return
        if not os.path.exists(scenario_path):
            analysis_fields.enabled = False
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        analysis_fields.enabled = True
        fields = _cli_output(scenario_path, 'demand-graphs', '--list-fields').split()
        analysis_fields.filter.list = list(fields)
        previous_run = ConfigurationStore().read(scenario_path, 'demand-graphs')
        if previous_run:
            analysis_fields.value = previous_run['analysis_fields']

    def execute(self, parameters, messages):
        scenario_path = parameters[0].valueAsText
        analysis_fields = parameters[1].valueAsText.split(';')[:4]  # max 4 fields for analysis
        run_cli(scenario_path, 'demand-graphs', '--analysis-fields', *analysis_fields)
        ConfigurationStore().write(scenario_path, 'demand-graphs', {'analysis_fields': analysis_fields})


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


class SolarTechnologyTool(object):
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

        pvonroof = arcpy.Parameter(
            displayName="Considering panels on roofs",
            name="pvonroof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        pvonroof.value = True

        pvonwall = arcpy.Parameter(
            displayName="Considering panels on walls",
            name="pvonwall",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        pvonwall.value = True

        worst_hour = arcpy.Parameter(
            displayName="worst hour (the hour of sunrise on the solar solstice at the site)",
            name="worst_hour",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        worst_hour.value = 8744

        type_PVpanel = arcpy.Parameter(
            displayName="PV technology to use",
            name="type_PVpanel",
            datatype="String",
            parameterType="Required",
            direction="Input")
        type_PVpanel.filter.list = ['monocrystalline', 'polycrystalline', 'amorphous']

        min_radiation = arcpy.Parameter(
            displayName="filtering surfaces with low radiation potential (% of the maximum radiation in the area)",
            name="min_radiation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        min_radiation.value = 0.75

        return [scenario_path, weather_name, year, latitude, longitude, pvonroof, pvonwall, worst_hour,
                type_PVpanel, min_radiation]

    def updateParameters(self, parameters):
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

        # scenario passes test
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
        scenario_path = parameters[0].valueAsText
        weather_name = parameters[1].valueAsText
        year = parameters[2].value
        latitude = parameters[3].value
        longitude = parameters[4].value
        pvonroof = parameters[5].value
        pvonwall = parameters[6].value
        worst_hour = parameters[7].value
        type_PVpanel = {'monocrystalline': 'PV1',
                        'polycrystalline': 'PV2',
                        'amorphous': 'PV3'}[parameters[8].value]
        min_radiation = parameters[9].value

        date_start = str(year) + '-01-01'

        if weather_name in get_weather_names():
            weather_path = get_weather_path(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = get_weather_path('.')

        add_message('longitude: %s' % longitude)
        add_message('latitude: %s' % latitude)

        run_cli_arguments = [scenario_path, 'photovoltaic', '--latitude', latitude, '--longitude', longitude,
                             '--weather-path', weather_path, '--worst-hour', worst_hour, '--type-PVpanel', type_PVpanel,
                             '--min-radiation', min_radiation, '--date-start', date_start]
        if pvonroof:
            run_cli_arguments.append('--pvonroof')
        if pvonwall:
            run_cli_arguments.append('--pvonwall')

        run_cli(*run_cli_arguments)
        return


class RadiationTool(object):
    def __init__(self):
        self.label = 'Solar Insolation'
        self.category= 'Renewable Energy Assessment'
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


def get_weather_path(weather_name='default'):
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
    os.environ['PATH'] = ';'.join((root_dir, scripts_dir, os.environ['PATH']))
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
                               env=get_environment())
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        add_message(next_line.rstrip())
    stdout, stderr = process.communicate()
    add_message(stdout)
    add_message(stderr)


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

class ConfigurationStore(object):
    """Read and write the parameters of a tool for populating the interface for subsequent runs.
    The parameters are written to a section called "ArcGIS", with the tool name as the key. The value is
    a json dictionary of the values for each parameter.
    """
    def read(self, scenario_path, tool):
        import json
        data = _cli_output(scenario_path, 'read-config', '--section', 'ArcGIS', '--key', tool)
        if len(data):
            return json.loads(data)
        return None

    def write(self, scenario_path, tool, parameters):
        """Assuming parameters is a dictionary of values to store, write them as a json string to the store"""
        import json
        data = json.dumps(parameters)
        run_cli(scenario_path, 'write-config', '--section', 'ArcGIS', '--key', tool, '--value', data)
