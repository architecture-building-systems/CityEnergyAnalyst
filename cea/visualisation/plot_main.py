"""
CEAFrontEnd - Combines everything

"""

import os
import sys
from typing import Any

import pandas as pd

from cea import CEAException
import cea.config
import cea.inputlocator
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


def plot_all(config: cea.config.Configuration, scenario: str, plot_dict: dict, hide_title: bool = False, bool_include_advanced_analytics: bool = False, whatif_names_override: list | None = None):
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
        plots_include = config.sections["plots-include-plants-buildings"]
        plot_config = config.sections[f"plots-{plot_cea_feature_umbrella}"]
    except KeyError as e:
        print(f"KeyError: {e}")
        print(f"Looking for: plots-general and plots-{plot_cea_feature_umbrella}")
        raise CEAException(f"Invalid plot_cea_feature: {plot_cea_feature_umbrella}. Ensure that it exists in default.config.")

    include_entities = list(getattr(plots_include, 'include', ['plants', 'buildings']))

    # Activate a_data_loader
    whatif_names = whatif_names_override if whatif_names_override is not None else getattr(plot_config, 'what_if_name', [])
    df_summary_data, df_architecture_data, plot_instance = plot_input_processor(plot_config, plots_building_filter, scenario, plot_cea_feature,
                                                                                period_start, period_end,
                                                                                solar_panel_types_list, bool_include_advanced_analytics,
                                                                                whatif_names=whatif_names,
                                                                                include_entities=include_entities)
    # Activate b_data_processor
    df_to_plotly, list_y_columns = calc_x_y_metric(plot_config, plot_config_general, plots_building_filter, plot_instance, plot_cea_feature, df_summary_data,
                                                   df_architecture_data,
                                                   solar_panel_types_list, scenario)
    
    # Extract lifecycle year range for title
    lifecycle_year_range = None
    if plot_cea_feature == 'lifecycle-emissions' and whatif_names:
        locator = cea.inputlocator.InputLocator(scenario)
        for wn in whatif_names:
            tl_path = locator.get_emissions_whatif_timeline_file(wn)
            if os.path.exists(tl_path):
                tl_df = pd.read_csv(tl_path, usecols=['period'])
                try:
                    yr_s = int(str(tl_df['period'].iloc[0]).replace('Y_', ''))
                    yr_e = int(str(tl_df['period'].iloc[-1]).replace('Y_', ''))
                    lifecycle_year_range = (yr_s, yr_e)
                except (ValueError, TypeError, IndexError):
                    pass
                break

    # Activate c_plotter
    fig = generate_fig(plot_config, plot_config_general, df_to_plotly, list_y_columns, plot_cea_feature, solar_panel_types_list, hide_title,
                       lifecycle_year_range=lifecycle_year_range)
    
    fig.update_layout(autosize=True)

    return fig


def main(config: cea.config.Configuration):
    scenario = config.scenario
    context: dict[str, Any] = config.plots_general.context
    # When running via CLI, the script identity is known — override any stale feature in context
    plot_cea_feature = None
    try:
        plot_cea_feature = get_plot_cea_feature(config)
        context = {**context, 'feature': plot_cea_feature}
    except CEAException:
        plot_cea_feature = context.get('feature')  # Fall back to feature stored in context

    # Determine config section umbrella (solar features all share 'plots-solar')
    whatif_names = []
    if plot_cea_feature:
        umbrella = 'solar' if plot_cea_feature in ('pv', 'pvt', 'sc') else plot_cea_feature
        try:
            _section = config.sections[f'plots-{umbrella}']
            whatif_names = list(getattr(_section, 'what_if_name', []) or [])
        except (KeyError, AttributeError):
            pass

    # ── Single-figure path (no what-if or only one selected) ─────────────────
    if len(whatif_names) <= 1:
        fig = plot_all(config, scenario, context, hide_title=False)
        fig.update_layout(autosize=True)

        if sys.stdout.isatty():
            fig.show(renderer="browser")

        html = fig.to_html(full_html=True, include_plotlyjs='cdn', config={'responsive': True})
        return html.replace('<head>', '<head><style>html,body{height:100%;margin:0}</style>', 1)

    # ── Multi-figure path: one figure per what-if with aligned y-axis ────────
    # slot: ('ok', whatif_name, fig) or ('err', whatif_name, html_str)
    slots = []
    for whatif_name in whatif_names:
        try:
            fig = plot_all(config, scenario, context, hide_title=False,
                           whatif_names_override=[whatif_name])
            slots.append(('ok', whatif_name, fig))
        except Exception as e:
            slots.append(('err', whatif_name, (
                f'<div style="padding:20px;border:2px solid #ff6b6b;border-radius:5px;'
                f'background:#ffe0e0;margin:12px 0">'
                f'<h3>Error plotting <em>{whatif_name}</em></h3>'
                f'<code>{e}</code></div>'
            )))

    # Compute global y-range from all successful figures when user has not set explicit bounds
    plot_config_general = config.plots_general
    user_y_min = plot_config_general.y_min
    user_y_max = plot_config_general.y_max

    global_y_min = global_y_max = None
    if user_y_min is None and user_y_max is None:
        y_ranges = [
            fig.layout.yaxis.range
            for kind, _, fig in slots
            if kind == 'ok' and fig.layout.yaxis.range
        ]
        if y_ranges:
            global_y_min = min(r[0] for r in y_ranges)
            global_y_max = max(r[1] for r in y_ranges)

    html_outputs = []
    plotly_included = False
    for slot in slots:
        if slot[0] == 'err':
            html_outputs.append(slot[2])
            continue
        _, whatif_name, fig = slot
        if global_y_min is not None:
            fig.update_yaxes(range=[global_y_min, global_y_max])
        fig.update_layout(autosize=True)
        include_js = 'cdn' if not plotly_included else False
        plotly_included = True
        html_outputs.append(fig.to_html(full_html=False, include_plotlyjs=include_js,
                                        config={'responsive': True}))

    body = '\n'.join(html_outputs)
    return (
        '<!DOCTYPE html><html>'
        '<head><meta charset="utf-8"><style>html,body{height:100%;margin:0}</style></head>'
        f'<body>{body}</body></html>'
    )


if __name__ == '__main__':
    main(cea.config.Configuration())
