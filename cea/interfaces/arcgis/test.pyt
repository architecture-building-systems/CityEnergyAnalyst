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
        self.tools = [DataHelperTool, TestTool]


class TestTool(object):
    def __init__(self):
        self.label = 'testing'
        self.description = 'testing some stuff'
        self.canRunInBackground = False

    def getParameterInfo(self):
        parameter = arcpy.Parameter(displayName="test-parameter", name="testparameter", datatype='DEFile',
                                    parameterType='Optional', direction='Output')
        #parameter.filter.list = ['xls']
        parameter.value = 'C:/reference-case-zurich/baseline/inputs/building-properties/technical_systems.xls'
        return [parameter]

class DataHelperTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'data-helper'
        self.label = 'Data helper'
        self.description = 'Query characteristics of buildings and systems from statistical data'
        self.category = 'Data Management'
        self.canRunInBackground = False




