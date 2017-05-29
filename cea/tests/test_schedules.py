import unittest


class TestBuildingPreprocessing(unittest.TestCase):
    def test_mixed_use_archetype_values(self):
        # test if a sample mixed use building gets standard results
        from cea.demand.preprocessing.properties import calculate_average_multiuse
        from cea.demand.preprocessing.properties import correct_archetype_areas
        import pandas as pd

        locator = cea.inputlocator.InputLocator(scenario_path=cea.globalvar.GlobalVariables().scenario_reference)

        self.assert(pd.DataFrame(data=np.array(['B1', 0.5, 0.5, 208.94736, 12.9],['B2', 0.75, 0.25, 14.4, 164.48275],
                                               columns=['Name', 'OFFICE', 'GYM', 'X_ghp', 'El_Wm2']),
                                 calculate_average_multiuse,
                                 properties_df = pd.DataFrame(data=np.array(['B1', 0.5, 0.5, 0, 0],
                                                                            ['B2', 0.25, 0.75, 0, 0]),
                                                              columns=['Name','OFFICE', 'GYM', 'X_ghp', 'El_Wm2']),
                                 occupant_densities = {'OFFICE': 0.071428571,'GYM': 0.2}, list_uses = ['OFFICE', 'GYM'],
                                 properties_DB = get_database(locator.get_archetypes_properties(), 'INTERNAL_LOADS')

        self.assert(pd.DataFrame(data=np.array(['B1', 0.5, 0.5, 0.5],['B2', 0.75, 0.25, 0.75],
                                               columns=['Name', 'SERVERROOM', 'PARKING', 'Hs']),
                                 correct_archetype_areas,
                                 prop_architecture_df = pd.DataFrame(
                                     data=np.array(['B1', 0.5, 0.5, 0.5], ['B2', 0.25, 0.75, 0.25]),
                                     columns=['Name','SERVERROOM', 'PARKING', 'Hs']),
                                 architecture_DB = get_database(locator.get_archetypes_properties(), 'ARCHITECTURE'),
                                 list_uses = ['OFFICE', 'GYM']))

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