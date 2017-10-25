"""
This is a template script - an example of how a CEA script should be set up.

Add such a script by adding a line to the ``default.config`` file like this:

.. source::

    [scripts]
    template = cea.example.template
"""
import sys
import cea.config
import cea.inputlocator

# list the sections in the configuration file that are used by this script
CEA_CONFIG_SECTIONS = ['general:scenario', 'general:region', 'data-helper']


def template(scenario, archetypes):
    # is this where the action happens????
    pass


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    template(config.scenario, config.archetypes)


if __name__ == '__main__':
    main(cea.config.Configuration(sys.argv))
