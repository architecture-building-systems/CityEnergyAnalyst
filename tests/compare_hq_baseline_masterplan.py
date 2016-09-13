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

    common_buildings = set(baseline_demand.index).intersection(set(masterplan_demand.index))
    print(common_buildings)

    for building in common_buildings:
        # compare building properties
        baseline_bpr = baseline_properties[building]
        masterplan_bpr = masterplan_properties[building]

        for column in baseline_bpr.architecture.keys():
            baseline_value = baseline_bpr.architecture[column]
            masterplan_value = masterplan_bpr.architecture[column]
            if baseline_value != masterplan_value:
                print('architecture difference: %s @ %s (baseline=%s, masterplan=%s)'
                      % (building, column, baseline_value, masterplan_value))


if __name__ == '__main__':
    main()