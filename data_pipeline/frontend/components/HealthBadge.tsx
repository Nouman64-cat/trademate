"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HealthResponse } from "@/types";

export default function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Backend unreachable
      </span>
    );
  }

  if (!health) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-500">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-zinc-400" />
        Checking…
      </span>
    );
  }

  const isHealthy = health.status === "healthy";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span
        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
          isHealthy
            ? "bg-green-100 text-green-700"
            : "bg-yellow-100 text-yellow-700"
        }`}
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            isHealthy ? "bg-green-500" : "bg-yellow-500"
          }`}
        />
        {isHealthy ? "All systems operational" : "Degraded"}
      </span>

      {Object.entries(health.services).map(([name, status]) => (
        <span
          key={name}
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs ${
            status === "ok"
              ? "bg-green-50 text-green-600"
              : "bg-red-50 text-red-600"
          }`}
        >
          {name}: {status === "ok" ? "ok" : "error"}
        </span>
      ))}
    </div>
  );
}
