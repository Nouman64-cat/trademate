// components/contact/ContactForm.tsx
"use client";

import { useState } from "react";
import Link from "next/link";

type FormState = "idle" | "submitting" | "success" | "error";

const benefits = [
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    title: "Live query walkthrough",
    desc: "We run a real trade query in front of you — HS code lookup to landed cost in one conversation.",
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
    title: "Knowledge graph demo",
    desc: "See 340K+ HS code relationships visualised and queried live in the admin portal.",
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21" /><line x1="9" y1="3" x2="9" y2="18" /><line x1="15" y1="6" x2="15" y2="21" />
      </svg>
    ),
    title: "Route cost breakdown",
    desc: "Live Freightos rate fetch + DDP calculation for your actual product and port pair.",
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
      </svg>
    ),
    title: "30 minutes, no fluff",
    desc: "We respect your time. Focused, technical, and tailored to your specific trade use case.",
  },
];

const roleOptions = [
  "Importer / Buyer",
  "Exporter / Seller",
  "Freight Forwarder",
  "Customs Broker",
  "Logistics Manager",
  "CTO / Technical Lead",
  "Founder / CEO",
  "Other",
];

export default function ContactForm() {
  const [formState, setFormState] = useState<FormState>("idle");
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    company: "",
    email: "",
    role: "",
    message: "",
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormState("submitting");
    // Simulated async submission
    await new Promise((r) => setTimeout(r, 1200));
    setFormState("success");
  }

  return (
    <>
      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <section
        style={{
          position: "relative",
          overflow: "hidden",
          paddingTop: "5rem",
          paddingBottom: "3rem",
          textAlign: "center",
        }}
      >
        <div className="bg-orb bg-orb-brand" style={{ width: "440px", height: "440px", top: "-160px", right: "-80px", opacity: 0.2 }} />

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
              marginBottom: "1.5rem",
            }}
          >
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--color-accent-500)", display: "inline-block" }} />
            Free 30-minute demo
          </div>

          <h1
            style={{
              fontSize: "clamp(2rem, 5vw, 3rem)",
              fontWeight: 900,
              letterSpacing: "-0.04em",
              lineHeight: 1.1,
              marginBottom: "1rem",
            }}
          >
            See {process.env.NEXT_PUBLIC_APP_NAME}{" "}
            <span className="text-gradient">live in action</span>
          </h1>

          <p style={{ fontSize: "1rem", color: "var(--text-secondary)", lineHeight: 1.7, maxWidth: "480px", margin: "0 auto" }}>
            Tell us a little about your trade operation and we&apos;ll set up a
            focused, technical demo tailored to your workflow.
          </p>
        </div>
      </section>

      {/* ── Two-column layout ─────────────────────────────────────────── */}
      <section style={{ paddingBottom: "5rem" }}>
        <div className="section-container">
          <div className="contact-layout">

            {/* ── Left: Benefits ──────────────────────────────────────── */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div
                style={{
                  padding: "2rem",
                  borderRadius: "var(--radius-xl)",
                  border: "1px solid var(--border-subtle)",
                  background: "var(--bg-surface)",
                  marginBottom: "0.5rem",
                }}
              >
                <h2 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "1.5rem", letterSpacing: "-0.02em" }}>
                  What to expect in the demo
                </h2>
                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                  {benefits.map((b, i) => (
                    <div key={i} style={{ display: "flex", gap: "0.875rem", alignItems: "flex-start" }}>
                      <div
                        style={{
                          width: "36px",
                          height: "36px",
                          borderRadius: "var(--radius-md)",
                          background: "rgba(59,130,246,0.1)",
                          border: "1px solid rgba(59,130,246,0.2)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "var(--color-brand-400)",
                          flexShrink: 0,
                        }}
                      >
                        {b.icon}
                      </div>
                      <div>
                        <p style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)", marginBottom: "0.2rem" }}>{b.title}</p>
                        <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", lineHeight: 1.6 }}>{b.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Contact info strip */}
              <div
                style={{
                  padding: "1.25rem 1.5rem",
                  borderRadius: "var(--radius-lg)",
                  border: "1px solid var(--border-subtle)",
                  background: "var(--bg-surface)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.625rem",
                }}
              >
                <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
                  Prefer to reach out directly?
                </p>
                <a
                  href="mailto:hello@trademate.ai"
                  style={{ fontSize: "0.875rem", color: "var(--color-brand-400)", display: "flex", alignItems: "center", gap: "0.5rem" }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                  hello@trademate.ai
                </a>
              </div>
            </div>

            {/* ── Right: Form ─────────────────────────────────────────── */}
            <div
              style={{
                padding: "2rem",
                borderRadius: "var(--radius-xl)",
                border: "1px solid var(--border-subtle)",
                background: "var(--bg-surface)",
              }}
            >
              {formState === "success" ? (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    textAlign: "center",
                    gap: "1.25rem",
                    minHeight: "400px",
                    padding: "2rem",
                  }}
                >
                  <div
                    style={{
                      width: "64px",
                      height: "64px",
                      borderRadius: "50%",
                      background: "rgba(16,185,129,0.15)",
                      border: "1px solid rgba(16,185,129,0.3)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-500)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                  <div>
                    <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: "0.5rem", letterSpacing: "-0.025em" }}>
                      Request received!
                    </h3>
                    <p style={{ fontSize: "0.9375rem", color: "var(--text-secondary)", lineHeight: 1.7, maxWidth: "320px" }}>
                      We&apos;ll reach out within one business day to schedule your demo.
                    </p>
                  </div>
                  <Link
                    href="/features"
                    style={{
                      padding: "0.625rem 1.5rem",
                      borderRadius: "var(--radius-full)",
                      border: "1px solid var(--border-default)",
                      color: "var(--text-secondary)",
                      fontWeight: 500,
                      fontSize: "0.875rem",
                    }}
                  >
                    Explore Features
                  </Link>
                </div>
              ) : (
                <>
                  <h2 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "1.75rem", letterSpacing: "-0.02em" }}>
                    Request a demo
                  </h2>

                  <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.125rem" }}>
                    {/* Name row */}
                    <div className="form-row">
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                        <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                          First name <span style={{ color: "var(--color-brand-400)" }}>*</span>
                        </label>
                        <input
                          name="firstName"
                          type="text"
                          required
                          value={formData.firstName}
                          onChange={handleChange}
                          placeholder="Akif"
                          style={inputStyle}
                          onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-brand-500)"; }}
                          onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
                        />
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                        <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                          Last name <span style={{ color: "var(--color-brand-400)" }}>*</span>
                        </label>
                        <input
                          name="lastName"
                          type="text"
                          required
                          value={formData.lastName}
                          onChange={handleChange}
                          placeholder="Butt"
                          style={inputStyle}
                          onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-brand-500)"; }}
                          onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
                        />
                      </div>
                    </div>

                    {/* Company */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                      <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                        Company <span style={{ color: "var(--color-brand-400)" }}>*</span>
                      </label>
                      <input
                        name="company"
                        type="text"
                        required
                        value={formData.company}
                        onChange={handleChange}
                        placeholder="NovaTex Exports"
                        style={inputStyle}
                        onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-brand-500)"; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
                      />
                    </div>

                    {/* Email */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                      <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                        Work email <span style={{ color: "var(--color-brand-400)" }}>*</span>
                      </label>
                      <input
                        name="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="akif@novatex.com"
                        style={inputStyle}
                        onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-brand-500)"; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
                      />
                    </div>

                    {/* Role */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                      <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                        Your role <span style={{ color: "var(--color-brand-400)" }}>*</span>
                      </label>
                      <select
                        name="role"
                        required
                        value={formData.role}
                        onChange={handleChange}
                        style={{ ...inputStyle, appearance: "none", cursor: "pointer" }}
                        onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-brand-500)"; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
                      >
                        <option value="" disabled>Select your role…</option>
                        {roleOptions.map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    </div>

                    {/* Message */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                      <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                        What would you like to explore?{" "}
                        <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>(optional)</span>
                      </label>
                      <textarea
                        name="message"
                        rows={4}
                        value={formData.message}
                        onChange={handleChange}
                        placeholder="e.g. We import textiles from Pakistan and want to automate HS classification and duty calculation."
                        style={{ ...inputStyle, resize: "vertical", minHeight: "96px" }}
                        onFocus={(e) => { e.currentTarget.style.borderColor = "var(--color-brand-500)"; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
                      />
                    </div>

                    {/* Submit */}
                    <button
                      type="submit"
                      disabled={formState === "submitting"}
                      style={{
                        padding: "0.8125rem 1.5rem",
                        borderRadius: "var(--radius-full)",
                        background: formState === "submitting"
                          ? "var(--color-brand-700)"
                          : "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
                        color: "white",
                        fontWeight: 700,
                        fontSize: "0.9375rem",
                        border: "none",
                        cursor: formState === "submitting" ? "not-allowed" : "pointer",
                        boxShadow: "var(--shadow-glow)",
                        transition: "all var(--transition-fast)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "0.5rem",
                        width: "100%",
                        opacity: formState === "submitting" ? 0.75 : 1,
                      }}
                    >
                      {formState === "submitting" ? (
                        <>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
                            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" className="spinner" />
                          </svg>
                          Sending…
                        </>
                      ) : (
                        <>
                          Request Demo
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M3 8h10M9 4l4 4-4 4" stroke="white" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </>
                      )}
                    </button>

                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", textAlign: "center", lineHeight: 1.6 }}>
                      By submitting you agree to our{" "}
                      <Link href="/privacy" style={{ color: "var(--color-brand-400)" }}>Privacy Policy</Link>.
                      No spam — ever.
                    </p>
                  </form>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      <style>{`
        .contact-layout {
          display: grid;
          grid-template-columns: 1fr;
          gap: 2rem;
          align-items: start;
        }
        @media (min-width: 768px) {
          .contact-layout { grid-template-columns: 1fr 1.2fr; gap: 2.5rem; }
        }
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }
        @media (max-width: 480px) {
          .form-row { grid-template-columns: 1fr; }
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .spinner { animation: spin 1s linear infinite; transform-origin: center; }
      `}</style>
    </>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "0.6875rem 0.875rem",
  borderRadius: "var(--radius-md)",
  border: "1px solid var(--border-subtle)",
  background: "var(--bg-muted)",
  color: "var(--text-primary)",
  fontSize: "0.9375rem",
  outline: "none",
  width: "100%",
  transition: "border-color var(--transition-fast)",
  fontFamily: "inherit",
};
