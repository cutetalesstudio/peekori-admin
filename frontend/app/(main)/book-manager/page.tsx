"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const STOREFRONT_BASE = (process.env.NEXT_PUBLIC_STOREFRONT_BASE_URL || "http://localhost:3000").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";
const DEFAULT_STYLES = ["paperback", "hardcover"];
const EMPTY_PRICE = { price: "", shipping: "", taxes: "" };

type PriceFields = typeof EMPTY_PRICE;
type ValidationCheck = {
  level: "error" | "warning" | "success" | "info";
  code: string;
  message: string;
};
type CatalogBook = {
  bookKey?: string;
  slug?: string;
  title?: string;
  imageSrc?: string;
  hoverImageSrc?: string;
  age?: string;
  description?: string;
  category?: string[];
  hero_images?: string[];
  cta_label?: string;
  create_section_title?: string;
  create_section_description?: string;
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
  home_featured?: boolean;
  home_order?: number;
  prices?: Record<string, Record<string, PriceFields>>;
  [key: string]: unknown;
};
type CountryConfig = { currency?: string; allowed_books?: string[]; [key: string]: unknown };
type ConfigStatus = {
  has_draft?: boolean;
  live_updated_at?: string | null;
  draft_updated_at?: string | null;
};
type CatalogContent = {
  countries?: Record<string, CountryConfig>;
  normalization_rules?: Array<Record<string, unknown>>;
  books?: Record<string, CatalogBook>;
  [key: string]: unknown;
};
type FaqItemForm = { id: string; question: string; answer: string };
type BookForm = {
  bookKey: string;
  slug: string;
  title: string;
  imageSrc: string;
  hoverImageSrc: string;
  age: string;
  description: string;
  categories: string;
  enabledCountries: string[];
  prices: Record<string, Record<string, PriceFields>>;
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
  homeFeatured: boolean;
  homeOrder: string;
};
type SectionId =
  | "overview"
  | "basic"
  | "copy"
  | "seo"
  | "validation"
  | "countries"
  | "media"
  | "previewAssets"
  | "gallery"
  | "features"
  | "trust"
  | "faq"
  | "pricing";

export default function BookManagerPage() {
  const [catalog, setCatalog] = useState<CatalogContent | null>(null);
  const [selectedBookKey, setSelectedBookKey] = useState("");
  const [form, setForm] = useState<BookForm | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [configStatus, setConfigStatus] = useState<ConfigStatus | null>(null);
  const [checks, setChecks] = useState<ValidationCheck[]>([]);
  const [checking, setChecking] = useState(false);
  const [assetCountry, setAssetCountry] = useState("IN");
  const [sampleCountry, setSampleCountry] = useState("IN");
  const [sampleVariant, setSampleVariant] = useState("boy");
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [hoverFile, setHoverFile] = useState<File | null>(null);
  const [galleryFiles, setGalleryFiles] = useState<File[]>([]);
  const [layoutFiles, setLayoutFiles] = useState<File[]>([]);
  const [sampleFiles, setSampleFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState("");
  const [expandedSections, setExpandedSections] = useState<Record<SectionId, boolean>>(defaultExpandedSections());
  const [editingSection, setEditingSection] = useState<SectionId | null>(null);
  const [sectionSnapshot, setSectionSnapshot] = useState<BookForm | null>(null);
  const [loadedFormSnapshot, setLoadedFormSnapshot] = useState<BookForm | null>(null);
  const [statusPanelOpen, setStatusPanelOpen] = useState(false);
  const gallerySectionRef = useRef<HTMLDivElement | null>(null);

  const authHeaders = (): Record<string, string> => {
    if (typeof window === "undefined") return {};
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const countries = useMemo(() => Object.entries(catalog?.countries || {}), [catalog]);
  const bookEntries = useMemo(
    () => Object.entries(catalog?.books || {}).sort(([a], [b]) => a.localeCompare(b)),
    [catalog]
  );
  const styles = DEFAULT_STYLES;
  const publicStoryPath = useMemo(() => buildStorybookPublicPath(form?.bookKey, form?.slug), [form?.bookKey, form?.slug]);
  const customizeStoryPath = useMemo(() => (publicStoryPath ? `${publicStoryPath}/customize` : ""), [publicStoryPath]);
  const draftPreviewPath = useMemo(() => buildStorybookDraftPreviewPath(form?.bookKey), [form?.bookKey]);
  const isCreatingNewBook = !selectedBookKey;
  const sectionDirty = useMemo(() => {
    if (!form || !loadedFormSnapshot) return defaultDirtySections();
    return buildBookSectionDirtyMap(form, loadedFormSnapshot);
  }, [form, loadedFormSnapshot]);
  const sectionSummaries = useMemo(
    () =>
      form
        ? {
            overview: summarizeValues([form.title || form.bookKey || "No storybook selected", `${form.enabledCountries.length} countries`, `${cleanedList(form.heroImages).length} gallery images`]),
            basic: summarizeValues([
              form.title || "Untitled storybook",
              form.age || "Age not set",
              form.homeFeatured ? `Home order ${form.homeOrder || "auto"}` : "Not featured on home",
            ]),
            copy: summarizeValues([form.ctaLabel || "CTA not set", form.reviewCountLabel || "Review count not set", form.deliveryNote || "Delivery note not set"]),
            seo: summarizeValues([form.seoTitle || "SEO title not set", form.seoCanonicalPath || buildStorybookPublicPath(form.bookKey, form.slug) || "Canonical path pending"]),
            validation: summarizeValues(checks.slice(0, 2).map((check) => check.message), checking ? "Checking assets..." : "No validation messages yet"),
            countries: summarizeValues(form.enabledCountries, "No countries enabled"),
            media: summarizeValues([form.imageSrc || "No cover image", form.hoverImageSrc || "No hover image"]),
            previewAssets: summarizeValues([`Layout files pending`, `Sample preview country: ${sampleCountry}`, `Gallery uploads queued: ${galleryFiles.length}`]),
            gallery: summarizeValues(cleanedList(form.heroImages), "No gallery images"),
            features: summarizeValues(cleanedList(form.featureItems), "No feature bullets"),
            trust: summarizeValues(cleanedList(form.trustItems), "No trust badges"),
            faq: summarizeValues(form.faqItems.map((item) => item.question).filter(Boolean), "No FAQs"),
            pricing: summarizeValues(styles.map((style) => style), "No pricing styles"),
          }
        : null,
    [checks, checking, form, galleryFiles.length, sampleCountry, styles]
  );

  useEffect(() => {
    void loadCatalog();
  }, []);

  useEffect(() => {
    if (!form?.bookKey.trim()) {
      setChecks([]);
      return;
    }
    const timer = window.setTimeout(async () => {
      setChecking(true);
      try {
        const res = await fetch(`${API_BASE}/api/admin/book-manager/validate`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body: JSON.stringify({
            book_key: form.bookKey.trim(),
            image_src: form.imageSrc,
            hover_image_src: form.hoverImageSrc,
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
  }, [form]);

  async function loadCatalog(preferredBookKey?: string) {
    setLoading(true);
    setError("");
    setStatus("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/product-config/catalog`, {
        headers: authHeaders(),
        cache: "no-store",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      const content = (data.content || {}) as CatalogContent;
      setConfigStatus((data.status || null) as ConfigStatus | null);
      setCatalog(content);
      const keys = Object.keys(content.books || {});
      const nextKey = preferredBookKey && keys.includes(preferredBookKey) ? preferredBookKey : keys[0] || "";
      const nextForm = nextKey ? buildForm(nextKey, content) : buildEmptyForm(content);
      setSelectedBookKey(nextKey);
      setForm(nextForm);
      setLoadedFormSnapshot(cloneForm(nextForm));
      const defaultCountry = nextForm.enabledCountries[0] || "IN";
      setAssetCountry(defaultCountry);
      setSampleCountry(defaultCountry);
      clearUploads();
      resetSectionUi();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load catalog");
    } finally {
      setLoading(false);
    }
  }

  function clearUploads() {
    setCoverFile(null);
    setHoverFile(null);
    setGalleryFiles([]);
    setLayoutFiles([]);
    setSampleFiles([]);
    setUploading("");
  }

  function resetSectionUi() {
    setExpandedSections(defaultExpandedSections());
    setEditingSection(null);
    setSectionSnapshot(null);
  }

  function setField<K extends keyof BookForm>(key: K, value: BookForm[K]) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function selectBook(bookKey: string) {
    if (!catalog) return;
    const nextForm = buildForm(bookKey, catalog);
    setSelectedBookKey(bookKey);
    setForm(nextForm);
    setLoadedFormSnapshot(cloneForm(nextForm));
    setAssetCountry(nextForm.enabledCountries[0] || "IN");
    setSampleCountry(nextForm.enabledCountries[0] || "IN");
    clearUploads();
    setError("");
    setStatus("");
    resetSectionUi();
  }

  function startNewBook() {
    if (!catalog) return;
    setSelectedBookKey("");
    const nextForm = buildEmptyForm(catalog);
    setForm(nextForm);
    setLoadedFormSnapshot(cloneForm(nextForm));
    setAssetCountry("IN");
    setSampleCountry("IN");
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
      const enabledCountries = prev.enabledCountries.includes(countryCode)
        ? prev.enabledCountries.filter((code) => code !== countryCode)
        : [...prev.enabledCountries, countryCode];
      return { ...prev, enabledCountries };
    });
  }

  function updatePrice(countryCode: string, style: string, field: keyof PriceFields, value: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const currentCountry = prev.prices[countryCode] || {};
      const currentStyle = currentCountry[style] || { ...EMPTY_PRICE };
      return {
        ...prev,
        prices: {
          ...prev.prices,
          [countryCode]: { ...currentCountry, [style]: { ...currentStyle, [field]: value } },
        },
      };
    });
  }

  function updateListField(key: "heroImages" | "featureItems" | "trustItems", index: number, value: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const nextList = [...prev[key]];
      nextList[index] = value;
      return { ...prev, [key]: nextList };
    });
  }

  function addListField(key: "heroImages" | "featureItems" | "trustItems") {
    setForm((prev) => (prev ? { ...prev, [key]: [...prev[key], ""] } : prev));
  }

  function removeListField(key: "heroImages" | "featureItems" | "trustItems", index: number) {
    setForm((prev) => {
      if (!prev) return prev;
      return { ...prev, [key]: prev[key].filter((_, idx) => idx !== index) };
    });
  }

  function updateFaq(index: number, key: keyof FaqItemForm, value: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const faqItems = [...prev.faqItems];
      faqItems[index] = { ...faqItems[index], [key]: value };
      return { ...prev, faqItems };
    });
  }

  function addFaq() {
    setForm((prev) => (prev ? { ...prev, faqItems: [...prev.faqItems, { id: "", question: "", answer: "" }] } : prev));
  }

  function removeFaq(index: number) {
    setForm((prev) => (prev ? { ...prev, faqItems: prev.faqItems.filter((_, idx) => idx !== index) } : prev));
  }

  async function handleSave() {
    if (!catalog || !form) return;
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const bookKey = form.bookKey.trim();
      const slug = normalizeSlug(form.slug);
      if (!bookKey) throw new Error("Book key is required");
      if (!form.title.trim()) throw new Error("Title is required");
      const currentBooks = { ...(catalog.books || {}) };
      if (!selectedBookKey && currentBooks[bookKey]) throw new Error("A book with this key already exists");
      const duplicateSlug = Object.entries(currentBooks).find(([existingKey, existingBook]) => {
        if (selectedBookKey && existingKey === selectedBookKey) return false;
        return normalizeSlug((existingBook as CatalogBook)?.slug) === slug && Boolean(slug);
      });
      if (duplicateSlug) throw new Error(`Slug '${slug}' is already used by ${duplicateSlug[0]}`);
      const existing = selectedBookKey ? currentBooks[selectedBookKey] || {} : {};
      const nextBook: CatalogBook = {
        ...existing,
        bookKey,
        slug,
        title: form.title.trim(),
        imageSrc: form.imageSrc.trim(),
        hoverImageSrc: form.hoverImageSrc.trim(),
        age: form.age.trim(),
        description: form.description.trim(),
        category: csvToList(form.categories),
        prices: buildPricesPayload(form.prices),
        hero_images: cleanedList(form.heroImages),
        cta_label: form.ctaLabel.trim(),
        create_section_title: form.createSectionTitle.trim(),
        create_section_description: form.createSectionDescription.trim(),
        feature_items: cleanedList(form.featureItems),
        trust_items: cleanedList(form.trustItems),
        faq_items: form.faqItems
          .map((item, index) => ({
            id: item.id.trim() || `faq-${index + 1}`,
            question: item.question.trim(),
            answer: item.answer.trim(),
          }))
          .filter((item) => item.question && item.answer),
        review_rating: form.reviewRating.trim(),
        review_count_label: form.reviewCountLabel.trim(),
        delivery_note: form.deliveryNote.trim(),
        preview_note: form.previewNote.trim(),
        seo_title: form.seoTitle.trim(),
        seo_description: form.seoDescription.trim(),
        seo_keywords: csvToList(form.seoKeywords),
        seo_image: form.seoImage.trim(),
        seo_canonical_path: form.seoCanonicalPath.trim(),
        home_featured: form.homeFeatured,
        home_order: parseOptionalNumber(form.homeOrder),
      };

      if (!nextBook.imageSrc) delete nextBook.imageSrc;
      if (!nextBook.slug) delete nextBook.slug;
      if (!nextBook.hoverImageSrc) delete nextBook.hoverImageSrc;
      if (!nextBook.age) delete nextBook.age;
      if (!nextBook.description) delete nextBook.description;
      if (!nextBook.category?.length) delete nextBook.category;
      if (!nextBook.hero_images?.length) delete nextBook.hero_images;
      if (!nextBook.cta_label) delete nextBook.cta_label;
      if (!nextBook.create_section_title) delete nextBook.create_section_title;
      if (!nextBook.create_section_description) delete nextBook.create_section_description;
      if (!nextBook.feature_items?.length) delete nextBook.feature_items;
      if (!nextBook.trust_items?.length) delete nextBook.trust_items;
      if (!nextBook.faq_items?.length) delete nextBook.faq_items;
      if (!nextBook.review_rating) delete nextBook.review_rating;
      if (!nextBook.review_count_label) delete nextBook.review_count_label;
      if (!nextBook.delivery_note) delete nextBook.delivery_note;
      if (!nextBook.preview_note) delete nextBook.preview_note;
      if (!nextBook.seo_title) delete nextBook.seo_title;
      if (!nextBook.seo_description) delete nextBook.seo_description;
      if (!nextBook.seo_keywords?.length) delete nextBook.seo_keywords;
      if (!nextBook.seo_image) delete nextBook.seo_image;
      if (!nextBook.seo_canonical_path) delete nextBook.seo_canonical_path;
      if (!nextBook.home_featured) delete nextBook.home_featured;
      if (typeof nextBook.home_order !== "number") delete nextBook.home_order;

      const nextCatalog: CatalogContent = {
        ...catalog,
        books: { ...currentBooks, [bookKey]: nextBook },
        countries: { ...(catalog.countries || {}) },
      };
      if (selectedBookKey && selectedBookKey !== bookKey) delete nextCatalog.books?.[selectedBookKey];

      Object.entries(nextCatalog.countries || {}).forEach(([countryCode, cfg]) => {
        const allowed = Array.isArray(cfg.allowed_books) ? [...cfg.allowed_books] : [];
        const withoutBook = allowed.filter((item) => item !== selectedBookKey && item !== bookKey);
        if (form.enabledCountries.includes(countryCode)) withoutBook.push(bookKey);
        nextCatalog.countries![countryCode] = { ...cfg, allowed_books: withoutBook };
      });

      await saveCatalog(nextCatalog);
      setStatus(`Saved draft for ${bookKey}.`);
      await loadCatalog(bookKey);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save book");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!catalog || !selectedBookKey) return;
    if (!window.confirm(`Delete book '${selectedBookKey}' from catalog?`)) return;
    setSaving(true);
    setError("");
    setStatus("");
    try {
      const nextBooks = { ...(catalog.books || {}) };
      delete nextBooks[selectedBookKey];
      const nextCountries: Record<string, CountryConfig> = {};
      Object.entries(catalog.countries || {}).forEach(([countryCode, cfg]) => {
        const allowed = Array.isArray(cfg.allowed_books) ? cfg.allowed_books : [];
        nextCountries[countryCode] = { ...cfg, allowed_books: allowed.filter((item) => item !== selectedBookKey) };
      });
      const nextNormalizationRules = Array.isArray(catalog.normalization_rules)
        ? catalog.normalization_rules.filter((rule) => String(rule.from || "") !== selectedBookKey && String(rule.to || "") !== selectedBookKey)
        : catalog.normalization_rules;
      await saveCatalog({ ...catalog, books: nextBooks, countries: nextCountries, normalization_rules: nextNormalizationRules });
      setStatus(`Deleted ${selectedBookKey}.`);
      await loadCatalog();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete book");
    } finally {
      setSaving(false);
    }
  }

  async function saveCatalog(content: CatalogContent) {
    const res = await fetch(`${API_BASE}/api/admin/product-config/catalog`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ content }),
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
      const res = await fetch(`${API_BASE}/api/admin/product-config/catalog/publish`, {
        method: "POST",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setConfigStatus((data.status || null) as ConfigStatus | null);
      setStatus("Published draft to live catalog.json.");
      await loadCatalog(selectedBookKey || form?.bookKey || "");
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
      const res = await fetch(`${API_BASE}/api/admin/product-config/catalog/draft`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setConfigStatus((data.status || null) as ConfigStatus | null);
      setStatus("Discarded catalog draft and reloaded live config.");
      await loadCatalog(selectedBookKey || form?.bookKey || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to discard draft");
    } finally {
      setSaving(false);
    }
  }

  async function uploadOne(assetKind: "cover" | "hover" | "gallery" | "preview_layout" | "sample_preview", file: File, country?: string, variant?: string) {
    if (!form?.bookKey.trim()) throw new Error("Enter a book key before uploading assets");
    const body = new FormData();
    body.append("book_key", form.bookKey.trim());
    body.append("asset_kind", assetKind);
    body.append("country", country || "IN");
    body.append("sample_variant", variant || "boy");
    body.append("file", file);
    const res = await fetch(`${API_BASE}/api/admin/book-manager/upload`, { method: "POST", headers: authHeaders(), body });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return String(data.public_path || "");
  }

  async function handleSingleUpload(kind: "cover" | "hover", file: File | null, setPath: (path: string) => void) {
    if (!file) return;
    setUploading(kind);
    setError("");
    setStatus("");
    try {
      const path = await uploadOne(kind, file, assetCountry);
      setPath(path);
      setStatus(`Uploaded ${file.name} to ${path}.`);
      if (kind === "cover") setCoverFile(null);
      if (kind === "hover") setHoverFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to upload ${kind}`);
    } finally {
      setUploading("");
    }
  }

  async function handleGalleryUpload() {
    if (!galleryFiles.length) return;
    setUploading("gallery");
    setError("");
    setStatus("");
    try {
      const uploadedPaths: string[] = [];
      for (const file of galleryFiles) uploadedPaths.push(await uploadOne("gallery", file, assetCountry));
      setForm((prev) => (prev ? { ...prev, heroImages: [...prev.heroImages, ...uploadedPaths] } : prev));
      setStatus(`Uploaded ${galleryFiles.length} gallery file(s).`);
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
      const path = await uploadOne("gallery", file, assetCountry);
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

  async function handleBatchUpload(kind: "preview_layout" | "sample_preview", files: File[], country?: string, variant?: string) {
    if (!files.length) return;
    setUploading(kind);
    setError("");
    setStatus("");
    try {
      for (const file of files) await uploadOne(kind, file, country, variant);
      setStatus(`Uploaded ${files.length} file(s) to ${kind}.`);
      if (kind === "preview_layout") setLayoutFiles([]);
      if (kind === "sample_preview") setSampleFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to upload ${kind}`);
    } finally {
      setUploading("");
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Book Manager</h1>
          <p className="text-sm text-slate-600">Manage every storybook field used on the storefront page. Raw JSON editor remains available for advanced changes.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-slate-900">Books</h2>
              <button type="button" onClick={startNewBook} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">New Book</button>
            </div>
            <div className="space-y-2">
              {bookEntries.map(([bookKey, book]) => (
                <button key={bookKey} type="button" onClick={() => selectBook(bookKey)} className={`w-full rounded-xl border px-4 py-3 text-left ${selectedBookKey === bookKey ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-900 hover:border-slate-300"}`}>
                  <div className="text-sm font-medium">{book.title || bookKey}</div>
                  <div className={`mt-1 text-xs ${selectedBookKey === bookKey ? "text-slate-200" : "text-slate-500"}`}>{bookKey}</div>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            {loading || !form ? <p className="text-sm text-slate-500">Loading book manager...</p> : (
              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-medium text-slate-900">{selectedBookKey ? `Edit ${selectedBookKey}` : "Create Book"}</h2>
                      <p className="text-sm text-slate-600">This form saves into `catalog.draft.json`. Use Publish when the draft is finalized.</p>
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
                      {publicStoryPath ? <a href={publicStoryPath} target="_blank" rel="noreferrer" className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">View Live</a> : null}
                      {configStatus?.has_draft ? <button type="button" onClick={() => void discardDraft()} disabled={saving} className="rounded-lg border border-amber-300 px-4 py-2 text-sm text-amber-700 hover:bg-amber-50 disabled:opacity-60">Discard Draft</button> : null}
                      <button type="button" onClick={() => void publishDraft()} disabled={saving || !configStatus?.has_draft} className="rounded-lg border border-green-300 px-4 py-2 text-sm text-green-700 hover:bg-green-50 disabled:opacity-60">Publish Draft</button>
                      {selectedBookKey ? <button type="button" onClick={handleDelete} disabled={saving} className="rounded-lg border border-red-300 px-4 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-60">Delete</button> : null}
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

                {isCreatingNewBook ? (
                  <div className="space-y-4">
                    <CreateModeSteps
                      title="New Book Setup"
                      steps={[
                        "Basic Info",
                        "Media",
                        "Product Copy",
                        "SEO",
                        "Countries and Pricing",
                        "Save Draft",
                        "Preview Draft",
                      ]}
                      note="Follow the steps in order. Preview Draft only shows the last saved draft."
                    />
                    <CreateModeNotice
                      title="Create Mode"
                      message="You are creating a brand-new storybook. Fill the open sections below, save the draft, then preview the saved result."
                    />
                  </div>
                ) : (
                <SectionCard
                  title="Current Page Snapshot"
                  description="This shows the currently loaded content so a non-technical editor can see what already exists before changing it."
                  summary={sectionSummaries?.overview || ""}
                  expanded={expandedSections.overview}
                  onToggle={() => toggleSection("overview")}
                >
                  <div className="grid gap-4 md:grid-cols-2">
                    <InfoBlock label="Public URL" value={publicStoryPath || "Not available until a book key is set"} />
                    <InfoBlock label="Customize URL" value={customizeStoryPath || "Not available until a book key is set"} />
                    <InfoBlock label="Draft Preview URL" value={draftPreviewPath || "Not available until a book key is set"} />
                    <InfoBlock label="Categories" value={form.categories || "None"} />
                    <InfoBlock label="Enabled Countries" value={form.enabledCountries.length ? form.enabledCountries.join(", ") : "None"} />
                  </div>
                  <div className="grid gap-4 md:grid-cols-3">
                    <ImagePreviewCard title="Current Cover" path={form.imageSrc} />
                    <ImagePreviewCard title="Current Hover" path={form.hoverImageSrc} />
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
                  description="These fields drive the listing cards and the product detail header."
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
                      <Field label="Book Key" value={form.bookKey} onChange={(v) => setField("bookKey", v)} disabled={Boolean(selectedBookKey) || editingSection !== "basic"} help={selectedBookKey ? "Existing keys are locked here." : "Lowercase id used in config and URLs."} />
                      <Field label="Slug" value={form.slug} onChange={(v) => setField("slug", v)} disabled={editingSection !== "basic"} help="Optional public URL slug, like starbound-dreamer. Leave blank to keep using the book key." />
                      <Field label="Title" value={form.title} onChange={(v) => setField("title", v)} disabled={editingSection !== "basic"} />
                      <Field label="Age Range" value={form.age} onChange={(v) => setField("age", v)} disabled={editingSection !== "basic"} help="Example: 3 - 7" />
                      <Field label="Categories" value={form.categories} onChange={(v) => setField("categories", v)} disabled={editingSection !== "basic"} help="Comma separated tags shown as badges and filters." />
                      <Field label="Home Display Order" value={form.homeOrder} onChange={(v) => setField("homeOrder", sanitizeIntegerInput(v))} disabled={editingSection !== "basic" || !form.homeFeatured} help="Lower numbers appear first on the homepage bestseller section." />
                      <Field label="Cover Image Path" value={form.imageSrc} onChange={(v) => setField("imageSrc", v)} disabled={editingSection !== "basic"} />
                      <Field label="Hover Image Path" value={form.hoverImageSrc} onChange={(v) => setField("hoverImageSrc", v)} disabled={editingSection !== "basic"} />
                    </div>
                    <label className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={form.homeFeatured}
                        disabled={editingSection !== "basic"}
                        onChange={(e) => setField("homeFeatured", e.target.checked)}
                      />
                      <span>Feature this book in the homepage bestseller section</span>
                    </label>
                    <Area label="Description" value={form.description} onChange={(v) => setField("description", v)} disabled={editingSection !== "basic"} />
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="Product Page Copy"
                  description="These fields control the storybook detail page copy and merchandising blocks."
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
                      <Field label="CTA Label" value={form.ctaLabel} onChange={(v) => setField("ctaLabel", v)} disabled={editingSection !== "copy"} help="Main purple button text." />
                      <Field label="Review Rating" value={form.reviewRating} onChange={(v) => setField("reviewRating", v)} disabled={editingSection !== "copy"} help="Example: 4.8" />
                      <Field label="Review Count Label" value={form.reviewCountLabel} onChange={(v) => setField("reviewCountLabel", v)} disabled={editingSection !== "copy"} help="Example: 3,179 reviews" />
                      <Field label="Delivery Note" value={form.deliveryNote} onChange={(v) => setField("deliveryNote", v)} disabled={editingSection !== "copy"} help="Small note below the CTA." />
                      <Field label="Preview Note" value={form.previewNote} onChange={(v) => setField("previewNote", v)} disabled={editingSection !== "copy"} help="Small note above the delivery note." />
                      <Field label="Create Section Title" value={form.createSectionTitle} onChange={(v) => setField("createSectionTitle", v)} disabled={editingSection !== "copy"} />
                    </div>
                    <Area label="Create Section Description" value={form.createSectionDescription} onChange={(v) => setField("createSectionDescription", v)} disabled={editingSection !== "copy"} />
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="SEO"
                  description="These fields drive page title, description, canonical URL, and share image for this storybook page."
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
                      <Field label="SEO Image Path" value={form.seoImage} onChange={(v) => setField("seoImage", v)} disabled={editingSection !== "seo"} help="Used for Open Graph and Twitter cards." />
                      <Field label="Canonical Path" value={form.seoCanonicalPath} onChange={(v) => setField("seoCanonicalPath", v)} disabled={editingSection !== "seo"} help="Optional override. If blank, SEO uses /storybook/{slug-or-book-key}." />
                      <Field label="SEO Keywords" value={form.seoKeywords} onChange={(v) => setField("seoKeywords", v)} disabled={editingSection !== "seo"} help="Comma separated." />
                    </div>
                    <Area label="SEO Description" value={form.seoDescription} onChange={(v) => setField("seoDescription", v)} disabled={editingSection !== "seo"} />
                    <ImagePreviewCard title="SEO Share Image" path={form.seoImage} />
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="Country Availability"
                  description="Controls which countries can see this storybook."
                  summary={sectionSummaries?.countries || ""}
                  dirty={sectionDirty.countries}
                  expanded={expandedSections.countries}
                  editing={editingSection === "countries"}
                  actionLabel="Edit Countries"
                  actionDisabled={Boolean(editingSection && editingSection !== "countries")}
                  onToggle={() => toggleSection("countries")}
                  onEdit={() => beginSectionEdit("countries")}
                  onSave={() => saveSectionEdit("countries")}
                  onCancel={() => cancelSectionEdit("countries")}
                >
                  <fieldset disabled={editingSection !== "countries"} className="disabled:opacity-80">
                    <div className="grid gap-3 md:grid-cols-3">
                      {countries.map(([countryCode, cfg]) => (
                        <label key={countryCode} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                          <input type="checkbox" checked={form.enabledCountries.includes(countryCode)} onChange={() => toggleCountry(countryCode)} />
                          <span>{countryCode}</span>
                          <span className="text-slate-500">{cfg.currency || ""}</span>
                        </label>
                      ))}
                    </div>
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="Product Media"
                  description="Upload cover, hover, gallery, preview layout, and sample preview assets from here."
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
                        <div className="text-sm font-medium text-slate-900">Cover / Hover Upload</div>
                        <select value={assetCountry} onChange={(e) => setAssetCountry(e.target.value)} className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                          {countries.map(([countryCode]) => <option key={countryCode} value={countryCode}>{countryCode}</option>)}
                        </select>
                        <UploadField label="Change Cover Image" file={coverFile} uploading={uploading === "cover"} onPick={setCoverFile} onUpload={() => void handleSingleUpload("cover", coverFile, (path) => setField("imageSrc", path))} disabled={editingSection !== "media"} />
                        <UploadField label="Change Hover Image" file={hoverFile} uploading={uploading === "hover"} onPick={setHoverFile} onUpload={() => void handleSingleUpload("hover", hoverFile, (path) => setField("hoverImageSrc", path))} disabled={editingSection !== "media"} />
                      </div>

                      <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-sm font-medium text-slate-900">Gallery Upload</div>
                        <p className="mt-1 text-xs text-slate-500">Uploaded images are appended to the product-page gallery list below.</p>
                        <input type="file" multiple onChange={(e) => setGalleryFiles(Array.from(e.target.files || []))} className="mt-3 w-full text-sm" />
                        <button type="button" disabled={!galleryFiles.length || uploading === "gallery"} onClick={() => void handleGalleryUpload()} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">{uploading === "gallery" ? "Uploading..." : "Upload Gallery Images"}</button>
                      </div>
                    </div>
                    <div className="mt-4 grid gap-4 md:grid-cols-2">
                      <ImagePreviewCard title="Current Cover" path={form.imageSrc} />
                      <ImagePreviewCard title="Current Hover" path={form.hoverImageSrc} />
                    </div>
                  </fieldset>
                </SectionCard>

                <SectionCard
                  title="Preview Layout And Sample Assets"
                  description="Preview layout is used by the generated preview UI. Sample assets are optional static previews."
                  summary={sectionSummaries?.previewAssets || ""}
                  dirty={sectionDirty.previewAssets}
                  expanded={expandedSections.previewAssets}
                  editing={editingSection === "previewAssets"}
                  actionLabel="Upload Assets"
                  actionDisabled={Boolean(editingSection && editingSection !== "previewAssets")}
                  onToggle={() => toggleSection("previewAssets")}
                  onEdit={() => beginSectionEdit("previewAssets")}
                  onSave={() => saveSectionEdit("previewAssets")}
                  onCancel={() => cancelSectionEdit("previewAssets")}
                >
                  <fieldset disabled={editingSection !== "previewAssets"} className="space-y-4 disabled:opacity-80">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-sm font-medium text-slate-900">Preview Layout Upload</div>
                        <p className="mt-1 text-xs text-slate-500">Upload `frontcover.png` and `pg*.png` files for the story preview template.</p>
                        <input type="file" multiple onChange={(e) => setLayoutFiles(Array.from(e.target.files || []))} className="mt-3 w-full text-sm" />
                        <button type="button" disabled={!layoutFiles.length || uploading === "preview_layout"} onClick={() => void handleBatchUpload("preview_layout", layoutFiles)} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">{uploading === "preview_layout" ? "Uploading..." : "Upload Preview Layout Files"}</button>
                      </div>

                      <div className="rounded-lg border border-slate-200 p-4">
                        <div className="text-sm font-medium text-slate-900">Optional Sample Preview Upload</div>
                        <div className="mt-3 grid gap-3 md:grid-cols-3">
                          <select value={sampleCountry} onChange={(e) => setSampleCountry(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                            {countries.map(([countryCode]) => <option key={countryCode} value={countryCode}>{countryCode}</option>)}
                          </select>
                          <select value={sampleVariant} onChange={(e) => setSampleVariant(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                            <option value="boy">boy</option>
                            <option value="girl">girl</option>
                          </select>
                          <input type="file" multiple onChange={(e) => setSampleFiles(Array.from(e.target.files || []))} className="w-full text-sm" />
                        </div>
                        <button type="button" disabled={!sampleFiles.length || uploading === "sample_preview"} onClick={() => void handleBatchUpload("sample_preview", sampleFiles, sampleCountry, sampleVariant)} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">{uploading === "sample_preview" ? "Uploading..." : "Upload Sample Preview Files"}</button>
                      </div>
                    </div>
                  </fieldset>
                </SectionCard>

                <div ref={gallerySectionRef}>
                <SectionCard
                  title="Product Page Gallery"
                  description="These images drive the storybook preview carousel. If left blank, the storefront falls back to `/books/{book}/{country}/{book}-book-1..5` files."
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
                      emptyLabel="No custom gallery images yet."
                      onChange={(index, value) => updateListField("heroImages", index, value)}
                      onAdd={() => addListField("heroImages")}
                      onRemove={(index) => removeListField("heroImages", index)}
                      onMove={moveGalleryImage}
                      onReplace={(index, file) => void handleGalleryReplace(index, file)}
                      uploadingKey={uploading}
                      disabled={editingSection !== "gallery"}
                    />
                    <div className="mt-4">
                      <ImagePreviewGrid title="Current Gallery Images" paths={form.heroImages} />
                    </div>
                  </fieldset>
                </SectionCard>
                </div>

                <div className="grid gap-6 xl:grid-cols-2">
                  <SectionCard
                    title="Feature Bullets"
                    description="Shown under the reviews near the top of the product page."
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
                    description="Small assurance items shown in the boxed strip below the CTA."
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
                  description="Accordion content on the product detail page."
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
                            <Field label="FAQ Id" value={item.id} onChange={(v) => updateFaq(index, "id", v)} disabled={editingSection !== "faq"} help="Optional. Auto-generated if blank." />
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
                  title="Pricing by Country and Style"
                  description="Stored exactly as strings in `catalog.json` so the storefront pricing logic stays unchanged."
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
                    <div className="mt-4 space-y-5">
                      {countries.map(([countryCode, cfg]) => (
                        <div key={countryCode} className="rounded-xl border border-slate-200 p-4">
                          <div className="mb-3 text-sm font-semibold text-slate-900">{countryCode} <span className="text-xs font-normal text-slate-500">{cfg.currency || ""}</span></div>
                          <div className="space-y-4">
                            {styles.map((style) => (
                              <div key={`${countryCode}-${style}`} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                                <div className="mb-2 text-sm font-medium text-slate-900">{style}</div>
                                <div className="grid gap-3 md:grid-cols-3">
                                  <CurrencyField label="Price" currency={String(cfg.currency || "")} value={form.prices[countryCode]?.[style]?.price || ""} onChange={(v) => updatePrice(countryCode, style, "price", v)} disabled={editingSection !== "pricing"} />
                                  <CurrencyField label="Shipping" currency={String(cfg.currency || "")} value={form.prices[countryCode]?.[style]?.shipping || ""} onChange={(v) => updatePrice(countryCode, style, "shipping", v)} disabled={editingSection !== "pricing"} />
                                  <Field label="Taxes" value={form.prices[countryCode]?.[style]?.taxes || ""} onChange={(v) => updatePrice(countryCode, style, "taxes", v)} disabled={editingSection !== "pricing"} help="Numbers only." />
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

function buildEmptyForm(catalog: CatalogContent): BookForm {
  const prices: Record<string, Record<string, PriceFields>> = {};
  Object.keys(catalog.countries || {}).forEach((countryCode) => {
    prices[countryCode] = Object.fromEntries(DEFAULT_STYLES.map((style) => [style, { ...EMPTY_PRICE }]));
  });
  return {
    bookKey: "",
    slug: "",
    title: "",
    imageSrc: "",
    hoverImageSrc: "",
    age: "",
    description: "",
    categories: "",
    enabledCountries: [],
    prices,
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
    homeFeatured: false,
    homeOrder: "",
  };
}

function buildForm(bookKey: string, catalog: CatalogContent): BookForm {
  const book = (catalog.books || {})[bookKey] || {};
  const empty = buildEmptyForm(catalog);
  const prices = { ...empty.prices };
  Object.entries(book.prices || {}).forEach(([countryCode, styleMap]) => {
    prices[countryCode] = { ...(prices[countryCode] || {}) };
    Object.entries(styleMap || {}).forEach(([style, fields]) => {
      if (!DEFAULT_STYLES.includes(style)) return;
      prices[countryCode][style] = {
        price: extractNumericValue(fields?.price),
        shipping: extractNumericValue(fields?.shipping),
        taxes: String(fields?.taxes || ""),
      };
    });
  });

  const enabledCountries = Object.entries(catalog.countries || {})
    .filter(([, cfg]) => Array.isArray(cfg.allowed_books) && cfg.allowed_books.includes(bookKey))
    .map(([countryCode]) => countryCode);

  return {
    bookKey,
    slug: String(book.slug || ""),
    title: String(book.title || ""),
    imageSrc: String(book.imageSrc || ""),
    hoverImageSrc: String(book.hoverImageSrc || ""),
    age: String(book.age || ""),
    description: String(book.description || ""),
    categories: Array.isArray(book.category) ? book.category.join(", ") : "",
    enabledCountries,
    prices,
    heroImages: Array.isArray(book.hero_images) ? book.hero_images.map((item) => String(item || "")) : [],
    ctaLabel: String(book.cta_label || ""),
    createSectionTitle: String(book.create_section_title || ""),
    createSectionDescription: String(book.create_section_description || ""),
    featureItems: Array.isArray(book.feature_items) ? book.feature_items.map((item) => String(item || "")) : [],
    trustItems: Array.isArray(book.trust_items) ? book.trust_items.map((item) => String(item || "")) : [],
    faqItems: Array.isArray(book.faq_items)
      ? book.faq_items.map((item, index) => ({
          id: String(item?.id || `faq-${index + 1}`),
          question: String(item?.question || ""),
          answer: String(item?.answer || ""),
        }))
      : [],
    reviewRating: String(book.review_rating || ""),
    reviewCountLabel: String(book.review_count_label || ""),
    deliveryNote: String(book.delivery_note || ""),
    previewNote: String(book.preview_note || ""),
    seoTitle: String(book.seo_title || ""),
    seoDescription: String(book.seo_description || ""),
    seoKeywords: Array.isArray(book.seo_keywords) ? book.seo_keywords.join(", ") : "",
    seoImage: String(book.seo_image || ""),
    seoCanonicalPath: String(book.seo_canonical_path || ""),
    homeFeatured: Boolean(book.home_featured),
    homeOrder: typeof book.home_order === "number" ? String(book.home_order) : "",
  };
}

function buildPricesPayload(prices: Record<string, Record<string, PriceFields>>) {
  const payload: Record<string, Record<string, PriceFields>> = {};
  Object.entries(prices).forEach(([countryCode, styleMap]) => {
    const cleanedStyles: Record<string, PriceFields> = {};
    Object.entries(styleMap || {}).forEach(([style, fields]) => {
      if (!DEFAULT_STYLES.includes(style)) return;
      const currency = getCurrencyForCountryCode(countryCode);
      const next = {
        price: formatCurrencyValue(String(fields?.price || "").trim(), currency),
        shipping: formatCurrencyValue(String(fields?.shipping || "").trim(), currency),
        taxes: String(fields?.taxes || "").trim(),
      };
      if (next.price || next.shipping || next.taxes) cleanedStyles[style] = next;
    });
    if (Object.keys(cleanedStyles).length > 0) payload[countryCode] = cleanedStyles;
  });
  return payload;
}

function csvToList(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function cleanedList(items: string[]) {
  return items.map((item) => item.trim()).filter(Boolean);
}

function normalizeSlug(value?: string) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function buildStorybookPublicPath(bookKey?: string, slug?: string) {
  const identifier = normalizeSlug(slug) || String(bookKey || "").trim().toLowerCase();
  return identifier ? `http://localhost:3000/storybook/${identifier}` : "";
}

function extractNumericValue(value: unknown) {
  return String(value || "").replace(/[^0-9.]/g, "");
}

function sanitizeNumericInput(value: string) {
  const cleaned = value.replace(/[^0-9.]/g, "");
  const [whole, ...rest] = cleaned.split(".");
  return rest.length ? `${whole}.${rest.join("")}` : cleaned;
}

function sanitizeIntegerInput(value: string) {
  return String(value || "").replace(/\D/g, "");
}

function parseOptionalNumber(value: string) {
  const trimmed = String(value || "").trim();
  if (!trimmed) return undefined;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function getCurrencyForCountryCode(countryCode: string) {
  const code = String(countryCode || "").trim().toUpperCase();
  if (code === "US") return "USD";
  if (code === "GB") return "GBP";
  if (code === "CA") return "CAD";
  if (code === "AE") return "AED";
  return "INR";
}

function currencyPrefix(currency: string) {
  if (currency === "USD") return "$";
  return currency;
}

function formatCurrencyValue(value: string, currency: string) {
  const numeric = sanitizeNumericInput(value).trim();
  if (!numeric) return "";
  if (currency === "USD") return `$${numeric}`;
  return `${currency} ${numeric}`;
}

function buildStorybookDraftPreviewPath(bookKey?: string) {
  const id = String(bookKey || "").trim().toLowerCase();
  return id ? `http://localhost:3000/child-details?book_id=${encodeURIComponent(id)}&product=storybook&draft=1` : "";
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

function Field({
  label,
  value,
  onChange,
  disabled,
  help,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  help?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <input value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 disabled:bg-slate-100" />
      {help ? <span className="mt-1 block text-xs text-slate-500">{help}</span> : null}
    </label>
  );
}

function CurrencyField({
  label,
  currency,
  value,
  onChange,
  disabled,
}: {
  label: string;
  currency: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <div className="flex items-center overflow-hidden rounded-lg border border-slate-300 bg-white">
        <span className="border-r border-slate-200 px-3 py-2 text-sm text-slate-500">{currencyPrefix(currency)}</span>
        <input
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(sanitizeNumericInput(e.target.value))}
          className="w-full px-3 py-2 text-sm text-slate-900 disabled:bg-slate-100"
          inputMode="decimal"
        />
      </div>
      <span className="mt-1 block text-xs text-slate-500">Enter numbers only. Currency is added automatically.</span>
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

function UploadField({
  label,
  file,
  uploading,
  onPick,
  onUpload,
  disabled,
}: {
  label: string;
  file: File | null;
  uploading: boolean;
  onPick: (file: File | null) => void;
  onUpload: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="mt-3 rounded-lg border border-slate-200 p-3">
      <div className="text-sm font-medium text-slate-900">{label}</div>
      <input type="file" disabled={disabled} onChange={(e) => onPick((e.target.files || [])[0] || null)} className="mt-2 w-full text-sm" />
      {file ? <p className="mt-2 text-xs text-slate-500">{file.name}</p> : null}
      <button type="button" disabled={!file || uploading || disabled} onClick={onUpload} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">{uploading ? "Uploading..." : "Upload"}</button>
    </div>
  );
}

function ImagePreviewCard({ title, path }: { title: string; path?: string }) {
  const value = String(path || "").trim();
  const displayUrl = resolveAssetUrl(value);
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="text-sm font-medium text-slate-900">{title}</div>
      {!value ? (
        <p className="mt-2 text-sm text-slate-500">No image selected.</p>
      ) : (
        <div className="mt-3 space-y-2">
          <img src={displayUrl} alt={title} className="h-40 w-full rounded-lg border border-slate-200 object-cover bg-slate-50" />
          <a href={displayUrl} target="_blank" rel="noreferrer" className="block break-all text-xs text-blue-700 underline">
            {value}
          </a>
        </div>
      )}
    </div>
  );
}

function ImagePreviewGrid({ title, paths, actionLabel, onAction }: { title: string; paths: string[]; actionLabel?: string; onAction?: () => void }) {
  const cleaned = paths.map((item) => item.trim()).filter(Boolean);
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
      {cleaned.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No gallery images configured.</p>
      ) : (
        <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {cleaned.map((path, index) => (
            <div key={`${path}-${index}`} className="rounded-lg border border-slate-200 p-2">
              <img src={resolveAssetUrl(path)} alt={`Gallery ${index + 1}`} className="h-32 w-full rounded-md object-cover bg-slate-50" />
              <a href={resolveAssetUrl(path)} target="_blank" rel="noreferrer" className="mt-2 block break-all text-[11px] text-blue-700 underline">
                {path}
              </a>
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
    countries: false,
    media: false,
    previewAssets: false,
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
    countries: true,
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
    countries: false,
    media: false,
    previewAssets: false,
    gallery: false,
    features: false,
    trust: false,
    faq: false,
    pricing: false,
  };
}

function buildBookSectionDirtyMap(form: BookForm, baseline: BookForm): Record<SectionId, boolean> {
  const sections = defaultDirtySections();
  (Object.keys(sections) as SectionId[]).forEach((section) => {
    if (section === "overview" || section === "validation") return;
    sections[section] = JSON.stringify(getBookSectionValue(form, section)) !== JSON.stringify(getBookSectionValue(baseline, section));
  });
  return sections;
}

function getBookSectionValue(form: BookForm, section: SectionId) {
  switch (section) {
    case "basic":
      return { bookKey: form.bookKey, slug: form.slug, title: form.title, age: form.age, categories: form.categories, imageSrc: form.imageSrc, hoverImageSrc: form.hoverImageSrc, description: form.description, homeFeatured: form.homeFeatured, homeOrder: form.homeOrder };
    case "copy":
      return { ctaLabel: form.ctaLabel, reviewRating: form.reviewRating, reviewCountLabel: form.reviewCountLabel, deliveryNote: form.deliveryNote, previewNote: form.previewNote, createSectionTitle: form.createSectionTitle, createSectionDescription: form.createSectionDescription };
    case "seo":
      return { seoTitle: form.seoTitle, seoDescription: form.seoDescription, seoKeywords: form.seoKeywords, seoImage: form.seoImage, seoCanonicalPath: form.seoCanonicalPath };
    case "countries":
      return { enabledCountries: form.enabledCountries };
    case "media":
      return { imageSrc: form.imageSrc, hoverImageSrc: form.hoverImageSrc };
    case "previewAssets":
      return { sampleCountry: "", sampleVariant: "" };
    case "gallery":
      return { heroImages: form.heroImages };
    case "features":
      return { featureItems: form.featureItems };
    case "trust":
      return { trustItems: form.trustItems };
    case "faq":
      return { faqItems: form.faqItems };
    case "pricing":
      return { prices: form.prices };
    default:
      return null;
  }
}
