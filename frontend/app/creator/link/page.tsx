"use client";

import { useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_creator_token";

export default function CreatorLinkPage() {
  const [data, setData] = useState<any>(null);
  const [copied, setCopied] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    fetch(`${API_BASE}/api/creator/link`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      cache: "no-store",
    })
      .then(async (res) => {
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
        setData(body);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load link"));
  }, []);

  const copy = async (value: string, label: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(label);
      setTimeout(() => setCopied(""), 1500);
    } catch {
      setCopied("");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">My Link</h1>
        <p className="text-sm text-slate-600">Use this tracked link and code in your promotions.</p>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="space-y-4">
          <div>
            <div className="mb-1 text-sm font-medium text-slate-700">Primary Link</div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm break-all">{data?.primary_link || "-"}</div>
            <button onClick={() => void copy(data?.primary_link || "", "link")} className="mt-2 rounded-lg bg-slate-900 px-3 py-2 text-sm text-white">
              Copy Link
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <div className="mb-1 text-sm font-medium text-slate-700">Ref Code</div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">{data?.ref_code || "-"}</div>
            </div>
            <div>
              <div className="mb-1 text-sm font-medium text-slate-700">Coupon Code</div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">{data?.coupon_code || "-"}</div>
            </div>
          </div>
          {copied ? <p className="text-sm text-green-600">Copied {copied}.</p> : null}
        </div>
      </div>
    </div>
  );
}
