from aiocache import BaseCache
from typing import Optional


class AsyncDictCache:
    def __init__(self, cache: BaseCache, cache_key: str, default_ttl: Optional[int] = None):
        """
        Args:
            cache: The underlying cache instance
            cache_key: The key used to store the dictionary in the cache
            default_ttl: Default TTL in seconds for cache entries. None means no expiration.
        """
        self._cache = cache
        self._cache_key = cache_key
        self._default_ttl = default_ttl

    async def get(self, item_id, default=None):
        # Try to get the entire dictionary from cache
        _dict: dict = await self._cache.get(self._cache_key)
        # If dictionary doesn't exist yet, return default
        if _dict is None:
            return default
        # Otherwise return the requested item or default
        return _dict.get(item_id, default)

    async def pop(self, item_id, default=None):
        value = await self.get(item_id, default)
        try:
            await self.delete(item_id)
        except KeyError:
            pass
        return value

    async def set(self, item_id, value, ttl: Optional[int] = None):
        """
        Set an item in the cache dictionary.

        Args:
            item_id: The key for the item
            value: The value to store
            ttl: Optional TTL in seconds. If None, uses default_ttl. If both None, no expiration.

        Note:
            This operation is NOT atomic. Concurrent writes to different items in the same
            cache key can cause lost updates (read-modify-write race condition). In practice,
            this is rarely an issue since each item_id is typically written by a single source.
            For truly concurrent scenarios, consider using per-item cache keys or distributed locking.
        """
        # Read-modify-write pattern (not atomic across concurrent operations)
        _dict = await self._cache.get(self._cache_key)
        if _dict is None:
            _dict = {}
        _dict[item_id] = value

        # Use provided TTL, fall back to default, or no expiration
        effective_ttl = ttl if ttl is not None else self._default_ttl

        if effective_ttl is not None:
            await self._cache.set(self._cache_key, _dict, ttl=effective_ttl)
        else:
            await self._cache.set(self._cache_key, _dict)

        return value

    async def delete(self, item_id):
        _dict = await self._cache.get(self._cache_key)
        if _dict is None:
            raise KeyError(f"Cache key '{self._cache_key}' not found")
        if item_id not in _dict:
            raise KeyError(f"Item '{item_id}' not found in cache")
        del _dict[item_id]

        # Preserve TTL to prevent memory leak
        if self._default_ttl is not None:
            await self._cache.set(self._cache_key, _dict, ttl=self._default_ttl)
        else:
            await self._cache.set(self._cache_key, _dict)

    async def values(self):
        _dict = await self._cache.get(self._cache_key)
        if _dict is None:
            return []
        return _dict.values()

    async def keys(self):
        _dict = await self._cache.get(self._cache_key)
        if _dict is None:
            return []
        return _dict.keys()
