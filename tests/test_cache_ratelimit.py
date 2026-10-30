from shortener.cache import TTLCache
from shortener.ratelimit import RateLimiter


class Clock:
    t = 0.0

    def __call__(self):
        return self.t


def test_cache_hit_miss_and_ttl():
    c = Clock()
    cache = TTLCache(10, ttl=5, clock=c)
    assert cache.get("a") is None
    cache.set("a", 1)
    assert cache.get("a") == 1
    c.t = 5
    assert cache.get("a") is None and len(cache) == 0


def test_cache_lru_eviction():
    cache = TTLCache(2, ttl=100, clock=Clock())
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")  # a is now most recent
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1 and cache.get("c") == 3


def test_cache_invalidate_and_disabled():
    cache = TTLCache(2, ttl=100, clock=Clock())
    cache.set("a", 1)
    cache.invalidate("a")
    cache.invalidate("missing")
    assert cache.get("a") is None
    off = TTLCache(0, ttl=100, clock=Clock())
    off.set("a", 1)
    assert off.get("a") is None


def test_rate_limiter_bucket_and_refill():
    c = Clock()
    rl = RateLimiter(2, clock=c)
    assert rl.allow("ip") and rl.allow("ip")
    assert not rl.allow("ip")
    assert rl.allow("other")
    c.t = 30  # 2/min -> 1 token per 30s
    assert rl.allow("ip")
    assert not rl.allow("ip")


def test_rate_limiter_disabled():
    rl = RateLimiter(0, clock=Clock())
    assert not rl.enabled and all(rl.allow("x") for _ in range(100))
