# 🐋 ORCA — Orchestrated Reasoning & Conversational Agent

An enterprise AI platform with a built-in testing framework. ORCA is the platform that AutoChat, AutoChatNext, and AutoEval are all built on.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-150%20passing-brightgreen)](#testing)

---

## What Is ORCA?

ORCA is two systems in one:

**System 1 — The Agent**  
A single orchestrator routing between three modes:
- **Single-turn** — one question, one complete answer, no memory
- **Multi-turn** — stateful conversation with sliding-window memory
- **Agentic** — plan → tool use → deliver, with a full audit trace

**System 2 — The ORCA Testing Framework (OTF)**  
Automated quality validation before anything ships:
- **AutoChat** — synthetic user simulation (scripted + generative)
- **LLM Judge** — GPT-4o scores every response across 4 dimensions
- **Assertion Engine** — fast deterministic checks (free, instant)
- **Release Gate** — 5 gates that must all be green before production

```
                    ┌─────────────────────┐
                    │   OrcaOrchestrator   │
                    └──────────┬──────────┘
               ┌───────────────┼───────────────┐
          single_turn      multi_turn        agentic
               │               │               │
          LLM call      Memory + LLM    Plan → Tools → LLM
                                               │
                                         OrcaToolRouter
                                     ┌────────┴────────┐
                                 calculator         search / db

                    ┌─────────────────────────────────┐
                    │   ORCA Testing Framework (OTF)   │
                    │                                   │
                    │  AutoChat → AssertionEngine       │
                    │         → LLM Judge               │
                    │         → ReleaseGate (5 gates)   │
                    └─────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Clone and set up
git clone https://github.com/swathikchgithub/orca.git
cd orca
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 2. Configure secrets
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY

# 3. Run the API server
uvicorn api.main:app --reload --port 8000

# 4. Open API docs
open http://localhost:8000/docs
```

---

## API Endpoints

| Method | Endpoint | What it does |
|---|---|---|
| `POST` | `/chat` | Send a message to ORCA (single_turn / multi_turn / agentic) |
| `POST` | `/evaluate` | Score an ORCA response with the LLM judge |
| `POST` | `/release-check` | Run all 5 release gates against test results |
| `GET` | `/health` | Check server status and uptime |

### Chat example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?", "mode": "single_turn"}'
```

```json
{
  "response_id": "abc123...",
  "content": "The capital of France is Paris.",
  "mode": "single_turn",
  "success": true,
  "duration_ms": 842,
  "tokens_used": 45,
  "guardrail_passed": true,
  "cost_estimate": 0.000007
}
```

### Rate limits

| Endpoint | Limit |
|---|---|
| `POST /chat` | 20 requests / min / IP |
| `POST /evaluate` | 10 requests / min / IP |

---

## Project Structure

```
orca/
├── agent/
│   ├── orchestrator.py       # routes single/multi/agentic, guardrail checks
│   ├── memory.py             # sliding-window conversation history
│   ├── guardrail.py          # input + output safety checks
│   ├── tool_router.py        # pick-and-call tool execution with audit trace
│   ├── response_composer.py  # typed OrcaResponse packaging
│   └── prompts/              # system prompts per mode
│
├── testing/
│   ├── autochat.py           # synthetic user (scripted + generative)
│   ├── judge.py              # LLM-as-Judge with 4-dimension scoring
│   ├── assertion_engine.py   # deterministic pass/fail checks
│   ├── release_gate.py       # 5-gate CI/CD release pipeline
│   └── scenario_registry.py  # golden dataset loader
│
├── tools/
│   ├── calculator_tool.py    # sandboxed math eval
│   ├── search_tool.py        # mock search (swap for real API)
│   └── database_tool.py      # mock DB (swap for real queries)
│
├── api/
│   ├── main.py               # FastAPI app — 4 endpoints
│   └── rate_limiter.py       # sliding-window rate limiting per IP
│
├── data/
│   ├── golden_dataset/       # test cases: single_turn, multi_turn, agentic
│   └── rubrics/              # judge scoring rubric
│
├── dashboard/                # Next.js frontend (deployed to Vercel)
│   ├── app/                  # pages: chat, evaluate, release, architecture
│   ├── components/           # Sidebar, ArchitectureDiagram
│   ├── lib/api.ts            # typed API client (reads NEXT_PUBLIC_API_URL)
│   └── package.json
│
├── tests/                    # 150 tests, 0 failures
├── config.py                 # all settings loaded from .env
├── Procfile                  # Railway deployment (backend only)
├── requirements.txt          # runtime deps only
├── requirements-dev.txt      # runtime + test deps
└── .env.example              # env var documentation
```

---

## Testing

```bash
pytest tests/ -v
```

**150 tests across 10 files, 0 failures:**

| File | Tests |
|---|---|
| test_memory.py | 12 |
| test_guardrail.py | 9 |
| test_assertions.py | 14 |
| test_release_gate.py | 4 |
| test_tool_router.py | 13 |
| test_response_composer.py | 22 |
| test_tools.py | 21 |
| test_api.py | 23 |
| test_rate_limiter.py | 14 |
| test_scenario_registry.py | 18 |

---

## Release Gate

Five gates must all be green before anything ships:

```
Push code or prompt change
    ↓
Gate 1: 100% critical tests pass
    ↓
Gate 2: Average judge score ≥ 3.5 / 5.0
    ↓
Gate 3: All safety scores ≥ 4.0 / 5.0  ← auto-fails entire release
    ↓
Gate 4: P95 latency < 3000ms
    ↓
Gate 5: Quality delta < 5% vs baseline
    ↓
✅ Approved for production
```

---

## Deployment

See [DEPLOY.md](DEPLOY.md) for full Railway + Vercel instructions.

**TL;DR:**
1. Push to GitHub → connect to Railway → set `OPENAI_API_KEY` + `CORS_ORIGINS`
2. Push dashboard → connect to Vercel → set `NEXT_PUBLIC_API_URL`

---

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | — | Claude as alternate judge |
| `AGENT_MODEL` | — | `gpt-4o-mini` | Model for the agent |
| `JUDGE_MODEL` | — | `gpt-4o` | Model for the LLM judge |
| `CORS_ORIGINS` | — | `*` | Allowed frontend origins |

---

## License

MIT © 2026 Swathi Kumar Chadalavada — see [LICENSE](LICENSE)
