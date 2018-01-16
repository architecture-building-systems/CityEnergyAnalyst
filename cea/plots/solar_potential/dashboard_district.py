"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
from cea.plots.solar_potential.insolation_curve import insolation_curve
from cea.utilities import epwreader
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def aggregate(analysis_fields, buildings, locator):
    for i, building in enumerate(buildings):
        geometry = pd.read_csv(locator.get_radiation_metadata(building))
        geometry['code'] = geometry['TYPE'] + '_' + geometry['orientation']
        insolation = pd.read_json(locator.get_radiation_building(building))
        if i == 0:
            df = {}
            for field in analysis_fields:
                select_sensors = geometry.loc[geometry['code']== field].SURFACE.values

                df[field] = insolation[select_sensors].sum(axis=1)

        else:
            for field in analysis_fields:
                select_sensors = geometry.loc[geometry['code']== field].SURFACE.values
                df[field] = df[field] + insolation[select_sensors].sum(axis=1)
    return pd.DataFrame(df)

def dashboard(locator, config):

    # Local Variables
    # GET LOCAL VARIABLES
    buildings = []#["B05","B03", "B01", "B04", "B06"]

    if buildings == []:
        buildings = pd.read_csv(locator.get_total_demand()).Name.values


    #CREATE INSOLATION CURVE PER MAIN SURFACE
    output_path = locator.get_timeseries_plots_file("District" + '_Solar_isolation_load_curve')
    title = "Insolation Curve for District"
    analysis_fields = ['windows_east', 'windows_west', 'windows_south', 'windows_north',
                       'walls_east','walls_west','walls_south','walls_north','roofs_top', "T_out_dry_C"]
    data = aggregate(analysis_fields, buildings, locator)
    weather_data = epwreader.epw_reader(config.weather)[["drybulb_C", "wetbulb_C", "skytemp_C"]]
    data["T_out_dry_C"] = weather_data["drybulb_C"].values
    insolation_curve(data, analysis_fields, title, output_path)


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    dashboard(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
