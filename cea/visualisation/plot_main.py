"""
CEAFrontEnd – Combines everything

"""

import cea.config
from cea.visualisation.c_plotter import generate_fig
from cea.visualisation.a_data_loader import plot_input_processor
from cea.visualisation.b_data_processor import calc_x_y_metric


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def config_config_locator(config, plot_cea_feature):
    if plot_cea_feature == 'demand':
        config_config = config.plots_demand
    else:
        raise ValueError(f"Cannot locate the config section for {plot_cea_feature}")
    return config_config


def plot_all(config, scenario, plot_cea_feature, hour_start, hour_end):
    # Find the config file
    config_config = config_config_locator(config, plot_cea_feature)

    # Activate a_data_loader
    df_summary_data, df_architecture_data, plot_instance = plot_input_processor(config_config, scenario, plot_cea_feature, hour_start, hour_end)

    # Activate b_data_processor
    df_to_plotly, list_y_columns = calc_x_y_metric(config_config, plot_instance, plot_cea_feature, df_summary_data, df_architecture_data)

    # Activate c_plotter
    fig = generate_fig(config_config, df_to_plotly, list_y_columns)

    return fig


def main(config):

    scenario = '/Users/zshi/Library/CloudStorage/Dropbox/CEA2/batch_gh1/_ZRH'
    plot_cea_feature = 'demand'
    hour_start = 0
    hour_end = 8759
    fig = plot_all(config, scenario, plot_cea_feature, hour_start, hour_end)
    fig.show()


if __name__ == '__main__':
    main(cea.config.Configuration())
