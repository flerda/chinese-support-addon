def Empty(size):
  return [[], size]


def CacheContains(cache, key):
  for k, _ in cache[0]:
    if key == k:
      return True
  return False


def CacheGet(cache, key):
  for k, v in cache[0]:
    if key == k:
      cache[0].remove((k, v))
      cache[0].insert(0, (k, v))
      return v
  return None


def CachePut(cache, key, value):
  if len(cache[0]) >= cache[1]:
    cache[0].pop()
  cache[0].insert(0, (key, value))


def caching(cache):
  def decorator(fn):
    def new(*args, **kwargs):
      key = (args, tuple(kwargs.items()))
      if CacheContains(cache, key):
        return CacheGet(cache, key)
      else:
        value = fn(*args, **kwargs)
        CachePut(cache, key, value)
        return value
    return new
  return decorator
