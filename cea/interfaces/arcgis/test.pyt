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
        self.tools = [DemandGraphsTool]


class DemandGraphsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'demand-graphs'
        self.label = 'Plots'
        self.description = 'Plot demand time-series data'
        self.category = 'Dynamic Demand Forecasting'
        self.canRunInBackground = False