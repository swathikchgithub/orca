import type { Metadata } from "next";
import { Syne, DM_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-display",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "🐋 ORCA Dashboard",
  description: "Orchestrated Reasoning & Conversational Agent",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${syne.variable} ${dmSans.variable} ${jetbrainsMono.variable}`}>
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          {/* pt-14 = mobile top bar height; pb-20 = mobile bottom tab bar height */}
          <main className="flex-1 flex flex-col overflow-auto pt-14 lg:pt-0 pb-20 lg:pb-0 min-w-0">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
