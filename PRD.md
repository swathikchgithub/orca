# ORCA — Product Requirements Document

**Version:** 1.0  
**Last Updated:** May 2026  
**Author:** Swathi Kumar Chadalavada  
**Status:** Active

---

## 1. Problem

Building production AI agents is deceptively hard. The core challenge isn't the LLM call — it's everything around it: memory management across turns, safe tool execution, guardrail enforcement, and verifying that quality holds after every prompt or model change.

Most teams ship agents without a systematic way to catch regressions before they reach users. When a prompt change silently breaks multi-turn coherence, or a model update drops accuracy on safety-critical inputs, teams find out from user complaints — not from tests.

ORCA solves both problems: it provides a production-ready agent with three routing modes, and a built-in testing framework that validates quality automatically before any release.

---

## 2. Users

### Primary: AI/ML Engineers
Engineers building or operating LLM-powered products who need:
- A reference implementation of a multi-mode agent they can fork and adapt
- A testing harness that catches quality regressions before production
- An API they can point existing frontends at

### Secondary: Platform Teams
Teams evaluating AI infrastructure who need:
- A deployable agent backend with observable quality metrics
- A release gate they can integrate into CI/CD

### Not in scope
- End users interacting directly with ORCA as a consumer product
- Non-technical users — this is an engineering tool

---

## 3. Goals

| # | Goal | Success Signal |
|---|---|---|
| G1 | Ship a multi-mode agent with guardrails | Single, multi, and agentic modes all respond correctly in production |
| G2 | Catch quality regressions before release | 5-gate release check blocks bad deploys before they hit production |
| G3 | Make testing fast enough to run on every commit | Full test suite < 60 seconds on a laptop |
| G4 | Keep deployment friction low | Deploy to Railway + Vercel in < 30 minutes from a clean account |
| G5 | Make quality metrics observable | LLM judge scores visible per response via the `/evaluate` endpoint |

---

## 4. Non-Goals

- **No fine-tuning** — ORCA uses foundation models as-is; fine-tuning is out of scope
- **No streaming** — responses are synchronous; streaming SSE is a future enhancement
- **No persistent sessions** — multi-turn memory is in-process only; Redis persistence is a known limitation
- **No user auth** — ORCA does not authenticate callers; auth is left to the deployer
- **No UI** — ORCA is an API; the `orca-dashboard` Next.js app is a separate companion project

---

## 5. Features

### 5.1 Agent — Three Routing Modes

**Single-Turn**
- One stateless LLM call per request
- No session ID required
- Fastest path; use for one-shot Q&A, search, classification

**Multi-Turn**
- Stateful conversation via sliding-window memory (last N messages)
- Requires a `session_id` to tie turns together
- Memory stored in-process (not durable across restarts)

**Agentic**
- Full plan → tool use → deliver loop
- Tool router selects from: `calculator`, `search`, `database`
- Every tool call appended to an audit trace on the response
- Guardrail checked on both input and output

### 5.2 Guardrail

- Blocks requests that contain harmful, hateful, or injection-pattern text
- Blocks responses that the LLM should not have produced
- Auto-fails release gate if any safety score < 4.0

### 5.3 ORCA Testing Framework (OTF)

**AutoChat** — synthetic user simulator
- *Scripted mode*: runs predefined turn sequences from the golden dataset
- *Generative mode*: LLM generates follow-up turns dynamically

**LLM Judge** — GPT-4o scores every response across 4 dimensions:
| Dimension | Weight |
|---|---|
| Accuracy | 35% |
| Helpfulness | 30% |
| Safety | 25% |
| Clarity | 10% |

**Assertion Engine** — 6 deterministic check types (fast, free, no LLM cost):
- `contains` / `not_contains`
- `starts_with`
- `length_min` / `length_max`
- `regex_match`

**Release Gate** — 5 gates that all must be green before production:
1. 100% of critical tests pass
2. Average judge score ≥ 3.5 / 5.0
3. All safety scores ≥ 4.0 / 5.0 *(auto-fails entire release)*
4. P95 latency < 3000ms
5. Quality delta vs baseline < 5%

### 5.4 API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Send message; returns typed `OrcaResponse` |
| `POST` | `/evaluate` | Score a response with the LLM judge |
| `POST` | `/release-check` | Run all 5 gates; returns per-gate pass/fail |
| `GET` | `/health` | Server status, uptime, model config |

### 5.5 Rate Limiting

- `/chat`: 20 requests / min / IP
- `/evaluate`: 10 requests / min / IP
- Sliding-window implementation; keys on `X-Forwarded-For` when behind a proxy
- Returns `HTTP 429` with `Retry-After: 60` header on breach

---

## 6. Out-of-Scope Features (Future)

| Feature | Rationale for deferral |
|---|---|
| Streaming responses (SSE) | Adds complexity to judge and release gate; requires async rewrite |
| Redis session persistence | In-memory is sufficient for single-instance demo; Redis needed for scale |
| OpenAI function calling | Current regex tool parsing works at demo scale; migration is straightforward |
| Horizontal scaling | Blocked on Redis session persistence |
| User authentication | Left to deploying team — ORCA is infrastructure, not a consumer product |
| Fine-tuning pipeline | Out of scope for a testing-focused platform |

---

## 7. Success Metrics

| Metric | Target |
|---|---|
| Test suite pass rate | 100% (150 tests, 0 failures) |
| Release gate false-positive rate | < 5% — gate should block real regressions, not noise |
| Time-to-first-response (P50) | < 2000ms in single-turn mode |
| Time-to-first-response (P95) | < 3000ms in all modes |
| Deploy time (Railway + Vercel) | < 30 min from clean accounts |
| Judge score on golden dataset | ≥ 3.5 average across all scenarios |

---

## 8. Constraints

| Constraint | Detail |
|---|---|
| Python 3.9+ | Minimum version for all production and test code |
| OpenAI dependency | `OPENAI_API_KEY` required; all LLM calls go through OpenAI |
| No secrets in source | `.env` is gitignored; `.env.example` has placeholders only |
| Rate limit cost protection | `/evaluate` capped at 10 req/min — every call invokes GPT-4o |
| CORS restricted | `GET` and `POST` only; not `*` |

---

## 9. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| LLM output format drift breaks tool parsing | Medium | Migrate to OpenAI function calling; current regex is fragile |
| Railway restart wipes active sessions | High | Document limitation; add Redis when scaling beyond single instance |
| Judge scores fluctuate between model versions | Medium | Pin `JUDGE_MODEL` in env; baseline re-established on every model upgrade |
| OpenAI API key cost overrun | Low | Rate limiting caps spend; `/evaluate` limit is tightest |
| Safety gate flaps on edge-case inputs | Low | Safety scoring is conservative; tune rubric if false positive rate rises |
