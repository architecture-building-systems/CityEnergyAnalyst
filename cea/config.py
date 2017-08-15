"""
Manage configuration information for the CEA. See the cascading configuration files section in the documentation
for more information on configuration files.
"""
import os
import ConfigParser
import cea.databases

class Configuration(object):
    def __init__(self, scenario=None):
        """Read in configuration information for a scenario (or the default scenario)"""
        defaults = dict(os.environ)
        defaults['CEA.SCENARIO'] = str(scenario)
        defaults['CEA.DB'] = os.path.dirname(cea.databases.__file__)
        self._parser = ConfigParser.SafeConfigParser(defaults=defaults)
        files_found = self._parser.read(self._list_configuration_files(scenario))
        print("Configuration files: " + ', '.join(files_found))
        self.demand = DemandConfiguration(self._parser)
        self.photovoltaic = PhotovoltaicConfiguration(self._parser)

    @property
    def default_scenario(self):
        return self._parser.get('general', 'default-scenario')

    @property
    def weather(self):
        return self._parser.get('general', 'weather')

    def _list_configuration_files(self, scenario):
        """Return the list of configuration files to try and load for a given scenario. The list is given in order
        of importance, with items at the end of the files overriding files at the beginning of the list."""
        cascade = [
            os.path.join(os.path.dirname(__file__), 'default.config'),
            os.path.join(os.path.expanduser(r'~/cea.config')),
        ]
        if scenario:
            cascade.append(os.path.join(scenario, '..', 'project.config'))
            cascade.append(os.path.join(scenario, 'scenario.config'))
        return cascade


class DemandConfiguration(object):
    def __init__(self, parser):
        self._parser = parser

    @property
    def heating_season_start(self):
        return self._parser.get('demand', 'heating-season-start')

    @property
    def heating_season_end(self):
        return self._parser.get('demand', 'heating-season-end')

    @property
    def cooling_season_start(self):
        return self._parser.get('demand', 'cooling-season-start')

    @property
    def cooling_season_end(self):
        return self._parser.get('demand', 'cooling-season-end')


class PhotovoltaicConfiguration(object):
    def __init__(self, parser):
        self._parser = parser

    # site specific input
    @property
    def date_start(self):
        """format: yyyy-mm-dd"""
        return self._parser.get('photovoltaic', 'date-start')

    @property
    def type_PVpanel(self):
        """type of panels
        for PVT, please choose type_PVpanel = 'PV1', type_SCpanel = 'SC1'
        PV1: monocrystalline, PV2: poly, PV3: amorphous. please refer to supply system database.
        """
        return self._parser.get('photovoltaic', 'type-PVpanel')

    @property
    def type_SCpanel(self):
        """SC1: flat plat collectors, SC2: evacuated tubes"""
        return self._parser.get('photovoltaic', 'type-SCpanel')

    # installed locations
    @property
    def panel_on_roof(self):
        """flag for considering panels on roof"""
        return self._parser.getboolean('photovoltaic', 'panel-on-roof')

    @property
    def panel_on_wall(self):
        """flag for considering panels on wall"""
        return self._parser.getboolean('photovoltaic', 'panel-on-wall')

    @property
    def min_radiation(self):
        """filtering criteria: at least a minimum production of this % from the maximum in the area."""
        return self._parser.getfloat('photovoltaic', 'min-radiation')

    # panel spacing
    @property
    def solar_window_solstice(self):
        """desired hours of solar window on the solstice"""
        return self._parser.getint('photovoltaic', 'solar-window-solstice')

    @property
    def T_in_SC(self):
        """inlet temperature of solar collectors [C]"""
        return self._parser.getfloat('photovoltaic', 'T-in-SC')

    @property
    def T_in_PVT(self):
        """inlet temperature of PVT panels [C]"""
        return self._parser.getfloat('photovoltaic', 'T-in-PVT')

    @property
    def dpl(self):
        """pressure losses per length of pipe according to Solar District Heating Guidelines, [Pa/m]"""
        return self._parser.getfloat('photovoltaic', 'dpl')

    @property
    def fcr(self):
        """additional loss factor due to accessories"""
        return self._parser.getfloat('photovoltaic', 'fcr')

    @property
    def Ro(self):
        """water density [kg/m3]"""
        return self._parser.getfloat('photovoltaic', 'Ro')

    @property
    def eff_pumping(self):
        """pump efficiency"""
        return self._parser.getfloat('photovoltaic', 'eff-pumping')

    # solar collectors heat losses
    @property
    def k_msc_max(self):
        """linear heat transmittance coefficient of piping (2*pi*k/ln(Do/Di))) [W/mK]"""
        return self._parser.getfloat('photovoltaic', 'k-msc-max')

if __name__ == '__main__':
    config = Configuration(r'c:\reference-case-open\baseline')
    print config.demand.heating_season_start
    print config.default_scenario, os.path.exists(config.default_scenario)
    print config.weather, os.path.exists(config.weather)