import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Voice Assistant",
  description:
    `Hands-free trade intelligence with ${process.env.NEXT_PUBLIC_APP_NAME}'s Voice Assistant. Speak your queries and get instant answers on HS codes, tariffs, and shipping rates.`,
};

const features = [
  {
    id: "naturalConversations",
    title: "Natural Conversations",
    description:
      "Talk naturally as you would with a trade expert. No need to type or navigate complex menus — just ask your question and get an instant answer.",
    icon: "MessageCircle",
  },
  {
    id: "handsFree",
    title: "Hands-Free Operation",
    description:
      `Use ${process.env.NEXT_PUBLIC_APP_NAME} while on the go. Check HS codes during warehouse visits or verify tariffs during client calls — all voice-activated.`,
    icon: "Mic",
  },
  {
    id: "instantAnswers",
    title: "Instant Answers",
    description:
      "Get immediate responses on tariff rates, SRO exemptions, shipping costs, and compliance requirements without switching screens.",
    icon: "Zap",
  },
  {
    id: "fullAccess",
    title: "Full Platform Access",
    description:
      "Everything available in text chat is accessible via voice — HS lookup, tariff analysis, route planning, and knowledge graph queries.",
    icon: "Database",
  },
];

const useCases = [
  {
    id: "warehouse",
    title: "Warehouse Operations",
    description: "Quickly classify products as you inspect inventory. Just say the product name and get the HS code instantly.",
  },
  {
    id: "clientCalls",
    title: "Client Consultations",
    description: "Check live shipping rates and tariff duties during client calls without breaking conversation flow.",
  },
  {
    id: "tradeShows",
    title: "Trade Shows & Events",
    description: "Answer attendee questions about market access, tariffs, and compliance in real time.",
  },
  {
    id: "logistics",
    title: "Logistics Coordination",
    description: "Verify shipping routes and costs while on the warehouse floor or at the port.",
  },
];

function FeatureIcon({ name, size = 24 }: { name: string; size?: number }) {
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
    case "MessageCircle":
      return (
        <svg {...base}>
          <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.8a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
        </svg>
      );
    case "Mic":
      return (
        <svg {...base}>
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="22" />
        </svg>
      );
    case "Zap":
      return (
        <svg {...base}>
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
      );
    case "Database":
      return (
        <svg {...base}>
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
        </svg>
      );
    default:
      return <svg {...base}><circle cx="12" cy="12" r="10" /></svg>;
  }
}

export default function VoiceAssistantPage() {
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
            Voice Assistant
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
            Hands-free trade intelligence. Speak your queries and get instant answers on
            HS codes, tariffs, shipping rates, and compliance requirements.
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
              Try Voice Demo
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
              View Plans
            </Link>
          </div>
        </div>
      </section>

      {/* Demo preview */}
      <section className="section-container" style={{ marginBottom: "4rem" }}>
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "2rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "1.5rem",
          }}
        >
          <div
            style={{
              width: "80px",
              height: "80px",
              borderRadius: "50%",
              background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 40px -8px rgba(59 130 246 / 0.5)",
            }}
          >
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="22" />
            </svg>
          </div>
          <div style={{ textAlign: "center" }}>
            <p
              style={{
                fontSize: "1.125rem",
                color: "var(--text-secondary)",
                fontStyle: "italic",
                maxWidth: "400px",
              }}
            >
              "What's the HS code for lithium-ion batteries and what's the current US import duty?"
            </p>
            <div
              style={{
                marginTop: "1rem",
                padding: "0.5rem 1rem",
                borderRadius: "var(--radius-full)",
                background: "rgba(16 185 129 / 0.1)",
                color: "var(--color-accent-500)",
                fontSize: "0.875rem",
                fontWeight: 500,
                display: "inline-block",
              }}
            >
              Processing...
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
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
          Why Use Voice?
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
          Speed, convenience, and accessibility for trade professionals on the move.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {features.map((feature) => (
            <div
              key={feature.id}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "1.75rem",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              <div
                style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "var(--radius-lg)",
                  background: "rgba(59 130 246 / 0.1)",
                  color: "var(--color-brand-400)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <FeatureIcon name={feature.icon} />
              </div>
              <h3
                style={{
                  fontSize: "1.125rem",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                }}
              >
                {feature.title}
              </h3>
              <p
                style={{
                  fontSize: "0.9375rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                }}
              >
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Use cases */}
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
            Perfect For
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
            Industries and scenarios where voice shines.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {useCases.map((useCase) => (
              <div
                key={useCase.id}
                style={{
                  background: "var(--bg-muted)",
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
                    fontSize: "0.9375rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.5,
                  }}
                >
                  {useCase.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing note */}
      <section className="section-container" style={{ marginBottom: "4rem" }}>
        <div
          style={{
            background: "var(--bg-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "2rem",
            textAlign: "center",
          }}
        >
          <h2
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "0.75rem",
            }}
          >
            Available in Professional & Enterprise Plans
          </h2>
          <p
            style={{
              fontSize: "1rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 1.5rem",
            }}
          >
            Voice Assistant is included in Professional (60 min/month) and Enterprise
            (unlimited) plans.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link
              href="/pricing"
              style={{
                padding: "0.625rem 1.25rem",
                borderRadius: "var(--radius-full)",
                fontSize: "0.9375rem",
                fontWeight: 600,
                color: "white",
                background: "var(--color-brand-500)",
                textDecoration: "none",
              }}
            >
              View Pricing
            </Link>
            <Link
              href="/contact"
              style={{
                padding: "0.625rem 1.25rem",
                borderRadius: "var(--radius-full)",
                fontSize: "0.9375rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                border: "1px solid var(--border-subtle)",
                textDecoration: "none",
              }}
            >
              Contact Sales
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ preview */}
      <section className="section-container">
        <h2
          style={{
            fontSize: "clamp(1.5rem, 3vw, 2rem)",
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: "2rem",
            textAlign: "center",
          }}
        >
          Frequently Asked Questions
        </h2>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
            maxWidth: "700px",
            margin: "0 auto",
          }}
        >
          {[
            {
              q: "Is voice secure for confidential trade queries?",
              a: "Yes. All voice conversations are encrypted end-to-end. Enterprise clients can enable additional audit logging.",
            },
            {
              q: "Can I transcribe voice calls for records?",
              a: "Yes. Every voice session is automatically transcribed and saved to your conversation history.",
            },
            {
              q: "What languages are supported?",
              a: "Currently English, with support for Urdu and regional languages coming soon.",
            },
          ].map((faq, idx) => (
            <div
              key={idx}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                padding: "1.25rem",
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
                {faq.q}
              </h3>
              <p
                style={{
                  fontSize: "0.9375rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                }}
              >
                {faq.a}
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
            Ready to go hands-free?
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 2rem",
            }}
          >
            Start your free trial and experience voice-powered trade intelligence.
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