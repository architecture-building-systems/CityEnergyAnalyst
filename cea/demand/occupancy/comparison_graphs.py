import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

path_to_scenarios = r'C:\reference-case-open'

# columns_to_plot = [column for column in list(pd.read_csv(
#     os.path.join(path_to_scenarios, 'zurich_baseline\deterministic\outputs\data\demand\Total_demand.csv')).columns) if
#                    column not in ['Name', 'Af_m2', 'Aroof_m2', 'GFA_m2', 'Ecaf_MWhyr', 'Ecaf0_kW', 'Q_cool_ref_MWhyr',
#                                   'q_cs_lat_peop_MWhyr', 'q_cs_lat_peop0_kW', 'Qcs_sen0_kW', 'Qhsf_lat_MWhyr',
#                                   'Qhsf_lat_kW']]

columns_to_plot_yearly = ['people0', 'Qcsf0_kW', 'Qcsf_MWhyr', 'Qhsf_MWhyr', 'Qhsf0_kW', 'Eauxf_ve_MWhyr',
                          'Eauxf_ve0_kW', 'Qcsf_lat_MWhyr', 'Qcsf_lat0_kW', 'Qgain_pers_MWhyr', 'Qgain_pers0_kW',
                          'Qgain_vent_MWhyr', 'Qgain_vent0_kW']
columns_to_plot_hourly = ['people', 'Qcsf_kWh', 'Qhsf_kWh', 'Eauxf_ve_kWh', 'Qcsf_lat_kWh']

scenarios = ['baseline', 'masterplan', 'dynamic']
cases = ['deterministic', 'stochastic']

which_plots = {'bar': True,
               'vs': True,
               'hourly': True}

# which_hourly = ['people', 'Qcsf_kWh', 'Eauxf_ve_kWh']
columns_to_plot = columns_to_plot_yearly
which_hourly = columns_to_plot_hourly

for scenario in scenarios:
    baseline_df = pd.read_csv(os.path.join(path_to_scenarios, 'zurich_'+scenario,
                                           'deterministic\outputs\data\demand\Total_demand.csv')).set_index('Name')
    stochastic_df = pd.read_csv(os.path.join(path_to_scenarios, 'zurich_'+scenario,
                                             'stochastic\outputs\data\demand\Total_demand.csv')).set_index('Name')
    for column in columns_to_plot:
        if which_plots['bar']:
            if column != 'people0':
                unit = column.split('_')[len(column.split('_')) - 1]
            else:
                unit = 'people'
            # data to plot
            n_groups = len(baseline_df.index)
            baseline = baseline_df[column]
            stochastic = stochastic_df[column]

            # create plot
            fig, ax = plt.subplots()
            index = np.arange(n_groups)
            bar_width = 0.35
            opacity = 0.8

            rects1 = plt.bar(index, baseline, bar_width,
                             alpha=opacity,
                             color='b',
                             label='baseline')

            rects2 = plt.bar(index + bar_width, stochastic, bar_width,
                             alpha=opacity,
                             color='g',
                             label='stochastic')

            plt.xlabel('Building')
            plt.ylabel(unit)
            plt.title(column)
            plt.xticks(index + bar_width, (baseline_df.index))
            plt.legend()

            plt.tight_layout()
            plt.savefig(os.path.join(path_to_scenarios,'zurich_'+scenario,'comparison', column + '.png'))
            plt.close()

        if which_plots['vs']:
            # create point plot
            plt.plot(baseline, stochastic, 'o')
            if max(abs(baseline)) > max(baseline):
                plt.plot([0, -max(abs(baseline))], [0, -max(abs(baseline))], 'k--')
            else:
                plt.plot([0, max(baseline)], [0, max(baseline)], 'k--')
            plt.title(column)
            plt.savefig(os.path.join(path_to_scenarios,'zurich_'+scenario,'comparison', column + '_points.png'))
            plt.close()

if which_plots['hourly']:
    for scenario in scenarios:
        for measurement in which_hourly:
            comparison_path = os.path.join(path_to_scenarios, 'zurich_' + scenario, 'comparison', measurement)
            if not os.path.exists(comparison_path):
                os.makedirs(comparison_path)

            data = pd.DataFrame(data=None, columns=cases, index=range(8760))
            if measurement != 'people':
                unit = measurement.split('_')[len(measurement.split('_')) - 1]
            else:
                unit = 'people'

            for file in os.listdir(
                    os.path.join(path_to_scenarios, 'zurich_' + scenario, 'deterministic', 'outputs\data\demand')):
                if file != 'Total_demand.csv':
                    building_file = os.path.splitext(file)[0]
                    for case in cases:
                        current_data = pd.read_csv(
                            os.path.join(path_to_scenarios, 'zurich_' + scenario, case, 'outputs\data\demand', file))
                        data[case] = current_data[measurement]

                    plt.plot(data)
                    plt.title(measurement)
                    plt.ylabel(unit)
                    plt.legend(cases)
                    plt.savefig(os.path.join(comparison_path, building_file + '.png'))
                    plt.close()
