"""
Test all the main scripts in one go - drink coffee while you wait :)
"""
import properties
import demand
import emissions
import embodied
import graphs

properties.test_properties()
demand.test_demand()
emissions.test_lca_operation()
embodied.test_lca_embodied()
graphs.test_graph_demand()
