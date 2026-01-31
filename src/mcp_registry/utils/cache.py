"""Redis cache implementation."""

import json
from typing import Any, Optional
from functools import wraps
import hashlib

import redis.asyncio as redis
from mcp_registry.config import get_settings

settings = get_settings()

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            str(settings.redis_url),
            max_connections=settings.redis_pool_size,
            decode_responses=True
        )
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = await get_redis()
    value = await r.get(key)
    if value:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache with TTL."""
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))


async def cache_delete(key: str) -> None:
    """Delete key from cache."""
    r = await get_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete keys matching pattern."""
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


class RateLimiter:
    """Redis-based sliding window rate limiter."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> redis.Redis:
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis
    
    async def is_allowed(
        self, 
        key: str, 
        max_requests: int, 
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.
        Returns (allowed, remaining_requests).
        """
        r = await self._get_redis()
        now = int(__import__('time').time())
        window_start = now - window_seconds
        
        # Remove old entries
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current entries
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        current_count = results[1]
        
        if current_count > max_requests:
            # Remove the request we just added (over limit)
            await r.zrem(key, str(now))
            return False, 0
        
        remaining = max_requests - current_count
        return True, remaining
