from __future__ import division

import numpy as np
import pandas as pd
import cea.config
import cea.globalvar
import cea.inputlocator

from cea.optimization.prices import Prices as Prices
import cea.optimization.distribution.network_opt_main as network_opt
import cea.technologies.pumps as pumps
import cea.technologies.cogeneration as chp
import cea.technologies.chiller_vapor_compression as VCCModel
import cea.technologies.cooling_tower as CTModel
from cea.optimization.constants import PUMP_ETA
from cea.optimization.lca_calculations import lca_calculations
from cea.technologies.heat_exchangers import calc_Cinv_HEX_hisaka

__author__ = "Lennart Rogenhofer, Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class Thermal_Network(object):
    """
    Storage of information for the network currently being calculated.
    """

    def __init__(self, locator, config, network_type, gv):
        # sotre key variables
        self.locator = locator
        self.config = config
        self.network_type = network_type
        self.network_name = config.thermal_network_optimization.network_name
        # initialize optimization storage variables and dictionaries
        self.cost_storage = None
        self.building_names = None
        self.number_of_buildings = 0
        self.gv = gv
        self.prices = None
        self.network_features = None
        self.layout = 0
        self.has_loops = None
        self.populations = {}
        self.all_individuals = None
        self.generation_number = 0
        self.building_index = []
        self.individual_number = 0
        self.disconnected_buildings_index = []
        # list of all possible heating or cooling systems. used to compare which ones are centralized / decentralized
        self.full_heating_systems = ['ahu', 'aru', 'shu', 'ww']
        self.full_cooling_systems = ['ahu', 'aru',
                                     'scu']  # Todo: add 'data', 're' here once the are available disconnectedly


def calc_Capex_a_network_pipes(network_info):
    ''' Calculates network piping costs'''
    if network_info.network_type == 'DH':
        InvC = network_info.network_features.pipesCosts_DHN
    else:
        InvC = network_info.network_features.pipesCosts_DCN
    # Assume lifetime of 25 years and 5 % IR
    Inv_IR = 0.05
    Inv_LT = 20
    Capex_a_netw = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    return Capex_a_netw


def calc_Ctot_network_pump(network_info):
    """
    Computes the total pump investment and operational cost, slightly adapted version of original in optimization main script.
    :type network_info: class storing network information
    :returns Capex_aannulized pump capex
    :returns Opex_a_tot: pumping cost, operational
    """
    network_type = network_info.config.thermal_network.network_type

    # read in node mass flows
    df = pd.read_csv(network_info.locator.get_edge_mass_flow_csv_file(network_type, ''), index_col=0)
    mdotA_kgpers = np.array(df)
    mdotA_kgpers = np.nan_to_num(mdotA_kgpers)
    mdotnMax_kgpers = np.amax(mdotA_kgpers)  # find highest mass flow of all nodes at all timesteps (should be at plant)
    # read in total pressure loss in kW
    deltaP_kW = pd.read_csv(network_info.locator.get_ploss('', network_type))
    deltaP_kW = deltaP_kW['pressure_loss_total_kW'].sum()

    Opex_var = deltaP_kW * 1000 * network_info.prices.ELEC_PRICE

    if network_info.config.thermal_network.network_type == 'DH':
        deltaPmax = np.max(network_info.network_features.DeltaP_DHN)
    else:
        deltaPmax = np.max(network_info.network_features.DeltaP_DCN)
    Capex_a, Opex_fixed = pumps.calc_Cinv_pump(deltaPmax, mdotnMax_kgpers, PUMP_ETA, network_info.config,
                                               network_info.locator, 'PU1')  # investment of Machinery
    Opex_a_tot = Opex_var + Opex_fixed

    return Capex_a, Opex_a_tot


def calc_Ctot_cooling_plants(network_info):
    ''' calculates chiller and cooling tower costs '''

    # read in plant heat requirement
    plant_heat_sum_kWh = pd.read_csv(network_info.locator.get_optimization_network_layout_plant_heat_requirement_file(
        network_info.network_type, network_info.config.thermal_network_optimization.network_name))
    # read in number of plants
    number_of_plants = len(plant_heat_sum_kWh.columns)

    plant_heat_peak_kW_list = plant_heat_sum_kWh.abs().max(axis=0).values  # calculate peak demand
    plant_heat_sum_kWh_list = plant_heat_sum_kWh.abs().sum().values  # calculate aggregated demand

    Opex_var_chiller = 0
    Capex_a_chiller = 0
    Opex_a_chiller = 0
    Capex_a_CT = 0
    Opex_a_CT = 0
    # calculate cost of chiller heat production and chiller capex and opex
    for plant_number in range(number_of_plants):  # iterate through all plants
        if number_of_plants > 1:
            plant_heat_peak_kW = plant_heat_peak_kW_list[plant_number]
        else:
            plant_heat_peak_kW = plant_heat_peak_kW_list[0]
        plant_heat_sum_kWh = plant_heat_sum_kWh_list[plant_number]

        Capex_chiller = 0
        Opex_fixed_chiller = 0
        Capex_CT = 0
        Opex_fixed_CT = 0
        if plant_heat_peak_kW > 0:  # we have non 0 demand
            peak_demand = plant_heat_peak_kW * 1000  # convert to W
            # calculate Heat loss costs
            if network_info.network_type == 'DH':
                # Assume a COP of 1.5 e.g. in CHP plant, calculate cost of producing cooling
                Opex_var_chiller += (
                                        plant_heat_sum_kWh) / 1.5 * 1000 * network_info.prices.ELEC_PRICE  # TODO: Setup COP calculation for DH case
                # calculate price of equipment
                Capex_chiller, Opex_fixed_chiller = chp.calc_Cinv_CCGT(peak_demand, network_info.locator,
                                                                       network_info.config, technology=0)
                # FIXME: what is this? can we just change the function to chiller plants, and dont calculate the DH part here? we could have a COP plant when calculating DH
            else:
                # Clark D (CUNDALL). Chiller energy efficiency 2013.
                # FIXME: please add reference in the documentation of this function (see thermal_network_matrix
                # calculate plant COP according to the cold water supply temperature in SG context
                COP_plant = VCCModel.calc_VCC_COP(network_info.config,
                                                  network_info.config.thermal_network.substation_cooling_systems,
                                                  centralized=True)
                # calculate cost of producing cooling
                Opex_var_chiller += (plant_heat_sum_kWh) / COP_plant * 1000 * network_info.prices.ELEC_PRICE
                # calculate equipment cost of chiller and cooling tower
                Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand, network_info.locator,
                                                                           network_info.config, 'CH1')
                Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand, network_info.locator,
                                                               network_info.config, 'CT1')
                # FIXME: missing Opex_var_CT, which should be connected to cooling_tower.calc_CT (hourly)
                # FIXME: that being said, the Opex_var_chiller should also be calculated hourly
        # sum over all plants
        Capex_a_chiller += Capex_chiller
        Opex_a_chiller += Opex_fixed_chiller
        Capex_a_CT += Capex_CT
        Opex_a_CT += Opex_fixed_CT

    return Opex_var_chiller, Opex_a_CT, Opex_a_chiller, Capex_a_CT, Capex_a_chiller


def calc_Ctot_cooling_disconnected(network_info):
    ''' caclulates the cost of disconnected loads at the building level '''
    disconnected_systems = []
    ## Calculate disconnected heat load costs
    dis_opex = 0
    dis_capex = 0
    # if optimal_network.network_type == 'DH':
    # information not yet available
    '''
        for system in optimal_network.full_heating_systems:
            if system not in optimal_network.config.thermal_network.substation_heating_systems:
                disconnected_systems.append(system)
        # Make sure files to read in exist
        for system in disconnected_systems:
            for building in optimal_network.building_names:
                assert optimal_network.locator.get_optimization_disconnected_folder_building_result_heating(building), "Missing diconnected building files. Please run disconnected_buildings_heating first."
            # Read in disconnected cost of all buildings
                disconnected_cost = optimal_network.locator.get_optimization_disconnected_folder_building_result_heating(building)
    '''
    if network_info.network_type == 'DC':
        # iterate through all possible cooling systems
        for system in network_info.full_cooling_systems:
            if system not in network_info.config.thermal_network.substation_cooling_systems:
                # add system to list of loads that are supplied at building level
                disconnected_systems.append(system)
        if len(disconnected_systems) > 0:
            # check if we have any disconnected systems
            system_string = find_systems_string(
                disconnected_systems)  # returns string nevessary for further calculations of which systems are disconnected
            # iterate trhough all buildings
            for building_index, building in enumerate(network_info.building_names):
                Opex_var_chiller = 0
                Capex_chiller = 0
                # Read in building demand
                disconnected_demand = pd.read_csv(
                    network_info.locator.get_demand_results_file(building))
                if not system_string:  # this means there are no disconnected loads. Shouldn't happen but is a failsafe
                    disconnected_demand_total = 0.0
                    peak_demand = 0.0
                else:
                    for system_index, system in enumerate(system_string):  # iterate through all disconnected loads
                        # go through all systems and sum up demand values and sum
                        if system_index == 0:
                            disconnected_demand_t = disconnected_demand[system]
                            disconnected_demand_total = disconnected_demand_t.abs().sum()
                        else:
                            disconnected_demand_t = disconnected_demand_t + disconnected_demand[system]
                            disconnected_demand_total = disconnected_demand_total + disconnected_demand[
                                system].abs().sum()
                    peak_demand = disconnected_demand_t.abs().max()  # calculate peak demand of all disconnected systems
                # calculate disonnected system COP
                COP_chiller_system = VCCModel.calc_VCC_COP(network_info.config,
                                                           disconnected_systems,
                                                           centralized=False)
                # calculate operational costs of producing cooling
                Opex_var_chiller = disconnected_demand_total / COP_chiller_system * 1000 * network_info.prices.ELEC_PRICE
                # calculate disconnected systems cost of disconnected loads. Assumes that all these loads are supplied by one chiller, unless this exceeds maximum chiller capacity of database
                Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand * 1000, network_info.locator,
                                                                           network_info.config, 'CH3')
                Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand * 1000, network_info.locator,
                                                               network_info.config, 'CT1')
                # FIXME: missing Opex_var_CT, which should be connected to cooling_tower.calc_CT (hourly)
                # FIXME: that being said, the Opex_var_chiller should also be calculated hourly
                # sum up costs
                dis_opex += Opex_var_chiller + Opex_fixed_chiller + Opex_fixed_CT
                dis_capex += Capex_chiller + Capex_CT

    dis_total = dis_opex + dis_capex
    return dis_total, dis_opex, dis_capex


def calc_Ctot_disconnected_buildings(network_info):
    ## Calculate disconnected heat load costs
    dis_opex = 0
    dis_capex = 0
    # if optimal_network.network_type == 'DH':
    # information not yet available
    if len(network_info.disconnected_buildings_index) > 0:  # we have disconnected buildings
        # Make sure files to read in exist
        for building_index, building in enumerate(network_info.building_names):  # iterate through all buildings
            if building_index in network_info.disconnected_buildings_index:  # disconnected building
                # Read in demand of building
                disconnected_demand = pd.read_csv(
                    network_info.locator.get_demand_results_file(building))
                # sum up demand of all loads
                disconnected_demand_total = disconnected_demand['Qcs_sys_scu_kWh'].abs() + disconnected_demand[
                    'Qcs_sys_ahu_kWh'].abs() + disconnected_demand['Qcs_sys_aru_kWh'].abs()
                # calculate peak demand
                peak_demand = disconnected_demand_total.abs().max()
                # calculate aggregated demand
                disconnected_demand_total = disconnected_demand_total.abs().sum()
                # calculate system COP
                COP_chiller_system = VCCModel.calc_VCC_COP(network_info.config,
                                                           ['ahu', 'aru', 'scu'],
                                                           centralized=False)
                # FIXME: shouldn't it be reading from the building technical_systems.dbf?
                # calculate cost of producing cooling
                Opex_var_chiller = disconnected_demand_total / COP_chiller_system * 1000 * network_info.prices.ELEC_PRICE
                # calculate cost of Chiller and cooling tower at building level
                Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand * 1000, network_info.locator,
                                                                           network_info.config, 'CH3')
                Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand * 1000, network_info.locator,
                                                               network_info.config, 'CT1')
                # FIXME: missing Opex_var_CT, which should be connected to cooling_tower.calc_CT (hourly)
                # FIXME: that being said, the Opex_var_chiller should also be calculated hourly
                # sum up costs
                dis_opex += Opex_var_chiller + Opex_fixed_chiller + Opex_fixed_CT
                dis_capex += Capex_chiller + Capex_CT

    dis_total = dis_opex + dis_capex
    return dis_total, dis_opex, dis_capex


def calc_Ctot_network(network_info):
    # read in general values for cost calculation
    lca = lca_calculations(network_info.locator, network_info.config)
    network_info.prices = Prices(network_info.locator, network_info.config)
    network_info.prices.ELEC_PRICE = lca.ELEC_PRICE  # [USD/kWh]
    network_info.network_features = network_opt.network_opt_main(network_info.config,
                                                                 network_info.locator)
    ## calculate Network costs
    # maintenance of network neglected, see Documentation Master Thesis Lennart Rogenhofer
    Capex_a_netw = calc_Capex_a_network_pipes(network_info)
    # calculate Pressure loss and Pump costs
    Capex_a_pump, Opex_tot_pump = calc_Ctot_network_pump(network_info)
    # calculate plant costs of producing heat, and costs of chiller, cooling tower, etc.
    Opex_var_chiller, Opex_fixed_CT, Opex_fixed_chiller, Capex_a_CT, Capex_a_chiller = calc_Ctot_cooling_plants(
        network_info)
    if Opex_var_chiller < 1:  # no heat supplied by network
        Capex_a_netw = 0
    # calculate costs of disconnected loads
    Ctot_dis_loads, Opex_tot_dis_loads, Capex_a_dis_loads = calc_Ctot_cooling_disconnected(network_info)
    # calculate costs of disconnected buildings
    Ctot_dis_buildings, Opex_tot_dis_buildings, Capex_a_dis_buildings = calc_Ctot_disconnected_buildings(network_info)
    # calculate costs of HEX at connected buildings
    Capex_a_hex, Opex_fixed_hex = calc_Cinv_HEX_hisaka(network_info)
    # store results
    network_info.cost_storage.ix['capex'][
        network_info.individual_number] = Capex_a_netw + Capex_a_pump + Capex_a_dis_loads + Capex_a_dis_buildings + \
                                          Capex_a_chiller + Capex_a_CT + Capex_a_hex
    network_info.cost_storage.ix['opex'][
        network_info.individual_number] = Opex_tot_pump + Opex_var_chiller + Opex_tot_dis_loads + \
                                          Opex_tot_dis_buildings + Opex_fixed_chiller + Opex_fixed_CT + Opex_fixed_hex
    network_info.cost_storage.ix['total'][
        network_info.individual_number] = Capex_a_netw + Capex_a_pump + Capex_a_chiller + Capex_a_CT + Capex_a_hex + \
                                          Opex_tot_pump + Opex_var_chiller + Ctot_dis_loads + Ctot_dis_buildings + \
                                          Opex_fixed_chiller + Opex_fixed_CT + Opex_fixed_hex
    network_info.cost_storage.ix['capex_network'][network_info.individual_number] = Capex_a_netw
    network_info.cost_storage.ix['capex_pump'][network_info.individual_number] = Capex_a_pump
    network_info.cost_storage.ix['capex_hex'][network_info.individual_number] = Capex_a_hex
    network_info.cost_storage.ix['capex_dis_loads'][network_info.individual_number] = Capex_a_dis_loads
    network_info.cost_storage.ix['capex_dis_build'][network_info.individual_number] = Capex_a_dis_buildings
    network_info.cost_storage.ix['capex_chiller'][network_info.individual_number] = Capex_a_chiller
    network_info.cost_storage.ix['capex_CT'][network_info.individual_number] = Capex_a_CT
    network_info.cost_storage.ix['opex_heat'][network_info.individual_number] = Opex_var_chiller
    network_info.cost_storage.ix['opex_pump'][network_info.individual_number] = Opex_tot_pump
    network_info.cost_storage.ix['opex_hex'][network_info.individual_number] = Opex_fixed_hex
    network_info.cost_storage.ix['opex_dis_loads'][network_info.individual_number] = Opex_tot_dis_loads
    network_info.cost_storage.ix['opex_dis_build'][network_info.individual_number] = Opex_tot_dis_buildings
    network_info.cost_storage.ix['opex_chiller'][network_info.individual_number] = Opex_fixed_chiller
    network_info.cost_storage.ix['opex_CT'][network_info.individual_number] = Opex_fixed_CT
    # write outputs to console for user
    print 'Annualized Capex network: ', Capex_a_netw
    print 'Annualized Capex pump: ', Capex_a_pump
    print 'Annualized Capex heat exchangers: ', Capex_a_hex
    print 'Annualized Capex disconnected loads: ', Capex_a_dis_loads
    print 'Annualized Capex disconnected buildings: ', Capex_a_dis_buildings
    print 'Annualized Capex centralized chiller: ', Capex_a_chiller
    print 'Annualized Capex centralized cooling tower: ', Capex_a_CT
    print 'Annualized Opex chiller: ', Opex_var_chiller
    print 'Annualized Opex network pump: ', Opex_tot_pump
    print 'Annualized Opex heat exchangers: ', Opex_fixed_hex
    print 'Annualized Opex disconnected loads: ', Opex_tot_dis_loads
    print 'Annualized Opex disconnected building: ', Opex_tot_dis_buildings
    print 'Annualized Opex(fixed) chiller: ', Opex_fixed_chiller
    print 'Annualized Opex(fixed) cooling tower: ', Opex_fixed_CT


def main(config):
    """
    This function calculates the total costs of a network after running simulation from thermal_network_matrix.
    Assumption: all loads are connected to the network
    :param config:
    :return:
    """
    # initialize key variables
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    network_type = config.thermal_network.network_type
    network_info = Thermal_Network(locator, config, network_type, gv)
    # read in basic information and save to object, e.g. building demand, names, total number of buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    if network_type == 'DC':
        annual_demand_Wh = total_demand['Qcs_sys_MWhyr'].sum() * 10e6  # to Wh
    else:
        annual_demand_Wh = total_demand['Qhs_sys_MWhyr'].sum() * 10e6
    network_info.building_names = total_demand.Name.values
    network_info.number_of_buildings = total_demand.Name.count()
    # initialize data storage for later output to file
    network_info.cost_storage = pd.DataFrame(np.zeros((19, 1)))
    network_info.cost_storage.index = ['capex', 'opex', 'total', 'opex_heat', 'opex_pump', 'opex_dis_loads',
                                       'opex_dis_build', 'opex_chiller', 'opex_CT', 'opex_hex', 'capex_hex',
                                       'capex_network', 'capex_pump', 'capex_dis_loads', 'capex_dis_build',
                                       'capex_chiller', 'capex_CT', 'length', 'avg_diam']
    # calculate total network costs
    calc_Ctot_network(network_info)
    # write outputs
    cost_output = {}
    cost_output['total_cost'] = network_info.cost_storage.ix['total'][0]
    cost_output['opex'] = network_info.cost_storage.ix['opex'][0]
    cost_output['capex'] = network_info.cost_storage.ix['capex'][0]
    cost_output['total_cost_per_Wh'] = cost_output['total_cost'] / annual_demand_Wh
    cost_output['opex_per_Wh'] = cost_output['opex'] / annual_demand_Wh
    cost_output['capex_per_Wh'] = cost_output['capex'] / annual_demand_Wh
    cost_output = pd.DataFrame.from_dict(cost_output, orient='index')
    cost_output.to_csv(locator.get_optimization_network_layout_costs_file(config.thermal_network.network_type))
    return


if __name__ == '__main__':
    main(cea.config.Configuration())
