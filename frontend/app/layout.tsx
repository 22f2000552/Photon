import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "RFQ Copilot — AI procurement analyst",
  description: "Find, contact and compare building-material vendors in minutes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/90 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
            <Link href="/" className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-sm font-bold text-white">
                R
              </span>
              <div>
                <div className="text-sm font-semibold leading-tight">RFQ Copilot</div>
                <div className="text-[11px] leading-tight text-zinc-500">
                  AI procurement analyst for Indian contractors
                </div>
              </div>
            </Link>
            <nav className="flex items-center gap-4 text-sm text-zinc-600">
              <Link href="/" className="hover:text-zinc-900">
                Dashboard
              </Link>
              <Link href="/vendors" className="hover:text-zinc-900">
                Vendor pool
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-6">{children}</main>
      </body>
    </html>
  );
}
