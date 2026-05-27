"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api";

const NAV = [
  { href: "/",             label: "Dashboard",    short: "Home",     emoji: "🏠" },
  { href: "/chat",         label: "Chat",         short: "Chat",     emoji: "💬" },
  { href: "/evaluate",     label: "Evaluate",     short: "Score",    emoji: "⚖️"  },
  { href: "/release",      label: "Release Gate", short: "Release",  emoji: "🚀" },
  { href: "/architecture", label: "Architecture", short: "Flow",     emoji: "🏗️"  },
];

function NavButton({
  href, label, emoji, active,
}: {
  href: string; label: string; emoji: string; active: boolean;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group"
      style={{
        background: active
          ? "linear-gradient(135deg, rgba(99,102,241,0.22), rgba(99,102,241,0.1))"
          : "rgba(255,255,255,0.04)",
        border: active
          ? "1px solid rgba(99,102,241,0.4)"
          : "1px solid rgba(255,255,255,0.07)",
        boxShadow: active ? "0 2px 20px rgba(99,102,241,0.18)" : "none",
      }}
      onMouseEnter={e => {
        if (!active) {
          (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.07)";
          (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.12)";
        }
      }}
      onMouseLeave={e => {
        if (!active) {
          (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
          (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.07)";
        }
      }}
    >
      {/* Icon box */}
      <span
        className="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
        style={{
          background: active ? "rgba(99,102,241,0.28)" : "rgba(255,255,255,0.06)",
          border: active ? "1px solid rgba(99,102,241,0.4)" : "1px solid rgba(255,255,255,0.08)",
        }}
      >
        {emoji}
      </span>

      {/* Label */}
      <span
        className="text-sm font-semibold font-display flex-1"
        style={{ color: active ? "var(--text-primary)" : "var(--text-secondary)" }}
      >
        {label}
      </span>

      {/* Active chevron */}
      {active && (
        <span
          className="flex-shrink-0 text-sm font-bold"
          style={{ color: "var(--accent)" }}
        >
          ›
        </span>
      )}
    </Link>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const check = () =>
      healthCheck().then(() => setIsOnline(true)).catch(() => setIsOnline(false));
    check();
    const id = setInterval(check, 30_000);
    return () => clearInterval(id);
  }, []);

  const statusColor = isOnline === null ? "var(--yellow)" : isOnline ? "var(--green)" : "var(--red)";
  const statusLabel = isOnline === null ? "Checking…" : isOnline ? "Online" : "Offline";

  return (
    <>
      {/* ════ DESKTOP SIDEBAR (lg+) ══════════════════════════ */}
      <aside
        className="hidden lg:flex w-64 flex-col flex-shrink-0 sticky top-0"
        style={{
          background: "linear-gradient(180deg, #0b0b18 0%, var(--bg-base) 100%)",
          borderRight: "1px solid var(--border)",
          height: "100vh",
          overflowY: "auto",
        }}
      >
        {/* Brand */}
        <div className="px-4 py-5" style={{ borderBottom: "1px solid var(--border)" }}>
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
              style={{
                background: "linear-gradient(135deg, var(--accent), var(--purple))",
                boxShadow: "0 0 20px rgba(99,102,241,0.4)",
              }}
            >
              🐋
            </div>
            <div className="flex flex-col">
              <span className="text-base font-black tracking-tight font-display gradient-text leading-none">
                ORCA
              </span>
              <span className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                AI Agent Platform
              </span>
            </div>
            <span
              className="ml-auto text-xs font-mono px-2 py-0.5 rounded-md flex-shrink-0"
              style={{
                background: "rgba(99,102,241,0.1)",
                border: "1px solid rgba(99,102,241,0.25)",
                color: "var(--accent)",
              }}
            >
              v1.0
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4">
          <p className="section-label px-1 mb-3">Navigation</p>
          <div className="flex flex-col gap-1.5">
            {NAV.map(({ href, label, emoji }) => (
              <NavButton key={href} href={href} label={label} emoji={emoji} active={pathname === href} />
            ))}
          </div>
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 flex items-center gap-2" style={{ borderTop: "1px solid var(--border)" }}>
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ background: statusColor, boxShadow: `0 0 8px ${statusColor}` }}
          />
          <span className="text-xs flex-1" style={{ color: "var(--text-muted)" }}>
            Agent {statusLabel}
          </span>
          <span
            className="text-xs font-mono px-2 py-0.5 rounded"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid var(--border)",
              color: "var(--text-muted)",
            }}
          >
            M1
          </span>
        </div>
      </aside>

      {/* ════ MOBILE TOP NAV BAR (< lg) ══════════════════════ */}
      <div
        className="lg:hidden fixed top-0 left-0 right-0 z-40"
        style={{
          background: "rgba(7,7,15,0.96)",
          borderBottom: "1px solid var(--border)",
          backdropFilter: "blur(16px)",
        }}
      >
        <div className="flex items-center gap-2 px-3 py-2">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 flex-shrink-0 mr-1">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
              style={{
                background: "linear-gradient(135deg, var(--accent), var(--purple))",
                boxShadow: "0 0 10px rgba(99,102,241,0.4)",
              }}
            >
              🐋
            </div>
            <span className="text-sm font-black font-display gradient-text hidden xs:inline">ORCA</span>
          </Link>

          {/* Divider */}
          <div className="w-px h-5 flex-shrink-0" style={{ background: "var(--border)" }} />

          {/* Nav icon buttons */}
          <div className="flex items-center gap-1.5 flex-1">
            {NAV.map(({ href, emoji, short }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className="flex flex-col items-center justify-center gap-0.5 rounded-xl transition-all duration-200 flex-1"
                  style={{
                    padding: "5px 4px",
                    background: active ? "rgba(99,102,241,0.18)" : "rgba(255,255,255,0.04)",
                    border: active ? "1px solid rgba(99,102,241,0.4)" : "1px solid rgba(255,255,255,0.07)",
                    boxShadow: active ? "0 0 12px rgba(99,102,241,0.25)" : "none",
                    minWidth: 0,
                  }}
                >
                  <span
                    className="text-lg leading-none"
                    style={active ? { filter: "drop-shadow(0 0 4px rgba(99,102,241,0.8))" } : {}}
                  >
                    {emoji}
                  </span>
                  <span
                    style={{
                      fontSize: "9px",
                      fontWeight: 700,
                      fontFamily: "var(--font-display)",
                      color: active ? "var(--accent)" : "var(--text-muted)",
                      lineHeight: 1,
                    }}
                  >
                    {short}
                  </span>
                </Link>
              );
            })}
          </div>

          {/* Status dot */}
          <div
            className="w-2 h-2 rounded-full flex-shrink-0 ml-1"
            style={{ background: statusColor, boxShadow: `0 0 6px ${statusColor}` }}
          />
        </div>
      </div>

      {/* ════ MOBILE BOTTOM TAB BAR (< lg) ══════════════════ */}
      <nav
        className="lg:hidden fixed bottom-0 left-0 right-0 z-40 flex"
        style={{
          background: "rgba(7,7,15,0.96)",
          borderTop: "1px solid var(--border)",
          backdropFilter: "blur(16px)",
          paddingBottom: "env(safe-area-inset-bottom, 0px)",
        }}
      >
        {NAV.map(({ href, short, emoji }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className="flex-1 flex flex-col items-center py-2.5 gap-0.5 transition-all duration-150 relative"
              style={{ color: active ? "var(--accent)" : "var(--text-muted)" }}
            >
              {active && (
                <span
                  className="absolute top-0 left-1/2 -translate-x-1/2 w-8 rounded-full"
                  style={{ height: "2px", background: "var(--accent)", boxShadow: "0 0 8px var(--accent)" }}
                />
              )}
              <span
                className="text-xl leading-none"
                style={active ? { filter: "drop-shadow(0 0 6px rgba(99,102,241,0.9))" } : {}}
              >
                {emoji}
              </span>
              <span
                className="font-semibold font-display"
                style={{ fontSize: "10px", color: active ? "var(--accent)" : "var(--text-muted)" }}
              >
                {short}
              </span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
