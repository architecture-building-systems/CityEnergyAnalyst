# import data
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
scenario_path = r'C:\microclimate-study'
mp_path = os.path.join(scenario_path,'masterplan')
envi_path = os.path.join(scenario_path,'masterplan_envi')
output_path = 'outputs\data\demand'
bdgs = pd.read_csv(os.path.join(envi_path,'inputs','microclimate-data','rh_ext.csv')).columns.drop('hoy')
sum = {}
sum = pd.DataFrame(data=None, columns=['building','no microclimate', 'with microclimate'])
hottest_or_coldest = 'hottest'
if hottest_or_coldest == 'coldest':
	variable = 'Qhsf'
	service = 'Heating'
	day_of_analysis = 'Jan 12th'
	hour_start = 264
	hour_end = 287
else:
	variable = 'Qcsf'
	service = 'Cooling'
	day_of_analysis = 'Aug 19th'
	hour_start = 5520
	hour_end = 5543

buildings_to_add = {'B155192': 'B155192', 'B302007201': 'B155192', 'B155194': 'B155194', 'B2372522': 'B2372522',
                    'B302006839': 'B302006839', 'B302007086': 'B302007086', 'B302007087': 'B302007087',
                    'B302007093': 'B302007093', 'MPB1A': 'MPB1', 'MPB1B': 'MPB1', 'MPB1C': 'MPB1', 'MPB1D': 'MPB1',
                    'MPB1E': 'MPB1', 'MPB1F': 'MPB1', 'MPB1G': 'MPB1', 'MPB1H': 'MPB1', 'MPB1I': 'MPB1', 'MPB1J':
                        'MPB1', 'MPB1K': 'MPB1', 'MPB1L': 'MPB1', 'B302007714': 'MPB1', 'B302049800': 'MPB1',
                    'B155061': 'MPB1', 'B302061510': 'MPB1', 'MPB3A': 'MPB3', 'MPB3B': 'MPB3', 'MPB3C': 'MPB3',
                    'MPB3D': 'MPB3', 'MPB3E': 'MPB3', 'MPB3F': 'MPB3', 'MPB3G': 'MPB3', 'MPB3H': 'MPB3', 'MPB3I':
                        'MPB3', 'MPB3J': 'MPB3', 'MPB4A': 'MPB4', 'MPB4B': 'MPB4', 'MPB4C': 'MPB4', 'MPB5A': 'MPB5',
                    'MPB5B': 'MPB5', 'MPB5C': 'MPB5', 'MPB5D': 'MPB5', 'B302007387': 'MPB5', 'MPB5E': 'MPB5E',
                    'MPB6A': 'MPB6A', 'MPB6B': 'MPB6B', 'MPB7A': 'MPB7A', 'MPB7B': 'MPB7B', 'MPB7C': 'MPB7B',
                    'MPB7D': 'MPB7B', 'MPB7E': 'MPB7E', 'MPB8A': 'MPB8', 'MPB8B': 'MPB8', 'B2367084': 'MPB8'}
buildings_final = []
for key in buildings_to_add.keys():
    if not buildings_to_add[key] in buildings_final:
        buildings_final.append(buildings_to_add[key])

# hourly graphs
for q in [0,1,2]:
    f, ax = plt.subplots(3, 6, sharex=True, sharey=True)
    m = 0
    n = 0
    for i in range(18*q, 18*(q+1)):
        if i < len(bdgs):
            mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
            envi_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
            sum.loc[i,'building'] = bdgs[i]
            sum.loc[i,'no microclimate'] = mp_df.loc[hour_start:hour_end,variable+'_kWh'].sum()
            sum.loc[i,'with microclimate'] = envi_df.loc[hour_start:hour_end,variable+'_kWh'].sum()
            if n > 5:
                m += 1
                n = 0
            ax[m][n].plot(range(24), mp_df.loc[hour_start:hour_end, variable+'_kWh'], range(24), envi_df.loc[hour_start:hour_end, variable+'_kWh'])
            ax[m][n].set_title(bdgs[i])
            n += 1
    if q  < 2:
        ax[2][5].legend(['no microclimate', 'with microclimate'])
    else:
        ax[2][4].legend(['no microclimate', 'with microclimate'])

# daily bar chart
sum.set_index('building', inplace=True)
sum_summarized = pd.DataFrame(data=0, columns=sum.columns.values, index=buildings_final)
for key in buildings_to_add.keys():
    sum_summarized.loc[buildings_to_add[key]] += sum.loc[key]

f, ax = plt.subplots()
index = np.arange(len(bdgs))
plt.bar(index,sum['no microclimate'], 0.35, label='No microclimate')
plt.bar(index+.35,sum['with microclimate'], 0.35, label='With microclimate')
plt.ylabel(service+' demand on '+day_of_analysis+' (kWh)')
plt.legend()

# generate csv files
## if DataFrames doesn't exist yet
hourly_mp = pd.DataFrame(data=0,columns=buildings_final, index=range(hour_start,hour_end+1))
hourly_mp['DATE'] = mp_df.loc[hour_start:hour_end,'DATE']
hourly_nv = hourly_mp.copy(deep=True)
## if DataFrames already exist
for column in buildings_final:
    hourly_mp[column] = np.zeros(len(hourly_mp[column]))
    hourly_nv[column] = np.zeros(len(hourly_nv[column]))


for i in range(len(bdgs)):
    mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
    nv_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
    hourly_mp[buildings_to_add[bdgs[i]]] += mp_df.loc[hour_start:hour_end,variable+'_kWh']
    hourly_nv[buildings_to_add[bdgs[i]]] += nv_df.loc[hour_start:hour_end,variable+'_kWh']
hourly_mp.set_index('DATE').to_csv(os.path.join(r'C:\microclimate-study',hottest_or_coldest+'_day_results',
                                                day_of_analysis+'_hourly_'+service+'_kWh_mp.csv'))
hourly_nv.set_index('DATE').to_csv(os.path.join(r'C:\microclimate-study',hottest_or_coldest+'_day_results',
                                                day_of_analysis+'_hourly_'+service+'_kWh_nv.csv'))

daily_mp = pd.DataFrame(data=0,index=buildings_final,columns=['Heating (kWh)','Cooling (kWh)','Electricity (kWh)'])
daily_nv = pd.DataFrame(data=0,index=buildings_final,columns=['Heating (kWh)','Cooling (kWh)','Electricity (kWh)'])
for i in range(len(bdgs)):
    mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
    nv_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
    daily_mp.loc[buildings_to_add[bdgs[i]],'Heating (kWh)'] += mp_df.loc[hour_start:hour_end,'Qhsf_kWh'].sum()
    daily_nv.loc[buildings_to_add[bdgs[i]],'Heating (kWh)'] += nv_df.loc[hour_start:hour_end,'Qhsf_kWh'].sum()
    daily_mp.loc[buildings_to_add[bdgs[i]],'Cooling (kWh)'] += mp_df.loc[hour_start:hour_end,'QCf_kWh'].sum()
    daily_nv.loc[buildings_to_add[bdgs[i]],'Cooling (kWh)'] += nv_df.loc[hour_start:hour_end,'QCf_kWh'].sum()
    daily_mp.loc[buildings_to_add[bdgs[i]],'Electricity (kWh)'] += mp_df.loc[hour_start:hour_end,'QEf_kWh'].sum()
    daily_nv.loc[buildings_to_add[bdgs[i]],'Electricity (kWh)'] += nv_df.loc[hour_start:hour_end,'QEf_kWh'].sum()
daily_mp.to_csv(os.path.join(r'C:\microclimate-study',hottest_or_coldest+'_day_results',day_of_analysis+'_daily_'+
                             service+'_kWh_mp.csv'))
daily_nv.to_csv(os.path.join(r'C:\microclimate-study',hottest_or_coldest+'_day_results',day_of_analysis+'_daily_'+
                             service+'_kWh_nv.csv'))

daily_non_added_mp = pd.DataFrame(data=0,columns=['Qhsf_kWh','QCf_kWh','Ef_kWh'],index=bdgs)
daily_non_added_nv = pd.DataFrame(data=0,columns=['Qhsf_kWh','QCf_kWh','Ef_kWh'],index=bdgs)
for i in range(len(bdgs)):
    mp_df = pd.read_csv(os.path.join(mp_path, output_path, bdgs[i] + '.csv'))
    nv_df = pd.read_csv(os.path.join(envi_path, output_path, bdgs[i] + '.csv'))
    daily_non_added_mp.loc[bdgs[i],'Qhsf_kWh'] += mp_df.loc[hour_start:hour_end,'Qhsf_kWh'].sum()
    daily_non_added_nv.loc[bdgs[i],'Qhsf_kWh'] += nv_df.loc[hour_start:hour_end,'Qhsf_kWh'].sum()
    daily_non_added_mp.loc[bdgs[i],'QCf_kWh'] += mp_df.loc[hour_start:hour_end,'QCf_kWh'].sum()
    daily_non_added_nv.loc[bdgs[i],'QCf_kWh'] += nv_df.loc[hour_start:hour_end,'QCf_kWh'].sum()
    daily_non_added_mp.loc[bdgs[i],'Ef_kWh'] += mp_df.loc[hour_start:hour_end,'QEf_kWh'].sum()
    daily_non_added_nv.loc[bdgs[i],'Ef_kWh'] += nv_df.loc[hour_start:hour_end,'QEf_kWh'].sum()
# daily_non_added_mp.to_csv(r'C:\microclimate-study\coldest_day_results\Jan12_daily_heating_kWh_non_added_mp')
# daily_non_added_nv.to_csv(r'C:\microclimate-study\coldest_day_results\Jan12_daily_heating_kWh_non_added_nv')
areas_df = pd.read_csv(r'C:\microclimate-study\masterplan_envi\outputs\data\demand\Total_demand.csv').set_index('Name')['Af_m2']
pd.concat([daily_non_added_mp, areas_df], axis=1, join='inner').to_csv(
    os.path.join(r'C:\microclimate-study',hottest_or_coldest+'_day_results',day_of_analysis+'_daily_'+service+
                 '_kWh_non_added_mp.csv'))
pd.concat([daily_non_added_nv, areas_df], axis=1, join='inner').to_csv(
    os.path.join(r'C:\microclimate-study',hottest_or_coldest+'_day_results',day_of_analysis+'_daily_'+service+
                 '_kWh_non_added_nv.csv'))

