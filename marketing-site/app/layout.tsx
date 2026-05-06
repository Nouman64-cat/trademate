import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

const siteConfig = {
  name: process.env.NEXT_PUBLIC_APP_NAME || "TradeMate",
  shortName: process.env.NEXT_PUBLIC_APP_NAME || "TradeMate",
  description:
    "AI-powered trade intelligence platform for instant HS code classification, tariff analysis, and shipping route optimization across Pakistan and the US.",
  url: process.env.NEXT_PUBLIC_SITE_URL || "https://trademate.ai",
  ogImage: "/images/og-image.png",
  twitter: "@trademate",
  email: "hello@trademate.ai",
};

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: {
    default: `${siteConfig.name} — AI-Powered Trade Intelligence`,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  keywords: [
    "HS code lookup",
    "tariff analysis",
    "trade intelligence",
    "shipping routes",
    "Pakistan PCT",
    "US HTS",
    "AI trade assistant",
    "freight calculator",
    "customs compliance",
  ],
  authors: [{ name: siteConfig.name }],
  creator: siteConfig.name,
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteConfig.url,
    siteName: siteConfig.name,
    title: siteConfig.name,
    description: siteConfig.description,
    images: [
      {
        url: siteConfig.ogImage,
        width: 1200,
        height: 630,
        alt: siteConfig.name,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: siteConfig.twitter,
    creator: siteConfig.twitter,
    title: siteConfig.name,
    description: siteConfig.description,
    images: [siteConfig.ogImage],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#3b82f6",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: siteConfig.name,
    url: siteConfig.url,
    description: siteConfig.description,
    email: siteConfig.email,
    sameAs: [
      `https://twitter.com/${siteConfig.twitter.replace("@", "")}`,
      "https://linkedin.com/company/trademate",
    ],
  };

  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`} suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          background: "var(--bg-base)",
          color: "var(--text-primary)",
        }}
      >
        <Navbar />
        <main style={{ flex: 1, paddingTop: "68px" }}>{children}</main>
        <Footer />
      </body>
    </html>
  );
}

