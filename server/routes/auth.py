from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from database.database import get_session
from models.user import User
from schemas.user import (
    LoginRequest,
    LoginResponse,
    OnboardingRequest,
    OnboardingResponse,
    RegisterRequest,
    RegisterResponse,
)
from security.security import create_access_token, decode_access_token, hash_password, verify_password

router = APIRouter(prefix="/v1", tags=["auth"])
_bearer = HTTPBearer()


def _get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> int:
    payload = decode_access_token(credentials.credentials)
    try:
        return int(payload["id"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email_address == body.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email_address=body.email,
        user_name=body.username,
        phone_number=body.phone_number,
        password_hash=hash_password(body.password),
        status="active",
        is_onboarded=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return RegisterResponse(id=user.id, message="Registration successful")


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email_address == body.email)).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    token = create_access_token({
        "sub": str(user.id),
        "id": user.id,
        "is_onboarded": user.is_onboarded,
        "status": user.status,
    })

    return LoginResponse(access_token=token)


@router.post("/onboarding", response_model=OnboardingResponse)
def onboarding(
    body: OnboardingRequest,
    user_id: int = Depends(_get_current_user_id),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_onboarded:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already onboarded")

    user.trade_role = body.trade_role.value
    user.user_type = body.user_type
    user.company_name = body.company_name
    user.target_region = body.target_region
    user.language_preference = body.language_preference
    user.is_onboarded = True

    session.add(user)
    session.commit()

    return OnboardingResponse(message="Onboarding complete", is_onboarded=True)
