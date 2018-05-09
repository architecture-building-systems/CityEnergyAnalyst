import os
import pandas as pd
import cea.plots


# GET SHORT NAMES OF VARIABLES IN CEA
naming_file = pd.read_csv(os.path.join(os.path.dirname(cea.plots.__file__), "naming.csv"))
keys = naming_file["VARIABLE"]
values = naming_file["SHORT_DESCRIPTION"]
NAMING = dict(zip(keys, values))

# GET COLORS OF VARIABLES IN CEA
keys = naming_file["VARIABLE"]
values2 = naming_file["COLOR"]
COLOR = dict(zip(keys, values2))

# GET LOGO OF CEA
LOGO =  [dict(
        source= "https://raw.githubusercontent.com/architecture-building-systems/CityEnergyAnalyst/master/logo/CEA.png",
        xref="paper", yref="paper",
        x=0.0, y=1.2,
        sizex=0.15, sizey=0.15,
        xanchor="center", yanchor="top")]