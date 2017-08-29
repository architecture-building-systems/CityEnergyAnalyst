import esoreader
import pandas as pd

eso_path=r"F:\outcalib\DB6new\LHS-000000\eplusout.eso"
eso = esoreader.read_from_path(eso_path)
f_vars=eso.find_variable('Mean')
f_vars2=f_vars[300:]
#df = pd.DataFrame.from_items(f_vars[1:30])
#df = eso.to_frame('heating energy')

#eso = esoreader.read_from_path(eso_path)
#df = eso.to_frame('Zone Mean Air Temperature', key='T_FLOOR3:N.31')
#eso.find_variable('Zone Mean Air Temperature')
#df = eso.to_frame('Zone Mean Air Temperature')
#print df
#df = eso.to_frame('heating energy')

#pp=pd.DataFrame(time_series)
#print pd
eso_path1=r"F:\outcalib\DB6new\LHS-000000\eplusout.csv"
#df.to_csv(eso_path1, index=False, header=True, float_format='%.3f', decimal='.')

