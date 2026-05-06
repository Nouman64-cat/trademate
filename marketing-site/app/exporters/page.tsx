import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "For Exporters",
  description:
    `${process.env.NEXT_PUBLIC_APP_NAME} helps exporters expand globally. Get market intelligence, tariff analysis, and compliance guidance for destination markets.`,
};

const benefits = [
  {
    id: "marketAccess",
    title: "Market Access Intelligence",
    description: "Understand tariffs and requirements for any export destination. Compare market entry costs and identify the best opportunities.",
  },
  {
    id: "rulesOfOrigin",
    title: "Rules of Origin",
    description: "Determine if your product qualifies for preferential tariffs under FTAs. Calculate local content requirements.",
  },
  {
    id: "gspPlus",
    title: "GSP+ Eligibility",
    description: "Check if your products qualify for duty-free access to the EU under GSP+. Get guidance on certificate of origin requirements.",
  },
  {
    id: "destinationTariffs",
    title: "Destination Tariffs",
    description: "Look up import tariffs for Pakistan products in 180+ countries. Know what your buyer will pay.",
  },
  {
    id: "compliance",
    title: "Export Compliance",
    description: "Navigate labeling requirements, product standards, and certification needs for each market.",
  },
  {
    id: "competitorIntel",
    title: "Competitor Intelligence",
    description: "Understand how your costs compare to exporters from Bangladesh, Vietnam, and other competitor nations.",
  },
];

const features = [
  {
    id: "aiChat",
    title: "AI Trade Chat",
    description: "Ask market entry questions in plain language.",
  },
  {
    id: "tariffCompare",
    title: "Multi-Country Comparison",
    description: "Compare tariffs across potential export markets.",
  },
  {
    id: "originAnalysis",
    title: "Origin Analysis",
    description: "Calculate rules of origin for FTA benefits.",
  },
  {
    id: "labeling",
    title: "Labeling Requirements",
    description: "Get country-specific labeling compliance guides.",
  },
  {
    id: "certification",
    title: "Certification Guide",
    description: "Identify required certificates for your products.",
  },
  {
    id: "marketReports",
    title: "Market Reports",
    description: "Access detailed market entry intelligence.",
  },
];

const useCases = [
  {
    id: "textiles",
    title: "Textile Exports",
    description: "Navigate US and EU tariffs, quota restrictions, and labeling requirements for garments.",
  },
  {
    id: "pharma",
    title: "Pharmaceutical Exports",
    description: "Meet WHO and destination country registration requirements.",
  },
  {
    id: "food",
    title: "Food Products",
    description: "Ensure FDA/EU compliance and HACCP documentation.",
  },
  {
    id: "rice",
    title: "Rice & Commodities",
    description: "Navigate export quotas and destination country quality standards.",
  },
];

const markets = [
  { id: "usa", name: "United States", flag: "🇺🇸" },
  { id: "eu", name: "European Union", flag: "🇪🇺" },
  { id: "uk", name: "United Kingdom", flag: "🇬🇧" },
  { id: "uae", name: "UAE", flag: "🇦🇪" },
  { id: "china", name: "China", flag: "🇨🇳" },
  { id: "saudi", name: "Saudi Arabia", flag: "🇸🇦" },
];

export default function ExportersPage() {
  return (
    <div style={{ paddingBottom: "6rem" }}>
      {/* Hero */}
      <section style={{ padding: "6rem 0 4rem", textAlign: "center" }}>
        <div className="section-container">
          <h1
            style={{
              fontSize: "clamp(2.5rem, 5vw, 3.5rem)",
              fontWeight: 700,
              letterSpacing: "-0.04em",
              color: "var(--text-primary)",
              marginBottom: "1rem",
            }}
          >
            Trade Intelligence for Exporters
          </h1>
          <p
            style={{
              fontSize: "clamp(1.125rem, 2vw, 1.25rem)",
              color: "var(--text-secondary)",
              maxWidth: "600px",
              margin: "0 auto 2rem",
              lineHeight: 1.6,
            }}
          >
            Expand globally with confidence. Understand destination tariffs, FTA
            benefits, and compliance requirements for every market.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link
              href="/contact"
              style={{
                padding: "0.75rem 1.5rem",
                borderRadius: "var(--radius-full)",
                fontSize: "1rem",
                fontWeight: 600,
                color: "white",
                background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                boxShadow: "0 0 24px -4px rgba(59 130 246 / 0.5)",
                textDecoration: "none",
              }}
            >
              Request Demo
            </Link>
            <Link
              href="/pricing"
              style={{
                padding: "0.75rem 1.5rem",
                borderRadius: "var(--radius-full)",
                fontSize: "1rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                border: "1px solid var(--border-subtle)",
                textDecoration: "none",
              }}
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* Markets */}
      <section className="section-container" style={{ marginBottom: "4rem" }}>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "1.5rem",
          }}
        >
          {markets.map((market) => (
            <div
              key={market.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.75rem 1.25rem",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-full)",
              }}
            >
              <span style={{ fontSize: "1.25rem" }}>{market.flag}</span>
              <span style={{ fontSize: "0.9375rem", fontWeight: 500, color: "var(--text-primary)" }}>
                {market.name}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Benefits */}
      <section className="section-container">
        <h2
          style={{
            fontSize: "clamp(1.5rem, 3vw, 2rem)",
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: "0.5rem",
            textAlign: "center",
          }}
        >
          Why Exporters Choose {process.env.NEXT_PUBLIC_APP_NAME}
        </h2>
        <p
          style={{
            fontSize: "1rem",
            color: "var(--text-secondary)",
            textAlign: "center",
            maxWidth: "500px",
            margin: "0 auto 2.5rem",
          }}
        >
          Everything you need to export profitably.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {benefits.map((benefit) => (
            <div
              key={benefit.id}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "1.75rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              <h3
                style={{
                  fontSize: "1.125rem",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                }}
              >
                {benefit.title}
              </h3>
              <p
                style={{
                  fontSize: "0.9375rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                }}
              >
                {benefit.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: "4rem 0" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "0.5rem",
              textAlign: "center",
            }}
          >
            Features Included
          </h2>
          <p
            style={{
              fontSize: "1rem",
              color: "var(--text-secondary)",
              textAlign: "center",
              maxWidth: "500px",
              margin: "0 auto 2.5rem",
            }}
          >
            Full platform access for exporters.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1rem",
            }}
          >
            {features.map((feature) => (
              <div
                key={feature.id}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.75rem",
                  padding: "1.25rem",
                  background: "var(--bg-muted)",
                  borderRadius: "var(--radius-lg)",
                }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  style={{ color: "var(--color-accent-500)", flexShrink: 0, marginTop: "0.125rem" }}
                >
                  <path
                    d="M7 10l2 2 4-4"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div>
                  <h4
                    style={{
                      fontSize: "0.9375rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      marginBottom: "0.25rem",
                    }}
                  >
                    {feature.title}
                  </h4>
                  <p
                    style={{
                      fontSize: "0.8125rem",
                      color: "var(--text-muted)",
                      lineHeight: 1.5,
                    }}
                  >
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use cases */}
      <section className="section-container">
        <h2
          style={{
            fontSize: "clamp(1.5rem, 3vw, 2rem)",
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: "0.5rem",
            textAlign: "center",
          }}
        >
          Common Export Scenarios
        </h2>
        <p
          style={{
            fontSize: "1rem",
            color: "var(--text-secondary)",
            textAlign: "center",
            maxWidth: "500px",
            margin: "0 auto 2.5rem",
          }}
        >
          {process.env.NEXT_PUBLIC_APP_NAME} handles all major export categories.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {useCases.map((useCase) => (
            <div
              key={useCase.id}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                padding: "1.5rem",
              }}
            >
              <h3
                style={{
                  fontSize: "1rem",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                  marginBottom: "0.5rem",
                }}
              >
                {useCase.title}
              </h3>
              <p
                style={{
                  fontSize: "0.875rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                {useCase.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "6rem 0", textAlign: "center" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.75rem, 3vw, 2.25rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "1rem",
            }}
          >
            Start Expanding Globally
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 2rem",
            }}
          >
            Understand your destination markets and maximize FTA benefits.
          </p>
          <Link
            href="/contact"
            style={{
              padding: "0.75rem 1.5rem",
              borderRadius: "var(--radius-full)",
              fontSize: "1rem",
              fontWeight: 600,
              color: "white",
              background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
              boxShadow: "0 0 24px -4px rgba(59 130 246 / 0.5)",
              textDecoration: "none",
            }}
          >
            Request Demo
          </Link>
        </div>
      </section>
    </div>
  );
}