"""
District cooling; cooling technology activation chain

Subsequent activation of eligible cooling technologies to meet the district cooling network's cooling demand.
"""

import numpy as np

import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.cooling_tower as CTModel
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.optimization.constants import VCC_T_COOL_IN, DT_COOL, ACH_T_IN_FROM_CHP_K
from cea.technologies.pumps import calc_water_body_uptake_pumping

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Shanshan Hsieh", "Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def cooling_resource_activator(Q_thermal_req,
                               T_district_cooling_supply_K,
                               T_district_cooling_return_K,
                               Q_water_body_potential_W,
                               T_source_average_water_body_K,
                               T_ground_K,
                               daily_storage_class,
                               absorption_chiller,
                               VC_chiller,
                               CCGT_operation_data,
                               master_to_slave_variables):
    """
    This function checks which cooling technologies need to be activated to meet the energy demand for a given hour.
    The technology activation chain set to be the following:
        1. Trigeneration plant (combined cycle gas turbine [heat + electricity] & absorption chiller [cooling])
        2. Base vapour compression chiller water source or free cooling using water body
        3. Peak vapour compression chiller water source or free cooling using water body
        4. Base vapour compression chiller air source
        5. Peak vapour compression chiller air source
        6. Backup vapour compression chiller air source

    * before each of these cooling technologies is activated, the current state of charge of the cold storage is
    checked. If the storage is at least partially filled, it will be prioritized to meet the cooling demand. However,
    if the storage is empty and another technology needs to be activated, the technology will be run at maximum
    capacity and the storage will be filled using the available cooling capacity.

    :param Q_thermal_req: cooling demand of DCN (in hour x)
    :param T_district_cooling_supply_K: supply temperature of DCN (in hour x)
    :param T_district_cooling_return_K: return temperature of DCN (in hour x)
    :param Q_water_body_potential_W: free cooling capacity of water body (in hour x)
    :param T_source_average_water_body_K: temperature of water drawn from the water body (in hour x)
    :param T_ground_K: temperature of ground (in hour x)
    :param daily_storage_class: characteristics of selected thermal energy storage tank (including state of charge)
    :param absorption_chiller: eligible absorption chiller types
    :param VC_chiller: eligible vapor compression chiller types
    :param CCGT_operation_data: combined cycle gas turbine characteristics
                                (input-output curves: heat content of fuel input vs. heat output of CCGT
                                                      electricity output vs. heat output of CCGT
                                                      electrical efficiency vs. heat content of fuel input)
    :param master_to_slave_variables: all the important information on the energy system configuration of an individual
                                      (buildings [connected, non-connected], heating technologies, cooling technologies,
                                      storage etc.)
    :type Q_thermal_req: float
    :type T_district_cooling_supply_K: float
    :type T_district_cooling_return_K: float
    :type Q_water_body_potential_W: float
    :type T_source_average_water_body_K: float
    :type T_ground_K: float
    :type daily_storage_class: cea.optimization.slave.daily_storage.load_leveling.LoadLevelingDailyStorage class object
    :type absorption_chiller: cea.technologies.chiller_vapor_compression.VaporCompressionChiller class object
    :type VC_chiller: cea.technologies.chiller_vapor_compression.VaporCompressionChiller class object
    :type master_to_slave_variables: cea.optimization.slave_data.SlaveDate class object

    :return daily_storage_class: characteristics of selected thermal energy storage tank (including state of charge)
    :return thermal_output: thermal energy supply by each of the eligible cooling technologies
    :return electricity_output: electrical power demand and supply (trigen-plant) of each cooling technology
    :return gas_output: natural gas demand of the trigeneration plant
    :rtype daily_storage_class: cea.optimization.slave.daily_storage.load_leveling.LoadLevelingDailyStorage class object
    :rtype thermal_output: dict (5 x float)
    :rtype electricity_output: dict (13 x float)
    :rtype gas_output: dict (1 x float)
    """

    # initializing unmet cooling load and requirements from daily storage for this hour
    Q_cooling_unmet_W = Q_thermal_req
    Q_DailyStorage_gen_directload_W = 0.0
    Q_DailyStorage_to_storage_W = 0.0
    Q_DailyStorage_content_W = 0.0

    # ACTIVATE THE TRIGEN
    if master_to_slave_variables.NG_Trigen_on == 1 and Q_cooling_unmet_W > 0.0 \
            and not np.isclose(T_district_cooling_supply_K, T_district_cooling_return_K):

        # Check what the maximum cooling capacity of the trigeneration plant can be for this individual
        size_trigen_W = master_to_slave_variables.NG_Trigen_ACH_size_W

        # If the unmet cooling load exceeds the trigen-plant's maximum capacity,
        #   try meeting the remaining cooling demand using the cold storage
        if Q_cooling_unmet_W > size_trigen_W:
            Q_Trigen_NG_gen_directload_W = size_trigen_W
            Qc_Trigen_gen_storage_W = 0.0
            Qc_from_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.discharge_storage(Q_cooling_unmet_W - size_trigen_W)
            Q_Trigen_gen_W = Q_Trigen_NG_gen_directload_W + Qc_Trigen_gen_storage_W

        # If the unmet cooling load is smaller than the trigen-plant's maximum capacity,
        #   use the available capacity to fill the cold storage
        else:
            Q_Trigen_NG_gen_directload_W = Q_cooling_unmet_W
            Qc_Trigen_gen_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.charge_storage(size_trigen_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_Trigen_gen_W = Q_Trigen_NG_gen_directload_W + Qc_Trigen_gen_storage_W

        # GET THE ABSORPTION CHILLER PERFORMANCE
        T_ACH_in_C = ACH_T_IN_FROM_CHP_K - 273
        Qc_CT_ACH_W, \
        Qh_CCGT_req_W, \
        E_ACH_req_W = calc_chiller_absorption_operation(Q_Trigen_gen_W,
                                                        T_district_cooling_return_K,
                                                        T_district_cooling_supply_K,
                                                        T_ACH_in_C,
                                                        T_ground_K,
                                                        absorption_chiller,
                                                        size_trigen_W)

        # operation of the CCGT
        Q_used_prim_CC_fn_W = CCGT_operation_data['q_input_fn_q_output_W']
        q_output_CC_min_W = CCGT_operation_data['q_output_min_W']
        Q_output_CC_max_W = CCGT_operation_data['q_output_max_W']
        eta_elec_interpol = CCGT_operation_data['eta_el_fn_q_input']

        # operation of gas turbine possible if above minimum capacity
        if Qh_CCGT_req_W >= q_output_CC_min_W:

            if Qh_CCGT_req_W <= Q_output_CC_max_W:  # Normal operation possible within part load regime
                Q_CHP_gen_W = float(Qh_CCGT_req_W)
                NG_Trigen_req_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_Trigen_NG_gen_W = np.float(eta_elec_interpol(NG_Trigen_req_W)) * NG_Trigen_req_W

            else:  # Only part of the demand can be delivered as 100% load achieved
                Q_CHP_gen_W = Q_output_CC_max_W
                NG_Trigen_req_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_Trigen_NG_gen_W = np.float(eta_elec_interpol(NG_Trigen_req_W)) * NG_Trigen_req_W
        else:
            Q_Trigen_gen_W = 0.0
            Qc_Trigen_gen_storage_W = 0.0
            NG_Trigen_req_W = 0.0
            E_Trigen_NG_gen_W = 0.0
            Q_Trigen_NG_gen_directload_W = 0.0
            Qc_from_storage_W = 0.0

        # update unmet cooling load
        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_Trigen_NG_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_to_storage_W += Qc_Trigen_gen_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_Trigen_gen_W = 0.0
        NG_Trigen_req_W = 0.0
        E_Trigen_NG_gen_W = 0.0
        Q_Trigen_NG_gen_directload_W = 0.0

    # ACTIVATE WATER SOURCE COOLING TECHNOLOGIES
    Q_water_body_W = 0.0
    E_water_body_W = 0.0
    Q_FreeCooling_WS_directload_W = 0.0

    # Base VCC water-source OR free cooling using water body
    if master_to_slave_variables.WS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0 \
            and T_source_average_water_body_K < VCC_T_COOL_IN \
            and not np.isclose(T_district_cooling_supply_K, T_district_cooling_return_K):

        # initialise variables for the wator source vapour compression chiller and free cooling calculation
        BaseVCC_WS_activated = False
        FreeCooling_WS_activated = False
        Q_BaseVCC_WS_gen_directload_W = 0.0
        # TODO: Replace the current calculation of the thermal efficiency (Carnot efficiency) to a more realistic value
        thermal_efficiency_VCC = T_district_cooling_supply_K / T_source_average_water_body_K
        capacity_BaseVCC_WS_W = master_to_slave_variables.WS_BaseVCC_size_W
        Qc_output_BaseVCC_WS_max_W = min(capacity_BaseVCC_WS_W, thermal_efficiency_VCC * Q_water_body_potential_W)

        # Activation Case 1: The water temperature doesn't allow for free cooling, therefore the VCC is activated.
        # The unmet cooling demand is larger than the maximum VCC output, therefore the storage is discharged.
        if T_district_cooling_supply_K - T_source_average_water_body_K < DT_COOL \
                and Q_cooling_unmet_W >= Qc_output_BaseVCC_WS_max_W:
            BaseVCC_WS_activated = True
            Q_BaseVCC_WS_gen_directload_W = Qc_output_BaseVCC_WS_max_W
            Qc_BaseVCC_WS_gen_storage_W = 0.0
            Qc_from_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.discharge_storage(Q_cooling_unmet_W - Qc_output_BaseVCC_WS_max_W)
            Q_BaseVCC_WS_gen_W = Q_BaseVCC_WS_gen_directload_W + Qc_BaseVCC_WS_gen_storage_W

        # Activation Case 1: The water temperature doesn't allow for free cooling, therefore the VCC is activated.
        # The maximum VCC output is larger than the unmet cooling demand, therefore the storage is charged.
        elif T_district_cooling_supply_K - T_source_average_water_body_K < DT_COOL \
                and Q_cooling_unmet_W < Qc_output_BaseVCC_WS_max_W:
            BaseVCC_WS_activated = True
            Q_BaseVCC_WS_gen_directload_W = Q_cooling_unmet_W
            Qc_BaseVCC_WS_gen_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.charge_storage(Qc_output_BaseVCC_WS_max_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_BaseVCC_WS_gen_W = Q_BaseVCC_WS_gen_directload_W + Qc_BaseVCC_WS_gen_storage_W

        # Activation Case 3: The water temperature allows for free cooling, therefore the VCC is bypassed.
        # The unmet cooling demand is larger than the water body's cooling potential, hence the storage is discharged.
        elif T_district_cooling_supply_K - T_source_average_water_body_K >= DT_COOL \
                and Q_cooling_unmet_W >= Q_water_body_potential_W:
            FreeCooling_WS_activated = True
            Q_FreeCooling_WS_directload_W = Q_water_body_potential_W
            Qc_water_body_to_storage_W = 0.0
            Qc_from_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.discharge_storage(Q_cooling_unmet_W - Q_water_body_potential_W)
            Q_water_body_W = Q_FreeCooling_WS_directload_W + Qc_water_body_to_storage_W

        # Activation Case 4: The water temperature allows for free cooling, therefore the VCC is bypassed.
        # The water body's cooling potential is larger than the unmet cooling demand, therefore the storage is charged.
        elif T_district_cooling_supply_K - T_source_average_water_body_K >= DT_COOL \
                and Q_cooling_unmet_W < Q_water_body_potential_W:
            FreeCooling_WS_activated = True
            Q_FreeCooling_WS_directload_W = Q_cooling_unmet_W
            Qc_water_body_to_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.charge_storage(Q_water_body_potential_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_water_body_W = Q_FreeCooling_WS_directload_W + Qc_water_body_to_storage_W

        # Determine the electricity needed for the hydraulic pumps and the VCC if the latter is activated...
        if BaseVCC_WS_activated:
            # TODO: Make sure the water source Base VCC's cooling output returned from the function below is in
            #       accordance with the thermal efficiency definition above
            Q_BaseVCC_WS_gen_W, \
            E_BaseVCC_WS_req_W = calc_vcc_operation(Q_BaseVCC_WS_gen_W,
                                                    T_district_cooling_return_K,
                                                    T_district_cooling_supply_K,
                                                    T_source_average_water_body_K,
                                                    capacity_BaseVCC_WS_W,
                                                    VC_chiller)

            # Delta P from linearization after distribution optimization
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_BaseVCC_WS_gen_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)

            E_BaseVCC_WS_req_W += E_pump_WS_req_W

            # Calculate metrics for energy balancing
            # The first expression below corresponds to the second law of thermodynamics, assuming that there are no
            # losses to the air (i.e. the water in the VCC is thermally sealed from the surrounding air)
            Qc_from_water_body_W = Q_BaseVCC_WS_gen_W + E_BaseVCC_WS_req_W
            Qc_from_activated_cooling_system_W = Q_BaseVCC_WS_gen_W - Qc_BaseVCC_WS_gen_storage_W
            Qc_to_storage_W = Qc_BaseVCC_WS_gen_storage_W

        # ...determine the electricity needed for only the pumps if the systems runs on free cooling.
        elif FreeCooling_WS_activated:
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_water_body_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)
            E_water_body_W = E_pump_WS_req_W
            E_BaseVCC_WS_req_W = E_pump_WS_req_W  # TODO: Check if direct water body cooling can be displayed separately

            # Calculate metrics for energy balancing
            Qc_from_water_body_W = Q_water_body_W
            Qc_from_activated_cooling_system_W = Q_water_body_W - Qc_water_body_to_storage_W
            Qc_to_storage_W = Qc_water_body_to_storage_W

        else:
            print("no water body source base load VCC was used")

        # energy balance: calculate the remaining cooling potential of the water body, the remaining unmet cooling
        # demand (after contributions from VCC and storage) of the DCN and the cooling provided by the storage
        Q_water_body_potential_W -= Qc_from_water_body_W
        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_from_activated_cooling_system_W - Qc_from_storage_W
        Q_DailyStorage_to_storage_W += Qc_to_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_BaseVCC_WS_gen_W = 0.0
        E_BaseVCC_WS_req_W = 0.0
        Q_BaseVCC_WS_gen_directload_W = 0.0

    # Peak VCC water-source OR free cooling using water body
    if master_to_slave_variables.WS_PeakVCC_on == 1 and Q_cooling_unmet_W > 0.0 \
            and T_source_average_water_body_K < VCC_T_COOL_IN \
            and not np.isclose(T_district_cooling_supply_K, T_district_cooling_return_K):

        # initialise variables for the wator source vapour compression chiller and free cooling calculation
        PeakVCC_WS_activated = False
        FreeCooling_WS_activated = False
        Q_PeakVCC_WS_gen_directload_W = 0.0
        # TODO: Replace the current calculation of the thermal efficiency (Carnot efficiency) to a more realistic value
        thermal_efficiency_VCC = T_district_cooling_supply_K / T_source_average_water_body_K
        capacity_PeakVCC_WS_W = master_to_slave_variables.WS_PeakVCC_size_W
        Qc_output_PeakVCC_WS_max_W = min(capacity_PeakVCC_WS_W, thermal_efficiency_VCC * Q_water_body_potential_W)

        # Activation Case 1: The water temperature doesn't allow for free cooling, therefore the VCC is activated.
        # The unmet cooling demand is larger than the maximum VCC output, therefore the storage is discharged.
        if T_district_cooling_supply_K - T_source_average_water_body_K < DT_COOL \
                and Q_cooling_unmet_W >= Qc_output_PeakVCC_WS_max_W:
            PeakVCC_WS_activated = True
            Q_PeakVCC_WS_gen_directload_W = Qc_output_PeakVCC_WS_max_W
            Qc_PeakVCC_WS_gen_storage_W = 0.0
            Qc_from_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.discharge_storage(Q_cooling_unmet_W - Qc_output_PeakVCC_WS_max_W)
            Q_PeakVCC_WS_gen_W = Q_PeakVCC_WS_gen_directload_W + Qc_PeakVCC_WS_gen_storage_W

        # Activation Case 1: The water temperature doesn't allow for free cooling, therefore the VCC is activated.
        # The maximum VCC output is larger than the unmet cooling demand, therefore the storage is charged.
        elif T_district_cooling_supply_K - T_source_average_water_body_K < DT_COOL \
                and Q_cooling_unmet_W < Qc_output_PeakVCC_WS_max_W:
            PeakVCC_WS_activated = True
            Q_PeakVCC_WS_gen_directload_W = Q_cooling_unmet_W
            Qc_PeakVCC_WS_gen_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.charge_storage(Qc_output_PeakVCC_WS_max_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_PeakVCC_WS_gen_W = Q_PeakVCC_WS_gen_directload_W + Qc_PeakVCC_WS_gen_storage_W

        # Activation Case 3: The water temperature allows for free cooling, therefore the VCC is bypassed.
        # The unmet cooling demand is larger than the water body's cooling potential, hence the storage is discharged.
        elif T_district_cooling_supply_K - T_source_average_water_body_K >= DT_COOL \
                and Q_cooling_unmet_W >= Q_water_body_potential_W:
            FreeCooling_WS_activated = True
            Q_FreeCooling_WS_directload_W = Q_water_body_potential_W
            Qc_water_body_to_storage_W = 0.0
            Qc_from_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.discharge_storage(Q_cooling_unmet_W - Q_water_body_potential_W)
            Q_water_body_W = Q_FreeCooling_WS_directload_W + Qc_water_body_to_storage_W

        # Activation Case 4: The water temperature allows for free cooling, therefore the VCC is bypassed.
        # The water body's cooling potential is larger than the unmet cooling demand, therefore the storage is charged.
        elif T_district_cooling_supply_K - T_source_average_water_body_K >= DT_COOL \
                and Q_cooling_unmet_W < Q_water_body_potential_W:
            FreeCooling_WS_activated = True
            Q_FreeCooling_WS_directload_W = Q_cooling_unmet_W
            Qc_water_body_to_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.charge_storage(Q_water_body_potential_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_water_body_W = Q_FreeCooling_WS_directload_W + Qc_water_body_to_storage_W

        # Determine the electricity needed for the hydraulic pumps and the VCC if the latter is activated...
        if PeakVCC_WS_activated:
            # TODO: Make sure the water source Peak VCC's cooling output returned from the function below is in
            #       accordance with the thermal efficiency definition above
            Q_PeakVCC_WS_gen_W, \
            E_PeakVCC_WS_req_W = calc_vcc_operation(Q_PeakVCC_WS_gen_W,
                                                    T_district_cooling_return_K,
                                                    T_district_cooling_supply_K,
                                                    T_source_average_water_body_K,
                                                    capacity_PeakVCC_WS_W,
                                                    VC_chiller)

            # Delta P from linearization after distribution optimization
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_PeakVCC_WS_gen_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)

            E_PeakVCC_WS_req_W += E_pump_WS_req_W

            # Calculate metrics for energy balancing
            # The first expression below corresponds to the second law of thermodynamics, assuming that there are no
            # losses to the air (i.e. the water in the VCC is thermally sealed from the surrounding air)
            Qc_from_water_body_W = Q_PeakVCC_WS_gen_W + E_PeakVCC_WS_req_W
            Qc_from_activated_cooling_system_W = Q_PeakVCC_WS_gen_W - Qc_PeakVCC_WS_gen_storage_W
            Qc_to_storage_W = Qc_PeakVCC_WS_gen_storage_W

            # ...determine the electricity needed for only the pumps if the systems runs on free cooling.
        elif FreeCooling_WS_activated:
            E_pump_WS_req_W = calc_water_body_uptake_pumping(Q_water_body_W,
                                                             T_district_cooling_return_K,
                                                             T_district_cooling_supply_K)
            E_water_body_W = E_pump_WS_req_W
            E_BaseVCC_WS_req_W = E_pump_WS_req_W  # TODO: Check if direct water body cooling can be displayed separately

            # Calculate metrics for energy balancing
            Qc_from_water_body_W = Q_water_body_W
            Qc_from_activated_cooling_system_W = Q_water_body_W - Qc_water_body_to_storage_W
            Qc_to_storage_W = Qc_water_body_to_storage_W

        else:
            print("no water body source peak load VCC was used")
        # energy balance: calculate the remaining cooling potential of the water body, the remaining unmet cooling
        # demand (after contributions from VCC and storage) of the DCN and the cooling provided by the storage
        Q_water_body_potential_W -= Qc_from_water_body_W
        Q_cooling_unmet_W = Q_cooling_unmet_W - Qc_from_activated_cooling_system_W - Qc_from_storage_W
        Q_DailyStorage_to_storage_W += Qc_to_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W

    else:
        Q_PeakVCC_WS_gen_directload_W = 0.0
        Q_PeakVCC_WS_gen_W = 0.0
        E_PeakVCC_WS_req_W = 0.0

    # ACTIVATE AIR SOURCE COOLING TECHNOLOGIES
    # Base VCC air-source with a cooling tower
    if master_to_slave_variables.AS_BaseVCC_on == 1 and Q_cooling_unmet_W > 0.0 and not np.isclose(
            T_district_cooling_supply_K,
            T_district_cooling_return_K):
        size_AS_BaseVCC_W = master_to_slave_variables.AS_BaseVCC_size_W
        if Q_cooling_unmet_W > size_AS_BaseVCC_W:
            Q_BaseVCC_AS_gen_directload_W = size_AS_BaseVCC_W
            Q_BaseVCC_AS_gen_storage_W = 0.0
            Qc_from_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.discharge_storage(Q_cooling_unmet_W - size_AS_BaseVCC_W)
            Q_BaseVCC_AS_gen_W = Q_BaseVCC_AS_gen_directload_W + Q_BaseVCC_AS_gen_storage_W
        else:
            Q_BaseVCC_AS_gen_directload_W = Q_cooling_unmet_W
            Q_BaseVCC_AS_gen_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.charge_storage(size_AS_BaseVCC_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_BaseVCC_AS_gen_W = Q_BaseVCC_AS_gen_directload_W + Q_BaseVCC_AS_gen_storage_W

        Q_BaseVCC_AS_gen_W, \
        E_BaseVCC_AS_req_W = calc_vcc_CT_operation(Q_BaseVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   size_AS_BaseVCC_W,
                                                   VC_chiller)
        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_BaseVCC_AS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_to_storage_W += Q_BaseVCC_AS_gen_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_BaseVCC_AS_gen_W = 0.0
        E_BaseVCC_AS_req_W = 0.0
        Q_BaseVCC_AS_gen_directload_W = 0.0

    # Peak VCC air-source with a cooling tower
    if master_to_slave_variables.AS_PeakVCC_on == 1 and Q_cooling_unmet_W > 0.0 and not np.isclose(
            T_district_cooling_supply_K,
            T_district_cooling_return_K):
        size_AS_PeakVCC_W = master_to_slave_variables.AS_PeakVCC_size_W
        if Q_cooling_unmet_W > size_AS_PeakVCC_W:
            Q_PeakVCC_AS_gen_directload_W = size_AS_PeakVCC_W
            Q_PeakVCC_AS_gen_storage_W = 0.0
            Qc_from_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.discharge_storage(Q_cooling_unmet_W - size_AS_PeakVCC_W)
            Q_PeakVCC_AS_gen_W = Q_PeakVCC_AS_gen_directload_W + Q_PeakVCC_AS_gen_storage_W
        else:
            Q_PeakVCC_AS_gen_directload_W = Q_cooling_unmet_W
            Q_PeakVCC_AS_gen_storage_W, Q_DailyStorage_content_W = \
                daily_storage_class.charge_storage(size_AS_PeakVCC_W - Q_cooling_unmet_W)
            Qc_from_storage_W = 0.0
            Q_PeakVCC_AS_gen_W = Q_PeakVCC_AS_gen_directload_W + Q_PeakVCC_AS_gen_storage_W

        Q_PeakVCC_AS_gen_W, \
        E_PeakVCC_AS_req_W = calc_vcc_CT_operation(Q_PeakVCC_AS_gen_W,
                                                   T_district_cooling_return_K,
                                                   T_district_cooling_supply_K,
                                                   VCC_T_COOL_IN,
                                                   size_AS_PeakVCC_W,
                                                   VC_chiller)

        Q_cooling_unmet_W = Q_cooling_unmet_W - Q_PeakVCC_AS_gen_directload_W - Qc_from_storage_W
        Q_DailyStorage_to_storage_W += Q_PeakVCC_AS_gen_storage_W
        Q_DailyStorage_gen_directload_W += Qc_from_storage_W
    else:
        Q_PeakVCC_AS_gen_W = 0.0
        E_PeakVCC_AS_req_W = 0.0
        Q_BaseVCC_AS_gen_directload_W = 0.0
        Q_PeakVCC_AS_gen_directload_W = 0.0

    if Q_cooling_unmet_W > 1.0E-3:
        Q_BackupVCC_AS_gen_W = Q_cooling_unmet_W  # this will become the back-up chiller
        Q_BackupVCC_AS_directload_W = Q_cooling_unmet_W
    else:
        Q_BackupVCC_AS_gen_W = 0.0
        Q_BackupVCC_AS_directload_W = 0.0

    # writing outputs
    electricity_output = {
        'E_BaseVCC_WS_req_W': E_BaseVCC_WS_req_W,
        'E_PeakVCC_WS_req_W': E_PeakVCC_WS_req_W,
        'E_water_body_W': E_water_body_W,
        'E_BaseVCC_AS_req_W': E_BaseVCC_AS_req_W,
        'E_PeakVCC_AS_req_W': E_PeakVCC_AS_req_W,
        'E_Trigen_NG_gen_W': E_Trigen_NG_gen_W
    }

    thermal_output = {
        # cooling total
        'Q_Trigen_NG_gen_W': Q_Trigen_gen_W,
        'Q_BaseVCC_WS_gen_W': Q_BaseVCC_WS_gen_W,
        'Q_PeakVCC_WS_gen_W': Q_PeakVCC_WS_gen_W,
        'Q_water_body_W': Q_water_body_W,
        'Q_BaseVCC_AS_gen_W': Q_BaseVCC_AS_gen_W,
        'Q_PeakVCC_AS_gen_W': Q_PeakVCC_AS_gen_W,
        'Q_BackupVCC_AS_gen_W': Q_BackupVCC_AS_gen_W,

        # daily storage
        'Q_DailyStorage_content_W': Q_DailyStorage_content_W,
        'Q_DailyStorage_to_storage_W': Q_DailyStorage_to_storage_W,

        # cooling to direct load
        'Q_DailyStorage_gen_directload_W': Q_DailyStorage_gen_directload_W,
        "Q_Trigen_NG_gen_directload_W": Q_Trigen_NG_gen_directload_W,
        "Q_BaseVCC_WS_gen_directload_W": Q_BaseVCC_WS_gen_directload_W,
        "Q_PeakVCC_WS_gen_directload_W": Q_PeakVCC_WS_gen_directload_W,
        "Q_FreeCooling_WS_directload_W": Q_FreeCooling_WS_directload_W,
        "Q_BaseVCC_AS_gen_directload_W": Q_BaseVCC_AS_gen_directload_W,
        "Q_PeakVCC_AS_gen_directload_W": Q_PeakVCC_AS_gen_directload_W,
        "Q_BackupVCC_AS_directload_W": Q_BackupVCC_AS_directload_W,
    }

    gas_output = {
        'NG_Trigen_req_W': NG_Trigen_req_W
    }

    return daily_storage_class, thermal_output, electricity_output, gas_output


def calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, T_source_K, chiller_size, VC_chiller):
    """
    Calculate cooling energy supplied by the vapour compression chiller and the corresponding electrical energy
    required.

    :param float Qc_from_VCC_W: cooling supplied by the vapour compression chiller
    :param float T_DCN_re_K: return temperature of the district cooling network (chilled water cycle supply)
    :param float T_DCN_sup_K: supply temperature of the district cooling network (chilled water cycle supply)
    :param float T_source_K: temperature of the water body used for cooling (cooling water cycle supply)
    :param float chiller_size: capacity of vapor compression chiller
    :param VaporCompressionChiller class object VC_chiller: eligible vapor compression chiller types

    :return float Qc_VCC_W: cold energy supply to the district cooling network (chilled water cycle supply)
    :return float E_used_VCC_W: electrical energy required to operate the VCC to output Qc_VCC_W
    """
    Qc_from_VCC_W = min(Qc_from_VCC_W,
                        chiller_size)  # The chiller can not supply more cooling than the installed capacity allows
    VCC_operation = chiller_vapor_compression.calc_VCC(chiller_size, Qc_from_VCC_W, T_DCN_sup_K, T_DCN_re_K, T_source_K,
                                                       VC_chiller)

    # unpack outputs
    Qc_VCC_W = VCC_operation['q_chw_W']
    E_used_VCC_W = VCC_operation['wdot_W']

    return Qc_VCC_W, E_used_VCC_W


def calc_vcc_CT_operation(Qc_from_VCC_W,
                          T_DCN_re_K,
                          T_DCN_sup_K,
                          T_source_K,
                          size_chiller_CT,
                          VC_chiller):
    VCC_operation = chiller_vapor_compression.calc_VCC(size_chiller_CT, Qc_from_VCC_W, T_DCN_sup_K, T_DCN_re_K,
                                                       T_source_K, VC_chiller)

    # unpack outputs
    Qc_CT_VCC_W = VCC_operation['q_cw_W']
    Qc_VCC_W = VCC_operation['q_chw_W']

    # calculate cooling tower
    wdot_CT_Wh = CTModel.calc_CT(Qc_CT_VCC_W, size_chiller_CT)

    # calcualte energy consumption and variable costs
    E_used_VCC_W = (VCC_operation['wdot_W'] + wdot_CT_Wh)

    return Qc_VCC_W, E_used_VCC_W


def calc_chiller_absorption_operation(Qc_ACH_req_W, T_DCN_re_K, T_DCN_sup_K, T_ACH_in_C, T_ground_K, chiller_prop,
                                      size_ACH_W):
    if T_DCN_re_K == T_DCN_sup_K:
        mdot_ACH_kgpers = 0
    else:
        mdot_ACH_kgpers = Qc_ACH_req_W / (
                (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH

    ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers,
                                                         T_DCN_sup_K,
                                                         T_DCN_re_K,
                                                         T_ACH_in_C,
                                                         T_ground_K,
                                                         chiller_prop)

    Qc_CT_ACH_W = ACH_operation['q_cw_W']

    # calculate cooling tower
    wdot_CT_Wh = CTModel.calc_CT(Qc_CT_ACH_W, size_ACH_W)

    # calcualte energy consumption and variable costs
    Qh_CHP_ACH_W = ACH_operation['q_hw_W']
    E_used_ACH_W = ACH_operation['wdot_W'] + wdot_CT_Wh

    return Qc_CT_ACH_W, Qh_CHP_ACH_W, E_used_ACH_W
