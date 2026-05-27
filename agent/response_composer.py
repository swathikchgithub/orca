"""
agent/response_composer.py — ORCA's Response Composer

✍️ What this does (5-year-old version):
   Imagine you order pizza. The chef makes it (LLM).
   But before it reaches you, someone puts it in a box,
   adds a receipt, stamps it with the order number, and
   notes how long it took to make.

   That's the response composer. It takes the raw LLM answer
   and wraps it in a clean, structured package that:
   - Tells you WHAT mode was used
   - Tells you HOW LONG it took
   - Tells you HOW MANY tokens were used (cost!)
   - Tells you WHICH tools were called (if any)
   - Tells you if it PASSED the guardrail
   - Gives you a UNIQUE ID to trace this response forever

🏗️ Why does this matter?
   Without this, every caller gets a random string back.
   With this, every caller gets a consistent, typed object.
   That means you can log it, test it, compare it, and audit it.
   THAT is what makes ORCA enterprise-ready.
"""

import time
import uuid
import config
from dataclasses import dataclass, field
from typing import Literal
from typing import Optional, List, Dict, Any

# Import our tool call type for the trace
from agent.tool_router import ToolCall


# ─────────────────────────────────────────────
# 📦 OrcaResponse — the single output object
# ─────────────────────────────────────────────

AgentMode = Literal["single_turn", "multi_turn", "agentic"]

@dataclass
class OrcaResponse:
    """
    The standard output object for every ORCA interaction.

    Every single response ORCA ever gives comes back as this object.
    No exceptions. This is the contract between ORCA and the outside world.

    Fields:
        response_id      : unique ID — use this to find a response in logs
        content          : the actual answer text shown to the user
        mode             : which mode was used (single_turn/multi_turn/agentic)
        success          : True if ORCA completed the task, False if blocked/failed
        duration_ms      : how long the full response took in milliseconds
        tokens_used      : estimated tokens used (input + output)
        tool_calls       : list of tools called (agentic mode only)
        guardrail_passed : True if both input and output guardrails passed
        blocked_reason   : why it was blocked (empty if not blocked)
        session_id       : conversation session this belongs to
        timestamp        : when this response was created (unix time)
        metadata         : any extra info (model used, temperature, etc.)
    """
    # Core fields — always present
    response_id     : str
    content         : str
    mode            : str
    success         : bool

    # Performance fields
    duration_ms     : int
    tokens_used     : int

    # Agentic fields
    tool_calls      : list

    # Safety fields
    guardrail_passed: bool
    blocked_reason  : Optional[str] = None

    # Tracing fields
    session_id      : Optional[str] = None
    timestamp       : str           = ""
    metadata        : dict          = field(default_factory=dict)


    @property
    def is_blocked(self) -> bool:
        """Shortcut: response.is_blocked"""
        return not self.guardrail_passed

    @property
    def cost_estimate_usd(self) -> float:
        """
        Rough cost estimate in USD.
        Based on gpt-4o-mini pricing: ~$0.15 per 1M tokens
        """
        return round((self.tokens_used / 1_000_000) * 0.15, 6)

    def to_dict(self) -> dict:
        """
        Convert to a plain dictionary.
        Use this for: JSON serialization, logging, API responses.
        """
        return {
            "response_id"     : self.response_id,
            "content"         : self.content,
            "mode"            : self.mode,
            "success"         : self.success,
            "duration_ms"     : self.duration_ms,
            "tokens_used"     : self.tokens_used,
            "tool_calls_count": len(self.tool_calls),
            "guardrail_passed": self.guardrail_passed,
            "blocked_reason"  : self.blocked_reason,
            "session_id"      : self.session_id,
            "timestamp"       : self.timestamp,
            "cost_estimate"   : self.cost_estimate_usd,
            "metadata"        : self.metadata,
        }

    def summary(self) -> str:
        """Human-readable one-line summary. Great for logs."""
        icon    = "✅" if self.success else "❌"
        blocked = f" [BLOCKED: {self.blocked_reason}]" if self.is_blocked else ""
        tools   = f" | tools: {len(self.tool_calls)}" if self.tool_calls else ""
        return (
            f"{icon} OrcaResponse | id={self.response_id[:8]}... "
            f"| mode={self.mode} | {self.duration_ms:.0f}ms "
            f"| ~{self.tokens_used} tokens{tools}{blocked}"
        )

    def __repr__(self):
        return self.summary()


# ─────────────────────────────────────────────
# ✍️ OrcaResponseComposer — builds OrcaResponse objects
# ─────────────────────────────────────────────

class OrcaResponseComposer:
    """
    Builds OrcaResponse objects from raw LLM output + metadata.

    Usage:
        composer = OrcaResponseComposer()

        # Build a successful response
        response = composer.compose(
            content     = "The capital of France is Paris.",
            mode        = "single_turn",
            duration_ms = 842.3,
            tokens_used = 45,
            session_id  = "session_123"
        )

        # Build a blocked response
        response = composer.compose_blocked(
            reason     = "Blocked phrase detected",
            safe_msg   = "I can't help with that.",
            mode       = "single_turn",
            session_id = "session_123"
        )
    """

    def compose(
        self,
        content     : str,
        mode        : AgentMode,
        duration_ms : float        = 0.0,
        tokens_used : int          = 0,
        tool_calls  : list         = None,
        session_id  : str          = "",
        metadata    : dict         = None,
    ) -> OrcaResponse:
        """
        Build a SUCCESSFUL OrcaResponse.

        Call this when: ORCA completed the task and the guardrail passed.

        Args:
            content     : the answer text to show the user
            mode        : "single_turn", "multi_turn", or "agentic"
            duration_ms : how long the full call took
            tokens_used : estimated total tokens (input + output)
            tool_calls  : list of ToolCall objects (agentic only)
            session_id  : which conversation session this belongs to
            metadata    : any extra info to attach

        Returns:
            OrcaResponse with success=True
        """
        # Estimate tokens from content if not provided
        if tokens_used == 0:
            tokens_used = len(content) // 4

        return OrcaResponse(
            response_id      = str(uuid.uuid4()),
            content          = content.strip(),
            mode             = mode,
            success          = True,
            duration_ms      = round(duration_ms, 2),
            tokens_used      = tokens_used,
            tool_calls       = tool_calls or [],
            guardrail_passed = True,
            blocked_reason   = "",
            session_id       = session_id,
            metadata         = metadata or {"model": config.AGENT_MODEL},
        )

    def compose_blocked(
        self,
        reason     : str,
        safe_msg   : str,
        mode       : AgentMode,
        session_id : str  = "",
        duration_ms: float = 0.0,
    ) -> OrcaResponse:
        """
        Build a BLOCKED OrcaResponse.

        Call this when: the guardrail blocked the input or output.

        Args:
            reason     : why it was blocked (for internal logs)
            safe_msg   : the safe message to show the user
            mode       : which mode was active
            session_id : which session this belongs to
            duration_ms: how long until it was blocked

        Returns:
            OrcaResponse with success=False, guardrail_passed=False
        """
        return OrcaResponse(
            response_id      = str(uuid.uuid4()),
            content          = safe_msg,
            mode             = mode,
            success          = False,
            duration_ms      = round(duration_ms, 2),
            tokens_used      = 0,   # blocked before LLM call = $0 cost
            tool_calls       = [],
            guardrail_passed = False,
            blocked_reason   = reason,
            session_id       = session_id,
            metadata         = {"blocked": True},
        )

    def compose_error(
        self,
        error_msg  : str,
        mode       : AgentMode,
        session_id : str   = "",
        duration_ms: float = 0.0,
    ) -> OrcaResponse:
        """
        Build an ERROR OrcaResponse.

        Call this when: something unexpected went wrong (not a guardrail block).
        Examples: API timeout, network error, unexpected exception.

        Args:
            error_msg  : what went wrong (for internal logs)
            mode       : which mode was active
            session_id : which session this belongs to
            duration_ms: how long until the error occurred

        Returns:
            OrcaResponse with success=False
        """
        return OrcaResponse(
            response_id      = str(uuid.uuid4()),
            content          = (
                "I encountered an unexpected error. "
                "Please try again in a moment."
            ),
            mode             = mode,
            success          = False,
            duration_ms      = round(duration_ms, 2),
            tokens_used      = 0,
            tool_calls       = [],
            guardrail_passed = True,   # not a safety issue — a system error
            blocked_reason   = "",
            session_id       = session_id,
            metadata         = {"error": error_msg},
        )


# ─────────────────────────────────────────────
# ✅ TEST IT — run: python agent/response_composer.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("✍️  Testing ORCA Response Composer")
    print("=" * 60)

    composer = OrcaResponseComposer()

    # Test 1: Successful single-turn response
    print("\n📦 Test 1: Successful single-turn response")
    r = composer.compose(
        content     = "The capital of France is Paris.",
        mode        = "single_turn",
        duration_ms = 842.3,
        tokens_used = 45,
        session_id  = "session_test_001"
    )
    print(f"   {r.summary()}")
    assert r.success         == True
    assert r.guardrail_passed == True
    assert r.is_blocked      == False
    assert r.content         == "The capital of France is Paris."
    assert r.mode            == "single_turn"
    assert len(r.response_id) > 0
    print("   ✅ Success response built correctly!")

    # Test 2: Multi-turn response
    print("\n📦 Test 2: Multi-turn response")
    r = composer.compose(
        content     = "Nice to meet you, Swathi! How can I help?",
        mode        = "multi_turn",
        duration_ms = 1203.7,
        tokens_used = 120,
        session_id  = "session_test_002"
    )
    print(f"   {r.summary()}")
    assert r.mode == "multi_turn"
    print("   ✅ Multi-turn response built correctly!")

    # Test 3: Blocked response
    print("\n📦 Test 3: Blocked response")
    r = composer.compose_blocked(
        reason     = "Blocked phrase: 'how to hack'",
        safe_msg   = "I'm not able to help with that request.",
        mode       = "single_turn",
        session_id = "session_test_003"
    )
    print(f"   {r.summary()}")
    assert r.success          == False
    assert r.guardrail_passed == False
    assert r.is_blocked       == True
    assert r.tokens_used      == 0      # blocked = no cost!
    print("   ✅ Blocked response built correctly!")

    # Test 4: Error response
    print("\n📦 Test 4: Error response")
    r = composer.compose_error(
        error_msg  = "OpenAI API timeout after 30s",
        mode       = "agentic",
        session_id = "session_test_004"
    )
    print(f"   {r.summary()}")
    assert r.success == False
    assert r.guardrail_passed == True   # error ≠ safety violation
    print("   ✅ Error response built correctly!")

    # Test 5: Agentic response with tool calls
    print("\n📦 Test 5: Agentic response with tool calls")
    from agent.tool_router import ToolCall
    fake_tool_call = ToolCall(
        tool_name  = "calculator_tool",
        input_data = {"expression": "47.50 * 0.15"},
        output     = "7.125",
        success    = True,
        duration_ms= 2.1
    )
    r = composer.compose(
        content     = "15% tip on $47.50 is $7.13.",
        mode        = "agentic",
        duration_ms = 1850.0,
        tokens_used = 230,
        tool_calls  = [fake_tool_call],
        session_id  = "session_test_005"
    )
    print(f"   {r.summary()}")
    assert len(r.tool_calls) == 1
    assert r.cost_estimate_usd > 0
    print(f"   Cost estimate: ${r.cost_estimate_usd}")
    print("   ✅ Agentic response with tools built correctly!")

    # Test 6: to_dict()
    print("\n📦 Test 6: Serialization to dict")
    d = r.to_dict()
    assert "response_id" in d
    assert "content" in d
    assert "duration_ms" in d
    print(f"   Dict keys: {list(d.keys())}")
    print("   ✅ Serialization works!")

    print("\n" + "=" * 60)
    print("✅ All composer tests passed! ORCA wraps beautifully. ✍️🐋")
    print("=" * 60)
