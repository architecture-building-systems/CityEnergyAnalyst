class ColorCodeCEA(object):
    def __init__(self):
        self.COLORS = {"red": "rgb(240,75,91)",
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
                       "purple_light'": "rgb(198,149,167)",
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

        self.COLOR_MATCH = {'Qhsf': "red",
                            'Qcsf': "blue",
                            'Qwwf': "orange",
                            'Ef': "green",
                            "Twwf_sup_C": "orange",
                            "Twwf_re_C": "orange_light",
                            "Thsf_sup_C": "red",
                            "Thsf_re_C": "yellow",
                            "Tcsf_sup_C": "blue",
                            "Tcsf_re_C": "blue_light",
                            'windows_east': "blue",
                            'windows_west': "grey",
                            'windows_south': "green",
                            'windows_north': "orange_light",
                            'walls_east': "purple",
                            'walls_west': "brown",
                            'walls_north': "orange",
                            'walls_south': "red",
                            'roofs_top': "yellow",
                            # solar technologies
                            'PV_walls_east_E': "purple",
                            'PV_walls_west_E': "brown",
                            'PV_walls_north_E': "orange",
                            'PV_walls_south_E': "red",
                            'PV_roofs_top_E': "yellow",
                            'PVT_walls_east_E': "purple",
                            'PVT_walls_west_E': "brown",
                            'PVT_walls_north_E': "orange",
                            'PVT_walls_south_E': "red",
                            'PVT_roofs_top_E': "yellow",
                            'PVT_walls_east_Q': "purple_light",
                            'PVT_walls_west_Q': "brown_light",
                            'PVT_walls_north_Q': "orange_light",
                            'PVT_walls_south_Q': "red_light",
                            'PVT_roofs_top_Q': "yellow_light",
                            'SC_walls_east_Q': "purple_light",
                            'SC_walls_west_Q': "brown_light",
                            'SC_walls_north_Q': "orange_light",
                            'SC_walls_south_Q': "red_light",
                            'SC_roofs_top_Q': "yellow_light",
                            }

    def get_color_rgb(self, field):
        try:
            match = self.COLOR_MATCH[field]
        except ValueError:
            print (
            "You are trying to put colors in one variable that is not recognized by CEA, check the list of variables,"
            "recognized in the file color_code.py")
        color_rgb = self.COLORS[match]
        return color_rgb
