# CHANGELOG

### v6.8.0 -04/28/2026

#### Updated
- Made changes in the admin portal so that all the harcoded features now work. Also added a module in admin portal named token economy.

### v6.7.1 -04/28/2026

#### Updated
 - Changed System Instructions and cypher query generation mechanism to extract the correct HS code related information.

### v6.7.0 - 04/28/2026
+ Added Web Search Tool 
+ US to Pak Route Added 
+### v6.6.0 - 04/23/2026

+#### Added - TIPP Scraper API & S3 Integration
+
+- **FastAPI Scraper Server** (`tipp_scrapping/main.py`):
+  - New standalone API server for the TIPP scraping module (port 8003).
+  - Background task management for triggering Full, Product, and Detail scrapes.
+  - Real-time statistics endpoint providing row counts for all scraped data.
+  - Task status monitoring and live log streaming.
+
+- **AWS S3 Persistence Layer** (`tipp_scrapping/s3_utils.py`):
+  - Full integration with `data-trademate` S3 bucket.
+  - **Bidirectional Synchronization**: Automatically downloads checkpoints from S3 at startup to resume progress and uploads results back to the cloud.
+  - Periodic S3 syncing during long-running scraping tasks (every 50-100 items).
+  - Automated final sync of all CSVs, logs, and master files upon task completion.
+
+- **Infrastructure & Reliability**:
+  - Added `boto3`, `beautifulsoup4`, `lxml`, and `requests` to the scraping environment.
+  - Configured `.env.example` for cloud-ready deployments.
+  - Verified and fixed `.venv` dependency chain.
+
+#### Added - Admin Portal Enhancements
+
+- **Security Settings Page** (`/settings/security`):
+  - New interface for managing platform authentication policies.
+  - Configuration for password complexity (min length, symbols, numbers).
+  - Global 2FA enforcement and session timeout management.
+  - Brute force protection with configurable login attempt limits.
+  - Backend implementation with `SecuritySettings` SQLModel and admin API endpoints.
+
+#### Fixed - UI/UX Improvements
+
+- **Sidebar Dropdown Persistence**: Resolved an issue where sidebar sections would collapse during navigation. The sidebar now automatically detects and expands the parent section of the active route.
+- **UI Alignment**: Centralized the layout for General and Security settings pages to maintain design consistency across the portal.
+- **Import Errors**: Fixed multiple `ModuleNotFoundError` issues in the main server by correcting absolute `server.` imports to relative paths.
+

### v6.8.0 - 04/28/2026
#### Added 
- **Marketing Site:**
  - Implemented Landing Page
  - Implemented Feature Page
  - Implemented About Page
  - Implemented Pricing Page
  - Implemented Request Demo Form 
  - Added Navbar
  - Added Footer
#### Changes
 - Marketing site is now live at [IntelloTrade](https://www.intellotrade.com/)
- Marketing site deployed on Vercel and then linked to custom domain [IntelloTrade](https://www.intellotrade.com/)

### v6.7.0 - 04/28/2026
- Added Web Search Tool 
- US to Pak Route Added 
### v6.6.0 - 04/23/2026

#### Added - TIPP Scraper API & S3 Integration

 **FastAPI Scraper Server** (`tipp_scrapping/main.py`):
  - New standalone API server for the TIPP scraping module (port 8003).
  - Background task management for triggering Full, Product, and Detail scrapes.
  - Real-time statistics endpoint providing row counts for all scraped data.
  - Task status monitoring and live log streaming.

 **AWS S3 Persistence Layer** (`tipp_scrapping/s3_utils.py`):
  - Full integration with `data-trademate` S3 bucket.
  - **Bidirectional Synchronization**: Automatically downloads checkpoints from S3 at startup to resume progress and uploads results back to the cloud.
  - Periodic S3 syncing during long-running scraping tasks (every 50-100 items).
  - Automated final sync of all CSVs, logs, and master files upon task completion.

 **Infrastructure & Reliability**:
  - Added `boto3`, `beautifulsoup4`, `lxml`, and `requests` to the scraping environment.
  - Configured `.env.example` for cloud-ready deployments.
  - Verified and fixed `.venv` dependency chain.

#### Added - Admin Portal Enhancements

 **Security Settings Page** (`/settings/security`):
  - New interface for managing platform authentication policies.
  - Configuration for password complexity (min length, symbols, numbers).
  - Global 2FA enforcement and session timeout management.
  - Brute force protection with configurable login attempt limits.
  - Backend implementation with `SecuritySettings` SQLModel and admin API endpoints.

#### Fixed - UI/UX Improvements

**Sidebar Dropdown Persistence**: Resolved an issue where sidebar sections would collapse during navigation. The sidebar now automatically detects and expands the parent section of the active route.
**UI Alignment**: Centralized the layout for General and Security settings pages to maintain design consistency across the portal.
**Import Errors**: Fixed multiple `ModuleNotFoundError` issues in the main server by correcting absolute `server.` imports to relative paths.


### v6.5.0 - 04/23/2026

#### Added - Data Pipeline Admin Integration

- **Admin API Routes** (`server/routes/data_pipeline.py`):
  - Health monitoring for Pinecone, S3, and OpenAI services
  - Document upload endpoint with multipart file support
  - Ingestion job management with real-time status polling
  - Pipeline statistics and configuration endpoints
  - Proxy architecture to data pipeline backend (port 8001)

- **Admin Portal Pages**:
  - **Data Pipeline Dashboard** (`/data-pipeline`): System health status, statistics overview (documents ingested, vectors in Pinecone, research runs, S3 storage), quick action cards
  - **Document Ingestion** (`/data-pipeline/documents`): File upload interface with drag-and-drop, real-time job tracking with auto-refresh, status indicators (pending/processing/completed/failed), detailed job metrics (chunks, vectors, timestamps)
  - **Research Pipeline** (`/data-pipeline/research`): Trigger form for news/trade data research, configurable parameters (query, max items, fetch limit, keyword matching), automated schedule information, data source descriptions

#### Added - Knowledge Graph Admin Integration

- **Knowledge Graph API** (port 8002):
  - **Health Endpoints** (`routes/health.py`): Memgraph connection status check
  - **Statistics Endpoints** (`routes/stats.py`): Comprehensive graph stats (total nodes/relationships, HS codes by source, hierarchy breakdown, related data counts)
  - **Query Endpoints** (`routes/query.py`):
    - Get HS code details with all relationships (tariffs, exemptions, procedures, measures, cess, anti-dumping)
    - Text search across HS code descriptions
    - Hierarchy path retrieval (Chapter → SubChapter → Heading → SubHeading → HSCode)
  - **Ingestion Endpoints** (`routes/ingest.py`): Background job processing for PK/US data, live log streaming (last 100 lines), job status tracking with timestamps
  - Complete FastAPI application with auto-generated Swagger docs at `/docs`

- **Admin Proxy Routes** (`server/routes/knowledge_graph.py`):
  - Proxy all Knowledge Graph API endpoints under `/v1/admin/knowledge-graph/*`
  - Admin authentication required for all endpoints
  - Clean separation: Admin Server → KG API → Memgraph

- **Admin Portal Pages**:
  - **Knowledge Graph Dashboard** (`/knowledge-graph`): Memgraph connection health, node/relationship statistics, HS code counts (PK vs US), breakdown of tariffs, exemptions, procedures, measures, cess, anti-dumping
  - **Ingestion Control** (`/knowledge-graph/ingest`): Separate trigger buttons for Pakistan PCT and US HTS, real-time job monitoring with auto-refresh (3s intervals), expandable logs viewer with terminal-style output, concurrent ingestion prevention
  - **HS Code Explorer** (`/knowledge-graph/query`): Search interface with source selector (PK/US), detailed results display with all relationships, visual breakdown by category (tariffs, exemptions, procedures, measures), color-coded relationship cards

- **Documentation**:
  - `knowledge_graph/README_API.md`: Complete API documentation with endpoint descriptions, request/response examples, integration guide, testing instructions, production deployment tips

#### Enhanced - Navigation

- Added **Data Pipeline** section to admin sidebar with Overview, Documents, and Research sub-pages
- Added **Knowledge Graph** section to admin sidebar with Overview, Ingestion, and Query sub-pages
- Updated navigation icons (Workflow, GitBranch, Search, TrendingUp)

#### Fixed - Environment Variables

- Changed Knowledge Graph environment variables from `NEO4J_*` to `MEMGRAPH_*` for clarity
- Added fallback support for `NEO4J_*` variables for backward compatibility
- Updated `db_utils.py` to read `MEMGRAPH_URI`, `MEMGRAPH_USERNAME`, `MEMGRAPH_PASSWORD`
- Updated `.env.example` with correct Memgraph variable names
- Updated all documentation to reflect Memgraph naming

#### Technical Improvements

- **Background Job Processing**: AsyncIO subprocess execution for ingestion scripts with stdout capture
- **Real-time Log Streaming**: Live log updates during ingestion (100-line buffer)
- **Proxy Architecture**: Clean separation between admin server, data pipeline API, and knowledge graph API
- **Type Safety**: Full TypeScript coverage for all new frontend pages
- **Dark Mode Support**: Complete dark theme integration across all new pages
- **Error Handling**: Comprehensive error messages with retry mechanisms
- **Auto-polling**: Job status refresh every 2-3 seconds during execution

### v6.4.0 - 04/23/2026

#### Migrated

- Completed infrastructure migration from Neo4j to **Memgraph**, including driver initialization and connection logic.
- Updated environment variables (`MEMGRAPH_*`) across all services and config files.

#### Fixed

- Resolved Cypher query ordering constraints (`MATCH` after `OPTIONAL MATCH`) for full Memgraph compatibility.
- Fixed `UserInteraction` schema to support 20-character international HS codes (PostgreSQL migration).
- Resolved attribute mapping bugs in `RouteRecommender` for carrier data and port identifiers.

#### Enhanced

- Improved HS code and cargo value extraction in chat with robust regex patterns that filter out quantities and commas.
- Enabled prefix-based matching for HS recommendations to support 4, 6, and 12-digit codes.
- Fully integrated all 4 recommendation layers (HS, Document, Route, and Tariff) into the live chat stream.

### v6.3.0

#### Added

- Added user feedback and also updated a column in pgadmin4

### v6.2.1

#### Updated

- feat: enhance route evaluation and text search functionality with widget support and container handling

### v6.2.0 - 04/19/2026

#### Added

- Memgraph db is added.
- Enhanced the ingestions scripts and added checkpointer functions.

#### Changed

- Refined the system prompts.
- Shifted from neo4j to memgraph
- Rerun the ingestion scripts

### v6.0.1 - 04/19/2026

#### Added

- Research pipeline: RSS/news fetcher, query-driven research runner, OpenAI analysis, embeddings, and Pinecone upsert.
- Persistence of research runs to S3 under `research/` and a verifier that previews the last 3 stored runs.

#### Changed

- Batch embeddings and batched Pinecone upserts to reduce API calls and runtime.
- News fetcher tightened (AND matching by default) and limited full-HTML fetches to reduce outbound HTTP.
- Scheduler changed: researcher Lambda now runs hourly (cron).

### v6.0.0 - 04/17/2026

#### Added

- Voice Conversation feature of 60 seconds using the OpenAI Realtime API (gpt-realtime-mini)

### v5.3.0 - 04/17/2026

#### Added

- **Route Widget (UI):** Interactive maps built with React/Leaflet/CartoDB to visually plot international sea/air freight legs directly within the chat interface, containing interactive route cards and cost breakdowns.
- **Real-Time Freightos API:** Integrated the public Freightos shipping calculator (FaaS) to pull live spot quotes for ocean/air freight (FCL/LCL) concurrently. The system automatically tags results as "(Live Freightos Rate)" or gracefully falls back to cached estimates.
- **Cost Engine:** A comprehensive backend pipeline (`route_engine.py`) that calculates total landed Double Duty Paid (DDP) logistics costs. It dynamically adds up Origin Inland Haulage, Origin/Transshipment/Destination THC, Base Freight, Customs Brokerage, Destination Drayage, US Federal fees (HMF/MPF limits), and assessed HS Duty percentages.

### v5.2.0 - 04/17/2026

#### Added

- Router node that classifies each query and selects only the relevant tools (Pakistan HS, US HS, Pinecone) before passing to the agent — reduces token usage and improves reliability
- Conversation persistence: all chat messages stored in PostgreSQL (`conversations` + `messages` tables) with per-user isolation
- LLM-generated conversation titles via `gpt-5.4` after the first exchange; sidebar shows a skeleton loader until the title arrives
- OTP email verification on registration: new accounts are created with `is_verified=False`, a 6-digit code is sent via AWS SES, and the account is activated only after the code is confirmed
- Forgot-password flow: OTP request → verify OTP → reset password, all backed by short-lived JWT reset tokens (15 min)
- `verify-otp` page handles both registration verification (`mode=registration`) and password-reset (`mode=reset`) from a single UI
- Dedicated email templates: registration emails say "Verify your email", password-reset emails say "Password Reset" — no more shared copy

#### Fix

- Conversations were shared across users because the chat store persisted to `localStorage` without clearing on logout — fixed by calling `clearAll()` on the chat store during logout
- Backend now returns 403 if a user tries to access another user's conversation
- `/verify-otp`, `/forgot-password`, and `/reset-password` routes were blocked by the proxy middleware (not in `PUBLIC_PATHS`) — all three are now whitelisted
- `otp_codes.used` column was created as `varchar` instead of `boolean` — migrated with `ALTER COLUMN … TYPE BOOLEAN`
- `users.is_verified` column was missing from the database — added via `ALTER TABLE`

### v5.0.3 4/16/2026

#### Update

- Created a tool for vector db and created logs for tools

### v5.0.2 4/15/2026

#### Update

- Connected neo4j to answer queries to user.

### v5.0.1 4/15/2026

#### Update

- Changed Recursive Text Splitter to Semantic Chunking

### v5.1.0 4/15/2026

#### Added

- User Query to Vector db

### v5.0.0 4/15/2026

#### Added

- Data Pipeline (Extraction,Embedding and Ingestion)

### v4.1.0 4/15/2026

#### Added

- Shifted to Neo4j's Docker image because of the free tier's limitations.

### v4.0.0 4/15/2026

#### Added

- Made ingest-us.py that makes embeddings of US-HTS data and ingest that in Neo4j.

### v3.0.2 4/15/2026

#### Added

- Scrapped the data of US-HTC manually and added all the csv files in the data directory.

### v3.0.1 - 04/09/2026

#### Fix

- Onbording `broker` enum problem resolved

### v3.0.0 - 04/09/2026

#### Added

- Made a frontend for trademate chatbot and implemented 3 layer api architecture

### v2.1.0 - 04/09/2026

#### Added

- Added the scrapping service for PCT via TIPP.

### v2.0.0 - 04/09/2026

#### Added

- data ingestion pipeline using knowlege graph (Neo4j)

### v1.1.0 - 04/08/2026

#### Added

- User auth and `JWT mechanism`
- User onboarding mechanism

### v1.0.1 - 04/07/2026

- Update `requirements.txt`

### v1.0.0 - 04/07/2026

- Codebase setup
