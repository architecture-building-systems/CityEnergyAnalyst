import asyncio

from aiocache import caches, Cache
from aiocache.serializers import PickleSerializer
from fastapi import Depends
from typing_extensions import Annotated

import cea.config
from cea.plots.cache import PlotCache

CACHE_NAME = 'default'
caches.set_config({
    CACHE_NAME: {
        'cache': Cache.MEMORY,
        'serializer': {
            'class': PickleSerializer
        }
    }
})


class JobStoreCache:
    def __init__(self, cache, key):
        self._loop = asyncio.get_event_loop()
        self._cache = cache
        self._key = key

    async def get(self, job_id):
        jobs = await self._cache.get(self._key)

        if jobs is None:
            jobs = {}

        return jobs[job_id]

    async def set(self, job_id, value):
        jobs = await self._cache.get(self._key)

        if jobs is None:
            jobs = {}

        jobs[job_id] = value
        await self._cache.set(self._key, jobs)

        return value

    async def values(self):
        jobs = await self._cache.get(self._key)
        return jobs.values()

    async def keys(self):
        jobs = await self._cache.get(self._key)
        return jobs.keys()


async def get_cea_config():
    _cache = caches.get(CACHE_NAME)
    cea_config = await _cache.get("cea_config")

    if cea_config is None:
        cea_config = cea.config.Configuration()
        await _cache.set("cea_config", cea_config)

    return cea_config


async def save_cea_config():
    async def fn(config):
        _cache = caches.get(CACHE_NAME)
        await _cache.set("cea_config", config)
    return fn


async def get_plot_cache():
    cea_config = await get_cea_config()
    _plot_cache = PlotCache(cea_config.project)

    return _plot_cache


async def get_jobs():
    _cache = caches.get(CACHE_NAME)
    jobs = await _cache.get("jobs")

    if jobs is None:
        jobs = dict()
        await _cache.set("jobs", jobs)

    return JobStoreCache(_cache, "jobs")


CEAConfig = Annotated[dict, Depends(get_cea_config)]
CEAConfigSaveFunc = Annotated[dict, Depends(save_cea_config)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAJobs = Annotated[dict, Depends(get_jobs)]
