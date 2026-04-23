from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class SecuritySettings(SQLModel, table=True):
    __tablename__ = "security_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    min_password_length: int = Field(default=8)
    require_special_characters: bool = Field(default=True)
    require_numbers: bool = Field(default=True)
    two_factor_required: bool = Field(default=False)
    session_timeout_minutes: int = Field(default=60)
    max_login_attempts: int = Field(default=5)
    jwt_access_token_expire_minutes: int = Field(default=30)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
