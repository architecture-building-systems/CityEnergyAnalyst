"""
A base class for creating CEA plugins. Subclass this class in your own namespace to become a CEA plugin.
"""

import configparser
import importlib
import inspect
import os
import warnings

import yaml

import cea.inputlocator
import cea.plots.categories
import cea.schemas
from cea.plots.base import PlotBase
from cea.utilities import identifier

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
            scripts = yaml.safe_load(scripts_yml_fp)
        return scripts

    @property
    def plot_categories(self):
        """
        Return a list of :py:class`cea.plots.PlotCategory` instances to add to the GUI. The default implementation
        uses the ``plots.yml`` file to create PluginPlotCategory instances that use PluginPlotBase.
        """
        plots_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "plots.yml")
        if not os.path.exists(plots_yml):
            return {}
        with open(plots_yml, "r") as plots_yml_fp:
            categories = yaml.load(plots_yml_fp, Loader=yaml.CLoader)
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
            schemas = yaml.load(schemas_yml_fp, Loader=yaml.CLoader)
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


class PluginPlotCategory(cea.plots.categories.PlotCategory):
    """
    Normally, a PlotCategory reads its plot classes by traversing a folder structure and importing all modules found
    there. The PluginPlotCategory works just like a PlotCategory (i.e. compatible with the CEA GUI / Dashboard) but
    the category information and plots are loaded from a ``plots.yml`` file. Plugin Plots are a bit restricted (so
    you might want to implement your plots directly the way they are implemented in CEA)
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
                if "scenario-name" not in expected_parameters:
                    expected_parameters["scenario-name"] = "general:scenario-name"

                def __init__(self, project, parameters, cache):
                    super(Plot, self).__init__(project, parameters, cache, plugin, plot_config)

                    # for some reason these are being over-written in the call to super
                    self.category_name = category.name
                    self.category_path = category.name

            # Plot.__name__ = identifier(plot_label, sep="_")
            yield Plot


class PluginPlotBase(PlotBase):
    """
    A simplified version of cea.plots.PlotBase that is configured with the ``plots.yml`` entries.
    """

    def __init__(self, project, parameters, cache, plugin, plot_config):
        super(PluginPlotBase, self).__init__(project, parameters, cache)
        self.plugin = plugin
        self.plot_config = plot_config
        self.locator_method = getattr(self.locator, self.plot_config["data"]["location"])  # type: cea.schemas.SchemaIo
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
            raise KeyError("{key} not found in {parameters}".format(key=str(error), parameters=self.parameters))

    @property
    def layout(self):
        return self.plot_config.get("layout", {})

    def _plot_div_producer(self):
        import plotly

        # load the data
        df = self.locator_method.read(**self.locator_kwargs)
        if "index" in self.plot_config["data"]:
            df = df.set_index(self.plot_config["data"]["index"])
        if "fields" in self.plot_config["data"]:
            df = df[self.plot_config["data"]["fields"]]

        # rename the columns (for the legend)
        schema = self.locator_method.schema["schema"]["columns"]
        columns_mapping = {c: schema[c]["description"] for c in schema.keys()}
        df = df.rename(columns=columns_mapping)

        # colors need to be re-mapped because we renamed the columns
        colors = {columns_mapping[k]: v for k, v in self.locator_method.colors().items()}

        fig = df.iplot(asFigure=True, colors=colors, theme="white", **self.layout)
        div = plotly.io.to_html(fig, full_html=False, include_plotlyjs=False)
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
        warnings.warn(f"Could not instantiate plugin {plugin_fqname} ({ex})")
        return None


def add_plugins(default_config, user_config):
    """
    Patch in the plugin configurations during __init__ and __setstate__

    :param configparser.ConfigParser default_config:
    :param configparser.ConfigParser user_config:
    :return: (modifies default_config and user_config in-place)
    :rtype: None
    """
    plugin_fqnames = cea.config.parse_string_to_list(user_config.get("general", "plugins"))
    for plugin in [instantiate_plugin(plugin_fqname) for plugin_fqname in plugin_fqnames]:
        if plugin is None:
            # plugin could not be instantiated
            continue
        for section_name in plugin.config.sections():
            if section_name in default_config.sections():
                raise ValueError("Plugin tried to redefine config section {section_name}".format(
                    section_name=section_name))
            default_config.add_section(section_name)
            if not user_config.has_section(section_name):
                user_config.add_section(section_name)
            for option_name in plugin.config.options(section_name):
                if option_name in default_config.options(section_name):
                    raise ValueError("Plugin tried to redefine parameter {section_name}:{option_name}".format(
                        section_name=section_name, option_name=option_name))
                default_config.set(section_name, option_name, plugin.config.get(section_name, option_name))
                if "." not in option_name and not user_config.has_option(section_name, option_name):
                    user_config.set(section_name, option_name, default_config.get(section_name, option_name))
