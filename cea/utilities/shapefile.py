"""
Implements the CEA script
``csv-to-shapefile-to-csv``

Similar to how ``csv-to-dbf-to-csv`` takes a dBase database file (example.dbf) and converts that to csv format,
this does the same with a Shapefile.

It uses the ``geopandas.GeoDataFrame`` class to read in the shapefile.
The geometry column is serialized to a nested list of coordinates using the JSON notation.
"""


import os
import shapely
import json
import pandas as pd
import geopandas as gpd
import ast

import cea.config
import cea.inputlocator
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_lat_lon_projected_shapefile

__author__ = "Daren Thomas, Zhongming Shi"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas, Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def csv_xlsx_to_shapefile(input_file, shapefile_path, shapefile_name, reference_shapefile, polygon):
    """
    This function converts .csv file to ESRI shapefile using the crs of a reference ESRI shapefile.

    :param csv_file: path to the input .csv file
    :type csv_file: string
    :param shapefile_path: directory to story the output shapefile
    :type shapefile_path: string
    :param shapefile_name: name of the output shapefile
    :type shapefile_name: string
    :param reference_shapefile: path to the reference shapefile
    :type reference_shapefile: string
    :param polygon: Set this to ``False`` if the csv file contains polyline data in the
        ``geometry`` column instead of the default polygon data. (polylines are used for representing streets etc.)
    :type polygon: bool
    """

    if not reference_shapefile:
        raise ValueError("""The reference-shapefile cannot be blank when converting csv files to ESRI Shapefiles. """)

    # generate crs and DataFrame from files
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file, sep=None)

    elif input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file)

    else:
        print("The input file type is not valid. Only .csv or .xlsx file types are supported.")

    # generate GeoDataFrames from files and get its crs
    gdf = gpd.GeoDataFrame.from_file(reference_shapefile)
    crs = gdf.crs

    # Check if the unit of the geometry's coordinates is in metres
    geometry = df['geometry'].values.tolist()
    x0 = ast.literal_eval(geometry[0])[0][0]
    y0 = ast.literal_eval(geometry[0])[0][1]
    geometry_in_metres = abs(x0) > 180 or abs(y0) > 90     # True if coordinates in metres
    #todo: this method is not 100% accurate but at least for now works for most of the cases.

    # if the coordinates are in metres and the crs of the reference shapefile is not projected in metres,
    # convert the coordinates to degrees
    if 'epsg:4326' in str(crs) and geometry_in_metres:
        print("The coordinates in this reference shapefile seems to be in decimal degrees while the unit of coordinates "
              "in the .csv file is in metres. CEA is projecting the reference shapefile first in metres and then convert "
              "the .csv file to ESRI Shapefile based on the reference shapefile.")

        # get longitude and latitude of reference shapefile's centroid
        lat, lon = get_lat_lon_projected_shapefile(gdf)
        # project the reference geometry to the global crs and get the crs
        gdf = gdf.to_crs(get_projected_coordinate_system(lat=lat, lon=lon))

    if polygon:
        geometry = [shapely.geometry.polygon.Polygon(json.loads(g)) for g in df.geometry]
    else:
        geometry = [shapely.geometry.LineString(json.loads(g)) for g in df.geometry]
    df.drop('geometry', axis=1)

    gdf = gpd.GeoDataFrame(df, crs=gdf.crs, geometry=geometry)
    gdf.to_file(os.path.join(shapefile_path, '{filename}'.format(filename=shapefile_name)),
                driver='ESRI Shapefile', encoding='ISO-8859-1')


import geopandas as gpd
import pandas as pd
import os

def shapefile_to_csv_xlsx(shapefile, output_file_path, output_file_name):
    """
    Converts an ESRI shapefile to a .csv or .xlsx file, including a 'geometry' column with serialized coordinates.
    Writes CRS information to a .txt file.

    :param shapefile: Path to the input shapefile
    :type shapefile: str
    :param output_file_path: Directory to store the output .csv or .xlsx file
    :type output_file_path: str
    :param output_file_name: Name of the output .csv or .xlsx file
    :type output_file_name: str
    """
    try:
        # Read shapefile into a GeoDataFrame
        gdf = gpd.read_file(shapefile)
        crs = gdf.crs.to_string() if gdf.crs else "CRS information not available"

        # Process geometries and convert to a projected CRS if possible
        lat, lon = get_lat_lon_projected_shapefile(gdf)  # Ensure this function is implemented
        gdf = gdf.to_crs(get_projected_coordinate_system(lat=lat, lon=lon))

        # Convert GeoDataFrame to DataFrame
        df = pd.DataFrame(gdf.drop(columns='geometry'))
        df['geometry'] = gdf.geometry.apply(serialize_geometry)  # Ensure serialize_geometry is implemented

        # Write DataFrame to CSV or Excel
        output_path = os.path.join(output_file_path, output_file_name)
        if output_file_name.endswith('.csv'):
            df.to_csv(output_path, index=False)
        elif output_file_name.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        else:
            raise ValueError("Output file name must end with '.csv' or '.xlsx'.")

        # Write CRS to a text file
        crs_file_name = os.path.splitext(output_file_name)[0] + "_crs.txt"
        crs_file_path = os.path.join(output_file_path, crs_file_name)
        with open(crs_file_path, 'w') as file:
            file.write(crs)

    except Exception as e:
        print(f"An error occurred: {e}")


def serialize_geometry(geometry):
    """Take a shapely.geometry.polygon.Polygon and represent it as a string of tuples (x, y)

    :param geometry: a polygon or polyline to extract the points from and represent as a json object
    :type geometry: shapely.geometry.polygon.Polygon
    """
    if isinstance(geometry, shapely.geometry.polygon.Polygon):
        points = list(geometry.exterior.coords)
    elif isinstance(geometry, shapely.geometry.LineString):
        points = list(geometry.coords)
    else:
        raise ValueError("Expected either a Polygon or a LineString, got %s" % type(geometry))
    return json.dumps(points)


def main(config):
    """
    Run :py:func:`shp-to-csv-to-shp` with the values from the configuration file, section ``[shapefile-tools]``.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """

    assert os.path.exists(config.shapefile_tools.input_file), 'input file not found: %s' % config.scenario

    input_file = config.shapefile_tools.input_file
    output_file_name = config.shapefile_tools.output_file_name
    output_path = config.shapefile_tools.output_path
    polygon = config.shapefile_tools.polygon
    reference_shapefile = config.shapefile_tools.reference_shapefile

    if input_file.endswith('.csv') or input_file.endswith('.xlsx'):
        # print out all configuration variables used by this script
        print("Running csv-xlsx-to-shapefile with csv-file = %s" % input_file)
        print("Running csv-xlsx-to-shapefile with polygon = %s" % polygon)
        print("Saving the generated shapefile to directory = %s" % output_path)

        csv_xlsx_to_shapefile(input_file=input_file, shapefile_path=output_path, shapefile_name=output_file_name, reference_shapefile=reference_shapefile, polygon=polygon)

        print("ESRI Shapefile has been generated.")

    elif input_file.endswith('.shp'):
        # print out all configuration variables used by this script
        print("Running shapefile-to-csv with shapefile = %s" % config.shapefile_tools.input_file)
        print("Running shapefile-to-csv with csv-file = %s" % config.shapefile_tools.output_path)

        shapefile_to_csv_xlsx(shapefile=input_file, output_file_path=output_path, output_file_name=output_file_name)

        print("csv file has been generated.")

    else:
        raise ValueError("""Input file type is not supported. Only .shp, .csv and .xlsx file types are supported.""")


if __name__ == '__main__':
    main(cea.config.Configuration())
