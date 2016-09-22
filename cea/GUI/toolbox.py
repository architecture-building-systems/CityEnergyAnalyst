"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.
"""
import os
import tempfile
import arcpy
import cea
import cea.inputlocator
import cea.globalvar


__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def add_message(msg, **kwargs):
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    if len(kwargs):
        msg = msg % kwargs
    arcpy.AddMessage(msg)
    log_file = os.path.join(tempfile.gettempdir(), 'cea.log')
    with open(log_file, 'a') as log:
        log.write(msg)


class PropertiesTool(object):
    """
    integrate the properties script with ArcGIS.
    """

    def __init__(self):
        self.label = 'Data helper'
        self.description = 'Query characteristics of buildings and systems from statistical data'
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

    def execute(self, parameters, messages):
        from cea.demand.preprocessing.properties import properties

        scenario_path = parameters[0].valueAsText
        locator = cea.inputlocator.InputLocator(scenario_path)

        prop_thermal_flag = parameters[1]
        prop_architecture_flag = parameters[2]
        prop_HVAC_flag = parameters[3]
        prop_comfort_flag = parameters[3]
        prop_internal_loads_flag = parameters[3]
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message
        properties(locator=locator, prop_thermal_flag=prop_thermal_flag.value,
                   prop_architecture_flag=prop_architecture_flag.value, prop_hvac_flag=prop_HVAC_flag.value,
                   prop_comfort_flag=prop_comfort_flag.value, prop_internal_loads_flag=prop_internal_loads_flag.value,
                   gv=gv)


class DemandTool(object):
    """integrate the demand script with ArcGIS"""

    def __init__(self):
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
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
        locator = cea.inputlocator.InputLocator(None)
        weather_name.filter.list = locator.get_weather_names()

        return [scenario_path, weather_name]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import cea.demand.demand_main

        scenario_path = parameters[0].valueAsText
        locator = cea.inputlocator.InputLocator(scenario_path)

        weather_name = parameters[1].valueAsText
        if weather_name in locator.get_weather_names():
            weather_path = locator.get_weather(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = locator.get_default_weather()

        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message

        # find the version of python to use:
        import pandas
        import os
        import subprocess
        import sys

        # find python executable to use
        python_exe = os.path.normpath(os.path.join(os.path.dirname(pandas.__file__), '..', '..', '..', 'python.exe'))
        gv.log("Using python: %(python_exe)s", python_exe=python_exe)
        assert os.path.exists(python_exe), 'Python interpreter (see above) not found.'

        # find demand script
        demand_py = cea.demand.demand_main.__file__
        if os.path.splitext(demand_py)[1].endswith('c'):
            demand_py = demand_py[:-1]
        gv.log("Path to demand script: %(demand_py)s", demand_py=demand_py)

        # add root of CEAforArcGIS to python path
        cea_root_path = os.path.normpath(os.path.join(os.path.dirname(demand_py), '..', '..'))
        gv.log("Adding path to PYTHONPATH: %(path)s", path=cea_root_path)
        sys.path.append(cea_root_path)

        # run demand script in subprocess (for multiprocessing)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen([python_exe, '-u', demand_py, '--scenario', scenario_path, '--weather', weather_path],
                                   startupinfo=startupinfo,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=dict(os.environ, PYTHONPATH=cea_root_path))
        while True:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break
            gv.log(nextline.rstrip())
        stdout, stderr = process.communicate()
        gv.log(stdout)
        gv.log(stderr)

class EmbodiedEnergyTool(object):
    def __init__(self):
        self.label = 'Embodied Energy'
        self.description = 'Calculate the Emissions for operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
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

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import cea.analysis.embodied
        reload(cea.analysis.embodied)

        yearcalc = int(parameters[0].valueAsText)
        scenario_path = parameters[1].valueAsText
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message
        locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
        cea.analysis.embodied.lca_embodied(yearcalc=yearcalc, locator=locator, gv=gv)


class EmissionsTool(object):
    def __init__(self):
        self.label = 'Emissions Operation'
        self.description = 'Calculate emissions and primary energy due to building operation'
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

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        from cea.analysis.operation import lca_operation
        import cea.inputlocator
        scenario_path = parameters[0].valueAsText
        locator = cea.inputlocator.InputLocator(scenario_path)
        Qww_flag = parameters[1].value
        Qhs_flag = parameters[2].value
        Qcs_flag = parameters[3].value
        Qcdata_flag = parameters[4].value
        Qcrefri_flag = parameters[5].value
        Eal_flag = parameters[6].value
        Eaux_flag = parameters[7].value
        Epro_flag = parameters[8].value
        Edata_flag = parameters[9].value
        lca_operation(locator=locator, Qww_flag=Qww_flag, Qhs_flag=Qhs_flag, Qcs_flag=Qcs_flag, Qcdata_flag=Qcdata_flag,
                      Qcrefri_flag=Qcrefri_flag, Eal_flag=Eal_flag, Eaux_flag=Eaux_flag, Epro_flag=Epro_flag,
                      Edata_flag=Edata_flag)


class GraphsDemandTool(object):
    def __init__(self):
        self.label = 'Demand graphs'
        self.description = 'Calculate Graphs of the Demand'
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
        import pandas as pd
        scenario_path = parameters[0].valueAsText
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        analysis_fields = parameters[1]
        locator = cea.inputlocator.InputLocator(scenario_path)
        df_total_demand = pd.read_csv(locator.get_total_demand())
        total_fields = set(df_total_demand.columns.tolist())
        first_building = df_total_demand['Name'][0]
        df_building = pd.read_csv(locator.get_demand_results_file(first_building))
        fields = set(df_building.columns.tolist())
        fields.remove('DATE')
        fields.remove('Name')

        # remove fields in demand results files that do not have a corresponding field in the totals file
        bad_fields = set(field for field in fields if not field.split('_')[0] + "_MWhyr" in total_fields)
        fields = fields - bad_fields

        analysis_fields.filter.list = list(fields)
        return

    def execute(self, parameters, messages):
        import cea.plots.graphs
        reload(cea.plots.graphs)
        
        scenario_path = parameters[0].valueAsText
        analysis_fields = parameters[1].valueAsText.split(';')[:4]  # max 4 fields for analysis
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message

        # find the version of python to use:
        import pandas
        import os
        import subprocess
        import sys

        # find python executable to use
        python_exe = os.path.normpath(os.path.join(os.path.dirname(pandas.__file__), '..', '..', '..', 'python.exe'))
        gv.log("Using python: %(python_exe)s", python_exe=python_exe)
        assert os.path.exists(python_exe), 'Python interpreter (see above) not found.'

        # find demand script
        graphs_py = cea.plots.graphs.__file__
        if os.path.splitext(graphs_py)[1].endswith('c'):
            graphs_py = graphs_py[:-1]
        gv.log("Path to demand script: %(graphs_py)s", graphs_py=graphs_py)

        # add root of CEAforArcGIS to python path
        cea_root_path = os.path.normpath(os.path.join(os.path.dirname(graphs_py), '..', '..'))
        gv.log("Adding path to PYTHONPATH: %(path)s", path=cea_root_path)
        sys.path.append(cea_root_path)

        # run demand script in subprocess (for multiprocessing)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            [python_exe, '-u', graphs_py, '--scenario', scenario_path, '--analysis_fields', ';'.join(analysis_fields)],
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=dict(os.environ, PYTHONPATH=cea_root_path))
        while True:
            next_line = process.stdout.readline()
            if next_line == '' and process.poll() is not None:
                break
            gv.log(next_line.rstrip())
        stdout, stderr = process.communicate()
        gv.log(stdout)
        gv.log(stderr)


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


class RadiationTool(object):
    def __init__(self):
        self.label = 'Radiation'
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
        locator = cea.inputlocator.InputLocator(None)
        weather_name.filter.list = locator.get_weather_names()

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = 2014

        return [scenario_path, weather_name, year]

    def execute(self, parameters, messages):
        import cea

        scenario_path = parameters[0].valueAsText
        weather_name = parameters[1].valueAsText
        year = parameters[2].value

        locator = cea.inputlocator.InputLocator(scenario_path)
        if weather_name in locator.get_weather_names():
            weather_path = locator.get_weather(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = locator.get_default_weather()

        # FIXME: use current arcgis databases...
        path_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))

        locator = cea.inputlocator.InputLocator(scenario_path)
        latitude, longitude = self.get_location(locator)
        arcpy.AddMessage('longitude: %s' % longitude)
        arcpy.AddMessage('latitude: %s' % latitude)

        import cea.resources.radiation
        reload(cea.resources.radiation)
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message
        cea.resources.radiation.solar_radiation_vertical(locator=locator, path_arcgis_db=path_arcgis_db, latitude=latitude,
                                                         longitude=longitude, year=year, gv=gv, weather_path=weather_path)
        return

    def get_location(self, locator):
        """returns (latitude, longitude) for a given scenario."""
        import fiona
        with fiona.open(locator.get_building_geometry()) as shp:
            longitude = shp.crs['lon_0']
            latitude = shp.crs['lat_0']
        return latitude, longitude


class ScenarioPlotsTool(object):
    def __init__(self):
        self.label = 'Scenario Plots'
        self.description = 'Create summary plots of scenarios in a folder'
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

        arcpy.AddMessage(scenarios)

        import cea.plots.scenario_plots
        reload(cea.plots.scenario_plots)
        cea.plots.scenario_plots.plot_scenarios(scenarios=scenarios, output_file=output_file)
        return


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
        scenarios = parameters[0].valueAsText
        scenarios = scenarios.replace('"', '')
        scenarios = scenarios.replace("'", '')
        scenarios = scenarios.split(';')
        arcpy.AddMessage(scenarios)
        output_file = parameters[1].valueAsText

        from cea.analysis import benchmark
        reload(benchmark)
        locator_list = [cea.inputlocator.InputLocator(scenario_path=scenario) for scenario in scenarios]
        benchmark.benchmark(locator_list=locator_list, output_file=output_file)
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

        return [scenario_path]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        from cea.analysis.mobility import lca_mobility

        scenario_path = parameters[0].valueAsText
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message
        locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
        lca_mobility(locator=locator)
