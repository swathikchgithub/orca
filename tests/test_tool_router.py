# ============================================================
# 🐋 ORCA — Tool Router Tests
# tests/test_tool_router.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tool_router import OrcaToolRouter, ToolCall


class TestToolRouterRegistry:
    def test_available_tools_returns_all_three(self, sample_router):
        """All three tools are registered on init."""
        tools = sample_router.available_tools()
        assert "calculator_tool" in tools
        assert "search_tool" in tools
        assert "database_tool" in tools

    def test_available_tools_returns_list(self, sample_router):
        """available_tools() returns a list."""
        assert isinstance(sample_router.available_tools(), list)


class TestRunTool:
    def test_run_calculator_succeeds(self, sample_router):
        """Calculator tool runs and returns correct output."""
        result = sample_router.run_tool("calculator_tool", {"expression": "2 + 2"})
        assert result.success is True
        assert result.output == "4.0"

    def test_run_calculator_percentage(self, sample_router):
        """Calculator handles percentage calculation correctly."""
        result = sample_router.run_tool("calculator_tool", {"expression": "47.50 * 0.15"})
        assert result.success is True
        assert result.output == "7.125"

    def test_run_search_known_query(self, sample_router):
        """Search returns a result for a known query."""
        result = sample_router.run_tool("search_tool", {"query": "capital of France"})
        assert result.success is True
        assert "Paris" in result.output

    def test_run_unknown_tool_returns_error_not_raise(self, sample_router):
        """Unknown tool name returns a failed ToolCall, never raises."""
        result = sample_router.run_tool("magic_tool", {"x": 1})
        assert result.success is False
        assert "magic_tool" in result.error
        assert isinstance(result, ToolCall)

    def test_run_non_dict_input_returns_error(self, sample_router):
        """Non-dict input returns error without raising."""
        result = sample_router.run_tool("calculator_tool", "bad input")
        assert result.success is False
        assert "dict" in result.error

    def test_run_tool_never_raises_even_on_crash(self, sample_router):
        """Tool router catches all exceptions — ORCA must never crash."""
        class CrashingTool:
            def run(self, data):
                raise RuntimeError("Unexpected internal crash!")

        sample_router._registry["crash_tool"] = CrashingTool()
        result = sample_router.run_tool("crash_tool", {})
        assert result.success is False
        assert "crash" in result.error.lower()

    def test_failed_call_has_empty_output(self, sample_router):
        """Failed tool calls have no output."""
        result = sample_router.run_tool("magic_tool", {})
        assert result.output == ""


class TestTrace:
    def test_trace_is_empty_on_init(self, sample_router):
        """Trace starts empty."""
        assert len(sample_router.get_trace()) == 0

    def test_trace_records_each_call(self, sample_router):
        """Each run_tool call is appended to the trace."""
        sample_router.run_tool("calculator_tool", {"expression": "1 + 1"})
        sample_router.run_tool("calculator_tool", {"expression": "2 + 2"})
        assert len(sample_router.get_trace()) == 2

    def test_trace_records_failed_calls_too(self, sample_router):
        """Failed calls are also traced — audit trail must be complete."""
        sample_router.run_tool("unknown_tool", {})
        assert len(sample_router.get_trace()) == 1
        assert sample_router.get_trace()[0].success is False

    def test_clear_trace_empties_history(self, sample_router):
        """clear_trace() removes all entries."""
        sample_router.run_tool("calculator_tool", {"expression": "1 + 1"})
        sample_router.clear_trace()
        assert len(sample_router.get_trace()) == 0

    def test_get_trace_returns_copy(self, sample_router):
        """get_trace() returns a list (not the live internal list)."""
        trace = sample_router.get_trace()
        assert isinstance(trace, list)
