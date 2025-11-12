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
from cea.visualisation.format.plot_colours import COLOURS_TO_RGB
from cea.import_export.result_summary import filter_buildings

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

# constants
# vertices of PMV comfort zones visually extracted from graph:
# [https://www.researchgate.net/figure/Psychrometric-chart-with-superimposed-comfort-zones-for-05-and-10-clo-summer-and_fig2_261566668]
VERTICES_WINTER_COMFORT = [(21.5, 0.0), (26.5, 0.0), (24.0, 12.0), (19.5, 12.0)]  # (T, moisture ratio)
VERTICES_SUMMER_COMFORT = [(25.0, 0.0), (28.25, 0.0), (26.75, 12.0), (24.0, 12.0)]  # (T, moisture ratio)

# layout of graph and table
YAXIS_DOMAIN_GRAPH = [0, 1]
XAXIS_DOMAIN_GRAPH = [0, 1]


class ComfortChartPlot(cea.plots.demand.DemandSingleBuildingPlotBase):
    name = "Comfort Chart"
    
    expected_parameters = dict(cea.plots.demand.DemandSingleBuildingPlotBase.expected_parameters)

    def __init__(self, project, parameters, cache):
        super(ComfortChartPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = None

    @property
    def layout(self):
        return create_layout(self.title)

    @property
    def data(self):
        return self.hourly_loads

    @property
    def dict_graph(self):
        if not hasattr(self, '_dict_graph'):
            self._dict_graph = calc_data(self.building, self.data, self.locator)
        return self._dict_graph

    def calc_graph(self):
        # calculate points of comfort in different conditions

        # create lines of constant relative humidity first (as background)
        traces_graph = create_relative_humidity_lines()
        
        # create scatter of comfort on top
        traces_comfort = calc_graph(self.dict_graph)
        traces_graph.extend(traces_comfort)

        # add text for winter / summer comfort zones
        trace_layout = go.Scatter(
            x=[23, 26.5],
            y=[2, 3],
            text=['Comfort zone: heating season',
                  'Comfort zone: cooling season'],
            mode='text',
            showlegend=False
        )
        traces_graph.append(trace_layout)
        return traces_graph

    def _plot_data_producer(self):
        """Override to bypass caching and ensure traces are returned correctly"""
        traces = self.calc_graph()
        # DON'T add the table here - let's see if that's what's breaking it
        return traces
        
    def plot(self, auto_open=False):
        """Use direct Plotly to ensure curves work, with table and proper styling"""
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # Get all the traces directly (this works and shows curves)
        traces = self.calc_graph()
        
        # Create the layout with styling (no title in chart)
        layout = create_layout("")
        
        # Create figure with direct Plotly (this ensures curves show)
        import plotly.graph_objs as go
        
        fig = go.Figure(data=traces, layout=layout)
        
        # Apply CEA styling manually with narrower width
        fig['layout'].update(dict(
            hovermode='closest',
            width=500,
            height=500,
            plot_bgcolor='#F7F7F7',  # Set chart background to light gray
            paper_bgcolor='rgba(0,0,0,0)',  # Make outer background transparent
            title=None  # Remove plotly chart title
        ))
        fig['layout']['yaxis'].update(dict(hoverformat=".2f"))  
        fig['layout']['margin'].update(dict(l=0, r=0, t=50, b=50))
        fig['layout']['font'].update(dict(size=10))
        
        # Make legend background transparent
        fig['layout']['legend'].update(dict(
            bgcolor='rgba(0,0,0,0)',  # Transparent background
            bordercolor='rgba(0,0,0,0)'  # Transparent border
        ))
        
        # Generate the chart HTML
        import plotly.offline as pyo
        chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=True)
        
        # Generate the academic-style table HTML
        table_html = self.create_academic_table()
        
        # Combine chart and table in a clean layout
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{self.title}</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    margin: 14px;
                    background-color: white;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0;
                }}
                .chart-container {{
                    background-color: transparent;
                    padding: 0;
                    margin-bottom: 20px;
                    width: 500px;
                }}
                .table-container {{
                    background-color: transparent;
                    padding: 0;
                    width: 500px;
                }}
                h1 {{
                    text-align: left;
                    color: #333;
                    font-size: 20px;
                    margin-bottom: 0px;
                    margin-left: 0px
                }}
                h2 {{
                    color: #333;
                    margin-bottom: 0px;
                    display: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{self.title}</h1>
                <div class="chart-container">
                    {chart_html}
                </div>
                <div class="table-container">
                    {table_html}
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(self.output_path, 'w') as f:
            f.write(full_html)
        
        print("Plotted '%s' to %s" % (self.name, self.output_path))
        if auto_open:
            import webbrowser
            webbrowser.open(self.output_path)

    def create_academic_table(self):
        """Create academic-style HTML table with proper formatting"""
        
        # Get table data
        table_data = self.calc_table()
        
        # Create academic-style HTML table
        table_html = """
        <style>
            .academic-table {
                width: 470px;
                margin-left: 0px;
                border-collapse: collapse;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                margin-top: 20px;
                margin-bottom: 20px;
            }
            .academic-table th {
                background-color: white;
                font-weight: bold;
                padding: 1px 0px;
                text-align: left;
                border-top: 2px solid #333;
                border-bottom: 1px solid #333;
            }
            .academic-table td {
                padding: 1px 0px;
                text-align: left;
                border: none;
            }
            .academic-table td:nth-child(2),
            .academic-table td:nth-child(3) {
                text-align: right;
            }
            .academic-table tr:last-child td {
                border-bottom: 2px solid #333;
            }
            .academic-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
        <table class="academic-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Comfort [h]</th>
                    <th>Discomfort [h]</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Add data rows
        conditions = table_data['Occupied hours'].tolist()
        comfort_hours = table_data['Comfort [h]'].tolist()
        uncomfort_hours = table_data['Uncomfort [h]'].tolist()
        
        for i in range(len(conditions)):
            table_html += f"""
                <tr>
                    <td>{conditions[i].title()}</td>
                    <td>{comfort_hours[i]}</td>
                    <td>{uncomfort_hours[i]}</td>
                </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        
        return table_html

    def calc_table(self):
        """
        draws table of monthly energy balance
        """

        # create table arrays
        # check winter comfort
        count_winter_comfort, count_winter_uncomfort = check_comfort(self.dict_graph['t_op_occupied_winter'],
                                                                     self.dict_graph['x_int_occupied_winter'],
                                                                     VERTICES_WINTER_COMFORT)
        winter_hours = len(self.dict_graph['t_op_occupied_winter'])
        perc_winter_comfort = count_winter_comfort / winter_hours if winter_hours > 0 else 0
        cell_winter_comfort = "{} ({:.0%})".format(count_winter_comfort, perc_winter_comfort)
        perc_winter_uncomfort = count_winter_uncomfort / winter_hours if winter_hours > 0 else 0
        cell_winter_uncomfort = "{} ({:.0%})".format(count_winter_uncomfort, perc_winter_uncomfort)

        # check summer comfort
        count_summer_comfort, count_summer_uncomfort = check_comfort(self.dict_graph['t_op_occupied_summer'],
                                                                     self.dict_graph['x_int_occupied_summer'],
                                                                     VERTICES_SUMMER_COMFORT)
        summer_hours = len(self.dict_graph['t_op_occupied_summer'])
        perc_summer_comfort = count_summer_comfort / summer_hours if summer_hours > 0 else 0
        cell_summer_comfort = "{} ({:.0%})".format(count_summer_comfort, perc_summer_comfort)
        perc_summer_uncomfort = count_summer_uncomfort / summer_hours if summer_hours > 0 else 0
        cell_summer_uncomfort = "{} ({:.0%})".format(count_summer_uncomfort, perc_summer_uncomfort)

        # draw table
        column_names = ['Occupied hours', 'Comfort [h]', 'Uncomfort [h]']
        column_data = [['Cooling season - occupied', 'Heating season - occupied'],
                       [cell_summer_comfort, cell_winter_comfort],
                      [cell_summer_uncomfort, cell_winter_uncomfort]]
        table_df = pd.DataFrame({cn: cd for cn, cd in zip(column_names, column_data)}, columns=column_names)
        return table_df


def comfort_chart(building_name, data_frame, title, output_path, config, locator):
    """
    Main function of comfort chart plot

    :param data_frame: results from demand calculation
    :type data_frame: pandas.DataFrame
    :param title: title of plot
    :type title: string
    :param output_path: path to output folder
    :type output_path: system path
    :return:
    """

    # calculate points of comfort in different conditions
    dict_graph = calc_data(building_name, data_frame, locator)

    # create scatter of comfort
    traces_graph = calc_graph(dict_graph)

    # create lines of constant relative humidity
    traces_relative_humidity = create_relative_humidity_lines()
    traces_graph.extend(traces_relative_humidity)

    # create layout
    layout = create_layout(title)

    # create table
    traces_table = calc_table(dict_graph)
    # add table in first place of traces
    traces_graph.insert(0, traces_table)

    # create figure
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': [traces_graph], 'layout': layout}


def create_layout(title):
    """
    Creates layout of plot, including polygon comfort areas

    :param title: title of plot
    :type title: string
    :return: trace_layout, layout
    :rtype: plotly.graph_objs.trace, plotly.graph_objs.layout
    """

    layout = {
        'title': title,
        'xaxis': {
            'title': 'Operative Temperature [°C]',
            'range': [5, 49],
            'domain': XAXIS_DOMAIN_GRAPH,
            'dtick': 5  # Set tick interval to 5°C
        },
        'yaxis': {
            'title': 'Moisture content [g/kg dry air]',
            'side': 'right',
            'range': [0, 44],
            'domain': YAXIS_DOMAIN_GRAPH,
            'showgrid': True,
        },
        'legend': {
            'x': XAXIS_DOMAIN_GRAPH[0],
            'y': YAXIS_DOMAIN_GRAPH[1] - 0.05,
        },
        'shapes': [
            # Winter comfort zone
            {
                'type': 'path',
                'path': ' M {},{} L{},{} L{},{} L{},{} Z'.format(VERTICES_WINTER_COMFORT[0][0],
                                                                 VERTICES_WINTER_COMFORT[0][1],
                                                                 VERTICES_WINTER_COMFORT[1][0],
                                                                 VERTICES_WINTER_COMFORT[1][1],
                                                                 VERTICES_WINTER_COMFORT[2][0],
                                                                 VERTICES_WINTER_COMFORT[2][1],
                                                                 VERTICES_WINTER_COMFORT[3][0],
                                                                 VERTICES_WINTER_COMFORT[3][1]),
                'fillcolor': COLOURS_TO_RGB['blue'],
                'opacity': 0.2,
                'line': {
                    'color': COLOURS_TO_RGB['blue'],
                },
            },
            # Summer comfort zone
            {
                'type': 'path',
                'path': ' M {},{} L{},{} L{},{} L{},{} Z'.format(VERTICES_SUMMER_COMFORT[0][0],
                                                                 VERTICES_SUMMER_COMFORT[0][1],
                                                                 VERTICES_SUMMER_COMFORT[1][0],
                                                                 VERTICES_SUMMER_COMFORT[1][1],
                                                                 VERTICES_SUMMER_COMFORT[2][0],
                                                                 VERTICES_SUMMER_COMFORT[2][1],
                                                                 VERTICES_SUMMER_COMFORT[3][0],
                                                                 VERTICES_SUMMER_COMFORT[3][1]),
                'fillcolor': COLOURS_TO_RGB['red'],
                'opacity': 0.2,
                'line': {
                    'color': COLOURS_TO_RGB['red'],
                },
            },

        ]
    }

    return layout


def calc_graph(dict_graph):
    """
    creates scatter of comfort and curves of constant relative humidity

    :param dict_graph: contains comfort conditions to plot, output of comfort_chart.calc_data()
    :type dict_graph: dict
    :return: traces of scatter plot of 4 comfort conditions
    :rtype: list of plotly.graph_objs.Scatter
    """

    traces = []

    # draw scatter of comfort conditions in building
    trace = go.Scatter(x=dict_graph['t_op_occupied_winter'], y=dict_graph['x_int_occupied_winter'],
                       name='Heating season - occupied hours', mode='markers',
                       marker=dict(color=COLOURS_TO_RGB['red'], size=6, opacity=0.7))
    traces.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_unoccupied_winter'], y=dict_graph['x_int_unoccupied_winter'],
                       name='Heating season - unoccupied hours', mode='markers',
                       marker=dict(color=COLOURS_TO_RGB['blue'], size=4, opacity=0.7))
    traces.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_occupied_summer'], y=dict_graph['x_int_occupied_summer'],
                       name='Cooling season - occupied hours', mode='markers',
                       marker=dict(color=COLOURS_TO_RGB['purple'], size=6, opacity=0.7))
    traces.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_unoccupied_summer'], y=dict_graph['x_int_unoccupied_summer'],
                       name='Cooling season - unoccupied hours', mode='markers',
                       marker=dict(color=COLOURS_TO_RGB['orange'], size=4, opacity=0.7))
    traces.append(trace)

    return traces


def create_relative_humidity_lines():
    """
    calculates curves of constant relative humidity for plotting (10% - 100% in steps of 10%)

    :return: list of plotly table trace
    :rtype: list of plotly.graph_objs.Scatter
    """

    traces = []

    # draw lines of constant relative humidity for psychrometric chart
    rh_lines = np.linspace(0.1, 1, 10)  # lines from 10% to 100%
    t_axis = np.linspace(5, 49, 50)  # match x-axis range
    P_ATM = 101325  # Pa, standard atmospheric pressure at sea level

    for rh_line in rh_lines:

        y_data = calc_constant_rh_curve(t_axis, rh_line, P_ATM)
        trace = go.Scatter(x=t_axis, y=y_data, mode='lines', name="{:.0%} relative humidity".format(rh_line),
                           line=dict(color='rgba(150,150,150,0.5)', width=1), showlegend=False,
                           xaxis='x', yaxis='y', hoverinfo='skip')
        traces.append(trace)

    return traces


def calc_data(building_name, data_frame, locator):
    """
    split up operative temperature and humidity points into 4 categories for plotting
    (1) occupied in heating season
    (2) un-occupied in heating season
    (3) occupied in cooling season
    (4) un-occupied in cooling season

    :param data_frame: results from demand calculation
    :type data_frame: pandas.DataFrame
    :return: dict of lists with operative temperatures and moistures
     \for 4 conditions (summer (un)occupied, winter (un)occupied)
    :rtype: dict
    """
    from cea.demand.building_properties.building_hvac import verify_has_season

    # read region-specific control parameters (identical for all buildings), i.e. heating and cooling season
    hvac_path = locator.get_building_air_conditioning()
    try:
        air_con_data = pd.read_csv(hvac_path).set_index('name')
    except FileNotFoundError as e:
        raise FileNotFoundError(f"HVAC configuration not found at {hvac_path}") from e
    
    if building_name not in air_con_data.index:
        raise ValueError(f"Building '{building_name}' not found in HVAC configuration at {hvac_path}")

    building_air_con_data = air_con_data.loc[building_name]
    has_winter = verify_has_season(building_name,
                                   building_air_con_data.loc['hvac_heat_starts'],
                                   building_air_con_data.loc['hvac_heat_ends'])
    has_summer = verify_has_season(building_name,
                                   building_air_con_data.loc['hvac_cool_starts'],
                                   building_air_con_data.loc['hvac_cool_ends'])

    winter_start = building_air_con_data.loc['hvac_heat_starts']
    winter_end = building_air_con_data.loc['hvac_heat_ends']
    summer_start = building_air_con_data.loc['hvac_cool_starts']
    summer_end =  building_air_con_data.loc['hvac_cool_ends']

    # split up operative temperature and humidity points into 4 categories
    # (1) occupied in heating season
    # (2) un-occupied in heating season
    # (3) occupied in cooling season
    # (4) un-occupied in cooling season

    t_op_occupied_summer = []
    x_int_occupied_summer = []
    t_op_unoccupied_summer = []
    x_int_unoccupied_summer = []
    t_op_occupied_winter = []
    x_int_occupied_winter = []
    t_op_unoccupied_winter = []
    x_int_unoccupied_winter = []

    # convert index from string to datetime (because someone changed the type)
    data_frame.index = pd.to_datetime(data_frame.index)

    # find indexes of the 4 categories
    for index, row in data_frame.iterrows():

        # occupied in winter
        if row['people'] > 0 and has_winter and datetime_in_season(index, winter_start, winter_end):
            t_op_occupied_winter.append(row['theta_o_C'])
            x_int_occupied_winter.append(row['x_int'])
        # unoccupied in winter
        elif row['people'] == 0 and has_winter and datetime_in_season(index, winter_start, winter_end):
            t_op_unoccupied_winter.append(row['theta_o_C'])
            x_int_unoccupied_winter.append(row['x_int'])
        # occupied in summer
        elif row['people'] > 0 and has_summer and datetime_in_season(index, summer_start, summer_end):
            t_op_occupied_summer.append(row['theta_o_C'])
            x_int_occupied_summer.append(row['x_int'])
        # unoccupied in summer
        elif row['people'] == 0 and has_summer and datetime_in_season(index, summer_start, summer_end):
            t_op_unoccupied_summer.append(row['theta_o_C'])
            x_int_unoccupied_summer.append(row['x_int'])

    return {'t_op_occupied_winter': t_op_occupied_winter, 'x_int_occupied_winter': x_int_occupied_winter,
            't_op_unoccupied_winter': t_op_unoccupied_winter, 'x_int_unoccupied_winter': x_int_unoccupied_winter,
            't_op_occupied_summer': t_op_occupied_summer, 'x_int_occupied_summer': x_int_occupied_summer,
            't_op_unoccupied_summer': t_op_unoccupied_summer, 'x_int_unoccupied_summer': x_int_unoccupied_summer}


def calc_table(dict_graph):
    """
    draws table of monthly energy balance

    :param dict_graph: dict containing the lists of summer, winter, occupied and unoccupied operative temperatures and
     moisture ratios, i.e. the results of comfort_chart.calc_data
    :type dict_graph: dict
    :return: plotly table trace
    :rtype: plotly.graph_objs.Table
    """

    # create table arrays
    # check winter comfort
    count_winter_comfort, count_winter_uncomfort = check_comfort(dict_graph['t_op_occupied_winter'],
                                                                 dict_graph['x_int_occupied_winter'],
                                                                 VERTICES_WINTER_COMFORT)
    winter_hours = len(dict_graph['t_op_occupied_winter'])
    perc_winter_comfort = count_winter_comfort/winter_hours if winter_hours > 0 else 0
    cell_winter_comfort = "{} ({:.0%})".format(count_winter_comfort, perc_winter_comfort)
    perc_winter_uncomfort = count_winter_uncomfort / winter_hours if winter_hours > 0 else 0
    cell_winter_uncomfort = "{} ({:.0%})".format(count_winter_uncomfort, perc_winter_uncomfort)

    # check summer comfort
    count_summer_comfort, count_summer_uncomfort = check_comfort(dict_graph['t_op_occupied_summer'],
                                                                 dict_graph['x_int_occupied_summer'],
                                                                 VERTICES_SUMMER_COMFORT)
    summer_hours = len(dict_graph['t_op_occupied_summer'])
    perc_summer_comfort = count_summer_comfort / summer_hours if summer_hours > 0 else 0
    cell_summer_comfort = "{} ({:.0%})".format(count_summer_comfort, perc_summer_comfort)
    perc_summer_uncomfort = count_summer_uncomfort / summer_hours if summer_hours > 0 else 0
    cell_summer_uncomfort = "{} ({:.0%})".format(count_summer_uncomfort, perc_summer_uncomfort)

    # draw table
    table = go.Table(domain=dict(x=[0.0, 1], y=[YAXIS_DOMAIN_GRAPH[1], 1.0]),
                     header=dict(values=['Occupied hours', 'Comfort [h]', 'Uncomfort [h]']),
                     cells=dict(values=[['Cooling season', 'Heating season'],
                                        [cell_summer_comfort, cell_winter_comfort],
                                        [cell_summer_uncomfort, cell_winter_uncomfort]]),
                     visible=True)

    return table


def check_comfort(temperature, moisture, vertices_comfort_area):
    """
    checks if a point of operative temperature and moisture ratio is inside the polygon of comfort defined by its
     vertices, the function only works if the polygon has constant moisture ratio edges

    :param temperature: operative temperature [°C]
    :type temperature: list
    :param moisture: moisture ratio [g/kg dry air]
    :type moisture: list
    :param vertices_comfort_area: vertices of operative temperature and moisture ratio ([°C],[g/kg dry air])
    :type vertices_comfort_area: list of tuples
    :return: hours of comfort, hours of uncomfort
    :rtype: double, double
    """
    # check winter comfort
    # equation for lower temp boundary in winter t = m*x + b
    b_low = vertices_comfort_area[0][0]
    m_low = (vertices_comfort_area[3][0] - b_low) / (vertices_comfort_area[3][1] - vertices_comfort_area[0][1])
    b_high = vertices_comfort_area[1][0]
    m_high = (vertices_comfort_area[2][0] - b_high) / (vertices_comfort_area[2][1] - vertices_comfort_area[1][1])

    count_winter_comfort = 0
    for t, x in zip(temperature, moisture):

        if vertices_comfort_area[0][1] <= x <= vertices_comfort_area[2][1]:

            if m_low * x + b_low <= t <= m_high * x + b_high:
                count_winter_comfort = count_winter_comfort + 1
            else:
                pass
        else:
            pass

    count_winter_uncomfort = len(temperature) - count_winter_comfort

    return count_winter_comfort, count_winter_uncomfort


def datetime_in_season(dt, season_start, season_end):
    """
    small function to determine if a datetime index of the results dataframe is in heating season (winter)
     or cooling season (summer)

    :param dt: datetime, index of resulting csv of cea.demand_main
    :type dt: datetime.datetime
    :param season_start: start of season ["DD|MM"]
    :type season_start: string
    :param season_end: end of season ["DD|MM"]
    :type season_end: string
    :return: True or False
    :rtype: bool
    """

    day_start, month_start = map(int, season_start.split('|'))
    season_start_dt = datetime.datetime(dt.year, month_start, day_start, 0)
    day_end , month_end = map(int, season_end.split('|'))
    season_end_dt = datetime.datetime(dt.year, month_end, day_end, 23)

    if season_start_dt < season_end_dt:

        if season_start_dt <= dt <= season_end_dt:
            return True
        else:
            return False

    elif season_start_dt > season_end_dt:
        if dt <= season_end_dt or dt >= season_start_dt:
            return True
        else:
            return False


def p_ws_from_t(t_celsius):
    """
    Calculate water vapor saturation pressure over liquid water for the temperature range of 0 to 200°C
    Eq (6) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"

    :param t_celsius: temperature [°C]
    :type t_celsius: double
    :return: water vapor saturation pressure [Pa]
    :rtype: double
    """

    # convert temperature
    t = t_celsius + 273.15

    # constants
    C8 = -5.8002206E+03
    C9 = 1.3914993E+00
    C10 = -4.8640239E-02
    C11 = 4.1764768E-05
    C12 = -1.4452093E-08
    C13 = 6.5459673E+00

    return math.exp(C8/t+C9+C10*t+C11*t**2+C12*t**3+C13*math.log(t))


def p_w_from_rh_p_and_ws(rh, p_ws):
    """
    Calculate water vapor pressure from relative humidity and water vapor saturation pressure
    Eq(6) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"

    :param rh: relative humidity [-]
    :type rh: double
    :param p_ws: water vapor saturation pressure [Pa]
    :type p_ws: double
    :return: water vapor pressure [Pa]
    :rtype: double
    """

    return rh * p_ws


def hum_ratio_from_p_w_and_p(p_w, p):
    """
    Calculate humidity ratio from water vapor pressure and atmospheric pressure
    Eq(22) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"

    :param p_w: water vapor pressure [Pa]
    :type p_w: double
    :param p: atmospheric pressure [Pa]
    :type p: double
    :return: humidity ratio [g / kg dry air]
    :rtype: double
    """

    return 0.62198 * p_w/(p-p_w)


def calc_constant_rh_curve(t_array, rh, p):
    """
    Calculates curves of humidity ratio at different temperatures for a constant relative humidity and pressure

    :param t_array: array pf temperatures [°C]
    :type t_array: numpy.array
    :param rh: relative humidity [-]
    :type rh: double
    :param p: atmospheric pressure [Pa]
    :type p: double
    :return: humidity ratio [g / kg dry air]
    :rtype: numpy.array
    """

    p_ws = np.vectorize(p_ws_from_t)(t_array)
    p_w = p_w_from_rh_p_and_ws(rh, p_ws)

    return hum_ratio_from_p_w_and_p(p_w, p) * 1000

def create_multi_building_plot(building_plots):
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
            print(f"Winter temp range: {min(dict_graph['t_op_occupied_winter']):.2f} - {max(dict_graph['t_op_occupied_winter']):.2f}")
        if len(dict_graph['t_op_occupied_summer']) > 0:
            print(f"Summer temp range: {min(dict_graph['t_op_occupied_summer']):.2f} - {max(dict_graph['t_op_occupied_summer']):.2f}")
        
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
    output_path = building_plots[0].output_path.replace(f"Building_{building_plots[0].building}_comfort-chart.html", "comfort-chart.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
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
                flex-wrap: wrap;
                gap: 100px;
                width: 100%;
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


def main(config: cea.config.Configuration):
    import cea.inputlocator

    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()

    list_buildings = config.plots_building_filter.buildings
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

    # Generate comfort charts for all buildings
    building_plots = []
    for building in list_buildings:
        plot_obj = ComfortChartPlot(config.project, {'building': building,
                                                    'scenario-name': config.scenario_name},
                                   cache)
        building_plots.append(plot_obj)
    
    # Create multi-building plot
    plot_html = create_multi_building_plot(building_plots)

    return plot_html


if __name__ == '__main__':
    main(cea.config.Configuration())
