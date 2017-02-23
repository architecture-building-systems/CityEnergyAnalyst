
__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class ScenarioPlotsTool(object):
    def __init__(self):
        self.label = 'Scenario Plots'
        self.description = 'Create summary plots of scenarios in a folder'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
        scenarios = arcpy.Parameter(
            displayName="Path to the scenarios to plot",
            name="scenarios",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        output_file = arcpy.Parameter(
            displayName="Path to output PDF",
            name="output_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        output_file.filter.list = ['pdf']
        return [scenarios, output_file]

    def execute(self, parameters, messages):
        import arcpy
        scenarios = parameters[0].valueAsText
        scenarios = scenarios.replace("'", "")
        scenarios = scenarios.replace('"', '')
        scenarios = scenarios.split(';')
        output_file = parameters[1].valueAsText

        arcpy.AddMessage(scenarios)

        import cea.plots.scenario_plots
        reload(cea.plots.scenario_plots)
        cea.plots.scenario_plots.plot_scenarios(scenarios=scenarios, output_file=output_file)
        return