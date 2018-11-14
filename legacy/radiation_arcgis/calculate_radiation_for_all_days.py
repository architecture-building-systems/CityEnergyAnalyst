import traceback
import cea.inputlocator
from cea.interfaces.arcgis.modules import arcpy
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2013, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calculate_radiation_for_all_days(daily_transmissivity, dem_rasterfinal_path, latitude, locator, observers_path, path_arcgis_db):
    # let's just be sure this is set
    arcpy.env.workspace = path_arcgis_db
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")

    aspect_slope = "FROM_DEM"
    heightoffset = 1

    temporary_folder = locator.get_temporary_folder()
    for day in range(1, 366):
        calculate_radiation_single_day(day, dem_rasterfinal_path, observers_path, daily_transmissivity, latitude,
                                       temporary_folder, aspect_slope, heightoffset, path_arcgis_db)


def calculate_radiation_single_day(day, in_surface_raster, in_points_feature, T_G_day, latitude, locationtemp1,
                                   aspect_slope, heightoffset, path_arcgis_db):
    # Local Variables
    Latitude = str(latitude)
    skySize = '1400'  # max 10000
    dayInterval = '1'
    hourInterval = '1'
    calcDirections = '32'
    zenithDivisions = '512'  # max 1200cor hlaf the skysize
    azimuthDivisions = '80'  # max 160
    diffuseProp = str(T_G_day.loc[day, 'diff'])
    transmittivity = str(T_G_day.loc[day, 'trr'])
    heightoffset = str(heightoffset)
    global_radiation = locationtemp1 + '\\' + 'Day_' + str(day) + '.shp'
    timeConfig = 'WithinDay    ' + str(day) + ', 0, 24'

    arcpy.env.workspace = path_arcgis_db
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")

    # Run the extension of arcgis, retry max_retries times before giving up...
    max_retries = 3
    for _ in range(max_retries):
        try:
            arcpy.sa.PointsSolarRadiation(in_surface_raster, in_points_feature, global_radiation, heightoffset,
                                          Latitude, skySize, timeConfig, dayInterval, hourInterval, "INTERVAL", "1",
                                          aspect_slope,
                                          calcDirections, zenithDivisions, azimuthDivisions, "STANDARD_OVERCAST_SKY",
                                          diffuseProp, transmittivity, "#", "#", "#")
            print('complete calculating radiation of day No. %(day)i' % locals())
            return arcpy.GetMessages()
        except:
            print(traceback.format_exc())
    raise AssertionError('CalcRadiation failed %(max_retries)i times... giving up!' % locals())


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    parser.add_argument('--daily-transmissivity-pickle', help='Path to a pickle of the daily_transmissivity dataframe')
    parser.add_argument('--latitude', help='Latitude', type=float)
    parser.add_argument('--observers-path', help='path to observers feature layer')
    parser.add_argument('--dem-rasterfinal-path', help='path to the DEM with the burnt-in buildings')
    parser.add_argument('--arcgis_db', help='path to arcgis geodatabase')
    args = parser.parse_args()

    locator = cea.inputlocator.InputLocator(args.scenario)
    daily_transmissivity = pd.read_pickle(args.daily_transmissivity_pickle)

    calculate_radiation_for_all_days(daily_transmissivity=daily_transmissivity,
                                     dem_rasterfinal_path=args.dem_rasterfinal_path, latitude=args.latitude,
                                     locator=locator, observers_path=args.observers_path, path_arcgis_db=args.arcgis_db)
