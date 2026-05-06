import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Case Studies",
  description:
    "See how trading companies transformed their operations with TradeMate. Real success stories from importers, exporters, and freight forwarders.",
};

const caseStudies = [
  {
    id: "novatex",
    company: "NovaTex Exports",
    industry: "Textiles",
    role: "Exporter",
    location: "Lahore, Pakistan",
    logo: "N",
    stats: [
      { label: "Time Saved", value: "85%", description: "Reduced classification time" },
      { label: "Duty Savings", value: "$120K", description: "Annual duty optimization" },
      { label: "HS Accuracy", value: "99.9%", description: "Classification accuracy" },
    ],
    challenge:
      "NovaTex was spending hours manually classifying products across 500+ SKUs. HS code errors were causing customs delays and unexpected duty costs. They needed a faster, more accurate way to classify textile products.",
    solution:
      "TradeMate's AI automatically classifies each product and identifies applicable SRO exemptions. The team now generates accurate HS codes in seconds with full duty breakdowns.",
    result:
      "85% reduction in classification time, $120K annual duty savings from correct SRO identification, and zero customs delays in the past year.",
  },
  {
    id: "meridian",
    company: "Meridian Freight",
    industry: "Logistics",
    role: "Freight Forwarder",
    location: "Chicago, USA",
    logo: "M",
    stats: [
      { label: "Quote Time", value: "85%", description: "Faster quote generation" },
      { label: "Client Growth", value: "+40%", description: "New clients YoY" },
      { label: "Revenue", value: "+35%", description: "Increased revenue" },
    ],
    challenge:
      "Meridian was losing deals to competitors who could provide faster quotes. Their team spent hours manually researching tariffs and shipping routes for each client request.",
    solution:
      "TradeMate's live Freightos integration and AI chat gives instant quotes. They now provide complete DDP breakdowns in seconds, not hours.",
    result:
      "85% faster quote generation, won 40% more deals, and 35% revenue increase. Clients love the instant, accurate cost breakdowns.",
  },
  {
    id: "tradelink",
    company: "TradeLink Technologies",
    industry: "Electronics",
    role: "Importer",
    location: "Islamabad, Pakistan",
    logo: "T",
    stats: [
      { label: "API Integration", value: "1 Day", description: "Time to integrate" },
      { label: "Tariff Coverage", value: "100%", description: "PK + US coverage" },
      { label: "Uptime", value: "99.9%", description: "API availability" },
    ],
    challenge:
      "TradeLink needed to integrate trade intelligence into their ERP system. Existing solutions lacked complete data and had poor API reliability.",
    solution:
      "TradeMate's REST API provides complete tariff data with webhooks for real-time updates. Integration took less than a day with comprehensive documentation.",
    result:
      "Fully integrated in 1 day, complete Pakistan + US tariff coverage, and 99.9% API uptime. Their ERP now automatically classifies all imports.",
  },
  {
    id: "healthplus",
    company: "HealthPlus Pharma",
    industry: "Pharmaceuticals",
    role: "Importer",
    location: "Karachi, Pakistan",
    logo: "H",
    stats: [
      { label: "Compliance", value: "100%", description: "DRAP compliance" },
      { label: "Classification", value: "50%", description: "Faster process" },
      { label: "Alerts", value: "24/7", description: "Regulatory monitoring" },
    ],
    challenge:
      "Pharmaceutical imports require strict DRAP compliance. Manual classification risked regulatory issues. They needed a solution that understood pharma-specific requirements.",
    solution:
      "TradeMate's specialized pharma module identifies controlled substances, registers required permits, and flags DRAP-specific HS codes. Real-time alerts keep them updated on regulatory changes.",
    result:
      "100% DRAP compliance, 50% faster classification process, and peace of mind with 24/7 regulatory monitoring.",
  },
];

const testimonials = [
  {
    id: "t-1",
    quote:
      "TradeMate cut our HS code classification time from hours to seconds. What used to require three different databases and a compliance expert is now a single AI-powered query.",
    author: "Zainab Hussain",
    title: "Head of Trade Compliance",
    company: "NovaTex Exports",
  },
  {
    id: "t-2",
    quote:
      "The live Freightos rate integration alone pays for the subscription. Being able to ask 'what's the cheapest sea freight route from Karachi to Los Angeles?' and get an answer instantly is incredibly powerful.",
    author: "James Whitfield",
    title: "Logistics Director",
    company: "Meridian Freight Solutions",
  },
  {
    id: "t-3",
    quote:
      "We integrated TradeMate's API into our ERP in under a day. The tariff data for both Pakistan and the US is remarkably comprehensive.",
    author: "Bilal Chaudhry",
    title: "CTO",
    company: "TradeLink Technologies",
  },
];

export default function CaseStudiesPage() {
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
            Case Studies
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
            Real results from real trading companies. See how TradeMate transforms trade
            operations across importers, exporters, and freight forwarders.
          </p>
        </div>
      </section>

      {/* Case studies */}
      <section className="section-container">
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "3rem",
          }}
        >
          {caseStudies.map((study) => (
            <article
              key={study.id}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "2rem",
                display: "grid",
                gridTemplateColumns: "1fr",
                gap: "2rem",
              }}
            >
              {/* Header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "1rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                  <div
                    style={{
                      width: "56px",
                      height: "56px",
                      borderRadius: "var(--radius-lg)",
                      background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "1.5rem",
                      fontWeight: 700,
                      color: "white",
                    }}
                  >
                    {study.logo}
                  </div>
                  <div>
                    <h2
                      style={{
                        fontSize: "1.5rem",
                        fontWeight: 700,
                        color: "var(--text-primary)",
                      }}
                    >
                      {study.company}
                    </h2>
                    <p
                      style={{
                        fontSize: "0.875rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      {study.industry} • {study.role} • {study.location}
                    </p>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                  gap: "1rem",
                }}
              >
                {study.stats.map((stat, idx) => (
                  <div
                    key={idx}
                    style={{
                      textAlign: "center",
                      padding: "1rem",
                      background: "var(--bg-muted)",
                      borderRadius: "var(--radius-lg)",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "1.5rem",
                        fontWeight: 700,
                        color: "var(--color-brand-400)",
                      }}
                    >
                      {stat.value}
                    </div>
                    <div
                      style={{
                        fontSize: "0.8125rem",
                        fontWeight: 500,
                        color: "var(--text-primary)",
                        marginTop: "0.25rem",
                      }}
                    >
                      {stat.label}
                    </div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      {stat.description}
                    </div>
                  </div>
                ))}
              </div>

              {/* Content */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                  gap: "2rem",
                }}
              >
                <div>
                  <h3
                    style={{
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      marginBottom: "0.75rem",
                    }}
                  >
                    Challenge
                  </h3>
                  <p
                    style={{
                      fontSize: "0.9375rem",
                      color: "var(--text-secondary)",
                      lineHeight: 1.6,
                    }}
                  >
                    {study.challenge}
                  </p>
                </div>
                <div>
                  <h3
                    style={{
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      color: "var(--color-accent-500)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      marginBottom: "0.75rem",
                    }}
                  >
                    Solution
                  </h3>
                  <p
                    style={{
                      fontSize: "0.9375rem",
                      color: "var(--text-secondary)",
                      lineHeight: 1.6,
                    }}
                  >
                    {study.solution}
                  </p>
                </div>
              </div>

              {/* Result */}
              <div
                style={{
                  padding: "1.25rem",
                  background: "rgba(16 185 129 / 0.1)",
                  borderRadius: "var(--radius-lg)",
                  borderLeft: "4px solid var(--color-accent-500)",
                }}
              >
                <h3
                  style={{
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    color: "var(--color-accent-500)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    marginBottom: "0.5rem",
                  }}
                >
                  Result
                </h3>
                <p
                  style={{
                    fontSize: "1rem",
                    color: "var(--text-primary)",
                    fontWeight: 500,
                    lineHeight: 1.6,
                  }}
                >
                  {study.result}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section style={{ padding: "4rem 0" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "2rem",
              textAlign: "center",
            }}
          >
            What Our Clients Say
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {testimonials.map((t) => (
              <div
                key={t.id}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-xl)",
                  padding: "1.75rem",
                }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  style={{ color: "var(--color-brand-400)", marginBottom: "1rem" }}
                >
                  <path
                    d="M3 21c3 0 7-1 7-8V5c0-1-1-2-2-2H6c0 1-2 2-2 2l2 8v10l5-8zM14 21c3 0 7-1 7-8V5c0-1-1-2-2-2h-2c0 1-2 2-2 2l2 8v10l5-8z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  />
                </svg>
                <p
                  style={{
                    fontSize: "1rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                    marginBottom: "1.25rem",
                  }}
                >
                  "{t.quote}"
                </p>
                <div>
                  <div
                    style={{
                      fontSize: "0.9375rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {t.author}
                  </div>
                  <div
                    style={{
                      fontSize: "0.8125rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    {t.title}, {t.company}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "4rem 0", textAlign: "center" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.75rem, 3vw, 2.25rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "1rem",
            }}
          >
            Ready to Write Your Success Story?
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 2rem",
            }}
          >
            Join hundreds of trading companies already using TradeMate.
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