from aiocache import caches, Cache, BaseCache
from aiocache.serializers import PickleSerializer
from fastapi import Depends
from typing_extensions import Annotated

import cea.config
from cea.config import CEA_CONFIG
from cea.interfaces.dashboard.settings import get_settings
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


class CEAConfigCache(cea.config.Configuration):
    _cache = caches.get(CACHE_NAME)
    _cache_key = "cea_config"

    def __init__(self, config_file: str = CEA_CONFIG):
        super().__init__(config_file)

    async def save(self, config_file: str = CEA_CONFIG) -> None:
        """
        Write to cache as well when saving to file
        """
        await self._cache.set(self._cache_key, self)
        super().save(config_file)


class AsyncDictCache:
    def __init__(self, cache: BaseCache, cache_key: str):
        self._cache = cache
        self._cache_key = cache_key

    async def get(self, item_id):
        _dict = await self._cache.get(self._cache_key, dict())
        return _dict[item_id]

    async def set(self, item_id, value):
        _dict = await self._cache.get(self._cache_key, dict())
        _dict[item_id] = value
        await self._cache.set(self._cache_key, _dict)

        return value

    async def delete(self, item_id):
        _dict = await self._cache.get(self._cache_key, dict())
        del _dict[item_id]
        await self._cache.set(self._cache_key, _dict)

    async def values(self):
        _dict = await self._cache.get(self._cache_key)
        return _dict.values()

    async def keys(self):
        _dict = await self._cache.get(self._cache_key)
        return _dict.keys()


async def get_cea_config():
    _cache = caches.get(CACHE_NAME)
    cea_config = await _cache.get("cea_config")

    if cea_config is None:
        cea_config = CEAConfigCache()
        await _cache.set("cea_config", cea_config)

    return cea_config


async def get_plot_cache():
    cea_config = await get_cea_config()
    _plot_cache = PlotCache(cea_config.project)

    return _plot_cache

    


async def get_worker_processes():
    _cache = caches.get(CACHE_NAME)
    worker_processes = await _cache.get("worker_processes")

    if worker_processes is None:
        worker_processes = dict()
        await _cache.set("worker_processes", worker_processes)

    return AsyncDictCache(_cache, "worker_processes")


def get_server_url():
    host = get_settings().host
    port = get_settings().port
    worker_url = f"http://{host}:{port}/server"
    return worker_url


def get_project_root():
    return get_settings().project_root


CEAConfig = Annotated[dict, Depends(get_cea_config)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAWorkerProcesses = Annotated[dict, Depends(get_worker_processes)]
CEAServerUrl = Annotated[dict, Depends(get_server_url)]
CEAProjectRoot = Annotated[dict, Depends(get_project_root)]
CEAServerSettings = Annotated[dict, Depends(get_settings)]
