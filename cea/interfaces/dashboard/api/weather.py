from fastapi import APIRouter

from cea.databases import get_weather_files

router = APIRouter()


@router.get('')
async def get_weather():
    return {'weather': get_weather_files()}
