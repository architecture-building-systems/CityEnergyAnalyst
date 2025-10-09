"""
Base class for building properties with common database merge functionality
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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
        field_defaults: Optional mapping of field names to default values for missing/legacy fields
                       (e.g., {"shading_location": "interior", "shading_setpoint_wm2": 300})

                       NOTE: This is a temporary solution. Long-term, defaults should be defined
                       in schemas.yml as the single source of truth. See migration plan in docs.

    Raises:
        ValueError: If column_renames targets are not in fields, or field_defaults keys are not in fields
    """
    file_path: str
    join_column: str
    fields: List[str]
    column_renames: Optional[Dict[str, str]] = None
    field_defaults: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """
        Validate that column_renames and field_defaults reference fields that exist in the fields list.
        """
        # Validate column_renames: all target names (values) must be in fields
        if self.column_renames:
            renamed_fields = set(self.column_renames.values())
            fields_set = set(self.fields)
            invalid_renames = renamed_fields - fields_set

            if invalid_renames:
                raise ValueError(
                    f"Invalid column_renames for '{self.join_column}': "
                    f"Renamed columns {invalid_renames} are not in fields list {self.fields}. "
                    f"All renamed column names must appear in the 'fields' list."
                )

        # Validate field_defaults: all keys must be in fields
        if self.field_defaults:
            default_fields = set(self.field_defaults.keys())
            fields_set = set(self.fields)
            invalid_defaults = default_fields - fields_set

            if invalid_defaults:
                raise ValueError(
                    f"Invalid field_defaults for '{self.join_column}': "
                    f"Default fields {invalid_defaults} are not in fields list {self.fields}. "
                    f"All fields with defaults must appear in the 'fields' list."
                )


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
            if column_renames:
                merged_df.rename(columns=column_renames, inplace=True)

            # Apply field defaults for missing columns (handles legacy databases)
            if mapping.field_defaults:
                for field_name, default_value in mapping.field_defaults.items():
                    if field_name not in merged_df.columns:
                        print(f"  → Adding missing field '{field_name}' with default value: {default_value}")
                        merged_df[field_name] = default_value

            # Validate that all required fields exist before slicing
            missing_fields = set(fields) - set(merged_df.columns)
            if missing_fields:
                available_columns = sorted(merged_df.columns.tolist())
                raise ValueError(
                    f"Missing required fields in database '{file_path}' for component '{component_type}':\n"
                    f"  Missing fields: {sorted(missing_fields)}\n"
                    f"  Required fields: {sorted(fields)}\n"
                    f"  Available columns in database: {available_columns}\n\n"
                    f"Possible causes:\n"
                    f"  1. Fields are misspelled in the DatabaseMapping configuration\n"
                    f"  2. Database file is missing expected columns\n"
                    f"  3. column_renames may have incorrect mappings\n"
                    f"  4. Legacy database needs field_defaults for missing columns"
                )

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
