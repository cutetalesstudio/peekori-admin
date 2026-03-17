"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

type ConfigStatus = {
  has_draft?: boolean;
  live_updated_at?: string | null;
  draft_updated_at?: string | null;
};

type CatalogContent = {
  books?: Record<string, { title?: string }>;
};

type ProductsContent = {
  products?: Record<string, { title?: string }>;
};

type DiscountsContent = {
  default?: string;
  codes?: Record<string, number>;
  platform_offer?: {
    default_percent?: number;
    by_product?: Record<string, number>;
    by_book?: Record<string, number>;
  };
  [key: string]: unknown;
};

type CodeRow = {
  id: string;
  code: string;
  percent: string;
};

type OfferRow = {
  id: string;
  target: string;
  percent: string;
};

type ValidationItem = {
  level: "error" | "warning" | "success";
  message: string;
};

function makeRowId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function DiscountManagerPage() {
  const [catalog, setCatalog] = useState<CatalogContent | null>(null);
  const [products, setProducts] = useState<ProductsContent | null>(null);
  const [content, setContent] = useState<DiscountsContent | null>(null);
  const [status, setStatus] = useState<ConfigStatus | null>(null);
  const [codeRows, setCodeRows] = useState<CodeRow[]>([]);
  const [bookOfferRows, setBookOfferRows] = useState<OfferRow[]>([]);
  const [productOfferRows, setProductOfferRows] = useState<OfferRow[]>([]);
  const [defaultCode, setDefaultCode] = useState("");
  const [defaultPercent, setDefaultPercent] = useState("20");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [discarding, setDiscarding] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const authHeaders = (): Record<string, string> => {
    if (typeof window === "undefined") return {};
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const bookOptions = useMemo(
    () =>
      Object.entries(catalog?.books || {}).map(([bookKey, book]) => ({
        value: bookKey,
        label: `${book?.title || bookKey} (${bookKey})`,
      })),
    [catalog]
  );

  const productOptions = useMemo(() => {
    const liveProducts = Object.keys(products?.products || {});
    const normalized = Array.from(new Set(["storybook", ...liveProducts])).sort((a, b) => a.localeCompare(b));
    return normalized.map((productId) => ({
      value: productId,
      label: `${products?.products?.[productId]?.title || productId} (${productId})`,
    }));
  }, [products]);

  const validations = useMemo<ValidationItem[]>(() => {
    const items: ValidationItem[] = [];
    const bookSet = new Set(bookOptions.map((item) => item.value));
    const productSet = new Set(productOptions.map((item) => item.value));
    const codeSet = new Set<string>();

    for (const row of codeRows) {
      const code = normalizeCode(row.code);
      const pct = parsePercent(row.percent);
      if (!code) {
        items.push({ level: "warning", message: "One coupon code row is blank." });
        continue;
      }
      if (codeSet.has(code)) {
        items.push({ level: "error", message: `Duplicate coupon code: ${code}` });
      }
      codeSet.add(code);
      if (pct === null) {
        items.push({ level: "error", message: `Coupon code ${code} needs a valid percent between 0 and 100.` });
      }
    }

    if (defaultCode && !codeSet.has(normalizeCode(defaultCode))) {
      items.push({ level: "error", message: `Default coupon code ${normalizeCode(defaultCode)} does not exist in the coupon list.` });
    }

    const defaultOfferPct = parsePercent(defaultPercent);
    if (defaultOfferPct === null) {
      items.push({ level: "error", message: "Default website offer percent must be between 0 and 100." });
    }

    for (const row of bookOfferRows) {
      const key = normalizeKey(row.target);
      const pct = parsePercent(row.percent);
      if (!key) continue;
      if (!bookSet.has(key)) {
        items.push({ level: "error", message: `Book offer target ${key} does not exist in catalog.json.` });
      }
      if (pct === null) {
        items.push({ level: "error", message: `Book offer ${key} needs a valid percent between 0 and 100.` });
      }
    }

    for (const row of productOfferRows) {
      const key = normalizeKey(row.target);
      const pct = parsePercent(row.percent);
      if (!key) continue;
      if (!productSet.has(key)) {
        items.push({ level: "error", message: `Product offer target ${key} does not exist in products.json.` });
      }
      if (pct === null) {
        items.push({ level: "error", message: `Product offer ${key} needs a valid percent between 0 and 100.` });
      }
    }

    if (items.length === 0) {
      items.push({ level: "success", message: "Discount config is aligned with current catalog and products." });
    }
    return items;
  }, [bookOfferRows, bookOptions, codeRows, defaultCode, defaultPercent, productOfferRows, productOptions]);

  useEffect(() => {
    void loadAll();
  }, []);

  async function loadAll() {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const [catalogRes, productsRes, discountsRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/product-config/catalog`, { headers: authHeaders(), cache: "no-store" }),
        fetch(`${API_BASE}/api/admin/product-config/products`, { headers: authHeaders(), cache: "no-store" }),
        fetch(`${API_BASE}/api/admin/product-config/discounts`, { headers: authHeaders(), cache: "no-store" }),
      ]);

      const [catalogData, productsData, discountsData] = await Promise.all([
        catalogRes.json().catch(() => ({})),
        productsRes.json().catch(() => ({})),
        discountsRes.json().catch(() => ({})),
      ]);

      if (!catalogRes.ok) throw new Error(catalogData.detail || `Catalog HTTP ${catalogRes.status}`);
      if (!productsRes.ok) throw new Error(productsData.detail || `Products HTTP ${productsRes.status}`);
      if (!discountsRes.ok) throw new Error(discountsData.detail || `Discounts HTTP ${discountsRes.status}`);

      const nextContent = (discountsData.content || {}) as DiscountsContent;
      setCatalog((catalogData.content || {}) as CatalogContent);
      setProducts((productsData.content || {}) as ProductsContent);
      setContent(nextContent);
      setStatus((discountsData.status || null) as ConfigStatus | null);
      hydrateForm(nextContent);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load discount config");
    } finally {
      setLoading(false);
    }
  }

  function hydrateForm(nextContent: DiscountsContent) {
    const nextCodes = nextContent.codes || {};
    const nextOffer = nextContent.platform_offer || {};
    const nextByBook = nextOffer.by_book || {};
    const nextByProduct = nextOffer.by_product || {};

    setDefaultCode(String(nextContent.default || ""));
    setDefaultPercent(stringifyPercent(nextOffer.default_percent, "20"));
    setCodeRows(
      Object.entries(nextCodes).map(([code, percent]) => ({
        id: makeRowId(),
        code,
        percent: stringifyPercent(percent, ""),
      }))
    );
    setBookOfferRows(
      Object.entries(nextByBook).map(([target, percent]) => ({
        id: makeRowId(),
        target,
        percent: stringifyPercent(percent, ""),
      }))
    );
    setProductOfferRows(
      Object.entries(nextByProduct).map(([target, percent]) => ({
        id: makeRowId(),
        target,
        percent: stringifyPercent(percent, ""),
      }))
    );
  }

  async function saveDraft() {
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const payload = buildPayload(content, {
        defaultCode,
        defaultPercent,
        codeRows,
        bookOfferRows,
        productOfferRows,
      });
      const res = await fetch(`${API_BASE}/api/admin/product-config/discounts`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ content: payload }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setStatus((data.status || null) as ConfigStatus | null);
      setContent(payload);
      setMessage("Saved discounts draft.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save discounts draft");
    } finally {
      setSaving(false);
    }
  }

  async function publishDraft() {
    setPublishing(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/product-config/discounts/publish`, {
        method: "POST",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setStatus((data.status || null) as ConfigStatus | null);
      setMessage("Published discounts draft to live.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to publish discounts draft");
    } finally {
      setPublishing(false);
    }
  }

  async function discardDraft() {
    setDiscarding(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/product-config/discounts/draft`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setStatus((data.status || null) as ConfigStatus | null);
      setMessage("Discarded discounts draft.");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to discard discounts draft");
    } finally {
      setDiscarding(false);
    }
  }

  const errorCount = validations.filter((item) => item.level === "error").length;
  const warningCount = validations.filter((item) => item.level === "warning").length;
  const successCount = validations.filter((item) => item.level === "success").length;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Discount Manager</h1>
            <p className="mt-1 text-sm text-slate-600">
              Manage site-wide product offers and checkout coupon codes backed by <code>discounts.json</code>.
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Catalog and products stay separate. This page only updates the discount config JSON used by the storefront.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void loadAll()} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
              Refresh
            </button>
            <button type="button" onClick={() => void discardDraft()} disabled={discarding || !status?.has_draft} className="rounded-lg border border-amber-300 px-4 py-2 text-sm text-amber-700 hover:bg-amber-50 disabled:opacity-50">
              {discarding ? "Discarding..." : "Discard Draft"}
            </button>
            <button type="button" onClick={() => void publishDraft()} disabled={publishing || errorCount > 0 || !status?.has_draft} className="rounded-lg border border-emerald-300 px-4 py-2 text-sm text-emerald-700 hover:bg-emerald-50 disabled:opacity-50">
              {publishing ? "Publishing..." : "Publish Draft"}
            </button>
            <button type="button" onClick={() => void saveDraft()} disabled={saving || loading || errorCount > 0} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">
              {saving ? "Saving..." : "Save Draft"}
            </button>
          </div>
        </div>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-sm font-semibold text-slate-900">Publish Readiness</div>
              <p className="mt-1 text-sm text-slate-600">Validation is view-only. Use it to keep discount targets aligned with current books and products.</p>
            </div>
            <div className="flex flex-wrap gap-2 text-sm">
              <span className="rounded-full bg-red-50 px-3 py-1 text-red-700">Errors: {errorCount}</span>
              <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-700">Warnings: {warningCount}</span>
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700">Success: {successCount}</span>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {validations.map((item) => (
              <div
                key={`${item.level}-${item.message}`}
                className={`rounded-xl border px-4 py-3 text-sm ${
                  item.level === "error"
                    ? "border-red-200 bg-red-50 text-red-700"
                    : item.level === "warning"
                    ? "border-amber-200 bg-amber-50 text-amber-800"
                    : "border-emerald-200 bg-emerald-50 text-emerald-700"
                }`}
              >
                {item.message}
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-slate-500">
            Draft mode: {status?.has_draft ? `active, last updated ${formatTimestamp(status.draft_updated_at)}` : "no draft file yet, showing live config as the starting point."}
          </div>
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
          {message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
        </section>

        <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr]">
          <section className="space-y-6">
            <Card title="Website Offer Defaults" description="Control the strike-through offer percentages shown across the storefront.">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="block">
                  <div className="mb-1 text-sm font-medium text-slate-700">Default Offer Percent</div>
                  <input value={defaultPercent} onChange={(e) => setDefaultPercent(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="20" />
                </label>
                <label className="block">
                  <div className="mb-1 text-sm font-medium text-slate-700">Default Coupon Code</div>
                  <select value={defaultCode} onChange={(e) => setDefaultCode(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                    <option value="">Select default code</option>
                    {codeRows.map((row) => {
                      const code = normalizeCode(row.code);
                      return code ? <option key={row.id} value={code}>{code}</option> : null;
                    })}
                  </select>
                </label>
              </div>
            </Card>

            <Card title="Per-Book Offers" description="Override the default storybook discount for specific books.">
              <div className="space-y-3">
                {bookOfferRows.map((row, index) => (
                  <div key={row.id} className="grid gap-3 rounded-xl border border-slate-200 p-4 md:grid-cols-[1fr_180px_auto]">
                    <select value={row.target} onChange={(e) => updateOfferRow(setBookOfferRows, row.id, { target: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                      <option value="">Select book</option>
                      {bookOptions.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                    <input value={row.percent} onChange={(e) => updateOfferRow(setBookOfferRows, row.id, { percent: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="20" />
                    <button type="button" onClick={() => removeRow(setBookOfferRows, row.id)} className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50">
                      Remove
                    </button>
                    <div className="text-xs text-slate-500 md:col-span-3">Book offer #{index + 1}</div>
                  </div>
                ))}
                <button type="button" onClick={() => setBookOfferRows((rows) => [...rows, { id: makeRowId(), target: bookOptions[0]?.value || "", percent: "" }])} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
                  Add Book Offer
                </button>
              </div>
            </Card>

            <Card title="Per-Product Offers" description="Override the default offer for storybook, frame, sticker, or any future product type in products.json.">
              <div className="space-y-3">
                {productOfferRows.map((row, index) => (
                  <div key={row.id} className="grid gap-3 rounded-xl border border-slate-200 p-4 md:grid-cols-[1fr_180px_auto]">
                    <select value={row.target} onChange={(e) => updateOfferRow(setProductOfferRows, row.id, { target: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                      <option value="">Select product</option>
                      {productOptions.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                    <input value={row.percent} onChange={(e) => updateOfferRow(setProductOfferRows, row.id, { percent: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="10" />
                    <button type="button" onClick={() => removeRow(setProductOfferRows, row.id)} className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50">
                      Remove
                    </button>
                    <div className="text-xs text-slate-500 md:col-span-3">Product offer #{index + 1}</div>
                  </div>
                ))}
                <button type="button" onClick={() => setProductOfferRows((rows) => [...rows, { id: makeRowId(), target: productOptions[0]?.value || "storybook", percent: "" }])} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
                  Add Product Offer
                </button>
              </div>
            </Card>
          </section>

          <section className="space-y-6">
            <Card title="Coupon Codes" description="Create, update, or delete the actual coupon codes used at checkout.">
              <div className="space-y-3">
                {codeRows.map((row, index) => (
                  <div key={row.id} className="grid gap-3 rounded-xl border border-slate-200 p-4 md:grid-cols-[1fr_180px_auto]">
                    <input value={row.code} onChange={(e) => updateCodeRow(setCodeRows, row.id, { code: e.target.value.toUpperCase() })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="WELCOME10" />
                    <input value={row.percent} onChange={(e) => updateCodeRow(setCodeRows, row.id, { percent: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="10" />
                    <button type="button" onClick={() => removeRow(setCodeRows, row.id)} className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50">
                      Delete
                    </button>
                    <div className="text-xs text-slate-500 md:col-span-3">Coupon code #{index + 1}</div>
                  </div>
                ))}
                <button type="button" onClick={() => setCodeRows((rows) => [...rows, { id: makeRowId(), code: "", percent: "" }])} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
                  Add Coupon Code
                </button>
              </div>
            </Card>

            <Card title="Current Logic Notes" description="These are the existing contracts kept intact by this UI.">
              <ul className="space-y-2 text-sm text-slate-600">
                <li>`platform_offer.by_book` controls per-book site-wide display discounts.</li>
                <li>`platform_offer.by_product` controls per-product site-wide display discounts.</li>
                <li>`codes` controls checkout coupon codes.</li>
                <li>`default` is the default coupon code used where the backend expects one.</li>
                <li>`catalog.json` and `products.json` are not merged into `discounts.json`; this page only validates references against them.</li>
              </ul>
            </Card>
          </section>
        </div>
      </div>
    </div>
  );
}

function Card({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-medium text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
      </div>
      {children}
    </section>
  );
}

function normalizeCode(value: string) {
  return String(value || "").trim().toUpperCase();
}

function normalizeKey(value: string) {
  return String(value || "").trim().toLowerCase();
}

function parsePercent(value: string) {
  const parsed = Number(String(value || "").trim());
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) return null;
  return parsed;
}

function stringifyPercent(value: unknown, fallback: string) {
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  const parsed = Number(value);
  return Number.isFinite(parsed) ? String(parsed) : fallback;
}

function buildPayload(
  previousContent: DiscountsContent | null,
  values: {
    defaultCode: string;
    defaultPercent: string;
    codeRows: CodeRow[];
    bookOfferRows: OfferRow[];
    productOfferRows: OfferRow[];
  }
): DiscountsContent {
  const nextCodes: Record<string, number> = {};
  for (const row of values.codeRows) {
    const code = normalizeCode(row.code);
    const pct = parsePercent(row.percent);
    if (!code || pct === null) continue;
    nextCodes[code] = pct;
  }

  const nextByBook: Record<string, number> = {};
  for (const row of values.bookOfferRows) {
    const key = normalizeKey(row.target);
    const pct = parsePercent(row.percent);
    if (!key || pct === null) continue;
    nextByBook[key] = pct;
  }

  const nextByProduct: Record<string, number> = {};
  for (const row of values.productOfferRows) {
    const key = normalizeKey(row.target);
    const pct = parsePercent(row.percent);
    if (!key || pct === null) continue;
    nextByProduct[key] = pct;
  }

  const fallbackDefaultCode = Object.keys(nextCodes)[0] || "";
  return {
    ...(previousContent || {}),
    default: normalizeCode(values.defaultCode) || fallbackDefaultCode,
    codes: nextCodes,
    platform_offer: {
      ...((previousContent?.platform_offer as Record<string, unknown>) || {}),
      default_percent: parsePercent(values.defaultPercent) ?? 20,
      by_product: nextByProduct,
      by_book: nextByBook,
    },
  };
}

function updateCodeRow(
  setter: React.Dispatch<React.SetStateAction<CodeRow[]>>,
  rowId: string,
  patch: Partial<CodeRow>
) {
  setter((rows) => rows.map((row) => (row.id === rowId ? { ...row, ...patch } : row)));
}

function updateOfferRow(
  setter: React.Dispatch<React.SetStateAction<OfferRow[]>>,
  rowId: string,
  patch: Partial<OfferRow>
) {
  setter((rows) => rows.map((row) => (row.id === rowId ? { ...row, ...patch } : row)));
}

function removeRow<T extends { id: string }>(
  setter: React.Dispatch<React.SetStateAction<T[]>>,
  rowId: string
) {
  setter((rows) => rows.filter((row) => row.id !== rowId));
}

function formatTimestamp(value?: string | null) {
  if (!value) return "unknown";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
