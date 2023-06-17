"""
This is a template script - an example of how a CEA script should be set up.

NOTE: Hello. this is the main script for optimsiaiton of different energy system components that may incur in a PED concept
"""




import os
import cea.config
import cea.inputlocator
from cea.constants import *
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


def main(config, locator):
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
    # my_variable = config.my_tool.my_variable

    #Part II. Input paths
    # Example:
    path_to_my_input_file = locator.PVT_totals()

    #Part III. Output paths
    # Example:
    # path_to_my_output_file = locator.get_my_output_file_path()

    #Part IV. Main function
    # Example:
    my_input_csv = pd.read_csv(path_to_my_input_file)
    mcp_from_pvt = my_input_csv["mcp_PVT_kWperC"]
    ptc_area_from_pvt = my_input_csv["PVT_roofs_top_m2"]
    #ghi_rooftop_ptc = np.zeros(8760) #this is the dummy file to calculate solar radiation. we WILL do this.
    ghi_rooftop_ptc = my_input_csv["radiation_kWh"]




    #Part V. Saving to Outputs
    # Example:
    # my_result_df.to_csv(path_to_my_output_file)

    #Part VI return (if the function is meant to return something.
    #return my_result_df


if __name__ == '__main__':
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    main(config, locator)
