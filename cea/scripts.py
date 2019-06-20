"""
Provides the list of scripts known to the CEA - to be used by interfaces built on top of the CEA.
"""
from __future__ import print_function

import os
import cea
import cea.inputlocator


class CeaScript(object):
    def __init__(self, script_dict, category):
        self.name = script_dict['name']
        self.module = script_dict['module']
        self.description = script_dict.get('description', '')
        self.interfaces = script_dict.get('interfaces', ['cli'])
        self.label = script_dict.get('label', self.name)
        self.category = category
        self.parameters = script_dict.get('parameters', [])
        self.input_files = script_dict.get('input-files', [])

    def __repr__(self):
        return '<cea %s>' % self.name

    def print_script_configuration(self, config, verb='Running'):
        """
        Print a list of script parameters being used for this run of the tool. Historically, each tool
        was responsible for printing their own parameters, but that requires manually keeping track of these
        parameters.
        """
        default_config = cea.config.Configuration(config_file=cea.config.DEFAULT_CONFIG)
        print('City Energy Analyst version %s' % cea.__version__)
        script_name = self.name
        print("%(verb)s `cea %(script_name)s` with the following parameters:" % locals())
        for section, parameter in config.matching_parameters(self.parameters):
            section_name = section.name
            parameter_name = parameter.name
            parameter_value = parameter.get()
            print("- %(section_name)s:%(parameter_name)s = %(parameter_value)s" % locals())
            print("  (default: %s)" % default_config.get(parameter.fqname))

    def print_missing_input_files(self, config):
        schema_data = schemas()
        print()
        print("---------------------------")
        print("ERROR: Missing input files:")
        for method_name, path in self.missing_input_files(config):
            script_suggestions = (schema_data[method_name]['created_by']
                                  if 'created_by' in schema_data[method_name]
                                  else None)
            print('- {path}'.format(path=path))
            if script_suggestions:
                print('  - try running {scripts}'.format(path=path, scripts=', '.join(script_suggestions)))

    def missing_input_files(self, config):
        """
        Return a list of bound :py:class:`cea.inputlocator.InputLocator` method names, one for each file required as
        input for this script that is not present yet as well as the applied path searched for.
        :return: Sequence[str]
        """
        locator = cea.inputlocator.InputLocator(config.scenario)
        for locator_spec in self.input_files:
            method_name, args = locator_spec[0], locator_spec[1:]
            method = getattr(locator, method_name)
            path = method(*self._lookup_args(config, locator, args))
            if not os.path.exists(path):
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


def _get_categories_dict():
    """Load the categories -> [script] mapping either from the YAML file or, in the case of arcgis / grasshopper,
    which don't support YAML, load from a pickled version generated on the call to ``cea install-toolbox``."""
    scripts_yml = os.path.join(os.path.dirname(__file__), 'scripts.yml')
    scripts_pickle = os.path.join(os.path.dirname(__file__), 'scripts.pickle')
    try:
        import yaml
        categories = yaml.load(open(scripts_yml))
    except ImportError:
        import pickle
        categories = pickle.load(open(scripts_pickle))
    return categories


def list_scripts():
    """List all scripts"""
    categories = _get_categories_dict()
    for category in categories.keys():
        for script_dict in categories[category]:
            yield CeaScript(script_dict, category)


def by_name(script_name):
    for script in list_scripts():
        if script.name == script_name:
            return script
    raise cea.ScriptNotFoundException('Invalid script name: %s' % script_name)


def for_interface(interface='cli'):
    """Return the list of CeaScript instances that are listed for the interface"""
    return [script for script in list_scripts() if interface in script.interfaces]


def schemas():
    """Return the contents of the schemas.yml file"""
    import yaml
    schemas_yml = os.path.join(os.path.dirname(__file__), 'schemas.yml')
    return yaml.load(open(schemas_yml))