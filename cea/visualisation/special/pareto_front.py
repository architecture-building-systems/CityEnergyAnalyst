import cea.config
from cea.plots.optimization_new.a_pareto_front import main as pareto_front_main

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config: cea.config.Configuration):
    plot_2d, plot_3d =  pareto_front_main(config)

    return plot_2d.to_html(), plot_3d.to_html() if plot_3d is not None else ""

if __name__ == '__main__':
    main(cea.config.Configuration())
