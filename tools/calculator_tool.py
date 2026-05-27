"""
tools/calculator_tool.py — ORCA's Math Tool

🧮 What this does (5-year-old version):
   ORCA is smart but we never let AI do raw math in its head.
   Why? Because LLMs can say "2 + 2 = 5" with full confidence. 😱
   So whenever there's math — we use THIS tool.
   Real Python math. 100% accurate. Every time.
"""

import math
from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    output : str
    error  : str = ""


def run(input_data: dict) -> ToolResult:
    """
    Run a math calculation safely.

    Args:
        input_data: {"expression": "47.50 * 0.15"}

    Returns:
        ToolResult with the answer or error
    """
    expression = input_data.get("expression", "").strip()

    if not expression:
        return ToolResult(success=False, output="", error="No expression provided")

    # Safe math context — only named functions, no builtins, no module access.
    # Never use eval() on raw user input without a restricted namespace.
    try:
        safe_context = {
            "sqrt" : math.sqrt,
            "pow"  : math.pow,
            "abs"  : abs,
            "round": round,
            "pi"   : math.pi,
        }
        result = eval(expression, {"__builtins__": {}}, safe_context)
        return ToolResult(success=True, output=str(round(float(result), 4)))

    except ZeroDivisionError:
        return ToolResult(success=False, output="", error="Division by zero")
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Math error: {str(e)}")
