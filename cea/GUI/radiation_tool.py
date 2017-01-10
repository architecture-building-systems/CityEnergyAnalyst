import os

import arcpy

import cea
import cea.globalvar
import cea.inputlocator
import cea.resources
from cea.GUI.toolbox import add_message

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class RadiationTool(object):
    def __init__(self):
        self.label = 'Radiation'
        self.description = 'Create radiation file'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        weather_name = arcpy.Parameter(
            displayName="Weather file (choose from list or enter full path to .epw file)",
            name="weather_name",
            datatype="String",
            parameterType="Required",
            direction="Input")
        locator = cea.inputlocator.InputLocator(None)
        weather_name.filter.list = locator.get_weather_names()
        weather_name.enabled = False

        year = arcpy.Parameter(
            displayName="Year",
            name="year",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        year.value = 2014
        year.enabled = False

        latitude = arcpy.Parameter(
            displayName="Latitude",
            name="latitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        latitude.enabled = False

        longitude = arcpy.Parameter(
            displayName="Longitude",
            name="longitude",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        longitude.enabled = False


        return [scenario_path, weather_name, year, latitude, longitude]

    def updateParameters(self, parameters):
        scenario_path = parameters[0].valueAsText
        if scenario_path is None:
            return
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return

        weather_parameter = parameters[1]
        year_parameter = parameters[2]
        latitude_parameter = parameters[3]
        longitude_parameter = parameters[4]

        weather_parameter.enabled = True
        year_parameter.enabled = True

        locator = cea.inputlocator.InputLocator(scenario_path)
        latitude_value, longitude_value = self.get_location(locator)
        if not latitude_parameter.enabled:
            # only overwrite on first try
            latitude_parameter.value = latitude_value
            latitude_parameter.enabled = True

        if not longitude_parameter.enabled:
            # only overwrite on first try
            longitude_parameter.value = longitude_value
            longitude_parameter.enabled = True
        return

    def execute(self, parameters, messages):
        import cea

        scenario_path = parameters[0].valueAsText
        weather_name = parameters[1].valueAsText
        year = parameters[2].value
        latitude = parameters[3].value
        longitude = parameters[4].value

        locator = cea.inputlocator.InputLocator(scenario_path)
        if weather_name in locator.get_weather_names():
            weather_path = locator.get_weather(weather_name)
        elif os.path.exists(weather_name) and weather_name.endswith('.epw'):
            weather_path = weather_name
        else:
            weather_path = locator.get_default_weather()

        # FIXME: use current arcgis databases...
        path_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))

        locator = cea.inputlocator.InputLocator(scenario_path)
        arcpy.AddMessage('longitude: %s' % longitude)
        arcpy.AddMessage('latitude: %s' % latitude)

        import cea.resources.radiation_arcgis.radiation
        reload(cea.resources.radiation_arcgis.radiation)
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message
        cea.resources.radiation_arcgis.radiation.solar_radiation_vertical(locator=locator, path_arcgis_db=path_arcgis_db, latitude=latitude,
                                                                          longitude=longitude, year=year, gv=gv, weather_path=weather_path)
        return

    def get_location(self, locator):
        """returns (latitude, longitude) for a given scenario."""
        import fiona
        with fiona.open(locator.get_building_geometry()) as shp:
            longitude = shp.crs['lon_0']
            latitude = shp.crs['lat_0']
        return latitude, longitude
