"""
A base class for creating CEA plugins. Subclass this class in your own namespace to become a CEA plugin.
"""

import configparser
import inspect
import os

import yaml


__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class CeaPlugin:
    """
    A CEA Plugin defines a list of scripts and a list of plots - the CEA uses this to populate the GUI
    and other interfaces. In addition, any input- and output files need to be defined.
    """

    @property
    def scripts(self):
        """Return the scripts.yml dictionary."""
        scripts_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "scripts.yml")
        if not os.path.exists(scripts_yml):
            return {}
        with open(scripts_yml, "r") as scripts_yml_fp:
            scripts = yaml.safe_load(scripts_yml_fp) or {}
        return scripts

    @property
    def plot_categories(self):
        """
        Return a list of :py:class`cea.plots.PlotCategory` instances to add to the GUI. The default implementation
        uses the ``plots.yml`` file to create PluginPlotCategory instances that use PluginPlotBase.
        """
        from .plot_category import PluginPlotCategory

        plots_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "plots.yml")
        if not os.path.exists(plots_yml):
            return []
        with open(plots_yml, "r") as plots_yml_fp:
            categories = yaml.safe_load(plots_yml_fp) or {}
        return [PluginPlotCategory(category_label, categories[category_label], self) for category_label in
                categories.keys()]

    @property
    def schemas(self):
        """Return the schemas dict for this plugin - it should be in the same format as ``cea/schemas.yml``

        (You don't actually have to implement this for your own plugins - having a ``schemas.yml`` file in the same
        folder as the plugin class will trigger the default behavior)
        """
        schemas_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "schemas.yml")
        if not os.path.exists(schemas_yml):
            return {}
        with open(schemas_yml, "r") as schemas_yml_fp:
            schemas = yaml.safe_load(schemas_yml_fp) or {}
        return schemas

    @property
    def config(self):
        """
        Return the configuration for this plugin - the `cea.config.Configuration` object will include these.

        The format is expected to be the same format as `default.config` in the CEA.

        :rtype: configparser.ConfigParser
        """

        plugin_config = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "plugin.config")
        parser = configparser.ConfigParser()
        if not os.path.exists(plugin_config):
            return parser
        parser.read(plugin_config)
        return parser

    def __str__(self):
        """To enable encoding in cea.config.PluginListParameter, return the fqname of the class"""
        return "{module}.{name}".format(module=self.__class__.__module__, name=self.__class__.__name__)
