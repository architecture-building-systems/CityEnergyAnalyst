"""
List the fields that can be used for the demand-graphs ``--analysis-fields`` parameter given a scenario
"""
from __future__ import division

import os
import pandas as pd
import cea.config
import cea.inputlocator

def demand_graph_fields(scenario):
    """Lists the available fields for the demand graphs - these are fields that are present in both the
    building demand results files as well as the totals file (albeit with different units)."""
    locator = cea.inputlocator.InputLocator(scenario)
    df_total_demand = pd.read_csv(locator.get_total_demand())
    total_fields = set(df_total_demand.columns.tolist())
    first_building = df_total_demand['Name'][0]
    df_building = pd.read_csv(locator.get_demand_results_file(first_building))
    fields = set(df_building.columns.tolist())
    fields.remove('DATE')
    fields.remove('Name')
    # remove fields in demand results files that do not have a corresponding field in the totals file
    bad_fields = set(field for field in fields if not field.split('_')[0] + "_MWhyr" in total_fields)
    fields = fields - bad_fields
    return list(fields)


def main(config):
    """
    print the available fields for the demand graphs to STDOUT.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario

    # print out all configuration variables used by this script
    print('\n'.join(sorted(demand_graph_fields(config.scenario))))


if __name__ == '__main__':
    main(cea.config.Configuration())
