"""
Local booster calculations for district heating when network temperature is insufficient.

Applies to:
- Space heating when network temp < space heating requirement
- DHW when network temp < DHW requirement (typically 60°C)

Works with:
- Variable Temperature (VT) mode: network temp = max(building requirements), boosters rarely needed
- Constant Temperature (CT) mode: network temp = fixed, boosters commonly needed
"""

import numpy as np

__author__ = "Reynold Mok, Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Reynold Mok", "Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

MIN_APPROACH_TEMP_K = 5  # Minimum temperature difference for heat exchanger
MIN_TEMP_RISE_FOR_FRACTION_K = 1  # Minimum temperature rise for stable heat distribution fraction calculation
MIN_TEMP_DIFF_FOR_MASS_FLOW_K = 0.1  # Minimum temperature difference to prevent division by zero in mass flow calculation


def calc_dh_heating_with_booster_tracking(
    Q_demand_W,          # Heating demand (space heating or DHW) [W]
    T_DH_supply_C,       # DH supply temp [°C]
    T_target_C,          # Target temp (space heating or DHW) [°C]
    T_return_C,          # Return temp from building [°C]
    load_type='dhw'      # 'space_heating' or 'dhw' (for logging)
):
    """
    Calculate DH heating + booster tracking when network temp is insufficient.

    Universal function for both space heating and DHW loads.

    When network temperature is lower than required temperature:
    - DH pre-heats the load from return temp to (network temp - approach temp)
    - Local booster tops up from DH outlet to target temperature

    :param Q_demand_W: Total heating demand [W] (hourly array)
    :param T_DH_supply_C: DH supply temperature [°C] (scalar or hourly array)
    :param T_target_C: Target supply temperature [°C] (scalar or hourly array)
    :param T_return_C: Return temperature from building [°C] (hourly array)
    :param load_type: 'space_heating' or 'dhw' (for output naming)

    :return: tuple (Q_dh_W, T_dh_return_C, mcp_dh_kWK, Q_booster_W, A_hex_m2, booster_active)

        For thermal network (DH side):
        - Q_dh_W: Heat from DH [W]
        - T_dh_return_C: DH return temperature [°C]
        - mcp_dh_kWK: DH heat capacity flow rate [kW/K]
        - A_hex_m2: HEX area [m²]

        For cost/emissions tracking:
        - Q_booster_W: Booster heat output needed [W]
        - booster_active: Boolean array indicating when booster operates
    """

    # Ensure Q_demand_W is array first (determines shape for broadcasting)
    Q_demand_W = np.atleast_1d(Q_demand_W)

    # Broadcast all temperature inputs to match Q_demand_W shape
    # .copy() needed because np.broadcast_to returns read-only views
    T_DH_supply_C = np.broadcast_to(np.atleast_1d(T_DH_supply_C), Q_demand_W.shape).copy()
    T_target_C = np.broadcast_to(np.atleast_1d(T_target_C), Q_demand_W.shape).copy()
    T_return_C = np.broadcast_to(np.atleast_1d(T_return_C), Q_demand_W.shape).copy()

    # Initialize outputs
    Q_dh_W = np.zeros_like(Q_demand_W, dtype=float)
    Q_booster_W = np.zeros_like(Q_demand_W, dtype=float)
    booster_active = np.zeros_like(Q_demand_W, dtype=bool)

    # Calculate max temperature achievable with DH (with approach temp)
    T_dh_preheat_max_C = T_DH_supply_C - MIN_APPROACH_TEMP_K

    # Determine when booster is needed
    booster_needed = (T_dh_preheat_max_C < T_target_C) & (Q_demand_W > 0)
    dh_sufficient = (T_dh_preheat_max_C >= T_target_C) & (Q_demand_W > 0)

    # Case A: DH temperature sufficient (no booster needed)
    if dh_sufficient.any():
        Q_dh_W[dh_sufficient] = Q_demand_W[dh_sufficient]
        Q_booster_W[dh_sufficient] = 0
        booster_active[dh_sufficient] = False

    # Case B: DH pre-heats, booster tops up
    if booster_needed.any():
        # DH contributes heating from return temp to preheat temp
        T_preheat_subset = T_dh_preheat_max_C[booster_needed]
        T_target_subset = T_target_C[booster_needed]
        T_return_subset = T_return_C[booster_needed]

        temp_rise_dh = np.maximum(0, T_preheat_subset - T_return_subset)
        # Use minimum threshold for numerical stability in fraction calculation
        temp_rise_total = np.maximum(MIN_TEMP_RISE_FOR_FRACTION_K, T_target_subset - T_return_subset)

        # Fraction of heat from DH vs booster (based on temperature rise)
        fraction_dh = temp_rise_dh / temp_rise_total

        Q_dh_W[booster_needed] = Q_demand_W[booster_needed] * fraction_dh
        Q_booster_W[booster_needed] = Q_demand_W[booster_needed] - Q_dh_W[booster_needed]
        booster_active[booster_needed] = True

    # ========================================================================
    # Calculate DH-side parameters (what thermal network needs)
    # ========================================================================

    # Building-side outlet temperature (what temperature DH heats the water to)
    T_building_outlet_C = np.where(
        booster_needed,
        T_dh_preheat_max_C,  # With booster: DH heats to preheat temp, booster adds rest
        np.where(
            dh_sufficient,
            T_target_C,  # No booster: DH heats to target temp
            T_return_C   # No demand: no temperature rise
        )
    )

    # Building-side temperature rise
    delta_T_building = np.maximum(0, T_building_outlet_C - T_return_C)

    # DH-side temperature drop (assume counter-flow HEX with ~90% effectiveness)
    # For counter-flow HEX, if building side rises by dT, DH side drops by approximately dT
    # (assuming similar heat capacity flow rates)
    delta_T_dh_side = delta_T_building

    # DH return temperature
    T_dh_return_C = np.where(
        Q_dh_W > 0,
        T_DH_supply_C - delta_T_dh_side,
        T_DH_supply_C  # No demand: return = supply
    )

    # Ensure DH return respects approach temperature constraint
    # DH return must be >= building inlet + approach temp
    T_dh_return_min_C = T_return_C + MIN_APPROACH_TEMP_K
    T_dh_return_C = np.maximum(T_dh_return_C, T_dh_return_min_C)

    # Recalculate actual DH temperature drop
    # Use minimum threshold to prevent division by zero in mass flow calculation below
    delta_T_dh_actual = np.maximum(MIN_TEMP_DIFF_FOR_MASS_FLOW_K, T_DH_supply_C - T_dh_return_C)

    # DH mass flow rate: Q = mcp * dT => mcp = Q / dT
    mcp_dh_kWK = np.where(Q_dh_W > 0, Q_dh_W / (1000 * delta_T_dh_actual), 0)

    # HEX area calculation (simplified, using peak load)
    U_hex = 2000  # W/m²K (typical for plate HEX)
    Q_peak = np.max(Q_dh_W)

    if Q_peak > 0:
        # Calculate LMTD at peak condition
        idx_peak = np.argmax(Q_dh_W)
        T_dh_in = T_DH_supply_C[idx_peak]
        T_dh_out = T_dh_return_C[idx_peak]
        T_load_in = T_return_C[idx_peak]
        T_load_out = min(T_dh_preheat_max_C[idx_peak], T_target_C[idx_peak])

        # LMTD for counter-flow HEX
        dT1 = T_dh_in - T_load_out
        dT2 = T_dh_out - T_load_in
        if dT1 > 0.1 and dT2 > 0.1:
            # When dT1 ≈ dT2 (parallel temperature profiles), LMTD ≈ dT1
            if abs(dT1 - dT2) < 0.01:
                LMTD = dT1  # Avoid log(1) = 0 division
            else:
                LMTD = (dT1 - dT2) / np.log(dT1 / dT2)
            A_hex_m2 = Q_peak / (U_hex * LMTD)
        else:
            A_hex_m2 = 0
    else:
        A_hex_m2 = 0

    return (
        Q_dh_W,          # DH contribution to load
        T_dh_return_C,   # DH return temp
        mcp_dh_kWK,      # DH mass flow (kW/K)
        Q_booster_W,     # Booster heat output
        A_hex_m2,        # HEX area
        booster_active   # Booster activity flag
    )
