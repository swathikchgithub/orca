# ============================================================
# 🐋 ORCA — Release Gate Tests
# tests/test_release_gate.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing.release_gate import OrcaReleaseGate


class TestReleaseGate:
    def test_perfect_release_approved(
        self,
        sample_gate,
        good_test_results,
        good_judge_scores,
        good_safety_scores,
        good_latency_samples
    ):
        """Perfect metrics get release approved."""
        decision = sample_gate.evaluate(
            version         = "1.0.0",
            test_results    = good_test_results,
            judge_scores    = good_judge_scores,
            safety_scores   = good_safety_scores,
            latency_samples = good_latency_samples,
            baseline_score  = None
        )
        assert decision.approved  is True
        assert decision.passed_gates == 5

    def test_safety_failure_blocks_release(self, sample_gate):
        """Low safety score blocks release."""
        decision = sample_gate.evaluate(
            version         = "1.1.0",
            test_results    = [{"priority": "critical", "passed": True}],
            judge_scores    = [4.5, 4.3],
            safety_scores   = [3.5, 3.2],   # ❌ below 4.0!
            latency_samples = [900, 950],
            baseline_score  = None
        )
        assert decision.approved is False
        failed_names = [g.gate_name for g in decision.failed_gates]
        assert "3_SAFETY_SCORE" in failed_names

    def test_critical_test_failure_blocks_release(self, sample_gate):
        """Failed critical test blocks release."""
        decision = sample_gate.evaluate(
            version         = "1.2.0",
            test_results    = [
                {"priority": "critical", "passed": True},
                {"priority": "critical", "passed": False},  # ❌ failed!
            ],
            judge_scores    = [4.5, 4.3],
            safety_scores   = [5.0, 4.8],
            latency_samples = [900, 950],
            baseline_score  = None
        )
        assert decision.approved is False
        failed_names = [g.gate_name for g in decision.failed_gates]
        assert "1_CRITICAL_TESTS" in failed_names

    def test_latency_failure_blocks_release(self, sample_gate):
        """High latency blocks release."""
        decision = sample_gate.evaluate(
            version         = "1.3.0",
            test_results    = [{"priority": "critical", "passed": True}],
            judge_scores    = [4.5, 4.6],
            safety_scores   = [5.0, 4.8],
            latency_samples = [4000, 5000, 6000],  # ❌ too slow!
            baseline_score  = None
        )
        assert decision.approved is False
        failed_names = [g.gate_name for g in decision.failed_gates]
        assert "4_LATENCY_SLA" in failed_names

    def test_regression_failure_blocks_release(self, sample_gate):
        """Big quality drop blocks release."""
        decision = sample_gate.evaluate(
            version         = "1.4.0",
            test_results    = [{"priority": "critical", "passed": True}],
            judge_scores    = [3.2, 3.1],    # dropped from 4.5!
            safety_scores   = [4.5, 4.8],
            latency_samples = [900, 950],
            baseline_score  = 4.5            # ❌ dropped > 5%!
        )
        assert decision.approved is False
        failed_names = [g.gate_name for g in decision.failed_gates]
        assert "5_REGRESSION" in failed_names

    def test_judge_score_below_threshold_blocks(self, sample_gate):
        """Judge score below 3.5 blocks release."""
        decision = sample_gate.evaluate(
            version         = "1.5.0",
            test_results    = [{"priority": "critical", "passed": True}],
            judge_scores    = [3.0, 2.9, 3.1],  # ❌ below 3.5!
            safety_scores   = [4.5, 4.8, 4.6],
            latency_samples = [900, 950, 880],
            baseline_score  = None
        )
        assert decision.approved is False
        failed_names = [g.gate_name for g in decision.failed_gates]
        assert "2_JUDGE_SCORE" in failed_names

    def test_first_release_skips_regression(self, sample_gate):
        """First release with no baseline skips regression gate."""
        decision = sample_gate.evaluate(
            version         = "1.0.0",
            test_results    = [{"priority": "critical", "passed": True}],
            judge_scores    = [4.5],
            safety_scores   = [5.0],
            latency_samples = [900],
            baseline_score  = None   # no baseline!
        )
        # regression gate should pass (non-critical skip)
        regression_gate = next(
            g for g in decision.gates if g.gate_name == "5_REGRESSION"
        )
        assert regression_gate.passed is True

    def test_failed_gates_list(self, sample_gate):
        """Failed gates list contains correct gates."""
        decision = sample_gate.evaluate(
            version         = "1.6.0",
            test_results    = [{"priority": "critical", "passed": True}],
            judge_scores    = [4.5],
            safety_scores   = [3.0],   # ❌ safety fails
            latency_samples = [5000],  # ❌ latency fails
            baseline_score  = None
        )
        assert len(decision.failed_gates) == 2