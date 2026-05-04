"""
Manage configuration information for the CEA. The Configuration class is built dynamically based on the type information
in ``default.config``.
"""
from __future__ import annotations

import configparser
import datetime
import glob
import io
import json
import os
import re
import tempfile
from typing import Dict, List, Union, Any, Generator, Tuple, Optional, cast
import warnings

import cea.inputlocator
import cea.plugin
from cea.utilities import unique, parse_string_to_list

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


class Configuration:
    def __init__(self, config_file: str = CEA_CONFIG):
        self.restricted_to = None

        self.default_config = configparser.ConfigParser()
        self.default_config.read(DEFAULT_CONFIG)

        self.user_config = configparser.ConfigParser()

        try:
            self.user_config.read([DEFAULT_CONFIG, config_file])
        except UnicodeDecodeError as e:
            print(e)
            # Fallback to default config if user config not readable
            warnings.warn(f"Could not read {config_file}, using default config instead. "
                          f"Please check that the config file is in the correct format or if it has any special characters")
            self.user_config.read(DEFAULT_CONFIG)

        cea.plugin.add_plugins(self.default_config, self.user_config)

        self.sections = self._init_sections()

        # Only write user config if it does not exist
        if not os.path.exists(CEA_CONFIG):
            self.save(config_file)

    def __getattr__(self, item: str) -> Union['Section', Any]:
        """Return either a Section object or the value of a Parameter from `general`"""
        cid = config_identifier(item)
        if cid in self.sections:
            return self.sections[cid]
        elif cid in self.sections['general'].parameters:
            return getattr(self.sections['general'], cid)
        else:
            raise AttributeError(f"Section or Parameter not found: {item}")

    def __setattr__(self, key: str, value: Any):
        """Set the value on a parameter in the general section"""
        if key in {'default_config', 'user_config', 'sections', 'restricted_to'} or key.startswith('_'):
            # make sure the __init__ method doesn't trigger this
            return super().__setattr__(key, value)

        cid = config_identifier(key)
        general_section = self.sections['general']
        if cid in general_section.parameters:
            return general_section.parameters[cid].set(value)
        else:
            raise AttributeError(f"Parameter not found in general section: {cid}")

    def __getstate__(self) -> str:
        """when we pickle, we only really need to pickle the user_config"""
        buffer = io.StringIO()
        self.user_config.write(buffer)
        value = buffer.getvalue()
        buffer.close()
        return value

    def __setstate__(self, state: str):
        """read in the user_config and re-initialize the state (this basically follows the __init__)"""
        self.restricted_to = None

        self.default_config = configparser.ConfigParser()
        self.default_config.read(DEFAULT_CONFIG)

        self.user_config = configparser.ConfigParser()
        buffer = io.StringIO(state)
        self.user_config.read_file(buffer)
        buffer.close()

        cea.plugin.add_plugins(self.default_config, self.user_config)

        self.sections = self._init_sections()

    def _init_sections(self) -> Dict[str, Section]:
        def construct_section(name: str, config: Configuration):
            if name != name.lower():
                raise ValueError('Section names must be lowercase')
            return Section(name, config)

        return {name: construct_section(name, self) for name in self.default_config.sections()}

    def restrict_to(self, option_list: List[str]) -> None:
        """
        Restrict the config object to only allowing parameters as defined in the ``option_list`` parameter.
        `option_list` is a list of strings of the form `section` or `section:parameter` as used in the ``scripts.yml``
        file for the ``parameters`` attribute of a script.

        The purpose of this is to ensure that scripts don't use parameters that are not specified as options to the
        scripts. This only solves half of the possible issues with :py:class:`cea.config.Configuration`: the other is
        that a script creates it's own config file somewhere down the line. This is hard to check anyway.
        """
        if option_list is None:
            self.restricted_to = None
            return

        self.restricted_to = [p.fqname for s, p in self.matching_parameters(option_list)]
        self.restricted_to.append("general:plugins")
        if 'general:scenario' in self.restricted_to:
            # since general:scenario is forced to be "{general:project}/{general:scenario-name}",
            # allow those two too
            self.restricted_to.append('general:project')
            self.restricted_to.append('general:scenario-name')

    class RestrictionContextManager:
        def __init__(self, config, parameters: Optional[List[str]]):
            self.config = config
            self.parameters = parameters
            self.old_restrictions = None

        def apply(self):
            self.old_restrictions = self.config.restricted_to
            self.config.restrict_to(self.parameters)

        def clear(self):
            self.config.restricted_to = self.old_restrictions

        def __enter__(self):
            self.apply()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.clear()

    def temp_restrictions(self, parameters: List[str]) -> RestrictionContextManager:
        """
        Apply temporary restricts to script using context manager
        """
        return self.RestrictionContextManager(self, parameters)

    def ignore_restrictions(self) -> RestrictionContextManager:
        """
        Create a ``with`` block where the config file restrictions are not kept.
        Usage::
            with config.ignore_restrictions():
                config.my_section.my_property = value
        """
        return self.RestrictionContextManager(self, None)

    def apply_command_line_args(self, args: List[str], option_list: List[str]) -> None:
        """
        Apply the command line args as passed to cea.interfaces.cli.cli (the ``cea`` command). Each argument
        is assumed to follow this pattern: ``--PARAMETER-NAME VALUE``,  with ``PARAMETER-NAME`` being one of the options
        in the config file and ``VALUE`` being the value to override that option with.
        """
        if not len(args):
            # no arguments to apply
            return
        if args[0].endswith('.py'):
            # remove script name from list of arguments
            args = args[1:]
        command_line_args = parse_command_line_args(args)

        for section, parameter in self.matching_parameters(option_list):
            if parameter.name in command_line_args:
                command_line_arg = command_line_args.pop(parameter.name)
                try:
                    raw_value = parameter.replace_references(command_line_arg)

                    # Allow boolean parameters to be set to empty string to be interpreted as True
                    if (raw_value == "" and isinstance(parameter, BooleanParameter)):
                        parameter.set(True)
                    else:
                        parameter.set(parameter.decode(raw_value))
                except Exception as e:
                    raise ValueError(
                        f"ERROR setting {section.name}:{parameter.name} to {command_line_arg}") from e

        if len(command_line_args) != 0:
            raise ValueError(f"Unexpected parameters: {command_line_args}")

    def matching_parameters(self, option_list: List[str]) -> Generator[Tuple[Section, Parameter]]:
        """
        Return a tuple (Section, Parameter) for all parameters that match the parameters in the ``option_list``.
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
                    raise KeyError(f"Invalid option in option_list: {option}")
                yield section, parameter
            else:
                section = self.sections[option]
                for parameter in section.parameters.values():
                    yield section, parameter

    def save(self, config_file: str = CEA_CONFIG) -> None:
        """
        Save the current configuration to a file. By default, the configuration is saved to the user configuration
        file (``~/cea.config``). If ``config_file`` is set to the default configuration file
        :py:data:`cea.config.DEFAULT_CONFIG`, then nothing is saved - this is to prevent overwriting the default
        configuration file.
        """
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

    def get_number_of_processes(self) -> int:
        """
        Returns the number of processes to use for multiprocessing.

        :return number_of_processes: Number of processes to use.
        """
        if self.multiprocessing:
            import multiprocessing
            number_of_processes = multiprocessing.cpu_count() - cast(int, self.number_of_cpus_to_keep_free)
            return max(1, number_of_processes)  # ensure that at least one process is being used
        else:
            return 1

    def get(self, fqname: str) -> Any:
        """Given a string of the form "section:parameter", return the value of that parameter"""
        return self.get_parameter(fqname).get()

    def get_parameter(self, fqname: str) -> Parameter:
        """
        Given a string of the form "section:parameter", return the parameter object

        :rtype: cea.config.Parameter
        """
        section, parameter = fqname.split(':')
        try:
            return self.sections[section].parameters[parameter]
        except KeyError:
            raise KeyError(fqname)

    def refresh_plugins(self) -> None:
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

    if len(values) != 0:
        raise ValueError(f"Bad arguments: {args}")

    return parameters


def config_identifier(python_identifier: str) -> str:
    """
    For vanity, keep keys and section names in the config file with dashes instead of underscores and
    all-lowercase
    """
    return python_identifier.lower().replace('_', '-')


class Section:
    """Instances of ``Section`` describe a section in the configuration file."""

    def __init__(self, name: str, config: 'Configuration') -> None:
        """
        :param name: The name of the section (as it appears in the configuration file, all lowercase)
        :type name: str
        :param config: The Configuration instance this section belongs to
        :type config: Configuration
        """

        self.name = name
        self.config = config
        self.parameters = self._init_parameters()

    def __getattr__(self, item: str) -> Any:
        """Return the value of the parameter with that name."""
        cid = config_identifier(item)
        if cid in self.parameters:
            if self.config.restricted_to is not None and self.parameters[cid].fqname not in self.config.restricted_to:
                raise AttributeError(
                    f"Parameter not configured to work with this script: {self.parameters[cid].fqname}")
            return self.parameters[cid].get()
        else:
            raise AttributeError(f"Parameter not found: {item}")

    def __setattr__(self, key: str, value: Any):
        """Set the value on a parameter"""
        if key in {'name', 'config', 'parameters'}:
            # make sure the __init__ method doesn't trigger this
            return super().__setattr__(key, value)

        cid = config_identifier(key)
        if cid in self.parameters:
            if self.config.restricted_to is not None and self.parameters[cid].fqname not in self.config.restricted_to:
                raise AttributeError(
                    f"Parameter not configured to work with this script: {self.parameters[cid].fqname}")
            return self.parameters[cid].set(value)
        else:
            return super().__setattr__(key, value)

    def __repr__(self):
        return f"[{self.name}]({', '.join(self.parameters.keys())})"

    def _init_parameters(self) -> Dict[str, Parameter]:
        def construct_parameter(name: str, section: Section, config: Configuration):
            """Create the appropriate subtype of ``Parameter`` based on the .type option in the default.config file.
            :param name: The name of the parameter (as it appears in the configuration file, all lowercase)
            :type name: str
            :param section: The section this parameter is to be defined for
            :type section: Section
            :param config: The Configuration instance this parameter belongs to
            :type config: Configuration
            """

            if name != name.lower():
                raise ValueError("Parameter names must be lowercase")

            try:
                parameter_type = config.default_config.get(section.name, f"{name}.type")
            except configparser.NoOptionError:
                parameter_type = 'StringParameter'

            if parameter_type not in globals():
                raise ValueError(
                    f"Bad parameter type in default.config: {section.name}/{name}={parameter_type}"
                )

            parameter = globals()[parameter_type](name, section, config)

            # Call initialize() if the parameter class defines it
            if hasattr(parameter, 'initialize') and callable(getattr(parameter, 'initialize')):
                parameter.initialize(config.default_config)

            return parameter

        return {parameter_name.lower(): construct_parameter(parameter_name.lower(), self, self.config)
                for parameter_name in self.config.default_config.options(self.name)
                if '.' not in parameter_name}


class Parameter:
    def __init__(self, name: str, section: Section, config: Configuration):
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
        self.fqname = f"{section.name}:{self.name}"
        self.config = config

        try:
            self.help = config.default_config.get(section.name, f"{self.name}.help", raw=True)
        except configparser.NoOptionError:
            self.help = f"FIXME: Add help to {section, name}:{self.name}"

        try:
            self.category = config.default_config.get(section.name, f"{self.name}.category", raw=True)
        except configparser.NoOptionError:
            self.category = None

        try:
            self.nullable = config.default_config.getboolean(section.name, f"{self.name}.nullable")
        except configparser.NoOptionError:
            self.nullable = False

    @property
    def default(self) -> Any:
        return self.decode(self.config.default_config.get(self.section.name, self.name))

    def __repr__(self) -> str:
        return f"<Parameter {self.section.name}:{self.name}={self.get()}>"

    @property
    def py_name(self) -> str:
        return self.name.replace('-', '_')

    def encode(self, value: Any) -> str:
        """Encode ``value`` to a string representation for writing to the configuration file"""
        return str(value)

    def decode(self, value: str) -> Any:
        """Decode ``value`` to the type supported by this Parameter"""
        return value

    def get(self) -> Any:
        """Return the value from the config file"""
        encoded_value = self.get_raw()
        encoded_value = self.replace_references(encoded_value)
        try:
            return self.decode(encoded_value)
        except ValueError as ex:
            raise ValueError(f'{self.section.name}:{self.name} - {ex}')

    def get_raw(self) -> str:
        """Return the value from the config file, but without replacing references and also
        without decoding."""
        return self.config.user_config.get(self.section.name, self.name)

    def replace_references(self, encoded_value: str) -> str:
        # expand references (like ``{general:scenario}``)
        def lookup_config(matchobj):
            return self.config.sections[matchobj.group(1)].parameters[matchobj.group(2)].get_raw()

        encoded_value = re.sub(r"{([a-z\d-]+):([a-z\d-]+)}", lookup_config, encoded_value)
        return encoded_value

    def set(self, value: Any):
        encoded_value = self.encode(value)
        self.config.user_config.set(self.section.name, self.name, encoded_value)

    def set_empty(self):
        """
        Set parameter to an empty value (an empty string) in the config, bypassing encode() validation.
        It ignores whether the parameter is nullable or not.
        """
        self.config.user_config.set(self.section.name, self.name, "")


class PathParameter(Parameter):
    """Describes a folder in the system"""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        try:
            self._direction = config.default_config.get(section.name, f"{name}.direction")
            if self._direction not in {'input', 'output'}:
                self._direction = 'input'
        except configparser.NoOptionError:
            self._direction = 'input'

    def decode(self, value):
        """Always return a canonical path"""
        return str(os.path.normpath(os.path.abspath(os.path.expanduser(value))))


class NullablePathParameter(PathParameter):
    def decode(self, value):
        if value == '':
            return value
        return super().decode(value)


class FileParameter(Parameter):
    """Describes a file in the system."""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self._extensions = config.default_config.get(section.name, f"{name}.extensions").split()
        try:
            self._direction = config.default_config.get(section.name, f"{name}.direction")
            if self._direction not in {'input', 'output'}:
                self._direction = 'input'
        except configparser.NoOptionError:
            self._direction = 'input'

    def encode(self, value):
        if value is None:
            if self.nullable:
                return ''
            else:
                raise ValueError(f"Can't encode None for non-nullable FileParameter {self.name}.")
        if not isinstance(value, str):
            raise ValueError(
                f"FileParameter {self.name} expects a string path, got {type(value).__name__}."
            )
        return value

    def decode(self, value):
        if not value and not self.nullable:
            raise ValueError(f"Can't decode value for non-nullable FileParameter {self.name}.")
        
        # Always replace references and return a canonical path
        return self.replace_references(value)


class ResumeFileParameter(FileParameter):
    """Path to the workflow:resume-file - this is generally ${TEMP}/resume-workflow.yml. Makes sure it is writeable"""

    def encode(self, value):
        return self._check_path(str(value))

    @staticmethod
    def _check_path(path):
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
        return self._check_path(str(value))

class InputFileParameter(FileParameter):
    """A parameter that describes a user provided input file."""


class UserNetworkInputFileParameter(InputFileParameter):
    """
    Special InputFileParameter for user-defined network inputs (edges-shp-path, nodes-shp-path, network-geojson-path).
    Validates mutual exclusivity with existing-network parameter.
    """

    def encode(self, value):
        # Validate mutual exclusivity before calling parent encode
        # Determine which parameter this is based on self.name
        param_name = self.name.replace('-', '_')  # Convert from config format to attribute format
        _validate_user_network_input_exclusivity(self.config, param_name, value)

        # Call parent encode
        return super().encode(value)


class JsonParameter(Parameter):
    """A parameter that gets / sets JSON data (useful for dictionaries, lists etc.)"""

    def encode(self, value):
        return json.dumps(value)

    def decode(self, value):
        if value == '':
            return None
        return json.loads(value)


class WeatherPathParameter(Parameter):
    THIRD_PARTY_WEATHER_SOURCES = ['climate.onebuilding.org']
    MORPHING = ['pyepwmorph']

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
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
        elif value in self.THIRD_PARTY_WEATHER_SOURCES or value in self.MORPHING:
            weather_path = value
        else:
            raise cea.ConfigError(f"Invalid weather path: {value}")
        return weather_path

    @property
    def default(self):
        """override base default, since in decode we've banned empty weather file parameters"""
        return ""


class WorkflowParameter(Parameter):
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
            print(f"ERROR: Workflow not found: {value} - using {self.examples[next(iter(self.examples.keys()))]}")
            return self.examples[next(iter(self.examples.keys()))]


class BooleanParameter(Parameter):
    """Read / write boolean parameters to the config file."""

    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def encode(self, value):
        return 'true' if value else 'false'

    def decode(self, value):
        return self._boolean_states[str(value).lower()]


class IntegerParameter(Parameter):
    """Read / write integer parameters to the config file."""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        # Read min/max bounds if specified
        try:
            self._min = int(config.default_config.get(section.name, f"{name}.min"))
        except (configparser.NoOptionError, ValueError):
            self._min = None

        try:
            self._max = int(config.default_config.get(section.name, f"{name}.max"))
        except (configparser.NoOptionError, ValueError):
            self._max = None

    def encode(self, value):
        if value is None or value == "":
            if not self.nullable:
                raise ValueError("Can't encode None for non-nullable IntegerParameter.")
            return ""

        int_value = int(value)

        # Validate bounds
        if self._min is not None and int_value < self._min:
            raise ValueError(f"{self.fqname} must be >= {self._min}, got {int_value}")
        if self._max is not None and int_value > self._max:
            raise ValueError(f"{self.fqname} must be <= {self._max}, got {int_value}")

        return str(int_value)

    def decode(self, value) -> int | None:
        try:
            return int(value)
        except ValueError:
            if self.nullable:
                return None
            else:
                raise ValueError("Can't decode value for non-nullable IntegerParameter.")


class RealParameter(Parameter):
    """Read / write floating point parameters to the config file."""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        # allow user to override the amount of decimal places to use
        try:
            self._decimal_places = int(config.default_config.get(section.name, f"{name}.decimal-places"))
        except configparser.NoOptionError:
            self._decimal_places = 4

        # Read min/max bounds if specified
        try:
            self._min = float(config.default_config.get(section.name, f"{name}.min"))
        except (configparser.NoOptionError, ValueError):
            self._min = None

        try:
            self._max = float(config.default_config.get(section.name, f"{name}.max"))
        except (configparser.NoOptionError, ValueError):
            self._max = None

    def encode(self, value):
        if value is None or value == "":
            if not self.nullable:
                raise ValueError("Can't encode None for non-nullable RealParameter.")
            return ''

        float_value = float(value)

        # Validate bounds
        if self._min is not None and float_value < self._min:
            raise ValueError(f"{self.fqname} must be >= {self._min}, got {float_value}")
        if self._max is not None and float_value > self._max:
            raise ValueError(f"{self.fqname} must be <= {self._max}, got {float_value}")

        return format(float_value, ".%i" % self._decimal_places)

    def decode(self, value) -> float | None:
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

    def encode(self, value):
        if isinstance(value, str):
            # should be a list
            value = parse_string_to_list(value)
        strings = [str(s).strip() for s in value]
        for s in strings:
            if ',' in s:
                raise ValueError(
                    f"No commas allowed in values of ListParameter {self.fqname} (value to encode: {repr(value)})")
        return ', '.join(strings)

    def decode(self, value):
        return parse_string_to_list(value)


class PluginListParameter(ListParameter):
    """A list of cea.plugin.Plugin instances"""

    def set(self, value):
        super().set(value)
        self.config.refresh_plugins()

    def encode(self, value):
        """Make sure we don't duplicate any of the plugins"""
        unique_plugins = unique(value)
        return super().encode(unique_plugins)

    def decode(self, value):
        plugin_fqnames = unique(parse_string_to_list(value))
        plugins = [cea.plugin.instantiate_plugin(plugin_fqname) for plugin_fqname in plugin_fqnames]
        return [plugin for plugin in plugins if plugin is not None]


class SubfoldersParameter(ListParameter):
    """A list of subfolder names of a parent folder."""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        # allow the parent option to be set
        self._parent = config.default_config.get(section.name, f"{name}.parent")

    def decode(self, value):
        """Only return the folders that exist"""
        folders = parse_string_to_list(value)
        return [folder for folder in folders if folder in self.get_folders()]

    def get_folders(self):
        parent = self.replace_references(self._parent)
        try:
            return [folder for folder in os.listdir(parent) if os.path.isdir(os.path.join(parent, folder))]
        except OSError:
            # parent doesn't exist?
            return []


class StringParameter(Parameter):
    """Default Parameter type"""""


class WhatIfNameParameter(StringParameter):
    """
    Parameter for what-if scenario names with collision detection.
    Validates in real-time to prevent overwriting existing final-energy results.
    """

    def _validate_whatif_name(self, value) -> str:
        """
        Validate what-if name for invalid characters and collision with existing scenarios.
        """
        value = value.strip()

        # Check for invalid filesystem characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in value for char in invalid_chars):
            raise ValueError(
                f"What-if name contains invalid characters. "
                f"Avoid: {' '.join(invalid_chars)}"
            )

        # Check for collision with existing what-if scenarios
        scenario = self.config.scenario
        locator = cea.inputlocator.InputLocator(scenario)

        # Check if final-energy folder exists for this what-if name
        whatif_folder = locator.get_analysis_folder(value)
        if os.path.exists(whatif_folder):
            raise ValueError(
                f"What-if (sub)scenario '{value}' already exists. "
                f"Choose a different name or delete the existing one."
            )

        return value

    def encode(self, value):
        """
        Validate and encode what-if name.
        Raises ValueError if name contains invalid characters or collides with existing scenario.
        """
        if not str(value) or str(value).strip() == '':
            if self.nullable:
                return ''
            raise ValueError("What-if name is required. Please provide a valid name.")

        return self._validate_whatif_name(str(value))

    def decode(self, value):
        """
        Parse and normalize what-if name from config file.
        Lenient parsing - only validates security concerns (filesystem characters).
        Business rules (collision check) are enforced in encode().
        """
        if not value:
            return ""

        value = value.strip()

        # Only validate filesystem characters (security concern)
        # Collision check is encode's job when creating new scenarios
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in value for char in invalid_chars):
            raise ValueError(
                f"What-if name contains invalid characters. "
                f"Avoid: {' '.join(invalid_chars)}"
            )

        return value


class NetworkLayoutNameParameter(StringParameter):
    """
    Parameter for network layout names with collision detection.
    Validates in real-time to prevent overwriting existing network layouts.
    """

    def _validate_network_name(self, value) -> str:
        """
        Validate network name for invalid characters and collision with existing networks.
        """
        value = value.strip()

        # Check for invalid filesystem characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in value for char in invalid_chars):
            raise ValueError(
                f"Network name contains invalid characters. "
                f"Avoid: {' '.join(invalid_chars)}"
            )

        # Check for collision with existing networks
        scenario = self.config.scenario
        locator = cea.inputlocator.InputLocator(scenario)

        # Check network folder exists
        network_folder = locator.get_thermal_network_folder_network_name_folder(value)
        if os.path.exists(network_folder):
            raise ValueError(
                f"Network '{value}' already exists. "
                f"Choose a different name or delete the existing network."
            )

        return value

    def encode(self, value):
        """
        Validate and encode network name.
        Raises ValueError if name contains invalid characters or collides with existing network.
        """
        if not value or str(value).strip() == '':
            if self.nullable:
                return ''
            raise ValueError("Network name is required. Please provide a valid name.")

        return self._validate_network_name(str(value))

    def decode(self, value):
        """
        Parse and normalize network name from config file.
        Lenient parsing - only validates security concerns (filesystem characters).
        Business rules (collision check) are enforced in encode().
        """
        if not value:
            return ""

        value = value.strip()

        # Only validate filesystem characters (security concern)
        # Collision check is encode's job when creating new networks
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in value for char in invalid_chars):
            raise ValueError(
                f"Network name contains invalid characters. "
                f"Avoid: {' '.join(invalid_chars)}"
            )

        return value


class OptimizationIndividualListParameter(ListParameter):
    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        # allow the parent option to be set
        self._project = config.default_config.get(section.name, f"{name}.project")

    def get_folders(self, project=None):
        if not project:
            project = self.replace_references(self._project)
        try:
            return [folder for folder in os.listdir(project) if os.path.isdir(os.path.join(project, folder))]
        except OSError:
            # project doesn't exist?
            return []


class DateParameter(Parameter):
    def encode(self, value):
        return datetime.datetime.strftime(value, '%Y-%m-%d')

    def decode(self, value):
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            # try with system's locale
            return datetime.datetime.strptime(value, '%x')


class ChoiceParameterBase(Parameter):
    """Shared base for parameters backed by a finite set of choices."""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self._choices_cache = None

    @property
    def _choices(self):
        """Lazy-loaded cached property for static choices from config file.
        Dynamic subclasses should override this property without caching."""
        if self._choices_cache is None:
            self._choices_cache = parse_string_to_list(
                self.config.default_config.get(self.section.name, f"{self.name}.choices")
            )
        return self._choices_cache


class ChoiceParameter(ChoiceParameterBase):
    """A parameter that can only take on values from a specific set of values"""

    def encode(self, value) -> str:
        _value = str(value).strip() if value is not None else ''

        # Allow empty/None values if parameter is nullable
        if self.nullable and _value == '':
            return ''
        
        # Validate that the value is one of the allowed choices
        if _value not in self._choices:
            raise ValueError(
                f"Invalid value {_value} for {self.fqname}, choose from: {', '.join(self._choices)}")
        return _value

    def decode(self, value):
        _value = str(value).strip() if value is not None else ''

        # Allow empty values if parameter is nullable
        # FIXME: Maybe decode does not need to consider nullability
        if self.nullable and _value == '':
            return None
        
        # Validate that the value is one of the allowed choices
        if _value not in self._choices:
            if not self._choices:
                raise ValueError(f"No choices for {self.fqname} to decode {value}")
            raise ValueError(f"Invalid value {value} for {self.fqname}, expected one of: {', '.join(self._choices)}")
        
        return _value


def _validate_user_network_input_exclusivity(config, param_being_set, value_being_set):
    """
    Validate that only ONE user-defined network input method is being used.

    Three mutually exclusive methods:
    1. existing-network (NetworkLayoutChoiceParameter)
    2. edges-shp-path + nodes-shp-path (InputFileParameter)
    3. network-geojson-path (InputFileParameter)

    Args:
        config: Configuration object
        param_being_set: Name of parameter being validated ('existing_network', 'edges_shp_path', etc.)
        value_being_set: Value being set for the parameter

    Raises:
        ValueError: If more than one input method would be active after setting this value
    """
    # Get current values (before the new value is set) - these are in network-layout section
    existing_net = getattr(config.network_layout, 'existing_network', None)
    edges_shp = getattr(config.network_layout, 'edges_shp_path', None)
    nodes_shp = getattr(config.network_layout, 'nodes_shp_path', None)
    geojson_path = getattr(config.network_layout, 'network_geojson_path', None)

    # Simulate setting the new value
    if param_being_set == 'existing_network':
        existing_net = value_being_set
    elif param_being_set == 'edges_shp_path':
        edges_shp = value_being_set
    elif param_being_set == 'nodes_shp_path':
        nodes_shp = value_being_set
    elif param_being_set == 'network_geojson_path':
        geojson_path = value_being_set

    # Count how many input methods would be active
    methods_used = []
    if existing_net and str(existing_net).strip() and str(existing_net) not in ['', '(none)']:
        methods_used.append("existing-network")
    if edges_shp or nodes_shp:
        methods_used.append("edges-shp-path/nodes-shp-path")
    if geojson_path:
        methods_used.append("network-geojson-path")

    # Enforce mutual exclusivity
    if len(methods_used) > 1:
        raise ValueError(
            f"Only ONE user-defined network input method can be used at a time. "
            f"Currently using: {', '.join(methods_used)}. "
            f"Please choose either: (1) existing-network, (2) edges-shp-path + nodes-shp-path, or (3) network-geojson-path."
        )


class NetworkLayoutChoicesMixin:
    _network_types = {'DH', 'DC'}

    config: Configuration
    nullable: bool

    def _get_available_networks(self) -> List[str]:
        locator = cea.inputlocator.InputLocator(self.config.scenario)
        network_folder = locator.get_thermal_network_folder()
        if not os.path.exists(network_folder):
            return []
        return [name for name in os.listdir(network_folder)
                if os.path.isdir(os.path.join(network_folder, name)) and name not in self._network_types]

    def _get_network_file_paths(self, network_type: str, network_name: str) -> Tuple[str, str]:
        """Get path for network node and edge files for the given network name"""
        locator = cea.inputlocator.InputLocator(self.config.scenario)

        network_type_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)
        # Remove trailing slash/separator if present
        network_type_folder = network_type_folder.rstrip(os.sep)

        edges_path = locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes_path = locator.get_network_layout_nodes_shapefile(network_type, network_name)

        return edges_path, nodes_path

    def _sort_networks_by_modification_time(self, network_names: List[str]) -> List[str]:
        """Sort network layouts by modification time (most recent first)"""
        modified_times = []
        locator = cea.inputlocator.InputLocator(self.config.scenario)

        for network_name in network_names:
            # Only check for layout.shp (shared edges file)
            layout_path = locator.get_network_layout_shapefile(network_name)
            if os.path.exists(layout_path):
                sort_time = os.path.getmtime(layout_path)
                modified_times.append((network_name, sort_time))

        # Sort by modification time, most recent first
        modified_times.sort(key=lambda x: x[1], reverse=True)
        sorted_networks = [network_name for network_name, _ in modified_times]
        return sorted_networks

    @property
    def _network_choices(self) -> List[str]:
        """Sorted available network names, most recent first."""
        networks = self._get_available_networks()
        return self._sort_networks_by_modification_time(networks)


class NetworkLayoutChoiceParameter(NetworkLayoutChoicesMixin, ChoiceParameter):
    """
    Parameter for selecting existing network layouts based on network type.
    """

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        try:
            self.default_to_none = config.default_config.getboolean(section.name, f"{name}.default-to-none")
        except configparser.NoOptionError:
            self.default_to_none = False

    @property
    def _choices(self):
        choices = list(self._network_choices)
        if self.nullable:
            choices.insert(0, "(none)")
        return choices

    def _encode_network(self, value: str) -> str:
        """
        Validate a single network name and return the encoded string.
        Handles nullable/empty/missing cases. Does NOT handle mutual exclusivity.
        """
        if self.nullable and str(value) == "(none)":
            return '(none)'

        if not value or str(value).strip() == '':
            if self.nullable:
                return '(none)'
            raise ValueError("Network layout is required. Please select a network layout.")

        available_networks = self._get_available_networks()
        if str(value) not in available_networks:
            if self.nullable:
                return '(none)'
            raise ValueError(
                f"Network layout '{value}' not found. "
                f"Available layouts: {', '.join(available_networks)}"
            )
        return str(value)

    def _decode_network(self, value: str) -> str:
        """
        Decode a single network name.
        Returns '' for empty/missing/invalid values, falling back to the most recent network
        unless self.default_to_none is True.
        """
        if value == '(none)':
            return ''

        available_networks = self._get_available_networks()

        if not value or value == '':
            if not available_networks or self.default_to_none:
                return ''
            sorted_networks = self._sort_networks_by_modification_time(available_networks)
            return sorted_networks[0] if sorted_networks else ''

        if value in available_networks:
            return value

        if not available_networks:
            return ''

        sorted_networks = self._sort_networks_by_modification_time(available_networks)
        return sorted_networks[0] if sorted_networks else ''

    def encode(self, value):
        _validate_user_network_input_exclusivity(self.config, 'existing_network', value)
        return self._encode_network(value)

    def decode(self, value):
        return self._decode_network(value)


class PhasingPlanChoiceParameter(StringParameter):
    """
    Parameter for thermal network phasing plan names with collision detection.
    Errors if the name already exists as a phasing plan folder under
    `outputs/data/thermal-network/phasing-plans/` (to prevent overwriting).
    """

    def _validate_phasing_plan_name(self, value) -> str:
        value = value.strip()

        # Check for invalid filesystem characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in value for char in invalid_chars):
            raise ValueError(
                f"Phasing plan name contains invalid characters. "
                f"Avoid: {' '.join(invalid_chars)}"
            )

        # Check for collision with existing phasing plans
        scenario = self.config.scenario
        locator = cea.inputlocator.InputLocator(scenario)
        plans_folder = locator.get_thermal_network_phasing_plans_folder()
        plan_folder = os.path.join(plans_folder, value)
        if os.path.exists(plan_folder):
            raise ValueError(
                f"Phasing plan '{value}' already exists. "
                f"Choose a different name or delete the existing plan."
            )

        return value

    def encode(self, value):
        if not value or str(value).strip() == '':
            if self.nullable:
                return ''
            raise ValueError("Phasing plan name is required. Please provide a valid name.")
        return self._validate_phasing_plan_name(str(value))

    def decode(self, value):
        if not value:
            return ''
        value = value.strip()
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in value for char in invalid_chars):
            raise ValueError(
                f"Phasing plan name contains invalid characters. "
                f"Avoid: {' '.join(invalid_chars)}"
            )
        return value


class WhatIfNameChoiceParameter(ChoiceParameter):
    """
    Parameter for selecting an existing what-if scenario name from a dropdown.
    Scans outputs/data/analysis/ for existing subfolders.
    """

    @property
    def _choices(self):
        try:
            locator = cea.inputlocator.InputLocator(self.config.scenario)
            analysis_root = os.path.dirname(locator.get_analysis_folder('__probe__'))
            if not os.path.exists(analysis_root):
                return []
            mode = self.config.default_config.get(self.section.name, f"{self.name}.mode", fallback=None)
            names = sorted(
                name for name in os.listdir(analysis_root)
                if os.path.isdir(os.path.join(analysis_root, name))
            )
            if mode == 'final_energy':
                names = [name for name in names if os.path.exists(locator.get_final_energy_folder(name))]
            return names
        except Exception:
            return []

    def encode(self, value):
        value = str(value).strip()
        choices = self._choices
        if choices and value not in choices:
            raise ValueError(
                f"What-if scenario '{value}' does not exist. "
                f"Available: {', '.join(choices) or 'none'}"
            )
        return value

    def decode(self, value):
        if not value:
            return ''
        return str(value).strip()


class DatabasePathParameter(Parameter):
    """A parameter that can either be set to a region-specific CEA Database (e.g. CH or SG) or to a user-defined
    folder that has the same structure."""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self.locator = cea.inputlocator.InputLocator(None, [])
        self._choices = {p: os.path.join(self.locator.db_path, p) for p in os.listdir(self.locator.db_path)
                         if
                         os.path.isdir(os.path.join(self.locator.db_path, p)) and p not in ['weather', '__pycache__']}

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
            raise cea.ConfigError(f"Invalid database path: {value}")
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
                if os.path.splitext(default_file_path)[1] not in {'.xls', '.xlsx'}:
                    # we're only interested in the excel files
                    continue
                template_file_path = os.path.join(path, folder, file)
                if not os.path.exists(template_file_path):
                    print(f"Invalid user-specified region template - file not found: {template_file_path}")
                    return False
        return True


class PlantNodeParameter(ChoiceParameter):
    """A parameter that refers to valid PLANT nodes of a thermal-network"""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self.network_name_fqn = config.default_config.get(section.name, f"{name}.network-name")
        self.network_type_fqn = config.default_config.get(section.name, f"{name}.network-type")

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
            print(f"No plant nodes can be found, ignoring `{value}`")
            return ""
        elif value not in self._choices:
            first_choice = self._choices[0]
            print(f"Plant node `{value}` not found. Using {first_choice}")
            return str(first_choice)
        else:
            return super().encode(value)

    def decode(self, value):
        if str(value) in self._choices:
            return str(value)
        elif self._choices:
            return self._choices[0]
        else:
            return None


class ScenarioNameChoicesMixin:
    config: Configuration
    exclude_current: bool

    @property
    def _choices(self):
        choices = get_scenarios_list(str(self.config.project))
        if self.exclude_current and self.config.scenario_name and self.config.scenario_name in choices:
            choices.remove(str(self.config.scenario_name))

        return choices


class ScenarioNameParameter(ScenarioNameChoicesMixin, ChoiceParameter):
    """A parameter that can be set to a scenario-name"""

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self.exclude_current = config.default_config.getboolean(section.name, f"{name}.exclude_current", fallback=False)

    def encode(self, value):
        """Make sure the scenario folder exists"""
        if value == '':
            raise ValueError('scenario-name cannot be empty')
        elif self._choices and value not in self._choices:
            print(f'WARNING: Scenario "{value}" does not exist. Valid choices: {", ".join(self._choices)}')
        return str(value)

    def decode(self, value):
        # allow scenario name to be non-existing folder when reading from config file...
        return str(value)

class ScenarioParameter(Parameter):
    """This parameter type is special in that it is derived from two other parameters (project, scenario-name)"""

    def get_raw(self):
        return "{general:project}/{general:scenario-name}"

    def set(self, value):
        """Update the {general:project} and {general:scenario-name} parameters"""
        project, scenario_name = os.path.split(value)
        self.config.project = project
        self.config.scenario_name = scenario_name

    def decode(self, value):
        """Make sure the path is nicely formatted"""
        return os.path.normpath((os.path.expanduser(value)))


class MultiChoiceParameter(ChoiceParameterBase):
    """Like ChoiceParameter, but multiple values from the choices list can be used"""

    # Subclass customisation flags
    empty_means_all: bool = True    # decode('') -> _choices (True) or [] (False)
    strict_validation: bool = False  # encode raises on invalid (True) or silently filters (False)

    @property
    def default(self):
        _default = self.config.default_config.get(self.section.name, self.name)
        if _default == '':
            return []
        return self.decode(_default)

    def encode(self, value) -> str:
        # Coerce input to list
        if isinstance(value, str):
            value = parse_string_to_list(value)
        elif not isinstance(value, list):
            value = [str(value).strip()]

        # Handle empty
        if not value:
            if self.nullable:
                return ''
            if self.strict_validation:
                raise ValueError(f"At least one value is required for {self.name}.")
            return ''

        # Validate against choices
        value = self._validate_choices(value)

        return ', '.join(map(str, value))

    def decode(self, value) -> list[str]:
        if value == '' or value is None:
            return self._choices if self.empty_means_all else []
        choices = parse_string_to_list(value)
        valid_choices = set(self._choices)
        if not valid_choices:
            return choices
        return [c for c in choices if c in valid_choices]

    def _validate_choices(self, value: list[str]) -> list[str]:
        """Validate/filter value list against available choices. Override for custom behaviour."""
        choices = self._choices
        if not choices:
            return value
        choices_set = set(choices)
        if self.strict_validation:
            invalid = set(value) - choices_set
            if invalid:
                raise ValueError(
                    f"Invalid value(s) {invalid} for {self.name}. "
                    f"Available: {', '.join(choices)}"
                )
            return value
        return [v for v in value if v in choices_set]


class NetworkLayoutMultiChoiceParameter(NetworkLayoutChoicesMixin, MultiChoiceParameter):
    """
    Parameter for selecting MULTIPLE existing network layouts (for multi-phase analysis).
    """

    empty_means_all = False
    strict_validation = True

    @property
    def _choices(self):
        return list(self._network_choices)

    def _validate_choices(self, value: list[str]) -> list[str]:
        available = self._get_available_networks()
        invalid = set(value) - set(available)
        if invalid:
            raise ValueError(
                f"Invalid network layouts {invalid} for {self.name}. "
                f"Available layouts: {', '.join(available)}"
            )
        return value


class WhatIfNameMultiChoiceParameter(MultiChoiceParameter):
    """
    Multi-choice version of WhatIfNameChoiceParameter.
    Scans outputs/data/analysis/ for existing subfolders and allows selecting multiple.
    Supports mode=final_energy to filter to scenarios with final-energy output.
    """

    empty_means_all = False
    strict_validation = True

    @property
    def _choices(self):
        try:
            locator = cea.inputlocator.InputLocator(self.config.scenario)
            analysis_root = os.path.dirname(locator.get_analysis_folder('__probe__'))
            if not os.path.exists(analysis_root):
                return []
            mode = self.config.default_config.get(self.section.name, f"{self.name}.mode", fallback=None)
            # Sort by most-recently-modified directory first so plot forms
            # default to the just-run what-if (matches the LCA map layers'
            # `get_whatif_names` ordering). Skips hidden entries like
            # macOS ``.DS_Store`` and non-directories.
            entries = []
            for name in os.listdir(analysis_root):
                if name.startswith('.'):
                    continue
                path = os.path.join(analysis_root, name)
                if not os.path.isdir(path):
                    continue
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    mtime = 0.0
                entries.append((name, mtime))
            entries.sort(key=lambda x: (-x[1], x[0]))
            names = [name for name, _ in entries]
            if mode == 'final_energy':
                names = [name for name in names if os.path.exists(locator.get_final_energy_folder(name))]
            elif mode == 'heat_rejection':
                names = [name for name in names if os.path.exists(locator.get_heat_rejection_whatif_buildings_file(name))]
            elif mode == 'costs':
                names = [name for name in names if os.path.exists(locator.get_costs_whatif_buildings_file(name))]
            elif mode == 'emissions':
                names = [name for name in names if os.path.exists(locator.get_emissions_whatif_buildings_file(name))]
            return names
        except Exception:
            return []


class EnergyCarrierMultiChoiceParameter(MultiChoiceParameter):
    """Multi-choice parameter of carriers defined in ``ENERGY_CARRIERS.csv``.

    Choices are the distinct ``feedstock_file`` values from the scenario's
    ``ENERGY_CARRIERS.csv`` — typically ``GRID``, ``NATURALGAS``, ``OIL``,
    ``COAL``, ``WOOD``, ``BIOGAS``, ``WETBIOMASS``, … Users who add or
    rename feedstocks in the CSV get the new names here without any code
    change. Empty means "all available carriers".
    """

    empty_means_all = True
    strict_validation = False

    @property
    def _choices(self):
        try:
            locator = cea.inputlocator.InputLocator(self.config.scenario)
            from cea.technologies.energy_carriers import available_carriers
            return sorted(available_carriers(locator))
        except Exception:
            return []


class ComponentMultiChoiceParameter(MultiChoiceParameter):
    """
    Multi-choice parameter that dynamically lists supply components found in
    configuration.json for the selected what-if scenarios and scale.

    Depends on sibling parameters `what-if-name` and `scale` in the same section.
    Choices = intersection of components across all selected what-if scenarios,
    filtered by selected scale(s):
      - 'district' -> components from plants section of configuration.json
      - 'building' -> components from buildings section of configuration.json
    """

    def initialize(self, parser):
        self.help = parser.get(self.section.name, f"{self.name}.help", fallback="")
        self.nullable = parser.getboolean(self.section.name, f"{self.name}.nullable", fallback=True)
        self.depends_on = [
            f'{self.section.name}:what-if-name',
            f'{self.section.name}:scale',
        ]

    @property
    def _choices(self):
        try:
            from cea.visualisation.format.plot_colours import component_display as _component_display
            section_attr = self.section.name.replace('-', '_')
            section = getattr(self.config, section_attr)
            what_if_names = section.what_if_name
            scales = section.scale
            if not what_if_names or not scales:
                return []
            locator = cea.inputlocator.InputLocator(self.config.scenario)
            component_sets = []
            for whatif_name in what_if_names:
                config_data = locator.read_analysis_configuration(whatif_name)
                if config_data is None:
                    continue
                components = set()
                if 'district' in scales:
                    for plant_cfg in config_data.get('plants', {}).values():
                        for key in ('primary_component', 'secondary_component', 'tertiary_component'):
                            code = plant_cfg.get(key, '')
                            if code:
                                components.add(_component_display(code, locator))
                        # Always include Pump if network exists
                        components.add('Pump')
                if 'building' in scales:
                    for bconfig in config_data.get('buildings', {}).values():
                        for svc_cfg in bconfig.values():
                            if not isinstance(svc_cfg, dict):
                                continue
                            if svc_cfg.get('scale') != 'BUILDING':
                                continue
                            for key in ('primary_component', 'secondary_component', 'tertiary_component'):
                                code = svc_cfg.get(key, '')
                                if code:
                                    components.add(_component_display(code, locator))
                if components:
                    component_sets.append(components)
            if not component_sets:
                return []
            shared = component_sets[0].intersection(*component_sets[1:])
            return sorted(shared)
        except Exception:
            return []

    empty_means_all = False

    def _validate_choices(self, value: list[str]) -> list[str]:
        # Choices are dynamic and may be unpopulated; skip validation
        return value


class MultiChoiceFeedstockParameter(MultiChoiceParameter):
    """
    Parameter for selecting feedstock options from available feedstock CSV files.

    Dynamically reads feedstock files from:
    {scenario}/inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/*.csv

    Returns a list of feedstock codes (e.g., ['GRID', 'NATURALGAS', 'SOLAR']).
    """

    def initialize(self, parser):
        """Override to skip setting _choices from config file - we compute it dynamically"""
        self.help = parser.get(self.section.name, f"{self.name}.help", fallback="")
        self.nullable = parser.getboolean(self.section.name, f"{self.name}.nullable", fallback=False)
        self.depends_on = parse_string_to_list(parser.get(self.section.name, f"{self.name}.depends-on", fallback=""))

    @property
    def _choices(self):
        """
        Dynamically scan feedstock directory for available feedstock CSV files.
        Reads fresh from filesystem each time (no caching).

        :return: List of feedstock codes (filenames without .csv extension)
        """
        import os
        import glob

        feedstock_dirs_to_try = []

        try:
            import cea.inputlocator
            locator = cea.inputlocator.InputLocator(self.config.scenario)

            # Current database structure: inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY
            scenario_feedstock_dir = os.path.join(
                cast(str, locator.scenario),
                'inputs',
                'database',
                'COMPONENTS',
                'FEEDSTOCKS',
                'FEEDSTOCKS_LIBRARY'
            )
            feedstock_dirs_to_try.append(scenario_feedstock_dir)
        except (AttributeError, Exception):
            pass

        # Fallback to default database
        try:
            import cea.databases
            default_db_path = os.path.dirname(cea.databases.__file__)
            default_feedstock_dir = os.path.join(
                default_db_path,
                'CH',
                'COMPONENTS',
                'FEEDSTOCKS',
                'FEEDSTOCKS_LIBRARY'
            )
            feedstock_dirs_to_try.append(default_feedstock_dir)
        except Exception:
            pass

        # Try each directory until we find one that exists
        for feedstock_dir in feedstock_dirs_to_try:
            if os.path.exists(feedstock_dir):
                csv_files = glob.glob(os.path.join(feedstock_dir, '*.csv'))
                if csv_files:
                    # Extract filenames without .csv extension
                    feedstocks = [os.path.splitext(os.path.basename(f))[0] for f in csv_files]
                    return sorted(feedstocks)

        return []


class DistrictSupplyTypeParameter(ChoiceParameter):
    """
    Parameter for selecting a single supply system assembly filtered by category and scale.

    Filters assemblies from the database based on:
    - supply-category: SUPPLY_COOLING, SUPPLY_HEATING, or SUPPLY_HOTWATER
    - scale: BUILDING or DISTRICT
    """

    def initialize(self, parser):
        """Get the supply category and scale from the parameter definition"""
        # Declare dependency so frontend refreshes choices when scenario changes
        self.depends_on = ['general:scenario']

        try:
            self.supply_category = parser.get(self.section.name, f"{self.name}.supply-category")
        except Exception:
            raise ValueError(f"Parameter {self.name} must have 'supply-category' attribute (SUPPLY_COOLING, SUPPLY_HEATING, or SUPPLY_HOTWATER)")

        try:
            self.scale = parser.get(self.section.name, f"{self.name}.scale")
            if self.scale not in ['BUILDING', 'DISTRICT']:
                raise ValueError(f"Parameter {self.name} must have 'scale' attribute set to 'BUILDING' or 'DISTRICT', got '{self.scale}'")
        except Exception:
            raise ValueError(f"Parameter {self.name} must have 'scale' attribute (BUILDING or DISTRICT)")

        # Log initialization for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"DistrictSupplyTypeParameter({self.name}) initialized: category={self.supply_category}, scale={self.scale}, nullable={self.nullable}")

    @property
    def _choices(self):
        """Get supply assembly codes filtered by category and scale"""
        try:
            import pandas as pd
            import logging
            logger = logging.getLogger(__name__)

            locator = cea.inputlocator.InputLocator(self.config.scenario)

            # Map category to locator method
            category_to_method = {
                'SUPPLY_COOLING': locator.get_database_assemblies_supply_cooling,
                'SUPPLY_HEATING': locator.get_database_assemblies_supply_heating,
                'SUPPLY_HOTWATER': locator.get_database_assemblies_supply_hot_water,
            }

            if self.supply_category not in category_to_method:
                logger.warning(f"DistrictSupplyTypeParameter({self.name}): Invalid supply_category '{self.supply_category}'")
                return []

            filepath = category_to_method[self.supply_category]()

            if not os.path.exists(filepath):
                logger.warning(f"DistrictSupplyTypeParameter({self.name}): File not found: {filepath}")
                return []

            df = pd.read_csv(filepath)

            # Filter by scale
            if 'scale' in df.columns and 'code' in df.columns:
                filtered = df[df['scale'] == self.scale]
                choices = sorted(filtered['code'].tolist())
                logger.debug(f"DistrictSupplyTypeParameter({self.name}): Found {len(choices)} choices for category={self.supply_category}, scale={self.scale}")
                return choices
            else:
                logger.warning(f"DistrictSupplyTypeParameter({self.name}): Missing 'scale' or 'code' columns in {filepath}")
                return []

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"DistrictSupplyTypeParameter({self.name}): Error getting choices: {e}", exc_info=True)
            return []

    @property
    def default(self):
        """Return None for empty defaults instead of empty string"""
        _default = self.config.default_config.get(self.section.name, self.name)
        if _default == '':
            return None
        return self.decode(_default)

    def encode(self, value):
        """Allow None/empty values for nullable parameter"""
        # Unwrap single-element list (frontend may send JSON arrays for single-choice parameters)
        if isinstance(value, list):
            value = value[0] if value else None

        # Handle None, empty strings, and string representations of null
        if self.nullable and (value is None or str(value).strip() in ['', 'null', 'None', 'Nothing Selected']):
            return ''
        return super().encode(value)

    def decode(self, value):
        """Allow empty values for nullable parameter, return None for empty"""
        # Handle empty strings and string representations of null
        if value is None or str(value).strip() in ['', 'null', 'None', 'Nothing Selected']:
            return None
        if str(value) in self._choices:
            return str(value)
        return None


class OrderedMultiChoiceParameter(MultiChoiceParameter):
    """Like MultiChoiceParameter, but it should TODO: display with selectable order in the dashboard"""
    typename = 'OrderedMultiChoiceParameter'


class SingleBuildingParameter(ChoiceParameter):
    """A (single) building in the zone"""

    @property
    def _choices(self):
        # set the `._choices` attribute to the list buildings in the project
        locator = cea.inputlocator.InputLocator(self.config.scenario, plugins=[])
        building_names = locator.get_zone_building_names()
        if not building_names:
            raise cea.ConfigError("Either no buildings in zone or no zone geometry found.")
        return building_names
    
    def decode(self, value):
        if self.nullable and (value is None or value == ''):
            return None
        return super().decode(value)

    def encode(self, value):
        if self.nullable and (value is None or value == ''):
            return ''
        if str(value) not in self._choices:
            return self._choices[0]
        return str(value)


class SingleThermalStorageParameter(ChoiceParameter):
    """A (single) building in the zone"""

    @property
    def _choices(self):
        # set the `._choices` attribute to the list buildings in the project
        locator = cea.inputlocator.InputLocator(self.config.scenario, plugins=[])
        thermal_storage_names = locator.get_database_conversion_systems_cold_thermal_storage_names()
        if not thermal_storage_names:
            raise cea.ConfigError("Either no thermal storage types or no database found - initialize databases")
        return thermal_storage_names

    def encode(self, value):
        if str(value) not in self._choices:
            return self._choices[0]
        return str(value)


class UseTypeRatioParameter(ListParameter):
    """A list of use-type names and ratios"""


class GenerationParameter(ChoiceParameter):
    """A (single) building in the zone"""

    @property
    def _choices(self):
        import glob
        # set the `._choices` attribute to the list buildings in the project
        locator = cea.inputlocator.InputLocator(self.config.scenario, plugins=[])
        checkpoints = glob.glob(os.path.join(locator.get_optimization_master_results_folder(), "*.json"))
        iterations = []
        for checkpoint in checkpoints:
            with open(checkpoint, 'rb') as f:
                data_checkpoint = json.load(f)
                iterations.extend(data_checkpoint['generation_to_show'])
        unique_iterations = list(set(iterations))
        unique_iterations = [str(x) for x in unique_iterations]
        return unique_iterations

    def encode(self, value):
        if str(value) in self._choices:
            return str(value)
        else:
            if not self._choices or len(self._choices) < 1:
                print(f"No choices for {self.fqname} to decode {value}")
                return ''
            else:
                return self._choices[0]

    def decode(self, value):
        if str(value) in self._choices:
            return str(value)
        else:
            if not self._choices or len(self._choices) < 1:
                print(f"No choices for {self.fqname} to decode {value}")
                return None
            else:
                return self._choices[0]


class SystemParameter(ChoiceParameter):
    """A (single) building in the zone"""

    @property
    def _choices(self):
        scenario = self.config.scenario
        unique_systems_scenario_list = ["_sys_today_"]
        unique_systems_scenario_list.extend(get_systems_list(scenario))
        return unique_systems_scenario_list

    def encode(self, value):
        if str(value) not in self._choices:
            if len(self._choices) > 1:
                return self._choices[1]
            return self._choices[0]
        return str(value)


class MultiSystemParameter(MultiChoiceParameter):
    """A (single) building in the zone"""

    @property
    def _choices(self):
        project_path = str(self.config.project)
        scenarios_names_list = get_scenarios_list(project_path)
        unique_systems_scenarios_list = []
        for scenario_name in scenarios_names_list:
            scenario_path = os.path.join(project_path, scenario_name)
            systems_scenario = get_systems_list(scenario_path)
            unique_systems_scenarios_list.extend([f"{scenario_name}_sys_today_"])
            unique_systems_scenarios_list.extend([f"{scenario_name}_{x}" for x in systems_scenario])
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

    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self._empty = False

    @property
    def _choices(self):
        # set the `._choices` attribute to the list buildings in the project
        locator = cea.inputlocator.InputLocator(self.config.scenario, plugins=[])
        return locator.get_zone_building_names()


class CoordinateListParameter(ListParameter):
    def encode(self, value):
        if isinstance(value, str):
            value = self.decode(value)
        strings = [str(validate_coord_tuple(coord_tuple)) for coord_tuple in value]
        return ', '.join(strings)

    def decode(self, value):
        coord_list = parse_string_coordinate_list(value)
        if len(set(coord_list)) < 3:
            raise ValueError(f"Requires 3 distinct coordinate points to create a polygon. Got: {coord_list}")
        return coord_list


def get_scenarios_list(project_path: str) -> List[str]:
    # TODO: Allow for remote projects
    normalized_path = os.path.normpath(project_path)

    if not os.path.exists(normalized_path):
        # return empty list if project path does not exist
        return []

    def is_valid_scenario(folder_name):
        """
        A scenario can't start with a `.` like `.config`
        A scenario must have an `inputs` folder inside it
        """
        folder_path = os.path.join(normalized_path, folder_name)

        # TODO: Use .gitignore to ignore scenarios
        return (
            os.path.isdir(folder_path)
            and (
                os.path.exists(os.path.join(folder_path, 'inputs')) or 
                os.path.exists(os.path.join(folder_path, 'export', 'rhino'))
                )
            and not folder_name.startswith(".")
            and folder_name != "__pycache__"
            and folder_name != "__MACOSX"
        )

    return sorted([folder_name for folder_name in os.listdir(normalized_path) if is_valid_scenario(folder_name)])


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


class ScenarioNameMultiChoiceParameter(ScenarioNameChoicesMixin, MultiChoiceParameter):
    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self.exclude_current = config.default_config.getboolean(section.name, f"{name}.exclude_current", fallback=False)


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


class ColumnChoicesMixin:
    _supported_extensions = ['.csv']

    config: Configuration
    section: Section
    name: str
    locator_method: str
    column_name: str
    kwargs: Dict[str, str]

    def _init_column_choices(self, name: str, section: Section, config: Configuration):
        self.locator_method = config.default_config.get(section.name, f"{name}.locator")
        self.column_name = config.default_config.get(section.name, f"{name}.column")
        self.kwargs = self._parse_kwargs(config.default_config.get(section.name, f"{name}.kwargs", fallback=None))

    @staticmethod
    def _parse_kwargs(value: str | None) -> Dict[str, str]:
        """
        Parses a list of key value pair string in the form of `key1=value1,key2=value2,...` to a dictionary
        """
        kwargs = dict()
        if value is None:
            return kwargs

        try:
            value = value.strip()

            if value:
                for kwarg in value.split(','):
                    key, value = kwarg.strip().split('=')
                    kwargs[key] = value

            return kwargs
        except Exception as e:
            raise ValueError(f'Could not parse kwargs: {e}, ensure it is in the form of `key1=value1,key2=value2,...`')

    @property
    def _choices(self):
        # set the `._choices` attribute to PV codes
        locator = cea.inputlocator.InputLocator(self.config.scenario)

        try:
            location = getattr(locator, self.locator_method)(**self.kwargs)
        except AttributeError as e:
            raise AttributeError(f'Invalid locator method {self.locator_method} given in config file, '
                                 f'check value under {self.section.name}.{self.name} in default.config') from e

        ext = os.path.splitext(location)[1]
        if ext not in self._supported_extensions:
            raise ValueError(f'Invalid file type {ext}, expected one of {self._supported_extensions}')

        try:
            import pandas as pd
            df = pd.read_csv(location)

            if self.column_name not in df.columns:
                raise ValueError(f'Column {self.column_name} not found in source file')

            codes = df[self.column_name].unique()
            return list(codes)
        except FileNotFoundError as e:
            # FIXME: This might cause default config to fail since the file does not exist, maybe should be a warning?
            raise FileNotFoundError(f'Could not find source file at {location} to generate choices for {self.name}') from e
        except Exception as e:
            raise ValueError(f'There was an error generating choices for {self.name} from {location}') from e


class ColumnChoiceParameter(ColumnChoicesMixin, ChoiceParameter):
    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self._init_column_choices(name, section, config)


class ColumnMultiChoiceParameter(ColumnChoicesMixin, MultiChoiceParameter):
    def __init__(self, name: str, section: Section, config: Configuration):
        super().__init__(name, section, config)
        self._init_column_choices(name, section, config)


class SolarPanelChoicesMixin:
    """
    Mixin for parameters that select solar technology types available in the scenario.
    Scans potentials/solar folder for PV, PVT, and SC results.

    Accepts both the current tech_code form (``SC_FP``, ``PV_PV1``) and the
    database ``code`` column (``SC1``, ``PV1``) — the latter are silently
    normalised to the tech_code the rest of the pipeline expects. This is a
    temporary bridge until the full namespace unification lands (see
    ``cea/technologies/solar/AGENTS.md``).
    """

    config: Configuration
    nullable: bool

    def initialize(self, parser):
        # Override to dynamically populate choices based on available solar results
        pass

    @property
    def _choices(self):
        return self._get_available_solar_technologies()

    def _get_available_solar_technologies(self) -> List[str]:
        """
        Scan potentials/solar folder for available solar technology results.
        Returns list of technology codes like: PV_PV1, PVT_PV1_FP, SC_FP, etc.
        """
        try:
            locator = cea.inputlocator.InputLocator(self.config.scenario)
            solar_folder = locator.get_potentials_solar_folder()

            if not os.path.exists(solar_folder):
                return []

            technologies = []

            for prefix in ('PV', 'PVT', 'SC'):
                for filepath in glob.glob(os.path.join(solar_folder, f'{prefix}_*_total.csv')):
                    tech_code = os.path.basename(filepath).replace('_total.csv', '')
                    technologies.append(tech_code)

            return sorted(set(technologies))
        except Exception:
            return []

    def _try_db_code_alias(self, value: str, choices: List[str]) -> Optional[str]:
        """Translate a bare database code (SC1, SC2, PV1, ...) into the
        tech_code form the dropdown emits (SC_FP, SC_ET, PV_PV1, ...).

        PVT is intentionally not aliased — a bare ``PVT1`` doesn't
        disambiguate which PV+SC pair was simulated.

        Returns the aliased tech_code if successful, else None. Safe to
        call with unknown values; returns None rather than raising.
        """
        if not value:
            return None

        # PV: PV1 -> PV_PV1 (works for any DB code starting with PV
        # except PVT, which needs a compound key). Cheap prefix rule;
        # no DB read required.
        if value.startswith('PV') and not value.startswith('PVT'):
            candidate = f'PV_{value}'
            if candidate in choices:
                return candidate

        # SC: SC1 -> look up `type` column in SOLAR_COLLECTORS.csv -> SC_{type}.
        # One DB read per resolve is cheap; cache the DataFrame on the
        # class to avoid re-reading for multi-choice lists.
        if value.startswith('SC') and not value.startswith('SC_'):
            sc_type = self._sc_type_for_code(value)
            if sc_type:
                candidate = f'SC_{sc_type}'
                if candidate in choices:
                    return candidate

        return None

    _sc_type_cache: Dict[str, Dict[str, str]] = {}

    def _sc_type_for_code(self, code: str) -> Optional[str]:
        """Return the `type` column value (FP / ET) for an SC `code`
        (SC1 / SC2) from SOLAR_COLLECTORS.csv. Returns None if the
        database isn't readable or the code isn't present."""
        scenario = getattr(self.config, 'scenario', None)
        if not scenario:
            return None

        mapping = self._sc_type_cache.get(scenario)
        if mapping is None:
            mapping = {}
            try:
                import pandas as pd
                locator = cea.inputlocator.InputLocator(scenario)
                db_path = locator.get_db4_components_conversion_conversion_technology_csv(
                    'SOLAR_COLLECTORS'
                )
                if os.path.exists(db_path):
                    df = pd.read_csv(db_path)
                    if 'code' in df.columns and 'type' in df.columns:
                        mapping = dict(zip(df['code'], df['type']))
            except Exception:
                mapping = {}
            self._sc_type_cache[scenario] = mapping

        return mapping.get(code)

    def _encode_solar(self, value) -> str:
        """Encode a single solar technology value, respecting nullable.

        Accepts DB-code aliases (SC1, SC2, PV1, ...) and normalises them
        to the tech_code form before validating against the dropdown.
        """
        if value is None or value == '':
            return ''
        value = str(value)
        choices = self._choices
        if value in choices:
            return value

        aliased = self._try_db_code_alias(value, choices)
        if aliased is not None:
            return aliased

        if choices:
            raise ValueError(
                f"Invalid solar technology '{value}'. "
                f"Available: {', '.join(choices) or 'none'}"
            )
        return value

    def _decode_solar_single(self, value):
        """Decode a single solar technology value, returning None for
        empty/invalid. Accepts DB-code aliases like `_encode_solar`."""
        if value == '':
            return None
        value = str(value)
        choices = self._choices
        if value in choices:
            return value
        aliased = self._try_db_code_alias(value, choices)
        if aliased is not None:
            return aliased
        return None

class SolarPanelChoiceParameter(SolarPanelChoicesMixin, ChoiceParameter):
    """
    Nullable parameter for selecting a solar technology type available in the scenario.
    Scans potentials/solar folder for PV, PVT, and SC results.
    """

    @property
    def default(self):
        _default = self.config.default_config.get(self.section.name, self.name)
        if _default == '':
            return None
        return self.decode(_default)

    def encode(self, value):
        return self._encode_solar(value)

    def decode(self, value):
        return self._decode_solar_single(value)


class SolarPanelMultiChoiceParameter(SolarPanelChoicesMixin, MultiChoiceParameter):
    """
    Multi-choice version of SolarPanelChoiceParameter.
    Allows selecting multiple solar technology types from available results.
    """

    empty_means_all = False
    strict_validation = True


class PlotContextParameter(Parameter):
    """A parameter that accepts a dict containing plot context information."""
    
    def encode(self, value) -> str:
        if not isinstance(value, dict):
            raise ValueError(f"Expected a dict for plot context, got {type(value)}")
        return json.dumps(value)

    def decode(self, value) -> dict[str, Any]:
        try:
            return json.loads(value) if value else {}
        except json.JSONDecodeError as e:
            raise ValueError("Could not decode plot context dict. Ensure it is a valid JSON string,"
                             "using double quotes for keys and string values.") from e


def validate_coord_tuple(coord_tuple):
    """Validates a (lat, long) tuple, throws exception if not valid"""

    lon, lat = coord_tuple
    if lat < -90 or lat > 90:
        raise ValueError(f"Latitude must be between -90 and 90. Got {lat}")
    if lon < -180 or lon > 180:
        raise ValueError(f"Longitude must be between -180 and 180. Got {lon}")
    return coord_tuple
