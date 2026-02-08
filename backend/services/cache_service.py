"""
Redis cache service for performance optimization
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
from core.config import settings

class CacheService:
    """Redis cache service"""
    
    def __init__(self):
        self.redis_client = None
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception:
            # Fallback to in-memory cache if Redis not available
            self.redis_client = InMemoryCache()
            
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client and hasattr(self.redis_client, 'close'):
            await self.redis_client.close()
            
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        try:
            return await self.redis_client.get(key)
        except Exception:
            return None
            
    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set value in cache"""
        if not self.redis_client:
            return
        try:
            if ttl:
                await self.redis_client.setex(key, ttl, value)
            else:
                await self.redis_client.set(key, value)
        except Exception:
            pass
            
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            return
        try:
            await self.redis_client.delete(key)
        except Exception:
            pass
            
    async def health_check(self) -> bool:
        """Check cache health"""
        try:
            if self.redis_client:
                if hasattr(self.redis_client, 'ping'):
                    await self.redis_client.ping()
                return True
        except Exception:
            pass
        return False

class InMemoryCache:
    """Fallback in-memory cache"""
    
    def __init__(self):
        self.cache = {}
        
    async def get(self, key: str) -> Optional[str]:
        return self.cache.get(key)
        
    async def set(self, key: str, value: str):
        self.cache[key] = value
        
    async def setex(self, key: str, ttl: int, value: str):
        # Simplified - doesn't actually expire
        self.cache[key] = value
        
    async def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]