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
        self.tools = [PhotovoltaicPanelsTool]


class PhotovoltaicPanelsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'photovoltaic'
        self.label = 'Photovoltaic Panels'
        self.description = 'Calculate electricity production from solar photovoltaic technologies'
        self.category = 'Dynamic Supply Systems'
        self.canRunInBackground = False


if __name__ == '__main__':
    parameters = list(get_parameters('photovoltaic'))



