import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Enterprise",
  description: `${process.env.NEXT_PUBLIC_APP_NAME} Enterprise delivers unlimited API access, custom document ingestion, dedicated support, and enterprise-grade security for large trading organizations and logistics platforms.`,
};

const capabilities = [
  {
    id: "api",
    title: "Unlimited API Access",
    description:
      "Integrate trade intelligence directly into your ERP, TMS, or custom workflows. Unlimited requests, webhooks, and a dedicated rate-limit tier with no throttling.",
  },
  {
    id: "ingestion",
    title: "Custom Document Ingestion",
    description:
      "Upload proprietary tariff guides, internal SOP documents, and regulatory filings. Our pipeline semantically chunks and indexes them into your private knowledge base.",
  },
  {
    id: "support",
    title: "Dedicated Account Manager",
    description:
      "A named account manager handles onboarding, training, and ongoing feature requests. Direct escalation path with a guaranteed response SLA.",
  },
  {
    id: "security",
    title: "Enterprise-Grade Security",
    description:
      "SSO and SAML 2.0 support, role-based access controls, audit logs, and data residency options. Meets the compliance requirements of regulated industries.",
  },
  {
    id: "collaboration",
    title: "Unlimited Team Seats",
    description:
      "Deploy across your entire compliance, procurement, and logistics teams with no per-seat cap. Centralised user management with department-level access controls.",
  },
  {
    id: "sla",
    title: "Guaranteed Uptime SLA",
    description:
      "99.9% uptime commitment backed by a contractual SLA. Priority infrastructure, dedicated failover, and a real-time status page for your IT operations team.",
  },
];

const includedFeatures = [
  { id: "queries",   title: "Unlimited AI chat queries",           description: "No monthly cap on trade queries across all users." },
  { id: "hscodes",   title: "Full HS code coverage (PK + US)",     description: "Pakistan PCT and US HTS schedules with extended classifications." },
  { id: "freight",   title: "Live Freightos rate queries",         description: "Unlimited real-time FCL/LCL and air freight spot rates." },
  { id: "voice",     title: "Voice assistant (unlimited)",         description: "Hands-free trade consultations with no session time limit." },
  { id: "kg",        title: "Knowledge graph explorer",            description: "Full access to 340K+ HS code relationships and Cypher search." },
  { id: "apiaccess", title: "API access + webhooks",               description: "Unlimited requests, event-driven webhooks, and OpenAPI spec." },
  { id: "custom",    title: "Custom document ingestion",           description: "Private pipeline for your proprietary compliance documents." },
  { id: "sso",       title: "SSO & SAML 2.0",                     description: "Connect to your identity provider — Okta, Azure AD, Google Workspace." },
  { id: "audit",     title: "Audit logs & access controls",        description: "Full query history, role-based permissions, and exportable audit trails." },
  { id: "manager",   title: "Dedicated account manager",           description: "Named contact for onboarding, QBRs, and escalations." },
];

const integrations = [
  {
    id: "erp",
    title: "ERP Integration",
    description:
      "Connect to SAP, Oracle, or Microsoft Dynamics. Push HS codes, duty rates, and landed cost calculations directly into your procurement workflows.",
  },
  {
    id: "customs",
    title: "Customs Management Systems",
    description:
      "Pre-validate classifications before submitting to your CMS. Reduce customs queries and clearance delays caused by HS code mismatches.",
  },
  {
    id: "tms",
    title: "Logistics TMS",
    description:
      "Feed live Freightos rates and route data into your transportation management system. Automate carrier selection based on DDP cost calculations.",
  },
  {
    id: "bi",
    title: "Data Warehouse & BI",
    description:
      "Stream tariff data, query logs, and cost metrics into Snowflake, BigQuery, or Redshift. Build trade intelligence dashboards on top of your data.",
  },
];

export default function EnterprisePage() {
  return (
    <div style={{ paddingBottom: "6rem" }}>

      {/* ── Hero ──────────────────────────────────────────────────────────────── */}
      <section style={{ padding: "6rem 0 4rem", textAlign: "center" }}>
        <div className="section-container">
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.375rem 0.875rem",
              borderRadius: "var(--radius-full)",
              fontSize: "0.75rem",
              fontWeight: 600,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              color: "var(--color-brand-500)",
              background: "rgba(59, 130, 246, 0.08)",
              border: "1px solid rgba(59, 130, 246, 0.2)",
              marginBottom: "1.5rem",
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "var(--color-accent-500)",
                display: "inline-block",
              }}
            />
            Enterprise Solution
          </div>

          <h1
            style={{
              fontSize: "clamp(2.5rem, 5vw, 3.5rem)",
              fontWeight: 700,
              letterSpacing: "-0.04em",
              color: "var(--text-primary)",
              marginBottom: "1rem",
            }}
          >
            Trade Intelligence Built for Scale
          </h1>

          <p
            style={{
              fontSize: "clamp(1.125rem, 2vw, 1.25rem)",
              color: "var(--text-secondary)",
              maxWidth: "620px",
              margin: "0 auto 2rem",
              lineHeight: 1.6,
            }}
          >
            Unlimited API access, custom data ingestion, and dedicated support — designed
            for large trading organisations with complex compliance and integration needs.
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
              Contact Sales
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

      {/* ── Capabilities ──────────────────────────────────────────────────────── */}
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
          Built for Enterprise Demands
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
          Everything a large organisation needs to operationalise trade intelligence at scale.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {capabilities.map((item) => (
            <div
              key={item.id}
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
                {item.title}
              </h3>
              <p
                style={{
                  fontSize: "0.9375rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                }}
              >
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── What's Included ───────────────────────────────────────────────────── */}
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
            Everything Included
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
            The full platform, unlimited, plus capabilities exclusive to Enterprise.
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1rem",
            }}
          >
            {includedFeatures.map((feature) => (
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
                  aria-hidden="true"
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

      {/* ── Integration Options ───────────────────────────────────────────────── */}
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
          Fits Into Your Existing Stack
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
          {process.env.NEXT_PUBLIC_APP_NAME} connects to the systems your teams already rely on.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {integrations.map((item) => (
            <div
              key={item.id}
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
                {item.title}
              </h3>
              <p
                style={{
                  fontSize: "0.875rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.5,
                }}
              >
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────────── */}
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
            Ready to Deploy at Scale?
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 2rem",
            }}
          >
            Talk to our sales team to scope a deployment tailored to your organisation&apos;s
            compliance and integration requirements.
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
            Contact Sales
          </Link>
        </div>
      </section>

    </div>
  );
}
