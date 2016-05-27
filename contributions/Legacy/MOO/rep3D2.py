import pandas as pd
import numpy as np
import plotly.plotly as py
from plotly.graph_objs import *

datafile = pd.read_csv('C:\ArcGIS\ESMdata\DataFinal\MOO\CAMP\NtwRes\Network_summary_result_all.csv',usecols=['Q_DH_building_netw_total','Electr_netw_total','T_sst_heat_supply_netw_total'])
heat = datafile.T_sst_heat_supply_netw_total.values
heat = datafile.Electr_netw_total.values
heat_ravel = []
for day in range (365):
   heat_ravel.append(heat[day*24:(day+1)*24])

data = Data([
    Surface(
        z=heat_ravel)
])
layout = Layout(
    autosize=True,
    
)
fig = Figure(data=data, layout=layout)
plot_url = py.plot(fig, filename='elevations-3d-surface')


datafile = pd.read_csv('C:\ArcGIS\EDMdata\DataFinal\EDM\SQ\ZONE_4\Bau 19.csv',usecols=['tshs'])
heat = datafile.tshs.values
heat_ravel = []
for day in range (365):
   heat_ravel.append(heat[day*24:(day+1)*24])

data = Data([
    Surface(
        z=heat_ravel)
])
layout = Layout(
    autosize=True,
    
)
fig = Figure(data=data, layout=layout)
plot_url = py.plot(fig, filename='elevations-3d-surface')