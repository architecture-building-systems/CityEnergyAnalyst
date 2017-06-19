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
        defaults = dict() # dict(os.environ)
        defaults['CEA.SCENARIO'] = str(scenario)
        defaults['CEA.DB'] = os.path.dirname(cea.databases.__file__)
        self._parser = ConfigParser.SafeConfigParser(defaults=defaults)
        self._files_found = self._parser.read(self._list_configuration_files(scenario))
        self.demand = DemandConfiguration(self._parser)

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




if __name__ == '__main__':
    config = Configuration(r'c:\reference-case-open\baseline')
    print config.demand.heating_season_start
    print config.default_scenario, os.path.exists(config.default_scenario)
    print config.weather, os.path.exists(config.weather)