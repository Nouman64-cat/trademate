import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "For Freight Forwarders",
  description:
    `${process.env.NEXT_PUBLIC_APP_NAME} helps freight forwarders serve clients faster with instant HS codes, live shipping rates, and AI-powered trade intelligence.`,
};

const benefits = [
  {
    id: "instantQuotes",
    title: "Instant Rate Quotes",
    description: "Fetch live Freightos rates instantly. Provide clients with accurate FCL/LCL quotes in seconds, not hours.",
  },
  {
    id: "hsValidation",
    title: "HS Code Validation",
    description: "Validate client HS codes against official schedules. Catch classification errors before customs clearance.",
  },
  {
    id: "ddpBreakdown",
    title: "DDP Cost Breakdowns",
    description: "Generate complete DDP landed cost breakdowns. Factor in freight, duties, THC, brokerage, MPF, HMF, and all fees.",
  },
  {
    id: "routeOptimization",
    title: "Route Optimization",
    description: "Compare multiple shipping routes. Find the fastest and most cost-effective option for each shipment.",
  },
  {
    id: "clientPortal",
    title: "Client Portal Access",
    description: "Give clients self-service access to HS lookups, rate queries, and shipment tracking.",
  },
  {
    id: "compliance",
    title: "Compliance Confidence",
    description: "Ensure accurate customs documentation. Reduce delays and penalties from classification errors.",
  },
];

const features = [
  { id: "liveRates", title: "Live Freightos Rates", description: "Real-time FCL/LCL quotes" },
  { id: "hsLookup", title: "HS Code Lookup", description: "Pakistan PCT & US HTS" },
  { id: "ddpCalc", title: "DDP Calculator", description: "Complete cost breakdowns" },
  { id: "routeMap", title: "Route Visualization", description: "Interactive map views" },
  { id: "chatAgent", title: "AI Trade Chat", description: "Instant tariff answers" },
  { id: "kgExplorer", title: "Knowledge Graph", description: "Trade relationships" },
];

const useCases = [
  {
    id: "quoteGeneration",
    title: "Quote Generation",
    description: "Create accurate quotes with full DDP breakdowns for client proposals.",
  },
  {
    id: "customsClearance",
    title: "Customs Clearance",
    description: "Validate HS codes and prepare accurate customs documentation.",
  },
  {
    id: "clientConsulting",
    title: "Client Consulting",
    description: "Answer tariff and classification questions during sales calls.",
  },
  {
    id: "routePlanning",
    title: "Route Planning",
    description: "Compare routes and optimize shipping strategies for clients.",
  },
];

const plans = [
  {
    id: "starter",
    name: "Starter",
    description: "Perfect for small forwarding companies",
    price: "49",
    features: ["500 AI queries/mo", "Basic HS lookup", "Email support"],
  },
  {
    id: "professional",
    name: "Professional",
    description: "For growing forwarding teams",
    price: "149",
    features: ["Unlimited queries", "Live rate fetching", "Client portal", "Priority support"],
    popular: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    description: "For large forwarding operations",
    price: "499",
    features: ["Unlimited everything", "Custom integrations", "Dedicated account manager", "SLA"],
  },
];

export default function FreightForwardersPage() {
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
            Trade Intelligence for Freight Forwarders
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
            Serve clients faster with instant quotes, accurate HS codes, and AI-powered
            trade intelligence. Stand out from the competition.
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
          Why Forwarders Choose {process.env.NEXT_PUBLIC_APP_NAME}
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
          Win more clients with faster, more accurate service.
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
            Everything you need to serve clients better.
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
          Common Use Cases
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
          How forwarders use {process.env.NEXT_PUBLIC_APP_NAME} day-to-day.
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

      {/* Pricing preview */}
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
            Simple Pricing
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
            Plans that scale with your business.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {plans.map((plan) => (
              <div
                key={plan.id}
                style={{
                  background: plan.popular ? "rgba(59 130 246 / 0.05)" : "var(--bg-surface)",
                  border: plan.popular ? "2px solid var(--color-brand-400)" : "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-xl)",
                  padding: "1.75rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                }}
              >
                {plan.popular && (
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: "var(--color-brand-400)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Most Popular
                  </span>
                )}
                <div>
                  <h3
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {plan.name}
                  </h3>
                  <p
                    style={{
                      fontSize: "0.875rem",
                      color: "var(--text-muted)",
                      marginTop: "0.25rem",
                    }}
                  >
                    {plan.description}
                  </p>
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.25rem" }}>
                  <span
                    style={{
                      fontSize: "2rem",
                      fontWeight: 700,
                      color: "var(--text-primary)",
                    }}
                  >
                    ${plan.price}
                  </span>
                  <span style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>/mo</span>
                </div>
                <ul
                  style={{
                    listStyle: "none",
                    padding: 0,
                    margin: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.625rem",
                  }}
                >
                  {plan.features.map((feat, idx) => (
                    <li
                      key={idx}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        fontSize: "0.875rem",
                        color: "var(--text-secondary)",
                      }}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 16 16"
                        fill="none"
                        style={{ color: "var(--color-accent-500)" }}
                      >
                        <path
                          d="M6 8l2 2 4-4"
                          stroke="currentColor"
                          strokeWidth="1.75"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      {feat}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
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
            Serve Clients Faster
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 2rem",
            }}
          >
            Stand out from the competition with AI-powered trade intelligence.
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