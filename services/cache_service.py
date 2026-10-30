from cachetools import TTLCache
from config import settings

_cache = TTLCache(maxsize=128, ttl=max(30, settings.cache_ttl_seconds))


def cache_get(key: str):
    return _cache.get(key)


def cache_set(key: str, value):
    _cache[key] = value
