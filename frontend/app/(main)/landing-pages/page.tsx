import MarketingCrudPage from "../components/MarketingCrudPage";

export default function LandingPagesPage() {
  return (
    <MarketingCrudPage
      title="Landing Pages"
      endpoint="/api/admin/landing-pages"
      defaultItem={{
        slug: "",
        title: "",
        product_type: "",
        hero_heading: "",
        hero_media_url: "",
        target_path: "",
        active: true,
        notes: "",
      }}
      fields={[
        { key: "title", label: "Title" },
        { key: "slug", label: "Slug" },
        { key: "product_type", label: "Product Type" },
        { key: "hero_heading", label: "Hero Heading" },
        { key: "hero_media_url", label: "Hero Media URL" },
        { key: "target_path", label: "Target Path" },
        { key: "active", label: "Active", type: "checkbox" },
        { key: "notes", label: "Notes", type: "textarea" },
      ]}
    />
  );
}

