import redis.asyncio as aioredis
import json

redis_client = aioredis.Redis(host='redis', port=6379, db=0)

async def cache_task(task):
    await redis_client.set(task['id'], json.dumps(task), ex=3600)  # Cache for 1 hour

async def get_cached_task(task_id):
    cached_task = await redis_client.get(task_id)
    if cached_task:
        return json.loads(cached_task)  # Returns a dict if task is found
    return None
