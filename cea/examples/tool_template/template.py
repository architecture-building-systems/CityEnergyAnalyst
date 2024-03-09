"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""




import cea.config
import cea.inputlocator
from cea.constants import *
import pandas as pd

__author__ = "JImeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main_function(config, locator):
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
    # path_to_my_input_file = locator.get_my_input_file_path()

    #Part III. Output paths
    # Example:
    # path_to_my_output_file = locator.get_my_output_file_path()

    #Part IV. Main function
    # Example:
    # my_input_csv = pd.read_csv(path_to_my_input_file)
    # my_result_df = my_input_csv["A"] * my_input_csv["B"]

    #Part V. Saving to Outputs
    # Example:
    # my_result_df.to_csv(path_to_my_output_file)

    #Part VI return (if the function is meant to return something.
    #return my_result_df


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    main_function(config, locator)

if __name__ == '__main__':
    main(cea.config.Configuration())
