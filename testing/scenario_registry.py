"""
testing/scenario_registry.py — ORCA's Test Case Library

🧪 What this does (5-year-old version):
   Imagine a library with 3 shelves:
   📚 Shelf 1 = Single-turn test cases
   📚 Shelf 2 = Multi-turn test cases
   📚 Shelf 3 = Agentic test cases

   The scenario registry is the LIBRARIAN.
   You say "give me all critical tests" → librarian finds them.
   You say "give me only safety tests" → librarian finds them.
   You say "give me test ST-001" → librarian finds exactly that.

   This is your golden dataset. These tests NEVER change
   unless a human explicitly approves the change.
   That's what makes them "golden."

🏗️ Design Decision:
   Test cases live in JSON files — not in Python code.
   Why? So QA engineers, product managers, and domain experts
   can add test cases WITHOUT writing Python.
   That's how you scale a testing culture. 💡
"""

import json
import os
import config
from dataclasses import dataclass, field
from typing import Literal, Optional


# ─────────────────────────────────────────────
# 📦 Data Types
# ─────────────────────────────────────────────

Priority = Literal["critical", "high", "medium", "low"]

@dataclass
class TestScenario:
    """
    One test case in ORCA's golden dataset.

    Single-turn:  has input + expected_contains + check_type
    Multi-turn:   has turns[] instead of input
    Agentic:      has input + expected_tools[]
    """
    id                   : str
    description          : str
    mode                 : str
    tags                 : list[str]
    priority             : Priority

    # Single-turn / Agentic fields
    input                : str        = ""
    expected_contains    : list[str]  = field(default_factory=list)
    expected_not_contains: list[str]  = field(default_factory=list)
    check_type           : str        = "contains"
    expected_tools       : list[str]  = field(default_factory=list)
    expected_bullet_count: int        = 0
    max_words            : int        = 0

    # Multi-turn field
    turns                : list[dict] = field(default_factory=list)

    def is_multi_turn(self) -> bool:
        return self.mode == "multi_turn" and len(self.turns) > 0

    def is_critical(self) -> bool:
        return self.priority == "critical"

    def __repr__(self):
        return f"TestScenario({self.id} | {self.mode} | {self.priority} | '{self.description}')"


# ─────────────────────────────────────────────
# 📚 OrcaScenarioRegistry — the test case librarian
# ─────────────────────────────────────────────

class OrcaScenarioRegistry:
    """
    Loads and serves test scenarios from the golden dataset.

    Usage:
        registry = OrcaScenarioRegistry()

        # Get all tests
        all_tests = registry.get_all()

        # Get only critical tests (for smoke test / fast CI)
        critical = registry.get_by_priority("critical")

        # Get tests by tag
        safety_tests = registry.get_by_tag("safety")

        # Get one specific test
        test = registry.get_by_id("ST-001")

        # Get tests for one mode
        agentic_tests = registry.get_by_mode("agentic")
    """

    # Map mode names to their JSON files
    DATASET_FILES = {
        "single_turn": "single_turn_cases.json",
        "multi_turn" : "multi_turn_cases.json",
        "agentic"    : "agentic_cases.json",
    }

    def __init__(self):
        self._scenarios: list[TestScenario] = []
        self._load_all()

    def _load_all(self):
        """Load all test cases from all JSON files."""
        for mode, filename in self.DATASET_FILES.items():
            filepath = os.path.join(config.GOLDEN_DATA_DIR, filename)

            if not os.path.exists(filepath):
                print(f"⚠️  Dataset file not found: {filepath}")
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                cases = json.load(f)

            for case in cases:
                scenario = TestScenario(
                    id                    = case["id"],
                    description           = case["description"],
                    mode                  = case["mode"],
                    tags                  = case.get("tags", []),
                    priority              = case.get("priority", "medium"),
                    input                 = case.get("input", ""),
                    expected_contains     = case.get("expected_contains", []),
                    expected_not_contains = case.get("expected_not_contains", []),
                    check_type            = case.get("check_type", "contains"),
                    expected_tools        = case.get("expected_tools", []),
                    expected_bullet_count = case.get("expected_bullet_count", 0),
                    max_words             = case.get("max_words", 0),
                    turns                 = case.get("turns", []),
                )
                self._scenarios.append(scenario)

        print(f"📚 Loaded {len(self._scenarios)} test scenarios from golden dataset")

    # ─────────────────────────────────────────
    # 🔍 QUERY METHODS
    # ─────────────────────────────────────────

    def get_all(self) -> list[TestScenario]:
        """Return ALL test scenarios."""
        return list(self._scenarios)

    def get_by_id(self, scenario_id: str) -> Optional[TestScenario]:
        """Return ONE scenario by ID. Returns None if not found."""
        for s in self._scenarios:
            if s.id == scenario_id:
                return s
        return None

    def get_by_mode(self, mode: str) -> list[TestScenario]:
        """Return all scenarios for a specific mode."""
        return [s for s in self._scenarios if s.mode == mode]

    def get_by_priority(self, priority: Priority) -> list[TestScenario]:
        """Return all scenarios with a specific priority."""
        return [s for s in self._scenarios if s.priority == priority]

    def get_by_tag(self, tag: str) -> list[TestScenario]:
        """Return all scenarios that have a specific tag."""
        return [s for s in self._scenarios if tag in s.tags]

    def get_critical(self) -> list[TestScenario]:
        """Shortcut: return all CRITICAL scenarios (smoke test set)."""
        return self.get_by_priority("critical")

    def get_smoke_tests(self) -> list[TestScenario]:
        """Return scenarios tagged 'smoke_test' — fastest CI check."""
        return self.get_by_tag("smoke_test")

    # ─────────────────────────────────────────
    # 📊 STATS
    # ─────────────────────────────────────────

    def summary(self) -> str:
        """Human-readable summary of the registry."""
        total    = len(self._scenarios)
        by_mode  = {}
        by_pri   = {}

        for s in self._scenarios:
            by_mode[s.mode]     = by_mode.get(s.mode, 0) + 1
            by_pri[s.priority]  = by_pri.get(s.priority, 0) + 1

        lines = [
            f"📚 ORCA Golden Dataset — {total} scenarios",
            f"   By mode    : {by_mode}",
            f"   By priority: {by_pri}",
            f"   Smoke tests: {len(self.get_smoke_tests())}",
            f"   Critical   : {len(self.get_critical())}",
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────
# ✅ TEST IT — run: python testing/scenario_registry.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("📚 Testing ORCA Scenario Registry")
    print("=" * 55)

    registry = OrcaScenarioRegistry()

    # Show summary
    print(f"\n{registry.summary()}")

    # Test: get by mode
    print(f"\n🔍 Single-turn scenarios ({len(registry.get_by_mode('single_turn'))}):")
    for s in registry.get_by_mode("single_turn"):
        print(f"   {s.id} | {s.priority:8} | {s.description}")

    # Test: get critical
    print(f"\n🚨 Critical scenarios ({len(registry.get_critical())}):")
    for s in registry.get_critical():
        print(f"   {s}")

    # Test: get smoke tests
    print(f"\n💨 Smoke tests ({len(registry.get_smoke_tests())}):")
    for s in registry.get_smoke_tests():
        print(f"   {s.id} — {s.description}")

    # Test: get by ID
    print(f"\n🔎 Get by ID (ST-001):")
    s = registry.get_by_id("ST-001")
    print(f"   Found: {s}")
    print(f"   Input: {s.input}")
    print(f"   Expects: {s.expected_contains}")

    # Test: get by tag
    print(f"\n🏷️  Safety-tagged scenarios:")
    for s in registry.get_by_tag("safety"):
        print(f"   {s.id} — {s.description}")

    print("\n" + "=" * 55)
    print("✅ Registry tests passed! Golden dataset loaded. 📚🐋")
    print("=" * 55)
