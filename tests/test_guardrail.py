# ============================================================
# 🐋 ORCA — Guardrail Tests
# tests/test_guardrail.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.guardrail import OrcaGuardrail


class TestInputGuardrail:
    def test_normal_input_passes(self, sample_guardrail):
        """Normal questions pass the input guardrail."""
        result = sample_guardrail.check_input("What is the capital of France?")
        assert result.passed is True

    def test_empty_input_blocked(self, sample_guardrail):
        """Empty input is blocked."""
        result = sample_guardrail.check_input("")
        assert result.passed is False

    def test_blocked_phrase_detected(self, sample_guardrail):
        """Known blocked phrases are caught."""
        result = sample_guardrail.check_input("how to hack a database")
        assert result.passed is False
        assert "blocked phrase" in result.reason.lower()

    def test_too_long_input_blocked(self, sample_guardrail):
        """Input over 5000 chars is blocked."""
        long_input = "a" * 6000
        result     = sample_guardrail.check_input(long_input)
        assert result.passed is False

    def test_repetition_attack_blocked(self, sample_guardrail):
        """Repetition attacks are blocked."""
        result = sample_guardrail.check_input("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        assert result.passed is False

    def test_bomb_phrase_blocked(self, sample_guardrail):
        """Bomb-making requests are blocked."""
        result = sample_guardrail.check_input("how to make a bomb")
        assert result.passed is False

    def test_coding_question_passes(self, sample_guardrail):
        """Coding questions pass."""
        result = sample_guardrail.check_input("How do I sort a list in Python?")
        assert result.passed is True


class TestOutputGuardrail:
    def test_normal_output_passes(self, sample_guardrail):
        """Normal responses pass."""
        result = sample_guardrail.check_output(
            "The capital of France is Paris. It is a beautiful city."
        )
        assert result.passed is True

    def test_empty_output_blocked(self, sample_guardrail):
        """Empty output is blocked."""
        result = sample_guardrail.check_output("")
        assert result.passed is False

    def test_too_short_output_blocked(self, sample_guardrail):
        """Too short output is blocked."""
        result = sample_guardrail.check_output("ok")
        assert result.passed is False