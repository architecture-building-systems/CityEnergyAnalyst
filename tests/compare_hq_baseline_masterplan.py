"""
For the issue #i338 (Baseline and masterplan results are inconsistent) this file does some analysis on the inputs
and outputs.
"""
import pandas as pd
from cea.inputlocator import InputLocator
from cea.globalvar import GlobalVariables
from cea.demand.thermal_loads import BuildingProperties


# change these to suit your reference case structure:
BASELINE_PATH = r"C:\reference-case\reference-case-hq\baseline"
MASTERPLAN_PATH = r"C:\reference-case\reference-case-hq\masterplan"

def main():
    gv = GlobalVariables()

    baseline_locator = InputLocator(BASELINE_PATH)
    masterplan_locator = InputLocator(MASTERPLAN_PATH)

    baseline_demand = pd.read_csv(baseline_locator.get_total_demand()).set_index('Name')
    masterplan_demand = pd.read_csv(masterplan_locator.get_total_demand()).set_index('Name')

    baseline_properties = BuildingProperties(baseline_locator, gv)
    masterplan_properties = BuildingProperties(masterplan_locator, gv)

    main_buildings = ['B9011701', 'B3169989']

    print ('-' * 80)
    for building in main_buildings:
        print('Checking building %s' % building)
        # compare building properties
        baseline_bpr = baseline_properties[building]
        masterplan_bpr = masterplan_properties[building]

        # architecture
        print('testing architecture')
        for column in baseline_bpr.architecture.keys():
            baseline_value = baseline_bpr.architecture[column]
            masterplan_value = masterplan_bpr.architecture[column]
            if baseline_value != masterplan_value:
                print('architecture difference: %s @ %s (baseline=%s, masterplan=%s)'
                      % (building, column, baseline_value, masterplan_value))

        # building systems
        print('testing building systems')
        for column in baseline_bpr.building_systems.keys():
            baseline_value = baseline_bpr.building_systems[column]
            masterplan_value = masterplan_bpr.building_systems[column]
            if baseline_value != masterplan_value:
                print('building system difference: %s @ %s (baseline=%s, masterplan=%s)'
                      % (building, column, baseline_value, masterplan_value))

        # hvac
        print('testing hvac')
        for column in baseline_bpr.hvac.keys():
            baseline_value = baseline_bpr.hvac[column]
            masterplan_value = masterplan_bpr.hvac[column]
            if baseline_value != masterplan_value:
                print('hvac difference: %s @ %s (baseline=%s, masterplan=%s)'
                      % (building, column, baseline_value, masterplan_value))

        # age
        print('testing age')
        for column in baseline_bpr.age.keys():
            baseline_value = baseline_bpr.age[column]
            masterplan_value = masterplan_bpr.age[column]
            if baseline_value != masterplan_value:
                print('age difference: %s @ %s (baseline=%s, masterplan=%s)'
                      % (building, column, baseline_value, masterplan_value))

        # age
        print('testing rc_model')
        for column in baseline_bpr.rc_model.keys():
            baseline_value = baseline_bpr.rc_model[column]
            masterplan_value = masterplan_bpr.rc_model[column]
            if baseline_value != masterplan_value:
                print('rc_model difference: %s @ %s (baseline=%s, masterplan=%s)'
                      % (building, column, baseline_value, masterplan_value))




        print('QHf: baseline=%.2f, masterp0lan=%.2f' % (baseline_demand['QHf_MWhyr'][building],
                                                        masterplan_demand['QHf_MWhyr'][building]))
        print('QCf: baseline=%.2f, masterp0lan=%.2f' % (baseline_demand['QCf_MWhyr'][building],
                                                        masterplan_demand['QCf_MWhyr'][building]))
        print ('-' * 80)



if __name__ == '__main__':
    main()