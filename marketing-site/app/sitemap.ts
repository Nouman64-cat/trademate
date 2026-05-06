import { MetadataRoute } from "next";

const BASE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ?? "https://trademate.ai";

// lastModified values are static so crawlers get stable dates instead of "now"
const staticPages: { url: string; lastModified: string; priority: number }[] = [
  { url: "",                      lastModified: "2025-05-01", priority: 1.0 },
  { url: "/about",                lastModified: "2025-05-01", priority: 0.9 },
  { url: "/features",             lastModified: "2025-05-01", priority: 0.9 },
  { url: "/solutions",            lastModified: "2025-05-01", priority: 0.9 },
  { url: "/solutions/enterprise", lastModified: "2025-05-07", priority: 0.8 },
  { url: "/pricing",              lastModified: "2025-05-01", priority: 0.8 },
  { url: "/contact",              lastModified: "2025-05-01", priority: 0.8 },
  { url: "/how-it-works",         lastModified: "2025-05-01", priority: 0.8 },
  { url: "/importers",            lastModified: "2025-05-01", priority: 0.7 },
  { url: "/exporters",            lastModified: "2025-05-01", priority: 0.7 },
  { url: "/freight-forwarders",   lastModified: "2025-05-01", priority: 0.7 },
  { url: "/voice",                lastModified: "2025-05-01", priority: 0.7 },
  { url: "/docs",                 lastModified: "2025-05-01", priority: 0.7 },
  { url: "/resources",            lastModified: "2025-05-01", priority: 0.7 },
  { url: "/blog",                 lastModified: "2025-05-01", priority: 0.7 },
  { url: "/case-studies",         lastModified: "2025-05-01", priority: 0.7 },
  { url: "/use-cases",            lastModified: "2025-05-01", priority: 0.7 },
  { url: "/help",                 lastModified: "2025-05-01", priority: 0.6 },
];

export default function sitemap(): MetadataRoute.Sitemap {
  return staticPages.map((page) => ({
    url: `${BASE_URL}${page.url}`,
    lastModified: new Date(page.lastModified),
    changeFrequency: "weekly",
    priority: page.priority,
  }));
}
