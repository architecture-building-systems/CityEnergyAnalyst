"""
Manage configuration information for the CEA. The Configuration class is built dynamically based on the type information
in ``default.config``.
"""

import collections
import configparser
import datetime
import glob
import json
import os
import re
import tempfile

import cea.inputlocator
from cea.utilities import unique

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), 'default.config')
CEA_CONFIG = os.path.expanduser('~/cea.config')


class Configuration(object):
    def __init__(self, config_file=CEA_CONFIG):
        self.restricted_to = None
        self.default_config = configparser.ConfigParser()
        self.default_config.read(DEFAULT_CONFIG)
        self.user_config = configparser.ConfigParser()
        self.user_config.read([DEFAULT_CONFIG, config_file])

        import cea.plugin
        cea.plugin.add_plugins(self.default_config, self.user_config)

        self.sections = self._init_sections()

        # Only write user config if it does not exist
        if not os.path.exists(CEA_CONFIG):
            self.save(config_file)

    def __getattr__(self, item):
        """Return either a Section object or the value of a Parameter"""
        cid = config_identifier(item)
        if cid in self.sections:
            return self.sections[cid]
        elif cid in self.sections['general'].parameters:
            return getattr(self.sections['general'], cid)
        else:
            raise AttributeError("Section or Parameter not found: %s" % item)

    def __setattr__(self, key, value):
        """Set the value on a parameter in the general section"""
        if key in {'default_config', 'user_config', 'sections', 'restricted_to'}:
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
        import io
        config_data = io.StringIO()
        self.user_config.write(config_data)
        return config_data.getvalue()

    def __setstate__(self, state):
        """read in the user_config and re-initialize the state (this basically follows the __init__)"""
        import io
        import cea.plugin

        self.restricted_to = None
        self.default_config = configparser.ConfigParser()
        self.default_config.read(DEFAULT_CONFIG)
        self.user_config = configparser.ConfigParser()
        self.user_config.read_file(io.StringIO(state))

        cea.plugin.add_plugins(self.default_config, self.user_config)

        self.sections = {section_name: Section(section_name, config=self)
                         for section_name in self.default_config.sections()}

    def _init_sections(self):
        return collections.OrderedDict([(section_name, Section(section_name, self))
                                        for section_name in self.default_config.sections()])

    def restrict_to(self, option_list):
        """
        Restrict the config object to only allowing parameters as defined in the ``option_list`` parameter.
        `option_list` is a list of strings of the form `section` or `section:parameter` as used in the ``scripts.yml``
        file for the ``parameters`` attribute of a script.

        The purpose of this is to ensure that scripts don't use parameters that are not specified as options to the
        scripts. This only solves half of the possible issues with :py:class:`cea.config.Configuration`: the other is
        that a script creates it's own config file somewhere down the line. This is hard to check anyway.
        """
        self.restricted_to = [p.fqname for s, p in self.matching_parameters(option_list)]
        self.restricted_to.append("general:plugins")
        if 'general:scenario' in self.restricted_to:
            # since general:scenario is forced to be "{general:project}/{general:scenario-name}",
            # allow those two too
            self.restricted_to.append('general:project')
            self.restricted_to.append('general:scenario-name')

    def ignore_restrictions(self):
        """Create a ``with`` block where the config file restrictions are not kept. Usage::


            with config.ignore_restrictions():
                config.my_section.my_property = value

        .. note: this will produce a warning in the output.
        """

        class RestrictionsIgnorer(object):
            def __init__(self, config):
                self.config = config
                self.old_restrictions = None

            def __enter__(self):
                # print("WARNING: Ignoring config file restrictions. Consider refactoring the code.")
                self.old_restrictions = self.config.restricted_to
                self.config.restricted_to = None

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.config.restricted_to = self.old_restrictions

        return RestrictionsIgnorer(self)

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
                    import traceback;
                    traceback.print_exc()
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
                try:
                    parameter = section.parameters[parameter_name]
                except KeyError:
                    raise KeyError('Invalid option in option_list: %s' % option)
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

        parser = configparser.ConfigParser()
        for section in self.sections.values():
            parser.add_section(section.name)
            for parameter in section.parameters.values():
                parser.set(section.name, parameter.name, self.user_config.get(section.name, parameter.name))
        with open(config_file, 'w') as f:
            parser.write(f)

    def get_number_of_processes(self):
        """
        Returns the number of processes to use for multiprocessing.
        :param config: Configuration file.
        :return number_of_processes: Number of processes to use.
        """
        if self.multiprocessing:
            import multiprocessing
            number_of_processes = multiprocessing.cpu_count() - self.number_of_CPUs_to_keep_free
            return max(1, number_of_processes)  # ensure that at least one process is being used
        else:
            return 1

    def get(self, fqname):
        """Given a string of the form "section:parameter", return the value of that parameter"""
        return self.get_parameter(fqname).get()

    def get_parameter(self, fqname):
        """Given a string of the form "section:parameter", return the parameter object

        :rtype: cea.config.Parameter
        """
        section, parameter = fqname.split(':')
        try:
            return self.sections[section].parameters[parameter]
        except KeyError:
            raise KeyError(fqname)

    def refresh_plugins(self):
        import cea.plugin
        cea.plugin.add_plugins(self.default_config, self.user_config)
        self.sections = self._init_sections()

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
        self.parameters = collections.OrderedDict([(pn.lower(), construct_parameter(pn.lower(), self, config))
                                                   for pn in config.default_config.options(self.name)
                                                   if not '.' in pn])

    def __getattr__(self, item):
        """Return the value of the parameter with that name."""
        cid = config_identifier(item)
        if cid in self.parameters:
            if not self.config.restricted_to is None and not self.parameters[cid].fqname in self.config.restricted_to:
                raise AttributeError(
                    "Parameter not configured to work with this script: {%s}" % self.parameters[cid].fqname)
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
            if not self.config.restricted_to is None and not self.parameters[cid].fqname in self.config.restricted_to:
                raise AttributeError(
                    "Parameter not configured to work with this script: {%s}" % self.parameters[cid].fqname)
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
    assert parameter_name == parameter_name.lower(), 'Parameter names must be lowercase: {}:{}'.format(parameter_name,
                                                                                                       section.name)
    try:
        parameter_type = config.default_config.get(section.name, parameter_name + '.type')
    except configparser.NoOptionError:
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
        self.fqname = '%s:%s' % (section.name, self.name)
        self.config = config
        try:
            self.help = config.default_config.get(section.name, self.name + ".help", raw=True)
        except configparser.NoOptionError:
            self.help = "FIXME: Add help to %s:%s" % (section.name, self.name)
        try:
            self.category = config.default_config.get(section.name, self.name + ".category", raw=True)
        except configparser.NoOptionError:
            self.category = None

        # give subclasses a chance to specialize their behavior
        self.initialize(config.default_config)

    @property
    def default(self):
        return self.decode(self.config.default_config.get(self.section.name, self.name))

    def __repr__(self):
        return "<Parameter %s:%s=%s>" % (self.section.name, self.name, self.get())

    @property
    def py_name(self):
        return self.name.replace('-', '_')

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
        encoded_value = self.get_raw()
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
            return self.config.sections[matchobj.group(1)].parameters[matchobj.group(2)].get_raw()

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
        except configparser.NoOptionError:
            self._direction = 'input'

    def decode(self, value):
        """Always return a canonical path"""
        return str(os.path.normpath(os.path.abspath(os.path.expanduser(value))))


class FileParameter(Parameter):
    """Describes a file in the system."""
    typename = 'FileParameter'

    def initialize(self, parser):
        self._extensions = parser.get(self.section.name, self.name + '.extensions').split()
        try:
            self._direction = parser.get(self.section.name, self.name + '.direction')
            if not self._direction in {'input', 'output'}:
                self._direction = 'input'
        except configparser.NoOptionError:
            self._direction = 'input'

        try:
            self.nullable = parser.getboolean(self.section.name, self.name + '.nullable')
        except configparser.NoOptionError:
            self.nullable = False

    def encode(self, value):
        if value is None:
            if self.nullable:
                return ''
            else:
                raise ValueError("Can't encode None for non-nullable FileParameter %s." % self.name)
        return str(value)

    def decode(self, value):
        _KEYCRE = re.compile(r"\{([^}]+)\}")
        if not value and not self.nullable:
            raise ValueError("Can't decode value for non-nullable FileParameter %s." % self.name)
        elif _KEYCRE.match(value):
            return _KEYCRE.sub(lambda match: self.config.get(match.group(1)), value)
        else:
            return value


class ResumeFileParameter(FileParameter):
    """Path to the workflow:resume-file - this is generally ${TEMP}/resume-workflow.yml. Makes sure it is writeable"""
    typename = "ResumeFileParameter"

    def encode(self, value):
        return self.check_path(str(value))

    def check_path(self, path):
        """Make sure I can read/write that file"""
        if not path:
            path = os.path.join(tempfile.gettempdir(), "resume-workflow.yml")
        try:
            if os.path.exists(path):
                # make sure we can write to this file
                with open(path, "r") as fp:
                    contents = fp.read()
            else:
                contents = json.dumps(dict())

            with open(path, "w") as fp:
                fp.write(contents)

        except IOError:
            # let's just assume we can always write to the temp folder...
            path = os.path.join(tempfile.gettempdir(), "resume-workflow.yml")
        return path

    def decode(self, value):
        return self.check_path(str(value))


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
        self._locator = None  # cache the InputLocator in case we need it again as they can be expensive to create
        self._extensions = ['epw']

    @property
    def locator(self):
        if self._locator is None:
            self._locator = cea.inputlocator.InputLocator(None, [])
        return self._locator

    def decode(self, value):
        if value == '':
            return ''
        elif value in self.locator.get_weather_names():
            weather_path = self.locator.get_weather(value)
        elif os.path.exists(value) and value.endswith('.epw'):
            weather_path = value
        elif any(w.lower().startswith(value.lower()) for w in self.locator.get_weather_names()) and value.strip():
            # allow using shortcuts
            weather_path = self.locator.get_weather(
                [w for w in self.locator.get_weather_names() if w.lower().startswith(value.lower())][0])
        else:
            raise cea.ConfigError("Invalid weather path: {}".format(value))
        return weather_path

    @property
    def default(self):
        """override base default, since in decode we've banned empty weather file parameters"""
        return ""


class WorkflowParameter(Parameter):
    typename = "WorkflowParameter"
    workflows_path = os.path.join(os.path.dirname(__file__), "workflows")
    examples = {}
    for w in os.listdir(workflows_path):
        example_name = os.path.splitext(w)[0].replace("_", "-")
        example_path = os.path.join(workflows_path, w)
        examples[example_name] = example_path

    def decode(self, value):
        if value in self.examples:
            return self.examples[value]
        elif os.path.exists(value) and value.endswith(".yml"):
            return value
        else:
            print("ERROR: Workflow not found: {workflow} - using {default}".format(
                workflow=value, default=self.examples[next(iter(self.examples.keys()))]))
            return self.examples[next(iter(self.examples.keys()))]


class BooleanParameter(Parameter):
    """Read / write boolean parameters to the config file."""
    typename = 'BooleanParameter'
    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def encode(self, value):
        return 'true' if value else 'false'

    def decode(self, value):
        return self._boolean_states[str(value).lower()]


class IntegerParameter(Parameter):
    """Read / write integer parameters to the config file."""
    typename = 'IntegerParameter'

    def initialize(self, parser):
        try:
            self.nullable = parser.getboolean(self.section.name, self.name + '.nullable')
        except configparser.NoOptionError:
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
        except configparser.NoOptionError:
            self._decimal_places = 4

        try:
            self.nullable = parser.getboolean(self.section.name, self.name + '.nullable')
        except configparser.NoOptionError:
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
        if isinstance(value, str):
            # should be a list
            value = parse_string_to_list(value)
        strings = [str(s).strip() for s in value]
        for s in strings:
            assert ',' not in s, 'No commas allowed in values of ListParameter %s (value to encode: %s)' % (
                self.fqname, repr(value))
        return ', '.join(strings)

    def decode(self, value):
        return parse_string_to_list(value)


class PluginListParameter(ListParameter):
    """A list of cea.plugin.Plugin instances"""
    typename = "PluginListParameter"

    def set(self, value):
        super(PluginListParameter, self).set(value)
        self.config.refresh_plugins()

    def encode(self, list_of_plugins):
        """Make sure we don't duplicate any of the plugins"""
        unique_plugins = unique(list_of_plugins)
        return super(PluginListParameter, self).encode(unique_plugins)

    def decode(self, value):
        from cea.plugin import instantiate_plugin
        plugin_fqnames = unique(parse_string_to_list(value))
        plugins = [instantiate_plugin(plugin_fqname) for plugin_fqname in plugin_fqnames]
        return [plugin for plugin in plugins if plugin is not None]


class SubfoldersParameter(ListParameter):
    """A list of subfolder names of a parent folder."""
    typename = 'SubfoldersParameter'

    def initialize(self, parser):
        # allow the parent option to be set
        self._parent = parser.get(self.section.name, self.name + '.parent')

    def decode(self, value):
        """Only return the folders that exist"""
        folders = parse_string_to_list(value)
        return [folder for folder in folders if folder in self.get_folders()]

    def get_folders(self):
        parent = self.replace_references(self._parent)
        try:
            return [folder for folder in os.listdir(parent) if os.path.isdir(os.path.join(parent, folder))]
        except:
            # parent doesn't exist?
            return []


class StringParameter(Parameter):
    typename = 'StringParameter'


class OptimizationIndividualListParameter(ListParameter):
    typename = 'OptimizationIndividualListParameter'

    def initialize(self, parser):
        # allow the parent option to be set
        self._project = parser.get(self.section.name, self.name + '.project')

    def get_folders(self, project=None):
        if not project:
            project = self.replace_references(self._project)
        try:
            return [folder for folder in os.listdir(project) if os.path.isdir(os.path.join(project, folder))]
        except:
            # project doesn't exist?
            return []


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
        # when called for the first time, make sure there is a `._choices` parameter
        self._choices = parse_string_to_list(parser.get(self.section.name, self.name + '.choices'))

    def encode(self, value):
        assert str(
            value) in self._choices, 'Invalid parameter value {value} for {fqname}, choose from: {choices}'.format(
            value=value,
            fqname=self.fqname,
            choices=', '.join(self._choices)
        )
        return str(value)

    def decode(self, value):
        if str(value) in self._choices:
            return str(value)
        else:
            assert self._choices, 'No choices for {fqname} to decode {value}'.format(fqname=self.fqname, value=value)
            return self._choices[0]


class DatabasePathParameter(Parameter):
    """A parameter that can either be set to a region-specific CEA Database (e.g. CH or SG) or to a user-defined
    folder that has the same structure."""
    typename = "DatabasePathParameter"

    def initialize(self, parser):
        self.locator = cea.inputlocator.InputLocator(None, [])
        self._choices = {p: os.path.join(self.locator.db_path, p) for p in os.listdir(self.locator.db_path)
                         if os.path.isdir(os.path.join(self.locator.db_path, p)) and p != 'weather'}

    def encode(self, value):
        return str(value)

    def decode(self, value):
        if value == '':
            return ''
        # Assume value is CH or SG
        if value in self._choices.keys():
            database_path = self._choices[value]
        # Assume value is a path
        elif os.path.exists(value) and os.path.isdir(value) and self.is_valid_template(value):
            database_path = value
        else:
            raise cea.ConfigError("Invalid database path: {}".format(value))
        return database_path

    @property
    def default(self):
        """override base default, since in decode we've banned empty parameter"""
        return ""

    def is_valid_template(self, path):
        """True, if the path is a valid template path - containing the same excel files as the standard regions."""
        default_template = os.path.join(self.locator.db_path, self.default)
        for folder in os.listdir(default_template):
            if not os.path.isdir(os.path.join(default_template, folder)):
                continue
            for file in os.listdir(os.path.join(default_template, folder)):
                default_file_path = os.path.join(default_template, folder, file)
                if not os.path.isfile(default_file_path):
                    continue
                if not os.path.splitext(default_file_path)[1] in {'.xls', '.xlsx'}:
                    # we're only interested in the excel files
                    continue
                template_file_path = os.path.join(path, folder, file)
                if not os.path.exists(template_file_path):
                    print("Invalid user-specified region template - file not found: {template_file_path}".format(
                        template_file_path=template_file_path))
                    return False
        return True


class PlantNodeParameter(ChoiceParameter):
    """A parameter that refers to valid PLANT nodes of a thermal-network"""
    typename = 'PlantNodeParameter'

    def initialize(self, parser):
        self.network_name_fqn = parser.get(self.section.name, self.name + '.network-name')
        self.network_type_fqn = parser.get(self.section.name, self.name + '.network-type')

    @property
    def _choices(self):
        locator = cea.inputlocator.InputLocator(scenario=self.config.scenario, plugins=[])
        network_type = self.config.get(self.network_type_fqn)
        network_name = self.config.get(self.network_name_fqn)
        return locator.get_plant_nodes(network_type, network_name)

    def encode(self, value):
        """Allow encoding None, because not all scenarios have a thermal network"""
        if value is None:
            return ""
        elif not self._choices:
            print('No plant nodes can be found, ignoring `{value}`'.format(value=value))
            return ""
        elif value not in self._choices:
            first_choice = self._choices[0]
            print('Plant node `{value}` not found. Using {first_choice}'.format(value=value, first_choice=first_choice))
            return str(first_choice)
        else:
            return super(PlantNodeParameter, self).encode(value)

    def decode(self, value):
        if str(value) in self._choices:
            return str(value)
        elif self._choices:
            return self._choices[0]
        else:
            return None


class ScenarioNameParameter(ChoiceParameter):
    """A parameter that can be set to a scenario-name"""
    typename = 'ScenarioNameParameter'

    def initialize(self, parser):
        pass

    def encode(self, value):
        """Make sure the scenario folder exists"""
        if value == '':
            raise ValueError('scenario-name cannot be empty')
        elif self._choices and value not in self._choices:
            print('WARNING: Scenario "{value}" does not exist. Valid choices: {choices}'
                  .format(value=value, choices=','.join(self._choices)))
        return str(value)

    def decode(self, value):
        # allow scenario name to be non-existing folder when reading from config file...
        return str(value)

    @property
    def _choices(self):
        return get_scenarios_list(self.config.project)


class ScenarioParameter(Parameter):
    """This parameter type is special in that it is derived from two other parameters (project, scenario-name)"""

    typename = 'ScenarioParameter'

    def get_raw(self):
        return "{general:project}/{general:scenario-name}"

    def set(self, value):
        """Update the {general:project} and {general:scenario-name} parameters"""
        project, scenario_name = os.path.split(value)
        self.config.project = project
        self.config.scenario_name = scenario_name

    def decode(self, value):
        """Make sure the path is nicely formatted"""
        return os.path.normpath(value)


class MultiChoiceParameter(ChoiceParameter):
    """Like ChoiceParameter, but multiple values from the choices list can be used"""
    typename = 'MultiChoiceParameter'

    def initialize(self, parser):
        super().initialize(parser)

    @property
    def default(self):
        _default = self.config.default_config.get(self.section.name, self.name)
        if _default == '':
            return []
        return self.decode(_default)

    # Does not make sense for MultiChoiceParameter to be null, there should be at least one choice
    # @property
    # def nullable(self):
    #     try:
    #         return self.config.default_config.getboolean(self.section.name, self.name + '.nullable')
    #     except configparser.NoOptionError:
    #         return False

    def get(self):
        """Return the value from the config file"""
        encoded_value = self.get_raw()
        encoded_value = self.replace_references(encoded_value)

        try:
            return self.decode(encoded_value)
        except ValueError as ex:
            raise ValueError('%s:%s - %s' % (self.section.name, self.name, ex.message))

    def set(self, value):
        encoded_value = self.encode(value)
        self.config.user_config.set(self.section.name, self.name, encoded_value)

    def encode(self, value):
        assert not isinstance(value, str), "Bad value for encode of parameter {pname}".format(pname=self.name)
        for choice in value:
            assert str(choice) in self._choices, 'Invalid parameter value %s for %s, choose from: %s' % (
                value, self.name, self._choices)
        return ', '.join(map(str, value))

    def decode(self, value):
        if value == '':
            return self._choices
        choices = parse_string_to_list(value)
        return [choice for choice in choices if choice in self._choices]


class SingleBuildingParameter(ChoiceParameter):
    """A (single) building in the zone"""
    typename = 'SingleBuildingParameter'

    def initialize(self, parser):
        # skip the default ChoiceParameter initialization of _choices
        pass

    @property
    def _choices(self):
        # set the `._choices` attribute to the list buildings in the project
        locator = cea.inputlocator.InputLocator(self.config.scenario, plugins=[])
        building_names = locator.get_zone_building_names()
        if not building_names:
            raise cea.ConfigError("Either no buildings in zone or no zone geometry found.")
        return building_names

    def encode(self, value):
        if not str(value) in self._choices:
            return self._choices[0]
        return str(value)


class UseTypeRatioParameter(ListParameter):
    """A list of use-type names and ratios"""
    typename = 'UseTypeRatioParameter'


class GenerationParameter(ChoiceParameter):
    """A (single) building in the zone"""
    typename = 'GenerationParameter'

    def initialize(self, parser):
        # skip the default ChoiceParameter initialization of _choices
        pass

    @property
    def _choices(self):
        import glob
        # set the `._choices` attribute to the list buildings in the project
        locator = cea.inputlocator.InputLocator(self.config.scenario, plugins=[])
        checkpoints = glob.glob(os.path.join(locator.get_optimization_master_results_folder(), "*.json"))
        interations = []
        for checkpoint in checkpoints:
            with open(checkpoint, 'rb') as f:
                data_checkpoint = json.load(f)
                interations.extend(data_checkpoint['generation_to_show'])
        unique_iterations = list(set(interations))
        unique_iterations = [str(x) for x in unique_iterations]
        return unique_iterations

    def encode(self, value):
        if str(value) in self._choices:
            return str(value)
        else:
            if not self._choices or len(self._choices) < 1:
                print('No choices for {fqname} to decode {value}'.format(fqname=self.fqname, value=value))
                return ''
            else:
                return self._choices[0]

    def decode(self, value):
        if str(value) in self._choices:
            return str(value)
        else:
            if not self._choices or len(self._choices) < 1:
                print('No choices for {fqname} to decode {value}'.format(fqname=self.fqname, value=value))
                return None
            else:
                return self._choices[0]


class SystemParameter(ChoiceParameter):
    """A (single) building in the zone"""
    typename = 'SystemParameter'

    def initialize(self, parser):
        # skip the default ChoiceParameter initialization of _choices
        pass

    @property
    def _choices(self):
        scenario = self.config.scenario
        unique_systems_scenario_list = ["_sys_today_"]
        unique_systems_scenario_list.extend(get_systems_list(scenario))
        return unique_systems_scenario_list

    def encode(self, value):
        if not str(value) in self._choices:
            if len(self._choices) > 1:
                return self._choices[1]
            return self._choices[0]
        return str(value)


class MultiSystemParameter(MultiChoiceParameter):
    """A (single) building in the zone"""
    typename = 'MultiSystemParameter'

    def initialize(self, parser):
        # skip the default MultiChoiceParameter initialization of _choices
        pass

    @property
    def _choices(self):
        project_path = self.config.project
        scenarios_names_list = get_scenarios_list(project_path)
        unique_systems_scenarios_list = []
        for scenario_name in scenarios_names_list:
            scenario_path = os.path.join(project_path, scenario_name)
            systems_scenario = get_systems_list(scenario_path)
            unique_systems_scenarios_list.extend([scenario_name + "_sys_today_"])
            unique_systems_scenarios_list.extend([scenario_name + "_" + x for x in systems_scenario])
        return unique_systems_scenarios_list

    def decode(self, value):
        value = self.replace_references(value)
        choices = parse_string_to_list(value)
        if not choices:  # Return default if choices is empty
            return self.default
        return [self.replace_references(choice) for choice in choices if
                self.replace_references(choice) in self._choices]


class BuildingsParameter(MultiChoiceParameter):
    """A list of buildings in the zone"""
    typename = 'BuildingsParameter'

    def initialize(self, parser):
        # skip the default MultiChoiceParameter initialization of _choices
        self._empty = False

    @property
    def _choices(self):
        # set the `._choices` attribute to the list buildings in the project
        locator = cea.inputlocator.InputLocator(self.config.scenario, plugins=[])
        return locator.get_zone_building_names()


class CoordinateListParameter(ListParameter):
    typename = 'CoordinateListParameter'

    def encode(self, value):
        if isinstance(value, str):
            value = self.decode(value)
        strings = [str(validate_coord_tuple(coord_tuple)) for coord_tuple in value]
        return ', '.join(strings)

    def decode(self, value):
        coord_list = parse_string_coordinate_list(value)
        if len(set(coord_list)) < 3:
            raise ValueError('Requires 3 distinct coordinate points to create a polygon. Got: {}'.format(coord_list))
        return coord_list


def get_scenarios_list(project_path):
    # return empty list if project path does not exist
    if not os.path.exists(project_path):
        return []

    def is_valid_scenario(project_path, folder_name):
        folder_path = os.path.join(project_path, folder_name)
        # a scenario must be a valid path
        # a scenario can't start with a . like `.config`
        return all([os.path.isdir(folder_path), not folder_name.startswith('.')])

    return [folder_name for folder_name in os.listdir(project_path)
            if is_valid_scenario(project_path, folder_name)]


def get_systems_list(scenario_path):
    locator = cea.inputlocator.InputLocator(scenario_path, plugins=[])
    checkpoints = glob.glob(os.path.join(locator.get_optimization_master_results_folder(), "*.json"))
    iterations = set()
    for checkpoint in checkpoints:
        with open(checkpoint, 'rb') as f:
            data_checkpoint = json.load(f)
            iterations.update(data_checkpoint['systems_to_show'])
    unique_iterations = [str(x) for x in iterations]
    return unique_iterations


def parse_string_to_list(line):
    """Parse a line in the csv format into a list of strings"""
    if line is None:
        return []
    line = line.replace('\n', ' ')
    line = line.replace('\r', ' ')
    return [str(field.strip()) for field in line.split(',') if field.strip()]


def parse_string_coordinate_list(string_tuples):
    """Parse a string of comma-separated coordinate tuples into a list of tuples"""
    numerical = r'\d+(\.\d+)?'
    capture_group = r'\((-?{numerical},\s?-?{numerical})\)'.format(numerical=numerical)
    string_format = r'^(?:{capture_group},\s?)*(?:{capture_group})$'.format(capture_group=capture_group)

    match_string_format = re.match(string_format, string_tuples)
    if match_string_format is None:
        raise ValueError("Input is not in a valid format.\n"
                         "Expected example: (1,1),(-1,-1),(0,0)\n"
                         "Got: {}".format(string_tuples))

    coordinates_list = []
    for match in re.finditer(capture_group, string_tuples):
        coord_string = match.group(1)
        coord_tuple = tuple([float(coord.strip()) for coord in coord_string.split(',')])
        validate_coord_tuple(coord_tuple)
        coordinates_list.append(coord_tuple)

    return coordinates_list


def validate_coord_tuple(coord_tuple):
    """Validates a (lat, long) tuple, throws exception if not valid"""

    lon, lat = coord_tuple
    if lat < -90 or lat > 90:
        raise ValueError('Latitude must be between -90 and 90. Got {}'.format(lat))
    if lon < -180 or lon > 180:
        raise ValueError('Longitude must be between -180 and 180. Got {}'.format(lon))
    return coord_tuple


if __name__ == "__main__":
    config = Configuration()
