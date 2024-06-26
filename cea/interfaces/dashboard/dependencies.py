
from aiocache import caches, Cache
from aiocache.serializers import PickleSerializer
from fastapi import Depends
from typing_extensions import Annotated

import cea.config
from cea.plots.cache import MemoryPlotCache

CACHE_NAME = 'default'
caches.set_config({
    CACHE_NAME: {
        'cache': Cache.MEMORY,
        'serializer': {
            'class': PickleSerializer
        }
    }
})


async def get_cea_config():
    _cache = caches.get(CACHE_NAME)
    cea_config = await _cache.get("cea_config")

    if cea_config is None:
        cea_config = cea.config.Configuration()
        await _cache.set("cea_config", cea_config)

    return cea_config


async def get_plot_cache():
    _cache = caches.get(CACHE_NAME)
    plot_cache = await _cache.get("plot_cache")

    if plot_cache is None:
        cea_config = await get_cea_config()
        plot_cache = MemoryPlotCache(cea_config.project)
        await _cache.set("plot_cache", plot_cache)

    return plot_cache


async def get_jobs():
    _cache = caches.get(CACHE_NAME)
    jobs = await _cache.get("jobs")

    if jobs is None:
        jobs = dict()
        await _cache.set("jobs", jobs)

    print(jobs)
    return jobs


CEAConfig = Annotated[dict, Depends(get_cea_config)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAJobs = Annotated[dict, Depends(get_jobs)]
