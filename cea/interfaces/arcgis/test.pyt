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
        self.tools = [DemandTool]


class DemandTool(CeaTool):
    """integrate the demand script with ArcGIS"""

    def __init__(self):
        self.cea_tool = 'demand'
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.category = 'Demand forecasting'
        self.canRunInBackground = False
        with open(r'c:\Users\darthoma\polybox\cea.log', 'a') as f:
            import datetime
            f.write('DemandTool.__init__: %s\n' % datetime.datetime.now())

    def getParameterInfo(self):
        with open(r'c:\Users\darthoma\polybox\cea.log', 'a') as f:
            import datetime
            f.write('DemandTool.getParameterInfo: %s\n' % datetime.datetime.now())
        return super(DemandTool, self).getParameterInfo()

    def updateParameters(self, parameters):
        with open(r'c:\Users\darthoma\polybox\cea.log', 'a') as f:
            import datetime
            f.write('DemandTool.updateParameters: %s\n' % datetime.datetime.now())
            for parameter in parameters:
                f.write('- %s: %s (%s)\n' % (parameter.name, parameter.value, parameter.altered))
        return super(DemandTool, self).updateParameters(parameters)


    def override_parameter_info(self, parameter_info, parameter):
        """Override this method if you need to use a non-default ArcGIS parameter handling"""
        if parameter.name == 'buildings':
            # ignore this parameter in the ArcGIS interface
            return None
        return parameter_info


if __name__ == '__main__':
    parameters = list(get_parameters('photovoltaic'))



