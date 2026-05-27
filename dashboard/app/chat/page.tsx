"use client";

import { useState, useRef, useEffect } from "react";
import { chatWithOrca, ChatResponse } from "@/lib/api";

interface Message {
    role: "user" | "orca";
    content: string;
    blocked: boolean;
    duration: number;
    tokens: number;
}

const MODES = [
    {
        value: "single_turn",
        icon: "🎯",
        label: "Single Turn",
        shortDesc: "No memory",
        color: "#6366f1",
        bg: "rgba(99,102,241,0.15)",
        border: "rgba(99,102,241,0.5)",
        cardBg: "rgba(99,102,241,0.07)",
        cardBorder: "rgba(99,102,241,0.25)",
        fullDesc: "Each message is independent. ORCA won't remember anything from earlier in the conversation.",
        whenToUse: "Quick factual questions, one-off tasks, or when you don't need context.",
        examples: [
            { text: "What is the capital of Japan?",       tag: "Geography" },
            { text: "Who invented the telephone?",         tag: "History"   },
            { text: "Explain photosynthesis simply.",      tag: "Science"   },
        ],
    },
    {
        value: "multi_turn",
        icon: "🧠",
        label: "Multi Turn",
        shortDesc: "Remembers chat",
        color: "#a855f7",
        bg: "rgba(168,85,247,0.15)",
        border: "rgba(168,85,247,0.5)",
        cardBg: "rgba(168,85,247,0.07)",
        cardBorder: "rgba(168,85,247,0.25)",
        fullDesc: "ORCA keeps a memory of everything said in the session. Follow-up questions reference earlier context.",
        whenToUse: "Multi-step conversations, teaching ORCA facts about you, or building on earlier answers.",
        examples: [
            { text: "My name is Swathi — remember it!",   tag: "Memory setup" },
            { text: "I'm learning Python from scratch.",   tag: "Context"      },
            { text: "What did I just tell you my name is?", tag: "Memory test" },
        ],
    },
    {
        value: "agentic",
        icon: "🔧",
        label: "Agentic",
        shortDesc: "Uses tools",
        color: "#f97316",
        bg: "rgba(249,115,22,0.15)",
        border: "rgba(249,115,22,0.5)",
        cardBg: "rgba(249,115,22,0.07)",
        cardBorder: "rgba(249,115,22,0.25)",
        fullDesc: "ORCA can call real tools — a calculator, a search engine, and a database — to answer questions it can't answer alone.",
        whenToUse: "Calculations, real-time lookups, or anything that needs external data.",
        examples: [
            { text: "Calculate 15% tip on $47.50",         tag: "Calculator" },
            { text: "What is 25% of 320?",                 tag: "Calculator" },
            { text: "Search for the latest Python news.",  tag: "Search"     },
        ],
    },
];

const SAFETY_EXAMPLES = [
    { text: "How do I hack into a website?",              tag: "Will be blocked 🛡️" },
    { text: "Give me instructions to make a weapon.",     tag: "Will be blocked 🛡️" },
];

export default function ChatPage() {
    const [messages,  setMessages]  = useState<Message[]>([]);
    const [input,     setInput]     = useState("");
    const [mode,      setMode]      = useState("single_turn");
    const [sessionId, setSessionId] = useState("session_" + Date.now());
    const [loading,   setLoading]   = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async (override?: string) => {
        const text = (override ?? input).trim();
        if (!text || loading) return;
        setInput("");
        setMessages(prev => [...prev, { role: "user", content: text, blocked: false, duration: 0, tokens: 0 }]);
        setLoading(true);
        try {
            const resp: ChatResponse = await chatWithOrca(text, mode, mode === "multi_turn" ? sessionId : null);
            setMessages(prev => [...prev, {
                role: "orca",
                content: resp.content,
                blocked: !resp.success || !!resp.blocked_reason,
                duration: resp.duration_ms,
                tokens: resp.tokens_used,
            }]);
        } catch (e) {
            const raw = e instanceof Error ? e.message : "Unknown error";
            const isNetwork = raw.includes("DOCTYPE") || raw.includes("fetch") || raw.includes("Failed") || raw.startsWith("HTTP");
            setMessages(prev => [...prev, {
                role: "orca",
                content: isNetwork
                    ? "Could not reach the ORCA backend. Check that NEXT_PUBLIC_API_URL is set correctly in Vercel and the Railway service is running."
                    : `Error: ${raw}`,
                blocked: false,
                duration: 0,
                tokens: 0,
            }]);
        } finally {
            setLoading(false);
        }
    };

    const clearChat = () => { setMessages([]); setSessionId("session_" + Date.now()); };
    const activeMode = MODES.find(m => m.value === mode)!;

    return (
        <div
            className="flex flex-col"
            style={{ height: "100%", minHeight: "100%", background: "radial-gradient(ellipse at top, #0d0819 0%, var(--bg-base) 65%)" }}
        >
            {/* ── Header ──────────────────────────────────── */}
            <div
                className="flex items-start justify-between px-4 sm:px-6 py-3 sm:py-4 flex-shrink-0"
                style={{ borderBottom: "1px solid var(--border)" }}
            >
                <div>
                    <h1 className="text-2xl font-black tracking-tight font-display" style={{ color: "var(--text-primary)" }}>
                        💬 Chat with <span className="gradient-text">ORCA</span>
                    </h1>
                    <p className="text-sm mt-0.5" style={{ color: "var(--text-muted)" }}>
                        Talk to ORCA in 3 modes — single turn, memory, and tool use
                    </p>
                </div>
                <button onClick={clearChat} className="btn-ghost text-sm px-3 py-1.5 mt-0.5">
                    🗑 Clear
                </button>
            </div>

            {/* ── Mode Tabs ───────────────────────────────── */}
            <div className="flex gap-2 px-4 sm:px-6 py-3 flex-shrink-0 overflow-x-auto" style={{ borderBottom: "1px solid var(--border)" }}>
                {MODES.map(m => {
                    const active = mode === m.value;
                    return (
                        <button
                            key={m.value}
                            onClick={() => setMode(m.value)}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 font-display"
                            style={{
                                background: active ? m.bg : "rgba(255,255,255,0.03)",
                                border: `1px solid ${active ? m.border : "var(--border)"}`,
                                color: active ? m.color : "var(--text-muted)",
                                boxShadow: active ? `0 0 16px ${m.bg}` : "none",
                            }}
                        >
                            <span>{m.icon}</span>
                            <span>{m.label}</span>
                            <span className="hidden sm:inline text-xs opacity-70">· {m.shortDesc}</span>
                        </button>
                    );
                })}
                {mode === "multi_turn" && (
                    <span
                        className="ml-auto self-center text-xs px-3 py-1 rounded-full font-mono"
                        style={{ background: "rgba(168,85,247,0.1)", color: "#c084fc", border: "1px solid rgba(168,85,247,0.3)" }}
                    >
                        Session: …{sessionId.slice(-6)}
                    </span>
                )}
            </div>

            {/* ── Messages / Guide ────────────────────────── */}
            <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-6">

                {/* ── Empty state guide ─────────────────────── */}
                {messages.length === 0 && (
                    <div className="max-w-2xl mx-auto space-y-6">

                        {/* Hero */}
                        <div className="text-center py-4">
                            <div
                                className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4"
                                style={{
                                    background: "rgba(99,102,241,0.1)",
                                    border: "1px solid rgba(99,102,241,0.3)",
                                    boxShadow: "0 0 32px rgba(99,102,241,0.2)",
                                }}
                            >
                                🐋
                            </div>
                            <h2 className="text-xl font-black mb-1 font-display" style={{ color: "var(--text-primary)" }}>
                                ORCA is ready
                            </h2>
                            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                                Type any message below, or pick an example — it sends immediately
                            </p>
                        </div>

                        {/* How it works callout */}
                        <div
                            className="rounded-2xl p-5 flex gap-4"
                            style={{ background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.25)" }}
                        >
                            <span className="text-2xl flex-shrink-0">✏️</span>
                            <div>
                                <p className="text-sm font-semibold font-display mb-1" style={{ color: "var(--text-primary)" }}>
                                    Just type and press Enter
                                </p>
                                <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                                    This is a <strong style={{ color: "var(--text-primary)" }}>live chat</strong> — every message goes to the real ORCA agent running on the backend.
                                    Switch modes using the tabs above to change how ORCA behaves.
                                    Each reply shows response time and token count underneath.
                                </p>
                            </div>
                        </div>

                        {/* 3 Mode cards */}
                        <div>
                            <p className="text-xs font-bold uppercase tracking-widest mb-3 font-display" style={{ color: "var(--text-muted)" }}>
                                The 3 modes — what they do
                            </p>
                            <div className="space-y-3">
                                {MODES.map(m => (
                                    <div
                                        key={m.value}
                                        className="rounded-2xl p-5"
                                        style={{ background: m.cardBg, border: `1px solid ${m.cardBorder}` }}
                                    >
                                        {/* Mode header */}
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="text-xl">{m.icon}</span>
                                            <span className="font-bold font-display text-sm" style={{ color: m.color }}>{m.label}</span>
                                            <button
                                                onClick={() => setMode(m.value)}
                                                className="ml-auto text-xs px-2.5 py-1 rounded-lg font-semibold transition-all"
                                                style={{
                                                    background: mode === m.value ? m.bg : "rgba(255,255,255,0.05)",
                                                    border: `1px solid ${mode === m.value ? m.border : "var(--border)"}`,
                                                    color: mode === m.value ? m.color : "var(--text-muted)",
                                                }}
                                            >
                                                {mode === m.value ? "✓ Active" : "Switch"}
                                            </button>
                                        </div>

                                        {/* Description */}
                                        <p className="text-sm leading-relaxed mb-1" style={{ color: "var(--text-secondary)" }}>
                                            {m.fullDesc}
                                        </p>
                                        <p className="text-xs mb-3 font-mono" style={{ color: "var(--text-muted)" }}>
                                            ↳ Best for: {m.whenToUse}
                                        </p>

                                        {/* Example chips */}
                                        <div className="flex gap-2 flex-wrap">
                                            {m.examples.map(ex => (
                                                <button
                                                    key={ex.text}
                                                    onClick={() => { setMode(m.value); sendMessage(ex.text); }}
                                                    className="text-xs px-3 py-1.5 rounded-lg transition-all text-left"
                                                    style={{
                                                        background: "rgba(255,255,255,0.04)",
                                                        border: "1px solid var(--border)",
                                                        color: "var(--text-secondary)",
                                                    }}
                                                    onMouseEnter={e => {
                                                        e.currentTarget.style.borderColor = m.cardBorder;
                                                        e.currentTarget.style.color = m.color;
                                                    }}
                                                    onMouseLeave={e => {
                                                        e.currentTarget.style.borderColor = "var(--border)";
                                                        e.currentTarget.style.color = "var(--text-secondary)";
                                                    }}
                                                >
                                                    &ldquo;{ex.text}&rdquo;
                                                    <span className="ml-1.5 opacity-50">{ex.tag}</span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Multi-turn walkthrough */}
                        <div
                            className="rounded-2xl p-5"
                            style={{ background: "rgba(168,85,247,0.07)", border: "1px solid rgba(168,85,247,0.25)" }}
                        >
                            <p className="text-xs font-bold uppercase tracking-widest mb-3 font-display" style={{ color: "#c084fc" }}>
                                🧠 Try this multi-turn sequence
                            </p>
                            <div className="space-y-2">
                                {[
                                    { n: "1", msg: "My name is Swathi.",            note: "Switch to Multi Turn, send this first" },
                                    { n: "2", msg: "I love programming in Python.", note: "ORCA stores this in session memory"      },
                                    { n: "3", msg: "What do you know about me?",    note: "ORCA recalls everything from this session" },
                                ].map(step => (
                                    <div key={step.n} className="flex gap-3 items-start">
                                        <span
                                            className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 font-mono"
                                            style={{ background: "rgba(168,85,247,0.2)", color: "#c084fc" }}
                                        >
                                            {step.n}
                                        </span>
                                        <div>
                                            <button
                                                onClick={() => { setMode("multi_turn"); sendMessage(step.msg); }}
                                                className="text-sm font-medium transition-all"
                                                style={{ color: "var(--text-primary)" }}
                                                onMouseEnter={e => (e.currentTarget.style.color = "#c084fc")}
                                                onMouseLeave={e => (e.currentTarget.style.color = "var(--text-primary)")}
                                            >
                                                &ldquo;{step.msg}&rdquo;
                                            </button>
                                            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{step.note}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Safety demo */}
                        <div
                            className="rounded-2xl p-5"
                            style={{ background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.2)" }}
                        >
                            <p className="text-xs font-bold uppercase tracking-widest mb-3 font-display" style={{ color: "#f87171" }}>
                                🛡️ See the safety guardrail in action
                            </p>
                            <p className="text-sm mb-3 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                                ORCA has an input guardrail that blocks harmful requests before they reach the LLM. Try sending one of these — you&apos;ll get a blocked reply instead of an answer.
                            </p>
                            <div className="flex gap-2 flex-wrap">
                                {SAFETY_EXAMPLES.map(ex => (
                                    <button
                                        key={ex.text}
                                        onClick={() => { setMode("single_turn"); sendMessage(ex.text); }}
                                        className="text-xs px-3 py-1.5 rounded-lg transition-all"
                                        style={{
                                            background: "rgba(239,68,68,0.1)",
                                            border: "1px solid rgba(239,68,68,0.3)",
                                            color: "#f87171",
                                        }}
                                    >
                                        &ldquo;{ex.text}&rdquo;
                                        <span className="ml-1.5 opacity-60">{ex.tag}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Pro tips */}
                        <div
                            className="rounded-2xl p-5"
                            style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                        >
                            <p className="text-xs font-bold uppercase tracking-widest mb-3 font-display" style={{ color: "var(--text-muted)" }}>
                                💡 Tips
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {[
                                    { icon: "⏎",  tip: "Press Enter to send — no need to click the button" },
                                    { icon: "🔄",  tip: "Hit Clear (top right) to reset the session and start fresh" },
                                    { icon: "📋",  tip: "Copy any ORCA reply and paste it into the Evaluate page to score it" },
                                    { icon: "⏱️",  tip: "Response time (ms) and token count appear under every ORCA reply" },
                                ].map(t => (
                                    <div key={t.tip} className="flex gap-2.5">
                                        <span
                                            className="w-6 h-6 rounded-lg flex items-center justify-center text-xs flex-shrink-0 font-mono"
                                            style={{ background: "rgba(99,102,241,0.15)", color: "var(--accent)" }}
                                        >
                                            {t.icon}
                                        </span>
                                        <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>{t.tip}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                    </div>
                )}

                {/* ── Chat messages ─────────────────────────── */}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in mb-4`}>
                        <div style={{ maxWidth: "min(640px, 80%)" }}>
                            {msg.role === "orca" && (
                                <p className="text-xs mb-1 ml-1 font-display" style={{ color: "var(--text-muted)" }}>
                                    🐋 ORCA
                                </p>
                            )}
                            <div
                                className={`px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                                    msg.role === "user" ? "bubble-user" : msg.blocked ? "" : "bubble-assistant"
                                }`}
                                style={msg.blocked ? {
                                    background: "rgba(239,68,68,0.1)",
                                    border: "1px solid rgba(239,68,68,0.4)",
                                    borderRadius: "16px 16px 16px 4px",
                                    color: "#fca5a5",
                                } : { color: "var(--text-primary)" }}
                            >
                                {msg.blocked && <span className="font-semibold">🛡️ Blocked: </span>}
                                {msg.content}
                            </div>
                            {msg.role === "orca" && msg.duration > 0 && (
                                <div className="flex gap-3 mt-1 ml-1">
                                    <span className="metric-pill">{msg.duration}ms</span>
                                    <span className="metric-pill">{msg.tokens} tokens</span>
                                    {msg.blocked && <span className="metric-pill" style={{ color: "#f87171" }}>blocked</span>}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start animate-in mb-4">
                        <div className="bubble-assistant px-4 py-3">
                            <div className="flex gap-1.5 items-center" style={{ height: "20px" }}>
                                <div className="thinking-dot" style={{ background: activeMode.color }} />
                                <div className="thinking-dot" style={{ background: activeMode.color, animationDelay: "0.2s" }} />
                                <div className="thinking-dot" style={{ background: activeMode.color, animationDelay: "0.4s" }} />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* ── Input Bar ───────────────────────────────── */}
            <div
                className="flex gap-3 px-4 sm:px-6 py-3 sm:py-4 flex-shrink-0"
                style={{ borderTop: "1px solid var(--border)" }}
            >
                <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && sendMessage()}
                    placeholder={`Message ORCA in ${activeMode.label} mode… (Enter to send)`}
                    disabled={loading}
                    className="flex-1 input-dark px-4 py-3 text-sm"
                />
                <button
                    onClick={() => sendMessage()}
                    disabled={loading || !input.trim()}
                    className="btn-primary px-6 py-3 text-sm"
                >
                    {loading ? "…" : "Send →"}
                </button>
            </div>
        </div>
    );
}
