"""
Base class for building properties with common database merge functionality
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class DatabaseMapping:
    """
    Configuration for mapping database properties to building properties.

    Attributes:
        file_path: Path to the database CSV file
        join_column: Column name in building properties to join on (matches 'code' in database)
        fields: List of field names to extract from the database
        column_renames: Optional mapping to rename columns from database (e.g., {"feedstock": "source_hs"})
    """
    file_path: str
    join_column: str
    fields: List[str]
    column_renames: Optional[Dict[str, str]] = None


class BuildingPropertiesDatabase:
    """
    Base class for building properties that provides common database merge functionality.
    """

    @staticmethod
    def map_database_properties(
            building_properties: pd.DataFrame,
            db_mappings: Dict[str, DatabaseMapping],
    ) -> pd.DataFrame:
        """
        Common method to merge building properties with database properties.

        :param building_properties: DataFrame with building properties to merge
        :param db_mappings: Dictionary mapping component types to DatabaseMapping objects
        :return: Concatenated DataFrame with all merged properties
        """
        merged_dfs = [building_properties]
        errors = []

        for component_type, mapping in db_mappings.items():
            file_path = mapping.file_path
            join_column = mapping.join_column
            column_renames = mapping.column_renames
            fields = mapping.fields

            # Read database and merge
            prop_data = pd.read_csv(file_path)

            # Validate join_column values before merging
            print(f"Checking building {component_type} properties...")
            join_column_values = set(building_properties[join_column].unique())
            code_column_values = set(prop_data['code'].unique())
            invalid_values = list(join_column_values - code_column_values)
            if len(invalid_values) > 0:
                errors.append({
                    "component_type": component_type,
                    "invalid_column": join_column,
                    "invalid_values": invalid_values,
                    "invalid_buildings": building_properties[
                        building_properties[join_column].isin(invalid_values)].index.tolist(),
                })
                continue

            merged_df = (building_properties[[join_column]].reset_index()
                         .merge(prop_data, left_on=join_column, right_on='code', how='left')
                         .set_index('name'))

            # Apply column renames if specified
            # Apply column renames if specified
            if column_renames:
                merged_df.rename(columns=column_renames, inplace=True)
            
            if join_column == 'type_shade':
                # legacy condition for missing shading_location and shading_setpoint_wm2 of shading assembly in older projects
                # added 2025 Oct 09
                if 'shading_location' not in merged_df.columns:
                    merged_df['shading_location'] = 'interior'
                if 'shading_setpoint_wm2' not in merged_df.columns:
                    merged_df['shading_setpoint_wm2'] = 300
            
            properties = merged_df[fields]
            merged_dfs.append(properties)

        if errors:
            errors = [f"Invalid code {error['invalid_values']} "
                      f"found in buildings: {error['invalid_buildings']} "
                      f"for building property '{error['invalid_column']}' "
                      for error in errors]
            errors += [
                "Please check the respective values in building properties or add the missing entries to the database."]
            raise ValueError("Errors found in building properties\n\n" + "\n".join(errors))

        return pd.concat(merged_dfs, axis=1)
