# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import matplotlib.pyplot as plt
import pandas as pd

# <codecell>

CQ_name = 'UC2030'
Scenario = 'UC2030'
locationFinal = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+Scenario+'\\'+CQ_name
locationFinal2 = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'SEDM'+'\\'+'UC2030'+'\\'+CQ_name

# <codecell>

Data_Analytical = pd.read_csv(locationFinal+'\\'+'total.csv')
Analytical = Data_Analytical[['Name','Qhsf','Qcsf','Ealf','Qwwf']]

# <codecell>

Data_statistic = pd.read_csv(locationFinal2+'\\'+'Loads.csv')
Statistic = Data_statistic[['Name','Qcsf','Qcdataf','Qcpf','Ealf','Edataf','Epf','Qwwf','Qhpf','Qhsf']]

# <codecell>

Demand_join = pd.merge(Analytical,Statistic,left_on='Name', right_on='Name',suffixes=('_A', '_S'),how='inner')
Demand_join.to_excel(r'C:\ArcGIS\EDMdata\DataFinal\Models Validation\ValueUC.xls',sheet_name='Values')
Demand_join.transpose().to_excel(r'C:\ArcGIS\EDMdata\DataFinal\Models Validation\ValuesUCT.xls',sheet_name='Values')

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Qhsf_A,width, color='#000000', label='Qhsf_A');
ax.bar(Demand_join.index+width+0.3,Demand_join.Qhsf_S,width,color='#2f4f4f',label='Qhsf_S');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>


