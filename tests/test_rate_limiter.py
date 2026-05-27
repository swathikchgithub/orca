# ============================================================
# 🐋 ORCA — Rate Limiter Tests
# tests/test_rate_limiter.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock
from fastapi import HTTPException

from api.rate_limiter import check_rate_limit, clear_buckets, RateLimitConfig, LIMITS


def make_request(ip: str = "1.2.3.4") -> MagicMock:
    """Build a fake FastAPI Request with a given IP."""
    req = MagicMock()
    req.headers = {}
    req.client.host = ip
    return req


@pytest.fixture(autouse=True)
def reset_buckets():
    """Clear rate limit state before every test — tests must be independent."""
    clear_buckets()
    yield
    clear_buckets()


class TestRateLimiterConfig:
    def test_chat_limit_is_configured(self):
        assert "/chat" in LIMITS
        assert LIMITS["/chat"].max_requests > 0
        assert LIMITS["/chat"].window_secs > 0

    def test_evaluate_limit_is_configured(self):
        assert "/evaluate" in LIMITS
        assert LIMITS["/evaluate"].max_requests > 0

    def test_chat_allows_more_than_evaluate(self):
        """Chat should have a higher limit than the expensive evaluate endpoint."""
        assert LIMITS["/chat"].max_requests > LIMITS["/evaluate"].max_requests


class TestRateLimiterAllows:
    def test_first_request_always_passes(self):
        """First request from any IP always passes."""
        check_rate_limit(make_request("10.0.0.1"), "/chat")  # should not raise

    def test_requests_under_limit_pass(self):
        """All requests below the limit pass without error."""
        limit = LIMITS["/chat"].max_requests
        req = make_request("10.0.0.2")
        for _ in range(limit - 1):
            check_rate_limit(req, "/chat")  # none should raise

    def test_unknown_endpoint_passes(self):
        """Endpoints without a configured limit are not blocked."""
        check_rate_limit(make_request(), "/health")  # no limit for /health

    def test_different_ips_are_independent(self):
        """Hitting the limit on one IP does not block another IP."""
        limit = LIMITS["/chat"].max_requests
        req_a = make_request("10.0.0.10")
        req_b = make_request("10.0.0.11")

        # Exhaust IP A's limit
        for _ in range(limit):
            check_rate_limit(req_a, "/chat")

        # IP B should still pass
        check_rate_limit(req_b, "/chat")  # should not raise


class TestRateLimiterBlocks:
    def test_exceeding_limit_raises_429(self):
        """One request over the limit raises HTTP 429."""
        limit = LIMITS["/chat"].max_requests
        req = make_request("10.0.0.20")

        for _ in range(limit):
            check_rate_limit(req, "/chat")

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(req, "/chat")

        assert exc_info.value.status_code == 429

    def test_429_detail_contains_retry_after(self):
        """Rate limit error detail includes retry guidance."""
        limit = LIMITS["/chat"].max_requests
        req = make_request("10.0.0.21")

        for _ in range(limit):
            check_rate_limit(req, "/chat")

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(req, "/chat")

        assert exc_info.value.headers.get("Retry-After") is not None

    def test_evaluate_blocked_at_its_own_limit(self):
        """Evaluate endpoint enforces its own (lower) limit."""
        limit = LIMITS["/evaluate"].max_requests
        req = make_request("10.0.0.22")

        for _ in range(limit):
            check_rate_limit(req, "/evaluate")

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(req, "/evaluate")

        assert exc_info.value.status_code == 429


class TestRateLimiterForwardedFor:
    def test_x_forwarded_for_header_used(self):
        """Rate limiting keys on the forwarded IP, not the proxy IP."""
        req = MagicMock()
        req.headers = {"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}
        req.client.host = "10.0.0.1"   # proxy IP

        limit = LIMITS["/chat"].max_requests

        # Exhaust limit on the real client IP (203.0.113.5)
        for _ in range(limit):
            check_rate_limit(req, "/chat")

        with pytest.raises(HTTPException):
            check_rate_limit(req, "/chat")

        # A different real IP through the same proxy should still pass
        req2 = MagicMock()
        req2.headers = {"X-Forwarded-For": "203.0.113.99, 10.0.0.1"}
        req2.client.host = "10.0.0.1"
        check_rate_limit(req2, "/chat")  # should not raise
