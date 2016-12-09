"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.
"""
import os
import tempfile

import arcpy

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def add_message(msg, **kwargs):
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    if len(kwargs):
        msg = msg % kwargs
    arcpy.AddMessage(msg)
    log_file = os.path.join(tempfile.gettempdir(), 'cea.log')
    with open(log_file, 'a') as log:
        log.write(msg)
