"use client";

import { useState, useEffect } from "react";

const PIPELINE_STEPS = [
    { id: "input",        icon: "👤", label: "User Message",      desc: "Request comes in",                      color: "blue",   layer: "Input",  canBlock: false, isAgentic: false, isPulse: false },
    { id: "guardrail_in", icon: "🛡️", label: "Input Guardrail",   desc: "Safety check — blocks harmful requests", color: "red",    layer: "Safety", canBlock: true,  isAgentic: false, isPulse: false },
    { id: "memory",       icon: "🧠", label: "Memory",             desc: "Load conversation history",             color: "purple", layer: "Agent",  canBlock: false, isAgentic: false, isPulse: false },
    { id: "prompt",       icon: "📝", label: "Prompt Builder",     desc: "System prompt + history + message",     color: "yellow", layer: "Agent",  canBlock: false, isAgentic: false, isPulse: false },
    { id: "llm",          icon: "🤖", label: "LLM Call",           desc: "GPT-4o-mini generates response",        color: "blue",   layer: "LLM",   canBlock: false, isAgentic: false, isPulse: true  },
    { id: "tools",        icon: "🔧", label: "Tool Router",        desc: "Calculator · Search · Database",        color: "orange", layer: "Tools",  canBlock: false, isAgentic: true,  isPulse: false },
    { id: "guardrail_out",icon: "🛡️", label: "Output Guardrail",  desc: "Check response is safe",                color: "red",    layer: "Safety", canBlock: true,  isAgentic: false, isPulse: false },
    { id: "composer",     icon: "✍️", label: "Response Composer",  desc: "Wrap in OrcaResponse object",          color: "green",  layer: "Output", canBlock: false, isAgentic: false, isPulse: false },
    { id: "output",       icon: "✅", label: "OrcaResponse",       desc: "ID + content + metrics + trace",        color: "green",  layer: "Output", canBlock: false, isAgentic: false, isPulse: false },
];

const SCENARIOS = [
    {
        name: "Single Turn", icon: "🎯", color: "blue",
        desc: "Simple question → answer",
        message: "What is the capital of France?",
        response: "The capital of France is Paris.",
        skipSteps: ["tools"], blockAt: null,
    },
    {
        name: "Multi Turn", icon: "🧠", color: "purple",
        desc: "Conversation with memory",
        message: "My name is Swathi. What is my name?",
        response: "Your name is Swathi!",
        skipSteps: ["tools"], blockAt: null,
    },
    {
        name: "Agentic", icon: "🔧", color: "orange",
        desc: "Uses tools to answer",
        message: "Calculate 15% tip on $47.50",
        response: "The 15% tip on $47.50 is $7.13",
        skipSteps: [], blockAt: null,
    },
    {
        name: "Blocked", icon: "🛡️", color: "red",
        desc: "Guardrail stops bad request",
        message: "How to hack a database",
        response: "I cannot help with that.",
        skipSteps: ["memory", "prompt", "llm", "tools", "guardrail_out", "composer", "output"],
        blockAt: "guardrail_in",
    },
];

// Inline color tokens — all CSS var–based so they respect the design system
const C: Record<string, { bg: string; border: string; text: string; shadow: string; dot: string; connLine: string }> = {
    blue:   { bg: "rgba(99,102,241,0.1)",  border: "rgba(99,102,241,0.55)",  text: "#818cf8", shadow: "0 0 28px rgba(99,102,241,0.45)",  dot: "#6366f1", connLine: "#6366f1" },
    red:    { bg: "rgba(239,68,68,0.1)",   border: "rgba(239,68,68,0.55)",   text: "#f87171", shadow: "0 0 28px rgba(239,68,68,0.45)",   dot: "#ef4444", connLine: "#ef4444" },
    purple: { bg: "rgba(168,85,247,0.1)",  border: "rgba(168,85,247,0.55)",  text: "#c084fc", shadow: "0 0 28px rgba(168,85,247,0.45)",  dot: "#a855f7", connLine: "#a855f7" },
    yellow: { bg: "rgba(245,158,11,0.1)",  border: "rgba(245,158,11,0.55)",  text: "#fbbf24", shadow: "0 0 28px rgba(245,158,11,0.45)",  dot: "#f59e0b", connLine: "#f59e0b" },
    orange: { bg: "rgba(249,115,22,0.1)",  border: "rgba(249,115,22,0.55)",  text: "#fb923c", shadow: "0 0 28px rgba(249,115,22,0.45)",  dot: "#f97316", connLine: "#f97316" },
    green:  { bg: "rgba(16,185,129,0.1)",  border: "rgba(16,185,129,0.55)",  text: "#34d399", shadow: "0 0 28px rgba(16,185,129,0.45)",  dot: "#10b981", connLine: "#10b981" },
};

const SC: Record<string, { tabBg: string; tabBorder: string; tabText: string; tabGlow: string; cardBg: string; cardBorder: string }> = {
    blue:   { tabBg: "rgba(99,102,241,0.18)",  tabBorder: "rgba(99,102,241,0.5)",  tabText: "#a5b4fc", tabGlow: "0 0 20px rgba(99,102,241,0.4)",  cardBg: "rgba(99,102,241,0.08)",  cardBorder: "rgba(99,102,241,0.3)" },
    purple: { tabBg: "rgba(168,85,247,0.18)", tabBorder: "rgba(168,85,247,0.5)", tabText: "#d8b4fe", tabGlow: "0 0 20px rgba(168,85,247,0.4)", cardBg: "rgba(168,85,247,0.08)", cardBorder: "rgba(168,85,247,0.3)" },
    orange: { tabBg: "rgba(249,115,22,0.18)",  tabBorder: "rgba(249,115,22,0.5)",  tabText: "#fdba74", tabGlow: "0 0 20px rgba(249,115,22,0.4)",  cardBg: "rgba(249,115,22,0.08)",  cardBorder: "rgba(249,115,22,0.3)" },
    red:    { tabBg: "rgba(239,68,68,0.18)",   tabBorder: "rgba(239,68,68,0.5)",   tabText: "#fca5a5", tabGlow: "0 0 20px rgba(239,68,68,0.4)",   cardBg: "rgba(239,68,68,0.08)",   cardBorder: "rgba(239,68,68,0.3)" },
};

const LAYER_LEGEND = [
    { dot: "#6366f1", label: "Input Layer" },
    { dot: "#ef4444", label: "Safety Layer" },
    { dot: "#a855f7", label: "Agent Layer" },
    { dot: "#f97316", label: "Tool Layer" },
    { dot: "#10b981", label: "Output Layer" },
];

export default function ArchitectureDiagram() {
    const [activeScenario, setActiveScenario] = useState(0);
    const [activeStep, setActiveStep] = useState(-1);
    const [isPlaying, setIsPlaying] = useState(true);
    const [isBlocked, setIsBlocked] = useState(false);
    const [completed, setCompleted] = useState<string[]>([]);

    const scenario = SCENARIOS[activeScenario];
    const sc = SC[scenario.color];

    useEffect(() => {
        if (!isPlaying) return;
        setActiveStep(-1);
        setIsBlocked(false);
        setCompleted([]);

        const steps = PIPELINE_STEPS.filter(s => !scenario.skipSteps.includes(s.id));
        let idx = 0;

        const iv = setInterval(() => {
            if (idx >= steps.length) {
                clearInterval(iv);
                setTimeout(() => setActiveScenario(p => (p + 1) % SCENARIOS.length), 2000);
                return;
            }
            const step = steps[idx];
            if (step.id === scenario.blockAt) {
                setActiveStep(idx);
                setIsBlocked(true);
                setCompleted(p => [...p, step.id]);
                clearInterval(iv);
                setTimeout(() => setActiveScenario(p => (p + 1) % SCENARIOS.length), 2500);
                return;
            }
            setActiveStep(idx);
            setCompleted(p => [...p, step.id]);
            idx++;
        }, 600);

        return () => clearInterval(iv);
    }, [activeScenario, isPlaying]);

    const visibleSteps = PIPELINE_STEPS.filter(s => !scenario.skipSteps.includes(s.id));

    return (
        <div
            className="rounded-2xl overflow-hidden"
            style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
                // Top accent gradient line
                borderTop: `2px solid transparent`,
                backgroundImage: `linear-gradient(var(--bg-card), var(--bg-card)), linear-gradient(90deg, var(--accent), var(--cyan))`,
                backgroundOrigin: "border-box",
                backgroundClip: "padding-box, border-box",
            }}
        >
            {/* ── Header ───────────────────────────────────────── */}
            <div
                className="px-6 py-4 flex items-center justify-between"
                style={{ borderBottom: "1px solid var(--border)" }}
            >
                <div>
                    <h2 className="font-bold text-lg font-display" style={{ color: "var(--text-primary)" }}>
                        🎬 Live Architecture Flow
                    </h2>
                    <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        Auto-advances through all 4 scenarios
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <span
                        className="text-xs px-3 py-1 rounded-full font-semibold font-display"
                        style={{ background: sc.cardBg, border: `1px solid ${sc.cardBorder}`, color: sc.tabText }}
                    >
                        {scenario.icon} {scenario.name}
                    </span>
                    <button
                        onClick={() => setIsPlaying(p => !p)}
                        className="text-xs px-3 py-1.5 rounded-lg transition-all btn-ghost"
                    >
                        {isPlaying ? "⏸ Pause" : "▶ Play"}
                    </button>
                </div>
            </div>

            {/* ── Scenario Tabs ─────────────────────────────────── */}
            <div className="flex gap-2 px-6 py-3" style={{ borderBottom: "1px solid var(--border)", background: "rgba(0,0,0,0.2)" }}>
                {SCENARIOS.map((s, i) => {
                    const colors = SC[s.color];
                    const active = activeScenario === i;
                    return (
                        <button
                            key={i}
                            onClick={() => { setActiveScenario(i); setIsPlaying(true); }}
                            className="flex-1 py-2 px-3 rounded-xl text-xs font-semibold transition-all duration-200 font-display"
                            style={{
                                background: active ? colors.tabBg : "rgba(255,255,255,0.03)",
                                border: `1px solid ${active ? colors.tabBorder : "var(--border)"}`,
                                color: active ? colors.tabText : "var(--text-muted)",
                                boxShadow: active ? colors.tabGlow : "none",
                            }}
                        >
                            <span className="block text-base mb-0.5">{s.icon}</span>
                            {s.name}
                        </button>
                    );
                })}
            </div>

            {/* ── Body ─────────────────────────────────────────── */}
            <div className="p-6 flex gap-6">

                {/* ── Pipeline Column ──────────────────────────── */}
                <div className="flex-1 min-w-0">

                    {/* Message bubble */}
                    <div
                        className="rounded-xl p-4 mb-5"
                        style={{
                            background: sc.cardBg,
                            border: `1px solid ${sc.cardBorder}`,
                        }}
                    >
                        <p className="text-xs font-semibold mb-2" style={{ color: sc.tabText, fontFamily: "var(--font-display)" }}>
                            {scenario.icon} {scenario.name} · {scenario.desc}
                        </p>
                        <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                            &ldquo;{scenario.message}&rdquo;
                        </p>
                    </div>

                    {/* Steps */}
                    <div>
                        {visibleSteps.map((step, i) => {
                            const isDone      = completed.includes(step.id);
                            const isActive    = activeStep === i;
                            const isBlockedHere = isBlocked && step.id === scenario.blockAt;
                            const c           = C[step.color] || C.blue;
                            const isLast      = i === visibleSteps.length - 1;

                            return (
                                <div key={step.id}>
                                    {/* Step card */}
                                    <div
                                        className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300"
                                        style={{
                                            background: isBlockedHere
                                                ? "rgba(239,68,68,0.12)"
                                                : isActive
                                                    ? c.bg
                                                    : isDone
                                                        ? "rgba(255,255,255,0.02)"
                                                        : "transparent",
                                            border: `1px solid ${
                                                isBlockedHere
                                                    ? "rgba(239,68,68,0.5)"
                                                    : isActive
                                                        ? c.border
                                                        : isDone
                                                            ? "var(--border)"
                                                            : "transparent"
                                            }`,
                                            boxShadow: isBlockedHere
                                                ? "0 0 28px rgba(239,68,68,0.4)"
                                                : isActive
                                                    ? c.shadow
                                                    : "none",
                                        }}
                                    >
                                        {/* Icon bubble */}
                                        <div
                                            className="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
                                            style={{
                                                background: isBlockedHere
                                                    ? "rgba(239,68,68,0.2)"
                                                    : isActive
                                                        ? c.bg
                                                        : isDone
                                                            ? "rgba(255,255,255,0.06)"
                                                            : "rgba(255,255,255,0.03)",
                                                border: `1px solid ${isActive || isBlockedHere ? c.border : "var(--border)"}`,
                                            }}
                                        >
                                            {isActive && step.isPulse
                                                ? <span style={{ animation: "thinking 1.2s ease-in-out infinite" }}>{step.icon}</span>
                                                : isBlockedHere
                                                    ? "🚫"
                                                    : step.icon}
                                        </div>

                                        {/* Text */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <p
                                                    className="text-sm font-semibold font-display"
                                                    style={{
                                                        color: isBlockedHere ? "#f87171"
                                                            : isActive ? c.text
                                                            : isDone ? "var(--text-secondary)"
                                                            : "var(--text-muted)",
                                                    }}
                                                >
                                                    {step.label}
                                                </p>
                                                {step.isAgentic && (
                                                    <span
                                                        className="text-xs px-1.5 py-0.5 rounded-full font-medium"
                                                        style={{ background: "rgba(249,115,22,0.15)", color: "#fb923c", border: "1px solid rgba(249,115,22,0.3)" }}
                                                    >
                                                        agentic
                                                    </span>
                                                )}
                                                {step.canBlock && !isBlockedHere && (
                                                    <span
                                                        className="text-xs px-1.5 py-0.5 rounded-full font-medium"
                                                        style={{ background: "rgba(239,68,68,0.1)", color: "#f87171", border: "1px solid rgba(239,68,68,0.25)" }}
                                                    >
                                                        safety gate
                                                    </span>
                                                )}
                                            </div>
                                            <p
                                                className="text-xs mt-0.5"
                                                style={{ color: isActive ? "var(--text-secondary)" : "var(--text-muted)" }}
                                            >
                                                {isBlockedHere ? "❌ Request rejected by safety guardrail" : step.desc}
                                            </p>
                                        </div>

                                        {/* Status indicator */}
                                        <div className="flex-shrink-0 w-8 flex justify-center">
                                            {isBlockedHere ? (
                                                <span
                                                    className="text-xs px-2 py-0.5 rounded-full font-bold font-mono"
                                                    style={{ background: "rgba(239,68,68,0.2)", color: "#f87171", border: "1px solid rgba(239,68,68,0.4)" }}
                                                >
                                                    ✕
                                                </span>
                                            ) : isActive ? (
                                                <div className="flex gap-0.5">
                                                    {[0, 1, 2].map(n => (
                                                        <div key={n} className="thinking-dot" style={{ animationDelay: `${n * 0.2}s`, background: c.dot }} />
                                                    ))}
                                                </div>
                                            ) : isDone ? (
                                                <span style={{ color: C.green.dot, fontSize: "16px", fontWeight: 700 }}>✓</span>
                                            ) : (
                                                <span style={{ color: "var(--border)", fontSize: "14px" }}>○</span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Connector line */}
                                    {!isLast && !isBlockedHere && (
                                        <div className="flex items-center justify-center" style={{ height: "14px" }}>
                                            <div
                                                style={{
                                                    width: "1px",
                                                    height: "100%",
                                                    background: isDone
                                                        ? `linear-gradient(to bottom, ${c.connLine}, rgba(255,255,255,0.05))`
                                                        : "var(--border)",
                                                    transition: "background 0.4s ease",
                                                    borderRadius: "1px",
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {/* Success output */}
                    {completed.includes("output") && (
                        <div
                            className="mt-4 rounded-xl p-4 animate-in"
                            style={{
                                background: "rgba(16,185,129,0.08)",
                                border: "1px solid rgba(16,185,129,0.4)",
                                boxShadow: "0 0 24px rgba(16,185,129,0.2)",
                            }}
                        >
                            <p className="text-xs font-semibold mb-2 font-display" style={{ color: "#34d399" }}>
                                ✅ OrcaResponse delivered
                            </p>
                            <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                                &ldquo;{scenario.response}&rdquo;
                            </p>
                            <div className="flex gap-3 mt-3">
                                {["ID", "Metrics", "Trace", "Mode"].map(tag => (
                                    <span key={tag} className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Blocked output */}
                    {isBlocked && (
                        <div
                            className="mt-4 rounded-xl p-4 animate-in"
                            style={{
                                background: "rgba(239,68,68,0.08)",
                                border: "1px solid rgba(239,68,68,0.4)",
                                boxShadow: "0 0 24px rgba(239,68,68,0.2)",
                            }}
                        >
                            <p className="text-xs font-semibold mb-2 font-display" style={{ color: "#f87171" }}>
                                🛡️ Blocked by input guardrail
                            </p>
                            <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                                &ldquo;I cannot help with that request.&rdquo;
                            </p>
                        </div>
                    )}
                </div>

                {/* ── Right Panel ──────────────────────────────── */}
                <div className="w-52 flex-shrink-0 space-y-3">

                    {/* Layer legend */}
                    <div
                        className="rounded-xl p-4"
                        style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}
                    >
                        <p
                            className="text-xs font-bold uppercase tracking-widest mb-3 font-display"
                            style={{ color: "var(--text-muted)" }}
                        >
                            Layers
                        </p>
                        <div className="space-y-2.5">
                            {LAYER_LEGEND.map(item => (
                                <div key={item.label} className="flex items-center gap-2.5">
                                    <div
                                        className="w-2 h-2 rounded-full flex-shrink-0"
                                        style={{ background: item.dot, boxShadow: `0 0 6px ${item.dot}` }}
                                    />
                                    <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{item.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Stats */}
                    <div
                        className="rounded-xl p-4"
                        style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}
                    >
                        <p
                            className="text-xs font-bold uppercase tracking-widest mb-3 font-display"
                            style={{ color: "var(--text-muted)" }}
                        >
                            Pipeline Stats
                        </p>
                        <div className="space-y-2">
                            {[
                                { label: "Total Steps",   value: "9",  color: "var(--text-primary)" },
                                { label: "Safety Gates",  value: "2",  color: "#f87171" },
                                { label: "Tool Calls",    value: "3",  color: "#fb923c" },
                                { label: "Run Modes",     value: "3",  color: "#818cf8" },
                            ].map(row => (
                                <div key={row.label} className="flex justify-between items-center">
                                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>{row.label}</span>
                                    <span className="text-xs font-bold font-mono" style={{ color: row.color }}>{row.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Current mode */}
                    <div
                        className="rounded-xl p-4"
                        style={{ background: sc.cardBg, border: `1px solid ${sc.cardBorder}` }}
                    >
                        <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>Current Mode</p>
                        <p className="font-bold font-display" style={{ color: sc.tabText }}>
                            {scenario.icon} {scenario.name}
                        </p>
                        <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{scenario.desc}</p>
                    </div>

                    {/* Progress */}
                    <div
                        className="rounded-xl p-4"
                        style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}
                    >
                        <div className="flex justify-between mb-2">
                            <p
                                className="text-xs font-bold uppercase tracking-widest font-display"
                                style={{ color: "var(--text-muted)" }}
                            >
                                Progress
                            </p>
                            <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                {completed.length}/{visibleSteps.length}
                            </span>
                        </div>
                        <div
                            className="w-full rounded-full overflow-hidden"
                            style={{ height: "6px", background: "var(--bg-base)" }}
                        >
                            <div
                                className="h-full rounded-full transition-all duration-500"
                                style={{
                                    width: `${visibleSteps.length ? (completed.length / visibleSteps.length) * 100 : 0}%`,
                                    background: isBlocked
                                        ? "linear-gradient(90deg, #ef4444, #f97316)"
                                        : completed.includes("output")
                                            ? "linear-gradient(90deg, #10b981, #22d3ee)"
                                            : "linear-gradient(90deg, var(--accent), var(--cyan))",
                                    boxShadow: `0 0 10px ${isBlocked ? "rgba(239,68,68,0.5)" : "var(--accent-glow)"}`,
                                }}
                            />
                        </div>
                        <p className="text-xs mt-2 text-right font-mono" style={{ color: "var(--text-muted)" }}>
                            {completed.includes("output") ? "✓ Complete"
                                : isBlocked ? "✕ Blocked"
                                : activeStep >= 0 ? "Running..."
                                : "Idle"}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
