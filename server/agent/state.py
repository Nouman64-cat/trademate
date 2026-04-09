from typing import Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    State flowing through the TradeMate LangGraph agent.

    messages  — full conversation turn list (user + assistant).
                The add_messages reducer appends new messages rather
                than replacing the list on every node update.
    context   — raw text retrieved from the Neo4j knowledge graph for
                the current user turn.  Overwritten on every retrieve call.
    """

    messages: Annotated[List[BaseMessage], add_messages]
    context: str
