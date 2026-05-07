'use client';

import * as React from 'react';

interface MouseTrackGlowProps {
  children: React.ReactNode;
  className?: string;
}

export function MouseTrackGlow({ children, className }: MouseTrackGlowProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [pos, setPos] = React.useState({ x: 50, y: 55 });

  const handleMouseMove = React.useCallback(
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

  const handleMouseLeave = React.useCallback(() => setPos({ x: 50, y: 55 }), []);

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative overflow-hidden${className ? ` ${className}` : ''}`}
    >
      {/* Primary orb — tracks cursor closely */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          width: '380px',
          height: '380px',
          left: `${pos.x}%`,
          top: `${pos.y}%`,
          transform: 'translate(-50%, -50%)',
          borderRadius: '9999px',
          background: 'rgba(59,130,246,0.2)',
          filter: 'blur(80px)',
          pointerEvents: 'none',
          transition: 'left 0.08s ease-out, top 0.08s ease-out',
        }}
      />
      {/* Secondary orb — trails for depth effect */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          width: '220px',
          height: '220px',
          left: `${pos.x}%`,
          top: `${pos.y}%`,
          transform: 'translate(-50%, -50%)',
          borderRadius: '9999px',
          background: 'rgba(37,99,235,0.16)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
          transition: 'left 0.18s ease-out, top 0.18s ease-out',
        }}
      />
      {children}
    </div>
  );
}
