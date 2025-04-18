from aiocache import SimpleMemoryCache, RedisCache
from aiocache.serializers import PickleSerializer

from cea.interfaces.dashboard.lib.cache.base import AsyncDictCache
from cea.interfaces.dashboard.lib.cache.settings import CACHE_NAME, CacheSettings
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-cache")

_cache_instance = None


def get_cache():
    """Gets the singleton cache instance, initializing it on first call."""
    global _cache_instance

    if _cache_instance is not None:
        return _cache_instance

    settings = CacheSettings()
    if settings.host and settings.port:
        _cache_instance = RedisCache(serializer=PickleSerializer(), namespace=CACHE_NAME,
                                     endpoint=settings.host, port=settings.port)
        logger.info(f"Using RedisCache: {CACHE_NAME} [{settings.host}:{settings.port}]")
    else:
        _cache_instance = SimpleMemoryCache(serializer=PickleSerializer(), namespace=CACHE_NAME)
        logger.info(f"Using SimpleMemoryCache: {CACHE_NAME}")

    return _cache_instance


async def get_dict_cache(key: str) -> AsyncDictCache:
    """Get or create a dictionary cache for a specific key."""
    _cache = get_cache()
    cache_data = await _cache.get(key)

    if cache_data is None:
        cache_data = dict()
        await _cache.set(key, cache_data)
        logger.debug(f"Created new cache for key: {key}")

    return AsyncDictCache(_cache, key)
