# ============================================================
# 🐋 ORCA — Scenario Registry Tests
# tests/test_scenario_registry.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing.scenario_registry import OrcaScenarioRegistry, TestScenario


class TestRegistryLoading:
    def test_loads_scenarios_on_init(self, sample_registry):
        """Registry loads at least one scenario from golden dataset."""
        assert len(sample_registry.get_all()) > 0

    def test_loads_all_three_modes(self, sample_registry):
        """Golden dataset includes single_turn, multi_turn, and agentic."""
        modes = {s.mode for s in sample_registry.get_all()}
        assert "single_turn" in modes
        assert "multi_turn"  in modes
        assert "agentic"     in modes

    def test_all_scenarios_have_required_fields(self, sample_registry):
        """Every scenario has id, mode, description, and priority."""
        for s in sample_registry.get_all():
            assert s.id
            assert s.mode
            assert s.description
            assert s.priority in ("critical", "high", "medium", "low")


class TestGetById:
    def test_get_known_id_returns_scenario(self, sample_registry):
        first = sample_registry.get_all()[0]
        found = sample_registry.get_by_id(first.id)
        assert found is not None
        assert found.id == first.id

    def test_get_unknown_id_returns_none(self, sample_registry):
        result = sample_registry.get_by_id("DOES-NOT-EXIST-999")
        assert result is None


class TestGetByMode:
    def test_single_turn_filter(self, sample_registry):
        results = sample_registry.get_by_mode("single_turn")
        assert all(s.mode == "single_turn" for s in results)
        assert len(results) > 0

    def test_multi_turn_filter(self, sample_registry):
        results = sample_registry.get_by_mode("multi_turn")
        assert all(s.mode == "multi_turn" for s in results)

    def test_unknown_mode_returns_empty(self, sample_registry):
        results = sample_registry.get_by_mode("nonexistent_mode")
        assert results == []


class TestGetByPriority:
    def test_critical_filter_returns_critical_only(self, sample_registry):
        results = sample_registry.get_by_priority("critical")
        assert all(s.priority == "critical" for s in results)

    def test_get_critical_shortcut_matches_filter(self, sample_registry):
        via_shortcut = sample_registry.get_critical()
        via_filter   = sample_registry.get_by_priority("critical")
        assert len(via_shortcut) == len(via_filter)


class TestGetByTag:
    def test_safety_tag_returns_safety_scenarios(self, sample_registry):
        results = sample_registry.get_by_tag("safety")
        assert all("safety" in s.tags for s in results)

    def test_smoke_test_tag_returns_subset(self, sample_registry):
        smoke = sample_registry.get_smoke_tests()
        all_  = sample_registry.get_all()
        assert len(smoke) <= len(all_)
        assert all("smoke_test" in s.tags for s in smoke)

    def test_unknown_tag_returns_empty(self, sample_registry):
        results = sample_registry.get_by_tag("nonexistent_tag_xyz")
        assert results == []


class TestScenarioFields:
    def test_single_turn_scenario_has_input(self, sample_registry):
        """Single-turn scenarios need an input field."""
        for s in sample_registry.get_by_mode("single_turn"):
            assert s.input, f"Scenario {s.id} has no input"

    def test_multi_turn_scenario_has_turns(self, sample_registry):
        """Multi-turn scenarios need a turns list."""
        for s in sample_registry.get_by_mode("multi_turn"):
            assert s.is_multi_turn(), f"Scenario {s.id} has no turns"
            assert len(s.turns) > 0

    def test_critical_flag_matches_priority(self, sample_registry):
        for s in sample_registry.get_all():
            if s.priority == "critical":
                assert s.is_critical() is True
            else:
                assert s.is_critical() is False
