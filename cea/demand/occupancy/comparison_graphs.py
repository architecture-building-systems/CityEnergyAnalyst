import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import plot

path_to_scenarios = r'C:\Users\User\Downloads\reference-case-ETH-Mahshid'
scenarios = ['0_archetypes', '1_visual', '2_manual_calibration_orig', '2_manual_calibration', '3_hybrid']
measurement_filename = 'Total_demand_metering_summarized_v5.xls'
# columns_to_plot = ['QH_sys_MWhyr', 'Qhs_sys_MWhyr', 'Qww_sys_MWhyr', 'Qhpro_sys_MWhyr',
#                    'QC_sys_MWhyr', 'Qcs_sys_MWhyr', 'Qcre_sys_MWhyr', 'Qcpro_sys_MWhyr', 'Qcdata_MWhyr',
#                    'E_sys_MWhyr', 'Eal_sys_MWhyr', 'Epro_sys_MWhyr']
columns_to_plot = ['QH_sys_MWhyr', 'QC_sys_MWhyr', 'Qcs_sys_MWhyr', 'E_sys_MWhyr', 'Qcre_sys_MWhyr', 'Qcdata_sys_MWhyr']
                   # 'Qhpro_sys_MWhyr']
list_buildings = ['B153767', 'B302006694', 'B302006646', 'B302007056a', 'B302006839', 'B302049656', 'B302007086',
                  'B302007412', 'B153701', 'B302006827', 'B302023104', 'B302049659', 'B302007081', 'B302007064',
                  'B153766', 'B3169932', 'B302007073', 'B302007089', 'B302023103', 'B302049650', 'B302049632',
                  'B302007868', 'B302007317', 'B302007331', 'B302049821', 'B302007876', 'B9011701', 'B3169989',
                  'B302007529', 'B302007869', 'B2367084', 'B302007864', 'B153690', 'B302007056', 'B9011838',
                  'B302034660a', 'B302034660b', 'B302034660c', 'B140577a', 'B140577b', 'B140577c']

dataframe_dict = {}
dataframe_dict['measured'] = pd.read_excel(os.path.join(path_to_scenarios, 'building-metering',
                                                        measurement_filename)).set_index('Name')
for scenario in scenarios:
    dataframe_dict[scenario] = pd.read_csv(os.path.join(path_to_scenarios, scenario,
                                                        'outputs\data\demand\Total_demand.csv')).set_index('Name')

min_error = pd.DataFrame(data=1e6 * np.ones([len(list_buildings), len(columns_to_plot)]), index=list_buildings,
                         columns=columns_to_plot)
min_error_labels = pd.DataFrame(data=None, index=list_buildings, columns=columns_to_plot)

for column in columns_to_plot:
    data = []
    for scenario in dataframe_dict.keys():
        data.append(go.Bar(x=list_buildings, y=dataframe_dict[scenario].loc[list_buildings, column], name=scenario))
    layout = go.Layout(barmode='group')
    fig = go.Figure(data=data, layout=layout)
    plot(fig, auto_open=False, filename=os.path.join(path_to_scenarios, 'comparison-graphs', column+'.html'))

    data2 = []
    data3 = []
    data4 = []
    measured_data = dataframe_dict['measured'].loc[list_buildings, column]
    for scenario in scenarios:
        error_data = np.abs((dataframe_dict[scenario].loc[list_buildings, column] - measured_data) / measured_data)
        error_data_2 = error_data * dataframe_dict[scenario].loc[list_buildings, column]
        data2.append(go.Bar(x=list_buildings, y=error_data, name=scenario))
        data3.append(go.Bar(x=list_buildings, y=error_data_2, name=scenario))
        for i in range(len(list_buildings)):
            if error_data[i] < min_error.loc[list_buildings[i], column]:
                min_error.loc[list_buildings[i], column] = error_data[i]
                min_error_labels.loc[list_buildings[i], column] = scenario

    layout2 = go.Layout(barmode='group')
    layout3 = go.Layout(barmode='group')
    fig2 = go.Figure(data=data2, layout=layout2)
    fig3 = go.Figure(data=data3, layout=layout3)
    plot(fig2, auto_open=False, filename=os.path.join(path_to_scenarios, 'comparison-graphs', column+'_error.html'))
    plot(fig3, auto_open=False,
         filename=os.path.join(path_to_scenarios, 'comparison-graphs', column+'_normalized_error.html'))

min_error.to_csv(r'C:\Users\User\Downloads\reference-case-ETH-Mahshid\min_error.csv')
min_error_labels.to_csv(r'C:\Users\User\Downloads\reference-case-ETH-Mahshid\min_error_labels.csv')