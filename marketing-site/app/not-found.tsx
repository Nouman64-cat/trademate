import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "404 — Page Not Found",
  description: "The page you are looking for does not exist.",
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "70vh",
        textAlign: "center",
        padding: "4rem 1.5rem",
      }}
    >
      <p
        style={{
          fontSize: "0.8125rem",
          fontWeight: 700,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--color-brand-400)",
          marginBottom: "1rem",
        }}
      >
        404
      </p>

      <h1
        style={{
          fontSize: "clamp(2rem, 5vw, 3rem)",
          fontWeight: 800,
          letterSpacing: "-0.04em",
          color: "var(--text-primary)",
          marginBottom: "1rem",
        }}
      >
        Page not found
      </h1>

      <p
        style={{
          fontSize: "1.0625rem",
          color: "var(--text-secondary)",
          maxWidth: "460px",
          lineHeight: 1.6,
          marginBottom: "2.5rem",
        }}
      >
        The page you&apos;re looking for doesn&apos;t exist or has been moved. Try
        heading back to the homepage.
      </p>

      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", justifyContent: "center" }}>
        <Link
          href="/"
          style={{
            padding: "0.75rem 1.5rem",
            borderRadius: "var(--radius-full)",
            fontSize: "0.9375rem",
            fontWeight: 600,
            color: "white",
            background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
            boxShadow: "0 0 24px -4px rgba(59 130 246 / 0.5)",
            textDecoration: "none",
          }}
        >
          Back to Home
        </Link>
        <Link
          href="/contact"
          style={{
            padding: "0.75rem 1.5rem",
            borderRadius: "var(--radius-full)",
            fontSize: "0.9375rem",
            fontWeight: 500,
            color: "var(--text-secondary)",
            border: "1px solid var(--border-subtle)",
            textDecoration: "none",
          }}
        >
          Contact Support
        </Link>
      </div>
    </div>
  );
}
