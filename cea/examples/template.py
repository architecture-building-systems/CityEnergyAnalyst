"""
This is a template script - an example of how a CEA script should be set up.

Add such a script by appending to the ``cea/cli.config`` file like this:

.. source::

    [scripts]
    template = cea.example.template
    template.sections = general:scenario general:region data-helper

In the above example, ``template`` is the name of the script (as in ``cea template``) and ``template.sections``
refers to the list of sections in the default.config file that this script uses as parameters. If you only need some
parameters from a section, you can use the form ``section:key`` to specify a specific parameter in a section.
"""
from __future__ import division

import os
import cea.config
import cea.inputlocator

def template(locator, archetypes):
    # this is where the action happens if it is more than a few lines in ``main``.
    pass


def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line - this is how the ArcGIS interface interacts with the scripts
    BTW.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running template for scenario = %s" % config.scenario)
    print("Running template with archetypes = %s" % config.data_helper.archetypes)

    template(locator, config.archetypes)


if __name__ == '__main__':
    main(cea.config.Configuration())
