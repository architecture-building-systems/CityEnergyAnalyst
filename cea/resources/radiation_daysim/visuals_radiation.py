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

def calc_spatio_temporal_visuals(locator, period):

    date = pd.date_range('1/1/2010', periods=8760, freq='H')[period[0]: period[1]]
    buildings = dbfreader.dbf2df(locator.get_building_occupancy())['Name']
    location = locator.get_solar_radiation_folder()
    time = date.strftime("%Y%m%d%H%M%S")

    for i, building in enumerate(buildings):
        data = pd.read_csv(os.path.join(location, building+'_geometry.csv'))
        geometry = data.set_index('SURFACE')
        solar = pd.read_csv(os.path.join(location, building+'_insolation_Whm2.csv'))
        surfaces = solar.columns.values

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

    dbfreader.df2dbf(final, locator.get_solar_radiation_folder()+"result_solar_48h.dbf")

def main(locator):
    # Create City GML file (this is necesssary only once).
    period = [1,48] # period in hours of the year to viualize
    calc_spatio_temporal_visuals(locator, period)

if __name__ == '__main__':

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    main(locator=locator)