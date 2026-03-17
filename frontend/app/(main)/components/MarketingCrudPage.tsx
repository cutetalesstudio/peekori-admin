"use client";

import { useEffect, useState } from "react";

type FieldType = "text" | "number" | "checkbox" | "textarea";

type FieldConfig = {
  key: string;
  label: string;
  type?: FieldType;
  placeholder?: string;
};

type MarketingCrudPageProps = {
  title: string;
  endpoint: string;
  fields: FieldConfig[];
  defaultItem: Record<string, string | number | boolean>;
};

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

export default function MarketingCrudPage({
  title,
  endpoint,
  fields,
  defaultItem,
}: MarketingCrudPageProps) {
  const [items, setItems] = useState<any[]>([]);
  const [form, setForm] = useState<Record<string, string | number | boolean>>(defaultItem);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const getAuthHeaders = (): Record<string, string> => {
    const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchItems = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: getAuthHeaders(),
        cache: "no-store",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchItems();
  }, []);

  const resetForm = () => {
    setForm(defaultItem);
    setEditingId(null);
    setError("");
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const method = editingId ? "PATCH" : "POST";
      const url = editingId ? `${API_BASE}${endpoint}/${editingId}` : `${API_BASE}${endpoint}`;
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      await fetchItems();
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Delete this item?")) return;
    setError("");
    try {
      const res = await fetch(`${API_BASE}${endpoint}/${id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      await fetchItems();
      if (editingId === id) resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
          <p className="text-sm text-slate-600">Additive admin config only. No live checkout behavior changes here.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-slate-900">{editingId ? "Edit Item" : "New Item"}</h2>
              <button onClick={resetForm} className="text-sm text-slate-500 hover:text-slate-900">
                Reset
              </button>
            </div>
            <div className="space-y-3">
              {fields.map((field) => {
                const value = form[field.key];
                if (field.type === "checkbox") {
                  return (
                    <label key={field.key} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                      <input
                        type="checkbox"
                        checked={Boolean(value)}
                        onChange={(e) => setForm((prev) => ({ ...prev, [field.key]: e.target.checked }))}
                      />
                      <span>{field.label}</span>
                    </label>
                  );
                }
                if (field.type === "textarea") {
                  return (
                    <label key={field.key} className="block text-sm">
                      <span className="mb-1 block font-medium text-slate-700">{field.label}</span>
                      <textarea
                        rows={3}
                        value={String(value ?? "")}
                        placeholder={field.placeholder}
                        onChange={(e) => setForm((prev) => ({ ...prev, [field.key]: e.target.value }))}
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                      />
                    </label>
                  );
                }
                return (
                  <label key={field.key} className="block text-sm">
                    <span className="mb-1 block font-medium text-slate-700">{field.label}</span>
                    <input
                      type={field.type === "number" ? "number" : "text"}
                      value={String(value ?? "")}
                      placeholder={field.placeholder}
                      onChange={(e) =>
                        setForm((prev) => ({
                          ...prev,
                          [field.key]: field.type === "number" ? Number(e.target.value || 0) : e.target.value,
                        }))
                      }
                      className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />
                  </label>
                );
              })}
            </div>
            {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
            <button
              onClick={handleSave}
              disabled={saving}
              className="mt-4 w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60"
            >
              {saving ? "Saving..." : editingId ? "Save Changes" : "Create"}
            </button>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-slate-900">Items</h2>
              <button onClick={() => void fetchItems()} className="text-sm text-slate-500 hover:text-slate-900">
                Refresh
              </button>
            </div>
            {loading ? (
              <p className="text-sm text-slate-500">Loading...</p>
            ) : items.length === 0 ? (
              <p className="text-sm text-slate-500">No items yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-slate-500">
                      {fields.slice(0, 5).map((field) => (
                        <th key={field.key} className="px-3 py-2 font-medium">{field.label}</th>
                      ))}
                      <th className="px-3 py-2 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr key={item.id} className="border-b border-slate-100 align-top">
                        {fields.slice(0, 5).map((field) => (
                          <td key={field.key} className="px-3 py-3 text-slate-700">
                            {typeof item[field.key] === "boolean" ? (item[field.key] ? "Yes" : "No") : (item[field.key] || "-")}
                          </td>
                        ))}
                        <td className="px-3 py-3">
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                setEditingId(item.id);
                                setForm({ ...defaultItem, ...item });
                              }}
                              className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => void handleDelete(item.id)}
                              className="rounded-md border border-red-300 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
