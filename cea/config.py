from __future__ import print_function

"""
Manage configuration information for the CEA. See the cascading configuration files section in the documentation
for more information on configuration files.
"""
import os
import ConfigParser


class Configuration(object):
    def __init__(self, config_file=None):
        """Read in the configuration file and configure the sections and parameters."""
        self._read_config_file(config_file)
        self._sections = {}

        ## ADD NEW PARAMETERS HERE
        self.add_section('general',
                         PathParameter('default-scenario'),
                         ChoiceParameter('region', ['CH', 'SIN']),
                         WeatherPathParameter('weather'),
                         BooleanParameter('multiprocessing'))

        self.add_section('data-helper',
                         ListParameter('archetypes'))

        self.add_section('demand-graphs',
                         ListParameter('analysis-fields'))

        self.add_section('embodied-energy',
                         IntegerParameter('year-to-calculate'))

        self.add_section('demand',
                         DateParameter('heating-season-start'),
                         DateParameter('heating-season-end'),
                         BooleanParameter('has-heating-season'),
                         DateParameter('cooling-season-start'),
                         DateParameter('cooling-season-end'),
                         BooleanParameter('has-cooling-season'),
                         BooleanParameter('use-dynamic-infiltration-calculation'))

        self.add_section('solar',
                         DateParameter('date-start'),
                         ChoiceParameter('type-pvpanel', ['PV1', 'PV2', 'PV3']),
                         ChoiceParameter('type-scpanel', ['SC1', 'SC2']),
                         BooleanParameter('panel-on-roof'),
                         BooleanParameter('panel-on-wall'),
                         RealParameter('min-radiation'),
                         IntegerParameter('solar-window-solstice'),
                         RealParameter('t-in-sc'),
                         RealParameter('t-in-pvt'),
                         RealParameter('dpl'),
                         RealParameter('fcr'),
                         RealParameter('ro'),
                         RealParameter('eff-pumping'),
                         RealParameter('k-msc-max'))

        self.add_section('radiation-daysim',
                         IntegerParameter('rad-n'),
                         StringParameter('rad-af'),
                         IntegerParameter('rad-ab'),
                         IntegerParameter('rad-ad'),
                         IntegerParameter('rad-as'),
                         IntegerParameter('rad-ar'),
                         RealParameter('rad-aa'),
                         IntegerParameter('rad-lr'),
                         RealParameter('rad-st'),
                         RealParameter('rad-sj'),
                         RealParameter('rad-lw'),
                         RealParameter('rad-dj'),
                         RealParameter('rad-ds'),
                         IntegerParameter('rad-dr'),
                         IntegerParameter('rad-dp'),
                         IntegerParameter('sensor-x-dim'),
                         IntegerParameter('sensor-y-dim'),
                         RealParameter('e-terrain'),
                         IntegerParameter('n-buildings-in-chunk'),
                         BooleanParameter('multiprocessing'),
                         IntegerParameter('zone-geometry'),
                         IntegerParameter('surrounding-geometry'),
                         BooleanParameter('consider-windows'),
                         BooleanParameter('consider-floors'))


        ## ADD NEW SECTIONS HERE

    def _read_config_file(self, config_file):
        """Read in the configuration information from the home folder (cea.config)"""
        if not config_file:
            config_file = [os.path.expanduser('~/cea.config'),
                           os.path.join(os.path.dirname(__file__), 'default.config')]
        self._config_file = config_file
        self.config_parser = ConfigParser.SafeConfigParser()
        # read from the user config file, with the default.config as a backup
        self.config_parser.read(config_file)

    def add_section(self, name, *parameters):
        section = Section(name=name, config=self)
        self._sections[name] = section
        for parameter in parameters:
            section.add_parameter(parameter)

    def __getattr__(self, attr):
        identifier = config_identifier(attr)
        if identifier in self._sections:
            return self._sections[identifier]
        else:
            # assume the default section [general]
            return getattr(self._sections['general'], identifier)

    def save(self):
        """Write this configuration to the scenario folder"""
        assert os.path.exists(self.scenario), "Can't save to scenario: %s" % self.scenario
        scenario_config = os.path.join(self.scenario, 'scenario.config')
        with open(scenario_config, 'w') as f:
            self._parser.write(f)


def config_identifier(python_identifier):
    """For vanity, keep keys and section names in the config file with dashes instead of underscores and all-lowercase"""
    return python_identifier.lower().replace('_', '-')

class Section(object):
    """Instances of ``Section`` describe a section in the configuration file."""
    def __init__(self, name, config):
        self._name = name
        self._config = config
        self._parameters = {}

    def __getattr__(self, attr):
        return self._parameters[config_identifier(attr)].read(config.config_parser, self._name)

    def add_parameter(self, parameter):
        """Add a new parameter to a section, using ``parameter_type`` to parse and unparse the values"""
        self._parameters[parameter.name] = parameter

class Parameter(object):
    def __init__(self, name):
        self.name = name

    def read(self, config_parser, section):
        """Read a value from a ``ConfigParser``"""
        return self.decode(config_parser.get(section, self.name))

    def write(self, config_parser, section, value):
        """Write a value to a ``ConfigParser``"""
        config_parser.set(section, self.name, self.encode(value))

    def encode(self, value):
        """Encode ``value`` to a string representation for writing to the configuration file"""
        return str(value)

    def decode(self, value):
        """Decode ``value`` to the type supported by this Parameter"""
        return value


class PathParameter(Parameter):
    pass

class WeatherPathParameter(Parameter):
    pass

class BooleanParameter(Parameter):
    """Read / write boolean parameters to the config file."""
    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}
    def encode(self, value):
        return 'true' if value else 'false'

    def decode(self, value):
        return self._boolean_states[value.lower()]

class IntegerParameter(Parameter):
    """Read / write integer parameters to the config file."""
    def encode(self, value):
        return str(int(value))

    def decode(self, value):
        return int(value)

class RealParameter(Parameter):
    """Read / write floating point parameters to the config file."""
    def __init__(self, name, decimal_places=2):
        self._decimal_places = decimal_places
        super(RealParameter, self).__init__(name)

    def encode(self, value):
        return format(value, ".%i" % self._decimal_places)

    def decode(self, value):
        return float(value)

class ListParameter(Parameter):
    """A parameter that is a list of whitespace-separated strings. An error is raised when writing
    strings that contain whitespace themselves."""
    def encode(self, value):
        strings = [str(s).strip() for s in value]
        for s in strings:
            assert len(s.split()) == 1, 'No whitespace allowed in values of ListParameter'
        return ' '.join(strings)

    def decode(self, value):
        return value.split()

class StringParameter(Parameter):
    pass

class DateParameter(Parameter):
    pass

class ChoiceParameter(Parameter):
    """A parameter that can only take on values from a specific set of values"""
    def __init__(self, name, choices):
        self._choices = set(choices)
        super(ChoiceParameter, self).__init__(name)

    def encode(self, value):
        assert str(value) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return str(value)

    def decode(self, value):
        assert str(value) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return str(value)

if __name__ == '__main__':
    config = Configuration()
    print(config.general.default_scenario)
    print(config.general.multiprocessing)
    print(config.demand.heating_season_start)
    print(config.default_scenario)
    print(config.weather)
