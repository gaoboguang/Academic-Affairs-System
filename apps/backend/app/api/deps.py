from __future__ import annotations

from collections.abc import Callable, Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.auth import AuthContext


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db_session(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.db
    with db.session_scope() as session:
        yield session


def get_gaokao_db_session(request: Request) -> Generator[Session | None, None, None]:
    db = getattr(request.app.state, "gaokao_db", None)
    if db is None:
        yield None
        return
    with db.session_scope() as session:
        yield session


def get_current_user(request: Request) -> AuthContext:
    context = getattr(request.state, "auth_context", None)
    if context is None:
        raise HTTPException(status_code=401, detail="请先登录")
    return context


def require_admin(current_user: AuthContext = Depends(get_current_user)) -> AuthContext:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def require_permission(permission: str) -> Callable[[AuthContext], AuthContext]:
    def _dependency(current_user: AuthContext = Depends(get_current_user)) -> AuthContext:
        if current_user.is_admin or permission in current_user.permissions:
            return current_user
        raise HTTPException(status_code=403, detail="无权执行该操作")

    return _dependency
