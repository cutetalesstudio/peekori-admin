"use client";

import Link from "next/link";
import { useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");

export default function CreatorSignupPage() {
  const [step, setStep] = useState<"form" | "otp" | "done">("form");
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    country: "IN",
    instagram_handle: "",
    youtube_channel: "",
  });
  const [otp, setOtp] = useState("");
  const [debugOtp, setDebugOtp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const socialProvided = Boolean(form.instagram_handle.trim() || form.youtube_channel.trim());

  const startSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!socialProvided) {
      setError("Add your Instagram handle or YouTube channel.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/creator/auth/signup/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "Failed to start signup");
      setDebugOtp(body.otp_debug || "");
      setStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start signup");
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/creator/auth/signup/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email, otp }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "Failed to verify OTP");
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to verify OTP");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Create Creator Account</h1>
        <p className="mb-6 mt-2 text-sm text-slate-600">Verify your email, share your creator channel details, and wait for admin approval.</p>

        {step === "form" ? (
          <form onSubmit={startSignup} className="space-y-4">
            <Input label="Full Name" value={form.name} onChange={(value) => setForm((prev) => ({ ...prev, name: value }))} />
            <Input label="Email" value={form.email} onChange={(value) => setForm((prev) => ({ ...prev, email: value }))} />
            <Input label="Password" type="password" value={form.password} onChange={(value) => setForm((prev) => ({ ...prev, password: value }))} />
            <label className="block">
              <div className="mb-1 text-sm font-medium text-slate-700">Country</div>
              <select value={form.country} onChange={(e) => setForm((prev) => ({ ...prev, country: e.target.value }))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                <option value="IN">India</option>
                <option value="US">United States</option>
                <option value="GB">United Kingdom</option>
                <option value="CA">Canada</option>
                <option value="AE">United Arab Emirates</option>
                <option value="OTHER">Other</option>
              </select>
            </label>
            <Input label="Instagram Handle" value={form.instagram_handle} onChange={(value) => setForm((prev) => ({ ...prev, instagram_handle: value }))} />
            <Input label="YouTube Channel" value={form.youtube_channel} onChange={(value) => setForm((prev) => ({ ...prev, youtube_channel: value }))} />
            <p className="text-xs text-slate-500">At least one channel is required for approval review.</p>
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <button type="submit" disabled={loading} className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
              {loading ? "Sending OTP..." : "Send OTP"}
            </button>
          </form>
        ) : null}

        {step === "otp" ? (
          <form onSubmit={verifyOtp} className="space-y-4">
            <p className="text-sm text-slate-600">Enter the OTP sent to {form.email}.</p>
            <Input label="OTP" value={otp} onChange={setOtp} />
            {debugOtp ? <p className="text-xs text-amber-700">Local debug OTP: {debugOtp}</p> : null}
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <button type="submit" disabled={loading} className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
              {loading ? "Verifying..." : "Verify OTP"}
            </button>
          </form>
        ) : null}

        {step === "done" ? (
          <div className="space-y-3">
            <p className="rounded-lg bg-green-50 p-3 text-sm text-green-700">Signup complete. Your account is pending admin approval. You can log in after approval.</p>
            <Link href="/creator/login" className="inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white">
              Go to Login
            </Link>
          </div>
        ) : null}

        <div className="mt-6 text-sm text-slate-600">
          Already have an account?{" "}
          <Link href="/creator/login" className="font-medium text-slate-900 underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="block">
      <div className="mb-1 text-sm font-medium text-slate-700">{label}</div>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
    </label>
  );
}
