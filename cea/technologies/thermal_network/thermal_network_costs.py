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
from cea.constants import HOURS_IN_YEAR
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
        self.network_name = config.thermal_network_optimization.network_names
        # initialize optimization storage variables and dictionaries
        self.cost_storage = None
        self.building_names = None
        self.number_of_buildings_in_district = 0
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
        InvC = network_info.network_features.pipesCosts_DHN_USD
    else:
        InvC = network_info.network_features.pipesCosts_DCN_USD
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
    Capex_a_pump, Opex_fixed_pump, Capex_pump = pumps.calc_Cinv_pump(deltaPmax, mdotnMax_kgpers, PUMP_ETA, network_info.config,
                                               network_info.locator, 'PU1')  # investment of Machinery
    Opex_a_tot_pump = Opex_var + Opex_fixed_pump

    return Capex_a_pump, Opex_a_tot_pump


def calc_Ctot_cooling_plants(network_info):
    """
    Calculates costs of centralized cooling plants (chillers and cooling towers).
    :param network_info: an object storing information of the current network
    :return:
    """

    # read in plant heat requirement
    plant_heat_hourly_kWh = pd.read_csv(
        network_info.locator.get_optimization_network_layout_plant_heat_requirement_file(
            network_info.network_type, network_info.config.thermal_network_optimization.network_names))
    # read in number of plants
    number_of_plants = len(plant_heat_hourly_kWh.columns)

    plant_heat_original_kWh = plant_heat_hourly_kWh.copy()
    plant_heat_peak_kW_list = plant_heat_hourly_kWh.abs().max(axis=0).values  # calculate peak demand
    plant_heat_sum_kWh_list = plant_heat_hourly_kWh.abs().sum().values  # calculate aggregated demand

    Opex_var_chiller = 0.0
    Opex_var_CT = 0.0
    Capex_a_chiller = 0.0
    Opex_a_chiller = 0.0
    Capex_a_CT = 0.0
    Opex_a_CT = 0.0
    # calculate cost of chiller heat production and chiller capex and opex
    for plant_number in range(number_of_plants):  # iterate through all plants
        if number_of_plants > 1:
            plant_heat_peak_kW = plant_heat_peak_kW_list[plant_number]
        else:
            plant_heat_peak_kW = plant_heat_peak_kW_list[0]
        plant_heat_yearly_kWh = plant_heat_sum_kWh_list[plant_number]
        print 'Annual plant heat production:', round(plant_heat_yearly_kWh, 0), '[kWh]'
        Capex_a_chiller = 0
        Opex_fixed_chiller = 0
        Capex_a_CT = 0
        Opex_fixed_CT = 0
        if plant_heat_peak_kW > 0:  # we have non 0 demand
            peak_demand_W = plant_heat_peak_kW * 1000  # convert to W
            print 'Calculating cost of heat production at plant number: ', plant_number
            if network_info.config.thermal_network_optimization.yearly_cost_calculations:
                # calculates operation costs with yearly approximation
                COP_plant = VCCModel.calc_VCC_COP(network_info.config,
                                                  network_info.full_cooling_systems,
                                                  centralized=True)
                Opex_var_chiller += abs(
                    plant_heat_yearly_kWh) / COP_plant * 1000 * network_info.prices.ELEC_PRICE
                Opex_var_CT += CTModel.calc_CT_yearly(plant_heat_yearly_kWh)

            else:
                # calculates operation costs with hourly simulation
                # Read in building demand
                building_demand = {}
                for building in network_info.building_names:
                    building_demand[building] = pd.read_csv(
                        network_info.locator.get_demand_results_file(building))
                for t in range(HOURS_IN_YEAR):
                    # calculate COP of plant operation in this hour based on supplied loads
                    # calculate plant COP according to the cold water supply temperature in SG context
                    supplied_systems = find_non_zero_demand_systems(network_info, t, building_demand)
                    COP_plant = VCCModel.calc_VCC_COP(network_info.config, supplied_systems, centralized=True)
                    # calculate cost of producing cooling
                    column_name = plant_heat_original_kWh.columns[plant_number]
                    Opex_var_chiller += abs(
                        plant_heat_original_kWh[column_name][t]) / COP_plant * 1000 * network_info.prices.ELEC_PRICE
                    # FIXME: the cooling tower is cooling the heat from the condenser, so it should not be sized for the heat in the evaoprator
                    Opex_var_CT += CTModel.calc_CT(abs(plant_heat_original_kWh[column_name][t] * 1000),
                                                   peak_demand_W) * network_info.prices.ELEC_PRICE

            # calculate equipment cost of chiller and cooling tower
            Capex_a_chiller, Opex_fixed_chiller, Capex_chiller = VCCModel.calc_Cinv_VCC(peak_demand_W, network_info.locator,
                                                                       network_info.config, 'CH1')
            Capex_a_CT, Opex_fixed_CT, Capex_CT = CTModel.calc_Cinv_CT(peak_demand_W, network_info.locator,
                                                           network_info.config, 'CT1')
        # sum over all plants
        Capex_a_chiller += Capex_a_chiller
        Opex_a_chiller += Opex_fixed_chiller
        Capex_a_CT += Capex_a_CT
        Opex_a_CT += Opex_fixed_CT + Opex_var_CT

    return Opex_var_chiller, Opex_a_CT, Opex_a_chiller, Capex_a_CT, Capex_a_chiller


def calc_Ctot_cs_disconnected_loads(network_info):
    """
    Caclulates the space cooling cost of disconnected loads at the building level.
    The calculation for entirely disconnected buildings is done in calc_Ctot_cs_disconnected_buildings.
    :param network_info: an object storing information of the current network
    :return:
    """
    disconnected_systems = []
    dis_opex = 0
    dis_capex = 0
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
        supplied_systems = []
        # iterate through all possible cooling systems
        for system in network_info.full_cooling_systems:
            if system not in network_info.config.thermal_network.substation_cooling_systems:
                # add system to list of loads that are supplied at building level
                disconnected_systems.append(system)
        if len(disconnected_systems) > 0:
            # check if we have any disconnected systems
            system_string = find_cooling_systems_string(disconnected_systems)
            # iterate through all buildings
            for building_index, building in enumerate(network_info.building_names):
                Opex_var_chiller = 0.0
                Capex_chiller = 0.0
                Opex_var_CT = 0.0
                if building_index not in network_info.disconnected_buildings_index:
                    # if this building is disconnected it will be calculated separately
                    # Read in building demand
                    disconnected_building_demand = pd.read_csv(
                        network_info.locator.get_demand_results_file(building))
                    if not system_string:
                        # this means there are no disconnected loads. Shouldn't happen but is a failsafe
                        peak_demand_kW = 0.0
                        disconnected_demand_t_sum = 0.0
                    else:
                        for system_index, system in enumerate(system_string):  # iterate through all disconnected loads
                            # go through all systems and sum up demand values
                            if system_index == 0:
                                disconnected_demand_t = disconnected_building_demand[system]
                            else:
                                disconnected_demand_t = disconnected_demand_t + disconnected_building_demand[system]
                        peak_demand_kW = disconnected_demand_t.abs().max()  # calculate peak demand of all disconnected systems
                        disconnected_demand_t_sum = disconnected_demand_t.abs().sum()
                    print 'Calculate cost of disconnected loads in building ', building
                    if network_info.config.thermal_network_optimization.yearly_cost_calculations:
                        COP_chiller_system = VCCModel.calc_VCC_COP(network_info.config, system_string,
                                                                   centralized=False)  # FIXME [?]: changed to centralized = False please confirm
                        # calculate cost of producing cooling
                        Opex_var_chiller += disconnected_demand_t_sum / COP_chiller_system * 1000 * network_info.prices.ELEC_PRICE
                        Opex_var_CT += CTModel.calc_CT_yearly(disconnected_demand_t_sum)
                    else:
                        for t in range(HOURS_IN_YEAR):
                            # calculate COP of chiller and CT operation in this hour based on supplied loads
                            # calculate chiller COP according to the cold water supply temperature in SG context
                            for system_index, system in enumerate(
                                    system_string):  # iterate through all disconnected loads
                                if abs(disconnected_building_demand[system][t]) > 0.0:
                                    supplied_systems.append(disconnected_systems[system_index])

                            if len(supplied_systems) > 0:
                                COP_chiller_system = VCCModel.calc_VCC_COP(network_info.config,
                                                                           supplied_systems,
                                                                           centralized=True)
                                # calculate cost of producing cooling
                                Opex_var_chiller += abs(disconnected_demand_t[
                                                            t]) / COP_chiller_system * 1000 * network_info.prices.ELEC_PRICE

                                Opex_var_CT += CTModel.calc_CT(abs(disconnected_demand_t[t] * 1000),
                                                               peak_demand_kW * 1000) * network_info.prices.ELEC_PRICE

                    # calculate disconnected systems cost of disconnected loads. Assumes that all these loads are supplied by one chiller, unless this exceeds maximum chiller capacity of database
                    Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand_kW * 1000,
                                                                               network_info.locator,
                                                                               network_info.config, 'CH3')
                    Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand_kW * 1000, network_info.locator,
                                                                   network_info.config, 'CT1')
                    # sum up costs
                    dis_opex += Opex_var_chiller + Opex_fixed_chiller + Opex_fixed_CT + Opex_var_CT
                    dis_capex += Capex_chiller + Capex_CT

    dis_total = dis_opex + dis_capex
    return dis_total, dis_opex, dis_capex


def find_non_zero_demand_systems(network_info, t, disconnected_demand):
    '''
    This function iterates through all buildings to find out from which loads we have a demand, and return the non zero loads.
    :param network_info:
    :param t: hour we are looking at
    :return:
    '''
    systems = []
    if len(network_info.full_cooling_systems) > 0:
        system_string = find_cooling_systems_string(
            network_info.full_cooling_systems)  # returns string nevessary for further calculations of which systems are disconnected

        # iterate trhough all buildings
        for building_index, building in enumerate(network_info.building_names):
            for system_index, system in enumerate(list(system_string)):  # iterate through all disconnected loads
                if network_info.full_cooling_systems[system_index] not in systems:
                    # go through all systems and sum up demand values and sum
                    if abs(disconnected_demand[building][system][t]) > 0:
                        if network_info.full_cooling_systems[system_index] not in systems:
                            systems.append(network_info.full_cooling_systems[system_index])
    return systems


def calc_Ctot_cs_disconnected_buildings(network_info):
    """
    Caclulates the space cooling cost of disconnected buildings.
    The calculation for partially disconnected buildings is done in calc_Ctot_cs_disconnected_loads.
    :param network_info: an object storing information of the current network
    :return:
    """
    ## Calculate disconnected heat load costs
    dis_opex = 0.0
    dis_capex = 0.0
    supplied_systems = []
    if len(network_info.disconnected_buildings_index) > 0:  # we have disconnected buildings
        # Make sure files to read in exist
        for building_index, building in enumerate(network_info.building_names):  # iterate through all buildings
            Opex_var_chiller = 0.0
            Opex_var_CT = 0.0
            if building_index in network_info.disconnected_buildings_index:  # disconnected building
                # Read in demand of building
                disconnected_building_demand = pd.read_csv(
                    network_info.locator.get_demand_results_file(building))
                # sum up demand of all loads
                demand_total_hourly_kWh = disconnected_building_demand['Qcs_sys_scu_kWh'].abs() + \
                                          disconnected_building_demand[
                                              'Qcs_sys_ahu_kWh'].abs() + disconnected_building_demand[
                                              'Qcs_sys_aru_kWh'].abs()
                # calculate peak demand
                peak_demand_kW = demand_total_hourly_kWh.abs().max()
                print 'Calculate cost of disconnected building production at building ', building
                if network_info.config.thermal_network_optimization.yearly_cost_calculations:
                    demand_total_yearly_kWh = demand_total_hourly_kWh.sum()
                    # calculate plant COP according to the cold water supply temperature in SG context
                    COP_chiller_system = VCCModel.calc_VCC_COP(network_info.config,
                                                               ['ahu', 'aru', 'scu'],
                                                               centralized=True)
                    # calculate cost of producing cooling
                    Opex_var_chiller += demand_total_yearly_kWh / COP_chiller_system * 1000 * network_info.prices.ELEC_PRICE
                    Opex_var_CT += CTModel.calc_CT_yearly(demand_total_yearly_kWh)
                else:
                    for t in range(HOURS_IN_YEAR):
                        if abs(disconnected_building_demand['Qcs_sys_scu_kWh'][t]) > 0:
                            supplied_systems.append('scu')
                        if abs(disconnected_building_demand['Qcs_sys_ahu_kWh'][t]) > 0:
                            supplied_systems.append('ahu')
                        if abs(disconnected_building_demand['Qcs_sys_aru_kWh'][t]) > 0:
                            supplied_systems.append('aru')
                        # calculate COP of plant operation in this hour based on supplied loads
                        # calculate plant COP according to the cold water supply temperature in SG context
                        COP_chiller_system = VCCModel.calc_VCC_COP(network_info.config, supplied_systems,
                                                                   centralized=True)
                        # calculate cost of producing cooling
                        Opex_var_chiller += abs(demand_total_hourly_kWh[
                                                    t]) / COP_chiller_system * 1000 * network_info.prices.ELEC_PRICE

                        Opex_var_CT += CTModel.calc_CT(abs(demand_total_hourly_kWh[t] * 1000),
                                                       peak_demand_kW * 1000) * network_info.prices.ELEC_PRICE

                # calculate cost of chiller and cooling tower at building level
                Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand_kW * 1000, network_info.locator,
                                                                           network_info.config, 'CH3')
                # FIXME: cooling tower should be sized for the heat rejected from chiller condenser
                Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand_kW * 1000, network_info.locator,
                                                               network_info.config, 'CT1')
                # sum up costs
                dis_opex += Opex_var_chiller + Opex_fixed_chiller + Opex_fixed_CT + Opex_var_CT
                dis_capex += Capex_chiller + Capex_CT

    dis_total = dis_opex + dis_capex
    return dis_total, dis_opex, dis_capex


def calc_Ctot_cs_district(network_info):
    """
    Calculates the total costs for cooling of the entire district (including cooling networks and disconnected loads/buildings)
    Maintenance of network neglected, see Documentation Master Thesis Lennart Rogenhofer
    :param network_info:
    :return:
    """
    # read in general values for cost calculation
    lca = lca_calculations(network_info.locator, network_info.config)
    network_info.prices = Prices(network_info.locator, network_info.config)
    network_info.prices.ELEC_PRICE = lca.ELEC_PRICE  # [USD/kWh]
    network_info.network_features = network_opt.network_opt_main(network_info.config,
                                                                 network_info.locator)
    ## calculate Network costs
    # Network pipes
    Capex_a_netw = calc_Capex_a_network_pipes(network_info)
    # Network Pump
    Capex_a_pump, Opex_tot_pump = calc_Ctot_network_pump(network_info)
    # Centralized plant
    Opex_var_chiller, Opex_tot_CT, Opex_fixed_chiller, Capex_a_CT, Capex_a_chiller = calc_Ctot_cooling_plants(
        network_info)
    if Opex_var_chiller < 1:  # no heat supplied by network # FIXME[?]: why is this necessary?
        Capex_a_netw = 0
    # calculate costs of disconnected loads
    Ctot_dis_loads, Opex_tot_dis_loads, Capex_a_dis_loads = calc_Ctot_cs_disconnected_loads(network_info)
    # calculate costs of disconnected buildings
    Ctot_dis_buildings, Opex_tot_dis_buildings, Capex_a_dis_buildings = calc_Ctot_cs_disconnected_buildings(
        network_info)
    # calculate costs of HEX at connected buildings
    Capex_a_hex, Opex_fixed_hex, Capex_hex = calc_Cinv_HEX_hisaka(network_info)
    # store results
    network_info.cost_storage.ix['capex'][
        network_info.individual_number] = Capex_a_netw + Capex_a_pump + Capex_a_dis_loads + Capex_a_dis_buildings + \
                                          Capex_a_chiller + Capex_a_CT + Capex_a_hex
    network_info.cost_storage.ix['opex'][
        network_info.individual_number] = Opex_tot_pump + Opex_var_chiller + Opex_tot_dis_loads + \
                                          Opex_tot_dis_buildings + Opex_fixed_chiller + Opex_tot_CT + Opex_fixed_hex
    network_info.cost_storage.ix['total'][
        network_info.individual_number] = Capex_a_netw + Capex_a_pump + Capex_a_chiller + Capex_a_CT + Capex_a_hex + \
                                          Opex_tot_pump + Opex_var_chiller + Ctot_dis_loads + Ctot_dis_buildings + \
                                          Opex_fixed_chiller + Opex_tot_CT + Opex_fixed_hex
    network_info.cost_storage.ix['capex_network'][network_info.individual_number] = Capex_a_netw
    network_info.cost_storage.ix['capex_pump'][network_info.individual_number] = Capex_a_pump
    network_info.cost_storage.ix['capex_hex'][network_info.individual_number] = Capex_a_hex
    network_info.cost_storage.ix['capex_dis_loads'][network_info.individual_number] = Capex_a_dis_loads
    network_info.cost_storage.ix['capex_dis_build'][network_info.individual_number] = Capex_a_dis_buildings
    network_info.cost_storage.ix['capex_chiller'][network_info.individual_number] = Capex_a_chiller
    network_info.cost_storage.ix['capex_CT'][network_info.individual_number] = Capex_a_CT
    network_info.cost_storage.ix['opex_heat'][network_info.individual_number] = Opex_var_chiller
    network_info.cost_storage.ix['opex_chiller'][network_info.individual_number] = Opex_fixed_chiller
    network_info.cost_storage.ix['opex_CT'][network_info.individual_number] = Opex_tot_CT
    network_info.cost_storage.ix['opex_pump'][network_info.individual_number] = Opex_tot_pump
    network_info.cost_storage.ix['opex_hex'][network_info.individual_number] = Opex_fixed_hex
    network_info.cost_storage.ix['opex_dis_loads'][network_info.individual_number] = Opex_tot_dis_loads
    network_info.cost_storage.ix['opex_dis_build'][network_info.individual_number] = Opex_tot_dis_buildings

    # write outputs to console for user
    print 'Annualized Capex network: ', round(Capex_a_netw)
    print 'Annualized Capex pump: ', round(Capex_a_pump)
    print 'Annualized Capex heat exchangers: ', round(Capex_a_hex)
    print 'Annualized Capex disconnected loads: ', round(Capex_a_dis_loads)
    print 'Annualized Capex disconnected buildings: ', round(Capex_a_dis_buildings)
    print 'Annualized Capex centralized chiller: ', round(Capex_a_chiller)
    print 'Annualized Capex centralized cooling tower: ', round(Capex_a_CT)
    print 'Annualized Opex chiller: ', round(Opex_var_chiller + Opex_fixed_chiller)
    print 'Annualized Opex cooling tower: ', round(Opex_tot_CT)
    print 'Annualized Opex network pump: ', round(Opex_tot_pump)
    print 'Annualized Opex heat exchangers: ', round(Opex_fixed_hex)
    print 'Annualized Opex disconnected loads: ', round(Opex_tot_dis_loads)
    print 'Annualized Opex disconnected building: ', round(Opex_tot_dis_buildings)


def find_cooling_systems_string(disconnected_systems):
    """
    Returns string of cooling load column names to read in demand at building for disocnnected supply
    :param disconnected_systems: a list containing different cooling systems (ahu, aru, scu...)
    :return:
    """
    system_string = []
    system_string_options = ['Qcs_sys_scu_kWh', 'Qcs_sys_ahu_kWh', 'Qcs_sys_aru_kWh']
    if len(disconnected_systems) <= 3:
        if 'ahu' in disconnected_systems:
            system_string.append(system_string_options[1])
        if 'aru' in disconnected_systems:
            system_string.append(system_string_options[2])
        if 'scu' in disconnected_systems:
            system_string.append(system_string_options[0])
    else:
        print 'Error in disconnected buildings list. invalid number of elements.'
        print disconnected_systems
        print len(disconnected_systems)
    return system_string


def main(network, config, network_number):
    """
    This function calculates the total costs of a network after running simulation from thermal_network_matrix.
    :param config:
    :return:
    """

    # initialize key variables
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    network_type = config.thermal_network.network_type
    network_info = Thermal_Network(locator, config, network_type, gv)
    # print('Running thermal network cost calculation for scenario %s' % config.scenario)
    # print('Running thermal network cost calculation with weather file %s' % config.weather)
    # print('Running thermal network cost calculation for region %s' % config.region)
    # print('Network costs of %s:' % network_type)

    ## read in basic information and save to object, e.g. building demand, names, total number of buildings

    total_demand = pd.read_csv(locator.get_total_demand())
    network_info.building_names = total_demand.Name.values
    network_info.number_of_buildings_in_district = total_demand.Name.count()

    # write disconnected_buildings_index into network_info
    disconnected_buildings_list = config.thermal_network.disconnected_buildings
    disconnected_buildings_index = []
    for building in disconnected_buildings_list:
        disconnected_buildings_index.append(int(np.where(network_info.building_names == building)[0]))
    network_info.disconnected_buildings_index = disconnected_buildings_index

    # initialize data storage for later output to file
    network_info.cost_storage = pd.DataFrame(np.zeros((19, 1)))
    network_info.cost_storage.index = ['capex', 'opex', 'total', 'opex_heat', 'opex_pump', 'opex_dis_loads',
                                       'opex_dis_build', 'opex_chiller', 'opex_CT', 'opex_hex', 'capex_hex',
                                       'capex_network', 'capex_pump', 'capex_dis_loads', 'capex_dis_build',
                                       'capex_chiller', 'capex_CT', 'length', 'avg_diam']
    # calculate total network costs
    calc_Ctot_cs_district(network_info)

    # calculate annual space cooling demands
    if network_type == 'DC':
        annual_demand_district_MWh = total_demand['Qcs_sys_MWhyr'].sum()
        annual_demand_disconnected_MWh = 0
        for building_index in disconnected_buildings_index:
            annual_demand_disconnected_MWh += total_demand.ix[building_index, 'Qcs_sys_MWhyr']
        annual_demand_network_MWh = annual_demand_district_MWh - annual_demand_disconnected_MWh
    else:
        annual_demand_district_MWh = total_demand['Qhs_sys_MWhyr'].sum()

    # write outputs
    cost_output = {}
    cost_output['total_annual_cost'] = round(network_info.cost_storage.ix['total'][0], 2)
    cost_output['annual_opex'] = round(network_info.cost_storage.ix['opex'][0], 2)
    cost_output['annual_capex'] = round(network_info.cost_storage.ix['capex'][0], 2)
    cost_output['total_cost_per_MWh'] = round(cost_output['total_annual_cost'] / annual_demand_district_MWh, 2)
    cost_output['opex_per_MWh'] = round(cost_output['annual_opex'] / annual_demand_district_MWh, 2)
    cost_output['capex_per_MWh'] = round(cost_output['annual_capex'] / annual_demand_district_MWh, 2)
    cost_output['annual_demand_district_MWh'] = round(annual_demand_district_MWh, 2)
    cost_output['annual_demand_disconnected_MWh'] = round(annual_demand_disconnected_MWh, 2)
    cost_output['annual_demand_network_MWh'] = round(annual_demand_network_MWh, 2)
    total_annual_cost = cost_output['total_annual_cost']
    total_annual_capex = cost_output['annual_capex']
    total_annual_opex = cost_output['annual_opex']
    cost_output = pd.DataFrame.from_dict(cost_output, orient='index')
    cost_output.to_csv(locator.get_optimization_network_layout_costs_file(config.thermal_network.network_type, network_number))
    return total_annual_cost, total_annual_capex, total_annual_opex


if __name__ == '__main__':
    main(cea.config.Configuration(), 0)
