"""
ArcGIS Toolbox for integrating the CEA with ArcGIS.

ArcGIS starts by creating an instance of Toolbox, which in turn names the tools to include in the interface.

These tools shell out to ``cli.py`` because the ArcGIS python version is old and can't be updated. Therefore
we would decouple the python version used by CEA from the ArcGIS version.

See the script ``install_toolbox.py`` for the mechanics of installing the toolbox into the ArcGIS system.
"""

import inspect

import cea.config
import cea.inputlocator
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
        self.tools = [tool for tool in globals().values()
                      if inspect.isclass(tool) and issubclass(tool, CeaTool) and not tool is CeaTool]

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


class HeatmapsTool(CeaTool):
    def __init__(self):
        self.cea_tool = 'heatmaps'
        self.label = 'Heatmaps'
        self.description = 'Generate maps representing hot and cold spots of energy consumption'
        self.category = 'Visualization'
        self.canRunInBackground = False

    def override_parameter_info(self, parameter_info, parameter):
        if parameter.name == 'file-to-analyze':
            parameter_info.datatype = "String"
            parameter_info.filter.list = []
        elif parameter.name == 'analysis-fields':
            parameter_info.datatype = 'String'
            parameter_info.multiValue = True
            parameter_info.parameterDependencies = ['file-to-analyze']
        return parameter_info

    def updateParameters(self, parameters):
        super(HeatmapsTool, self).updateParameters(parameters)
        parameters = dict_parameters(parameters)
        locator = cea.inputlocator.InputLocator(parameters['general:scenario'].valueAsText)
        file_names = [os.path.basename(locator.get_total_demand())]
        file_names.extend(
            [f for f in os.listdir(locator.get_lca_emissions_results_folder())
             if f.endswith('.csv')])
        file_to_analyze = parameters['heatmaps:file-to-analyze']
        if not file_to_analyze.value or file_to_analyze.value not in file_names:
            file_to_analyze.filter.list = file_names
            file_to_analyze.value = file_names[0]
        # analysis_fields
        analysis_fields = parameters['heatmaps:analysis-fields']
        if file_to_analyze.value == file_names[0]:
            file_path = locator.get_total_demand()
        else:
            file_path = os.path.join(locator.get_lca_emissions_results_folder(),
                                     file_to_analyze.value)
        import pandas as pd
        df = pd.read_csv(file_path)
        fields = df.columns.tolist()
        fields.remove('Name')
        analysis_fields.filter.list = list(fields)

    def execute(self, parameters, _):
        param_dict = dict_parameters(parameters)
        scenario = param_dict['general:scenario'].valueAsText
        file_path = param_dict['heatmaps:file-to-analyze'].valueAsText
        locator = cea.inputlocator.InputLocator(scenario)
        if file_path == os.path.basename(locator.get_total_demand()):
            file_path = locator.get_total_demand()
        else:
            file_path = os.path.join(locator.get_lca_emissions_results_folder(), file_path)
        param_dict['heatmaps:file-to-analyze'].value = file_path
        super(HeatmapsTool, self).execute(parameters, _)