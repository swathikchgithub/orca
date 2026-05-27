"use client";

import { useEffect, useState } from "react";
import { healthCheck, HealthResponse } from "@/lib/api";
import Link from "next/link";

const ACTIONS = [
  {
    href: "/chat",
    icon: "💬",
    title: "Chat",
    subtitle: "Live Agent Testing",
    desc: "Talk to ORCA across all 3 modes — single turn, multi-turn memory, and agentic tool use.",
    tags: ["Single Turn", "Multi Turn", "Agentic"],
    accent: "#6366f1",
    bg: "rgba(99,102,241,0.07)",
    border: "rgba(99,102,241,0.22)",
    tagBg: "rgba(99,102,241,0.12)",
    tagColor: "#818cf8",
  },
  {
    href: "/evaluate",
    icon: "⚖️",
    title: "Evaluate",
    subtitle: "Response Scoring",
    desc: "Score any ORCA response with GPT-4o as judge — accuracy, helpfulness, safety, clarity.",
    tags: ["Accuracy", "Safety", "Clarity"],
    accent: "#a855f7",
    bg: "rgba(168,85,247,0.07)",
    border: "rgba(168,85,247,0.22)",
    tagBg: "rgba(168,85,247,0.12)",
    tagColor: "#c084fc",
  },
  {
    href: "/release",
    icon: "🚀",
    title: "Release Gate",
    subtitle: "Production Readiness",
    desc: "Run 5 automated quality gates — judge score, safety, latency, regression, min samples.",
    tags: ["5 Gates", "Safety", "Latency"],
    accent: "#10b981",
    bg: "rgba(16,185,129,0.07)",
    border: "rgba(16,185,129,0.22)",
    tagBg: "rgba(16,185,129,0.12)",
    tagColor: "#34d399",
  },
];

export default function HomePage() {
  const [health,  setHealth]  = useState<HealthResponse | null>(null);
  const [error,   setError]   = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    healthCheck()
      .then(setHealth)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const online = !loading && !error;

  const metrics = [
    {
      label: "API Status",
      value: loading ? "—" : error ? "Offline" : "Online",
      sub: `Uptime ${health ? Math.floor(health.uptime_secs) : 0}s`,
      icon: online ? "🟢" : "🔴",
      accent: online ? "#10b981" : "#ef4444",
    },
    {
      label: "Agent Model",
      value: health?.agent_model ?? "—",
      sub: "Single · Multi · Agentic",
      icon: "🤖",
      accent: "#6366f1",
    },
    {
      label: "Judge Model",
      value: health?.judge_model ?? "—",
      sub: "4-dim quality scoring",
      icon: "⚖️",
      accent: "#a855f7",
    },
    {
      label: "Test Suite",
      value: "150 / 150",
      sub: "All passing · 0.46s",
      icon: "✅",
      accent: "#10b981",
    },
  ];

  return (
    <div
      className="flex-1 header-grid noise"
      style={{
        background:
          "radial-gradient(ellipse 80% 50% at 50% -10%, #180d3a 0%, var(--bg-base) 60%)",
      }}
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-16 page-enter">

        {/* ── Hero ─────────────────────────────────────────── */}
        <div className="text-center mb-12">

          {/* Status badge */}
          <div className="flex items-center justify-center gap-3 mb-6">
            <span
              className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-full font-semibold font-display"
              style={online ? {
                background: "rgba(16,185,129,0.1)",
                border: "1px solid rgba(16,185,129,0.35)",
                color: "#34d399",
              } : {
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.35)",
                color: "#f87171",
              }}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${online ? "status-online" : "status-error"}`}
                style={{ background: online ? "#10b981" : "#ef4444" }}
              />
              {online ? "System Online" : "System Offline"}
            </span>
            <span
              className="text-xs px-3 py-1.5 rounded-full font-mono"
              style={{ border: "1px solid var(--border)", color: "var(--text-muted)" }}
            >
              v{health?.version ?? "1.0.0"}
            </span>
          </div>

          {/* Title */}
          <h1
            className="font-black tracking-tight font-display leading-none mb-4"
            style={{ fontSize: "clamp(3rem, 9vw, 6rem)" }}
          >
            🐋 <span className="gradient-text">ORCA</span>
          </h1>
          <p
            className="font-bold font-display mb-3"
            style={{
              fontSize: "clamp(1.1rem, 3vw, 1.6rem)",
              color: "var(--text-secondary)",
            }}
          >
            AI Agent Platform
          </p>
          <p
            className="text-sm sm:text-base max-w-md mx-auto"
            style={{ color: "var(--text-muted)", lineHeight: 1.65 }}
          >
            Build, test, evaluate, and ship AI agents with confidence.
          </p>
        </div>

        {/* ── Action Cards ─────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          {ACTIONS.map(a => (
            <Link key={a.href} href={a.href} className="block group">
              <div
                className="card-hover rounded-2xl p-6 h-full"
                style={{
                  background: a.bg,
                  border: `1px solid ${a.border}`,
                  borderTop: `3px solid ${a.accent}`,
                  "--card-accent": `${a.accent}88`,
                  "--card-accent-glow": `${a.accent}20`,
                } as React.CSSProperties}
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl"
                    style={{
                      background: `${a.accent}18`,
                      border: `1px solid ${a.accent}44`,
                      boxShadow: `0 0 18px ${a.accent}22`,
                    }}
                  >
                    {a.icon}
                  </div>
                  <span
                    className="text-lg transition-all duration-200 group-hover:translate-x-1"
                    style={{ color: "var(--text-muted)" }}
                  >
                    →
                  </span>
                </div>
                <p className="section-label mb-1" style={{ color: a.accent }}>{a.subtitle}</p>
                <h3 className="text-xl font-black mb-2 font-display" style={{ color: "var(--text-primary)" }}>
                  {a.title}
                </h3>
                <p className="text-xs leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
                  {a.desc}
                </p>
                <div className="flex gap-1.5 flex-wrap">
                  {a.tags.map(tag => (
                    <span
                      key={tag}
                      className="text-xs px-2.5 py-0.5 rounded-full font-medium"
                      style={{ background: a.tagBg, color: a.tagColor }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* ── Metrics ──────────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {metrics.map(m => (
            <div
              key={m.label}
              className="rounded-2xl p-4"
              style={{
                background: "var(--bg-card)",
                border: `1px solid ${m.accent}22`,
                borderTop: `2px solid ${m.accent}`,
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="section-label">{m.label}</span>
                <span className="text-xl">{m.icon}</span>
              </div>
              <p
                className="font-black font-display truncate mb-0.5"
                style={{ fontSize: "clamp(0.9rem, 2.5vw, 1.1rem)", color: m.accent }}
              >
                {m.value}
              </p>
              <p className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{m.sub}</p>
            </div>
          ))}
        </div>

        {/* ── Architecture Link ─────────────────────────────── */}
        <Link href="/architecture">
          <div
            className="card-hover rounded-2xl p-5 group"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderLeft: "3px solid var(--accent)",
              "--card-accent": "rgba(99,102,241,0.5)",
              "--card-accent-glow": "rgba(99,102,241,0.15)",
            } as React.CSSProperties}
          >
            <div className="flex items-center gap-4">
              <div
                className="w-11 h-11 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
                style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.25)" }}
              >
                🏗️
              </div>
              <div className="flex-1 min-w-0">
                <p className="section-label mb-0.5" style={{ color: "var(--accent)" }}>Live Visualization</p>
                <h3 className="text-base font-black font-display" style={{ color: "var(--text-primary)" }}>
                  System Architecture
                </h3>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  Watch ORCA process requests in real time — 4 animated scenarios, 9 pipeline steps
                </p>
              </div>
              <span
                className="text-xl flex-shrink-0 transition-all duration-200 group-hover:translate-x-1"
                style={{ color: "var(--text-muted)" }}
              >
                →
              </span>
            </div>
          </div>
        </Link>

      </div>
    </div>
  );
}
