import MarketingCrudPage from "../components/MarketingCrudPage";

export default function CampaignsPage() {
  return (
    <MarketingCrudPage
      title="Campaigns"
      endpoint="/api/admin/campaigns"
      defaultItem={{
        name: "",
        slug: "",
        platform: "meta",
        product_type: "",
        landing_page_slug: "",
        utm_source: "facebook",
        utm_medium: "paid_social",
        utm_campaign: "",
        utm_content: "",
        active: true,
        commission_type: "percent",
        commission_rate: 0,
        notes: "",
      }}
      fields={[
        { key: "name", label: "Name" },
        { key: "slug", label: "Slug" },
        { key: "platform", label: "Platform" },
        { key: "product_type", label: "Product Type" },
        { key: "landing_page_slug", label: "Landing Page Slug" },
        { key: "utm_source", label: "UTM Source" },
        { key: "utm_medium", label: "UTM Medium" },
        { key: "utm_campaign", label: "UTM Campaign" },
        { key: "utm_content", label: "UTM Content" },
        { key: "commission_type", label: "Commission Type" },
        { key: "commission_rate", label: "Commission Rate", type: "number" },
        { key: "active", label: "Active", type: "checkbox" },
        { key: "notes", label: "Notes", type: "textarea" },
      ]}
    />
  );
}

