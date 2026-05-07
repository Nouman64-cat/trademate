"use client";

import { useRef, useState, useCallback } from "react";
import { cn } from "@/lib/cn";

interface MouseTrackGlowProps {
  children: React.ReactNode;
  className?: string;
}

export function MouseTrackGlow({ children, className }: MouseTrackGlowProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: 50, y: 55 });

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setPos({
        x: ((e.clientX - rect.left) / rect.width) * 100,
        y: ((e.clientY - rect.top) / rect.height) * 100,
      });
    },
    []
  );

  const handleMouseLeave = useCallback(() => setPos({ x: 50, y: 55 }), []);

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={cn("relative overflow-hidden", className)}
    >
      {/* Primary orb — tracks cursor closely */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{
          width: "380px",
          height: "380px",
          left: `${pos.x}%`,
          top: `${pos.y}%`,
          background: "rgba(139,92,246,0.22)",
          filter: "blur(80px)",
          transition: "left 0.08s ease-out, top 0.08s ease-out",
        }}
      />
      {/* Secondary orb — trails slightly for a depth effect */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{
          width: "220px",
          height: "220px",
          left: `${pos.x}%`,
          top: `${pos.y}%`,
          background: "rgba(99,102,241,0.18)",
          filter: "blur(50px)",
          transition: "left 0.18s ease-out, top 0.18s ease-out",
        }}
      />
      {children}
    </div>
  );
}
