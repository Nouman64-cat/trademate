"""
agent/bot.py — Tool-Based ReAct Agent for TradeMate.

Routing Architecture
────────────────────
The LLM reads each tool's docstring and decides at inference time which schema
to query. The routing decision is based purely on *intent*, not brittle keyword
matching:

  "Import duty on mobile phones in Pakistan?"
      → search_pakistan_hs_data("mobile phones import duty")
        Cypher traverses  (:HSCode:PK)─[:HAS_TARIFF]→(:Tariff:PK)
                          (:HSCode:PK)─[:HAS_CESS]→(:Cess:PK)
                          (:HSCode:PK)─[:HAS_EXEMPTION]→(:Exemption:PK)
                          (:HSCode:PK)─[:REQUIRES_PROCEDURE]→(:Procedure:PK)
                          (:HSCode:PK)─[:HAS_MEASURE]→(:Measure:PK)

  "What is the US tariff on live horses (HTS 0101.21.00)?"
      → search_us_hs_data("live horses HTS 0101.21.00")
        Cypher finds (:HSCode:US {hts_code: '0101.21.00'}) directly,
        then surfaces its parent and children for hierarchical context.

  "Compare Pakistan vs US duties on cotton yarn."
      → search_pakistan_hs_data("cotton yarn tariff")   [sequential]
      → search_us_hs_data("cotton yarn US HTS tariff")  [sequential]
      → LLM synthesises both results into one answer.

The agent loop (LangGraph prebuilt ReAct):
  __start__ → agent_node ──tool_call?──► tool_node ──► agent_node ──► ...
                         └──no tool calls──► __end__

Security Guarantees
───────────────────
  1. READ_ACCESS on every Neo4j session — the agent cannot write or delete.
  2. Every Cypher query is parameterized ($param). User input never touches
     the query string itself, preventing Cypher injection.
  3. HS / HTS code inputs are validated with strict regexes before the
     code-lookup path executes; invalid patterns fall through to vector search.
"""

from __future__ import annotations

import contextvars
import logging
import os
import re
from pathlib import Path
from typing import Optional

# Mutable list injected per-request so the evaluate_shipping_routes tool can
# pass its full result back to the SSE stream without changing any interfaces.
# chat.py sets this to a fresh list before each agent invocation.
route_widget_ctx: contextvars.ContextVar[list | None] = contextvars.ContextVar(
    "route_widget_ctx", default=None
)

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

# ── env loading ────────────────────────────────────────────────────────────────
# Credentials live in knowledge_graph/.env; server/.env may hold overrides.
_KG_ENV = Path(__file__).parent.parent.parent / "knowledge_graph" / ".env"
load_dotenv(dotenv_path=_KG_ENV, override=False)
load_dotenv(override=False)  # server/.env

logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────────
_INDEX_NAME    = "hscode_embedding_index"
_EMBED_DIMS    = 1536   # text-embedding-3-small (used for Neo4j vector index)

# db.index.vector.queryNodes has no label awareness — it returns the globally
# top-FETCH_K nodes across BOTH :PK and :US.  The WHERE label filter then
# discards the wrong-schema nodes, so we need a large enough pool to guarantee
# that at least TOP_K nodes of the desired label survive the filter.
_VECTOR_FETCH_K = 100   # nodes pulled from the shared index before label filter
_VECTOR_TOP_K   = 5     # nodes returned to the LLM after label filter

# Pakistan 12-digit HS code (zero-padded by ingest_pk.py)
_PK_CODE_RE = re.compile(r"^\d{12}$")

# US HTS code: 4-digit chapter + 1–3 dot-separated 2-digit segments
# Matches: 0101  |  0101.21  |  0101.21.00  |  0101.21.00.10
# Also matches digit-only variants: 01012100  |  0101210010
_US_CODE_RE = re.compile(r"^\d{4}(?:\.\d{2}){1,3}$|^\d{6,10}$")

# ── Cypher query templates ─────────────────────────────────────────────────────
#
# IMPORTANT: every $param is sent via the Neo4j driver's parameter dict.
# User-supplied strings NEVER appear in the query text itself.

# --- Pakistan ----------------------------------------------------------------

_PK_CODE_CYPHER = """
MATCH (hs:HSCode:PK {code: $code})
OPTIONAL MATCH (hs)-[:HAS_TARIFF]->(t:Tariff)
OPTIONAL MATCH (hs)-[:HAS_CESS]->(c:Cess)
OPTIONAL MATCH (hs)-[:HAS_EXEMPTION]->(ex:Exemption)
OPTIONAL MATCH (hs)-[:REQUIRES_PROCEDURE]->(pr:Procedure)
RETURN
    hs.code                                                              AS code,
    hs.description                                                       AS description,
    hs.full_label                                                        AS full_label,
    null                                                                 AS score,
    collect(DISTINCT {type: t.duty_type,   name: t.duty_name, rate: t.rate})  AS tariffs,
    collect(DISTINCT {province: c.province, import_rate: c.import_rate,
                      export_rate: c.export_rate})                       AS cess,
    collect(DISTINCT {description: ex.exemption_desc, rate: ex.rate})   AS exemptions,
    collect(DISTINCT {name: pr.name, category: pr.category})            AS procedures
"""

_PK_VECTOR_CYPHER = f"""
CALL db.index.vector.queryNodes('{_INDEX_NAME}', $fetch_k, $query_vector)
YIELD node AS hs, score
WHERE 'PK' IN labels(hs)
WITH hs, score ORDER BY score DESC LIMIT $top_k
OPTIONAL MATCH (hs)-[:HAS_TARIFF]->(t:Tariff)
OPTIONAL MATCH (hs)-[:HAS_CESS]->(c:Cess)
OPTIONAL MATCH (hs)-[:HAS_EXEMPTION]->(ex:Exemption)
OPTIONAL MATCH (hs)-[:REQUIRES_PROCEDURE]->(pr:Procedure)
RETURN
    hs.code                                                              AS code,
    hs.description                                                       AS description,
    hs.full_label                                                        AS full_label,
    score,
    collect(DISTINCT {{type: t.duty_type,   name: t.duty_name, rate: t.rate}})  AS tariffs,
    collect(DISTINCT {{province: c.province, import_rate: c.import_rate,
                      export_rate: c.export_rate}})                      AS cess,
    collect(DISTINCT {{description: ex.exemption_desc, rate: ex.rate}})  AS exemptions,
    collect(DISTINCT {{name: pr.name, category: pr.category}})           AS procedures
ORDER BY score DESC
"""

# --- United States -----------------------------------------------------------

_US_CODE_CYPHER = """
MATCH (hs:HSCode:US {hts_code: $code})
OPTIONAL MATCH (parent:HSCode:US)-[:HAS_CHILD]->(hs)
OPTIONAL MATCH (hs)-[:HAS_CHILD]->(child:HSCode:US)
RETURN
    hs.hts_code              AS hts_code,
    hs.description           AS description,
    hs.full_path_description AS full_path,
    hs.indent                AS indent,
    hs.general_rate          AS general_rate,
    hs.special_rate          AS special_rate,
    hs.column_2_rate         AS column_2_rate,
    hs.unit                  AS unit,
    null                     AS score,
    parent.hts_code          AS parent_code,
    parent.description       AS parent_description,
    collect({code: child.hts_code, description: child.description,
             general_rate: child.general_rate}) AS children
"""

_US_VECTOR_CYPHER = f"""
CALL db.index.vector.queryNodes('{_INDEX_NAME}', $fetch_k, $query_vector)
YIELD node AS hs, score
WHERE 'US' IN labels(hs)
WITH hs, score ORDER BY score DESC LIMIT $top_k
OPTIONAL MATCH (parent:HSCode:US)-[:HAS_CHILD]->(hs)
RETURN
    hs.hts_code              AS hts_code,
    hs.description           AS description,
    hs.full_path_description AS full_path,
    hs.indent                AS indent,
    hs.general_rate          AS general_rate,
    hs.special_rate          AS special_rate,
    hs.column_2_rate         AS column_2_rate,
    hs.unit                  AS unit,
    score,
    parent.hts_code          AS parent_code,
    parent.description       AS parent_description,
    [] AS children
ORDER BY score DESC
"""

# ── lazy singletons ────────────────────────────────────────────────────────────


def _get_driver():
    """
    Return the shared Neo4j driver.

    READ_ACCESS is enforced per-session inside each retrieval helper so that
    the agent cannot write to or delete from the database.
    _ensure_index() intentionally opens its session without READ_ACCESS because
    CREATE VECTOR INDEX is a schema-write operation.
    """
    # pylint: disable=global-statement
    global _driver  # noqa: PLW0603
    if _driver is None:
        from neo4j import GraphDatabase

        uri      = os.getenv("NEO4J_URI")
        user     = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([uri, user, password]):
            raise EnvironmentError(
                "NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must all be set in .env"
            )

        _driver = GraphDatabase.driver(uri, auth=(user, password))
        _driver.verify_connectivity()
        logger.info("Neo4j driver initialised → %s", uri)

    return _driver


def _get_embeddings() -> OpenAIEmbeddings:
    """Return the shared text-embedding-3-small model (1536 dims)."""
    global _embeddings  # noqa: PLW0603
    if _embeddings is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY must be set in .env")
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
        )
        logger.info("Embeddings model initialised (text-embedding-3-small, 1536 dims)")
    return _embeddings


_driver     = None
_embeddings: Optional[OpenAIEmbeddings] = None
_pinecone_index = None

_PINECONE_INDEX_NAME = "trademate-documents"


def _get_pinecone_index():
    """Return the shared Pinecone index singleton."""
    global _pinecone_index  # noqa: PLW0603
    if _pinecone_index is None:
        from pinecone import Pinecone

        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise EnvironmentError("PINECONE_API_KEY must be set in .env")

        pc = Pinecone(api_key=api_key)
        _pinecone_index = pc.Index(_PINECONE_INDEX_NAME)
        logger.info("Pinecone index '%s' connected.", _PINECONE_INDEX_NAME)
    return _pinecone_index


# ── index setup ───────────────────────────────────────────────────────────────


def _ensure_index() -> None:
    """
    Idempotently create the shared vector index on HSCode.embedding.
    Covers both :PK and :US nodes — the WHERE label filter in each query
    restricts which schema is actually searched.
    Safe to call multiple times (IF NOT EXISTS).
    """
    try:
        driver = _get_driver()
        with driver.session() as session:
            session.run(
                f"""
                CREATE VECTOR INDEX {_INDEX_NAME} IF NOT EXISTS
                FOR (h:HSCode) ON (h.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {_EMBED_DIMS},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
            )
        logger.info("Vector index '%s' verified / created.", _INDEX_NAME)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not verify vector index: %s", exc)


# ── formatters ────────────────────────────────────────────────────────────────


def _format_pk_results(records: list[dict]) -> str:
    """Convert raw PK Cypher result rows into a readable text block."""
    if not records:
        return "No Pakistan HS code data found for this query."

    blocks: list[str] = []
    for r in records:
        lines: list[str] = [
            "─" * 50,
            f"[Pakistan PCT]  HS Code : {r.get('code', 'N/A')}",
            f"Description              : {r.get('description', '')}",
        ]
        if r.get("full_label"):
            lines.append(f"Full Hierarchy           : {r['full_label']}")
        if r.get("score") is not None:
            lines.append(f"Vector Similarity        : {r['score']:.4f}")

        tariffs = [t for t in (r.get("tariffs") or []) if t.get("type")]
        if tariffs:
            lines.append("Tariffs:")
            for t in tariffs:
                lines.append(
                    f"  • {t.get('name', '')} ({t.get('type', '')}): "
                    f"{t.get('rate', 'N/A')}"
                )

        cess = [c for c in (r.get("cess") or []) if c.get("province")]
        if cess:
            lines.append(f"Cess (first {min(5, len(cess))} provinces):")
            for c in cess[:5]:
                lines.append(
                    f"  • {c['province']} — "
                    f"Import: {c.get('import_rate', 'N/A')}, "
                    f"Export: {c.get('export_rate', 'N/A')}"
                )

        exemptions = [e for e in (r.get("exemptions") or []) if e.get("description")]
        if exemptions:
            lines.append("Exemptions / Concessions:")
            for e in exemptions[:3]:
                rate_str = f" ({e['rate']})" if e.get("rate") else ""
                lines.append(f"  • {e['description']}{rate_str}")

        procedures = [p for p in (r.get("procedures") or []) if p.get("name")]
        if procedures:
            lines.append("Required Trade Procedures:")
            for p in procedures[:3]:
                cat = f" [{p['category']}]" if p.get("category") else ""
                lines.append(f"  • {p['name']}{cat}")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def _format_us_results(records: list[dict]) -> str:
    """Convert raw US Cypher result rows into a readable text block."""
    if not records:
        return "No US HTS data found for this query."

    blocks: list[str] = []
    for r in records:
        lines: list[str] = [
            "─" * 50,
            f"[US HTS]  HTS Code        : {r.get('hts_code', 'N/A')}",
            f"Description               : {r.get('description', '')}",
        ]
        if r.get("full_path"):
            lines.append(f"Full Path                 : {r['full_path']}")
        if r.get("score") is not None:
            lines.append(f"Vector Similarity         : {r['score']:.4f}")
        if r.get("indent") is not None:
            lines.append(f"Hierarchy Level (indent)  : {r['indent']}")
        if r.get("parent_code"):
            lines.append(
                f"Parent HTS Code           : {r['parent_code']} — "
                f"{r.get('parent_description', '')}"
            )
        if r.get("unit"):
            lines.append(f"Unit of Quantity          : {r['unit']}")
        if r.get("general_rate"):
            lines.append(f"General Rate of Duty      : {r['general_rate']}")
        if r.get("special_rate"):
            lines.append(f"Special Rate of Duty      : {r['special_rate']}")
        if r.get("column_2_rate"):
            lines.append(f"Column 2 Rate of Duty     : {r['column_2_rate']}")

        children = [c for c in (r.get("children") or []) if c.get("code")]
        if children:
            lines.append(f"Sub-Headings ({len(children)} shown, first 5):")
            for c in children[:5]:
                rate_str = (
                    f" | General: {c['general_rate']}" if c.get("general_rate") else ""
                )
                lines.append(f"  • {c.get('code', '')} — {c.get('description', '')}{rate_str}")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


# ── core retrieval helpers ────────────────────────────────────────────────────
# These are plain functions — they are not exposed as tools themselves.
# The @tool wrappers below call them and add error handling.


def _read_session():
    """
    Open a read-only Neo4j session.

    READ_ACCESS is the correct place to enforce read-only behaviour in the
    neo4j Python driver — it is a *session* configuration key, not a driver
    constructor key.
    """
    from neo4j import READ_ACCESS
    return _get_driver().session(default_access_mode=READ_ACCESS)


def _pk_code_lookup(code: str) -> list[dict]:
    """Exact match on hs.code for the PK schema. Returns raw Cypher result."""
    with _read_session() as session:
        return session.run(_PK_CODE_CYPHER, code=code).data()


def _pk_vector_search(query: str, top_k: int = _VECTOR_TOP_K) -> list[dict]:
    """Vector similarity search restricted to :PK labelled nodes.

    Fetches _VECTOR_FETCH_K nodes from the shared index (wide net), then the
    WHERE 'PK' IN labels(hs) filter + LIMIT $top_k trims to the best PK hits.
    """
    vector = _get_embeddings().embed_query(query)
    with _read_session() as session:
        return session.run(
            _PK_VECTOR_CYPHER,
            fetch_k=_VECTOR_FETCH_K,
            top_k=top_k,
            query_vector=vector,
        ).data()


def _us_code_lookup(code: str) -> list[dict]:
    """Exact match on hs.hts_code for the US schema. Returns raw Cypher result."""
    with _read_session() as session:
        return session.run(_US_CODE_CYPHER, code=code).data()


def _us_vector_search(query: str, top_k: int = _VECTOR_TOP_K) -> list[dict]:
    """Vector similarity search restricted to :US labelled nodes.

    Same wide-net strategy as _pk_vector_search.
    """
    vector = _get_embeddings().embed_query(query)
    with _read_session() as session:
        return session.run(
            _US_VECTOR_CYPHER,
            fetch_k=_VECTOR_FETCH_K,
            top_k=top_k,
            query_vector=vector,
        ).data()


# ── tool input schemas ────────────────────────────────────────────────────────


class _PKSearchInput(BaseModel):
    query: str = Field(
        description=(
            "The user's question or product description to look up in Pakistan's "
            "PCT database. Can be a product name (e.g. 'mobile phones'), a "
            "12-digit Pakistan HS code (e.g. '851712000000'), or a natural-language "
            "description. Do not include words like 'US' or 'American' here."
        )
    )


class _USSearchInput(BaseModel):
    query: str = Field(
        description=(
            "The user's question or product description to look up in the US HTS "
            "database. Can be a product name (e.g. 'live horses'), a US HTS code "
            "(e.g. '0101.21.00'), or a natural-language description. "
            "Do not include words like 'Pakistan' or 'PCT' here."
        )
    )


# ── LangChain tool definitions ────────────────────────────────────────────────


@tool("search_pakistan_hs_data", args_schema=_PKSearchInput)
def search_pakistan_hs_data(query: str) -> str:
    """
    Search Pakistan's PCT (Pakistan Customs Tariff) HS code database.

    Use this tool EXCLUSIVELY when the user asks about:
    - Import or export tariffs / duties for Pakistan
    - Pakistan Customs Tariff rates: CD (Customs Duty), RD (Regulatory Duty),
      ACD (Additional Customs Duty), FED (Federal Excise Duty), ST (Sales Tax),
      IT (Income Tax), DS (Development Surcharge), EOC, ERD
    - Provincial cess collection rates (Sindh, Punjab, KPK, Balochistan, …)
    - Trade exemptions or concessions under Pakistan's tariff schedule (SROs)
    - Trade procedures required by Pakistan Customs (Form-I, licensing, …)
    - NTMs / trade measures applied at the Pakistan border
    - Any product classified under Pakistan's PCT system

    DO NOT use this tool for questions about US HTS codes or US tariff rates.

    Routing logic (internal):
      • If `query` is a 12-digit number → exact HS code lookup (no embedding call)
      • Otherwise → vector similarity search on the :PK index partition
    """
    query = query.strip()
    try:
        if _PK_CODE_RE.match(query):
            logger.info("━━━ [NEO4J → PK] Exact code lookup: '%s'", query)
            records = _pk_code_lookup(query)
            if not records:
                logger.info("━━━ [NEO4J → PK] Code not found — falling back to vector search.")
                records = _pk_vector_search(query)
                logger.info("━━━ [NEO4J → PK] Vector search complete.")
        else:
            logger.info("━━━ [NEO4J → PK] Vector search: %r", query[:80])
            records = _pk_vector_search(query)

        if records:
            logger.info("━━━ [NEO4J → PK ✔] Returned %d record(s) from Graph DB (Pakistan PCT).", len(records))
        else:
            logger.warning("━━━ [NEO4J → PK ✘] No results found in Pakistan PCT data.")

        return _format_pk_results(records)

    except Exception as exc:  # noqa: BLE001
        logger.warning("━━━ [NEO4J → PK ✘] search_pakistan_hs_data failed: %s", exc)
        return (
            f"Pakistan HS data retrieval failed: {exc}. "
            "Please ensure Neo4j is running (docker start neo4j-trademate) "
            "and NEO4J_URI / credentials are correct in knowledge_graph/.env."
        )


@tool("search_us_hs_data", args_schema=_USSearchInput)
def search_us_hs_data(query: str) -> str:
    """
    Search the US Harmonized Tariff Schedule (HTS) database.

    Use this tool EXCLUSIVELY when the user asks about:
    - US import tariff rates (General, Special / GSP, Column 2)
    - US HTS codes (Harmonized Tariff Schedule of the United States)
    - US trade classifications for any product
    - US duty rates on specific goods imported into the United States
    - Hierarchical breakdown of US HTS chapters, headings, or subheadings
    - Unit of quantity for US customs declarations

    DO NOT use this tool for Pakistan PCT, cess, SRO, or provincial duty questions.

    Routing logic (internal):
      • If `query` looks like a US HTS code (e.g. '0101.21.00' or '01012100')
        → exact hts_code lookup; returns the node, its parent, and its children
      • Otherwise → vector similarity search on the :US index partition
        using the full_path_description embedding for each node
    """
    query = query.strip()
    try:
        if _US_CODE_RE.match(query):
            logger.info("━━━ [NEO4J → US] Exact code lookup: '%s'", query)
            records = _us_code_lookup(query)
            if not records:
                logger.info("━━━ [NEO4J → US] Code not found — falling back to vector search.")
                records = _us_vector_search(query)
                logger.info("━━━ [NEO4J → US] Vector search complete.")
        else:
            logger.info("━━━ [NEO4J → US] Vector search: %r", query[:80])
            records = _us_vector_search(query)

        if records:
            logger.info("━━━ [NEO4J → US ✔] Returned %d record(s) from Graph DB (US HTS).", len(records))
        else:
            logger.warning("━━━ [NEO4J → US ✘] No results found in US HTS data.")

        return _format_us_results(records)

    except Exception as exc:  # noqa: BLE001
        logger.warning("━━━ [NEO4J → US ✘] search_us_hs_data failed: %s", exc)
        return (
            f"US HTS data retrieval failed: {exc}. "
            "Please ensure Neo4j is running (docker start neo4j-trademate) "
            "and NEO4J_URI / credentials are correct in knowledge_graph/.env."
        )


class _DocSearchInput(BaseModel):
    query: str = Field(
        description=(
            "The user's question to search in uploaded trade policy documents, "
            "regulations, reports, and reference materials stored in Pinecone. "
            "Use natural-language descriptions. Examples: 'SRO exemptions for textile', "
            "'Pakistan trade policy 2024', 'WTO safeguard measures'."
        )
    )


@tool("search_trade_documents", args_schema=_DocSearchInput)
def search_trade_documents(query: str) -> str:
    """
    Search uploaded trade policy documents, regulations, and reports stored in
    Pinecone (Vector DB).

    Use this tool when the user asks about:
    - Trade policies, agreements, or regulations (e.g. SROs, FTAs, WTO rules)
    - Uploaded reference documents or reports
    - General trade procedures, compliance requirements, or policy context
    - Any question where background document context would help

    This tool complements the Neo4j tools — it searches unstructured document
    chunks rather than structured HS code / tariff data.

    DO NOT use this as a substitute for search_pakistan_hs_data or
    search_us_hs_data when the user wants specific duty rates or HS codes.
    """
    query = query.strip()
    try:
        logger.info("━━━ [PINECONE] Vector search: %r", query[:80])

        embedding_model = _get_embeddings()
        query_vector = embedding_model.embed_query(query)

        index = _get_pinecone_index()
        results = index.query(
            vector=query_vector,
            top_k=5,
            include_metadata=True,
        )

        matches = results.get("matches", [])
        if not matches:
            logger.warning("━━━ [PINECONE ✘] No results found in document store.")
            return "No relevant documents found in the document store for this query."

        blocks: list[str] = []
        for i, match in enumerate(matches, 1):
            meta  = match.get("metadata", {})
            score = match.get("score", 0)
            text  = meta.get("text", "").strip()
            source = meta.get("source", "unknown")
            page   = meta.get("page", "")

            if not text:
                continue

            header = f"[Document {i}] {source}"
            if page != "":
                header += f" (page {page})"
            header += f" — relevance: {score:.4f}"
            blocks.append(f"{header}\n{text}")

        if not blocks:
            logger.warning("━━━ [PINECONE ✘] Matches returned but all had empty text.")
            return "No usable document content found."

        logger.info("━━━ [PINECONE ✔] Returned %d document chunk(s) from Vector DB.", len(blocks))
        return "\n\n---\n\n".join(blocks)

    except Exception as exc:  # noqa: BLE001
        logger.warning("━━━ [PINECONE ✘] search_trade_documents failed: %s", exc)
        return (
            f"Document search failed: {exc}. "
            "Please ensure PINECONE_API_KEY is set and the index exists."
        )


# ── Route evaluation tool ────────────────────────────────────────────────────


class _RouteEvalInput(BaseModel):
    origin_city: str = Field(
        description="Origin city in Pakistan (e.g. Karachi, Lahore, Faisalabad, Sialkot, Islamabad, Multan, Peshawar)"
    )
    destination_city: str = Field(
        description="Destination city in the USA (e.g. Los Angeles, New York, Chicago, Miami, Savannah, Seattle). MUST be spelled correctly."
    )
    cargo_type: str = Field(
        description="Cargo type: FCL_20, FCL_40, FCL_40HC, LCL, or AIR"
    )
    cargo_value_usd: float = Field(
        description="Total declared cargo value in USD"
    )
    hs_code: Optional[str] = Field(
        default=None,
        description="HS code (first 2–6 digits) for import duty calculation, if known"
    )
    cargo_volume_cbm: Optional[float] = Field(
        default=None,
        description="Cargo volume in CBM — required for LCL shipments"
    )
    cargo_weight_kg: Optional[float] = Field(
        default=None,
        description="Cargo weight in kg — required for AIR shipments"
    )
    cost_weight: float = Field(
        default=0.5,
        description="Optimization preference: 0 = fastest, 1 = cheapest, 0.5 = balanced"
    )


@tool("evaluate_shipping_routes", args_schema=_RouteEvalInput)
def evaluate_shipping_routes(
    origin_city: str,
    destination_city: str,
    cargo_type: str,
    cargo_value_usd: float,
    hs_code: Optional[str] = None,
    cargo_volume_cbm: Optional[float] = None,
    cargo_weight_kg: Optional[float] = None,
    cost_weight: float = 0.5,
) -> str:
    """
    Evaluate all viable shipping routes from a Pakistan city to a USA city.

    Use this tool when the user asks about:
    - Shipping routes from Pakistan to the USA
    - Freight costs, ocean freight rates, air freight rates
    - Transit times for Pakistan → USA shipments
    - Comparing shipping options (FCL, LCL, Air)
    - Import duties, logistics costs, or total landed cost estimates

    Returns a summary of available routes with costs, transit times, and
    carrier options. An interactive route widget will be shown to the user.

    DO NOT use this tool for HS code lookups, tariff rates, or trade policy questions —
    use the Neo4j tools for those.
    """
    try:
        from schemas.routes import RouteEvaluationRequest
        from services.route_engine import evaluate_routes

        req = RouteEvaluationRequest(
            origin_city=origin_city,
            destination_city=destination_city,
            cargo_type=cargo_type,
            cargo_value_usd=cargo_value_usd,
            hs_code=hs_code or None,
            cargo_volume_cbm=cargo_volume_cbm,
            cargo_weight_kg=cargo_weight_kg,
            cost_weight=cost_weight,
        )
        result = evaluate_routes(req)

        # Push full result into the per-request widget store so chat.py can
        # emit a widget SSE event after the text stream completes.
        store = route_widget_ctx.get(None)
        if store is not None:
            store.append(result.model_dump())

        # Return a concise human-readable summary for the LLM to use.
        def _fmt(n: float) -> str:
            return f"${n:,.0f}"

        lines = [
            f"{len(result.routes)} routes found: {result.origin_city} → {result.destination_city}",
            f"Cargo type: {result.cargo_type} | Value: {_fmt(result.cargo_value_usd)} | Duty rate: {result.duty_rate_pct}%",
            "",
        ]
        for route in result.routes:
            tag = f" [{route.tag.upper()}]" if route.tag else ""
            source = " (Live Freightos Rate)" if route.rate_source == "live" else ""
            lines.append(
                f"• {route.name}{tag} — "
                f"Cost{source}: {_fmt(route.cost.total_min)}–{_fmt(route.cost.total_max)} | "
                f"Transit: {route.transit.total_min}–{route.transit.total_max} days | "
                f"Reliability: {round(route.reliability_score * 100)}%"
            )
        lines += [
            "",
            f"Recommended: Cheapest={result.recommended['cheapest']}  "
            f"Fastest={result.recommended['fastest']}  "
            f"Balanced={result.recommended['balanced']}",
        ]
        logger.info("━━━ [ROUTE TOOL] Evaluated %d routes for %s→%s", len(result.routes), origin_city, destination_city)
        return "\n".join(lines)

    except Exception as exc:  # noqa: BLE001
        logger.warning("━━━ [ROUTE TOOL] Failed: %s", exc)
        return f"Route evaluation failed: {exc}"


# ── agent system prompt ───────────────────────────────────────────────────────

_BOT_SYSTEM_PROMPT = SystemMessage(content="""\
You are TradeMate, an expert AI assistant specialising in international trade,
Harmonized System (HS) codes, import/export regulations, and tariff schedules.

You have access to four tools:

  1. search_pakistan_hs_data  [Neo4j — Graph DB]
     → Pakistan PCT (Pakistan Customs Tariff) database (:PK schema)
     → Star schema: HS codes connected to Tariff, Cess, Exemption,
       Procedure, and Measure nodes
     → Use for: CD/RD/ACD/FED/ST rates, provincial cess, SRO exemptions,
       customs procedures, NTMs

  2. search_us_hs_data  [Neo4j — Graph DB]
     → US Harmonized Tariff Schedule database (:US schema)
     → 11-level implicit hierarchy via HAS_CHILD relationships
     → Rates stored as properties: general_rate, special_rate, column_2_rate
     → Use for: US import duties, HTS classifications, US trade data

  3. search_trade_documents  [Pinecone — Vector DB]
     → Uploaded trade policy documents, regulations, and reports
     → Use for: policy context, trade agreements, SRO documents,
       compliance guidelines, any question needing document-level context
     → Call this alongside the Neo4j tools for richer answers

  4. evaluate_shipping_routes  [Route Engine]
     → Evaluates all viable Pakistan → USA shipping routes
     → Returns cost breakdown, transit times, carrier options, live freight rates
     → Use for: shipping route questions, freight cost estimates, logistics planning
     → When this tool is called, an interactive route widget is shown to the user

Rules you MUST follow
──────────────────────
• ALWAYS call at least one tool for EVERY user question — no exceptions.
  Never answer any trade question from training knowledge alone.
• For ANY question about products, commodities, or goods:
    - Call search_pakistan_hs_data to find PK tariff/HS data
    - Call search_us_hs_data to find US HTS data
    - Call search_trade_documents to find relevant policy documents
• For tariff/duty/rate questions: call search_pakistan_hs_data and/or
  search_us_hs_data depending on the country mentioned.
• For policy, regulation, SRO, or document questions: call search_trade_documents.
• For general "what is X" or "tell me about X" trade questions: call
  search_trade_documents AND the relevant Neo4j tools.
• For cross-country comparisons: call BOTH Neo4j tools.
• For shipping route, freight cost, logistics, or transit time questions:
  call evaluate_shipping_routes. An interactive widget will be rendered for the user.
• ONLY cite HS codes and duty rates that appear verbatim in tool results.
  Never invent, estimate, interpolate, or recall rates from training data.
• If all tools return no data, say so clearly and suggest a more specific query.
• Label every rate you quote with its source country and duty type.
• Use bullet points or tables when listing multiple rates — clarity matters.

When evaluate_shipping_routes is called
────────────────────────────────────────
• Give a brief conversational summary (2–4 sentences): mention the recommended
  route, cheapest cost range, and fastest transit time.
• Do NOT repeat every route's numbers — the user sees an interactive widget.
• End with one sentence like: "The full breakdown with all routes is shown in the
  widget below."

RESPONSE FILTERING — THIS IS THE MOST IMPORTANT RULE
══════════════════════════════════════════════════════
Tool results contain many fields. You MUST act as a strict filter.
Output ONLY the fields the user explicitly asked for. Omit everything else.
Treat this as an absolute rule — there are no exceptions.

Identify what the user asked for, then apply exactly one of the rules below:

  ► User asks for "HS code" / "classification" / "code" only
      OUTPUT  : HS code + description only. ALWAYS label each code with its country.
      FORMAT  : Group results under two clear headings:
                  "Pakistan HS Codes (PCT)" — for codes from search_pakistan_hs_data
                  "US HTS Codes"            — for codes from search_us_hs_data
                If only one country returned data, still use that country's heading.
                NEVER mix codes from different countries in the same list without headings.
      OMIT    : tariffs, cess, exemptions, procedures, measures, rates — everything else.

  ► User asks for "tariff" / "duty" / "rate" / "tax" only
      OUTPUT  : duty rates only (CD, RD, ACD, FED, ST, IT, etc.).
      OMIT    : cess, exemptions, procedures, measures, HS code description detail.

  ► User asks for "cess" only
      OUTPUT  : cess rates by province only.
      OMIT    : tariffs, exemptions, procedures, measures, HS code description detail.

  ► User asks for "exemption" / "concession" / "SRO" only
      OUTPUT  : exemptions list only.
      OMIT    : tariffs, cess, procedures, measures, HS code description detail.

  ► User asks for "procedure" / "procedures" only
      OUTPUT  : required trade procedures only.
      OMIT    : tariffs, cess, exemptions, measures, HS code description detail.

  ► User asks for "measure" / "measures" / "NTM" only
      OUTPUT  : trade measures only.
      OMIT    : tariffs, cess, exemptions, procedures, HS code description detail.

  ► User asks for "procedures and measures" / "measures and procedures"
      OUTPUT  : procedures + measures only.
      OMIT    : tariffs, cess, exemptions, HS code description detail — everything else.

  ► User asks for "full details" / "everything" / "complete breakdown"
      OUTPUT  : all fields.

  ► User asks for two or more specific fields (e.g. "HS code and tariff")
      OUTPUT  : only those exact fields.
      OMIT    : all other fields not mentioned.

Critical prohibitions — NEVER do these:
  ✗ NEVER volunteer tariff rates when the user only asked for procedures/measures.
  ✗ NEVER volunteer cess when the user did not ask for cess.
  ✗ NEVER volunteer exemptions when the user did not ask for exemptions.
  ✗ NEVER add a "Summary" section at the end.
  ✗ NEVER add closing phrases like "If you need further details, feel free to ask!"
  ✗ NEVER repeat information already stated.
  ✗ Be concise. A short accurate answer is always better than a long one.
""")

# ── LLM singleton ─────────────────────────────────────────────────────────────


def _get_llm() -> ChatOpenAI:
    global _llm  # noqa: PLW0603
    if _llm is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY must be set in .env")
        _llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=api_key,
            temperature=0.1,   # low temperature for factual tariff data
            streaming=True,
        )
        logger.info("LLM singleton initialised (gpt-4o-mini, streaming=True)")
    return _llm


_llm: Optional[ChatOpenAI] = None

# ── Tool registry ─────────────────────────────────────────────────────────────
# Add new tools here — the router will automatically learn to select them.

_ALL_TOOLS = [search_pakistan_hs_data, search_us_hs_data, search_trade_documents, evaluate_shipping_routes]
_TOOL_MAP  = {t.name: t for t in _ALL_TOOLS}

# ── Router ────────────────────────────────────────────────────────────────────

_ROUTER_PROMPT = """\
You are a query router for TradeMate. Return ONLY a JSON array of tool names. No explanation.

Tools:
  search_pakistan_hs_data  — Pakistan PCT: HS codes, tariffs, cess, exemptions, procedures, measures
  search_us_hs_data        — US HTS: HS codes, duty rates, US trade classifications
  search_trade_documents   — Trade policy documents, agreements, SROs, regulations
  evaluate_shipping_routes — Shipping routes & freight costs from Pakistan to USA

Follow this exact decision tree in order:

STEP 1 — Shipping
  If the query is about shipping routes, freight costs, transit times, or logistics:
    → always include "evaluate_shipping_routes"

STEP 2 — HS Codes / Tariffs / Duties / Classifications / Products
  These queries need Neo4j tools. Apply ONE of these sub-rules:

  A. User says "Pakistan only" OR uses words like "Pakistani customs", "PCT", "in Pakistan":
       AND does NOT mention US/America/United States
       → include ONLY "search_pakistan_hs_data"

  B. User says "US only" OR uses words like "HTS", "in the US", "American tariff", "United States":
       AND does NOT mention Pakistan
       → include ONLY "search_us_hs_data"

  C. Everything else — no country mentioned, OR both countries mentioned, OR generic product query:
       → include BOTH "search_pakistan_hs_data" AND "search_us_hs_data"
       This is the DEFAULT for any product/commodity/HS-code query without a clear single country.

  Note: "HS code" and "HTS code" are the same thing in user language. Treat both as triggering rule C
  unless the user clearly specifies a single country.

STEP 3 — Pakistan-specific fields (procedures, measures, cess, exemptions, SROs)
  If the query asks ONLY about procedures, measures, cess, exemptions, or NTMs
  AND does not ask for HS codes or tariff rates:
    → include ONLY "search_pakistan_hs_data"
  (These fields exist only in the Pakistan database.)

STEP 4 — Policy / Documents
  If the query is about trade policy, agreements, regulations, SRO documents, or general trade context:
    → include "search_trade_documents"
  Also include for general "what is X" questions alongside the Neo4j tools.

Examples (follow these exactly):
  "give me the hs codes for fruits"                       → ["search_pakistan_hs_data", "search_us_hs_data"]
  "hs code for mangoes"                                   → ["search_pakistan_hs_data", "search_us_hs_data"]
  "hs codes for textiles"                                 → ["search_pakistan_hs_data", "search_us_hs_data"]
  "tariffs for rice"                                      → ["search_pakistan_hs_data", "search_us_hs_data"]
  "duty on electronics"                                   → ["search_pakistan_hs_data", "search_us_hs_data"]
  "classification for steel"                              → ["search_pakistan_hs_data", "search_us_hs_data"]
  "what is the hs code for smartphones in pakistan"       → ["search_pakistan_hs_data"]
  "pakistan customs duty on cars"                         → ["search_pakistan_hs_data"]
  "US tariff on cotton"                                   → ["search_us_hs_data"]
  "HTS code for live horses"                              → ["search_us_hs_data"]
  "compare pakistan and us duties on steel"               → ["search_pakistan_hs_data", "search_us_hs_data"]
  "procedures and measures for mangoes"                   → ["search_pakistan_hs_data"]
  "exemptions for textile imports in pakistan"            → ["search_pakistan_hs_data"]
  "what is an SRO exemption"                              → ["search_trade_documents"]
  "show me shipping routes from karachi to new york"      → ["evaluate_shipping_routes"]
  "cheapest way to ship textiles from pakistan to usa"    → ["evaluate_shipping_routes", "search_pakistan_hs_data"]
  "what are automotive products"                          → ["search_pakistan_hs_data", "search_us_hs_data", "search_trade_documents"]

Respond with ONLY the JSON array. No explanation, no markdown.
"""


def _get_router_llm() -> ChatOpenAI:
    """Lightweight LLM for routing — no tools bound, low temperature."""
    global _router_llm  # noqa: PLW0603
    if _router_llm is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY must be set in .env")
        _router_llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=api_key,
            temperature=0.0,   # deterministic routing
            streaming=False,   # no streaming needed for routing
        )
        logger.info("Router LLM initialised (gpt-4o-mini, streaming=False)")
    return _router_llm


_router_llm: Optional[ChatOpenAI] = None


def _route_query(query: str) -> list:
    """
    Call the router LLM with the query and return the list of tool objects
    to bind for this request. Falls back to all tools on any error.
    """
    import json

    try:
        router_llm = _get_router_llm()
        response   = router_llm.invoke([
            SystemMessage(content=_ROUTER_PROMPT),
            {"role": "user", "content": query},
        ])
        raw = response.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = "\n".join(
                line for line in raw.splitlines()
                if not line.startswith("```")
            ).strip()

        selected_names: list[str] = json.loads(raw)

        # Validate — keep only names that exist in the registry
        valid   = [n for n in selected_names if n in _TOOL_MAP]
        invalid = [n for n in selected_names if n not in _TOOL_MAP]

        if invalid:
            logger.warning("━━━ [ROUTER] Unknown tool name(s) ignored: %s", invalid)

        if not valid:
            logger.warning("━━━ [ROUTER] No valid tools selected — falling back to all tools.")
            return _ALL_TOOLS

        selected_tools = [_TOOL_MAP[n] for n in valid]

        logger.info(
            "━━━ [ROUTER] Query: %r", query[:120]
        )
        logger.info(
            "━━━ [ROUTER] Selected %d/%d tool(s): %s",
            len(selected_tools),
            len(_ALL_TOOLS),
            [t.name for t in selected_tools],
        )
        skipped = [n for n in _TOOL_MAP if n not in valid]
        if skipped:
            logger.info("━━━ [ROUTER] Skipped (not needed): %s", skipped)

        return selected_tools

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "━━━ [ROUTER] Routing failed (%s) — falling back to all tools.", exc
        )
        return _ALL_TOOLS


# ── Agent builder with cache ──────────────────────────────────────────────────

_agent_cache: dict[frozenset, object] = {}


def _build_agent(tools: list):
    """
    Return a compiled ReAct agent for the given tool subset.
    Agents are cached by their tool combination — no redundant recompilation
    when the router selects the same tools across requests.
    """
    cache_key = frozenset(t.name for t in tools)
    if cache_key not in _agent_cache:
        llm = _get_llm()
        _agent_cache[cache_key] = create_react_agent(
            model=llm.bind_tools(tools),
            tools=tools,
            prompt=_BOT_SYSTEM_PROMPT,
        )
        logger.info(
            "━━━ [AGENT CACHE] Compiled new agent for tool combination: %s",
            sorted(cache_key),
        )
    else:
        logger.info(
            "━━━ [AGENT CACHE] Reusing cached agent for: %s",
            sorted(cache_key),
        )
    return _agent_cache[cache_key]


_bot = None


def get_bot():
    """
    Return a callable that routes each query then runs the ReAct agent.

    The returned object exposes .astream() so routes/chat.py needs no changes.

    Graph topology:
        START → router_node → react_agent (with subset of tools) → END
    """
    global _bot  # noqa: PLW0603
    if _bot is None:
        logger.info("Initialising TradeMate ReAct bot with Router …")
        _ensure_index()
        # Pre-warm singletons
        _get_llm()
        _get_router_llm()
        _bot = _RouterAgent()
        logger.info(
            "ReAct bot ready. Tool registry: %s", list(_TOOL_MAP.keys())
        )
    return _bot


class _RouterAgent:
    """
    Wraps the router + dynamic agent into a single object that mimics the
    LangGraph compiled graph interface (astream).

    Flow per request:
      1. Router LLM classifies the query → selects N tools
      2. A ReAct agent is compiled with only those N tools
      3. Agent streams the response
    """

    async def astream(self, state: dict, stream_mode: str = "messages"):
        query = ""
        for msg in reversed(state.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "human":
                query = msg.content if isinstance(msg.content, str) else ""
                break

        # ── Route ──────────────────────────────────────────────────────────
        selected_tools = _route_query(query)

        # ── Build agent with selected tools only ───────────────────────────
        agent = _build_agent(selected_tools)
        logger.info(
            "━━━ [AGENT] Compiled with tools: %s",
            [t.name for t in selected_tools],
        )

        # ── Stream ─────────────────────────────────────────────────────────
        async for chunk, metadata in agent.astream(state, stream_mode=stream_mode):
            yield chunk, metadata
