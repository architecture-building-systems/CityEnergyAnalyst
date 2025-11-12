"""
Implements the CEA script
``csv-to-shapefile-to-csv``

Similar to how ``csv-to-dbf-to-csv`` takes a dBase database file (example.dbf) and converts that to csv format,
this does the same with a Shapefile.

It uses the ``geopandas.GeoDataFrame`` class to read in the shapefile.
The geometry column is serialized to a nested list of coordinates using the JSON notation.
"""


import cea.config
import cea.inputlocator


__author__ = "Daren Thomas, Zhongming Shi"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas, Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


import pandas as pd
import geopandas as gpd
import shapely
import json
import os


def csv_xlsx_to_shapefile(input_file, shapefile_path, shapefile_name, reference_crs_txt, geometry_type="polygon"):
    """
    Converts a CSV or Excel file to an ESRI shapefile using the CRS from a reference CRS text file.

    :param input_file: Path to the input .csv or .xlsx file.
    :param shapefile_path: Directory to store the output shapefile.
    :param shapefile_name: Name of the output shapefile.
    :param reference_crs_txt: Path to the text file containing the reference CRS.
    :param geometry_type: Type of geometry to handle. Options: "polygon", "polyline", "point".
    """

    if not reference_crs_txt:
        raise ValueError("CRS information is required when converting CSV files to ESRI Shapefiles.")

    # Read input data
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file, sep=None, engine='python')
    elif input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file)
    else:
        raise ValueError("Invalid input file format. Only .csv or .xlsx files are supported.")

    # Read reference CRS
    with open(reference_crs_txt, 'r') as file:
        crs = file.read().strip()

    # Check coordinate system (Degrees or Metres)
    geometry = df['geometry'].values.tolist()
    first_geom = json.loads(geometry[0])

    if isinstance(first_geom, list) and isinstance(first_geom[0], list):  # Checking if it is a nested list
        x0, y0, z0 = first_geom[0]
    else:
        x0, y0, z0 = first_geom

    geometry_in_metres = abs(x0) > 180 or abs(y0) > 90  # True if coordinates are in metres

    if 'epsg:4326' in str(crs) and geometry_in_metres:
        raise ValueError("The provided reference CRS appears to be in decimal degrees while the coordinates "
                         "in the CSV file are in metres. A projected CRS is required for converting metre-based coordinates.")

    # Convert geometry based on type
    if geometry_type == "polygon":
        geometry = [shapely.Polygon(json.loads(g)) for g in df.geometry]
    elif geometry_type == "polyline":
        geometry = [shapely.LineString(json.loads(g)) for g in df.geometry]
    elif geometry_type == "point":
        geometry = [shapely.Point(json.loads(g)) for g in df.geometry]
    else:
        raise ValueError("Invalid geometry type. Use 'polygon', 'polyline', or 'point'.")

    # Create GeoDataFrame and export
    df.drop(columns=['geometry'], inplace=True, errors='ignore')
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf.to_file(os.path.join(shapefile_path, f"{shapefile_name}"), driver='ESRI Shapefile', encoding='ISO-8859-1')

    print(f"Shapefile {shapefile_name} successfully created at {shapefile_path}.")


def serialize_geometry(geom):
    if geom.geom_type == 'Polygon':
        return [[coord[0], coord[1], coord[2] if len(coord) == 3 else 0.0] for coord in geom.exterior.coords]
    elif geom.geom_type == 'LineString':
        return [[coord[0], coord[1], coord[2] if len(coord) == 3 else 0.0] for coord in geom.coords]
    elif geom.geom_type == 'Point':
        if geom.has_z:
            return [geom.x, geom.y, geom.z]
        else:
            return [geom.x, geom.y, 0.0]
    else:
        return None

def shapefile_to_csv_xlsx(shapefile, output_path, new_crs=None):
    """
    Converts an ESRI shapefile to a .csv or .xlsx file, including a 'geometry' column with serialized coordinates.
    Writes CRS information to a .txt file.

    :param shapefile: Path to the input shapefile
    :param output_path: Path to store the output .csv or .xlsx file
    :param new_crs: Coordinate reference system to project the geometries (optional)
    """
    try:
        gdf = gpd.read_file(shapefile)
        if new_crs is None:
            new_crs = gdf.crs
        gdf = gdf.to_crs(new_crs)

        df = pd.DataFrame(gdf.drop(columns='geometry'))
        df['geometry'] = gdf.geometry.apply(serialize_geometry)

        if output_path.endswith('.csv'):
            df.to_csv(output_path, index=False)
        elif output_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        else:
            raise ValueError("Output file name must end with '.csv' or '.xlsx'.")

        crs_file_path = os.path.splitext(output_path)[0] + "_crs.txt"
        with open(crs_file_path, 'w') as file:
            file.write(str(new_crs))

        print(f"File saved at {output_path}")
        print(f"CRS saved at {crs_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")



def main(config: cea.config.Configuration):
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
    reference_crs_txt = config.shapefile_tools.reference_crs_file

    if input_file.endswith('.csv') or input_file.endswith('.xlsx'):
        # print out all configuration variables used by this script
        print("Running csv-xlsx-to-shapefile with csv-file = %s" % input_file)
        print("Running csv-xlsx-to-shapefile with polygon = %s" % polygon)
        print("Saving the generated shapefile to directory = %s" % output_path)
        if polygon:
            csv_xlsx_to_shapefile(input_file=input_file, shapefile_path=output_path, shapefile_name=output_file_name, reference_crs_txt=reference_crs_txt, geometry_type="polygon")
        else:
            csv_xlsx_to_shapefile(input_file=input_file, shapefile_path=output_path, shapefile_name=output_file_name, reference_crs_txt=reference_crs_txt, geometry_type="polyline")

        print("ESRI Shapefile has been generated.")

    elif input_file.endswith('.shp'):
        # print out all configuration variables used by this script
        print("Running shapefile-to-csv with shapefile = %s" % config.shapefile_tools.input_file)
        print("Running shapefile-to-csv with csv-file = %s" % config.shapefile_tools.output_path)

        output_file_path = os.path.join(output_path, output_file_name)
        shapefile_to_csv_xlsx(shapefile=input_file, output_path=output_file_path)

        print("csv file has been generated.")

    else:
        raise ValueError("""Input file type is not supported. Only .shp, .csv and .xlsx file types are supported.""")


if __name__ == '__main__':
    main(cea.config.Configuration())
