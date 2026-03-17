"use client";

import { useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_creator_token";

type Wallet = {
  pending_commission: number;
  paid_commission: number;
  requested_amount: number;
  available_to_withdraw: number;
};

type PayoutProfile = {
  preferred_method?: string;
  account_holder_name?: string;
  bank_name?: string;
  account_number?: string;
  ifsc_code?: string;
  upi_id?: string;
  paypal_email?: string;
  notes?: string;
};

export default function CreatorPayoutsPage() {
  const [wallet, setWallet] = useState<Wallet>({
    pending_commission: 0,
    paid_commission: 0,
    requested_amount: 0,
    available_to_withdraw: 0,
  });
  const [profile, setProfile] = useState<PayoutProfile>({});
  const [withdrawals, setWithdrawals] = useState<any[]>([]);
  const [payouts, setPayouts] = useState<any[]>([]);
  const [country, setCountry] = useState("");
  const [profileComplete, setProfileComplete] = useState(false);
  const [saving, setSaving] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const authHeaders = (): Record<string, string> => {
    const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) || "" : "";
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchAll = async () => {
    setError("");
    try {
      const [profileRes, withdrawalsRes, payoutsRes] = await Promise.all([
        fetch(`${API_BASE}/api/creator/payout-profile`, { headers: authHeaders(), cache: "no-store" }),
        fetch(`${API_BASE}/api/creator/withdrawals`, { headers: authHeaders(), cache: "no-store" }),
        fetch(`${API_BASE}/api/creator/payouts`, { headers: authHeaders(), cache: "no-store" }),
      ]);
      const profileBody = await profileRes.json().catch(() => ({}));
      const withdrawalsBody = await withdrawalsRes.json().catch(() => ({}));
      const payoutsBody = await payoutsRes.json().catch(() => ({}));
      if (!profileRes.ok) throw new Error(profileBody.detail || `HTTP ${profileRes.status}`);
      if (!withdrawalsRes.ok) throw new Error(withdrawalsBody.detail || `HTTP ${withdrawalsRes.status}`);
      if (!payoutsRes.ok) throw new Error(payoutsBody.detail || `HTTP ${payoutsRes.status}`);
      setProfile(profileBody.profile || {});
      setWallet(profileBody.wallet || {
        pending_commission: 0,
        paid_commission: 0,
        requested_amount: 0,
        available_to_withdraw: 0,
      });
      setCountry(String(profileBody.country || "").toUpperCase());
      setProfileComplete(Boolean(profileBody.profile_complete));
      setWithdrawals(Array.isArray(withdrawalsBody.items) ? withdrawalsBody.items : []);
      setPayouts(Array.isArray(payoutsBody.items) ? payoutsBody.items : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load payouts");
    }
  };

  useEffect(() => {
    void fetchAll();
  }, []);

  useEffect(() => {
    setProfile((prev) => {
      const method = prev.preferred_method || "";
      if (country === "IN") {
        if (method !== "upi" && method !== "bank") {
          return { ...prev, preferred_method: "upi" };
        }
        return prev;
      }
      if (method !== "paypal") {
        return { ...prev, preferred_method: "paypal" };
      }
      return prev;
    });
  }, [country]);

  const saveProfile = async () => {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API_BASE}/api/creator/payout-profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders(),
        },
        body: JSON.stringify(profile),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      setProfile(body.profile || {});
      setCountry(String(body.country || country).toUpperCase());
      setProfileComplete(Boolean(body.profile_complete));
      setSuccess("Payout details saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save payout details");
    } finally {
      setSaving(false);
    }
  };

  const requestWithdrawal = async () => {
    setRequesting(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API_BASE}/api/creator/withdrawals/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders(),
        },
        body: JSON.stringify({ notes: profile.notes || "" }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      setSuccess("Withdrawal request submitted.");
      await fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to request withdrawal");
    } finally {
      setRequesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Payouts</h1>
        <p className="text-sm text-slate-600">Manage your payout method and request withdrawal of your available balance.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Available" value={wallet.available_to_withdraw.toFixed(2)} />
        <MetricCard label="Pending" value={wallet.pending_commission.toFixed(2)} />
        <MetricCard label="Requested" value={wallet.requested_amount.toFixed(2)} />
        <MetricCard label="Paid" value={wallet.paid_commission.toFixed(2)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-lg font-medium text-slate-900">Payout Details</h2>
          <p className="mb-4 text-sm text-slate-600">
            {country === "IN"
              ? "Indian creators can withdraw through UPI or bank transfer."
              : "Non-India creators can withdraw through PayPal payout only."}
          </p>
          <div className="space-y-3">
            <Field label="Preferred Method">
              <select
                value={profile.preferred_method || ""}
                onChange={(e) => setProfile((prev) => ({ ...prev, preferred_method: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {country === "IN" ? (
                  <>
                    <option value="upi">UPI</option>
                    <option value="bank">Bank Transfer</option>
                  </>
                ) : (
                  <option value="paypal">PayPal</option>
                )}
              </select>
            </Field>
            <Field label="Account Holder Name">
              <input value={profile.account_holder_name || ""} onChange={(e) => setProfile((prev) => ({ ...prev, account_holder_name: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </Field>
            {country === "IN" && profile.preferred_method === "bank" ? (
              <>
                <Field label="Bank Name">
                  <input value={profile.bank_name || ""} onChange={(e) => setProfile((prev) => ({ ...prev, bank_name: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                </Field>
                <Field label="Account Number">
                  <input value={profile.account_number || ""} onChange={(e) => setProfile((prev) => ({ ...prev, account_number: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                </Field>
                <Field label="IFSC Code">
                  <input value={profile.ifsc_code || ""} onChange={(e) => setProfile((prev) => ({ ...prev, ifsc_code: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                </Field>
              </>
            ) : null}
            {country === "IN" && profile.preferred_method === "upi" ? (
              <Field label="UPI ID">
                <input value={profile.upi_id || ""} onChange={(e) => setProfile((prev) => ({ ...prev, upi_id: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </Field>
            ) : null}
            {country !== "IN" ? (
              <Field label="PayPal Email">
                <input type="email" value={profile.paypal_email || ""} onChange={(e) => setProfile((prev) => ({ ...prev, paypal_email: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </Field>
            ) : null}
            <Field label="Notes">
              <textarea value={profile.notes || ""} onChange={(e) => setProfile((prev) => ({ ...prev, notes: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" rows={3} />
            </Field>
          </div>
          <div className="mt-4 flex gap-3">
            <button onClick={() => void saveProfile()} disabled={saving} className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-60">
              {saving ? "Saving..." : "Save Details"}
            </button>
            <button
              onClick={() => void requestWithdrawal()}
              disabled={requesting || wallet.available_to_withdraw <= 0}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-800 hover:bg-slate-50 disabled:opacity-60"
            >
              {requesting ? "Requesting..." : `Withdraw ${wallet.available_to_withdraw.toFixed(2)}`}
            </button>
          </div>
          {wallet.available_to_withdraw > 0 && !profileComplete ? (
            <p className="mt-3 text-sm text-amber-700">Complete and save your payout profile before requesting withdrawal.</p>
          ) : null}
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
          {success ? <p className="mt-3 text-sm text-green-600">{success}</p> : null}
        </section>

        <section className="space-y-6">
          <Panel title="Withdrawal Requests">
            {withdrawals.length === 0 ? <EmptyText text="No withdrawal requests yet." /> : (
              <SimpleTable
                headers={["Date", "Amount", "Status", "Reference"]}
                rows={withdrawals.map((item) => [
                  item.created_at ? new Date(item.created_at).toLocaleString() : "-",
                  `${item.currency || ""} ${Number(item.amount || 0).toFixed(2)}`,
                  item.status || "-",
                  item.payout_id || "-",
                ])}
              />
            )}
          </Panel>
          <Panel title="Paid Payouts">
            {payouts.length === 0 ? <EmptyText text="No payouts yet." /> : (
              <SimpleTable
                headers={["Date", "Amount", "Reference", "Status"]}
                rows={payouts.map((item) => [
                  item.created_at ? new Date(item.created_at).toLocaleString() : "-",
                  `${item.currency || ""} ${Number(item.amount || 0).toFixed(2)}`,
                  item.payout_reference || "-",
                  item.status || "-",
                ])}
              />
            )}
          </Panel>
        </section>
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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="mb-1 text-sm font-medium text-slate-700">{label}</div>
      {children}
    </label>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-medium text-slate-900">{title}</h2>
      {children}
    </div>
  );
}

function EmptyText({ text }: { text: string }) {
  return <p className="text-sm text-slate-500">{text}</p>;
}

function SimpleTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-slate-500">
            {headers.map((header) => (
              <th key={header} className="px-3 py-2 font-medium">{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx} className="border-b border-slate-100">
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="px-3 py-3">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
