"use client";

import { useState } from "react";
import { runReleaseCheck, ReleaseCheckResponse } from "@/lib/api";

function NumericInput({
    value, onChange, min = 0, max = 5, step = 0.1,
}: {
    value: number; onChange: (v: number) => void; min?: number; max?: number; step?: number;
}) {
    return (
        <input
            type="number"
            value={value}
            min={min} max={max} step={step}
            onChange={e => onChange(parseFloat(e.target.value) || 0)}
            className="w-20 input-dark px-3 py-2 text-sm text-center font-mono"
        />
    );
}

function InputGroup({
    label, hint, values, onChange, min, max, step,
}: {
    label: string; hint: string; values: number[];
    onChange: (v: number[]) => void; min?: number; max?: number; step?: number;
}) {
    return (
        <div>
            <div className="flex items-baseline gap-2 mb-2">
                <label className="text-xs font-bold uppercase tracking-widest font-display" style={{ color: "var(--text-muted)" }}>{label}</label>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>{hint}</span>
            </div>
            <div className="flex gap-2 flex-wrap">
                {values.map((v, i) => (
                    <NumericInput
                        key={i} value={v} min={min} max={max} step={step}
                        onChange={nv => { const next = [...values]; next[i] = nv; onChange(next); }}
                    />
                ))}
            </div>
        </div>
    );
}

const GATE_ICONS: Record<string, string> = {
    "Judge Score":    "⚖️",
    "Safety Score":   "🛡️",
    "Latency P95":    "⚡",
    "Regression":     "📊",
    "Min Sample":     "🔢",
};

export default function ReleasePage() {
    const [version, setVersion]             = useState("v1.0.0");
    const [judgeScores, setJudgeScores]     = useState([4.2, 4.0, 3.8, 4.5]);
    const [safetyScores, setSafetyScores]   = useState([4.5, 4.8, 4.2, 4.6]);
    const [latencySamples, setLatencySamples] = useState([450, 520, 380, 490]);
    const [baselineScore, setBaselineScore] = useState("3.8");
    const [result, setResult]               = useState<ReleaseCheckResponse | null>(null);
    const [loading, setLoading]             = useState(false);
    const [error, setError]                 = useState("");

    const runCheck = async () => {
        if (!version.trim()) return;
        setLoading(true); setError(""); setResult(null);
        try {
            const baseline = baselineScore.trim() ? parseFloat(baselineScore) : null;
            setResult(await runReleaseCheck(version.trim(), judgeScores, safetyScores, latencySamples, baseline));
        } catch (e) {
            setError(e instanceof Error ? e.message : "Release check failed");
        } finally {
            setLoading(false);
        }
    };

    const gatesPassed  = result?.gates_passed ?? 0;
    const gatesTotal   = result?.gates_total ?? 5;
    const progressPct  = gatesTotal > 0 ? (gatesPassed / gatesTotal) * 100 : 0;

    return (
        <div
            className="min-h-screen p-4 sm:p-6 lg:p-8 noise header-grid"
            style={{ background: "radial-gradient(ellipse at top, #0a1a14 0%, var(--bg-base) 60%)" }}
        >
            <div className="max-w-7xl mx-auto relative z-10">

                {/* ── Header ─────────────────────────────── */}
                <div className="mb-8 fade-in-up">
                    <div className="flex items-center gap-2 mb-4">
                        <span className="text-xs px-3 py-1 rounded-full font-medium" style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.3)", color: "#34d399" }}>
                            Production Gate
                        </span>
                        <span className="text-xs px-3 py-1 rounded-full" style={{ border: "1px solid var(--border)", color: "var(--text-muted)" }}>
                            5 Quality Gates
                        </span>
                    </div>
                    <h1 className="text-4xl font-black tracking-tight mb-2 font-display" style={{ color: "var(--text-primary)" }}>
                        🚀 <span className="gradient-text">Release</span> Gate
                    </h1>
                    <p style={{ color: "var(--text-secondary)" }}>
                        Run 5 automated quality checks before shipping ORCA to production
                    </p>
                </div>

                {/* ── 2-Column Layout ────────────────────── */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

                    {/* ── Left Column: Form + Results ──────── */}
                    <div className="flex flex-col gap-6">

                        {/* Input Card */}
                        <div className="glass-dark rounded-2xl p-6">
                            <div className="space-y-5">

                                {/* Version */}
                                <div>
                                    <label className="text-xs font-bold uppercase tracking-widest mb-2 block font-display" style={{ color: "var(--text-muted)" }}>
                                        Version Tag
                                    </label>
                                    <input
                                        type="text"
                                        value={version}
                                        onChange={e => setVersion(e.target.value)}
                                        placeholder="e.g. v1.0.0"
                                        className="input-dark px-4 py-2.5 text-sm w-48"
                                    />
                                </div>

                                {/* Score inputs */}
                                <InputGroup label="Judge Scores"   hint="4 samples · scale 0–5" values={judgeScores}    onChange={setJudgeScores} />
                                <InputGroup label="Safety Scores"  hint="4 samples · scale 0–5" values={safetyScores}   onChange={setSafetyScores} />
                                <InputGroup label="Latency (ms)"   hint="4 samples"              values={latencySamples} onChange={setLatencySamples} min={0} max={10000} step={1} />

                                {/* Baseline */}
                                <div>
                                    <div className="flex items-baseline gap-2 mb-2">
                                        <label className="text-xs font-bold uppercase tracking-widest font-display" style={{ color: "var(--text-muted)" }}>Baseline Score</label>
                                        <span className="text-xs" style={{ color: "var(--text-muted)" }}>optional · regression check</span>
                                    </div>
                                    <input
                                        type="number" value={baselineScore}
                                        onChange={e => setBaselineScore(e.target.value)}
                                        min={0} max={5} step={0.1} placeholder="e.g. 3.8"
                                        className="input-dark px-4 py-2.5 text-sm w-32 font-mono"
                                    />
                                </div>

                                {/* Run button */}
                                <button
                                    onClick={runCheck}
                                    disabled={loading || !version.trim()}
                                    className="w-full py-3 text-sm font-bold rounded-xl transition-all duration-200"
                                    style={{
                                        background: loading || !version.trim()
                                            ? "rgba(255,255,255,0.05)"
                                            : "linear-gradient(135deg, #10b981, #059669)",
                                        color: loading || !version.trim() ? "var(--text-muted)" : "white",
                                        border: "none",
                                        boxShadow: loading || !version.trim() ? "none" : "0 4px 20px rgba(16,185,129,0.35)",
                                        cursor: loading || !version.trim() ? "not-allowed" : "pointer",
                                    }}
                                >
                                    {loading ? "⏳ Running gates…" : "🚀 Run Release Check"}
                                </button>
                            </div>
                        </div>

                        {/* Disclaimer */}
                        <div
                            className="rounded-xl px-4 py-3 flex gap-3"
                            style={{ background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)" }}
                        >
                            <span className="text-base flex-shrink-0 mt-0.5">⚠️</span>
                            <div>
                                <p className="text-xs font-bold font-display mb-1" style={{ color: "#fbbf24" }}>Hard gates — no exceptions</p>
                                <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                                    All 5 gates must pass for ORCA to be approved for release.
                                    A single failure blocks the entire release, regardless of how well other gates perform.
                                </p>
                            </div>
                        </div>

                        {/* Error */}
                        {error && (
                            <div className="rounded-xl p-4" style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.4)" }}>
                                <p className="text-sm" style={{ color: "#fca5a5" }}>❌ {error}</p>
                            </div>
                        )}

                        {/* Results */}
                        {result && (
                            <div className="glass-dark rounded-2xl p-6 animate-in">

                                {/* Verdict */}
                                <div
                                    className="rounded-xl p-6 mb-6 text-center"
                                    style={result.approved ? {
                                        background: "rgba(16,185,129,0.08)",
                                        border: "1px solid rgba(16,185,129,0.4)",
                                        boxShadow: "0 0 40px rgba(16,185,129,0.2)",
                                    } : {
                                        background: "rgba(239,68,68,0.08)",
                                        border: "1px solid rgba(239,68,68,0.4)",
                                        boxShadow: "0 0 40px rgba(239,68,68,0.2)",
                                    }}
                                >
                                    <div className="text-5xl mb-3">{result.approved ? "✅" : "❌"}</div>
                                    <div
                                        className="text-3xl font-black mb-1 font-display"
                                        style={{ color: result.approved ? "#34d399" : "#f87171", textShadow: `0 0 20px ${result.approved ? "rgba(16,185,129,0.5)" : "rgba(239,68,68,0.5)"}` }}
                                    >
                                        {result.approved ? "APPROVED" : "BLOCKED"}
                                    </div>
                                    <p className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>{result.reason}</p>

                                    {/* Progress bar */}
                                    <div className="mx-auto max-w-xs">
                                        <div className="flex justify-between mb-1">
                                            <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{gatesPassed}/{gatesTotal} gates</span>
                                            <span className="text-xs font-mono" style={{ color: result.approved ? "#34d399" : "#f87171" }}>{Math.round(progressPct)}%</span>
                                        </div>
                                        <div className="w-full rounded-full overflow-hidden" style={{ height: "6px", background: "var(--bg-base)" }}>
                                            <div
                                                className="h-full rounded-full transition-all duration-700"
                                                style={{
                                                    width: `${progressPct}%`,
                                                    background: result.approved
                                                        ? "linear-gradient(90deg, #10b981, #22d3ee)"
                                                        : "linear-gradient(90deg, #ef4444, #f97316)",
                                                    boxShadow: `0 0 10px ${result.approved ? "rgba(16,185,129,0.5)" : "rgba(239,68,68,0.5)"}`,
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <p className="text-xs mt-3 font-mono" style={{ color: "var(--text-muted)" }}>{result.version}</p>
                                </div>

                                {/* Gate details */}
                                <div className="space-y-2.5">
                                    {result.gate_details.map(gate => {
                                        const icon = Object.entries(GATE_ICONS).find(([k]) => gate.gate.includes(k))?.[1] ?? "🔹";
                                        return (
                                            <div
                                                key={gate.gate}
                                                className="flex items-center gap-3 px-4 py-3 rounded-xl"
                                                style={gate.passed ? {
                                                    background: "rgba(16,185,129,0.06)",
                                                    border: "1px solid rgba(16,185,129,0.25)",
                                                } : {
                                                    background: "rgba(239,68,68,0.06)",
                                                    border: "1px solid rgba(239,68,68,0.25)",
                                                }}
                                            >
                                                <span className="text-lg flex-shrink-0">{icon}</span>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center justify-between gap-2">
                                                        <span className="text-sm font-semibold font-display" style={{ color: "var(--text-primary)" }}>{gate.gate}</span>
                                                        <span
                                                            className="text-xs font-mono px-2 py-0.5 rounded-lg flex-shrink-0"
                                                            style={gate.passed ? {
                                                                background: "rgba(16,185,129,0.15)", color: "#34d399",
                                                            } : {
                                                                background: "rgba(239,68,68,0.15)", color: "#f87171",
                                                            }}
                                                        >
                                                            {gate.actual} / {gate.threshold}
                                                        </span>
                                                    </div>
                                                    <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{gate.message}</p>
                                                </div>
                                                <span className="text-base flex-shrink-0">{gate.passed ? "✓" : "✗"}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ── Right Column: How it Works (sticky) ── */}
                    <div className="lg:sticky lg:top-8">
                        <div className="glass-dark rounded-2xl p-6">
                            <p className="text-xs font-bold uppercase tracking-widest mb-5 font-display" style={{ color: "var(--text-muted)" }}>
                                📋 How the Release Gate Works
                            </p>

                            <p className="text-sm leading-relaxed mb-6" style={{ color: "var(--text-secondary)" }}>
                                Before ORCA ships to production, it must pass <strong style={{ color: "var(--text-primary)" }}>5 automated quality gates</strong>.
                                Each gate has a hard threshold. If even one gate fails, the release is <strong style={{ color: "#f87171" }}>blocked</strong> — no exceptions.
                                This stops you from accidentally shipping a degraded, unsafe, or slow model.
                            </p>

                            {/* The 5 gates */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                                {[
                                    {
                                        icon: "⚖️", name: "Judge Score Gate",
                                        color: "#818cf8", bg: "rgba(99,102,241,0.08)", border: "rgba(99,102,241,0.25)",
                                        rule: "Average ≥ 3.5 / 5",
                                        why: "Proves the model gives good-quality answers on average.",
                                        input: "Your 4 judge evaluation scores",
                                    },
                                    {
                                        icon: "🛡️", name: "Safety Score Gate",
                                        color: "#f87171", bg: "rgba(239,68,68,0.08)", border: "rgba(239,68,68,0.25)",
                                        rule: "Average ≥ 4.0 / 5",
                                        why: "Safety threshold is stricter than quality — non-negotiable.",
                                        input: "Your 4 safety evaluation scores",
                                    },
                                    {
                                        icon: "⚡", name: "Latency P95 Gate",
                                        color: "#fbbf24", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.25)",
                                        rule: "95th-percentile ≤ 600 ms",
                                        why: "Users notice anything slower than ~600ms. P95 covers the slowest 5%.",
                                        input: "4 end-to-end response times in ms",
                                    },
                                    {
                                        icon: "📊", name: "Regression Gate",
                                        color: "#34d399", bg: "rgba(16,185,129,0.08)", border: "rgba(16,185,129,0.25)",
                                        rule: "New score ≥ baseline − 0.2",
                                        why: "Catches regressions — prevents shipping a model that got worse.",
                                        input: "Baseline score from previous release (optional)",
                                    },
                                    {
                                        icon: "🔢", name: "Min Sample Gate",
                                        color: "#c084fc", bg: "rgba(168,85,247,0.08)", border: "rgba(168,85,247,0.25)",
                                        rule: "At least 3 samples per metric",
                                        why: "Prevents releasing based on a single lucky test run.",
                                        input: "Automatically checked from your input arrays",
                                    },
                                ].map(gate => (
                                    <div
                                        key={gate.name}
                                        className="rounded-xl p-4"
                                        style={{ background: gate.bg, border: `1px solid ${gate.border}` }}
                                    >
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="text-lg">{gate.icon}</span>
                                            <span className="text-sm font-bold font-display" style={{ color: gate.color }}>{gate.name}</span>
                                        </div>
                                        <div
                                            className="text-xs font-mono px-2 py-0.5 rounded-md inline-block mb-2"
                                            style={{ background: gate.bg, border: `1px solid ${gate.border}`, color: gate.color }}
                                        >
                                            {gate.rule}
                                        </div>
                                        <p className="text-xs leading-relaxed mb-1" style={{ color: "var(--text-secondary)" }}>{gate.why}</p>
                                        <p className="text-xs" style={{ color: "var(--text-muted)" }}>↳ {gate.input}</p>
                                    </div>
                                ))}
                            </div>

                            {/* How to fill the form */}
                            <div className="rounded-xl p-4" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}>
                                <p className="text-xs font-bold uppercase tracking-widest mb-3 font-display" style={{ color: "var(--text-muted)" }}>
                                    How to fill the form
                                </p>
                                <div className="space-y-2">
                                    {[
                                        { n: "1", label: "Version tag",     hint: "Just a label, e.g. v1.2.0 — used for tracking only." },
                                        { n: "2", label: "Judge Scores",    hint: "Run the Evaluate page 4 times with different test prompts. Enter those weighted scores here." },
                                        { n: "3", label: "Safety Scores",   hint: "Enter only the Safety dimension score from each evaluation run (0–5 scale)." },
                                        { n: "4", label: "Latency (ms)",    hint: "Open the Chat page, send 4 messages, note the ms shown under each reply." },
                                        { n: "5", label: "Baseline Score",  hint: "Optional. Enter the judge score from your last known-good release to enable the regression check." },
                                    ].map(row => (
                                        <div key={row.n} className="flex gap-3">
                                            <span
                                                className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 font-mono"
                                                style={{ background: "rgba(99,102,241,0.2)", color: "var(--accent)" }}
                                            >
                                                {row.n}
                                            </span>
                                            <div>
                                                <span className="text-xs font-semibold font-display" style={{ color: "var(--text-primary)" }}>{row.label}</span>
                                                <span className="text-xs ml-2" style={{ color: "var(--text-muted)" }}>— {row.hint}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
