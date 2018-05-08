import os
import pandas as pd
import cea.plots

naming_file = pd.read_csv(os.path.join(os.path.dirname(cea.plots.__file__), "naming.csv"))
keys = naming_file["VARIABLE"]
values = naming_file["SHORT_DESCRIPTION"]
NAMING = dict(zip(keys, values))

source = "https://raw.githubusercontent.com/architecture-building-systems/CityEnergyAnalyst/master/logo/CEA.png"
LOGO =  [dict(
        source= source,
        xref="paper", yref="paper",
        x=0.0, y=1.2,
        sizex=0.15, sizey=0.15,
        xanchor="center", yanchor="top")]