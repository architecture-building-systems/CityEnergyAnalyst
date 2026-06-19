"""
Anthropogenic Heat Assessment - Main Entry Point

Calculates heat rejection to the environment from building energy systems.
Reads supply configuration and final-energy results (sole source of truth).
"""
import cea.config
import cea.inputlocator
from cea.analysis.heat.heat_rejection import calculate_heat_rejection_for_whatif

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config: cea.config.Configuration):
    """
    Main entry point for anthropogenic-heat script.

    Calculates heat rejection to the environment for each what-if scenario using
    final-energy results and supply configuration as sole inputs.

    Outputs per what-if scenario:
    - heat_rejection_buildings.csv: Summary by building/plant
    - heat_rejection_components.csv: Detailed component breakdown
    - {name}.csv: Hourly heat rejection time series per building/plant

    :param config: Configuration object
    """
    locator = cea.inputlocator.InputLocator(config.scenario)

    whatif_names = config.what_ifs.what_if_name
    if not whatif_names:
        raise ValueError(
            "what-if-name is required. Please select at least one What-if Scenario."
        )
    if isinstance(whatif_names, str):
        whatif_names = [whatif_names]

    print("=" * 80)
    print("HEAT REJECTION CALCULATION")
    print("=" * 80)

    for whatif_name in whatif_names:
        print(f"\nProcessing what-if scenario: {whatif_name}")
        print("-" * 60)

        try:
            buildings_df, components_df = calculate_heat_rejection_for_whatif(whatif_name, locator)

            buildings_file = locator.get_heat_rejection_whatif_buildings_file(whatif_name)
            components_file = locator.get_heat_rejection_whatif_components_file(whatif_name)
            locator.ensure_parent_folder_exists(buildings_file)

            buildings_df.to_csv(buildings_file, index=False, float_format='%.4f')
            components_df.to_csv(components_file, index=False, float_format='%.4f')

            print(f"  Buildings processed: {len(buildings_df)}")
            print(f"  Component rows: {len(components_df)}")

            if not buildings_df.empty:
                total_hr = buildings_df['heat_rejection_annual_MWh'].sum()
                print(f"  Total heat rejection: {total_hr:,.1f} MWh/yr")

            print(f"  Saved: {buildings_file}")
            print(f"  Saved: {components_file}")

        except FileNotFoundError as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 80)
    print("HEAT REJECTION CALCULATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main(cea.config.Configuration())
