import pyomo_planning_and_operation_mixed
from pyomo.environ import *
import time
from lp_op_config import *
import datetime
import lp_op_support_functions as sf

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main():
    t0 = time.clock()

    print('Running scenario: ' + SCENARIO)

    date_main = datetime.datetime.now()
    time_main = time.time()

    str_output_filename = (
            '_'.join(SCENARIO.split('/'))
            + '%4i%02i%02i_%2i%02i%02i'
            % (date_main.year, date_main.month, date_main.day, date_main.hour, date_main.minute, date_main.second)
    )

    # ============================
    # Solve Problem
    # ============================

    m = pyomo_planning_and_operation_mixed.main()
    opt = SolverFactory(SOLVER_NAME)  # Create a solver
    if TIME_LIMIT > 0:
        if SOLVER_NAME == 'cplex':
            opt.options['timelimit'] = TIME_LIMIT
        elif SOLVER_NAME == 'gurobi':
            opt.options['TimeLimit'] = TIME_LIMIT
    opt.options['threads'] = THREADS
    opt.solve(
        m,
        tee=True,
        keepfiles=True,
        symbolic_solver_labels=True
    )
    # m.display()  # Display the results

    # ============================
    # Process Results
    # ============================

    sf.print_res(m)
    sf.write_results(m, str_output_filename, time_main)
    sf.save_plots(m, str_output_filename)

    print('Completed.')
    print('Total time: ', time.clock() - t0)


if __name__ == '__main__':
    main()
