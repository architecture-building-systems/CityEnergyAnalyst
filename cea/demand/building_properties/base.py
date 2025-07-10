"""
Base class for building properties with common database merge functionality
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Optional

import pandas as pd


class BuildingPropertiesDatabase:
    """
    Base class for building properties that provides common database merge functionality.
    """

    @staticmethod
    def map_database_properties(
            building_properties: pd.DataFrame,
            db_mappings: Dict[str, Tuple[str, str, Optional[Dict[str, str]], List[str]]],
    ) -> pd.DataFrame:
        """
        Common method to merge building properties with database properties.
        
        :param building_properties: DataFrame with building properties to merge
        :param db_mappings: Dictionary mapping component types to (file_path, join_column, column_renames, fields_to_extract)
        :return: Concatenated DataFrame with all merged properties
        """
        merged_dfs = [building_properties]
        errors = []

        for component_type, mapping in db_mappings.items():
            file_path, join_column, column_renames, fields = mapping

            # Read database and merge
            prop_data = pd.read_csv(file_path)
            merged_df = (building_properties[[join_column]].reset_index()
                         .merge(prop_data, left_on=join_column, right_on='code', how='left')
                         .set_index('name'))

            # Apply column renames if specified
            if column_renames:
                merged_df.rename(columns=column_renames, inplace=True)

            # Validate merge, ensure there are no empty values
            print(f"Checking building {component_type} properties...")
            invalid_buildings = merged_df.loc[merged_df['code'].isna()]
            if len(invalid_buildings) > 0:
                errors.append({
                    "component_type": component_type,
                    "invalid_column": join_column,
                    "invalid_values": invalid_buildings[join_column].tolist(),
                    "invalid_buildings": invalid_buildings.index.tolist(),
                })

            merged_dfs.append(merged_df[fields])

        if errors:
            errors = [f"Invalid codes {error['invalid_values']} "
                      f"found in building property '{error['invalid_column']}' "
                      f"for buildings: {error['invalid_buildings']}"
                      for error in errors]
            errors += ["Please check the respective values in building properties."]
            raise ValueError("Errors found in building properties\n\n" + "\n".join(errors))

        return pd.concat(merged_dfs, axis=1)
