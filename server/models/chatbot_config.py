from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class ChatbotConfig(SQLModel, table=True):
    __tablename__ = "chatbot_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    llm_model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)
    top_p: float = Field(default=0.9)
    available_tools: str = Field(
        default="search_pakistan_hs_data,search_us_hs_data,search_trade_documents,evaluate_shipping_routes"
    )
    router_enabled: bool = Field(default=True)
    max_tool_calls: int = Field(default=5)
    max_messages_per_hour: int = Field(default=100)
    max_conversations_per_day: int = Field(default=50)
    document_search_enabled: bool = Field(default=True)
    route_evaluation_enabled: bool = Field(default=True)
    hs_code_search_enabled: bool = Field(default=True)
    recommendation_enabled: bool = Field(default=True)
    interaction_tracking_enabled: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
