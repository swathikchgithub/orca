# ============================================================
# 🐋 ORCA — Tool Unit Tests
# tests/test_tools.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import calculator_tool, search_tool, database_tool


class TestCalculatorTool:
    def test_basic_addition(self):
        result = calculator_tool.run({"expression": "2 + 2"})
        assert result.success is True
        assert result.output == "4.0"

    def test_percentage_calculation(self):
        result = calculator_tool.run({"expression": "47.50 * 0.15"})
        assert result.success is True
        assert result.output == "7.125"

    def test_subtraction(self):
        result = calculator_tool.run({"expression": "100 - 37.5"})
        assert result.success is True
        assert float(result.output) == pytest.approx(62.5)

    def test_sqrt_function_available(self):
        result = calculator_tool.run({"expression": "sqrt(16)"})
        assert result.success is True
        assert result.output == "4.0"

    def test_pi_constant_available(self):
        result = calculator_tool.run({"expression": "round(pi, 2)"})
        assert result.success is True
        assert result.output == "3.14"

    def test_division_by_zero_returns_error(self):
        result = calculator_tool.run({"expression": "10 / 0"})
        assert result.success is False
        assert "zero" in result.error.lower()

    def test_empty_expression_returns_error(self):
        result = calculator_tool.run({"expression": ""})
        assert result.success is False

    def test_missing_expression_key_returns_error(self):
        result = calculator_tool.run({})
        assert result.success is False

    def test_malicious_import_blocked(self):
        """eval sandbox must block __import__ and builtins access."""
        result = calculator_tool.run({"expression": "__import__('os').system('ls')"})
        assert result.success is False

    def test_malicious_builtins_blocked(self):
        result = calculator_tool.run({"expression": "open('/etc/passwd').read()"})
        assert result.success is False

    def test_result_is_string(self):
        result = calculator_tool.run({"expression": "3 * 7"})
        assert isinstance(result.output, str)


class TestSearchTool:
    def test_known_query_france_returns_paris(self):
        result = search_tool.run({"query": "capital of France"})
        assert result.success is True
        assert "Paris" in result.output

    def test_known_query_japan_returns_tokyo(self):
        result = search_tool.run({"query": "capital of Japan"})
        assert result.success is True
        assert "Tokyo" in result.output

    def test_known_query_orca_returns_description(self):
        result = search_tool.run({"query": "what is orca"})
        assert result.success is True
        assert "ORCA" in result.output

    def test_unknown_query_returns_success_not_error(self):
        """Unknown queries return a graceful 'not found' — not an error."""
        result = search_tool.run({"query": "obscure_topic_xyz_12345"})
        assert result.success is True

    def test_empty_query_returns_error(self):
        result = search_tool.run({"query": ""})
        assert result.success is False

    def test_missing_query_key_returns_error(self):
        result = search_tool.run({})
        assert result.success is False

    def test_output_is_string(self):
        result = search_tool.run({"query": "python"})
        assert isinstance(result.output, str)


class TestDatabaseTool:
    def test_valid_lookup_returns_success(self):
        result = database_tool.run({"table": "users", "field": "total"})
        assert result.success is True

    def test_output_is_not_empty(self):
        result = database_tool.run({"table": "users", "field": "active"})
        assert result.success is True
        assert len(result.output) > 0

    def test_missing_input_returns_error(self):
        result = database_tool.run({})
        assert result.success is False
