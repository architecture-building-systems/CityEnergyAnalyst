import os
import subprocess
import tempfile

import cea.config
import cea.inputlocator
import cea.interfaces.arcgis.arcgishelper
reload(cea.interfaces.arcgis.arcgishelper)
from cea.interfaces.arcgis.arcgishelper import *

class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'Testing the City Energy Analyst'
        self.alias = 'testcea'
        self.tools = [EmbodiedTool]


class EmbodiedTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'embodied-energy'
        self.label = 'LCA Construction'
        self.description = 'Calculate the emissions and primary energy for building construction and decommissioning'
        self.category = 'Life Cycle Analysis'
        self.canRunInBackground = False