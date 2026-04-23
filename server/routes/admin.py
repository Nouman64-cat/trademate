"""
routes/admin.py — Admin portal API endpoints.

Endpoints for:
- Dashboard statistics
- User management (CRUD)
- Chatbot configuration
- System analytics
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlmodel import Session, select, func, and_

from database.database import get_session
from models.user import User
from models.conversation import Conversation, Message
from security.security import decode_access_token, hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])
_bearer = HTTPBearer()


# ── Authentication ─────────────────────────────────────────────────────────────


def _get_current_admin_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: Session = Depends(get_session),
) -> int:
    """
    Extract user ID from JWT token and verify admin privileges.
    """
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload["id"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Check if user is admin
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user_id


# ── Response Schemas ───────────────────────────────────────────────────────────


class DashboardStatsResponse(BaseModel):
    total_users: int
    verified_users: int
    active_users: int
    total_conversations: int
    total_messages: int
    avg_response_time_ms: float
    users_last_24h: int
    conversations_last_24h: int
    messages_last_24h: int


class UserListItem(BaseModel):
    id: int
    email: str
    full_name: str
    trade_role: Optional[str]
    target_region: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: str
    last_login: Optional[str]


class UserListResponse(BaseModel):
    users: List[UserListItem]
    total: int
    page: int
    page_size: int


class UserDetailResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone_number: str
    trade_role: Optional[str]
    company_name: Optional[str]
    user_type: Optional[str]
    target_region: Optional[str]
    language_preference: Optional[str]
    is_verified: bool
    is_active: bool
    is_onboarded: bool
    created_at: str
    updated_at: str


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    phone_number: str
    password: str
    trade_role: Optional[str] = None
    company_name: Optional[str] = None
    target_region: Optional[str] = None


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    trade_role: Optional[str] = None
    company_name: Optional[str] = None
    target_region: Optional[str] = None
    is_verified: Optional[bool] = None
    status: Optional[str] = None


class ChatbotConfigResponse(BaseModel):
    llm_model: str
    temperature: float
    max_tokens: int
    top_p: float
    available_tools: List[str]
    router_enabled: bool
    max_tool_calls: int
    max_messages_per_hour: int
    max_conversations_per_day: int
    document_search_enabled: bool
    route_evaluation_enabled: bool
    hs_code_search_enabled: bool
    recommendation_enabled: bool
    interaction_tracking_enabled: bool


class UpdateChatbotConfigRequest(BaseModel):
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    router_enabled: Optional[bool] = None
    max_tool_calls: Optional[int] = None
    max_messages_per_hour: Optional[int] = None
    max_conversations_per_day: Optional[int] = None
    document_search_enabled: Optional[bool] = None
    route_evaluation_enabled: Optional[bool] = None
    hs_code_search_enabled: Optional[bool] = None
    recommendation_enabled: Optional[bool] = None
    interaction_tracking_enabled: Optional[bool] = None


# ── Dashboard Stats ────────────────────────────────────────────────────────────


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Get dashboard statistics for admin portal."""

    # Total users
    total_users = session.exec(select(func.count(User.id))).one()

    # Verified users
    verified_users = session.exec(
        select(func.count(User.id)).where(User.is_verified == True)
    ).one()

    # Active users (status = 'active')
    active_users = session.exec(
        select(func.count(User.id)).where(User.status == "active")
    ).one()

    # Total conversations
    total_conversations = session.exec(select(func.count(Conversation.id))).one()

    # Total messages
    total_messages = session.exec(select(func.count(Message.id))).one()

    # Average response time (placeholder - calculate from message timestamps)
    # TODO: Implement actual response time tracking
    avg_response_time_ms = 1250.0

    # Last 24 hours stats
    yesterday = datetime.utcnow() - timedelta(hours=24)

    users_last_24h = session.exec(
        select(func.count(User.id)).where(User.created_at >= yesterday)
    ).one()

    conversations_last_24h = session.exec(
        select(func.count(Conversation.id)).where(Conversation.created_at >= yesterday)
    ).one()

    messages_last_24h = session.exec(
        select(func.count(Message.id)).where(Message.created_at >= yesterday)
    ).one()

    logger.info("[ADMIN] Dashboard stats requested by admin_id=%d", admin_id)

    return DashboardStatsResponse(
        total_users=total_users,
        verified_users=verified_users,
        active_users=active_users,
        total_conversations=total_conversations,
        total_messages=total_messages,
        avg_response_time_ms=avg_response_time_ms,
        users_last_24h=users_last_24h,
        conversations_last_24h=conversations_last_24h,
        messages_last_24h=messages_last_24h,
    )


# ── User Management ────────────────────────────────────────────────────────────


@router.get("/users", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    trade_role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """List all users with pagination and filters."""

    # Build query
    query = select(User)

    # Apply filters
    conditions = []
    if search:
        search_term = f"%{search.lower()}%"
        conditions.append(
            (User.user_name.ilike(search_term)) | (User.email_address.ilike(search_term))
        )

    if trade_role and trade_role != "all":
        conditions.append(User.trade_role == trade_role)

    if status and status != "all":
        if status == "active":
            conditions.append(User.status == "active")
        elif status == "inactive":
            conditions.append(User.status == "inactive")

    if is_verified is not None:
        conditions.append(User.is_verified == is_verified)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    total = session.exec(select(func.count(User.id)).where(and_(*conditions)) if conditions else select(func.count(User.id))).one()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    users = session.exec(query).all()

    logger.info("[ADMIN] Users list requested by admin_id=%d, page=%d, total=%d", admin_id, page, total)

    return UserListResponse(
        users=[
            UserListItem(
                id=u.id,
                email=u.email_address,
                full_name=u.user_name,
                trade_role=u.trade_role,
                target_region=u.target_region,
                is_verified=u.is_verified,
                is_active=u.status == "active",
                created_at=u.created_at.isoformat(),
                last_login=None,  # TODO: Track last login in User model
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: int,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Get detailed user information."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    logger.info("[ADMIN] User %d details requested by admin_id=%d", user_id, admin_id)

    return UserDetailResponse(
        id=user.id,
        email=user.email_address,
        full_name=user.user_name,
        phone_number=user.phone_number,
        trade_role=user.trade_role,
        company_name=user.company_name,
        user_type=user.user_type,
        target_region=user.target_region,
        language_preference=user.language_preference,
        is_verified=user.is_verified,
        is_active=user.status == "active",
        is_onboarded=user.is_onboarded,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )


@router.post("/users", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserRequest,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Create a new user."""
    email = body.email.lower().strip()

    # Check if user exists
    existing = session.exec(select(User).where(User.email_address == email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email_address=email,
        user_name=body.full_name,
        phone_number=body.phone_number,
        password_hash=hash_password(body.password),
        trade_role=body.trade_role,
        company_name=body.company_name,
        target_region=body.target_region,
        status="active",
        is_verified=True,  # Admin-created users are auto-verified
        is_onboarded=False,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info("[ADMIN] User %d created by admin_id=%d", user.id, admin_id)

    return UserDetailResponse(
        id=user.id,
        email=user.email_address,
        full_name=user.user_name,
        phone_number=user.phone_number,
        trade_role=user.trade_role,
        company_name=user.company_name,
        user_type=user.user_type,
        target_region=user.target_region,
        language_preference=user.language_preference,
        is_verified=user.is_verified,
        is_active=user.status == "active",
        is_onboarded=user.is_onboarded,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )


@router.put("/users/{user_id}", response_model=UserDetailResponse)
def update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Update user information."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Update fields
    if body.full_name is not None:
        user.user_name = body.full_name
    if body.phone_number is not None:
        user.phone_number = body.phone_number
    if body.trade_role is not None:
        user.trade_role = body.trade_role
    if body.company_name is not None:
        user.company_name = body.company_name
    if body.target_region is not None:
        user.target_region = body.target_region
    if body.is_verified is not None:
        user.is_verified = body.is_verified
    if body.status is not None:
        user.status = body.status

    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info("[ADMIN] User %d updated by admin_id=%d", user_id, admin_id)

    return UserDetailResponse(
        id=user.id,
        email=user.email_address,
        full_name=user.user_name,
        phone_number=user.phone_number,
        trade_role=user.trade_role,
        company_name=user.company_name,
        user_type=user.user_type,
        target_region=user.target_region,
        language_preference=user.language_preference,
        is_verified=user.is_verified,
        is_active=user.status == "active",
        is_onboarded=user.is_onboarded,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Delete a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    session.delete(user)
    session.commit()

    logger.info("[ADMIN] User %d deleted by admin_id=%d", user_id, admin_id)


# ── Chatbot Configuration ──────────────────────────────────────────────────────


@router.get("/chatbot/config", response_model=ChatbotConfigResponse)
def get_chatbot_config(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get current chatbot configuration."""
    # TODO: Store config in database or config file
    # For now, return hardcoded defaults
    logger.info("[ADMIN] Chatbot config requested by admin_id=%d", admin_id)

    return ChatbotConfigResponse(
        llm_model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2048,
        top_p=0.9,
        available_tools=[
            "search_pakistan_hs_data",
            "search_us_hs_data",
            "search_trade_documents",
            "evaluate_shipping_routes",
        ],
        router_enabled=True,
        max_tool_calls=5,
        max_messages_per_hour=100,
        max_conversations_per_day=50,
        document_search_enabled=True,
        route_evaluation_enabled=True,
        hs_code_search_enabled=True,
        recommendation_enabled=True,
        interaction_tracking_enabled=True,
    )


@router.put("/chatbot/config", response_model=ChatbotConfigResponse)
def update_chatbot_config(
    body: UpdateChatbotConfigRequest,
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Update chatbot configuration."""
    # TODO: Persist config to database or config file
    logger.info("[ADMIN] Chatbot config updated by admin_id=%d", admin_id)

    # For now, just return the current config
    # In production, you'd update the config and reload it
    return ChatbotConfigResponse(
        llm_model=body.llm_model or "gpt-4o-mini",
        temperature=body.temperature if body.temperature is not None else 0.7,
        max_tokens=body.max_tokens or 2048,
        top_p=body.top_p if body.top_p is not None else 0.9,
        available_tools=[
            "search_pakistan_hs_data",
            "search_us_hs_data",
            "search_trade_documents",
            "evaluate_shipping_routes",
        ],
        router_enabled=body.router_enabled if body.router_enabled is not None else True,
        max_tool_calls=body.max_tool_calls or 5,
        max_messages_per_hour=body.max_messages_per_hour or 100,
        max_conversations_per_day=body.max_conversations_per_day or 50,
        document_search_enabled=body.document_search_enabled if body.document_search_enabled is not None else True,
        route_evaluation_enabled=body.route_evaluation_enabled if body.route_evaluation_enabled is not None else True,
        hs_code_search_enabled=body.hs_code_search_enabled if body.hs_code_search_enabled is not None else True,
        recommendation_enabled=body.recommendation_enabled if body.recommendation_enabled is not None else True,
        interaction_tracking_enabled=body.interaction_tracking_enabled if body.interaction_tracking_enabled is not None else True,
    )
