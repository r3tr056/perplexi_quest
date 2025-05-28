import time
from typing import Dict
import redis.asyncio as redis
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:

    def __init__(self):
        self.redis_client = None
        self.local_cache = {}
        
    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Redis rate limiter initialized successfully")
        except Exception as e:
            logger.warning(f"Redis unavailable, using local cache: {str(e)}")
            self.redis_client = None

    async def check_rate_limit(
        self, 
        identifier: str, 
        max_attempts: int, 
        window_minutes: int = 60,
        namespace: str = "rate_limit"
    ) -> bool:
        if not settings.RATE_LIMIT_ENABLED:
            return True
        
        key = f"{namespace}:{identifier}"
        window_seconds = window_minutes * 60
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        try:
            if self.redis_client:
                return await self._redis_rate_limit(key, max_attempts, window_start, current_time)
            else:
                return await self._local_rate_limit(key, max_attempts, window_start, current_time)
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True

    async def _redis_rate_limit(self, key: str, max_attempts: int, window_start: int, current_time: int) -> bool:
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, 3600)
        results = await pipe.execute()
        current_count = results[1]
        return current_count < max_attempts

    async def _local_rate_limit(self, key: str, max_attempts: int, window_start: int, current_time: int) -> bool:

        if key not in self.local_cache:
            self.local_cache[key] = []
        self.local_cache[key] = [
            timestamp for timestamp in self.local_cache[key] 
            if timestamp > window_start
        ]
        current_count = len(self.local_cache[key])
        if current_count < max_attempts:
            self.local_cache[key].append(current_time)
            return True
        return False

    async def get_rate_limit_info(
        self, 
        identifier: str, 
        max_attempts: int, 
        window_minutes: int = 60,
        namespace: str = "rate_limit"
    ) -> Dict[str, int]:

        key = f"{namespace}:{identifier}"
        window_seconds = window_minutes * 60
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        try:
            if self.redis_client:
                await self.redis_client.zremrangebyscore(key, 0, window_start)

                current_count = await self.redis_client.zcard(key)
                oldest_entries = await self.redis_client.zrange(key, 0, 0, withscores=True)
                reset_time = int(oldest_entries[0][1]) + window_seconds if oldest_entries else current_time + window_seconds
                
            else:
                if key not in self.local_cache:
                    self.local_cache[key] = []
                self.local_cache[key] = [
                    timestamp for timestamp in self.local_cache[key] 
                    if timestamp > window_start
                ]
                current_count = len(self.local_cache[key])
                reset_time = min(self.local_cache[key]) + window_seconds if self.local_cache[key] else current_time + window_seconds
            
            return {
                "limit": max_attempts,
                "remaining": max(0, max_attempts - current_count),
                "used": current_count,
                "reset_time": reset_time,
                "window_minutes": window_minutes
            }
        
        except Exception as e:
            logger.error(f"Rate limit info error: {str(e)}")
            return {
                "limit": max_attempts,
                "remaining": max_attempts,
                "used": 0,
                "reset_time": current_time + (window_minutes * 60),
                "window_minutes": window_minutes
            }

    async def reset_rate_limit(self, identifier: str, namespace: str = "rate_limit"):

        key = f"{namespace}:{identifier}"
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.local_cache.pop(key, None)
            logger.info(f"Rate limit reset for {identifier}")
        except Exception as e:
            logger.error(f"Rate limit reset error: {str(e)}")

rate_limiter = RateLimiter()