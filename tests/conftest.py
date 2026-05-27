# ============================================================
# 🐋 ORCA — Pytest Configuration & Shared Fixtures
# tests/conftest.py
# ============================================================

import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Shared Fixtures ──────────────────────────────────────────

@pytest.fixture
def sample_memory():
    """Fresh memory instance for each test."""
    from agent.memory import ConversationMemory
    return ConversationMemory(system_prompt="You are ORCA, a helpful assistant.")


@pytest.fixture
def sample_guardrail():
    """Fresh guardrail instance for each test."""
    from agent.guardrail import OrcaGuardrail
    return OrcaGuardrail()


@pytest.fixture
def sample_engine():
    """Fresh assertion engine for each test."""
    from testing.assertion_engine import OrcaAssertionEngine
    return OrcaAssertionEngine()


@pytest.fixture
def sample_registry():
    """Fresh scenario registry for each test."""
    from testing.scenario_registry import OrcaScenarioRegistry
    return OrcaScenarioRegistry()


@pytest.fixture
def sample_gate():
    """Fresh release gate for each test."""
    from testing.release_gate import OrcaReleaseGate
    return OrcaReleaseGate()


@pytest.fixture
def good_test_results():
    """Sample passing test results."""
    return [
        {"priority": "critical", "passed": True},
        {"priority": "critical", "passed": True},
        {"priority": "high",     "passed": True},
    ]


@pytest.fixture
def good_judge_scores():
    return [4.8, 4.5, 4.9, 4.7]


@pytest.fixture
def good_safety_scores():
    return [5.0, 4.8, 5.0, 4.9]


@pytest.fixture
def good_latency_samples():
    return [800, 900, 950, 850, 1000, 780, 920, 880, 950, 810]


@pytest.fixture
def sample_router():
    """Fresh tool router for each test."""
    from agent.tool_router import OrcaToolRouter
    return OrcaToolRouter()


@pytest.fixture
def sample_composer():
    """Fresh response composer for each test."""
    from agent.response_composer import OrcaResponseComposer
    return OrcaResponseComposer()