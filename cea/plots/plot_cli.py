"""
Provide a cli interface to plotting - for testing plots from the command line.

Useage: cea-plot CATEGORY PLOT-ID [--PARAMETER VALUE]*

(e.g. cea-plot energy-demand energy-balance --building B001 --scenario-name baseline)
"""

from __future__ import print_function
from __future__ import division

import sys
import cea.config
import cea.plots.categories
import cea.inputlocator
import cea.plots.cache
import cea.plots.base

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(*args):
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()

    # handle arguments
    if not args:
        args = sys.argv[1:]  # drop the script name (plot_cli.py) from the arguments
    category_name, plot_id, plot_args = args[0], args[1], args[2:]

    plot_class = cea.plots.categories.load_plot_by_id(category_name, plot_id, config.plugins)
    if not plot_class:
        print("Could not load plot {category_name}/{plot_id}".format(**locals()))
        print("Choose from:")
        for plot_category, plot_class in cea.plots.categories.list_plots(config.plugins):
            print("{category}/{plot}".format(category=plot_category.name, plot=plot_class.id()))
        return

    parameters = {k: config.get(v) for k, v in plot_class.expected_parameters.items() }
    parameters.update(cea.config.parse_command_line_args(plot_args))
    plot = plot_class(config.project, parameters, cache)
    plot.plot(auto_open=True)


if __name__ == "__main__":
    main("demand-summary", "total-system-demand")