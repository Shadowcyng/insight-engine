import json
from functools import wraps
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from app.core.redis import redis_client
from app.models.user import User
import structlog

log = structlog.get_logger()

def cache_response(ttl_seconds:int = 300):
    """Decorator to cache FastAPI route responses in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            current_user: User = kwargs.get("current_user")

            if not request or not current_user:
                # Fallback: execute normally if dependencies are missing
                return await func(*args, **kwargs)

            # 2. Construct an enterprise-safe, user-isolated key
            # Example: "cache:user_12:/api/v1/uploads"
            cache_key = f"cache:user_{current_user.db_user.id}:{request.url.path}"
            # 3. Cache Read (The Hit)
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                log.info(f"[Cache HIT] Serving from Redis:", key=cache_key)
                return json.loads(cached_data)

            # 4. Cache Miss: Execute the actual database logic
            log.info(f"[Cache MISS] Querying DB for: {cache_key}")
            response_data = await func(*args, **kwargs)
            # 5. Serialize and Save
            json_compatible_data = jsonable_encoder(response_data)
            await redis_client.setex(
                name=cache_key,
                time=ttl_seconds,
                value=json.dumps(json_compatible_data)
            )
            return json_compatible_data
        return wrapper
    return decorator

async def invalidate_user_cache(user_id: int, prefix: str = "/api/v1"):
    """Deletes all cached routes for a specific user to prevent stale data."""
    # SCAN is safer than KEYS in production to avoid blocking the Redis thread
    pattern = f"cache:user_{user_id}:{prefix}*"
    keys_deleted = 0
    
    # scan_iter() automatically manages the cursor under the hood!
    # It acts exactly like a Python generator.
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)
        keys_deleted += 1
        
    if keys_deleted > 0:
        log.info(f"[Cache INVALIDATED] Deleted {keys_deleted} keys for user {user_id}")