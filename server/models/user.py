from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class TradeRole(str, Enum):
    importer = "importer"
    exporter = "exporter"
    both = "both"


class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email_address: str = Field(max_length=255, unique=True)
    phone_number: str = Field(max_length=20)
    password_hash: str = Field(max_length=255)
    trade_role: Optional[str] = Field(
        default=None,
        sa_column=Column(
            SAEnum("importer", "exporter", "both", name="trade_role_enum"),
            nullable=True,
        ),
    )
    company_name: Optional[str] = Field(default=None, max_length=255)
    user_type: Optional[str] = Field(default=None, max_length=100)
    user_name: str = Field(max_length=100)
    status: str = Field(
        default="active",
        sa_column=Column(
            SAEnum("active", "inactive", "suspended", name="user_status_enum"),
            nullable=False,
            default="active",
        ),
    )
    target_region: Optional[str] = Field(default=None, max_length=100)
    language_preference: Optional[str] = Field(default=None, max_length=50)
    is_onboarded: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )
