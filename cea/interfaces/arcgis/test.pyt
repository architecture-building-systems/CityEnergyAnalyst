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
        self.tools = [PlotsTool]


class PlotsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots'
        self.label = 'Plots'
        self.description = 'Create plots for single or gorups of buildings'
        self.canRunInBackground = False
        self.category = 'Visualization'


if __name__ == '__main__':
    parameters = list(get_parameters('photovoltaic'))



