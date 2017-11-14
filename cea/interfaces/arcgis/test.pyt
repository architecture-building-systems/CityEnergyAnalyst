import os
import subprocess
import tempfile

import cea.config
reload(cea.config)
import cea.inputlocator
import cea.interfaces.arcgis.arcgishelper
reload(cea.interfaces.arcgis.arcgishelper)
from cea.interfaces.arcgis.arcgishelper import *

class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'Testing the City Energy Analyst'
        self.alias = 'testcea'
        self.tools = [DbfToExcelTool]


class DbfToExcelTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'dbf-to-excel'
        self.label = 'Convert DBF to Excel'
        self.description = 'dbf => xls'
        self.canRunInBackground = False
        self.category = 'Utilities'



