"""
tools/search_tool.py — ORCA's Search Tool

🔍 What this does (5-year-old version):
   When ORCA needs to look something up, it uses this tool.
   Right now it's a MOCK — it returns fake results.
   In production you'd swap in a real search API (Bing, Google, Brave).
   The interface stays the same. That's great architecture. 💡
"""

from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    output : str
    error  : str = ""


# Mock knowledge base — in production, replace with real search API
MOCK_KNOWLEDGE = {
    "capital of france"    : "The capital of France is Paris.",
    "capital of japan"     : "The capital of Japan is Tokyo.",
    "python"               : "Python is a high-level programming language known for readability.",
    "openai"               : "OpenAI is an AI research company that created GPT-4 and ChatGPT.",
    "what is orca"         : "ORCA is an Orchestrated Reasoning & Conversational Agent — an enterprise AI platform.",
}


def run(input_data: dict) -> ToolResult:
    """
    Search for information.

    Args:
        input_data: {"query": "capital of France"}

    Returns:
        ToolResult with search result or not-found message
    """
    query = input_data.get("query", "").strip().lower()

    if not query:
        return ToolResult(success=False, output="", error="No query provided")

    # Check mock knowledge base
    for key, value in MOCK_KNOWLEDGE.items():
        if key in query or query in key:
            return ToolResult(success=True, output=value)

    # Not found
    return ToolResult(
        success=True,
        output=f"No specific information found for '{query}'. This is a mock search tool."
    )
