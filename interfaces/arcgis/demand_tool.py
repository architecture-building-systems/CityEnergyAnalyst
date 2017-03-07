import os
import subprocess

import toolbox

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


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
        weather_name.filter.list = toolbox.get_weather_names()

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
        if not os.path.exists(toolbox.get_radiation(scenario_path)):
            parameters[0].setErrorMessage("No radiation data found for scenario. Run radiation script first.")
        if not os.path.exists(toolbox.get_surface_properties(scenario_path)):
            parameters[0].setErrorMessage("No radiation data found for scenario. Run radiation script first.")
        return

    def execute(self, parameters, _):
        scenario_path = parameters[0].valueAsText
        weather_name = parameters[1].valueAsText
        if weather_name in toolbox.get_weather_names():
            weather_path = toolbox.get_weather(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = toolbox.get_weather()

        # find python executable to use
        python_exe = toolbox.get_python_exe()
        toolbox.add_message("Using python: %(python_exe)s", python_exe=python_exe)
        assert os.path.exists(python_exe), 'Python interpreter (see above) not found.'

        # run demand script in subprocess (for multiprocessing)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            [python_exe, '-u', '-m', 'cea.cea', '--scenario', scenario_path, 'demand', '--weather', weather_path],
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        while True:
            next_line = process.stdout.readline()
            if next_line == '' and process.poll() is not None:
                break
            toolbox.add_message(next_line.rstrip())
        stdout, stderr = process.communicate()
        toolbox.add_message(stdout)
        toolbox.add_message(stderr)
