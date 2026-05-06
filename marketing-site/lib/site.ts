export const site = {
  name: process.env.NEXT_PUBLIC_APP_NAME || "TradeMate",
  shortName: process.env.NEXT_PUBLIC_APP_NAME || "TradeMate",
  tagline: "AI-Powered Trade Intelligence",
  description:
    "AI-powered trade intelligence platform for instant HS code classification, tariff analysis, and shipping route optimization across Pakistan and the US.",
  url: process.env.NEXT_PUBLIC_SITE_URL || "https://trademate.ai",
  ogImage: "/images/og-image.png",
  twitter: "@trademate",
  email: "hello@trademate.ai",
  phone: "+92-300-1234567",
  location: "Lahore, Pakistan",
  founded: "2024",
} as const;

export type Site = typeof site;
export default site;