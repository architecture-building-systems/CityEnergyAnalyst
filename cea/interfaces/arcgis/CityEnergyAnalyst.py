"""
ArcGIS Toolbox for integrating the CEA with ArcGIS.

ArcGIS starts by creating an instance of Toolbox, which in turn names the tools to include in the interface.

These tools shell out to ``cli.py`` because the ArcGIS python version is old and can't be updated. Therefore
we would decouple the python version used by CEA from the ArcGIS version.

See the script ``install_toolbox.py`` for the mechanics of installing the toolbox into the ArcGIS system.
"""

import inspect
import cea.interfaces.arcgis.arcgishelper

reload(cea.interfaces.arcgis.arcgishelper)
from cea.interfaces.arcgis.arcgishelper import *

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Martin Mosteiro Romero", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

arcpy.env.overwriteOutput = True


class Toolbox(object):
    """List the tools to show in the toolbox."""

    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.generate_tools()
        self.tools = [tool for tool in globals().values()
                      if inspect.isclass(tool) and issubclass(tool, CeaTool) and not tool is CeaTool]

    def generate_tools(self):
        # here some magic: create the list of script classes based on the ``scripts.yml`` file.
        # any tools that need more configuration can just be overwritten below.
        import cea.scripts
        for cea_script in cea.scripts.for_interface('arcgis'):
            tool = create_cea_tool(cea_script)
            globals()[tool.__name__] = tool


# ----------------------------------------------------------------------------------------------------------------------
# Redefine tools that need more than just the basic definition below.
# The name of the class should be the same as the name in the scripts.yml file with dashes removed and first letters
# capitalized and ending in "Tool"

class DemandTool(CeaTool):
    """integrate the demand script with ArcGIS"""

    def __init__(self):
        self.cea_tool = 'demand'
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.category = 'Demand forecasting'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        """Override this method if you need to use a non-default ArcGIS parameter handling"""
        if parameter.name == 'buildings':
            # ignore this parameter in the ArcGIS interface
            return None
        return parameter_info


class RadiationDaysimTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'radiation-daysim'
        self.label = 'Solar radiation (Daysim engine)'
        self.description = 'Use Daysim to calculate solar radiation for a scenario'
        self.category = 'Energy potentials'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        if parameter.name == 'buildings':
            return None
        else:
            return parameter_info