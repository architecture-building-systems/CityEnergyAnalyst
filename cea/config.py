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
        self._parser = ConfigParser.SafeConfigParser()
        self._read_default_config()
        self._copy_general()
        if not config_file:
            config_file = CEA_CONFIG
        if not os.path.exists(config_file):
            self.save(config_file)
        self._parser.read(config_file)
        normalize = lambda x: os.path.normpath(os.path.normcase(x))
        if normalize(config_file) != normalize(DEFAULT_CONFIG):
            self.save(config_file)

    def _read_default_config(self):
        """Read in the ``default.config`` file and build the parameters and sections with the appropriate types"""
        self._parser.readfp(open(DEFAULT_CONFIG))
        for section_name in self._parser.sections():
            section_class = create_section_type(self._parser, section_name)
            section = section_class(name=section_name, config=self)
            setattr(self, python_identifier(section_name), section)
            self._sections[section_name] = section



    def apply_command_line_args(self, args, option_list):
        """Apply the command line args as passed to cea.interfaces.cli.cli (the ``cea`` command). Each argument
        is assumed to follow this pattern: ``--PARAMETER-NAME VALUE``,  with ``PARAMETER-NAME`` being one of the options
        in the config file and ``VALUE`` being the value to override that option with."""
        if not len(args):
            # no arguments to apply
            return
        if args[0].endswith('.py'):
            # remove script name from list of arguments
            args = args[1:]
        command_line_args = self._parse_command_line_args(args)

        for section, parameter in self._matching_parameters(option_list):
            if parameter.name in command_line_args:
                try:
                    parameter.__set__(section, parameter.decode(command_line_args[parameter.name], self._parser))
                except:
                    print('ERROR setting %s:%s to %s' % (
                          section._name, parameter.name, command_line_args[parameter.name]))
                    raise
                del command_line_args[parameter.name]
        assert len(command_line_args) == 0, 'Unexpected parameters: %s' % command_line_args

    def _matching_parameters(self, option_list):
        """Return a tuple (Section, Parameter) for all parameters that match the parameters in the ``option_list``.
        ``option_list`` is a sequence of parameter names in the form ``section[:parameter]``
        if only a section is mentioned, all the parameters of that section are added. Otherwise, only the specified
        parameter is added to the resulting list.
        """
        for option in option_list:
            if ':' in option:
                section_name, parameter_name = option.split(':')
                section = self._sections[section_name]
                parameter = section._parameters[parameter_name]
                yield (section, parameter)
            else:
                section = self._sections[option]
                for parameter in section._parameters.values():
                    yield (section, parameter)



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
        """Copy parameters from the 'general' section to self for easy access"""
        general_section = self._sections['general']
        for parameter in general_section._parameters.values():
            setattr(self.__class__, python_identifier(parameter.name),
                    general_section._parameters[parameter.name])
            pass

    def save(self, config_file):
        """Save the sections and properties to a config file. This does not save all the type info
        in the default.config..."""
        parser = ConfigParser.SafeConfigParser()
        for section in self._sections.values():
            parser.add_section(section._name)
            for parameter in section._parameters.values():
                parser.set(section._name, parameter.name, parameter.encode(parameter.__get__(self), self._parser))
        with open(config_file, 'w') as f:
            parser.write(f)

    def __getstate__(self):
        """make sure we don't save the copies of the general section - we'll add them afterwards again"""
        import StringIO
        config_data = StringIO.StringIO()
        self._parser.write(config_data)
        return {'config_data': config_data.getvalue()}

    def __setstate__(self, state):
        """re-create the sections as attributes"""
        self._sections = {}
        self._parser = ConfigParser.SafeConfigParser()
        self._read_default_config()
        self._copy_general()

        # read in state data
        import StringIO
        config_data = StringIO.StringIO(state['config_data'])
        self._parser.readfp(config_data)



def config_identifier(python_identifier):
    """For vanity, keep keys and section names in the config file with dashes instead of underscores and
    all-lowercase"""
    return python_identifier.lower().replace('_', '-')


def python_identifier(config_identifier):
    """For vanity, keep keys and section names in the config file with dashes instead of underscores and
    all-lowercase, but use underscores for python identifiers"""
    return config_identifier.lower().replace('-', '_')


def create_section_type(parser, section_name):
    """Create a subclass of ``Section`` with properties for each parameter in the section"""
    section_class = type('Section_' + python_identifier(section_name), (Section,), {'_parameters': {}})
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
        setattr(section_class, python_identifier(parameter.name), parameter)
        section_class._parameters[parameter.name] = parameter

        section_class.__reduce__ = lambda self: (create_section_instance, (parser, section_name))
    return section_class


def create_section_instance(parser, section_name):
    """Return a new instance of the custom type for the section in the config file"""
    section_class = create_section_type(parser, section_name)
    section = section_class(section_name)
    return section

class Section(object):
    """Instances of ``Section`` describe a section in the configuration file."""
    def __init__(self, name, config):
        self._name = name
        self._config = config

class Parameter(object):
    def __init__(self, name, section, parser):
        self.name = name
        self.section = section
        self.initialize(parser)

    def initialize(self, parser):
        """
        Override this function to initialize a parameter with values as read from
        the default.config
        """

    def encode(self, value, parser):
        """Encode ``value`` to a string representation for writing to the configuration file"""
        return str(value)

    def decode(self, value, parser):
        """Decode ``value`` to the type supported by this Parameter"""
        return value

    def __get__(self, obj, objtype=None):
        """Make the property a "descriptor" so we can get/set values. It can either be on a Constructor or on a Section
        instance (depending if 'general' or not..."""
        if isinstance(obj, Configuration):
            parser = obj._parser
        else:
            parser = obj._config._parser

        return self.decode(parser.get(self.section, self.name), parser)


    def __set__(self, obj, value):
        if isinstance(obj, Configuration):
            parser = obj._parser
        else:
            parser = obj._config._parser

        parser.set(self.section, self.name, self.encode(value, parser))



class PathParameter(Parameter):
    pass


class RelativePathParameter(PathParameter):
    """A PathParameter that is relative to the scenario."""
    def initialize(self, parser):
        # allow the relative-to option to be set to something other than general:scenario
        try:
            self._relative_to_section, self._relative_to_option = parser.get(self.section,
                                                                             self.name + '.relative-to').split(':')
        except ConfigParser.NoOptionError:
            self._relative_to_section = 'general'
            self._relative_to_option = 'scenario'

    def decode(self, value, parser):
        """return a full path"""
        return os.path.normpath(os.path.join(parser.get(self._relative_to_section,
                                                             self._relative_to_option), value))


class WeatherPathParameter(Parameter):
    def decode(self, value, _):
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
    def encode(self, value, _):
        return 'true' if value else 'false'

    def decode(self, value, _):
        return self._boolean_states[value.lower()]


class IntegerParameter(Parameter):
    """Read / write integer parameters to the config file."""
    def encode(self, value, _):
        try:
            return str(int(value))
        except TypeError:
            return ''

    def decode(self, value, _):
        try:
            return int(value)
        except ValueError:
            return None

class RealParameter(Parameter):
    """Read / write floating point parameters to the config file."""
    def initialize(self, parser):
        # allow user to override the amount of decimal places to use
        try:
            self._decimal_places = int(parser.get(self.section, self.name + '.decimal-places'))
        except ConfigParser.NoOptionError:
            self._decimal_places = 4

    def encode(self, value, _):
        try:
            return format(value, ".%i" % self._decimal_places)
        except ValueError:
            return 'None'

    def decode(self, value, _):
        try:
            return float(value)
        except ValueError:
            return None

class ListParameter(Parameter):
    """A parameter that is a list of whitespace-separated strings. An error is raised when writing
    strings that contain whitespace themselves."""
    def encode(self, value, _):
        if isinstance(value, basestring):
            # should be a list
            value = value.split()
        strings = [str(s).strip() for s in value]
        for s in strings:
            assert len(s.split()) == 1, 'No whitespace allowed in values of ListParameter'
        return ' '.join(strings)

    def decode(self, value, _):
        return value.split()

class StringParameter(Parameter):
    pass

class DateParameter(Parameter):
    pass

class ChoiceParameter(Parameter):
    """A parameter that can only take on values from a specific set of values"""
    def initialize(self, parser):
        # when called for the first time, make sure there is a `.choices` parameter
        self._choices = parser.get(self.section, self.name + '.choices').split()

    def encode(self, value, _):
        assert str(value) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return str(value)

    def decode(self, value, _):
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
    print(config.heatmaps.file_to_analyze)

    # make sure the config can be pickled (for multiprocessing)
    import pickle
    pickle.loads(pickle.dumps(config))
    # config = pickle.loads(pickle.dumps(config))

    # test overriding
    args = ['--weather', 'Zurich',
            '--scenario', 'C:\\reference-case-test\\baseline']
    config.apply_command_line_args(args, ['general', 'sensitivity-demand'])

    # make sure the WeatherPathParameter resolves weather names...
    assert config.general.weather.endswith('Zurich.epw'), config.general.weather
    assert config.weather.endswith('Zurich.epw'), config.weather

    config.weather = 'Zug'
    assert config.general.weather.endswith('Zug.epw')
    print(config.general.weather)

    # test if pickling keeps state
    config.weather = 'Singapore'
    print(config.weather)
    config = pickle.loads(pickle.dumps(config))
    print(config.weather)

    # test changing scenario (and resulting RelativePathParameters)
    config.scenario = r'C:\reference-case-open'
    print(config.heatmaps.file_to_analyze)
