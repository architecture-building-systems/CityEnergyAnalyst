import lp_op_plotting as pf
import matplotlib.pyplot as plt
from lp_op_config import *
import re
import csv
import errno
import time


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


def write_results(m, str_output_filename, time_main):

    filename = LOCATOR + '/lp_op_output/' + str_output_filename + '_lp_op_results.csv'

    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(['SCENARIO', SCENARIO])
        writer.writerow(['SOLVER_NAME', SOLVER_NAME])
        writer.writerow(['THREADS', THREADS])
        writer.writerow(['TIME_LIMIT', TIME_LIMIT])
        writer.writerow(['INTEREST_RATE', INTEREST_RATE])
        writer.writerow(['VOLTAGE_NOMINAL', VOLTAGE_NOMINAL])
        writer.writerow(['APPROX_LOSS_HOURS', APPROX_LOSS_HOURS])
        writer.writerow(['TIMESTEPS', len(m.date_and_time_prediction)])
        writer.writerow(['ALPHA', ALPHA])
        writer.writerow(['BETA', BETA])
        writer.writerow(['LOAD_FACTOR', LOAD_FACTOR])
        writer.writerow(['Program Time', (time.time() - time_main)])

        writer.writerow([])

        writer.writerow(['Cost type', 'Value in SGD'])

        writer.writerow(['Electricity', m.var_costs['electricity_price'].value])
        writer.writerow(['Investment (lines)', m.var_costs['investment_line'].value])
        writer.writerow(['Investment (substation)', m.var_costs['investment_sub'].value])
        writer.writerow(['Investment (building transformer)', m.var_costs['investment_build'].value])
        writer.writerow(['Operation & maintenance', m.var_costs['om'].value])
        writer.writerow(['Invest., op. & main. total', sum([
            m.var_costs['investment_line'].value,
            m.var_costs['investment_sub'].value,
            m.var_costs['investment_build'].value,
            m.var_costs['om'].value
        ])])
        writer.writerow(['Losses', m.var_costs['losses'].value])
        writer.writerow(['Total', sum([
            m.var_costs['electricity_price'].value,
            m.var_costs['investment_line'].value,
            m.var_costs['investment_sub'].value,
            m.var_costs['investment_build'].value,
            m.var_costs['losses'].value,
            m.var_costs['om'].value
        ])])

        writer.writerow([])

        writer.writerow(['Set temperature tracking', m.var_costs['set_temperature'].value])
        writer.writerow(['Total (with set temp. tracking)', sum([
            m.var_costs['electricity_price'].value,
            m.var_costs['investment_line'].value,
            m.var_costs['investment_sub'].value,
            m.var_costs['investment_build'].value,
            m.var_costs['losses'].value,
            m.var_costs['om'].value,
            m.var_costs['set_temperature'].value
        ])])

        writer.writerow([])

        writer.writerow(['Startnode', 'Endnode', 'Linetype', 'Power in kW', 'Loading in %'])
        for i, j in m.set_edge:
            for k in m.set_linetypes:
                if m.var_x[i, j, k].value > 0.5:
                    power_line_limit = (
                            float(m.var_x[i, j, k].value)
                            * (m.dict_line_tech[k]['I_max_A'] * VOLTAGE_NOMINAL)
                            * (3 ** 0.5)
                    )
                    power_over_line_abs = abs(m.var_power_over_line[i, j, k].value)
                    writer.writerow([
                        i,
                        j,
                        k,
                        power_over_line_abs / (10 ** 3),  # in kW
                        100 * power_over_line_abs / power_line_limit
                    ])



        writer.writerow([])

        writer.writerow(['Time step', 'Base demand in kW', 'Total demand in kW'])

        for time_step in m.date_and_time_prediction:
            sum_base = []
            for demand in m.dict_hourly_power_demand.itervalues():
                sum_base.append(demand[time_step])
            sum_base = LOAD_FACTOR * sum(sum_base)  # already in kW

            sum_total = sum(m.var_per_building_electric_load[:, time_step].value) * (10 ** 3)  # kW

            writer.writerow([
                str(time_step),
                sum_base,
                sum_total
            ])

        writer.writerow([])

        writer.writerow(['Time step', 'Base demand in W/m2', 'Total demand in W/m2'])

        for time_step in m.date_and_time_prediction:
            sum_base = []
            for demand in m.dict_hourly_power_demand.itervalues():
                sum_base.append(demand[time_step])
            sum_base = LOAD_FACTOR * sum(sum_base)  # already in kW

            sum_total = sum(m.var_per_building_electric_load[:, time_step].value) * (10 ** 6)  # W

            writer.writerow([
                str(time_step),
                sum_base / sum(m.gross_floor_area_m2.values()) / LOAD_FACTOR,
                sum_total / sum(m.gross_floor_area_m2.values()) / LOAD_FACTOR
            ])

        writer.writerow([])

        writer.writerow(['Building name', 'Average demand in kW', 'Peak demand in kW'])

        for building in m.buildings_names:
            building_avg = (
                    sum(m.var_per_building_electric_load[building, :].value)
                    / float(len(m.date_and_time_prediction))
                    * (10 ** 3)  # in kW
            )
            building_peak = max(m.var_per_building_electric_load[building, :].value) * (10 ** 3)  # in kW

            writer.writerow([
                building,
                building_avg,
                building_peak
            ])

        writer.writerow([])

        writer.writerow(['Building name', 'Average demand in W/m2', 'Peak demand in W/m2'])

        for building in m.buildings_names:
            building_avg = (
                    sum(m.var_per_building_electric_load[building, :].value)
                    / float(len(m.date_and_time_prediction))
                    * (10 ** 6)  # in W
            )
            building_peak = max(m.var_per_building_electric_load[building, :].value) * (10 ** 6)  # in W

            writer.writerow([
                building,
                building_avg / m.gross_floor_area_m2[building] / LOAD_FACTOR,
                building_peak / m.gross_floor_area_m2[building] / LOAD_FACTOR
            ])

        writer.writerow([])

        writer.writerow(['Linetype', 'Crosssection in mm2'])
        for node_idx, node in enumerate(m.dict_line_tech):
            writer.writerow([str(node_idx), m.dict_line_tech[node_idx]['cross_section_mm2']])


def save_plots(m, str_output_filename):

    filename_street = LOCATOR + '/lp_op_output/' + str_output_filename + '_lp_op_plot_street.pdf'
    filename_graph = LOCATOR + '/lp_op_output/' + str_output_filename + '_lp_op_plot_graph.pdf'

    pf.plot_network_on_street(m)
    plt.savefig(filename_street)

    pf.plot_network(m)
    plt.savefig(filename_graph)