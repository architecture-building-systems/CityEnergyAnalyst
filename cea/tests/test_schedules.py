import unittest


class TestScheduleCreation(unittest.TestCase):
    def test_mixed_use_schedules(self):
        from cea.demand.occupancy_model import calc_schedules
        from cea.demand.occupancy_model import schedule_maker
        dates = pd.date_range('2016-01-01', periods=72, freq='H')
        locator = cea.inputlocator.InputLocator(r'C:')
        list_uses = ['MULTI_RES', 'OFFICE']
        archetype_schedules, archetype_values = schedule_maker(dates, locator, list_uses)
        schedules = calc_schedules(list_uses, archetype_schedules, occupancy, archetype_values)

        self.assertRaises(ValueError, calc_delta_theta_int_inc_cooling, cooling_system='T1', control_system=None)
        self.assertRaises(ValueError, calc_delta_theta_int_inc_cooling, cooling_system='XYZ', control_system='T1')
        self.assertRaises(ValueError, calc_delta_theta_int_inc_cooling, cooling_system=None, control_system='T1')