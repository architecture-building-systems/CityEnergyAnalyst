import os

from cea.interfaces.arcgis.CityEnergyAnalyst import add_message
from cea.plots.graphs_demand import demand_graph_fields

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class DemandGraphsTool(object):
    def __init__(self):
        self.label = 'Demand graphs'
        self.description = 'Calculate Graphs of the Demand'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        analysis_fields = arcpy.Parameter(
            displayName="Variables to analyse",
            name="analysis_fields",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        analysis_fields.filter.list = []
        return [scenario_path, analysis_fields]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        analysis_fields = parameters[1]
        fields = demand_graph_fields(scenario_path)

        analysis_fields.filter.list = list(fields)
        return

    def execute(self, parameters, messages):
        import cea.plots.graphs_demand
        reload(cea.plots.graphs_demand)

        scenario_path = parameters[0].valueAsText
        analysis_fields = parameters[1].valueAsText.split(';')[:4]  # max 4 fields for analysis
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message

        # find the version of python to use:
        import pandas
        import os
        import subprocess
        import sys

        # find python executable to use
        python_exe = os.path.normpath(os.path.join(os.path.dirname(pandas.__file__), '..', '..', '..', 'python.exe'))
        gv.log("Using python: %(python_exe)s", python_exe=python_exe)
        assert os.path.exists(python_exe), 'Python interpreter (see above) not found.'

        # find demand script
        graphs_py = cea.plots.graphs_demand.__file__
        if os.path.splitext(graphs_py)[1].endswith('c'):
            graphs_py = graphs_py[:-1]
        gv.log("Path to demand script: %(graphs_py)s", graphs_py=graphs_py)

        # add root of CEAforArcGIS to python path
        cea_root_path = os.path.normpath(os.path.join(os.path.dirname(graphs_py), '..', '..'))
        gv.log("Adding path to PYTHONPATH: %(path)s", path=cea_root_path)
        sys.path.append(cea_root_path)

        # run demand script in subprocess (for multiprocessing)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            [python_exe, '-u', graphs_py, '--scenario', scenario_path, '--analysis_fields', ';'.join(analysis_fields)],
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=dict(os.environ, PYTHONPATH=cea_root_path))
        while True:
            next_line = process.stdout.readline()
            if next_line == '' and process.poll() is not None:
                break
            gv.log(next_line.rstrip())
        stdout, stderr = process.communicate()
        gv.log(stdout)
        gv.log(stderr)