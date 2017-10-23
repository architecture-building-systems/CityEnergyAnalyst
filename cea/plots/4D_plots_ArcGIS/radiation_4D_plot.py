import pandas as pd
import os
from cea.utilities import dbfreader
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_spatio_temporal_visuals(locator, period, variables_to_plot, initial_date, list_of_buildings):

    date = pd.date_range(initial_date, periods=8760, freq='H')[period[0]: period[1]]
    location = locator.get_solar_radiation_folder()
    time = date.strftime("%Y%m%d%H%M%S")

    # this loop checks if all the buildings are selected and gets the building names from Total demand.csv file
    if 'all' in list_of_buildings:
        building_names = pd.read_csv(locator.get_total_demand())['Name'].values
    else:
        building_names = list_of_buildings

    for i, building in enumerate(building_names):
        data = pd.read_csv(locator.get_radiation_metadata(building))
        geometry = data.set_index('SURFACE')
        solar = pd.read_json(locator.get_radiation_building(building))
        surfaces = solar.columns.values
        print (building)

        for surface in surfaces:
            Xcoor = geometry.loc[surface, 'Xcoor']
            Ycoor = geometry.loc[surface, 'Ycoor']
            Zcoor = geometry.loc[surface, 'Zcoor']
            result = pd.DataFrame({'date': time , 'surface':building+surface,
                                   'I_Wm2': solar[surface].values[period[0]: period[1]],
                                   'Xcoor': Xcoor, 'Ycoor': Ycoor, 'Zcoor':Zcoor})
            if i == 0:
                final = result
            else:
                final = final.append(result, ignore_index=True)

    dbfreader.dataframe_to_dbf(final, locator.get_solar_radiation_folder() + "result_solar_48h.dbf")

def run_as_script():
    import cea.inputlocator
    import cea.config
    config = cea.config.Configuration()

    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)

    variables_to_plot = ['E_PV_gen_kWh', 'radiation_kWh']
    initial_date = '1/1/2015'
    list_of_buildings = ['all']  # 'all' for all buildings or else provide a list of building names
    # Create City GML file (this is necesssary only once).
    period = [1,48] # period in hours of the year to viualize
    calc_spatio_temporal_visuals(locator, period, variables_to_plot, initial_date, list_of_buildings)

if __name__ == '__main__':

    run_as_script()