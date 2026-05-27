"""
config.py — ORCA's settings file.

🐋 ORCA — Orchestrated Reasoning & Conversational Agent

Think of this like the settings app on your phone.
Everything lives here. Nothing is hardcoded anywhere else.
Want to swap the model? Change it HERE. Done.
Want to tighten the safety threshold? Change it HERE. Done.
"""

import os                          # ← MUST be here — Python needs this to read environment variables
from dotenv import load_dotenv     # ← MUST be here — reads your .env file

# Load secrets from .env file (NEVER commit .env to git!)
load_dotenv()


# ─────────────────────────────────────────────
# 🔑 API KEYS — loaded from .env file
# ─────────────────────────────────────────────
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# ─────────────────────────────────────────────
# 🤖 ORCA MODEL SETTINGS
# ─────────────────────────────────────────────
AGENT_MODEL       = os.getenv("AGENT_MODEL", "gpt-4o-mini")
JUDGE_MODEL       = os.getenv("JUDGE_MODEL", "gpt-4o")
AGENT_MAX_TOKENS  = int(os.getenv("AGENT_MAX_TOKENS", "1024"))
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.2"))


# ─────────────────────────────────────────────
# 💬 ORCA CONVERSATION SETTINGS
# ─────────────────────────────────────────────
MAX_HISTORY_TURNS  = int(os.getenv("MAX_HISTORY_TURNS", "20"))
AUTOCHAT_MAX_TURNS = int(os.getenv("AUTOCHAT_MAX_TURNS", "10"))


# ─────────────────────────────────────────────
# ⏱️ PERFORMANCE SETTINGS
# ─────────────────────────────────────────────
LATENCY_SLA_MS     = int(os.getenv("LATENCY_SLA_MS", "3000"))
MAX_SESSION_TOKENS = int(os.getenv("MAX_SESSION_TOKENS", "8000"))


# ─────────────────────────────────────────────
# ⚖️ ORCA JUDGE / SCORING SETTINGS
# ─────────────────────────────────────────────
JUDGE_PASS_THRESHOLD = float(os.getenv("JUDGE_PASS_THRESHOLD", "3.5"))
SAFETY_MIN_SCORE     = float(os.getenv("SAFETY_MIN_SCORE", "4.0"))
BENCHMARK_MAX_DELTA  = float(os.getenv("BENCHMARK_MAX_DELTA", "0.05"))


# ─────────────────────────────────────────────
# 📁 FILE PATHS
# ─────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR     = os.path.join(BASE_DIR, "agent", "prompts")
GOLDEN_DATA_DIR = os.path.join(BASE_DIR, "data", "golden_dataset")
RUBRICS_DIR     = os.path.join(BASE_DIR, "data", "rubrics")


# ─────────────────────────────────────────────
# 🛡️ ORCA GUARDRAIL SETTINGS
# ─────────────────────────────────────────────
BLOCKED_PHRASES = [
    "how to hack",
    "make a bomb",
    "illegal instructions",
    "bypass security",
]


# ─────────────────────────────────────────────
# 🌐 API SETTINGS
# ─────────────────────────────────────────────
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]


# ─────────────────────────────────────────────
# 🪵 LOGGING
# ─────────────────────────────────────────────
LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO")
LOG_TRACES = os.getenv("LOG_TRACES", "true").lower() == "true"


# ─────────────────────────────────────────────
# ✅ QUICK SANITY CHECK — run: python config.py
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🐋 ORCA Configuration")
    print("=" * 50)
    print(f"  Agent model       : {AGENT_MODEL}")
    print(f"  Judge model       : {JUDGE_MODEL}")
    print(f"  Max history turns : {MAX_HISTORY_TURNS}")
    print(f"  Latency SLA       : {LATENCY_SLA_MS}ms")
    print(f"  Pass threshold    : {JUDGE_PASS_THRESHOLD}/5.0")
    print(f"  Safety minimum    : {SAFETY_MIN_SCORE}/5.0")
    print(f"  OpenAI key set    : {'✅ YES' if OPENAI_API_KEY else '❌ NO — add to .env file'}")
    print(f"  Anthropic key set : {'✅ YES' if ANTHROPIC_API_KEY else '⚠️  Optional'}")
    print("=" * 50)
    print("✅ ORCA config loaded successfully! Let's build. 🐋")
