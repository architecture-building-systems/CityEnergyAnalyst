import lp_plotting as pf
import matplotlib.pyplot as plt
import sys

import pyomo_multi_linetype
from pyomo.environ import *
from lp_config import *
import time
import datetime
import lp_support_functions as sf

import concept.model_electric_network.emodel as emodel
import get_initial_network as gia
import pandas as pd


def main():
    date_main = datetime.datetime.now()
    time_main = time.time()

    str_datetime = '%4i%02i%02i_%2i%02i%02i' \
                   % (date_main.year, date_main.month, date_main.day,
                      date_main.hour, date_main.minute, date_main.second)

    tempdir = LOCATOR + '/lp_output/' + str_datetime + '_logfile.log'

    # ============================
    # Solve Problem
    # ============================

    m = pyomo_multi_linetype.main()
    opt = SolverFactory('gurobi',
                        # executable='/opt/ibm/ILOG/CPLEX_Studio1271/cplex/bin/x86-64_linux/cplex' # LINUX
                        )
    opt.options['threads'] = 3
    # opt.options['mipgap'] = 0.7
    opt.solve(m,
              tee=True,
              keepfiles=True,
              symbolic_solver_labels=True,
              # logfile=tempdir
              )

    m.display()  # Display the results


    # ============================
    # Process Results
    # ============================

    sf.print_res(m)
    sf.write_results(m, str_datetime, time_main)
    sf.save_plots(m, str_datetime)

    if PLOTTING:
        if PLOT_LINES_ON_STREETS:
            pf.plot_network_on_street(m)
        else:
            pf.plot_lines(m)

        plt.show()

    # # test
    df_nodes, tranches = gia.connect_building_to_grid()
    df_nodes_processed = gia.process_network(df_nodes)
    dict_length, dict_path = gia.create_length_dict(df_nodes_processed, tranches)
    df_line_parameter = pd.read_csv(LOCATOR + '/electric_line_data.csv')
    net = emodel.powerflow_lp(m, df_nodes_processed, dict_length, df_line_parameter)

    filename_pp = LOCATOR + '/lp_output/' + str_datetime + '_lp_net_result.txt'

    orig_stdout = sys.stdout
    f = open(filename_pp, 'w')
    sys.stdout = f

    print net.line
    print net.res_line

    sys.stdout = orig_stdout
    f.close()


if __name__ == '__main__':
    main()
    print 'main() succeeded'

