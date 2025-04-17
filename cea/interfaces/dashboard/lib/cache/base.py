from aiocache import BaseCache


class AsyncDictCache:
    def __init__(self, cache: BaseCache, cache_key: str):
        self._cache = cache
        self._cache_key = cache_key

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

    async def set(self, item_id, value):
        # Atomic update pattern to prevent race conditions
        _dict = await self._cache.get(self._cache_key)
        if _dict is None:
            _dict = {}
        _dict[item_id] = value
        await self._cache.set(self._cache_key, _dict)
        return value

    async def delete(self, item_id):
        _dict = await self._cache.get(self._cache_key)
        if _dict is None:
            raise KeyError(f"Cache key '{self._cache_key}' not found")
        if item_id not in _dict:
            raise KeyError(f"Item '{item_id}' not found in cache")
        del _dict[item_id]
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
