from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session, get_settings, require_admin
from app.core.config import Settings
from app.schemas.auth import (
    AdminUserCreatePayload,
    AdminUserCreateResponse,
    AdminUserResetPasswordResponse,
    AdminUserUpdatePayload,
    AppUserRead,
    AuthResponse,
    ChangePasswordPayload,
    CurrentUserResponse,
    LoginPayload,
)
from app.services import auth as service
from app.services.auth import AuthContext

router = APIRouter(tags=["auth"])


def _set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.auth_cookie_name,
        token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="strict",
        max_age=settings.auth_session_expire_hours * 60 * 60,
        path="/",
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/", samesite="strict")


@router.post("/auth/login", response_model=AuthResponse)
def login(
    payload: LoginPayload,
    request: Request,
    response: Response,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    token, auth_response = service.login(session, settings, payload, request)
    _set_session_cookie(response, settings, token)
    return auth_response


@router.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    service.logout(session, request.cookies.get(settings.auth_cookie_name))
    _clear_session_cookie(response, settings)
    return {"message": "已退出登录"}


@router.get("/auth/me", response_model=CurrentUserResponse)
def get_me(
    current_user: AuthContext = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CurrentUserResponse:
    return service.current_user_response(session, current_user)


@router.post("/auth/change-password", response_model=CurrentUserResponse)
def change_password(
    payload: ChangePasswordPayload,
    current_user: AuthContext = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CurrentUserResponse:
    return service.change_password(session, payload, current_user)


@router.get("/admin/users", response_model=list[AppUserRead])
def list_users(
    _: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> list[AppUserRead]:
    return service.list_users(session)


@router.post("/admin/users", response_model=AdminUserCreateResponse)
def create_user(
    payload: AdminUserCreatePayload,
    current_user: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> AdminUserCreateResponse:
    return service.create_user(session, payload, current_user)


@router.put("/admin/users/{user_id}", response_model=AppUserRead)
def update_user(
    user_id: int,
    payload: AdminUserUpdatePayload,
    current_user: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> AppUserRead:
    return service.update_user(session, user_id, payload, current_user)


@router.post("/admin/users/{user_id}/reset-password", response_model=AdminUserResetPasswordResponse)
def reset_password(
    user_id: int,
    current_user: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> AdminUserResetPasswordResponse:
    return service.reset_password(session, user_id, current_user)


@router.post("/admin/users/{user_id}/disable", response_model=AppUserRead)
def disable_user(
    user_id: int,
    current_user: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> AppUserRead:
    return service.set_user_active(session, user_id, is_active=False, context=current_user)


@router.post("/admin/users/{user_id}/enable", response_model=AppUserRead)
def enable_user(
    user_id: int,
    current_user: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> AppUserRead:
    return service.set_user_active(session, user_id, is_active=True, context=current_user)
