"""
Prints out input data for a list of buildings.
"""
import pandas as pd
from cea.inputlocator import InputLocator
from cea.globalvar import GlobalVariables
from cea.demand.thermal_loads import BuildingProperties


def main(scenario_path, output_path, buildings=None):
    locator = InputLocator(scenario_path)
    gv = GlobalVariables()
    bp = BuildingProperties(locator, gv)
    if not buildings:
        buildings = list(bp._prop_RC_model.index)
    row_index = []
    row_index.extend(bp._prop_thermal.columns)
    row_index.extend(bp._prop_geometry.columns)
    row_index.extend(bp._prop_architecture.columns)
    row_index.extend(bp._prop_occupancy.columns)
    row_index.extend(bp._prop_HVAC_result.columns)
    row_index.extend(bp._prop_RC_model.columns)
    row_index.extend(bp._prop_comfort.columns)
    row_index.extend(bp._prop_internal_loads.columns)
    row_index.extend(bp._prop_age.columns)
    df = pd.DataFrame(columns=buildings, index=row_index)

    for building in buildings:
        bdata = {}
        bdata.update(bp._prop_thermal.T[building].to_dict())
        bdata.update(bp._prop_geometry.T[building].to_dict())
        bdata.update(bp._prop_architecture.T[building].to_dict())
        bdata.update(bp._prop_occupancy.T[building].to_dict())
        bdata.update(bp._prop_HVAC_result.T[building].to_dict())
        bdata.update(bp._prop_RC_model.T[building].to_dict())
        bdata.update(bp._prop_comfort.T[building].to_dict())
        bdata.update(bp._prop_internal_loads.T[building].to_dict())
        bdata.update(bp._prop_age.T[building].to_dict())
        bseries = pd.Series(bdata, index=row_index)
        df[building] = bseries

    df.to_csv(output_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder', default=r"C:\reference-case-zug\baseline")
    parser.add_argument('-o', '--output', help='Path to output file', default='building_info.csv')
    parser.add_argument('-b', '--buildings', nargs='+', help='list of buildings to print', default=None)
    args = parser.parse_args()
    main(scenario_path=args.scenario, buildings=args.buildings, output_path=args.output)