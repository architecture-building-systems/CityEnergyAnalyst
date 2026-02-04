import math
import numpy as np
from cea.constants import P_WATER_KGPERM3

from .fluid_properties import calc_kinematic_viscosity
from cea.technologies.constants import ROUGHNESS


def calc_pressure_loss_pipe(pipe_diameter_m, pipe_length_m, mass_flow_rate_kgs, t_edge__k, loop_type):
    """
    Calculate pressure loss in pipe using Darcy-Weisbach equation.

    Standards Compliance
    --------------------
    - Darcy-Weisbach equation: Fundamental fluid mechanics
    - EN 13941-1:2019: District heating pipe hydraulic calculations

    Formula
    -------
    For branch calculation (loop_type = 2):
        ΔP = f × 8 × m² × L / (π² × D⁵ × ρ)  [Pa]

    For loop derivative (loop_type = 1):
        ∂P/∂m = f × 16 × m × L / (π² × D⁵ × ρ)  [Pa·s/kg]

    where:
        - f: Darcy friction factor (calculated using Swamee-Jain equation)
        - m: mass flow rate [kg/s]
        - L: pipe length [m]
        - D: pipe diameter [m]
        - ρ: water density [kg/m³]

    Parameters
    ----------
    pipe_diameter_m : ndarray
        Pipe diameter [m] for each edge in the network (e x 1)
    pipe_length_m : ndarray
        Pipe length [m] for each edge in the network (e x 1)
    mass_flow_rate_kgs : ndarray
        Mass flow rate [kg/s] in each edge at time t (t x e)
    t_edge__k : list or ndarray
        Temperature [K] in each edge at time t (t x e)
    loop_type : int
        Calculation mode:
        - 1: Partial derivative for loop calculation (∂P/∂m)
        - 2: Direct pressure loss calculation (ΔP)

    Returns
    -------
    ndarray
        Pressure loss [Pa] through each edge at each time (t x e)
        Or pressure loss derivative [Pa·s/kg] if loop_type = 1

    References
    ----------
    [Oppelt2016] Oppelt, T., et al. (2016). Applied Thermal Engineering, 102, 336-345.
    [White2016] White, F.M. (2016). Fluid Mechanics (8th ed.). McGraw-Hill

    Notes
    -----
    The Darcy-Weisbach equation is the fundamental equation for pressure loss
    in pipe flow and is valid for all flow regimes (laminar, transition, turbulent).

    The loop_type parameter allows this function to be used both in:
    1. Direct pressure loss calculation for network branches
    2. Iterative network solving using the gradient method (Todini & Pilati, 1987)"""

    mass_flow_rate_kgs = np.array(mass_flow_rate_kgs)
    pipe_length_m = np.array(pipe_length_m)
    pipe_diameter_m = np.array(pipe_diameter_m)
    reynolds = calc_reynolds(mass_flow_rate_kgs, t_edge__k, pipe_diameter_m)

    darcy = calc_darcy(pipe_diameter_m, reynolds, ROUGHNESS)

    if loop_type == 1:  # dp/dm partial derivative of edge pressure loss equation
        pressure_loss_edge_Pa = darcy * 16 * mass_flow_rate_kgs * pipe_length_m / (
                math.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
    else:
        # [STANDARD: ISO 5167] Darcy-Weisbach equation for pressure loss
        pressure_loss_edge_Pa = darcy * 8 * mass_flow_rate_kgs ** 2 * pipe_length_m / (
                math.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
    return pressure_loss_edge_Pa


def calc_darcy(pipe_diameter_m, reynolds, pipe_roughness_m):
    """
    Calculate Darcy friction factor using flow regime-appropriate correlations.

    Standards Compliance
    --------------------
    - Colebrook-White equation: Colebrook (1939)
    - Swamee-Jain: Explicit approximation with ±1% accuracy

    Flow Regimes
    ------------
    1. Laminar (Re ≤ 2300):
           f = 64/Re
       [Standard laminar flow correlation]

    2. Transition (2300 < Re ≤ 5000):
           f = 0.316 × Re⁻⁰·²⁵
       [Blasius equation for smooth pipes]

    3. Turbulent (Re > 5000):
           f = 1.325 × [ln(ε/(3.7D) + 5.74/Re⁰·⁹)]⁻²
       [Swamee-Jain explicit equation]

    Valid Ranges (Turbulent)
    -------------------------
    - Reynolds number: 5,000 - 10⁸
    - Relative roughness (ε/D): 10⁻⁶ - 0.05
    - Accuracy: ±1% vs. Colebrook-White

    Parameters
    ----------
    pipe_diameter_m : ndarray
        Pipe diameter [m] for each edge (e x 1)
    reynolds : ndarray
        Reynolds number [-] for each edge (e x 1)
    pipe_roughness_m : float
        Absolute pipe roughness [m]
        Typical value: 0.02 mm (2×10⁻⁵ m) for steel pipe
        Range: 10⁻⁶ - 0.05 m (EN 13941)

    Returns
    -------
    ndarray
        Darcy friction factor [-] for each edge (e x 1)

    Raises
    ------
    ValueError
        If logarithm argument is invalid in Swamee-Jain calculation
        (indicates extreme pipe roughness or diameter values)

    References
    ----------
    [Oppelt2016] Oppelt, T., et al. (2016). Applied Thermal Engineering, 102, 336-345.
    [Incropera2007] Incropera, F. P., et al. (2007). Fundamentals of Heat and Mass Transfer.
    [Colebrook1939] Colebrook, C.F. (1939). J. Institution of Civil Engineers
    [SwameeJain1976] Swamee, P.K.; Jain, A.K. (1976). J. Hydraulics Division, ASCE

    Notes
    -----
    The Swamee-Jain equation provides an explicit solution to the Colebrook-White
    equation, eliminating the need for iterative calculations whilst maintaining
    accuracy within ±1%.

    For transition regime (2300 < Re ≤ 5000), a smooth pipe approximation is used
    as roughness effects are minimal at low Reynolds numbers (see Moody Diagram).

    The function returns f = 0 for Re ≤ 1 to avoid division by zero and represent
    negligible flow conditions."""
    darcy = np.zeros(reynolds.size)
    # necessary to make sure pipe_diameter is 1D vector as input formats can vary
    if hasattr(pipe_diameter_m[0], '__len__'):
        pipe_diameter_m = pipe_diameter_m[0]
    for rey in range(reynolds.size):
        if reynolds[rey] <= 1:
            darcy[rey] = 0
        elif reynolds[rey] <= 2300:
            # [STANDARD: ISO 5167] Laminar flow: f = 64/Re
            darcy[rey] = 64 / reynolds[rey]
        elif reynolds[rey] <= 5000:
            # [STANDARD: Transition regime] Blasius equation for smooth pipes
            # Reference: Moody Diagram (Incropera et al., 2007)
            # At low Re, roughness effects negligible
            darcy[rey] = 0.316 * reynolds[rey] ** -0.25
        else:
            # [STANDARD: ISO 5167, EN 13941] Swamee-Jain equation
            # Explicit Colebrook-White approximation
            # Valid: Re ∈ [5000, 10⁸], ε/D ∈ [10⁻⁶, 0.05]
            log_arg = pipe_roughness_m / (3.7 * pipe_diameter_m[rey]) + 5.74 / reynolds[rey] ** 0.9
            if not np.isfinite(log_arg) or log_arg <= 0:
                raise ValueError(
                    f"Invalid argument for logarithm in Swamee-Jain friction factor calculation!\n"
                    f"Logarithm argument: {log_arg}\n"
                    f"Pipe roughness: {pipe_roughness_m:.6e} m\n"
                    f"Pipe diameter: {pipe_diameter_m[rey]:.6f} m\n"
                    f"Reynolds number: {reynolds[rey]:.2f}\n"
                    f"Darcy friction factor: {darcy[rey] if rey < len(darcy) else 'N/A'}\n\n"
                    f"For valid Swamee-Jain calculation:\n"
                    f"- Pipe roughness must be > 0 (typical: 1e-6 to 0.05 m)\n"
                    f"- Pipe diameter must be > 0\n"
                    f"- Reynolds number should be 5000 - 1e8\n"
                    f"- Values must be finite (not NaN or inf)\n\n"
                    f"**Check the pipe properties and flow conditions."
                )

            darcy[rey] = 1.325 * np.log(log_arg) ** (-2)

    return darcy


def calc_reynolds(mass_flow_rate_kgs, temperature__k, pipe_diameter_m):
    """
    Calculate Reynolds number for internal pipe flow.

    Standards Compliance
    --------------------
    - Standard fluid mechanics definition (Reynolds, 1883)

    Formula
    -------
    Re = ρ × V × D / μ = 4 × ṁ / (π × D × μ) = 4 × Q / (π × D × ν)  [-]

    where:
        - ρ: fluid density [kg/m³]
        - V: flow velocity [m/s]
        - D: pipe diameter [m]
        - μ: dynamic viscosity [Pa·s]
        - ṁ: mass flow rate [kg/s]
        - Q: volumetric flow rate [m³/s]
        - ν: kinematic viscosity [m²/s]

    Flow Regimes
    ------------
    - Re < 2300: Laminar flow
    - 2300 < Re < 5000: Transition regime
    - Re > 5000: Turbulent flow

    Parameters
    ----------
    mass_flow_rate_kgs : ndarray
        Mass flow rate [kg/s] for each edge at time t (t x e)
    temperature__k : list or ndarray
        Fluid temperature [K] for each edge at time t (t x e)
        Used to calculate temperature-dependent viscosity
    pipe_diameter_m : ndarray
        Pipe diameter [m] for each edge (e x 1)

    Returns
    -------
    ndarray
        Reynolds number [-] for each flow condition

    Raises
    ------
    ValueError
        If pipe diameter ≤ 0 (invalid pipe geometry)
        If kinematic viscosity ≤ 0 (invalid temperature)
        If denominator near zero (numerical instability)

    Notes
    -----
    The Reynolds number is dimensionless and represents the ratio of inertial
    forces to viscous forces in the flow. It is the primary parameter for
    determining flow regime and selecting appropriate friction factor correlations.

    The function uses temperature-dependent kinematic viscosity calculated from
    the Engineering Toolbox correlation for water.

    Valid ranges:
        - Temperature: 273-413 K (0-140°C for liquid water)
        - Pipe diameter: 0.01-1.0 m (typical district heating range)
        - Mass flow rate: ≥ 0 kg/s"""

    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature__k)  # m2/s

    # Validate inputs before calculation
    if np.any(pipe_diameter_m <= 0):
        min_diameter = np.min(pipe_diameter_m)
        raise ValueError(
            f"Invalid pipe diameter for Reynolds number calculation!\n"
            f"Minimum pipe diameter: {min_diameter:.6e} m\n\n"
            f"Pipe diameter must be > 0 (typical: 0.01-1.0 m)\n\n"
            f"**Check pipe diameter values in the thermal network."
        )

    if np.any(kinematic_viscosity_m2s <= 0):
        min_viscosity = np.min(kinematic_viscosity_m2s)
        raise ValueError(
            f"Invalid kinematic viscosity for Reynolds number calculation!\n"
            f"Minimum kinematic viscosity: {min_viscosity:.6e} m²/s\n\n"
            f"Kinematic viscosity must be > 0 (typical: 1e-6 m²/s for water)\n\n"
            f"**Check temperature values (used for viscosity calculation)."
        )

    # Validate denominator for Reynolds number calculation
    denominator = math.pi * kinematic_viscosity_m2s * pipe_diameter_m

    # Check for invalid denominator values
    if np.any(np.abs(denominator) < 1e-15):
        min_denominator = np.min(np.abs(denominator))
        raise ValueError(
            f"Invalid configuration for Reynolds number calculation!\n"
            f"Denominator (π * ν * D): minimum absolute value = {min_denominator:.6e}\n"
            f"Kinematic viscosity (ν): {np.mean(kinematic_viscosity_m2s):.6e} m²/s (mean)\n"
            f"Pipe diameter (D): {np.mean(pipe_diameter_m):.6f} m (mean)\n\n"
            f"For valid Reynolds calculation:\n"
            f"- Kinematic viscosity must be > 0 (typical: 1e-6 m²/s for water)\n"
            f"- Pipe diameter must be > 0 (typical: 0.01-1.0 m)\n\n"
            f"**Check:\n"
            f"  - Temperature values (used for viscosity calculation)\n"
            f"  - Pipe diameter values in the thermal network"
        )

    reynolds = np.nan_to_num(
        4 * (abs(mass_flow_rate_kgs) / P_WATER_KGPERM3) / denominator)
    # necessary if statement to make sure output is an array type, as input formats of files can vary
    if hasattr(reynolds[0], '__len__'):
        reynolds = reynolds[0]
    return reynolds
