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

def calc_spatio_temporal_visuals(locator, period, list_of_buildings, initial_date, config):

    # now the dates in which the building demand is calculated is stored in 'date'
    date = pd.date_range(initial_date, periods=8760, freq='H')
    time = date.strftime("%Y%m%d%H%M%S")
    weather_data = epwreader.epw_reader(config.weather)


    # this loop checks if all the buildings are selected and gets the building names from Total demand.csv file
    if 'all' in list_of_buildings:
        building_names = pd.read_csv(locator.get_total_demand())['Name'].values
    else:
        building_names = list_of_buildings

    for i, building in enumerate(building_names):
        # importing corresponding variables of each building and then slicing it to take just a single period value
        # i.e a time step
        yearly_horizontal_rad = weather_data.glohorrad_Whm2.sum()  # [Wh/m2/year]

        # read radiation file
        sensors_rad = pd.read_json(locator.get_radiation_building(building_name=building))
        sensors_metadata = pd.read_csv(locator.get_radiation_metadata(building_name= building))
        sensors_rad.to_csv(locator.radiation_results(building_name=building + 'a'), index=True, float_format='%.2f')

        # join total radiation to sensor_metadata
        sensors_rad['total_rad_Whm2'] = sensors_rad.sum(1)  # add new row with yearly radiation
        sensors_rad['date'] = time
        sensors_metadata.set_index('SURFACE', inplace=True)
        sensors_metadata = sensors_metadata.merge(sensors_rad, left_index=True, right_index=True)  # [Wh/m2]

        # remove window surfaces
        sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'windows']

        # keep sensors if allow pv installation on walls or on roofs
        if config.solar.panel_on_roof is False:
            sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'roofs']
        if config.solar.panel_on_wall is False:
            sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'walls']

        sensors_rad_clean = sensors_rad[sensors_metadata.index.tolist()]  # keep sensors above min radiation
        sensors_rad.to_csv(locator.radiation_results(building_name=building), index=True, float_format='%.2f')  # print PV generation potential



def main(config):

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    initial_date = '1/1/2015'
    list_of_buildings = ['all']  # 'all' for all buildings or else provide a list of building names
    period = [1680, 1848] # period in hours of the year to viualize
    calc_spatio_temporal_visuals(locator, period, list_of_buildings, initial_date, config)


if __name__ == '__main__':
    main(cea.config.Configuration())