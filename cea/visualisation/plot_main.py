"""
CEAFrontEnd – Combines everything

"""

import sys
import cea.config
from cea import CEAException
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


def get_plot_cea_feature(config: cea.config.Configuration) -> str:
    """
    Tries to determine the cea feature to plot based on the provided config.
    Currently, only works with the cli interface.

    When running using the cli interface, the config parameters passed to the script are restricted based on the scripts.yml file.
    Using the restricted_to property, we can determine the cea feature to use based on the section name of the parameters.
    e.g. plots-demand for demand plots. There should only be one section of parameters for each cea feature plot.

    When running the script using the main function, the config parameters passed to the script are not restricted.
    In this case, we can't determine the cea feature to use. Therefore, we do not support this mode.
    """
    if config.restricted_to is None:
        raise CEAException("Unable to determine feature to plot. "
                           "This currently only works on the cli interface by calling the relevant plot script directly.")

    sections = {p.split(":")[0] for p in config.restricted_to if p.startswith("plots-")}
    if len(sections) != 1:
        raise CEAException("Unable to determine feature to plot. "
                           "Ensure that only one type of plot config is provided in scripts.yml in the correct format. "
                           "e.g. plots-demand")

    return sections.pop().split("-", 1)[1]


def plot_all(config: cea.config.Configuration, scenario: str, plot_cea_feature: str, hour_start=0, hour_end=8759):
    # Find the plot config section for the cea feature
    try:
        plot_config = config.sections[f"plots-{plot_cea_feature}"]
    except KeyError:
        raise CEAException(f"Invalid plot_cea_feature: {plot_cea_feature}. Ensure that it exists in default.config.")

    # Activate a_data_loader
    df_summary_data, df_architecture_data, plot_instance = plot_input_processor(plot_config, scenario, plot_cea_feature,
                                                                                hour_start, hour_end)

    # Activate b_data_processor
    df_to_plotly, list_y_columns = calc_x_y_metric(plot_config, plot_instance, plot_cea_feature, df_summary_data,
                                                   df_architecture_data)

    # Activate c_plotter
    fig = generate_fig(plot_config, df_to_plotly, list_y_columns)
    return fig


def main(config):
    scenario = config.scenario

    plot_cea_feature = get_plot_cea_feature(config)
    fig = plot_all(config, scenario, plot_cea_feature)

    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    if sys.stdout.isatty():
        fig.show(renderer="browser")
    return plot_html


if __name__ == '__main__':
    main(cea.config.Configuration())
