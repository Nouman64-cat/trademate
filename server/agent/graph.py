"""
graph.py — LangGraph agent graph for TradeMate.

Graph topology
──────────────
    START ──► retrieve ──► generate ──► END

• retrieve  — embeds the latest user message, queries Memgraph, and writes the
              text results into state["context"].
• generate  — injects the system prompt (with context) and calls ChatOpenAI,
              appending the assistant reply to state["messages"].

The compiled graph is a module-level singleton so it is built only once per
worker process.
"""

import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from agent.prompts import SYSTEM_PROMPT
from agent.state import AgentState
from agent.tools import ensure_vector_index, retrieve_pinecone_context, retrieve_trade_context

load_dotenv()

logger = logging.getLogger(__name__)

# ── LLM singleton ──────────────────────────────────────────────────────────────


def _build_llm() -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY must be set in .env")
    return ChatOpenAI(
        model="gpt-5.4",
        openai_api_key=api_key,
        streaming=True,
        temperature=0.2,
    )


_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = _build_llm()
    return _llm


# ── graph nodes ────────────────────────────────────────────────────────────────


def retrieve_node(state: AgentState) -> dict:
    """
    Pull the latest human message from the conversation, embed it, and
    retrieve the top-k matching HS code records from Memgraph.

    Returns a partial state update: {"context": <retrieved text>}.
    """
    last_msg: BaseMessage = state["messages"][-1]
    query: str = last_msg.content if isinstance(last_msg.content, str) else ""

    logger.info("━━━ [QUERY] %r", query[:120])
    logger.info("━━━ [SOURCE 1/2] Querying Memgraph (Graph DB) …")
    context = retrieve_trade_context(query)

    if context:
        # Count how many records came back (each block is separated by ---)
        record_count = context.count("HTS/HS Code")
        pk_count = context.count("Source      : PK")
        us_count = context.count("Source      : US")
        logger.info(
            "━━━ [MEMGRAPH ✔] Returned %d record(s)  [PK: %d | US: %d]",
            record_count, pk_count, us_count,
        )
    else:
        logger.warning("━━━ [MEMGRAPH ✘] No results returned from Memgraph.")

    return {"context": context}


def vector_search_node(state: AgentState) -> dict:
    """
    Embed the latest user message and query Pinecone for semantically
    relevant document chunks (trade policies, reports, regulations).

    Returns a partial state update: {"pinecone_context": <retrieved text>}.
    Runs after retrieve_node so both knowledge sources are populated before
    the LLM generates its response.
    """
    last_msg: BaseMessage = state["messages"][-1]
    query: str = last_msg.content if isinstance(last_msg.content, str) else ""

    logger.info("━━━ [SOURCE 2/2] Querying Pinecone (Vector DB) …")
    pinecone_context = retrieve_pinecone_context(query)

    if pinecone_context:
        chunk_count = pinecone_context.count("[Document ")
        logger.info("━━━ [PINECONE ✔] Returned %d document chunk(s).", chunk_count)
    else:
        logger.warning("━━━ [PINECONE ✘] No results returned from Pinecone.")

    return {"pinecone_context": pinecone_context}


def generate_node(state: AgentState) -> dict:
    """
    Build a prompt from the system message + retrieved context + full
    conversation history, then call the LLM.

    Returns a partial state update: {"messages": [<assistant reply>]}.
    The add_messages reducer in AgentState will append the reply.
    """
    llm = _get_llm()
    context = state.get("context") or ""
    pinecone_context = state.get("pinecone_context") or ""

    memgraph_hit = bool(context)
    pinecone_hit = bool(pinecone_context)

    if memgraph_hit and pinecone_hit:
        sources_used = "Memgraph (Graph DB) + Pinecone (Vector DB)"
    elif memgraph_hit:
        sources_used = "Memgraph (Graph DB) only"
    elif pinecone_hit:
        sources_used = "Pinecone (Vector DB) only"
    else:
        sources_used = "None — LLM answering from training knowledge only"

    logger.info("━━━ [GENERATE] Sources used → %s", sources_used)

    context = context or "No relevant trade data was found in the knowledge base."
    pinecone_context = pinecone_context or "No relevant documents were found."

    system_msg = SystemMessage(
        content=SYSTEM_PROMPT.format(context=context, pinecone_context=pinecone_context)
    )
    prompt_messages = [system_msg] + list(state["messages"])

    response = llm.invoke(prompt_messages)
    logger.info("━━━ [DONE] Response generated.")
    return {"messages": [response]}


# ── graph assembly ─────────────────────────────────────────────────────────────


def _build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("retrieve", retrieve_node)
    builder.add_node("vector_search", vector_search_node)
    builder.add_node("generate", generate_node)

    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "vector_search")
    builder.add_edge("vector_search", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


# ── singleton accessor ─────────────────────────────────────────────────────────

_compiled_graph = None


def get_graph():
    """
    Return the compiled LangGraph agent.  On the first call the Memgraph vector
    index is verified / created and the graph is compiled.
    """
    global _compiled_graph
    if _compiled_graph is None:
        logger.info("Initialising TradeMate agent graph …")
        ensure_vector_index()
        _compiled_graph = _build_graph()
        logger.info("Agent graph ready.")
    return _compiled_graph
