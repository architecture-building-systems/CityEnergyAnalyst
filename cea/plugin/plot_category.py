import os

import cea.inputlocator
import cea.schemas

from cea.plots.base import PlotBase
from cea.plots.categories import PlotCategory
from cea.utilities import identifier


class PluginPlotCategory(PlotCategory):
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


