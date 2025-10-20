#!/usr/bin/env python3
"""
Quick Redis connectivity and functionality check.
"""

import asyncio
import redis.asyncio as redis
from app.core.config import settings


async def check_redis_connection():
    """Check if Redis is accessible and working."""
    print("🔍 Checking Redis Connection")
    print("-" * 30)
    
    try:
        # Try to connect using the configured URL
        redis_client = redis.from_url(settings.REDIS_STATE_STORE_URL, decode_responses=True)
        
        # Test basic operations
        await redis_client.ping()
        print("✅ Redis PING successful")
        
        # Test set/get
        test_key = "test:connection"
        await redis_client.set(test_key, "working", ex=10)  # Expires in 10 seconds
        value = await redis_client.get(test_key)
        print(f"✅ Redis SET/GET successful: {value}")
        
        # Test hash operations (used by state store)
        hash_key = "test:hash"
        await redis_client.hset(hash_key, mapping={"field1": "value1", "field2": "value2"})
        hash_data = await redis_client.hgetall(hash_key)
        print(f"✅ Redis HASH operations successful: {len(hash_data)} fields")
        
        # Test list operations (used for context)
        list_key = "test:list"
        await redis_client.lpush(list_key, "item1", "item2", "item3")
        list_items = await redis_client.lrange(list_key, 0, -1)
        print(f"✅ Redis LIST operations successful: {len(list_items)} items")
        
        # Clean up test keys
        await redis_client.delete(test_key, hash_key, list_key)
        print("✅ Test cleanup successful")
        
        # Close connection
        await redis_client.close()
        print("✅ Redis connection closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running on the configured URL:")
        print(f"   {settings.REDIS_STATE_STORE_URL}")
        return False


async def main():
    """Main function."""
    print("🎯 Redis Connectivity Check")
    print("=" * 40)
    print(f"Redis URL: {settings.REDIS_STATE_STORE_URL}")
    print()
    
    success = await check_redis_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Redis is working correctly!")
        print("The state store should work without issues.")
    else:
        print("⚠️ Redis connection issues detected.")
        print("Please check your Redis installation and configuration.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)