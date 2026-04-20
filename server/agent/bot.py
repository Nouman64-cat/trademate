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
_EMBED_DIMS    = 1536   # text-embedding-3-small
# Memgraph auto-names vector indexes as "Label_property"
_INDEX_NAME    = "HSCode_embedding"

# vector_search.search has no label awareness — wide net then filter by label
_VECTOR_FETCH_K = 200   # nodes pulled from the index before label filter
_VECTOR_TOP_K   = 15    # nodes returned to the LLM after label filter

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
OPTIONAL MATCH (sh:SubHeading:PK)-[:HAS_HSCODE]->(hs)
OPTIONAL MATCH (hd:Heading:PK)-[:HAS_SUBHEADING]->(sh)
OPTIONAL MATCH (sc:SubChapter:PK)-[:HAS_HEADING]->(hd)
OPTIONAL MATCH (ch:Chapter:PK)-[:HAS_SUBCHAPTER]->(sc)
OPTIONAL MATCH (hs)-[:HAS_TARIFF]->(t:Tariff)
OPTIONAL MATCH (hs)-[:HAS_CESS]->(c:Cess)
OPTIONAL MATCH (hs)-[:HAS_EXEMPTION]->(ex:Exemption)
OPTIONAL MATCH (hs)-[:REQUIRES_PROCEDURE]->(pr:Procedure)
RETURN
    hs.code            AS code,
    hs.description     AS description,
    hs.full_label      AS full_label,
    null               AS score,
    ch.code            AS chapter_code,
    ch.description     AS chapter_desc,
    sc.code            AS subchapter_code,
    sc.description     AS subchapter_desc,
    hd.code            AS heading_code,
    hd.description     AS heading_desc,
    sh.code            AS subheading_code,
    sh.description     AS subheading_desc,
    collect(DISTINCT {type: t.duty_type,   name: t.duty_name, rate: t.rate})  AS tariffs,
    collect(DISTINCT {province: c.province, import_rate: c.import_rate,
                      export_rate: c.export_rate})                             AS cess,
    collect(DISTINCT {description: ex.exemption_desc, rate: ex.rate})         AS exemptions,
    collect(DISTINCT {name: pr.name, category: pr.category})                  AS procedures
"""

_PK_VECTOR_CYPHER = f"""
CALL vector_search.search('{_INDEX_NAME}', $fetch_k, $query_vector)
YIELD node AS hs, similarity AS score
WITH hs, score
WHERE 'PK' IN labels(hs)
WITH hs, score ORDER BY score DESC LIMIT $top_k
OPTIONAL MATCH (sh:SubHeading:PK)-[:HAS_HSCODE]->(hs)
OPTIONAL MATCH (hd:Heading:PK)-[:HAS_SUBHEADING]->(sh)
OPTIONAL MATCH (sc:SubChapter:PK)-[:HAS_HEADING]->(hd)
OPTIONAL MATCH (ch:Chapter:PK)-[:HAS_SUBCHAPTER]->(sc)
OPTIONAL MATCH (hs)-[:HAS_TARIFF]->(t:Tariff)
OPTIONAL MATCH (hs)-[:HAS_CESS]->(c:Cess)
OPTIONAL MATCH (hs)-[:HAS_EXEMPTION]->(ex:Exemption)
OPTIONAL MATCH (hs)-[:REQUIRES_PROCEDURE]->(pr:Procedure)
RETURN
    hs.code                                                              AS code,
    hs.description                                                       AS description,
    hs.full_label                                                        AS full_label,
    score,
    ch.code            AS chapter_code,
    ch.description     AS chapter_desc,
    sc.code            AS subchapter_code,
    sc.description     AS subchapter_desc,
    hd.code            AS heading_code,
    hd.description     AS heading_desc,
    sh.code            AS subheading_code,
    sh.description     AS subheading_desc,
    collect(DISTINCT {{type: t.duty_type,   name: t.duty_name, rate: t.rate}})  AS tariffs,
    collect(DISTINCT {{province: c.province, import_rate: c.import_rate,
                      export_rate: c.export_rate}})                      AS cess,
    collect(DISTINCT {{description: ex.exemption_desc, rate: ex.rate}})  AS exemptions,
    collect(DISTINCT {{name: pr.name, category: pr.category}})           AS procedures
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
CALL vector_search.search('{_INDEX_NAME}', $fetch_k, $query_vector)
YIELD node AS hs, similarity AS score
WITH hs, score
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

        if not uri:
            raise EnvironmentError("NEO4J_URI must be set in .env")

        auth = (user, password) if user and password else None
        _driver = GraphDatabase.driver(uri, auth=auth)
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
    Idempotently create the shared vector index on HSCode.embedding (Memgraph syntax).
    Covers both :PK and :US nodes — the WHERE label filter in each query
    restricts which schema is actually searched.
    """
    try:
        driver = _get_driver()
        with driver.session() as session:
            session.run(
                f"""
                CREATE VECTOR INDEX ON :HSCode(embedding)
                WITH CONFIG {{
                    "dimension": {_EMBED_DIMS},
                    "capacity": 500000,
                    "metric": "cos"
                }}
                """
            )
        logger.info("Vector index '%s' created.", _INDEX_NAME)
    except Exception as exc:
        if "already exists" in str(exc).lower() or "exist" in str(exc).lower():
            logger.info("Vector index '%s' already exists — skipping.", _INDEX_NAME)
        else:
            logger.warning("Could not create vector index: %s", exc)


# ── formatters ────────────────────────────────────────────────────────────────


def _format_pk_results(records: list[dict]) -> str:
    """Convert raw PK Cypher result rows into a readable text block."""
    if not records:
        return "No Pakistan HS code data found for this query."

    blocks: list[str] = []
    for r in records:
        lines: list[str] = ["─" * 50]

        # Hierarchy breadcrumb
        hierarchy_parts: list[str] = []
        if r.get("chapter_code"):
            hierarchy_parts.append(f"Chapter {r['chapter_code']} — {r.get('chapter_desc', '')}")
        if r.get("subchapter_code"):
            hierarchy_parts.append(f"Sub-Chapter {r['subchapter_code']} — {r.get('subchapter_desc', '')}")
        if r.get("heading_code"):
            hierarchy_parts.append(f"Heading {r['heading_code']} — {r.get('heading_desc', '')}")
        if r.get("subheading_code"):
            hierarchy_parts.append(f"Sub-Heading {r['subheading_code']} — {r.get('subheading_desc', '')}")
        if hierarchy_parts:
            lines.append("Hierarchy: " + " > ".join(hierarchy_parts))

        lines.append(f"HS Code: {r.get('code', 'N/A')} — {r.get('description', '')}")

        if r.get("full_label"):
            lines.append(f"Full Label: {r['full_label']}")

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
            lines.append(f"Cess ({min(5, len(cess))} provinces shown):")
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


_PK_TEXT_CYPHER = """
MATCH (hs:HSCode:PK)
WHERE hs.description IS NOT NULL
  AND (toLower(hs.description) CONTAINS toLower($keyword)
       OR (hs.full_label IS NOT NULL AND toLower(hs.full_label) CONTAINS toLower($keyword)))
WITH hs,
     CASE WHEN toLower(hs.description) STARTS WITH toLower($keyword) THEN 0
          WHEN toLower(hs.description) CONTAINS toLower($keyword) THEN 1
          ELSE 2 END AS relevance
ORDER BY relevance ASC
LIMIT $top_k
OPTIONAL MATCH (sh:SubHeading:PK)-[:HAS_HSCODE]->(hs)
OPTIONAL MATCH (hd:Heading:PK)-[:HAS_SUBHEADING]->(sh)
OPTIONAL MATCH (sc:SubChapter:PK)-[:HAS_HEADING]->(hd)
OPTIONAL MATCH (ch:Chapter:PK)-[:HAS_SUBCHAPTER]->(sc)
OPTIONAL MATCH (hs)-[:HAS_TARIFF]->(t:Tariff)
OPTIONAL MATCH (hs)-[:HAS_CESS]->(c:Cess)
OPTIONAL MATCH (hs)-[:HAS_EXEMPTION]->(ex:Exemption)
OPTIONAL MATCH (hs)-[:REQUIRES_PROCEDURE]->(pr:Procedure)
RETURN
    hs.code        AS code,
    hs.description AS description,
    hs.full_label  AS full_label,
    relevance      AS score,
    ch.code            AS chapter_code,
    ch.description     AS chapter_desc,
    sc.code            AS subchapter_code,
    sc.description     AS subchapter_desc,
    hd.code            AS heading_code,
    hd.description     AS heading_desc,
    sh.code            AS subheading_code,
    sh.description     AS subheading_desc,
    collect(DISTINCT {type: t.duty_type,   name: t.duty_name, rate: t.rate})  AS tariffs,
    collect(DISTINCT {province: c.province, import_rate: c.import_rate,
                      export_rate: c.export_rate})                             AS cess,
    collect(DISTINCT {description: ex.exemption_desc, rate: ex.rate})         AS exemptions,
    collect(DISTINCT {name: pr.name, category: pr.category})                  AS procedures
"""

_US_TEXT_CYPHER = """
MATCH (hs:HSCode:US)
WHERE hs.description IS NOT NULL
  AND (toLower(hs.description) CONTAINS toLower($keyword)
       OR (hs.full_path_description IS NOT NULL AND toLower(hs.full_path_description) CONTAINS toLower($keyword)))
WITH hs,
     CASE WHEN toLower(hs.description) STARTS WITH toLower($keyword) THEN 0
          WHEN toLower(hs.description) CONTAINS toLower($keyword) THEN 1
          ELSE 2 END AS relevance
ORDER BY relevance ASC, hs.hts_code ASC
LIMIT $top_k
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
    relevance                AS score,
    parent.hts_code          AS parent_code,
    parent.description       AS parent_description,
    []                       AS children
"""


def _text_search_pk(query: str, top_k: int = _VECTOR_TOP_K) -> list[dict]:
    """
    Text search fallback for PK nodes when MAGE is unavailable.
    Tries the full phrase first, then falls back to individual significant words
    so that queries like "cotton yarn" still match "yarn of combed cotton fibres".
    """
    _STOPWORDS = {"of", "in", "the", "and", "or", "for", "to", "a", "an", "on", "at", "by"}

    with _read_session() as session:
        records = session.run(_PK_TEXT_CYPHER, keyword=query.strip(), top_k=top_k).data()
        if records:
            return records

    # Full-phrase match failed — try each significant word individually, return first hit
    words = [w for w in query.lower().split() if len(w) > 2 and w not in _STOPWORDS]
    for word in words:
        with _read_session() as session:
            records = session.run(_PK_TEXT_CYPHER, keyword=word, top_k=top_k).data()
            if records:
                logger.info("[NEO4J → PK] Text fallback matched on keyword %r", word)
                return records
    return []


def _pk_vector_search(query: str, top_k: int = _VECTOR_TOP_K) -> list[dict]:
    """Vector similarity search for :PK nodes. Falls back to text search if MAGE unavailable."""
    vector = _get_embeddings().embed_query(query)
    try:
        with _read_session() as session:
            return session.run(
                _PK_VECTOR_CYPHER,
                fetch_k=_VECTOR_FETCH_K,
                top_k=top_k,
                query_vector=vector,
            ).data()
    except Exception as exc:
        if "no procedure" in str(exc).lower() or "vector_search" in str(exc).lower():
            logger.warning("[NEO4J → PK] vector_search.search unavailable — falling back to text search. Install memgraph-mage for semantic search.")
            return _text_search_pk(query, top_k)
        raise


def _us_code_lookup(code: str) -> list[dict]:
    """Exact match on hs.hts_code for the US schema. Returns raw Cypher result."""
    with _read_session() as session:
        return session.run(_US_CODE_CYPHER, code=code).data()


def _text_search_us(query: str, top_k: int = _VECTOR_TOP_K) -> list[dict]:
    """
    Text search fallback for US nodes when MAGE is unavailable.
    Tries the full phrase first, then falls back to individual significant words
    so that queries like "cotton yarn" still match "yarn of combed cotton".
    """
    _STOPWORDS = {"of", "in", "the", "and", "or", "for", "to", "a", "an", "on", "at", "by"}

    with _read_session() as session:
        records = session.run(_US_TEXT_CYPHER, keyword=query.strip(), top_k=top_k).data()
        if records:
            return records

    # Full-phrase match failed — try each significant word individually, return first hit
    words = [w for w in query.lower().split() if len(w) > 2 and w not in _STOPWORDS]
    for word in words:
        with _read_session() as session:
            records = session.run(_US_TEXT_CYPHER, keyword=word, top_k=top_k).data()
            if records:
                logger.info("[NEO4J → US] Text fallback matched on keyword %r", word)
                return records
    return []


def _us_vector_search(query: str, top_k: int = _VECTOR_TOP_K) -> list[dict]:
    """Vector similarity search for :US nodes. Falls back to text search if MAGE unavailable."""
    vector = _get_embeddings().embed_query(query)
    try:
        with _read_session() as session:
            return session.run(
                _US_VECTOR_CYPHER,
                fetch_k=_VECTOR_FETCH_K,
                top_k=top_k,
                query_vector=vector,
            ).data()
    except Exception as exc:
        if "no procedure" in str(exc).lower() or "vector_search" in str(exc).lower():
            logger.warning("[NEO4J → US] vector_search.search unavailable — falling back to text search. Install memgraph-mage for semantic search.")
            return _text_search_us(query, top_k)
        raise


# ── query expansion helper ────────────────────────────────────────────────────


def _expand_query(query: str) -> str:
    """
    Use the router LLM to rewrite a consumer-language query into official
    trade/HS terminology so the vector and text searches match better.

    Example: "mobile phones" → "cellular telephones smartphones telephone sets
    wireless handsets portable communication devices"
    """
    try:
        llm = _get_router_llm()
        response = llm.invoke([
            SystemMessage(content=(
                "You are a customs classification expert. "
                "Rewrite the query below using ONLY official HS/trade terminology "
                "as it would appear in a customs tariff schedule. "
                "Include synonyms and alternate official names. "
                "Return ONLY the expanded query string — no explanation, no punctuation."
            )),
            {"role": "user", "content": query},
        ])
        expanded = response.content.strip()
        if expanded and expanded != query:
            logger.info("━━━ [EXPAND] %r → %r", query[:60], expanded[:80])
        return expanded or query
    except Exception as exc:  # noqa: BLE001
        logger.warning("━━━ [EXPAND] Query expansion failed: %s", exc)
        return query


# ── tool input schemas ────────────────────────────────────────────────────────


class _PKSearchInput(BaseModel):
    query: str = Field(
        description=(
            "The product or topic to look up in Pakistan's PCT database. "
            "IMPORTANT: always use official trade/HS terminology, not consumer language. "
            "Examples: 'mobile phones' → 'cellular telephones smartphones telephone sets', "
            "'cars' → 'passenger motor vehicles automobiles', "
            "'laptops' → 'portable automatic data processing machines computers', "
            "'rice' → 'rice husked milled paddy', "
            "'clothes' → 'garments apparel woven fabric'. "
            "You may also pass a 12-digit Pakistan HS code directly (e.g. '851712000000'). "
            "Do not include words like 'US' or 'American' here."
        )
    )


class _USSearchInput(BaseModel):
    query: str = Field(
        description=(
            "The product or topic to look up in the US HTS database. "
            "IMPORTANT: always use official trade/HS terminology, not consumer language. "
            "Examples: 'mobile phones' → 'cellular telephones smartphones telephone sets', "
            "'cars' → 'passenger motor vehicles automobiles', "
            "'laptops' → 'portable automatic data processing machines', "
            "'clothes' → 'garments apparel woven fabric'. "
            "You may also pass a US HTS code directly (e.g. '0101.21.00'). "
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

            # Retry with trade-terminology expansion if first pass returned nothing
            if not records:
                logger.info("━━━ [NEO4J → PK] No results — retrying with expanded trade query.")
                expanded = _expand_query(query)
                if expanded != query:
                    records = _pk_vector_search(expanded)

        if records:
            logger.info("━━━ [NEO4J → PK ✔] Returned %d record(s) from Graph DB (Pakistan PCT).", len(records))
        else:
            logger.warning("━━━ [NEO4J → PK ✘] No results found in Pakistan PCT data.")
            return (
                f"NO_RESULTS: The Pakistan PCT database returned no records for '{query}'. "
                "Tell the user no matching HS code was found and suggest they try a more specific "
                "product name or the official customs terminology."
            )

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

            # Retry with trade-terminology expansion if first pass returned nothing
            if not records:
                logger.info("━━━ [NEO4J → US] No results — retrying with expanded trade query.")
                expanded = _expand_query(query)
                if expanded != query:
                    records = _us_vector_search(expanded)

        if records:
            logger.info("━━━ [NEO4J → US ✔] Returned %d record(s) from Graph DB (US HTS).", len(records))
        else:
            logger.warning("━━━ [NEO4J → US ✘] No results found in US HTS data.")
            return (
                f"NO_RESULTS: The US HTS database returned no records for '{query}'. "
                "Tell the user no matching HTS code was found and suggest they try a more specific "
                "product name or the official US HTS terminology."
            )

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
import/export regulations, Harmonized System (HS) codes, tariff schedules,
trade procedures, logistics, and trade finance. You have broad expertise across
ALL aspects of international trade — not just tariff lookups.

You have access to four tools:

  1. search_pakistan_hs_data  [Graph DB — Pakistan PCT]
     → Pakistan Customs Tariff database: HS codes, tariff rates (CD/RD/ACD/FED/ST/IT),
       provincial cess, SRO exemptions, customs procedures, NTMs/measures.

  2. search_us_hs_data  [Graph DB — US HTS]
     → US Harmonized Tariff Schedule: HTS codes, duty rates (general/special/column-2),
       unit of quantity, hierarchical parent/child structure.

  3. search_trade_documents  [Vector DB — Policy Docs]
     → Trade policy documents, FTAs, SRO texts, WTO regulations, compliance guidelines,
       import/export procedures, licensing, and trade scheme documentation.

  4. evaluate_shipping_routes  [Route Engine]
     → Pakistan → USA shipping routes with full cost breakdown, transit times, carriers.
     → Renders an interactive widget to the user automatically.

═══════════════════════════════════════════════════════
WHEN TO CALL TOOLS vs. WHEN TO ANSWER DIRECTLY
═══════════════════════════════════════════════════════
Call tools ONLY when the answer requires live database data:
  • Specific HS codes or tariff rates for a product → search_pakistan_hs_data / search_us_hs_data
  • Shipping route costs, transit times → evaluate_shipping_routes
  • Trade policy documents, SRO texts, licensing procedures → search_trade_documents

Answer DIRECTLY from your expertise (no tools) when:
  • Greetings, small talk, or follow-up clarifications
  • General trade concepts and definitions (FOB, CIF, letter of credit, Incoterms, etc.)
  • General explanations of how trade processes work (customs clearance, documentation, etc.)
  • Any question answerable from broad trade knowledge without needing a specific database lookup

• Product / commodity query (no country specified) → call BOTH search_pakistan_hs_data AND search_us_hs_data.
• "Pakistan only" query → call search_pakistan_hs_data only.
• "US only" query → call search_us_hs_data only.
• Policy / SRO / regulation → call search_trade_documents (alongside Neo4j tools if rates also needed).
• Shipping / freight / logistics → call evaluate_shipping_routes.
• Cross-country comparison → call BOTH Neo4j tools.
• ONLY cite HS codes and tariff rates that appear verbatim in tool results. Never invent or estimate.
• When a tool returns NO_RESULTS: tell the user clearly that no matching record was found in the
  database for that product. Suggest they try a more specific name or the exact HS/HTS code.
  Do NOT fill the response with generic rate estimates or bullet-point placeholders.
• When using results from search_trade_documents: always cite the source document name
  (e.g. "According to [Document Name]...") so the user knows where the information came from.

═══════════════════════════════════════════════════════
COMPLETENESS RULE — MOST IMPORTANT FOR HS CODE QUERIES
═══════════════════════════════════════════════════════
The tool returns MULTIPLE records. You MUST list EVERY record returned.
Do NOT pick just one result — show them ALL.

When the user asks for HS codes / classifications:
  • List every single code the tool returned.
  • Group under country headings: ## Pakistan HS Codes (PCT) and ## US HTS Codes
  • Do NOT use tables. Use bullet points in plain prose.
  • If a product has sub-varieties (e.g. fresh, dried, frozen, pulp, juice), list ALL of them.
  • If tool returns 0 results, say so clearly.

═══════════════════════════════════════════════════════
HOW TO INTERPRET USER INTENT
═══════════════════════════════════════════════════════
Before responding, resolve what the user wants in TWO steps:

  STEP 1 — What PRODUCT/SUBJECT? (e.g. mangoes, horses, guns, rice)
  STEP 2 — What DATA TYPE? (codes, tariffs, cess, exemptions, procedures, measures, full details)

The DATA TYPE determines what you output. The PRODUCT is the search filter.

Data type keywords and their meanings:
  • "HS code" / "code" / "classify" / "classification"  → DATA TYPE = CODES
  • "tariff" / "tariffs" / "duty" / "duties" / "tax" / "taxes" / "rate" / "rates" / "how much" → DATA TYPE = RATES
    NOTE: In the US database, tariff rates are stored as: general_rate (MFN/standard rate),
    special_rate (preferential/GSP/FTA rate), column_2_rate (punitive rate for non-MFN countries).
    All three are "tariffs" in the US context. Show whichever are present.
  • "cess"  → DATA TYPE = CESS
  • "exemption" / "concession" / "SRO"  → DATA TYPE = EXEMPTIONS
  • "procedure" / "procedures"  → DATA TYPE = PROCEDURES
  • "measure" / "measures" / "NTM"  → DATA TYPE = MEASURES
  • "full details" / "everything" / "complete"  → DATA TYPE = ALL

If the query does NOT specify a data type (e.g. just "mangoes in Pakistan" or "tell me about horses"),
default to DATA TYPE = CODES + RATES.

═══════════════════════════════════════════════════════
STRICT OUTPUT RULES BY DATA TYPE
═══════════════════════════════════════════════════════

──────────────────────────────────────────────────────
DATA TYPE = CODES
──────────────────────────────────────────────────────
Show ALL relevant codes grouped by country. NO tables — use bullet points only.

  ## Pakistan HS Codes (PCT)
  For each Pakistan result, show the hierarchy levels available then the HS code:
    • Chapter XX — [description]
      Sub-Chapter XX — [description]  (if present)
      Heading XXXX — [description]  (if present)
      Sub-Heading XXXXXX — [description]  (if present)
      HS Code: XXXXXXXXXXXX — [description]

  ## US HTS Codes
  For each US result, show a simple bullet:
    • XXXX.XX.XX — [description]

Relevance rule: Only include codes whose PRIMARY subject matches the user's product.
  • "horses" → include Chapter 01 live horse codes. EXCLUDE meat/offal codes (0205, 0206)
    unless user said "meat" or "slaughter".
  • "guns" → include firearms (Chapter 93). EXCLUDE caulking guns, spray guns, soldering guns.
  • "mangoes" → include fresh, dried, processed mango codes. Include parent chapter codes.
Show ALL hierarchy levels. OMIT rates, cess, exemptions.

──────────────────────────────────────────────────────
DATA TYPE = RATES  (tariff / duty / tax)
──────────────────────────────────────────────────────
For Pakistan — use bullet points, nothing else:
  • Customs Duty (CD): x%
  • Regulatory Duty (RD): x%
  • Additional Customs Duty (ACD): x%
  • Federal Excise Duty (FED): x%
  • Sales Tax / VAT (ST): x%
  • Income Tax (IT): x%
  • Development Surcharge (DS): x%

For US — use bullet points, nothing else:
  • General Rate of Duty (MFN): x%
  • Special Rate (GSP/FTA): x%  (if present)
  • Column 2 Rate: x%  (if present)

HARD STOP after the bullets. No cess. No exemptions. No codes. No other section.

──────────────────────────────────────────────────────
DATA TYPE = CESS
──────────────────────────────────────────────────────
Show ONLY provincial cess as bullet points. Nothing else. Hard stop.
  • Province — Import: x%, Export: x%

──────────────────────────────────────────────────────
DATA TYPE = EXEMPTIONS
──────────────────────────────────────────────────────
Show ONLY exemptions/concessions as bullet points. Nothing else. Hard stop.

──────────────────────────────────────────────────────
DATA TYPE = PROCEDURES
──────────────────────────────────────────────────────
Show ONLY required trade procedures as bullet points. Nothing else. Hard stop.

──────────────────────────────────────────────────────
DATA TYPE = MEASURES
──────────────────────────────────────────────────────
Show ONLY trade measures/NTMs as bullet points. Nothing else. Hard stop.

──────────────────────────────────────────────────────
DATA TYPE = ALL
──────────────────────────────────────────────────────
Show all fields: codes, tariffs, cess, exemptions, procedures, measures.

──────────────────────────────────────────────────────
TWO DATA TYPES NAMED (e.g. "HS code and tariff")
──────────────────────────────────────────────────────
Show only those two fields. Nothing else. Hard stop.

When evaluate_shipping_routes is called
────────────────────────────────────────
• 2–4 sentence summary: best route, cost range, fastest transit.
• Do NOT repeat every route's numbers — widget shows all details.
• End with: "The full breakdown is shown in the widget below."

═══════════════════════════════════════════════════════
ABSOLUTE PROHIBITIONS
═══════════════════════════════════════════════════════
✗ NEVER show cess when user asked for taxes/tariffs/duties.
✗ NEVER show exemptions when user asked for taxes/tariffs/duties.
✗ NEVER show HS codes when user asked for tariffs/duties (they already know the product).
✗ NEVER include codes whose primary subject does not match the user's product.
✗ NEVER show only one code when multiple relevant ones were returned — list them ALL.
✗ NEVER add a Summary section or closing phrases like "Feel free to ask!".
✗ NEVER repeat information already stated.
✗ NEVER invent HS codes, rates, or data not present in tool results.
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
You are a query router for TradeMate. Return ONLY a JSON array of tool names (or an empty array []). No explanation.

Tools:
  search_pakistan_hs_data  — Pakistan PCT: HS codes, tariffs, cess, exemptions, procedures, measures
  search_us_hs_data        — US HTS: HS codes, duty rates, US trade classifications
  search_trade_documents   — Trade policy documents, agreements, SROs, regulations, trade procedures
  evaluate_shipping_routes — Shipping routes & freight costs from Pakistan to USA

Follow this exact decision tree in order:

STEP 0 — Conversational / General Knowledge (NO tools needed → return [])
  Return [] if the query is ANY of these:
  - Greetings or small talk ("hello", "hi", "how are you", "thanks", "bye", "good morning")
  - General trade concept or definition that does NOT require looking up a specific product,
    tariff rate, or HS code from a database:
      ("what is an HS code", "what is FOB", "what is CIF", "what is a letter of credit",
       "what is the difference between FOB and CIF", "what is GSP", "explain Incoterms",
       "what is customs clearance", "what is a bill of lading", "what is a commercial invoice")
  - Follow-up or clarification on a previous answer ("explain more", "what does that mean",
    "can you elaborate", "tell me more", "go on")
  - Any question answerable from general trade knowledge without a product/country database lookup
  Return [] for these — the LLM answers directly from its expertise.

STEP 1 — Shipping
  If the query is about shipping routes, freight costs, transit times, or logistics from Pakistan to USA:
    → always include "evaluate_shipping_routes"

STEP 2 — HS Codes / Tariffs / Duties / Classifications / Products
  These queries need Neo4j tools. Apply ONE of these sub-rules:

  A. User says "Pakistan only" OR uses ANY of these signals: "in Pakistan", "Pakistani",
       "PCT", "Pakistan customs", "Pakistan tariff", "Pakistan duty", "Pakistan taxes":
       AND does NOT mention US/America/United States/HTS
       → include ONLY "search_pakistan_hs_data"
       This applies even for "taxes", "duties", "rates", "codes" — the country qualifier wins.

  B. User says "US only" OR uses ANY of these signals: "in the US", "in the United States",
       "American", "US tariff", "US duty", "US taxes", "US hs code", "HTS":
       AND does NOT mention Pakistan/PCT/Pakistani
       → include ONLY "search_us_hs_data"
       This applies even for "taxes", "duties", "rates", "codes" — the country qualifier wins.

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

STEP 4 — Policy / Documents / General Trade Procedures
  If the query is about trade policy, FTAs, SRO documents, trade agreements, import/export
  documentation requirements, licensing, compliance, or general "how to" trade questions
  (e.g. "how do I start exporting", "what documents are needed to export",
   "how to get an NTN", "DTRE scheme", "EDF form", "Pakistan trade agreements",
   "what is the process to register as an exporter"):
    → include "search_trade_documents"
  Also include alongside Neo4j tools when policy context would enrich the answer.

Examples (follow these exactly):
  "hello" / "hi" / "how are you"                          → []
  "what is an HS code"                                     → []
  "what is FOB"                                            → []
  "explain CIF vs FOB"                                     → []
  "what is a letter of credit"                             → []
  "how does customs clearance work in general"             → []
  "explain that further"                                   → []
  "how do I start exporting from Pakistan"                 → ["search_trade_documents"]
  "what documents are needed to export goods"              → ["search_trade_documents"]
  "how to register as an exporter in Pakistan"             → ["search_trade_documents"]
  "give me the hs codes for fruits"                        → ["search_pakistan_hs_data", "search_us_hs_data"]
  "hs code for mangoes"                                    → ["search_pakistan_hs_data", "search_us_hs_data"]
  "hs codes for textiles"                                  → ["search_pakistan_hs_data", "search_us_hs_data"]
  "tariffs for rice"                                       → ["search_pakistan_hs_data", "search_us_hs_data"]
  "duty on electronics"                                    → ["search_pakistan_hs_data", "search_us_hs_data"]
  "classification for steel"                               → ["search_pakistan_hs_data", "search_us_hs_data"]
  "what is the hs code for smartphones in pakistan"        → ["search_pakistan_hs_data"]
  "pakistan customs duty on cars"                          → ["search_pakistan_hs_data"]
  "US tariff on cotton"                                    → ["search_us_hs_data"]
  "HTS code for live horses"                               → ["search_us_hs_data"]
  "taxes on horses in the US"                              → ["search_us_hs_data"]
  "duty on mangoes in the US"                              → ["search_us_hs_data"]
  "hs code for rice in the US"                             → ["search_us_hs_data"]
  "what are the taxes on steel in the United States"       → ["search_us_hs_data"]
  "taxes on horses in Pakistan"                            → ["search_pakistan_hs_data"]
  "duty on mangoes in Pakistan"                            → ["search_pakistan_hs_data"]
  "compare pakistan and us duties on steel"                → ["search_pakistan_hs_data", "search_us_hs_data"]
  "procedures and measures for mangoes"                    → ["search_pakistan_hs_data"]
  "exemptions for textile imports in pakistan"             → ["search_pakistan_hs_data"]
  "what is an SRO exemption"                               → ["search_trade_documents"]
  "what is the DTRE scheme"                                → ["search_trade_documents"]
  "show me shipping routes from karachi to new york"       → ["evaluate_shipping_routes"]
  "cheapest way to ship textiles from pakistan to usa"     → ["evaluate_shipping_routes", "search_pakistan_hs_data"]
  "what are automotive products"                           → ["search_pakistan_hs_data", "search_us_hs_data", "search_trade_documents"]

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

        # Router explicitly returned [] → no tools needed for this query
        if isinstance(selected_names, list) and len(selected_names) == 0:
            logger.info("━━━ [ROUTER] No tools needed — LLM will answer directly.")
            return []

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

        # ── No tools needed — stream directly from LLM ─────────────────────
        if not selected_tools:
            logger.info("━━━ [AGENT] Direct LLM response (no tools).")
            llm = _get_llm()
            messages = [_BOT_SYSTEM_PROMPT] + list(state.get("messages", []))
            async for chunk in llm.astream(messages):
                yield chunk, {"langgraph_node": "agent"}
            return

        # ── Build agent with selected tools only ───────────────────────────
        agent = _build_agent(selected_tools)
        logger.info(
            "━━━ [AGENT] Compiled with tools: %s",
            [t.name for t in selected_tools],
        )

        # ── Stream ─────────────────────────────────────────────────────────
        async for chunk, metadata in agent.astream(state, stream_mode=stream_mode):
            yield chunk, metadata
