# ============================================================
# 🐋 ORCA — In-Memory Sliding Window Rate Limiter
# api/rate_limiter.py
# ============================================================
# Limits requests per IP per endpoint.
# Sliding window: only counts requests in the last N seconds.
# Fails open — if something breaks, users are NOT blocked.
# ============================================================

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from fastapi import Request, HTTPException


@dataclass
class RateLimitConfig:
    max_requests : int   # max calls allowed
    window_secs  : int   # rolling window in seconds


# Per-endpoint limits
LIMITS: dict[str, RateLimitConfig] = {
    "/chat"    : RateLimitConfig(max_requests=20, window_secs=60),
    "/evaluate": RateLimitConfig(max_requests=10, window_secs=60),
}

# In-memory store: { "endpoint:ip" -> deque of timestamps }
_buckets: dict[str, deque] = defaultdict(deque)


def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For for proxied deploys."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, endpoint: str) -> None:
    """
    Enforce rate limit for the given endpoint.
    Raises HTTP 429 if the client is over the limit.
    Fails open on any unexpected error.

    Args:
        request  : FastAPI Request (used to extract client IP)
        endpoint : endpoint key matching LIMITS dict (e.g. "/chat")
    """
    try:
        config = LIMITS.get(endpoint)
        if config is None:
            return  # no limit configured for this endpoint

        ip  = get_client_ip(request)
        key = f"{endpoint}:{ip}"
        now = time.monotonic()
        cutoff = now - config.window_secs

        bucket = _buckets[key]

        # Prune timestamps outside the window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= config.max_requests:
            raise HTTPException(
                status_code=429,
                detail={
                    "error"      : "rate_limit_exceeded",
                    "message"    : f"Too many requests. Max {config.max_requests} per {config.window_secs}s.",
                    "retry_after": config.window_secs,
                },
                headers={"Retry-After": str(config.window_secs)},
            )

        bucket.append(now)

    except HTTPException:
        raise  # re-raise 429s — don't swallow them
    except Exception:
        return  # fail open — never block users due to limiter bugs


def clear_buckets() -> None:
    """Reset all rate limit state. Used in tests."""
    _buckets.clear()
