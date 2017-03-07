"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.

These tools shell out to ``cea.py`` because the ArcGIS python version is old and we would like to decouple the
python version used by CEA from the ArcGIS version.
"""
import os
import subprocess
import tempfile

import exceptions

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def add_message(msg, **kwargs):
    import arcpy
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    if len(kwargs):
        msg %= kwargs
    arcpy.AddMessage(msg)
    log_file = os.path.join(tempfile.gettempdir(), 'cea.log')
    with open(log_file, 'a') as log:
        log.write(msg)


def get_weather_names():
    """Shell out to cea.py and collect the list of weather files registered with the CEA"""
    def get_weather_names_inner():
        p = subprocess.Popen([get_python_exe(), '-u', '-m', 'cea.cea', 'weather-files'], stdout=subprocess.PIPE)
        while True:
            line = p.stdout.readline()
            if line == '':
                # end of input
                break
            yield line.rstrip()
    return list(get_weather_names_inner())


def get_weather(weather_name='default'):
    """Shell out to cea.py and find the path to the weather file"""
    weather_path = subprocess.check_output(
        [get_python_exe(), '-m', 'cea.cea', 'weather-path', weather_name]
    )
    return weather_path


def get_radiation(scenario_path):
    """Shell out to cea.py and find the path to the ``radiation.csv`` file for the scenario."""
    radiation = subprocess.check_output(
        [get_python_exe(), '-m', 'cea.cea', '--scenario', scenario_path, 'location', 'get_radiation'])
    return radiation


def get_surface_properties(scenario_path):
    """Shell out to cea.py and find the path to the ``surface_properties.csv`` file for the scenario."""
    surface_properties = subprocess.check_output(
        [get_python_exe(), '-m', 'cea.cea', '--scenario', scenario_path, 'location', 'get_surface_properties'])
    return surface_properties


def get_python_exe():
    """Return the path to the python interpreter that was used to install CEA"""
    try:
        with open(os.path.expanduser('~/cea_python.pth'), 'r') as f:
            python_exe = f.read().strip()
    except:
        raise exceptions.AssertionError("Could not find 'cea_python.pth' in home directory.")
