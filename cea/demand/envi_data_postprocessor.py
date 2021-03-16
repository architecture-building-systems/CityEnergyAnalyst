# import data
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

# folder path
scenario_path = r'C:\small_studies\microclimate-study\20180530'

# scenarios
for (no_micro_scenario_name, envi_scenario_name) in [('no-micro', 'envi'), ('envi-s', 'envi-o')]:
    # no_micro_scenario_name = 'no-micro'
    # envi_scenario_name = 'envi'
    mp_path = os.path.join(scenario_path, no_micro_scenario_name)
    envi_path = os.path.join(scenario_path, envi_scenario_name)

    # type of outputs
    hourly_graphs = False
    daily_bar_chart = False
    generate_csv_files = True
    aggregated = False
    # hottest_or_coldest = 'coldest'

    for hottest_or_coldest in ['hottest', 'coldest']:
        output_path = 'outputs\data\demand'
        # get data
        bdgs = pd.read_csv(os.path.join(envi_path, 'outputs', 'data', 'demand', 'Total_demand.csv'))['Name']
        sum = pd.DataFrame(data=None, columns=['building', 'no microclimate', 'with microclimate'])

        if hottest_or_coldest == 'coldest':
            variable = 'Qhsf'
            service = 'Space heating'
            day_of_analysis = 'Jan 12th'
            hour_start = 264
            hour_end = 287
        else:
            variable = 'Qcsf'
            service = 'Space cooling'
            day_of_analysis = 'Aug 19th'
            hour_start = 5520
            hour_end = 5543

        if aggregated:
            buildings_to_add_df = pd.read_csv(os.path.join(scenario_path, 'Buildings_to_add.csv')).set_index('part_name')
            buildings_to_add = dict(zip(bdgs, buildings_to_add_df['total_name'].loc[bdgs]))
        else:
            buildings_to_add = dict(zip(bdgs, bdgs))

        buildings_final = []
        for key in buildings_to_add.keys():
            if not buildings_to_add[key] in buildings_final:
                buildings_final.append(buildings_to_add[key])

        if hourly_graphs:
            # hourly graphs
            for q in [0, 1, 2]:
                f, ax = plt.subplots(3, 6, sharex=True, sharey=True)
                m = 0
                n = 0
                for i in range(18 * q, 18 * (q + 1)):
                    if i < len(bdgs):
                        mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
                        envi_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
                        sum.loc[i, 'building'] = bdgs[i]
                        sum.loc[i, 'no microclimate'] = mp_df.loc[hour_start:hour_end, variable + '_kWh'].sum()
                        sum.loc[i, 'with microclimate'] = envi_df.loc[hour_start:hour_end, variable + '_kWh'].sum()
                        if n > 5:
                            m += 1
                            n = 0
                        ax[m][n].plot(range(24), mp_df.loc[hour_start:hour_end, variable + '_kWh'], range(24),
                                      envi_df.loc[hour_start:hour_end, variable + '_kWh'])
                        ax[m][n].set_title(bdgs[i])
                        n += 1
                if q < 2:
                    ax[2][5].legend(['no microclimate', 'with microclimate'])
                else:
                    ax[2][4].legend(['no microclimate', 'with microclimate'])

            plt.savefig(os.path.join(scenario_path, hottest_or_coldest + '_day_results', day_of_analysis + '_hourly.png'))
            plt.close()

        else:
            for i in range(len(bdgs)):
                mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
                envi_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
                sum.loc[i, 'building'] = bdgs[i]
                sum.loc[i, 'no microclimate'] = mp_df.loc[hour_start:hour_end, variable + '_kWh'].sum()
                sum.loc[i, 'with microclimate'] = envi_df.loc[hour_start:hour_end, variable + '_kWh'].sum()

        if daily_bar_chart:
            # daily bar chart
            sum.set_index('building', inplace=True)
            sum_summarized = pd.DataFrame(data=0, columns=sum.columns.values, index=buildings_final)
            for key in buildings_to_add.keys():
                sum_summarized.loc[buildings_to_add[key]] += sum.loc[key]

            f, ax = plt.subplots()
            index = np.arange(len(bdgs))
            plt.bar(index, sum['no microclimate'], 0.35, label='No microclimate')
            plt.bar(index + .35, sum['with microclimate'], 0.35, label='With microclimate')
            plt.ylabel(service + ' demand on ' + day_of_analysis + ' (kWh)')
            plt.legend()

            plt.savefig(os.path.join(scenario_path, hottest_or_coldest + '_day_results', day_of_analysis + '_daily.png'))
            plt.close()

        if generate_csv_files:
            # generate csv files
            ## if DataFrames doesn't exist yet
            hourly_mp = pd.DataFrame(data=0, columns=buildings_final, index=range(hour_start, hour_end + 1))
            hourly_mp['DATE'] = mp_df.loc[hour_start:hour_end, 'DATE']
            hourly_nv = hourly_mp.copy(deep=True)
            ## if DataFrames already exist
            for column in buildings_final:
                hourly_mp[column] = np.zeros(len(hourly_mp[column]))
                hourly_nv[column] = np.zeros(len(hourly_nv[column]))

            for i in range(len(bdgs)):
                mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
                nv_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
                hourly_mp[buildings_to_add[bdgs[i]]] += mp_df.loc[hour_start:hour_end, variable + '_kWh']
                hourly_nv[buildings_to_add[bdgs[i]]] += nv_df.loc[hour_start:hour_end, variable + '_kWh']
            hourly_mp.set_index('DATE').to_csv(os.path.join(scenario_path, hottest_or_coldest + '_day_results',
                                                            day_of_analysis + '_hourly_' + service + '_kWh_' +
                                                            no_micro_scenario_name + '.csv'))
            hourly_nv.set_index('DATE').to_csv(os.path.join(scenario_path, hottest_or_coldest + '_day_results',
                                                            day_of_analysis + '_hourly_' + service + '_kWh_' +
                                                            envi_scenario_name + '.csv'))

            daily_mp = pd.DataFrame(data=0, index=buildings_final, columns=['Space heating (kWh)', 'Space cooling (kWh)',
                                                                            'Electricity (kWh)'])
            daily_nv = pd.DataFrame(data=0, index=buildings_final, columns=['Space heating (kWh)', 'Space cooling (kWh)',
                                                                            'Electricity (kWh)'])
            for i in range(len(bdgs)):
                mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
                nv_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
                daily_mp.loc[buildings_to_add[bdgs[i]], 'Space heating (kWh)'] += mp_df.loc[hour_start:hour_end,
                                                                                  'Qhsf_kWh'].sum()
                daily_nv.loc[buildings_to_add[bdgs[i]], 'Space heating (kWh)'] += nv_df.loc[hour_start:hour_end,
                                                                                  'Qhsf_kWh'].sum()
                daily_mp.loc[buildings_to_add[bdgs[i]], 'Space cooling (kWh)'] += mp_df.loc[hour_start:hour_end,
                                                                                  'Qcsf_kWh'].sum()
                daily_nv.loc[buildings_to_add[bdgs[i]], 'Space cooling (kWh)'] += nv_df.loc[hour_start:hour_end,
                                                                                  'Qcsf_kWh'].sum()
                daily_mp.loc[buildings_to_add[bdgs[i]], 'Electricity (kWh)'] += mp_df.loc[hour_start:hour_end, 'QEf_kWh'].sum()
                daily_nv.loc[buildings_to_add[bdgs[i]], 'Electricity (kWh)'] += nv_df.loc[hour_start:hour_end, 'QEf_kWh'].sum()
            daily_mp.to_csv(os.path.join(scenario_path, hottest_or_coldest + '_day_results', day_of_analysis + '_daily_' +
                                         service + '_kWh_' + no_micro_scenario_name + '.csv'))
            daily_nv.to_csv(os.path.join(scenario_path, hottest_or_coldest + '_day_results', day_of_analysis + '_daily_' +
                                         service + '_kWh_' + envi_scenario_name + '.csv'))

            daily_non_added_mp = pd.DataFrame(data=0, columns=['Qhsf_kWh', 'Qcsf_kWh', 'Ef_kWh'], index=bdgs)
            daily_non_added_nv = pd.DataFrame(data=0, columns=['Qhsf_kWh', 'Qcsf_kWh', 'Ef_kWh'], index=bdgs)
            for i in range(len(bdgs)):
                mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
                nv_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
                daily_non_added_mp.loc[bdgs[i], 'Qhsf_kWh'] += mp_df.loc[hour_start:hour_end, 'Qhsf_kWh'].sum()
                daily_non_added_nv.loc[bdgs[i], 'Qhsf_kWh'] += nv_df.loc[hour_start:hour_end, 'Qhsf_kWh'].sum()
                daily_non_added_mp.loc[bdgs[i], 'Qcsf_kWh'] += mp_df.loc[hour_start:hour_end, 'Qcsf_kWh'].sum()
                daily_non_added_nv.loc[bdgs[i], 'Qcsf_kWh'] += nv_df.loc[hour_start:hour_end, 'Qcsf_kWh'].sum()
                daily_non_added_mp.loc[bdgs[i], 'Ef_kWh'] += mp_df.loc[hour_start:hour_end, 'QEf_kWh'].sum()
                daily_non_added_nv.loc[bdgs[i], 'Ef_kWh'] += nv_df.loc[hour_start:hour_end, 'QEf_kWh'].sum()

            areas_df = \
                pd.read_csv(os.path.join(scenario_path, envi_path,
                                         'outputs\data\demand\Total_demand.csv')).set_index('Name')['Af_m2']
            pd.concat([daily_non_added_mp, areas_df], axis=1, join='inner').to_csv(
                os.path.join(scenario_path, hottest_or_coldest + '_day_results', day_of_analysis + '_daily_' + service +
                             '_kWh_' + no_micro_scenario_name + '.csv'))
            pd.concat([daily_non_added_nv, areas_df], axis=1, join='inner').to_csv(
                os.path.join(scenario_path, hottest_or_coldest + '_day_results', day_of_analysis + '_daily_' + service +
                             '_kWh_' + envi_scenario_name + '.csv'))
