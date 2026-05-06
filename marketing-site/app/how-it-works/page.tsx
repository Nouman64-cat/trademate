// app/how-it-works/page.tsx
import type { Metadata } from "next";
import Link from "next/link";
import { platformStats } from "@/lib/static-data";

export const metadata: Metadata = {
  title: "How It Works",
  description:
    `See how ${process.env.NEXT_PUBLIC_APP_NAME}'s multi-agent AI pipeline classifies queries, queries the knowledge graph, retrieves documents, and delivers streaming trade answers in under 3 seconds.`,
};

// ── Step data ─────────────────────────────────────────────────────────────
const steps = [
  {
    number: "01",
    title: "You Ask",
    subtitle: "Natural language — typed or spoken",
    description:
      `Type any trade question in plain English, or use the voice interface for hands-free queries. No special syntax, no form fields. ${process.env.NEXT_PUBLIC_APP_NAME} understands context from the full conversation history.`,
    detail: "Examples: \"What's the HS code for surgical gloves?\", \"Show me the cheapest sea route from Karachi to LA\", \"Are there any SRO exemptions for textile machinery?\"",
    accent: "var(--color-brand-400)",
    accentBg: "rgba(59,130,246,0.1)",
    accentBorder: "rgba(59,130,246,0.2)",
  },
  {
    number: "02",
    title: "AI Routes",
    subtitle: "LangGraph classifies and selects tools",
    description:
      "The LangGraph state machine classifies your intent and determines which tools to invoke — Knowledge Graph for structured tariff data, Pinecone for regulatory documents, Freightos for live rates. Multiple tools run concurrently.",
    detail: "Under the hood: gpt-5.4 reads your query and the conversation context, then constructs a tool call plan. Tool selection is deterministic — no hallucination of data.",
    accent: "#a78bfa",
    accentBg: "rgba(139,92,246,0.1)",
    accentBorder: "rgba(139,92,246,0.2)",
  },
  {
    number: "03",
    title: "Data Retrieved",
    subtitle: "Three live sources, queried in parallel",
    description:
      "Concurrently: Memgraph returns HS codes, tariff rates, exemptions, and anti-dumping duties via Cypher. Pinecone retrieves the most relevant trade policy chunks via semantic search. Freightos returns live FCL/LCL spot quotes.",
    detail: "58,000+ HS codes, 340K+ graph relationships, and 12,400+ embedded documents are all searchable in milliseconds.",
    accent: "var(--color-accent-500)",
    accentBg: "rgba(16,185,129,0.1)",
    accentBorder: "rgba(16,185,129,0.2)",
  },
  {
    number: "04",
    title: "Answer Delivered",
    subtitle: "Streamed, cited, and actionable",
    description:
      "gpt-5.4 synthesizes the retrieved data into a clear, cited answer that streams token-by-token. Complex responses render rich widgets: route cost breakdowns, HS code tables, tariff comparisons — directly in the chat.",
    detail: "Average end-to-end response time including live rate fetching: under 3 seconds. Every answer references its data source.",
    accent: "#fb923c",
    accentBg: "rgba(249,115,22,0.1)",
    accentBorder: "rgba(249,115,22,0.2)",
  },
];

// ── Tech stack rows ────────────────────────────────────────────────────────
const techStack = [
  { layer: "AI Orchestration", tech: "LangGraph StateGraph + gpt-5.4", detail: "Multi-step reasoning, concurrent tool execution" },
  { layer: "Structured Data", tech: "Memgraph (Bolt) + Cypher", detail: "58K HS codes, 340K+ relationships" },
  { layer: "Semantic Search", tech: "Pinecone + OpenAI Embeddings", detail: "12,400+ trade docs, RAG retrieval" },
  { layer: "Live Market Data", tech: "Freightos FaaS API", detail: "Real-time FCL/LCL ocean & air quotes" },
  { layer: "Delivery", tech: "FastAPI SSE → Next.js App Router", detail: "Token-level streaming, <3s TTFB" },
  { layer: "Background Jobs", tech: "Celery + Redis", detail: "Hourly research runner, daily personalisation" },
];

export default function HowItWorksPage() {
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
        <div className="bg-orb bg-orb-brand" style={{ width: "480px", height: "480px", top: "-160px", left: "-80px", opacity: 0.22 }} />
        <div className="bg-orb bg-orb-accent" style={{ width: "320px", height: "320px", bottom: "-80px", right: "-60px", opacity: 0.16 }} />

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
            Under the Hood
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
            From question to{" "}
            <span className="text-gradient">answer in seconds</span>
          </h1>

          <p
            style={{
              fontSize: "1.0625rem",
              color: "var(--text-secondary)",
              lineHeight: 1.7,
              maxWidth: "540px",
              margin: "0 auto",
            }}
          >
            {process.env.NEXT_PUBLIC_APP_NAME}&apos;s multi-agent pipeline combines a knowledge graph,
            vector search, and live market data into a single conversational
            interface.
          </p>
        </div>
      </section>

      {/* ── 4-Step Flow ───────────────────────────────────────────────── */}
      <section style={{ paddingBottom: "5rem" }}>
        <div className="section-container">
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {steps.map((step, i) => (
              <div
                key={step.number}
                style={{
                  display: "grid",
                  gap: "2rem",
                  alignItems: "start",
                }}
                className={`step-row ${i % 2 === 1 ? "step-row-reverse" : ""}`}
              >
                {/* Number + connector */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: "0",
                  }}
                  className="step-connector"
                >
                  <div
                    style={{
                      width: "64px",
                      height: "64px",
                      borderRadius: "var(--radius-xl)",
                      background: step.accentBg,
                      border: `2px solid ${step.accentBorder}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "1.375rem",
                      fontWeight: 800,
                      color: step.accent,
                      letterSpacing: "-0.02em",
                      flexShrink: 0,
                    }}
                  >
                    {step.number}
                  </div>
                  {i < steps.length - 1 && (
                    <div
                      style={{
                        width: "2px",
                        height: "100%",
                        minHeight: "40px",
                        background: `linear-gradient(to bottom, ${step.accentBorder}, transparent)`,
                        marginTop: "0.5rem",
                      }}
                    />
                  )}
                </div>

                {/* Content card */}
                <div
                  style={{
                    background: "var(--bg-surface)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-xl)",
                    padding: "2rem",
                  }}
                >
                  <p
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      letterSpacing: "0.07em",
                      textTransform: "uppercase",
                      color: step.accent,
                      marginBottom: "0.5rem",
                    }}
                  >
                    {step.subtitle}
                  </p>
                  <h2
                    style={{
                      fontSize: "1.5rem",
                      fontWeight: 800,
                      letterSpacing: "-0.03em",
                      color: "var(--text-primary)",
                      marginBottom: "0.875rem",
                    }}
                  >
                    {step.title}
                  </h2>
                  <p style={{ color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: "1rem", fontSize: "0.9375rem" }}>
                    {step.description}
                  </p>
                  <p
                    style={{
                      fontSize: "0.8125rem",
                      color: "var(--text-muted)",
                      fontFamily: "var(--font-mono)",
                      padding: "0.75rem 1rem",
                      borderRadius: "var(--radius-md)",
                      background: "var(--bg-muted)",
                      border: "1px solid var(--border-subtle)",
                      lineHeight: 1.6,
                    }}
                  >
                    {step.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Platform Stats ────────────────────────────────────────────── */}
      <section
        style={{
          background: "var(--bg-subtle)",
          borderTop: "1px solid var(--border-subtle)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "4rem 0",
        }}
      >
        <div className="section-container">
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <h2
              style={{
                fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
                fontWeight: 800,
                letterSpacing: "-0.03em",
                marginBottom: "0.75rem",
              }}
            >
              By the numbers
            </h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: "420px", margin: "0 auto", lineHeight: 1.6 }}>
              The scale of knowledge powering every answer.
            </p>
          </div>

          <div className="stats-grid">
            {platformStats.map((stat) => (
              <div
                key={stat.id}
                style={{
                  textAlign: "center",
                  padding: "1.5rem 1rem",
                  borderRadius: "var(--radius-lg)",
                  border: "1px solid var(--border-subtle)",
                  background: "var(--bg-surface)",
                }}
              >
                <p
                  style={{
                    fontSize: "clamp(1.75rem, 3vw, 2.25rem)",
                    fontWeight: 900,
                    letterSpacing: "-0.04em",
                    lineHeight: 1,
                    marginBottom: "0.375rem",
                    color: "var(--color-brand-400)",
                  }}
                >
                  {stat.value}
                </p>
                <p style={{ fontWeight: 700, fontSize: "0.875rem", color: "var(--text-primary)", marginBottom: "0.25rem" }}>
                  {stat.label}
                </p>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  {stat.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Tech Stack ────────────────────────────────────────────────── */}
      <section style={{ padding: "5rem 0" }}>
        <div className="section-container">
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <h2
              style={{
                fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
                fontWeight: 800,
                letterSpacing: "-0.03em",
                marginBottom: "0.75rem",
              }}
            >
              The stack behind the answers
            </h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: "460px", margin: "0 auto", lineHeight: 1.6 }}>
              Purpose-built with best-in-class components for trade intelligence.
            </p>
          </div>

          <div
            style={{
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-xl)",
              overflow: "hidden",
              background: "var(--bg-surface)",
            }}
          >
            {techStack.map((row, i) => (
              <div
                key={row.layer}
                style={{
                  display: "grid",
                  padding: "1.25rem 1.75rem",
                  borderBottom: i < techStack.length - 1 ? "1px solid var(--border-subtle)" : "none",
                  alignItems: "center",
                  gap: "1rem",
                }}
                className="tech-row"
              >
                <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>
                  {row.layer}
                </p>
                <p style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                  {row.tech}
                </p>
                <p style={{ fontSize: "0.8375rem", color: "var(--text-secondary)" }}>
                  {row.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────── */}
      <section
        style={{
          background: "var(--bg-subtle)",
          borderTop: "1px solid var(--border-subtle)",
          padding: "4rem 0",
          textAlign: "center",
        }}
      >
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2rem)",
              fontWeight: 800,
              letterSpacing: "-0.03em",
              marginBottom: "1rem",
            }}
          >
            See every step live — not just a slideshow
          </h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2rem", maxWidth: "440px", margin: "0 auto 2rem", lineHeight: 1.6 }}>
            In a 30-minute demo we run a real query end-to-end so you can see
            the pipeline respond in real time.
          </p>
          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link
              href="/contact"
              style={{
                padding: "0.75rem 1.75rem",
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
              href="/features"
              style={{
                padding: "0.75rem 1.75rem",
                borderRadius: "var(--radius-full)",
                border: "1px solid var(--border-default)",
                color: "var(--text-secondary)",
                fontWeight: 500,
                fontSize: "0.9375rem",
              }}
            >
              Explore Features
            </Link>
          </div>
        </div>
      </section>

      <style>{`
        .step-row {
          grid-template-columns: 64px 1fr;
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1rem;
        }
        .tech-row {
          grid-template-columns: 1fr;
        }
        @media (min-width: 640px) {
          .stats-grid { grid-template-columns: repeat(3, 1fr); }
          .tech-row { grid-template-columns: 160px 1fr 1fr; }
        }
        @media (min-width: 1024px) {
          .stats-grid { grid-template-columns: repeat(6, 1fr); }
        }
      `}</style>
    </>
  );
}
