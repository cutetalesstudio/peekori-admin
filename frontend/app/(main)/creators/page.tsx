"use client";

import { useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

type Creator = {
  id: string;
  name: string;
  email?: string;
  country?: string;
  instagram_handle?: string;
  youtube_channel?: string;
  ref_code?: string;
  coupon_code?: string;
  approval_status?: string;
  approval_notes?: string;
  active?: boolean;
};

export default function CreatorsAdminPage() {
  const [creators, setCreators] = useState<Creator[]>([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");

  const authHeaders = (): Record<string, string> => {
    const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "";
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchCreators = async () => {
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/creators`, { headers: authHeaders(), cache: "no-store" });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      setCreators(Array.isArray(body.items) ? body.items : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load creators");
    }
  };

  useEffect(() => {
    void fetchCreators();
  }, []);

  const handleDecision = async (creator: Creator, action: "approve" | "reject") => {
    const notes = window.prompt(`${action === "approve" ? "Approval" : "Rejection"} notes`, creator.approval_notes || "") || "";
    setBusyId(creator.id);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/creators/${creator.id}/${action}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders(),
        },
        body: JSON.stringify({ notes }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      await fetchCreators();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} creator`);
    } finally {
      setBusyId("");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Creators</h1>
          <p className="text-sm text-slate-600">Review self-signups, approve creators, and inspect payout readiness.</p>
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="px-4 py-3 font-medium">Creator</th>
                <th className="px-4 py-3 font-medium">Country</th>
                <th className="px-4 py-3 font-medium">Channels</th>
                <th className="px-4 py-3 font-medium">Referral</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {creators.map((creator) => (
                <tr key={creator.id} className="border-b border-slate-100 align-top">
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">{creator.name}</div>
                    <div className="text-xs text-slate-500">{creator.email || "-"}</div>
                  </td>
                  <td className="px-4 py-3">{creator.country || "-"}</td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    <div>IG: {creator.instagram_handle || "-"}</div>
                    <div>YT: {creator.youtube_channel || "-"}</div>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    <div>Ref: {creator.ref_code || "-"}</div>
                    <div>Coupon: {creator.coupon_code || "-"}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                      creator.approval_status === "active"
                        ? "bg-green-100 text-green-800"
                        : creator.approval_status === "rejected"
                          ? "bg-red-100 text-red-800"
                          : "bg-amber-100 text-amber-800"
                    }`}>
                      {creator.approval_status || "pending_admin_approval"}
                    </span>
                    {creator.approval_notes ? <div className="mt-2 text-xs text-slate-500">{creator.approval_notes}</div> : null}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => void handleDecision(creator, "approve")}
                        disabled={busyId === creator.id}
                        className="rounded-lg bg-slate-900 px-3 py-2 text-xs text-white hover:bg-slate-700 disabled:opacity-60"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => void handleDecision(creator, "reject")}
                        disabled={busyId === creator.id}
                        className="rounded-lg border border-red-300 px-3 py-2 text-xs text-red-700 hover:bg-red-50 disabled:opacity-60"
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
