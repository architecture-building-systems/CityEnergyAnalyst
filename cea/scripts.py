"""
Provides the list of scripts known to the CEA - to be used by interfaces built on top of the CEA.
"""


import os
from typing import List

import yaml
import cea
import cea.inputlocator
from cea.schemas import schemas

SCRIPTS_YML = os.path.abspath(os.path.join(os.path.dirname(cea.__file__), 'scripts.yml'))


class CeaScript(object):
    def __init__(self, script_dict, category):
        self.name = script_dict['name']
        self.module = script_dict['module']
        self.description = script_dict.get('description', '')
        self.short_description = script_dict.get('short_description', '')
        self.interfaces = script_dict.get('interfaces', ['cli'])
        self.label = script_dict.get('label', self.name)
        self.category = category
        self.parameters = self._ensure_parameters_order(script_dict.get('parameters', []))
        self.input_files = script_dict.get('input-files', [])

    def __repr__(self):
        return '<cea %s>' % self.name

    @staticmethod
    def _ensure_parameters_order(parameters: List[str]) -> List[str]:
        """
        Ensure that the first parameter is `general:scenario` and move it to the first position.
        Some parameters depend on the scenario parameter, so it should be the first parameter to be set.

        That also means that order of parameters are important if there are dependencies between them.
        # TODO: Add tests for this
        """
        # Ignore if there is only one parameter
        if len(parameters) <= 1:
            return parameters

        try:
            scenario_in_parameters = parameters.index("general:scenario")
        except ValueError:
            # Ignore if scenario is not in parameters
            return parameters

        if scenario_in_parameters != 0:
            # Move scenario parameter to the first position, since some parameters could depend on it.
            parameters.insert(0, parameters.pop(scenario_in_parameters))

        return parameters


    def print_script_configuration(self, config, verb='Running'):
        """
        Print a list of script parameters being used for this run of the tool. Historically, each tool
        was responsible for printing their own parameters, but that requires manually keeping track of these
        parameters.
        """
        print('City Energy Analyst version %s' % cea.__version__)
        script_name = self.name
        print("%(verb)s `cea %(script_name)s` with the following parameters:" % locals())
        for section, parameter in config.matching_parameters(self.parameters):
            section_name = section.name
            parameter_name = parameter.name
            parameter_value = parameter.get()
            print("- %(section_name)s:%(parameter_name)s = %(parameter_value)s" % locals())
            print("  (default: %s)" % parameter.default)

    def print_missing_input_files(self, config):
        schema_data = schemas(config.plugins)
        print()
        print("---------------------------")
        print("ERROR: Missing input files:")
        for method_name, path in self.missing_input_files(config):
            script_suggestions = (schema_data[method_name]['created_by']
                                  if 'created_by' in schema_data[method_name]
                                  else None)
            print('- {path}'.format(path=path))
            if script_suggestions:
                print('  (HINT: try running {scripts})'.format(scripts=', '.join(script_suggestions)))

    def missing_input_files(self, config):
        """
        Return a list of bound :py:class:`cea.inputlocator.InputLocator` method names, one for each file required as
        input for this script that is not present yet as well as the applied path searched for.
        :return: Sequence[str]
        """
        # get a locator without triggering the restricted to
        restricted_to = config.restricted_to
        config.restricted_to = None
        locator = cea.inputlocator.InputLocator(config.scenario, config.plugins)
        config.restricted_to = restricted_to

        for locator_spec in self.input_files:
            method_name, args = locator_spec[0], locator_spec[1:]
            method = getattr(locator, method_name)
            path = method(*self._lookup_args(config, locator, args))
            if not os.path.exists(os.path.abspath(os.path.normpath(os.path.expanduser(path)))):
                yield [method_name, path]

    def _lookup_args(self, config, locator, args):
        """returns a list of arguments to a locator method"""
        result = []
        for arg in args:
            if arg == 'building_name':
                result.append(locator.get_zone_building_names()[0])
            else:
                # expect an fqname for the config object
                result.append(config.get(arg))
        return result


def list_scripts(plugins):
    """List all scripts in scripts.yml and those defined in configured plugins
    :parameter List[CeaPlugin] plugins: the list of plugins to include in the search for scripts.
    """
    with open(SCRIPTS_YML, "r") as fp:
        scripts_by_category = yaml.load(fp, Loader=yaml.CLoader)
    for plugin in plugins:
        scripts_by_category.update(plugin.scripts)

    for category in scripts_by_category.keys():
        for script_dict in scripts_by_category[category]:
            yield CeaScript(script_dict, category)


def by_name(script_name, plugins=None):
    """
    Returns a CeaScript object by name.

    :parameter str script_name: The name of the script to return (e.g. "demand")
    :parameter List[CeaPlugin]: The list of plugins to include in the search.
    """
    if plugins is None:
        plugins = []

    for script in list_scripts(plugins):
        # Convert script names that use "_" instead of "-"
        if script.name == script_name.replace("_", "-"):
            return script
    raise cea.ScriptNotFoundException('Invalid script name: %s' % script_name)


def for_interface(interface, plugins):
    """Return the list of CeaScript instances that are listed for the interface

    :parameter str interface: The interface to filter the scripts by (see interfaces key in scripts.yml) e.g. "cli"
    :parameter List[CeaPlugin] plugins: The list of plugins to include in the search.
    """
    return [script for script in list_scripts(plugins) if interface in script.interfaces]


