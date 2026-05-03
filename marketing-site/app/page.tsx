import type { Metadata } from "next";
import Link from "next/link";
import { platformStats, features, testimonials } from "@/lib/static-data";
import AnimatedCursor from "@/components/AnimatedCursor";

export const metadata: Metadata = {
  title: "TradeMate — AI-Powered Trade Intelligence",
  description:
    "Instant HS code classification, tariff analysis, and live shipping rates powered by AI. Built for the Pakistan–US trade corridor.",
};

export default function HomePage() {
  return (
    <div>
      <AnimatedCursor />
      
      {/* Hero Section */}
      <section
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "6rem 1.5rem 4rem",
          position: "relative",
          overflow: "hidden",
          background: "linear-gradient(135deg, var(--color-neutral-0) 0%, var(--color-neutral-50) 100%)",
        }}
      >
        {/* Animated background elements */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            overflow: "hidden",
            pointerEvents: "none",
          }}
        >
          {/* Floating shapes */}
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="float"
              style={{
                position: "absolute",
                width: `${Math.random() * 200 + 100}px`,
                height: `${Math.random() * 200 + 100}px`,
                borderRadius: "50%",
                background: i % 2 === 0 
                  ? "radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)"
                  : "radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%)",
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animation: `float ${8 + i * 2}s ease-in-out infinite`,
                animationDelay: `${i * 0.5}s`,
              }}
            />
          ))}
          
          {/* Grid pattern */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: `
                linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px)
              `,
              backgroundSize: "60px 60px",
              opacity: 0.5,
            }}
          />
        </div>

        {/* Glowing orb */}
        <div
          style={{
            position: "absolute",
            width: "800px",
            height: "800px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, transparent 60%)",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            filter: "blur(60px)",
            animation: "pulse 8s ease-in-out infinite",
          }}
        />

        {/* Content */}
        <div style={{ position: "relative", zIndex: 1, maxWidth: "900px" }}>
          {/* Badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.5rem 1.25rem",
              borderRadius: "var(--radius-full)",
              border: "1px solid rgba(59 130 246 / 0.3)",
              background: "rgba(255, 255, 255, 0.8)",
              backdropFilter: "blur(10px)",
              fontSize: "0.8125rem",
              fontWeight: 600,
              color: "var(--color-brand-500)",
              marginBottom: "2rem",
              boxShadow: "0 4px 20px rgba(59, 130, 246, 0.15)",
            }}
          >
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--color-accent-500)", display: "inline-block", boxShadow: "0 0 10px var(--color-accent-500)" }} />
            Trusted by 500+ Trading Companies
          </div>

          {/* Main heading */}
          <h1
            style={{
              fontSize: "clamp(3rem, 8vw, 5.5rem)",
              fontWeight: 800,
              letterSpacing: "-0.045em",
              lineHeight: 1.05,
              marginBottom: "1.75rem",
              background: "linear-gradient(135deg, var(--text-primary) 0%, var(--color-brand-600) 50%, var(--color-accent-500) 100%)",
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              textShadow: "0 0 80px rgba(59, 130, 246, 0.3)",
            }}
          >
            Trade Smarter
            <br />
            <span style={{ fontSize: "0.85em" }}>With AI Intelligence</span>
          </h1>

          <p
            style={{
              fontSize: "clamp(1.0625rem, 2vw, 1.375rem)",
              color: "var(--text-secondary)",
              lineHeight: 1.7,
              maxWidth: "650px",
              margin: "0 auto 3rem",
              fontWeight: 450,
            }}
          >
            Instant HS code classification, accurate landed costs, and tariff insights — all through natural conversation.
            <br />
            <span style={{ color: "var(--color-brand-500)", fontWeight: 600 }}>Built for Pakistan–US trade corridor.</span>
          </p>

          {/* CTA Buttons */}
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap", marginBottom: "3rem" }}>
            <Link
              href="/contact"
              style={{
                padding: "1rem 2.25rem",
                borderRadius: "var(--radius-full)",
                background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                color: "white",
                fontWeight: 600,
                fontSize: "1.0625rem",
                boxShadow: "0 8px 30px rgba(59, 130, 246, 0.4), 0 0 60px rgba(59, 130, 246, 0.2)",
                textDecoration: "none",
                transition: "all 0.3s ease",
                position: "relative",
                overflow: "hidden",
              }}
            >
              <span style={{ position: "relative", zIndex: 1 }}>Request Demo</span>
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)",
                  transform: "translateX(-100%)",
                  animation: "shimmer 3s ease-in-out infinite",
                }}
              />
            </Link>
            <Link
              href="/features"
              style={{
                padding: "1rem 2.25rem",
                borderRadius: "var(--radius-full)",
                border: "2px solid var(--border-default)",
                color: "var(--text-primary)",
                fontWeight: 600,
                fontSize: "1.0625rem",
                textDecoration: "none",
                background: "rgba(255, 255, 255, 0.8)",
                backdropFilter: "blur(10px)",
                transition: "all 0.3s ease",
              }}
            >
              Explore Features
            </Link>
          </div>

          {/* Scroll indicator */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "0.5rem",
              animation: "bounce 2s ease-in-out infinite",
            }}
          >
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.1em" }}>SCROLL TO EXPLORE</span>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ color: "var(--text-muted)" }}>
              <path d="M5 7.5L10 12.5L15 7.5M5 12.5L10 17.5L15 12.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section style={{ padding: "4rem 0", background: "var(--bg-subtle)", borderTop: "1px solid var(--border-subtle)" }}>
        <div className="section-container">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
              gap: "2rem",
              textAlign: "center",
            }}
          >
            {platformStats.slice(0, 6).map((stat) => (
              <div key={stat.id} style={{ padding: "1rem" }}>
                <div
                  style={{
                    fontSize: "clamp(1.75rem, 4vw, 2.5rem)",
                    fontWeight: 700,
                    color: "var(--color-brand-400)",
                    marginBottom: "0.25rem",
                    fontFeatureSettings: "tnum",
                  }}
                >
                  {stat.value}
                  <span style={{ fontSize: "0.4em", marginLeft: "2px" }}>{stat.suffix}</span>
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", fontWeight: 500 }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Overview */}
      <section style={{ padding: "7rem 0" }}>
        <div className="section-container">
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <h2
              style={{
                fontSize: "clamp(2rem, 5vw, 3rem)",
                fontWeight: 700,
                color: "var(--text-primary)",
                marginBottom: "1rem",
                letterSpacing: "-0.02em",
              }}
            >
              Everything You Need to Trade Smarter
            </h2>
            <p
              style={{
                fontSize: "1.125rem",
                color: "var(--text-secondary)",
                maxWidth: "550px",
                margin: "0 auto",
              }}
            >
              From HS code classification to live shipping rates — all in one AI-powered platform.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {features.slice(0, 6).map((feature) => (
              <div
                key={feature.id}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-xl)",
                  padding: "2rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1.25rem",
                  transition: "all 0.3s ease",
                  cursor: "pointer",
                }}
              >
                <div
                  style={{
                    width: "56px",
                    height: "56px",
                    borderRadius: "var(--radius-lg)",
                    background: "linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(16, 185, 129, 0.1))",
                    color: "var(--color-brand-400)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M12 2l9 5v10l-9 5-9-5V7l9-5z" />
                    <path d="M12 22V12M12 12l9-5M12 12l-9 5" />
                  </svg>
                </div>
                <div>
                  <h3
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      marginBottom: "0.5rem",
                    }}
                  >
                    {feature.name}
                  </h3>
                  <p
                    style={{
                      fontSize: "0.9375rem",
                      color: "var(--text-secondary)",
                      lineHeight: 1.6,
                    }}
                  >
                    {feature.tagline}
                  </p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "auto" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--color-brand-400)" }}>
                    Learn more
                  </span>
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ color: "var(--color-brand-400)" }}>
                    <path d="M3 7h8M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: "center", marginTop: "3rem" }}>
            <Link
              href="/features"
              style={{
                padding: "0.75rem 1.5rem",
                borderRadius: "var(--radius-full)",
                fontSize: "0.9375rem",
                fontWeight: 600,
                color: "white",
                background: "var(--color-brand-500)",
                textDecoration: "none",
              }}
            >
              View All Features
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section style={{ padding: "7rem 0", background: "var(--bg-subtle)" }}>
        <div className="section-container">
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <h2
              style={{
                fontSize: "clamp(2rem, 5vw, 3rem)",
                fontWeight: 700,
                color: "var(--text-primary)",
                marginBottom: "1rem",
                letterSpacing: "-0.02em",
              }}
            >
              How It Works
            </h2>
            <p
              style={{
                fontSize: "1.125rem",
                color: "var(--text-secondary)",
                maxWidth: "500px",
                margin: "0 auto",
              }}
            >
              Get started in seconds. Just ask TradeMate your trade question.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "2rem",
            }}
          >
            {[
              {
                step: "01",
                title: "Ask Your Question",
                description: "Type or speak your trade question in natural language. No forms or dropdowns.",
                icon: "💬",
              },
              {
                step: "02",
                title: "AI Processes Instantly",
                description: "TradeMate searches knowledge graphs, tariff databases, and live shipping rates.",
                icon: "⚡",
              },
              {
                step: "03",
                title: "Get Detailed Answers",
                description: "Receive instant answers with citations, calculations, and actionable insights.",
                icon: "📊",
              },
            ].map((item) => (
              <div
                key={item.step}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-xl)",
                  padding: "2.5rem",
                  textAlign: "center",
                  position: "relative",
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: "-12px",
                    left: "50%",
                    transform: "translateX(-50%)",
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "1.25rem",
                  }}
                >
                  {item.step}
                </div>
                <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>{item.icon}</div>
                <h3
                  style={{
                    fontSize: "1.375rem",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                    marginBottom: "0.75rem",
                  }}
                >
                  {item.title}
                </h3>
                <p
                  style={{
                    fontSize: "1rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.6,
                  }}
                >
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Preview */}
      <section style={{ padding: "7rem 0" }}>
        <div className="section-container">
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-xl)",
              padding: "2rem",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
              gap: "3rem",
              alignItems: "center",
              boxShadow: "0 20px 60px rgba(0, 0, 0, 0.08)",
            }}
          >
            <div>
              <h2
                style={{
                  fontSize: "clamp(1.5rem, 3vw, 2rem)",
                  fontWeight: 700,
                  color: "var(--text-primary)",
                  marginBottom: "1.25rem",
                }}
              >
                Try TradeMate Now
              </h2>
              <p
                style={{
                  fontSize: "1rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.7,
                  marginBottom: "1.5rem",
                }}
              >
                See how TradeMate answers real trade questions. Try these examples:
              </p>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {[
                  "What's the HS code for laptops?",
                  "Compare shipping Karachi to LA",
                  "What duties apply to textile exports to US?",
                ].map((q, idx) => (
                  <li
                    key={idx}
                    style={{
                      padding: "0.875rem 1.125rem",
                      background: "var(--bg-muted)",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.9375rem",
                      color: "var(--text-secondary)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    "{q}"
                  </li>
                ))}
              </ul>
            </div>
            <div
              style={{
                background: "var(--bg-muted)",
                borderRadius: "var(--radius-lg)",
                padding: "1.5rem",
                minHeight: "320px",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem", paddingBottom: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
                <div
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "var(--radius-sm)",
                    background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="white" strokeWidth="1.5">
                    <path d="M9 2L15.5 5.5V12.5L9 16L2.5 12.5V5.5L9 2Z" />
                  </svg>
                </div>
                <span style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)" }}>TradeMate</span>
                <span style={{ marginLeft: "auto", fontSize: "0.75rem", color: "var(--color-accent-500)", fontWeight: 500 }}>Online</span>
              </div>
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div style={{ padding: "0.75rem", background: "var(--bg-surface)", borderRadius: "var(--radius-md)", alignSelf: "flex-start" }}>
                  <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>What's the HS code for laptops?</span>
                </div>
                <div style={{ padding: "1rem", background: "rgba(16 185 129 / 0.1)", borderRadius: "var(--radius-md)", borderLeft: "3px solid var(--color-accent-500)", alignSelf: "flex-end" }}>
                  <p style={{ fontSize: "0.9375rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
                    The HS code for laptops is <strong>8471.30</strong> (US HTS) / <strong>8471.30</strong> (Pakistan PCT).
                  </p>
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                    US Rate: 0% (MFN) • PK Rate: 16% + RD
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section style={{ padding: "7rem 0", background: "var(--bg-subtle)" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(2rem, 5vw, 3rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "3rem",
              textAlign: "center",
              letterSpacing: "-0.02em",
            }}
          >
            Trusted by Industry Leaders
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {testimonials.slice(0, 3).map((t) => (
              <div
                key={t.id}
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-xl)",
                  padding: "2rem",
                }}
              >
                <div style={{ display: "flex", gap: "0.25rem", marginBottom: "1.25rem" }}>
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} width="18" height="18" viewBox="0 0 16 16" fill="var(--color-brand-400)">
                      <path d="M8 1l2.2 4.5 5 .7-3.6 3.5.8 5L8 12.3 3.6 14.7l.8-5L.8 6.2l5-.7L8 1z" />
                    </svg>
                  ))}
                </div>
                <p
                  style={{
                    fontSize: "1rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.7,
                    marginBottom: "1.5rem",
                  }}
                >
                  "{t.quote}"
                </p>
                <div>
                  <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    {t.author}
                  </div>
                  <div style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
                    {t.title}, {t.company}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "8rem 0", textAlign: "center" }}>
        <div className="section-container">
          <h2
            style={{
              fontSize: "clamp(2rem, 5vw, 3rem)",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "1.25rem",
              letterSpacing: "-0.02em",
            }}
          >
            Ready to Trade Smarter?
          </h2>
          <p
            style={{
              fontSize: "1.125rem",
              color: "var(--text-secondary)",
              maxWidth: "550px",
              margin: "0 auto 2.5rem",
            }}
          >
            Join 500+ trading companies already using TradeMate to streamline their operations.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link
              href="/contact"
              style={{
                padding: "1rem 2.25rem",
                borderRadius: "var(--radius-full)",
                background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                color: "white",
                fontWeight: 600,
                fontSize: "1.0625rem",
                boxShadow: "0 8px 30px rgba(59, 130, 246, 0.4)",
                textDecoration: "none",
              }}
            >
              Request Demo
            </Link>
            <Link
              href="/pricing"
              style={{
                padding: "1rem 2.25rem",
                borderRadius: "var(--radius-full)",
                border: "2px solid var(--border-default)",
                color: "var(--text-primary)",
                fontWeight: 600,
                fontSize: "1.0625rem",
                textDecoration: "none",
              }}
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(2deg); }
        }
        @keyframes pulse {
          0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.8; }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(8px); }
        }
      `}</style>
    </div>
  );
}