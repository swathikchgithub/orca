# ============================================================
# 🐋 ORCA — Assertion Engine Tests
# tests/test_assertions.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing.assertion_engine import OrcaAssertionEngine


class TestAssertionEngine:
    def test_keyword_found(self, sample_engine):
        """Keyword assertion passes when word is present."""
        results = sample_engine.run(
            response_text = "The capital of France is Paris.",
            assertions    = [{"type": "contains_keyword", "value": "Paris"}]
        )
        assert results[0].passed is True

    def test_keyword_not_found(self, sample_engine):
        """Keyword assertion fails when word is missing."""
        results = sample_engine.run(
            response_text = "The capital of France is Paris.",
            assertions    = [{"type": "contains_keyword", "value": "London"}]
        )
        assert results[0].passed is False

    def test_keyword_case_insensitive(self, sample_engine):
        """Keyword check is case insensitive by default."""
        results = sample_engine.run(
            response_text = "The answer is PARIS.",
            assertions    = [{"type": "contains_keyword", "value": "paris"}]
        )
        assert results[0].passed is True

    def test_is_blocked_pass(self, sample_engine):
        """is_blocked passes when response is correctly blocked."""
        results = sample_engine.run(
            response_text = "I cannot help with that.",
            assertions    = [{"type": "is_blocked", "value": True}],
            is_blocked    = True
        )
        assert results[0].passed is True

    def test_is_blocked_fail(self, sample_engine):
        """is_blocked fails when response should be blocked but isn't."""
        results = sample_engine.run(
            response_text = "Here is how to hack...",
            assertions    = [{"type": "is_blocked", "value": True}],
            is_blocked    = False
        )
        assert results[0].passed is False

    def test_bullet_count_exact(self, sample_engine):
        """Bullet count passes with exact match."""
        results = sample_engine.run(
            response_text = "Items:\n- One\n- Two\n- Three",
            assertions    = [{"type": "bullet_count", "value": 3}]
        )
        assert results[0].passed is True

    def test_bullet_count_wrong(self, sample_engine):
        """Bullet count fails with wrong count."""
        results = sample_engine.run(
            response_text = "Items:\n- One\n- Two",
            assertions    = [{"type": "bullet_count", "value": 3}]
        )
        assert results[0].passed is False

    def test_word_count_under_limit(self, sample_engine):
        """Word count passes when under limit."""
        results = sample_engine.run(
            response_text = "Short answer.",
            assertions    = [{"type": "word_count_max", "value": 80}]
        )
        assert results[0].passed is True

    def test_word_count_over_limit(self, sample_engine):
        """Word count fails when over limit."""
        long_text = " ".join(["word"] * 100)
        results   = sample_engine.run(
            response_text = long_text,
            assertions    = [{"type": "word_count_max", "value": 80}]
        )
        assert results[0].passed is False

    def test_tool_was_used_pass(self, sample_engine):
        """Tool check passes when tool was used."""
        results = sample_engine.run(
            response_text = "The tip is $7.13",
            assertions    = [{"type": "tool_was_used", "value": "calculator_tool"}],
            tools_used    = ["calculator_tool"]
        )
        assert results[0].passed is True

    def test_tool_was_used_fail(self, sample_engine):
        """Tool check fails when tool was not used."""
        results = sample_engine.run(
            response_text = "The tip is $7.13",
            assertions    = [{"type": "tool_was_used", "value": "calculator_tool"}],
            tools_used    = []
        )
        assert results[0].passed is False

    def test_response_not_empty_pass(self, sample_engine):
        """Not empty check passes for real content."""
        results = sample_engine.run(
            response_text = "Hello I am ORCA!",
            assertions    = [{"type": "response_not_empty"}]
        )
        assert results[0].passed is True

    def test_response_not_empty_fail(self, sample_engine):
        """Not empty check fails for blank response."""
        results = sample_engine.run(
            response_text = "   ",
            assertions    = [{"type": "response_not_empty"}]
        )
        assert results[0].passed is False

    def test_summary_calculation(self, sample_engine):
        """Summary correctly counts pass and fail."""
        results = sample_engine.run(
            response_text = "Paris is the capital.",
            assertions    = [
                {"type": "contains_keyword", "value": "Paris"},   # pass
                {"type": "contains_keyword", "value": "London"},  # fail
            ]
        )
        summary = sample_engine.summary(results)
        assert summary["total"]   == 2
        assert summary["passed"]  == 1
        assert summary["failed"]  == 1
        assert summary["pass_pct"] == 50.0