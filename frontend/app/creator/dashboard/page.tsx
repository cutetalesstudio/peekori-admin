"use client";

import { useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_creator_token";

export default function CreatorDashboardPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    fetch(`${API_BASE}/api/creator/dashboard`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      cache: "no-store",
    })
      .then(async (res) => {
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
        setData(body);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-600">Your current attributed orders and commission status.</p>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Orders" value={String(data?.summary?.orders ?? 0)} />
        <MetricCard label="Available" value={Number(data?.summary?.available_to_withdraw ?? 0).toFixed(2)} />
        <MetricCard label="Pending" value={Number(data?.summary?.pending_commission ?? 0).toFixed(2)} />
        <MetricCard label="Paid" value={Number(data?.summary?.paid_commission ?? 0).toFixed(2)} />
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid gap-4 md:grid-cols-2">
          <Detail label="Requested amount" value={Number(data?.summary?.requested_amount ?? 0).toFixed(2)} />
          <Detail label="Last payout" value={data?.summary?.last_payout_at ? new Date(data.summary.last_payout_at).toLocaleString() : "-"} />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-medium text-slate-900">{value}</div>
    </div>
  );
}
