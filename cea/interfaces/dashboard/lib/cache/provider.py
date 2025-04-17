from aiocache import caches

from cea.interfaces.dashboard.lib.cache.base import AsyncDictCache
from cea.interfaces.dashboard.lib.cache.settings import CACHE_NAME


def get_cache():
    """Get the cache instance with the default name."""
    return caches.get(CACHE_NAME)


async def get_dict_cache(key: str) -> AsyncDictCache:
    """Get or create a dictionary cache for a specific key."""
    _cache = get_cache()
    cache_data = await _cache.get(key)

    if cache_data is None:
        cache_data = dict()
        await _cache.set(key, cache_data)
        logger.debug(f"Created new cache for key: {key}")

    return AsyncDictCache(_cache, key)