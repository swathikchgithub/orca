# ORCA — Deployment Guide

**Stack:** Python FastAPI backend → Railway | Next.js dashboard → Vercel  
**Last updated:** May 2026

---

## What Changed to Make This Deploy-Ready

| # | Change | File | Why |
|---|---|---|---|
| 1 | `PORT` reads from env var | `api/main.py` | Railway injects `$PORT` — hardcoded 8000 would fail |
| 2 | `Procfile` added | `Procfile` | Railway needs this to know how to start the server |
| 3 | Split `requirements.txt` | `requirements.txt` + `requirements-dev.txt` | Keeps pytest/rich out of the production image |
| 4 | CORS `allow_methods` restricted | `api/main.py` | Was `["*"]`, now `["GET", "POST"]` — principle of least privilege |
| 5 | Rate limiting added | `api/rate_limiter.py` | `/chat`: 20 req/min per IP. `/evaluate`: 10 req/min per IP. Protects LLM cost budget |
| 6 | `.env.example` added | `.env.example` | Documents every env var required to run the app |

---

## Prerequisites

- GitHub account (both repos pushed)
- Railway account → [railway.app](https://railway.app) (free tier works)
- Vercel account → [vercel.com](https://vercel.com) (free tier works)
- OpenAI API key with GPT-4o access

---

## Part 1 — Deploy the Backend (Railway)

### Step 1: Push `orca` to GitHub

```bash
cd /Volumes/LaCie/orca
git remote add origin https://github.com/<your-username>/orca.git
git push -u origin main
```

### Step 2: Create a new Railway project

1. Go to [railway.app](https://railway.app) → **New Project**
2. Choose **Deploy from GitHub repo**
3. Select the `orca` repository
4. Railway auto-detects Python and reads the `Procfile`

### Step 3: Set environment variables in Railway

Go to your service → **Variables** tab → add each:

```
OPENAI_API_KEY        = sk-...            # required
ANTHROPIC_API_KEY     = sk-ant-...        # optional — for Claude judge
CORS_ORIGINS          = https://orca-dashboard.vercel.app   # set after Vercel deploy
AGENT_MODEL           = gpt-4o-mini
JUDGE_MODEL           = gpt-4o
LOG_LEVEL             = INFO
```

> **Do not set `PORT`** — Railway injects it automatically.

### Step 4: Verify the backend is running

Once Railway shows **✅ Active**, open:
```
https://<your-railway-url>.up.railway.app/health
```

Expected response:
```json
{
  "status": "🟢 healthy",
  "version": "1.0.0",
  "uptime_secs": 12.4,
  "agent_model": "gpt-4o-mini",
  "judge_model": "gpt-4o"
}
```

Also check the interactive API docs:
```
https://<your-railway-url>.up.railway.app/docs
```

---

## Part 2 — Deploy the Dashboard (Vercel)

The dashboard lives in the `dashboard/` subfolder of this repo — no separate repository needed.

### Step 1: Create a new Vercel project

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import the `orca` repository (same repo as the backend)
3. **Important:** Set **Root Directory** to `dashboard`
4. Framework preset: **Next.js** (auto-detected)

### Step 2: Set environment variable in Vercel

Go to **Settings → Environment Variables** → add:

```
NEXT_PUBLIC_API_URL = https://<your-railway-url>.up.railway.app
```

> Use the Railway URL from Part 1, Step 4.

### Step 3: Deploy

Click **Deploy**. Vercel builds only the `dashboard/` subtree — the Python backend files are ignored.

### Step 4: Update CORS on Railway

Once Vercel gives you the dashboard URL, go back to Railway → Variables and update:

```
CORS_ORIGINS = https://<your-project>.vercel.app
```

Railway will auto-redeploy.

---

## Verify End-to-End

1. Open the Vercel dashboard URL
2. Click **Chat** → send a message in **Single-Turn** mode
3. You should get a response from ORCA in the UI

If the chat returns an error:
- Check browser DevTools → Network tab for the failing request
- Confirm `NEXT_PUBLIC_API_URL` in Vercel matches the Railway URL exactly (no trailing slash)
- Confirm `CORS_ORIGINS` in Railway matches the Vercel URL exactly

---

## Rate Limits

| Endpoint | Limit | Window |
|---|---|---|
| `POST /chat` | 20 requests | per IP per 60s |
| `POST /evaluate` | 10 requests | per IP per 60s |
| `POST /release-check` | unlimited | — pure Python, no LLM cost |
| `GET /health` | unlimited | — |

Over-limit requests receive `HTTP 429` with a `Retry-After: 60` header.

---

## Known Limitations (post-deploy)

| Limitation | Impact | Fix when needed |
|---|---|---|
| **Sessions are in-memory** | A Railway restart wipes all active multi-turn conversations | Add Redis with `REDIS_URL` env var and store memory there |
| **Single instance** | No horizontal scaling — all sessions live on one dyno | Add Redis session store first, then scale out |
| **Tool calls use text parsing** | Agentic tool calls parsed via regex — fragile if model format drifts | Migrate to OpenAI function calling API |

---

## Running Locally

```bash
# Backend
cd orca
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in OPENAI_API_KEY
uvicorn api.main:app --reload --port 8000

# Frontend (separate terminal)
cd orca-dashboard
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000`.

---

## Running Tests

```bash
cd orca
source .venv/bin/activate
pytest tests/ -v
```

**150 tests, 0 failures** across 10 test files:

| File | Tests | Covers |
|---|---|---|
| `test_memory.py` | 12 | ConversationMemory + Message |
| `test_guardrail.py` | 9 | Input + output safety checks |
| `test_assertions.py` | 14 | All 6 assertion types |
| `test_release_gate.py` | 4 | All 5 release gates |
| `test_tool_router.py` | 13 | Registry, run, trace, crash safety |
| `test_response_composer.py` | 22 | compose, blocked, error paths |
| `test_tools.py` | 21 | Calculator sandbox, search, database |
| `test_api.py` | 23 | All 4 HTTP endpoints |
| `test_rate_limiter.py` | 14 | Limits, 429 responses, X-Forwarded-For |
| `test_scenario_registry.py` | 18 | Golden dataset loading and filtering |

---

*ORCA — Orchestrated Reasoning & Conversational Agent*
