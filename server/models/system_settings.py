from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class SystemSettings(SQLModel, table=True):
    __tablename__ = "system_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    site_name: str = Field(default="TradeMate Admin")
    support_email: str = Field(default="support@trademate.com")
    maintenance_mode: bool = Field(default=False)
    default_language: str = Field(default="en")
    timezone: str = Field(default="UTC")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
