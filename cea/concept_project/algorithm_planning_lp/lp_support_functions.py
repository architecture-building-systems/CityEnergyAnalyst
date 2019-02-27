import lp_plotting as pf
import matplotlib.pyplot as plt
from lp_config import *
import re
import csv
import errno
import time

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def print_res(m):
    # Print objective function values
    obj_val = 0.0
    for cost_type in [m.var_costs.values()][0]:
        obj_val += cost_type.value
        print cost_type, cost_type.value

    print 'obj_val ', obj_val
    print '\n'

    # Print results of decision variables
    var_x = m.var_x.values()
    for x in var_x:
        if x.value > 0.5:
            node_int = re.findall(r'\d+', x.local_name)

            start_node = int(node_int[0])
            end_node = int(node_int[1])
            linetype = int(node_int[2])

            print ("Start: %02i End: %02i LineType %02i" % (start_node, end_node, linetype))


def write_results(m, str_datetime, time_main):

    filename = LOCATOR + '/lp_output/' + str_datetime + '_lp_results.csv'

    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(['SCENARIO', SCENARIO])
        writer.writerow(['THREADS', THREADS])
        writer.writerow(['INTEREST_RATE', INTEREST_RATE])
        writer.writerow(['V_BASE', V_BASE])
        writer.writerow(['S_BASE', S_BASE])
        writer.writerow(['I_BASE', I_BASE])
        writer.writerow(['APPROX_LOSS_HOURS', APPROX_LOSS_HOURS])
        writer.writerow(['Program Time', (time.time() - time_main)])

        writer.writerow([''])
        obj_val = 0.0
        for cost_type in [m.var_costs.values()][0]:
            obj_val += cost_type.value
            writer.writerow([cost_type, cost_type.value])

        writer.writerow(['obj_val', obj_val])

        writer.writerow([''])

        writer.writerow(['Startnode', 'Endnode', 'Linetype', 'Power in kW', 'Loading in %'])
        var_x = m.var_x.values()
        for idx_x, x in enumerate(var_x):
            if x.value > 0.5:
                node_int = re.findall(r'\d+', x.local_name)

                start_node = int(node_int[0])
                end_node = int(node_int[1])
                linetype = int(node_int[2])
                var_power = m.var_power_over_line.values()[idx_x].value * S_BASE * 10 ** 3
                loading = abs((var_power * 10 ** 3) /
                              (2.0 * (m.dict_line_tech[linetype]['I_max_A'] * V_BASE * 10 ** 3)) * 100.0)

                writer.writerow([start_node, end_node, linetype, var_power, loading])

        writer.writerow([''])

        writer.writerow(['Node index', 'Demand in kW'])
        for node_idx, node in enumerate(m.dict_power_demand):
            writer.writerow(['Node ' + str(node_idx), m.dict_power_demand[node_idx] * S_BASE * 10 ** 3])

        writer.writerow([''])

        writer.writerow(['Linetype', 'Crosssection in mm2'])
        for node_idx, node in enumerate(m.dict_line_tech):
            writer.writerow(['Linetype ' + str(node_idx), m.dict_line_tech[node_idx]['cross_section_mm2']])


def save_plots(m, str_datetime):

    filename_street = LOCATOR + '/lp_output/' + str_datetime + '_lp_plot_street.pdf'
    filename_graph = LOCATOR + '/lp_output/' + str_datetime + '_lp_plot_graph.pdf'

    pf.plot_network_on_street(m)
    plt.savefig(filename_street)

    pf.plot_network(m)
    plt.savefig(filename_graph)