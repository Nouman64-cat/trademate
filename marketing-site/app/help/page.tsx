import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Help Center",
  description:
    `Get help with ${process.env.NEXT_PUBLIC_APP_NAME}. Find answers to FAQs, troubleshooting guides, and contact support.`,
};

const categories = [
  {
    id: "getting-started",
    title: "Getting Started",
    icon: "rocket",
    articles: [
      { label: `How to sign up for ${process.env.NEXT_PUBLIC_APP_NAME}`, href: "#" },
      { label: "Understanding your dashboard", href: "#" },
      { label: "Your first HS code lookup", href: "#" },
      { label: "Inviting team members", href: "#" },
    ],
  },
  {
    id: "hs-codes",
    title: "HS Code Classification",
    icon: "search",
    articles: [
      { label: "How HS codes work", href: "#" },
      { label: "Finding the right code", href: "#" },
      { label: "Pakistan PCT vs US HTS", href: "#" },
      { label: "Common classification mistakes", href: "#" },
    ],
  },
  {
    id: "tariffs",
    title: "Tariffs & Duties",
    icon: "dollar",
    articles: [
      { label: "Understanding duty rates", href: "#" },
      { label: "SRO exemptions explained", href: "#" },
      { label: "Anti-dumping duties", href: "#" },
      { label: "DDP vs FOB costs", href: "#" },
    ],
  },
  {
    id: "shipping",
    title: "Shipping & Logistics",
    icon: "truck",
    articles: [
      { label: "Getting shipping quotes", href: "#" },
      { label: "Understanding DDP breakdowns", href: "#" },
      { label: "Route optimization", href: "#" },
      { label: "Freightos integration", href: "#" },
    ],
  },
  {
    id: "api",
    title: "API & Integrations",
    icon: "code",
    articles: [
      { label: "Getting your API key", href: "#" },
      { label: "API authentication", href: "#" },
      { label: "Rate limits explained", href: "#" },
      { label: "Webhooks setup", href: "#" },
    ],
  },
  {
    id: "billing",
    title: "Billing & Plans",
    icon: "credit-card",
    articles: [
      { label: "Plan comparison", href: "#" },
      { label: "Upgrading your plan", href: "#" },
      { label: "Team seat pricing", href: "#" },
      { label: "Annual vs monthly billing", href: "#" },
    ],
  },
];

const faqs = [
  {
    id: "faq-1",
    question: "What is an HS code?",
    answer:
      "HS (Harmonized System) codes are a standardized system of names and numbers used to classify traded products. They're 6-12 digits long and determine the tariff rate, regulations, and documentation required for your product. Pakistan uses PCT codes while the US uses HTS codes.",
  },
  {
    id: "faq-2",
    question: `How accurate are ${process.env.NEXT_PUBLIC_APP_NAME}'s HS codes?`,
    answer:
      `${process.env.NEXT_PUBLIC_APP_NAME} achieves 99.7% accuracy on HS code classification, validated against official Pakistan PCT and US HTS schedules. Our AI considers product descriptions, materials, function, and intended use to find the correct code.`,
  },
  {
    id: "faq-3",
    question: "Can I get a refund if I'm not satisfied?",
    answer:
      "Yes, we offer a 14-day free trial on all plans. If you're not satisfied within the first 30 days, contact support for a full refund. Enterprise plans include a custom SLA.",
  },
  {
    id: "faq-4",
    question: "Is my data secure?",
    answer:
      "Absolutely. We use bank-level encryption (AES-256), are SOC 2 compliant, and never share your data. Your trade information stays confidential.",
  },
  {
    id: "faq-5",
    question: `How do I integrate ${process.env.NEXT_PUBLIC_APP_NAME} into my ERP?`,
    answer:
      "Our REST API supports standard OAuth2 authentication. Check our docs for code samples in Python, JavaScript, and cURL. Integration typically takes less than a day.",
  },
  {
    id: "faq-6",
    question: "What's included in the free trial?",
    answer:
      "The free trial includes full Professional plan access: unlimited HS lookups, tariff analysis, DDP calculator, AI chat, and live rate queries. No credit card required.",
  },
];

function CategoryIcon({ name, size = 20 }: { name: string; size?: number }) {
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
    case "rocket":
      return (
        <svg {...base}>
          <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.95-.95 2.6-.95 3.55 0 .95.94.95 2.55 0 3.55L8 22h8l-.45-1.45c.95-.94.95-2.6 0-3.55-.94-.95-2.6-.95-3.55 0z" />
          <path d="M12 15l-3-3" />
          <path d="M8.5 13.5l-3-3" />
        </svg>
      );
    case "search":
      return (
        <svg {...base}>
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
      );
    case "dollar":
      return (
        <svg {...base}>
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
        </svg>
      );
    case "truck":
      return (
        <svg {...base}>
          <path d="M1 3h15v13H1zM16 8h4l3 3v5h-7V8z" />
          <circle cx="5.5" cy="18.5" r="2.5" />
          <circle cx="18.5" cy="18.5" r="2.5" />
        </svg>
      );
    case "code":
      return (
        <svg {...base}>
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
      );
    case "credit-card":
      return (
        <svg {...base}>
          <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
          <line x1="1" y1="10" x2="23" y2="10" />
        </svg>
      );
    default:
      return <svg {...base}><circle cx="12" cy="12" r="10" /></svg>;
  }
}

export default function HelpCenterPage() {
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
            Help Center
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
            Find answers to common questions or get in touch with our support team.
          </p>

          {/* Search */}
          <div
            style={{
              maxWidth: "500px",
              margin: "0 auto",
              position: "relative",
            }}
          >
            <input
              type="text"
              placeholder="Search for help..."
              style={{
                width: "100%",
                padding: "1rem 1rem 1rem 3rem",
                borderRadius: "var(--radius-full)",
                border: "1px solid var(--border-subtle)",
                background: "var(--bg-surface)",
                color: "var(--text-primary)",
                fontSize: "1rem",
              }}
            />
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              style={{
                position: "absolute",
                left: "1rem",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="section-container">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {categories.map((category) => (
            <div
              key={category.id}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "1.5rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  marginBottom: "1rem",
                }}
              >
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "var(--radius-md)",
                    background: "rgba(59 130 246 / 0.1)",
                    color: "var(--color-brand-400)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <CategoryIcon name={category.icon} />
                </div>
                <h2
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                  }}
                >
                  {category.title}
                </h2>
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {category.articles.map((article, idx) => (
                  <li key={idx}>
                    <a
                      href={article.href}
                      style={{
                        display: "block",
                        padding: "0.5rem 0",
                        fontSize: "0.9375rem",
                        color: "var(--text-secondary)",
                        textDecoration: "none",
                        transition: "color var(--transition-fast)",
                      }}
                    >
                      {article.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* FAQs */}
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
            Frequently Asked Questions
          </h2>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
              maxWidth: "800px",
              margin: "0 auto",
            }}
          >
            {faqs.map((faq) => (
              <details
                key={faq.id}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                  padding: "1rem 1.25rem",
                }}
              >
                <summary
                  style={{
                    fontSize: "1rem",
                    fontWeight: 500,
                    color: "var(--text-primary)",
                    cursor: "pointer",
                    listStyle: "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  {faq.question}
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    style={{ color: "var(--text-muted)" }}
                  >
                    <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" />
                  </svg>
                </summary>
                <p
                  style={{
                    fontSize: "0.9375rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                    marginTop: "0.75rem",
                  }}
                >
                  {faq.answer}
                </p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Contact support */}
      <section className="section-container" style={{ marginBottom: "4rem" }}>
        <div
          style={{
            background: "var(--bg-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "2.5rem",
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
            Still Need Help?
          </h2>
          <p
            style={{
              fontSize: "1rem",
              color: "var(--text-secondary)",
              maxWidth: "400px",
              margin: "0 auto 1.5rem",
            }}
          >
            Our support team is here to help you with any questions.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link
              href="/contact"
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
              Contact Support
            </Link>
            <a
              href="mailto:support@trademate.ai"
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
              Email Support
            </a>
          </div>
        </div>
      </section>

      {/* Quick stats */}
      <section className="section-container">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "1rem",
            textAlign: "center",
          }}
        >
          {[
            { value: "< 2h", label: "Average Response Time" },
            { value: "4.9/5", label: "Satisfaction Rating" },
            { value: "24/7", label: "Support Availability" },
          ].map((stat, idx) => (
            <div
              key={idx}
              style={{
                padding: "1.5rem",
                background: "var(--bg-muted)",
                borderRadius: "var(--radius-lg)",
              }}
            >
              <div
                style={{
                  fontSize: "1.75rem",
                  fontWeight: 700,
                  color: "var(--color-brand-400)",
                }}
              >
                {stat.value}
              </div>
              <div
                style={{
                  fontSize: "0.875rem",
                  color: "var(--text-muted)",
                }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}