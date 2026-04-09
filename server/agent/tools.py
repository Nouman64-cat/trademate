"""
tools.py — Neo4j knowledge-graph retrieval for TradeMate.

Responsibilities
────────────────
1. Maintain lazy-initialised singletons for the Neo4j driver and the
   OpenAI embeddings model so the expensive setup happens once per process.
2. Ensure a vector index exists on HSCode.embedding before the first query.
3. Embed the user query and run a vector similarity search, then expand each
   hit with its related Tariff, Cess, Exemption, and Procedure nodes.
4. Degrade gracefully — if Neo4j or OpenAI is unavailable the retrieve
   function logs a warning and returns an empty string so the LLM can still
   answer from its training knowledge.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Knowledge-graph credentials (Neo4j + OpenAI) live in knowledge_graph/.env —
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

        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([uri, user, password]):
            raise EnvironmentError(
                "NEO4J_URI, NEO4J_USERNAME and NEO4J_PASSWORD must be set in .env"
            )

        _driver = GraphDatabase.driver(uri, auth=(user, password))
        _driver.verify_connectivity()
        logger.info("Neo4j driver initialised → %s", uri)

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

_INDEX_NAME = "hscode_embedding_index"
_EMBEDDING_DIMS = 1536  # text-embedding-3-small


def ensure_vector_index() -> None:
    """
    Idempotently create a Neo4j vector index on HSCode.embedding.
    Safe to call multiple times — uses IF NOT EXISTS.
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
                        `vector.dimensions`: {_EMBEDDING_DIMS},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
            )
        logger.info("Vector index '%s' verified / created.", _INDEX_NAME)
    except Exception as exc:
        logger.warning("Could not create vector index: %s", exc)


# ── retrieval ─────────────────────────────────────────────────────────────────

_RETRIEVE_CYPHER = f"""
CALL db.index.vector.queryNodes('{_INDEX_NAME}', $top_k, $query_vector)
YIELD node AS hs, score

OPTIONAL MATCH (hs)-[:HAS_TARIFF]->(t:Tariff)
OPTIONAL MATCH (hs)-[:HAS_CESS]->(c:Cess)
OPTIONAL MATCH (hs)-[:HAS_EXEMPTION]->(ex:Exemption)
OPTIONAL MATCH (hs)-[:REQUIRES_PROCEDURE]->(pr:Procedure)

RETURN
    hs.code        AS code,
    hs.description AS description,
    hs.full_label  AS full_label,
    score,
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
        description: ex.description,
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
    """Convert a single Neo4j record into a readable text block."""
    lines = [
        f"HS Code : {record['code']}",
        f"Description : {record['description']}",
    ]

    if record.get("full_label"):
        lines.append(f"Full Label  : {record['full_label']}")

    lines.append(f"Similarity  : {record['score']:.4f}")

    # Tariffs
    valid_tariffs = [t for t in (record.get("tariffs") or []) if t.get("type")]
    if valid_tariffs:
        lines.append("Tariffs:")
        for t in valid_tariffs:
            lines.append(f"  • {t['name']} ({t['type']}): {t['rate']}")

    # Cess (show up to 5 provinces)
    valid_cess = [c for c in (record.get("cess") or []) if c.get("province")]
    if valid_cess:
        lines.append("Cess Collection (up to 5 provinces):")
        for c in valid_cess[:5]:
            lines.append(
                f"  • {c['province']} — Import: {c['import_rate']}, Export: {c['export_rate']}"
            )

    # Exemptions
    valid_ex = [e for e in (record.get("exemptions") or []) if e.get("description")]
    if valid_ex:
        lines.append("Exemptions / Concessions:")
        for e in valid_ex[:3]:
            rate_str = f" ({e['rate']})" if e.get("rate") else ""
            lines.append(f"  • {e['description']}{rate_str}")

    # Procedures
    valid_pr = [p for p in (record.get("procedures") or []) if p.get("name")]
    if valid_pr:
        lines.append("Trade Procedures:")
        for p in valid_pr[:3]:
            cat = f" [{p['category']}]" if p.get("category") else ""
            lines.append(f"  • {p['name']}{cat}")

    return "\n".join(lines)


def retrieve_trade_context(query: str, top_k: int = 5) -> str:
    """
    Embed *query*, search the Neo4j vector index, and return a formatted
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
            "Retrieved %d HS code(s) from Neo4j for query: %r", len(blocks), query[:80]
        )
        return "\n\n---\n\n".join(blocks)

    except Exception as exc:
        logger.warning(
            "Neo4j retrieval failed — falling back to LLM-only mode. Error: %s", exc
        )
        return ""
