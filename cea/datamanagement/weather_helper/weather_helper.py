"""
The weather-helper script sets the weather data used (``inputs/weather.epw``) for simulations.
"""

import os
import shutil
from io import BytesIO
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import geopandas as gpd
import requests

import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.weather_helper.generate_weather_data_sources import WEATHER_DATA_LOCATION


def fetch_weather_data(weather_file: str, zone_file: str):
    """
    Fetch weather data from Climate.OneBuilding based on zone location

    """
    zone_gdf = gpd.read_file(zone_file)
    weather_data = gpd.read_file(WEATHER_DATA_LOCATION)

    # Find nearest weather data based on centroid of zone
    centroid = zone_gdf.make_valid().to_crs(weather_data.crs).unary_union.centroid
    index = weather_data.sindex.nearest(centroid)[1][0]
    url = f"https://climate.onebuilding.org/{weather_data.iloc[index]['url']}"
    data_source_url = "https://climate.onebuilding.org/sources/default.html"

    print(f"Downloading weather data: {url}")
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError(f"Failed to download weather data from {url}")

    with TemporaryDirectory() as tmpdir, ZipFile(BytesIO(r.content)) as z:
        for file_info in z.infolist():
            if file_info.filename.endswith('.epw'):
                z.extract(file_info, tmpdir)
                shutil.copyfile(os.path.join(tmpdir, file_info.filename), weather_file)
    print(f"For more information about TMYx weather files, visit {data_source_url}")

    with open(os.path.join(os.path.dirname(weather_file), "reference.txt"), "w") as f:
        f.write(
            f"Weather file downloaded from {url}\n\n"
            f"Data source information: {data_source_url}"
        )


def copy_weather_file(source_weather_file, locator):
    """
    Copy a weather file to the scenario's inputs.

    :param string source_weather_file: path to a weather file (``*.epw``)
    :param cea.inputlocator.InputLocator locator: use the InputLocator to find output path
    :return: (this script doesn't return anything)
    """
    from shutil import copyfile
    assert os.path.exists(source_weather_file), "Could not find weather file: {source_weather_file}".format(
        source_weather_file=source_weather_file
    )
    copyfile(source_weather_file, locator.get_weather_file())
    print("Set weather for scenario <{scenario}> to {source_weather_file}".format(
        scenario=os.path.basename(locator.scenario),
        source_weather_file=source_weather_file
    ))


def main(config):
    """
    Assign the weather file to the input folder.

    :param cea.config.Configuration config: Configuration object for this script
    :return:
    """
    locator = cea.inputlocator.InputLocator(config.scenario)
    weather = config.weather_helper.weather

    locator.ensure_parent_folder_exists(locator.get_weather_file())
    if config.weather_helper.weather == 'climate.onebuilding.org':
        print("No weather provided, fetching from online sources.")
        fetch_weather_data(locator.get_weather_file(), locator.get_zone_geometry())
    else:
        copy_weather_file(weather, locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
