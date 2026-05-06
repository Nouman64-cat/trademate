import Link from "next/link";

interface ComingSoonProps {
  title: string;
  description: string;
}

export default function ComingSoon({ title, description }: ComingSoonProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "60vh",
        textAlign: "center",
        padding: "2rem",
      }}
    >
      <div
        style={{
          width: "64px",
          height: "64px",
          borderRadius: "16px",
          background: "linear-gradient(135deg, var(--color-brand-500), var(--color-accent-500))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "2rem",
        }}
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2L2 7L12 12L22 7L12 2Z"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M2 17L12 22L22 17"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M2 12L12 17L22 12"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h1
        style={{
          fontSize: "clamp(2rem, 4vw, 3rem)",
          fontWeight: 700,
          color: "var(--text-primary)",
          marginBottom: "1rem",
        }}
      >
        {title}
      </h1>
      <p
        style={{
          fontSize: "1.125rem",
          color: "var(--text-secondary)",
          maxWidth: "500px",
          marginBottom: "2rem",
          lineHeight: 1.6,
        }}
      >
        {description}
      </p>
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
        <Link
          href="/"
          style={{
            padding: "0.75rem 1.5rem",
            borderRadius: "var(--radius-full)",
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--text-secondary)",
            border: "1px solid var(--border-subtle)",
            textDecoration: "none",
            transition: "all var(--transition-fast)",
          }}
        >
          Return Home
        </Link>
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
            transition: "all var(--transition-fast)",
          }}
        >
          Contact Sales
        </Link>
      </div>
    </div>
  );
}
