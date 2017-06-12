import unittest


class TestCorrectionFactorForHeatingAndCoolingSetpoints(unittest.TestCase):
    """
    def test_calc_delta_theta_int_inc_cooling_raises_ValueError(self):
        from cea.demand.space_emission_systems import calc_delta_theta_int_inc_cooling
        self.assertRaises(ValueError, calc_delta_theta_int_inc_cooling, cooling_system='T1', control_system=None)
        self.assertRaises(ValueError, calc_delta_theta_int_inc_cooling, cooling_system='XYZ', control_system='T1')
        self.assertRaises(ValueError, calc_delta_theta_int_inc_cooling, cooling_system=None, control_system='T1')

    def test_calc_delta_theta_int_inc_heating_raises_ValueError(self):
        from cea.demand.space_emission_systems import calc_delta_theta_int_inc_heating
        self.assertRaises(ValueError, calc_delta_theta_int_inc_heating, heating_system='T1', control_system=None)
        self.assertRaises(ValueError, calc_delta_theta_int_inc_heating, heating_system='XYZ', control_system='T1')
        self.assertRaises(ValueError, calc_delta_theta_int_inc_heating, heating_system=None, control_system='T1')

    def test_calc_delta_theta_int_inc_cooling_T0(self):
        from cea.demand.space_emission_systems import calc_delta_theta_int_inc_cooling
        self.assertEqual(calc_delta_theta_int_inc_cooling('T0', 'T1'), 0.0)

    def test_calc_delta_theta_int_inc_heating_T0(self):
        from cea.demand.space_emission_systems import calc_delta_theta_int_inc_heating
        self.assertEqual(calc_delta_theta_int_inc_heating('T0', 'T1'), 0.0)
    """