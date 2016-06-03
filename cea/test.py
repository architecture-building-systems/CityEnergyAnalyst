"""
Test all the main scripts in one go - drink coffee while you wait :)
"""
import properties
import demand
import emissions
import embodied
import graphs
import radiation

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
demand.test_demand()
emissions.test_lca_operation()
embodied.test_lca_embodied()
<<<<<<< HEAD
graphs.test_graph_demand()

print 'full test completed'
=======
graphs.test_graph_demand()
>>>>>>> refs/remotes/origin/master
