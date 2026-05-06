// ─── TradeMate Marketing Site — Static Mock Data ─────────────────────────────

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  bio: string;
  avatar: string;
  linkedin?: string;
  github?: string;
}

export interface Testimonial {
  id: string;
  quote: string;
  author: string;
  title: string;
  company: string;
  avatar: string;
  rating: number;
}

export interface PlatformStat {
  id: string;
  value: string;
  numericValue: number;
  suffix: string;
  label: string;
  description: string;
}

export interface PricingFeature {
  label: string;
  included: boolean;
  note?: string;
}

export interface PricingTier {
  id: string;
  name: string;
  description: string;
  price: {
    monthly: number;
    annual: number;
  };
  badge?: string;
  isPopular?: boolean;
  cta: string;
  features: PricingFeature[];
}

export interface Feature {
  id: string;
  slug: string;
  name: string;
  tagline: string;
  description: string;
  icon: string;
  category: string;
  capabilities: string[];
  techNote: string;
}

// ── Team ─────────────────────────────────────────────────────────────────────

export const team: TeamMember[] = [
  {
    id: "tm-1",
    name: "Abdul Rehman",
    role: "AI Engineer",
    bio: `Architected ${process.env.NEXT_PUBLIC_APP_NAME}'s multi-agent LangGraph pipeline, knowledge graph ingestion, and the FastAPI microservices backbone. Passionate about making global trade accessible through AI.`,
    avatar: "/images/team/placeholder-team.webp",
    linkedin: "https://www.linkedin.com/in/abdul-rehman-54621a266/",
    github: "https://github.com/AbdulRehman942004",
  },
  {
    id: "tm-2",
    name: "Akif Aziz",
    role: "Frontend Engineer & Product Designer",
    bio: "Leads the client and admin portal UX, chat interface, route visualizations, and marketing site. Focuses on turning complex trade data into intuitive, actionable interfaces.",
    avatar: "/images/team/placeholder-team.webp",
    linkedin: "https://www.linkedin.com/in/akif-aziz-211972281/",
    github: "https://github.com",
  },
  {
    id: "tm-3",
    name: "Hussain Adnan",
    role: "Backend Engineer & DevOps",
    bio: "Manages the Docker Compose infrastructure, Celery task scheduling, AWS SES email integration, and CI/CD pipelines. Ensures TradeMate runs reliably at scale.",
    avatar: "/images/team/placeholder-team.webp",
    linkedin: "https://www.linkedin.com/in/hussain-adnan-553b65307/",
    github: "https://github.com/hussainrizvipk03-debug",
  },
  // {
  //   id: "tm-4",
  //   name: "Nouman Ijaz",
  //   role: "Full Stack Engineer",
  //   bio: `Responsible for the RAG data pipeline, semantic chunking strategy, Pinecone vector indexing, and the automated research runner that keeps ${process.env.NEXT_PUBLIC_APP_NAME}'s knowledge base current.`,
  //   avatar: "/images/team/placeholder-team.webp",
  //   linkedin: "https://www.linkedin.com/in/nouman-ejaz-64251125b/",
  //   github: "https://github.com/Nouman64-cat",
  // },
];

// ── Testimonials ──────────────────────────────────────────────────────────────

export const testimonials: Testimonial[] = [
  {
    id: "t-1",
    quote:
      `${process.env.NEXT_PUBLIC_APP_NAME} cut our HS code classification time from hours to seconds. What used to require sifting through multiple databases and a compliance expert is now a single AI-powered query. It's a genuine game-changer for our import operations.`,
    author: "Adnan Saeed Rizvi",
    title: "CEO",
    company: "Saeed Trading and Co., Islamabad",
    avatar: "/images/team/placeholder-team.webp",
    rating: 5,
  },
  {
    id: "t-2",
    quote:
      "The real-time tariff and shipping analysis is game-changing. Being able to ask 'what's the total landed cost from Karachi to Los Angeles?' and get a breakdown instantly gives us a massive edge over our competitors.",
    author: "Syed Faraz Mehdi",
    title: "Operations Director",
    company: "Rizviz International Impex, Lahore",
    avatar: "/images/team/placeholder-team.webp",
    rating: 5,
  },
  {
    id: "t-3",
    quote:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s ability to instantly retrieve and summarize complex customs documents and SROs has transformed our workflow. It's literally like having a trade expert available 24/7.`,
    author: "Furqan Saeed",
    title: "Managing Partner",
    company: "Fed Point, USA",
    avatar: "/images/team/placeholder-team.webp",
    rating: 5,
  },
];

// ── Platform Stats ─────────────────────────────────────────────────────────────

export const platformStats: PlatformStat[] = [
  {
    id: "s-1",
    value: "58,000+",
    numericValue: 58000,
    suffix: "+",
    label: "HS Codes Indexed",
    description: "Pakistan PCT and US HTS codes with full tariff schedules",
  },
  {
    id: "s-2",
    value: "12,400+",
    numericValue: 12400,
    suffix: "+",
    label: "Trade Documents",
    description: "Ingested into Pinecone vector store for RAG retrieval",
  },
  {
    id: "s-3",
    value: "340K+",
    numericValue: 340000,
    suffix: "+",
    label: "Graph Relationships",
    description: "Tariffs, exemptions, procedures, and anti-dumping duties",
  },
  {
    id: "s-4",
    value: "99.7%",
    numericValue: 99.7,
    suffix: "%",
    label: "Query Accuracy",
    description: "For HS code lookups validated against official schedules",
  },
  {
    id: "s-5",
    value: "< 3s",
    numericValue: 3,
    suffix: "s",
    label: "Avg Response Time",
    description: "End-to-end AI query resolution including live rate fetching",
  },
  {
    id: "s-6",
    value: "2",
    numericValue: 2,
    suffix: "",
    label: "Countries Covered",
    description: "Pakistan (PCT via TIPP) and United States (HTS) — expanding",
  },
];

// ── Pricing ────────────────────────────────────────────────────────────────────

export const pricingTiers: PricingTier[] = [
  {
    id: "starter",
    name: "Starter",
    description: "Perfect for individual traders and small import/export businesses getting started with AI-powered trade intelligence.",
    price: {
      monthly: 30,
      annual: 24,
    },
    cta: "Start Free Trial",
    features: [
      { label: "500 AI chat queries / month", included: true },
      { label: "HS code lookup (PK + US)", included: true },
      { label: "Basic tariff information", included: true },
      { label: "Shipping route suggestions", included: true },
      { label: "Email support", included: true },
      { label: "Live Freightos rate queries", included: false },
      { label: "Voice assistant access", included: false },
      { label: "Knowledge graph explorer", included: false },
      { label: "API access", included: false },
      { label: "Team seats", included: false, note: "1 user" },
      { label: "Custom document ingestion", included: false },
    ],
  },
  {
    id: "professional",
    name: "Professional",
    description: "For growing trading companies and freight forwarders who need full platform access and live market data.",
    price: {
      monthly: 90,
      annual: 72,
    },
    badge: "Most Popular",
    isPopular: true,
    cta: "Start Free Trial",
    features: [
      { label: "Unlimited AI chat queries", included: true },
      { label: "HS code lookup (PK + US)", included: true },
      { label: "Full tariff & exemption data", included: true },
      { label: "Shipping route optimization", included: true },
      { label: "Priority email & chat support", included: true },
      { label: "Live Freightos rate queries", included: true },
      { label: "Voice assistant (60 min/mo)", included: true },
      { label: "Knowledge graph explorer", included: true },
      { label: "API access", included: true, note: "10K req/mo" },
      { label: "Team seats", included: true, note: "Up to 5 users" },
      { label: "Custom document ingestion", included: false },
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    description: "For large enterprises, customs brokers, and logistics platforms that need maximum scale, compliance features, and dedicated support.",
    price: {
      monthly: 250,
      annual: 200,
    },
    cta: "Contact Sales",
    features: [
      { label: "Unlimited AI chat queries", included: true },
      { label: "HS code lookup (PK + US + more)", included: true, note: "Expanded coverage" },
      { label: "Full tariff, exemption & anti-dumping", included: true },
      { label: "Advanced route cost engine (DDP)", included: true },
      { label: "Dedicated account manager", included: true },
      { label: "Live Freightos rate queries", included: true, note: "Unlimited" },
      { label: "Voice assistant", included: true, note: "Unlimited" },
      { label: "Knowledge graph explorer", included: true },
      { label: "API access", included: true, note: "Unlimited + webhooks" },
      { label: "Team seats", included: true, note: "Unlimited" },
      { label: "Custom document ingestion", included: true },
    ],
  },
];

// ── Features ──────────────────────────────────────────────────────────────────

export const features: Feature[] = [
  {
    id: "f-1",
    slug: "ai-chat-agent",
    name: "AI Trade Chat Agent",
    tagline: "Ask any trade question. Get expert-level answers instantly.",
    description:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s core AI agent is powered by a LangGraph multi-step reasoning engine. It classifies your query, selects the right tools (Knowledge Graph, Document RAG, Live Rates), executes them concurrently, and synthesizes a clear, actionable answer — with citations.`,
    icon: "MessageSquare",
    category: "AI Intelligence",
    capabilities: [
      "Natural language trade query understanding",
      "Multi-tool concurrent execution (KG + RAG + Freightos)",
      "Streaming responses with real-time widget rendering",
      "Conversation history with PostgreSQL persistence",
      "LLM-generated conversation titles",
      "Share conversations via unique public links",
    ],
    techNote: "Powered by LangGraph StateGraph + gpt-5.4 with custom tool router",
  },
  {
    id: "f-2",
    slug: "hs-code-lookup",
    name: "HS Code Intelligence",
    tagline: "Instant classification. Precise tariffs. Zero guesswork.",
    description:
      `Stop manually searching through thousands of tariff schedule pages. ${process.env.NEXT_PUBLIC_APP_NAME}'s Knowledge Graph contains the complete Pakistan PCT and US HTS schedules — including 4, 6, and 12-digit codes with full hierarchy traversal.`,
    icon: "Search",
    category: "Trade Data",
    capabilities: [
      "Full Pakistan PCT coverage (scraped from TIPP)",
      "Complete US HTS schedule with all duty columns",
      "Prefix-based matching (4, 6, 12-digit codes)",
      "Chapter → SubChapter → Heading → SubHeading hierarchy",
      "Anti-dumping duties, SRO exemptions, and cess",
      "Linked trade procedures per HS code",
    ],
    techNote: "Data stored in Memgraph with 340K+ relationships; queried via Cypher",
  },
  {
    id: "f-3",
    slug: "knowledge-graph",
    name: "Trade Knowledge Graph",
    tagline: "Every tariff, exemption, and rule — connected.",
    description:
      `${process.env.NEXT_PUBLIC_APP_NAME} models trade data as a graph, not a flat table. Every HS code is a node with edges to its tariff rates, SRO exemptions, anti-dumping orders, regulatory procedures, cess charges, and related measures. The result is a living, queryable map of trade compliance.`,
    icon: "GitBranch",
    category: "Knowledge Graph",
    capabilities: [
      "Graph-native storage in Memgraph (Bolt protocol)",
      "Node types: HSCode, Chapter, Heading, Tariff, Exemption, Procedure, Measure, Cess, AntiDumping",
      "Relationship traversal for complex compliance chains",
      "Real-time graph statistics (nodes, relationships, coverage)",
      "Admin portal for ingestion monitoring and live log streaming",
      "Cypher-based text search across all HS descriptions",
    ],
    techNote: "Memgraph graph database; ingestion via custom Python scripts with AsyncIO",
  },
  {
    id: "f-4",
    slug: "route-planner",
    name: "Shipping Route Planner",
    tagline: "Plan the optimal route. Know the total landed cost.",
    description:
      "${process.env.NEXT_PUBLIC_APP_NAME} integrates the Freightos API to fetch live FCL/LCL ocean and air freight spot quotes. Combined with its own cost engine, it calculates the complete DDP (Delivered Duty Paid) landed cost — factoring in THC, customs brokerage, drayage, MPF, HMF, and assessed HS duty.",
    icon: "Map",
    category: "Logistics",
    capabilities: [
      "Live spot rates via Freightos API (FCL/LCL, sea/air)",
      "DDP landed cost engine: Inland Haulage + THC + Freight + Brokerage + Drayage + Fees + Duty",
      "Interactive route map with React Leaflet + CartoDB tiles",
      "Multi-leg route visualization (origin → transshipment → destination)",
      "Concurrent rate fetching (graceful Freightos fallback)",
      "Cost breakdown cards within the chat interface",
    ],
    techNote: "Freightos FaaS API + custom route_engine.py DDP calculator",
  },
  {
    id: "f-5",
    slug: "tariff-analysis",
    name: "Tariff & Duty Analysis",
    tagline: "Every duty, exemption, and SRO — explained in plain language.",
    description:
      `${process.env.NEXT_PUBLIC_APP_NAME} doesn't just look up tariff rates — it explains them. The AI synthesizes raw tariff schedule data with regulatory context to give you a clear picture of what you'll pay, what exemptions might apply, and what compliance steps are required.`,
    icon: "BarChart2",
    category: "Trade Data",
    capabilities: [
      "General duty + additional duty + regulatory duty breakdown",
      "SRO exemption identification and applicability check",
      "Anti-dumping duty alerts by origin country",
      "Cess and additional levy identification",
      "Side-by-side PK vs US tariff comparison",
      "Plain-language compliance explanations from the AI agent",
    ],
    techNote: "Combines Knowledge Graph Cypher queries + RAG document retrieval for regulatory context",
  },
  {
    id: "f-6",
    slug: "voice-assistant",
    name: "Voice Trade Assistant",
    tagline: "Speak your query. Hear your answer.",
    description:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s voice interface uses the OpenAI Realtime API (gpt-5.4 Realtime) to enable natural, spoken trade consultations. Up to 60-second real-time voice conversations give you hands-free access to the full platform intelligence.`,
    icon: "Mic",
    category: "AI Intelligence",
    capabilities: [
      "OpenAI gpt-5.4 Realtime API integration",
      "Up to 60-second voice conversations",
      "Full access to trade knowledge during voice session",
      "Automatic transcription and response display",
      "Seamless handoff from voice to text conversation",
    ],
    techNote: "OpenAI Realtime API with WebSockets; handled in server/routes/voice.py",
  },
  {
    id: "f-7",
    slug: "data-pipeline",
    name: "Document Intelligence Pipeline",
    tagline: "Your trade documents. Searchable. Queryable. Always current.",
    description:
      `${process.env.NEXT_PUBLIC_APP_NAME}'s RAG pipeline ingests trade policy documents, regulatory notices, and research reports into a Pinecone vector store. An automated researcher fetches and analyzes live news and trade publications hourly, keeping the knowledge base continuously updated.`,
    icon: "Database",
    category: "Data Infrastructure",
    capabilities: [
      "PDF and document ingestion with semantic chunking",
      "OpenAI text-embedding-3-small vector embeddings",
      "Pinecone vector store with metadata filtering",
      "Automated hourly research runner (news + trade publications)",
      "S3 persistence for ingestion checkpoints and results",
      "Admin portal with real-time job monitoring and drag-and-drop upload",
    ],
    techNote: "Semantic chunking + batch Pinecone upserts; scheduler via Celery Beat",
  },
];

// ── Navigation Links ────────────────────────────────────────────────────────

export interface NavItem {
  label: string;
  href: string;
  items?: { label: string; href: string; description?: string }[];
}

export const navLinks: NavItem[] = [
  { label: "About", href: "/about" },
  {
    label: "Product",
    href: "/product",
    items: [
      { label: "Features", href: "/features", description: "Explore all capabilities" },
      { label: "Pricing", href: "/pricing", description: "Plans for every scale" },
      { label: "Voice Assistant", href: "/voice", description: "Speak your trade queries" },
    ],
  },
  {
    label: "Solutions",
    href: "/solutions",
    items: [
      { label: "For Importers", href: "/importers", description: "Streamline your imports" },
      { label: "For Exporters", href: "/exporters", description: "Expand globally" },
      { label: "Freight Forwarders", href: "/freight-forwarders", description: "Serve clients better" },
      { label: "Enterprise", href: "/solutions/enterprise", description: "Custom solutions" },
    ],
  },
  {
    label: "Resources",
    href: "/resources",
    items: [
      { label: "Blog", href: "/blog", description: "Trade insights & updates" },
      { label: "Case Studies", href: "/case-studies", description: "Success stories" },
      { label: "Help Center", href: "/help", description: "Support & FAQs" },
    ],
  },
  { label: "Contact", href: "/contact" },
];

// ── Footer Links ────────────────────────────────────────────────────────────

export const footerLinks = {
  product: {
    title: "Product",
    links: [
      { label: "Features", href: "/features" },
      { label: "Solutions", href: "/solutions" },
      { label: "Pricing", href: "/pricing" },
      { label: "API Docs", href: "/docs" },
      { label: "Voice Assistant", href: "/voice" },
    ],
  },
  resources: {
    title: "Resources",
    links: [
      { label: "Documentation", href: "/docs" },
      { label: "Blog", href: "/blog" },
      { label: "Case Studies", href: "/case-studies" },
      { label: "Use Cases", href: "/use-cases" },
      { label: "Help Center", href: "/help" },
    ],
  },
  company: {
    title: "Company",
    links: [
      { label: "About Us", href: "/about" },
      { label: "Contact", href: "/contact" },
      { label: "Careers", href: "#" },
      { label: "Privacy Policy", href: "/privacy" },
    ],
  },
  legal: {
    title: "Legal",
    links: [
      { label: "Terms of Service", href: "/terms" },
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Cookie Policy", href: "/cookies" },
    ],
  },
};
