"""
Water / Ice / PCM short-term thermal storage (for daily operation)
"""

import math

import numpy as np
from scipy.integrate import odeint

from cea.constants import ASPECT_RATIO, HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3, WH_TO_J
from cea.demand.constants import TWW_SETPOINT, B_F
from cea.optimization.constants import T_TANK_FULLY_DISCHARGED_K, T_TANK_FULLY_CHARGED_K, DT_COOL
from cea.technologies.constants import U_COOL, U_HEAT, TANK_HEX_EFFECTIVENESS
from cea.technologies.storage_tank import calc_tank_surface_area, calc_cold_tank_heat_loss

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2021, Cooling Singapore"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "jimeno.fonseca@ebp.ch"
__status__ = "Production"


class Storage_tank_PCM(object):
    def __init__(self, available, size_Wh, properties, T_ambient_K, code):
        self.storage_on = available  # depending on the operation, it can be indicated that the tank is available or not
        self.size_Wh = size_Wh  # size of the storage in Wh
        self.T_ambient_K = T_ambient_K  # temperature outside the tank used to calculate thermal losses
        self.code = code  # code which refers to the type of storage to be used from the conversion database

        # extract properties according to chosen technology from the conversion database
        self.storage_prop = properties[properties['code'] == code]
        self.T_phase_change_K = self.storage_prop['T_PHCH_C'].values[0] + 273.0
        self.T_tank_fully_charged_K = self.storage_prop['T_min_C'].values[0] + 273.0
        self.T_tank_fully_discharged_K = self.storage_prop['T_max_C'].values[0] + 273.0
        self.latent_heat_phase_change_kJ_kg = self.storage_prop['HL_kJkg'].values[0]
        self.density_phase_change_kg_m3 = self.storage_prop['Rho_T_PHCH_kgm3'].values[0]
        self.specific_heat_capacity_solid_kJ_kgK = self.storage_prop['Cp_kJkgK'].values[0]
        self.specific_heat_capacity_liquid_kJ_kgK = self.storage_prop['Cp_kJkgK'].values[0]
        self.charging_efficiency = self.storage_prop['n_ch'].values[0]
        self.discharging_efficiency = self.storage_prop['n_disch'].values[0]

        # calculate other useful properties
        self.AT_solid_to_phase_K = self.T_phase_change_K - self.T_tank_fully_charged_K
        self.AT_phase_to_liquid_K = self.T_tank_fully_discharged_K - self.T_phase_change_K
        self.mass_storage_max_kg = calc_storage_tank_mass(self.size_Wh,
                                                          self.AT_solid_to_phase_K,
                                                          self.AT_phase_to_liquid_K,
                                                          self.latent_heat_phase_change_kJ_kg,
                                                          self.specific_heat_capacity_liquid_kJ_kgK,
                                                          self.specific_heat_capacity_solid_kJ_kgK)
        self.storage_heat_phase_change_kJ = self.mass_storage_max_kg * self.latent_heat_phase_change_kJ_kg
        self.storage_heat_solid_phase_kJ = self.mass_storage_max_kg * self.specific_heat_capacity_solid_kJ_kgK * self.AT_solid_to_phase_K
        self.storage_heat_liquid_phase_kJ = self.mass_storage_max_kg * self.specific_heat_capacity_liquid_kJ_kgK * self.AT_phase_to_liquid_K

        self.V_tank_m3 = self.mass_storage_max_kg / self.density_phase_change_kg_m3
        self.Area_tank_surface_m2 = calc_tank_surface_area(self.V_tank_m3)

        # initialize variables and properties
        self.T_tank_K = self.T_phase_change_K
        self.Q_from_storage_W = 0.0  # it is the load supplied, it starts with 0.0
        self.current_storage_capacity_Wh = 0.50 * size_Wh  # since the simualtion start at mid-night it is considered that the storage is half full by then.
        self.current_thermal_loss_Wh = self.current_storage_capacity_Wh * 0.1

    def charge_storage(self, load_to_storage_Wh, available):

        # if self.current_storage_capacity_Wh <= self.size_Wh:
        # charging the storage is possible:
        # calculate the storage capacity once it receives the new charge and account for inneficiencies
        self.storage_on = available
        if self.storage_on:
            effective_load_to_storage_Wh = load_to_storage_Wh * self.charging_efficiency
            if np.isclose((self.current_storage_capacity_Wh + self.current_thermal_loss_Wh), self.size_Wh, rtol=0.01):
                # Storage is already full, no need to recharge.
                effective_load_to_storage_Wh = 0.0
                new_storage_capacity_wh = self.current_storage_capacity_Wh - self.current_thermal_loss_Wh
                if self.storage_heat_solid_phase_kJ > new_storage_capacity_wh > 0.0:
                    new_T_tank_K = self.T_tank_K - (self.current_thermal_loss_Wh * 3.6) / (
                            self.mass_storage_max_kg * self.specific_heat_capacity_liquid_kJ_kgK)
                # case 2: the storage tank is in phase change
                elif (
                        self.storage_heat_phase_change_kJ + self.storage_heat_liquid_phase_kJ) >= new_storage_capacity_wh >= self.storage_heat_liquid_phase_kJ:
                    new_T_tank_K = self.T_phase_change_K
                # case 3: the storage tank is in the solid phase
                elif self.size_Wh > new_storage_capacity_wh > (
                        self.storage_heat_liquid_phase_kJ + self.storage_heat_phase_change_kJ):
                    new_T_tank_K = self.T_tank_K - (self.storage_heat_liquid_phase_kJ - (self.size_Wh * 3.6) + (
                            new_storage_capacity_wh * 3.6)) \
                                   / (self.mass_storage_max_kg * self.specific_heat_capacity_solid_kJ_kgK)
                else:
                    new_T_tank_K = 0.0
                    print("there was an error in the storage tank calculation")

            elif (self.current_storage_capacity_Wh + effective_load_to_storage_Wh) > self.size_Wh:
                effective_load_to_storage_Wh = self.size_Wh - self.current_storage_capacity_Wh
                new_storage_capacity_wh = self.current_storage_capacity_Wh + effective_load_to_storage_Wh
                new_T_tank_K = self.T_tank_fully_charged_K
            else:
                # charging is possible with the full request
                new_storage_capacity_wh = self.current_storage_capacity_Wh + effective_load_to_storage_Wh

                # calculate temperatures
                # case 1: the storage tank is in the liquid phase
                if self.storage_heat_solid_phase_kJ > new_storage_capacity_wh > 0.0:
                    new_T_tank_K = self.T_tank_K - (effective_load_to_storage_Wh * 3.6) / (
                            self.mass_storage_max_kg * self.specific_heat_capacity_liquid_kJ_kgK)

                # case 2: the storage tank is in phase change
                elif (
                        self.storage_heat_phase_change_kJ + self.storage_heat_liquid_phase_kJ) >= new_storage_capacity_wh >= self.storage_heat_liquid_phase_kJ:
                    new_T_tank_K = self.T_phase_change_K
                # case 3: the storage tank is in the solid phase
                elif self.size_Wh > new_storage_capacity_wh > (
                        self.storage_heat_liquid_phase_kJ + self.storage_heat_phase_change_kJ):
                    new_T_tank_K = self.T_tank_K - (self.storage_heat_liquid_phase_kJ - (self.size_Wh * 3.6) + (
                            new_storage_capacity_wh * 3.6)) \
                                   / (self.mass_storage_max_kg * self.specific_heat_capacity_solid_kJ_kgK)
                else:
                    new_T_tank_K = 0.0
                    print("there was an error in the storage tank calculation")

                # recalculate the storage capacity after losses
            self.current_thermal_loss_Wh = calc_cold_tank_heat_loss(self.Area_tank_surface_m2,
                                                                    (new_T_tank_K + self.T_tank_K) / 2,
                                                                    self.T_ambient_K)

            new_storage_capacity_wh = new_storage_capacity_wh - self.current_thermal_loss_Wh
            load_to_storage_Wh = effective_load_to_storage_Wh / self.charging_efficiency

        else:
            load_to_storage_Wh = 0.0
            new_storage_capacity_wh = self.current_storage_capacity_Wh - self.current_thermal_loss_Wh
            if self.storage_heat_solid_phase_kJ > new_storage_capacity_wh > 0.0:
                new_T_tank_K = self.T_tank_K - (self.current_thermal_loss_Wh * 3.6) / (
                        self.mass_storage_max_kg * self.specific_heat_capacity_liquid_kJ_kgK)

            # case 2: the storage tank is in phase change
            elif (
                    self.storage_heat_phase_change_kJ + self.storage_heat_liquid_phase_kJ) >= new_storage_capacity_wh >= self.storage_heat_liquid_phase_kJ:
                new_T_tank_K = self.T_phase_change_K

            # case 3: the storage tank is in the solid phase
            elif self.size_Wh > new_storage_capacity_wh > (
                    self.storage_heat_liquid_phase_kJ + self.storage_heat_phase_change_kJ):
                new_T_tank_K = self.T_tank_K - (self.storage_heat_liquid_phase_kJ - (self.size_Wh * 3.6) + (
                        new_storage_capacity_wh * 3.6)) \
                               / (self.mass_storage_max_kg * self.specific_heat_capacity_solid_kJ_kgK)
            else:
                new_T_tank_K = 0.0
                print("there was an error in the storage tank calculation")

        # finally update all variables
        self.T_tank_K = new_T_tank_K
        self.current_storage_capacity_Wh = new_storage_capacity_wh

        return load_to_storage_Wh, new_storage_capacity_wh

    def discharge_storage(self, Q_request_W):
        if self.storage_on and self.Q_current_storage_empty_capacity_W != self.size_W:
            if Q_request_W < self.current_storage_capacity_Wh:
                Q_from_storage_possible_W = Q_request_W
            else:
                Q_from_storage_possible_W = self.current_storage_capacity_Wh

            self.T_tank_K = self.storage_temperature(Q_from_storage_possible_W, "discharge")
            self.Q_current_storage_empty_capacity_W = self.Q_current_storage_empty_capacity_W + Q_from_storage_possible_W
            self.current_storage_capacity_Wh = self.current_storage_capacity_Wh - Q_from_storage_possible_W
        else:
            Q_from_storage_possible_W = 0.0

        return Q_from_storage_possible_W


def calc_storage_tank_mass(size_Wh,
                           AT_solid_to_phase_K,
                           AT_phase_to_liquid_K,
                           latent_heat_phase_change_kJ_kg,
                           specific_heat_capacity_liquid_kJ_kgK,
                           specific_heat_capacity_solid_kJ_kgK):

    mass_kg = size_Wh * 3.6 / (specific_heat_capacity_solid_kJ_kgK * AT_solid_to_phase_K +
                               specific_heat_capacity_liquid_kJ_kgK * AT_phase_to_liquid_K +
                               latent_heat_phase_change_kJ_kg)
    return mass_kg


import pandas as pd

code = "TES2"
available = True
size_Wh = 3516852  # "1000 RTh or 3516 kWh"
properties = \
    pd.read_excel(r"C:\Users\jfo\OneDrive - EBP\Dokumente\CityEnergyAnalyst\CityEnergyAnalyst\cea\databases\SG\components\CONVERSION.xls",
                  "TES")
T_ambient_K = 30 + 273
load = [size_Wh * 0.2, size_Wh * 0.25, 69000]
available = [True] * 24
tank = Storage_tank_PCM(available=available[0],
                        size_Wh=size_Wh,
                        properties=properties,
                        T_ambient_K=T_ambient_K,
                        code=code
                        )

print(tank.storage_heat_phase_change_kJ / 3600, tank.storage_heat_solid_phase_kJ / 3600,
      tank.storage_heat_liquid_phase_kJ / 3600)

for x, y in zip(load, available):
    load_proposed_to_storage_Wh = x
    avaialbility = y
    load_to_storage_Wh, \
    storage_capacity_wh = tank.charge_storage(load_proposed_to_storage_Wh,
                                              avaialbility)
    print(load_to_storage_Wh / 1000, storage_capacity_wh / 1000, tank.T_tank_K - 273, tank.T_ambient_K - 273,
          tank.current_thermal_loss_Wh / 1000)
