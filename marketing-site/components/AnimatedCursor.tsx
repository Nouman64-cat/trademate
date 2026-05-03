"use client";

import { useEffect, useState, useRef } from "react";

type VehicleType = "truck" | "plane" | "ship";

export default function AnimatedCursor() {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [trailingPosition, setTrailingPosition] = useState({ x: -100, y: -100 });
  const [vehicle, setVehicle] = useState<VehicleType>("truck");
  const requestRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const vehicles: VehicleType[] = ["truck", "plane", "ship"];
    const interval = setInterval(() => {
      setVehicle((prev) => {
        const currentIndex = vehicles.indexOf(prev);
        return vehicles[(currentIndex + 1) % vehicles.length];
      });
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let currentX = -100;
    let currentY = -100;
    let targetX = -100;
    let targetY = -100;

    const handleMouseMove = (e: MouseEvent) => {
      targetX = e.clientX;
      targetY = e.clientY;
    };

    const animate = () => {
      currentX += (targetX - currentX) * 0.1;
      currentY += (targetY - currentY) * 0.1;
      
      setPosition({ x: targetX, y: targetY });
      setTrailingPosition({ x: currentX, y: currentY });
      
      requestRef.current = requestAnimationFrame(animate);
    };

    window.addEventListener("mousemove", handleMouseMove);
    requestRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, []);

  const getRotation = () => {
    if (position.x > trailingPosition.x + 2) return -10;
    if (position.x < trailingPosition.x - 2) return 10;
    return 0;
  };

  const vehicleData = {
    truck: { w: 36, h: 28 },
    plane: { w: 44, h: 24 },
    ship: { w: 44, h: 36 },
  };

  const vehicles: VehicleType[] = ["truck", "plane", "ship"];
  const currentIndex = vehicles.indexOf(vehicle);
  const prevIndex = (currentIndex - 1 + vehicles.length) % vehicles.length;
  const prevVehicle = vehicles[prevIndex];

  const renderTruck = () => (
    <svg width="36" height="28" viewBox="0 0 36 28" fill="none">
      <g fill="var(--color-brand-400)">
        <path d="M2 18L2 26L14 26L14 18L2 18Z" />
        <path d="M2 18L2 20L8 20L8 12L2 12Z" />
        <rect x="3" y="13" width="5" height="5" fill="var(--color-brand-500)" opacity="0.6" rx="1"/>
        <path d="M14 8L14 26L34 26L34 8L14 8Z" />
        <circle cx="8" cy="26" r="3" fill="var(--color-brand-500)" />
        <circle cx="28" cy="26" r="3" fill="var(--color-brand-500)" />
        <circle cx="28" cy="26" r="1.5" fill="var(--color-neutral-400)" />
      </g>
    </svg>
  );

  const renderPlane = () => (
    <svg width="44" height="24" viewBox="0 0 44 24" fill="none">
      <g fill="var(--color-brand-400)">
        {/* Main body - fuselage */}
        <ellipse cx="22" cy="12" rx="18" ry="4" />
        <ellipse cx="22" cy="12" rx="14" ry="3" fill="var(--color-brand-400)" />
        
        {/* Nose */}
        <path d="M40 12Q44 12 44 12Q44 8 40 8L38 8Q36 8 36 10L36 14Q36 16 38 16L40 16Q44 16 44 12Z" fill="var(--color-brand-400)" />
        
        {/* Cockpit */}
        <ellipse cx="34" cy="11" rx="3" ry="2" fill="var(--color-brand-500)" opacity="0.5" />
        
        {/* Main wing (left) */}
        <path d="M20 12L20 4L26 4L28 12L26 12Z" fill="var(--color-brand-400)" />
        
        {/* Main wing (right) */}
        <path d="M20 12L20 20L26 20L28 12L26 12Z" fill="var(--color-brand-400)" />
        
        {/* Tail wing (horizontal) */}
        <path d="M6 12L6 8L10 8L12 12L10 12Z" fill="var(--color-brand-400)" />
        <path d="M6 12L6 16L10 16L12 12L10 12Z" fill="var(--color-brand-400)" />
        
        {/* Vertical tail */}
        <path d="M4 4L4 8L8 4Z" fill="var(--color-brand-400)" />
        
        {/* Engine */}
        <ellipse cx="24" cy="6" rx="2" ry="1.5" fill="var(--color-brand-500)" opacity="0.6" />
        <ellipse cx="24" cy="18" rx="2" ry="1.5" fill="var(--color-brand-500)" opacity="0.6" />
      </g>
    </svg>
  );

  const renderShip = () => (
    <svg width="44" height="36" viewBox="0 0 44 36" fill="none">
      <g fill="var(--color-brand-400)">
        {/* Hull */}
        <path d="M4 20L8 32L40 32L44 20L44 18L0 18L0 28L4 20Z" />
        
        {/* Cabin/deck */}
        <rect x="8" y="6" width="28" height="14" rx="2" />
        
        {/* Windows */}
        <circle cx="14" cy="13" r="2" fill="var(--color-brand-500)" opacity="0.6"/>
        <circle cx="22" cy="13" r="2" fill="var(--color-brand-500)" opacity="0.6"/>
        <circle cx="30" cy="13" r="2" fill="var(--color-brand-500)" opacity="0.6"/>
        
        {/* Bridge */}
        <rect x="16" y="2" width="12" height="4" rx="1" fill="var(--color-brand-400)" />
        
        {/* Mast */}
        <rect x="21" y="4" width="2" height="6" fill="var(--color-brand-400)" />
        
        {/* Flag */}
        <path d="M23 4L23 6L28 5L23 4Z" fill="var(--color-brand-500)" />
        
        {/* Cargo lines on deck */}
        <path d="M12 24L32 24" stroke="var(--color-brand-500)" strokeWidth="1.5" strokeDasharray="2 2"/>
        
        {/* Water line */}
        <path d="M2 28L42 28" stroke="var(--color-brand-500)" strokeWidth="1" opacity="0.5"/>
      </g>
    </svg>
  );

  const renderVehicle = (v: VehicleType) => {
    switch (v) {
      case "truck": return renderTruck();
      case "plane": return renderPlane();
      case "ship": return renderShip();
      default: return renderTruck();
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        left: 0,
        top: 0,
        pointerEvents: "none",
        zIndex: 9999,
        transform: `translate(${trailingPosition.x - vehicleData[vehicle].w / 2 + 4}px, ${trailingPosition.y - vehicleData[vehicle].h / 2 + 4}px) rotate(${getRotation()}deg)`,
        transition: "transform 0.15s linear",
        filter: "drop-shadow(0 0 20px rgba(59,130,246,0.8))",
      }}
    >
      {prevVehicle !== vehicle && (
        <div style={{ position: "absolute", inset: 0, opacity: 0, animation: "fadeOut 0.4s ease-out forwards" }}>
          {renderVehicle(prevVehicle)}
        </div>
      )}
      <div style={{ animation: "fadeIn 0.4s ease-out forwards" }}>
        {renderVehicle(vehicle)}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.7); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes fadeOut {
          from { opacity: 1; transform: scale(1); }
          to { opacity: 0; transform: scale(0.7); }
        }
      `}</style>
    </div>
  );
}