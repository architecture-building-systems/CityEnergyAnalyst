"""
Provides the list of scripts known to the CEA - to be used by interfaces built on top of the CEA.
"""
import os
import yaml


class CeaScript(object):
    def __init__(self, script_dict):
        self.name = script_dict['name']
        self.module = script_dict['module']
        self.category = script_dict.get('category', 'default')
        self.description = script_dict.get('description', '')
        self.interfaces = script_dict.get('interfaces', ['cli'])
        self.label = script_dict.get('label', self.name)

    def __repr__(self):
        return '<cea %s>' % self.name


def list_scripts():
    """List all scripts"""
    scripts_yml = os.path.join(os.path.dirname(__file__), 'scripts.yml')
    for script_dict in yaml.load(open(scripts_yml)):
        yield CeaScript(script_dict)


def by_name(script_name):
    for script in list_scripts():
        if script.name == script_name:
            return script
    return None


def for_interface(interface='cli'):
    """Return the list of CeaScript instances that are listed for the interface"""
    return [script for script in list_scripts() if interface in script.interfaces]