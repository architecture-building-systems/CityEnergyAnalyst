import arcpy

import cea
import cea.demand
import cea.globalvar
import cea.inputlocator
from cea.GUI.toolbox import add_message

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