"use client";

import { useEffect } from "react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log to an error reporting service in production
    console.error(error);
  }, [error]);

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
        Something went wrong
      </p>

      <h2
        style={{
          fontSize: "clamp(1.75rem, 4vw, 2.5rem)",
          fontWeight: 800,
          letterSpacing: "-0.04em",
          color: "var(--text-primary)",
          marginBottom: "1rem",
        }}
      >
        An unexpected error occurred
      </h2>

      <p
        style={{
          fontSize: "1rem",
          color: "var(--text-secondary)",
          maxWidth: "440px",
          lineHeight: 1.6,
          marginBottom: "2.5rem",
        }}
      >
        We&apos;ve been notified and are looking into it. You can try again or
        return to the homepage.
      </p>

      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", justifyContent: "center" }}>
        <button
          onClick={reset}
          style={{
            padding: "0.75rem 1.5rem",
            borderRadius: "var(--radius-full)",
            fontSize: "0.9375rem",
            fontWeight: 600,
            color: "white",
            background: "linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))",
            boxShadow: "0 0 24px -4px rgba(59 130 246 / 0.5)",
            border: "none",
            cursor: "pointer",
          }}
        >
          Try Again
        </button>
        <a
          href="/"
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
          Back to Home
        </a>
      </div>
    </div>
  );
}
