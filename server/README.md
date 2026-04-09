# TradeMate — Server

FastAPI backend for TradeMate.  Handles authentication, onboarding, and the
AI-powered chat endpoint that queries a Neo4j knowledge graph and streams
responses via Server-Sent Events (SSE).

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Running the Server](#running-the-server)
5. [API Endpoints](#api-endpoints)
6. [Running Tests](#running-tests)
7. [Architecture — Chat Pipeline](#architecture--chat-pipeline)

---

## Project Structure

```
server/
├── agent/                  # LangGraph AI agent
│   ├── graph.py            # Graph topology: retrieve → generate
│   ├── nodes.py            # Node functions (retrieve, generate)
│   ├── prompts.py          # System prompt for TradeMate
│   ├── state.py            # AgentState TypedDict
│   └── tools.py            # Neo4j vector retrieval
├── database/
│   └── database.py         # SQLAlchemy engine + session
├── models/
│   └── user.py             # User SQLModel table
├── routes/
│   ├── auth.py             # /v1/register, /v1/login, /v1/onboarding
│   └── chat.py             # /v1/chat  (authenticated SSE stream)
├── schemas/
│   ├── chat.py             # ChatRequest schema
│   └── user.py             # Auth request/response schemas
├── security/
│   └── security.py         # JWT creation/decoding, Argon2 password hashing
├── tests/
│   └── test_graph_retrieval.py   # Neo4j + LLM grounding tests
├── main.py                 # FastAPI app entry point
├── .env.example            # Environment variable template
└── README.md               # This file
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | 3.11 +  |
| PostgreSQL  | 14 +    |
| Neo4j Aura  | 5 +     |

The knowledge graph must be ingested before the chat endpoint returns useful
results.  See `knowledge_graph/README.md` or run `knowledge_graph/ingest.py`.

---

## Environment Setup

### 1. Install dependencies

```bash
pip install fastapi "uvicorn[standard]" sqlmodel psycopg2-binary \
            argon2-cffi pyjwt python-dotenv \
            langchain-openai langgraph langchain-core \
            neo4j email-validator pytest
```

### 2. Create the server `.env` file

Copy the example and fill in your values:

```bash
cp .env.example .env
```

```env
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/trademate
SECRET_KEY=your-random-secret-key-here
```

> **Note:** `OPENAI_API_KEY` and the Neo4j credentials (`NEO4J_URI`,
> `NEO4J_USERNAME`, `NEO4J_PASSWORD`) are read automatically from
> `knowledge_graph/.env` — you do **not** need to duplicate them here.

### 3. Verify `knowledge_graph/.env` exists

The chat agent reads Neo4j and OpenAI credentials from this file:

```
knowledge_graph/
└── .env          ← must contain NEO4J_URI, NEO4J_USERNAME,
                     NEO4J_PASSWORD, OPENAI_API_KEY
```

---

## Running the Server

Run from inside the `server/` directory:

```bash
cd trademate/server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server starts at `http://localhost:8000`.

Interactive API docs (Swagger UI): `http://localhost:8000/docs`

On first startup the server will:
- Create all database tables automatically.
- Create the Neo4j vector index (`hscode_embedding_index`) if it does not exist.

---

## API Endpoints

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/register` | No | Create a new user account |
| POST | `/v1/login` | No | Authenticate and receive a JWT |
| POST | `/v1/onboarding` | JWT | Complete the user profile |

### Chat

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/chat` | JWT | Stream an AI response via SSE |

#### `POST /v1/chat` — Request body

```json
{
  "message": "What is the customs duty on importing laptops to Pakistan?",
  "conversation_id": "optional-uuid-string",
  "history": [
    { "role": "user",      "content": "Hello" },
    { "role": "assistant", "content": "Hi! How can I help?" }
  ]
}
```

#### `POST /v1/chat` — SSE response stream

```
data: {"type": "token",  "content": "The ",         "conversation_id": "..."}
data: {"type": "token",  "content": "customs ",      "conversation_id": "..."}
data: {"type": "token",  "content": "duty ...",      "conversation_id": "..."}
data: {"type": "done",                                "conversation_id": "..."}
```

On error:
```
data: {"type": "error", "detail": "error message",   "conversation_id": "..."}
```

---

## Running Tests

All tests live in `server/tests/`.  Run from the `server/` directory:

```bash
cd trademate/server

# Run all tests
python -m pytest tests/ -v

# Run only the graph retrieval tests
python -m pytest tests/test_graph_retrieval.py -v

# Run a single test with printed output
python -m pytest tests/test_graph_retrieval.py::test_neo4j_connection -v -s
```

### Test suite — `test_graph_retrieval.py`

These tests verify that the AI responses are grounded in real knowledge-graph
data and that the LLM is not hallucinating duty rates.

| Test | What it verifies |
|------|-----------------|
| `test_neo4j_connection` | Neo4j Aura instance is reachable |
| `test_vector_index_exists` | `hscode_embedding_index` is ONLINE and populated |
| `test_retrieval_returns_results` | Vector search returns results for 5 known product queries |
| `test_context_contains_hs_codes` | Returned context contains real 12-digit HS codes |
| `test_context_contains_tariff_data` | Tariff nodes (CD, RD, ST …) are linked and appear in context |
| `test_llm_response_cites_graph_hs_code` | LLM reply cites an HS code that was in the retrieved context |
| `test_llm_refuses_to_hallucinate_on_empty_context` | LLM says "not found" for nonsense queries instead of inventing rates |

### Common test failures and fixes

| Failure message | Cause | Fix |
|-----------------|-------|-----|
| `Neo4j connection failed` | Wrong credentials or Aura instance is paused | Check `knowledge_graph/.env`, wake up the Aura instance |
| `Index 'hscode_embedding_index' not found` | Knowledge graph not ingested | Run `python knowledge_graph/ingest.py` |
| `No Tariff nodes exist` | Tariff ingestion step was skipped | Re-run `ingest.py` — all steps run by default |
| `LLM response contains NO HS code from context` | LLM ignoring context | Check system prompt in `agent/prompts.py` |
| `LLM did NOT refuse on nonsense query` | Prompt too permissive | Tighten rule #5 in `agent/prompts.py` |

---

## Architecture — Chat Pipeline

```
POST /v1/chat
      │
      ▼  JWT validated → user_id extracted
      │
      ▼  LangGraph  graph.astream(stream_mode="messages")
      │
      ├─ retrieve node
      │    └─ embed user message (OpenAI text-embedding-3-small)
      │    └─ vector search Neo4j (top-5 HS codes)
      │    └─ expand with Tariff, Cess, Exemption, Procedure nodes
      │    └─ write formatted text → state["context"]
      │
      └─ generate node
           └─ system prompt + context + conversation history
           └─ ChatOpenAI gpt-4o-mini (streaming=True)
           └─ tokens streamed back as SSE events
```

The LLM is instructed to **only** cite duty rates that appear verbatim in
the retrieved context.  If retrieval returns nothing it must say so rather
than guessing — this is enforced by the system prompt in `agent/prompts.py`
and verified by `test_llm_refuses_to_hallucinate_on_empty_context`.
