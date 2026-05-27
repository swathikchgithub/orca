"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api";

const NAV = [
  { href: "/",             label: "Dashboard",    emoji: "🏠" },
  { href: "/chat",         label: "Chat",         emoji: "💬" },
  { href: "/evaluate",     label: "Evaluate",     emoji: "⚖️"  },
  { href: "/release",      label: "Release Gate", emoji: "🚀" },
  { href: "/architecture", label: "Architecture", emoji: "🏗️"  },
];

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

  const statusColor =
    isOnline === null ? "var(--yellow)" : isOnline ? "var(--green)" : "var(--red)";
  const statusLabel =
    isOnline === null ? "Checking…" : isOnline ? "Online" : "Offline";

  return (
    <header
      className="sticky top-0 z-40 w-full"
      style={{
        background: "rgba(7,7,15,0.9)",
        borderBottom: "1px solid var(--border)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
      }}
    >
      <div className="max-w-6xl mx-auto px-6 sm:px-10 h-16 flex items-center justify-between gap-4">

        {/* ── Logo ── */}
        <Link href="/" className="flex items-center gap-2.5 flex-shrink-0">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0"
            style={{
              background: "linear-gradient(135deg, var(--accent), var(--purple))",
              boxShadow: "0 0 18px rgba(99,102,241,0.45)",
            }}
          >
            🐋
          </div>
          <span className="text-base font-black font-display gradient-text hidden sm:inline">
            ORCA
          </span>
        </Link>

        {/* ── Nav — centered ── */}
        <nav className="flex items-center gap-1">
          {NAV.map(({ href, label, emoji }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-2 rounded-xl font-semibold font-display transition-all duration-200"
                style={{
                  padding: "8px 14px",
                  background: active ? "rgba(99,102,241,0.18)" : "transparent",
                  border: active ? "1px solid rgba(99,102,241,0.4)" : "1px solid transparent",
                  color: active ? "var(--text-primary)" : "var(--text-muted)",
                  boxShadow: active ? "0 0 14px rgba(99,102,241,0.22)" : "none",
                  fontSize: "0.875rem",
                  whiteSpace: "nowrap",
                }}
              >
                <span style={{ fontSize: "1.1rem", lineHeight: 1 }}>{emoji}</span>
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* ── Status ── */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{
              background: statusColor,
              boxShadow: `0 0 8px ${statusColor}`,
            }}
          />
          <span
            className="text-xs font-mono hidden sm:inline"
            style={{ color: "var(--text-muted)" }}
          >
            {statusLabel}
          </span>
        </div>

      </div>
    </header>
  );
}
