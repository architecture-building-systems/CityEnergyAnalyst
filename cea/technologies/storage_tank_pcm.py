"""
Water / Ice / PCM short-term thermal storage (for daily operation)
"""

import numpy as np
from cea.technologies.storage_tank import calc_tank_surface_area, calc_cold_tank_heat_gain
from math import log
from cea.analysis.costs.equations import calc_capex_annualized

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2021, Cooling Singapore"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "jimeno.fonseca@ebp.ch"
__status__ = "Production"


class Storage_tank_PCM(object):
    def __init__(self,  activation, size_Wh, properties, T_ambient_K, type_storage, debug=False):
        self.hour = np.nan
        self.debug = debug
        self.activated = activation # is it the storage actually on in the optimization, otehrwise return 0.0 in all values.
        self.size_Wh = size_Wh  # size of the storage in Wh
        self.T_ambient_K = T_ambient_K  # temperature outside the tank used to calculate thermal losses
        self.type_storage = type_storage  # code which refers to the type of storage to be used from the conversion database

        # extract properties according to chosen technology from the conversion database
        self.storage_prop = properties[properties['code'] == type_storage]
        self.description = self.storage_prop['Description'].values[0]
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
        self.cap_phase_change_Wh = self.mass_storage_max_kg * self.latent_heat_phase_change_kJ_kg / 3.6
        self.cap_solid_phase_Wh = self.mass_storage_max_kg * self.specific_heat_capacity_solid_kJ_kgK * self.AT_solid_to_phase_K / 3.6
        self.cap_liquid_phase_Wh = self.mass_storage_max_kg * self.specific_heat_capacity_liquid_kJ_kgK * self.AT_phase_to_liquid_K / 3.6

        self.V_tank_m3 = self.mass_storage_max_kg / self.density_phase_change_kg_m3
        self.Area_tank_surface_m2 = calc_tank_surface_area(self.V_tank_m3)

        # initialize variables and properties
        self.T_tank_K = self.T_tank_fully_discharged_K
        self.current_phase = 1 #" 1= liquid, 2, phasechange, 3, solid"
        self.current_storage_capacity_Wh = 0.0 # since the simualtion start at mid-night it is considered that the storage is half full by then.
        self.current_thermal_gain_Wh = self.current_storage_capacity_Wh * 0.1
        if self.debug:
            print("...initializing the storage...")
            print("The type of storage is a {}".format(self.description))
            print("The volume and mass of the Storage is {:.2f} m3 and {:.2f} ton".format(self.V_tank_m3,
                                                                                          self.mass_storage_max_kg / 1000))
            print(
                "The storage capacity at solid, phase change, and liquid phase are {:.2f} kWh, {:.2f} kWh, and {:.2f} kWh".format(
                    self.cap_solid_phase_Wh/ 1000, self.cap_phase_change_Wh/ 1000, self.cap_liquid_phase_Wh/ 1000))
            print(
                "The minimum, phase change, and maximum Temperatures of the storaage are {:.2f} °C, {:.2f} °C, and {:.2f} °C".format(
                    self.T_tank_fully_charged_K - 273, self.T_phase_change_K - 273, self.T_tank_fully_discharged_K - 273))
            print("...initialization of the storage finished...")

    def balance_storage(self):
        if self.activated:
            if self.debug:
                print("The current capacity and temperature is {:.2f} kWh, and {:.2f} °C".format(
                    self.current_storage_capacity_Wh / 1000, self.T_tank_K - 273))
            new_storage_capacity_wh = self.current_storage_capacity_Wh - self.current_thermal_gain_Wh
            new_phase = self.new_phase_tank(new_storage_capacity_wh)
            new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, self.current_thermal_gain_Wh)
            new_thermal_loss_Wh = calc_cold_tank_heat_gain(self.Area_tank_surface_m2,
                                                           (new_T_tank_K + self.T_tank_K) / 2,
                                                           self.T_ambient_K)

            # finally update all variables
            self.current_phase = new_phase
            self.current_thermal_gain_Wh = new_thermal_loss_Wh
            self.T_tank_K = new_T_tank_K
            self.current_storage_capacity_Wh = new_storage_capacity_wh
            if self.debug:
                print("The new capacity and temperature is {:.2f} kWh, and {:.2f} °C".format(
                    self.current_storage_capacity_Wh / 1000, self.T_tank_K - 273, ))

        return self.current_storage_capacity_Wh

    def new_phase_tank(self, new_storage_capacity_wh):
        tol = 0.000001
        # case 1: the storage tank is in liquid change
        if 0.0 <= new_storage_capacity_wh <= self.cap_liquid_phase_Wh:
            new_phase = 1
        # case 2: the storage tank is in phase change
        elif self.cap_liquid_phase_Wh < new_storage_capacity_wh <= (self.cap_liquid_phase_Wh + self.cap_phase_change_Wh):
            new_phase = 2
        # case 3: the storage tank is in the solid phase
        elif (self.cap_liquid_phase_Wh + self.cap_phase_change_Wh) < new_storage_capacity_wh <= (
                self.cap_liquid_phase_Wh + self.cap_phase_change_Wh + self.cap_solid_phase_Wh + tol):
            new_phase = 3
        else:
            print("there was an error, the new capacity was {} and the thermal loss was {}".format(new_storage_capacity_wh, self.current_thermal_gain_Wh))
        return new_phase


    def new_temperature_tank(self, new_phase, new_storage_capacity_wh, load_difference_Wh):

        T0 = self.T_tank_K
        m = self.mass_storage_max_kg
        Cp_l = self.specific_heat_capacity_liquid_kJ_kgK
        Cp_s = self.specific_heat_capacity_solid_kJ_kgK

        current_phase = self.current_phase

        if current_phase == 1 and new_phase == 1:
            if self.debug:
                print("liquid phase is maintained")
            Tb = T0
            T1 = Tb - (load_difference_Wh * 3.6) / (m * Cp_l)

        elif (current_phase == 2 and new_phase == 2):
            if self.debug:
                print("phase change is maintained")
            T1 = self.T_phase_change_K

        elif current_phase == 3 and new_phase == 3:
            if self.debug:
                print("solid phase is maintained")
            Tb = T0
            T1 = Tb - (load_difference_Wh * 3.6) / (m * Cp_s)

        elif (current_phase == 1 and new_phase == 2):  # moving from liquid to phase # charging
            if self.debug:
                print("moving from liquid to phase change")
            T1 = self.T_phase_change_K

        elif (current_phase == 2 and new_phase == 3):  # moving from phase to solid # charging
            if self.debug:
                print("moving from phase to solid phase")
            Tb = self.T_phase_change_K
            T1 = Tb - ((self.cap_solid_phase_Wh - (self.size_Wh - new_storage_capacity_wh)) * 3.6) / (m * Cp_s)

        elif (current_phase == 1 and new_phase == 3): #moving from liquid to solid # charging
            if self.debug:
                print("moving from liquid to solid phase")
            Tb = self.T_phase_change_K
            T1 = Tb - ((self.cap_solid_phase_Wh - (self.size_Wh - new_storage_capacity_wh)) * 3.6) / (m * Cp_s)

        elif (current_phase == 3 and new_phase == 2): #moving from solid to phase # discharging
            if self.debug:
                print("moving from solid to phase change")
            T1 = self.T_phase_change_K

        elif (current_phase == 2 and new_phase == 1): #moving from phase to liquid # discharging
            if self.debug:
                print("moving from phase change to liquid phase")
            Tb = self.T_phase_change_K
            T1 = Tb + ((self.cap_liquid_phase_Wh - new_storage_capacity_wh) * 3.6) / (m * Cp_l)

        elif (current_phase == 3 and new_phase == 1): #moving from solid to liquid # discharging
            if self.debug:
                print("moving from solid to liquid change")
            Tb = self.T_phase_change_K
            T1 = Tb + ((self.cap_liquid_phase_Wh - new_storage_capacity_wh) * 3.6) / (m * Cp_l)

        if T1 == np.nan:
            print("error at hour {}".format(self.hour))

        return T1

    def charge_storage(self, load_to_storage_Wh):
        if self.activated:
            if self.debug:
                print("...charging...")
                print("The current capacity and temperature is {:.2f} kWh, and {:.2f} °C".format(
                    self.current_storage_capacity_Wh / 1000, self.T_tank_K - 273))
                print("The requested load was {:.2f} kW".format(
                    load_to_storage_Wh / 1000))
                print("The current thermal gain is {:.2f} kW".format(
                    self.current_thermal_gain_Wh / 1000))

            effective_load_to_storage_Wh = load_to_storage_Wh * self.charging_efficiency
            state_the_storage_after_thermal_gain = self.current_storage_capacity_Wh - self.current_thermal_gain_Wh
            if state_the_storage_after_thermal_gain <= 0.0:
                state_the_storage_after_thermal_gain = 0.0
            # CASE 1 the storage is empty:
            if state_the_storage_after_thermal_gain == 0.0:
                #CASE 1.1 the storage can be partialy filled:
                if effective_load_to_storage_Wh >= self.size_Wh:
                    effective_load_to_storage_Wh = self.size_Wh
                    new_storage_capacity_wh = self.size_Wh
                    new_phase = self.new_phase_tank(new_storage_capacity_wh)
                    new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, effective_load_to_storage_Wh)
                elif effective_load_to_storage_Wh < self.size_Wh:
                    new_storage_capacity_wh = effective_load_to_storage_Wh
                    new_phase = self.new_phase_tank(new_storage_capacity_wh)
                    new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, effective_load_to_storage_Wh)
            # CASE 2 the storage is partialy full or full
            elif 0.0 < state_the_storage_after_thermal_gain <= self.size_Wh:
                if (state_the_storage_after_thermal_gain + effective_load_to_storage_Wh) >= self.size_Wh:
                    effective_load_to_storage_Wh = self.size_Wh - state_the_storage_after_thermal_gain
                    new_storage_capacity_wh = self.size_Wh
                    new_phase = self.new_phase_tank(new_storage_capacity_wh)
                    new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, effective_load_to_storage_Wh)
                elif (state_the_storage_after_thermal_gain + effective_load_to_storage_Wh) < self.size_Wh:
                    effective_load_to_storage_Wh = effective_load_to_storage_Wh
                    new_storage_capacity_wh = state_the_storage_after_thermal_gain + effective_load_to_storage_Wh
                    new_phase = self.new_phase_tank(new_storage_capacity_wh)
                    new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, effective_load_to_storage_Wh)

            # recalculate the storage capacity after losses
            final_load_to_storage_Wh = effective_load_to_storage_Wh / self.charging_efficiency
            new_thermal_loss_Wh = calc_cold_tank_heat_gain(self.Area_tank_surface_m2,
                                                           (new_T_tank_K + self.T_tank_K) / 2,
                                                           self.T_ambient_K)

            # finally update all variables
            self.current_phase = new_phase
            self.current_thermal_gain_Wh = new_thermal_loss_Wh
            self.T_tank_K = new_T_tank_K
            self.current_storage_capacity_Wh = new_storage_capacity_wh

            if self.debug:
                print("The possible load was {:.2f} kWh".format(final_load_to_storage_Wh / 1000))
                print("The new capacity and temperature is {:.2f} kWh, and {:.2f} °C".format(
                    self.current_storage_capacity_Wh / 1000, self.T_tank_K - 273, ))

            return final_load_to_storage_Wh, new_storage_capacity_wh
        else:
            return 0.0, 0.0

    def discharge_storage(self, load_from_storage_Wh):
        if self.activated:
            if self.debug:
                print("...discharging...")
                print("The current capacity and temperature is {:.2f} kWh, and {:.2f} °C".format(
                    self.current_storage_capacity_Wh / 1000, self.T_tank_K - 273))
                print("The requested load was {:.2f} kW".format(
                    load_from_storage_Wh / 1000))
                print("The current thermal gain is {:.2f} kW".format(
                    self.current_thermal_gain_Wh / 1000))

            effective_load_from_storage_Wh = load_from_storage_Wh / self.discharging_efficiency
            state_the_storage_after_thermal_gain = self.current_storage_capacity_Wh - self.current_thermal_gain_Wh
            if state_the_storage_after_thermal_gain <= 0.0:
                state_the_storage_after_thermal_gain = 0.0
            print(state_the_storage_after_thermal_gain)
            # CASE 1 the storage is empty:
            if state_the_storage_after_thermal_gain == 0.0:
                effective_load_from_storage_Wh = 0.0
                new_storage_capacity_wh = state_the_storage_after_thermal_gain
                new_phase = self.new_phase_tank(new_storage_capacity_wh)
                new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, 0.0)

            # CASE 2 the storage is partialy full or full
            elif 0.0 < state_the_storage_after_thermal_gain <= self.size_Wh:
                if (state_the_storage_after_thermal_gain - effective_load_from_storage_Wh) < 0.0:
                    effective_load_from_storage_Wh = state_the_storage_after_thermal_gain
                    new_storage_capacity_wh = 0.0
                    new_phase = self.new_phase_tank(new_storage_capacity_wh)
                    new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, -effective_load_from_storage_Wh)
                elif (state_the_storage_after_thermal_gain - effective_load_from_storage_Wh) >= 0.0:
                    effective_load_from_storage_Wh = effective_load_from_storage_Wh
                    new_storage_capacity_wh = state_the_storage_after_thermal_gain - effective_load_from_storage_Wh
                    new_phase = self.new_phase_tank(new_storage_capacity_wh)
                    new_T_tank_K = self.new_temperature_tank(new_phase, new_storage_capacity_wh, -effective_load_from_storage_Wh)

            # recalculate the storage capacity after losses
            final_load_to_storage_Wh = effective_load_from_storage_Wh * self.discharging_efficiency
            new_thermal_loss_Wh = calc_cold_tank_heat_gain(self.Area_tank_surface_m2,
                                                           (new_T_tank_K + self.T_tank_K) / 2,
                                                           self.T_ambient_K)

            # finally update all variables
            self.current_phase = new_phase
            self.current_thermal_gain_Wh = new_thermal_loss_Wh
            self.T_tank_K = new_T_tank_K
            self.current_storage_capacity_Wh = new_storage_capacity_wh

            if self.debug:
                print("The requested load to discharge  was {:.2f} kW, the possible load to discharge was {:.2f} kWh".format(
                    load_from_storage_Wh / 1000, final_load_to_storage_Wh / 1000))
                print("The new capacity and temperature is {:.2f} kWh, and {:.2f} °C".format(
                    self.current_storage_capacity_Wh / 1000, self.T_tank_K - 273, ))
            return final_load_to_storage_Wh, new_storage_capacity_wh
        else:
            return 0.0, 0.0

    def costs_storage(self):
        if self.activated:
            capacity_kWh = self.size_Wh / 1000
            if capacity_kWh > 0.0:
                storage_cost_data = self.storage_prop

                # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
                # capacity for the corresponding technology from the database
                if capacity_kWh < storage_cost_data.iloc[0]['cap_min']:
                    capacity_kWh = storage_cost_data[0]['cap_min']

                storage_cost_data = storage_cost_data[(storage_cost_data['cap_min'] <= capacity_kWh) & (storage_cost_data['cap_max'] > capacity_kWh)]

                Inv_a = storage_cost_data.iloc[0]['a']
                Inv_b = storage_cost_data.iloc[0]['b']
                Inv_c = storage_cost_data.iloc[0]['c']
                Inv_d = storage_cost_data.iloc[0]['d']
                Inv_e = storage_cost_data.iloc[0]['e']
                Inv_IR = storage_cost_data.iloc[0]['IR_%']
                Inv_LT = storage_cost_data.iloc[0]['LT_yr']
                Inv_mat_LT = storage_cost_data.iloc[0]['LT_mat_yr']
                C_mat_LT = storage_cost_data.iloc[0]['C_mat_%'] / 100
                Inv_OM = storage_cost_data.iloc[0]['O&M_%'] / 100

                Capex_total_USD = Inv_a + Inv_b * (capacity_kWh) ** Inv_c + (Inv_d + Inv_e * capacity_kWh) * log(capacity_kWh)
                Capex_a_storage_USD = calc_capex_annualized(Capex_total_USD, Inv_IR, Inv_LT)
                Capex_a_storage_USD += calc_capex_annualized(Capex_total_USD * C_mat_LT, Inv_IR, Inv_mat_LT)
                Opex_fixed_storage_USD = Capex_total_USD * Inv_OM
            else:
                Capex_a_storage_USD = 0.0
                Opex_fixed_storage_USD = 0.0
                Capex_total_USD = 0.0
            return Capex_a_storage_USD, Opex_fixed_storage_USD, Capex_total_USD
        else:
            return 0.0, 0.0, 0.0


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




if __name__ == '__main__':
    ##### TEST  ######
    import plotly.graph_objs as go
    from cea.plots.variable_naming import COLOR, NAMING

    # selct one tank to test
    type_storage = "TES6"

    # test tank based in unittests (Check the unittests to see how this works)
    from cea.tests.test_technologies import TestColdPcmThermalStorage
    test = TestColdPcmThermalStorage()
    TestColdPcmThermalStorage.setUpClass()
    test.type_storage = type_storage

    # the test returns a. results of the unittest, b. the data, c. a description of the tank.
    # the first is used as reference parameter o fthe unittest. The B and C are used to make a plot as follows.
    results, data, description = test.test_cold_pcm_thermal_storage(unittest=False)
    print(results)

    #here is the second test about volume and costs of the storage
    results = test.test_cold_pcm_thermal_storage_costs(unittest=False)
    print(results)

    # plot results
    analysis_fields = ["Q_DailyStorage_gen_directload_W", "Q_DailyStorage_to_storage_W"]
    traces = []
    fig = go.Figure()
    for field in analysis_fields:
        y = data[field].values / 1E3  # to kWh
        name = NAMING[field]
        fig.add_trace(go.Bar(x=data.index, y=y, name=name, marker=dict(color=COLOR[field]), yaxis='y'))

    fig.add_trace(go.Line(x=data.index, y=data["Q_DailyStorage_content_W"] / 1000, yaxis='y', name=NAMING["Q_DailyStorage_content_W"], line_shape='spline'))
    fig.add_trace(go.Line(x=data.index, y=data["T_DailyStorage_C"], yaxis='y2', name=NAMING["T_DailyStorage_C"], line_shape='spline'))
    fig.update_layout(title=description,
                        yaxis=dict(title='Load [kWh]'),
                            yaxis2=dict(title='Tank Temperature [C]', overlaying='y', side='right', range=[-1, 14]))
    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    fig.show()

