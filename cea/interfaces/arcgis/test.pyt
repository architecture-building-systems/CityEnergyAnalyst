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
        self.tools = [ExtractReferenceCaseTool]


class ExtractReferenceCaseTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'extract-reference-case'
        self.label = 'Extract reference case'
        self.description = 'Extract sample reference case to folder'
        self.canRunInBackground = False
        self.category = 'Utilities'



