

NAMING = {'Qhsf': 'final space heating',
          'Qcsf': 'final space cooling',
          'Qwwf': 'final hot water',
          'Ef': 'final electricity'}

COLOR =  {'Qhsf': "rgb(240,75,91)",
          'Qcsf': "rgb(63,192,194)",
          'Qwwf': "rgb(245, 131, 69)",
          'Ef': "rgb(126,199,143)",
          "Twwf_sup_C": "rgb(245, 131, 69)",
          "Twwf_re_C": "rgb(250, 177, 133)",
          "Thsf_sup_C": "rgb(240,75,91)",
          "Thsf_re_C": "rgb(255,209,29)",
          "Tcsf_sup_C": "rgb(63,192,194)",
          "Tcsf_re_C": "rgb(150,214,215)",
          'windows_east': "rgb(63,192,194)",
          'windows_west': "rgb(68,76,83)",
          'windows_south': "rgb(126,199,143)",
          'windows_north': "rgb(240,75,91)",
          'walls_east': "rgb(171,95,127)",
          'walls_west': "rgb(174,148,72)",
          'walls_north': "rgb(245, 131, 69)", ###
          'walls_south': "rgb(28, 117, 188)", ###
          'roofs_top': "rgb(255,209,29)"}


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