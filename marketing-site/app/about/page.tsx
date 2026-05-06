// app/about/page.tsx
import type { Metadata } from "next";
import Link from "next/link";
import { team, testimonials, platformStats } from "@/lib/static-data";

export const metadata: Metadata = {
  title: "About",
  description:
    `Meet the team behind ${process.env.NEXT_PUBLIC_APP_NAME} — a final-year project built by four engineers passionate about making Pakistan–US trade intelligence accessible to everyone.`,
};

// ── Star rating ────────────────────────────────────────────────────────────
function Stars({ count }: { count: number }) {
  return (
    <div style={{ display: "flex", gap: "2px" }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <svg key={i} width="14" height="14" viewBox="0 0 24 24" fill={i < count ? "#fbbf24" : "none"} stroke="#fbbf24" strokeWidth="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ))}
    </div>
  );
}

// ── LinkedIn / GitHub icons ────────────────────────────────────────────────
function LinkedInIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}
function GitHubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
    </svg>
  );
}

// ── Avatar placeholder ─────────────────────────────────────────────────────
function AvatarPlaceholder({ name, size = 64 }: { name: string; size?: number }) {
  const initials = name.split(" ").map((n) => n[0]).join("").slice(0, 2);
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: "linear-gradient(135deg, var(--color-brand-600), var(--color-accent-600))",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: size * 0.3,
        fontWeight: 700,
        color: "white",
        flexShrink: 0,
        letterSpacing: "-0.02em",
      }}
    >
      {initials}
    </div>
  );
}

export default function AboutPage() {
  return (
    <>
      {/* ── Hero / Mission ────────────────────────────────────────────── */}
      <section
        style={{
          position: "relative",
          overflow: "hidden",
          paddingTop: "5rem",
          paddingBottom: "4rem",
          textAlign: "center",
        }}
      >
        <div className="bg-orb bg-orb-brand" style={{ width: "500px", height: "500px", top: "-200px", right: "-100px", opacity: 0.2 }} />
        <div className="bg-orb bg-orb-accent" style={{ width: "280px", height: "280px", bottom: "-60px", left: "-40px", opacity: 0.15 }} />

        <div className="section-container" style={{ position: "relative", zIndex: 1, maxWidth: "760px" }}>
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
            Final Year Project — 2025
          </div>

          <h1
            style={{
              fontSize: "clamp(2rem, 5vw, 3.25rem)",
              fontWeight: 900,
              letterSpacing: "-0.04em",
              lineHeight: 1.1,
              marginBottom: "1.5rem",
            }}
          >
            Built by traders,{" "}
            <span className="text-gradient">for traders</span>
          </h1>

          <p
            style={{
              fontSize: "1.0625rem",
              color: "var(--text-secondary)",
              lineHeight: 1.75,
              maxWidth: "620px",
              margin: "0 auto",
            }}
          >
            ${process.env.NEXT_PUBLIC_APP_NAME} started from a simple frustration: why does it take hours
            of manual research to answer a basic trade question? We built an AI
            platform that makes world-class trade intelligence available to
            everyone — from solo importers in Lahore to freight desks in Chicago.
          </p>
        </div>
      </section>

      {/* ── Platform Stats ────────────────────────────────────────────── */}
      <section
        style={{
          background: "var(--bg-subtle)",
          borderTop: "1px solid var(--border-subtle)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "3rem 0",
        }}
      >
        <div className="section-container">
          <div className="about-stats-grid">
            {platformStats.map((stat) => (
              <div key={stat.id} style={{ textAlign: "center", padding: "0.5rem" }}>
                <p
                  style={{
                    fontSize: "clamp(1.5rem, 3vw, 2rem)",
                    fontWeight: 900,
                    letterSpacing: "-0.04em",
                    lineHeight: 1,
                    marginBottom: "0.25rem",
                    color: "var(--color-brand-400)",
                  }}
                >
                  {stat.value}
                </p>
                <p style={{ fontWeight: 600, fontSize: "0.8125rem", color: "var(--text-primary)", marginBottom: "0.2rem" }}>
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Team ──────────────────────────────────────────────────────── */}
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
              Meet the team
            </h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: "460px", margin: "0 auto", lineHeight: 1.6 }}>
              Four engineers who built ${process.env.NEXT_PUBLIC_APP_NAME} as a final-year project and
              haven&apos;t stopped shipping since.
            </p>
          </div>

          <div className="team-grid">
            {team.map((member) => (
              <div
                key={member.id}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-xl)",
                  padding: "2rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1.25rem",
                }}
                className="team-card"
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
                  <AvatarPlaceholder name={member.name} size={56} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.2rem" }}>
                      {member.name}
                    </h3>
                    <p style={{ fontSize: "0.8125rem", color: "var(--color-brand-400)", fontWeight: 500 }}>
                      {member.role}
                    </p>
                  </div>
                </div>

                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.7, flexGrow: 1 }}>
                  {member.bio}
                </p>

                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {member.linkedin && (
                    <a
                      href={member.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`${member.name} on LinkedIn`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.375rem",
                        padding: "0.375rem 0.75rem",
                        borderRadius: "var(--radius-full)",
                        border: "1px solid var(--border-subtle)",
                        fontSize: "0.75rem",
                        fontWeight: 500,
                        color: "var(--text-muted)",
                        transition: "all var(--transition-fast)",
                      }}
                      className="social-link"
                    >
                      <LinkedInIcon />
                      LinkedIn
                    </a>
                  )}
                  {member.github && (
                    <a
                      href={member.github}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`${member.name} on GitHub`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.375rem",
                        padding: "0.375rem 0.75rem",
                        borderRadius: "var(--radius-full)",
                        border: "1px solid var(--border-subtle)",
                        fontSize: "0.75rem",
                        fontWeight: 500,
                        color: "var(--text-muted)",
                        transition: "all var(--transition-fast)",
                      }}
                      className="social-link"
                    >
                      <GitHubIcon />
                      GitHub
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ──────────────────────────────────────────────── */}
      <section
        style={{
          background: "var(--bg-subtle)",
          borderTop: "1px solid var(--border-subtle)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "5rem 0",
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
              What traders are saying
            </h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: "440px", margin: "0 auto", lineHeight: 1.6 }}>
              Real feedback from importers, exporters, and logistics professionals.
            </p>
          </div>

          <div className="testimonials-grid">
            {testimonials.map((t) => (
              <div
                key={t.id}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-xl)",
                  padding: "2rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1.25rem",
                }}
              >
                {/* Quote mark */}
                <div style={{ color: "var(--color-brand-500)", opacity: 0.4 }}>
                  <svg width="32" height="32" viewBox="0 0 32 32" fill="currentColor">
                    <path d="M9.333 21.333c-2.933 0-5.333-2.4-5.333-5.333 0-4.267 2.667-8 8-9.333l1.333 2.666C10.4 10.4 8 12.267 8 14.667c0 .266 0 .533.133.8.4-.267.933-.4 1.2-.4 2.267 0 4 1.6 4 3.866 0 2.267-1.733 4-4 4zm13.334 0c-2.934 0-5.334-2.4-5.334-5.333 0-4.267 2.667-8 8-9.333l1.334 2.666C23.733 10.4 21.333 12.267 21.333 14.667c0 .266 0 .533.134.8.4-.267.933-.4 1.2-.4 2.266 0 4 1.6 4 3.866C26.667 21.2 24.933 23 22.667 23z" />
                  </svg>
                </div>

                <p style={{ fontSize: "0.9375rem", color: "var(--text-secondary)", lineHeight: 1.75, flexGrow: 1, fontStyle: "italic" }}>
                  &ldquo;{t.quote}&rdquo;
                </p>

                <div style={{ display: "flex", alignItems: "center", gap: "0.875rem" }}>
                  <AvatarPlaceholder name={t.author} size={40} />
                  <div>
                    <p style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)" }}>{t.author}</p>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t.title} · {t.company}</p>
                  </div>
                  <div style={{ marginLeft: "auto" }}>
                    <Stars count={t.rating} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────── */}
      <section style={{ padding: "5rem 0", textAlign: "center" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
              fontWeight: 800,
              letterSpacing: "-0.03em",
              marginBottom: "1rem",
            }}
          >
            Want to collaborate or give feedback?
          </h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2rem", maxWidth: "460px", margin: "0 auto 2rem", lineHeight: 1.6 }}>
            We&apos;re always looking for industry feedback to make {process.env.NEXT_PUBLIC_APP_NAME}
            more useful for real traders.
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
              Get in Touch
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
              Explore the Platform
            </Link>
          </div>
        </div>
      </section>

      <style>{`
        .about-stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.5rem;
        }
        @media (min-width: 768px) {
          .about-stats-grid { grid-template-columns: repeat(6, 1fr); }
        }
        .team-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 1.5rem;
        }
        @media (min-width: 640px) {
          .team-grid { grid-template-columns: repeat(2, 1fr); }
        }
        .testimonials-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 1.5rem;
        }
        @media (min-width: 768px) {
          .testimonials-grid { grid-template-columns: repeat(3, 1fr); }
        }
        .team-card:hover { border-color: var(--border-default); }
        .social-link:hover { color: var(--text-primary) !important; border-color: var(--border-default) !important; }
      `}</style>
    </>
  );
}
