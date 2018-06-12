import os
import subprocess
import tempfile

import cea.config
reload(cea.config)
import cea.inputlocator
import cea.interfaces.arcgis.arcgishelper
reload(cea.interfaces.arcgis.arcgishelper)
from cea.interfaces.arcgis.arcgishelper import *

from cea.interfaces.arcgis.modules import arcpy

class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'Testing the City Energy Analyst'
        self.alias = 'testcea'
        self.tools = [CopyDefaultDatabases]


class CopyDefaultDatabases(CeaTool):
    def __init__(self):
        self.cea_tool = 'copy-default-databases'
        self.label = 'Copy Default Databases'
        self.description = 'Copy default databsases to scenario based on region'
        self.category = 'Data Management'
        self.canRunInBackground = False


