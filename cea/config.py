from __future__ import print_function

"""
Manage configuration information for the CEA. The Configuration class is built dynamically based on the type information
in ``default.config``.
"""
import os
import re
import json
import csv
import ConfigParser
import cea.inputlocator
import collections
import datetime

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
    def __init__(self, config_file=CEA_CONFIG):
        self.default_config = ConfigParser.SafeConfigParser()
        self.default_config.read(DEFAULT_CONFIG)
        self.user_config = ConfigParser.SafeConfigParser()
        self.user_config.read([DEFAULT_CONFIG, config_file])
        self.sections = collections.OrderedDict([(section_name, Section(section_name, self))
                                                 for section_name in self.default_config.sections()])

        # update cea.config with new options
        self.save(config_file)

    def __getattr__(self, item):
        """Return either a Section object or the value of a Parameter"""
        cid = config_identifier(item)
        if cid in self.sections:
            return self.sections[cid]
        elif cid in self.sections['general'].parameters:
            return self.sections['general'].parameters[cid].get()
        else:
            raise AttributeError("Section or Parameter not found: %s" % item)

    def __setattr__(self, key, value):
        """Set the value on a parameter in the general section"""
        if key in {'default_config', 'user_config', 'sections'}:
            # make sure the __init__ method doesn't trigger this
            return super(Configuration, self).__setattr__(key, value)

        cid = config_identifier(key)
        general_section = self.sections['general']
        if cid in general_section.parameters:
            return general_section.parameters[cid].set(value)
        else:
            return super(Configuration, self).__setattr__(key, value)

    def __getstate__(self):
        """when we pickle, we only really need to pickle the user_config"""
        import StringIO
        config_data = StringIO.StringIO()
        self.user_config.write(config_data)
        return config_data.getvalue()

    def __setstate__(self, state):
        """read in the user_config and re-initialize the state (this basically follows the __init__)"""
        import StringIO
        self.default_config = ConfigParser.SafeConfigParser()
        self.default_config.read(DEFAULT_CONFIG)
        self.user_config = ConfigParser.SafeConfigParser()
        self.user_config.readfp(StringIO.StringIO(state))
        self.sections = {section_name: Section(section_name, config=self)
                         for section_name in self.default_config.sections()}

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
        command_line_args = parse_command_line_args(args)

        for section, parameter in self.matching_parameters(option_list):
            if parameter.name in command_line_args:
                try:
                    parameter.set(
                        parameter.decode(
                            parameter.replace_references(
                                command_line_args[parameter.name])))
                except:
                    raise ValueError('ERROR setting %s:%s to %s' % (
                        section.name, parameter.name, command_line_args[parameter.name]))
                del command_line_args[parameter.name]
        assert len(command_line_args) == 0, 'Unexpected parameters: %s' % command_line_args

    def matching_parameters(self, option_list):
        """Return a tuple (Section, Parameter) for all parameters that match the parameters in the ``option_list``.
        ``option_list`` is a sequence of parameter names in the form ``section[:parameter]``
        if only a section is mentioned, all the parameters of that section are added. Otherwise, only the specified
        parameter is added to the resulting list.
        """
        for option in option_list:
            if ':' in option:
                section_name, parameter_name = option.split(':')
                section = self.sections[section_name]
                parameter = section.parameters[parameter_name]
                yield (section, parameter)
            else:
                section = self.sections[option]
                for parameter in section.parameters.values():
                    yield (section, parameter)

    def save(self, config_file=CEA_CONFIG):
        """Save the current configuration to a file. By default, the configuration is saved to the user configuration
        file (``~/cea.config``). If ``config_file`` is set to the default configuration file
        :py:data:`cea.config.DEFAULT_CONFIG`, then nothing is saved - this is to prevent overwriting the default
        configuration file."""
        config_file = os.path.normcase(os.path.normpath(os.path.abspath(config_file)))
        default_config = os.path.normcase(os.path.normpath(os.path.abspath(DEFAULT_CONFIG)))
        if config_file == default_config:
            # don't overwrite the default.config
            return

        parser = ConfigParser.SafeConfigParser()
        for section in self.sections.values():
            parser.add_section(section.name)
            for parameter in section.parameters.values():
                parser.set(section.name, parameter.name, self.user_config.get(section.name, parameter.name))
        with open(config_file, 'w') as f:
            parser.write(f)

    def __repr__(self):
        """Sometimes it would be nice to have a printable version of the config..."""
        return repr({s.name: {p.name: p for p in s.parameters.values} for s in self.sections.values()})


def parse_command_line_args(args):
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


def config_identifier(python_identifier):
    """For vanity, keep keys and section names in the config file with dashes instead of underscores and
    all-lowercase"""
    return python_identifier.lower().replace('_', '-')


class Section(object):
    """Instances of ``Section`` describe a section in the configuration file."""

    def __init__(self, name, config):
        """
        :param name: The name of the section (as it appears in the configuration file, all lowercase)
        :type name: str
        :param config: The Configuration instance this section belongs to
        :type config: Configuration
        """
        assert name == name.lower(), 'Section names must be lowercase'
        self.name = name
        self.config = config
        self.parameters = collections.OrderedDict([(pn, construct_parameter(pn, self, config))
                                                   for pn in config.default_config.options(self.name)
                                                   if not '.' in pn])

    def __getattr__(self, item):
        """Return the value of the parameter with that name."""
        cid = config_identifier(item)
        if cid in self.parameters:
            return self.parameters[cid].get()
        else:
            raise AttributeError("Parameter not found: %s" % item)

    def __setattr__(self, key, value):
        """Set the value on a parameter"""
        if key in {'name', 'config', 'parameters'}:
            # make sure the __init__ method doesn't trigger this
            return super(Section, self).__setattr__(key, value)

        cid = config_identifier(key)
        if cid in self.parameters:
            return self.parameters[cid].set(value)
        else:
            return super(Section, self).__setattr__(key, value)

    def __repr__(self):
        return "[%s](%s)" % (self.name, ", ".join(self.parameters.keys()))



def construct_parameter(parameter_name, section, config):
    """Create the approriate subtype of ``Parameter`` based on the .type option in the default.config file.
    :param parameter_name: The name of the parameter (as it appears in the configuration file, all lowercase)
    :type parameter_name: str
    :param section: The section this parameter is to be defined for
    :type section: Section
    :param config: The Configuration instance this parameter belongs to
    :type config: Configuration
    """
    assert parameter_name == parameter_name.lower(), 'Parameter names must be lowercase'
    try:
        parameter_type = config.default_config.get(section.name, parameter_name + '.type')
    except ConfigParser.NoOptionError:
        parameter_type = 'StringParameter'

    if not parameter_type in globals():
        section_name = section.name
        raise ValueError('Bad parameter type in default.config: %(section_name)s/%(parameter_name)s=%(parameter_type)s'
                         % locals())
    return globals()[parameter_type](parameter_name, section, config)


class Parameter(object):
    typename = 'Parameter'
    def __init__(self, name, section, config):
        """
        :param name: The name of the parameter (as it appears in the configuration file, all lowercase)
        :type name: str
        :param section: The section this parameter is to be defined for
        :type section: Section
        :param config: The Configuration instance this parameter belongs to
        :type config: Configuration
        """
        self.name = name
        self.section = section
        self.config = config
        try:
            self.help = config.default_config.get(section.name, self.name + ".help", raw=True)
        except ConfigParser.NoOptionError:
            self.help = "FIXME: Add help to %s:%s" % (section.name, self.name)
        try:
            self.category = config.default_config.get(section.name, self.name + ".category", raw=True)
        except ConfigParser.NoOptionError:
            self.category = None

        # give subclasses a chance to specialize their behavior
        self.initialize(config.default_config)

    def __repr__(self):
        return "<Parameter %s:%s=%s>" % (self.section.name, self.name, self.get())

    def initialize(self, parser):
        """
        Override this function to initialize a parameter with values as read from
        the default.config
        """

    def encode(self, value):
        """Encode ``value`` to a string representation for writing to the configuration file"""
        return str(value)

    def decode(self, value):
        """Decode ``value`` to the type supported by this Parameter"""
        return value

    def get(self):
        """Return the value from the config file"""
        encoded_value = self.config.user_config.get(self.section.name, self.name)
        encoded_value = self.replace_references(encoded_value)
        try:
            return self.decode(encoded_value)
        except ValueError as ex:
            raise ValueError('%s:%s - %s' % (self.section.name, self.name, ex.message))

    def get_raw(self):
        """Return the value from the config file, but without replacing references and also
        without decoding."""
        return self.config.user_config.get(self.section.name, self.name)

    def replace_references(self, encoded_value):
        # expand references (like ``{general:scenario}``)
        def lookup_config(matchobj):
            return self.config.sections[matchobj.group(1)].parameters[matchobj.group(2)].get()

        encoded_value = re.sub('{([a-z0-9-]+):([a-z0-9-]+)}', lookup_config, encoded_value)
        return encoded_value

    def set(self, value):
        encoded_value = self.encode(value)
        self.config.user_config.set(self.section.name, self.name, encoded_value)


class PathParameter(Parameter):
    """Describes a folder in the system"""
    typename = 'PathParameter'
    def initialize(self, parser):
        try:
            self._direction = parser.get(self.section.name, self.name + '.direction')
            if not self._direction in {'input', 'output'}:
                self._direction = 'input'
        except ConfigParser.NoOptionError:
            self._direction = 'input'

    def decode(self, value):
        """Always return a canonical path"""
        return os.path.normpath(os.path.abspath(value))


class FileParameter(Parameter):
    """Describes a file in the system."""
    typename = 'FileParameter'
    def initialize(self, parser):
        self._extensions = parser.get(self.section.name, self.name + '.extensions').split()
        try:
            self._direction = parser.get(self.section.name, self.name + '.direction')
            if not self._direction in {'input', 'output'}:
                self._direction = 'input'
        except ConfigParser.NoOptionError:
            self._direction = 'input'


class JsonParameter(Parameter):
    """A parameter that gets / sets JSON data (useful for dictionaries, lists etc.)"""
    typename = 'JsonParameter'
    def encode(self, value):
        return json.dumps(value)

    def decode(self, value):
        if value == '':
            return None
        return json.loads(value)


class WeatherPathParameter(Parameter):
    typename = 'WeatherPathParameter'
    def initialize(self, parser):
        self.locator = cea.inputlocator.InputLocator(None)

    def decode(self, value):
        if value in self.locator.get_weather_names():
            weather_path = self.locator.get_weather(value)
        elif os.path.exists(value) and value.endswith('.epw'):
            weather_path = value
        else:
            weather_path = self.locator.get_weather('Zug')
        return weather_path


class BooleanParameter(Parameter):
    """Read / write boolean parameters to the config file."""
    typename = 'BooleanParameter'
    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def encode(self, value):
        return 'true' if value else 'false'

    def decode(self, value):
        return self._boolean_states[value.lower()]


class IntegerParameter(Parameter):
    """Read / write integer parameters to the config file."""
    typename = 'IntegerParameter'

    def initialize(self, parser):
        try:
            self.nullable = parser.getboolean(self.section.name, self.name + '.nullable')
        except ConfigParser.NoOptionError:
            self.nullable = False

    def encode(self, value):
        if value is None:
            if self.nullable:
                return ''
            else:
                raise ValueError("Can't encode None for non-nullable IntegerParameter.")
        return str(value)

    def decode(self, value):
        try:
            return int(value)
        except ValueError:
            if self.nullable:
                return None
            else:
                raise ValueError("Can't decode value for non-nullable IntegerParameter.")


class RealParameter(Parameter):
    """Read / write floating point parameters to the config file."""
    typename = 'RealParameter'

    def initialize(self, parser):
        # allow user to override the amount of decimal places to use
        try:
            self._decimal_places = int(parser.get(self.section.name, self.name + '.decimal-places'))
        except ConfigParser.NoOptionError:
            self._decimal_places = 4

        try:
            self.nullable = parser.getboolean(self.section.name, self.name + '.nullable')
        except ConfigParser.NoOptionError:
            self.nullable = False

    def encode(self, value):
        if value is None:
            if self.nullable:
                return ''
            else:
                raise ValueError("Can't encode None for non-nullable RealParameter.")
        return format(value, ".%i" % self._decimal_places)

    def decode(self, value):
        try:
            return float(value)
        except ValueError:
            if self.nullable:
                return None
            else:
                raise ValueError("Can't decode value for non-nullable RealParameter.")

class ListParameter(Parameter):
    """A parameter that is a list of comma-separated strings. An error is raised when writing
    strings that contain commas themselves."""
    typename = 'ListParameter'

    def encode(self, value):
        if isinstance(value, basestring):
            # should be a list
            value = parse_string_to_list(value)
        strings = [str(s).strip() for s in value]
        for s in strings:
            assert not ',' in s, 'No commas allowed in values of ListParameter'
        return ', '.join(strings)

    def decode(self, value):
        return parse_string_to_list(value)


class SubfoldersParameter(ListParameter):
    """A list of subfolder names of a parent folder."""
    typename = 'SubfoldersParameter'

    def initialize(self, parser):
        # allow the parent option to be set
        self._parent_section, self._parent_option = parser.get(self.section.name,
                                                               self.name + '.parent').split(':')

    def decode(self, value):
        """Only return the folders that exist"""
        folders = parse_string_to_list(value)
        return [folder for folder in folders if folder in self.get_folders()]

    def get_folders(self):
        parent = self.config.sections[self._parent_section].parameters[self._parent_option].get()
        try:
            return [folder for folder in os.listdir(parent) if os.path.isdir(os.path.join(parent, folder))]
        except:
            # parent doesn't exist?
            return []


class StringParameter(Parameter):
    typename = 'StringParameter'


class DateParameter(Parameter):
    typename = 'DateParameter'

    def encode(self, value):
        return datetime.datetime.strftime(value, '%Y-%m-%d')

    def decode(self, value):
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            # try with system's locale
            return datetime.datetime.strptime(value, '%x')


class ChoiceParameter(Parameter):
    """A parameter that can only take on values from a specific set of values"""
    typename = 'ChoiceParameter'

    def initialize(self, parser):
        # when called for the first time, make sure there is a `.choices` parameter
        self._choices = parse_string_to_list(parser.get(self.section.name, self.name + '.choices'))

    def encode(self, value):
        assert str(value) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return str(value)

    def decode(self, value):
        assert str(value) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return str(value)


class MultiChoiceParameter(ChoiceParameter):
    """Like ChoiceParameter, but multiple values from the choices list can be used"""
    typename = 'MultiChoiceParameter'

    def encode(self, value):
        assert not isinstance(value, basestring)
        for choice in value:
            assert str(choice) in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return ', '.join(map(str, value))

    def decode(self, value):
        choices = parse_string_to_list(value)
        for choice in choices:
            assert choice in self._choices, 'Invalid parameter, choose from: %s' % self._choices
        return choices


def parse_string_to_list(line):
    """Parse a line in the csv format into a list of strings"""
    line = line.replace('\n', ' ')
    line = line.replace('\r', ' ')
    reader = csv.reader((line,))
    return [field.strip() for field in reader.next()]


def main():
    """Run some tests on the configuration module"""
    config = Configuration()
    print(config.general.scenario)
    print(config.general.multiprocessing)
    # print(config.demand.heating_season_start)
    print(config.scenario)
    print(config.weather)
    print(config.sensitivity_demand.samples_folder)
    print(config.heatmaps.file_to_analyze)
    # make sure the config can be pickled (for multiprocessing)
    config.scenario = r'C:\reference-case-zurich'
    import pickle
    config = pickle.loads(pickle.dumps(config))
    assert config.scenario == r'C:\reference-case-zurich'
    print('reference case: %s' % config.scenario)
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
    args = ['--reference-cases', 'zurich/baseline']
    config.apply_command_line_args(args, ['test'])
    print(config.test.reference_cases)
    print(config.scenario_plots.scenarios)


if __name__ == '__main__':
    main()