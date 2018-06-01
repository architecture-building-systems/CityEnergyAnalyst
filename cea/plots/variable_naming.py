import os
import pandas as pd
import cea.plots


# GET SHORT NAMES OF VARIABLES IN CEA
naming_file = pd.read_csv(os.path.join(os.path.dirname(cea.plots.__file__), "naming.csv"))
keys = naming_file["VARIABLE"]
values = naming_file["SHORT_DESCRIPTION"]
NAMING = dict(zip(keys, values))

# GET LOGO OF CEA
LOGO =  [dict(
        source= "https://raw.githubusercontent.com/architecture-building-systems/CityEnergyAnalyst/master/logo/CEA.png",
        xref="paper", yref="paper",
        x=0.0, y=1.2,
        sizex=0.15, sizey=0.15,
        xanchor="center", yanchor="top")]

# GET COLORS OF CEA
COLORS = {"red": "rgb(240,75,91)",
                       "red_light": "rgb(246,148,143)",
                       "red_lighter": "rgb(252,217,210)",
                       "blue": "rgb(63,192,194)",
                       "blue_light": "rgb(171,221,222)",
                       "blue_lighter": "rgb(225,242,242)",
                       "yellow": "rgb(255,209,29)",
                       "yellow_light": "rgb(255,225,133)",
                       "yellow_lighter": "rgb(255,243,211)",
                       "brown": "rgb(174,148,72)",
                       "brown_light": "rgb(201,183,135)",
                       "brown_lighter": "rgb(233,225,207)",
                       "purple": "rgb(171,95,127)",
                       "purple_light": "rgb(198,149,167)",
                       "purple_lighter": "rgb(231,214,219)",
                       "green": "rgb(126,199,143)",
                       "green_light": "rgb(178,219,183)",
                       "green_lighter": "rgb(227,241,228)",
                       "grey": "rgb(68,76,83)",
                       "grey_light": "rgb(126,127,132)",
                       "black": "rgb(35,31,32)",
                       "white": "rgb(255,255,255)",
                       "orange": "rgb(245,131,69)",
                       "orange_light": "rgb(248,159,109)",
                       "orange_lighter": "rgb(254,220,198)"}

# GET COLORS OF VARIABLES IN CEA
keys = naming_file["VARIABLE"]
values2 = [COLORS[x] for x in naming_file["COLOR"]]
COLOR = dict(zip(keys, values2))

