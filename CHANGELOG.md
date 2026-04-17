# CHANGELOG

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
- LLM-generated conversation titles via `gpt-4o-mini` after the first exchange; sidebar shows a skeleton loader until the title arrives
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

