import pyomo_multi_linetype
import plot_functions as pf
from pyomo.environ import *
import time
from concept_parameters import *
import process_results


def pyomo_print_results(options=None, instance=None, results=None):
    """A callback with dummy default values"""
    print options


def electrical_grid_calculations(dict_connected):
    # ============================
    # Solve Problem
    # ============================

    m = pyomo_multi_linetype.main(dict_connected)
    opt = SolverFactory('cplex',
                        # executable='/opt/ibm/ILOG/CPLEX_Studio1271/cplex/bin/x86-64_linux/cplex' # LINUX
                        )  # Create a solver
    opt.options['threads'] = THREADS

    results = opt.solve(m,
                        tee=True,
                        # keepfiles=True,
                        symbolic_solver_labels=True,
                        )

    # for i in xrange(100):
    #     parameter = i
    #     instance = create_model(parameter)
    #     opt.solve(instance)

    m.display()  # Display the results

    # Print objective function values
    for cost_type in [m.var_costs.values()][0]:
        print cost_type, cost_type.value
    print '\n'

    # pf.plot_network_on_street(m)
    # pf.plot_complete(m)
    # pf.plot_network(m)

    return m


if __name__ == '__main__':

    dict_connected = {0: 1, 1: 1, 2: 0,
                      3: 1, 4: 0, 5: 1,
                      6: 0, 7: 1, 8: 1,
                      9: 1}
#                        , 10: 1, 11: 1,
#                   12: 1, 13: 1, 14: 1,
#                   15: 1, 16: 1, 17: 1,
#                   18: 1, 19: 1, 20: 1,
#                   21: 1, 22: 1, 23: 1,
#                   }

    t0 = time.clock()
    electrical_grid_calculations(dict_connected)
    print 'main() succeeded'
    print 'total time: ', time.clock() - t0
