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

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
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
        # self.tools = [HeatmapsTool, DemandGraphsTool,
        #               RadiationTool, ScenarioPlotsTool, BenchmarkGraphsTool]
        self.tools = [DemandTool, DataHelperTool, BenchmarkGraphsTool, EmissionsTool, EmbodiedEnergyTool, MobilityTool]


class DemandTool(object):
    """integrate the demand script with ArcGIS"""

    def __init__(self):
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
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

        return [scenario_path, weather_name]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

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
        scenario_path = parameters[0].valueAsText
        weather_name = parameters[1].valueAsText
        if weather_name in get_weather_names():
            weather_path = get_weather(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = get_weather()

        run_cli(scenario_path, 'demand', '--weather', weather_path)


class DataHelperTool(object):
    """
    integrate the cea/demand/preprocessing/properties.py script with ArcGIS.
    """

    def __init__(self):
        self.label = 'Data helper'
        self.description = 'Query characteristics of buildings and systems from statistical data'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
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
        run_cli(scenario_path, 'demand-helper', '--archetypes', *archetypes)

class BenchmarkGraphsTool(object):
    """Integrates the cea/analysis/benchmark.py tool with ArcGIS"""
    def __init__(self):
        self.label = 'Benchmark graphs'
        self.description = 'Create benchmark plots of scenarios in a folder'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
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
        import arcpy
        scenarios = parameters[0].valueAsText
        scenarios = scenarios.replace('"', '')
        scenarios = scenarios.replace("'", '')
        scenarios = scenarios.split(';')
        arcpy.AddMessage(scenarios)
        output_file = parameters[1].valueAsText
        run_cli(None, 'benchmark-graphs', '--output-file', output_file, '--scenarios', *scenarios)
        return


class EmissionsTool(object):
    def __init__(self):
        self.label = 'Emissions Operation'
        self.description = 'Calculate emissions and primary energy due to building operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
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


class EmbodiedEnergyTool(object):
    def __init__(self):
        self.label = 'Embodied Energy'
        self.description = 'Calculate the Emissions for operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
        yearcalc = arcpy.Parameter(
            displayName="Year to calculate",
            name="yearcalc",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

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
        self.label = 'Emissions Mobility'
        self.description = 'Calculate emissions and primary energy due to mobility'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
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


def add_message(msg, **kwargs):
    import arcpy
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


def get_weather(weather_name='default'):
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

    result = subprocess.check_output(command, startupinfo=startupinfo)
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
    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        add_message(next_line.rstrip())
    stdout, stderr = process.communicate()
    add_message(stdout)
    add_message(stderr)