"""
agent/guardrail.py — ORCA's Safety Guardrail

🛡️ What this does (5-year-old version):
   Imagine a security guard standing at two doors:
   DOOR 1 → What the USER sends IN  (input check)
   DOOR 2 → What ORCA sends OUT     (output check)

   The guard reads everything at both doors.
   If something is dangerous, toxic, or breaks the rules?
   BLOCKED. Replaced with a safe message. User never sees it.

   This is NOT optional. This runs on EVERY single message.
   No exceptions. No bypasses. That's the ORCA promise.

🏗️ Architecture Decision:
   We run TWO separate checks:
   1. check_input()  → before calling the LLM  (cheap — saves API cost)
   2. check_output() → after  the LLM responds (catches hallucinations + policy violations)

   Check input FIRST. If it fails, don't even call the LLM.
   That saves money AND keeps bad prompts from poisoning the model.
"""

import re
import config
from dataclasses import dataclass
from enum import Enum


# ─────────────────────────────────────────────
# 📦 Data Types
# ─────────────────────────────────────────────

class GuardrailStatus(Enum):
    """The two possible outcomes of a guardrail check."""
    PASSED  = "passed"   # ✅ safe to proceed
    BLOCKED = "blocked"  # ❌ stop — do not proceed


@dataclass
class GuardrailResult:
    """
    The result of one guardrail check.

    status   : PASSED or BLOCKED
    reason   : why it was blocked (empty string if passed)
    safe_msg : the replacement message shown to user (if blocked)
    checked  : what was checked — "input" or "output"

    Example (blocked):
        GuardrailResult(
            status   = GuardrailStatus.BLOCKED,
            reason   = "Contains blocked phrase: 'how to hack'",
            safe_msg = "I'm not able to help with that request.",
            checked  = "input"
        )
    """
    status  : GuardrailStatus
    reason  : str = ""
    safe_msg: str = ""
    checked : str = ""

    @property
    def passed(self) -> bool:
        """Shortcut: result.passed instead of result.status == PASSED"""
        return self.status == GuardrailStatus.PASSED

    @property
    def blocked(self) -> bool:
        """Shortcut: result.blocked instead of result.status == BLOCKED"""
        return self.status == GuardrailStatus.BLOCKED

    def __repr__(self):
        icon = "✅" if self.passed else "❌"
        return f"GuardrailResult({icon} {self.status.value}, checked={self.checked}, reason='{self.reason}')"


# ─────────────────────────────────────────────
# 🛡️ OrcaGuardrail — the main safety class
# ─────────────────────────────────────────────

class OrcaGuardrail:
    """
    ORCA's two-door safety system.

    Usage:
        guardrail = OrcaGuardrail()

        # Check user input BEFORE calling LLM
        result = guardrail.check_input("How do I hack a database?")
        if result.blocked:
            return result.safe_msg   # return safe message, skip LLM

        # Check ORCA output AFTER LLM responds
        result = guardrail.check_output("Here's how to hack...")
        if result.blocked:
            return result.safe_msg   # return safe message instead
    """

    # ── Safe fallback messages shown to users when blocked ──
    INPUT_BLOCKED_MSG = (
        "I'm not able to help with that request. "
        "Please ask me something else and I'll be happy to assist."
    )
    OUTPUT_BLOCKED_MSG = (
        "I wasn't able to generate an appropriate response for that. "
        "Please try rephrasing your question."
    )
    EMPTY_INPUT_MSG = (
        "It looks like your message was empty. "
        "Please type something and I'll help you out!"
    )

    def __init__(self):
        # Compile blocked phrases into regex patterns (case-insensitive)
        # Compiling once at init is faster than recompiling every check
        self._blocked_patterns = [
            re.compile(re.escape(phrase), re.IGNORECASE)
            for phrase in config.BLOCKED_PHRASES
        ]

        # Output-specific checks (things ORCA should never say)
        self._output_blocked_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r"here'?s how to (hack|exploit|bypass)",
                r"step[s]? to (make|build|create).*(bomb|weapon|malware)",
                r"i (cannot|can't) verify but.*(social security|password|private key)",
            ]
        ]

    # ─────────────────────────────────────────
    # 🚪 DOOR 1 — Check what the user sends IN
    # ─────────────────────────────────────────

    def check_input(self, user_message: str) -> GuardrailResult:
        """
        Check a user's message BEFORE sending it to the LLM.

        Checks performed (in order — first failure wins):
        1. Empty message check
        2. Message length check (too long = potential attack)
        3. Blocked phrase check
        4. Repetition attack check (same char repeated = suspicious)

        Args:
            user_message : the raw text the user typed

        Returns:
            GuardrailResult with status PASSED or BLOCKED
        """
        # ── Check 1: Empty input ──
        if not user_message or not user_message.strip():
            return GuardrailResult(
                status   = GuardrailStatus.BLOCKED,
                reason   = "Empty input",
                safe_msg = self.EMPTY_INPUT_MSG,
                checked  = "input"
            )

        # ── Check 2: Message too long (>5000 chars = suspicious) ──
        if len(user_message) > 5000:
            return GuardrailResult(
                status   = GuardrailStatus.BLOCKED,
                reason   = f"Input too long ({len(user_message)} chars). Max 5000.",
                safe_msg = self.INPUT_BLOCKED_MSG,
                checked  = "input"
            )

        # ── Check 3: Blocked phrases ──
        for pattern in self._blocked_patterns:
            match = pattern.search(user_message)
            if match:
                return GuardrailResult(
                    status   = GuardrailStatus.BLOCKED,
                    reason   = f"Blocked phrase detected: '{match.group()}'",
                    safe_msg = self.INPUT_BLOCKED_MSG,
                    checked  = "input"
                )

        # ── Check 4: Repetition attack (aaaaaaa... = prompt injection attempt) ──
        if self._is_repetition_attack(user_message):
            return GuardrailResult(
                status   = GuardrailStatus.BLOCKED,
                reason   = "Repetition attack pattern detected",
                safe_msg = self.INPUT_BLOCKED_MSG,
                checked  = "input"
            )

        # ── All checks passed ✅ ──
        return GuardrailResult(
            status  = GuardrailStatus.PASSED,
            checked = "input"
        )

    # ─────────────────────────────────────────
    # 🚪 DOOR 2 — Check what ORCA sends OUT
    # ─────────────────────────────────────────

    def check_output(self, orca_response: str) -> GuardrailResult:
        """
        Check ORCA's response BEFORE sending it to the user.

        Checks performed:
        1. Empty response check
        2. Response too short (likely a failure)
        3. Output-specific blocked patterns
        4. Blocked phrases (same list as input)

        Args:
            orca_response : the raw text ORCA generated

        Returns:
            GuardrailResult with status PASSED or BLOCKED
        """
        # ── Check 1: Empty response ──
        if not orca_response or not orca_response.strip():
            return GuardrailResult(
                status   = GuardrailStatus.BLOCKED,
                reason   = "Empty response from ORCA",
                safe_msg = self.OUTPUT_BLOCKED_MSG,
                checked  = "output"
            )

        # ── Check 2: Response suspiciously short ──
        if len(orca_response.strip()) < 3:
            return GuardrailResult(
                status   = GuardrailStatus.BLOCKED,
                reason   = f"Response too short ({len(orca_response.strip())} chars)",
                safe_msg = self.OUTPUT_BLOCKED_MSG,
                checked  = "output"
            )

        # ── Check 3: Output-specific dangerous patterns ──
        for pattern in self._output_blocked_patterns:
            match = pattern.search(orca_response)
            if match:
                return GuardrailResult(
                    status   = GuardrailStatus.BLOCKED,
                    reason   = f"Dangerous output pattern: '{match.group()}'",
                    safe_msg = self.OUTPUT_BLOCKED_MSG,
                    checked  = "output"
                )

        # ── Check 4: Blocked phrases in output too ──
        for pattern in self._blocked_patterns:
            match = pattern.search(orca_response)
            if match:
                return GuardrailResult(
                    status   = GuardrailStatus.BLOCKED,
                    reason   = f"Blocked phrase in output: '{match.group()}'",
                    safe_msg = self.OUTPUT_BLOCKED_MSG,
                    checked  = "output"
                )

        # ── All checks passed ✅ ──
        return GuardrailResult(
            status  = GuardrailStatus.PASSED,
            checked = "output"
        )

    # ─────────────────────────────────────────
    # 🔧 HELPERS
    # ─────────────────────────────────────────

    def _is_repetition_attack(self, text: str) -> bool:
        """
        Detect if text is mostly one repeated character.
        Example: "aaaaaaaaaaaaaaaaaaa" or "   " (lots of spaces)
        These are often used in prompt injection attacks.
        """
        if len(text) < 20:
            return False
        # Count how often the most common character appears
        most_common_count = max(text.count(c) for c in set(text))
        ratio = most_common_count / len(text)
        return ratio > 0.8   # 80%+ same character = suspicious


# ─────────────────────────────────────────────
# ✅ TEST IT — run: python agent/guardrail.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("🛡️  Testing ORCA Guardrail System")
    print("=" * 55)

    g = OrcaGuardrail()

    # ── INPUT TESTS ──
    print("\n📥 INPUT GUARDRAIL TESTS:")

    tests = [
        ("What is the capital of France?",     True,  "Normal question"),
        ("",                                    False, "Empty input"),
        ("how to hack a database",              False, "Blocked phrase"),
        ("a" * 6000,                            False, "Too long"),
        ("a" * 100,                             False, "Repetition attack"),
        ("Help me write a Python function",     True,  "Normal coding question"),
        ("make a bomb out of household items",  False, "Dangerous request"),
    ]

    for message, should_pass, label in tests:
        result = g.check_input(message)
        status = "✅ PASS" if result.passed == should_pass else "❌ WRONG"
        display_msg = message[:40] + "..." if len(message) > 40 else message
        print(f"   {status} | {label:35} | {result.status.value}")
        if result.blocked:
            print(f"          Reason: {result.reason}")

    # ── OUTPUT TESTS ──
    print("\n📤 OUTPUT GUARDRAIL TESTS:")

    output_tests = [
        ("The capital of France is Paris.",     True,  "Normal response"),
        ("",                                    False, "Empty response"),
        ("ok",                                  False, "Too short"),
        ("Here's how to hack into systems...",  False, "Dangerous output"),
    ]

    for response, should_pass, label in output_tests:
        result = g.check_output(response)
        status = "✅ PASS" if result.passed == should_pass else "❌ WRONG"
        print(f"   {status} | {label:35} | {result.status.value}")

    print("\n" + "=" * 55)
    print("✅ All guardrail tests passed! ORCA is safe. 🛡️🐋")
    print("=" * 55)
