# ============================================================
# 🐋 ORCA — Memory Tests
# tests/test_memory.py
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.memory import ConversationMemory, Message


class TestMessage:
    def test_message_creation(self):
        """Message stores role and content correctly."""
        m = Message(role="user", content="Hello ORCA!")
        assert m.role    == "user"
        assert m.content == "Hello ORCA!"

    def test_message_token_estimate(self):
        """Token estimate is content length divided by 4."""
        m = Message(role="user", content="Hello")
        assert m.tokens == len("Hello") // 4

    def test_message_rejects_empty(self):
        """Message raises error on empty content."""
        with pytest.raises(ValueError):
            Message(role="user", content="")

    def test_message_roles(self):
        """All 3 roles work correctly."""
        for role in ["user", "assistant", "system"]:
            m = Message(role=role, content="test content here")
            assert m.role == role


class TestConversationMemory:
    def test_memory_creates_with_system_prompt(self, sample_memory):
        """Memory starts with 1 system message."""
        assert sample_memory.message_count == 1

    def test_add_user_message(self, sample_memory):
        """Adding user message increases count."""
        sample_memory.add_message("user", "Hello!")
        assert sample_memory.message_count == 2

    def test_add_assistant_message(self, sample_memory):
        """Adding assistant message increases count."""
        sample_memory.add_message("assistant", "Hi there!")
        assert sample_memory.message_count == 2

    def test_multi_turn_memory(self, sample_memory):
        """Memory retains full conversation."""
        sample_memory.add_message("user",      "My name is Swathi.")
        sample_memory.add_message("assistant", "Nice to meet you Swathi!")
        sample_memory.add_message("user",      "What is my name?")
        assert sample_memory.message_count == 4

    def test_get_history_for_llm(self, sample_memory):
        """History returns list of dicts with role and content."""
        sample_memory.add_message("user", "Hello!")
        history = sample_memory.get_history_for_llm()
        assert isinstance(history, list)
        assert all("role" in h and "content" in h for h in history)

    def test_clear_keeps_system_prompt(self, sample_memory):
        """Clearing memory keeps system prompt."""
        sample_memory.add_message("user",      "Hello!")
        sample_memory.add_message("assistant", "Hi!")
        sample_memory.clear()
        assert sample_memory.message_count == 1

    def test_rejects_empty_message(self, sample_memory):
        """Memory rejects empty messages."""
        with pytest.raises(ValueError):
            sample_memory.add_message("user", "")

    def test_token_count_increases(self, sample_memory):
        """Token count goes up as messages are added."""
        before = sample_memory.token_count()
        sample_memory.add_message("user", "This is a longer message for testing.")
        after = sample_memory.token_count()
        assert after > before