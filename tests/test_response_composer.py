# ============================================================
# 🐋 ORCA — Response Composer Tests
# tests/test_response_composer.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.response_composer import OrcaResponseComposer, OrcaResponse
from agent.tool_router import ToolCall


class TestComposeSuccess:
    def test_returns_orca_response_type(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn")
        assert isinstance(r, OrcaResponse)

    def test_content_is_stripped(self, sample_composer):
        r = sample_composer.compose(content="  Paris.  ", mode="single_turn")
        assert r.content == "Paris."

    def test_success_is_true(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn")
        assert r.success is True

    def test_guardrail_passed_is_true(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn")
        assert r.guardrail_passed is True

    def test_is_blocked_is_false(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn")
        assert r.is_blocked is False

    def test_tokens_used_preserved(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn", tokens_used=100)
        assert r.tokens_used == 100

    def test_estimates_tokens_when_zero(self, sample_composer):
        """If tokens_used=0, composer estimates from content length."""
        r = sample_composer.compose(content="Hello world", mode="single_turn", tokens_used=0)
        assert r.tokens_used > 0

    def test_session_id_stored(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn", session_id="sess-42")
        assert r.session_id == "sess-42"

    def test_tool_calls_stored(self, sample_composer):
        fake_call = ToolCall(tool_name="calculator_tool", input_data={"expression": "2+2"}, output="4.0", success=True)
        r = sample_composer.compose(content="Hello", mode="agentic", tool_calls=[fake_call])
        assert len(r.tool_calls) == 1

    def test_unique_response_ids(self, sample_composer):
        """Every compose call must produce a different response_id."""
        r1 = sample_composer.compose(content="A", mode="single_turn")
        r2 = sample_composer.compose(content="B", mode="single_turn")
        assert r1.response_id != r2.response_id

    def test_cost_estimate_positive_for_real_tokens(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn", tokens_used=1000)
        assert r.cost_estimate_usd > 0

    def test_to_dict_has_required_keys(self, sample_composer):
        r = sample_composer.compose(content="Hello", mode="single_turn")
        d = r.to_dict()
        for key in ["response_id", "content", "mode", "success", "duration_ms", "tokens_used"]:
            assert key in d


class TestComposeBlocked:
    def test_success_is_false(self, sample_composer):
        r = sample_composer.compose_blocked(
            reason="Blocked phrase", safe_msg="I can't help.", mode="single_turn"
        )
        assert r.success is False

    def test_guardrail_passed_is_false(self, sample_composer):
        r = sample_composer.compose_blocked(
            reason="Blocked phrase", safe_msg="I can't help.", mode="single_turn"
        )
        assert r.guardrail_passed is False

    def test_is_blocked_is_true(self, sample_composer):
        r = sample_composer.compose_blocked(
            reason="Blocked phrase", safe_msg="I can't help.", mode="single_turn"
        )
        assert r.is_blocked is True

    def test_tokens_used_is_zero(self, sample_composer):
        """Blocked before LLM call — costs $0."""
        r = sample_composer.compose_blocked(
            reason="Blocked phrase", safe_msg="I can't help.", mode="single_turn"
        )
        assert r.tokens_used == 0

    def test_safe_msg_is_content(self, sample_composer):
        r = sample_composer.compose_blocked(
            reason="Blocked phrase", safe_msg="I can't help with that.", mode="single_turn"
        )
        assert r.content == "I can't help with that."

    def test_blocked_reason_stored(self, sample_composer):
        r = sample_composer.compose_blocked(
            reason="Contains bomb instructions", safe_msg="No.", mode="single_turn"
        )
        assert r.blocked_reason == "Contains bomb instructions"


class TestComposeError:
    def test_success_is_false(self, sample_composer):
        r = sample_composer.compose_error(error_msg="API timeout", mode="single_turn")
        assert r.success is False

    def test_guardrail_passed_is_true(self, sample_composer):
        """System error is not a safety violation."""
        r = sample_composer.compose_error(error_msg="API timeout", mode="single_turn")
        assert r.guardrail_passed is True

    def test_tokens_used_is_zero(self, sample_composer):
        r = sample_composer.compose_error(error_msg="API timeout", mode="single_turn")
        assert r.tokens_used == 0

    def test_content_is_user_safe_message(self, sample_composer):
        r = sample_composer.compose_error(error_msg="Internal crash details", mode="single_turn")
        # Must not leak internal error details to the user
        assert "Internal crash details" not in r.content
