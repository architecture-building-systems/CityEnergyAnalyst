"""
A base class for creating CEA plugins. Subclass this class in your own namespace to become a CEA plugin.
"""
from __future__ import print_function
from __future__ import division

import importlib
import os
from typing import Generator, Sequence
import yaml
import inspect
import cea.plots.categories
import cea.inputlocator
from cea.utilities.yaml_ordered_dict import OrderedDictYAMLLoader
from cea.utilities import identifier

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class CeaPlugin(object):
    """
    A CEA Plugin defines a list of scripts and a list of plots - the CEA uses this to populate the GUI
    and other interfaces. In addition, any input- and output files need to be defined.
    """

    @property
    def scripts(self):
        """Return the scripts.yml dictionary."""
        scripts_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "scripts.yml")
        with open(scripts_yml, "r") as scripts_yml_fp:
            scripts = yaml.load(scripts_yml_fp, OrderedDictYAMLLoader)
        return scripts

    @property
    def plot_categories(self):
        """
        Return a list of :py:class`cea.plots.PlotCategory` instances to add to the GUI. The default implementation
        uses the ``plots.yml`` file to create PluginPlotCategory instances that use PluginPlotBase to provide a
        simplified plot mechanism using cufflinks_

        .. _cufflinks: https://plotly.com/python/cufflinks/
        """
        plots_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "plots.yml")
        with open(plots_yml, "r") as plots_yml_fp:
            categories = yaml.load(plots_yml_fp, OrderedDictYAMLLoader)
        return [PluginPlotCategory(category_label, categories[category_label], self) for category_label in categories.keys()]

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


class PluginPlotCategory(cea.plots.categories.PlotCategory):
    """
    Normally, a PlotCategory reads it's plot classes by traversing a folder structure and importing all modules found
    there. The PluginPlotCategory works just like a PlotCategory (i.e. compatible with the CEA GUI / Dashboard) but
    the category information and plots are loaded from a ``plots.yml`` file. Plugin Plots are a bit restricted (so
    you might want to implement your plots directly the way they are implemented in CEA) but instead they are much
    easier to understand as they use the cufflinks library.
    """

    def __init__(self, category_label, plots, plugin):
        """Ignore calling super class' constructor as we use a totally different mechanism for building plots here
        :param str category_label: The category label shown in the interface
        :param Sequence[dict] plots: A dictionary mapping plot labels to plot definitions
        """
        self.label = category_label
        self.name = identifier(category_label)
        self.plot_configs = plots
        self.plugin = plugin

    @property
    def plots(category):
        """
        Return a list of Plot classes to be used in the Dashboard.

        :rtype: Generator[PluginPlotBase]
        """
        for plot_config in category.plot_configs:
            plot_label = plot_config["label"]
            plugin = category.plugin

            class Plot(PluginPlotBase):
                name = plot_label
                category_name = category.name
                category_path = category.name
                expected_parameters = plot_config.get("expected-parameters", {})
                if not "scenario-name" in expected_parameters:
                    expected_parameters["scenario-name"] = "general:scenario-name"

                def __init__(self, project, parameters, cache):
                    super(Plot, self).__init__(project, parameters, cache, plugin, plot_config)

                    # for some reason these are being over-written in the call to super
                    self.category_name = category.name
                    self.category_path = category.name

            # Plot.__name__ = identifier(plot_label, sep="_")
            yield Plot


class PluginPlotBase(cea.plots.PlotBase):
    """
    A simplified version of cea.plots.PlotBase that is configured with the ``plots.yml`` entries.
    """
    def __init__(self, project, parameters, cache, plugin, plot_config):
        super(PluginPlotBase, self).__init__(project, parameters, cache)
        self.plugin = plugin
        self.plot_config = plot_config
        self.locator_method = getattr(self.locator, self.plot_config["data"]["location"])
        self.locator_kwargs = {arg: self.parameters[arg] for arg in self.plot_config["data"].get("args", [])}
        self.input_files = [(self.locator_method, self.locator_kwargs)]

    def missing_input_files(self):
        """
        Return the list of missing input files for this plot - overriding cea.plots.PlotBase.missing_input_files
        because we're now moving to kwargs for locator methods.

        Also, PluginPlotBase only uses one input file.
        """
        result = []
        if not os.path.exists(self.locator_method(**self.locator_kwargs)):
            result.append((self.locator_method, self.locator_kwargs.values()))
        return result

    @property
    def title(self):
        return self.plot_config["label"]

    @property
    def locator(self):
        """
        Make sure the plot's input-locator is aware of the plugin that defines it.

        NOTE: We don't currently support depending on other plugins.

        :rtype: cea.inputlocator.InputLocator
        """
        try:
            scenario = os.path.join(self.project, self.parameters['scenario-name'])
            return cea.inputlocator.InputLocator(scenario=scenario, plugins=[self.plugin])
        except KeyError as error:
            raise KeyError("{key} not found in {parameters}".format(key=error.message, parameters=self.parameters))

    @property
    def layout(self):
        """The layout for plugin plots needs to conform to the input parameters to iplot (see cufflinks docs)"""
        return self.plot_config.get("layout", {})

    def _plot_div_producer(self):
        """Use the plot_config to create a plot with cufflinks"""
        import cufflinks
        import plotly.offline

        cufflinks.go_offline()

        df = self.locator_method.read(**self.locator_kwargs)
        fig = df.iplot(asFigure=True, **self.layout)
        div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
        return div

    def table_div(self):
        pass

    def calc_graph(self):
        raise AssertionError("cea.plots.PlotBase.calc_graph should not be part of the abstract interface")

    def calc_table(self):
        raise DeprecationWarning("cea.plots.PlotBase.calc_table is not used anymore and will be removed in future")

    @property
    def output_path(self):
        """override the cea.plots.PlotBase.output_path"""
        file_name = self.id()
        return self.locator.get_timeseries_plots_file(file_name, self.category_path)


if __name__ == "__main__":
    # try to plot the first plugin found
    # FIXME: remove this before commit
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    plugin = config.plugins[0]
    category = list(plugin.plot_categories)[0]
    plot_class = list(category.plots)[0]

    print(plot_class.expected_parameters)
    print(plot_class.name)
    print(plot_class.category_path)

    plot = plot_class(config.project, {"scenario-name": config.scenario_name}, cache)
    print(plot.category_path)
    print(plot.plot(auto_open=True))


def instantiate_plugin(plugin_fqname):
    """Return a new CeaPlugin based on it's fully qualified name - this is how the config object creates plugins"""
    try:
        plugin_path = plugin_fqname.split(".")
        plugin_module = ".".join(plugin_path[:-1])
        plugin_class = plugin_path[-1]
        module = importlib.import_module(plugin_module)
        instance = getattr(module, plugin_class)()
        return instance
    except BaseException as ex:
        raise ValueError("Could not instantiate plugin {plugin_fqname} ({msg})".format(
            plugin_fqname=plugin_fqname, msg=ex.message))