from typing import Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    State flowing through the TradeMate LangGraph agent.

    messages         — full conversation turn list (user + assistant).
                       The add_messages reducer appends new messages rather
                       than replacing the list on every node update.
    context          — structured trade data retrieved from the Memgraph
                       knowledge graph (HS codes, tariffs, procedures…).
                       Overwritten on every retrieve call.
    pinecone_context — semantic search results retrieved from Pinecone
                       (ingested trade documents, policies, reports…).
                       Overwritten on every vector_search call.
    """

    messages: Annotated[List[BaseMessage], add_messages]
    context: str
    pinecone_context: str
