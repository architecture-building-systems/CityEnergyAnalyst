

NAMING = {'Qhsf': 'final space heating',
          'Qcsf': 'final space cooling',
          'Qwwf': 'final hot water',
          'Ef': 'final electricity'}

COLOR =  {'Qhsf': "rgb(240,75,91)",
          'Qcsf': "rgb(63,192,194)",
          'Qwwf': "rgb(255,209,29)",
          'Ef': "rgb(126,199,143)",
          "Twwf_sup_C": "rgb(255,209,29)",
          "Twwf_re_C": "rgb(255,209,29)",
          "Thsf_sup_C": "rgb(240,75,91)",
          "Thsf_re_C": "rgbs(239,75,91)",
          "Tcsf_sup_C": "rgb(63,192,194)",
          "Tcsf_re_C": "rgb(63,192,194)"}


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