import os
import tempfile
import pandas as pd
import arcpy
from simpledbf import Dbf5



def CalcRadiationSurfaces(Observers, DataFactorsCentroids, DataradiationLocation,  locationtemp1, locationtemp2):
    # local variables
    CQSegments_centroid = locationtemp2+'\\'+'CQSegmentCentro'
    Outjoin = locationtemp2+'\\'+'Join'
    CQSegments = locationtemp2+'\\'+'CQSegment'
    OutTable = 'CentroidsIDobserver.dbf'
    # Create Join of features Observers and CQ_sementscentroids to
    # assign Names and IDS of observers (field TARGET_FID) to the centroids of the lines of the buildings,
    # then create a table to import as a Dataframe
    arcpy.SpatialJoin_analysis(CQSegments_centroid,Observers,Outjoin,"JOIN_ONE_TO_ONE","KEEP_ALL",match_option="CLOSEST",search_radius="10 METERS")
    arcpy.JoinField_management(Outjoin,'OBJECTID',CQSegments, 'OBJECTID') # add the lenghts of the Lines to the File
    arcpy.TableToTable_conversion(Outjoin, locationtemp1, OutTable)

    #ORIG_FID represents the points in the segments of the simplified shape of the building
    #ORIG_FID_1 is the observers ID
    Centroids_ID_observers0 = Dbf5(locationtemp1+'\\'+OutTable).to_dataframe()
    Centroids_ID_observers = Centroids_ID_observers0[['Name','height_ag','ORIG_FID','ORIG_FID_1','Shape_Leng']]
    Centroids_ID_observers.rename(columns={'ORIG_FID_1':'ID'},inplace=True)

    #Create a Join of the Centroid_ID_observers and Datacentroids in the Second Chapter to get values of surfaces Shaded.
    Datacentroids = pd.read_csv(DataFactorsCentroids)
    DataCentroidsFull = pd.merge(Centroids_ID_observers,Datacentroids,left_on='ORIG_FID',right_on='ORIG_FID')

    #Read again the radiation table and merge values with the Centroid_ID_observers under the field ID in Radiationtable and 'ORIG_ID' in Centroids...
    Radiationtable = pd.read_csv(DataradiationLocation,index_col='Unnamed: 0')
    DataRadiation = pd.merge(left=DataCentroidsFull, right=Radiationtable, left_on='ID', right_on='ID')

    Data_radiation_path = locationtemp1+'\\'+'tempradaition.csv'
    DataRadiation.to_csv(Data_radiation_path, index = False)

    return Data_radiation_path




if __name__ == '__main__':
    path_temporary = tempfile.gettempdir()
    DataFactorsCentroids = path_temporary + '\\' + 'DataFactorsCentroids.csv'
    DataradiationLocation = path_temporary + '\\' + 'RadiationYear.csv'
    path_arcgisDB = os.path.expandvars(r'%USERPROFILE%\Documents\ArcGIS\Default.gdb')
    observers = path_arcgisDB + '\\' + 'observers'

    Data_radiation_path = CalcRadiationSurfaces(observers, DataFactorsCentroids,
                                                DataradiationLocation, path_temporary, path_arcgisDB)