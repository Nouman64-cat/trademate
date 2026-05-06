import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Solutions",
  description:
    `${process.env.NEXT_PUBLIC_APP_NAME} provides tailored trade intelligence solutions for importers, exporters, freight forwarders, and enterprises. Streamline customs compliance, optimize shipping, and reduce costs.`,
};

const solutions = [
  {
    id: "importers",
    title: "For Importers",
    subtitle: "Reduce landed costs and ensure compliance",
    description:
      `Stop guessing at HS codes and duty rates. ${process.env.NEXT_PUBLIC_APP_NAME} instantly classifies your products, identifies applicable exemptions, and calculates your total landed cost — before your shipment leaves the factory.`,
    benefits: [
      "Instant HS code classification with 99.7% accuracy",
      "Auto-detect SRO exemptions and anti-dumping duties",
      "DDP landed cost calculations before you buy",
      "Real-time tariff rate alerts for policy changes",
    ],
    icon: "Package",
  },
  {
    id: "exporters",
    title: "For Exporters",
    subtitle: "Expand globally with confidence",
    description:
      `Navigate complex destination country requirements. ${process.env.NEXT_PUBLIC_APP_NAME} helps you understand tariffs, labeling requirements, and certification needs for any market you want to enter.`,
    benefits: [
      "Multi-country tariff comparison in seconds",
      "Certificate of origin requirements by destination",
      "Labeling and packaging compliance guidance",
      "Market entry intelligence for 180+ countries",
    ],
    icon: "Truck",
  },
  {
    id: "freight-forwarders",
    title: "For Freight Forwarders",
    subtitle: "Serve clients faster and more accurately",
    description:
      "Give your clients instant answers on shipping routes, transit times, and total costs. Stand out with AI-powered trade expertise that competitors can't match.",
    benefits: [
      "Live Freightos rate fetching for quotes",
      "DDP breakdowns for client proposals",
      "HS code validation for customs clearance",
      "Multi-leg route optimization",
    ],
    icon: "Navigation",
  },
  {
    id: "enterprise",
    title: "Enterprise",
    subtitle: "Scale with custom integrations",
    description:
      "Custom deployments, unlimited API access, dedicated support, and custom document ingestion for large trading organizations with complex compliance needs.",
    benefits: [
      "Unlimited API requests with webhooks",
      "Custom document ingestion pipeline",
      "Dedicated account manager",
      "On-premise or cloud deployment options",
    ],
    icon: "Building",
  },
];

function SolutionIcon({ name, size = 48 }: { name: string; size?: number }) {
  const base = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  switch (name) {
    case "Package":
      return (
        <svg {...base}>
          <path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </svg>
      );
    case "Truck":
      return (
        <svg {...base}>
          <path d="M1 3h15v13H1zM16 8h4l3 3v5h-7V8z" />
          <circle cx="5.5" cy="18.5" r="2.5" />
          <circle cx="18.5" cy="18.5" r="2.5" />
        </svg>
      );
    case "Navigation":
      return (
        <svg {...base}>
          <polygon points="3 11 22 2 13 21 11 13 3 11" />
        </svg>
      );
    case "Building":
      return (
        <svg {...base}>
          <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
          <path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01" />
        </svg>
      );
    default:
      return <svg {...base}><circle cx="12" cy="12" r="10" /></svg>;
  }
}

export default function SolutionsPage() {
  return (
    <div style={{ paddingBottom: "6rem" }}>
      {/* Hero */}
      <section
        style={{
          padding: "6rem 0 4rem",
          textAlign: "center",
        }}
      >
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
            Solutions for Every Trade Role
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
            Whether you import, export, or move freight — {process.env.NEXT_PUBLIC_APP_NAME} adapts to your workflow with
            role-specific intelligence and automation.
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

      {/* Solutions grid */}
      <section className="section-container">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {solutions.map((solution) => (
            <article
              key={solution.id}
              id={solution.id}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "2rem",
                display: "flex",
                flexDirection: "column",
                gap: "1.25rem",
                transition: "transform var(--transition-base), box-shadow var(--transition-base)",
              }}
            >
              <div
                style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "var(--radius-lg)",
                  background: "rgba(59 130 246 / 0.1)",
                  color: "var(--color-brand-400)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <SolutionIcon name={solution.icon} />
              </div>
              <div>
                <h2
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 700,
                    color: "var(--text-primary)",
                    marginBottom: "0.25rem",
                  }}
                >
                  {solution.title}
                </h2>
                <p
                  style={{
                    fontSize: "0.9375rem",
                    color: "var(--color-brand-400)",
                    fontWeight: 500,
                  }}
                >
                  {solution.subtitle}
                </p>
              </div>
              <p
                style={{
                  fontSize: "1rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                }}
              >
                {solution.description}
              </p>
              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  margin: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.75rem",
                }}
              >
                {solution.benefits.map((benefit, idx) => (
                  <li
                    key={idx}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "0.625rem",
                      fontSize: "0.9375rem",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 18 18"
                      fill="none"
                      style={{
                        color: "var(--color-accent-500)",
                        flexShrink: 0,
                        marginTop: "0.125rem",
                      }}
                    >
                      <path
                        d="M6 9l2 2 4-4"
                        stroke="currentColor"
                        strokeWidth="1.75"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    {benefit}
                  </li>
                ))}
              </ul>
            </article>
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
            Ready to transform your trade operations?
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 2rem",
            }}
          >
            Join hundreds of trading companies already using {process.env.NEXT_PUBLIC_APP_NAME} to streamline their operations.
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
            Get Started
          </Link>
        </div>
      </section>
    </div>
  );
}