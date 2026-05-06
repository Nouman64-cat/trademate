"use client";

import { useEffect, useRef, useState } from "react";
import AnimatedCursor from "@/components/AnimatedCursor";

type Vehicle = {
  from: { name: string; x: number; y: number; type: string };
  to: { name: string; x: number; y: number; type: string };
  progress: number;
  id: number;
};

const locations = {
  karachi: { name: "Karachi", x: 18, y: 35, type: "port" },
  lahore: { name: "Lahore", x: 22, y: 33, type: "city" },
  usla: { name: "Los Angeles", x: 12, y: 35, type: "port" },
  usny: { name: "New York", x: 24, y: 28, type: "port" },
  uk: { name: "London", x: 47, y: 22, type: "port" },
  uae: { name: "Dubai", x: 62, y: 32, type: "port" },
  china: { name: "Shanghai", x: 78, y: 30, type: "port" },
  tokyo: { name: "Tokyo", x: 88, y: 30, type: "port" },
  singapore: { name: "Singapore", x: 76, y: 40, type: "port" },
  mumbai: { name: "Mumbai", x: 68, y: 36, type: "port" },
};

function getVehicleIcon(fromType: string, toType: string, progress: number) {
  const isInternational = fromType === "port" && toType === "port";
  return isInternational ? (progress < 0.4 ? "✈️" : "🚢") : "🚛";
}

function WorldMapBackground() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const rafRef = useRef<number | undefined>(undefined);
  const lastTimeRef = useRef<number>(0);

  useEffect(() => {
    const locKeys = Object.keys(locations);
    const initial: Vehicle[] = [];

    for (let i = 0; i < 4; i++) {
      const fromKey = locKeys[Math.floor(Math.random() * locKeys.length)];
      let toKey = locKeys[Math.floor(Math.random() * locKeys.length)];
      while (toKey === fromKey) toKey = locKeys[Math.floor(Math.random() * locKeys.length)];

      initial.push({
        from: locations[fromKey as keyof typeof locations],
        to: locations[toKey as keyof typeof locations],
        progress: Math.random(),
        id: i,
      });
    }
    setVehicles(initial);
  }, []);

  useEffect(() => {
    if (vehicles.length === 0) return;

    const STEP_INTERVAL = 60;

    const tick = (timestamp: number) => {
      if (timestamp - lastTimeRef.current >= STEP_INTERVAL) {
        lastTimeRef.current = timestamp;
        setVehicles((prev) =>
          prev.map((v) => ({
            ...v,
            progress: v.progress >= 1 ? 0 : v.progress + 0.002,
          }))
        );
      }
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [vehicles.length]);

  const routeColors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b"];

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>
      <svg viewBox="0 0 100 50" style={{ position: "absolute", width: "100%", height: "100%", opacity: 0.4 }}>
        <g fill="var(--color-brand-400)">
          <path d="M8 12 L22 10 L32 16 L38 28 L28 36 L18 34 L10 28 Z" />
          <path d="M22 38 L28 40 L32 48 L26 48 L22 42 Z" />
          <path d="M46 14 L54 12 L56 20 L52 24 L46 20 Z" />
          <path d="M46 26 L54 24 L60 36 L52 42 L44 36 Z" />
          <path d="M56 12 L78 14 L86 28 L78 36 L64 30 L56 22 Z" />
          <path d="M82 40 L90 38 L92 44 L86 46 L80 44 Z" />
        </g>
      </svg>

      <svg viewBox="0 0 100 50" style={{ position: "absolute", width: "100%", height: "100%" }}>
        {vehicles.map((v) => {
          const isInternational = v.from.type === "port" && v.to.type === "port";
          return (
            <line
              key={`route-${v.id}`}
              x1={v.from.x}
              y1={v.from.y}
              x2={v.to.x}
              y2={v.to.y}
              stroke={routeColors[v.id % routeColors.length]}
              strokeWidth={isInternational ? "0.15" : "0.2"}
              strokeDasharray={isInternational ? "2 1" : "0.8 0.4"}
              opacity={0.5}
            />
          );
        })}
      </svg>

      {vehicles.map((v) => {
        const x = v.from.x + (v.to.x - v.from.x) * v.progress;
        const y = v.from.y + (v.to.y - v.from.y) * v.progress;
        const icon = getVehicleIcon(v.from.type, v.to.type, v.progress);
        
        return (
          <div
            key={`vehicle-${v.id}`}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              transform: "translate(-50%, -50%)",
              fontSize: 8,
              opacity: v.progress > 0.02 && v.progress < 0.98 ? 0.85 : 0,
              transition: "all 0.06s linear",
              filter: "drop-shadow(0 0 2px rgba(59,130,246,0.7))",
            }}
          >
            {icon}
          </div>
        );
      })}

      <svg viewBox="0 0 100 50" style={{ position: "absolute", width: "100%", height: "100%" }}>
        {Object.values(locations).map((loc, i) => (
          <circle key={i} cx={loc.x} cy={loc.y} r="0.3" fill="var(--color-brand-400)" opacity={0.55} />
        ))}
      </svg>
    </div>
  );
}

function Hero() {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollOpacity = Math.max(0, 1 - scrollY / 150);

  return (
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
        background: "var(--color-neutral-0)",
      }}
    >
      <AnimatedCursor />
      <WorldMapBackground />

      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle, rgba(255,255,255,0.74) 0%, rgba(255,255,255,0.94) 100%)", pointerEvents: "none" }} />

      <div style={{ position: "relative", zIndex: 1, maxWidth: 700 }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.375rem 0.875rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: 500,
            color: "var(--color-brand-500)",
            background: "rgba(59, 130, 246, 0.08)",
            marginBottom: "1.5rem",
          }}
        >
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--color-accent-500)" }} />
          AI-Powered Trade Intelligence
        </div>

        <h1
          style={{
            fontSize: "clamp(2.5rem, 6vw, 4rem)",
            fontWeight: 800,
            letterSpacing: "-0.035em",
            lineHeight: 1.15,
            marginBottom: "1.25rem",
            color: "var(--text-primary)",
          }}
        >
          Trade Smarter
          <br />
          <span style={{ color: "var(--color-brand-500)" }}>With AI</span>
        </h1>

        <p
          style={{
            fontSize: "clamp(1rem, 1.5vw, 1.125rem)",
            color: "var(--text-secondary)",
            lineHeight: 1.6,
            maxWidth: 500,
            margin: "0 auto 2rem",
          }}
        >
          Instant HS code classification, tariff analysis, and live shipping rates — all in one conversational interface.
        </p>

        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap" }}>
          <a
            href="/contact"
            style={{
              padding: "0.75rem 1.75rem",
              borderRadius: "9999px",
              background: "var(--color-brand-500)",
              color: "white",
              fontWeight: 600,
              fontSize: "0.9375rem",
              textDecoration: "none",
            }}
          >
            Get Started
          </a>
          <a
            href="/features"
            style={{
              padding: "0.75rem 1.75rem",
              borderRadius: "9999px",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-secondary)",
              fontWeight: 500,
              fontSize: "0.9375rem",
              textDecoration: "none",
            }}
          >
            Learn More
          </a>
        </div>
      </div>

      <div style={{ 
        position: "absolute", 
        bottom: "2rem", 
        display: "flex", 
        flexDirection: "column", 
        alignItems: "center", 
        gap: "0.375rem",
        opacity: scrollOpacity,
        transition: "opacity 0.1s ease-out",
        pointerEvents: "none"
      }}>
        <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", letterSpacing: "0.15em" }}>SCROLL</span>
      </div>
    </section>
  );
}

export default Hero;