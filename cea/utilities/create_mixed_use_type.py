"""
This script creates a new use-type by aggregating values from a list of different use-types
"""

import pandas as pd

import cea
import cea.config
import cea.inputlocator
from cea.datamanagement.archetypes_mapper import calculate_average_multiuse
from cea.datamanagement.schedule_helper import calc_single_mixed_schedule, ScheduleData
from cea.utilities.schedule_reader import save_cea_schedules


__author__ = "Reynold Mok"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Reynold Mok, Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


DEFAULT_USE_TYPE = 'MULTI_RES'
COLUMN_VAR_NAME_TEMPLATE = 'USE_{}'
COLUMN_VAR_VAL_TEMPLATE = 'USE_{}_R'


def create_mixed_use_type(locator, internal_loads_df, indoor_comfort_df,
                          use_type_name, use_type_metadata, use_type_ratios_dict):
    """
    Takes a list of use-types and their respective ratios to aggregate and create a new use-type
    with schedules, internal loads and indoor comfort data

    :param schedules_path:
    :param internal_loads_df:
    :param indoor_comfort_df:
    :param use_type_name:
    :param use_type_metadata:
    :param use_type_ratios_dict:
    :return:
    """
    list_uses = use_type_ratios_dict.keys()
    list_var_names = [COLUMN_VAR_NAME_TEMPLATE.format(i) for i in range(len(use_type_ratios_dict))]
    list_var_values = [COLUMN_VAR_VAL_TEMPLATE.format(i) for i in range(len(use_type_ratios_dict))]

    # Creating required parameters
    properties_dict = {}
    for i, (k, v) in enumerate(use_type_ratios_dict.items()):
        properties_dict[list_var_names[i]] = k
        properties_dict[list_var_values[i]] = v
    properties_df = pd.DataFrame([properties_dict])
    occupant_densities = calculate_occupant_density(list_uses, internal_loads_df)

    print("Calculating internal loads...")
    new_internal_loads_df = calculate_mixed_loads(properties_df, internal_loads_df, occupant_densities, list_uses,
                                                  use_type_name, list_var_names, list_var_values)
    print("Calculating indoor comfort...")
    new_indoor_comfort_df = calculate_mixed_loads(properties_df, indoor_comfort_df, occupant_densities, list_uses,
                                                  use_type_name, list_var_names, list_var_values)

    prop_df_c = properties_df.copy()
    prop_df_c['name'] = '0'  # Set a `Name` column as index for function to work
    prop_df_c.set_index('name', inplace=True)
    schedule_data_all_uses = ScheduleData(locator)
    internal_loads = internal_loads_df.set_index('code')
    print("Calculating schedules...")
    schedule_new_data, schedule_complementary_data = calc_single_mixed_schedule(list_uses, occupant_densities,
                                                                                prop_df_c, internal_loads, '0',
                                                                                schedule_data_all_uses, list_var_names,
                                                                                list_var_values, use_type_metadata)

    print("Writing to disk...")
    use_type_properties_path = locator.get_database_archetypes_schedules()
    merged_df = pd.merge(new_internal_loads_df, new_indoor_comfort_df, on='code', how="outer")
    merged_df.to_csv(use_type_properties_path, index=False)

    schedule_path = locator.get_database_archetypes_schedules(use_type_name)
    save_cea_schedules(schedule_new_data, schedule_path)


def calculate_mixed_loads(properties_df, loads_df, occupant_densities, list_uses, use_type_name, list_var_names, list_var_values):
    prop_df = properties_df.copy().merge(loads_df, left_on=list_var_names[0], right_on='code')
    loads_df_columns = loads_df.columns
    calculated_loads_df = calculate_average_multiuse(loads_df_columns, prop_df, occupant_densities,
                                                     list_uses, loads_df,
                                                     list_var_names, list_var_values).loc[:, loads_df_columns]
    calculated_loads_df['code'] = use_type_name
    # Remove rows that have the same `code` as new row
    clean_loads_df = loads_df[loads_df['code'] != use_type_name]
    return clean_loads_df.append(calculated_loads_df)


def calculate_occupant_density(use_types, internal_loads_df):
    occupant_densities = {}
    internal_loads = internal_loads_df.copy().set_index('code')
    for use in use_types:
        if internal_loads.loc[use, 'Occ_m2p'] > 0.0:
            occupant_densities[use] = 1.0 / internal_loads.loc[use, 'Occ_m2p']
        else:
            occupant_densities[use] = 0.0
    return occupant_densities


def main(config: cea.config.Configuration):
    # Config Parameters
    use_type_name = config.create_mixed_use_type.use_type
    use_type_metadata = config.create_mixed_use_type.metadata
    use_type_ratios = config.create_mixed_use_type.ratios
    use_type_ratios_dict = {k: float(v) for k, v in [ratio.split('|') for ratio in use_type_ratios]}

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    use_type_properties_df = pd.read_csv(locator.get_database_archetypes_use_type())
    internal_loads_df = use_type_properties_df['code', 'Occ_m2p', 'Qs_Wp', 'X_ghp', 'Ea_Wm2', 'El_Wm2',	'Epro_Wm2',	'Ed_Wm2', 'Vww_ldp', 'Vw_ldp', 'Qcre_Wm2', 'Qhpro_Wm2',	'Qcpro_Wm2', 'Ev_kWveh']
    indoor_comfort_df = use_type_properties_df['code', 'Tcs_set_C', 'Ths_set_C', 'Tcs_setb_C', 'Ths_setb_C', 'Ve_lsp', 'RH_min_pc', 'RH_max_pc']

    assert use_type_name not in internal_loads_df['code'].tolist() and use_type_name not in indoor_comfort_df['code'].tolist(), \
        'Use-type name {} already exists'.format(use_type_name)

    create_mixed_use_type(locator,
                          internal_loads_df=internal_loads_df,
                          indoor_comfort_df=indoor_comfort_df,
                          use_type_name=use_type_name,
                          use_type_metadata=use_type_metadata,
                          use_type_ratios_dict=use_type_ratios_dict)


if __name__ == '__main__':
    main(cea.config.Configuration())

