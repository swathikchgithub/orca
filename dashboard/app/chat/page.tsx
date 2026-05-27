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
    },
    {
        value: "multi_turn",
        icon: "🧠",
        label: "Multi Turn",
        shortDesc: "Remembers chat",
        color: "#a855f7",
        bg: "rgba(168,85,247,0.15)",
        border: "rgba(168,85,247,0.5)",
    },
    {
        value: "agentic",
        icon: "🔧",
        label: "Agentic",
        shortDesc: "Uses tools",
        color: "#f97316",
        bg: "rgba(249,115,22,0.15)",
        border: "rgba(249,115,22,0.5)",
    },
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
                    ? "Could not reach the ORCA backend. Check that NEXT_PUBLIC_API_URL is set in Vercel and the Railway service is running."
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
            style={{
                height: "100%",
                minHeight: "100%",
                background: "radial-gradient(ellipse at top, #0d0819 0%, var(--bg-base) 65%)",
            }}
        >
            {/* ── Header ────────────────────────────────────────── */}
            <div
                className="flex-shrink-0 px-6 sm:px-10 py-5"
                style={{ borderBottom: "1px solid var(--border)" }}
            >
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <div>
                        <h1
                            className="text-2xl sm:text-3xl font-black tracking-tight font-display"
                            style={{ color: "var(--text-primary)" }}
                        >
                            💬 Chat with <span className="gradient-text">ORCA</span>
                        </h1>
                        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                            Live agent — switch modes to change how ORCA behaves
                        </p>
                    </div>
                    <button
                        onClick={clearChat}
                        className="btn-ghost text-sm px-4 py-2 flex items-center gap-2"
                    >
                        🗑 Clear
                    </button>
                </div>
            </div>

            {/* ── Mode Tabs ─────────────────────────────────────── */}
            <div
                className="flex-shrink-0 px-6 sm:px-10 py-4"
                style={{ borderBottom: "1px solid var(--border)" }}
            >
                <div className="max-w-4xl mx-auto flex items-center gap-3 flex-wrap">
                    {MODES.map(m => {
                        const active = mode === m.value;
                        return (
                            <button
                                key={m.value}
                                onClick={() => setMode(m.value)}
                                className="flex items-center gap-2.5 px-5 py-3 rounded-xl text-sm font-bold transition-all duration-200 font-display"
                                style={{
                                    background: active ? m.bg : "rgba(255,255,255,0.04)",
                                    border: `1.5px solid ${active ? m.border : "var(--border)"}`,
                                    color: active ? m.color : "var(--text-muted)",
                                    boxShadow: active ? `0 0 20px ${m.bg}` : "none",
                                    fontSize: "0.9rem",
                                }}
                            >
                                <span className="text-lg">{m.icon}</span>
                                <span>{m.label}</span>
                                <span
                                    className="text-xs opacity-60 hidden sm:inline"
                                    style={{ fontWeight: 400 }}
                                >
                                    · {m.shortDesc}
                                </span>
                            </button>
                        );
                    })}
                    {mode === "multi_turn" && (
                        <span
                            className="ml-auto text-xs px-3 py-1.5 rounded-full font-mono"
                            style={{ background: "rgba(168,85,247,0.1)", color: "#c084fc", border: "1px solid rgba(168,85,247,0.3)" }}
                        >
                            Session: …{sessionId.slice(-6)}
                        </span>
                    )}
                </div>
            </div>

            {/* ── Messages ──────────────────────────────────────── */}
            <div className="flex-1 overflow-y-auto px-6 sm:px-10 py-8">
                <div className="max-w-4xl mx-auto space-y-6">

                    {/* Empty state */}
                    {messages.length === 0 && (
                        <div className="text-center py-16">
                            <div
                                className="w-20 h-20 rounded-3xl flex items-center justify-center text-4xl mx-auto mb-6"
                                style={{
                                    background: "rgba(99,102,241,0.1)",
                                    border: "1px solid rgba(99,102,241,0.3)",
                                    boxShadow: "0 0 40px rgba(99,102,241,0.15)",
                                }}
                            >
                                🐋
                            </div>
                            <h2 className="text-xl font-black mb-2 font-display" style={{ color: "var(--text-primary)" }}>
                                ORCA is ready
                            </h2>
                            <p className="text-sm mb-8" style={{ color: "var(--text-muted)" }}>
                                Type a message below, or try one of these examples
                            </p>

                            {/* Quick start examples */}
                            <div className="flex flex-wrap gap-3 justify-center">
                                {[
                                    { text: "What is the capital of Japan?",  mode: "single_turn", tag: "🎯" },
                                    { text: "My name is Swathi — remember it!", mode: "multi_turn",  tag: "🧠" },
                                    { text: "Calculate 15% tip on $47.50",     mode: "agentic",     tag: "🔧" },
                                    { text: "Who invented the telephone?",     mode: "single_turn", tag: "🎯" },
                                    { text: "What is 25% of 320?",            mode: "agentic",     tag: "🔧" },
                                ].map(ex => (
                                    <button
                                        key={ex.text}
                                        onClick={() => { setMode(ex.mode); sendMessage(ex.text); }}
                                        className="text-sm px-4 py-2.5 rounded-xl transition-all"
                                        style={{
                                            background: "var(--bg-card)",
                                            border: "1px solid var(--border)",
                                            color: "var(--text-secondary)",
                                        }}
                                        onMouseEnter={e => {
                                            e.currentTarget.style.borderColor = "rgba(99,102,241,0.5)";
                                            e.currentTarget.style.color = "var(--text-primary)";
                                        }}
                                        onMouseLeave={e => {
                                            e.currentTarget.style.borderColor = "var(--border)";
                                            e.currentTarget.style.color = "var(--text-secondary)";
                                        }}
                                    >
                                        {ex.tag} &ldquo;{ex.text}&rdquo;
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Chat messages */}
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in`}
                        >
                            <div style={{ maxWidth: "min(680px, 85%)" }}>
                                {msg.role === "orca" && (
                                    <p className="text-xs mb-2 ml-1 font-display font-semibold" style={{ color: "var(--text-muted)" }}>
                                        🐋 ORCA
                                    </p>
                                )}
                                <div
                                    className="px-5 py-4 text-sm leading-relaxed whitespace-pre-wrap"
                                    style={
                                        msg.role === "user"
                                            ? {
                                                background: "linear-gradient(135deg, rgba(99,102,241,0.18), rgba(139,92,246,0.12))",
                                                border: "1px solid rgba(99,102,241,0.25)",
                                                borderRadius: "18px 18px 4px 18px",
                                                color: "var(--text-primary)",
                                                fontSize: "0.95rem",
                                            }
                                            : msg.blocked
                                            ? {
                                                background: "rgba(239,68,68,0.08)",
                                                border: "1px solid rgba(239,68,68,0.3)",
                                                borderRadius: "18px 18px 18px 4px",
                                                color: "#fca5a5",
                                                fontSize: "0.95rem",
                                            }
                                            : {
                                                background: "var(--bg-elevated)",
                                                border: "1px solid var(--border)",
                                                borderRadius: "18px 18px 18px 4px",
                                                color: "var(--text-primary)",
                                                fontSize: "0.95rem",
                                            }
                                    }
                                >
                                    {msg.role === "user" ? msg.content : (
                                        <>
                                            {msg.blocked && (
                                                <span className="font-semibold text-red-400">🛡️ Blocked: </span>
                                            )}
                                            {msg.content}
                                        </>
                                    )}
                                </div>
                                {msg.role === "orca" && (msg.duration > 0 || msg.tokens > 0) && (
                                    <div className="flex gap-2 mt-2 ml-1">
                                        {msg.duration > 0 && <span className="metric-pill">{msg.duration}ms</span>}
                                        {msg.tokens > 0 && <span className="metric-pill">{msg.tokens} tokens</span>}
                                        {msg.blocked && <span className="metric-pill" style={{ color: "#f87171" }}>blocked</span>}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Thinking indicator */}
                    {loading && (
                        <div className="flex justify-start animate-in">
                            <div
                                className="px-5 py-4"
                                style={{
                                    background: "var(--bg-elevated)",
                                    border: "1px solid var(--border)",
                                    borderRadius: "18px 18px 18px 4px",
                                }}
                            >
                                <div className="flex gap-2 items-center" style={{ height: "22px" }}>
                                    <div className="thinking-dot" style={{ background: activeMode.color }} />
                                    <div className="thinking-dot" style={{ background: activeMode.color, animationDelay: "0.2s" }} />
                                    <div className="thinking-dot" style={{ background: activeMode.color, animationDelay: "0.4s" }} />
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={bottomRef} />
                </div>
            </div>

            {/* ── Input Bar ─────────────────────────────────────── */}
            <div
                className="flex-shrink-0 px-6 sm:px-10 py-5"
                style={{
                    borderTop: "1px solid var(--border)",
                    background: "rgba(7,7,15,0.8)",
                    backdropFilter: "blur(12px)",
                }}
            >
                <div className="max-w-4xl mx-auto flex gap-4 items-end">
                    <textarea
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                sendMessage();
                            }
                        }}
                        placeholder={`Message ORCA in ${activeMode.label} mode…`}
                        disabled={loading}
                        rows={2}
                        className="flex-1 input-dark px-5 py-4 text-base resize-none"
                        style={{
                            minHeight: "60px",
                            maxHeight: "160px",
                            lineHeight: "1.5",
                            fontSize: "1rem",
                        }}
                    />
                    <button
                        onClick={() => sendMessage()}
                        disabled={loading || !input.trim()}
                        className="btn-primary px-8 py-4 text-base font-bold flex-shrink-0"
                        style={{ minWidth: "110px", height: "60px", fontSize: "1rem" }}
                    >
                        {loading ? "…" : "Send →"}
                    </button>
                </div>
                <p className="text-xs text-center mt-2" style={{ color: "var(--text-muted)" }}>
                    Enter to send · Shift+Enter for new line
                </p>
            </div>
        </div>
    );
}
