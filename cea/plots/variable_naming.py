

NAMING = {'Qhsf': 'final space heating',
          'Qcsf': 'final space cooling',
          'Qwwf': 'final hot water',
          'Ef': 'final electricity'}

COLORS =  {'Qhsf': "rgb(,,)",
          'Qcsf': "rgb(,,)",
          'Qwwf': "rgb(,,)",
          'Ef': "rgb(,,)"}

LOGO =  [dict(
        source="https://raw.githubusercontent.com/architecture-building-systems/CityEnergyAnalyst/i905-dashboard/cea_logo.png",
        xref="paper", yref="paper",
        x=0.1, y=1.05,
        sizex=0.35, sizey=0.35,
        xanchor="center", yanchor="bottom")]

GENERATION_UNITS_CODE = {"0": "Photovoltaic Panel [kW]",
                         "1": "Photovoltaic-Thermal Panel",
                         "2": "Combined-cycle Gas Engine",
                         "3": "Gas Boiler"}