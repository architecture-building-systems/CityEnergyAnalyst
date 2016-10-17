"""
Compare the alternative function for `calc_t_em_ls` as described in #358 with the status quo.
"""
import cea.demand.sensible_loads


def calc_t_em_ls(heating_system, cooling_system, control_system):
    control_delta_heating = {'T1': 2.5, 'T2': 1.2, 'T3': 0.9, 'T4': 1.8}
    control_delta_cooling = {'T1': -2.5, 'T2': -1.2, 'T3': -0.9, 'T4': -1.8}
    temperature_correction_heating = {'T1': 0.15, 'T2': -0.1, 'T3': -1.1, 'T4': -0.9}
    temperature_correction_cooling = {'T1': 0.5, 'T2': 0.7, 'T3': 0.5}

    try:
        result_heating = control_delta_heating[control_system] + temperature_correction_heating[heating_system]
    except KeyError:
        result_heating = 0.0

    try:
        result_cooling = control_delta_cooling[control_system] + temperature_correction_cooling[cooling_system]
    except KeyError:
        result_cooling = 0.0

    return result_heating, result_cooling


if __name__ == '__main__':
    heating_systems = ['T1', 'T2', 'T3', 'T4', 'XYZ', None]
    cooling_systems = ['T1', 'T2', 'T3', 'T4', 'XYZ', None]
    control_systems = ['T1', 'T2', 'T3', 'T4', 'XYZ', None]

    for heating_system in heating_systems:
        for cooling_system in cooling_systems:
            for control_system in control_systems:
                original = cea.demand.sensible_loads.calc_T_em_ls(heating_system, cooling_system, control_system)
                refactored = calc_t_em_ls(heating_system, cooling_system, control_system)
                if original != refactored:
                    print "difference found for inputs:", heating_system, cooling_system, control_system, original, refactored