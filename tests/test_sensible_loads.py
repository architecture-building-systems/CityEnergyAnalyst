import unittest


class TestCorrectionFactorForHeatingAndCoolingSetpoints(unittest.TestCase):

    def test_calc_t_em_ls_raises_ValueError(self):
        from cea.demand.sensible_loads import calc_t_em_ls
        self.assertRaises(ValueError, calc_t_em_ls, heating_system='T1', cooling_system='T1', control_system=None)
        self.assertRaises(ValueError, calc_t_em_ls, heating_system='T1', cooling_system='XYZ', control_system='T1')
        self.assertRaises(ValueError, calc_t_em_ls, heating_system='T1', cooling_system=None, control_system='T1')

    def test_calc_t_em_ls_T0(self):
        from cea.demand.sensible_loads import calc_t_em_ls
        self.assertEqual(calc_t_em_ls('T1', 'T0', 'T1'),  (2.65, 0.0))
        self.assertEqual(calc_t_em_ls('T0', 'T3', 'T1'), (0.0, -2.0))
