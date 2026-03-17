"use client";

import { useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

type CommissionRow = {
  order_id: string;
  name: string;
  processed_at?: string;
  currency: string;
  revenue: number;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  ref_code: string;
  landing_page_slug: string;
  creator_name: string;
  campaign_name: string;
  commission_amount: number;
  commission_rule: string;
};

export default function CommissionReportPage() {
  const today = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 29 * 86400000).toISOString().slice(0, 10);
  const [startDate, setStartDate] = useState(monthAgo);
  const [endDate, setEndDate] = useState(today);
  const [rows, setRows] = useState<CommissionRow[]>([]);
  const [summary, setSummary] = useState({ orders: 0, revenue: 0, commission: 0 });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    setError("");
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
      const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
      const res = await fetch(`${API_BASE}/api/admin/commissions/report?${params.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        cache: "no-store",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setRows(Array.isArray(data.items) ? data.items : []);
      setSummary(data.summary || { orders: 0, revenue: 0, commission: 0 });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchReport();
  }, []);

  const syncLedger = async () => {
    setSyncing(true);
    setError("");
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
      const res = await fetch(`${API_BASE}/api/admin/commissions/sync`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ start_date: startDate, end_date: endDate, limit: 500 }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      await fetchReport();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync ledger");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Commissions Report</h1>
          <p className="text-sm text-slate-600">Read-only derived commission calculation from creators, campaigns, and attributed orders.</p>
        </div>

        <div className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">Start Date</span>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-700">End Date</span>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <button onClick={() => void fetchReport()} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
            Refresh
          </button>
          <button onClick={() => void syncLedger()} disabled={syncing} className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-60">
            {syncing ? "Syncing..." : "Sync Ledger"}
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-sm text-slate-500">Orders</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">{summary.orders}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-sm text-slate-500">Revenue</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">{summary.revenue.toFixed(2)}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-sm text-slate-500">Commission</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">{summary.commission.toFixed(2)}</div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          {error ? <p className="mb-4 text-sm text-red-600">{error}</p> : null}
          {loading ? (
            <p className="text-sm text-slate-500">Loading...</p>
          ) : rows.length === 0 ? (
            <p className="text-sm text-slate-500">No attributed paid orders found for this range.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="px-3 py-2 font-medium">Order</th>
                    <th className="px-3 py-2 font-medium">Creator</th>
                    <th className="px-3 py-2 font-medium">Campaign</th>
                    <th className="px-3 py-2 font-medium">Revenue</th>
                    <th className="px-3 py-2 font-medium">Commission</th>
                    <th className="px-3 py-2 font-medium">Attribution</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={`${row.order_id}-${row.commission_rule}`} className="border-b border-slate-100 align-top">
                      <td className="px-3 py-3 text-slate-700">
                        <div className="font-medium">{row.order_id}</div>
                        <div className="text-xs text-slate-500">{row.name}</div>
                      </td>
                      <td className="px-3 py-3 text-slate-700">{row.creator_name || "-"}</td>
                      <td className="px-3 py-3 text-slate-700">{row.campaign_name || "-"}</td>
                      <td className="px-3 py-3 text-slate-700">{row.currency} {row.revenue.toFixed(2)}</td>
                      <td className="px-3 py-3 text-slate-700">
                        <div>{row.currency} {row.commission_amount.toFixed(2)}</div>
                        <div className="text-xs text-slate-500">{row.commission_rule || "-"}</div>
                      </td>
                      <td className="px-3 py-3 text-xs text-slate-600">
                        <div>src: {row.utm_source || "-"}</div>
                        <div>med: {row.utm_medium || "-"}</div>
                        <div>cmp: {row.utm_campaign || "-"}</div>
                        <div>ref: {row.ref_code || "-"}</div>
                        <div>lp: {row.landing_page_slug || "-"}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
