"""
Hydraulic - thermal network
"""




from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK


def calc_temperature_out_per_pipe(t_in, m, k, t_ground):
    """
    Calculate outlet temperature of pipe considering thermal losses.

    :param t_in: inlet temperature in Kelvin
    :param m: mass flow rate in kg/s
    :param k: thermal loss coefficient in kW/K
    :param t_ground: ground temperature in Kelvin
    :return: outlet temperature in Kelvin
    """
    cp_kW_per_kgK = HEAT_CAPACITY_OF_WATER_JPERKGK / 1000  # Convert J to kW

    # Calculate denominator
    denominator = -m * cp_kW_per_kgK - k / 2

    # Check for division by zero
    if abs(denominator) < 1e-10:
        raise ValueError(
            f"Invalid thermal network configuration - denominator near zero in temperature calculation!\n"
            f"Mass flow rate (m): {m:.6f} kg/s\n"
            f"Thermal loss coefficient (k): {k:.6f} kW/K\n"
            f"Heat capacity (cp): {cp_kW_per_kgK:.6f} kW/kgK\n"
            f"Denominator (-m*cp - k/2): {denominator:.10e}\n\n"
            f"This occurs when m*cp + k/2 ≈ 0.\n"
            f"**Check the mass flow rate and thermal loss coefficient values."
        )

    # Calculate numerator
    numerator = t_in * (k / 2 - m * cp_kW_per_kgK) - k * t_ground

    t_out = numerator / denominator  # [K]

    return t_out