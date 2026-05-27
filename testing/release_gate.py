# ============================================================
# 🐋 ORCA — Release Gate
# testing/release_gate.py
# ============================================================
# 5 gates that must ALL be green before ORCA ships to prod.
# ONE red gate = release blocked. No exceptions.
# ============================================================

import time
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from config import (
    JUDGE_PASS_THRESHOLD,
    SAFETY_MIN_SCORE,
    LATENCY_SLA_MS,
    BENCHMARK_MAX_DELTA
)


# ── One Gate Result ──────────────────────────────────────────
@dataclass
class GateResult:
    gate_name   : str
    passed      : bool
    actual      : str
    threshold   : str
    message     : str
    critical    : bool = True   # critical gates block release

    def __str__(self):
        icon   = "✅" if self.passed else "❌"
        label  = "PASS" if self.passed else "FAIL"
        return (
            f"   {icon} Gate {self.gate_name:<25} "
            f"| {label} | actual={self.actual:<15} "
            f"| threshold={self.threshold}"
        )


# ── Full Release Decision ────────────────────────────────────
@dataclass
class ReleaseDecision:
    version     : str
    gates       : List[GateResult] = field(default_factory=list)
    approved    : bool = False
    reason      : str  = ""
    timestamp   : str  = ""

    @property
    def passed_gates(self):
        return sum(1 for g in self.gates if g.passed)

    @property
    def failed_gates(self):
        return [g for g in self.gates if not g.passed]

    def __str__(self):
        icon = "🟢 APPROVED" if self.approved else "🔴 BLOCKED"
        return (
            f"\n{'='*60}\n"
            f"🚪 ORCA Release Gate — v{self.version}\n"
            f"{'='*60}\n"
            f"   Decision : {icon}\n"
            f"   Gates    : {self.passed_gates}/{len(self.gates)} passed\n"
            f"   Reason   : {self.reason}\n"
            f"{'='*60}"
        )


# ── Release Gate Engine ──────────────────────────────────────
class OrcaReleaseGate:
    """
    5 gates that must ALL pass before ORCA ships.
    Runs assertions + judge scores + performance checks.
    """

    def __init__(self):
        self.pass_threshold  = JUDGE_PASS_THRESHOLD   # 3.5
        self.safety_minimum  = SAFETY_MIN_SCORE        # 4.0
        self.latency_sla_ms  = LATENCY_SLA_MS          # 3000ms
        self.max_delta       = BENCHMARK_MAX_DELTA      # 0.05 = 5%

    def evaluate(
        self,
        version          : str,
        test_results     : List[Dict],   # from assertion engine
        judge_scores     : List[float],  # weighted scores from judge
        safety_scores    : List[float],  # safety scores from judge
        latency_samples  : List[int],    # response times in ms
        baseline_score   : Optional[float] = None  # previous version score
    ) -> ReleaseDecision:
        """
        Run all 5 gates. Return a ReleaseDecision.
        ALL gates must pass for release approval.
        """
        import datetime
        decision = ReleaseDecision(
            version   = version,
            timestamp = datetime.datetime.now().isoformat()
        )

        # ── Gate 1: Critical Tests ───────────────────────────
        decision.gates.append(
            self._gate_critical_tests(test_results)
        )

        # ── Gate 2: Judge Score ──────────────────────────────
        decision.gates.append(
            self._gate_judge_score(judge_scores)
        )

        # ── Gate 3: Safety Score ─────────────────────────────
        decision.gates.append(
            self._gate_safety_score(safety_scores)
        )

        # ── Gate 4: Latency SLA ──────────────────────────────
        decision.gates.append(
            self._gate_latency(latency_samples)
        )

        # ── Gate 5: Regression Check ─────────────────────────
        decision.gates.append(
            self._gate_regression(judge_scores, baseline_score)
        )

        # ── Final Decision ───────────────────────────────────
        failed = [g for g in decision.gates if not g.passed and g.critical]

        if not failed:
            decision.approved = True
            decision.reason   = "All 5 gates passed. ORCA is cleared for production! 🚀"
        else:
            decision.approved = False
            gate_names        = ", ".join(g.gate_name for g in failed)
            decision.reason   = f"Blocked by: {gate_names}"

        return decision

    # ── Gate 1: All critical tests must pass ─────────────────
    def _gate_critical_tests(self, test_results: List[Dict]) -> GateResult:
        critical = [t for t in test_results if t.get("priority") == "critical"]
        passed   = [t for t in critical if t.get("passed", False)]
        all_pass = len(critical) > 0 and len(passed) == len(critical)

        return GateResult(
            gate_name = "1_CRITICAL_TESTS",
            passed    = all_pass,
            actual    = f"{len(passed)}/{len(critical)} passed",
            threshold = "100% critical tests",
            message   = (
                f"All {len(critical)} critical tests passed ✅"
                if all_pass
                else f"Only {len(passed)}/{len(critical)} critical tests passed ❌"
            )
        )

    # ── Gate 2: Average judge score >= 3.5 ───────────────────
    def _gate_judge_score(self, scores: List[float]) -> GateResult:
        if not scores:
            return GateResult(
                gate_name = "2_JUDGE_SCORE",
                passed    = False,
                actual    = "no scores",
                threshold = f">= {self.pass_threshold}",
                message   = "No judge scores provided"
            )
        avg    = round(sum(scores) / len(scores), 2)
        passed = avg >= self.pass_threshold

        return GateResult(
            gate_name = "2_JUDGE_SCORE",
            passed    = passed,
            actual    = f"{avg}/5.0",
            threshold = f">= {self.pass_threshold}/5.0",
            message   = (
                f"Average judge score {avg} passes threshold ✅"
                if passed
                else f"Average judge score {avg} below threshold ❌"
            )
        )

    # ── Gate 3: ALL safety scores >= 4.0 ─────────────────────
    def _gate_safety_score(self, scores: List[float]) -> GateResult:
        if not scores:
            return GateResult(
                gate_name = "3_SAFETY_SCORE",
                passed    = False,
                actual    = "no scores",
                threshold = f">= {self.safety_minimum} ALL",
                message   = "No safety scores provided"
            )
        min_score  = min(scores)
        all_passed = min_score >= self.safety_minimum

        return GateResult(
            gate_name = "3_SAFETY_SCORE",
            passed    = all_passed,
            actual    = f"min={min_score}/5.0",
            threshold = f">= {self.safety_minimum}/5.0 ALL",
            message   = (
                f"All safety scores >= {self.safety_minimum} ✅"
                if all_passed
                else f"Safety score {min_score} below minimum {self.safety_minimum} ❌"
            )
        )

    # ── Gate 4: p95 latency under 3000ms ─────────────────────
    def _gate_latency(self, samples: List[int]) -> GateResult:
        if not samples:
            return GateResult(
                gate_name = "4_LATENCY_SLA",
                passed    = False,
                actual    = "no samples",
                threshold = f"p95 < {self.latency_sla_ms}ms",
                message   = "No latency samples provided"
            )
        sorted_s = sorted(samples)
        p95_idx  = int(len(sorted_s) * 0.95)
        p95      = sorted_s[min(p95_idx, len(sorted_s) - 1)]
        passed   = p95 < self.latency_sla_ms

        return GateResult(
            gate_name = "4_LATENCY_SLA",
            passed    = passed,
            actual    = f"p95={p95}ms",
            threshold = f"p95 < {self.latency_sla_ms}ms",
            message   = (
                f"p95 latency {p95}ms within SLA ✅"
                if passed
                else f"p95 latency {p95}ms exceeds SLA {self.latency_sla_ms}ms ❌"
            )
        )

    # ── Gate 5: Quality didn't drop > 5% vs baseline ─────────
    def _gate_regression(
        self,
        scores   : List[float],
        baseline : Optional[float]
    ) -> GateResult:
        if baseline is None:
            return GateResult(
                gate_name = "5_REGRESSION",
                passed    = True,
                actual    = "no baseline",
                threshold = f"delta < {self.max_delta*100}%",
                message   = "No baseline — first release, skipping regression check ✅",
                critical  = False
            )
        avg   = round(sum(scores) / len(scores), 2) if scores else 0
        delta = round((baseline - avg) / baseline, 3) if baseline > 0 else 0
        passed = delta <= self.max_delta

        return GateResult(
            gate_name = "5_REGRESSION",
            passed    = passed,
            actual    = f"delta={delta*100:.1f}%",
            threshold = f"< {self.max_delta*100}% drop",
            message   = (
                f"Quality delta {delta*100:.1f}% within limit ✅"
                if passed
                else f"Quality dropped {delta*100:.1f}% vs baseline ❌"
            )
        )


# ── Self-Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🚪 Testing ORCA Release Gate")
    print("=" * 60)

    gate = OrcaReleaseGate()

    # ── Scenario 1: ALL GATES PASS → APPROVED ────────────────
    print("\n📋 Scenario 1: Perfect release (expect APPROVED 🟢)")
    decision1 = gate.evaluate(
        version         = "1.0.0",
        test_results    = [
            {"priority": "critical", "passed": True},
            {"priority": "critical", "passed": True},
            {"priority": "critical", "passed": True},
            {"priority": "high",     "passed": True},
        ],
        judge_scores    = [4.8, 4.5, 4.9, 4.7, 4.6],
        safety_scores   = [5.0, 4.8, 5.0, 4.9, 5.0],
        latency_samples = [800, 950, 1200, 780, 1100,
                          900, 850, 1050, 920, 880],
        baseline_score  = None   # first release!
    )
    for g in decision1.gates:
        print(g)
    print(decision1)
    assert decision1.approved, "Scenario 1 should be approved!"

    # ── Scenario 2: SAFETY FAILS → BLOCKED ───────────────────
    print("\n📋 Scenario 2: Safety failure (expect BLOCKED 🔴)")
    decision2 = gate.evaluate(
        version         = "1.1.0",
        test_results    = [
            {"priority": "critical", "passed": True},
            {"priority": "critical", "passed": True},
        ],
        judge_scores    = [4.5, 4.3, 4.6],
        safety_scores   = [3.5, 3.8, 3.2],   # ❌ below 4.0!
        latency_samples = [900, 1000, 850],
        baseline_score  = 4.5
    )
    for g in decision2.gates:
        print(g)
    print(decision2)
    assert not decision2.approved, "Scenario 2 should be blocked!"

    # ── Scenario 3: REGRESSION FAILS → BLOCKED ───────────────
    print("\n📋 Scenario 3: Regression failure (expect BLOCKED 🔴)")
    decision3 = gate.evaluate(
        version         = "1.2.0",
        test_results    = [
            {"priority": "critical", "passed": True},
            {"priority": "critical", "passed": True},
        ],
        judge_scores    = [3.2, 3.1, 3.3],   # dropped from 4.5!
        safety_scores   = [4.5, 4.8, 4.6],
        latency_samples = [900, 950, 880],
        baseline_score  = 4.5                 # ❌ dropped > 5%!
    )
    for g in decision3.gates:
        print(g)
    print(decision3)
    assert not decision3.approved, "Scenario 3 should be blocked!"

    # ── Scenario 4: LATENCY FAILS → BLOCKED ──────────────────
    print("\n📋 Scenario 4: Latency failure (expect BLOCKED 🔴)")
    decision4 = gate.evaluate(
        version         = "1.3.0",
        test_results    = [
            {"priority": "critical", "passed": True},
        ],
        judge_scores    = [4.5, 4.6],
        safety_scores   = [5.0, 4.8],
        latency_samples = [4000, 5000, 6000, 4500, 3800],  # ❌ too slow!
        baseline_score  = 4.5
    )
    for g in decision4.gates:
        print(g)
    print(decision4)
    assert not decision4.approved, "Scenario 4 should be blocked!"

    print("\n" + "=" * 60)
    print("✅ Release gate tests passed! ORCA ships safely. 🚪🐋")
    print("=" * 60)