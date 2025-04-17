from aiocache import caches, Cache
from aiocache.serializers import PickleSerializer

CACHE_NAME = 'cea-cache'
CONFIG_CACHE_TTL = 300

caches.set_config({
    CACHE_NAME: {
        'cache': Cache.MEMORY,
        'serializer': {
            'class': PickleSerializer
        }
    }
})
