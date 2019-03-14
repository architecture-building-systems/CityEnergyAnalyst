from __future__ import division
import os
import re
import csv
import time

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
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


def write_results(locator, output_folder, scenario_name,
        m,
        time_main,
        solver_name,
        threads,
        time_limit,
        interest_rate,
        voltage_nominal,
        approx_loss_hours,
        alpha,
        beta,
        load_factor
):
    with open(os.path.join(locator.get_mpc_results_folder(output_folder), 'output_folder.csv'), "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(['scenario', scenario_name])
        writer.writerow(['solver_name', solver_name])
        writer.writerow(['threads', threads])
        writer.writerow(['time_limit', time_limit])
        writer.writerow(['interest_rate', interest_rate])
        writer.writerow(['voltage_nominal', voltage_nominal])
        writer.writerow(['approx_loss_hours', approx_loss_hours])
        writer.writerow(['timesteps', len(m.date_and_time_prediction)])
        writer.writerow(['alpha', alpha])
        writer.writerow(['beta', beta])
        writer.writerow(['load_factor', load_factor])
        writer.writerow(['Runtime', (time.time() - time_main)])

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
                            * (m.dict_line_tech[k]['I_max_A'] * voltage_nominal)
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
            sum_base = load_factor * sum(sum_base)  # already in kW

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
            sum_base = load_factor * sum(sum_base)  # already in kW

            sum_total = sum(m.var_per_building_electric_load[:, time_step].value) * (10 ** 6)  # W

            writer.writerow([
                str(time_step),
                sum_base / sum(m.gross_floor_area_m2.values()) / load_factor,
                sum_total / sum(m.gross_floor_area_m2.values()) / load_factor
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
                building_avg / m.gross_floor_area_m2[building] / load_factor,
                building_peak / m.gross_floor_area_m2[building] / load_factor
            ])

        writer.writerow([])

        writer.writerow(['Linetype', 'Crosssection in mm2'])
        for node_idx, node in enumerate(m.dict_line_tech):
            writer.writerow([str(node_idx), m.dict_line_tech[node_idx]['cross_section_mm2']])
