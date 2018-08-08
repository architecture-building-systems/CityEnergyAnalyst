from __future__ import division

import numpy as np
import pandas as pd
import cea.technologies.pumps as pumps
from cea.optimization.prices import Prices as Prices
import cea.config
import cea.globalvar
import cea.inputlocator
import cea.technologies.cogeneration as chp
import cea.technologies.chiller_vapor_compression as VCCModel
import cea.technologies.cooling_tower as CTModel
from cea.optimization.constants import PUMP_ETA
from cea.optimization.lca_calculations import lca_calculations
from cea.technologies.thermal_network.thermal_network_optimization import find_systems_string

__author__ = "Lennart Rogenhofer, Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_Capex_a_network_pipes(optimal_network):
    ''' Calculates network piping costs'''
    if optimal_network.network_type == 'DH':
        InvC = optimal_network.network_features.pipesCosts_DHN
    else:
        InvC = optimal_network.network_features.pipesCosts_DCN
    # Assume lifetime of 25 years and 5 % IR
    Inv_IR = 0.05
    Inv_LT = 20
    Capex_a_netw = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    return Capex_a_netw


def calc_Ctot_network_pump(optimal_network):
    """
    Computes the total pump investment and operational cost, slightly adapted version of original in optimization main script.
    :type optimal_network: class storing network information
    :returns Capex_aannulized pump capex
    :returns Opex_a_tot: pumping cost, operational
    """
    network_type = optimal_network.config.thermal_network.network_type

    # read in node mass flows
    df = pd.read_csv(optimal_network.locator.get_edge_mass_flow_csv_file(network_type, ''), index_col=0)
    mdotA_kgpers = np.array(df)
    mdotA_kgpers = np.nan_to_num(mdotA_kgpers)
    mdotnMax_kgpers = np.amax(mdotA_kgpers)  # find highest mass flow of all nodes at all timesteps (should be at plant)
    # read in total pressure loss in kW
    deltaP_kW = pd.read_csv(optimal_network.locator.get_ploss('', network_type))
    deltaP_kW = deltaP_kW['pressure_loss_total_kW'].sum()

    Opex_var = deltaP_kW * 1000 * optimal_network.prices.ELEC_PRICE

    if optimal_network.config.thermal_network.network_type == 'DH':
        deltaPmax = np.max(optimal_network.network_features.DeltaP_DHN)
    else:
        deltaPmax = np.max(optimal_network.network_features.DeltaP_DCN)
    Capex_a, Opex_fixed = pumps.calc_Cinv_pump(deltaPmax, mdotnMax_kgpers, PUMP_ETA, optimal_network.config,
                                               optimal_network.locator, 'PU1')  # investment of Machinery
    Opex_a_tot = Opex_var + Opex_fixed

    return Capex_a, Opex_a_tot


def calc_Ctot_cooling_plants(optimal_network):
    ''' calculates chiller and cooling tower costs '''

    # read in plant heat requirement
    plant_heat_sum_kWh = pd.read_csv(optimal_network.locator.get_optimization_network_layout_plant_heat_requirement_file(
        optimal_network.network_type, optimal_network.config.thermal_network_optimization.network_name))
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
    for plant_number in range(number_of_plants): #iterate through all plants
        if number_of_plants > 1:
            plant_heat_peak_kW = plant_heat_peak_kW_list[plant_number]
        else:
            plant_heat_peak_kW = plant_heat_peak_kW_list[0]
        plant_heat_sum_kWh = plant_heat_sum_kWh_list[plant_number]

        Capex_chiller = 0
        Opex_fixed_chiller = 0
        Capex_CT = 0
        Opex_fixed_CT = 0
        if plant_heat_peak_kW > 0: # we have non 0 demand
            peak_demand = plant_heat_peak_kW * 1000  # convert to W
            # calculate Heat loss costs
            if optimal_network.network_type == 'DH':
                # Assume a COP of 1.5 e.g. in CHP plant, calculate cost of producing cooling
                Opex_var_chiller += (plant_heat_sum_kWh) / 1.5 * 1000 * optimal_network.prices.ELEC_PRICE  # TODO: Setup COP calculation for DH case
                #calculate price of equipment
                Capex_chiller, Opex_fixed_chiller = chp.calc_Cinv_CCGT(peak_demand, optimal_network.locator,
                                                                 optimal_network.config, technology=0)
                # FIXME: what is this? can we just change the function to chiller plants, and dont calculate the DH part here? we could have a COP plant when calculating DH
            else:
                # Clark D (CUNDALL). Chiller energy efficiency 2013.
                # FIXME: please add reference in the documentation of this function (see thermal_network_matrix
                # calculate plant COP according to the cold water supply temperature in SG context
                COP_plant = VCCModel.calc_VCC_COP(optimal_network.config,
                                                  optimal_network.config.thermal_network.substation_cooling_systems,
                                                  centralized=True)
                # calculate cost of producing cooling
                Opex_var_chiller += (plant_heat_sum_kWh) / COP_plant * 1000 * optimal_network.prices.ELEC_PRICE
                # calculate equipment cost of chiller and cooling tower
                Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand, optimal_network.locator,
                                                                     optimal_network.config, 'CH1')
                Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand, optimal_network.locator,
                                                               optimal_network.config, 'CT1')
                # FIXME: missing Opex_var_CT, which should be connected to cooling_tower.calc_CT (hourly)
                # FIXME: that being said, the Opex_var_chiller should also be calculated hourly
        # sum over all plants
        Capex_a_chiller += Capex_chiller
        Opex_a_chiller += Opex_fixed_chiller
        Capex_a_CT += Capex_CT
        Opex_a_CT += Opex_fixed_CT

    return Opex_var_chiller, Opex_a_CT, Opex_a_chiller, Capex_a_CT, Capex_a_chiller


def calc_Ctot_cooling_disconnected(optimal_network):
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
    if optimal_network.network_type == 'DC':
        # iterate through all possible cooling systems
        for system in optimal_network.full_cooling_systems:
            if system not in optimal_network.config.thermal_network.substation_cooling_systems:
                # add system to list of loads that are supplied at building level
                disconnected_systems.append(system)
        if len(disconnected_systems) > 0:
            # check if we have any disconnected systems
            system_string = find_systems_string(disconnected_systems) # returns string nevessary for further calculations of which systems are disconnected
            #iterate trhough all buildings
            for building_index, building in enumerate(optimal_network.building_names):
                Opex_var_chiller = 0
                Capex_chiller = 0
                # Read in building demand
                disconnected_demand = pd.read_csv(
                    optimal_network.locator.get_demand_results_file(building))
                if not system_string: # this means there are no disconnected loads. Shouldn't happen but is a failsafe
                    disconnected_demand_total = 0.0
                    peak_demand = 0.0
                else:
                    for system_index, system in enumerate(system_string): #iterate through all disconnected loads
                        # go through all systems and sum up demand values and sum
                        if system_index == 0:
                            disconnected_demand_t = disconnected_demand[system]
                            disconnected_demand_total = disconnected_demand_t.abs().sum()
                        else:
                            disconnected_demand_t = disconnected_demand_t + disconnected_demand[system]
                            disconnected_demand_total = disconnected_demand_total + disconnected_demand[
                                system].abs().sum()
                    peak_demand = disconnected_demand_t.abs().max() # calculate peak demand of all disconnected systems
                # calculate disonnected system COP
                COP_chiller_system = VCCModel.calc_VCC_COP(optimal_network.config,
                                                           disconnected_systems,
                                                           centralized=False)
                # calculate operational costs of producing cooling
                Opex_var_chiller = disconnected_demand_total / COP_chiller_system * 1000 * optimal_network.prices.ELEC_PRICE
                # calculate disconnected systems cost of disconnected loads. Assumes that all these loads are supplied by one chiller, unless this exceeds maximum chiller capacity of database
                Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand * 1000, optimal_network.locator,
                                                             optimal_network.config, 'CH3')
                Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand * 1000, optimal_network.locator,
                                                               optimal_network.config, 'CT1')
                # FIXME: missing Opex_var_CT, which should be connected to cooling_tower.calc_CT (hourly)
                # FIXME: that being said, the Opex_var_chiller should also be calculated hourly
                # sum up costs
                dis_opex += Opex_var_chiller + Opex_fixed_chiller + Opex_fixed_CT
                dis_capex += Capex_chiller + Capex_CT

    dis_total = dis_opex + dis_capex
    return dis_total, dis_opex, dis_capex


def calc_Ctot_disconnected_buildings(optimal_network):
    ## Calculate disconnected heat load costs
    dis_opex = 0
    dis_capex = 0
    # if optimal_network.network_type == 'DH':
    # information not yet available
    if len(optimal_network.disconnected_buildings_index) > 0: # we have disconnected buildings
        # Make sure files to read in exist
        for building_index, building in enumerate(optimal_network.building_names): # iterate through all buildings
            if building_index in optimal_network.disconnected_buildings_index:  # disconnected building
                # Read in demand of building
                disconnected_demand = pd.read_csv(
                    optimal_network.locator.get_demand_results_file(building))
                # sum up demand of all loads
                disconnected_demand_total = disconnected_demand['Qcs_sys_scu_kWh'].abs() + disconnected_demand[
                    'Qcs_sys_ahu_kWh'].abs() + disconnected_demand['Qcs_sys_aru_kWh'].abs()
                # calculate peak demand
                peak_demand = disconnected_demand_total.abs().max()
                # calculate aggregated demand
                disconnected_demand_total = disconnected_demand_total.abs().sum()
                # calculate system COP
                COP_chiller_system = VCCModel.calc_VCC_COP(optimal_network.config,
                                                           ['ahu', 'aru', 'scu'],
                                                           centralized=False)
                # FIXME: shouldn't it be reading from the building technical_systems.dbf?
                # calculate cost of producing cooling
                Opex_var_chiller = disconnected_demand_total / COP_chiller_system * 1000 * optimal_network.prices.ELEC_PRICE
                # calculate cost of Chiller and cooling tower at building level
                Capex_chiller, Opex_fixed_chiller = VCCModel.calc_Cinv_VCC(peak_demand * 1000, optimal_network.locator,
                                                             optimal_network.config, 'CH3')
                Capex_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(peak_demand * 1000, optimal_network.locator,
                                                               optimal_network.config, 'CT1')
                # FIXME: missing Opex_var_CT, which should be connected to cooling_tower.calc_CT (hourly)
                # FIXME: that being said, the Opex_var_chiller should also be calculated hourly
                # sum up costs
                dis_opex += Opex_var_chiller + Opex_fixed_chiller + Opex_fixed_CT
                dis_capex += Capex_chiller + Capex_CT

    dis_total = dis_opex + dis_capex
    return dis_total, dis_opex, dis_capex
