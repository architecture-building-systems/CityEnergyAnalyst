import cea.technologies.storage_tank as storage_tank


class LoadLevelingDailyStorage(object):
    def __init__(self, storage_on, Qc_tank_charging_limit_W, T_tank_fully_charged_K, T_tank_fully_discharged_K,
                 T_tank_K, T_ground_average_K):
        self.storage_on = storage_on
        self.T_ground_average_K = T_ground_average_K
        self.T_tank_K = T_tank_K
        self.Qc_tank_charging_limit_W = Qc_tank_charging_limit_W
        self.T_tank_fully_charged_K = T_tank_fully_charged_K
        self.T_tank_fully_discharged_K = T_tank_fully_discharged_K
        self.Q_from_storage_W = 0.0
        self.V_tank_m3 = storage_tank.calc_storage_tank_volume(self.Qc_tank_charging_limit_W,
                                                               self.T_tank_fully_charged_K,
                                                               self.T_tank_fully_discharged_K)
        self.Area_tank_surface_m2 = storage_tank.calc_tank_surface_area(self.V_tank_m3 )
        self.Q_from_storage_W = 0.0
        self.Q_current_storage_empty_capacity_W = self.Qc_tank_charging_limit_W  # start with an empty tank
        self.Q_current_storage_filled_capacity_W = 0.0  # start with an empty tank

    def storage_temperature(self, Q_storage_possible_W, activation):
        T_tank_C = self.T_tank_K - 273
        T_ground_C = self.T_ground_average_K - 273
        if activation == "charge":
            Qc_from_Tank_W = 0.0
            Qc_to_tank_W = Q_storage_possible_W
            T_tank_K = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                               self.V_tank_m3, self.Area_tank_surface_m2, 'cold_water')

        elif activation == "discharge":
            Qc_from_Tank_W = Q_storage_possible_W
            Qc_to_tank_W = 0.0
            T_tank_K = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                               self.V_tank_m3, self.Area_tank_surface_m2, 'cold_water')

        return T_tank_K

    def charge_storage(self, Q_request_W):
        if self.storage_on and self.Q_current_storage_filled_capacity_W != self.Qc_tank_charging_limit_W:
            if Q_request_W < self.Q_current_storage_empty_capacity_W:
                Q_to_storage_possible_W = Q_request_W
            else:
                Q_to_storage_possible_W = self.Q_current_storage_empty_capacity_W

            self.T_tank_K = self.storage_temperature(Q_to_storage_possible_W, "charge")
            self.Q_current_storage_empty_capacity_W = self.Q_current_storage_empty_capacity_W - Q_to_storage_possible_W
            self.Q_current_storage_filled_capacity_W = self.Qc_tank_charging_limit_W - self.Q_current_storage_empty_capacity_W
        else:
            Q_to_storage_possible_W = 0.0

        return Q_to_storage_possible_W

    def discharge_storage(self, Q_request_W):
        if self.storage_on and self.Q_current_storage_empty_capacity_W != self.Qc_tank_charging_limit_W:
            if Q_request_W < self.Q_current_storage_filled_capacity_W:
                Q_from_storage_possible_W = Q_request_W
            else:
                Q_from_storage_possible_W = self.Q_current_storage_filled_capacity_W

            self.T_tank_K = self.storage_temperature(Q_from_storage_possible_W, "discharge")
            self.Q_current_storage_empty_capacity_W = self.Q_current_storage_empty_capacity_W + Q_from_storage_possible_W
            self.Q_current_storage_filled_capacity_W = self.Q_current_storage_filled_capacity_W - Q_from_storage_possible_W
        else:
            Q_from_storage_possible_W = 0.0

        return Q_from_storage_possible_W
