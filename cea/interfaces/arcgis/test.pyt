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
        self.tools = [ExcelToShapefileTool, ShapefileToExcelTool]


class ExcelToShapefileTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'excel-to-shapefile'
        self.label = 'Excel to Shapefile'
        self.description = 'xls => shp'
        self.canRunInBackground = False
        self.category = 'Utilities'


class ShapefileToExcelTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'shapefile-to-excel'
        self.label = 'Shapefile to Excel'
        self.description = 'shp => xls'
        self.canRunInBackground = False
        self.category = 'Utilities'



