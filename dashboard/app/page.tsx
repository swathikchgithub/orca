"use client";

import { useEffect, useState } from "react";
import { healthCheck, HealthResponse } from "@/lib/api";
import Link from "next/link";

const METRICS = (health: HealthResponse | null, loading: boolean, error: boolean) => {
  const online = !loading && !error;
  return [
    {
      label: "API Status",
      value: loading ? "—" : error ? "Offline" : "Online",
      sub: `Uptime ${health ? Math.floor(health.uptime_secs) : 0}s`,
      icon: online ? "🟢" : "🔴",
      accent: online ? "#10b981" : "#ef4444",
      topBorder: online ? "#10b981" : "#ef4444",
    },
    {
      label: "Agent Model",
      value: health?.agent_model || "—",
      sub: "Single · Multi · Agentic",
      icon: "🤖",
      accent: "#6366f1",
      topBorder: "#6366f1",
    },
    {
      label: "Judge Model",
      value: health?.judge_model || "—",
      sub: "4-dim quality scoring",
      icon: "⚖️",
      accent: "#a855f7",
      topBorder: "#a855f7",
    },
    {
      label: "Test Suite",
      value: "44 / 44",
      sub: "All passing · 0.03s",
      icon: "✅",
      accent: "#10b981",
      topBorder: "#10b981",
    },
  ];
};

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
    border: "rgba(99,102,241,0.25)",
    hoverBorder: "rgba(99,102,241,0.55)",
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
    border: "rgba(168,85,247,0.25)",
    hoverBorder: "rgba(168,85,247,0.55)",
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
    border: "rgba(16,185,129,0.25)",
    hoverBorder: "rgba(16,185,129,0.55)",
    tagBg: "rgba(16,185,129,0.12)",
    tagColor: "#34d399",
  },
];

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error,  setError]  = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    healthCheck().then(setHealth).catch(() => setError(true)).finally(() => setLoading(false));
  }, []);

  const online = !loading && !error;
  const metrics = METRICS(health, loading, error);

  return (
    <div
      className="min-h-screen p-4 sm:p-6 lg:p-8 noise header-grid"
      style={{ background: "radial-gradient(ellipse at top, #110926 0%, var(--bg-base) 55%)" }}
    >
      <div className="max-w-6xl mx-auto relative z-10 page-enter">

        {/* ── Hero ─────────────────────────────────────────── */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-5">
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
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: online ? "#10b981" : "#ef4444", boxShadow: `0 0 6px ${online ? "#10b981" : "#ef4444"}` }}
              />
              {online ? "System Online" : "System Offline"}
            </span>
            <span
              className="text-xs px-3 py-1.5 rounded-full font-mono"
              style={{ border: "1px solid var(--border)", color: "var(--text-muted)" }}
            >
              v{health?.version || "1.0.0"}
            </span>
          </div>

          <h1
            className="font-black tracking-tight font-display mb-2 leading-none"
            style={{ fontSize: "clamp(2.4rem, 7vw, 5rem)", color: "var(--text-primary)" }}
          >
            🐋 <span className="gradient-text">ORCA</span>
          </h1>
          <p
            className="font-bold font-display mb-3"
            style={{ fontSize: "clamp(1rem, 3vw, 1.5rem)", color: "var(--text-secondary)" }}
          >
            AI Agent Platform
          </p>
          <p className="text-sm sm:text-base max-w-lg" style={{ color: "var(--text-muted)", lineHeight: 1.6 }}>
            Build, test, evaluate and ship AI agents with confidence.
          </p>
        </div>

        {/* ── Actions ──────────────────────────────────────── */}
        <div className="mb-10">
          <p className="section-label mb-4">Start here</p>

          {/* Mobile: stacked big tiles */}
          <div className="flex flex-col gap-4 md:hidden">
            {ACTIONS.map(a => (
              <Link key={a.href} href={a.href}>
                <div
                  className="rounded-2xl overflow-hidden group transition-all duration-200 active:scale-[0.98]"
                  style={{
                    background: `linear-gradient(135deg, ${a.accent}18 0%, ${a.accent}08 100%)`,
                    border: `1px solid ${a.accent}44`,
                    borderLeft: `4px solid ${a.accent}`,
                  }}
                >
                  {/* Top color bar */}
                  <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, ${a.accent}, ${a.accent}44)` }} />

                  <div className="flex items-center gap-5 p-5">
                    {/* Big icon */}
                    <div
                      className="w-20 h-20 rounded-2xl flex items-center justify-center text-4xl flex-shrink-0"
                      style={{
                        background: `${a.accent}22`,
                        border: `2px solid ${a.accent}55`,
                        boxShadow: `0 0 24px ${a.accent}33`,
                      }}
                    >
                      {a.icon}
                    </div>

                    {/* Text */}
                    <div className="flex-1 min-w-0">
                      <p className="section-label mb-1" style={{ color: a.accent }}>{a.subtitle}</p>
                      <h3
                        className="text-2xl font-black font-display mb-1 leading-tight"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {a.title}
                      </h3>
                      <div className="flex gap-1.5 flex-wrap mt-2">
                        {a.tags.map(tag => (
                          <span
                            key={tag}
                            className="text-xs px-2 py-0.5 rounded-full font-medium"
                            style={{ background: a.tagBg, color: a.tagColor }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Arrow */}
                    <span
                      className="text-2xl flex-shrink-0 transition-transform duration-200 group-hover:translate-x-1"
                      style={{ color: a.accent }}
                    >
                      →
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* Desktop: 3-column cards */}
          <div className="hidden md:grid md:grid-cols-3 gap-5">
            {ACTIONS.map(a => (
              <Link key={a.href} href={a.href} className="block">
                <div
                  className="card-hover rounded-2xl p-7 h-full group"
                  style={{
                    background: a.bg,
                    border: `1px solid ${a.border}`,
                    borderTop: `3px solid ${a.accent}`,
                    "--card-accent": `${a.accent}88`,
                    "--card-accent-glow": `${a.accent}20`,
                  } as React.CSSProperties}
                >
                  <div className="flex items-start justify-between mb-5">
                    <div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl"
                      style={{ background: `${a.accent}18`, border: `1px solid ${a.accent}44`, boxShadow: `0 0 20px ${a.accent}22` }}
                    >
                      {a.icon}
                    </div>
                    <span
                      className="text-xl transition-all duration-200 group-hover:translate-x-1"
                      style={{ color: "var(--text-muted)" }}
                    >
                      →
                    </span>
                  </div>
                  <p className="section-label mb-1" style={{ color: a.accent }}>{a.subtitle}</p>
                  <h3 className="text-2xl font-black mb-2 font-display" style={{ color: "var(--text-primary)" }}>
                    {a.title}
                  </h3>
                  <p className="text-sm leading-relaxed mb-5" style={{ color: "var(--text-secondary)" }}>
                    {a.desc}
                  </p>
                  <div className="flex gap-2 flex-wrap">
                    {a.tags.map(tag => (
                      <span
                        key={tag}
                        className="text-xs px-2.5 py-1 rounded-full font-medium"
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
        </div>

        {/* ── Metrics ──────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {metrics.map(m => (
            <div
              key={m.label}
              className="card-hover rounded-2xl p-4 sm:p-5"
              style={{
                background: "var(--bg-card)",
                border: `1px solid ${m.accent}22`,
                borderTop: `3px solid ${m.topBorder}`,
                "--card-accent": `${m.accent}55`,
                "--card-accent-glow": `${m.accent}18`,
              } as React.CSSProperties}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="section-label">{m.label}</span>
                <span className="text-2xl">{m.icon}</span>
              </div>
              <p
                className="stat-value mb-1 truncate"
                style={{ fontSize: "clamp(1.1rem, 3vw, 1.4rem)", color: m.accent }}
              >
                {m.value}
              </p>
              <p className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{m.sub}</p>
            </div>
          ))}
        </div>

        {/* ── Architecture ─────────────────────────────────── */}
        <Link href="/architecture">
          <div
            className="card-hover rounded-2xl p-6 group"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderLeft: "3px solid var(--accent)",
              "--card-accent": "rgba(99,102,241,0.5)",
              "--card-accent-glow": "rgba(99,102,241,0.15)",
            } as React.CSSProperties}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-5">
                <div
                  className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl flex-shrink-0"
                  style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.25)" }}
                >
                  🏗️
                </div>
                <div>
                  <p className="section-label mb-1" style={{ color: "var(--accent)" }}>Live Visualization</p>
                  <h3 className="text-lg font-black font-display" style={{ color: "var(--text-primary)" }}>
                    System Architecture
                  </h3>
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    Watch ORCA process requests in real time — 4 animated scenarios, 9 pipeline steps
                  </p>
                </div>
              </div>
              <span
                className="text-2xl transition-all duration-200 flex-shrink-0 group-hover:translate-x-1"
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
