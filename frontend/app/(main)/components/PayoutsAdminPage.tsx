"use client";

import { useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

type WithdrawalRequest = {
  id: string;
  creator_id: string;
  creator_name: string;
  amount: number;
  currency: string;
  status: string;
  notes?: string;
  created_at?: string;
};

type Payout = {
  id: string;
  creator_name: string;
  amount: number;
  currency: string;
  payout_reference?: string;
  status: string;
  created_at?: string;
};

export default function PayoutsAdminPage() {
  const [requests, setRequests] = useState<WithdrawalRequest[]>([]);
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");

  const getToken = () => (typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "");

  const fetchAll = async () => {
    setError("");
    try {
      const token = getToken();
      const [requestsRes, payoutsRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/withdrawal-requests`, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" }),
        fetch(`${API_BASE}/api/admin/payouts`, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" }),
      ]);
      const requestsBody = await requestsRes.json().catch(() => ({}));
      const payoutsBody = await payoutsRes.json().catch(() => ({}));
      if (!requestsRes.ok) throw new Error(requestsBody.detail || `HTTP ${requestsRes.status}`);
      if (!payoutsRes.ok) throw new Error(payoutsBody.detail || `HTTP ${payoutsRes.status}`);
      setRequests(Array.isArray(requestsBody.items) ? requestsBody.items : []);
      setPayouts(Array.isArray(payoutsBody.items) ? payoutsBody.items : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load payouts");
    }
  };

  useEffect(() => {
    void fetchAll();
  }, []);

  const approveRequest = async (request: WithdrawalRequest) => {
    const payoutReference = window.prompt("Payout reference (optional)", "") || "";
    setBusyId(request.id);
    setError("");
    try {
      const token = getToken();
      const res = await fetch(`${API_BASE}/api/admin/withdrawal-requests/${request.id}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ payout_reference: payoutReference, notes: request.notes || "" }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      await fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve request");
    } finally {
      setBusyId("");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Payouts</h1>
          <p className="text-sm text-slate-600">Review creator withdrawal requests and completed payouts.</p>
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <div className="grid gap-6 xl:grid-cols-2">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-slate-900">Withdrawal Requests</h2>
              <button onClick={() => void fetchAll()} className="text-sm text-slate-500 hover:text-slate-900">Refresh</button>
            </div>
            <div className="space-y-3">
              {requests.length === 0 ? <p className="text-sm text-slate-500">No withdrawal requests.</p> : requests.map((request) => (
                <div key={request.id} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="font-medium text-slate-900">{request.creator_name}</div>
                      <div className="text-sm text-slate-500">{request.currency} {Number(request.amount || 0).toFixed(2)}</div>
                      <div className="mt-1 text-xs text-slate-500">{request.created_at ? new Date(request.created_at).toLocaleString() : "-"}</div>
                      {request.notes ? <div className="mt-2 text-sm text-slate-600">{request.notes}</div> : null}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <span className={`rounded-full px-2 py-1 text-xs font-medium ${request.status === "requested" ? "bg-amber-100 text-amber-800" : "bg-green-100 text-green-800"}`}>
                        {request.status}
                      </span>
                      {request.status === "requested" ? (
                        <button
                          onClick={() => void approveRequest(request)}
                          disabled={busyId === request.id}
                          className="rounded-lg bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-60"
                        >
                          {busyId === request.id ? "Processing..." : "Mark Paid"}
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-slate-900">Completed Payouts</h2>
              <button onClick={() => void fetchAll()} className="text-sm text-slate-500 hover:text-slate-900">Refresh</button>
            </div>
            <div className="space-y-3">
              {payouts.length === 0 ? <p className="text-sm text-slate-500">No payouts yet.</p> : payouts.map((payout) => (
                <div key={payout.id} className="rounded-xl border border-slate-200 p-4">
                  <div className="font-medium text-slate-900">{payout.creator_name}</div>
                  <div className="text-sm text-slate-500">{payout.currency} {Number(payout.amount || 0).toFixed(2)}</div>
                  <div className="mt-1 text-xs text-slate-500">{payout.created_at ? new Date(payout.created_at).toLocaleString() : "-"}</div>
                  <div className="mt-2 text-sm text-slate-600">Reference: {payout.payout_reference || "-"}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

