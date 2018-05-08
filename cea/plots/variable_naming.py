import os
import pandas as pd
import logo

naming_file = pd.read_csv(os.path.join(os.path.dirname(cea.plots.__file__), "naming.csv"))
keys = naming_file["VARIABLE"]
values = naming_file["SHORT_DESCRIPTION"]
NAMING = dict(zip(keys, values))

source = os.path.join(os.path.dirname(logo.__file__), "CEA.png")
LOGO =  [dict(
        source= source,
        xref="paper", yref="paper",
        x=0.1, y=1.05,
        sizex=0.35, sizey=0.35,
        xanchor="center", yanchor="bottom")]