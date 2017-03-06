"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.
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
        p = subprocess.Popen(['python', '-u', 'cea.py', 'weather-files'], stdout=subprocess.PIPE)
        while True:
            line = p.stdout.readline()
            if line == '':
                # end of input
                break
            yield line.rstrip()
    return list(get_weather_names_inner())
