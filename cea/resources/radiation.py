"""
Solar vertical insolation algorithm based on ArcGIS Solar Analyst
"""
from __future__ import division

from cea.interfaces.arcgis.modules import arcgisscripting
import datetime
import os

from cea.interfaces.arcgis.modules import arcpy
import ephem
import numpy as np
import pandas as pd
from simpledbf import Dbf5

from cea.utilities import epwreader

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
    aspect_slope = "FROM_DEM"
    heightoffset = 1
    Simple_CQ = path_arcgis_db + '\\' + 'Simple_CQ'
    Simple_context = path_arcgis_db + '\\' + 'Simple_context'
    dem_rasterfinal = path_arcgis_db + '\\' + 'DEM_All2'
    observers = path_arcgis_db + '\\' + 'observers'
    DataFactorsBoundaries = locator.get_temporary_file('DataFactorsBoundaries.csv')
    DataFactorsCentroids = locator.get_temporary_file('DataFactorsCentroids.csv')
    DataradiationLocation = locator.get_temporary_file('RadiationYear.csv')

    # calculate sunrise
    sunrise = calc_sunrise(range(1, 366), year, longitude, latitude, gv)

    # calcuate daily transmissivity and daily diffusivity
    weather_data = epwreader.epw_reader(weather_path)[['dayofyear', 'exthorrad_Whm2',
                                                       'glohorrad_Whm2', 'difhorrad_Whm2']]
    weather_data['diff'] = weather_data.difhorrad_Whm2 / weather_data.glohorrad_Whm2
    weather_data = weather_data[np.isfinite(weather_data['diff'])]
    T_G_day = np.round(weather_data.groupby(['dayofyear']).mean(), 2)
    T_G_day['diff'] = T_G_day['diff'].replace(1, 0.90)
    T_G_day['trr'] = (1 - T_G_day['diff'])

    # T_G_day.to_csv(r'C:\Users\Jimeno\Documents/test4.csv')

    # Simplify building's geometry
    elevRaster = arcpy.sa.Raster(locator.get_terrain())
    dem_raster_extent = elevRaster.extent
    arcpy.SimplifyBuilding_cartography(locator.get_building_geometry(), Simple_CQ,
                                       simplification_tolerance=8, minimum_area=None)
    arcpy.SimplifyBuilding_cartography(locator.get_district(), Simple_context,
                                       simplification_tolerance=8, minimum_area=None)

    # # burn buildings into raster
    Burn(Simple_context, locator.get_terrain(), dem_rasterfinal, locator.get_temporary_folder(), dem_raster_extent, gv)

    # Calculate boundaries of buildings
    CalcBoundaries(Simple_CQ, locator.get_temporary_folder(), path_arcgis_db,
                   DataFactorsCentroids, DataFactorsBoundaries, gv)

    # calculate observers
    CalcObservers(Simple_CQ, observers, DataFactorsBoundaries, path_arcgis_db, gv)

    # Calculate radiation
    for day in range(1, 366):
        result = None
        while result is None:  # trick to avoid that arcgis stops calculating the days and tries again.
            try:
                result = CalcRadiation(day, dem_rasterfinal, observers, T_G_day, latitude,
                                       locator.get_temporary_folder(), aspect_slope, heightoffset, gv)
            except arcgisscripting.ExecuteError:
                # redo the calculation
                pass

    gv.log('complete raw radiation files')

    # run the transformation of files appending all and adding non-sunshine hours
    radiations = []
    for day in range(1, 366):
        radiations.append(calc_radiation_day(day, sunrise, locator.get_temporary_folder()))

    radiationyear = radiations[0]
    for r in radiations[1:]:
        radiationyear = radiationyear.merge(r, on='ID', how='outer')
    radiationyear.fillna(value=0, inplace=True)
    radiationyear.to_csv(DataradiationLocation, index=True)

    radiationyear = radiations = None
    gv.log('complete transformation radiation files')

    # Assign radiation to every surface of the buildings
    Data_radiation_path = CalcRadiationSurfaces(observers, DataFactorsCentroids,
                                                DataradiationLocation, locator.get_temporary_folder(), path_arcgis_db)

    # get solar insolation @ daren: this is a A BOTTLE NECK
    CalcIncidentRadiation(Data_radiation_path, locator.get_radiation(), locator.get_surface_properties(), gv)
    gv.log('done')


def CalcIncidentRadiation(path_radiation_data, path_radiation_year_final, surface_properties, gv):
    radiation = pd.read_csv(path_radiation_data)
    # export surfaces properties
    radiation['Awall_all'] = radiation['Shape_Leng'] * radiation['FactorShade'] * radiation['Freeheight']
    radiation[['Name', 'Freeheight', 'FactorShade', 'height_ag', 'Shape_Leng', 'Awall_all']].to_csv(surface_properties, index=False)

    # Import Radiation table and compute the Irradiation in W in every building's surface
    hours_in_year = 8760
    column_names = ['T%i' % (i + 1) for i in range(hours_in_year)]
    for column in column_names:
        # transform all the points of solar radiation into Wh
        radiation[column] = radiation[column] * radiation['Awall_all']

    # sum up radiation load per building
    # NOTE: this looks like an ugly hack because it is: in order to work around a pandas MemoryError, we group/sum the
    # columns individually...
    grouped_data_frames = {}
    for column in column_names:
        df = pd.DataFrame(data={'Name': radiation['Name'],
                                column: radiation[column]})
        grouped_data_frames[column] = df.groupby(by='Name').sum()
    radiation_load = pd.DataFrame(index=grouped_data_frames.values()[0].index)
    for column in column_names:
        radiation_load[column] = grouped_data_frames[column][column]

    incident_radiation = np.round(radiation_load[column_names], 2)
    incident_radiation.to_csv(path_radiation_year_final)

    return  # total solar radiation in areas exposed to radiation in Watts


def CalcRadiationSurfaces(Observers, DataFactorsCentroids, DataradiationLocation, locationtemp1, locationtemp2):
    # local variables
    CQSegments_centroid = locationtemp2 + '\\' + 'CQSegmentCentro'
    Outjoin = locationtemp2 + '\\' + 'Join'
    CQSegments = locationtemp2 + '\\' + 'CQSegment'
    OutTable = 'CentroidsIDobserver.dbf'
    # Create Join of features Observers and CQ_sementscentroids to
    # assign Names and IDS of observers (field TARGET_FID) to the centroids of the lines of the buildings,
    # then create a table to import as a Dataframe
    arcpy.SpatialJoin_analysis(CQSegments_centroid, Observers, Outjoin, "JOIN_ONE_TO_ONE", "KEEP_ALL",
                               match_option="CLOSEST", search_radius="10 METERS")
    arcpy.JoinField_management(Outjoin, 'OBJECTID', CQSegments, 'OBJECTID')  # add the lenghts of the Lines to the File
    arcpy.TableToTable_conversion(Outjoin, locationtemp1, OutTable)

    # ORIG_FID represents the points in the segments of the simplified shape of the building
    # ORIG_FID_1 is the observers ID
    Centroids_ID_observers0 = Dbf5(locationtemp1 + '\\' + OutTable).to_dataframe()
    Centroids_ID_observers = Centroids_ID_observers0[['Name', 'height_ag', 'ORIG_FID', 'ORIG_FID_1', 'Shape_Leng']]
    Centroids_ID_observers.rename(columns={'ORIG_FID_1': 'ID'}, inplace=True)

    # Create a Join of the Centroid_ID_observers and Datacentroids in the Second Chapter to get values of surfaces Shaded.
    Datacentroids = pd.read_csv(DataFactorsCentroids)
    DataCentroidsFull = pd.merge(Centroids_ID_observers, Datacentroids, left_on='ORIG_FID', right_on='ORIG_FID')

    # Read again the radiation table and merge values with the Centroid_ID_observers under the field ID in Radiationtable and 'ORIG_ID' in Centroids...
    Radiationtable = pd.read_csv(DataradiationLocation, index_col='Unnamed: 0')
    DataRadiation = pd.merge(left=DataCentroidsFull, right=Radiationtable, left_on='ID', right_on='ID')

    Data_radiation_path = locationtemp1 + '\\' + 'tempradaition.csv'
    DataRadiation.to_csv(Data_radiation_path, index=False)

    return Data_radiation_path


def calc_radiation_day(day, sunrise, route):
    radiation_sunnyhours = np.round(Dbf5(route + '\\' + 'Day_' + str(day) + '.dbf').to_dataframe(), 2)

    # Obtain the number of points modeled to do the iterations
    radiation_sunnyhours['ID'] = 0
    counter = radiation_sunnyhours.ID.count()
    value = counter + 1
    radiation_sunnyhours['ID'] = range(1, value)

    # Table with empty values with the same range as the points.
    Table = pd.DataFrame.copy(radiation_sunnyhours)
    listtimes = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12', 'T13', 'T14', 'T15', 'T16',
                 'T17', 'T18', 'T19', 'T20', 'T21', 'T22', 'T23', 'T24']
    for x in listtimes:
        Table[x] = 0
    Table.drop('T0', axis=1, inplace=True)

    # Counter of Columns in the Initial Table
    Counter = radiation_sunnyhours.count(1)[0]
    values = Counter - 1
    # Condition to take into account daysavingtime in Switzerland as the radiation data in ArcGIS is calculated for 2013.
    if 90 <= day < 300:
        D = 1
    else:
        D = 0
    # Calculation of Sunrise time
    Sunrise_time = sunrise[day - 1]
    # Calculation of table
    for x in range(values):
        Hour = int(Sunrise_time) + int(D) + int(x)
        Table['T' + str(Hour)] = radiation_sunnyhours['T' + str(x)]

    # rename the table for every T to get in 1 to 8760 hours.
    if day <= 1:
        name = 1
    else:
        name = int(day - 1) * 24 + 1

    Table.rename(
        columns={'T1': 'T' + str(name), 'T2': 'T' + str(name + 1), 'T3': 'T' + str(name + 2), 'T4': 'T' + str(name + 3),
                 'T5': 'T' + str(name + 4),
                 'T6': 'T' + str(name + 5), 'T7': 'T' + str(name + 6), 'T8': 'T' + str(name + 7),
                 'T9': 'T' + str(name + 8), 'T10': 'T' + str(name + 9),
                 'T11': 'T' + str(name + 10), 'T12': 'T' + str(name + 11), 'T13': 'T' + str(name + 12),
                 'T14': 'T' + str(name + 13), 'T15': 'T' + str(name + 14),
                 'T16': 'T' + str(name + 15), 'T17': 'T' + str(name + 16), 'T18': 'T' + str(name + 17),
                 'T19': 'T' + str(name + 18), 'T20': 'T' + str(name + 19),
                 'T21': 'T' + str(name + 20), 'T22': 'T' + str(name + 21), 'T23': 'T' + str(name + 22),
                 'T24': 'T' + str(name + 23), 'ID': 'ID'}, inplace=True)

    return Table


def CalcRadiation(day, in_surface_raster, in_points_feature, T_G_day, latitude, locationtemp1, aspect_slope,
                  heightoffset, gv):
    # Local Variables
    Latitude = str(latitude)
    skySize = '1400'  # max 10000
    dayInterval = '1'
    hourInterval = '1'
    calcDirections = '32'
    zenithDivisions = '600'  # max 1200cor hlaf the skysize
    azimuthDivisions = '80'  # max 160
    diffuseProp = str(T_G_day.loc[day, 'diff'])
    transmittivity = str(T_G_day.loc[day, 'trr'])
    heightoffset = str(heightoffset)
    global_radiation = locationtemp1 + '\\' + 'Day_' + str(day) + '.shp'
    timeConfig = 'WithinDay    ' + str(day) + ', 0, 24'

    # Run the extension of arcgis
    arcpy.sa.PointsSolarRadiation(in_surface_raster, in_points_feature, global_radiation, heightoffset,
                                  Latitude, skySize, timeConfig, dayInterval, hourInterval, "INTERVAL", "1",
                                  aspect_slope,
                                  calcDirections, zenithDivisions, azimuthDivisions, "STANDARD_OVERCAST_SKY",
                                  diffuseProp, transmittivity, "#", "#", "#")
    gv.log('complete calculating radiation of day No. ' + str(day))
    return arcpy.GetMessages()


def CalcObservers(Simple_CQ, Observers, DataFactorsBoundaries, locationtemporal2, gv):
    # local variables
    Buffer_CQ = locationtemporal2 + '\\' + 'BufferCQ'
    temporal_lines = locationtemporal2 + '\\' + 'lines'
    Points = locationtemporal2 + '\\' + 'Points'
    AggregatedBuffer = locationtemporal2 + '\\' + 'BufferAggregated'
    temporal_lines3 = locationtemporal2 + '\\' + 'lines3'
    Points3 = locationtemporal2 + '\\' + 'Points3'
    Points3Updated = locationtemporal2 + '\\' + 'Points3Updated'
    EraseObservers = locationtemporal2 + '\\' + 'eraseobservers'
    Observers0 = locationtemporal2 + '\\' + 'observers0'
    NonoverlappingBuildings = locationtemporal2 + '\\' + 'Non_overlap'
    templines = locationtemporal2 + '\\' + 'templines'
    templines2 = locationtemporal2 + '\\' + 'templines2'
    Buffer_CQ0 = locationtemporal2 + '\\' + 'Buffer_CQ0'
    Buffer_CQ = locationtemporal2 + '\\' + 'Buffer_CQ'
    Buffer_CQ1 = locationtemporal2 + '\\' + 'Buffer_CQ1'
    Simple_CQcopy = locationtemporal2 + '\\' + 'Simple_CQcopy'
    # First increase the boundaries in 2m of each surface in the community to
    # analyze- this will avoid that the observers overlap the buildings and Simplify
    # the community vertices to only create 1 point per surface

    arcpy.CopyFeatures_management(Simple_CQ, Simple_CQcopy)
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
    DataNear = pd.read_csv(DataFactorsBoundaries)
    CleanDataNear = DataNear[DataNear['FactorShade'] == 1]
    CleanDataNear.drop_duplicates(subset='Name_x', inplace=True)
    CleanDataNear.reset_index(inplace=True)
    rows = CleanDataNear.Name_x.count()
    for row in range(rows):
        Field = "Name"  # select field where the name exists to iterate
        Value = CleanDataNear.loc[row, 'Name_x']  # set the value or name of the City quarter
        Where_clausule = '''''' + '"' + Field + '"' + "=" + "\'" + str(
            Value) + "\'" + ''''''  # strange writing to introduce in ArcGIS
        if row == 0:
            arcpy.MakeFeatureLayer_management(Simple_CQ, 'Simple_lyr')
            arcpy.SelectLayerByAttribute_management('Simple_lyr', "NEW_SELECTION", Where_clausule)
        else:
            arcpy.SelectLayerByAttribute_management('Simple_lyr', "ADD_TO_SELECTION", Where_clausule)

        arcpy.CopyFeatures_management('simple_lyr', NonoverlappingBuildings)

    arcpy.ErasePoint_edit(Observers0, NonoverlappingBuildings, "INSIDE")
    arcpy.CopyFeatures_management(Observers0, Observers)  # copy features to reset the OBJECTID
    with arcpy.da.UpdateCursor(Observers, ["OBJECTID", "ORIG_FID"]) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
    gv.log('complete calculating observers')
    return arcpy.GetMessages()


def CalcBoundaries(Simple_CQ, locationtemp1, locationtemp2, DataFactorsCentroids, DataFactorsBoundaries, gv):
    # local variables
    NearTable = locationtemp1 + '\\' + 'NearTable.dbf'
    CQLines = locationtemp2 + '\\' + '\CQLines'
    CQVertices = locationtemp2 + '\\' + 'CQVertices'
    CQSegments = locationtemp2 + '\\' + 'CQSegment'
    CQSegments_centroid = locationtemp2 + '\\' + 'CQSegmentCentro'
    centroidsTable_name = 'CentroidCQdata.dbf'
    centroidsTable = locationtemp1 + '\\' + centroidsTable_name
    Overlaptable = locationtemp1 + '\\' + 'overlapingTable.csv'

    # Create points in the centroid of segment line and table with near features:
    # indentifying for each segment of line of building A the segment of line of building B in common.
    arcpy.FeatureToLine_management(Simple_CQ, CQLines)
    arcpy.FeatureVerticesToPoints_management(Simple_CQ, CQVertices, 'ALL')
    arcpy.SplitLineAtPoint_management(CQLines, CQVertices, CQSegments, '2 METERS')
    arcpy.FeatureVerticesToPoints_management(CQSegments, CQSegments_centroid, 'MID')
    arcpy.GenerateNearTable_analysis(CQSegments_centroid, CQSegments_centroid, NearTable, "1 Meters", "NO_LOCATION",
                                     "NO_ANGLE", "CLOSEST", "0")

    # Import the table with NearMatches
    NearMatches = Dbf5(NearTable).to_dataframe()

    # Import the table with attributes of the centroids of the Segments
    arcpy.TableToTable_conversion(CQSegments_centroid, locationtemp1, centroidsTable_name)
    DataCentroids0 = Dbf5(centroidsTable).to_dataframe()
    DataCentroids = DataCentroids0[['Name', 'height_ag', 'ORIG_FID']]

    # CreateJoin to Assign a Factor to every Centroid of the lines,
    FirstJoin = pd.merge(NearMatches, DataCentroids, left_on='IN_FID', right_on='ORIG_FID')
    SecondaryJoin = pd.merge(FirstJoin, DataCentroids, left_on='NEAR_FID', right_on='ORIG_FID')

    # delete matches within the same polygon Name (it can happen that lines are too close one to the other)
    # also delete matches with a distance of more than 20 cm making room for mistakes during the simplicfication of buildings but avoiding deleten boundaries
    rows = SecondaryJoin.IN_FID.count()
    for row in range(rows):
        if SecondaryJoin.loc[row, 'Name_x'] == SecondaryJoin.loc[row, 'Name_y'] or SecondaryJoin.loc[
            row, 'NEAR_DIST'] > 0.2:
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
    SecondaryJoin.to_csv(DataFactorsBoundaries, index=False)

    # Update table Datacentroids with the Fields Freeheight and Factor Shade. for those buildings without
    # shading boundaries these factors are equal to 1 and the field 'height' respectively.
    DataCentroids['FactorShade'] = 1
    DataCentroids['Freeheight'] = DataCentroids.height_ag
    Results = DataCentroids.merge(SecondaryJoin, left_on='ORIG_FID', right_on='ORIG_FID_x', how='outer')
    Results.FactorShade_y.fillna(Results['FactorShade_x'], inplace=True)
    Results.Freeheight_y.fillna(Results['Freeheight_x'], inplace=True)
    Results.rename(columns={'FactorShade_y': 'FactorShade', 'Freeheight_y': 'Freeheight'}, inplace=True)
    FinalDataCentroids = pd.DataFrame(Results, columns={'ORIG_FID', 'height', 'FactorShade', 'Freeheight'})

    FinalDataCentroids.to_csv(DataFactorsCentroids, index=False)
    gv.log('complete calculating boundaries')
    return arcpy.GetMessages()


def Burn(Buildings, DEM, DEMfinal, locationtemp1, DEM_extent, gv):
    # Create a raster with all the buildings
    Outraster = locationtemp1 + '\\' + 'AllRaster'
    arcpy.env.extent = DEM_extent  # These coordinates are extracted from the environment settings/once the DEM raster is selected directly in ArcGIS,
    arcpy.FeatureToRaster_conversion(Buildings, 'height_ag', Outraster,
                                     '0.5')  # creating raster of the footprints of the buildings

    # Clear non values and add all the Buildings to the DEM
    OutNullRas = arcpy.sa.IsNull(Outraster)  # identify noData Locations
    Output = arcpy.sa.Con(OutNullRas == 1, 0, Outraster)
    RadiationDEM = arcpy.sa.Raster(DEM) + Output
    RadiationDEM.save(DEMfinal)
    gv.log('complete burning buildings into raster')

    return arcpy.GetMessages()


def calc_sunrise(sunrise, year_to_simulate, longitude, latitude, gv):
    o = ephem.Observer()
    o.lat = str(latitude)
    o.long = str(longitude)
    s = ephem.Sun()
    for day in range(1, 366):  # Calculated according to NOAA website
        o.date = datetime.datetime(year_to_simulate, 1, 1) + datetime.timedelta(day - 1)
        next_event = o.next_rising(s)
        sunrise[day - 1] = next_event.datetime().hour
    gv.log('complete calculating sunrise')
    return sunrise


def run_as_script(scenario_path=None, weather_path=None, latitude=None, longitude=None, year=None):
    import cea.globalvar
    import cea.inputlocator
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    if weather_path is None:
        weather_path = locator.get_default_weather()
    if latitude is None:
        latitude = 47.1628017306431
    if longitude is None:
        longitude = 8.31
    if year is None:
        year = 2010
    path_default_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))

    solar_radiation_vertical(locator=locator, path_arcgis_db=path_default_arcgis_db,
                             latitude=latitude, longitude=longitude, year=year, gv=gv,
                             weather_path=weather_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    parser.add_argument('-w', '--weather', help='Path to the weather file')
    parser.add_argument('--latitude', help='Latitutde', default=47.1628017306431)
    parser.add_argument('--longitude', help='Longitude', default=8.31)
    parser.add_argument('--year', help='Year', default=2010)
    args = parser.parse_args()

    run_as_script(scenario_path=args.scenario, weather_path=args.weather, latitude=args.latitude,
                  longitude=args.longitude, year=args.year)
