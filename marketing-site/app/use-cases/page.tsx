import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Use Cases",
  description:
    `Explore how ${process.env.NEXT_PUBLIC_APP_NAME} powers real-world trade scenarios: importing consumer electronics from China, exporting textiles to the US, shipping automotive parts, and more.`,
};

const useCases = [
  {
    id: "consumer-electronics",
    title: "Consumer Electronics Import",
    industry: "Electronics",
    scenario: "Importing laptops and components from China to Pakistan",
    challenge:
      "HS code classification for 50+ different products, ensuring correct duty rates, and identifying SRO exemptions for tech components.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME} instantly classifies each product, flags applicable SROs (like SRO 653(I)/2023 for mobile phones), and calculates DDP landed costs including customs duties.`,
    features: ["HS Code Intelligence", "Tariff Analysis", "DDP Calculations"],
    company: "TechStar Electronics",
  },
  {
    id: "textile-export",
    title: "Textile Export to US Market",
    industry: "Textiles & Apparel",
    scenario: "Exporting finished garments from Pakistan to US retail chains",
    challenge:
      "Understanding US import tariffs, rules of origin requirements, and ensuring competitive landed costs against competitors from Bangladesh and Vietnam.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME} compares US HTS codes across origins, identifies GSP+ eligibility, and projects landed cost advantages for each market entry strategy.`,
    features: ["Multi-Country Comparison", "GSP Analysis", "Market Entry Intelligence"],
    company: "Royal Textiles",
  },
  {
    id: "auto-parts",
    title: "Automotive Spare Parts",
    industry: "Automotive",
    scenario: "Sourcing and shipping auto parts between US, China, and UAE",
    challenge:
      "Complex duty structures, parts that cross multiple HS categories, and managing anti-dumping duties on specific components.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME} navigates the HS complexity, alerts on anti-dumping duties by origin, and provides comprehensive DDP breakdowns for each shipping route.`,
    features: ["HS Code Intelligence", "Anti-Dumping Alerts", "Route Optimization"],
    company: "MotorWay Auto",
  },
  {
    id: "pharmaceuticals",
    title: "Pharmaceutical Imports",
    industry: "Healthcare & Pharma",
    scenario: "Importing medicines and medical devices into Pakistan",
    challenge:
      "Navigating DRAP regulations, identifying pharmaceutical-specific HS codes, and managing controlled items that require special permits.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME} provides specialized HS classifications for pharma products, identifies DRAP registration requirements, and flags items requiring special clearances.`,
    features: ["Pharma HS Codes", "Regulatory Alerts", "Compliance Guidance"],
    company: "HealthCare Plus",
  },
  {
    id: "food-beverages",
    title: "Food & Beverage Import",
    industry: "Food & Beverages",
    scenario: "Importing packaged foods from Europe and Southeast Asia",
    challenge:
      "Meeting food safety standards, correctly classifying food products, and identifying applicable cess and additional duties.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME} classifies food products at the correct HS level, identifies all applicable cess and additional levies, and flags labeling requirements.`,
    features: ["Food HS Classification", "Cess Identification", "Labeling Guidance"],
    company: "Fresh Foods Co.",
  },
  {
    id: "machinery",
    title: "Industrial Machinery",
    industry: "Manufacturing",
    scenario: "Importing industrial machinery for manufacturing plants",
    challenge:
      "Capital goods often qualify for exemptions, but identifying which machinery qualifies and ensuring proper documentation is critical.",
    solution:
      `${process.env.NEXT_PUBLIC_APP_NAME} identifies SRO tax exemptions for machinery, calculates total project costs including installation, and provides comprehensive compliance checklists.`,
    features: ["Exemption Analysis", "DDP Calculations", "Compliance Checklists"],
    company: "Industrial Corp",
  },
];

export default function UseCasesPage() {
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
            Use Cases
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
            See how traders across industries use {process.env.NEXT_PUBLIC_APP_NAME} to classify products,
            calculate costs, and ensure compliance.
          </p>
        </div>
      </section>

      {/* Use cases list */}
      <section className="section-container">
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "2rem",
          }}
        >
          {useCases.map((useCase) => (
            <article
              key={useCase.id}
              id={useCase.id}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "2rem",
                display: "grid",
                gridTemplateColumns: "1fr",
                gap: "1.5rem",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "var(--color-brand-400)",
                    background: "rgba(59 130 246 / 0.1)",
                    padding: "0.25rem 0.625rem",
                    borderRadius: "var(--radius-full)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  {useCase.industry}
                </span>
                <h2
                  style={{
                    fontSize: "1.75rem",
                    fontWeight: 700,
                    color: "var(--text-primary)",
                    marginTop: "0.75rem",
                    marginBottom: "0.5rem",
                  }}
                >
                  {useCase.title}
                </h2>
                <p
                  style={{
                    fontSize: "1.0625rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                  }}
                >
                  {useCase.scenario}
                </p>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
                  gap: "1.5rem",
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
                      marginBottom: "0.5rem",
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
                    {useCase.challenge}
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
                      marginBottom: "0.5rem",
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
                    {useCase.solution}
                  </p>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "1rem",
                  paddingTop: "1rem",
                  borderTop: "1px solid var(--border-subtle)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                  }}
                >
                  {useCase.features.map((feature, idx) => (
                    <span
                      key={idx}
                      style={{
                        fontSize: "0.8125rem",
                        fontWeight: 500,
                        color: "var(--text-secondary)",
                        background: "var(--bg-muted)",
                        padding: "0.375rem 0.75rem",
                        borderRadius: "var(--radius-full)",
                      }}
                    >
                      {feature}
                    </span>
                  ))}
                </div>
                <span
                  style={{
                    fontSize: "0.875rem",
                    color: "var(--text-muted)",
                    fontStyle: "italic",
                  }}
                >
                  Real use case from {useCase.company}
                </span>
              </div>
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
            Have a specific use case in mind?
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 2rem",
            }}
          >
            Our team can help you understand how {process.env.NEXT_PUBLIC_APP_NAME} addresses your specific trade scenario.
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
            Talk to an Expert
          </Link>
        </div>
      </section>
    </div>
  );
}