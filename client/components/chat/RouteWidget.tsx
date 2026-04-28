"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type * as LType from "leaflet";
const L = typeof window !== "undefined" ? require("leaflet") : null;
import "leaflet/dist/leaflet.css";
import {
  Ship, Plane, AlertTriangle, AlertCircle, Info,
  ChevronDown, ChevronUp, DollarSign, Clock, BarChart2,
  Zap, Scale, CheckCircle2, MapPin, Maximize2, Minimize2, X,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { RouteEvaluationResponse, RouteResult } from "@/types/routes";
import { useThemeStore } from "@/stores/themeStore";

// ── Map helpers (mirrors routes/page.tsx) ────────────────────────────────────

const ROUTE_COORDINATES: Record<string, [number, number]> = {
  // ── Pakistan ports / air gateways (origin for PK_TO_US, destination for US_TO_PK)
  PKKHI:  [24.8615, 67.0099],
  PKKHIA: [24.8615, 67.0099],  // alias used in pk_usa_routes.json
  PKBQM:  [24.7872, 67.3431],  // Port Qasim
  KHI:    [24.9061, 67.1605],
  LHE:    [31.5216, 74.4036],  // Allama Iqbal Intl (Lahore)
  ISB:    [33.5593, 72.8258],  // Islamabad Intl
  SKT:    [32.5353, 74.3639],  // Sialkot Intl

  // ── Transshipment hubs ────────────────────────────────────────────────────
  LKCMB:        [6.9271,   79.8612],
  "Colombo":    [6.9271,   79.8612],  // plain name used in pk_usa_routes.json
  SGSIN:        [1.2644,  103.8222],
  "Singapore":  [1.3521,  103.8198],  // plain name used in pk_usa_routes.json
  MYPKG:        [2.9734,  101.4094],
  "Port Klang": [2.9734,  101.4094],  // plain name used in pk_usa_routes.json
  AEJEA:        [25.0555,  55.0537],
  "Jebel Ali":  [25.0140,  55.1300],  // hub used in us_pk_routes.json
  DXB:          [25.2532,  55.3657],
  "Dubai (DXB)":[25.2532,  55.3657],
  DOH:          [25.2736,  51.6080],
  "Doha (DOH)": [25.2736,  51.6080],
  IST:          [41.2762,  28.7519],
  "Istanbul (IST)": [41.2762, 28.7519],
  "Port Said":  [31.2565,  32.2841],  // plain name used in pk_usa_routes.json

  // ── Canals ────────────────────────────────────────────────────────────────
  "Suez Canal":   [30.5495,  32.3137],
  "Panama Canal": [ 9.0800, -79.6800],

  // ── US ports / air gateways (destination for PK_TO_US, origin for US_TO_PK)
  JFK:   [40.6413,  -73.7781],
  ORD:   [41.9742,  -87.9073],
  LAX:   [33.9416, -118.4085],
  MIA:   [25.7959,  -80.2870],
  ATL:   [33.6407,  -84.4277],
  DFW:   [32.8998,  -97.0403],
  IAH:   [29.9902,  -95.3368],  // Houston Intercontinental
  SEA:   [47.4502, -122.3088],  // Seattle-Tacoma airport
  USLAX: [33.7405, -118.2775],
  USLGB: [33.7500, -118.2167],
  USNYC: [40.6782,  -73.9442],
  USNYK: [40.6782,  -73.9442],  // alias used in pk_usa_routes.json
  USSAV: [32.0809,  -81.0912],
  USBAL: [39.2904,  -76.6122],
  USMIA: [25.7959,  -80.2870],
  USCHI: [41.8781,  -87.6298],
  USSEA: [47.6062, -122.3321],
  USHOU: [29.7604,  -95.3698],  // Houston port
  USATL: [33.7490,  -84.3880],
  USDFW: [32.7767,  -96.7970],

  // ── City name fallbacks (used when port code lookup fails) ────────────────
  "Karachi":     [24.8607,   67.0011],
  "Lahore":      [31.5204,   74.3587],
  "Faisalabad":  [31.4504,   73.1350],
  "Sialkot":     [32.4945,   74.5229],
  "Islamabad":   [33.6844,   73.0479],
  "Peshawar":    [34.0151,   71.5249],
  "Multan":      [30.1575,   71.5249],
  "Los Angeles": [34.0522, -118.2437],
  "Long Beach":  [33.7701, -118.1937],
  "New York":    [40.7128,  -74.0060],
  "Chicago":     [41.8781,  -87.6298],
  "Miami":       [25.7617,  -80.1918],
  "Savannah":    [32.0809,  -81.0912],
  "Seattle":     [47.6062, -122.3321],
  "Houston":     [29.7604,  -95.3698],
  "Dallas":      [32.7767,  -96.7970],
  "Atlanta":     [33.7490,  -84.3880],
};

function getLocationCoordinates(location: string): [number, number] | null {
  const trimmed = location.trim();
  const codeMatch = trimmed.match(/\(([A-Z0-9']+)\)/);
  if (codeMatch && ROUTE_COORDINATES[codeMatch[1]]) return ROUTE_COORDINATES[codeMatch[1]];
  if (ROUTE_COORDINATES[trimmed]) return ROUTE_COORDINATES[trimmed];
  const fallback = trimmed.split(",")[0].trim();
  return ROUTE_COORDINATES[fallback] ?? null;
}

// Returns the short readable name for a port/hub/canal string
function getShortName(location: string): string {
  // "Colombo, Sri Lanka (LKCMB)" → "Colombo"
  // "Los Angeles (USLAX)"        → "Los Angeles"
  // "Suez Canal"                 → "Suez Canal"
  // "Karachi Intl (KHI)"         → "Karachi Intl"
  return location.replace(/\s*\([^)]+\)/, "").split(",")[0].trim();
}

type StopType = "origin" | "hub" | "destination";
interface RouteStop {
  name:  string;
  coord: [number, number];
  type:  StopType;
}

function getRouteStops(route: RouteResult, destinationCity: string): RouteStop[] {
  const normalizedDest = destinationCity.toLowerCase();
  const destPort = route.destination_ports.find(p => p.toLowerCase().includes(normalizedDest)) ?? route.destination_ports[0];
  // Prefer the destination city name directly when we have coordinates for it.
  // This fixes air routes where the port code (JFK) doesn't match the actual
  // destination city (Miami, Baltimore, etc.) — we pin the real city instead.
  const destName = ROUTE_COORDINATES[destinationCity] ? destinationCity : destPort;
  const raw: { name: string; type: StopType }[] = [
    { name: route.origin_port, type: "origin" },
    ...route.hubs.map(h => ({ name: h, type: "hub" as StopType })),
    { name: destName, type: "destination" },
  ];
  return raw
    .map(s => ({ ...s, coord: getLocationCoordinates(s.name) }))
    .filter((s): s is RouteStop => s.coord !== null);
}

// Inline-style label rendered via L.divIcon (no Tailwind – outside React tree)
function makeLabelIcon(text: string, type: StopType): any {
  if (!L) return null;
  const bg =
    type === "origin"      ? "#7c3aed" :
    type === "destination" ? "#0f766e" : "#1d4ed8";
  return L.divIcon({
    className: "",
    html: `<div style="
      background:${bg};
      color:#fff;
      border-radius:4px;
      padding:2px 6px;
      font-size:9px;
      font-weight:700;
      white-space:nowrap;
      box-shadow:0 1px 4px rgba(0,0,0,0.35);
      pointer-events:none;
    ">${text}</div>`,
    iconSize:   [0, 0],
    iconAnchor: [-6, 18], // offset so label sits just above-right of the dot
  });
}

// ── Route map component ──────────────────────────────────────────────────────

function RouteMap({ data }: { data: RouteEvaluationResponse }) {
  const { resolvedTheme } = useThemeStore();
  const isDark = resolvedTheme() === "dark";

  const [isFullscreen, setIsFullscreen] = useState(false);
  // Incrementing this key forces a full Leaflet destroy-and-recreate after the
  // fullscreen CSS has been applied, so the map initialises at the correct size.
  const [mapKey, setMapKey] = useState(0);

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef  = useRef<LType.Map | null>(null);
  const routeLayerRef   = useRef<LType.LayerGroup | null>(null);
  const tileLayerRef    = useRef<LType.TileLayer | null>(null);

  const routeLineData = useMemo(() => data.routes.map(route => ({
    route,
    stops:       getRouteStops(route, data.destination_city),
    isOptimized: route.id === data.routes[0]?.id,
  })).filter(item => item.stops.length >= 2), [data]);

  // After isFullscreen flips the CSS, wait for the browser to reflow then
  // bump mapKey so the build effect runs on a correctly-sized container.
  useEffect(() => {
    const timer = setTimeout(() => setMapKey(k => k + 1), 200);
    return () => clearTimeout(timer);
  }, [isFullscreen]);

  // Build / rebuild the entire Leaflet map whenever route data or mapKey changes.
  // Destroying the old instance each time guarantees tiles are always requested
  // for the actual container dimensions (fixes blank tiles on fullscreen toggle).
  useEffect(() => {
    if (!L || !mapContainerRef.current) return;

    // Destroy any stale Leaflet instance before creating a fresh one.
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
      routeLayerRef.current  = null;
      tileLayerRef.current   = null;
    }

    mapInstanceRef.current = L.map(mapContainerRef.current, {
      zoomControl: true,
      scrollWheelZoom: true,
      center: [25, 40],
      zoom: 3,
    });
    const tileUrl = isDark
      ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
    tileLayerRef.current = L.tileLayer(tileUrl, {
      attribution: '&copy; OpenStreetMap, CARTO',
      keepBuffer: 4,
    }).addTo(mapInstanceRef.current);
    routeLayerRef.current = L.layerGroup().addTo(mapInstanceRef.current);

    const map        = mapInstanceRef.current;
    const layerGroup = routeLayerRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();
    const allCoords:    [number, number][] = [];
    const labeledCoords = new Set<string>();

    routeLineData.forEach(({ route, stops, isOptimized }) => {
      const coords = stops.map(s => s.coord);

      const line = L.polyline(coords, {
        color:     isOptimized ? "#7c3aed" : "#38bdf8",
        weight:    isOptimized ? 4 : 2,
        opacity:   isOptimized ? 0.9 : 0.4,
        dashArray: route.mode === "AIR" ? "7 9" : undefined,
      }).addTo(layerGroup);
      line.bindTooltip(
        `<b>${route.id}</b> · ${route.name}<br/>${route.mode === "AIR" ? "✈ Air" : "🚢 Sea"}`,
        { sticky: true, direction: "auto" }
      );

      stops.forEach(({ name, coord, type }) => {
        const dotColor =
          type === "origin"      ? "#7c3aed" :
          type === "destination" ? "#0f766e" : "#3b82f6";

        L.circleMarker(coord, {
          radius:      type !== "hub" ? 6 : 4,
          fillColor:   dotColor,
          color:       "#fff",
          weight:      2,
          fillOpacity: 1,
        }).addTo(layerGroup);

        const key = coord.join(",");
        if (!labeledCoords.has(key)) {
          labeledCoords.add(key);
          const shortName = getShortName(name);
          const roleTag =
            type === "origin"      ? ` (Origin)` :
            type === "destination" ? ` (Dest.)` : "";
          L.marker(coord, {
            icon:         makeLabelIcon(shortName + roleTag, type),
            interactive:  false,
            zIndexOffset: 600,
          }).addTo(layerGroup);
        }
      });

      allCoords.push(...coords);
    });

    if (allCoords.length > 0) {
      map.fitBounds(L.latLngBounds(allCoords), { padding: [40, 40] });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeLineData, mapKey]);

  // Update tile URL when theme changes without rebuilding the whole map.
  useEffect(() => {
    if (tileLayerRef.current) {
      const tileUrl = isDark
        ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
      tileLayerRef.current.setUrl(tileUrl);
    }
  }, [isDark]);

  // Escape key exits fullscreen
  useEffect(() => {
    if (!isFullscreen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setIsFullscreen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isFullscreen]);

  // Cleanup on unmount
  useEffect(() => () => {
    mapInstanceRef.current?.remove();
    mapInstanceRef.current = null;
    routeLayerRef.current  = null;
    tileLayerRef.current   = null;
  }, []);

  const legend = (
    <div className="flex flex-wrap gap-3 text-[9px] text-zinc-500 dark:text-zinc-400">
      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-violet-500" /> Optimized</span>
      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-sky-400" /> Other routes</span>
      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-violet-500" /> Origin</span>
      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-teal-600" /> Destination</span>
      <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-full bg-blue-500" /> Hub</span>
    </div>
  );

  // Single render tree — only the wrapper class changes.
  // The map ref div never moves, so Leaflet keeps its container.
  return (
    <div className={cn(
      isFullscreen
        ? "fixed inset-0 z-[9999] flex flex-col bg-white dark:bg-zinc-950"
        : "rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2"
    )}>
      {/* Header */}
      <div className={cn(
        "flex items-center justify-between",
        isFullscreen
          ? "px-4 py-2 border-b border-zinc-200 dark:border-zinc-800 flex-shrink-0"
          : "mb-2"
      )}>
        <div className="flex items-center gap-1.5">
          <MapPin size={isFullscreen ? 14 : 12} className="text-violet-500" />
          <span className={cn("font-semibold text-zinc-800 dark:text-zinc-100", isFullscreen ? "text-sm" : "text-[10px] text-zinc-700 dark:text-zinc-300")}>
            {isFullscreen ? `Route Map — ${data.origin_city} → ${data.destination_city}` : "Route map"}
          </span>
          {isFullscreen && <span className="text-xs text-zinc-400">{data.routes.length} routes</span>}
        </div>
        <div className="flex items-center gap-2">
          {isFullscreen && legend}
          <button
            onClick={() => setIsFullscreen(v => !v)}
            className={cn(
              "flex items-center gap-1 rounded-md font-medium transition-colors",
              isFullscreen
                ? "px-2.5 py-1.5 text-xs text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                : "px-2 py-1 text-[10px] text-zinc-500 hover:text-violet-600 dark:hover:text-violet-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            )}
          >
            {isFullscreen ? <><Minimize2 size={13} /> Exit fullscreen</> : <><Maximize2 size={11} /> Expand</>}
          </button>
          {isFullscreen && (
            <button
              onClick={() => setIsFullscreen(false)}
              className="rounded-lg p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <X size={15} />
            </button>
          )}
        </div>
      </div>

      {/* Map container: explicit pixel height so Leaflet always has a non-zero size at init */}
      <div
        ref={mapContainerRef}
        className={cn(
          "w-full border border-zinc-200 dark:border-zinc-800",
          isFullscreen ? "rounded-none" : "rounded-xl"
        )}
        style={
          isFullscreen
            ? { flex: "1 1 0", minHeight: "300px" }
            : { height: "224px" }
        }
      />

      {/* Legend (embedded only — fullscreen has it in header) */}
      {!isFullscreen && <div className="mt-2">{legend}</div>}
    </div>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

const TAG_META = {
  cheapest: { label: "Cheapest",     icon: DollarSign, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800" },
  fastest:  { label: "Fastest",      icon: Zap,        color: "text-amber-600  dark:text-amber-400",    bg: "bg-amber-50  dark:bg-amber-950/40   border-amber-200   dark:border-amber-800"   },
  balanced: { label: "Best Balance", icon: Scale,      color: "text-violet-600 dark:text-violet-400",   bg: "bg-violet-50 dark:bg-violet-950/40  border-violet-200  dark:border-violet-800"  },
} as const;

const ALERT_ICONS = {
  info:     <Info         size={12} className="text-blue-500  flex-shrink-0 mt-0.5" />,
  warning:  <AlertTriangle size={12} className="text-amber-500 flex-shrink-0 mt-0.5" />,
  critical: <AlertCircle  size={12} className="text-red-500   flex-shrink-0 mt-0.5" />,
};

// ── Reliability dots ─────────────────────────────────────────────────────────

function ReliabilityDots({ score }: { score: number }) {
  const filled = Math.round(score * 5);
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className={cn("h-1.5 w-1.5 rounded-full", i < filled ? "bg-emerald-500" : "bg-zinc-300 dark:bg-zinc-600")} />
      ))}
    </div>
  );
}

// ── Scatter plot ─────────────────────────────────────────────────────────────

function ScatterPlot({ routes }: { routes: RouteResult[] }) {
  if (!routes.length) return null;
  const costs = routes.map(r => (r.cost.total_min + r.cost.total_max) / 2);
  const times = routes.map(r => (r.transit.total_min + r.transit.total_max) / 2);
  const minCost = Math.min(...costs), maxCost = Math.max(...costs);
  const minTime = Math.min(...times), maxTime = Math.max(...times);
  const W = 300, H = 160, PAD = 32;
  const x = (c: number) => PAD + ((c - minCost) / (maxCost - minCost || 1)) * (W - PAD * 2);
  const y = (t: number) => H - PAD - ((t - minTime) / (maxTime - minTime || 1)) * (H - PAD * 2);

  return (
    <svg width={W} height={H} className="mx-auto">
      <line x1={PAD} y1={H - PAD} x2={W - PAD / 2} y2={H - PAD} stroke="currentColor" strokeOpacity={0.15} />
      <line x1={PAD} y1={PAD / 2} x2={PAD}          y2={H - PAD} stroke="currentColor" strokeOpacity={0.15} />
      <text x={W / 2} y={H - 4}   textAnchor="middle" fontSize={8} fill="currentColor" opacity={0.4}>Cost</text>
      <text x={7}     y={H / 2}   textAnchor="middle" fontSize={8} fill="currentColor" opacity={0.4} transform={`rotate(-90,7,${H/2})`}>Days</text>
      {routes.map((r, i) => {
        const color = r.tag === "cheapest" ? "#10b981" : r.tag === "fastest" ? "#f59e0b" : r.tag === "balanced" ? "#7c3aed" : "#94a3b8";
        return (
          <g key={r.id}>
            <circle cx={x(costs[i])} cy={y(times[i])} r={6} fill={color} fillOpacity={0.18} stroke={color} strokeWidth={1.5} />
            <text x={x(costs[i])} y={y(times[i]) - 8} textAnchor="middle" fontSize={7} fill={color} fontWeight={600}>{r.id}</text>
          </g>
        );
      })}
    </svg>
  );
}

// ── Route card ───────────────────────────────────────────────────────────────

function RouteCard({ route }: { route: RouteResult }) {
  const [expanded, setExpanded] = useState(false);
  const tagMeta = route.tag ? TAG_META[route.tag as keyof typeof TAG_META] : null;
  const TagIcon = tagMeta?.icon;

  return (
    <div className={cn(
      "rounded-xl border bg-white dark:bg-zinc-900 text-sm",
      tagMeta ? `${tagMeta.bg} shadow-sm` : "border-zinc-200 dark:border-zinc-800"
    )}>
      <div className="p-3">
        {/* Header */}
        <div className="flex items-start gap-2 mb-2">
          <div className={cn(
            "h-7 w-7 rounded-lg flex items-center justify-center flex-shrink-0",
            route.mode === "AIR" ? "bg-sky-100 dark:bg-sky-900/30 text-sky-600" : "bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600"
          )}>
            {route.mode === "AIR" ? <Plane size={13} /> : <Ship size={13} />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-50 leading-snug">{route.name}</span>
              {tagMeta && TagIcon && (
                <span className={cn("inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-full border", tagMeta.color, tagMeta.bg)}>
                  <TagIcon size={9} />{tagMeta.label}
                </span>
              )}
            </div>
            <p className="text-[10px] text-zinc-400 mt-0.5">{route.hubs.join(" → ")}</p>
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-3 gap-1.5">
          <div className="rounded-lg bg-zinc-50 dark:bg-zinc-800/60 p-2">
            <div className="flex items-center gap-1 text-zinc-400 mb-0.5">
              <DollarSign size={10} />
              <span className="text-[9px] font-medium uppercase tracking-wide">Cost</span>
            </div>
            <p className="text-xs font-bold text-zinc-800 dark:text-zinc-100">{fmt(route.cost.total_min)}</p>
            <p className="text-[9px] text-zinc-400">–{fmt(route.cost.total_max)}</p>
          </div>
          <div className="rounded-lg bg-zinc-50 dark:bg-zinc-800/60 p-2">
            <div className="flex items-center gap-1 text-zinc-400 mb-0.5">
              <Clock size={10} />
              <span className="text-[9px] font-medium uppercase tracking-wide">Transit</span>
            </div>
            <p className="text-xs font-bold text-zinc-800 dark:text-zinc-100">{route.transit.total_min}d</p>
            <p className="text-[9px] text-zinc-400">–{route.transit.total_max} days</p>
          </div>
          <div className="rounded-lg bg-zinc-50 dark:bg-zinc-800/60 p-2">
            <div className="flex items-center gap-1 text-zinc-400 mb-0.5">
              <BarChart2 size={10} />
              <span className="text-[9px] font-medium uppercase tracking-wide">Reliab.</span>
            </div>
            <ReliabilityDots score={route.reliability_score} />
            <p className="text-[9px] text-zinc-400 mt-0.5">{Math.round(route.reliability_score * 100)}%</p>
          </div>
        </div>

        {/* Alerts */}
        {route.alerts.length > 0 && (
          <div className="mt-2 space-y-1">
            {route.alerts.map((a, i) => (
              <div key={i} className="flex items-start gap-1.5 text-[10px] rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 px-2 py-1.5">
                {ALERT_ICONS[a.level as keyof typeof ALERT_ICONS] ?? ALERT_ICONS.info}
                <span className="text-amber-800 dark:text-amber-300 leading-relaxed">{a.message}</span>
              </div>
            ))}
          </div>
        )}

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded(e => !e)}
          className="mt-2 w-full flex items-center justify-center gap-1 text-[10px] text-zinc-400 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
        >
          {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          {expanded ? "Hide breakdown" : "View cost breakdown"}
        </button>
      </div>

      {/* Cost breakdown */}
      {expanded && (
        <div className="border-t border-zinc-100 dark:border-zinc-800 px-3 pb-3 pt-2">
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px]">
            {[
              ["Inland haulage",    route.cost.inland_haulage],
              ["Origin THC",        route.cost.origin_thc],
              ["Freight (min)",     route.cost.ocean_air_freight_min],
              ["Freight (max)",     route.cost.ocean_air_freight_max],
              ["Transshipment THC", route.cost.transshipment_thc],
              ["Fixed charges",     route.cost.fixed_charges],
              ["Destination THC",   route.cost.destination_thc],
              ["Customs broker",    route.cost.customs_broker],
              ["Drayage",           route.cost.drayage],
              ["HMF",               route.cost.hmf],
              ["MPF",               route.cost.mpf],
              ["Import duty",       route.cost.import_duty],
            ].map(([label, val]) => (
              <>
                <span key={`l-${label}`} className="text-zinc-500 dark:text-zinc-400">{label}</span>
                <span key={`v-${label}`} className="text-right tabular-nums text-zinc-700 dark:text-zinc-300">{fmt(val as number)}</span>
              </>
            ))}
          </div>
          <div className="mt-2 pt-1.5 border-t border-zinc-100 dark:border-zinc-800 flex justify-between text-[10px] font-semibold text-zinc-800 dark:text-zinc-100">
            <span>Total</span>
            <span>{fmt(route.cost.total_min)} – {fmt(route.cost.total_max)}</span>
          </div>
          <p className="mt-1.5 text-[10px] text-zinc-400">
            {route.carriers.join(", ")} · {route.frequency_per_week}× per week
            {route.rate_source === "live" && <span className="ml-1 text-emerald-500">· live rate</span>}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Main widget ──────────────────────────────────────────────────────────────

export function RouteWidget({ data }: { data: RouteEvaluationResponse }) {
  const [showAll, setShowAll] = useState(false);

  const topRoutes = ["cheapest", "fastest", "balanced"]
    .map(tag => data.routes.find(r => r.id === data.recommended[tag as keyof typeof data.recommended]))
    .filter((r): r is RouteResult => Boolean(r) && Boolean(r?.tag))
    .filter((r, i, arr) => arr.findIndex(x => x.id === r.id) === i);

  const otherRoutes = data.routes.filter(r => !topRoutes.some(t => t.id === r.id));

  return (
    <div className="mt-3 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-md bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
              <Ship size={12} className="text-white" />
            </div>
            <div>
              <p className="text-xs font-semibold text-zinc-800 dark:text-zinc-100">
                {data.origin_city} → {data.destination_city}
              </p>
              <p className="text-[10px] text-zinc-500">
                {data.routes.length} routes · {data.cargo_type} · {fmt(data.cargo_value_usd)} · Duty {data.duty_rate_pct}%
              </p>
            </div>
          </div>
          {/* Recommended badges */}
          <div className="flex gap-1.5 flex-wrap">
            {topRoutes.map(r => {
              const meta = TAG_META[r.tag as keyof typeof TAG_META];
              const Icon = meta.icon;
              return (
                <span key={r.id} className={cn("text-[9px] px-2 py-0.5 rounded-full border font-semibold flex items-center gap-0.5", meta.color, meta.bg)}>
                  <Icon size={9} /> {meta.label}: {r.id}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      <div className="p-3 space-y-3">
        {/* Route map */}
        <RouteMap data={data} />

        {/* Scatter plot */}
        {data.routes.length > 1 && (
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2">
            <p className="text-[9px] font-semibold text-zinc-500 uppercase tracking-wide mb-2 text-center">Cost vs. Transit Time</p>
            <ScatterPlot routes={data.routes} />
            <p className="text-[9px] text-zinc-400 text-center mt-1">Lower-left = fast & cheap</p>
          </div>
        )}

        {/* Recommended routes */}
        {topRoutes.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <CheckCircle2 size={12} className="text-violet-500" />
              <span className="text-[10px] font-semibold text-zinc-700 dark:text-zinc-300">Recommended</span>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {topRoutes.map(r => <RouteCard key={r.id} route={r} />)}
            </div>
          </div>
        )}

        {/* All other routes (collapsed by default) */}
        {otherRoutes.length > 0 && (
          <div>
            <button
              onClick={() => setShowAll(v => !v)}
              className="flex items-center gap-1 text-[10px] text-zinc-500 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
            >
              {showAll ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
              {showAll ? "Hide" : "Show"} {otherRoutes.length} other route{otherRoutes.length > 1 ? "s" : ""}
            </button>
            {showAll && (
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                {otherRoutes.map(r => <RouteCard key={r.id} route={r} />)}
              </div>
            )}
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-[9px] text-zinc-400 dark:text-zinc-600 text-center px-2">
          ⚠ {data.disclaimer}
        </p>
      </div>
    </div>
  );
}
