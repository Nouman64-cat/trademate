<p align="center">
  <img src="https://img.shields.io/badge/version-6.8.0-blue?style=flat-square" alt="Version" />
  <img src="https://img.shields.io/badge/python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.135-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangGraph-1.1-1C3C3C?style=flat-square" alt="LangGraph" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
</p>

# TradeMate

**AI-powered trade intelligence for tariffs, HS codes, and global shipping routes.**

TradeMate is a conversational AI platform that gives customs brokers, freight forwarders, and importers/exporters instant access to tariff schedules, HS code classification, duty exemptions, live freight rates, and logistics cost analysis — all through a single chat interface. Built for the **Pakistan–US bilateral trade corridor**.

🌐 **Live at [intellotrade.com](https://www.intellotrade.com/)**

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Services & Ports](#services--ports)
- [Environment Variables](#environment-variables)
- [Day-to-Day Usage](#day-to-day-usage)
- [Hot Reload Behavior](#hot-reload-behavior)
- [External Services](#external-services)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### 🤖 AI Agent with 5 Specialized Tools
- **Pakistan PCT Search** — Vector + text search across 50,000+ Pakistan HS codes with full tariff hierarchies (CD, RD, ACD, FED, ST, IT), cess, exemptions, procedures, anti-dumping duties, and NTMs
- **US HTS Search** — Vector + text search across the full US Harmonized Tariff Schedule with general, special, and column-2 duty rates
- **Document Search** — Semantic search over trade policy documents, SROs, FTAs, and regulatory reports stored in Pinecone
- **Route Evaluation** — Bidirectional (PK→US and US→PK) shipping cost engine with live Freightos freight quotes, DDP cost breakdowns, and interactive map widgets
- **Web Search** — Anthropic Claude-powered real-time web search for current trade news, third-country tariffs, and policy updates

### 📊 Knowledge Graph
- **Memgraph** graph database with HS code hierarchies for both Pakistan (PCT) and US (HTS)
- Full relationship traversal: `Chapter → SubChapter → Heading → SubHeading → HSCode → Tariff/Cess/Exemption/Procedure/Measure/AntiDumpingDuty`
- Vector embeddings on every HS code node for semantic similarity search

### 🚢 Route Intelligence
- **Bidirectional DDP cost engine** — Calculates total landed cost including inland haulage, THC, ocean/air freight, customs brokerage, drayage, HMF, MPF, and import duties
- **Live Freightos integration** — Concurrent spot rate queries with automatic deduplication and static-rate fallback
- **Interactive route widgets** — React/Leaflet maps rendered in the chat interface with carrier info, transit breakdowns, and cost comparisons

### 🎙️ Voice Conversations
- 60-second voice interactions using OpenAI's Realtime API (`gpt-realtime-mini`)

### 🔐 Auth & Security
- JWT authentication with OTP email verification (AWS SES)
- Forgot-password flow with time-limited reset tokens
- Parameterized Cypher queries (injection-safe), read-only Memgraph sessions, rate limiting

### 🛡️ Admin Portal
- User management, system settings, A/B testing configuration
- Data pipeline monitoring (document ingestion, Pinecone stats)
- Knowledge graph dashboard (Memgraph health, HS code explorer, ingestion controls)
- TIPP scraper controls with S3 sync and live log streaming
- Security settings (2FA enforcement, session timeouts, brute-force protection)

### 📈 Recommendation System
- 4-layer recommendation engine: HS Code, Document, Route, and Tariff recommendations
- Interaction logging for personalization and analytics

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │   Client      │  │ Admin Portal │  │   Marketing Site      │    │
│  │  Next.js 16   │  │  Next.js 16  │  │  Next.js 16 (Vercel)  │    │
│  │   :3001       │  │   :3002      │  │  intellotrade.com     │    │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────────┘    │
└─────────┼─────────────────┼───────────────────────────────────────┘
          │                 │
          ▼                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Main API Server (:8000)                        │
│  FastAPI · 12 route modules · LangGraph ReAct Agent               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │   Auth   │ │   Chat   │ │  Routes  │ │  Voice   │  ...        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │
└───────┬───────────┬───────────┬───────────┬───────────────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Data    │ │Knowledge │ │  TIPP    │ │  Celery  │
│ Pipeline │ │  Graph   │ │ Scraper  │ │ Workers  │
│  :8001   │ │  :8002   │ │  :8003   │ │ + Beat   │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │             │
     ▼            ▼            ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Pinecone │ │ Memgraph │ │  AWS S3  │ │  Redis   │
│Vector DB │ │Graph DB  │ │  Bucket  │ │  Broker  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

External APIs: OpenAI · Anthropic · Freightos · AWS SES
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **AI Agent** | LangGraph 1.1 (ReAct), LangChain, OpenAI `gpt-4o`, `text-embedding-3-small` |
| **Web Search** | Anthropic Claude `claude-sonnet-4-6` with `web_search_20250305` tool |
| **Backend** | Python 3.12, FastAPI 0.135, Uvicorn, SQLModel, Pydantic v2 |
| **Frontends** | Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS 4 |
| **Knowledge Graph** | Memgraph (Bolt protocol via `neo4j` driver), MAGE vector search |
| **Vector DB** | Pinecone (`trademate-documents` index, 1536-dim embeddings) |
| **Relational DB** | PostgreSQL (users, conversations, OTPs, route history, recommendations) |
| **Task Queue** | Celery 5.4 + Redis 7 + Celery Beat (scheduled tasks) + Flower (monitoring) |
| **Live Freight** | Freightos FaaS API (concurrent spot quotes for ocean/air) |
| **Auth** | JWT (PyJWT), Argon2 password hashing, OTP via AWS SES |
| **Maps** | Leaflet + React-Leaflet + CartoDB tile layer |
| **Infrastructure** | Docker Compose, AWS S3, Vercel (marketing site) |

---

## Repository Structure

```
trademate/
├── server/                 # Main FastAPI backend (:8000)
│   ├── agent/              #   LangGraph ReAct agent + tools
│   │   ├── bot.py          #   Agent core (tools, Cypher, formatters, router)
│   │   ├── tools.py        #   Standalone retrieval helpers
│   │   └── prompts.py      #   System prompt template
│   ├── routes/             #   12 API route modules
│   ├── services/           #   Route engine, recommenders, Freightos client
│   ├── models/             #   SQLModel database models
│   ├── database/           #   PostgreSQL connection + migrations
│   ├── middleware/          #   Rate limiting
│   ├── data/               #   Static route graph JSON files
│   └── main.py             #   FastAPI application entry point
│
├── client/                 # User-facing chat app (:3001)
│   ├── app/                #   Next.js App Router pages
│   ├── components/         #   Chat UI, route widgets, layout
│   ├── stores/             #   Zustand state management
│   └── services/           #   API client
│
├── admin-portal/           # Admin dashboard (:3002)
│   └── app/                #   Dashboard, data pipeline, KG, settings
│
├── marketing-site/         # Public website (Vercel)
│   ├── app/                #   Home, Features, About, Pricing, Contact
│   ├── components/         #   Navbar, Footer, page sections
│   └── lib/                #   Static data (team, testimonials, pricing)
│
├── data_pipeline/          # Document ingestion service (:8001)
│   ├── app/                #   Extraction, embedding, Pinecone upsert
│   └── scripts/            #   Research pipeline (RSS, news, S3)
│
├── knowledge_graph/        # Memgraph interface service (:8002)
│   ├── ingest_pk.py        #   Pakistan PCT ingestion
│   ├── ingest_us.py        #   US HTS ingestion
│   ├── routes/             #   Health, stats, query, ingest endpoints
│   └── db_utils.py         #   Memgraph driver utilities
│
├── tipp_scrapping/         # TIPP rate scraper service (:8003)
│   ├── tipp_scraper.py     #   Main scraping engine
│   ├── s3_utils.py         #   AWS S3 sync utilities
│   └── main.py             #   FastAPI server with background tasks
│
├── docker-compose.yml      # Full orchestration
└── CHANGELOG.md            # Version history (v1.0.0 → v6.8.0)
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Docker** + Docker Compose | Latest | All services run as containers |
| **PostgreSQL** | 14+ | Runs on host machine, port `5432` |
| **Memgraph** | 2.x+ | Runs on host machine, port `7687` ([download](https://memgraph.com/download)) |
| **Node.js** | 20+ | Only needed for local frontend development without Docker |
| **Python** | 3.12 | Only needed for local backend development without Docker |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/AbdulRehman942004/trademate.git
cd trademate
```

### 2. Configure environment variables

Every service has a `.env.example` file. Copy each one and fill in your credentials:

```bash
# Server (main backend)
cp server/.env.example server/.env

# Client (chat app)
cp client/.env.example client/.env

# Admin Portal
cp admin-portal/.env.example admin-portal/.env

# Data Pipeline
cp data_pipeline/.env.example data_pipeline/.env

# Knowledge Graph
cp knowledge_graph/.env.example knowledge_graph/.env

# TIPP Scraper
cp tipp_scrapping/.env.example tipp_scrapping/.env

# Marketing Site (only needed if developing locally)
cp marketing-site/.env.example marketing-site/.env
```

> **Required API keys:** OpenAI, Pinecone, Anthropic, Freightos, AWS (SES + S3). See the [Environment Variables](#environment-variables) section for full details.

### 3. Start external databases

Make sure PostgreSQL and Memgraph are running on your host machine before launching Docker:

```bash
# PostgreSQL should be running on port 5432
# Create the database if it doesn't exist:
createdb trademate_db

# Start Memgraph (port 7687)
# On Linux/Mac:
memgraph
# On Windows, start via the Memgraph Desktop app or service
```

### 4. Build and launch all services

```bash
docker compose up --build
```

This starts the full stack: FastAPI server, 3 microservices, Celery workers, Celery Beat scheduler, Flower monitor, and Redis.

### 5. Verify

Open the following URLs to confirm everything is running:

| Service | URL |
|---|---|
| API Health Check | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Client App | http://localhost:3001 |
| Admin Portal | http://localhost:3002 |
| Celery Flower | http://localhost:5555 |

---

## Services & Ports

| Service | URL | Description |
|---|---|---|
| **Main API** (FastAPI) | http://localhost:8000 | Core backend — auth, chat, routes, voice, admin |
| **Data Pipeline** API | http://localhost:8001 | Document extraction, embedding, Pinecone ingestion |
| **Knowledge Graph** API | http://localhost:8002 | Memgraph interface — HS code queries, ingestion |
| **TIPP Scraper** API | http://localhost:8003 | Pakistan customs tariff rate scraping + S3 sync |
| **Client** (Next.js) | http://localhost:3001 | User-facing chat application |
| **Admin Portal** (Next.js) | http://localhost:3002 | Admin dashboard and system controls |
| **Celery Flower** | http://localhost:5555 | Background task monitoring |
| **Redis** | localhost:6379 | Internal — Celery broker and result backend |

---

## Environment Variables

### `server/.env`

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (long random string) |
| `OPENAI_API_KEY` | OpenAI API key (for gpt-4o + embeddings) |
| `ANTHROPIC_API_KEY` | Anthropic API key (for web search tool) |
| `PINECONE_API_KEY` | Pinecone API key (document vector store) |
| `FREIGHTOS_API_KEY` | Freightos FaaS API key (live freight rates) |
| `FREIGHTOS_API_SECRET` | Freightos FaaS API secret |
| `MEMGRAPH_URI` | Memgraph Bolt URI (e.g., `bolt://host.docker.internal:7687`) |
| `AWS_SES_FROM_EMAIL` | Sender email for OTP verification |
| `AWS_SES_USERNAME` | AWS SES SMTP username |
| `AWS_SES_PASSWORD` | AWS SES SMTP password |

### `client/.env`

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SERVER_URL` | Backend API URL (e.g., `http://localhost:8000`) |

### `admin-portal/.env`

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API URL (e.g., `http://localhost:8000`) |

### `data_pipeline/.env`

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (for document embeddings) |
| `PINECONE_API_KEY` | Pinecone API key |
| `AWS_S3_BUCKET_NAME` | S3 bucket for document storage (`data-trademate`) |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |

### `knowledge_graph/.env`

| Variable | Description |
|---|---|
| `MEMGRAPH_URI` | Bolt URI (e.g., `bolt://localhost:7687`) |
| `OPENAI_API_KEY` | OpenAI API key (for HS code embeddings) |

---

## Day-to-Day Usage

```bash
# Start all services
docker compose up

# Stop all services
docker compose down

# Rebuild a single service after a dependency change
docker compose up --build server
docker compose up --build client

# View logs for a specific service
docker compose logs -f server
docker compose logs -f celery-worker

# Run the client or admin portal locally (without Docker)
cd client && npm install && npm run dev
cd admin-portal && npm install && npm run dev
```

---

## Hot Reload Behavior

| Layer | Code Change | Dependency Change (pip/npm) |
|---|---|---|
| Python backends | ✅ Auto-reloads (uvicorn `--reload`) | 🔄 Container rebuild required |
| Next.js frontends | ✅ Auto-reloads (HMR) | 🔄 Container rebuild required |
| `NEXT_PUBLIC_*` env vars | — | 🔄 Container rebuild required |

---

## External Services

**PostgreSQL** — Runs on the host machine. Containers access it via `host.docker.internal:5432`. Create the `trademate_db` database before first launch.

**Memgraph** — Runs on the host machine on port `7687` (Bolt protocol). Start it before running `docker compose up`. The knowledge-graph service connects via `host.docker.internal:7687`. Install from [memgraph.com/download](https://memgraph.com/download).

---

## API Documentation

The main FastAPI server auto-generates interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

The Knowledge Graph API has its own docs:
- **KG Swagger**: http://localhost:8002/docs
- **KG API Guide**: [`knowledge_graph/README_API.md`](./knowledge_graph/README_API.md)

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- All Python code follows the existing style (type hints, docstrings)
- Frontend changes use TypeScript with strict mode
- New API endpoints include proper Pydantic schemas
- Environment variables are added to the relevant `.env.example` file

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ as a Final Year Project<br />
  <strong>TradeMate</strong> — AI-Powered Trade Intelligence
</p>
