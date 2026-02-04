import numpy as np
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3

from .hydraulics import calc_reynolds, calc_darcy
from .fluid_properties import calc_kinematic_viscosity, calc_thermal_conductivity
from cea.technologies.constants import ROUGHNESS


def calc_nusselt(mass_flow_rate_kgs, temperature_K, pipe_diameter_m, network_type):
    """
    Calculate Nusselt number for internal pipe flow using regime-appropriate correlations.

    Standards Compliance
    --------------------
    - Laminar flow (Nu = 3.66): Analytical solution
    - VDI Heat Atlas G1: Turbulent flow correlations
    - Dittus-Boelter equation: Standard turbulent correlation

    Correlations by Flow Regime
    ----------------------------
    Laminar (Re ≤ 2300):
        Nu = 3.66  [fully developed, constant wall temperature]

    Transition (2300 < Re ≤ 10000):
        Nu = (f/8)(Re-1000)Pr / [1 + 12.7√(f/8)(Pr^0.67 - 1)]
        [Gnielinski correlation for transition regime]

    Turbulent (Re > 10000):
        Nu = 0.023 × Re^0.8 × Pr^n  [Dittus-Boelter]
        where n = 0.3 for heating (DH networks)
              n = 0.4 for cooling (DC networks)

    Valid Ranges (Turbulent)
    -------------------------
    - 0.6 ≤ Pr ≤ 160
    - Re ≥ 10,000
    - L/D ≥ 10 (fully developed)

    Parameters
    ----------
    mass_flow_rate_kgs : ndarray
        Mass flow rate [kg/s] in each edge at time t (t x e)
    temperature_K : list or ndarray
        Fluid temperature [K] in each edge at time t (t x e)
    pipe_diameter_m : ndarray
        Pipe diameter [m] for each edge (e x 1)
    network_type : str
        Network type:
        - 'DH': District heating (hot fluid cooled by ground)
        - 'DC': District cooling (cold fluid heated by ground)

    Returns
    -------
    ndarray
        Nusselt number [-] for each flow condition

    Notes
    -----
    The Nusselt number represents the ratio of convective to conductive heat
    transfer across the fluid boundary layer:
        Nu = h × D / k_thermal

    For district heating (DH), the pipe fluid is hotter than ground, so heat
    flows outward (cooling case, n=0.3). For district cooling (DC), the pipe
    fluid is colder than ground, so heat flows inward (heating case, n=0.4).

    The different exponents in the Dittus-Boelter equation account for the
    asymmetry in velocity and temperature profiles between heating and cooling.

    References
    ----------
    [Incropera2007] Section 8.4: Internal flow heat transfer correlations
    [VDI] VDI Heat Atlas, Section G1: Heat transfer in pipe flow
    """

    # calculate variable values necessary for nusselt number evaluation
    reynolds = calc_reynolds(mass_flow_rate_kgs, temperature_K, pipe_diameter_m)
    prandtl = calc_prandtl(temperature_K)
    darcy = calc_darcy(pipe_diameter_m, reynolds, ROUGHNESS)

    # Vectorized calculation using np.select for different flow regimes
    # Define conditions for each regime
    cond_no_flow = reynolds <= 1
    cond_laminar = (reynolds > 1) & (reynolds <= 2300)
    cond_transition = (reynolds > 2300) & (reynolds <= 10000)
    cond_turbulent = reynolds > 10000

    # Calculate Nusselt for transition regime (Gnielinski correlation)
    # [STANDARD: VDI Heat Atlas] Gnielinski correlation for transition regime
    nusselt_transition = darcy / 8 * (reynolds - 1000) * prandtl / (
            1 + 12.7 * (darcy / 8) ** 0.5 * (prandtl ** 0.67 - 1))

    # Calculate Nusselt for turbulent regime (Dittus-Boelter equation)
    # [STANDARD: VDI Heat Atlas, Incropera] Dittus-Boelter equation for turbulent flow
    if network_type == 'DH':
        # District heating: warm fluid, ground cooling (n=0.3)
        nusselt_turbulent = 0.023 * reynolds ** 0.8 * prandtl ** 0.3
    else:
        # District cooling: cold fluid, ground heating (n=0.4)
        nusselt_turbulent = 0.023 * reynolds ** 0.8 * prandtl ** 0.4

    # Apply conditions to select appropriate Nusselt value
    conditions = [cond_no_flow, cond_laminar, cond_transition, cond_turbulent]
    choices = [
        0,                      # No flow
        3.66,                   # [STANDARD: ISO 12241] Laminar flow (fully developed, constant T_wall)
        nusselt_transition,     # Transition regime
        nusselt_turbulent       # Turbulent regime
    ]

    nusselt = np.select(conditions, choices, default=0)

    return nusselt


def calc_prandtl(temperature__k):
    """
    Calculate Prandtl number for water as function of temperature.

    Formula
    -------
    Pr = ν × ρ × cp / k_thermal = μ × cp / k_thermal  [-]

    where:
        - ν: kinematic viscosity [m²/s]
        - ρ: density [kg/m³]
        - cp: specific heat capacity [J/(kg·K)]
        - k_thermal: thermal conductivity [W/(m·K)]
        - μ: dynamic viscosity [Pa·s]

    Parameters
    ----------
    temperature__k : list or ndarray
        Water temperature [K] for each condition (t x e)

    Returns
    -------
    ndarray
        Prandtl number [-] for each temperature condition

    Notes
    -----
    The Prandtl number represents the ratio of momentum diffusivity
    (kinematic viscosity) to thermal diffusivity:
        Pr = ν / α = (μ/ρ) / (k/ρcp)

    For water at typical district heating temperatures:
        - 300 K (27°C): Pr ≈ 6
        - 350 K (77°C): Pr ≈ 2
        - 400 K (127°C): Pr ≈ 1.5

    Lower Prandtl numbers at higher temperatures indicate that thermal
    diffusion becomes relatively more important compared to momentum diffusion.

    Valid Range
    -----------
    273 K ≤ T ≤ 413 K (0-140°C for liquid water)

    References
    ----------
    [Incropera2007] Fundamentals of Heat and Mass Transfer, Chapter 8
    """

    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature__k)  # m2/s
    thermal_conductivity = calc_thermal_conductivity(temperature__k)  # W/(m*K)

    return np.nan_to_num(
        kinematic_viscosity_m2s * P_WATER_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK / thermal_conductivity)
