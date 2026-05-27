# ============================================================
# 🐋 ORCA — REST API
# api/main.py
# ============================================================
# FastAPI server that exposes ORCA to the world.
# 4 endpoints: /chat, /evaluate, /release-check, /health
# ============================================================

import os
import time
import uuid
from fastapi             import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic            import BaseModel, Field
from typing              import List, Optional, Dict
from contextlib          import asynccontextmanager

from agent.orchestrator      import OrcaOrchestrator
from testing.judge           import OrcaJudge
from testing.release_gate    import OrcaReleaseGate
from config                  import AGENT_MODEL, JUDGE_MODEL, CORS_ORIGINS
from api.rate_limiter        import check_rate_limit


# ── Lifespan — load everything once at startup ───────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start up ORCA components when server starts."""
    print("🐋 ORCA API starting up...")
    app.state.orchestrator = OrcaOrchestrator()
    app.state.judge        = OrcaJudge()
    app.state.gate         = OrcaReleaseGate()
    app.state.start_time   = time.time()
    print("✅ ORCA API ready!")
    yield
    print("🐋 ORCA API shutting down...")


# ── Create FastAPI App ───────────────────────────────────────
app = FastAPI(
    title       = "🐋 ORCA API",
    description = "Orchestrated Reasoning & Conversational Agent — REST API",
    version     = "1.0.0",
    lifespan    = lifespan
)

# Set CORS_ORIGINS in .env to restrict origins in production (e.g. "https://app.example.com")
app.add_middleware(
    CORSMiddleware,
    allow_origins     = CORS_ORIGINS,
    allow_methods     = ["GET", "POST"],
    allow_headers     = ["Content-Type"],
)


# ── Request / Response Models ────────────────────────────────

class ChatRequest(BaseModel):
    message    : str            = Field(...,           description="User message to ORCA")
    mode       : str            = Field("single_turn", description="single_turn / multi_turn / agentic")
    session_id : Optional[str]  = Field(None,          description="Session ID for multi-turn memory")

    class Config:
        json_schema_extra = {
            "example": {
                "message"   : "What is the capital of France?",
                "mode"      : "single_turn",
                "session_id": None
            }
        }


class ChatResponse(BaseModel):
    response_id      : str
    content          : str
    mode             : str
    success          : bool
    duration_ms      : int
    tokens_used      : int
    guardrail_passed : bool
    blocked_reason   : Optional[str]
    tool_calls_count : int
    cost_estimate    : float
    session_id       : Optional[str]


class EvaluateRequest(BaseModel):
    user_message  : str  = Field(..., description="Original user message")
    orca_response : str  = Field(..., description="ORCA's response to evaluate")

    class Config:
        json_schema_extra = {
            "example": {
                "user_message" : "What is the capital of France?",
                "orca_response": "The capital of France is Paris."
            }
        }


class EvaluateResponse(BaseModel):
    accuracy    : float
    helpfulness : float
    safety      : float
    clarity     : float
    weighted    : float
    passed      : bool
    auto_failed : bool
    reasoning   : str


class ReleaseCheckRequest(BaseModel):
    version          : str         = Field(...,  description="Version string e.g. 1.0.0")
    test_results     : List[Dict]  = Field(...,  description="List of test result dicts")
    judge_scores     : List[float] = Field(...,  description="Judge weighted scores")
    safety_scores    : List[float] = Field(...,  description="Judge safety scores")
    latency_samples  : List[int]   = Field(...,  description="Response times in ms")
    baseline_score   : Optional[float] = Field(None, description="Previous version score")

    class Config:
        json_schema_extra = {
            "example": {
                "version"        : "1.0.0",
                "test_results"   : [{"priority": "critical", "passed": True}],
                "judge_scores"   : [4.8, 4.5, 4.9],
                "safety_scores"  : [5.0, 4.8, 5.0],
                "latency_samples": [800, 900, 950],
                "baseline_score" : None
            }
        }


class ReleaseCheckResponse(BaseModel):
    version      : str
    approved     : bool
    gates_passed : int
    gates_total  : int
    reason       : str
    gate_details : List[Dict]


class HealthResponse(BaseModel):
    status      : str
    version     : str
    uptime_secs : float
    agent_model : str
    judge_model : str


# ── Endpoint 1: POST /chat ───────────────────────────────────
@app.post(
    "/chat",
    response_model = ChatResponse,
    summary        = "Send a message to ORCA",
    tags           = ["Agent"]
)
async def chat(request: ChatRequest, http_request: Request):
    """
    Send a message to ORCA and get a response.

    - **single_turn**: One-shot question and answer
    - **multi_turn**: Conversation with memory (use same session_id)
    - **agentic**: ORCA can use tools to answer
    """
    check_rate_limit(http_request, "/chat")
    try:
        # Auto-generate a session_id for multi-turn if caller didn't supply one,
        # preventing unrelated requests from sharing the same memory slot.
        session_id = request.session_id or str(uuid.uuid4())

        result = app.state.orchestrator.chat(
            user_message = request.message,
            mode         = request.mode,
            session_id   = session_id,
        )

        return ChatResponse(
            response_id      = result.response_id,
            content          = result.content,
            mode             = result.mode,
            success          = result.success,
            duration_ms      = int(result.duration_ms),
            tokens_used      = int(result.tokens_used),
            guardrail_passed = result.guardrail_passed,
            blocked_reason   = result.blocked_reason,
            tool_calls_count = len(result.tool_calls),
            cost_estimate    = result.cost_estimate_usd,
            session_id       = session_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ORCA error: {str(e)}")


# ── Endpoint 2: POST /evaluate ───────────────────────────────
@app.post(
    "/evaluate",
    response_model = EvaluateResponse,
    summary        = "Evaluate an ORCA response with the LLM judge",
    tags           = ["Testing"]
)
async def evaluate(request: EvaluateRequest, http_request: Request):
    """
    Use the LLM judge (GPT-4o) to score an ORCA response.
    Returns scores for accuracy, helpfulness, safety, clarity.
    """
    check_rate_limit(http_request, "/evaluate")
    try:
        score = app.state.judge.evaluate(
            user_message  = request.user_message,
            orca_response = request.orca_response
        )

        return EvaluateResponse(
            accuracy    = score.accuracy,
            helpfulness = score.helpfulness,
            safety      = score.safety,
            clarity     = score.clarity,
            weighted    = score.weighted,
            passed      = score.passed,
            auto_failed = score.auto_failed,
            reasoning   = score.reasoning
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Judge error: {str(e)}")


# ── Endpoint 3: POST /release-check ─────────────────────────
@app.post(
    "/release-check",
    response_model = ReleaseCheckResponse,
    summary        = "Run all 5 release gates",
    tags           = ["Testing"]
)
async def release_check(request: ReleaseCheckRequest):
    """
    Run all 5 ORCA release gates:
    1. Critical test coverage
    2. Judge score threshold
    3. Safety score minimum
    4. Latency SLA (p95)
    5. Regression vs baseline
    """
    try:
        decision = app.state.gate.evaluate(
            version         = request.version,
            test_results    = request.test_results,
            judge_scores    = request.judge_scores,
            safety_scores   = request.safety_scores,
            latency_samples = request.latency_samples,
            baseline_score  = request.baseline_score
        )

        return ReleaseCheckResponse(
            version      = decision.version,
            approved     = decision.approved,
            gates_passed = decision.passed_gates,
            gates_total  = len(decision.gates),
            reason       = decision.reason,
            gate_details = [
                {
                    "gate"      : g.gate_name,
                    "passed"    : g.passed,
                    "actual"    : g.actual,
                    "threshold" : g.threshold,
                    "message"   : g.message
                }
                for g in decision.gates
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gate error: {str(e)}")


# ── Endpoint 4: GET /health ──────────────────────────────────
@app.get(
    "/health",
    response_model = HealthResponse,
    summary        = "Check if ORCA is alive",
    tags           = ["System"]
)
async def health():
    """
    Health check endpoint.
    Returns ORCA status, uptime, and model configuration.
    """
    uptime = round(time.time() - app.state.start_time, 2)

    return HealthResponse(
        status      = "🟢 healthy",
        version     = "1.0.0",
        uptime_secs = uptime,
        agent_model = AGENT_MODEL,
        judge_model = JUDGE_MODEL
    )


# ── Root ─────────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    """Welcome message."""
    return {
        "name"     : "🐋 ORCA API",
        "status"   : "alive",
        "docs"     : "/docs",
        "health"   : "/health",
        "version"  : "1.0.0",
        "message"  : "Orchestrated Reasoning & Conversational Agent"
    }


# ── Run Server ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🐋 Starting ORCA API Server")
    print("=" * 60)
    print("   URL  : http://localhost:8000")
    print("   Docs : http://localhost:8000/docs")
    print("=" * 60)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "api.main:app",
        host      = "0.0.0.0",
        port      = port,
        reload    = False,   # disable reload in prod; use --reload flag locally
        log_level = "info"
    )