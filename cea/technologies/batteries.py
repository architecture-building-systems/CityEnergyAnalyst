"""
electric energy storage (for daily operation)
"""

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2021, Cooling Singapore"
__credits__ = ["Jimeno Fonseca, Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "jimeno.fonseca@ebp.ch"
__status__ = "Production"


class Battery(object):
    def __init__(self, size_Wh:float, database_model_parameters,
                 type_storage:str, activation=True, debug=False):

        # INITIALIZING THE CLASS
        self.hour = 0  # this just to know when the storage is being run.
        self.debug = debug  # this is to show extra messages and debug the code easily
        self.activated = activation  # It is a boolean and indicates if the storage is on or off (True or False)
        self.hour_of_last_activation = 0  # this is to make sure passive thermal gains are accounted for correctly.
        self.size_Wh = size_Wh  # It is a float and it is the size of the storage in Wh
        self.type_storage = type_storage  # code which refers to the type of storage to be used from the conversion database

        # INITIALIZING MODEL PARAMETERS FROM DATABASE OF CONVERSION TECHNOLOGIES / TES
        self.storage_prop = database_model_parameters[database_model_parameters['code'] == type_storage]
        self.description = self.storage_prop['Description'].values[0]
        self.specific_energy_Wh_kg = self.storage_prop['specific_energy_Wh_kg'].values[0]
        self.specific_power_W_kg = self.storage_prop['specific_power_W_kg'].values[0]
        self.energy_density_Wh_m3 = self.storage_prop['energy_density_Wh_m3'].values[0]
        self.power_density_W_m3 = self.storage_prop['power_density_W_m3'].values[0]
        self.charging_efficiency = self.storage_prop['n_ch'].values[0]
        self.discharging_efficiency = self.storage_prop['n_disch'].values[0]
        self.hourly_self_discharge = self.storage_prop['self_discharge'].values[0]

        # INITIALIZE OTHER PHYSICAL PROPERTIES NEEDED THROUGH THE SCRIPT
        self.mass_storage_max_kg = calc_battery_mass(self.size_Wh,
                                                          self.specific_energy_Wh_kg)
        self.V_battery_m3 = self.size_Wh / self.energy_density_Wh_m3

        # initialize variables and properties (empty storage)
        self.current_storage_capacity_Wh = 0.0
        self.current_thermal_gain_Wh = 0.0

    def balance_storage(self):
        """
        The aim of this function is to calculate the new state of the storage if it was not charged or discharged.
        So pretty much we factor in the thermal gain when the storage remains idle.
        """
        if self.activated:
            self.current_thermal_gain_Wh = self.hourly_self_discharge * (self.hour - self.hour_of_last_activation)
            new_storage_capacity_wh = self.current_storage_capacity_Wh * (1 - self.current_thermal_gain_Wh)

            # finally update all variables
            self.current_storage_capacity_Wh = new_storage_capacity_wh
            self.hour_of_last_activation = self.hour

        return self.current_storage_capacity_Wh

    def charge_storage(self, load_to_storage_Wh):
        if self.activated:
            # calculate passive thermal gain since last activation
            self.current_thermal_gain_Wh = self.hourly_self_discharge * (self.hour - self.hour_of_last_activation)

            # factor the efficiency of the exchange in
            effective_load_to_storage_Wh = load_to_storage_Wh * self.charging_efficiency
            # discount the thermal gain due to a hotter environment
            state_the_storage_after_thermal_gain = self.current_storage_capacity_Wh * (1 - self.current_thermal_gain_Wh)

            if state_the_storage_after_thermal_gain <= 0.0:  # check so we do not get negative storage capacities.
                state_the_storage_after_thermal_gain = 0.0

            # CASE 1 the storage is empty:
            if state_the_storage_after_thermal_gain == 0.0:
                # CASE 1.1 the effective load is bigger than the capacity of the storage
                if effective_load_to_storage_Wh >= self.size_Wh:
                    effective_load_to_storage_Wh = self.size_Wh
                    new_storage_capacity_Wh = self.size_Wh

                # CASE 1.2 the effective load is smaller than the capacity of the storage
                elif effective_load_to_storage_Wh < self.size_Wh:
                    new_storage_capacity_Wh = effective_load_to_storage_Wh

            # CASE 2 the storage is partially full or full
            elif 0.0 < state_the_storage_after_thermal_gain <= self.size_Wh:
                # CASE 2.1 the effective load + the storage capacity now is bigger than the total capacity
                if (state_the_storage_after_thermal_gain + effective_load_to_storage_Wh) >= self.size_Wh:
                    effective_load_to_storage_Wh = self.size_Wh - state_the_storage_after_thermal_gain
                    new_storage_capacity_Wh = self.size_Wh

                # CASE 2.2 the effective load + the storage capacity now is lower than the total capacity
                elif (state_the_storage_after_thermal_gain + effective_load_to_storage_Wh) < self.size_Wh:
                    effective_load_to_storage_Wh = effective_load_to_storage_Wh
                    new_storage_capacity_Wh = state_the_storage_after_thermal_gain + effective_load_to_storage_Wh

            # recalculate the storage capacity after losses
            final_load_to_storage_Wh = effective_load_to_storage_Wh / self.charging_efficiency

            # finally update all variables
            self.current_storage_capacity_Wh = new_storage_capacity_Wh
            self.hour_of_last_activation = self.hour

            return final_load_to_storage_Wh, new_storage_capacity_Wh
        else:
            return 0.0, 0.0

    def discharge_storage(self, load_from_storage_Wh):
        if self.activated:
            # calculate passive thermal gain since last activation
            self.current_thermal_gain_Wh = self.hourly_self_discharge * (self.hour - self.hour_of_last_activation)

            # factor in the efficiency of discharge
            effective_load_from_storage_Wh = load_from_storage_Wh / self.discharging_efficiency
            # discount the thermal gain due to a hotter environment
            state_the_storage_after_thermal_gain = self.current_storage_capacity_Wh * (1 - self.current_thermal_gain_Wh)

            if state_the_storage_after_thermal_gain <= 0.0:  # check so we do not get negative storage capacities.
                state_the_storage_after_thermal_gain = 0.0

            # CASE 1 the storage is empty:
            if state_the_storage_after_thermal_gain == 0.0:
                effective_load_from_storage_Wh = 0.0
                new_storage_capacity_Wh = state_the_storage_after_thermal_gain

            # CASE 2 the storage is partially full or full:
            elif 0.0 < state_the_storage_after_thermal_gain <= self.size_Wh:
                # CASE 2.1 the request is too high and will go beyond emptying the storage
                if (state_the_storage_after_thermal_gain - effective_load_from_storage_Wh) < 0.0:
                    effective_load_from_storage_Wh = state_the_storage_after_thermal_gain
                    new_storage_capacity_Wh = 0.0

                # CASE 2.2 the request is just right and it will not empty the storage
                elif (state_the_storage_after_thermal_gain - effective_load_from_storage_Wh) >= 0.0:
                    effective_load_from_storage_Wh = effective_load_from_storage_Wh
                    new_storage_capacity_Wh = state_the_storage_after_thermal_gain - effective_load_from_storage_Wh

            # recalculate the storage capacity after losses
            final_load_from_storage_Wh = effective_load_from_storage_Wh * self.discharging_efficiency

            # finally update all variables
            self.current_storage_capacity_Wh = new_storage_capacity_Wh
            self.hour_of_last_activation = self.hour

            return final_load_from_storage_Wh, new_storage_capacity_Wh
        else:
            return 0.0, 0.0


def calc_battery_mass(size_Wh, specific_energy_Wh_kg):

    mass_kg = size_Wh / specific_energy_Wh_kg
    return mass_kg



if __name__ == '__main__':
    ##### TEST  ######
    import plotly.graph_objs as go
    from cea.plots.variable_naming import COLOR, NAMING

    # select one tank to test
    type_storage = "BT1"

    # test tank based in unittests (Check the unittests to see how this works)
    from cea.tests.test_technologies import TestColdPcmThermalStorage
    test = TestColdPcmThermalStorage()
    TestColdPcmThermalStorage.setUpClass()
    test.type_storage = type_storage

    # the test returns a. results of the checkResults, b. the data, c. a description of the tank.
    # the first is used as reference parameter of the checkResults. The B and C are used to make a plot as follows.
    results, data, description = test.test_cold_pcm_thermal_storage(checkResults=False)
    print(results)

    # here is the second test about volume and costs of the storage
    results = test.test_cold_pcm_thermal_storage_costs(checkResults=False)
    print(results)

    # plot results
    analysis_fields = ["Q_DailyStorage_gen_directLoad_W", "Q_DailyStorage_to_storage_W"]
    traces = []
    fig = go.Figure()
    for field in analysis_fields:
        y = data[field].values / 1E3  # to kWh
        name = NAMING[field]
        fig.add_trace(go.Bar(x=data.index, y=y, name=name, marker=dict(color=COLOR[field]), yaxis='y'))

    fig.add_trace(go.Line(x=data.index, y=data["Q_DailyStorage_content_W"] / 1000, yaxis='y', name=NAMING["Q_DailyStorage_content_W"], line_shape='spline'))
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

