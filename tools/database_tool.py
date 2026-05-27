"""
tools/database_tool.py — ORCA's Database Tool

🗃️ What this does (5-year-old version):
   When ORCA needs to look up structured data — like "how many users
   signed up last month?" — it uses this tool.
   Right now it's a MOCK with fake data.
   In production, swap with real SQL/NoSQL queries.
"""

from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    output : str
    error  : str = ""


# Mock database — in production, replace with real DB queries
MOCK_DATA = {
    "users"    : {"total": 15420, "active": 8930, "new_this_month": 342},
    "revenue"  : {"monthly": 48500, "annual": 582000, "currency": "USD"},
    "tickets"  : {"open": 23, "closed_today": 47, "avg_resolution_hours": 4.2},
}


def run(input_data: dict) -> ToolResult:
    """
    Query the database.

    Args:
        input_data: {"table": "users", "field": "total"}

    Returns:
        ToolResult with the queried data
    """
    table = input_data.get("table", "").strip().lower()
    field = input_data.get("field", "").strip().lower()

    if not table:
        return ToolResult(success=False, output="", error="No table specified")

    if table not in MOCK_DATA:
        return ToolResult(
            success=False, output="",
            error=f"Table '{table}' not found. Available: {list(MOCK_DATA.keys())}"
        )

    data = MOCK_DATA[table]

    if field and field in data:
        return ToolResult(success=True, output=f"{field}: {data[field]}")

    # Return all fields if no specific field requested
    result = ", ".join(f"{k}: {v}" for k, v in data.items())
    return ToolResult(success=True, output=result)
