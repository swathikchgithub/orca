"use client";

import ArchitectureDiagram from "@/components/ArchitectureDiagram";

// ── Simple Flow Guide ─────────────────────────────────────────────
const FLOW_NODES = [
    { icon: "👤", label: "You ask",         sub: "A question",             color: "#6366f1", bg: "rgba(99,102,241,0.12)",  border: "rgba(99,102,241,0.5)" },
    { icon: "🛡️", label: "Safety check",    sub: "Is it okay?",            color: "#ef4444", bg: "rgba(239,68,68,0.12)",   border: "rgba(239,68,68,0.5)"  },
    { icon: "🧠", label: "ORCA thinks",     sub: "Finds the answer",       color: "#a855f7", bg: "rgba(168,85,247,0.12)", border: "rgba(168,85,247,0.5)" },
    { icon: "🔧", label: "Uses tools",      sub: "Calculator / Search",    color: "#f97316", bg: "rgba(249,115,22,0.12)",  border: "rgba(249,115,22,0.5)" },
    { icon: "✅", label: "Answers you!",    sub: "Safe & helpful",         color: "#10b981", bg: "rgba(16,185,129,0.12)",  border: "rgba(16,185,129,0.5)" },
];

const MODES = [
    {
        icon: "🎯", name: "Simple",   color: "#6366f1", bg: "rgba(99,102,241,0.08)", border: "rgba(99,102,241,0.3)",
        title: "Single-Turn",
        story: "You ask one question, ORCA answers it. Done! Like asking a librarian one thing.",
        skips: "Skips memory and tools — quick and straightforward.",
    },
    {
        icon: "🧠", name: "Memory",   color: "#a855f7", bg: "rgba(168,85,247,0.08)", border: "rgba(168,85,247,0.3)",
        title: "Multi-Turn",
        story: "ORCA remembers everything you said before — like chatting with a friend who never forgets.",
        skips: "Loads your chat history before thinking, saves the reply after.",
    },
    {
        icon: "🔧", name: "With Tools", color: "#f97316", bg: "rgba(249,115,22,0.08)", border: "rgba(249,115,22,0.3)",
        title: "Agentic",
        story: "ORCA can pick up tools — a calculator, a search engine, a database — like a student who can use a calculator on a test.",
        skips: "Goes through the Tool Router step before writing the reply.",
    },
    {
        icon: "🚫", name: "Blocked",  color: "#ef4444", bg: "rgba(239,68,68,0.08)",   border: "rgba(239,68,68,0.3)",
        title: "Safety Blocked",
        story: "If a question tries to do something harmful, the Safety Guard stops it right at the door — ORCA never even sees it.",
        skips: "Exits immediately after the input guardrail. No LLM call happens.",
    },
];

export default function ArchitecturePage() {
    return (
        <div
            className="min-h-screen p-4 sm:p-6 lg:p-8 noise header-grid"
            style={{ background: "radial-gradient(ellipse at top, #130d2a 0%, var(--bg-base) 60%)" }}
        >
            <div className="max-w-6xl mx-auto relative z-10">

                {/* ── Page Header ──────────────────────────────── */}
                <div className="mb-10 fade-in-up">
                    <div className="flex items-center gap-2 mb-4">
                        <span className="text-xs px-3 py-1 rounded-full font-medium" style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.3)", color: "var(--accent)" }}>
                            Live Visualization
                        </span>
                        <span className="text-xs px-3 py-1 rounded-full" style={{ border: "1px solid var(--border)", color: "var(--text-muted)" }}>
                            4 Scenarios · 9 Steps
                        </span>
                    </div>
                    <h1 className="text-4xl font-black mb-3 tracking-tight font-display" style={{ color: "var(--text-primary)" }}>
                        🏗️ <span className="gradient-text">System</span> Architecture
                    </h1>
                    <p style={{ color: "var(--text-secondary)" }}>
                        Watch ORCA process every request in real time — from user input to OrcaResponse
                    </p>
                </div>

                {/* ══════════════════════════════════════════════════
                    SIMPLE GUIDE — child-friendly explainer
                ══════════════════════════════════════════════════ */}
                <div className="mb-10">

                    {/* Section label */}
                    <div className="flex items-center gap-3 mb-6">
                        <span className="text-2xl">🧒</span>
                        <div>
                            <h2 className="text-xl font-black font-display" style={{ color: "var(--text-primary)" }}>
                                How ORCA Works
                                <span className="gradient-text"> — Simple Guide</span>
                            </h2>
                            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                                Simple enough for a 5-year-old to understand!
                            </p>
                        </div>
                    </div>

                    {/* Story intro */}
                    <div
                        className="rounded-2xl p-6 mb-6"
                        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                    >
                        <p className="text-base leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                            🐋 <strong style={{ color: "var(--text-primary)" }}>ORCA is like a really smart friend who lives inside the computer.</strong>{" "}
                            When you type a question, ORCA doesn&apos;t just answer right away.
                            It goes through careful steps — like a chef who checks the recipe,
                            washes their hands, and makes sure the food is safe before serving it.
                            Every single time, no shortcuts.
                        </p>
                    </div>

                    {/* Visual flow diagram */}
                    <div
                        className="rounded-2xl p-6 mb-6 overflow-x-auto"
                        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                    >
                        <p className="text-xs font-bold uppercase tracking-widest mb-5 font-display" style={{ color: "var(--text-muted)" }}>
                            The journey of your message
                        </p>

                        {/* Main flow row */}
                        <div className="flex items-center gap-0 min-w-max">
                            {FLOW_NODES.map((node, i) => (
                                <div key={node.label} className="flex items-center">
                                    {/* Node */}
                                    <div
                                        className="flex flex-col items-center text-center"
                                        style={{ width: "110px" }}
                                    >
                                        <div
                                            className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mb-2 flex-shrink-0"
                                            style={{
                                                background: node.bg,
                                                border: `2px solid ${node.border}`,
                                                boxShadow: `0 0 20px ${node.bg}`,
                                            }}
                                        >
                                            {node.icon}
                                        </div>
                                        <p className="text-xs font-bold font-display" style={{ color: node.color }}>{node.label}</p>
                                        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{node.sub}</p>
                                    </div>

                                    {/* Arrow (not after last) */}
                                    {i < FLOW_NODES.length - 1 && (
                                        <div className="flex flex-col items-center mx-1" style={{ width: "40px" }}>
                                            {/* Main arrow */}
                                            <div className="flex items-center" style={{ marginBottom: "32px" }}>
                                                <div style={{ width: "28px", height: "2px", background: `linear-gradient(90deg, ${node.color}88, ${FLOW_NODES[i+1].color}88)` }} />
                                                <div style={{ width: 0, height: 0, borderTop: "5px solid transparent", borderBottom: "5px solid transparent", borderLeft: `7px solid ${FLOW_NODES[i+1].color}88` }} />
                                            </div>
                                            {/* Safety branch */}
                                            {i === 1 && (
                                                <div className="flex flex-col items-center" style={{ marginTop: "-28px" }}>
                                                    <div style={{ width: "2px", height: "18px", background: "rgba(239,68,68,0.5)" }} />
                                                    <div
                                                        className="rounded-xl px-2 py-1 text-center"
                                                        style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.4)", minWidth: "56px" }}
                                                    >
                                                        <div className="text-base">🚫</div>
                                                        <p className="text-xs font-bold" style={{ color: "#f87171" }}>BLOCKED</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Legend */}
                        <div className="flex items-center gap-4 mt-6 pt-5" style={{ borderTop: "1px solid var(--border)" }}>
                            <div className="flex items-center gap-2">
                                <div style={{ width: "24px", height: "2px", background: "var(--accent)" }} />
                                <div style={{ width: 0, height: 0, borderTop: "4px solid transparent", borderBottom: "4px solid transparent", borderLeft: "6px solid var(--accent)" }} />
                                <span className="text-xs" style={{ color: "var(--text-muted)" }}>Normal path</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div style={{ width: "2px", height: "12px", background: "rgba(239,68,68,0.5)" }} />
                                <span className="text-xs" style={{ color: "var(--text-muted)" }}>Blocked path (harmful request)</span>
                            </div>
                        </div>
                    </div>

                    {/* 4 mode cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                        {MODES.map(m => (
                            <div
                                key={m.name}
                                className="rounded-2xl p-5"
                                style={{ background: m.bg, border: `1px solid ${m.border}` }}
                            >
                                <div className="flex items-center gap-3 mb-3">
                                    <span className="text-2xl">{m.icon}</span>
                                    <div>
                                        <p className="font-bold font-display text-sm" style={{ color: m.color }}>{m.title}</p>
                                        <p className="text-xs" style={{ color: "var(--text-muted)" }}>Mode</p>
                                    </div>
                                </div>
                                <p className="text-sm leading-relaxed mb-2" style={{ color: "var(--text-secondary)" }}>
                                    {m.story}
                                </p>
                                <p className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                    ↳ {m.skips}
                                </p>
                            </div>
                        ))}
                    </div>

                    {/* 3 golden rules */}
                    <div
                        className="rounded-2xl p-6"
                        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                    >
                        <p className="text-xs font-bold uppercase tracking-widest mb-4 font-display" style={{ color: "var(--text-muted)" }}>
                            🌟 Three things ORCA always does
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            {[
                                { icon: "🛡️", title: "Always checks safety", desc: "Every request goes through two safety guards — one before, one after. No exceptions." },
                                { icon: "💾", title: "Remembers if you ask", desc: "In multi-turn mode, ORCA stores and loads your conversation so it never forgets what you said." },
                                { icon: "📦", title: "Wraps every answer", desc: "The reply comes back as an OrcaResponse — an object with the text, timing, token count, and full trace." },
                            ].map(rule => (
                                <div key={rule.title} className="flex gap-3">
                                    <span className="text-2xl flex-shrink-0 mt-0.5">{rule.icon}</span>
                                    <div>
                                        <p className="text-sm font-bold font-display mb-1" style={{ color: "var(--text-primary)" }}>{rule.title}</p>
                                        <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>{rule.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ══════════════════════════════════════════════════
                    LIVE ANIMATED DIAGRAM
                ══════════════════════════════════════════════════ */}
                <div>
                    <div className="flex items-center gap-3 mb-6">
                        <span className="text-2xl">🎬</span>
                        <div>
                            <h2 className="text-xl font-black font-display" style={{ color: "var(--text-primary)" }}>
                                Live Pipeline Walkthrough
                            </h2>
                            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                                Watch each step light up in real time as ORCA processes a request
                            </p>
                        </div>
                    </div>
                    <ArchitectureDiagram />
                </div>

            </div>
        </div>
    );
}
