from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class ChatbotPrompt(SQLModel, table=True):
    __tablename__ = "chatbot_prompts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True) # e.g. "system_prompt", "agent_prompt"
    content: str
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
