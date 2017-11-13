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
        self.tools = [OperationCostsTool]


class OperationCostsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'operation-costs'
        self.label = 'Operation Costs'
        self.description = 'Calculate energy costs due to building operation'
        self.category = 'Cost Analysis'
        self.canRunInBackground = False