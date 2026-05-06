// app/features/page.tsx
import type { Metadata } from "next";
import Link from "next/link";
import { features } from "@/lib/static-data";
import type { Feature } from "@/lib/static-data";

export const metadata: Metadata = {
  title: "Features",
  description:
    `Explore ${process.env.NEXT_PUBLIC_APP_NAME}'s full feature set: AI trade chat, HS code intelligence, knowledge graph, live shipping rates, tariff analysis, voice assistant, and document pipeline.`,
};

// ── Inline SVG icons matching Lucide React style ───────────────────────────
function FeatureIcon({ name, size = 22 }: { name: string; size?: number }) {
  const p = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  switch (name) {
    case "MessageSquare":
      return <svg {...p}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>;
    case "Search":
      return <svg {...p}><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>;
    case "GitBranch":
      return <svg {...p}><line x1="6" y1="3" x2="6" y2="15" /><circle cx="18" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M18 9a9 9 0 0 1-9 9" /></svg>;
    case "Map":
      return <svg {...p}><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21" /><line x1="9" y1="3" x2="9" y2="18" /><line x1="15" y1="6" x2="15" y2="21" /></svg>;
    case "BarChart2":
      return <svg {...p}><line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" /></svg>;
    case "Mic":
      return <svg {...p}><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="22" /></svg>;
    case "Database":
      return <svg {...p}><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /></svg>;
    default:
      return <svg {...p}><circle cx="12" cy="12" r="10" /></svg>;
  }
}

// ── Category colour tokens ─────────────────────────────────────────────────
const categoryTheme: Record<string, { bg: string; text: string; border: string; iconBg: string }> = {
  "AI Intelligence":    { bg: "rgba(59,130,246,0.1)",  text: "var(--color-brand-400)",  border: "rgba(59,130,246,0.2)",  iconBg: "rgba(59,130,246,0.15)" },
  "Trade Data":         { bg: "rgba(16,185,129,0.1)",  text: "var(--color-accent-500)", border: "rgba(16,185,129,0.2)",  iconBg: "rgba(16,185,129,0.15)" },
  "Knowledge Graph":    { bg: "rgba(139,92,246,0.1)",  text: "#a78bfa",                 border: "rgba(139,92,246,0.2)",  iconBg: "rgba(139,92,246,0.15)" },
  "Logistics":          { bg: "rgba(249,115,22,0.1)",  text: "#fb923c",                 border: "rgba(249,115,22,0.2)",  iconBg: "rgba(249,115,22,0.15)" },
  "Data Infrastructure":{ bg: "rgba(100,116,139,0.1)", text: "var(--text-secondary)",   border: "rgba(100,116,139,0.2)", iconBg: "rgba(100,116,139,0.15)" },
};

// ── Feature card ───────────────────────────────────────────────────────────
function FeatureCard({ feature }: { feature: Feature }) {
  const theme = categoryTheme[feature.category] ?? categoryTheme["AI Intelligence"];
  return (
    <article
      id={feature.slug}
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-xl)",
        padding: "2rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        transition: "border-color var(--transition-base), transform var(--transition-base)",
        scrollMarginTop: "96px",
      }}
      className="feature-card"
    >
      {/* Icon + category */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
        <div
          style={{
            width: "48px",
            height: "48px",
            borderRadius: "var(--radius-md)",
            background: theme.iconBg,
            border: `1px solid ${theme.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: theme.text,
            flexShrink: 0,
          }}
        >
          <FeatureIcon name={feature.icon} />
        </div>
        <span
          style={{
            fontSize: "0.6875rem",
            fontWeight: 600,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            padding: "0.25rem 0.625rem",
            borderRadius: "var(--radius-full)",
            background: theme.bg,
            color: theme.text,
            border: `1px solid ${theme.border}`,
            whiteSpace: "nowrap",
          }}
        >
          {feature.category}
        </span>
      </div>

      {/* Title + tagline */}
      <div>
        <h3
          style={{
            fontSize: "1.1875rem",
            fontWeight: 700,
            letterSpacing: "-0.025em",
            marginBottom: "0.375rem",
            color: "var(--text-primary)",
          }}
        >
          {feature.name}
        </h3>
        <p style={{ fontSize: "0.875rem", color: theme.text, fontWeight: 500, lineHeight: 1.5 }}>
          {feature.tagline}
        </p>
      </div>

      {/* Description */}
      <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.7, flexGrow: 1 }}>
        {feature.description}
      </p>

      {/* Capabilities */}
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {feature.capabilities.map((cap) => (
          <li
            key={cap}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.625rem",
              fontSize: "0.8375rem",
              color: "var(--text-secondary)",
              lineHeight: 1.5,
            }}
          >
            <span
              style={{
                width: "16px",
                height: "16px",
                borderRadius: "50%",
                background: theme.iconBg,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                marginTop: "1px",
              }}
            >
              <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
                <path d="M2 6l3 3 5-5" stroke={theme.text} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            {cap}
          </li>
        ))}
      </ul>

      {/* Tech note */}
      <p
        style={{
          fontSize: "0.75rem",
          color: "var(--text-muted)",
          fontFamily: "var(--font-mono)",
          padding: "0.5rem 0.75rem",
          borderRadius: "var(--radius-sm)",
          background: "var(--bg-muted)",
          border: "1px solid var(--border-subtle)",
          lineHeight: 1.5,
        }}
      >
        {feature.techNote}
      </p>
    </article>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────
export default function FeaturesPage() {
  return (
    <>
      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <section
        style={{
          position: "relative",
          overflow: "hidden",
          paddingTop: "5rem",
          paddingBottom: "4rem",
          textAlign: "center",
        }}
      >
        <div className="bg-orb bg-orb-brand" style={{ width: "500px", height: "500px", top: "-180px", right: "-100px", opacity: 0.25 }} />
        <div className="bg-orb bg-orb-accent" style={{ width: "300px", height: "300px", bottom: "0", left: "-60px", opacity: 0.18 }} />

        <div className="section-container" style={{ position: "relative", zIndex: 1 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.3125rem 0.875rem",
              borderRadius: "var(--radius-full)",
              border: "1px solid rgba(59,130,246,0.3)",
              background: "rgba(59,130,246,0.07)",
              fontSize: "0.8rem",
              fontWeight: 500,
              color: "var(--color-brand-400)",
              marginBottom: "1.75rem",
            }}
          >
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--color-accent-500)", display: "inline-block" }} />
            7 Core Capabilities
          </div>

          <h1
            style={{
              fontSize: "clamp(2rem, 5vw, 3.25rem)",
              fontWeight: 900,
              letterSpacing: "-0.04em",
              lineHeight: 1.1,
              marginBottom: "1.25rem",
            }}
          >
            Everything you need to{" "}
            <span className="text-gradient">trade smarter</span>
          </h1>

          <p
            style={{
              fontSize: "1.0625rem",
              color: "var(--text-secondary)",
              lineHeight: 1.7,
              maxWidth: "560px",
              margin: "0 auto 2.5rem",
            }}
          >
            From instant HS code lookups to live freight quotes — every tool
            you need for the Pakistan–US trade corridor, powered by AI.
          </p>

          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link
              href="/contact"
              style={{
                padding: "0.625rem 1.5rem",
                borderRadius: "var(--radius-full)",
                background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                color: "white",
                fontWeight: 600,
                fontSize: "0.9375rem",
                boxShadow: "var(--shadow-glow)",
              }}
            >
              Request Demo
            </Link>
            <Link
              href="/pricing"
              style={{
                padding: "0.625rem 1.5rem",
                borderRadius: "var(--radius-full)",
                border: "1px solid var(--border-default)",
                color: "var(--text-secondary)",
                fontWeight: 500,
                fontSize: "0.9375rem",
              }}
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* ── Feature Grid ──────────────────────────────────────────────── */}
      <section style={{ paddingTop: "1rem", paddingBottom: "5rem" }}>
        <div className="section-container">
          <div className="features-grid">
            {features.map((feature) => (
              <FeatureCard key={feature.id} feature={feature} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Bottom CTA ────────────────────────────────────────────────── */}
      <section
        style={{
          background: "var(--bg-subtle)",
          borderTop: "1px solid var(--border-subtle)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "4rem 0",
          textAlign: "center",
        }}
      >
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
              fontWeight: 800,
              letterSpacing: "-0.03em",
              marginBottom: "1rem",
            }}
          >
            Ready to see it in action?
          </h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2rem", maxWidth: "460px", margin: "0 auto 2rem", lineHeight: 1.6 }}>
            Book a 30-minute demo and we&apos;ll walk through a live trade query
            from HS code to landed cost.
          </p>
          <Link
            href="/contact"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.75rem 2rem",
              borderRadius: "var(--radius-full)",
              background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
              color: "white",
              fontWeight: 600,
              fontSize: "1rem",
              boxShadow: "var(--shadow-glow)",
            }}
          >
            Book a Demo
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="white" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
        </div>
      </section>

      <style>{`
        .features-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 1.5rem;
        }
        @media (min-width: 768px) {
          .features-grid { grid-template-columns: repeat(2, 1fr); }
        }
        @media (min-width: 1100px) {
          .features-grid { grid-template-columns: repeat(2, 1fr); gap: 2rem; }
        }
        .feature-card:hover {
          border-color: var(--border-default);
          transform: translateY(-2px);
        }
      `}</style>
    </>
  );
}
