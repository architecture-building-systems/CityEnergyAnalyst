"""
The MainUse toolbox creates a csv file `main_use.csv` in the root of a scenario with two columns:
- Name (id for the buildings in the scenario)
- MainUse (main occupancy use of a building)
"""

class Toolbox(object):
    def __init__(self):
        self.label = 'Main Use'
        self.alias = 'main_use'
        self.tools = [MainUseTool]

class MainUseTool(object):
    def __init__(self):
        self.label = 'Main Use'
        self.description = 'Calculate main uses'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        return [scenario_path]

    def execute(self, parameters, messages):
        import os
        import pandas as pd
        from geopandas import GeoDataFrame as gpdf

        scenario_path = parameters[0].valueAsText
        occupation_shp = os.path.join(scenario_path, 'inputs', 'building-properties', 'occupancy.shp')
        df = gpdf.from_file(occupation_shp).drop('geometry', axis=1).set_index('Name')
        main_uses = pd.DataFrame({'main_use': df.idxmax(axis=1)})
        main_uses.to_csv(os.path.join(scenario_path, 'main_uses.csv'))
