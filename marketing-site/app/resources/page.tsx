import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Resources",
  description:
    `Documentation, guides, and insights to help you get the most out of ${process.env.NEXT_PUBLIC_APP_NAME}. Explore our API docs, read case studies, and stay updated with trade intelligence.`,
};

const resources = [
  {
    id: "docs",
    title: "Documentation",
    description: "Complete API references, integration guides, and quickstart tutorials.",
    href: "/docs",
    icon: "Book",
    count: "12+ guides",
  },
  {
    id: "case-studies",
    title: "Case Studies",
    description: `See how trading companies transformed their operations with ${process.env.NEXT_PUBLIC_APP_NAME}.`,
    href: "/case-studies",
    icon: "FileText",
    count: "6 stories",
  },
  {
    id: "blog",
    title: "Blog",
    description: "Latest insights on trade policy, HS codes, tariffs, and global logistics.",
    href: "/blog",
    icon: "PenTool",
    count: "Weekly updates",
  },
  {
    id: "help",
    title: "Help Center",
    description: `FAQs, troubleshooting, and support for all your ${process.env.NEXT_PUBLIC_APP_NAME} questions.`,
    href: "#",
    icon: "HelpCircle",
    count: "24/7 support",
  },
];

function ResourceIcon({ name, size = 32 }: { name: string; size?: number }) {
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
    case "Book":
      return (
        <svg {...base}>
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
        </svg>
      );
    case "FileText":
      return (
        <svg {...base}>
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
      );
    case "PenTool":
      return (
        <svg {...base}>
          <path d="M12 19l7-7 3 3-7 7-3-3z" />
          <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" />
          <path d="M2 2l7.586 7.586" />
          <circle cx="11" cy="11" r="2" />
        </svg>
      );
    case "HelpCircle":
      return (
        <svg {...base}>
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      );
    default:
      return <svg {...base}><circle cx="12" cy="12" r="10" /></svg>;
  }
}

export default function ResourcesPage() {
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
            Resources
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
            Everything you need to integrate {process.env.NEXT_PUBLIC_APP_NAME} into your workflow — from
            API docs to industry insights.
          </p>
        </div>
      </section>

      {/* Resource cards */}
      <section className="section-container">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {resources.map((resource) => (
            <Link
              key={resource.id}
              href={resource.href}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "1.75rem",
                textDecoration: "none",
                transition: "transform var(--transition-base), border-color var(--transition-base)",
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
                <ResourceIcon name={resource.icon} />
              </div>
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "0.375rem",
                  }}
                >
                  <h2
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {resource.title}
                  </h2>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 500,
                      color: "var(--color-brand-400)",
                      background: "rgba(59 130 246 / 0.1)",
                      padding: "0.25rem 0.625rem",
                      borderRadius: "var(--radius-full)",
                    }}
                  >
                    {resource.count}
                  </span>
                </div>
                <p
                  style={{
                    fontSize: "0.9375rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.5,
                  }}
                >
                  {resource.description}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Quick links */}
      <section style={{ padding: "4rem 0" }}>
        <div className="section-container">
          <div
            style={{
              background: "var(--bg-subtle)",
              borderRadius: "var(--radius-xl)",
              padding: "2rem",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              gap: "1rem",
            }}
          >
            <h2
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: "var(--text-primary)",
              }}
            >
              Can't find what you're looking for?
            </h2>
            <p
              style={{
                fontSize: "1rem",
                color: "var(--text-secondary)",
                maxWidth: "400px",
              }}
            >
              Our support team is here to help you with any questions about {process.env.NEXT_PUBLIC_APP_NAME}.
            </p>
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
          </div>
        </div>
      </section>
    </div>
  );
}