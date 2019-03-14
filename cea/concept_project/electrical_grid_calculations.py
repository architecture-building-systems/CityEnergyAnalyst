import pyomo_multi_linetype
import plot_functions as pf
from pyomo.environ import *
import time
from concept_parameters import *
import process_results
import cea.globalvar
import cea.inputlocator
import cea.config

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def electrical_grid_calculations(dict_connected, config, locator):
    # ============================
    # Solve Problem
    # ============================

    m = pyomo_multi_linetype.main(dict_connected, config, locator)
    opt = SolverFactory('gurobi',
                        # executable='/opt/ibm/ILOG/CPLEX_Studio1271/cplex/bin/x86-64_linux/cplex' # LINUX
                        )  # Create a solver
    opt.options['threads'] = THREADS

    opt.solve(m,
              tee=True,
              # keepfiles=True,
              symbolic_solver_labels=True
              )

    # for i in xrange(100):
    #     parameter = i
    #     instance = create_model(parameter)
    #     opt.solve(instance)

    # m.display()  # Display the results

    # Print objective function values
    # for cost_type in [m.var_costs.values()][0]:
    #     print cost_type, cost_type.value
    # print '\n'

    # pf.plot_network_on_street(m)
    # pf.plot_complete(m)
    # pf.plot_network(m)

    return m


if __name__ == '__main__':

    dict_connected = {0: 1, 1: 1, 2: 0,
                      3: 1, 4: 0, 5: 1,
                      6: 0, 7: 1, 8: 1,
                      9: 1}
    dict_connected = {0: 1, 1: 1, 2: 0,
                      3: 1, 4: 0, 5: 1,
                      6: 0, 7: 1, 8: 1,
                      9: 1, 10: 1, 11: 1,
                      12: 1, 13: 1, 14: 1,
                      15: 1, 16: 1, 17: 1,
                      18: 1, 19: 1, 20: 1,
                      21: 1, 22: 1, 23: 1}
#                        , 10: 1, 11: 1,
#                   12: 1, 13: 1, 14: 1,
#                   15: 1, 16: 1, 17: 1,
#                   18: 1, 19: 1, 20: 1,
#                   21: 1, 22: 1, 23: 1,
#                   }

    t0 = time.clock()
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    electrical_grid_calculations(dict_connected, config, locator)
    print 'main() succeeded'
    print 'total time: ', time.clock() - t0
