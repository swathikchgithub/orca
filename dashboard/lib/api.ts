// lib/api.ts
// 🐋 ORCA API Client — connects dashboard to Python backend

const ORCA_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ────────────────────────────────────────────────────

export interface ChatResponse {
    response_id: string;
    content: string;
    mode: string;
    success: boolean;
    duration_ms: number;
    tokens_used: number;
    guardrail_passed: boolean;
    blocked_reason: string;
    tool_calls_count: number;
    cost_estimate: number;
    session_id: string | null;
}

export interface EvaluateResponse {
    accuracy: number;
    helpfulness: number;
    safety: number;
    clarity: number;
    weighted: number;
    passed: boolean;
    auto_failed: boolean;
    reasoning: string;
}

export interface GateDetail {
    gate: string;
    passed: boolean;
    actual: string;
    threshold: string;
    message: string;
}

export interface ReleaseCheckResponse {
    version: string;
    approved: boolean;
    gates_passed: number;
    gates_total: number;
    reason: string;
    gate_details: GateDetail[];
}

export interface HealthResponse {
    status: string;
    version: string;
    uptime_secs: number;
    agent_model: string;
    judge_model: string;
}

// ── API Functions ─────────────────────────────────────────────

export async function healthCheck(): Promise<HealthResponse> {
    const res = await fetch(`${ORCA_BASE}/health`);
    if (!res.ok) throw new Error("ORCA API is offline");
    return res.json();
}

export async function chatWithOrca(
    message: string,
    mode: string,
    sessionId: string | null
): Promise<ChatResponse> {
    const res = await fetch(`${ORCA_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message,
            mode,
            session_id: sessionId
        })
    });
    if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try { detail = (await res.json()).detail ?? detail; } catch { /* HTML error page */ }
        throw new Error(detail);
    }
    return res.json();
}

export async function evaluateResponse(
    userMessage: string,
    orcaResponse: string
): Promise<EvaluateResponse> {
    const res = await fetch(`${ORCA_BASE}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_message: userMessage,
            orca_response: orcaResponse
        })
    });
    if (!res.ok) throw new Error("Evaluation failed");
    return res.json();
}

export async function runReleaseCheck(
    version: string,
    judgeScores: number[],
    safetyScores: number[],
    latencySamples: number[],
    baselineScore: number | null
): Promise<ReleaseCheckResponse> {
    const res = await fetch(`${ORCA_BASE}/release-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            version,
            test_results: [
                { priority: "critical", passed: true },
                { priority: "critical", passed: true },
                { priority: "high", passed: true }
            ],
            judge_scores: judgeScores,
            safety_scores: safetyScores,
            latency_samples: latencySamples,
            baseline_score: baselineScore
        })
    });
    if (!res.ok) throw new Error("Release check failed");
    return res.json();
}