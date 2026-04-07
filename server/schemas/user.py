from typing import Optional

from pydantic import BaseModel, EmailStr

from models.user import TradeRole


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    phone_number: str


class RegisterResponse(BaseModel):
    id: int
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OnboardingRequest(BaseModel):
    trade_role: TradeRole
    user_type: str
    company_name: Optional[str] = None
    target_region: Optional[str] = None
    language_preference: Optional[str] = None


class OnboardingResponse(BaseModel):
    message: str
    is_onboarded: bool
