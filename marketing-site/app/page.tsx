import type { Metadata } from "next";
import { platformStats, features, testimonials } from "@/lib/static-data";
import Hero from "@/components/HeroSection";
import Link from "next/link";

export const metadata: Metadata = {
  title: `${process.env.NEXT_PUBLIC_APP_NAME} — AI-Powered Trade Intelligence`,
  description:
    "Instant HS code classification, tariff analysis, and live shipping rates powered by AI. Built for the Pakistan–US trade corridor.",
  openGraph: {
    title: `${process.env.NEXT_PUBLIC_APP_NAME} — AI-Powered Trade Intelligence`,
    description:
      "Instant HS code classification, tariff analysis, and live shipping rates powered by AI.",
    url: "/",
  },
};

export default function HomePage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: `${process.env.NEXT_PUBLIC_APP_NAME}`,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    url: "/",
    description:
      "AI-powered trade intelligence platform for HS code classification and tariff analysis.",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: "4.8",
      reviewCount: "500",
    },
  };

  return (
    <div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Hero />

      {/* Stats */}
      <section style={{ padding: "3rem 0", background: "var(--bg-subtle)" }}>
        <div className="section-container">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
              gap: "1.5rem",
              textAlign: "center",
            }}
          >
            {platformStats.slice(0, 4).map((stat) => (
              <div key={stat.id}>
                <div
                  style={{
                    fontSize: "1.75rem",
                    fontWeight: 700,
                    color: "var(--color-brand-400)",
                  }}
                >
                  {stat.value}
                  {stat.suffix}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: "5rem 0" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              textAlign: "center",
              marginBottom: "2.5rem",
            }}
          >
            Powerful Features
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "1.25rem",
            }}
          >
            {features.slice(0, 4).map((f) => (
              <div
                key={f.id}
                style={{
                  padding: "1.5rem",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                }}
              >
                <h3
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                    marginBottom: "0.375rem",
                  }}
                >
                  {f.name}
                </h3>
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                  {f.tagline}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section style={{ padding: "5rem 0", background: "var(--bg-subtle)" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              textAlign: "center",
              marginBottom: "2.5rem",
            }}
          >
            How It Works
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {[
              { n: "01", t: "Ask Question", d: "Type or speak your trade question in natural language." },
              { n: "02", t: "AI Processes", d: "Searches tariff databases and knowledge graphs instantly." },
              { n: "03", t: "Get Answer", d: "Receive accurate results with citations and calculations." },
            ].map((i) => (
              <div
                key={i.n}
                style={{
                  padding: "1.5rem",
                  background: "var(--bg-surface)",
                  borderRadius: "var(--radius-lg)",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    color: "var(--color-brand-400)",
                    marginBottom: "0.5rem",
                  }}
                >
                  {i.n}
                </div>
                <div
                  style={{
                    fontSize: "1rem",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                    marginBottom: "0.25rem",
                  }}
                >
                  {i.t}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                  {i.d}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "5rem 0", textAlign: "center" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "0.75rem",
            }}
          >
            Ready to get started?
          </h2>
          <p
            style={{
              fontSize: "1rem",
              color: "var(--text-secondary)",
              marginBottom: "1.5rem",
            }}
          >
            Join trading companies using {process.env.NEXT_PUBLIC_APP_NAME}.
          </p>
          <Link
            href="/contact"
            style={{
              padding: "0.75rem 1.5rem",
              borderRadius: "9999px",
              background: "var(--color-brand-500)",
              color: "white",
              fontWeight: 600,
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