from __future__ import print_function

"""
Manage configuration information for the CEA. See the cascading configuration files section in the documentation
for more information on configuration files.
"""
import os
import tempfile
import ConfigParser
import cea.databases


class Configuration(object):
    def __init__(self, scenario=None):
        """Read in configuration information for a scenario (or the default scenario)"""
        self.scenario = scenario
        defaults = {'TEMP': tempfile.gettempdir(),
                    'CEA.SCENARIO': str(scenario),
                    'CEA.DB': os.path.dirname(cea.databases.__file__)}

        self._parser = ConfigParser.SafeConfigParser(defaults=defaults)
        self._parser = ConfigParser.SafeConfigParser(defaults=defaults)
        self._parser.read(self._list_configuration_files(scenario))
        self.demand = DemandConfiguration(self._parser)
        self.solar = PhotovoltaicConfiguration(self._parser)
        self.radiation_daysim = RadiationDaysimConfiguration(self._parser)

    @property
    def default_scenario(self):
        return self._parser.get('general', 'default-scenario')

    @property
    def weather(self):
        return self._parser.get('general', 'weather')

    @property
    def multiprocessing(self):
        return self._parser.getboolean('general', 'multiprocessing')

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

    @property
    def use_dynamic_infiltration(self):
        return self._parser.getboolean('demand', 'use-dynamic-infiltration')


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

class RadiationDaysimConfiguration(object):

    def __init__(self, parser):
        """
        :param parser: the SafeConfigParser used in the background
        :type parser: ConfigParser.SafeConfigParser
        """
        self._parser = parser

    @property
    def rad_parameters(self):
        return {
            'RAD_N': self._parser.getint('radiation-daysim', 'rad-n'),
            'RAD_AF': self._parser.get('radiation-daysim', 'rad-af'),
            'RAD_AB': self._parser.getint('radiation-daysim', 'rad-ab'),
            'RAD_AD': self._parser.getint('radiation-daysim', 'rad-ad'),
            'RAD_AS': self._parser.getint('radiation-daysim', 'rad-as'),
            'RAD_AR': self._parser.getint('radiation-daysim', 'rad-ar'),
            'RAD_AA': self._parser.getfloat('radiation-daysim', 'rad-aa'),
            'RAD_LR': self._parser.getint('radiation-daysim', 'rad-lr'),
            'RAD_ST': self._parser.getfloat('radiation-daysim', 'rad-st'),
            'RAD_SJ': self._parser.getfloat('radiation-daysim', 'rad-sj'),
            'RAD_LW': self._parser.getfloat('radiation-daysim', 'rad-lw'),
            'RAD_DJ': self._parser.getfloat('radiation-daysim', 'rad-dj'),
            'RAD_DS': self._parser.getfloat('radiation-daysim', 'rad-ds'),
            'RAD_DR': self._parser.getint('radiation-daysim', 'rad-dr'),
            'RAD_DP': self._parser.getint('radiation-daysim', 'rad-dp'),
        }

    @property
    def sensor_parameters(self):
        """Grid for the sensors, use 100 (maximum) if you want only one point per surface"""
        return {
            'X_DIM': self._parser.getint('radiation-daysim', 'sensor-x-dim'),
            'Y_DIM': self._parser.getint('radiation-daysim', 'sensor-y-dim'),
        }


    @property
    def terrain_parameters(self):
        """terrain parameters: e-terrain (reflection for the terrain)"""
        return {
            'e_terrain': self._parser.getfloat('radiation-daysim', 'e-terrain'),
        }

    @property
    def simulation_parameters(self):
        """simulation parameters:

        - n_build_in_chunk: min number of buildings for multiprocessing
        - multiprocessing: if set to true, run the process for chunk size ``n_build_in_chunk``
        """
        return {
            'n_build_in_chunk': self._parser.getint('radiation-daysim', 'n-buildings-in-chunk'),
            'multiprocessing': self._parser.getboolean('radiation-daysim', 'multiprocessing'),
            'run_all_buildings': self._parser.getboolean('radiation-daysim', 'run_all_buildings')
        }

    @property
    def simplification_parameters(self):
        """geometry simplification:
        - zone_geometry: level of simplification of the zone geometry
        - surrounding_geometry: level of simplification of the district geometry
        - consider_windows: boolean to consider or not windows in the geometry
        - consider_floors: boolean to consider or not floors in the geometry
        """
        return {
            'zone_geometry': self._parser.getint('radiation-daysim', 'zone-geometry'),
            'surrounding_geometry': self._parser.getint('radiation-daysim', 'surrounding-geometry'),
            'consider_windows': self._parser.getboolean('radiation-daysim', 'consider-windows'),
            'consider_floors': self._parser.getboolean('radiation-daysim', 'consider-floors'),
        }

if __name__ == '__main__':
    config = Configuration(r'c:\reference-case-open\baseline')
    print(config.demand.heating_season_start)
    print(config.default_scenario)
    print(config.weather)
