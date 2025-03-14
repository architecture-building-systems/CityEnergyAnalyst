from fastapi import APIRouter

from cea.glossary import read_glossary_df
from cea.interfaces.dashboard.dependencies import CEAConfig

router = APIRouter()


@router.get('/')
async def get_glossary():
    # TODO: Add plugin support
    glossary = read_glossary_df(plugins=[])
    groups = glossary.groupby('SCRIPT')
    data = []
    for group in groups.groups:
        df = groups.get_group(group)
        result = df[~df.index.duplicated(keep='first')].fillna('-')
        data.append({'script': group if group != '-' else 'inputs', 'variables': result.to_dict(orient='records')})
    return data
