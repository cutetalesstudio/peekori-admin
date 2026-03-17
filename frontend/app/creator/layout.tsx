"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_creator_token";

const navItems = [
  { href: "/creator/dashboard", label: "Dashboard" },
  { href: "/creator/link", label: "My Link" },
  { href: "/creator/orders", label: "Orders" },
  { href: "/creator/payouts", label: "Payouts" },
  { href: "/creator/settings", label: "Settings" },
];

export default function CreatorLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isAuthPage = pathname === "/creator/login" || pathname === "/creator/signup";
  const [ready, setReady] = useState(isAuthPage);

  useEffect(() => {
    if (isAuthPage) return;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      router.replace("/creator/login");
      return;
    }
    fetch(`${API_BASE}/api/creator/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
      .then((res) => {
        if (!res.ok) {
          localStorage.removeItem(TOKEN_KEY);
          router.replace("/creator/login");
          return;
        }
        setReady(true);
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        router.replace("/creator/login");
      });
  }, [isAuthPage, router]);

  if (isAuthPage) {
    return <>{children}</>;
  }

  if (!ready) {
    return <div className="min-h-screen bg-slate-50 p-8 text-sm text-slate-500">Loading creator portal...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-7xl gap-6 p-6">
        <aside className="w-56 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Peekori</div>
            <div className="text-lg font-semibold text-slate-900">Creator Portal</div>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-lg px-3 py-2 text-sm ${
                  pathname === item.href ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <button
            onClick={() => {
              localStorage.removeItem(TOKEN_KEY);
              router.replace("/creator/login");
            }}
            className="mt-6 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            Sign out
          </button>
        </aside>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
