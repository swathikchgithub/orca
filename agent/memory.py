# ============================================================
# 🐋 ORCA — Conversation Memory
# agent/memory.py
# ============================================================

import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from config import MAX_HISTORY_TURNS, AGENT_MAX_TOKENS


# ── Single Message ───────────────────────────────────────────
@dataclass
class Message:
    role    : str    # "user" / "assistant" / "system"
    content : str
    tokens  : int = 0

    def __post_init__(self):
        # ✅ FIX 1 — Raise ValueError on empty content
        if not self.content or not self.content.strip():
            raise ValueError(
                f"❌ Cannot create message with empty content."
            )
        # Estimate tokens (rough: 1 token ≈ 4 chars)
        self.tokens = len(self.content) // 4


# ── Conversation Memory ──────────────────────────────────────
class ConversationMemory:
    """
    ORCA's notepad — stores the full conversation history.
    Like a human's short-term memory for one session.
    """

    def __init__(
        self,
        system_prompt : str,
        session_id    : Optional[str] = None,
        max_turns     : int = MAX_HISTORY_TURNS
    ):
        self.session_id  = session_id or f"session_{int(time.time())}"
        self.max_turns   = max_turns
        self.max_tokens  = AGENT_MAX_TOKENS * 8
        self._messages   : List[Message] = []

        # Always start with system prompt
        self._messages.append(
            Message(role="system", content=system_prompt)
        )

    # ✅ FIX 2 — message_count is a @property (no brackets needed)
    @property
    def message_count(self) -> int:
        """Total number of messages including system prompt."""
        return len(self._messages)

    def add_message(self, role: str, content: str) -> None:
        """Save a new message to memory."""
        if not content or not content.strip():
            raise ValueError("❌ Cannot save an empty message to memory.")

        self._messages.append(Message(role=role, content=content))

        # Trim old messages if over limit (keep system prompt always)
        non_system = [m for m in self._messages if m.role != "system"]
        if len(non_system) > self.max_turns * 2:
            system_msgs = [m for m in self._messages if m.role == "system"]
            self._messages = system_msgs + non_system[-(self.max_turns * 2):]

    def get_history_for_llm(self) -> List[Dict]:
        """Return conversation as list of dicts for OpenAI API."""
        return [
            {"role": m.role, "content": m.content}
            for m in self._messages
        ]

    def get_last_n_turns(self, n: int) -> List[Dict]:
        """Get only the last N turns (user+assistant pairs)."""
        system = [m for m in self._messages if m.role == "system"]
        others = [m for m in self._messages if m.role != "system"]
        recent = others[-(n * 2):]
        return [
            {"role": m.role, "content": m.content}
            for m in system + recent
        ]

    def clear(self) -> None:
        """Reset conversation — keep system prompt only."""
        system_msgs    = [m for m in self._messages if m.role == "system"]
        self._messages = system_msgs

    def token_count(self) -> int:
        """Estimate total tokens used."""
        return sum(m.tokens for m in self._messages)

    def summary(self) -> str:
        """Debug summary of memory state."""
        user_count      = sum(1 for m in self._messages if m.role == "user")
        assistant_count = sum(1 for m in self._messages if m.role == "assistant")
        tokens          = self.token_count()
        budget_status   = "✅ OK" if tokens < self.max_tokens else "⚠️  NEAR LIMIT"

        return (
            f"\n🧠 ORCA Memory | Session: {self.session_id}\n"
            f"   Messages : {self.message_count} total "
            f"({user_count} user, {assistant_count} assistant)\n"
            f"   Tokens   : ~{tokens} estimated\n"
            f"   Budget   : {tokens}/{self.max_tokens} ({budget_status})"
        )

    def __repr__(self):
        return (
            f"ConversationMemory("
            f"messages={self.message_count}, "
            f"tokens~{self.token_count()})"
        )


    # ── Print what ORCA sends to LLM ─────────────────────────────
    def print_history(self) -> None:
        """Debug — print full conversation."""
        print("\n📤 What ORCA sends to the LLM:")
        icons = {"system": "⚙️ ", "user": "👤", "assistant": "🐋"}
        for i, m in enumerate(self._messages, 1):
            icon = icons.get(m.role, "❓")
            print(f"   {i}. {icon} [{m.role:<9}] {m.content[:60]}")


# ── Self-Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("🧠 Testing ORCA Memory System")
    print("=" * 55)

    mem = ConversationMemory(
        system_prompt = "You are ORCA, a helpful AI assistant.",
        session_id    = "test_session"
    )
    print(f"\n✅ Memory created: {mem}")

    print("\n📝 Simulating conversation...")
    mem.add_message("user",      "Hi! My name is Swathi.")
    mem.add_message("assistant", "Nice to meet you, Swathi! How can I help?")
    mem.add_message("user",      "What is 2 + 2?")
    mem.add_message("assistant", "2 + 2 = 4!")
    mem.add_message("user",      "What is my name?")

    print(f"\n✅ After conversation: {mem}")
    print(mem.summary())

    print("\n📤 What ORCA sends to the LLM:")
    icons = {"system": "⚙️ ", "user": "👤", "assistant": "🐋"}
    for i, msg in enumerate(mem.get_history_for_llm(), 1):
        icon = icons.get(msg["role"], "❓")
        print(f"   {i}. {icon} [{msg['role']:<9}] {msg['content']}")

    print("\n🗑️  Clearing conversation (keeping system prompt)...")
    mem.clear()
    print(f"✅ After clear: {mem}")

    print("\n🛡️  Testing error handling...")
    try:
        mem.add_message("user", "")
    except ValueError as e:
        print(f"✅ Correctly rejected empty message: {e}")

    print("\n" + "=" * 55)
    print("✅ All memory tests passed! ORCA has a brain. 🧠🐋")
    print("=" * 55)