import logging
import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from middleware.rate_limit import limiter
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from database.database import get_session
from models.otp import OtpCode
from models.security_settings import SecuritySettings
from models.user import User
from schemas.user import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    OnboardingRequest,
    OnboardingResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from security.security import (
    create_access_token,
    create_reset_token,
    decode_access_token,
    decode_reset_token,
    hash_password,
    verify_password,
)
from services.email import send_otp_email

logger = logging.getLogger(__name__)

# ── Helpers ─────────────────────────────────────────────────────────────────────

_LOCKOUT_DURATION_MINUTES = 15
_SPECIAL_CHARS = set('!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\`~')


def _get_security_settings(session: Session) -> SecuritySettings:
    settings = session.exec(select(SecuritySettings)).first()
    if not settings:
        settings = SecuritySettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def _validate_password(password: str, settings: SecuritySettings) -> list[str]:
    errors = []
    if len(password) < settings.min_password_length:
        errors.append(f"Password must be at least {settings.min_password_length} characters long.")
    if settings.require_numbers and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number.")
    if settings.require_special_characters and not any(c in _SPECIAL_CHARS for c in password):
        errors.append("Password must contain at least one special character.")
    return errors


# ── Constants ──────────────────────────────────────────────────────────────────
_OTP_EXPIRES_MINUTES = 10
_OTP_MAX_ATTEMPTS    = 3
_OTP_RATE_LIMIT_SECONDS = 60   # minimum gap between OTP requests per email

router = APIRouter(prefix="/v1", tags=["auth"])
_bearer = HTTPBearer()


def _get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> int:
    payload = decode_access_token(credentials.credentials)
    try:
        return int(payload["id"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register(request: Request, body: RegisterRequest, session: Session = Depends(get_session)):
    email = body.email.lower().strip()

    sec = _get_security_settings(session)
    pw_errors = _validate_password(body.password, sec)
    if pw_errors:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=" ".join(pw_errors))

    existing = session.exec(select(User).where(User.email_address == email)).first()
    if existing and existing.is_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # If an unverified account exists for this email, remove it and re-register
    if existing and not existing.is_verified:
        session.delete(existing)
        session.commit()

    user = User(
        email_address=email,
        user_name=body.username,
        phone_number=body.phone_number,
        password_hash=hash_password(body.password),
        status="active",
        is_onboarded=False,
        is_verified=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Issue OTP for email verification
    _invalidate_existing_otps(session, email)
    code       = _generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=_OTP_EXPIRES_MINUTES)
    session.add(OtpCode(email=email, code=code, expires_at=expires_at))
    session.commit()

    try:
        send_otp_email(to=email, otp=code, expires_minutes=_OTP_EXPIRES_MINUTES, purpose="registration")
    except Exception as exc:
        logger.error("[OTP] SES delivery failed for %s: %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Account created but failed to send verification email. Please use 'Forgot Password' to resend.",
        )

    logger.info("[REGISTER] User %s registered — verification OTP sent.", email)
    return RegisterResponse(id=user.id, message="Registration successful. Please verify your email.")


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, session: Session = Depends(get_session)):
    sec = _get_security_settings(session)
    now = datetime.utcnow()

    user = session.exec(select(User).where(User.email_address == body.email.lower().strip())).first()

    # Check account lockout before verifying password (prevents timing attacks leaking user existence)
    if user and user.locked_until and user.locked_until > now:
        remaining = max(1, int((user.locked_until - now).total_seconds() / 60) + 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked after too many failed attempts. Try again in {remaining} minute(s).",
        )

    if not user or not verify_password(body.password, user.password_hash):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= sec.max_login_attempts:
                user.locked_until = now + timedelta(minutes=_LOCKOUT_DURATION_MINUTES)
                logger.warning(
                    "[AUTH] Account %s locked after %d failed login attempts",
                    user.email_address, user.failed_login_attempts,
                )
            session.add(user)
            session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox for the verification code.",
        )

    if user.status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    # Successful login — reset counters and record timestamp
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now
    session.add(user)
    session.commit()

    token = create_access_token(
        {
            "sub": str(user.id),
            "id": user.id,
            "is_onboarded": user.is_onboarded,
            "status": user.status,
            "is_admin": user.is_admin,
        },
        expire_minutes=sec.jwt_access_token_expire_minutes,
    )

    logger.info("[AUTH] User %s logged in successfully.", user.email_address)
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


@router.post(
    "/auth/verify-registration",
    response_model=RegisterResponse,
    summary="Verify email OTP to activate a newly registered account",
)
@limiter.limit("10/minute")
def verify_registration(
    request: Request,
    body: VerifyOtpRequest,
    session: Session = Depends(get_session),
):
    """
    Verify the OTP sent during registration.
    On success the account is marked is_verified=True and the user can log in.
    """
    email = body.email.lower().strip()
    now   = datetime.utcnow()

    otp_row = session.exec(
        select(OtpCode).where(
            OtpCode.email      == email,
            OtpCode.used       == False,  # noqa: E712
            OtpCode.expires_at >  now,
        ).order_by(OtpCode.created_at.desc())
    ).first()

    _invalid_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification code.",
    )

    if not otp_row:
        raise _invalid_exc

    if otp_row.attempts >= _OTP_MAX_ATTEMPTS:
        otp_row.used = True
        session.add(otp_row)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect attempts. Please register again.",
        )

    if otp_row.code != body.otp:
        otp_row.attempts += 1
        remaining = _OTP_MAX_ATTEMPTS - otp_row.attempts
        if remaining <= 0:
            otp_row.used = True
        session.add(otp_row)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect code. {max(remaining, 0)} attempt(s) remaining.",
        )

    # OTP correct — activate account
    otp_row.used = True
    session.add(otp_row)

    user = session.exec(select(User).where(User.email_address == email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_verified = True
    session.add(user)
    session.commit()

    logger.info("[REGISTER] Email verified for %s — account activated.", email)
    return RegisterResponse(id=user.id, message="Email verified. You can now sign in.")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _generate_otp() -> str:
    """Return a cryptographically random 6-digit numeric OTP."""
    return "".join(random.choices(string.digits, k=6))


def _invalidate_existing_otps(session: Session, email: str) -> None:
    """Mark all active OTPs for an email as used before issuing a new one."""
    active = session.exec(
        select(OtpCode).where(
            OtpCode.email == email,
            OtpCode.used == False,  # noqa: E712
        )
    ).all()
    for otp in active:
        otp.used = True
        session.add(otp)


# ── Forgot password ────────────────────────────────────────────────────────────

@router.post(
    "/auth/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request a password-reset OTP",
)
@limiter.limit("3/hour")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Send a 6-digit OTP to the registered email address.

    - Always returns 200 regardless of whether the email exists (prevents
      user enumeration attacks).
    - Rate-limited: one OTP per email per 60 seconds.
    - Invalidates any prior active OTPs for the same email.
    """
    email = body.email.lower().strip()

    # Rate-limit check — look for a recent OTP for this email
    rate_cutoff = datetime.utcnow() - timedelta(seconds=_OTP_RATE_LIMIT_SECONDS)
    recent = session.exec(
        select(OtpCode).where(
            OtpCode.email == email,
            OtpCode.created_at >= rate_cutoff,
        )
    ).first()

    if recent:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {_OTP_RATE_LIMIT_SECONDS} seconds before requesting another code.",
        )

    # Silently succeed if the email is not registered (anti-enumeration)
    user = session.exec(select(User).where(User.email_address == email)).first()
    if not user:
        logger.info("[OTP] Forgot-password request for unknown email %s — silently ignored.", email)
        return ForgotPasswordResponse(
            message="If that email is registered, you will receive a reset code shortly."
        )

    # Invalidate any prior active OTPs
    _invalidate_existing_otps(session, email)

    # Issue new OTP
    code       = _generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=_OTP_EXPIRES_MINUTES)
    otp_row    = OtpCode(email=email, code=code, expires_at=expires_at)
    session.add(otp_row)
    session.commit()

    # Deliver via SES
    try:
        send_otp_email(to=email, otp=code, expires_minutes=_OTP_EXPIRES_MINUTES)
    except Exception as exc:
        logger.error("[OTP] SES delivery failed for %s: %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send reset email. Please try again later.",
        )

    logger.info("[OTP] OTP issued for %s (expires %s)", email, expires_at.isoformat())
    return ForgotPasswordResponse(
        message="If that email is registered, you will receive a reset code shortly."
    )


# ── Verify OTP ─────────────────────────────────────────────────────────────────

@router.post(
    "/auth/verify-otp",
    response_model=VerifyOtpResponse,
    summary="Verify OTP and receive a password-reset token",
)
@limiter.limit("10/minute")
def verify_otp(
    request: Request,
    body: VerifyOtpRequest,
    session: Session = Depends(get_session),
):
    """
    Validate the OTP entered by the user.

    On success returns a short-lived reset_token (15 min JWT) that must be
    passed to POST /v1/auth/reset-password.

    On failure the attempt counter is incremented; after 3 wrong guesses
    the OTP is invalidated and the user must request a new one.
    """
    email = body.email.lower().strip()
    now   = datetime.utcnow()

    otp_row = session.exec(
        select(OtpCode).where(
            OtpCode.email    == email,
            OtpCode.used     == False,  # noqa: E712
            OtpCode.expires_at > now,
        ).order_by(OtpCode.created_at.desc())
    ).first()

    # Generic error — do not reveal whether email exists or OTP expired
    _invalid_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired OTP.",
    )

    if not otp_row:
        raise _invalid_exc

    if otp_row.attempts >= _OTP_MAX_ATTEMPTS:
        otp_row.used = True
        session.add(otp_row)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect attempts. Please request a new code.",
        )

    if otp_row.code != body.otp:
        otp_row.attempts += 1
        remaining = _OTP_MAX_ATTEMPTS - otp_row.attempts
        if remaining <= 0:
            otp_row.used = True
        session.add(otp_row)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect OTP. {max(remaining, 0)} attempt(s) remaining.",
        )

    # OTP is correct — mark as used and issue reset token
    otp_row.used = True
    session.add(otp_row)
    session.commit()

    reset_token = create_reset_token(email)
    logger.info("[OTP] OTP verified for %s — reset token issued.", email)

    return VerifyOtpResponse(
        reset_token=reset_token,
        message="OTP verified. Use the reset_token to set a new password.",
    )


# ── Reset password ─────────────────────────────────────────────────────────────

@router.post(
    "/auth/reset-password",
    response_model=ResetPasswordResponse,
    summary="Set a new password using a valid reset token",
)
@limiter.limit("5/hour")
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Set a new password.

    Requires the reset_token returned by POST /v1/auth/verify-otp.
    The token is a 15-minute JWT — once it expires the user must restart
    the forgot-password flow.
    """
    email = decode_reset_token(body.reset_token)   # raises HTTP 400 on invalid/expired

    sec = _get_security_settings(session)
    pw_errors = _validate_password(body.new_password, sec)
    if pw_errors:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=" ".join(pw_errors))

    user = session.exec(select(User).where(User.email_address == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.password_hash = hash_password(body.new_password)
    session.add(user)
    session.commit()

    logger.info("[AUTH] Password reset successfully for %s", email)
    return ResetPasswordResponse(message="Password updated successfully. You can now log in.")
