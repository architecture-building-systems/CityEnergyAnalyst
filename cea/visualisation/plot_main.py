"""
CEAFrontEnd - Combines everything

"""

import sys
from typing import Any


from cea import CEAException
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
                           "If you are running the script using the main function, please specify the feature in the config using the context parameter. "
                           "e.g. {\"feature\": \"demand\"}")

    sections = {p.split(":")[0] for p in config.restricted_to if p.startswith("plots-")}
    # Ignore the plots-general section
    sections.discard("plots-general")
    if len(sections) != 1:
        raise CEAException("Unable to determine feature to plot. "
                           "Ensure that only one type of plot config is provided in scripts.yml in the correct format. "
                           "e.g. plots-demand")

    return sections.pop().split("-", 1)[1]


def plot_all(config: cea.config.Configuration, scenario: str, plot_dict: dict, hide_title: bool = False, bool_include_advanced_analytics: bool = False):
    # Extract parameters from dictionary
    plot_cea_feature: str | None = plot_dict.get('feature')
    # If feature is not found, figure out based on config
    if plot_cea_feature is None:
        raise CEAException("Unable to determine feature to plot. Please specify the feature in the config using the context parameter. "
                           "e.g. {\"feature\": \"demand\"}")
    
    period_start = plot_dict.get('period_start', 0)
    period_end = plot_dict.get('period_end', 8759)

    print(f"Using context: {plot_dict}")
    
    if plot_cea_feature in ('pv', 'pvt', 'sc'):
        solar_panel_types_dict = plot_dict.get('solar_panel_types', {})

        plot_cea_feature_umbrella = 'solar'
        if plot_cea_feature == 'pvt':
            # PVT requires both SC and PV panel types
            if 'sc' not in solar_panel_types_dict or 'pv' not in solar_panel_types_dict:
                raise CEAException(
                    f"PVT requires both 'sc' and 'pv' panel types in solar_panel_types. "
                    f"Got: {solar_panel_types_dict}"
                )
            solar_panel_types_list = [solar_panel_types_dict['sc'], solar_panel_types_dict['pv']]
        else:
            # PV or SC requires only one panel type
            if plot_cea_feature not in solar_panel_types_dict:
                raise CEAException(
                    f"Missing '{plot_cea_feature}' panel type in solar_panel_types. "
                    f"Got: {solar_panel_types_dict}"
                )
            solar_panel_types_list = [solar_panel_types_dict[plot_cea_feature]]

    elif plot_cea_feature in ('lifecycle-emissions', 'operational-emissions'):
        plot_cea_feature_umbrella = plot_cea_feature
        solar_panel_types_list = []
    else:
        plot_cea_feature_umbrella = plot_cea_feature
        solar_panel_types_list = []

    # Find the plot config section for the cea feature
    try:
        plot_config_general = config.sections["plots-general"]
        plots_building_filter = config.sections["plots-building-filter"]
        plot_config = config.sections[f"plots-{plot_cea_feature_umbrella}"]
    except KeyError as e:
        print(f"KeyError: {e}")
        print(f"Looking for: plots-general and plots-{plot_cea_feature_umbrella}")
        raise CEAException(f"Invalid plot_cea_feature: {plot_cea_feature_umbrella}. Ensure that it exists in default.config.")

    # Activate a_data_loader
    df_summary_data, df_architecture_data, plot_instance = plot_input_processor(plot_config, plots_building_filter, scenario, plot_cea_feature,
                                                                                period_start, period_end,
                                                                                solar_panel_types_list, bool_include_advanced_analytics)
    # Activate b_data_processor
    df_to_plotly, list_y_columns = calc_x_y_metric(plot_config, plot_config_general, plots_building_filter, plot_instance, plot_cea_feature, df_summary_data,
                                                   df_architecture_data,
                                                   solar_panel_types_list)
    
    # Activate c_plotter
    fig = generate_fig(plot_config, plot_config_general, df_to_plotly, list_y_columns, plot_cea_feature, solar_panel_types_list, hide_title)
    
    # Use 16:9 landscape aspect ratio for professional presentation
    plot_width = 1600
    plot_height = int(plot_width / 16 * 7)  # 16:9 aspect ratio = 900px height
    
    fig.update_layout(width=plot_width, height=plot_height)
    
    return fig


def main(config: cea.config.Configuration):
    scenario = config.scenario
    context: dict[str, Any] = config.plots_general.context
    fig = plot_all(config, scenario, context, hide_title=False)
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    if sys.stdout.isatty():
        fig.show(renderer="browser")
    return plot_html


if __name__ == '__main__':
    main(cea.config.Configuration())
