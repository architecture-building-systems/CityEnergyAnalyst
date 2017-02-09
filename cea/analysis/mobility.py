"""
Primary energy and CO2 emissions due to mobility
"""
from __future__ import division

import os

import pandas as pd
from geopandas import GeoDataFrame as gpdf

from cea import inputlocator

__author__ = "Martin Mosteiro"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def lca_mobility(locator):
    """
    algorithm to calculate the primary energy and CO2 emissions for mobility
    in the area in order to compare with the 2000 Watt society benchmark
    based on SIA Standard 2039 (expanded to include industry and hospital
    buildings)

    Produces Total_LCA_mobility.csv containing the yearly primary energy demand and emissions due to mobility for each
    building.

    :param locator: an InputLocator instance set to the scenario to work on
    :type locator: cea.inputlocator.InputLocator
    """

    # local files
    demand = pd.read_csv(locator.get_total_demand())
    prop_occupancy = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)  # .set_index('Name')
    data_mobility = locator.get_data_mobility()
    factors_mobility = pd.read_excel(data_mobility, sheetname='2010')

    # calculate total_LCA_mobility:.csv
    vt = factors_mobility['code']
    pt = factors_mobility['PEN']
    gt = factors_mobility['CO2']

    mobility = prop_occupancy.merge(demand, on='Name')
    fields_to_plot = ['Name', 'GFA_m2', 'M_nre_pen_GJ', 'M_nre_pen_MJm2', 'M_ghg_ton', 'M_ghg_kgm2']
    mobility[fields_to_plot[3]] = 0
    mobility[fields_to_plot[5]] = 0
    for i in range(len(vt)):
        mobility[fields_to_plot[3]] += mobility[vt[i]] * pt[i]
        mobility[fields_to_plot[5]] += mobility[vt[i]] * gt[i]
    mobility[fields_to_plot[2]] = mobility['GFA_m2'] * mobility[fields_to_plot[3]] / 1000
    mobility[fields_to_plot[4]] = mobility['GFA_m2'] * mobility[fields_to_plot[5]] / 1000

    mobility[fields_to_plot].to_csv(locator.get_lca_mobility(), index=False, float_format='%.2f')


def run_as_script(scenario_path=None):
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    if not scenario_path:
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    lca_mobility(locator=locator)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    args = parser.parse_args()
    run_as_script(scenario_path=args.scenario)
