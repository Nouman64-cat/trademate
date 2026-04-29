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
from sqlalchemy import text
from sqlmodel import Session, select, func, and_

from database.database import get_session
from models.user import User
from models.conversation import Conversation, Message
from security.security import decode_access_token, hash_password
from models.chatbot_prompt import ChatbotPrompt
from models.system_settings import SystemSettings
from models.chatbot_config import ChatbotConfig
from agent.bot import clear_agent_cache

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
    phone_number: str
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
    available_tools: Optional[List[str]] = None
    router_enabled: Optional[bool] = None
    max_tool_calls: Optional[int] = None
    max_messages_per_hour: Optional[int] = None
    max_conversations_per_day: Optional[int] = None
    document_search_enabled: Optional[bool] = None
    route_evaluation_enabled: Optional[bool] = None
    hs_code_search_enabled: Optional[bool] = None
    recommendation_enabled: Optional[bool] = None
    interaction_tracking_enabled: Optional[bool] = None


class PromptListItem(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    updated_at: str


class PromptDetailResponse(BaseModel):
    id: int
    name: str
    content: str
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str


class UpdatePromptRequest(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SystemSettingsResponse(BaseModel):
    site_name: str
    support_email: str
    maintenance_mode: bool
    default_language: str
    timezone: str
    updated_at: str


class UpdateSystemSettingsRequest(BaseModel):
    site_name: Optional[str] = None
    support_email: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    default_language: Optional[str] = None
    timezone: Optional[str] = None


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

    # Real avg response time: time from each user message to the next assistant message
    try:
        rt_row = session.execute(text("""
            SELECT AVG(delta_ms) FROM (
                SELECT
                    EXTRACT(EPOCH FROM (MIN(a.created_at) - u.created_at)) * 1000 AS delta_ms
                FROM messages u
                JOIN messages a
                  ON u.conversation_id = a.conversation_id
                 AND a.role = 'assistant'
                 AND a.created_at > u.created_at
                WHERE u.role = 'user'
                GROUP BY u.id, u.created_at
            ) sub
            WHERE delta_ms > 0 AND delta_ms < 60000
        """)).fetchone()
        avg_response_time_ms = float(rt_row[0]) if rt_row and rt_row[0] is not None else 0.0
    except Exception:
        avg_response_time_ms = 0.0

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


# ── Analytics ─────────────────────────────────────────────────────────────────


class DailyDataPoint(BaseModel):
    date: str
    new_users: int
    new_conversations: int
    new_messages: int


class DailyAnalyticsResponse(BaseModel):
    daily: list[DailyDataPoint]
    avg_response_time_ms: float


@router.get("/analytics/daily", response_model=DailyAnalyticsResponse)
def get_daily_analytics(
    days: int = Query(30, ge=7, le=90),
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Per-day breakdown of new users, conversations, and messages for the last N days."""
    from_date = datetime.utcnow() - timedelta(days=days)

    users_rows = session.exec(
        select(func.date(User.created_at), func.count(User.id))
        .where(User.created_at >= from_date)
        .group_by(func.date(User.created_at))
    ).all()

    convs_rows = session.exec(
        select(func.date(Conversation.created_at), func.count(Conversation.id))
        .where(Conversation.created_at >= from_date)
        .group_by(func.date(Conversation.created_at))
    ).all()

    msgs_rows = session.exec(
        select(func.date(Message.created_at), func.count(Message.id))
        .where(Message.created_at >= from_date)
        .group_by(func.date(Message.created_at))
    ).all()

    users_map = {str(r[0]): r[1] for r in users_rows}
    convs_map = {str(r[0]): r[1] for r in convs_rows}
    msgs_map  = {str(r[0]): r[1] for r in msgs_rows}

    daily = []
    for i in range(days, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).date()
        ds = str(d)
        daily.append(DailyDataPoint(
            date=ds,
            new_users=users_map.get(ds, 0),
            new_conversations=convs_map.get(ds, 0),
            new_messages=msgs_map.get(ds, 0),
        ))

    try:
        rt_row = session.execute(text("""
            SELECT AVG(delta_ms) FROM (
                SELECT
                    EXTRACT(EPOCH FROM (MIN(a.created_at) - u.created_at)) * 1000 AS delta_ms
                FROM messages u
                JOIN messages a
                  ON u.conversation_id = a.conversation_id
                 AND a.role = 'assistant'
                 AND a.created_at > u.created_at
                WHERE u.role = 'user'
                GROUP BY u.id, u.created_at
            ) sub
            WHERE delta_ms > 0 AND delta_ms < 60000
        """)).fetchone()
        avg_ms = float(rt_row[0]) if rt_row and rt_row[0] is not None else 0.0
    except Exception:
        avg_ms = 0.0

    logger.info("[ADMIN] Daily analytics requested by admin_id=%d, days=%d", admin_id, days)
    return DailyAnalyticsResponse(daily=daily, avg_response_time_ms=avg_ms)


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
                phone_number=u.phone_number or "",
                trade_role=u.trade_role,
                target_region=u.target_region,
                is_verified=u.is_verified,
                is_active=u.status == "active",
                created_at=u.created_at.isoformat(),
                last_login=u.last_login.isoformat() if u.last_login else None,
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


def _get_or_create_chatbot_config(session: Session) -> ChatbotConfig:
    cfg = session.exec(select(ChatbotConfig)).first()
    if not cfg:
        cfg = ChatbotConfig()
        session.add(cfg)
        session.commit()
        session.refresh(cfg)
    return cfg


def _chatbot_config_to_response(cfg: ChatbotConfig) -> ChatbotConfigResponse:
    return ChatbotConfigResponse(
        llm_model=cfg.llm_model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        top_p=cfg.top_p,
        available_tools=[t.strip() for t in cfg.available_tools.split(",") if t.strip()],
        router_enabled=cfg.router_enabled,
        max_tool_calls=cfg.max_tool_calls,
        max_messages_per_hour=cfg.max_messages_per_hour,
        max_conversations_per_day=cfg.max_conversations_per_day,
        document_search_enabled=cfg.document_search_enabled,
        route_evaluation_enabled=cfg.route_evaluation_enabled,
        hs_code_search_enabled=cfg.hs_code_search_enabled,
        recommendation_enabled=cfg.recommendation_enabled,
        interaction_tracking_enabled=cfg.interaction_tracking_enabled,
    )


@router.get("/chatbot/config", response_model=ChatbotConfigResponse)
def get_chatbot_config(
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Get current chatbot configuration."""
    logger.info("[ADMIN] Chatbot config requested by admin_id=%d", admin_id)
    cfg = _get_or_create_chatbot_config(session)
    return _chatbot_config_to_response(cfg)


@router.put("/chatbot/config", response_model=ChatbotConfigResponse)
def update_chatbot_config(
    body: UpdateChatbotConfigRequest,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Update chatbot configuration."""
    logger.info("[ADMIN] Chatbot config updated by admin_id=%d", admin_id)

    cfg = _get_or_create_chatbot_config(session)

    if body.llm_model is not None:
        cfg.llm_model = body.llm_model
    if body.temperature is not None:
        cfg.temperature = body.temperature
    if body.max_tokens is not None:
        cfg.max_tokens = body.max_tokens
    if body.top_p is not None:
        cfg.top_p = body.top_p
    if body.available_tools is not None:
        cfg.available_tools = ",".join(body.available_tools)
    if body.router_enabled is not None:
        cfg.router_enabled = body.router_enabled
    if body.max_tool_calls is not None:
        cfg.max_tool_calls = body.max_tool_calls
    if body.max_messages_per_hour is not None:
        cfg.max_messages_per_hour = body.max_messages_per_hour
    if body.max_conversations_per_day is not None:
        cfg.max_conversations_per_day = body.max_conversations_per_day
    if body.document_search_enabled is not None:
        cfg.document_search_enabled = body.document_search_enabled
    if body.route_evaluation_enabled is not None:
        cfg.route_evaluation_enabled = body.route_evaluation_enabled
    if body.hs_code_search_enabled is not None:
        cfg.hs_code_search_enabled = body.hs_code_search_enabled
    if body.recommendation_enabled is not None:
        cfg.recommendation_enabled = body.recommendation_enabled
    if body.interaction_tracking_enabled is not None:
        cfg.interaction_tracking_enabled = body.interaction_tracking_enabled

    cfg.updated_at = datetime.utcnow()
    session.add(cfg)
    session.commit()
    session.refresh(cfg)

    return _chatbot_config_to_response(cfg)


# ── Chatbot Prompts ───────────────────────────────────────────────────────────


@router.get("/chatbot/prompts", response_model=List[PromptListItem])
def list_prompts(
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """List all chatbot prompts."""
    prompts = session.exec(select(ChatbotPrompt).order_by(ChatbotPrompt.name)).all()
    logger.info("[ADMIN] Chatbot prompts list requested by admin_id=%d", admin_id)

    return [
        PromptListItem(
            id=p.id,
            name=p.name,
            description=p.description,
            is_active=p.is_active,
            updated_at=p.updated_at.isoformat(),
        )
        for p in prompts
    ]


@router.get("/chatbot/prompts/{prompt_id}", response_model=PromptDetailResponse)
def get_prompt(
    prompt_id: int,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Get detailed prompt information."""
    prompt = session.get(ChatbotPrompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    logger.info("[ADMIN] Chatbot prompt %d details requested by admin_id=%d", prompt_id, admin_id)

    return PromptDetailResponse(
        id=prompt.id,
        name=prompt.name,
        content=prompt.content,
        description=prompt.description,
        is_active=prompt.is_active,
        created_at=prompt.created_at.isoformat(),
        updated_at=prompt.updated_at.isoformat(),
    )


@router.put("/chatbot/prompts/{prompt_id}", response_model=PromptDetailResponse)
def update_prompt(
    prompt_id: int,
    body: UpdatePromptRequest,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Update a chatbot prompt."""
    prompt = session.get(ChatbotPrompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    if body.content is not None:
        prompt.content = body.content
    if body.description is not None:
        prompt.description = body.description
    if body.is_active is not None:
        prompt.is_active = body.is_active

    prompt.updated_at = datetime.utcnow()

    session.add(prompt)
    session.commit()
    session.refresh(prompt)

    # Clear agent cache to apply changes
    clear_agent_cache()

    logger.info("[ADMIN] Chatbot prompt %d updated by admin_id=%d", prompt_id, admin_id)

    return PromptDetailResponse(
        id=prompt.id,
        name=prompt.name,
        content=prompt.content,
        description=prompt.description,
        is_active=prompt.is_active,
        created_at=prompt.created_at.isoformat(),
        updated_at=prompt.updated_at.isoformat(),
    )

# ── System Settings ───────────────────────────────────────────────────────────


@router.get("/settings/general", response_model=SystemSettingsResponse)
def get_system_settings(
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Get current system settings."""
    settings = session.exec(select(SystemSettings)).first()
    if not settings:
        # Fallback if seed didn't run
        settings = SystemSettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)

    logger.info("[ADMIN] System settings requested by admin_id=%d", admin_id)

    return SystemSettingsResponse(
        site_name=settings.site_name,
        support_email=settings.support_email,
        maintenance_mode=settings.maintenance_mode,
        default_language=settings.default_language,
        timezone=settings.timezone,
        updated_at=settings.updated_at.isoformat(),
    )


@router.put("/settings/general", response_model=SystemSettingsResponse)
def update_system_settings(
    body: UpdateSystemSettingsRequest,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Update system settings."""
    settings = session.exec(select(SystemSettings)).first()
    if not settings:
        settings = SystemSettings()

    if body.site_name is not None:
        settings.site_name = body.site_name
    if body.support_email is not None:
        settings.support_email = body.support_email
    if body.maintenance_mode is not None:
        settings.maintenance_mode = body.maintenance_mode
    if body.default_language is not None:
        settings.default_language = body.default_language
    if body.timezone is not None:
        settings.timezone = body.timezone

    settings.updated_at = datetime.utcnow()

    session.add(settings)
    session.commit()
    session.refresh(settings)

    logger.info("[ADMIN] System settings updated by admin_id=%d", admin_id)

    return SystemSettingsResponse(
        site_name=settings.site_name,
        support_email=settings.support_email,
        maintenance_mode=settings.maintenance_mode,
        default_language=settings.default_language,
        timezone=settings.timezone,
        updated_at=settings.updated_at.isoformat(),
    )

# ── Security Settings ─────────────────────────────────────────────────────────

from models.security_settings import SecuritySettings

class SecuritySettingsResponse(BaseModel):
    min_password_length: int
    require_special_characters: bool
    require_numbers: bool
    two_factor_required: bool
    session_timeout_minutes: int
    max_login_attempts: int
    jwt_access_token_expire_minutes: int
    updated_at: str


class UpdateSecuritySettingsRequest(BaseModel):
    min_password_length: Optional[int] = None
    require_special_characters: Optional[bool] = None
    require_numbers: Optional[bool] = None
    two_factor_required: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    max_login_attempts: Optional[int] = None
    jwt_access_token_expire_minutes: Optional[int] = None


@router.get("/settings/security", response_model=SecuritySettingsResponse)
def get_security_settings(
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Get current security settings."""
    settings = session.exec(select(SecuritySettings)).first()
    if not settings:
        settings = SecuritySettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)

    logger.info("[ADMIN] Security settings requested by admin_id=%d", admin_id)

    return SecuritySettingsResponse(
        min_password_length=settings.min_password_length,
        require_special_characters=settings.require_special_characters,
        require_numbers=settings.require_numbers,
        two_factor_required=settings.two_factor_required,
        session_timeout_minutes=settings.session_timeout_minutes,
        max_login_attempts=settings.max_login_attempts,
        jwt_access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
        updated_at=settings.updated_at.isoformat(),
    )


@router.put("/settings/security", response_model=SecuritySettingsResponse)
def update_security_settings(
    body: UpdateSecuritySettingsRequest,
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Update security settings."""
    settings = session.exec(select(SecuritySettings)).first()
    if not settings:
        settings = SecuritySettings()

    if body.min_password_length is not None:
        settings.min_password_length = body.min_password_length
    if body.require_special_characters is not None:
        settings.require_special_characters = body.require_special_characters
    if body.require_numbers is not None:
        settings.require_numbers = body.require_numbers
    if body.two_factor_required is not None:
        settings.two_factor_required = body.two_factor_required
    if body.session_timeout_minutes is not None:
        settings.session_timeout_minutes = body.session_timeout_minutes
    if body.max_login_attempts is not None:
        settings.max_login_attempts = body.max_login_attempts
    if body.jwt_access_token_expire_minutes is not None:
        settings.jwt_access_token_expire_minutes = body.jwt_access_token_expire_minutes

    settings.updated_at = datetime.utcnow()

    session.add(settings)
    session.commit()
    session.refresh(settings)

    logger.info("[ADMIN] Security settings updated by admin_id=%d", admin_id)

    return SecuritySettingsResponse(
        min_password_length=settings.min_password_length,
        require_special_characters=settings.require_special_characters,
        require_numbers=settings.require_numbers,
        two_factor_required=settings.two_factor_required,
        session_timeout_minutes=settings.session_timeout_minutes,
        max_login_attempts=settings.max_login_attempts,
        jwt_access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
        updated_at=settings.updated_at.isoformat(),
    )


# ── Token Economy ─────────────────────────────────────────────────────────────


class ModelTokenStats(BaseModel):
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    message_count: int


class UserTokenStats(BaseModel):
    user_id: int
    email: str
    full_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    message_count: int


class DailyTokenStats(BaseModel):
    date: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class TokenEconomyResponse(BaseModel):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float
    tracked_messages: int
    by_model: List[ModelTokenStats]
    by_user: List[UserTokenStats]
    daily: List[DailyTokenStats]


@router.get("/token-economy", response_model=TokenEconomyResponse)
def get_token_economy(
    days: int = Query(30, ge=7, le=90),
    admin_id: int = Depends(_get_current_admin_user_id),
    session: Session = Depends(get_session),
):
    """Aggregate token usage and cost data for the Token Economy page."""

    # All-time totals
    try:
        total_row = session.execute(text("""
            SELECT
                COALESCE(SUM(prompt_tokens), 0),
                COALESCE(SUM(completion_tokens), 0),
                COALESCE(SUM(cost_usd), 0),
                COUNT(*)
            FROM messages
            WHERE role = 'assistant' AND model_name IS NOT NULL
        """)).fetchone()
        total_prompt = int(total_row[0])
        total_completion = int(total_row[1])
        total_cost = float(total_row[2])
        tracked_msgs = int(total_row[3])
    except Exception:
        total_prompt = total_completion = tracked_msgs = 0
        total_cost = 0.0

    # Per-model breakdown
    try:
        model_rows = session.execute(text("""
            SELECT
                COALESCE(model_name, 'unknown') as model_name,
                COALESCE(SUM(prompt_tokens), 0),
                COALESCE(SUM(completion_tokens), 0),
                COALESCE(SUM(cost_usd), 0),
                COUNT(*)
            FROM messages
            WHERE role = 'assistant' AND model_name IS NOT NULL
            GROUP BY model_name
            ORDER BY SUM(cost_usd) DESC NULLS LAST
        """)).fetchall()
        by_model = [
            ModelTokenStats(
                model_name=r[0],
                prompt_tokens=int(r[1]),
                completion_tokens=int(r[2]),
                total_tokens=int(r[1]) + int(r[2]),
                cost_usd=float(r[3]),
                message_count=int(r[4]),
            )
            for r in model_rows
        ]
    except Exception:
        by_model = []

    # Per-user breakdown
    try:
        user_rows = session.execute(text("""
            SELECT
                u.id,
                u.email_address,
                u.user_name,
                COALESCE(SUM(m.prompt_tokens), 0),
                COALESCE(SUM(m.completion_tokens), 0),
                COALESCE(SUM(m.cost_usd), 0),
                COUNT(m.id)
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            JOIN users u ON c.user_id = u.id
            WHERE m.role = 'assistant' AND m.model_name IS NOT NULL
            GROUP BY u.id, u.email_address, u.user_name
            ORDER BY SUM(m.cost_usd) DESC NULLS LAST
            LIMIT 100
        """)).fetchall()
        by_user = [
            UserTokenStats(
                user_id=int(r[0]),
                email=r[1],
                full_name=r[2],
                prompt_tokens=int(r[3]),
                completion_tokens=int(r[4]),
                total_tokens=int(r[3]) + int(r[4]),
                cost_usd=float(r[5]),
                message_count=int(r[6]),
            )
            for r in user_rows
        ]
    except Exception:
        by_user = []

    # Daily breakdown for selected period
    from_date = datetime.utcnow() - timedelta(days=days)
    try:
        daily_rows = session.execute(text("""
            SELECT
                DATE(created_at) as day,
                COALESCE(SUM(prompt_tokens), 0),
                COALESCE(SUM(completion_tokens), 0),
                COALESCE(SUM(cost_usd), 0)
            FROM messages
            WHERE role = 'assistant'
              AND model_name IS NOT NULL
              AND created_at >= :from_date
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """), {"from_date": from_date}).fetchall()
        daily_map = {str(r[0]): r for r in daily_rows}
    except Exception:
        daily_map = {}

    daily: list[DailyTokenStats] = []
    for i in range(days, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).date()
        ds = str(d)
        r = daily_map.get(ds)
        pt = int(r[1]) if r else 0
        ct = int(r[2]) if r else 0
        daily.append(DailyTokenStats(
            date=ds,
            prompt_tokens=pt,
            completion_tokens=ct,
            total_tokens=pt + ct,
            cost_usd=float(r[3]) if r else 0.0,
        ))

    logger.info("[ADMIN] Token economy requested by admin_id=%d, days=%d", admin_id, days)

    return TokenEconomyResponse(
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
        total_tokens=total_prompt + total_completion,
        total_cost_usd=total_cost,
        tracked_messages=tracked_msgs,
        by_model=by_model,
        by_user=by_user,
        daily=daily,
    )
