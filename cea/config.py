from __future__ import print_function

"""
Manage configuration information for the CEA. See the cascading configuration files section in the documentation
for more information on configuration files.
"""
import os
import sys
import ConfigParser

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), 'default.config')
CEA_CONFIG = os.path.expanduser('~/cea.config')


class Configuration(object):
    def __init__(self, config_file=None):
        """
        Read in the configuration file and configure the sections and parameters.
        As a first step, the ``default.config`` is read to build the structure of the file.
        Next, the ``cea.config`` file is parsed to update user-specific parameter values.
        Finally apply any command line arguments.
        """
        self._sections = {}
        self._read_default_config()
        if not config_file:
            config_file = CEA_CONFIG
        self._read_cea_config(config_file)
        self._copy_general()


    def _read_default_config(self):
        parser = ConfigParser.SafeConfigParser()
        parser.read(DEFAULT_CONFIG)
        for section_name in parser.sections():
            section = Section(name=section_name)

            for parameter_name in parser.options(section_name):
                if '.' in parameter_name:
                    # ignore the 'parameter.type', 'parameter.help' etc. keys - they're not parameter names
                    continue
                try:
                    parameter_type = parser.get(section_name, parameter_name + '.type')
                except ConfigParser.NoOptionError:
                    parameter_type = 'StringParameter'
                assert parameter_type in globals(), 'Bad parameter type in default.config: %(section_name)s/%(parameter_name)s=%(parameter_type)s' % locals()
                parameter = globals()[parameter_type](parameter_name, section_name, parser)
                section.add_parameter(parameter, parser)
            setattr(self, python_identifier(section_name), section)
            self._sections[section_name] = section

    def _read_cea_config(self, config_file):
        parser = ConfigParser.SafeConfigParser()
        parser.readfp(open(DEFAULT_CONFIG))
        parser.read(config_file)
        for section in self._sections.values():
            for parameter in section._parameters.values():
                setattr(section, python_identifier(parameter.name), parameter.read(parser, section._name))
        for parameter in self._sections['general']._parameters.values():
            setattr(self, python_identifier(parameter.name), parameter.read(parser, 'general'))

    def apply_command_line_args(self, args):
        """Apply the command line args as passed to cea.interfaces.cli.cli (the ``cea`` command). Each argument
        is assumed to follow this pattern: ``--PARAMETER-NAME VALUE``,  with ``PARAMETER-NAME`` being one of the options
        in the config file and ``VALUE`` being the value to override that option with."""
        if not len(args):
            # no arguments to apply
            return
        if args[0].endswith('.py'):
            # remove script name from list of arguments
            args = args[1:]
        parameters = self._parse_command_line_args(args)
        for section in self._sections.values():
            for parameter_name in parameters.keys():
                if parameter_name in section._parameters:
                    setattr(section, python_identifier(parameter_name),
                            section._parameters[parameter_name].decode(parameters[parameter_name]))
                    del parameters[parameter_name]
        assert len(parameters) == 0, 'Unexpected parameters: %s' % parameters
        # copy [general] to self
        self._copy_general()

    def _parse_command_line_args(self, args):
        """Group the arguments into a dictionary: parameter-name -> value"""
        parameters = {}
        values = []
        argument_stack = list(args)
        while len(argument_stack):
            token = argument_stack.pop()
            if token.startswith('--'):
                parameter_name = token[2:]
                parameters[parameter_name] = ' '.join(reversed(values))
                values = []
            else:
                values.append(token)
        assert len(values) == 0, 'Bad arguments: %s' % args
        return parameters

    def _copy_general(self):
        """Copy parameters from the 'genera' section to self for easy access"""
        general_section = self._sections['general']
        for parameter in general_section._parameters.values():
            setattr(self, python_identifier(parameter.name),
                    getattr(general_section, python_identifier(parameter.name)))

    def _add_section(self, name, config_parser, *parameters):
        section = Section(name=name)
        self._sections[name] = section
        for parameter in parameters:
            section.add_parameter(parameter, config_parser=config_parser)
        setattr(self, python_identifier(name), section)
        if name == 'general':
            # treat [general] specially
            for parameter in parameters:
                setattr(self, python_identifier(parameter.name), getattr(section, python_identifier(parameter.name)))


def config_identifier(python_identifier):
    """For vanity, keep keys and section names in the config file with dashes instead of underscores and
    all-lowercase"""
    return python_identifier.lower().replace('_', '-')


def python_identifier(config_identifier):
    """For vanity, keep keys and section names in the config file with dashes instead of underscores and
    all-lowercase, but use underscores for python identifiers"""
    return config_identifier.lower().replace('-', '_')

class Section(object):
    """Instances of ``Section`` describe a section in the configuration file."""
    def __init__(self, name):
        self._name = name
        self._parameters = {}

    def add_parameter(self, parameter, config_parser):
        """Add a new parameter to a section, using ``parameter_type`` to parse and unparse the values"""
        self._parameters[parameter.name] = parameter
        setattr(self, python_identifier(parameter.name), parameter.read(config_parser, self._name))

class Parameter(object):
    def __init__(self, name, section, parser):
        self.name = name
        self.initialize(section, parser)

    def initialize(self, section, parser):
        """
        Override this function to initialize a parameter with values as read from
        the default.config
        """

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

class RelativePathParameter(Parameter):
    pass

class WeatherPathParameter(Parameter):
    def decode(self, value):
        import cea.inputlocator
        locator = cea.inputlocator.InputLocator(None)
        if value in locator.get_weather_names():
            weather_path = locator.get_weather(value)
        elif os.path.exists(value) and value.endswith('.epw'):
                weather_path = value
        else:
            weather_path = locator.get_weather('Zug')
        return weather_path

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
    def initialize(self, section, parser):
        # when called for the first time, make sure there is a `.choices` parameter
        try:
            self._decimal_places = int(parser.get(section, self.name + '.decimal-places'))
        except ConfigParser.NoOptionError:
            self._decimal_places = 4

    def encode(self, value):
        return format(value, ".%i" % self._decimal_places)

    def decode(self, value):
        try:
            return float(value)
        except ValueError:
            return None

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
    def initialize(self, section, parser):
        # when called for the first time, make sure there is a `.choices` parameter
        self._choices = parser.get(section, self.name + '.choices').split()

    def read(self, config_parser, section):
        return self.decode(config_parser.get(section, self.name))

    def encode(self, value):
        assert str(value) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return str(value)

    def decode(self, value):
        assert str(value) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return str(value)

if __name__ == '__main__':
    config = Configuration()
    print(config.general.scenario)
    print(config.general.multiprocessing)
    #print(config.demand.heating_season_start)
    print(config.scenario)
    print(config.weather)
    print(config.sensitivity_demand.samples_folder)

    # make sure the config can be pickled (for multiprocessing)
    import pickle
    pickle.loads(pickle.dumps(config))

    # test overriding
    args = ['--weather', 'Zurich',
            '--scenario', 'C:\\reference-case-test\\baseline']
    config.apply_command_line_args(args, ['general', 'sensitivity-demand'])

    # make sure the WeatherPathParameter resolves weather names...
    assert config.general.weather.endswith('Zurich.epw'), config.general.weather
    assert config.weather.endswith('Zurich.epw'), config.weather
