from __future__ import division

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Bhargava Srepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def cost_analysis_curve_decentralized(data_frame, locator, final_generation, config):
    analysis_fields_cost_decentralized_heating = ["BoilerBG Share", "BoilerNG Share", "FC Share", "GHP Share",
                                                  "Operation Costs [CHF]", "Annualized Investment Costs [CHF]"]

    analysis_fields_cost_decentralized_cooling = ["DX to AHU_ARU_SCU Share", "VCC to AHU_ARU Share",
                                                  "VCC to AHU_ARU_SCU Share",
                                                  "VCC to SCU Share", "single effect ACH to AHU_ARU_SCU Share (ET)",
                                                  "single effect ACH to AHU_ARU_SCU Share (FP)",
                                                  "single effect ACH to SCU Share (FP)",
                                                  "Operation Costs [CHF]", "Annualized Investment Costs [CHF]"]
    for individual in range(len(data_frame.index)):

        title = 'Decentralized Cost Analysis for generation ' + str(final_generation) + ' individual ' + str(individual)
        total_demand = pd.read_csv(locator.get_total_demand())
        building_names = total_demand.Name.values

        if config.plots.network_type == 'DH':

            column_names = ['Disconnected_Capex_Boiler_BG', 'Disconnected_Capex_Boiler_NG', 'Disconnected_Capex_GHP',
                            'Disconnected_Capex_FC', 'Disconnected_Opex_Boiler_BG', 'Disconnected_Opex_Boiler_NG',
                            'Disconnected_Opex_GHP', 'Disconnected_Opex_FC', 'Building Name']

            data_frame_building = pd.DataFrame(np.zeros([len(building_names), len(column_names)]), columns=column_names)
            output_path = locator.get_timeseries_plots_file(
                'gen' + str(final_generation) + ' individual ' + str(individual) + '_decentralized_cost_analysis_split')

            for building_number, building_name in enumerate(building_names):

                analysis_fields_building = []
                for j in range(len(analysis_fields_cost_decentralized_heating)):
                    analysis_fields_building.append(
                        str(building_name) + " " + analysis_fields_cost_decentralized_heating[j])

                data_frame_building['Building Name'][building_number] = building_name
                data_frame_building['Disconnected_Capex_Boiler_BG'][building_number] = \
                data_frame[analysis_fields_building[0]][individual] * data_frame[analysis_fields_building[5]][
                    individual]
                data_frame_building['Disconnected_Capex_Boiler_NG'][building_number] = \
                data_frame[analysis_fields_building[1]][individual] * data_frame[analysis_fields_building[5]][
                    individual]
                data_frame_building['Disconnected_Capex_GHP'][building_number] = \
                data_frame[analysis_fields_building[2]][individual] * data_frame[analysis_fields_building[5]][
                    individual]
                data_frame_building['Disconnected_Capex_FC'][building_number] = data_frame[analysis_fields_building[3]][
                                                                                    individual] * \
                                                                                data_frame[analysis_fields_building[5]][
                                                                                    individual]
                data_frame_building['Disconnected_Opex_Boiler_BG'][building_number] = \
                data_frame[analysis_fields_building[0]][individual] * data_frame[analysis_fields_building[4]][
                    individual]
                data_frame_building['Disconnected_Opex_Boiler_NG'][building_number] = \
                data_frame[analysis_fields_building[1]][individual] * data_frame[analysis_fields_building[4]][
                    individual]
                data_frame_building['Disconnected_Opex_GHP'][building_number] = data_frame[analysis_fields_building[2]][
                                                                                    individual] * \
                                                                                data_frame[analysis_fields_building[4]][
                                                                                    individual]
                data_frame_building['Disconnected_Opex_FC'][building_number] = data_frame[analysis_fields_building[3]][
                                                                                   individual] * \
                                                                               data_frame[analysis_fields_building[4]][
                                                                                   individual]

            # CALCULATE GRAPH
            analysis_fields = ['Disconnected_Capex_Boiler_BG', 'Disconnected_Capex_Boiler_NG', 'Disconnected_Capex_GHP',
                               'Disconnected_Capex_FC', 'Disconnected_Opex_Boiler_BG', 'Disconnected_Opex_Boiler_NG',
                               'Disconnected_Opex_GHP', 'Disconnected_Opex_FC']
            traces_graph = calc_graph(analysis_fields, data_frame_building)

            # CREATE FIRST PAGE WITH TIMESERIES
            layout = go.Layout(images=LOGO, title=title, barmode='relative',
                               yaxis=dict(title='Cost [$ per year]', domain=[0.0, 1.0]))

            fig = go.Figure(data=traces_graph, layout=layout)
            plot(fig, auto_open=False, filename=output_path)

        if config.plots.network_type == 'DC':

            column_names = ['Disconnected_Capex_Direct_Expansion', 'Disconnected_Capex_VCC',
                            'Disconnected_Capex_single_effect_ACH_FP',
                            'Disconnected_Capex_single_effect_ACH_ET', 'Disconnected_Opex_Direct_Expansion',
                            'Disconnected_Opex_VCC',
                            'Disconnected_Opex_single_effect_ACH_FP', 'Disconnected_Opex_single_effect_ACH_ET',
                            'Building Name']

            data_frame_building = pd.DataFrame(np.zeros([len(building_names), len(column_names)]), columns=column_names)
            output_path = locator.get_timeseries_plots_file(
                'gen' + str(final_generation) + ' individual ' + str(individual) + '_decentralized_cost_analysis_split')

            for building_number, building_name in enumerate(building_names):

                analysis_fields_building = []
                for j in range(len(analysis_fields_cost_decentralized_cooling)):
                    analysis_fields_building.append(
                        str(building_name) + " " + analysis_fields_cost_decentralized_cooling[j])

                data_frame_building['Building Name'][building_number] = building_name
                data_frame_building['Disconnected_Capex_Direct_Expansion'][building_number] = \
                data_frame[analysis_fields_building[0]][individual] * data_frame[analysis_fields_building[8]][
                    individual]
                data_frame_building['Disconnected_Capex_VCC'][building_number] = (data_frame[
                                                                                      analysis_fields_building[1]][
                                                                                      individual] + data_frame[
                                                                                      analysis_fields_building[2]][
                                                                                      individual]) * data_frame[
                                                                                     analysis_fields_building[8]][
                                                                                     individual]
                data_frame_building['Disconnected_Capex_single_effect_ACH_FP'][building_number] = (data_frame[
                                                                                                       analysis_fields_building[
                                                                                                           5]][
                                                                                                       individual] +
                                                                                                   data_frame[
                                                                                                       analysis_fields_building[
                                                                                                           6]][
                                                                                                       individual]) * \
                                                                                                  data_frame[
                                                                                                      analysis_fields_building[
                                                                                                          8]][
                                                                                                      individual]
                data_frame_building['Disconnected_Capex_single_effect_ACH_ET'][building_number] = \
                data_frame[analysis_fields_building[3]][individual] * data_frame[analysis_fields_building[8]][
                    individual]
                data_frame_building['Disconnected_Opex_Direct_Expansion'][building_number] = \
                data_frame[analysis_fields_building[0]][individual] * data_frame[analysis_fields_building[7]][
                    individual]
                data_frame_building['Disconnected_Opex_VCC'][building_number] = (data_frame[
                                                                                     analysis_fields_building[1]][
                                                                                     individual] + data_frame[
                                                                                     analysis_fields_building[2]][
                                                                                     individual]) * \
                                                                                data_frame[analysis_fields_building[7]][
                                                                                    individual]
                data_frame_building['Disconnected_Opex_single_effect_ACH_FP'][building_number] = (data_frame[
                                                                                                      analysis_fields_building[
                                                                                                          5]][
                                                                                                      individual] +
                                                                                                  data_frame[
                                                                                                      analysis_fields_building[
                                                                                                          6]][
                                                                                                      individual]) * \
                                                                                                 data_frame[
                                                                                                     analysis_fields_building[
                                                                                                         7]][individual]
                data_frame_building['Disconnected_Opex_single_effect_ACH_ET'][building_number] = \
                data_frame[analysis_fields_building[3]][individual] * data_frame[analysis_fields_building[7]][
                    individual]

            # CALCULATE GRAPH
            analysis_fields = ['Disconnected_Capex_Direct_Expansion', 'Disconnected_Capex_VCC',
                               'Disconnected_Capex_single_effect_ACH_FP',
                               'Disconnected_Capex_single_effect_ACH_ET', 'Disconnected_Opex_Direct_Expansion',
                               'Disconnected_Opex_VCC',
                               'Disconnected_Opex_single_effect_ACH_FP', 'Disconnected_Opex_single_effect_ACH_ET']
            # CALCULATE GRAPH
            traces_graph = calc_graph(analysis_fields, data_frame_building)

            # CREATE FIRST PAGE WITH TIMESERIES
            layout = go.Layout(images=LOGO, title=title, barmode='relative',
                               yaxis=dict(title='Cost [$ per year]', domain=[0.0, 1.0]))

            fig = go.Figure(data=traces_graph, layout=layout)
            plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # main data about technologies
    data = (data_frame)
    graph = []
    for i, field in enumerate(analysis_fields):
        y = data[field].values
        flag_for_unused_technologies = all(v == 0 for v in y)
        if not flag_for_unused_technologies:
            trace = go.Bar(x=data["Building Name"], y=y, name=NAMING[field], marker=dict(color=COLOR[field]))
            graph.append(trace)

    return graph
