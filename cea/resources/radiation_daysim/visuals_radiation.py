import pandas as pd
import os
from cea.utilities import dbfreader


date = pd.date_range('1/1/2010', periods=8760, freq='H')[:48]
buildings = ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09']
location = r'C:\reference-case-open\baseline\outputs\data\solar-radiation'
time = date.strftime("%Y%m%d%H%M%S")


for i, building in enumerate(buildings):
    data = pd.read_csv(os.path.join(location, building+'_srf_properties.csv'))
    geometry = data.set_index('surface_name')
    solar = pd.read_csv(os.path.join(location, building+'_srf_solar_results.csv'))
    surfaces = solar.columns.values

    for surface in surfaces:
        Xcoor = geometry.loc[surface, 'centre_point_x']
        Ycoor = geometry.loc[surface, 'centre_point_y']
        Zcoor = geometry.loc[surface, 'centre_point_z']
        result = pd.DataFrame({'DATE': time , 'NAME':building+surface,
                               'I_Wm2': solar[surface].values[:48],
                               'Xcoor': Xcoor, 'Ycorr': Ycoor, 'Zcoor':Zcoor})
        if i == 0:
            final = result
        else:
            final = final.append(result, ignore_index=True)

dbfreader.df2dbf(final, r'C:\reference-case-open\baseline\outputs\data\solar-radiation/result_solar_48h.dbf')
#dbfreader.df2dbf(data, r'C:\reference-case-open\baseline\outputs\data\solar-radiation/surfaces.dbf')