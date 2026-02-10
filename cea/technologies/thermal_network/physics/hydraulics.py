import numpy as np
from enum import IntEnum
from cea.constants import P_WATER_KGPERM3

from .fluid_properties import calc_kinematic_viscosity
from cea.technologies.constants import ROUGHNESS


class PressureLossMode(IntEnum):
    """Mode for pressure loss calculation.

    GRADIENT: Calculate pressure gradient ∂P/∂m = f × 16 × m × L / (π² × D⁵ × ρ)
    DIRECT: Calculate pressure loss ΔP = f × 8 × m² × L / (π² × D⁵ × ρ)
    """
    GRADIENT = 1
    DIRECT = 2


def calc_pressure_loss_pipe(pipe_diameter_m, pipe_length_m, mass_flow_rate_kgs, t_edge__k, mode):
    """
    Calculate pressure loss in pipe using Darcy-Weisbach equation.

    Standards Compliance
    --------------------
    - Darcy-Weisbach equation: Fundamental fluid mechanics
    - EN 13941-1:2019: District heating pipe hydraulic calculations

    Formula
    -------
    For direct calculation (mode = DIRECT):
        ΔP = f × 8 × m² × L / (π² × D⁵ × ρ)  [Pa]

    For gradient calculation (mode = GRADIENT):
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
    mode : PressureLossMode or int
        Calculation mode:
        - PressureLossMode.GRADIENT (1): Partial derivative for loop calculation (∂P/∂m)
        - PressureLossMode.DIRECT (2): Direct pressure loss calculation (ΔP)

    Returns
    -------
    ndarray
        Pressure loss [Pa] through each edge at each time (t x e)
        Or pressure loss derivative [Pa·s/kg] if mode = GRADIENT

    References
    ----------
    [Oppelt2016] Oppelt, T., et al. (2016). Applied Thermal Engineering, 102, 336-345.
    [White2016] White, F.M. (2016). Fluid Mechanics (8th ed.). McGraw-Hill

    Notes
    -----
    The Darcy-Weisbach equation is the fundamental equation for pressure loss
    in pipe flow and is valid for all flow regimes (laminar, transition, turbulent).

    The mode parameter allows this function to be used both in:
    1. Direct pressure loss calculation for network branches
    2. Iterative network solving using the gradient method (Todini & Pilati, 1987)
    """

    mass_flow_rate_kgs = np.array(mass_flow_rate_kgs)
    pipe_length_m = np.array(pipe_length_m)
    pipe_diameter_m = np.array(pipe_diameter_m)
    reynolds = calc_reynolds(mass_flow_rate_kgs, t_edge__k, pipe_diameter_m)

    darcy = calc_darcy(pipe_diameter_m, reynolds, ROUGHNESS)

    if mode == PressureLossMode.GRADIENT:
        # Partial derivative ∂P/∂m for Hardy Cross method
        pressure_loss_edge_Pa = darcy * 16 * mass_flow_rate_kgs * pipe_length_m / (
                np.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
    else:
        # [STANDARD: ISO 5167] Darcy-Weisbach equation for direct pressure loss
        pressure_loss_edge_Pa = darcy * 8 * mass_flow_rate_kgs ** 2 * pipe_length_m / (
                np.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
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
        Reynolds number [-] for each edge at time t (t x e)
    pipe_roughness_m : float
        Absolute pipe roughness [m]
        Typical value: 0.02 mm (2×10⁻⁵ m) for steel pipe
        Range: 10⁻⁶ - 0.05 m (EN 13941)

    Returns
    -------
    ndarray
        Darcy friction factor [-] for each edge at time t (t x e)

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
    negligible flow conditions.
    """
    # Ensure pipe_diameter_m is 1-D array for broadcasting
    pipe_diameter_m = np.asarray(pipe_diameter_m, dtype=np.float64).flatten()
    reynolds = np.asarray(reynolds, dtype=np.float64)

    # Define conditions for each flow regime
    cond_no_flow = reynolds <= 1
    cond_laminar = (reynolds > 1) & (reynolds <= 2300)
    cond_transition = (reynolds > 2300) & (reynolds <= 5000)
    cond_turbulent = reynolds > 5000

    # Calculate Darcy for laminar regime
    # [STANDARD: ISO 5167] Laminar flow: f = 64/Re
    darcy_laminar = 64 / np.where(reynolds > 0, reynolds, 1)  # Avoid division by zero

    # Calculate Darcy for transition regime
    # [STANDARD: Transition regime] Blasius equation for smooth pipes
    # Reference: Moody Diagram (Incropera et al., 2007)
    darcy_transition = 0.316 * np.where(reynolds > 0, reynolds, 1) ** -0.25

    # Calculate Darcy for turbulent regime
    # [STANDARD: ISO 5167, EN 13941] Swamee-Jain equation
    # Explicit Colebrook-White approximation
    # Valid: Re ∈ [5000, 10⁸], ε/D ∈ [10⁻⁶, 0.05]
    log_arg = pipe_roughness_m / (3.7 * pipe_diameter_m) + 5.74 / np.where(reynolds > 0, reynolds, 1) ** 0.9

    # Validate logarithm argument for turbulent flow
    invalid_turbulent = cond_turbulent & (~np.isfinite(log_arg) | (log_arg <= 0))
    if np.any(invalid_turbulent):
        # Find first invalid case for error reporting
        idx = np.unravel_index(np.argmax(invalid_turbulent), invalid_turbulent.shape)
        raise ValueError(
            f"Invalid argument for logarithm in Swamee-Jain friction factor calculation!\n"
            f"Logarithm argument: {log_arg[idx]}\n"
            f"Pipe roughness: {pipe_roughness_m:.6e} m\n"
            f"Pipe diameter: {pipe_diameter_m[idx[-1]] if pipe_diameter_m.ndim > 0 else pipe_diameter_m:.6f} m\n"
            f"Reynolds number: {reynolds[idx]:.2f}\n\n"
            f"For valid Swamee-Jain calculation:\n"
            f"- Pipe roughness must be > 0 (typical: 1e-6 to 0.05 m)\n"
            f"- Pipe diameter must be > 0\n"
            f"- Reynolds number should be 5000 - 1e8\n"
            f"- Values must be finite (not NaN or inf)\n\n"
            f"**Check the pipe properties and flow conditions."
        )

    darcy_turbulent = 1.325 * np.log(log_arg) ** (-2)

    # Apply conditions to select appropriate Darcy value
    conditions = [cond_no_flow, cond_laminar, cond_transition, cond_turbulent]
    choices = [
        0,                  # No flow
        darcy_laminar,      # Laminar regime
        darcy_transition,   # Transition regime
        darcy_turbulent     # Turbulent regime
    ]

    darcy = np.select(conditions, choices, default=0)

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
        - Mass flow rate: ≥ 0 kg/s
    """

    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature__k)  # m2/s
    pipe_diameter_m = np.asarray(pipe_diameter_m, dtype=np.float64)

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
    denominator = np.pi * kinematic_viscosity_m2s * pipe_diameter_m

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

    return reynolds
