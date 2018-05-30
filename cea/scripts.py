"""
Provides the list of scripts known to the CEA - to be used by interfaces built on top of the CEA.
"""
import os
import yaml


class CeaScript(object):
    def __init__(self, name, values):
        self.name = name
        self.module = values['module']
        self.category = values.get('category', 'default')
        self.description = values.get('description', '')
        self.interfaces = values.get('interfaces', ['cli'])
        self.label = values.get('label', self.name)

    def __repr__(self):
        return '<cea %s>' % self.name


def list_scripts():
    """List all scripts"""
    scripts_yml = os.path.join(os.path.dirname(__file__), 'scripts.yml')
    for name, values in yaml.load(open(scripts_yml)).items():
        yield CeaScript(name, values)


def for_interface(interface='cli'):
    """Return the list of CeaScript instances that are listed for the interface"""
    return [script for script in list_scripts() if interface in script.interfaces]