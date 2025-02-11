import os
from typing import Optional, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

import cea.inputlocator
from cea.databases import get_regions, get_database_tree, databases_folder_path
from cea.interfaces.dashboard.dependencies import CEAConfig
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


def read_all_databases(database_path):
    out = dict()
    db_info = get_database_tree(database_path)
    for category in db_info['categories'].keys():
        out[category] = dict()
        for db_name in db_info['categories'][category]['databases']:
            db_files = db_info['databases'][db_name]['files']
            if db_name == 'USE_TYPES':
                out[category][db_name] = dict()
                out[category][db_name]['SCHEDULES'] = dict()
                for db_file in db_files:
                    # Use type property file
                    if db_file['name'] == 'USE_TYPE_PROPERTIES':
                        out[category][db_name]['USE_TYPE_PROPERTIES'] = database_to_dict(db_file['path'])
                    # Schedule files
                    elif db_file['extension'] == '.csv':
                        out[category][db_name]['SCHEDULES'][db_file['name']] = schedule_to_dict(db_file['path'])
            else:
                for db_file in db_files:
                    out[category][db_name] = database_to_dict(db_file['path'])
    return out


@router.get("/region")
async def get_database_regions():
    return {'regions': get_regions()}


@router.get("/region/{region}")
async def get_database_region(region: str):
    regions = get_regions()
    if region not in regions:
        _regions = ", ".join(regions)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find '{region}' region. Try instead {_regions}",
        )
    return {"categories": get_database_tree(os.path.join(databases_folder_path, region))['categories']}


@router.get("/region/{region}/databases")
async def get_database_region_data(region: str):
    regions = get_regions()
    if region not in regions:
        _regions = ", ".join(regions)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find '{region}' region. Try instead {_regions}",
        )

    db_path = os.path.normpath(os.path.join(databases_folder_path, region))
    if not db_path.startswith(databases_folder_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid database region.",
        )

    try:
        return read_all_databases(db_path)
    except IOError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


def convert_path_to_name(schema_dict):
    import cea.inputlocator
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
async def validate_database(config: CEAConfig, data: ValidateDatabase):
    """Validate the given databases (only checks if the folder structure is correct)"""
    if data.type == 'path':
        if data.path is None:
            raise HTTPException(status_code=400, detail="Missing path")

        # Override the locator to use path of database
        class DummyInputLocator(cea.inputlocator.InputLocator):
            def get_databases_folder(self):
                return data.path

        try:
            DummyInputLocator(config.scenario).verify_database_template()
        except IOError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        return {}
    return {}

