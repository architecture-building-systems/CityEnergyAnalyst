"""
Unit tests for thermal network physics.

Make sure thermodynamics and fluid dynamics functions used in the thermal network calculations are behaving as intended.
"""

import pytest
import numpy as np

from cea.technologies.thermal_network.physics import (
    calc_temperature_out_per_pipe,
    calc_pressure_loss_pipe, calc_darcy, calc_reynolds, PressureLossMode,
    calc_nusselt, calc_prandtl,
    calc_kinematic_viscosity, calc_thermal_conductivity,
)
from cea.constants import P_WATER_KGPERM3, HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.technologies.constants import ROUGHNESS


# Representative pipe states covering every flow-regime branch in the code,
# as well as the diameter, temperature, and network-type ranges found in the database.
#
# Regime states — T = 333.15 K (60 °C), D = 0.1 m, L = 100 m
# At these conditions: ν ≈ 4.76×10⁻⁷ m²/s, Re ≈ m × 26 800
#
# State            m [kg/s]   Re (approx)   Regime
# ─────────────────────────────────────────────────────────────────────────────
# no_flow          0          0             Re ≤ 1         → f = 0, Nu = 0
# laminar          0.019      509           Re ≤ 2300      → f = 64/Re, Nu = 3.66
# transitional     0.130      3 485         2300 < Re ≤ 5000  → Blasius / Gnielinski
# high_re          0.260      6 970         5000 < Re ≤ 10000 → Swamee-Jain / Gnielinski
# fully_turbulent  0.560     15 008         Re > 10000     → Swamee-Jain / Dittus-Boelter
#
# Parameter-variation states — all fully turbulent (Re > 10 000)
#
# State            D [m]   T [K]   m [kg/s]  Re (approx)   Network  Notes
# ─────────────────────────────────────────────────────────────────────────────
# small_pipe_dh    0.020  333.15   0.112     15 008         DH   20 mm branch; ν same as above
# large_pipe_dh    0.500  333.15   5.000     26 791         DH   500 mm main; ν same as above
# hot_supply_dh    0.100  368.15   0.360     15 016         DH   95 °C supply; ν ≈ 3.06×10⁻⁷ m²/s
# cold_supply_dc   0.100  283.15   1.540     15 047         DC   10 °C cold supply; ν ≈ 1.30×10⁻⁶ m²/s

PIPE_STATES = {
    "no_flow": {
        "mass_flow_rate_kgs": np.array([[0.0]]),
        "temperature_K": np.array([[333.15]]),
        "pipe_diameter_m": np.array([0.1]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 363.15,
        "k": 0.1,
        "t_ground": 283.15,
    },
    "laminar": {
        "mass_flow_rate_kgs": np.array([[0.019]]),
        "temperature_K": np.array([[333.15]]),
        "pipe_diameter_m": np.array([0.1]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 363.15,
        "k": 0.1,
        "t_ground": 283.15,
    },
    "transitional": {
        "mass_flow_rate_kgs": np.array([[0.130]]),
        "temperature_K": np.array([[333.15]]),
        "pipe_diameter_m": np.array([0.1]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 363.15,
        "k": 0.1,
        "t_ground": 283.15,
    },
    "high_re": {
        "mass_flow_rate_kgs": np.array([[0.260]]),
        "temperature_K": np.array([[333.15]]),
        "pipe_diameter_m": np.array([0.1]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 363.15,
        "k": 0.1,
        "t_ground": 283.15,
    },
    "fully_turbulent": {
        "mass_flow_rate_kgs": np.array([[0.560]]),
        "temperature_K": np.array([[333.15]]),
        "pipe_diameter_m": np.array([0.1]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 363.15,
        "k": 0.1,
        "t_ground": 283.15,
    },
    # ---- diameter variation ------------------------------------------------
    "small_pipe_dh": {
        # 20 mm residential branch at 60 °C — highest Re per kg/s due to small D
        "mass_flow_rate_kgs": np.array([[0.112]]),
        "temperature_K": np.array([[333.15]]),
        "pipe_diameter_m": np.array([0.020]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 363.15,
        "k": 0.05,
        "t_ground": 283.15,
    },
    "large_pipe_dh": {
        # 500 mm transmission main at 60 °C — lowest Re per kg/s due to large D
        "mass_flow_rate_kgs": np.array([[5.000]]),
        "temperature_K": np.array([[333.15]]),
        "pipe_diameter_m": np.array([0.500]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 363.15,
        "k": 0.2,
        "t_ground": 283.15,
    },
    # ---- temperature variation ---------------------------------------------
    "hot_supply_dh": {
        # 100 mm pipe at 95 °C — near upper temperature limit; ν ≈ 3.06×10⁻⁷ m²/s
        "mass_flow_rate_kgs": np.array([[0.360]]),
        "temperature_K": np.array([[368.15]]),
        "pipe_diameter_m": np.array([0.100]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DH",
        "t_in": 368.15,
        "k": 0.1,
        "t_ground": 283.15,
    },
    # ---- network-type variation (DC) --------------------------------------
    "cold_supply_dc": {
        # 100 mm pipe at 10 °C — district cooling cold supply; ν ≈ 1.30×10⁻⁶ m²/s
        # needs ~3× more mass flow to reach same Re as at 60 °C
        "mass_flow_rate_kgs": np.array([[1.540]]),
        "temperature_K": np.array([[283.15]]),
        "pipe_diameter_m": np.array([0.100]),
        "pipe_length_m": np.array([100.0]),
        "network_type": "DC",
        "t_in": 278.15,
        "k": 0.1,
        "t_ground": 293.15,
    },
}


class TestThermalNetworkPhysics:
    """Thermal network physics tests"""

    @pytest.fixture(params=list(PIPE_STATES.keys()))
    def pipe_state(self, request):
        """Parametrized fixture: one state per flow regime.

        Covers no-flow, laminar, transitional, high-Re Gnielinski, and fully
        turbulent conditions for a single pipe at T = 333.15 K, D = 0.1 m.
        """
        return PIPE_STATES[request.param]

    # ------------------------------------------------------------------ #
    #  Fluid properties                                                    #
    # ------------------------------------------------------------------ #

    def test_calc_kinematic_viscosity_tabulated_values(self):
        """Viscosity should reproduce tabulated Engineering Toolbox values within stated ±2% accuracy."""
        # True physical values from docstring
        assert np.isclose(calc_kinematic_viscosity(273.0), 1.79e-6, rtol=0.03)
        assert np.isclose(calc_kinematic_viscosity(293.0), 1.00e-6, rtol=0.03)
        assert np.isclose(calc_kinematic_viscosity(353.0), 0.36e-6, rtol=0.03)
        assert np.isclose(calc_kinematic_viscosity(373.0), 0.29e-6, rtol=0.03)

    def test_calc_kinematic_viscosity_decreases_with_temperature(self):
        """Viscosity decreases monotonically with temperature for liquid water."""
        T = np.linspace(273, 413, 50)
        nu = calc_kinematic_viscosity(T)
        assert np.all(np.diff(nu) < 0), "Kinematic viscosity should decrease as temperature rises"

    def test_calc_thermal_conductivity_tabulated_values(self):
        """Thermal conductivity should match IAPWS regression values from docstring."""
        assert np.isclose(calc_thermal_conductivity(273.0), 0.556, rtol=0.005)
        assert np.isclose(calc_thermal_conductivity(293.0), 0.597, rtol=0.005)
        assert np.isclose(calc_thermal_conductivity(353.0), 0.667, rtol=0.005)
        assert np.isclose(calc_thermal_conductivity(373.0), 0.672, rtol=0.005)

    def test_calc_prandtl_range(self):
        """Prandtl number should be in the expected physical range for liquid water."""
        pr_300 = calc_prandtl(np.array([[300.0]])).item()
        pr_350 = calc_prandtl(np.array([[350.0]])).item()
        pr_400 = calc_prandtl(np.array([[400.0]])).item()

        assert 5.0 < pr_300 < 8.0, f"Pr(300 K) = {pr_300:.2f}, expected ≈ 6"
        assert 1.5 < pr_350 < 3.5, f"Pr(350 K) = {pr_350:.2f}, expected ≈ 2"
        assert 1.0 < pr_400 < 2.5, f"Pr(400 K) = {pr_400:.2f}, expected ≈ 1.5"

    def test_calc_prandtl_decreases_with_temperature(self):
        """Prandtl number decreases with temperature in the district heating range."""
        pr_300 = calc_prandtl(np.array([[300.0]])).item()
        pr_350 = calc_prandtl(np.array([[350.0]])).item()
        pr_400 = calc_prandtl(np.array([[400.0]])).item()
        assert pr_300 > pr_350 > pr_400, "Prandtl number should decrease with temperature"

    # ------------------------------------------------------------------ #
    #  Reynolds number                                                     #
    # ------------------------------------------------------------------ #

    def test_calc_reynolds_formula(self, pipe_state):
        """Reynolds number must equal Re = 4ṁ / (ρ π ν D) for every pipe state."""
        m = pipe_state["mass_flow_rate_kgs"]
        T = pipe_state["temperature_K"]
        D = pipe_state["pipe_diameter_m"]

        nu = calc_kinematic_viscosity(T)
        expected_re = 4 * np.abs(m) / (P_WATER_KGPERM3 * np.pi * nu * D)

        np.testing.assert_allclose(calc_reynolds(m, T, D), expected_re, rtol=1e-6)

    def test_calc_reynolds_regime(self):
        """Each pipe state must fall inside its designated flow regime."""
        # (lower_exclusive, upper_inclusive) — None means unbounded
        regime_bounds = {
            "no_flow":          (None,  1),
            "laminar":          (1,     2300),
            "transitional":     (2300,  5000),
            "high_re":          (5000,  10000),
            "fully_turbulent":  (10000, None),
            # parameter-variation states — all fully turbulent
            "small_pipe_dh":    (10000, None),
            "large_pipe_dh":    (10000, None),
            "hot_supply_dh":    (10000, None),
            "cold_supply_dc":   (10000, None),
        }
        for name, state in PIPE_STATES.items():
            re = float(np.ravel(calc_reynolds(
                state["mass_flow_rate_kgs"],
                state["temperature_K"],
                state["pipe_diameter_m"],
            ))[0])
            lo, hi = regime_bounds[name]
            if lo is not None:
                assert re > lo, f"State '{name}': Re = {re:.1f} should be > {lo}"
            if hi is not None:
                assert re <= hi, f"State '{name}': Re = {re:.1f} should be ≤ {hi}"

    def test_calc_reynolds_zero_for_no_flow(self):
        """Zero mass flow rate must yield Re = 0."""
        state = PIPE_STATES["no_flow"]
        re = calc_reynolds(
            state["mass_flow_rate_kgs"],
            state["temperature_K"],
            state["pipe_diameter_m"],
        )
        assert np.all(re == 0)

    # ------------------------------------------------------------------ #
    #  Darcy friction factor                                               #
    # ------------------------------------------------------------------ #

    def test_calc_darcy_no_flow(self):
        """Friction factor is zero when Re ≤ 1 (no flow)."""
        state = PIPE_STATES["no_flow"]
        re = calc_reynolds(state["mass_flow_rate_kgs"], state["temperature_K"], state["pipe_diameter_m"])
        f = calc_darcy(state["pipe_diameter_m"], re, ROUGHNESS)
        assert np.all(f == 0)

    def test_calc_darcy_laminar_equals_64_over_re(self):
        """In laminar flow the Darcy friction factor equals 64/Re (Hagen-Poiseuille)."""
        state = PIPE_STATES["laminar"]
        re = calc_reynolds(state["mass_flow_rate_kgs"], state["temperature_K"], state["pipe_diameter_m"])
        f = calc_darcy(state["pipe_diameter_m"], re, ROUGHNESS)
        np.testing.assert_allclose(f, 64 / re, rtol=1e-6)

    def test_calc_darcy_transition_blasius(self):
        """In the transition regime (2300 < Re ≤ 5000) the Blasius equation applies: f = 0.316 Re^-0.25."""
        state = PIPE_STATES["transitional"]
        re = calc_reynolds(state["mass_flow_rate_kgs"], state["temperature_K"], state["pipe_diameter_m"])
        f = calc_darcy(state["pipe_diameter_m"], re, ROUGHNESS)
        np.testing.assert_allclose(f, 0.316 * re ** -0.25, rtol=1e-6)

    def test_calc_darcy_turbulent_swamee_jain(self):
        """In turbulent flow (Re > 5000) the Swamee-Jain approximation applies."""
        state = PIPE_STATES["fully_turbulent"]
        D = state["pipe_diameter_m"]
        re = calc_reynolds(state["mass_flow_rate_kgs"], state["temperature_K"], D)
        f = calc_darcy(D, re, ROUGHNESS)
        expected_f = 1.325 * np.log(ROUGHNESS / (3.7 * D) + 5.74 / re ** 0.9) ** (-2)
        np.testing.assert_allclose(f, expected_f, rtol=1e-6)

    def test_calc_darcy_non_negative(self, pipe_state):
        """Friction factor must be non-negative for all flow conditions."""
        re = calc_reynolds(
            pipe_state["mass_flow_rate_kgs"],
            pipe_state["temperature_K"],
            pipe_state["pipe_diameter_m"],
        )
        f = calc_darcy(pipe_state["pipe_diameter_m"], re, ROUGHNESS)
        assert np.all(f >= 0), f"Negative Darcy friction factor: {f}"

    # ------------------------------------------------------------------ #
    #  Nusselt number                                                      #
    # ------------------------------------------------------------------ #

    def test_calc_nusselt_no_flow(self):
        """With no flow there is no convective heat transfer, so Nu = 0."""
        state = PIPE_STATES["no_flow"]
        nu = calc_nusselt(
            state["mass_flow_rate_kgs"], state["temperature_K"],
            state["pipe_diameter_m"], state["network_type"],
        )
        assert np.all(nu == 0)

    def test_calc_nusselt_laminar_constant(self):
        """Fully developed laminar pipe flow gives Nu = 3.66 (constant wall temperature, Incropera 8.53)."""
        state = PIPE_STATES["laminar"]
        nu = calc_nusselt(
            state["mass_flow_rate_kgs"], state["temperature_K"],
            state["pipe_diameter_m"], state["network_type"],
        )
        np.testing.assert_allclose(nu, 3.66, rtol=1e-6)

    def test_calc_nusselt_transition_gnielinski(self):
        """In the Nusselt transition regime (2300 < Re ≤ 10000) the Gnielinski correlation is used."""
        state = PIPE_STATES["high_re"]
        D = state["pipe_diameter_m"]
        re = calc_reynolds(state["mass_flow_rate_kgs"], state["temperature_K"], D)
        pr = calc_prandtl(state["temperature_K"])
        f = calc_darcy(D, re, ROUGHNESS)
        expected_nu = f / 8 * (re - 1000) * pr / (1 + 12.7 * (f / 8) ** 0.5 * (pr ** 0.67 - 1))

        nu = calc_nusselt(
            state["mass_flow_rate_kgs"], state["temperature_K"],
            D, state["network_type"],
        )
        np.testing.assert_allclose(nu, expected_nu, rtol=1e-6)

    def test_calc_nusselt_turbulent_dittus_boelter(self):
        """In fully turbulent flow (Re > 10000) the Dittus-Boelter equation is used with n = 0.3 (DH) or 0.4 (DC)."""
        state = PIPE_STATES["fully_turbulent"]
        D = state["pipe_diameter_m"]
        re = calc_reynolds(state["mass_flow_rate_kgs"], state["temperature_K"], D)
        pr = calc_prandtl(state["temperature_K"])

        nu_dh = calc_nusselt(state["mass_flow_rate_kgs"], state["temperature_K"], D, "DH")
        nu_dc = calc_nusselt(state["mass_flow_rate_kgs"], state["temperature_K"], D, "DC")

        np.testing.assert_allclose(nu_dh, 0.023 * re ** 0.8 * pr ** 0.3, rtol=1e-6)
        np.testing.assert_allclose(nu_dc, 0.023 * re ** 0.8 * pr ** 0.4, rtol=1e-6)

    def test_calc_nusselt_dc_gt_dh_in_turbulent_regime(self):
        """For water (Pr > 1), the DC cooling exponent (n=0.4) gives higher Nu than DH heating (n=0.3)."""
        state = PIPE_STATES["fully_turbulent"]
        nu_dh = calc_nusselt(
            state["mass_flow_rate_kgs"], state["temperature_K"],
            state["pipe_diameter_m"], "DH",
        )
        nu_dc = calc_nusselt(
            state["mass_flow_rate_kgs"], state["temperature_K"],
            state["pipe_diameter_m"], "DC",
        )
        assert np.all(nu_dc > nu_dh), "For Pr > 1, n=0.4 (DC) should give higher Nu than n=0.3 (DH)"

    def test_calc_nusselt_invalid_network_type(self):
        """An unrecognised network_type must raise a ValueError."""
        state = PIPE_STATES["laminar"]
        with pytest.raises(ValueError, match="network_type"):
            calc_nusselt(
                state["mass_flow_rate_kgs"], state["temperature_K"],
                state["pipe_diameter_m"], "XX",
            )

    def test_calc_nusselt_non_negative(self, pipe_state):
        """Nusselt number must be non-negative for all flow conditions."""
        nu = calc_nusselt(
            pipe_state["mass_flow_rate_kgs"], pipe_state["temperature_K"],
            pipe_state["pipe_diameter_m"], pipe_state["network_type"],
        )
        assert np.all(nu >= 0)

    # ------------------------------------------------------------------ #
    #  Pressure loss                                                       #
    # ------------------------------------------------------------------ #

    def test_calc_pressure_loss_non_negative(self, pipe_state):
        """Pressure loss must be non-negative for all flow conditions."""
        dp = calc_pressure_loss_pipe(
            pipe_state["pipe_diameter_m"], pipe_state["pipe_length_m"],
            pipe_state["mass_flow_rate_kgs"], pipe_state["temperature_K"],
            PressureLossMode.DIRECT,
        )
        assert np.all(dp >= 0)

    def test_calc_pressure_loss_linear_in_pipe_length(self):
        """Doubling pipe length must double the pressure loss (Darcy-Weisbach is linear in L)."""
        state = PIPE_STATES["fully_turbulent"]
        dp_100 = calc_pressure_loss_pipe(
            state["pipe_diameter_m"], np.array([100.0]),
            state["mass_flow_rate_kgs"], state["temperature_K"],
            PressureLossMode.DIRECT,
        )
        dp_200 = calc_pressure_loss_pipe(
            state["pipe_diameter_m"], np.array([200.0]),
            state["mass_flow_rate_kgs"], state["temperature_K"],
            PressureLossMode.DIRECT,
        )
        np.testing.assert_allclose(dp_200, 2 * dp_100, rtol=1e-6)

    def test_calc_pressure_loss_gradient_equals_2_direct_over_m(self):
        """GRADIENT mode must equal 2 × DIRECT / ṁ (∂ΔP/∂ṁ from Darcy-Weisbach at constant f)."""
        state = PIPE_STATES["fully_turbulent"]
        m = state["mass_flow_rate_kgs"]
        dp_direct = calc_pressure_loss_pipe(
            state["pipe_diameter_m"], state["pipe_length_m"],
            m, state["temperature_K"],
            PressureLossMode.DIRECT,
        )
        dp_gradient = calc_pressure_loss_pipe(
            state["pipe_diameter_m"], state["pipe_length_m"],
            m, state["temperature_K"],
            PressureLossMode.GRADIENT,
        )
        np.testing.assert_allclose(dp_gradient, 2 * dp_direct / m, rtol=1e-6)

    # ------------------------------------------------------------------ #
    #  Thermal loss — outlet temperature                                   #
    # ------------------------------------------------------------------ #

    def test_calc_temperature_out_no_ground_gradient(self):
        """When T_in equals T_ground there is no driving force; T_out must equal T_in."""
        T = 363.15  # K — arbitrary value inside valid range
        t_out = calc_temperature_out_per_pipe(t_in=T, m=0.5, k=0.2, t_ground=T)
        assert np.isclose(t_out, T)

    def test_calc_temperature_out_energy_balance(self):
        """Outlet temperature must satisfy the energy balance m·cp·ΔT = −k·(T_avg − T_ground)."""
        t_in = 363.15   # K  (90 °C district heating supply)
        m = 0.5         # kg/s
        k = 0.2         # kW/K
        t_ground = 283.15  # K  (10 °C ground)
        cp_kW = HEAT_CAPACITY_OF_WATER_JPERKGK / 1000  # kW/(kg·K)

        t_out = calc_temperature_out_per_pipe(t_in=t_in, m=m, k=k, t_ground=t_ground)

        lhs = m * cp_kW * (t_out - t_in)
        rhs = -k * ((t_in + t_out) / 2 - t_ground)
        assert np.isclose(lhs, rhs, rtol=1e-6), (
            f"Energy balance violated: m·cp·ΔT = {lhs:.6f} kW, "
            f"−k·(T_avg − T_gnd) = {rhs:.6f} kW"
        )

    def test_calc_temperature_out_dh_pipe_cools(self):
        """In a DH pipe (T_in > T_ground), the outlet temperature should be between T_ground and T_in."""
        t_in = 363.15     # K  (90 °C, hot supply)
        t_ground = 283.15  # K  (10 °C)
        t_out = calc_temperature_out_per_pipe(t_in=t_in, m=0.5, k=0.2, t_ground=t_ground)
        assert t_ground < t_out < t_in, (
            f"DH pipe should cool from inlet to outlet; "
            f"got T_ground={t_ground:.1f} K, T_out={t_out:.1f} K, T_in={t_in:.1f} K"
        )

    def test_calc_temperature_out_dc_pipe_warms(self):
        """In a DC pipe (T_in < T_ground), the outlet temperature should be between T_in and T_ground."""
        t_in = 278.15      # K  (5 °C, cold supply)
        t_ground = 293.15  # K  (20 °C)
        t_out = calc_temperature_out_per_pipe(t_in=t_in, m=0.5, k=0.2, t_ground=t_ground)
        assert t_in < t_out < t_ground, (
            f"DC pipe should warm from inlet to outlet; "
            f"got T_in={t_in:.1f} K, T_out={t_out:.1f} K, T_ground={t_ground:.1f} K"
        )
    # ------------------------------------------------------------------ #
    #  Parameter sensitivity — diameter, temperature, network type        #
    # ------------------------------------------------------------------ #

    def test_calc_reynolds_decreases_monotonically_with_diameter(self):
        """Re is inversely proportional to pipe diameter (Re ∝ 1/D) at fixed ṁ and T.

        Checked across the full database range: 20 mm → 500 mm → 1 500 mm.
        """
        m = np.array([[0.560]])
        T = np.array([[333.15]])
        diameters = [np.array([d]) for d in [0.020, 0.100, 0.500, 1.500]]
        reynolds = [calc_reynolds(m, T, D).flat[0] for D in diameters]

        assert all(re_a > re_b for re_a, re_b in zip(reynolds, reynolds[1:])), (
            "Re should decrease monotonically as diameter increases: "
            + ", ".join(f"D={d:.3f} m → Re={r:.0f}" for d, r in zip(
                [0.020, 0.100, 0.500, 1.500], reynolds))
        )

    def test_calc_reynolds_increases_monotonically_with_temperature(self):
        """Re increases with temperature because water viscosity decreases (Re ∝ 1/ν(T)).

        Checked across the realistic DH/DC supply range: 280 K → 370 K.
        """
        m = np.array([[0.560]])
        D = np.array([0.100])
        temperatures = [280.0, 300.0, 333.15, 353.15, 368.15]
        reynolds = [calc_reynolds(m, np.array([[T]]), D).flat[0] for T in temperatures]

        assert all(re_a < re_b for re_a, re_b in zip(reynolds, reynolds[1:])), (
            "Re should increase monotonically as temperature rises: "
            + ", ".join(f"T={T:.0f} K → Re={r:.0f}" for T, r in zip(temperatures, reynolds))
        )

    def test_calc_pressure_loss_strongly_higher_for_smaller_diameter(self):
        """Pressure loss increases dramatically as diameter shrinks: ΔP ∝ f/D⁵.

        At the same ṁ and T, a 20 mm pipe should produce orders-of-magnitude
        more pressure drop than a 100 mm pipe (exact factor ≈ 2 400 at these conditions).
        """
        m = np.array([[0.560]])
        T = np.array([[333.15]])
        L = np.array([100.0])

        dp_20mm  = calc_pressure_loss_pipe(np.array([0.020]), L, m, T, PressureLossMode.DIRECT)
        dp_100mm = calc_pressure_loss_pipe(np.array([0.100]), L, m, T, PressureLossMode.DIRECT)
        dp_500mm = calc_pressure_loss_pipe(np.array([0.500]), L, m, T, PressureLossMode.DIRECT)

        assert dp_20mm.flat[0] > dp_100mm.flat[0] > dp_500mm.flat[0], (
            "Pressure loss should decrease as diameter increases"
        )
        # The D^-5 scaling (partially offset by the friction factor shift) should
        # produce a ratio of at least 1 000× between the 20 mm and 100 mm cases.
        ratio_20_to_100 = dp_20mm.flat[0] / dp_100mm.flat[0]
        assert ratio_20_to_100 > 1000, (
            f"Expected ΔP(20 mm) >> ΔP(100 mm); actual ratio = {ratio_20_to_100:.0f}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])