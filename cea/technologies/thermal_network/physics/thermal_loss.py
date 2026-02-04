from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK


def calc_temperature_out_per_pipe(t_in, m, k, t_ground):
    """
    Calculate outlet temperature of pipe considering thermal losses.

    Standards Compliance
    --------------------
    - EN 13941-1:2019: Thermal loss calculation for buried pipes
    - Wang et al. (2016): Equation for temperature drop

    This function implements the analytical solution for pipe outlet temperature
    considering heat conduction through pipe wall, insulation, and soil to ground
    temperature, as well as convective heat transfer inside the pipe.

    Formula
    -------
    T_out = [T_in × (k/2 - m×cp) - k×T_ground] / [-(m×cp) - k/2]  [K]

    where:
        - k: aggregated heat conduction coefficient [kW/K]
        - m: mass flow rate [kg/s]
        - cp: specific heat capacity of water [kW/(kg·K)]
        - T_ground: ground temperature [K]

    Parameters
    ----------
    t_in : float
        Inlet temperature [K]
    m : float
        Mass flow rate [kg/s]
    k : float
        Aggregated thermal loss coefficient [kW/K]
        (calculated using calc_aggregated_heat_conduction_coefficient)
    t_ground : float
        Ground temperature [K]

    Returns
    -------
    float
        Outlet temperature [K]

    Raises
    ------
    ValueError
        If denominator is near zero (invalid thermal network configuration)
        This occurs when m×cp + k/2 ≈ 0, indicating either:
        - Mass flow rate too low
        - Thermal loss coefficient too high
        - Invalid physical configuration

    References
    ----------
    [Wang2016] Wang, H., et al. (2016). Energy Conversion and Management, 120, 294-305.
    [EN13941] EN 13941-1:2019: District heating pipes design standard

    Notes
    -----
    The equation is derived from energy balance:
        m×cp×(T_out - T_in) = -k×(T_avg - T_ground)
    where T_avg = (T_in + T_out)/2

    Valid ranges:
        - Mass flow: > 0.1 kg/s (minimum to avoid numerical issues)
        - Temperature: 273-413 K (liquid water)
        - Thermal loss coefficient: > 0 kW/K"""
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
