"""
A base class for creating CEA plugins. Subclass this class in your own namespace to become a CEA plugin.
"""
from __future__ import print_function
from __future__ import division

import os
import yaml
import inspect


__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


### NOTE / FIXME: have this class read in the scripts.yml and schemas.yml. plots need to be python classes.


class CeaPlugin(object):
    """
    A CEA Plugin defines a list of scripts and a list of plots - the CEA uses this to populate the GUI
    and other interfaces. In addition, any input- and output files need to be defined.
    """

    @property
    def scripts(self):
        """Return a list of scripts - each is a subclass of :py:class`cea.scripts.CeaScript`"""
        return []

    @property
    def plots(self):
        """Return a list of plots - each is a subclass of :py:class:`cea.plots.base`"""
        return []

    @property
    def schemas(self):
        """Return the schemas dict for this plugin - it should be in the same format as ``cea/schemas.yml``

        (You don't actually have to implement this for your own plugins - having a ``schemas.yml`` file in the same
        folder as the plugin class will trigger the default behavior)
        """
        schemas_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "schemas.yml")
        with open(schemas_yml, "r") as schemas_yml_fp:
            schemas = yaml.load(schemas_yml_fp, Loader=yaml.CLoader)
        return schemas

    def __str__(self):
        """To enable encoding in cea.config.PluginListParameter, return the fqname of the class"""
        return "{module}.{name}".format(module=self.__class__.__module__, name=self.__class__.__name__)