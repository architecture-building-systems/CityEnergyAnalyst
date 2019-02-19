import os

import pandas as pd
from simpledbf import Dbf5

from legacy.arcgis import arcpy


def calculate_radiation_for_surfaces(observers_path, data_factor_centroids_csv, sunny_hours_of_year, temporary_folder,
                                     path_arcgis_db):
    arcpy.env.workspace = path_arcgis_db
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")

    # local variables
    CQSegments_centroid = os.path.join(path_arcgis_db, 'CQSegmentCentro')
    Outjoin = os.path.join(path_arcgis_db, 'Outjoin')
    CQSegments = os.path.join(path_arcgis_db, 'CQSegment')
    OutTable = 'CentroidsIDobserver.dbf'
    # Create Join of features Observers and CQ_sementscentroids to
    # assign Names and IDS of observers (field TARGET_FID) to the centroids of the lines of the buildings,
    # then create a table to import as a Dataframe
    arcpy.SpatialJoin_analysis(CQSegments_centroid, observers_path, Outjoin, "JOIN_ONE_TO_ONE", "KEEP_ALL",
                               match_option="CLOSEST", search_radius="10 METERS")
    arcpy.JoinField_management(Outjoin, 'OBJECTID', CQSegments, 'OBJECTID')  # add the lenghts of the Lines to the File
    arcpy.TableToTable_conversion(Outjoin, temporary_folder, OutTable)

    # ORIG_FID represents the points in the segments of the simplified shape of the building
    # ORIG_FID_1 is the observers ID
    Centroids_ID_observers0_dbf5 = Dbf5(os.path.join(temporary_folder, OutTable)).to_dataframe()
    Centroids_ID_observers_dbf5 = Centroids_ID_observers0_dbf5[
        ['Name', 'height_ag', 'ORIG_FID', 'ORIG_FID_1', 'Shape_Leng']].copy()
    Centroids_ID_observers_dbf5.rename(columns={'ORIG_FID_1': 'ID'}, inplace=True)

    # Create a Join of the Centroid_ID_observers and Datacentroids in the Second Chapter to get values of surfaces Shaded.
    Datacentroids = pd.read_csv(data_factor_centroids_csv)
    DataCentroidsFull = pd.merge(Centroids_ID_observers_dbf5, Datacentroids, left_on='ORIG_FID', right_on='ORIG_FID')

    # Read again the radiation table and merge values with the Centroid_ID_observers under the field ID in Radiationtable and 'ORIG_ID' in Centroids...
    DataRadiation = pd.merge(left=DataCentroidsFull, right=sunny_hours_of_year, left_on='ID', right_on='ID')

    return DataRadiation


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--radiation-pickle', help='path to STORE a pickle of the radiation dataframe')
    parser.add_argument('--observers-path', help='path to the observers feature layer')
    parser.add_argument('--data-factors-centroids', help='path to the DataFactorsCentroids.csv file')
    parser.add_argument('--sunny-hours-pickle', help='path to a pickle of the sunny_hours_of_year array')
    parser.add_argument('--temp-folder', help='path to a temporary folder')
    parser.add_argument('--arcgis-db', help='path to the ArcGIS geodatabase to use')
    args = parser.parse_args()

    sunny_hours_of_year = pd.read_pickle(args.sunny_hours_pickle)

    radiation = calculate_radiation_for_surfaces(observers_path=args.observers_path,
                                                 data_factor_centroids_csv=args.data_factors_centroids,
                                                 sunny_hours_of_year=sunny_hours_of_year,
                                                 temporary_folder=args.temp_folder,
                                                 path_arcgis_db=args.arcgis_db)
    radiation.to_pickle(args.radiation_pickle)
