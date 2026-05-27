# ORCA — Technical Design Document

**Version:** 1.0  
**Last Updated:** May 2026  
**Author:** Swathi Kumar Chadalavada  
**Status:** Active

---

## 1. Overview

ORCA is two systems sharing one codebase:

1. **The Agent** — a FastAPI service that routes requests through three LLM-backed modes (single-turn, multi-turn, agentic) with guardrail enforcement on every path
2. **The ORCA Testing Framework (OTF)** — a quality validation pipeline that runs synthetic conversations, scores them with an LLM judge, and gates releases through five automated checks

Both systems are designed to be extended independently: new agent modes can be added to the orchestrator without touching the testing layer, and new judge dimensions can be added without changing the agent.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI (api/main.py)                     │
│   /chat      /evaluate      /release-check      /health          │
│   RateLimiter               RateLimiter                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   OrcaOrchestrator   │
                    │  (agent/orchestra-   │
                    │       tor.py)        │
                    └──┬──────┬───────┬───┘
                       │      │       │
              single_turn  multi_turn  agentic
                       │      │       │
                 LLM call  Memory  OrcaToolRouter
                           +LLM   ┌───┴────┐
                                 calc  search/db

                    ┌─────────────────────────────────┐
                    │   ORCA Testing Framework (OTF)   │
                    │                                   │
                    │  OrcaScenarioRegistry             │
                    │      → AutoChat (scripted/gen)    │
                    │      → AssertionEngine            │
                    │      → OrcaJudge (LLM-as-Judge)  │
                    │      → OrcaReleaseGate (5 gates) │
                    └─────────────────────────────────┘
```

---

## 3. Module Contracts

### 3.1 OrcaOrchestrator (`agent/orchestrator.py`)

**Responsibility:** Route a chat request to the correct mode handler; enforce guardrails before and after the LLM call; return a typed `OrcaResponse`.

**Interface:**
```python
class OrcaOrchestrator:
    def run(self, message: str, mode: str, session_id: str | None) -> OrcaResponse
```

**Invariants:**
- Input guardrail runs before any LLM call; a blocked input returns immediately with `is_blocked=True`
- Output guardrail runs after every LLM call; a blocked output sets `is_blocked=True` on the response
- `session_id` is auto-generated (UUID4) if not provided
- `mode` must be one of `single_turn`, `multi_turn`, `agentic`; any other value raises `ValueError`
- Every call appends to the `tool_calls` trace if mode is `agentic`

**Dependencies:**
- `ConversationMemory` (injected; keyed by `session_id`)
- `OrcaGuardrail` (injected)
- `OrcaToolRouter` (injected; used only in agentic mode)
- `OrcaResponseComposer` (injected)
- OpenAI client (injected via `config.py`)

**Design pattern:** Strategy — mode handlers are functions selected at runtime by `mode` string. Adding a new mode requires adding one function and one branch in the dispatch dict, not modifying existing handlers.

---

### 3.2 ConversationMemory (`agent/memory.py`)

**Responsibility:** Store and retrieve sliding-window conversation history per session.

**Interface:**
```python
class ConversationMemory:
    def add(self, session_id: str, role: str, content: str) -> None
    def get(self, session_id: str) -> list[Message]
    def clear(self, session_id: str) -> None
```

**Invariants:**
- Window size is fixed at `N` most recent messages (configurable, default 10)
- Messages older than the window are discarded, not archived
- `get` on an unknown `session_id` returns `[]`, not an error
- In-process storage only — a process restart wipes all sessions (known limitation; Redis migration path documented in PRD)

**Complexity:**
- `add`: O(1) amortized — deque pop from left when over window
- `get`: O(N) — copy of the deque to a list

---

### 3.3 OrcaGuardrail (`agent/guardrail.py`)

**Responsibility:** Reject harmful or policy-violating input before it reaches the LLM, and flag harmful LLM output before it reaches the caller.

**Interface:**
```python
class OrcaGuardrail:
    def check_input(self, text: str) -> GuardrailResult
    def check_output(self, text: str) -> GuardrailResult
```

**`GuardrailResult` fields:**
- `passed: bool`
- `reason: str | None`

**Design note:** Current implementation is keyword/pattern based — fast and free. A future version can swap in an LLM-based classifier without changing the orchestrator, because the interface is stable (Dependency Inversion / Open-Closed).

---

### 3.4 OrcaToolRouter (`agent/tool_router.py`)

**Responsibility:** Parse the LLM's agentic response to determine which tool to call, execute it safely, and return the result with a full audit trace.

**Interface:**
```python
class OrcaToolRouter:
    def available_tools(self) -> list[str]
    def run(self, tool_name: str, params: dict) -> str
    def get_trace(self) -> list[ToolCall]
    def clear_trace(self) -> None
```

**Invariants:**
- Unknown tool name → returns an error string, does not raise
- Tool crash → caught, logged to trace as failure, returns error string (crash-safe)
- Non-dict `params` → treated as empty dict
- Every call (success or failure) appended to the audit trace

**Known fragility:** Tool dispatch currently relies on regex parsing of the LLM's free-text output to extract tool name and parameters. This is brittle if the model's output format drifts. Migration path: OpenAI function calling API (structured JSON tool calls, no parsing needed).

**Registered tools:**

| Tool | File | What it does |
|---|---|---|
| `calculator` | `tools/calculator_tool.py` | Sandboxed `eval` — math only; `__import__` and builtins blocked |
| `search` | `tools/search_tool.py` | Mock search returning canned results by topic keyword |
| `database` | `tools/database_tool.py` | Mock DB query returning fixture data by table/field |

**Security:** The calculator sandbox blocks `__import__`, `__builtins__`, and all names not in a whitelist. No arbitrary code can be executed. Production use should replace the mock tools with real, authenticated API clients.

---

### 3.5 OrcaResponseComposer (`agent/response_composer.py`)

**Responsibility:** Package LLM output, metadata, and status flags into a typed `OrcaResponse`.

**Interface:**
```python
class OrcaResponseComposer:
    def compose(self, content: str, mode: str, session_id: str,
                tokens_used: int, tool_calls: list) -> OrcaResponse
    def compose_blocked(self, reason: str, session_id: str) -> OrcaResponse
    def compose_error(self, session_id: str) -> OrcaResponse
```

**`OrcaResponse` fields:**
```python
response_id:       str       # UUID4
content:           str       # stripped LLM output or safe error message
mode:              str
success:           bool
guardrail_passed:  bool
is_blocked:        bool
duration_ms:       int
tokens_used:       int
cost_estimate:     float     # tokens_used × per-token rate
session_id:        str
tool_calls:        list[dict]
blocked_reason:    str | None
```

**Design note:** Every output path (success, blocked, error) routes through a dedicated method. The orchestrator never constructs `OrcaResponse` directly — it always goes through the composer. This is Single Responsibility: the composer owns the response shape contract.

---

### 3.6 OrcaJudge (`testing/judge.py`)

**Responsibility:** Score an ORCA response across 4 dimensions using GPT-4o as the judge model.

**Interface:**
```python
class OrcaJudge:
    def evaluate(self, scenario: TestScenario, response: OrcaResponse) -> JudgeResult
```

**Scoring dimensions and weights:**
| Dimension | Weight | Auto-fail threshold |
|---|---|---|
| Accuracy | 35% | — |
| Helpfulness | 30% | — |
| Safety | 25% | < 4.0 blocks release |
| Clarity | 10% | — |

**`JudgeResult` fields:**
- `overall_score: float` — weighted average, 1–5
- `dimension_scores: dict[str, float]`
- `passed: bool` — True if `overall_score >= 3.5`
- `feedback: str`

**Cost note:** Every `/evaluate` call invokes GPT-4o. The rate limiter caps this at 10 calls/min/IP to protect cost budget.

---

### 3.7 AssertionEngine (`testing/assertion_engine.py`)

**Responsibility:** Run deterministic pass/fail checks against a response string without any LLM call.

**Supported assertion types:**
| Type | Check |
|---|---|
| `contains` | Substring present |
| `not_contains` | Substring absent |
| `starts_with` | Prefix match |
| `length_min` | `len(response) >= n` |
| `length_max` | `len(response) <= n` |
| `regex_match` | `re.search(pattern, response)` is truthy |

**Complexity:** O(k) per assertion where k = len(response). All checks are O(1) or O(k) — never O(n²).

---

### 3.8 OrcaReleaseGate (`testing/release_gate.py`)

**Responsibility:** Enforce 5 quality gates before a release is approved. Gates are ordered: an early failure short-circuits the remaining gates.

**Interface:**
```python
class OrcaReleaseGate:
    def check(self, results: list[TestResult], version: str) -> GateReport
```

**Gate definitions:**
| Gate | Check | Fail behavior |
|---|---|---|
| G1 | All critical tests pass (0 failures) | Blocks G2–G5 |
| G2 | Average judge score ≥ 3.5 | Blocks G3–G5 |
| G3 | All safety scores ≥ 4.0 | **Auto-fails entire release** |
| G4 | P95 latency < 3000ms | Blocks G5 |
| G5 | Quality delta vs baseline < 5% | — |

**`GateReport` fields:**
- `version: str`
- `approved: bool`
- `gate_details: dict[str, GateResult]`
- `timestamp: str`

---

### 3.9 OrcaScenarioRegistry (`testing/scenario_registry.py`)

**Responsibility:** Load and filter test scenarios from the golden dataset on disk.

**Interface:**
```python
class OrcaScenarioRegistry:
    def get_all(self) -> list[TestScenario]
    def get_by_id(self, id: str) -> TestScenario | None
    def get_by_mode(self, mode: str) -> list[TestScenario]
    def get_by_priority(self, priority: str) -> list[TestScenario]
    def get_by_tag(self, tag: str) -> list[TestScenario]
    def get_critical(self) -> list[TestScenario]
    def get_smoke_tests(self) -> list[TestScenario]
```

**`TestScenario` fields:**
- `id: str`
- `mode: str` — `single_turn` | `multi_turn` | `agentic`
- `description: str`
- `priority: str` — `critical` | `high` | `medium` | `low`
- `tags: list[str]`
- `input: str | None` — for single-turn scenarios
- `turns: list[dict] | None` — for multi-turn scenarios

**Golden dataset location:** `data/golden_dataset/` — JSON files partitioned by mode.

---

## 4. Data Flow

### 4.1 Single-Turn Request

```
POST /chat {message, mode: "single_turn"}
  → RateLimiter.check (429 if over limit)
  → OrcaOrchestrator.run(message, "single_turn", session_id=None)
      → OrcaGuardrail.check_input(message)
          blocked? → OrcaResponseComposer.compose_blocked()
      → OpenAI chat completion (no memory, no tools)
      → OrcaGuardrail.check_output(llm_response)
          blocked? → OrcaResponseComposer.compose_blocked()
      → OrcaResponseComposer.compose(content, tokens, ...)
  → HTTP 200 {OrcaResponse}
```

### 4.2 Multi-Turn Request

```
POST /chat {message, mode: "multi_turn", session_id: "abc"}
  → RateLimiter.check
  → OrcaOrchestrator.run(message, "multi_turn", session_id="abc")
      → OrcaGuardrail.check_input(message)
      → ConversationMemory.get("abc")       # load history
      → OpenAI chat completion (history + new message)
      → OrcaGuardrail.check_output(response)
      → ConversationMemory.add("abc", "user", message)
      → ConversationMemory.add("abc", "assistant", response)
      → OrcaResponseComposer.compose(...)
  → HTTP 200 {OrcaResponse}
```

### 4.3 Agentic Request

```
POST /chat {message, mode: "agentic"}
  → RateLimiter.check
  → OrcaOrchestrator.run(message, "agentic", session_id=None)
      → OrcaGuardrail.check_input(message)
      → OpenAI chat completion (plan prompt → produces tool calls)
      → OrcaToolRouter.run(tool_name, params)  [1..N times]
          → each call appended to audit trace
      → OpenAI chat completion (plan + tool results → final answer)
      → OrcaGuardrail.check_output(final_answer)
      → OrcaResponseComposer.compose(content, tool_calls=trace)
  → HTTP 200 {OrcaResponse + tool_calls trace}
```

### 4.4 Release Check

```
POST /release-check {version, test_results}
  → OrcaReleaseGate.check(results, version)
      → Gate 1: critical tests 100%?
      → Gate 2: average score ≥ 3.5?
      → Gate 3: all safety ≥ 4.0?  (auto-fail)
      → Gate 4: P95 latency < 3000ms?
      → Gate 5: delta vs baseline < 5%?
  → HTTP 200 {approved: bool, gate_details: {...}}
```

---

## 5. API Contract

### `POST /chat`

**Request:**
```json
{
  "message": "string (required)",
  "mode": "single_turn | multi_turn | agentic (default: single_turn)",
  "session_id": "string (optional — auto-generated if absent)"
}
```

**Response:**
```json
{
  "response_id": "uuid",
  "content": "string",
  "mode": "string",
  "success": true,
  "guardrail_passed": true,
  "is_blocked": false,
  "duration_ms": 842,
  "tokens_used": 45,
  "cost_estimate": 0.000007,
  "session_id": "string",
  "tool_calls": []
}
```

**Error responses:**
- `400` — invalid `mode`
- `422` — missing `message`
- `429` — rate limit exceeded (+ `Retry-After: 60` header)

### `POST /evaluate`

**Request:**
```json
{
  "scenario_id": "string (required)",
  "response": "string (required)"
}
```

**Response:**
```json
{
  "overall_score": 4.1,
  "dimension_scores": {
    "accuracy": 4.5,
    "helpfulness": 4.0,
    "safety": 4.2,
    "clarity": 3.8
  },
  "passed": true,
  "feedback": "string"
}
```

### `POST /release-check`

**Request:**
```json
{
  "version": "string (required)",
  "test_results": [
    {
      "scenario_id": "string",
      "is_critical": false,
      "passed": true,
      "judge_score": 4.1,
      "safety_score": 4.5,
      "latency_ms": 1200
    }
  ]
}
```

**Response:**
```json
{
  "approved": true,
  "version": "string",
  "gate_details": {
    "gate_1_critical_tests": {"passed": true, "detail": "..."},
    "gate_2_judge_score":    {"passed": true, "detail": "..."},
    "gate_3_safety":         {"passed": true, "detail": "..."},
    "gate_4_latency":        {"passed": true, "detail": "..."},
    "gate_5_regression":     {"passed": true, "detail": "..."}
  },
  "timestamp": "ISO8601"
}
```

---

## 6. Configuration

All settings loaded from environment variables via `config.py`. No hardcoded values in application code.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | required | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Claude as alternate judge (optional) |
| `AGENT_MODEL` | `gpt-4o-mini` | Model for agent LLM calls |
| `JUDGE_MODEL` | `gpt-4o` | Model for LLM judge |
| `CORS_ORIGINS` | `*` | Allowed frontend origins (restrict in prod) |
| `PORT` | `8000` | Injected by Railway; do not set manually |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## 7. Security Design

### Input Validation
- All requests validated by Pydantic models at the FastAPI layer
- Unknown fields rejected (strict schema parsing)
- Guardrail blocks prompt injection patterns before the LLM sees them

### Rate Limiting (OWASP A07)
- Sliding-window per-IP limiter
- Keys on `X-Forwarded-For` when behind a proxy (correct real-client IP)
- Fails open (no block) if the limiter itself throws — availability over blocking

### CORS (OWASP A05)
- `allow_methods=["GET", "POST"]` — not `*`
- `allow_headers=["Content-Type"]` — not `*`
- `allow_origins` configurable via `CORS_ORIGINS` env var

### Secrets (OWASP A02)
- No secrets in source code
- `.env` is gitignored; `.env.example` has placeholder values only
- OpenAI key loaded from environment at runtime, never logged

### Calculator Sandbox (OWASP A03)
- `eval()` restricted to a whitelist of safe names
- `__import__`, `__builtins__`, `open`, `exec` all blocked
- User-controlled input never executed as shell commands

### No Stack Traces in Production (OWASP A05)
- `compose_error` returns a generic safe message to the caller
- Internal error details logged server-side only, never in the HTTP response

---

## 8. Testing Architecture

### Test Suite: 150 tests, 0 failures

All tests are in `tests/`. Run with `pytest tests/ -v`.

| File | Tests | What it covers |
|---|---|---|
| `test_memory.py` | 12 | `ConversationMemory` — add, get, sliding window, clear, unknown session |
| `test_guardrail.py` | 9 | Input and output safety checks, bypass patterns |
| `test_assertions.py` | 14 | All 6 assertion types: positive and negative cases |
| `test_release_gate.py` | 4 | All 5 gates: approved path, low safety block, critical failure |
| `test_tool_router.py` | 13 | Registry, run, crash safety, non-dict params, trace lifecycle |
| `test_response_composer.py` | 22 | `compose`, `compose_blocked`, `compose_error` — all fields |
| `test_tools.py` | 21 | Calculator sandbox, search, database — success + error paths |
| `test_api.py` | 23 | All 4 HTTP endpoints — happy path, auth, validation, errors |
| `test_rate_limiter.py` | 14 | Allow, block, 429 shape, X-Forwarded-For, per-endpoint limits |
| `test_scenario_registry.py` | 18 | Load, filter by mode/priority/tag, field validation |

### Test Isolation

- **Unit tests**: all dependencies mocked; no real LLM calls, no real filesystem I/O
- **API tests**: use `httpx.AsyncClient` + `ASGITransport` + manually initialized `app.state`; bypasses lifespan to avoid creating real OpenAI clients
- **Rate limiter tests**: autouse fixture calls `clear_buckets()` before and after each test — state is fully isolated
- **No test order dependencies**: every test arranges its own state; no shared mutable globals

### pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Async fixtures work without per-test `@pytest.mark.asyncio` decorators.

---

## 9. Deployment Architecture

```
GitHub push
  → Railway (Python/FastAPI backend)
       reads Procfile: uvicorn api.main:app --host 0.0.0.0 --port $PORT
       env: OPENAI_API_KEY, AGENT_MODEL, JUDGE_MODEL, CORS_ORIGINS
  → Vercel (Next.js dashboard)
       env: NEXT_PUBLIC_API_URL = https://<railway-url>.up.railway.app
```

**Known deployment constraints:**
1. Sessions are in-process — Railway restart wipes multi-turn history
2. Single instance — no horizontal scaling until Redis session store added
3. Tool calls use regex parsing — migrate to function calling API before scaling

See [DEPLOY.md](DEPLOY.md) for step-by-step instructions.

---

## 10. Known Limitations and Migration Paths

| Limitation | Current state | Migration |
|---|---|---|
| In-process session memory | Lost on restart | Add `REDIS_URL`; port `ConversationMemory` to use `redis-py` |
| Regex tool parsing | Fragile if model format drifts | Migrate to OpenAI function calling API |
| Synchronous responses | No streaming | Add SSE endpoint; requires async LLM streaming + judge refactor |
| Single instance | No horizontal scale | Redis sessions first; then Railway replicas |
| Mock tools | Not connected to real APIs | Swap `search_tool.py` and `database_tool.py` for real clients |
