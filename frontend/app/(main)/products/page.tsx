"use client";

import { useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

type ConfigSummary = {
  book_count?: number;
  country_count?: number;
  product_count?: number;
  item_count?: number;
  default_product_id?: string;
  code_count?: number;
  product_offer_count?: number;
  book_offer_count?: number;
};

type ConfigItem = {
  config_name: string;
  path: string;
  summary: ConfigSummary;
};

type ConfigResponse = {
  config_name: string;
  path: string;
  summary: ConfigSummary;
  content: Record<string, unknown>;
};

export default function ProductsConfigPage() {
  const [items, setItems] = useState<ConfigItem[]>([]);
  const [selectedConfig, setSelectedConfig] = useState("catalog");
  const [repoPath, setRepoPath] = useState("");
  const [editorValue, setEditorValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const getAuthHeaders = (): Record<string, string> => {
    if (typeof window === "undefined") return {};
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const loadIndex = async () => {
    const res = await fetch(`${API_BASE}/api/admin/product-config`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    setItems(Array.isArray(data.items) ? data.items : []);
    setRepoPath(String(data.repo_path || ""));
  };

  const loadConfig = async (configName: string) => {
    setLoading(true);
    setError("");
    setStatus("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/product-config/${encodeURIComponent(configName)}`, {
        headers: getAuthHeaders(),
        cache: "no-store",
      });
      const data = (await res.json().catch(() => ({}))) as Partial<ConfigResponse> & { detail?: string };
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setSelectedConfig(configName);
      setEditorValue(JSON.stringify(data.content || {}, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load config");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        await loadIndex();
        await loadConfig("catalog");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load product config");
        setLoading(false);
      }
    })();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const parsed = JSON.parse(editorValue);
      const res = await fetch(`${API_BASE}/api/admin/product-config/${encodeURIComponent(selectedConfig)}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ content: parsed }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setStatus(`Saved ${selectedConfig}.`);
      await loadIndex();
      await loadConfig(selectedConfig);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError(`Invalid JSON: ${err.message}`);
      } else {
        setError(err instanceof Error ? err.message : "Failed to save config");
      }
    } finally {
      setSaving(false);
    }
  };

  const formatJson = () => {
    try {
      const parsed = JSON.parse(editorValue);
      setEditorValue(JSON.stringify(parsed, null, 2));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? `Invalid JSON: ${err.message}` : "Invalid JSON");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Product Config</h1>
          <p className="text-sm text-slate-600">
            First live slice of product management. This edits Cutetales config JSON directly, so new books and product items
            can be managed without opening the repo.
          </p>
          {repoPath ? <p className="mt-1 text-xs text-slate-500">Source repo: {repoPath}</p> : null}
        </div>

        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-slate-900">Config Files</h2>
              <button
                onClick={() => void loadIndex()}
                className="text-sm text-slate-500 hover:text-slate-900"
                type="button"
              >
                Refresh
              </button>
            </div>
            <div className="space-y-3">
              {items.map((item) => (
                <button
                  key={item.config_name}
                  onClick={() => void loadConfig(item.config_name)}
                  type="button"
                  className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                    selectedConfig === item.config_name
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-200 bg-white text-slate-900 hover:border-slate-300"
                  }`}
                >
                  <div className="text-sm font-medium capitalize">{item.config_name}</div>
                  <div className={`mt-1 text-xs ${selectedConfig === item.config_name ? "text-slate-200" : "text-slate-500"}`}>
                    {item.path}
                  </div>
                  <div className={`mt-2 text-xs ${selectedConfig === item.config_name ? "text-slate-200" : "text-slate-600"}`}>
                    {renderSummary(item.summary)}
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-medium text-slate-900 capitalize">{selectedConfig}.json</h2>
                <p className="text-sm text-slate-600">
                  Save here, and the `cutetales-storybook` backend now reloads product config from disk automatically.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={formatJson}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                  type="button"
                >
                  Format JSON
                </button>
                <button
                  onClick={() => void handleSave()}
                  disabled={saving || loading}
                  className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60"
                  type="button"
                >
                  {saving ? "Saving..." : "Save"}
                </button>
              </div>
            </div>

            {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
            {status ? <p className="mb-3 text-sm text-green-700">{status}</p> : null}

            <textarea
              value={editorValue}
              onChange={(e) => setEditorValue(e.target.value)}
              className="min-h-[640px] w-full rounded-xl border border-slate-300 bg-slate-950 p-4 font-mono text-sm text-slate-100 outline-none"
              spellCheck={false}
            />
            {loading ? <p className="mt-3 text-sm text-slate-500">Loading config...</p> : null}
          </section>
        </div>
      </div>
    </div>
  );
}

function renderSummary(summary: ConfigSummary) {
  const parts: string[] = [];
  if (typeof summary.book_count === "number") parts.push(`${summary.book_count} books`);
  if (typeof summary.country_count === "number") parts.push(`${summary.country_count} countries`);
  if (typeof summary.product_count === "number") parts.push(`${summary.product_count} products`);
  if (typeof summary.item_count === "number") parts.push(`${summary.item_count} items`);
  if (typeof summary.code_count === "number") parts.push(`${summary.code_count} codes`);
  if (typeof summary.product_offer_count === "number") parts.push(`${summary.product_offer_count} product offers`);
  if (typeof summary.book_offer_count === "number") parts.push(`${summary.book_offer_count} book offers`);
  if (summary.default_product_id) parts.push(`default=${summary.default_product_id}`);
  return parts.join(" • ") || "No summary";
}
