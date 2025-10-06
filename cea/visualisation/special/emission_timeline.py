# -*- coding: utf-8 -*-




import math
import os
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objs as go
from plotly.offline import plot

import cea.config
import cea.plots.demand
from cea.visualisation.a_data_loader import plot_input_processor
from cea.visualisation.b_data_processor import calc_x_y_metric
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB
from cea.import_export.result_summary import filter_buildings

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

class EmissionTimelinePlot(df_to_plotly, list_y_columns):
    return plot_obj

def plot_emission_timeline(config, context: dict):
    scenario = config.scenario
    plot_cea_feature = 'lifecycle-emissions'
    period_start = context.get('period_start', 0)
    period_end = context.get('period_end', 8759)
    plot_cea_feature_umbrella = context.get('feature', 'emission-timeline')
    solar_panel_types_list = []
    plot_config_general = config.sections["plots-general"]
    plots_building_filter = config.sections["plots-building-filter"]
    plot_config = config.sections[f"plots-{plot_cea_feature_umbrella}"]
    bool_include_advanced_analytics = False

    # Activate a_data_loader
    df_summary_data, df_architecture_data, plot_instance = plot_input_processor(plot_config, plot_config_general,
                                                                                plots_building_filter, scenario,
                                                                                plot_cea_feature,
                                                                                period_start, period_end,
                                                                                solar_panel_types_list,
                                                                                bool_include_advanced_analytics)
    # Activate b_data_processor
    df_to_plotly, list_y_columns = calc_x_y_metric(plot_config, plot_config_general, plots_building_filter,
                                                   plot_instance, plot_cea_feature, df_summary_data,
                                                   df_architecture_data,
                                                   solar_panel_types_list)

    plot_obj =

    return plot_obj


def create_one_district_plot(building_plots):
    # Generate individual chart data for each building
    charts_data = []
    include_js = True
    for plot_obj in building_plots:
        print(f"\n=== Building {plot_obj.building} ===")
        # Check if dict_graph is unique per building
        dict_graph = plot_obj.dict_graph
        print(f"Winter occupied points: {len(dict_graph['t_op_occupied_winter'])}")
        print(f"Summer occupied points: {len(dict_graph['t_op_occupied_summer'])}")
        if len(dict_graph['t_op_occupied_winter']) > 0:
            print(
                f"Winter temp range: {min(dict_graph['t_op_occupied_winter']):.2f} - {max(dict_graph['t_op_occupied_winter']):.2f}")
        if len(dict_graph['t_op_occupied_summer']) > 0:
            print(
                f"Summer temp range: {min(dict_graph['t_op_occupied_summer']):.2f} - {max(dict_graph['t_op_occupied_summer']):.2f}")

        # Get traces and layout for this building
        traces = plot_obj.calc_graph()
        layout = create_layout("")

        # Create figure
        fig = go.Figure(data=traces, layout=layout)

        # Apply styling
        fig['layout'].update(dict(
            hovermode='closest',
            width=500,
            height=500,
            plot_bgcolor='#F7F7F7',
            paper_bgcolor='rgba(0,0,0,0)',
            title=None
        ))
        fig['layout']['yaxis'].update(dict(hoverformat=".2f"))
        fig['layout']['margin'].update(dict(l=0, r=0, t=50, b=50))
        fig['layout']['font'].update(dict(size=10))

        # Make legend background transparent
        fig['layout']['legend'].update(dict(
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)'
        ))

        # Generate chart HTML and table
        import plotly.offline as pyo
        js_opt = 'cdn' if include_js else False
        chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=js_opt)
        include_js = False
        table_html = plot_obj.create_academic_table()

        charts_data.append({
            'building': plot_obj.building,
            'chart_html': chart_html,
            'table_html': table_html
        })

    # Create combined HTML layout - use the correct scenario path from the first plot object
    output_path = building_plots[0].output_path.replace(f"Building_{building_plots[0].building}_comfort-chart.html",
                                                        "comfort-chart.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate charts HTML with horizontal layout
    charts_html = ""
    for i, chart_data in enumerate(charts_data):
        margin_left = "100px" if i > 0 else "0px"
        charts_html += f"""
        <div style="display: inline-block; vertical-align: top; margin-left: {margin_left};">
            <h2 style="text-align: left; color: #333; font-size: 18px; margin-bottom: 1px; margin-left: 5px;">
                Building {chart_data['building']}
            </h2>
            <div style="background-color: transparent; padding: 0; margin-bottom: 20px; width: 300px;">
                {chart_data['chart_html']}
            </div>
            <div style="background-color: transparent; padding: 0; width: 300px;">
                {chart_data['table_html']}
            </div>
        </div>
        """

    # Complete HTML document with improved layout
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Comfort Chart(s)</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                margin: 14px;
                background-color: white;
                min-width: fit-content;
            }}
            .container {{
                width: 100vw;
                overflow-x: auto;
                min-width: 1200px;
            }}
            .charts-wrapper {{
                display: flex;
                flex-direction: row;
                gap: 100px;
                width: max-content;
            }}
            .chart-item {{
                display: flex;
                flex-direction: column;
                width: 500px;
                flex-shrink: 0;
            }}
            h1 {{
                text-align: left;
                color: #333;
                font-size: 20px;
                margin-bottom: 5px;
                margin-left: 0px;
            }}
            h2 {{
                color: #333;
                font-size: 18px;
                margin-bottom: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Comfort Chart - Multiple Buildings ({len(charts_data)} buildings)</h1>
            <div class="charts-wrapper">
    """

    for chart_data in charts_data:
        full_html += f"""
                <div class="chart-item">
                    <h2>- Building {chart_data['building']}</h2>
                    <div style="background-color: transparent; padding: 0; margin-bottom: 20px;">
                        {chart_data['chart_html']}
                    </div>
                    <div style="background-color: transparent; padding: 0;">
                        {chart_data['table_html']}
                    </div>
                </div>
        """

    full_html += """
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, 'w') as f:
        f.write(full_html)

    print(f"Plotted multi-building comfort chart to {output_path}")
    import webbrowser
    webbrowser.open(output_path)

    return full_html


def main(config):
    import cea.inputlocator

    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()


    list_buildings = config.plots_general.buildings
    integer_year_start = config.plots_building_filter.filter_buildings_by_year_start
    integer_year_end = config.plots_building_filter.filter_buildings_by_year_end
    list_standard = config.plots_building_filter.filter_buildings_by_construction_type
    list_main_use_type = config.plots_building_filter.filter_buildings_by_use_type
    ratio_main_use_type = config.plots_building_filter.min_ratio_as_main_use
    _, list_buildings = filter_buildings(locator, list_buildings,
                                         integer_year_start, integer_year_end, list_standard,
                                         list_main_use_type, ratio_main_use_type)

    print(f"Filtered buildings list: {list_buildings}")
    print(f"Number of buildings: {len(list_buildings)}")


    context = {'feature': 'emission-timeline', 'period_end': 2035, 'period_start': 2060, 'solar_panel_types': {}}

    # Generate comfort charts for all buildings
    plot_obj = plot_emission_timeline(config, context)


    # Create multi-building plot
    plot_html = create_one_district_plot(plot_obj)

    return plot_html


if __name__ == '__main__':
    main(cea.config.Configuration())
