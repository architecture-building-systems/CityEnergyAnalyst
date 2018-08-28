import pyomo_multi_linetype
import plot_functions as pf
from pyomo.environ import *
import time
from config import *


def main():
    # ============================
    # Solve Problem
    # ============================

    m = pyomo_multi_linetype.main()
    opt = SolverFactory('cplex',
                        # executable='/opt/ibm/ILOG/CPLEX_Studio1271/cplex/bin/x86-64_linux/cplex' # LINUX
                        )  # Create a solver
    opt.options['threads'] = THREADS
    opt.solve(m,
              tee=True,
              # keepfiles=True,
              symbolic_solver_labels=True,
              )
    m.display()  # Display the results

    # Print objective function values
    for cost_type in [m.var_costs.values()][0]:
        print cost_type, cost_type.value
    print '\n'

    # pf.plot_network_on_street(m)
    # pf.plot_complete(m)
    pf.plot_network(m)


if __name__ == '__main__':
    t0 = time.clock()
    main()
    print 'main() succeeded'
    print 'total time: ', time.clock() - t0
