"""
This is a template script - an example of how a CEA script should be set up.

NOTE: Hello. this is the main script for optimsiaiton of different energy system components that may incur in a PED concept
"""




import os
import cea.config
import cea.inputlocator

from cea.constants import OPT_EFF, A1, A2, DT
import pandas as pd 
import numpy as np


__author__ = "Juveria och Puneet"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Juveria puneet"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def ptc_calculation(config, locator):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line / user interface

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    #Part I. local variables
    # Example:
    tin_ptc = config.solar_concentrating.t_in_ptc


    #Part II. Input paths
    # Example:
    path_to_my_input_file = locator.PVT_totals()
    path_to_my_date_file = locator.PV_totals()


    #Part III. Output paths
    # Example:
    output_path = locator.get_ptc_total_file_path()


    #Part IV. Main function
    # Example:
    my_input_csv = pd.read_csv(path_to_my_input_file)
    my_date_csv = pd.read_csv(path_to_my_date_file)
    date = my_date_csv["Date"].values
    mcp_from_pvt = my_input_csv["mcp_PVT_kWperC"].values
    ptc_area_from_pvt = my_input_csv["PVT_roofs_top_m2"].values
    #ghi_rooftop_ptc = np.zeros(8760) #this is the dummy file to calculate solar radiation. we WILL do this.
    ghi_rooftop_ptc = my_input_csv["radiation_kWh"].values

    solar_radiation_whm2 = ghi_rooftop_ptc / ( 1000 * ptc_area_from_pvt )
    eff_total = OPT_EFF - A1 * (DT + tin_ptc ) / solar_radiation_whm2  - A2 * ((DT + tin_ptc ) / solar_radiation_whm2) ** 2
    kwh_ptc_m2 = solar_radiation_whm2 * eff_total * 1000
    Q_ptc_kwhtotal = ptc_area_from_pvt * kwh_ptc_m2

    #Part V. Saving to Outputs
    # Example:
    my_result_df = pd.DataFrame({"Q_ptc_kwhtotal": Q_ptc_kwhtotal, "DATE": date})
    my_result_df.to_csv(output_path, index=False)

    #Part VI return (if the function is meant to return something.
    #return my_result_df

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    ptc_calculation(config, locator)

if __name__ == '__main__':
    main(cea.config.Configuration())
