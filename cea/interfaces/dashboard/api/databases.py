import json
import os
import shutil
import tempfile
from typing import Optional, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

import cea.inputlocator
from cea.databases import get_regions
from cea.datamanagement.format_helper.cea4_verify_db import cea4_verify_db
from cea.interfaces.dashboard.utils import secure_path
from cea.utilities.schedule_reader import schedule_to_dataframe

router = APIRouter()

DATABASES_SCHEMA_KEYS = {
    "CONSTRUCTION_STANDARD": ["get_database_construction_standards"],
    "USE_TYPES": ["get_database_standard_schedules_use", "get_database_use_types_properties"],
    "SUPPLY": ["get_database_supply_assemblies"],
    "HVAC": ["get_database_air_conditioning_systems"],
    "ENVELOPE": ["get_database_envelope_systems"],
    "CONVERSION": ["get_database_conversion_systems"],
    "DISTRIBUTION": ["get_database_distribution_systems"],
    "FEEDSTOCKS": ["get_database_feedstocks"],
}


def database_to_dict(db_path):
    out = dict()
    xls = pd.ExcelFile(db_path)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet, keep_default_na=False)
        out[sheet] = df.to_dict(orient='records')
    return out


def schedule_to_dict(schedule_path):
    out = dict()
    schedule_df = schedule_to_dataframe(schedule_path)
    for df_name, df in schedule_df.items():
        out[df_name] = df.to_dict(orient='records')
    return out


@router.get("/region")
async def get_database_regions():
    return {'regions': get_regions()}


def convert_path_to_name(schema_dict):
    locator = cea.inputlocator.InputLocator('')
    for sheet_name, sheet_info in schema_dict.items():
        for variable_name, schema in sheet_info['columns'].items():
            if 'choice' in schema and 'lookup' in schema['choice']:
                database_path = locator.__getattribute__(schema['choice']['lookup']['path'])()
                schema['choice']['lookup']['database_category'] = os.path.basename(os.path.dirname(database_path))
                schema['choice']['lookup']['database_name'] = os.path.basename(os.path.splitext(database_path)[0])
    return schema_dict


@router.get("/schema")
async def get_database_schema():
    import cea.schemas

    schemas = cea.schemas.schemas(plugins=[])
    out = {}
    for db_name, db_schema_keys in DATABASES_SCHEMA_KEYS.items():
        out[db_name] = {}
        for db_schema_key in db_schema_keys:
            try:
                out[db_name].update(convert_path_to_name(schemas[db_schema_key]['schema']))
            except KeyError as ex:
                raise KeyError(f"Could not convert_path_to_name for {db_name}/{db_schema_key}. {ex}")
    return out


class ValidateDatabase(BaseModel):
    type: Literal['path', 'file']
    path: Optional[str] = None
    file: Optional[str] = None


@router.post("/validate")
async def validate_database(data: ValidateDatabase):
    """Validate the given databases (only checks if the folder structure is correct)"""
    if data.type == 'path':
        if data.path is None:
            raise HTTPException(status_code=400, detail="Missing path")

        database_path = secure_path(data.path)
        try:
            # FIXME: Update verify_database_template to be able to verify databases from a path
            with tempfile.TemporaryDirectory() as tmpdir:
                scenario = os.path.join(tmpdir, "scenario")
                temp_db_path = os.path.join(scenario, "inputs", "database")
                os.makedirs(temp_db_path, exist_ok=True)

                # Copy the databases to the temporary directory
                shutil.copytree(database_path, temp_db_path, dirs_exist_ok=True)

                try:
                    dict_missing_db = cea4_verify_db(scenario, verbose=True)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=str(e),
                    )

            if dict_missing_db:
                errors = {db: missing_files for db, missing_files in dict_missing_db.items() if missing_files}

                if errors:
                    # FIXME: do not raise errors for now, remove once database is updated
                    print(json.dumps(errors))

                    # raise HTTPException(
                    #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    #     detail=json.dumps(errors),
                    # )

        except IOError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Uncaught exception: {str(e)}",
            )

        return {}
    return {}
