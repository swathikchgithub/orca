# ORCA — Orchestrated Reasoning & Conversational Agent
## Master Blueprint for Claude (and You, Swathi 🚀)

> *"ORCA orchestrates intelligent agents the way a pod of orcas hunts — coordinated, precise, and unstoppable."*

---

> **This file is your north star.**
> Every time you open this project, read this first.
> Every time you ask Claude for help, paste the relevant section.
> This is how principal architects work — they write the plan BEFORE they write the code.

---

## 🐋 What Are We Building? (5-year-old version)

We are building **two things that work together**:

1. **The ORCA Agent** — A smart AI assistant that can:
   - Answer one question → **Single-turn**
   - Have a full conversation and remember things → **Multi-turn**
   - Make a plan, use tools, get things done → **Agentic**

2. **The ORCA Testing Framework (OTF)** — A robot that tests our agent automatically:
   - Creates fake users (AutoChat)
   - Runs thousands of test conversations
   - Grades the answers with LLM judges
   - Blocks bad releases before they ever reach users

Together they are **ORCA** — the system that makes AI you can actually trust and prove.

---

## 🏗️ Project Structure (build this folder by folder)

```
orca/
│
├── CLAUDE.md                    ← YOU ARE HERE (read this first always)
│
├── agent/                       ← The ORCA Agent (System 1)
│   ├── __init__.py
│   ├── orchestrator.py          ← Brain — routes single/multi/agentic
│   ├── memory.py                ← Remembers conversation history
│   ├── tool_router.py           ← Picks and calls tools
│   ├── guardrail.py             ← Safety checker
│   ├── response_composer.py     ← Formats final answer
│   └── prompts/
│       ├── single_turn.txt      ← System prompt for single-turn
│       ├── multi_turn.txt       ← System prompt for multi-turn
│       └── agentic.txt          ← System prompt for agentic
│
├── testing/                     ← The ORCA Testing Framework — OTF (System 2)
│   ├── __init__.py
│   ├── autochat.py              ← Synthetic user that drives conversations
│   ├── scenario_registry.py     ← Loads test cases from golden dataset
│   ├── assertion_engine.py      ← Deterministic pass/fail checks
│   ├── judge.py                 ← LLM judge that scores quality
│   └── release_gate.py          ← CI/CD blocker logic
│
├── data/
│   ├── golden_dataset/
│   │   ├── single_turn_cases.json
│   │   ├── multi_turn_cases.json
│   │   └── agentic_cases.json
│   └── rubrics/
│       └── judge_rubric.json    ← Scoring weights and prompts
│
├── tools/                       ← Real/mock tools ORCA can use
│   ├── __init__.py
│   ├── search_tool.py
│   ├── calculator_tool.py
│   └── database_tool.py
│
├── api/
│   ├── __init__.py
│   └── main.py                  ← FastAPI server (Step 14)
│
├── tests/
│   ├── test_orchestrator.py
│   ├── test_memory.py
│   ├── test_autochat.py
│   └── test_judge.py
│
├── config.py                    ← All settings in one place
├── requirements.txt             ← All Python packages
├── .env.example                 ← Copy to .env, add your API keys
└── README.md                    ← How to run ORCA
```

---

## 🔢 Build Order — Do These In Order, Never Skip

| # | What to build | File | Why first |
|---|---|---|---|
| 1 | ✅ Config + setup | `config.py` + `requirements.txt` | Everything else imports from here |
| 2 | Memory | `agent/memory.py` | Needed by orchestrator |
| 3 | Prompts | `agent/prompts/*.txt` | The brain's instructions |
| 4 | Guardrail | `agent/guardrail.py` | Safety before anything goes live |
| 5 | Tool router | `agent/tool_router.py` | Tools needed for agentic mode |
| 6 | Response composer | `agent/response_composer.py` | Formats answers |
| 7 | Orchestrator | `agent/orchestrator.py` | Ties it all together |
| 8 | Scenario registry | `testing/scenario_registry.py` | Test cases go in here |
| 9 | Assertion engine | `testing/assertion_engine.py` | Hard checks |
| 10 | Judge | `testing/judge.py` | LLM scoring |
| 11 | AutoChat | `testing/autochat.py` | Synthetic user loop |
| 12 | Release gate | `testing/release_gate.py` | CI/CD blocker |
| 13 | Unit tests | `tests/*.py` | Prove everything works |
| 14 | API | `api/main.py` | Serve ORCA to the world |

---

## 🎯 The 3 Modes — How Each One Works

### Mode 1: Single-Turn (simplest)
```
User sends 1 message
    ↓
ORCA Orchestrator reads it
    ↓
Builds prompt (system + user message)
    ↓
Calls LLM once
    ↓
Guardrail checks the response
    ↓
Returns answer
```
**Test it with:** "Summarize this in 3 bullets." → Did it give exactly 3 bullets?

---

### Mode 2: Multi-Turn (needs memory)
```
User sends message N
    ↓
ORCA Memory loads messages 1 to N-1
    ↓
Builds prompt (system + full history + new message)
    ↓
Calls LLM
    ↓
Guardrail checks
    ↓
Saves new message + response to memory
    ↓
Returns answer
```
**Test it with:** "My name is Swathi" → (later) "What's my name?" → Should say "Swathi"

---

### Mode 3: Agentic (plan + act + check)
```
User sends a goal
    ↓
ORCA builds a plan (step 1, step 2, step 3...)
    ↓
For each step:
    → Pick a tool
    → Call the tool
    → Read the result
    → Decide: done? or next step?
    ↓
Guardrail checks final answer
    ↓
Returns answer + full audit trace
```
**Test it with:** "What's 15% tip on $47.50?" → Should call calculator_tool, get $7.13, return it

---

## 📋 Validation Rules — These Never Change

### Category 1: Deterministic (computer checks — fast & cheap)
- [ ] Response is not empty
- [ ] Output matches expected schema
- [ ] No forbidden words/topics
- [ ] All required fields present
- [ ] Tool calls used only approved tools
- [ ] Trace log is complete (agentic only)

### Category 2: Semantic (LLM judge checks — smarter)
- [ ] Task was actually completed
- [ ] No hallucinated facts
- [ ] Response is coherent
- [ ] Tone matches context
- [ ] Memory used correctly (multi-turn only)
- [ ] Plan was sensible (agentic only)

### Category 3: Business (custom per domain)
- [ ] Within latency SLA
- [ ] Token usage within budget
- [ ] Escalation triggered correctly
- [ ] Domain rules followed

---

## ⚖️ ORCA Judge Scoring Rubric

| Dimension | Weight | What it checks |
|---|---|---|
| Task success | 35% | Did ORCA solve the problem? |
| Factuality | 20% | Are the facts correct? |
| Safety | 20% | Is it safe and policy-compliant? |
| Conversation quality | 15% | Is it coherent and helpful? |
| Efficiency | 10% | Is it concise, not wasteful? |

**Pass threshold:** Weighted score ≥ 3.5 out of 5
**Blocker rule:** Safety score < 4.0 = automatic fail, no exceptions

---

## 🚪 ORCA Release Gates — Nothing Ships Without These

```
Push code or change prompt
    ↓
Gate 1: All unit tests pass
    ↓
Gate 2: AutoChat runs full golden dataset
    ↓
Gate 3: Assertion engine — 0 failures on critical cases
    ↓
Gate 4: Judge scores don't drop > 5% from baseline
    ↓
Gate 5: Zero regressions on previously passing tests
    ↓
✅ Promote to production
```
**If any gate fails → block → fix → re-run from Gate 1**

---

## 🔑 Key Design Decisions (explain these in interviews)

### Decision 1: Why separate agent from testing?
So you can swap the model (GPT-4 → Claude → Gemini) without changing the tests.
The tests are the truth. ORCA's responses are what you're measuring against them.

### Decision 2: Why AutoChat instead of manual testing?
One human can do ~20 test conversations a day. ORCA's AutoChat can do 10,000.
You need scale to catch edge cases before your users find them.

### Decision 3: Why assertions first, then judge?
Assertions are cheap and instant. If the schema is wrong, there's no point paying
for an LLM judge. Fail fast, fail cheap — then escalate to smarter checks.

### Decision 4: Why a rubric with weights?
Because "good" is fuzzy. A rubric makes quality measurable, reproducible, and
explainable. You can tell a VP exactly why a response scored 3.8 out of 5.

### Decision 5: Why release gates in CI/CD?
Because humans forget to test. Machines don't. Every push is automatically
validated — no one has the authority to skip the gates.

---

## 💡 How to Work With Claude on ORCA

When you want to code a specific file, say exactly this:

> "Claude, let's build `agent/memory.py` — Step 2 in CLAUDE.md. Explain it simply then show me the code."

Claude will:
1. Explain what the file does in simple terms (5-year-old style)
2. Show you the complete, commented code
3. Tell you exactly what to type and where to put it
4. Give you a test to verify it works before moving on

---

## 🎤 ORCA Interview One-Liners (memorize these)

**"What is ORCA?"**
> "ORCA is an Orchestrated Reasoning & Conversational Agent — an enterprise AI platform with a built-in testing framework that validates every response through 18 quality gates before it ships."

**"Why should I trust ORCA?"**
> "Because we don't just build it — we measure it. Every response is scored by an LLM judge, every release is gated by CI/CD checks, and every regression is caught automatically before it reaches users."

**"What's your competitive moat?"**
> "Trust. Enterprises don't buy chatbots — they buy guarantees. ORCA makes quality measurable, auditable, and contractable. That's what unlocks enterprise contracts."

**"How does ORCA scale?"**
> "Domains are pluggable, models are swappable, and judges are replaceable. Engineering maintains one core pipeline while each business unit owns their quality contract."

---

## 📦 Requirements (requirements.txt)

```
openai>=1.0.0         # GPT-4o agent + judge calls
anthropic>=0.20.0     # Claude as alternate judge
fastapi>=0.110.0      # REST API server
uvicorn>=0.29.0       # Server runner
pydantic>=2.6.0       # Schema validation on every input/output
python-dotenv>=1.0.0  # Load .env secrets safely
pytest>=8.0.0         # Unit testing
pytest-asyncio>=0.23  # Async test support
rich>=13.7.0          # Beautiful terminal traces
httpx>=0.27.0         # HTTP client for tool calls
```

---

## 🗓️ ORCA Build Milestones

| Milestone | Files | What you can demo |
|---|---|---|
| **M1 — Hello ORCA** | config.py, memory.py, prompts, orchestrator.py | ORCA answers a question |
| **M2 — Full ORCA Agent** | + guardrail.py, tool_router.py, response_composer.py | ORCA with safety + tools |
| **M3 — Testing Framework (OTF)** | + scenario_registry.py, assertion_engine.py | Run 1 test case end-to-end |
| **M4 — AutoChat + Judge** | + autochat.py, judge.py | Automated test + quality score |
| **M5 — Production Ready** | + release_gate.py, api/main.py, tests/ | Full CI/CD pipeline live |

---

## 🐋 The ORCA Promise

> *We don't just ship AI. We ship AI we can prove works.*
> *Every response measured. Every release gated. Every regression caught.*
> *That's the ORCA way.*

---
*Built by Swathi Chadalavada — Principal Engineer, AI Systems Architect* 🏆
*Next step: Open your terminal. Let's build Step 2 — `agent/memory.py`*
