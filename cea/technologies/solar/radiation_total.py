"""
Total radiation calculator from the insolation files
"""
from __future__ import division
import pandas as pd
from cea.utilities import dbfreader
import cea.inputlocator
import cea.config
from cea.utilities import epwreader


__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_spatio_temporal_visuals(locator, list_of_buildings, initial_date, config):

    # now the dates in which the building demand is calculated is stored in 'date'
    date = pd.date_range(initial_date, periods=8760, freq='H')
    time = date.strftime("%Y%m%d%H%M%S")

    # this loop checks if all the buildings are selected and gets the building names from Total demand.csv file
    if 'all' in list_of_buildings:
        building_names = pd.read_csv(locator.get_total_demand())['Name'].values
    else:
        building_names = list_of_buildings

    for i, building in enumerate(building_names):

        sensors_rad = pd.read_json(locator.get_radiation_building(building_name=building))
        sensors_metadata = pd.read_csv(locator.get_radiation_metadata(building_name= building))

        sensors_metadata_roof = sensors_metadata[sensors_metadata.TYPE == 'roofs']
        sensors_metadata_walls = sensors_metadata[sensors_metadata.TYPE == 'walls']
        sensors_metadata_windows = sensors_metadata[sensors_metadata.TYPE == 'windows']

        #  segregating the surfaces with SURFACE TYPE as roof
        roof_cols = [c for c in sensors_rad.columns if c in sensors_metadata_roof.SURFACE.tolist()]
        sensors_rad_roof = pd.DataFrame()
        #  Calculating weighted average for all the surfaces with SURFACE TYPE as roof
        for i in roof_cols:
            sensors_rad_roof[i] = sensors_rad[i] * (sensors_metadata_roof[sensors_metadata_roof.SURFACE == i].AREA_m2.values)
        sensors_rad_roof = sensors_rad_roof /  (sensors_metadata_roof.AREA_m2.sum(0))

        #  segregating the surfaces with SURFACE TYPE as walls
        walls_cols = [c for c in sensors_rad.columns if c in sensors_metadata_walls.SURFACE.tolist()]
        sensors_rad_walls = pd.DataFrame()
        #  Calculating weighted average for all the surfaces with SURFACE TYPE as walls
        for i in walls_cols:
            sensors_rad_walls[i] = sensors_rad[i] * (sensors_metadata_walls[sensors_metadata_walls.SURFACE == i].AREA_m2.values)
        sensors_rad_walls = sensors_rad_walls / (sensors_metadata_walls.AREA_m2.sum(0))

        sensors_rad_final = pd.DataFrame()
        sensors_rad_final['total_roof_rad_Wperm2'] = sensors_rad_roof.sum(1)
        sensors_rad_final['total_wall_rad_Wperm2'] = sensors_rad_walls.sum(1)
        sensors_rad_final['date'] = time
        sensors_rad_final.to_csv(locator.radiation_results(building_name=building), index=True, float_format='%.2f')

def main(config):

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    initial_date = '1/1/2015'
    list_of_buildings = ['all']  # 'all' for all buildings or else provide a list of building names
    calc_spatio_temporal_visuals(locator, list_of_buildings, initial_date, config)

if __name__ == '__main__':
    main(cea.config.Configuration())