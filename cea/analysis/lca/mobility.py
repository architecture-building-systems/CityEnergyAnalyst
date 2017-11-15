"""
Primary energy and CO2 emissions model algorithm for mobility

M. Mosteiro Romero  script development          31.08.16
"""

from __future__ import division

import os
import pandas as pd
from geopandas import GeoDataFrame as gpdf
import cea.inputlocator

__author__ = "Martin Mosteiro Romero"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro Romero"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def lca_mobility(locator, config):
    """
    Calculation of the primary energy and CO2 emissions for mobility in the area based on the present day values
    calculated for the 2000 Watt society target.

    The current values for the Swiss case for each type of occupancy are based on the following sources:

    - [SIA_2040_2011]_: 'MULTI_RES', 'SINGLE_RES', 'SCHOOL', 'OFFICE'
    - [BFE_2012]_: 'HOTEL', 'RETAIL', 'FOODSTORE', 'RESTAURANT'

    Due to a lack of data, multiple values had to be assumed:

    - 'INDUSTRY': assumed to be equal to the value for the use type 'OFFICE'
    - 'HOSPITAL': assumed to be equal to the value for the use type 'HOTEL'
    - 'GYM', 'SWIMMING': assumed to be equal to the value for use type 'RETAIL'
    - 'SERVERROOM', 'COOLROOM': assumed negligible

    The following file is created as a side effect by this script:

    - total_LCA_mobility (.csv)
      csv file of yearly non-renewable primary energy demand and emissions due to mobility for each building

    Additional references:

    - [SIA_Effizienzpfad_2011]_

    :param locator: an InputLocator instance set to the scenario to work on
    :type locator: InputLocator

    .. [SIA_2040_2011] Swiss Society of Engineers and Architects (SIA). 2011. "SIA Efficiency Path 2040."
    .. [BFE_2012] Bundesamt fur Energie (BFE). 2012. "Arealentwicklung fur die 2000-Watt Gesellschaft:
        Beurteilungsmethode in Anlehnung an den SIA-Effizienzpfad Energie."
    .. [SIA_Effizienzpfad_2011] Swiss Society of Engineers and Architects (SIA). 2011. "SIA Effizienzpfad: Bestimmung
        der Ziel- und Richtwerte mit dem Top-Down Approach."
    .. [SIA_2024_2015]: Swiss Society of Engineers and Architects (SIA). 2015. "Merkblatt 2024: Raumnutzungsdaten fur
        die Energie- und Gebaeudetechnik."
    """

    # local files
    demand = pd.read_csv(locator.get_total_demand())
    prop_occupancy = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)#.set_index('Name')
    factors_mobility = pd.read_excel(locator.get_data_benchmark(config.region), sheetname='MOBILITY').drop('Description', axis=1)

    # calculate total_LCA_mobility: .csv
    occupancy_type = factors_mobility['code']
    non_renewable_energy = factors_mobility['NRE_today']
    emissions = factors_mobility['CO2_today']

    mobility = prop_occupancy.merge(demand,on='Name')
    fields_to_plot = ['Name', 'GFA_m2', 'M_nre_pen_GJ', 'M_nre_pen_MJm2', 'M_ghg_ton', 'M_ghg_kgm2']
    mobility[fields_to_plot[3]] = 0
    mobility[fields_to_plot[5]] = 0
    for i in range(len(occupancy_type)):
        mobility[fields_to_plot[3]] += mobility[occupancy_type[i]] * non_renewable_energy[i]
        mobility[fields_to_plot[5]] += mobility[occupancy_type[i]] * emissions[i]
    mobility[fields_to_plot[2]] = mobility['GFA_m2'] * mobility[fields_to_plot[3]] / 1000
    mobility[fields_to_plot[4]] = mobility['GFA_m2'] * mobility[fields_to_plot[5]] / 1000

    mobility[fields_to_plot].to_csv(locator.get_lca_mobility(), index=False, float_format='%.2f')

def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print("Running mobility with scenario = %s" % config.scenario)

    lca_mobility(locator=locator, config=config)

if __name__ == '__main__':
    main(cea.config.Configuration())

