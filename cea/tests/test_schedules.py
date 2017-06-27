import os
import unittest
import zipfile
import tempfile
import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
import cea.examples
from cea.inputlocator import InputLocator
from cea.globalvar import GlobalVariables
from cea.demand.preprocessing.properties import calculate_average_multiuse
from cea.demand.preprocessing.properties import correct_archetype_areas
from cea.demand.preprocessing.properties import get_database
from cea.demand.occupancy_model import calc_schedules
from cea.demand.occupancy_model import schedule_maker


class TestBuildingPreprocessing(unittest.TestCase):
    def test_mixed_use_archetype_values(self):
        # test if a sample mixed use building gets standard results
        # get reference case to be tested
        archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
        archive.extractall(tempfile.gettempdir())
        reference_case = os.path.join(tempfile.gettempdir(), 'reference-case-open', 'baseline')
        locator = InputLocator(reference_case)

        # create test results
        office_occ = float(pd.read_excel(locator.get_archetypes_schedules(), 'OFFICE').T['density'].values[:1][0])
        gym_occ = float(pd.read_excel(locator.get_archetypes_schedules(), 'GYM').T['density'].values[:1][0])
        calculated_results = calculate_average_multiuse(
            properties_df=pd.DataFrame(data=[['B1', 0.5, 0.5, 0.0, 0.0], ['B2', 0.25, 0.75, 0.0, 0.0]],
                                       columns=['Name', 'OFFICE', 'GYM', 'X_ghp', 'El_Wm2']),
            occupant_densities={'OFFICE': 1 / office_occ, 'GYM': 1 / gym_occ},
            list_uses=['OFFICE', 'GYM'],
            properties_DB=pd.read_excel(locator.get_archetypes_properties(), 'INTERNAL_LOADS'))

        # compare to reference values
        expected_results = pd.DataFrame(data=[['B1', 0.5, 0.5, 208.947368, 12.9], ['B2', 0.25, 0.75, 236.382979, 11.4]],
                                        columns=['Name', 'OFFICE', 'GYM', 'X_ghp', 'El_Wm2'])
        assert_frame_equal(calculated_results, expected_results)

        architecture_DB = get_database(locator.get_archetypes_properties(), 'ARCHITECTURE')
        architecture_DB['Code'] = architecture_DB.apply(lambda x: x['building_use'] + str(x['year_start']) +
                                                                  str(x['year_end']) + x['standard'], axis=1)

        self.assertEqual(correct_archetype_areas(
            prop_architecture_df=pd.DataFrame(
                data=[['B1', 0.5, 0.5, 0.0, 2006, 2020, 'C'], ['B2', 0.2, 0.8, 0.0, 1300, 1920, 'R']],
                columns=['Name', 'SERVERROOM', 'PARKING', 'Hs', 'year_start', 'year_end', 'standard']),
            architecture_DB=architecture_DB,
            list_uses=['SERVERROOM', 'PARKING']),
            [0.5, 0.2])


class TestScheduleCreation(unittest.TestCase):
    def test_mixed_use_schedules(self):
        # get reference case to be tested
        archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
        archive.extractall(tempfile.gettempdir())
        reference_case = os.path.join(tempfile.gettempdir(), 'reference-case-open', 'baseline')
        locator = InputLocator(reference_case)

        # calculate schedules
        list_uses = ['OFFICE', 'INDUSTRIAL']
        occupancy = {'OFFICE': 0.5, 'INDUSTRIAL': 0.5}
        gv = GlobalVariables()
        date = pd.date_range(gv.date_start, periods=8760, freq='H')
        archetype_schedules, archetype_values = schedule_maker(date, locator, list_uses)
        calculated_schedules = calc_schedules(list_uses, archetype_schedules, occupancy, archetype_values)

        reference_time = 3456
        reference_results = {'El': 0.1080392156862745, 'Qs': 0.0088163265306122462, 've': 0.01114606741573034,
                             'Epro': 0.17661721828842394, 'people': 0.0080000000000000019, 'Ed': 0.0, 'Vww': 0.0,
                             'Ea': 0.1340740740740741, 'Ere': 0.0, 'Vw': 0.0, 'X': 0.010264150943396229}

        for schedule in reference_results:
            self.assertEqual(calculated_schedules[schedule][reference_time], reference_results[schedule],
                             msg="Schedule '%s' at time %s, %f != %f" % (schedule, str(reference_time),
                                                                         calculated_schedules[schedule][reference_time],
                                                                         reference_results[schedule]))
