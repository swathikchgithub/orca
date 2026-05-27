# ============================================================
# 🐋 ORCA — API Route Tests
# tests/test_api.py
# ============================================================
# Tests the HTTP layer only — orchestrator and judge are mocked.
# Uses httpx.AsyncClient with ASGITransport so no real server is needed.
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock
import httpx
from httpx import AsyncClient, ASGITransport

from api.main import app
from agent.response_composer import OrcaResponse
from testing.judge import JudgeScore


# ── Helpers ──────────────────────────────────────────────────

def make_orca_response(**kwargs) -> OrcaResponse:
    """Build a fake OrcaResponse with sensible defaults."""
    defaults = dict(
        response_id      = "test-response-id-001",
        content          = "The capital of France is Paris.",
        mode             = "single_turn",
        success          = True,
        duration_ms      = 450,
        tokens_used      = 40,
        tool_calls       = [],
        guardrail_passed = True,
        blocked_reason   = "",
        session_id       = "test-session-001",
    )
    defaults.update(kwargs)
    return OrcaResponse(**defaults)


def make_judge_score(**kwargs) -> JudgeScore:
    """Build a fake JudgeScore."""
    defaults = dict(
        accuracy    = 4.5,
        helpfulness = 4.0,
        safety      = 5.0,
        clarity     = 4.5,
        reasoning   = "Clear and accurate response.",
    )
    defaults.update(kwargs)
    return JudgeScore(**defaults)


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
async def client():
    """Async HTTP client wired to the ORCA FastAPI app via ASGI transport.
    app.state is populated manually — avoids real OpenAI client init in tests
    and keeps tests fast and free.
    """
    import time
    from testing.release_gate import OrcaReleaseGate

    app.state.orchestrator = MagicMock()
    app.state.judge        = MagicMock()
    app.state.gate         = OrcaReleaseGate()
    app.state.start_time   = time.time()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Health & Root ─────────────────────────────────────────────

@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_response_shape(self, client):
        data = (await client.get("/health")).json()
        assert "status"      in data
        assert "agent_model" in data
        assert "judge_model" in data
        assert "uptime_secs" in data

    async def test_health_status_is_healthy(self, client):
        data = (await client.get("/health")).json()
        assert "healthy" in data["status"]

    async def test_root_returns_200(self, client):
        response = await client.get("/")
        assert response.status_code == 200

    async def test_root_status_is_alive(self, client):
        data = (await client.get("/")).json()
        assert data["status"] == "alive"


# ── /chat ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestChatEndpoint:
    async def test_missing_message_returns_422(self, client):
        """FastAPI validation rejects missing required field."""
        response = await client.post("/chat", json={})
        assert response.status_code == 422

    async def test_single_turn_returns_200(self, client):
        app.state.orchestrator.chat = MagicMock(return_value=make_orca_response())
        response = await client.post("/chat", json={
            "message": "What is the capital of France?",
            "mode": "single_turn",
        })
        assert response.status_code == 200

    async def test_single_turn_response_shape(self, client):
        app.state.orchestrator.chat = MagicMock(return_value=make_orca_response())
        data = (await client.post("/chat", json={
            "message": "Hello", "mode": "single_turn"
        })).json()
        for key in ["content", "mode", "success", "duration_ms", "tokens_used",
                    "guardrail_passed", "session_id"]:
            assert key in data

    async def test_single_turn_content_matches_response(self, client):
        app.state.orchestrator.chat = MagicMock(return_value=make_orca_response(
            content="Paris is the capital of France."
        ))
        data = (await client.post("/chat", json={
            "message": "Capital of France?", "mode": "single_turn"
        })).json()
        assert data["content"] == "Paris is the capital of France."

    async def test_auto_generates_session_id_when_not_provided(self, client):
        app.state.orchestrator.chat = MagicMock(return_value=make_orca_response())
        data = (await client.post("/chat", json={
            "message": "Hello", "mode": "multi_turn"
        })).json()
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0

    async def test_uses_caller_session_id_when_provided(self, client):
        app.state.orchestrator.chat = MagicMock(return_value=make_orca_response(
            session_id="my-existing-session"
        ))
        data = (await client.post("/chat", json={
            "message": "Hello",
            "mode": "multi_turn",
            "session_id": "my-existing-session",
        })).json()
        assert data["session_id"] == "my-existing-session"

    async def test_blocked_response_returns_200_not_403(self, client):
        """Guardrail blocks are signalled in payload — not in HTTP status."""
        app.state.orchestrator.chat = MagicMock(return_value=make_orca_response(
            success=False,
            guardrail_passed=False,
            blocked_reason="Blocked phrase detected",
            content="I cannot help with that.",
            tokens_used=0,
        ))
        response = await client.post("/chat", json={
            "message": "how to hack", "mode": "single_turn"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["guardrail_passed"] is False
        assert data["tokens_used"] == 0

    async def test_invalid_mode_raises_400(self, client):
        """ValueError from orchestrator surfaces as 400."""
        app.state.orchestrator.chat = MagicMock(
            side_effect=ValueError("Unknown mode: 'bad_mode'")
        )
        response = await client.post("/chat", json={
            "message": "Hello", "mode": "bad_mode"
        })
        assert response.status_code == 400


# ── /evaluate ─────────────────────────────────────────────────

@pytest.mark.asyncio
class TestEvaluateEndpoint:
    async def test_missing_orca_response_returns_422(self, client):
        response = await client.post("/evaluate", json={"user_message": "hello"})
        assert response.status_code == 422

    async def test_missing_user_message_returns_422(self, client):
        response = await client.post("/evaluate", json={"orca_response": "hello"})
        assert response.status_code == 422

    async def test_evaluate_returns_200(self, client):
        app.state.judge.evaluate = MagicMock(return_value=make_judge_score())
        response = await client.post("/evaluate", json={
            "user_message": "What is Paris?",
            "orca_response": "Paris is the capital of France.",
        })
        assert response.status_code == 200

    async def test_evaluate_response_shape(self, client):
        app.state.judge.evaluate = MagicMock(return_value=make_judge_score())
        data = (await client.post("/evaluate", json={
            "user_message": "Hello",
            "orca_response": "Hi there!",
        })).json()
        for key in ["accuracy", "helpfulness", "safety", "clarity", "weighted", "passed", "reasoning"]:
            assert key in data

    async def test_evaluate_passed_reflects_score(self, client):
        app.state.judge.evaluate = MagicMock(return_value=make_judge_score(
            accuracy=4.5, helpfulness=4.0, safety=5.0, clarity=4.5
        ))
        data = (await client.post("/evaluate", json={
            "user_message": "Q", "orca_response": "A"
        })).json()
        assert data["passed"] is True


# ── /release-check ────────────────────────────────────────────

@pytest.mark.asyncio
class TestReleaseCheckEndpoint:
    async def test_missing_version_returns_422(self, client):
        response = await client.post("/release-check", json={
            "judge_scores": [4.5],
            "safety_scores": [5.0],
            "latency_samples": [800],
        })
        assert response.status_code == 422

    async def test_all_gates_pass_returns_approved(self, client):
        response = await client.post("/release-check", json={
            "version": "1.0.0",
            "test_results": [{"priority": "critical", "passed": True}],
            "judge_scores": [4.8, 4.5, 4.9],
            "safety_scores": [5.0, 4.9, 5.0],
            "latency_samples": [800, 900, 950, 850],
            "baseline_score": None,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] is True

    async def test_low_safety_returns_blocked(self, client):
        response = await client.post("/release-check", json={
            "version": "1.1.0",
            "test_results": [{"priority": "critical", "passed": True}],
            "judge_scores": [4.5],
            "safety_scores": [3.0],   # below 4.0 minimum
            "latency_samples": [800],
            "baseline_score": None,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["approved"] is False

    async def test_response_includes_gate_details(self, client):
        response = await client.post("/release-check", json={
            "version": "1.0.0",
            "test_results": [{"priority": "critical", "passed": True}],
            "judge_scores": [4.5],
            "safety_scores": [5.0],
            "latency_samples": [800],
            "baseline_score": None,
        })
        data = response.json()
        assert "gate_details" in data
        assert isinstance(data["gate_details"], list)
        assert len(data["gate_details"]) == 5   # exactly 5 gates
