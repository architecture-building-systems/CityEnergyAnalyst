import unittest
from pandas.util.testing import assert_frame_equal

class TestBuildingPreprocessing(unittest.TestCase):
    def test_mixed_use_archetype_values(self):
        # test if a sample mixed use building gets standard results
        from cea.globalvar import GlobalVariables
        from cea.inputlocator import InputLocator
        from cea.demand.preprocessing.properties import calculate_average_multiuse
        from cea.demand.preprocessing.properties import correct_archetype_areas
        from cea.demand.preprocessing.properties import get_database
        from cea.demand.preprocessing.properties import calc_code
        import pandas as pd
        import numpy as np

        locator = InputLocator(scenario_path=GlobalVariables().scenario_reference)

        # create test results
        results_df = pd.DataFrame(data=[['B1', 0.5, 0.5, 0.0, 0.0], ['B2', 0.25, 0.75, 0.0, 0.0]],
                                  columns=['Name', 'OFFICE', 'GYM', 'X_ghp', 'El_Wm2'])
        properties_DB = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS').set_index('Code')
        office_occ = float(pd.read_excel(locator.get_archetypes_schedules(), 'OFFICE').T['density'].values[:1][0])
        gym_occ = float(pd.read_excel(locator.get_archetypes_schedules(), 'GYM').T['density'].values[:1][0])
        for index in results_df.index:
            results_df['El_Wm2'][index] = properties_DB['El_Wm2']['OFFICE'] * results_df['OFFICE'][index] + \
                                          properties_DB['El_Wm2']['GYM'] * results_df['GYM'][index]
            results_df['X_ghp'][index] = (properties_DB['X_ghp']['OFFICE']/office_occ * results_df['OFFICE'][index] \
                                         + properties_DB['X_ghp']['GYM']/gym_occ * results_df['GYM'][index]) / \
                                         (results_df['OFFICE'][index]/office_occ + results_df['GYM'][index]/gym_occ)

        assert_frame_equal(calculate_average_multiuse(
            properties_df = pd.DataFrame(data=[['B1', 0.5, 0.5, 0.0, 0.0], ['B2', 0.25, 0.75, 0.0, 0.0]],
                                         columns=['Name','OFFICE', 'GYM', 'X_ghp', 'El_Wm2']),
            occupant_densities = {'OFFICE': 1/office_occ,'GYM': 1/gym_occ},
            list_uses = ['OFFICE', 'GYM'],
            properties_DB = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS')),
            results_df)

        architecture_DB = get_database(locator.get_archetypes_properties(), 'ARCHITECTURE')
        architecture_DB['Code'] = architecture_DB.apply(lambda x: x['building_use'] + str(x['year_start']) +
                                                                  str(x['year_end']) + x['standard'], axis=1)

        self.assertEqual(correct_archetype_areas(
            prop_architecture_df = pd.DataFrame(
                data=[['B1', 0.5, 0.5, 0.0, 2006, 2020, 'C'], ['B2', 0.2, 0.8, 0.0, 1300, 1920, 'R']],
                columns=['Name','SERVERROOM', 'PARKING', 'Hs', 'year_start', 'year_end', 'standard']),
            architecture_DB = architecture_DB,
            list_uses = ['SERVERROOM', 'PARKING']),
            [0.5, 0.2])


class TestScheduleCreation(unittest.TestCase):
    def test_mixed_use_schedules(self):
        from cea.globalvar import GlobalVariables
        from cea.inputlocator import InputLocator
        from cea.demand.occupancy_model import calc_schedules
        # from cea.demand.occupancy_model import schedule_maker
        import pandas as pd
        import numpy as np

        locator = InputLocator(scenario_path=GlobalVariables().scenario_reference)
        office_occ = float(pd.read_excel(locator.get_archetypes_schedules(), 'OFFICE').T['density'].values[:1][0])
        industrial_occ = float(pd.read_excel(locator.get_archetypes_schedules(),
                                             'INDUSTRIAL').T['density'].values[:1][0])

        # dates = pd.date_range('2016-01-01', periods=72, freq='H')
        # list_uses = ['MULTI_RES', 'OFFICE']
        # archetype_schedules, archetype_values = schedule_maker(dates, locator, list_uses)
        # schedules = calc_schedules(list_uses, archetype_schedules, occupancy, archetype_values)

        schedules_office = [0.4, 0.4, 0.4, 0.0]
        schedules_industry = [1.0, 1.0, 0.4, 0.3]
        occupancy = {'OFFICE': 0.5, 'INDUSTRIAL': 0.5}
        average_occ = 1 / (occupancy['OFFICE'] / office_occ + occupancy['INDUSTRIAL'] / industrial_occ)
        internal_loads_DB = pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS').set_index('Code')
        indoor_comfort_DB = pd.read_excel(locator.get_archetypes_properties(), 'INDOOR_COMFORT').set_index('Code')

        results = pd.DataFrame({'people': np.ones(8760) *
                             (occupancy['OFFICE'] * schedules_office[0] / office_occ + occupancy['INDUSTRIAL'] *
                              schedules_industry[0] / industrial_occ),
                   've': np.ones(8760) *
                         (occupancy['OFFICE'] * schedules_office[0] * indoor_comfort_DB['Ve_lps']['OFFICE'] /
                          office_occ + occupancy['INDUSTRIAL'] * schedules_industry[0] / industrial_occ *
                          indoor_comfort_DB['Ve_lps']['INDUSTRIAL']) /
                         ((occupancy['OFFICE'] * indoor_comfort_DB['Ve_lps']['OFFICE'] / office_occ +
                           occupancy['INDUSTRIAL'] * indoor_comfort_DB['Ve_lps']['INDUSTRIAL'] / industrial_occ) *
                          average_occ),
                   'Qs': np.ones(8760) *
                         (occupancy['OFFICE'] * schedules_office[0] / office_occ * internal_loads_DB['Qs_Wp']['OFFICE']
                          + occupancy['INDUSTRIAL'] * schedules_industry[0] / industrial_occ *
                          internal_loads_DB['Qs_Wp']['INDUSTRIAL']) /
                         ((occupancy['OFFICE'] * internal_loads_DB['Qs_Wp']['OFFICE'] / office_occ +
                           occupancy['INDUSTRIAL'] * internal_loads_DB['Qs_Wp']['INDUSTRIAL'] / industrial_occ) *
                          average_occ),
                   'X': np.ones(8760) *
                        (occupancy['OFFICE'] * schedules_office[0] / office_occ * internal_loads_DB['X_ghp']['OFFICE'] +
                         occupancy['INDUSTRIAL'] * schedules_industry[0] / industrial_occ *
                         internal_loads_DB['X_ghp']['INDUSTRIAL']) /
                        ((occupancy['OFFICE'] * internal_loads_DB['X_ghp']['OFFICE'] / office_occ +
                          occupancy['INDUSTRIAL'] * internal_loads_DB['X_ghp']['INDUSTRIAL'] / industrial_occ) *
                         average_occ),
                   'Ea': np.ones(8760) *
                         (occupancy['OFFICE'] * schedules_office[1] * internal_loads_DB['Ea_Wm2']['OFFICE'] +
                          occupancy['INDUSTRIAL'] * schedules_industry[1] * internal_loads_DB['Ea_Wm2']['INDUSTRIAL']) /
                         (occupancy['OFFICE'] * internal_loads_DB['Ea_Wm2']['OFFICE'] +
                          occupancy['INDUSTRIAL'] * internal_loads_DB['Ea_Wm2']['INDUSTRIAL']),
                   'El': np.ones(8760) *
                         (occupancy['OFFICE'] * schedules_office[1] * internal_loads_DB['El_Wm2']['OFFICE'] +
                          occupancy['INDUSTRIAL'] * schedules_industry[1] * internal_loads_DB['El_Wm2']['INDUSTRIAL']) /
                         (occupancy['OFFICE'] * internal_loads_DB['El_Wm2']['OFFICE'] +
                          occupancy['INDUSTRIAL'] * internal_loads_DB['El_Wm2']['INDUSTRIAL']),
                   'Epro': np.ones(8760) *
                         (occupancy['OFFICE'] * schedules_office[3] * internal_loads_DB['Epro_Wm2']['OFFICE'] +
                          occupancy['INDUSTRIAL'] * schedules_industry[3] * internal_loads_DB['Epro_Wm2']['INDUSTRIAL'])
                           / (occupancy['OFFICE'] * internal_loads_DB['Epro_Wm2']['OFFICE'] +
                              occupancy['INDUSTRIAL'] * internal_loads_DB['Epro_Wm2']['INDUSTRIAL']),
                   'Ere': np.ones(8760) *
                         (occupancy['OFFICE'] * schedules_office[1] * internal_loads_DB['Ere_Wm2']['OFFICE'] +
                          occupancy['INDUSTRIAL'] * schedules_industry[1] * internal_loads_DB['Ere_Wm2']['INDUSTRIAL'])
                           / (occupancy['OFFICE'] * internal_loads_DB['Ere_Wm2']['OFFICE'] +
                              occupancy['INDUSTRIAL'] * internal_loads_DB['Ere_Wm2']['INDUSTRIAL']),
                   'Ed': np.ones(8760) *
                         (occupancy['OFFICE'] * schedules_office[1] * internal_loads_DB['Ed_Wm2']['OFFICE'] +
                          occupancy['INDUSTRIAL'] * schedules_industry[1] * internal_loads_DB['Ed_Wm2']['INDUSTRIAL'])
                           / (occupancy['OFFICE'] * internal_loads_DB['Ed_Wm2']['OFFICE'] +
                              occupancy['INDUSTRIAL'] * internal_loads_DB['Ed_Wm2']['INDUSTRIAL']),
                   'Vww': np.ones(8760) * (
                       occupancy['OFFICE'] * schedules_office[2] / office_occ * internal_loads_DB['Vww_lpd']['OFFICE'] +
                       occupancy['INDUSTRIAL'] * schedules_industry[2] / industrial_occ *
                       internal_loads_DB['Vww_lpd']['INDUSTRIAL']) / (
                       (occupancy['OFFICE'] * internal_loads_DB['Vww_lpd']['OFFICE'] / office_occ +
                        occupancy['INDUSTRIAL'] * internal_loads_DB['Vww_lpd']['INDUSTRIAL'] / industrial_occ) *
                       average_occ),
                   'Vw': np.ones(8760) * (
                       occupancy['OFFICE'] * schedules_office[2] / office_occ * internal_loads_DB['Vw_lpd']['OFFICE'] +
                       occupancy['INDUSTRIAL'] * schedules_industry[2] / industrial_occ *
                       internal_loads_DB['Vw_lpd']['INDUSTRIAL']) / (
                       (occupancy['OFFICE'] * internal_loads_DB['Vw_lpd']['OFFICE'] / office_occ +
                        occupancy['INDUSTRIAL'] * internal_loads_DB['Vw_lpd']['INDUSTRIAL'] / industrial_occ) *
                       average_occ)})
        calculated_schedule = pd.DataFrame(
            calc_schedules(list_uses=['OFFICE', 'INDUSTRIAL'],
                                             archetype_schedules=[[schedules_office[0] + np.zeros(8760),
                                                                   schedules_office[1] + np.zeros(8760),
                                                                   schedules_office[2] + np.zeros(8760),
                                                                   schedules_office[3] + np.zeros(8760)],
                                                                  [schedules_industry[0] + np.zeros(8760),
                                                                   schedules_industry[1] + np.zeros(8760),
                                                                   schedules_industry[2] + np.zeros(8760),
                                                                   schedules_industry[3] + np.zeros(8760)]],
                                             occupancy=occupancy,
                                             archetype_values={'people': [1 / office_occ, 1 / industrial_occ],
                                                               've': [indoor_comfort_DB['Ve_lps']['OFFICE'],
                                                                      indoor_comfort_DB['Ve_lps']['INDUSTRIAL']],
                                                               'Qs': [internal_loads_DB['Qs_Wp']['OFFICE'],
                                                                      internal_loads_DB['Qs_Wp']['INDUSTRIAL']],
                                                               'X': [internal_loads_DB['X_ghp']['OFFICE'],
                                                                     internal_loads_DB['X_ghp']['INDUSTRIAL']],
                                                               'Ea': [internal_loads_DB['Ea_Wm2']['OFFICE'],
                                                                      internal_loads_DB['Ea_Wm2']['INDUSTRIAL']],
                                                               'El': [internal_loads_DB['El_Wm2']['OFFICE'],
                                                                      internal_loads_DB['El_Wm2']['INDUSTRIAL']],
                                                               'Epro': [internal_loads_DB['Epro_Wm2']['OFFICE'],
                                                                        internal_loads_DB['Epro_Wm2']['INDUSTRIAL']],
                                                               'Ere': [internal_loads_DB['Ere_Wm2']['OFFICE'],
                                                                       internal_loads_DB['Ere_Wm2']['INDUSTRIAL']],
                                                               'Ed': [internal_loads_DB['Ed_Wm2']['OFFICE'],
                                                                      internal_loads_DB['Ed_Wm2']['INDUSTRIAL']],
                                                               'Vww': [internal_loads_DB['Vww_lpd']['OFFICE'],
                                                                       internal_loads_DB['Vww_lpd']['INDUSTRIAL']],
                                                               'Vw': [internal_loads_DB['Vw_lpd']['OFFICE'],
                                                                      internal_loads_DB['Vw_lpd']['INDUSTRIAL']]}))

        assert_frame_equal(results, calculated_schedule)

