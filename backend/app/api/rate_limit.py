import time
import uuid
from typing import Callable, Optional
from fastapi import HTTPException, Request, Response, Depends, status
from app.core.redis import redis_client
import structlog

log = structlog.get_logger()

class RateLimiter:
    """
    IP-based Sliding Window Rate Limiter using Redis Pipelines.

    Supports IP-based rate limiting strategies:
    - Per-IP: f"rate_limit:ip:{client_ip}" (default)
    - Per-endpoint per-IP: f"rate_limit:endpoint_ip:{path}:{client_ip}"
    - Custom: Provide your own key_func
    """

    RATE_LIMIT_STRATEGIES = {
        "per_ip": lambda req: f"rate_limit:ip:{req.client.host}",
        "endpoint_per_ip": lambda req: f"rate_limit:endpoint_ip:{req.url.path}:{req.client.host}",
    }

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        key_strategy: str = "per_ip",
        key_func: Optional[Callable[[Request], str]] = None
    ):
        """
        Initialize the RateLimiter.

        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
            key_strategy: Built-in strategy name (per_ip, endpoint_per_ip)
                          Ignored if key_func is provided
            key_func: Custom function(request) -> key_string
                      Takes precedence over key_strategy
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # Use custom key function if provided, otherwise use built-in strategy
        if key_func:
            self.key_func = key_func
        elif key_strategy in self.RATE_LIMIT_STRATEGIES:
            self.key_func = self.RATE_LIMIT_STRATEGIES[key_strategy]
        else:
            raise ValueError(f"Unknown strategy: {key_strategy}. Available: {list(self.RATE_LIMIT_STRATEGIES.keys())}")

        self.key_strategy = key_strategy if not key_func else "custom"
        log.info("rate_limiter_initialized", max_requests=max_requests, window_seconds=window_seconds, strategy=self.key_strategy)

    async def __call__(
        self,
        request: Request,
        response: Response
    ):
        """
        Rate limiting logic using IP-based keys only.
        """
        # Generate the rate limit key using the configured strategy
        key = self.key_func(request)
        log.debug("rate_limit_key_generated", key=key, strategy=self.key_strategy)

        now = time.time()
        # We need a highly unique member name in case two requests hit at the exact same microsecond
        member = f"{now}:{uuid.uuid4().hex}"
        log.debug("sliding_window_member_created", member=member, current_time=now)
        
        # 2. Use a Redis Pipeline to execute all commands atomically.
        # This prevents Race Conditions if the user fires 10 concurrent async requests.
        async with redis_client.pipeline(transaction=True) as pipe:
            # Step A: Drop all timestamps older than our sliding window
            pipe.zremrangebyscore(key, 0, now - self.window_seconds)
            # Step B: Count how many requests are currently in the valid window
            pipe.zcard(key)

            # Step C: Add the current request's timestamp
            pipe.zadd(key, {member: now})

            # Step D: Update the key's TTL so Redis automatically deletes it if the user goes dormant (memory management)
            pipe.expire(key, self.window_seconds)

            # Execute the pipeline
            log.debug("executing_rate_limit_pipeline", key=key)
            results = await pipe.execute()

        # results[1] maps to Step B (zcard)
        current_request_count = results[1]
        log.debug("current_request_count", count=current_request_count, max_requests=self.max_requests)

        # 3. Calculate remaining quota for standard HTTP Headers
        remaining = max(0, self.max_requests - current_request_count - 1)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Strategy"] = self.key_strategy
        log.debug("rate_limit_headers_set", limit=self.max_requests, remaining=remaining, strategy=self.key_strategy)

        # 4. Enforce the limit
        if current_request_count >= self.max_requests:
            log.warning("rate_limit_exceeded", key=key, current_count=current_request_count, max_requests=self.max_requests, window_seconds=self.window_seconds)
            # Proper HTTP 429 Too Many Requests response
            response.headers["Retry-After"] = str(self.window_seconds)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({self.max_requests} requests per {self.window_seconds}s). Please try again later."
            )

        log.info("rate_limit_check_passed", key=key, remaining=remaining)
        return True