"""
Solar vertical insolation algorithm based on ArcGIS Solar Analyst
"""
from __future__ import division

import datetime
import os

import numpy as np
import pandas as pd
import pytz
from astral import Location
from simpledbf import Dbf5
from timezonefinder import TimezoneFinder
import pickle

from cea.interfaces.arcgis.modules import arcpy
from cea.utilities import epwreader
import cea.config
import cea.globalvar

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2013, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def solar_radiation_vertical(locator, path_arcgis_db, latitude, longitude, year, gv, weather_path):
    """
    algorithm to calculate the hourly solar isolation in vertical building surfaces.
    The algorithm is based on the Solar Analyst Engine of ArcGIS 10.
    For more info check the integrated demand model of Fonseca et al. 2015. Appl. energy.

    :param locator: input locator for file paths
    :type locator: cea.inputlocator.InputLocator

    :param path_arcgis_db:  path to default database of Arcgis. E.g.``c:\users\your_name\Documents\Arcgis\Default.gdb``
    :type path_arcgis_db: str

    :param latitude: latitude north  at the centre of the location
    :type latitude: float

    :param longitude: latitude north
    :type longitude: float

    :param year: year of calculation
    :type year: int

    :param gv: global context and constants
    :type gv: cea.globalvar.GlobalVariables

    :param weather_path: path to the weather file
    :type weather_path: str

    :returns: produces ``radiation.csv``, solar radiation file in vertical surfaces of buildings.
    """
    print(weather_path)
    # Set environment settings
    arcpy.env.workspace = path_arcgis_db
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")

    # local variables
    simple_cq_shp = locator.get_temporary_file('Simple_CQ_shp.shp')
    simple_context_shp = locator.get_temporary_file('Simple_Context.shp')
    dem_rasterfinal_path = os.path.join(path_arcgis_db, 'DEM_All2')
    observers_path = os.path.join(path_arcgis_db, 'observers')
    data_factors_boundaries_csv = locator.get_temporary_file('DataFactorsBoundaries.csv')
    data_factors_centroids_csv = locator.get_temporary_file('DataFactorsCentroids.csv')

    sunrise = calculate_sunrise(year, longitude, latitude)
    sunrise_pickle = locator.get_temporary_file('sunrise.pickle')
    pickle.dump(sunrise, open(sunrise_pickle, 'wb'))

    daily_transmissivity = calculate_daily_transmissivity_and_daily_diffusivity(weather_path)
    daily_transmissivity_pickle = locator.get_temporary_file('daily_transmissivity.pickle')
    daily_transmissivity.to_pickle(daily_transmissivity_pickle)

    dem_raster_extent = simplify_building_geometries(locator, simple_context_shp, simple_cq_shp)

    burn_buildings_into_raster(simple_context_shp, locator.get_terrain(), dem_rasterfinal_path,
                               locator.get_temporary_folder(), dem_raster_extent)

    calculate_boundaries_of_buildings(simple_cq_shp, locator.get_temporary_folder(), path_arcgis_db,
                                      data_factors_centroids_csv, data_factors_boundaries_csv)

    calculate_observers(simple_cq_shp, observers_path, data_factors_boundaries_csv, path_arcgis_db)

    run_script_in_subprocess('calculate_radiation_for_all_days',
                             '--daily-transmissivity-pickle', daily_transmissivity_pickle,
                             '--dem-rasterfinal-path', dem_rasterfinal_path,
                             '--latitude', latitude,
                             '--observers-path', observers_path,
                             '--arcgis_db', path_arcgis_db)
    gv.log('complete raw radiation files')

    sunny_hours_pickle = locator.get_temporary_file('sunny_hours.pickle')
    run_script_in_subprocess('calculate_sunny_hours_of_year',
                             '--scenario', locator.scenario,
                             '--sunrise-pickle', sunrise_pickle,
                             '--sunny-hours-pickle', sunny_hours_pickle)

    gv.log('complete transformation radiation files')

    # Assign radiation to every surface of the buildings
    radiation_pickle_path = locator.get_temporary_file('radiation.pickle')

    run_script_in_subprocess('calculate_radiation_for_surfaces',
                             '--observers-path', observers_path,
                             '--data-factors-centroids', data_factors_centroids_csv,
                             '--sunny-hours-pickle', sunny_hours_pickle,
                             '--temp-folder', locator.get_temporary_folder(),
                             '--arcgis-db', path_arcgis_db,
                             '--radiation-pickle', radiation_pickle_path)

    run_script_in_subprocess('calculate_wall_areas',
                             '--radiation-pickle', radiation_pickle_path)

    radiation = pd.read_pickle(radiation_pickle_path)
    export_surface_properties(radiation, locator.get_surface_properties())

    # get solar insolation @ daren: this is a A BOTTLE NECK
    run_script_in_subprocess('calculate_incident_radiation',
                             '--radiation-pickle', radiation_pickle_path,
                             '--radiation-csv', locator.get_radiation())
    gv.log('done')


def simplify_building_geometries(locator, simple_context_shp, simple_cq_shp):
    # Simplify building's geometry
    elevRaster = arcpy.sa.Raster(locator.get_terrain())
    dem_raster_extent = elevRaster.extent
    arcpy.SimplifyBuilding_cartography(locator.get_zone_geometry(), simple_cq_shp,
                                       simplification_tolerance=7, minimum_area=None)
    arcpy.SimplifyBuilding_cartography(locator.get_district_geometry(), simple_context_shp,
                                       simplification_tolerance=7, minimum_area=None)
    return dem_raster_extent


def calculate_daily_transmissivity_and_daily_diffusivity(weather_path):
    # calcuate daily transmissivity and daily diffusivity
    weather_data = epwreader.epw_reader(weather_path)[['dayofyear', 'exthorrad_Whm2',
                                                       'glohorrad_Whm2', 'difhorrad_Whm2']]
    weather_data['diff'] = weather_data.difhorrad_Whm2 / weather_data.glohorrad_Whm2
    weather_data = weather_data[np.isfinite(weather_data['diff'])]
    daily_transmissivity = np.round(weather_data.groupby(['dayofyear']).mean(), 2)
    daily_transmissivity['diff'] = daily_transmissivity['diff'].replace(1, 0.90)
    daily_transmissivity['trr'] = (1 - daily_transmissivity['diff'])
    return daily_transmissivity


def export_surface_properties(radiation, surface_properties):
    # export surfaces properties
    # radiation['Awall_all'] = radiation['Shape_Leng'] * radiation['FactorShade'] * radiation['Freeheight']
    radiation[['Name', 'Freeheight', 'FactorShade', 'height_ag', 'Shape_Leng', 'Awall_all']].to_csv(surface_properties,
                                                                                                    index=False)
    print('saved surface properties to disk')


def calculate_observers(simple_cq_shp, observers_path, data_factors_boundaries_csv, path_arcgis_db):
    # local variables
    Buffer_CQ = path_arcgis_db + '\\' + 'BufferCQ'
    temporal_lines = path_arcgis_db + '\\' + 'lines'
    Points = path_arcgis_db + '\\' + 'Points'
    AggregatedBuffer = path_arcgis_db + '\\' + 'BufferAggregated'
    temporal_lines3 = path_arcgis_db + '\\' + 'lines3'
    Points3 = path_arcgis_db + '\\' + 'Points3'
    Points3Updated = path_arcgis_db + '\\' + 'Points3Updated'
    EraseObservers = path_arcgis_db + '\\' + 'eraseobservers'
    Observers0 = path_arcgis_db + '\\' + 'observers0'
    NonoverlappingBuildings = path_arcgis_db + '\\' + 'Non_overlap'
    templines = path_arcgis_db + '\\' + 'templines'
    templines2 = path_arcgis_db + '\\' + 'templines2'
    Buffer_CQ0 = path_arcgis_db + '\\' + 'Buffer_CQ0'
    Buffer_CQ = path_arcgis_db + '\\' + 'Buffer_CQ'
    Buffer_CQ1 = path_arcgis_db + '\\' + 'Buffer_CQ1'
    Simple_CQcopy = path_arcgis_db + '\\' + 'Simple_CQcopy'
    # First increase the boundaries in 2m of each surface in the community to
    # analyze- this will avoid that the observers overlap the buildings and Simplify
    # the community vertices to only create 1 point per surface

    arcpy.CopyFeatures_management(simple_cq_shp, Simple_CQcopy)
    # Make Square-like buffers
    arcpy.PolygonToLine_management(Simple_CQcopy, templines, "IGNORE_NEIGHBORS")
    arcpy.SplitLine_management(templines, templines2)
    arcpy.Buffer_analysis(templines2, Buffer_CQ0, "0.75 Meters", "FULL", "FLAT", "NONE", "#")
    arcpy.Append_management(Simple_CQcopy, Buffer_CQ0, "NO_TEST")
    arcpy.Dissolve_management(Buffer_CQ0, Buffer_CQ1, "Name", "#", "SINGLE_PART", "DISSOLVE_LINES")
    arcpy.SimplifyBuilding_cartography(Buffer_CQ1, Buffer_CQ, simplification_tolerance=8, minimum_area=None)

    # arcpy.Buffer_analysis(Simple_CQ,Buffer_CQ,buffer_distance_or_field=1, line_end_type='FLAT') # buffer with a flat finishing
    # arcpy.Generalize_edit(Buffer_CQ,"2 METERS")

    # Transform all polygons of the simplified areas to observation points
    arcpy.SplitLine_management(Buffer_CQ, temporal_lines)
    arcpy.FeatureVerticesToPoints_management(temporal_lines, Points,
                                             'MID')  # Second the transformation of Lines to a mid point

    # Join all the polygons to get extra vertices, make lines and then get points.
    # these points should be added to the original observation points
    arcpy.AggregatePolygons_cartography(Buffer_CQ, AggregatedBuffer, "0.5 Meters", "0 SquareMeters", "0 SquareMeters",
                                        "ORTHOGONAL")  # agregate polygons
    arcpy.SplitLine_management(AggregatedBuffer, temporal_lines3)  # make lines
    arcpy.FeatureVerticesToPoints_management(temporal_lines3, Points3, 'MID')  # create extra points

    # add information to Points3 about their buildings
    arcpy.SpatialJoin_analysis(Points3, Buffer_CQ, Points3Updated, "JOIN_ONE_TO_ONE", "KEEP_ALL",
                               match_option="CLOSEST", search_radius="5 METERS")
    arcpy.Erase_analysis(Points3Updated, Points, EraseObservers, "2 Meters")  # erase overlaping points
    arcpy.Merge_management([Points, EraseObservers], Observers0)  # erase overlaping points

    #  Eliminate Observation points above roofs of the highest surfaces(a trick to make the
    # Import Overlaptable from function CalcBoundaries containing the data about buildings overlaping, eliminate duplicades, chose only those ones no overlaped and reindex
    DataNear = pd.read_csv(data_factors_boundaries_csv)
    CleanDataNear = DataNear[DataNear['FactorShade'] == 1]
    CleanDataNear.drop_duplicates(subset='Name_x', inplace=True)
    CleanDataNear.reset_index(inplace=True)
    rows = CleanDataNear.Name_x.count()
    if rows > 0:  # there are overlapping buildings
        for row in range(rows):
            Field = "Name"  # select field where the name exists to iterate
            Value = CleanDataNear.loc[row, 'Name_x']  # set the value or name of the City quarter
            Where_clausule = '''''' + '"' + Field + '"' + "=" + "\'" + str(
                Value) + "\'" + ''''''  # strange writing to introduce in ArcGIS
            if row == 0:
                arcpy.MakeFeatureLayer_management(simple_cq_shp, 'Simple_lyr')
                arcpy.SelectLayerByAttribute_management('Simple_lyr', "NEW_SELECTION", Where_clausule)
            else:
                arcpy.SelectLayerByAttribute_management('Simple_lyr', "ADD_TO_SELECTION", Where_clausule)

            arcpy.CopyFeatures_management('simple_lyr', NonoverlappingBuildings)
        arcpy.ErasePoint_edit(Observers0, NonoverlappingBuildings, "INSIDE")

    arcpy.CopyFeatures_management(Observers0, observers_path)  # copy features to reset the OBJECTID
    with arcpy.da.UpdateCursor(observers_path, ["OBJECTID", "ORIG_FID"]) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
    print('complete calculating observers')
    return arcpy.GetMessages()


def calculate_boundaries_of_buildings(simple_cq_shp, temporary_folder, path_arcgis_db, data_factors_centroids_csv,
                                      data_factors_boundaries_csv):
    # local variables
    NearTable = temporary_folder + '\\' + 'NearTable.dbf'
    CQLines = path_arcgis_db + '\\' + '\CQLines'
    CQVertices = path_arcgis_db + '\\' + 'CQVertices'
    CQSegments = path_arcgis_db + '\\' + 'CQSegment'
    CQSegments_centroid = path_arcgis_db + '\\' + 'CQSegmentCentro'
    centroidsTable_name = 'CentroidCQdata.dbf'
    centroidsTable = temporary_folder + '\\' + centroidsTable_name
    Overlaptable = temporary_folder + '\\' + 'overlapingTable.csv'

    # Create points in the centroid of segment line and table with near features:
    # identifying for each segment of line of building A the segment of line of building B in common.
    arcpy.FeatureToLine_management(simple_cq_shp, CQLines)
    arcpy.FeatureVerticesToPoints_management(simple_cq_shp, CQVertices, 'ALL')
    arcpy.SplitLineAtPoint_management(CQLines, CQVertices, CQSegments, '2 METERS')
    arcpy.FeatureVerticesToPoints_management(CQSegments, CQSegments_centroid, 'MID')
    arcpy.GenerateNearTable_analysis(CQSegments_centroid, CQSegments_centroid, NearTable, "1 Meters", "NO_LOCATION",
                                     "NO_ANGLE", "CLOSEST", "0")

    # Import the table with NearMatches
    NearMatches = Dbf5(NearTable).to_dataframe()

    # Import the table with attributes of the centroids of the Segments
    arcpy.TableToTable_conversion(CQSegments_centroid, temporary_folder, centroidsTable_name)
    DataCentroids = Dbf5(centroidsTable).to_dataframe()[['Name', 'height_ag', 'ORIG_FID']]

    # CreateJoin to Assign a Factor to every Centroid of the lines,
    FirstJoin = pd.merge(NearMatches, DataCentroids, left_on='IN_FID', right_on='ORIG_FID')
    SecondaryJoin = pd.merge(FirstJoin, DataCentroids, left_on='NEAR_FID', right_on='ORIG_FID')

    # delete matches within the same polygon Name (it can happen that lines are too close one to the other)
    # also delete matches with a distance of more than 20 cm making room for mistakes during the simplicfication of buildings but avoiding deleten boundaries
    rows = SecondaryJoin.IN_FID.count()
    for row in range(rows):
        if (SecondaryJoin.loc[row, 'Name_x'] == SecondaryJoin.loc[row, 'Name_y']
            or SecondaryJoin.loc[row, 'NEAR_DIST'] > 0.2):
            SecondaryJoin = SecondaryJoin.drop(row)
    SecondaryJoin.reset_index(inplace=True)

    # FactorShade = 0 if the line exist in a building totally covered by another one, and Freeheight is equal to the height of the line
    # that is not obstructed by the other building
    rows = SecondaryJoin.IN_FID.count()
    SecondaryJoin['FactorShade'] = 0
    SecondaryJoin['Freeheight'] = 0
    for row in range(rows):
        if SecondaryJoin.loc[row, 'height_ag_x'] <= SecondaryJoin.loc[row, 'height_ag_y']:
            SecondaryJoin.loc[row, 'FactorShade'] = 0
            SecondaryJoin.loc[row, 'Freeheight'] = 0
        elif SecondaryJoin.loc[row, 'height_ag_x'] > SecondaryJoin.loc[row, 'height_ag_y'] and SecondaryJoin.loc[
            row, 'height_ag_x'] - 1 <= SecondaryJoin.loc[row, 'height_ag_y']:
            SecondaryJoin.loc[row, 'FactorShade'] = 0
        else:
            SecondaryJoin.loc[row, 'FactorShade'] = 1
            SecondaryJoin.loc[row, 'Freeheight'] = abs(
                SecondaryJoin.loc[row, 'height_ag_y'] - SecondaryJoin.loc[row, 'height_ag_x'])

    # Create and export Secondary Join with results, it will be Useful for the function CalcObservers
    SecondaryJoin.to_csv(data_factors_boundaries_csv, index=False)

    # Update table Datacentroids with the Fields Freeheight and Factor Shade. for those buildings without
    # shading boundaries these factors are equal to 1 and the field 'height' respectively.
    pd.options.mode.chained_assignment = None
    DataCentroids['FactorShade'] = 1
    DataCentroids['Freeheight'] = DataCentroids.height_ag
    Results = DataCentroids.merge(SecondaryJoin, left_on='ORIG_FID', right_on='ORIG_FID_x', how='outer')
    Results.FactorShade_y.fillna(Results['FactorShade_x'], inplace=True)
    Results.Freeheight_y.fillna(Results['Freeheight_x'], inplace=True)
    Results.rename(columns={'FactorShade_y': 'FactorShade', 'Freeheight_y': 'Freeheight'}, inplace=True)
    FinalDataCentroids = pd.DataFrame(Results, columns={'ORIG_FID', 'height', 'FactorShade', 'Freeheight'})

    FinalDataCentroids.to_csv(data_factors_centroids_csv, index=False)
    print('complete calculating boundaries')
    return arcpy.GetMessages()


def burn_buildings_into_raster(simple_context_shp, terrain_tif, dem_rasterfinal_path, temporary_folder,
                               dem_raster_extent):
    # Create a raster with all the buildings
    Outraster = temporary_folder + '\\' + 'AllRaster'
    # These coordinates are extracted from the environment settings/once the DEM raster is selected directly in ArcGIS,
    arcpy.env.extent = dem_raster_extent
    # creating raster of the footprints of the buildings
    arcpy.FeatureToRaster_conversion(simple_context_shp, 'height_ag', Outraster, '0.5')

    # Clear non values and add all the Buildings to the DEM
    OutNullRas = arcpy.sa.IsNull(Outraster)  # identify noData Locations
    Output = arcpy.sa.Con(OutNullRas == 1, 0, Outraster)
    RadiationDEM = arcpy.sa.Raster(terrain_tif) + Output
    RadiationDEM.save(dem_rasterfinal_path)
    print('complete burning buildings into raster')

    return arcpy.GetMessages()


def calculate_sunrise(year_to_simulate, longitude, latitude):
    """
    Calculate the hour of sunrise for a given year, longitude and latitude. Returns an array
    of hours.
    """

    # get the time zone name
    tf = TimezoneFinder()
    time_zone = tf.timezone_at(lng=longitude, lat=latitude)

    # define the city_name
    location = Location()
    location.name = 'name'
    location.region = 'region'
    location.latitude = latitude
    location.longitude = longitude
    location.timezone = time_zone
    location.elevation = 0

    sunrise = []
    for day in range(1, 366):  # Calculated according to NOAA website
        dt = datetime.datetime(year_to_simulate, 1, 1) + datetime.timedelta(day - 1)
        dt = pytz.timezone(time_zone).localize(dt)
        sun = location.sun(dt)
        sunrise.append(sun['sunrise'].hour)
    print('complete calculating sunrise')
    return sunrise


def get_latitude(scenario_path):
    import fiona
    import cea.inputlocator
    with fiona.open(cea.inputlocator.InputLocator(scenario_path).get_zone_geometry()) as shp:
        lat = shp.crs['lat_0']
    return lat


def get_longitude(scenario_path):
    import fiona
    import cea.inputlocator
    with fiona.open(cea.inputlocator.InputLocator(scenario_path).get_zone_geometry()) as shp:
        lon = shp.crs['lon_0']
    return lon

def run_script_in_subprocess(script_name, *args):
    """Run the script `script_name` (in the same folder as this script) in a subprocess, printing the output"""
    import subprocess
    startupinfo = subprocess.STARTUPINFO()

    script_full_path = os.path.join(os.path.dirname(__file__), script_name + '.py')

    command = [get_python_exe(), '-u', script_full_path]
    command.extend(map(str, args))
    print(command)

    env = os.environ.copy()
    env['PATH'] = ';'.join((r'c:\Python27\ArcGISx6410.5', env['PATH']))

    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=env)
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        if len(next_line):
            print(script_name + ': ' + next_line.rstrip())
    stdout, stderr = process.communicate()
    if len(stdout):
        print(script_name + ': ' + stdout.rstrip())
    if len(stderr):
        print(script_name + '@STDERR:\n' + stderr)
    if process.returncode != 0:
        raise Exception('Failed to execute ' + script_name)


def get_python_exe():
    """Return the path to the python interpreter that was used to install CEA"""
    try:
        with open(os.path.expanduser('~/cea_python.pth'), 'r') as f:
            python_exe = f.read().strip()
            return python_exe
    except:
        raise AssertionError("Could not find 'cea_python.pth' in home directory.")


def main(config):
    import cea.inputlocator

    print('Running radiation with scenario = %s' % config.scenario)
    print('Running radiation with weather = %s' % config.weather)
    print('Running radiation with latitude = %s' % config.radiation.latitude)
    print('Running radiation with longitude = %s' % config.radiation.longitude)
    print('Running radiation with year = %s' % config.radiation.year)

    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(config.scenario)
    weather_path = config.weather

    latitude = config.radiation.latitude
    longitude = config.radiation.longitude


    if latitude is None:
        latitude = get_latitude(config.scenario)
    if longitude is None:
        longitude = get_longitude(config.scenario)

    path_default_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))

    solar_radiation_vertical(locator=locator, path_arcgis_db=path_default_arcgis_db,
                             latitude=latitude, longitude=longitude, year=config.radiation.year, gv=gv,
                             weather_path=weather_path)


if __name__ == '__main__':
    main(cea.config.Configuration())
