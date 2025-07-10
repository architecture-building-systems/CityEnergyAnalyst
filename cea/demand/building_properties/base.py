"""
Base class for building properties with common database merge functionality
"""
from __future__ import annotations
import pandas as pd

from typing import TYPE_CHECKING, Dict, List, Tuple, Callable, Optional

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingPropertiesDatabase:
    """
    Base class for building properties that provides common database merge functionality.
    """

    @staticmethod
    def merge_database_properties(
        building_properties: pd.DataFrame,
        db_mappings: Dict[str, Tuple[Callable, str, Optional[Dict[str, str]], List[str]]],
    ) -> pd.DataFrame:
        """
        Common method to merge building properties with database properties.
        
        :param building_properties: DataFrame with building properties to merge
        :param db_mappings: Dictionary mapping component types to (locator_method, join_column, column_renames, fields_to_extract)
        :return: Concatenated DataFrame with all merged properties
        """
        merged_dfs = []
        
        for component_type, mapping in db_mappings.items():
            if len(mapping) == 3:
                locator_method, join_column, fields = mapping
                column_renames = None
            else:
                locator_method, join_column, column_renames, fields = mapping
                
            # Read database and merge
            prop_data = pd.read_csv(locator_method())
            merged_df = (building_properties.reset_index()
                        .merge(prop_data, left_on=join_column, right_on='code', how='left')
                        .set_index('name'))
            
            # Apply column renames if specified
            if column_renames:
                merged_df.rename(columns=column_renames, inplace=True)
            
            # Validate merge, ensure there are no empty values
            print(f"Checking building {component_type} properties...")
            invalid_buildings = merged_df.loc[merged_df['code'].isna()]
            if len(invalid_buildings) > 0:
                raise ValueError(
                    f'WARNING: Invalid {component_type} type found in building {component_type} properties.'
                    f'Check the building properties for: {list(invalid_buildings.index)}.')

            merged_dfs.append(merged_df[fields])
        
        # Return concatenated or merged result
        if len(merged_dfs) == 1:
            return merged_dfs[0]
        
        # For envelope properties, concatenate columns
        if 'name' not in merged_dfs[0].columns:
            return pd.concat(merged_dfs, axis=1)
        
        # For HVAC/supply properties, merge on 'name'
        result = merged_dfs[0]
        for df in merged_dfs[1:]:
            result = result.merge(df, on='name')
        return result
