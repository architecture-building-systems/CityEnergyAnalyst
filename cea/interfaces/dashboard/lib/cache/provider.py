from typing import Tuple, Optional

from aiocache import SimpleMemoryCache, RedisCache
from aiocache.serializers import PickleSerializer

from cea.interfaces.dashboard.lib.cache.base import AsyncDictCache
from cea.interfaces.dashboard.lib.cache.settings import CACHE_NAME, cache_settings
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-cache")

_cache_instance = None


def parse_connection_string(connection_string: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Parse a connection string and extract authentication information"""
    # Parse connection string if it contains authentication info
    host = connection_string
    username = None
    password = None
    
    # Check if the host contains authentication information
    if '@' in host:
        auth_part, host = host.rsplit('@', 1)
        if ':' in auth_part:
            username, password = auth_part.split(':', 1)
    
    return host, username, password


def get_cache():
    """Gets the singleton cache instance, initializing it on first call."""
    global _cache_instance

    if _cache_instance is not None:
        return _cache_instance

    if cache_settings.host and cache_settings.port:
        host, username, password = parse_connection_string(cache_settings.host)
        port = int(cache_settings.port)

        redis_args = {
            'endpoint': host,
            'port': port
        }
        
        if username and password:
            # Not supported in aiocache 0.12.3
            # redis_args['username'] = username
            redis_args['password'] = password

        _cache_instance = RedisCache(serializer=PickleSerializer(), namespace=CACHE_NAME, **redis_args)
        logger.info(f"Using RedisCache: {CACHE_NAME} [{host}:{port}]")
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


async def cleanup_cache_connections():
    """Clean up cache connections on application shutdown."""
    global _cache_instance
    if _cache_instance is not None:
        try:
            # Close cache connections - different methods for different cache types
            if hasattr(_cache_instance, 'close'):
                await _cache_instance.close()
                logger.info("Closed cache connections")
            else:
                logger.info("Cache cleanup not required for this cache type")
        except Exception as e:
            logger.error(f"Error closing cache connections: {e}")
        finally:
            _cache_instance = None

# Initialise cache object
get_cache()
