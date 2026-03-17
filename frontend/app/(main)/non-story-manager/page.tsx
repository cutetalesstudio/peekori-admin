"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const STOREFRONT_BASE = (process.env.NEXT_PUBLIC_STOREFRONT_BASE_URL || "http://localhost:3000").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";
const EMPTY_PRICE = { price: "", shipping: "", taxes: "" };

type PriceFields = typeof EMPTY_PRICE;
type ValidationCheck = { level: "error" | "warning" | "success" | "info"; code: string; message: string };
type CheckoutOption = { id: string; label: string; description?: string };
type ProductItem = {
  id?: string;
  slug?: string;
  enabled?: boolean;
  title?: string;
  description?: string;
  imageSrc?: string;
  hero_images?: string[];
  cta_label?: string;
  create_section_title?: string;
  create_section_description?: string;
  features?: string[];
  feature_items?: string[];
  trust_items?: string[];
  faq_items?: Array<{ id?: string; question?: string; answer?: string }>;
  review_rating?: string;
  review_count_label?: string;
  delivery_note?: string;
  preview_note?: string;
  seo_title?: string;
  seo_description?: string;
  seo_keywords?: string[];
  seo_image?: string;
  seo_canonical_path?: string;
  [key: string]: unknown;
};
type ProductConfig = {
  id: string;
  title?: string;
  enabled?: boolean;
  default_item_id?: string;
  items?: ProductItem[];
  checkout_options?: CheckoutOption[];
  catalog?: {
    allowed_countries?: string[];
    prices?: Record<string, Record<string, PriceFields>>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};
type ProductsContent = {
  default_product_id?: string;
  products?: Record<string, ProductConfig>;
  [key: string]: unknown;
};
type ConfigStatus = {
  has_draft?: boolean;
  live_updated_at?: string | null;
  draft_updated_at?: string | null;
};
type FaqItemForm = { id: string; question: string; answer: string };
type CheckoutOptionForm = { id: string; label: string; description: string };
type ProductForm = {
  itemId: string;
  slug: string;
  enabled: boolean;
  title: string;
  description: string;
  imageSrc: string;
  heroImages: string[];
  ctaLabel: string;
  createSectionTitle: string;
  createSectionDescription: string;
  featureItems: string[];
  trustItems: string[];
  faqItems: FaqItemForm[];
  reviewRating: string;
  reviewCountLabel: string;
  deliveryNote: string;
  previewNote: string;
  seoTitle: string;
  seoDescription: string;
  seoKeywords: string;
  seoImage: string;
  seoCanonicalPath: string;
  enabledCountries: string[];
  checkoutOptions: CheckoutOptionForm[];
  prices: Record<string, Record<string, PriceFields>>;
};
type SectionId =
  | "overview"
  | "basic"
  | "copy"
  | "seo"
  | "validation"
  | "media"
  | "gallery"
  | "features"
  | "trust"
  | "faq"
  | "pricing";

export default function NonStoryManagerPage() {
  const [content, setContent] = useState<ProductsContent | null>(null);
  const [productType, setProductType] = useState("frame");
  const [selectedItemId, setSelectedItemId] = useState("");
  const [form, setForm] = useState<ProductForm | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [configStatus, setConfigStatus] = useState<ConfigStatus | null>(null);
  const [checks, setChecks] = useState<ValidationCheck[]>([]);
  const [checking, setChecking] = useState(false);
  const [mainImageFile, setMainImageFile] = useState<File | null>(null);
  const [galleryFiles, setGalleryFiles] = useState<File[]>([]);
  const [layoutFiles, setLayoutFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState("");
  const [expandedSections, setExpandedSections] = useState<Record<SectionId, boolean>>(defaultExpandedSections());
  const [editingSection, setEditingSection] = useState<SectionId | null>(null);
  const [sectionSnapshot, setSectionSnapshot] = useState<ProductForm | null>(null);
  const [loadedFormSnapshot, setLoadedFormSnapshot] = useState<ProductForm | null>(null);
  const [statusPanelOpen, setStatusPanelOpen] = useState(false);
  const gallerySectionRef = useRef<HTMLDivElement | null>(null);

  const authHeaders = (): Record<string, string> => {
    if (typeof window === "undefined") return {};
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const productMap = content?.products || {};
  const productEntries = useMemo(
    () => Object.entries(productMap).filter(([id]) => id !== "storybook"),
    [productMap]
  );
  const activeProduct = productMap[productType];
  const itemEntries = useMemo(
    () => ((activeProduct?.items || []) as ProductItem[]).map((item) => [String(item.id || ""), item] as const).filter(([id]) => Boolean(id)),
    [activeProduct]
  );
  const countryEntries = useMemo(() => {
    const catalogCountries = (content as any)?.catalog?.countries;
    return catalogCountries ? Object.entries(catalogCountries) : [["US", {}], ["CA", {}], ["IN", {}], ["GB", {}], ["AE", {}]];
  }, [content]);
  const publicItemPath = useMemo(() => buildNonStoryPublicPath(productType, form?.itemId, form?.slug), [productType, form?.itemId, form?.slug]);
  const draftPreviewPath = useMemo(() => buildNonStoryDraftPreviewPath(productType, form?.itemId), [productType, form?.itemId]);
  const isCreatingNewItem = !selectedItemId;
  const sectionDirty = useMemo(() => {
    if (!form || !loadedFormSnapshot) return defaultDirtySections();
    return buildProductSectionDirtyMap(form, loadedFormSnapshot);
  }, [form, loadedFormSnapshot]);
  const sectionSummaries = useMemo(
    () =>
      form
        ? {
            overview: summarizeValues([form.title || form.itemId || "No item selected", `${form.enabledCountries.length} countries`, `${cleanedList(form.heroImages).length} gallery images`]),
            basic: summarizeValues([form.title || "Untitled item", form.enabled ? "Enabled" : "Disabled", form.imageSrc || "No main image"]),
            copy: summarizeValues([form.ctaLabel || "CTA not set", form.reviewCountLabel || "Review count not set", form.deliveryNote || "Delivery note not set"]),
            seo: summarizeValues([form.seoTitle || "SEO title not set", form.seoCanonicalPath || buildNonStoryPublicPath(productType, form.itemId, form.slug) || "Canonical path pending"]),
            validation: summarizeValues(checks.slice(0, 2).map((check) => check.message), checking ? "Checking assets..." : "No validation messages yet"),
            media: summarizeValues([form.imageSrc || "No main image", `${galleryFiles.length} pending gallery uploads`, `${layoutFiles.length} pending layout files`]),
            gallery: summarizeValues(cleanedList(form.heroImages), "No gallery images"),
            features: summarizeValues(cleanedList(form.featureItems), "No feature bullets"),
            trust: summarizeValues(cleanedList(form.trustItems), "No trust badges"),
            faq: summarizeValues(form.faqItems.map((item) => item.question).filter(Boolean), "No FAQs"),
            pricing: summarizeValues([...form.enabledCountries, ...form.checkoutOptions.map((option) => option.label || option.id)], "No pricing setup"),
          }
        : null,
    [checks, checking, form, galleryFiles.length, layoutFiles.length, productType]
  );

  useEffect(() => {
    void loadProducts();
  }, []);

  useEffect(() => {
    if (!form?.itemId.trim()) {
      setChecks([]);
      return;
    }
    const timer = window.setTimeout(async () => {
      setChecking(true);
      try {
        const res = await fetch(`${API_BASE}/api/admin/non-story-manager/validate`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body: JSON.stringify({
            product_id: productType,
            item_id: form.itemId.trim(),
            image_src: form.imageSrc,
            hero_images: form.heroImages,
            enabled_countries: form.enabledCountries,
            prices: form.prices,
          }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
        setChecks(Array.isArray(data.checks) ? data.checks : []);
      } catch (err) {
        setChecks([{ level: "error", code: "validation_failed", message: err instanceof Error ? err.message : "Validation failed" }]);
      } finally {
        setChecking(false);
      }
    }, 400);
    return () => window.clearTimeout(timer);
  }, [form, productType]);

  async function loadProducts(nextProductType?: string, preferredItemId?: string) {
    setLoading(true);
    setError("");
    setStatus("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/product-config/products`, {
        headers: authHeaders(),
        cache: "no-store",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      const nextContent = (data.content || {}) as ProductsContent;
      setConfigStatus((data.status || null) as ConfigStatus | null);
      setContent(nextContent);
      const products = nextContent.products || {};
      const nextType =
        nextProductType && products[nextProductType]
          ? nextProductType
          : Object.keys(products).find((id) => id !== "storybook") || "frame";
      const product = products[nextType];
      const items = Array.isArray(product?.items) ? product.items : [];
      const nextItemId =
        preferredItemId && items.some((item) => String(item.id || "").trim().toLowerCase() === preferredItemId)
          ? preferredItemId
          : String(product?.default_item_id || items[0]?.id || "");
      setProductType(nextType);
      setSelectedItemId(nextItemId);
      const nextForm = nextItemId ? buildForm(nextType, nextItemId, nextContent) : buildEmptyForm(product);
      setForm(nextForm);
      setLoadedFormSnapshot(cloneForm(nextForm));
      clearUploads();
      resetSectionUi();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  }

  function clearUploads() {
    setMainImageFile(null);
    setGalleryFiles([]);
    setLayoutFiles([]);
    setUploading("");
  }

  function resetSectionUi() {
    setExpandedSections(defaultExpandedSections());
    setEditingSection(null);
    setSectionSnapshot(null);
  }

  function setField<K extends keyof ProductForm>(key: K, value: ProductForm[K]) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function selectProduct(nextType: string) {
    if (!content?.products?.[nextType]) return;
    const product = content.products[nextType];
    const items = Array.isArray(product.items) ? product.items : [];
    const itemId = String(product.default_item_id || items[0]?.id || "");
    setProductType(nextType);
    setSelectedItemId(itemId);
    setForm(itemId ? buildForm(nextType, itemId, content) : buildEmptyForm(product));
    clearUploads();
    setError("");
    setStatus("");
    resetSectionUi();
  }

  function selectItem(itemId: string) {
    if (!content) return;
    setSelectedItemId(itemId);
    const nextForm = buildForm(productType, itemId, content);
    setForm(nextForm);
    setLoadedFormSnapshot(cloneForm(nextForm));
    clearUploads();
    setError("");
    setStatus("");
    resetSectionUi();
  }

  function startNewItem() {
    setSelectedItemId("");
    const nextForm = buildEmptyForm(activeProduct);
    setForm(nextForm);
    setLoadedFormSnapshot(cloneForm(nextForm));
    clearUploads();
    setError("");
    setStatus("");
    setExpandedSections(defaultCreateExpandedSections());
    setSectionSnapshot(cloneForm(nextForm));
    setEditingSection("basic");
  }

  function toggleSection(section: SectionId) {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  }

  function beginSectionEdit(section: SectionId) {
    if (!form || (editingSection && editingSection !== section)) return;
    setSectionSnapshot(cloneForm(form));
    setEditingSection(section);
    setExpandedSections((prev) => ({ ...prev, [section]: true }));
    setStatus("");
  }

  function jumpToGalleryEditor() {
    setExpandedSections((prev) => ({ ...prev, gallery: true }));
    if (form) {
      setSectionSnapshot(cloneForm(form));
      setEditingSection("gallery");
    }
    window.setTimeout(() => {
      gallerySectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }

  function saveSectionEdit(section: SectionId) {
    if (editingSection !== section) return;
    setEditingSection(null);
    setSectionSnapshot(null);
    setStatus("Section updated in draft form. Save Draft to keep the change.");
  }

  function cancelSectionEdit(section: SectionId) {
    if (editingSection !== section) return;
    if (sectionSnapshot) setForm(cloneForm(sectionSnapshot));
    setEditingSection(null);
    setSectionSnapshot(null);
    clearUploads();
    setStatus("Section changes were discarded.");
  }

  function toggleCountry(countryCode: string) {
    setForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        enabledCountries: prev.enabledCountries.includes(countryCode)
          ? prev.enabledCountries.filter((code) => code !== countryCode)
          : [...prev.enabledCountries, countryCode],
      };
    });
  }

  function updateListField(key: "heroImages" | "featureItems" | "trustItems", index: number, value: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const next = [...prev[key]];
      next[index] = value;
      return { ...prev, [key]: next };
    });
  }

  function addListField(key: "heroImages" | "featureItems" | "trustItems") {
    setForm((prev) => (prev ? { ...prev, [key]: [...prev[key], ""] } : prev));
  }

  function removeListField(key: "heroImages" | "featureItems" | "trustItems", index: number) {
    setForm((prev) => (prev ? { ...prev, [key]: prev[key].filter((_, idx) => idx !== index) } : prev));
  }

  function updateFaq(index: number, key: keyof FaqItemForm, value: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const next = [...prev.faqItems];
      next[index] = { ...next[index], [key]: value };
      return { ...prev, faqItems: next };
    });
  }

  function addFaq() {
    setForm((prev) => (prev ? { ...prev, faqItems: [...prev.faqItems, { id: "", question: "", answer: "" }] } : prev));
  }

  function removeFaq(index: number) {
    setForm((prev) => (prev ? { ...prev, faqItems: prev.faqItems.filter((_, idx) => idx !== index) } : prev));
  }

  function updateOption(index: number, key: keyof CheckoutOptionForm, value: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const next = [...prev.checkoutOptions];
      next[index] = { ...next[index], [key]: value };
      return { ...prev, checkoutOptions: next };
    });
  }

  function addOption() {
    setForm((prev) => (prev ? { ...prev, checkoutOptions: [...prev.checkoutOptions, { id: "", label: "", description: "" }] } : prev));
  }

  function removeOption(index: number) {
    setForm((prev) => (prev ? { ...prev, checkoutOptions: prev.checkoutOptions.filter((_, idx) => idx !== index) } : prev));
  }

  function updatePrice(countryCode: string, optionId: string, field: keyof PriceFields, value: string) {
    setForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        prices: {
          ...prev.prices,
          [countryCode]: {
            ...(prev.prices[countryCode] || {}),
            [optionId]: {
              ...((prev.prices[countryCode] || {})[optionId] || { ...EMPTY_PRICE }),
              [field]: value,
            },
          },
        },
      };
    });
  }

  async function handleSave() {
    if (!content || !form || !activeProduct) return;
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const itemId = form.itemId.trim().toLowerCase();
      const slug = normalizeSlug(form.slug);
      if (!itemId) throw new Error("Item id is required");
      if (!form.title.trim()) throw new Error("Title is required");
      const products = { ...(content.products || {}) };
      const product = { ...(products[productType] || {}) } as ProductConfig;
      const items = Array.isArray(product.items) ? [...product.items] : [];
      if (!selectedItemId && items.some((item) => String(item.id || "").trim().toLowerCase() === itemId)) {
        throw new Error("An item with this id already exists");
      }
      const duplicateSlug = items.find((item) => {
        const existingId = String(item.id || "").trim().toLowerCase();
        if (selectedItemId && existingId === selectedItemId) return false;
        return normalizeSlug(String(item.slug || "")) === slug && Boolean(slug);
      });
      if (duplicateSlug) throw new Error(`Slug '${slug}' is already used by ${String(duplicateSlug.id || "")}`);
      const currentIndex = items.findIndex((item) => String(item.id || "").trim().toLowerCase() === selectedItemId);
      const existing = currentIndex >= 0 ? items[currentIndex] : {};
      const nextItem: ProductItem = {
        ...existing,
        id: itemId,
        slug,
        enabled: form.enabled,
        title: form.title.trim(),
        description: form.description.trim(),
        imageSrc: form.imageSrc.trim(),
        hero_images: cleanedList(form.heroImages),
        cta_label: form.ctaLabel.trim(),
        create_section_title: form.createSectionTitle.trim(),
        create_section_description: form.createSectionDescription.trim(),
        features: cleanedList(form.featureItems),
        feature_items: cleanedList(form.featureItems),
        trust_items: cleanedList(form.trustItems),
        faq_items: form.faqItems.map((item, index) => ({
          id: item.id.trim() || `faq-${index + 1}`,
          question: item.question.trim(),
          answer: item.answer.trim(),
        })).filter((item) => item.question && item.answer),
        review_rating: form.reviewRating.trim(),
        review_count_label: form.reviewCountLabel.trim(),
        delivery_note: form.deliveryNote.trim(),
        preview_note: form.previewNote.trim(),
        seo_title: form.seoTitle.trim(),
        seo_description: form.seoDescription.trim(),
        seo_keywords: csvToList(form.seoKeywords),
        seo_image: form.seoImage.trim(),
        seo_canonical_path: form.seoCanonicalPath.trim(),
      };
      cleanupEmptyFields(nextItem, [
        "slug",
        "description",
        "imageSrc",
        "cta_label",
        "create_section_title",
        "create_section_description",
        "review_rating",
        "review_count_label",
        "delivery_note",
        "preview_note",
        "seo_title",
        "seo_description",
        "seo_image",
        "seo_canonical_path",
      ]);
      if (!nextItem.hero_images?.length) delete nextItem.hero_images;
      if (!nextItem.features?.length) delete nextItem.features;
      if (!nextItem.feature_items?.length) delete nextItem.feature_items;
      if (!nextItem.trust_items?.length) delete nextItem.trust_items;
      if (!nextItem.faq_items?.length) delete nextItem.faq_items;
      if (!nextItem.seo_keywords?.length) delete nextItem.seo_keywords;

      if (currentIndex >= 0) items[currentIndex] = nextItem;
      else items.push(nextItem);

      const checkoutOptions = form.checkoutOptions
        .map((option) => ({
          id: option.id.trim().toLowerCase(),
          label: option.label.trim(),
          description: option.description.trim(),
        }))
        .filter((option) => option.id && option.label);
      if (!checkoutOptions.length) throw new Error("At least one checkout option is required");

      product.items = items;
      product.default_item_id = selectedItemId ? product.default_item_id || selectedItemId : itemId;
      product.catalog = {
        ...(product.catalog || {}),
        allowed_countries: form.enabledCountries,
        prices: buildPricesPayload(form.prices),
      };
      product.checkout_options = checkoutOptions;
      products[productType] = product;

      await saveProducts({ ...content, products });
      setStatus(`Saved draft for ${productType}/${itemId}.`);
      await loadProducts(productType, itemId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save item");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!content || !selectedItemId || !activeProduct) return;
    if (!window.confirm(`Delete item '${selectedItemId}' from ${productType}?`)) return;
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const products = { ...(content.products || {}) };
      const product = { ...(products[productType] || {}) } as ProductConfig;
      product.items = (product.items || []).filter((item) => String(item.id || "").trim().toLowerCase() !== selectedItemId);
      if (String(product.default_item_id || "").trim().toLowerCase() === selectedItemId) {
        product.default_item_id = String(product.items?.[0]?.id || "");
      }
      products[productType] = product;
      await saveProducts({ ...content, products });
      setStatus(`Deleted ${productType}/${selectedItemId}.`);
      await loadProducts(productType);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete item");
    } finally {
      setSaving(false);
    }
  }

  async function saveProducts(nextContent: ProductsContent) {
    const res = await fetch(`${API_BASE}/api/admin/product-config/products`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ content: nextContent }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    setConfigStatus((data.status || null) as ConfigStatus | null);
  }

  async function publishDraft() {
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/product-config/products/publish`, {
        method: "POST",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setConfigStatus((data.status || null) as ConfigStatus | null);
      setStatus("Published draft to live products.json.");
      await loadProducts(productType, selectedItemId || form?.itemId || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to publish draft");
    } finally {
      setSaving(false);
    }
  }

  async function discardDraft() {
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/product-config/products/draft`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setConfigStatus((data.status || null) as ConfigStatus | null);
      setStatus("Discarded products draft and reloaded live config.");
      await loadProducts(productType, selectedItemId || form?.itemId || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to discard draft");
    } finally {
      setSaving(false);
    }
  }

  async function uploadOne(assetKind: "main_image" | "gallery_image" | "preview_layout", file: File) {
    if (!form?.itemId.trim()) throw new Error("Enter an item id before uploading assets");
    const body = new FormData();
    body.append("product_id", productType);
    body.append("item_id", form.itemId.trim());
    body.append("asset_kind", assetKind);
    body.append("file", file);
    const res = await fetch(`${API_BASE}/api/admin/non-story-manager/upload`, { method: "POST", headers: authHeaders(), body });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return String(data.public_path || "");
  }

  async function handleMainImageUpload() {
    if (!mainImageFile) return;
    setUploading("main_image");
    try {
      const path = await uploadOne("main_image", mainImageFile);
      setField("imageSrc", path);
      setStatus(`Uploaded ${mainImageFile.name}.`);
      setMainImageFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload image");
    } finally {
      setUploading("");
    }
  }

  async function handleGalleryUpload() {
    if (!galleryFiles.length) return;
    setUploading("gallery_image");
    try {
      const uploaded: string[] = [];
      for (const file of galleryFiles) uploaded.push(await uploadOne("gallery_image", file));
      setForm((prev) => (prev ? { ...prev, heroImages: [...prev.heroImages, ...uploaded] } : prev));
      setStatus(`Uploaded ${galleryFiles.length} gallery image(s).`);
      setGalleryFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload gallery images");
    } finally {
      setUploading("");
    }
  }

  async function handleGalleryReplace(index: number, file: File | null) {
    if (!file) return;
    setUploading(`gallery-replace-${index}`);
    setError("");
    setStatus("");
    try {
      const path = await uploadOne("gallery_image", file);
      setForm((prev) => {
        if (!prev) return prev;
        const heroImages = [...prev.heroImages];
        heroImages[index] = path;
        return { ...prev, heroImages };
      });
      setStatus(`Replaced gallery image ${index + 1}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to replace gallery image");
    } finally {
      setUploading("");
    }
  }

  function moveGalleryImage(index: number, direction: -1 | 1) {
    setForm((prev) => {
      if (!prev) return prev;
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= prev.heroImages.length) return prev;
      const heroImages = [...prev.heroImages];
      [heroImages[index], heroImages[nextIndex]] = [heroImages[nextIndex], heroImages[index]];
      return { ...prev, heroImages };
    });
  }

  async function handleLayoutUpload() {
    if (!layoutFiles.length) return;
    setUploading("preview_layout");
    try {
      for (const file of layoutFiles) await uploadOne("preview_layout", file);
      setStatus(`Uploaded ${layoutFiles.length} preview layout file(s).`);
      setLayoutFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload preview layout");
    } finally {
      setUploading("");
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Frame & Sticker Manager</h1>
          <p className="text-sm text-slate-600">Non-technical manager for frame and sticker items backed by `products.json`.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700">Product Type</label>
              <select value={productType} onChange={(e) => selectProduct(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                {productEntries.map(([id, product]) => <option key={id} value={id}>{product.title || id}</option>)}
              </select>
            </div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-slate-900">Items</h2>
              <button type="button" onClick={startNewItem} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">New Item</button>
            </div>
            <div className="space-y-2">
              {itemEntries.map(([id, item]) => (
                <button key={id} type="button" onClick={() => selectItem(id)} className={`w-full rounded-xl border px-4 py-3 text-left ${selectedItemId === id ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-900 hover:border-slate-300"}`}>
                  <div className="text-sm font-medium">{item.title || id}</div>
                  <div className={`mt-1 text-xs ${selectedItemId === id ? "text-slate-200" : "text-slate-500"}`}>{id}</div>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            {loading || !form ? <p className="text-sm text-slate-500">Loading manager...</p> : (
              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-medium text-slate-900">{selectedItemId ? `Edit ${selectedItemId}` : `Create ${productType} item`}</h2>
                      <p className="text-sm text-slate-600">Uploads and edits save into `products.draft.json`. Publish when the draft is finalized.</p>
                    </div>
                    <div className="flex gap-2">
                      {draftPreviewPath ? (
                        <a
                          href={configStatus?.has_draft ? draftPreviewPath : "#"}
                          target={configStatus?.has_draft ? "_blank" : undefined}
                          rel={configStatus?.has_draft ? "noreferrer" : undefined}
                          aria-disabled={!configStatus?.has_draft}
                          onClick={(event) => {
                            if (!configStatus?.has_draft) {
                              event.preventDefault();
                              setStatus("Save Draft first, then Preview Draft will show the saved draft changes.");
                            }
                          }}
                          className={`rounded-lg border px-4 py-2 text-sm ${configStatus?.has_draft ? "border-slate-300 text-slate-700 hover:bg-slate-50" : "border-slate-200 text-slate-400"}`}
                        >
                          Preview Draft
                        </a>
                      ) : null}
                      {publicItemPath ? <a href={publicItemPath} target="_blank" rel="noreferrer" className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">View Live</a> : null}
                      {configStatus?.has_draft ? <button type="button" onClick={() => void discardDraft()} disabled={saving} className="rounded-lg border border-amber-300 px-4 py-2 text-sm text-amber-700 hover:bg-amber-50 disabled:opacity-60">Discard Draft</button> : null}
                      <button type="button" onClick={() => void publishDraft()} disabled={saving || !configStatus?.has_draft} className="rounded-lg border border-green-300 px-4 py-2 text-sm text-green-700 hover:bg-green-50 disabled:opacity-60">Publish Draft</button>
                      {selectedItemId ? <button type="button" onClick={handleDelete} disabled={saving} className="rounded-lg border border-red-300 px-4 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-60">Delete</button> : null}
                      <button type="button" onClick={() => void handleSave()} disabled={saving} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60">{saving ? "Saving..." : "Save Draft"}</button>
                    </div>
                  </div>

                  {error ? <p className="text-sm text-red-600">{error}</p> : null}
                  {status ? <p className="text-sm text-green-700">{status}</p> : null}
                  {configStatus ? <p className="text-xs text-slate-500">Draft mode: {configStatus.has_draft ? `active, last updated ${formatTimestamp(configStatus.draft_updated_at)}` : "no draft file yet, showing live config as the starting point."}</p> : null}
                </div>

                <CompactStatusSummary
                  checking={checking}
                  checks={checks}
                  open={statusPanelOpen}
                  onToggle={() => setStatusPanelOpen((prev) => !prev)}
                />

                {statusPanelOpen ? (
                  <TopStatusPanel
                    title="Pending Checks"
                    checking={checking}
                    checks={checks}
                    tips={[
                      "Validation is read-only. Use it as a publish-readiness checklist.",
                      "Open Product Page Gallery and click Change Images to replace, move, remove, or add images.",
                      "Save Section keeps changes on the page. Save Draft writes them to the draft JSON file.",
                    ]}
                    emptyLabel="No validation messages yet."
                  />
                ) : null}

                {isCreatingNewItem ? (
                  <div className="space-y-4">
                    <CreateModeSteps
                      title="New Item Setup"
                      steps={[
                        "Basic Info",
                        "Media",
                        "Product Copy",
                        "SEO",
                        "Pricing",
                        "Save Draft",
                        "Preview Draft",
                      ]}
                      note="Follow the steps in order. Preview Draft only shows the last saved draft."
                    />
                    <CreateModeNotice
                      title="Create Mode"
                      message="You are creating a brand-new item. Fill the open sections below, save the draft, then preview the saved result."
                    />
                  </div>
                ) : (
                <SectionCard
                  title="Current Page Snapshot"
                  description="This shows the currently loaded frame or sticker content before you start editing fields."
                  summary={sectionSummaries?.overview || ""}
                  expanded={expandedSections.overview}
                  onToggle={() => toggleSection("overview")}
                >
                  <div className="grid gap-4 md:grid-cols-2">
                    <InfoBlock label="Public URL" value={publicItemPath || "Not available until an item id is set"} />
                    <InfoBlock label="Draft Preview URL" value={draftPreviewPath || "Not available until an item id is set"} />
                    <InfoBlock label="Enabled Countries" value={form.enabledCountries.length ? form.enabledCountries.join(", ") : "None"} />
                    <InfoBlock label="Checkout Options" value={form.checkoutOptions.length ? form.checkoutOptions.map((item) => item.label || item.id).join(", ") : "None"} />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <ImagePreviewCard title="Current Main Image" path={form.imageSrc} />
                    <ImagePreviewCard title="Current SEO Share Image" path={form.seoImage} />
                  </div>
                  <ImagePreviewGrid title="Current Gallery Images" paths={form.heroImages} actionLabel="Edit Gallery" onAction={jumpToGalleryEditor} />
                  <div className="grid gap-6 xl:grid-cols-2">
                    <TextListCard title="Current Feature Bullets" items={form.featureItems} emptyLabel="No feature bullets configured." />
                    <TextListCard title="Current Trust Badges" items={form.trustItems} emptyLabel="No trust items configured." />
                  </div>
                  <FaqPreviewCard items={form.faqItems} />
                </SectionCard>
                )}

                <SectionCard
                  title="Basic Product Info"
                  description="Item-specific fields shown in the non-story product page."
                  summary={sectionSummaries?.basic || ""}
                  dirty={sectionDirty.basic}
                  expanded={expandedSections.basic}
                  editing={editingSection === "basic"}
                  actionLabel="Change Text"
                  actionDisabled={Boolean(editingSection && editingSection !== "basic")}
                  onToggle={() => toggleSection("basic")}
                  onEdit={() => beginSectionEdit("basic")}
                  onSave={() => saveSectionEdit("basic")}
                  onCancel={() => cancelSectionEdit("basic")}
                >
                  <fieldset disabled={editingSection !== "basic"} className="space-y-4 disabled:opacity-80">
                    <div className="grid gap-4 md:grid-cols-2">
                      <Field label="Item Id" value={form.itemId} onChange={(v) => setField("itemId", v)} disabled={Boolean(selectedItemId) || editingSection !== "basic"} help={selectedItemId ? "Existing item ids are locked here." : "Lowercase id used in URLs and asset folders."} />
                      <Field label="Slug" value={form.slug} onChange={(v) => setField("slug", v)} disabled={editingSection !== "basic"} help="Optional public URL slug, like personalized-photo-frame. Leave blank to keep using the item id." />
                      <Field label="Title" value={form.title} onChange={(v) => setField("title", v)} disabled={editingSection !== "basic"} />
                      <Field label="Main Image Path" value={form.imageSrc} onChange={(v) => setField("imageSrc", v)} disabled={editingSection !== "basic"} />
                      <ToggleField label="Enabled" checked={form.enabled} onChange={(checked) => setField("enabled", checked)} disabled={editingSection !== "basic"} />
                    </div>
                    <Area label="Description" value={form.description} onChange={(v) => setField("description", v)} disabled={editingSection !== "basic"} />
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="Product Page Copy"
                  description="CTA, support text, review text, and create-section copy."
                  summary={sectionSummaries?.copy || ""}
                  dirty={sectionDirty.copy}
                  expanded={expandedSections.copy}
                  editing={editingSection === "copy"}
                  actionLabel="Change Text"
                  actionDisabled={Boolean(editingSection && editingSection !== "copy")}
                  onToggle={() => toggleSection("copy")}
                  onEdit={() => beginSectionEdit("copy")}
                  onSave={() => saveSectionEdit("copy")}
                  onCancel={() => cancelSectionEdit("copy")}
                >
                  <fieldset disabled={editingSection !== "copy"} className="space-y-4 disabled:opacity-80">
                    <div className="grid gap-4 md:grid-cols-2">
                      <Field label="CTA Label" value={form.ctaLabel} onChange={(v) => setField("ctaLabel", v)} disabled={editingSection !== "copy"} />
                      <Field label="Review Rating" value={form.reviewRating} onChange={(v) => setField("reviewRating", v)} disabled={editingSection !== "copy"} />
                      <Field label="Review Count Label" value={form.reviewCountLabel} onChange={(v) => setField("reviewCountLabel", v)} disabled={editingSection !== "copy"} />
                      <Field label="Delivery Note" value={form.deliveryNote} onChange={(v) => setField("deliveryNote", v)} disabled={editingSection !== "copy"} />
                      <Field label="Preview Note" value={form.previewNote} onChange={(v) => setField("previewNote", v)} disabled={editingSection !== "copy"} />
                      <Field label="Create Section Title" value={form.createSectionTitle} onChange={(v) => setField("createSectionTitle", v)} disabled={editingSection !== "copy"} />
                    </div>
                    <Area label="Create Section Description" value={form.createSectionDescription} onChange={(v) => setField("createSectionDescription", v)} disabled={editingSection !== "copy"} />
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="SEO"
                  description="Page-level SEO and share settings for this item."
                  summary={sectionSummaries?.seo || ""}
                  dirty={sectionDirty.seo}
                  expanded={expandedSections.seo}
                  editing={editingSection === "seo"}
                  actionLabel="Edit SEO"
                  actionDisabled={Boolean(editingSection && editingSection !== "seo")}
                  onToggle={() => toggleSection("seo")}
                  onEdit={() => beginSectionEdit("seo")}
                  onSave={() => saveSectionEdit("seo")}
                  onCancel={() => cancelSectionEdit("seo")}
                >
                  <fieldset disabled={editingSection !== "seo"} className="space-y-4 disabled:opacity-80">
                    <div className="grid gap-4 md:grid-cols-2">
                      <Field label="SEO Title" value={form.seoTitle} onChange={(v) => setField("seoTitle", v)} disabled={editingSection !== "seo"} />
                      <Field label="SEO Image Path" value={form.seoImage} onChange={(v) => setField("seoImage", v)} disabled={editingSection !== "seo"} />
                      <Field label="Canonical Path" value={form.seoCanonicalPath} onChange={(v) => setField("seoCanonicalPath", v)} disabled={editingSection !== "seo"} help="Optional override. If blank, SEO uses /products/{type}/{slug-or-item-id}." />
                      <Field label="SEO Keywords" value={form.seoKeywords} onChange={(v) => setField("seoKeywords", v)} disabled={editingSection !== "seo"} help="Comma separated." />
                    </div>
                    <Area label="SEO Description" value={form.seoDescription} onChange={(v) => setField("seoDescription", v)} disabled={editingSection !== "seo"} />
                    <ImagePreviewCard title="SEO Share Image" path={form.seoImage} />
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="Media"
                  description="Upload and preview current item image, gallery images, and preview-layout files."
                  summary={sectionSummaries?.media || ""}
                  dirty={sectionDirty.media}
                  expanded={expandedSections.media}
                  editing={editingSection === "media"}
                  actionLabel="Change Images"
                  actionDisabled={Boolean(editingSection && editingSection !== "media")}
                  onToggle={() => toggleSection("media")}
                  onEdit={() => beginSectionEdit("media")}
                  onSave={() => saveSectionEdit("media")}
                  onCancel={() => cancelSectionEdit("media")}
                >
                  <fieldset disabled={editingSection !== "media"} className="space-y-4 disabled:opacity-80">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-sm font-medium text-slate-900">Main Image Upload</div>
                        <input type="file" onChange={(e) => setMainImageFile((e.target.files || [])[0] || null)} className="mt-3 w-full text-sm" />
                        {mainImageFile ? <p className="mt-2 text-xs text-slate-500">{mainImageFile.name}</p> : null}
                        <button type="button" disabled={!mainImageFile || uploading === "main_image"} onClick={() => void handleMainImageUpload()} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">{uploading === "main_image" ? "Uploading..." : "Upload Main Image"}</button>
                      </div>
                      <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-sm font-medium text-slate-900">Gallery Upload</div>
                        <input type="file" multiple onChange={(e) => setGalleryFiles(Array.from(e.target.files || []))} className="mt-3 w-full text-sm" />
                        <button type="button" disabled={!galleryFiles.length || uploading === "gallery_image"} onClick={() => void handleGalleryUpload()} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">{uploading === "gallery_image" ? "Uploading..." : "Upload Gallery Images"}</button>
                      </div>
                      <ImagePreviewCard title="Current Main Image" path={form.imageSrc} />
                      <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-sm font-medium text-slate-900">Preview Layout Upload</div>
                        <p className="mt-1 text-xs text-slate-500">{productType === "frame" ? "Upload frontcover.png." : "Upload pg1.png and additional pg*.png files if needed."}</p>
                        <input type="file" multiple onChange={(e) => setLayoutFiles(Array.from(e.target.files || []))} className="mt-3 w-full text-sm" />
                        <button type="button" disabled={!layoutFiles.length || uploading === "preview_layout"} onClick={() => void handleLayoutUpload()} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">{uploading === "preview_layout" ? "Uploading..." : "Upload Preview Layout Files"}</button>
                      </div>
                    </div>
                  </fieldset>
                </SectionCard>

                <div ref={gallerySectionRef}>
                <SectionCard
                  title="Product Page Gallery"
                  description="Used by the non-story product page carousel."
                  summary={sectionSummaries?.gallery || ""}
                  dirty={sectionDirty.gallery}
                  expanded={expandedSections.gallery}
                  editing={editingSection === "gallery"}
                  actionLabel="Change Images"
                  actionDisabled={Boolean(editingSection && editingSection !== "gallery")}
                  onToggle={() => toggleSection("gallery")}
                  onEdit={() => beginSectionEdit("gallery")}
                  onSave={() => saveSectionEdit("gallery")}
                  onCancel={() => cancelSectionEdit("gallery")}
                >
                  <fieldset disabled={editingSection !== "gallery"} className="space-y-4 disabled:opacity-80">
                    <GalleryEditor
                      items={form.heroImages}
                      emptyLabel="No gallery images configured."
                      onChange={(index, value) => updateListField("heroImages", index, value)}
                      onAdd={() => addListField("heroImages")}
                      onRemove={(index) => removeListField("heroImages", index)}
                      onMove={moveGalleryImage}
                      onReplace={(index, file) => void handleGalleryReplace(index, file)}
                      uploadingKey={uploading}
                      disabled={editingSection !== "gallery"}
                    />
                    <div className="mt-4"><ImagePreviewGrid title="Current Gallery Images" paths={form.heroImages} /></div>
                  </fieldset>
                </SectionCard>
                </div>

                <div className="grid gap-6 xl:grid-cols-2">
                  <SectionCard
                    title="Feature Bullets"
                    description="Shown near the top of the product page."
                    summary={sectionSummaries?.features || ""}
                    dirty={sectionDirty.features}
                    expanded={expandedSections.features}
                    editing={editingSection === "features"}
                    actionLabel="Change Text"
                    actionDisabled={Boolean(editingSection && editingSection !== "features")}
                    onToggle={() => toggleSection("features")}
                    onEdit={() => beginSectionEdit("features")}
                    onSave={() => saveSectionEdit("features")}
                    onCancel={() => cancelSectionEdit("features")}
                  >
                    <fieldset disabled={editingSection !== "features"} className="disabled:opacity-80">
                      <ListEditor items={form.featureItems} addLabel="Add Feature" emptyLabel="No custom feature bullets." onChange={(index, value) => updateListField("featureItems", index, value)} onAdd={() => addListField("featureItems")} onRemove={(index) => removeListField("featureItems", index)} disabled={editingSection !== "features"} />
                    </fieldset>
                  </SectionCard>
                  <SectionCard
                    title="Trust Badges"
                    description="Shown in the trust strip under the CTA."
                    summary={sectionSummaries?.trust || ""}
                    dirty={sectionDirty.trust}
                    expanded={expandedSections.trust}
                    editing={editingSection === "trust"}
                    actionLabel="Change Text"
                    actionDisabled={Boolean(editingSection && editingSection !== "trust")}
                    onToggle={() => toggleSection("trust")}
                    onEdit={() => beginSectionEdit("trust")}
                    onSave={() => saveSectionEdit("trust")}
                    onCancel={() => cancelSectionEdit("trust")}
                  >
                    <fieldset disabled={editingSection !== "trust"} className="disabled:opacity-80">
                      <ListEditor items={form.trustItems} addLabel="Add Trust Item" emptyLabel="No custom trust items." onChange={(index, value) => updateListField("trustItems", index, value)} onAdd={() => addListField("trustItems")} onRemove={(index) => removeListField("trustItems", index)} disabled={editingSection !== "trust"} />
                    </fieldset>
                  </SectionCard>
                </div>

                <SectionCard
                  title="FAQ Items"
                  description="Accordion content on the product page."
                  summary={sectionSummaries?.faq || ""}
                  dirty={sectionDirty.faq}
                  expanded={expandedSections.faq}
                  editing={editingSection === "faq"}
                  actionLabel="Edit FAQ"
                  actionDisabled={Boolean(editingSection && editingSection !== "faq")}
                  onToggle={() => toggleSection("faq")}
                  onEdit={() => beginSectionEdit("faq")}
                  onSave={() => saveSectionEdit("faq")}
                  onCancel={() => cancelSectionEdit("faq")}
                >
                  <fieldset disabled={editingSection !== "faq"} className="space-y-4 disabled:opacity-80">
                    <div className="space-y-4">
                      {form.faqItems.map((item, index) => (
                        <div key={`faq-${index}`} className="rounded-xl border border-slate-200 p-4">
                          <div className="grid gap-3 md:grid-cols-2">
                            <Field label="FAQ Id" value={item.id} onChange={(v) => updateFaq(index, "id", v)} disabled={editingSection !== "faq"} />
                            <Field label="Question" value={item.question} onChange={(v) => updateFaq(index, "question", v)} disabled={editingSection !== "faq"} />
                          </div>
                          <Area label="Answer" value={item.answer} onChange={(v) => updateFaq(index, "answer", v)} disabled={editingSection !== "faq"} />
                          <button type="button" onClick={() => removeFaq(index)} className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50">Remove FAQ</button>
                        </div>
                      ))}
                      <button type="button" onClick={addFaq} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">Add FAQ</button>
                    </div>
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="Country Availability & Pricing"
                  description="These settings are saved at product level for all items within the current product type."
                  summary={sectionSummaries?.pricing || ""}
                  dirty={sectionDirty.pricing}
                  expanded={expandedSections.pricing}
                  editing={editingSection === "pricing"}
                  actionLabel="Edit Pricing"
                  actionDisabled={Boolean(editingSection && editingSection !== "pricing")}
                  onToggle={() => toggleSection("pricing")}
                  onEdit={() => beginSectionEdit("pricing")}
                  onSave={() => saveSectionEdit("pricing")}
                  onCancel={() => cancelSectionEdit("pricing")}
                >
                  <fieldset disabled={editingSection !== "pricing"} className="space-y-4 disabled:opacity-80">
                    <div className="grid gap-3 md:grid-cols-3">
                      {countryEntries.map(([countryCode]) => (
                        <label key={String(countryCode)} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                          <input type="checkbox" checked={form.enabledCountries.includes(String(countryCode))} onChange={() => toggleCountry(String(countryCode))} />
                          <span>{String(countryCode)}</span>
                        </label>
                      ))}
                    </div>
                    <div className="mt-5 space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-semibold text-slate-900">Checkout Options</div>
                        <button type="button" onClick={addOption} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">Add Option</button>
                      </div>
                      {form.checkoutOptions.map((option, index) => (
                        <div key={`${option.id || "option"}-${index}`} className="rounded-xl border border-slate-200 p-4">
                          <div className="grid gap-3 md:grid-cols-3">
                            <Field label="Option Id" value={option.id} onChange={(v) => updateOption(index, "id", v)} disabled={editingSection !== "pricing"} />
                            <Field label="Label" value={option.label} onChange={(v) => updateOption(index, "label", v)} disabled={editingSection !== "pricing"} />
                            <Field label="Description" value={option.description} onChange={(v) => updateOption(index, "description", v)} disabled={editingSection !== "pricing"} />
                          </div>
                          <button type="button" onClick={() => removeOption(index)} className="mt-3 rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50">Remove Option</button>
                        </div>
                      ))}
                    </div>
                    <div className="mt-5 space-y-5">
                      {form.enabledCountries.map((countryCode) => (
                        <div key={countryCode} className="rounded-xl border border-slate-200 p-4">
                          <div className="mb-3 text-sm font-semibold text-slate-900">{countryCode}</div>
                          <div className="space-y-4">
                            {form.checkoutOptions.map((option) => (
                              <div key={`${countryCode}-${option.id}`} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                                <div className="mb-2 text-sm font-medium text-slate-900">{option.label || option.id || "Option"}</div>
                                <div className="grid gap-3 md:grid-cols-3">
                                  <Field label="Price" value={form.prices[countryCode]?.[option.id]?.price || ""} onChange={(v) => updatePrice(countryCode, option.id, "price", v)} disabled={editingSection !== "pricing"} />
                                  <Field label="Shipping" value={form.prices[countryCode]?.[option.id]?.shipping || ""} onChange={(v) => updatePrice(countryCode, option.id, "shipping", v)} disabled={editingSection !== "pricing"} />
                                  <Field label="Taxes" value={form.prices[countryCode]?.[option.id]?.taxes || ""} onChange={(v) => updatePrice(countryCode, option.id, "taxes", v)} disabled={editingSection !== "pricing"} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </fieldset>
                </SectionCard>
              </div>
            )}
          </section>

        </div>
      </div>
    </div>
  );
}

function buildEmptyForm(product?: ProductConfig): ProductForm {
  const countries = Array.isArray(product?.catalog?.allowed_countries) ? product?.catalog?.allowed_countries || [] : [];
  const options = Array.isArray(product?.checkout_options) ? product?.checkout_options || [] : [];
  const prices: Record<string, Record<string, PriceFields>> = {};
  countries.forEach((countryCode) => {
    prices[countryCode] = {};
    options.forEach((option) => {
      prices[countryCode][String(option.id || "").trim().toLowerCase()] = { ...EMPTY_PRICE };
    });
  });
  return {
    itemId: "",
    slug: "",
    enabled: true,
    title: "",
    description: "",
    imageSrc: "",
    heroImages: [],
    ctaLabel: "",
    createSectionTitle: "",
    createSectionDescription: "",
    featureItems: [],
    trustItems: [],
    faqItems: [],
    reviewRating: "",
    reviewCountLabel: "",
    deliveryNote: "",
    previewNote: "",
    seoTitle: "",
    seoDescription: "",
    seoKeywords: "",
    seoImage: "",
    seoCanonicalPath: "",
    enabledCountries: [...countries],
    checkoutOptions: options.map((option) => ({
      id: String(option.id || ""),
      label: String(option.label || ""),
      description: String(option.description || ""),
    })),
    prices,
  };
}

function buildForm(productType: string, itemId: string, content: ProductsContent): ProductForm {
  const product = content.products?.[productType];
  const empty = buildEmptyForm(product);
  const item = (product?.items || []).find((entry) => String(entry.id || "").trim().toLowerCase() === itemId) || {};
  const prices = { ...empty.prices };
  Object.entries(product?.catalog?.prices || {}).forEach(([countryCode, optionMap]) => {
    prices[countryCode] = { ...(prices[countryCode] || {}) };
    Object.entries(optionMap || {}).forEach(([optionId, fields]) => {
      prices[countryCode][optionId] = {
        price: String(fields?.price || ""),
        shipping: String(fields?.shipping || ""),
        taxes: String(fields?.taxes || ""),
      };
    });
  });
  return {
    itemId: String(item.id || ""),
    slug: String(item.slug || ""),
    enabled: Boolean(item.enabled ?? true),
    title: String(item.title || ""),
    description: String(item.description || ""),
    imageSrc: String(item.imageSrc || ""),
    heroImages: Array.isArray(item.hero_images) ? item.hero_images.map((entry) => String(entry || "")) : [],
    ctaLabel: String(item.cta_label || ""),
    createSectionTitle: String(item.create_section_title || ""),
    createSectionDescription: String(item.create_section_description || ""),
    featureItems: Array.isArray(item.feature_items)
      ? item.feature_items.map((entry) => String(entry || ""))
      : Array.isArray(item.features)
      ? item.features.map((entry) => String(entry || ""))
      : [],
    trustItems: Array.isArray(item.trust_items) ? item.trust_items.map((entry) => String(entry || "")) : [],
    faqItems: Array.isArray(item.faq_items)
      ? item.faq_items.map((entry, index) => ({
          id: String(entry?.id || `faq-${index + 1}`),
          question: String(entry?.question || ""),
          answer: String(entry?.answer || ""),
        }))
      : [],
    reviewRating: String(item.review_rating || ""),
    reviewCountLabel: String(item.review_count_label || ""),
    deliveryNote: String(item.delivery_note || ""),
    previewNote: String(item.preview_note || ""),
    seoTitle: String(item.seo_title || ""),
    seoDescription: String(item.seo_description || ""),
    seoKeywords: Array.isArray(item.seo_keywords) ? item.seo_keywords.join(", ") : "",
    seoImage: String(item.seo_image || ""),
    seoCanonicalPath: String(item.seo_canonical_path || ""),
    enabledCountries: Array.isArray(product?.catalog?.allowed_countries) ? product?.catalog?.allowed_countries || [] : [],
    checkoutOptions: Array.isArray(product?.checkout_options)
      ? product.checkout_options.map((option) => ({
          id: String(option.id || ""),
          label: String(option.label || ""),
          description: String(option.description || ""),
        }))
      : [],
    prices,
  };
}

function buildPricesPayload(prices: Record<string, Record<string, PriceFields>>) {
  const payload: Record<string, Record<string, PriceFields>> = {};
  Object.entries(prices).forEach(([countryCode, optionMap]) => {
    const cleanedOptions: Record<string, PriceFields> = {};
    Object.entries(optionMap || {}).forEach(([optionId, fields]) => {
      const next = {
        price: String(fields?.price || "").trim(),
        shipping: String(fields?.shipping || "").trim(),
        taxes: String(fields?.taxes || "").trim(),
      };
      if (next.price || next.shipping || next.taxes) cleanedOptions[optionId.trim().toLowerCase()] = next;
    });
    if (Object.keys(cleanedOptions).length > 0) payload[countryCode] = cleanedOptions;
  });
  return payload;
}

function csvToList(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function cleanedList(items: string[]) {
  return items.map((item) => item.trim()).filter(Boolean);
}

function cleanupEmptyFields(target: Record<string, unknown>, keys: string[]) {
  keys.forEach((key) => {
    if (!String(target[key] || "").trim()) delete target[key];
  });
}

function normalizeSlug(value?: string) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function buildNonStoryPublicPath(productType: string, itemId?: string, slug?: string) {
  const product = String(productType || "").trim().toLowerCase();
  const identifier = normalizeSlug(slug) || String(itemId || "").trim().toLowerCase();
  return product && identifier ? `http://localhost:3000/products/${product}/${identifier}` : "";
}

function buildNonStoryDraftPreviewPath(productType: string, itemId?: string) {
  const product = String(productType || "").trim().toLowerCase();
  const id = String(itemId || "").trim().toLowerCase();
  return product && id ? `http://localhost:3000/child-details?product=${encodeURIComponent(product)}&product_item_id=${encodeURIComponent(id)}&draft=1` : "";
}

function formatTimestamp(value?: string | null) {
  const text = String(value || "").trim();
  if (!text) return "unknown";
  const date = new Date(text);
  return Number.isNaN(date.getTime()) ? text : date.toLocaleString();
}

function SectionCard({
  title,
  description,
  summary,
  dirty,
  expanded,
  editing,
  actionLabel,
  actionDisabled,
  onToggle,
  onEdit,
  onSave,
  onCancel,
  children,
}: {
  title: string;
  description: string;
  summary?: string;
  dirty?: boolean;
  expanded: boolean;
  editing?: boolean;
  actionLabel?: string;
  actionDisabled?: boolean;
  onToggle: () => void;
  onEdit?: () => void;
  onSave?: () => void;
  onCancel?: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <button type="button" onClick={onToggle} className="text-left">
          <div className="text-sm font-semibold text-slate-900">{title}</div>
          <p className="mt-1 text-sm text-slate-600">{description}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {dirty ? <span className="rounded-full bg-amber-100 px-2 py-1 text-[11px] font-medium text-amber-800">Unsaved changes</span> : null}
            {summary ? <p className="text-xs text-slate-500">{summary}</p> : null}
          </div>
        </button>
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <button type="button" onClick={onCancel} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">Cancel</button>
              <button type="button" onClick={onSave} className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700">Save Section</button>
            </>
          ) : actionLabel && onEdit ? (
            <button type="button" onClick={onEdit} disabled={actionDisabled} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50">
              {actionLabel}
            </button>
          ) : null}
          <button type="button" onClick={onToggle} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">
            {expanded ? "Collapse" : "Expand"}
          </button>
        </div>
      </div>
      {expanded ? <div className="mt-4 space-y-4">{children}</div> : null}
    </div>
  );
}

function Field({ label, value, onChange, disabled, help }: { label: string; value: string; onChange: (value: string) => void; disabled?: boolean; help?: string }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <input value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 disabled:bg-slate-100" />
      {help ? <span className="mt-1 block text-xs text-slate-500">{help}</span> : null}
    </label>
  );
}

function Area({ label, value, onChange, disabled }: { label: string; value: string; onChange: (value: string) => void; disabled?: boolean }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <textarea value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} rows={4} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 disabled:bg-slate-100" />
    </label>
  );
}

function ToggleField({ label, checked, onChange, disabled }: { label: string; checked: boolean; onChange: (checked: boolean) => void; disabled?: boolean }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4 rounded border-slate-300 disabled:opacity-50" />
    </label>
  );
}

function ImagePreviewCard({ title, path }: { title: string; path?: string }) {
  const value = String(path || "").trim();
  const displayUrl = resolveAssetUrl(value);
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="text-sm font-medium text-slate-900">{title}</div>
      {!value ? <p className="mt-2 text-sm text-slate-500">No image selected.</p> : (
        <div className="mt-3 space-y-2">
          <img src={displayUrl} alt={title} className="h-40 w-full rounded-lg border border-slate-200 object-cover bg-slate-50" />
          <a href={displayUrl} target="_blank" rel="noreferrer" className="block break-all text-xs text-blue-700 underline">{value}</a>
        </div>
      )}
    </div>
  );
}

function ImagePreviewGrid({ title, paths, actionLabel, onAction }: { title: string; paths: string[]; actionLabel?: string; onAction?: () => void }) {
  const cleaned = cleanedList(paths);
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-medium text-slate-900">{title}</div>
        {actionLabel && onAction ? (
          <button type="button" onClick={onAction} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">
            {actionLabel}
          </button>
        ) : null}
      </div>
      {cleaned.length === 0 ? <p className="mt-2 text-sm text-slate-500">No gallery images configured.</p> : (
        <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {cleaned.map((item, index) => (
            <div key={`${item}-${index}`} className="rounded-lg border border-slate-200 p-2">
              <img src={resolveAssetUrl(item)} alt={`Gallery ${index + 1}`} className="h-32 w-full rounded-md object-cover bg-slate-50" />
              <a href={resolveAssetUrl(item)} target="_blank" rel="noreferrer" className="mt-2 block break-all text-[11px] text-blue-700 underline">{item}</a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  const linkable = value.startsWith("http://") || value.startsWith("https://");
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="text-sm font-medium text-slate-900">{label}</div>
      {linkable ? (
        <a href={value} target="_blank" rel="noreferrer" className="mt-2 block break-all text-sm text-blue-700 underline">
          {value}
        </a>
      ) : (
        <p className="mt-2 break-all text-sm text-slate-600">{value}</p>
      )}
    </div>
  );
}

function TextListCard({ title, items, emptyLabel }: { title: string; items: string[]; emptyLabel: string }) {
  const cleaned = cleanedList(items);
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="text-sm font-medium text-slate-900">{title}</div>
      {cleaned.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">{emptyLabel}</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {cleaned.map((item, index) => (
            <li key={`${title}-${index}`} className="rounded-md bg-slate-50 px-3 py-2">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function FaqPreviewCard({ items }: { items: FaqItemForm[] }) {
  const populated = items.filter((item) => item.question.trim() || item.answer.trim());
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="text-sm font-medium text-slate-900">Current FAQ Items</div>
      {populated.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No FAQs configured.</p>
      ) : (
        <div className="mt-3 space-y-3">
          {populated.map((item, index) => (
            <div key={`${item.id || "faq"}-${index}`} className="rounded-md bg-slate-50 px-3 py-3">
              <div className="text-xs uppercase tracking-wide text-slate-500">{item.id || `faq-${index + 1}`}</div>
              <div className="mt-1 text-sm font-medium text-slate-900">{item.question || "Untitled question"}</div>
              <p className="mt-1 text-sm text-slate-700">{item.answer || "No answer yet."}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ListEditor({
  items,
  addLabel,
  emptyLabel,
  onChange,
  onAdd,
  onRemove,
  disabled,
}: {
  items: string[];
  addLabel: string;
  emptyLabel: string;
  onChange: (index: number, value: string) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-3">
      {items.length === 0 ? <p className="text-sm text-slate-500">{emptyLabel}</p> : null}
      {items.map((item, index) => (
        <div key={`${addLabel}-${index}`} className="flex gap-2">
          <input value={item} disabled={disabled} onChange={(e) => onChange(index, e.target.value)} className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 disabled:bg-slate-100" />
          <button type="button" disabled={disabled} onClick={() => onRemove(index)} className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50">Remove</button>
        </div>
      ))}
      <button type="button" disabled={disabled} onClick={onAdd} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50">{addLabel}</button>
    </div>
  );
}

function GalleryEditor({
  items,
  emptyLabel,
  onChange,
  onAdd,
  onRemove,
  onMove,
  onReplace,
  uploadingKey,
  disabled,
}: {
  items: string[];
  emptyLabel: string;
  onChange: (index: number, value: string) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
  onMove: (index: number, direction: -1 | 1) => void;
  onReplace: (index: number, file: File | null) => void;
  uploadingKey: string;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-3">
      {items.length === 0 ? <p className="text-sm text-slate-500">{emptyLabel}</p> : null}
      {items.map((item, index) => (
        <div key={`gallery-item-${index}`} className="rounded-xl border border-slate-200 p-3">
          <div className="grid gap-3 lg:grid-cols-[180px_1fr]">
            {item.trim() ? (
              <img src={resolveAssetUrl(item)} alt={`Gallery ${index + 1}`} className="h-32 w-full rounded-lg border border-slate-200 object-cover bg-slate-50" />
            ) : (
              <div className="flex h-32 w-full items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-xs text-slate-500">
                No image path yet
              </div>
            )}
            <div className="space-y-3">
              <Field label={`Gallery Image ${index + 1}`} value={item} onChange={(value) => onChange(index, value)} disabled={disabled} />
              <div className="flex flex-wrap gap-2">
                <label className={`rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 ${disabled ? "opacity-50" : "cursor-pointer hover:bg-slate-50"}`}>
                  Replace
                  <input type="file" disabled={disabled} className="hidden" onChange={(e) => { void onReplace(index, (e.target.files || [])[0] || null); e.currentTarget.value = ""; }} />
                </label>
                <button type="button" disabled={disabled || index === 0} onClick={() => onMove(index, -1)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50">Move Up</button>
                <button type="button" disabled={disabled || index === items.length - 1} onClick={() => onMove(index, 1)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50">Move Down</button>
                <button type="button" disabled={disabled} onClick={() => onRemove(index)} className="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50">Remove</button>
                {uploadingKey === `gallery-replace-${index}` ? <span className="self-center text-xs text-slate-500">Uploading replacement...</span> : null}
              </div>
            </div>
          </div>
        </div>
      ))}
      <button type="button" disabled={disabled} onClick={onAdd} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50">Add Gallery Image</button>
    </div>
  );
}

function CreateModeNotice({ title, message }: { title: string; message: string }) {
  return (
    <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4">
      <div className="text-sm font-semibold text-slate-900">{title}</div>
      <p className="mt-2 text-sm text-slate-700">{message}</p>
    </div>
  );
}

function CreateModeSteps({ title, steps, note }: { title: string; steps: string[]; note: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-sm font-semibold text-slate-900">{title}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {steps.map((step, index) => (
          <div key={`${title}-step-${index}`} className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
            {index + 1}. {step}
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-500">{note}</p>
    </div>
  );
}

function CompactStatusSummary({
  checking,
  checks,
  open,
  onToggle,
}: {
  checking: boolean;
  checks: ValidationCheck[];
  open: boolean;
  onToggle: () => void;
}) {
  const counts = countCheckLevels(checks);
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-slate-900">Publish Readiness</div>
          <p className="mt-1 text-xs text-slate-500">Validation is view-only. Expand details only when needed.</p>
        </div>
        <button type="button" onClick={onToggle} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-white">
          {open ? "Hide Checks" : "View Checks"}
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <StatusBadge label="Errors" value={counts.error} tone="red" />
        <StatusBadge label="Warnings" value={counts.warning} tone="amber" />
        <StatusBadge label="Success" value={counts.success} tone="green" />
        {checking ? <span className="rounded-full bg-slate-200 px-3 py-1 text-slate-700">Checking...</span> : null}
      </div>
    </div>
  );
}

function TopStatusPanel({
  title,
  checking,
  checks,
  tips,
  emptyLabel,
}: {
  title: string;
  checking: boolean;
  checks: ValidationCheck[];
  tips: string[];
  emptyLabel: string;
}) {
  return (
    <aside className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-sm font-semibold text-slate-900">{title}</div>
      <p className="mt-1 text-xs text-slate-500">Visible here so editors can see pending issues before scrolling.</p>
      <div className="mt-3 space-y-2">
        {checking ? <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">Checking assets...</div> : null}
        {!checking && checks.length === 0 ? <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">{emptyLabel}</div> : null}
        {checks.map((check) => (
          <div key={check.code} className={`rounded-lg border px-3 py-2 text-sm ${checkClass(check.level)}`}>{check.message}</div>
        ))}
      </div>
      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">How Editing Works</div>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {tips.map((tip, index) => (
            <li key={`${title}-tip-${index}`}>{tip}</li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

function StatusBadge({ label, value, tone }: { label: string; value: number; tone: "red" | "amber" | "green" }) {
  const className =
    tone === "red"
      ? "bg-red-100 text-red-700"
      : tone === "amber"
        ? "bg-amber-100 text-amber-700"
        : "bg-green-100 text-green-700";
  return <span className={`rounded-full px-3 py-1 font-medium ${className}`}>{label}: {value}</span>;
}

function checkClass(level: ValidationCheck["level"]) {
  if (level === "error") return "border-red-200 bg-red-50 text-red-700";
  if (level === "warning") return "border-amber-200 bg-amber-50 text-amber-700";
  if (level === "success") return "border-green-200 bg-green-50 text-green-700";
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function resolveAssetUrl(path: string) {
  const value = String(path || "").trim();
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${STOREFRONT_BASE}${value.startsWith("/") ? value : `/${value}`}`;
}

function defaultExpandedSections(): Record<SectionId, boolean> {
  return {
    overview: true,
    basic: false,
    copy: false,
    seo: false,
    validation: false,
    media: false,
    gallery: false,
    features: false,
    trust: false,
    faq: false,
    pricing: false,
  };
}

function defaultCreateExpandedSections(): Record<SectionId, boolean> {
  return {
    ...defaultExpandedSections(),
    basic: true,
    copy: true,
    media: true,
    gallery: true,
    seo: true,
    pricing: true,
  };
}

function summarizeValues(values: string[], emptyLabel = "No details yet") {
  const cleaned = values.map((value) => value.trim()).filter(Boolean);
  return cleaned.length ? cleaned.slice(0, 3).join(" • ") : emptyLabel;
}

function cloneForm<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function countCheckLevels(checks: ValidationCheck[]) {
  return checks.reduce(
    (acc, check) => {
      acc[check.level] += 1;
      return acc;
    },
    { error: 0, warning: 0, success: 0, info: 0 }
  );
}

function defaultDirtySections(): Record<SectionId, boolean> {
  return {
    overview: false,
    basic: false,
    copy: false,
    seo: false,
    validation: false,
    media: false,
    gallery: false,
    features: false,
    trust: false,
    faq: false,
    pricing: false,
  };
}

function buildProductSectionDirtyMap(form: ProductForm, baseline: ProductForm): Record<SectionId, boolean> {
  const sections = defaultDirtySections();
  (Object.keys(sections) as SectionId[]).forEach((section) => {
    if (section === "overview" || section === "validation") return;
    sections[section] = JSON.stringify(getProductSectionValue(form, section)) !== JSON.stringify(getProductSectionValue(baseline, section));
  });
  return sections;
}

function getProductSectionValue(form: ProductForm, section: SectionId) {
  switch (section) {
    case "basic":
      return { itemId: form.itemId, slug: form.slug, enabled: form.enabled, title: form.title, imageSrc: form.imageSrc, description: form.description };
    case "copy":
      return { ctaLabel: form.ctaLabel, reviewRating: form.reviewRating, reviewCountLabel: form.reviewCountLabel, deliveryNote: form.deliveryNote, previewNote: form.previewNote, createSectionTitle: form.createSectionTitle, createSectionDescription: form.createSectionDescription };
    case "seo":
      return { seoTitle: form.seoTitle, seoDescription: form.seoDescription, seoKeywords: form.seoKeywords, seoImage: form.seoImage, seoCanonicalPath: form.seoCanonicalPath };
    case "media":
      return { imageSrc: form.imageSrc };
    case "gallery":
      return { heroImages: form.heroImages };
    case "features":
      return { featureItems: form.featureItems };
    case "trust":
      return { trustItems: form.trustItems };
    case "faq":
      return { faqItems: form.faqItems };
    case "pricing":
      return { enabledCountries: form.enabledCountries, checkoutOptions: form.checkoutOptions, prices: form.prices };
    default:
      return null;
  }
}
