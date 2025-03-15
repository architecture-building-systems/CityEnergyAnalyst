import json
import os
from dataclasses import dataclass

from aiocache import caches, Cache, BaseCache
from aiocache.serializers import PickleSerializer
from fastapi import Depends, Request
from typing_extensions import Annotated

import cea.config
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


class CEAServerConfig(cea.config.Configuration):
    def __init__(self, config_file: str = get_settings().config_path):
        if config_file.startswith("~"):
            config_file = os.path.expanduser(config_file)
        super().__init__(config_file)

    def save(self, config_file: str = get_settings().config_path) -> None:
        if config_file.startswith("~"):
            config_file = os.path.expanduser(config_file)
        print(f"Saving config to {config_file}")
        super().save(config_file)


async def get_cea_config(request: Request=None):
    """Get configuration from request headers or query parameters"""

    # Load config from body (priority)
    if request and request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
            if "config" in body:
                return json.loads(body["config"])
        except json.JSONDecodeError:
            pass

    # Read config from file if config_path is set
    if get_settings().config_path:
        cea_config = CEAServerConfig()

        return cea_config
    
    raise ValueError("No config provided")

@dataclass
class ProjectInfo:
    project: str
    scenario: str

async def get_project_info() -> ProjectInfo:
    """Get the current project and scenario in the config"""
    config = await get_cea_config()
    return ProjectInfo(
        project=config.project,
        scenario=config.scenario,
    )


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
CEAProjectInfo = Annotated[dict, Depends(get_project_info)]
CEAPlotCache = Annotated[dict, Depends(get_plot_cache)]
CEAWorkerProcesses = Annotated[dict, Depends(get_worker_processes)]
CEAServerUrl = Annotated[dict, Depends(get_server_url)]
CEAProjectRoot = Annotated[dict, Depends(get_project_root)]
CEAServerSettings = Annotated[dict, Depends(get_settings)]
