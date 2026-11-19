
import uuid

import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserPublic,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
        ),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(
            payload.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    from datetime import datetime, timezone

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        token_payload = decode_access_token(
            payload.refresh_token
        )

        if token_payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        subject = token_payload.get("sub")

        if not subject:
            raise ValueError("Missing subject")

        user_id = uuid.UUID(subject)

    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or unavailable",
        )

    return build_token_response(user)


@router.get("/me", response_model=UserPublic)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserPublic(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
    )
