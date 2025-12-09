"""
Load all the plot classes and generate the plots for test purposes

(This is run at the end of ``cea test --workflow slow`` as it requires a scenario with all the data from the
whole workflow to be present)
"""





import shutil
import tempfile
import cea.plots
import cea.plots.cache
import cea.config
import cea.workflows.workflow

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config: cea.config.Configuration):
    cache_folder = tempfile.mkdtemp()
    plot_cache = cea.plots.cache.MemoryPlotCache(cache_folder)

    with config.ignore_restrictions():
        if config.plots_supply_system.system == "_sys_today_":
            # BUGFIX: _sys_today_ not supported
            config.plots_supply_system.system = ""

    try:
        for category in cea.plots.categories.list_categories(plugins=[]):
            # create the new dashboard
            print("Plotting category {category}".format(category=category.label))

            for plot_class in category.plots:
                print("- Plotting {plot_class}".format(plot_class=plot_class.__name__))
                parameters = {k: config.get(v) for k, v in plot_class.expected_parameters.items() }
                plot = plot_class(config.project, parameters, plot_cache)
                print("    - plotting to {output_path}".format(output_path=plot.output_path))
                plot.plot()
                print("    - plotting div (len={len})".format(len=len(plot.plot_div())))
    finally:
        shutil.rmtree(cache_folder, ignore_errors=True)


if __name__ == "__main__":
    main(cea.config.Configuration())