from typing import Tuple

from aiocache import SimpleMemoryCache, RedisCache
from aiocache.serializers import PickleSerializer

from cea.interfaces.dashboard.lib.cache.base import AsyncDictCache
from cea.interfaces.dashboard.lib.cache.settings import CACHE_NAME, cache_settings
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-cache")

_cache_instance = None


def parse_connection_string(connection_string: str) -> Tuple[str, str]:
    """Parse a connection string and extract authentication information"""
    # Parse connection string if it contains authentication info
    endpoint = connection_string
    username = None
    password = None
    
    # Check if the host contains authentication information
    if '@' in endpoint:
        auth_part, endpoint = endpoint.rsplit('@', 1)
        if ':' in auth_part:
            username, password = auth_part.split(':', 1)
    
    return endpoint, username, password


def get_cache():
    """Gets the singleton cache instance, initializing it on first call."""
    global _cache_instance

    if _cache_instance is not None:
        return _cache_instance

    if cache_settings.host and cache_settings.port:
        endpoint, username, password = parse_connection_string(cache_settings.host)
        redis_args = {
            'serializer': PickleSerializer(),
            'namespace': CACHE_NAME,
            'endpoint': endpoint,
            'port': int(cache_settings.port)
        }
        
        if username and password:
            redis_args['username'] = username
            redis_args['password'] = password
        
        _cache_instance = RedisCache(**redis_args)
        logger.info(f"Using RedisCache: {CACHE_NAME} [{cache_settings.host}:{cache_settings.port}]")
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

# Initialise cache object
get_cache()
