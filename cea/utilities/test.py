"""
Test all the main scripts in one go - drink coffee while you wait :)
"""
import embodied

from cea import demand
from cea.analysis import emissions, mobility
from cea.preprocessing import properties
from cea.plots import graphs, benchmark, scenario_plots
from cea.resources import radiation

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"

__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

properties.test_properties()
radiation.test_solar_radiation()
demand.run_as_script()
emissions.test_lca_operation()
embodied.test_lca_embodied()
graphs.test_graph_demand()
mobility.test_mobility()
benchmark.test_benchmark()
scenario_plots.test_plot_scenarios()


print 'full test completed'
