import os
from datetime import datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

_ph = PasswordHasher()

SECRET_KEY         = os.getenv("SECRET_KEY")
ALGORITHM          = "HS256"
TOKEN_EXPIRE_HOURS = 24
RESET_TOKEN_EXPIRE_MINUTES = 15


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def create_access_token(payload: dict, expire_minutes: int | None = None) -> str:
    data = payload.copy()
    minutes = expire_minutes if expire_minutes is not None else TOKEN_EXPIRE_HOURS * 60
    data["exp"] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def create_reset_token(email: str) -> str:
    """
    Create a short-lived JWT used exclusively for the reset-password step.
    The 'purpose' claim prevents this token from being used as an access token.
    """
    payload = {
        "sub": email,
        "purpose": "password_reset",
        "exp": datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_reset_token(token: str) -> str:
    """
    Decode and validate a reset token. Returns the email address.
    Raises HTTP 400 on any validation failure.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new OTP.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token.",
        )

    if payload.get("purpose") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token purpose.",
        )

    return payload["sub"]
