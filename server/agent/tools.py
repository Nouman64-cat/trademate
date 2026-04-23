"""
tools.py — Memgraph knowledge-graph retrieval for TradeMate.

Responsibilities
────────────────
1. Maintain lazy-initialised singletons for the Memgraph driver and the
   OpenAI embeddings model so the expensive setup happens once per process.
2. Ensure a vector index exists on HSCode.embedding before the first query.
3. Embed the user query and run a vector similarity search, then expand each
   hit with its related Tariff, Cess, Exemption, and Procedure nodes.
4. Degrade gracefully — if Memgraph or OpenAI is unavailable the retrieve
   function logs a warning and returns an empty string so the LLM can still
   answer from its training knowledge.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Knowledge-graph credentials (Memgraph + OpenAI) live in knowledge_graph/.env —
# load from there so we have a single source of truth.
_KG_ENV = Path(__file__).parent.parent.parent / "knowledge_graph" / ".env"
load_dotenv(dotenv_path=_KG_ENV, override=False)
# Also load the server .env for any server-specific overrides.
load_dotenv(override=False)

logger = logging.getLogger(__name__)

# ── lazy singletons ────────────────────────────────────────────────────────────

_driver = None
_embeddings = None


def _get_driver():
    global _driver
    if _driver is None:
        from neo4j import GraphDatabase  # imported lazily to avoid hard dep at import time

        uri = os.getenv("MEMGRAPH_URI")
        user = os.getenv("MEMGRAPH_USERNAME")
        password = os.getenv("MEMGRAPH_PASSWORD")

        if not uri:
            raise EnvironmentError("MEMGRAPH_URI must be set in .env")

        auth = (user, password) if user and password else None
        _driver = GraphDatabase.driver(uri, auth=auth)
        _driver.verify_connectivity()
        logger.info("Memgraph driver initialised → %s", uri)

    return _driver


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_openai import OpenAIEmbeddings

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY must be set in .env")

        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
        )
        logger.info("OpenAI embeddings model initialised (text-embedding-3-small)")

    return _embeddings


# ── vector index setup ────────────────────────────────────────────────────────

_INDEX_NAME = "HSCode_embedding"
_EMBEDDING_DIMS = 1536  # text-embedding-3-small


def ensure_vector_index() -> None:
    """
    Idempotently create a Memgraph vector index on HSCode.embedding.
    """
    try:
        driver = _get_driver()
        with driver.session() as session:
            session.run(
                f"""
                CREATE VECTOR INDEX ON :HSCode(embedding)
                WITH CONFIG {{
                    "dimension": {_EMBEDDING_DIMS},
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


# ── retrieval ─────────────────────────────────────────────────────────────────

_RETRIEVE_CYPHER = f"""
CALL vector_search.search('{_INDEX_NAME}', $top_k, $query_vector)
YIELD node AS hs, similarity AS score

// Determine whether this is a PK or US node
WITH hs, score,
     CASE WHEN 'PK' IN labels(hs) THEN 'PK'
          WHEN 'US' IN labels(hs) THEN 'US'
          ELSE 'UNKNOWN' END AS source,
     // PK nodes use hs.code; US nodes use hs.hts_code
     coalesce(hs.code, hs.hts_code)          AS code,
     coalesce(hs.full_label, hs.full_path_description) AS full_label

// PK-only: tariff, cess, exemption, procedure relationships
OPTIONAL MATCH (hs)-[:HAS_TARIFF]->(t:Tariff)
OPTIONAL MATCH (hs)-[:HAS_CESS]->(c:Cess)
OPTIONAL MATCH (hs)-[:HAS_EXEMPTION]->(ex:Exemption)
OPTIONAL MATCH (hs)-[:REQUIRES_PROCEDURE]->(pr:Procedure)

// US-only: walk up the HAS_CHILD tree to find the parent (indent - 1)
OPTIONAL MATCH (parent:HSCode:US)-[:HAS_CHILD]->(hs)

RETURN
    source,
    code,
    hs.description                AS description,
    full_label,
    score,
    hs.general_rate               AS us_general_rate,
    hs.special_rate               AS us_special_rate,
    hs.column_2_rate              AS us_column2_rate,
    hs.unit                       AS us_unit,
    hs.indent                     AS us_indent,
    coalesce(parent.hts_code, '') AS us_parent_code,
    coalesce(parent.description, '') AS us_parent_desc,
    collect(DISTINCT {{
        type: t.duty_type,
        name: t.duty_name,
        rate: t.rate
    }})  AS tariffs,
    collect(DISTINCT {{
        province:     c.province,
        import_rate:  c.import_rate,
        export_rate:  c.export_rate
    }})  AS cess,
    collect(DISTINCT {{
        description: ex.exemption_desc,
        rate:        ex.rate
    }})  AS exemptions,
    collect(DISTINCT {{
        name:        pr.name,
        category:    pr.category,
        description: pr.description
    }})  AS procedures
ORDER BY score DESC
"""


def _format_record(record: dict) -> str:
    """Convert a single Memgraph record into a readable text block."""
    source = record.get("source", "UNKNOWN")

    lines = [
        f"Source      : {source} Trade Data",
        f"HTS/HS Code : {record.get('code', 'N/A')}",
        f"Description : {record.get('description', '')}",
    ]

    if record.get("full_label"):
        lines.append(f"Full Path   : {record['full_label']}")

    lines.append(f"Similarity  : {record['score']:.4f}")

    if source == "US":
        # US node — show rate columns and parent context
        if record.get("us_parent_code"):
            lines.append(f"Parent Code : {record['us_parent_code']} — {record.get('us_parent_desc', '')}")
        if record.get("us_unit"):
            lines.append(f"Unit        : {record['us_unit']}")
        if record.get("us_general_rate"):
            lines.append(f"General Rate of Duty  : {record['us_general_rate']}")
        if record.get("us_special_rate"):
            lines.append(f"Special Rate of Duty  : {record['us_special_rate']}")
        if record.get("us_column2_rate"):
            lines.append(f"Column 2 Rate of Duty : {record['us_column2_rate']}")

    else:
        # PK node — show tariff, cess, exemptions, procedures
        valid_tariffs = [t for t in (record.get("tariffs") or []) if t.get("type")]
        if valid_tariffs:
            lines.append("Tariffs:")
            for t in valid_tariffs:
                lines.append(f"  • {t['name']} ({t['type']}): {t['rate']}")

        valid_cess = [c for c in (record.get("cess") or []) if c.get("province")]
        if valid_cess:
            lines.append("Cess Collection (up to 5 provinces):")
            for c in valid_cess[:5]:
                lines.append(
                    f"  • {c['province']} — Import: {c['import_rate']}, Export: {c['export_rate']}"
                )

        valid_ex = [e for e in (record.get("exemptions") or []) if e.get("description")]
        if valid_ex:
            lines.append("Exemptions / Concessions:")
            for e in valid_ex[:3]:
                rate_str = f" ({e['rate']})" if e.get("rate") else ""
                lines.append(f"  • {e['description']}{rate_str}")

        valid_pr = [p for p in (record.get("procedures") or []) if p.get("name")]
        if valid_pr:
            lines.append("Trade Procedures:")
            for p in valid_pr[:3]:
                cat = f" [{p['category']}]" if p.get("category") else ""
                lines.append(f"  • {p['name']}{cat}")

    return "\n".join(lines)


# ── Pinecone retrieval ────────────────────────────────────────────────────────

_pinecone_index = None
_PINECONE_INDEX_NAME = "trademate-documents"
_PINECONE_EMBEDDING_DIMS = 1536  # text-embedding-3-small


def _get_pinecone_index():
    """Lazy singleton for the Pinecone index."""
    global _pinecone_index
    if _pinecone_index is None:
        from pinecone import Pinecone

        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise EnvironmentError("PINECONE_API_KEY must be set in .env")

        pc = Pinecone(api_key=api_key)
        _pinecone_index = pc.Index(_PINECONE_INDEX_NAME)
        logger.info("Pinecone index '%s' connected.", _PINECONE_INDEX_NAME)
    return _pinecone_index


def _get_pinecone_embeddings():
    """
    Pinecone uses text-embedding-3-small (1536 dims).
    We keep a separate singleton so it doesn't conflict with the
    Memgraph embeddings model (text-embedding-3-small, 1536 dims).
    """
    from langchain_openai import OpenAIEmbeddings

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY must be set in .env")

    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=api_key,
    )


def retrieve_pinecone_context(query: str, top_k: int = 5) -> str:
    """
    Embed *query* with text-embedding-3-small, query Pinecone, and return
    a formatted string of the top-k matching document chunks.
    Returns an empty string on any error so the graph degrades gracefully.
    """
    try:
        embedding_model = _get_pinecone_embeddings()
        query_vector = embedding_model.embed_query(query)

        index = _get_pinecone_index()
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )

        matches = results.get("matches", [])
        if not matches:
            logger.info("Pinecone returned no results for query: %r", query[:80])
            return ""

        blocks = []
        for i, match in enumerate(matches, 1):
            meta = match.get("metadata", {})
            score = match.get("score", 0)
            text = meta.get("text", "").strip()
            source = meta.get("source", "unknown")
            page = meta.get("page", "")

            if not text:
                continue

            header = f"[Document {i}] {source}"
            if page != "":
                header += f" (page {page})"
            header += f" — relevance: {score:.4f}"

            blocks.append(f"{header}\n{text}")

        logger.info(
            "Retrieved %d document chunk(s) from Pinecone for query: %r",
            len(blocks),
            query[:80],
        )
        return "\n\n---\n\n".join(blocks)

    except Exception as exc:
        logger.warning(
            "Pinecone retrieval failed — continuing without document context. Error: %s",
            exc,
        )
        return ""


def retrieve_trade_context(query: str, top_k: int = 5) -> str:
    """
    Embed *query*, search the Memgraph vector index, and return a formatted
    context string.  Returns an empty string on any error so the graph node
    can fall back gracefully to LLM-only answering.
    """
    try:
        embeddings = _get_embeddings()
        query_vector = embeddings.embed_query(query)

        driver = _get_driver()
        with driver.session() as session:
            result = session.run(
                _RETRIEVE_CYPHER,
                top_k=top_k,
                query_vector=query_vector,
            )
            records = result.data()

        if not records:
            logger.info("Vector search returned no results for query: %r", query[:80])
            return ""

        blocks = [_format_record(r) for r in records]
        logger.info(
            "Retrieved %d HS code(s) from Memgraph for query: %r", len(blocks), query[:80]
        )
        return "\n\n---\n\n".join(blocks)

    except Exception as exc:
        logger.warning(
            "Memgraph retrieval failed — falling back to LLM-only mode. Error: %s", exc
        )
        return ""
