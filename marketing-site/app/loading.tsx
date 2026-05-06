export default function Loading() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "70vh",
        padding: "4rem 1.5rem",
      }}
      aria-label="Loading page content"
      role="status"
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "1.25rem",
        }}
      >
        {/* Pulsing brand logo mark */}
        <div
          style={{
            width: "48px",
            height: "48px",
            borderRadius: "12px",
            background: "linear-gradient(135deg, var(--color-brand-500), var(--color-accent-500))",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
        <p
          style={{
            fontSize: "0.875rem",
            color: "var(--text-muted)",
            letterSpacing: "0.05em",
          }}
        >
          Loading…
        </p>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.5; transform: scale(0.92); }
        }
      `}</style>
    </div>
  );
}
