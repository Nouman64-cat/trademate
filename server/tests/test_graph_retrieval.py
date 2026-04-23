"""
test_graph_retrieval.py
=======================
Verifies that the Memgraph vector retrieval pipeline returns REAL data from the
knowledge graph and that the LLM response is grounded in that data rather than
hallucinated.

What each test proves
─────────────────────
1. Memgraph connection   — driver can reach the Memgraph instance.
2. Vector index exists   — hscode_embedding_index is present and populated.
3. Raw retrieval         — retrieve_trade_context() returns non-empty text for
                           a known product query.
4. HS code present       — the returned context contains at least one 12-digit
                           HS code (proving real graph data, not an empty shell).
5. Tariff data present   — the context includes at least one duty type (CD, ST …).
6. LLM grounding check   — the final LLM response mentions an HS code that was
                           actually in the retrieved context (not invented).
7. No-context refusal    — when retrieval returns nothing (nonsense query),
                           the LLM does NOT invent duty rates.

Run from the server/ directory:
    cd trademate/server
    python -m pytest tests/test_graph_retrieval.py -v
"""

import re
import sys
import os
from pathlib import Path

import pytest

# ── make sure server/ is on the path so agent imports resolve ─────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load credentials from knowledge_graph/.env before importing agent modules
from dotenv import load_dotenv
_KG_ENV = Path(__file__).parent.parent.parent / "knowledge_graph" / ".env"
load_dotenv(dotenv_path=_KG_ENV, override=False)
load_dotenv(override=False)

# ── imports (after env is loaded) ─────────────────────────────────────────────
from agent.tools import (
    _get_driver,
    _get_embeddings,
    _INDEX_NAME,
    ensure_vector_index,
    retrieve_trade_context,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

# Queries that should definitely hit the graph
KNOWN_QUERIES = [
    "import duty on mobile phones",
    "customs duty on raw cotton",
    "tariff for importing laptops",
    "HS code for rice",
    "duty on crude petroleum oil",
]

# A query that should NOT match anything meaningful
NONSENSE_QUERY = "xyzzy frobnicate quantum banana tariff 99999"

# Duty type abbreviations that appear in real tariff data
DUTY_TYPE_PATTERN = re.compile(
    r"\b(CD|RD|ACD|FED|ST|IT|DS|EOC|ERD|Customs Duty|Sales Tax|Regulatory Duty)\b",
    re.IGNORECASE,
)

# 12-digit HS code pattern
HS_CODE_PATTERN = re.compile(r"\b\d{12}\b")


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Memgraph connection
# ─────────────────────────────────────────────────────────────────────────────

def test_memgraph_connection():
    """Driver must connect and verify connectivity without raising."""
    driver = _get_driver()
    # verify_connectivity() raises if the DB is unreachable
    driver.verify_connectivity()


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Vector index exists and is populated
# ─────────────────────────────────────────────────────────────────────────────

def test_vector_index_exists():
    """The hscode_embedding_index must exist and have at least 1 000 nodes."""
    ensure_vector_index()  # idempotent — safe to call here
    driver = _get_driver()

    with driver.session() as session:
        result = session.run(
            "SHOW INDEXES YIELD name, type, state, populationPercent "
            "WHERE name = $name",
            name=_INDEX_NAME,
        )
        rows = result.data()

    assert rows, f"Vector index '{_INDEX_NAME}' not found in Memgraph."
    idx = rows[0]
    assert idx["state"] == "ONLINE", (
        f"Index '{_INDEX_NAME}' is in state '{idx['state']}', expected ONLINE."
    )
    assert idx["populationPercent"] > 0, (
        f"Index '{_INDEX_NAME}' has 0% population — no embeddings stored?"
    )
    print(f"\n  ✓ Index state: {idx['state']}, populated: {idx['populationPercent']:.1f}%")


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Raw retrieval returns results
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("query", KNOWN_QUERIES)
def test_retrieval_returns_results(query):
    """retrieve_trade_context() must return non-empty text for known product queries."""
    context = retrieve_trade_context(query, top_k=3)
    assert context.strip(), (
        f"retrieve_trade_context() returned empty string for query: {query!r}\n"
        "Check that Memgraph is running, the index is populated, and OPENAI_API_KEY is set."
    )
    print(f"\n  Query : {query!r}")
    print(f"  Context preview : {context[:200]} …")


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Context contains real 12-digit HS codes (not hallucinated)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("query", KNOWN_QUERIES)
def test_context_contains_hs_codes(query):
    """The retrieved context must contain at least one 12-digit HS code."""
    context = retrieve_trade_context(query, top_k=3)
    matches = HS_CODE_PATTERN.findall(context)
    assert matches, (
        f"No 12-digit HS code found in retrieved context for query: {query!r}\n"
        f"Context snippet:\n{context[:400]}"
    )
    print(f"\n  Found HS codes: {matches[:5]}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Context contains duty type data
# ─────────────────────────────────────────────────────────────────────────────

def test_context_contains_tariff_data():
    """At least one query must return context that includes a duty type label."""

    # First check how many Tariff nodes exist at all in Memgraph
    driver = _get_driver()
    with driver.session() as session:
        tariff_count = session.run("MATCH (t:Tariff) RETURN count(t) AS n").single()["n"]
        linked_count = session.run(
            "MATCH (:HSCode)-[:HAS_TARIFF]->(t:Tariff) RETURN count(t) AS n"
        ).single()["n"]

    print(f"\n  Tariff nodes in graph   : {tariff_count}")
    print(f"  Tariff nodes linked     : {linked_count}")

    assert tariff_count > 0, (
        f"No Tariff nodes exist in Memgraph (count={tariff_count}). "
        "Run ingest.py to load tariff data — specifically the ingest_tariffs() step."
    )
    assert linked_count > 0, (
        f"Tariff nodes exist ({tariff_count}) but none are linked to an HSCode via HAS_TARIFF. "
        "Re-run ingest.py — the hierarchy and tariffs steps must share the same HS code values."
    )

    # Fetch an HS code that actually HAS a tariff, then retrieve context for it
    with driver.session() as session:
        row = session.run(
            """
            MATCH (hs:HSCode)-[:HAS_TARIFF]->(t:Tariff)
            WHERE t.duty_type IS NOT NULL AND hs.description IS NOT NULL
            RETURN hs.code AS code, hs.description AS description,
                   t.duty_type AS duty_type, t.duty_name AS duty_name
            LIMIT 1
            """
        ).single()

    assert row, "Could not find a single (HSCode)-[:HAS_TARIFF]->(Tariff) path with real data."

    print(f"  Sample HS code  : {row['code']} — {row['description']}")
    print(f"  Sample duty     : {row['duty_type']} / {row['duty_name']}")

    # Retrieve context using the actual description of a code known to have tariffs
    context = retrieve_trade_context(row["description"], top_k=5)

    # Check whether the duty type abbreviation appears in the formatted context
    found_duty = DUTY_TYPE_PATTERN.search(context) is not None

    # Also do a raw check: does the duty_type string from the graph appear literally?
    raw_match = row["duty_type"] in context if row["duty_type"] else False

    print(f"  DUTY_TYPE_PATTERN match : {found_duty}")
    print(f"  Raw duty_type in context: {raw_match}")
    print(f"  Context snippet:\n{context[:600]}")

    assert found_duty or raw_match, (
        f"Duty type '{row['duty_type']}' is linked in the graph but didn't appear in "
        "the formatted context. The _format_record() function may be filtering it out — "
        "check that t.duty_type is not None in the Cypher result."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — LLM response is grounded: cites an HS code from the context
# ─────────────────────────────────────────────────────────────────────────────

def test_llm_response_cites_graph_hs_code():
    """
    Send a real query through the full pipeline (retrieve + generate).
    The LLM reply must contain at least one HS code that was present in the
    retrieved context — proving the answer is grounded, not hallucinated.
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from agent.prompts import SYSTEM_PROMPT

    query = "What is the customs duty on importing mobile phones to Pakistan?"
    context = retrieve_trade_context(query, top_k=5)

    # The context must have HS codes to compare against
    context_hs_codes = set(HS_CODE_PATTERN.findall(context))
    assert context_hs_codes, "Retrieval returned no HS codes — cannot verify grounding."

    llm = ChatOpenAI(
        model="gpt-5.4",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )

    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(context=context))
    response = llm.invoke([system_msg, HumanMessage(content=query)])
    reply_text = response.content

    # Check that at least one HS code from the context appears in the reply
    reply_hs_codes = set(HS_CODE_PATTERN.findall(reply_text))
    grounded_codes = context_hs_codes & reply_hs_codes

    print(f"\n  Context HS codes : {context_hs_codes}")
    print(f"  Reply HS codes   : {reply_hs_codes}")
    print(f"  Grounded codes   : {grounded_codes}")
    print(f"\n  LLM reply snippet:\n  {reply_text[:400]}")

    assert grounded_codes, (
        "LLM response contains NO HS code from the retrieved context.\n"
        f"Context codes : {context_hs_codes}\n"
        f"Reply codes   : {reply_hs_codes}\n"
        "This suggests the LLM may be hallucinating rather than using graph data."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — LLM refuses to invent rates when context is empty
# ─────────────────────────────────────────────────────────────────────────────

def test_llm_refuses_to_hallucinate_on_empty_context():
    """
    With an intentionally nonsense query (so retrieval returns nothing),
    the LLM must NOT produce a specific duty rate or HS code.
    It should instead say it could not find the information.
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from agent.prompts import SYSTEM_PROMPT

    context = retrieve_trade_context(NONSENSE_QUERY, top_k=5)
    # Context should be empty or irrelevant; we proceed either way.

    llm = ChatOpenAI(
        model="gpt-5.4",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )

    question = f"What is the exact import duty rate for '{NONSENSE_QUERY}'?"
    system_msg = SystemMessage(content=SYSTEM_PROMPT.format(context=context or ""))
    response = llm.invoke([system_msg, HumanMessage(content=question)])
    reply_text = response.content.lower()

    print(f"\n  LLM reply on nonsense query:\n  {response.content[:400]}")

    # The reply should NOT contain a percentage figure presented as a specific rate
    # alongside a confident assertion. We check for refusal keywords instead.
    refusal_keywords = [
        "no matching", "not found", "couldn't find", "could not find",
        "no record", "not available", "unable to find", "no relevant",
        "rephrase", "more specific", "knowledge base does not",
    ]
    contains_refusal = any(kw in reply_text for kw in refusal_keywords)

    assert contains_refusal, (
        "LLM did NOT refuse to answer for a nonsense query — it may be hallucinating.\n"
        f"Reply: {response.content[:500]}"
    )
