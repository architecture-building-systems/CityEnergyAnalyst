from __future__ import division
import pandas as pd
import matplotlib.pyplot as plt


index = pd.date_range('1/1/2016', periods=8760, freq='H')
file = pd.read_json(r'C:\reference-case-ecocampus\baseline\outputs\data\solar-radiation/B001_insolation_Whm2.json')
file.set_index(index, inplace=True)
print file.sum(axis = 0 )/1000

#print file[2300:2370]
file.plot()

plt.show()


