# ============================================================
# 🐋 ORCA — Assertion Engine
# testing/assertion_engine.py
# ============================================================
# The automatic grader — checks ORCA responses against
# expected values. Fast, cheap, no LLM needed.
# ============================================================

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


# ── Assertion Types ──────────────────────────────────────────
class AssertionType(str, Enum):
    CONTAINS_KEYWORD   = "contains_keyword"
    IS_BLOCKED         = "is_blocked"
    BULLET_COUNT       = "bullet_count"
    WORD_COUNT_MAX     = "word_count_max"
    TOOL_WAS_USED      = "tool_was_used"
    RESPONSE_NOT_EMPTY = "response_not_empty"


# ── Single Assertion Result ──────────────────────────────────
@dataclass
class AssertionResult:
    assertion_type : str
    passed         : bool
    expected       : Any
    actual         : Any
    message        : str

    def __str__(self):
        icon = "✅" if self.passed else "❌"
        return f"{icon} {self.assertion_type} — {self.message}"


# ── Assertion Engine ─────────────────────────────────────────
class OrcaAssertionEngine:
    """
    Runs deterministic checks on ORCA responses.
    No LLM needed. Instant. Free.
    """

    def run(
        self,
        response_text : str,
        assertions    : List[Dict],
        is_blocked    : bool = False,
        tools_used    : Optional[List[str]] = None
    ) -> List[AssertionResult]:
        """
        Run all assertions against a response.
        Returns list of AssertionResult objects.
        """
        results = []
        tools_used = tools_used or []

        for assertion in assertions:
            a_type = assertion.get("type", "")
            result = self._run_one(
                a_type        = a_type,
                assertion     = assertion,
                response_text = response_text,
                is_blocked    = is_blocked,
                tools_used    = tools_used
            )
            results.append(result)

        return results

    def _run_one(
        self,
        a_type        : str,
        assertion     : Dict,
        response_text : str,
        is_blocked    : bool,
        tools_used    : List[str]
    ) -> AssertionResult:
        """Run a single assertion."""

        # ── contains_keyword ────────────────────────────────
        if a_type == AssertionType.CONTAINS_KEYWORD:
            keyword  = assertion.get("value", "")
            case_sensitive = assertion.get("case_sensitive", False)

            if case_sensitive:
                passed = keyword in response_text
            else:
                passed = keyword.lower() in response_text.lower()

            return AssertionResult(
                assertion_type = a_type,
                passed         = passed,
                expected       = f"contains '{keyword}'",
                actual         = response_text[:80],
                message        = f"'{keyword}' {'found' if passed else 'NOT found'} in response"
            )

        # ── is_blocked ───────────────────────────────────────
        elif a_type == AssertionType.IS_BLOCKED:
            expected_blocked = assertion.get("value", True)
            passed = is_blocked == expected_blocked

            return AssertionResult(
                assertion_type = a_type,
                passed         = passed,
                expected       = f"blocked={expected_blocked}",
                actual         = f"blocked={is_blocked}",
                message        = f"Response {'correctly' if passed else 'incorrectly'} {'blocked' if is_blocked else 'passed'}"
            )

        # ── bullet_count ─────────────────────────────────────
        elif a_type == AssertionType.BULLET_COUNT:
            expected_count = assertion.get("value", 0)
            bullets = re.findall(r'^\s*[-•*]\s+.+', response_text, re.MULTILINE)
            actual_count = len(bullets)
            passed = actual_count == expected_count

            return AssertionResult(
                assertion_type = a_type,
                passed         = passed,
                expected       = f"{expected_count} bullets",
                actual         = f"{actual_count} bullets",
                message        = f"Found {actual_count} bullets, expected {expected_count}"
            )

        # ── word_count_max ───────────────────────────────────
        elif a_type == AssertionType.WORD_COUNT_MAX:
            max_words    = assertion.get("value", 100)
            actual_words = len(response_text.split())
            passed       = actual_words <= max_words

            return AssertionResult(
                assertion_type = a_type,
                passed         = passed,
                expected       = f"<= {max_words} words",
                actual         = f"{actual_words} words",
                message        = f"{actual_words} words — {'under' if passed else 'OVER'} {max_words} limit"
            )

        # ── tool_was_used ────────────────────────────────────
        elif a_type == AssertionType.TOOL_WAS_USED:
            expected_tool = assertion.get("value", "")
            passed        = expected_tool in tools_used

            return AssertionResult(
                assertion_type = a_type,
                passed         = passed,
                expected       = f"tool '{expected_tool}' used",
                actual         = f"tools used: {tools_used}",
                message        = f"'{expected_tool}' {'was' if passed else 'was NOT'} used"
            )

        # ── response_not_empty ───────────────────────────────
        elif a_type == AssertionType.RESPONSE_NOT_EMPTY:
            passed = bool(response_text and response_text.strip())

            return AssertionResult(
                assertion_type = a_type,
                passed         = passed,
                expected       = "non-empty response",
                actual         = f"{len(response_text)} chars",
                message        = f"Response is {'non-empty ✅' if passed else 'EMPTY ❌'}"
            )

        # ── unknown assertion type ───────────────────────────
        else:
            return AssertionResult(
                assertion_type = a_type,
                passed         = False,
                expected       = "known assertion type",
                actual         = a_type,
                message        = f"❓ Unknown assertion type: '{a_type}'"
            )

    def summary(self, results: List[AssertionResult]) -> Dict:
        """Summarize a list of assertion results."""
        total  = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        return {
            "total"   : total,
            "passed"  : passed,
            "failed"  : failed,
            "pass_pct": round((passed / total * 100), 1) if total > 0 else 0.0
        }


# ── Self-Test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("✅ Testing ORCA Assertion Engine")
    print("=" * 60)

    engine = OrcaAssertionEngine()
    all_passed = True

    # Test 1 — contains_keyword PASS
    print("\n🧪 Test 1: contains_keyword (should PASS)")
    results = engine.run(
        response_text = "The capital of France is Paris.",
        assertions    = [{"type": "contains_keyword", "value": "Paris"}]
    )
    for r in results:
        print(f"   {r}")
    assert results[0].passed, "Test 1 failed!"

    # Test 2 — is_blocked PASS
    print("\n🧪 Test 2: is_blocked (should PASS)")
    results = engine.run(
        response_text = "I cannot help with that.",
        assertions    = [{"type": "is_blocked", "value": True}],
        is_blocked    = True
    )
    for r in results:
        print(f"   {r}")
    assert results[0].passed, "Test 2 failed!"

    # Test 3 — bullet_count PASS
    print("\n🧪 Test 3: bullet_count (should PASS — exactly 3)")
    results = engine.run(
        response_text = "Here are 3 items:\n- First item\n- Second item\n- Third item",
        assertions    = [{"type": "bullet_count", "value": 3}]
    )
    for r in results:
        print(f"   {r}")
    assert results[0].passed, "Test 3 failed!"

    # Test 4 — word_count_max PASS
    print("\n🧪 Test 4: word_count_max (should PASS — under 80)")
    results = engine.run(
        response_text = "The answer is forty seven dollars and fifty cents.",
        assertions    = [{"type": "word_count_max", "value": 80}]
    )
    for r in results:
        print(f"   {r}")
    assert results[0].passed, "Test 4 failed!"

    # Test 5 — tool_was_used PASS
    print("\n🧪 Test 5: tool_was_used (should PASS)")
    results = engine.run(
        response_text = "The tip is $7.13",
        assertions    = [{"type": "tool_was_used", "value": "calculator_tool"}],
        tools_used    = ["calculator_tool"]
    )
    for r in results:
        print(f"   {r}")
    assert results[0].passed, "Test 5 failed!"

    # Test 6 — response_not_empty PASS
    print("\n🧪 Test 6: response_not_empty (should PASS)")
    results = engine.run(
        response_text = "Hello! I am ORCA.",
        assertions    = [{"type": "response_not_empty"}]
    )
    for r in results:
        print(f"   {r}")
    assert results[0].passed, "Test 6 failed!"

    # Test 7 — contains_keyword FAIL (wrong keyword)
    print("\n🧪 Test 7: contains_keyword (should FAIL — wrong keyword)")
    results = engine.run(
        response_text = "The capital of France is Paris.",
        assertions    = [{"type": "contains_keyword", "value": "London"}]
    )
    for r in results:
        print(f"   {r}")
    assert not results[0].passed, "Test 7 should have failed!"

    # Summary
    all_results = engine.run(
        response_text = "The capital of France is Paris.",
        assertions    = [
            {"type": "contains_keyword",   "value": "Paris"},
            {"type": "response_not_empty"},
            {"type": "word_count_max",     "value": 80},
            {"type": "contains_keyword",   "value": "London"},  # intentional fail
        ]
    )

    s = engine.summary(all_results)
    print(f"\n📊 Assertion Summary:")
    print(f"   Total   : {s['total']}")
    print(f"   Passed  : {s['passed']}")
    print(f"   Failed  : {s['failed']}")
    print(f"   Pass %  : {s['pass_pct']}%")

    print("\n" + "=" * 60)
    print("✅ Assertion engine working! ORCA can grade itself. ✅🐋")
    print("=" * 60)