"""
agent/prompts/prompt_loader.py — Loads ORCA's system prompts from .txt files

🧠 What this does (5-year-old version):
   The 3 prompt files are like instruction manuals stored in a drawer.
   This file is the person who opens the drawer, finds the right manual,
   reads it, and hands it to ORCA before every conversation.

🏗️ Why load from .txt files instead of hardcoding strings in Python?
   Because prompts change ALL THE TIME during development.
   Product managers, engineers, and testers all tweak prompts.
   If prompts are in .txt files → anyone can edit without touching Python code.
   If prompts are hardcoded → you need a developer for every tiny word change.
   That's a $1B lesson right there. 💡
"""

import os
import config
from typing import Literal

# The 3 valid ORCA modes — nothing else is allowed
AgentMode = Literal["single_turn", "multi_turn", "agentic"]

# Map each mode to its prompt filename
PROMPT_FILES: dict[str, str] = {
    "single_turn" : "single_turn.txt",
    "multi_turn"  : "multi_turn.txt",
    "agentic"     : "agentic.txt",
}


def load_prompt(mode: AgentMode) -> str:
    """
    Load and return the system prompt for a given ORCA mode.

    Args:
        mode : one of "single_turn", "multi_turn", "agentic"

    Returns:
        The full prompt text as a string

    Raises:
        ValueError  : if mode is not valid
        FileNotFoundError : if the prompt file is missing
    """
    # Validate the mode
    if mode not in PROMPT_FILES:
        raise ValueError(
            f"❌ Unknown mode '{mode}'. "
            f"Valid modes: {list(PROMPT_FILES.keys())}"
        )

    # Build the full path to the prompt file
    prompt_path = os.path.join(config.PROMPTS_DIR, PROMPT_FILES[mode])

    # Check the file actually exists
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(
            f"❌ Prompt file not found: {prompt_path}\n"
            f"   Make sure agent/prompts/{PROMPT_FILES[mode]} exists."
        )

    # Read and return the prompt
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    # Validate it's not empty
    if not prompt:
        raise ValueError(f"❌ Prompt file is empty: {prompt_path}")

    return prompt


def load_all_prompts() -> dict[str, str]:
    """
    Load all 3 prompts at once.
    Useful for validation and testing.

    Returns:
        {"single_turn": "...", "multi_turn": "...", "agentic": "..."}
    """
    return {mode: load_prompt(mode) for mode in PROMPT_FILES}


def get_prompt_stats() -> dict[str, dict]:
    """
    Returns stats about each prompt — useful for debugging.

    Returns:
        {
          "single_turn": {"chars": 1200, "lines": 39, "words": 210},
          ...
        }
    """
    stats = {}
    for mode, filename in PROMPT_FILES.items():
        prompt_path = os.path.join(config.PROMPTS_DIR, filename)
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                text = f.read()
            stats[mode] = {
                "chars" : len(text),
                "lines" : len(text.splitlines()),
                "words" : len(text.split()),
                "file"  : filename,
            }
        else:
            stats[mode] = {"error": "file not found"}
    return stats


# ─────────────────────────────────────────────
# ✅ TEST IT — run: python agent/prompts/prompt_loader.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("📝 Testing ORCA Prompt Loader")
    print("=" * 55)

    # Test 1: Load each prompt
    for mode in ["single_turn", "multi_turn", "agentic"]:
        prompt = load_prompt(mode)
        first_line = prompt.split('\n')[0]
        print(f"\n✅ [{mode}] loaded — first line: {first_line[:60]}")

    # Test 2: Show stats
    print("\n📊 Prompt Stats:")
    stats = get_prompt_stats()
    for mode, s in stats.items():
        print(f"   {mode:15} → {s['lines']} lines, {s['words']} words")

    # Test 3: Test bad mode error
    print("\n🛡️  Testing error handling...")
    try:
        load_prompt("invalid_mode")
    except ValueError as e:
        print(f"✅ Correctly rejected bad mode: {e}")

    # Test 4: Load all at once
    all_prompts = load_all_prompts()
    print(f"\n✅ load_all_prompts() returned {len(all_prompts)} prompts")

    print("\n" + "=" * 55)
    print("✅ All prompt tests passed! ORCA knows who it is. 📝🐋")
    print("=" * 55)
