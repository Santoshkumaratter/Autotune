import asyncio
import aioredis

async def initialize_redis_pool():
    global REDIS_POOL
    REDIS_POOL = await aioredis.create_redis_pool("redis://localhost", decode_responses=True)

def startup_event():
    asyncio.get_event_loop().run_until_complete(initialize_redis_pool())