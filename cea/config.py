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
        self.scenario = scenario
        defaults = dict(os.environ)
        defaults['CEA.SCENARIO'] = str(scenario)
        defaults['CEA.DB'] = os.path.dirname(cea.databases.__file__)
        self._parser = ConfigParser.SafeConfigParser(defaults=defaults)
        files_found = self._parser.read(self._list_configuration_files(scenario))
        self.demand = DemandConfiguration(self._parser)
        self.photovoltaic = PhotovoltaicConfiguration(self._parser)

    @property
    def default_scenario(self):
        return self._parser.get('general', 'default-scenario')

    @property
    def weather(self):
        return self._parser.get('general', 'weather')

    @weather.setter
    def weather(self, value):
        self._parser.set('general', 'weather', value)

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

    def save(self):
        """Write this configuration to the scenario folder"""
        assert os.path.exists(self.scenario), "Can't save to scenario: %s" % self.scenario
        scenario_config = os.path.join(self.scenario, 'scenario.config')
        with open(scenario_config, 'w') as f:
            self._parser.write(f)


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
        return self._parser.get('solar', 'date-start')

    @date_start.setter
    def date_start(self, value):
        """format: yyy-mm-dd"""
        self._parser.set('solar', 'date-start', value)

    @property
    def type_PVpanel(self):
        """type of panels
        for PVT, please choose type_PVpanel = 'PV1', type_SCpanel = 'SC1'
        PV1: monocrystalline, PV2: poly, PV3: amorphous. please refer to supply system database.
        """
        return self._parser.get('solar', 'type-PVpanel')

    @type_PVpanel.setter
    def type_PVpanel(self, value):
        """type of panels
        for PVT, please choose type_PVpanel = 'PV1', type_SCpanel = 'SC1'
        PV1: monocrystalline, PV2: poly, PV3: amorphous. please refer to supply system database.
        """
        assert value in {'PV1', 'PV2', 'PV3'}, 'invalid PV panel type: %s' % value
        self._parser.set('solar', 'type-PVpanel', value)

    @property
    def type_SCpanel(self):
        """SC1: flat plat collectors, SC2: evacuated tubes"""
        return self._parser.get('solar', 'type-SCpanel')

    @type_SCpanel.setter
    def type_SCpanel(self, value):
        """SC1: flat plat collectors, SC2: evacuated tubes"""
        assert value in {'SC1', 'SC2'}
        self._parser.set('solar', 'type-SCpanel', value)

    # installed locations
    @property
    def panel_on_roof(self):
        """flag for considering panels on roof"""
        return self._parser.getboolean('solar', 'panel-on-roof')

    @panel_on_roof.setter
    def panel_on_roof(self, value):
        """flag for considering panels on roof"""
        self._parser.set('solar', 'panel-on-roof', 'yes' if value else 'no')

    @property
    def panel_on_wall(self):
        """flag for considering panels on wall"""
        return self._parser.getboolean('solar', 'panel-on-wall')

    @panel_on_wall.setter
    def panel_on_wall(self, value):
        """flag for considering panels on wall"""
        self._parser.set('solar', 'panel-on-wall', 'yes' if value else 'no')

    @property
    def min_radiation(self):
        """filtering criteria: at least a minimum production of this % from the maximum in the area."""
        return self._parser.getfloat('solar', 'min-radiation')

    @min_radiation.setter
    def min_radiation(self, value):
        """filtering criteria: at least a minimum production of this % from the maximum in the area."""
        self._parser.set('solar', 'min-radiation', '%.4f' % value)

    # panel spacing
    @property
    def solar_window_solstice(self):
        """desired hours of solar window on the solstice"""
        return self._parser.getint('solar', 'solar-window-solstice')

    @solar_window_solstice.setter
    def solar_window_solstice(self, value):
        """desired hours of solar window on the solstice"""
        self._parser.set('solar', 'solar-window-solstice', '%i' % value)

    @property
    def T_in_SC(self):
        """inlet temperature of solar collectors [C]"""
        return self._parser.getfloat('solar', 'T-in-SC')

    @T_in_SC.setter
    def T_in_SC(self, value):
        """inlet temperature of solar collectors [C]"""
        self._parser.set('solar', 'T-in-SC', value)

    @property
    def T_in_PVT(self):
        """inlet temperature of PVT panels [C]"""
        return self._parser.getfloat('solar', 'T-in-PVT')

    @T_in_PVT.setter
    def T_in_PVT(self, value):
        """inlet temperature of PVT panels [C]"""
        self._parser.set('solar', 'T-in-PVT', value)

    @property
    def dpl(self):
        """pressure losses per length of pipe according to Solar District Heating Guidelines, [Pa/m]"""
        return self._parser.getfloat('solar', 'dpl')

    @property
    def fcr(self):
        """additional loss factor due to accessories"""
        return self._parser.getfloat('solar', 'fcr')

    @property
    def Ro(self):
        """water density [kg/m3]"""
        return self._parser.getfloat('solar', 'Ro')

    @property
    def eff_pumping(self):
        """pump efficiency"""
        return self._parser.getfloat('solar', 'eff-pumping')

    # solar collectors heat losses
    @property
    def k_msc_max(self):
        """linear heat transmittance coefficient of piping (2*pi*k/ln(Do/Di))) [W/mK]"""
        return self._parser.getfloat('solar', 'k-msc-max')

if __name__ == '__main__':
    config = Configuration(r'c:\reference-case-open\baseline')
    print config.demand.heating_season_start
    print config.default_scenario, os.path.exists(config.default_scenario)
    print config.weather, os.path.exists(config.weather)