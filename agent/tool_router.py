"""
agent/tool_router.py — ORCA's Tool Router

🔧 What this does (5-year-old version):
   Imagine ORCA has a toolbox with 3 tools inside.
   The tool router is the smart hand that reaches into the toolbox,
   picks the RIGHT tool for the job, uses it, and returns the result.

   ORCA says: "I need to calculate 15% of 47.50"
   Router says: "That's math → use calculator_tool"
   Router runs: calculator_tool.run({"expression": "47.50 * 0.15"})
   Router returns: "7.125"

🏗️ Architecture:
   - Tools are registered in a dictionary (easy to add new ones!)
   - Router validates the tool name before running it
   - Router catches ALL errors (tools should never crash ORCA)
   - Every tool call is logged in a trace (audit trail)
"""

import time

# Import all 3 tools
from tools import calculator_tool, search_tool, database_tool
from dataclasses import dataclass, field


# ─────────────────────────────────────────────
# 📦 Data Types
# ─────────────────────────────────────────────

@dataclass
class ToolCall:
    """One tool call — what was called, with what, and what came back."""
    tool_name  : str
    input_data : dict
    output     : str   = ""
    error      : str   = ""
    success    : bool  = False
    duration_ms: float = 0.0

    def __repr__(self):
        icon = "✅" if self.success else "❌"
        return (f"ToolCall({icon} {self.tool_name} | "
                f"input={self.input_data} | "
                f"output='{self.output[:50]}' | "
                f"{self.duration_ms:.0f}ms)")


# ─────────────────────────────────────────────
# 🔧 OrcaToolRouter — the main router class
# ─────────────────────────────────────────────

class OrcaToolRouter:
    """
    Routes tool calls to the right tool and returns results.

    Usage:
        router = OrcaToolRouter()

        # Run one tool
        result = router.run_tool("calculator_tool", {"expression": "47.50 * 0.15"})
        print(result.output)   # "7.125"

        # Check what tools are available
        print(router.available_tools())
    """

    def __init__(self):
        # 📦 Tool Registry — add new tools HERE
        # Key   = the name ORCA uses to call the tool
        # Value = the module with a run() function
        self._registry = {
            "calculator_tool" : calculator_tool,
            "search_tool"     : search_tool,
            "database_tool"   : database_tool,
        }

        # Tool call history — full audit trail
        self._trace: list[ToolCall] = []

    # ─────────────────────────────────────────
    # 🚀 RUN — execute a tool
    # ─────────────────────────────────────────

    def run_tool(self, tool_name: str, input_data: dict) -> ToolCall:
        """
        Run a tool by name with given input.

        Args:
            tool_name  : name of the tool (must be in registry)
            input_data : dict of inputs the tool needs

        Returns:
            ToolCall with output, error, success, and timing

        This NEVER raises an exception.
        All errors are caught and returned in the ToolCall object.
        ORCA must never crash because a tool failed.
        """
        call = ToolCall(tool_name=tool_name, input_data=input_data)
        start = time.time()

        # ── Validate tool exists ──
        if tool_name not in self._registry:
            call.error      = (f"Unknown tool '{tool_name}'. "
                               f"Available: {self.available_tools()}")
            call.success    = False
            call.duration_ms = (time.time() - start) * 1000
            self._trace.append(call)
            return call

        # ── Validate input is a dict ──
        if not isinstance(input_data, dict):
            call.error      = f"input_data must be a dict, got {type(input_data).__name__}"
            call.success    = False
            call.duration_ms = (time.time() - start) * 1000
            self._trace.append(call)
            return call

        # ── Run the tool ──
        try:
            tool   = self._registry[tool_name]
            result = tool.run(input_data)

            call.output  = result.output
            call.error   = result.error
            call.success = result.success

        except Exception as e:
            # Catch EVERYTHING — tools must never crash ORCA
            call.error   = f"Tool crashed unexpectedly: {str(e)}"
            call.success = False

        finally:
            call.duration_ms = round((time.time() - start) * 1000, 2)

        # ── Save to trace ──
        self._trace.append(call)
        return call

    # ─────────────────────────────────────────
    # 📋 INSPECT — check tools and history
    # ─────────────────────────────────────────

    def available_tools(self) -> list[str]:
        """Returns list of registered tool names."""
        return list(self._registry.keys())

    def get_trace(self) -> list[ToolCall]:
        """Returns full audit trail of all tool calls this session."""
        return list(self._trace)

    def clear_trace(self):
        """Wipe the trace (call between conversations)."""
        self._trace = []

    def trace_summary(self) -> str:
        """Human-readable summary of all tool calls."""
        if not self._trace:
            return "🔧 No tool calls made yet."
        lines = ["🔧 ORCA Tool Call Trace:"]
        for i, call in enumerate(self._trace, 1):
            icon = "✅" if call.success else "❌"
            lines.append(
                f"   {i}. {icon} {call.tool_name} "
                f"({call.duration_ms:.0f}ms) → {call.output[:60] or call.error[:60]}"
            )
        return "\n".join(lines)


# ─────────────────────────────────────────────
# ✅ TEST IT — run: python agent/tool_router.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("🔧 Testing ORCA Tool Router")
    print("=" * 55)

    router = OrcaToolRouter()

    print(f"\n📦 Available tools: {router.available_tools()}")

    # Test 1: Calculator
    print("\n🧮 Test 1: Calculator")
    result = router.run_tool("calculator_tool", {"expression": "47.50 * 0.15"})
    print(f"   47.50 * 0.15 = {result.output}")
    assert result.success, "Calculator should succeed"
    assert result.output == "7.125", f"Expected 7.125, got {result.output}"
    print("   ✅ Calculator works!")

    # Test 2: Search
    print("\n🔍 Test 2: Search")
    result = router.run_tool("search_tool", {"query": "capital of France"})
    print(f"   Result: {result.output}")
    assert result.success
    print("   ✅ Search works!")

    # Test 3: Database
    print("\n🗃️  Test 3: Database")
    result = router.run_tool("database_tool", {"table": "users", "field": "total"})
    print(f"   Result: {result.output}")
    assert result.success
    print("   ✅ Database works!")

    # Test 4: Unknown tool
    print("\n🛡️  Test 4: Unknown tool (error handling)")
    result = router.run_tool("magic_tool", {"input": "test"})
    assert not result.success
    print(f"   ✅ Correctly rejected: {result.error[:60]}")

    # Test 5: Math error
    print("\n🛡️  Test 5: Division by zero")
    result = router.run_tool("calculator_tool", {"expression": "10 / 0"})
    assert not result.success
    print(f"   ✅ Correctly caught: {result.error}")

    # Show trace
    print(f"\n{router.trace_summary()}")

    print("\n" + "=" * 55)
    print("✅ All tool router tests passed! ORCA has hands. 🔧🐋")
    print("=" * 55)
