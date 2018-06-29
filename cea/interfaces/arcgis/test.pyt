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
        self.tools = [MulticriteriaTool, PlotsTool]

class MulticriteriaTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'multi-criteria-analysis'
        self.label = 'Multicriteria analysis'
        self.description = 'Perform multicriteria analysis for results of optimzation of an urban scenario'
        self.canRunInBackground = False
        self.category = 'Analysis'

class PlotsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'plots'
        self.label = 'Plots basic'
        self.description = 'Create plots for the default energy system of an urban scenario'
        self.canRunInBackground = False
        self.category = 'Visualization'