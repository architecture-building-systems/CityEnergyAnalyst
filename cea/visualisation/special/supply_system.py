import cea.config
from cea.plots.optimization_new.b_supply_system import main as supply_system_main

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config):
    fig =  supply_system_main(config)

    return fig.to_html() if fig is not None else ""


if __name__ == '__main__':
    main(cea.config.Configuration())
