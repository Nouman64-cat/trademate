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

import logging
import os
import re
from pathlib import Path
from typing import Optional

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
OPTIONAL MATCH (hs)-[:HAS_MEASURE]->(m:Measure)
RETURN
    hs.code                                                              AS code,
    hs.description                                                       AS description,
    hs.full_label                                                        AS full_label,
    null                                                                 AS score,
    collect(DISTINCT {type: t.duty_type,   name: t.duty_name, rate: t.rate})  AS tariffs,
    collect(DISTINCT {province: c.province, import_rate: c.import_rate,
                      export_rate: c.export_rate})                       AS cess,
    collect(DISTINCT {description: ex.exemption_desc, rate: ex.rate})   AS exemptions,
    collect(DISTINCT {name: pr.name, category: pr.category})            AS procedures,
    collect(DISTINCT {name: m.name, type: m.measure_type})              AS measures
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
OPTIONAL MATCH (hs)-[:HAS_MEASURE]->(m:Measure)
RETURN
    hs.code                                                              AS code,
    hs.description                                                       AS description,
    hs.full_label                                                        AS full_label,
    score,
    collect(DISTINCT {{type: t.duty_type,   name: t.duty_name, rate: t.rate}})  AS tariffs,
    collect(DISTINCT {{province: c.province, import_rate: c.import_rate,
                      export_rate: c.export_rate}})                      AS cess,
    collect(DISTINCT {{description: ex.exemption_desc, rate: ex.rate}})  AS exemptions,
    collect(DISTINCT {{name: pr.name, category: pr.category}})           AS procedures,
    collect(DISTINCT {{name: m.name, type: m.measure_type}})             AS measures
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

        measures = [m for m in (r.get("measures") or []) if m.get("name")]
        if measures:
            lines.append("Trade Measures:")
            for m in measures[:3]:
                lines.append(f"  • {m.get('name', '')} ({m.get('type', '')})")

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
            # Fast path: exact code lookup — skip embedding call entirely
            logger.info("PK tool: exact code lookup for '%s'", query)
            records = _pk_code_lookup(query)
            if not records:
                # Code not found — fall back to semantic search on the description
                logger.info("PK code '%s' not found; falling back to vector search.", query)
                records = _pk_vector_search(query)
        else:
            logger.info("PK tool: vector search for '%s'", query[:80])
            records = _pk_vector_search(query)

        result = _format_pk_results(records)
        logger.info("PK tool returned %d record(s).", len(records))
        return result

    except Exception as exc:  # noqa: BLE001
        logger.warning("search_pakistan_hs_data failed: %s", exc)
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
            # Fast path: exact code lookup
            logger.info("US tool: exact code lookup for '%s'", query)
            records = _us_code_lookup(query)
            if not records:
                logger.info("US code '%s' not found; falling back to vector search.", query)
                records = _us_vector_search(query)
        else:
            logger.info("US tool: vector search for '%s'", query[:80])
            records = _us_vector_search(query)

        result = _format_us_results(records)
        logger.info("US tool returned %d record(s).", len(records))
        return result

    except Exception as exc:  # noqa: BLE001
        logger.warning("search_us_hs_data failed: %s", exc)
        return (
            f"US HTS data retrieval failed: {exc}. "
            "Please ensure Neo4j is running (docker start neo4j-trademate) "
            "and NEO4J_URI / credentials are correct in knowledge_graph/.env."
        )


# ── agent system prompt ───────────────────────────────────────────────────────

_BOT_SYSTEM_PROMPT = SystemMessage(content="""\
You are TradeMate, an expert AI assistant specialising in international trade,
Harmonized System (HS) codes, import/export regulations, and tariff schedules.

You have access to two tools that query a local Neo4j knowledge graph:

  1. search_pakistan_hs_data
     → Pakistan PCT (Pakistan Customs Tariff) database (:PK schema)
     → Star schema: HS codes connected to Tariff, Cess, Exemption,
       Procedure, and Measure nodes
     → Use for: CD/RD/ACD/FED/ST rates, provincial cess, SRO exemptions,
       customs procedures, NTMs

  2. search_us_hs_data
     → US Harmonized Tariff Schedule database (:US schema)
     → 11-level implicit hierarchy via HAS_CHILD relationships
     → Rates stored as properties: general_rate, special_rate, column_2_rate
     → Use for: US import duties, HTS classifications, US trade data

Rules you MUST follow
──────────────────────
• ALWAYS call a tool before answering a question about specific duty rates
  or HS/HTS codes. Never answer from training knowledge alone.
• For cross-country comparisons, call BOTH tools (one per country).
• ONLY cite HS codes and duty rates that appear verbatim in tool results.
  Never invent, estimate, interpolate, or recall rates from training data.
• If a tool returns no data, tell the user clearly and suggest they rephrase
  with a more specific product name, HS code, or HTS heading.
• Label every rate you quote with its source country and duty type.
• Use bullet points or tables when listing multiple rates — clarity matters.
• For general procedural questions (how customs clearance works, what an
  SRO is, etc.) you may answer from knowledge, but label it as general
  guidance, not authoritative PCT or HTS data.
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

# ── ReAct agent ───────────────────────────────────────────────────────────────

_TOOLS = [search_pakistan_hs_data, search_us_hs_data]


def _build_bot():
    """
    Compile the LangGraph ReAct agent.

    create_react_agent produces this graph:
        __start__
            │
            ▼
        agent_node  ─── no tool calls ──► __end__
            ▲                │
            │           tool_call?
            │                │
            └──── tool_node ◄┘

    The agent_node calls the LLM with the bound tools.
    If the LLM emits a tool call, tool_node executes it and appends the
    ToolMessage to state["messages"], then loops back to agent_node.
    When the LLM produces a plain AIMessage (no tool calls), the loop exits.
    """
    llm   = _get_llm()
    graph = create_react_agent(
        model=llm.bind_tools(_TOOLS),
        tools=_TOOLS,
        prompt=_BOT_SYSTEM_PROMPT,
    )
    logger.info("ReAct bot graph compiled (tools: %s).", [t.name for t in _TOOLS])
    return graph


_bot = None


def get_bot():
    """
    Return the compiled ReAct agent graph.

    On the first call this will:
      1. Verify / create the Neo4j vector index (idempotent).
      2. Initialise the LLM singleton.
      3. Compile the LangGraph ReAct graph.

    Subsequent calls return the cached graph immediately.

    Usage in routes/chat.py:
        from agent.bot import get_bot
        graph = get_bot()
        initial_state = {"messages": messages}
        async for chunk, metadata in graph.astream(initial_state,
                                                    stream_mode="messages"):
            ...
    """
    global _bot  # noqa: PLW0603
    if _bot is None:
        logger.info("Initialising TradeMate ReAct bot …")
        _ensure_index()
        _bot = _build_bot()
        logger.info("ReAct bot ready.")
    return _bot
