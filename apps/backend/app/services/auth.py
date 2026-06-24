from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.security import (
    generate_csrf_token,
    generate_session_token,
    generate_temporary_password,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.models import AppSession, AppUser, AppUserClassScope, SchoolClass, Teacher, TeachingAssignment
from app.repositories.system import write_audit_log
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

ADMIN_PERMISSIONS = [
    "admin:*",
    "accounts:manage",
    "base:manage",
    "students:read",
    "students:write",
    "teachers:manage",
    "scores:import",
    "analytics:read",
    "reports:read",
    "system:manage",
]

TEACHER_PERMISSIONS = [
    "dashboard:read",
    "students:read",
    "students:write",
    "scores:import",
    "analytics:read",
    "reports:read",
]

PUBLIC_API_PATHS = {
    "/api/auth/login",
    "/api/system/health",
}


@dataclass(frozen=True)
class AuthContext:
    user_id: int
    username: str
    display_name: str
    role: str
    teacher_id: int | None
    permissions: tuple[str, ...]
    class_scope_ids: tuple[int, ...]
    csrf_token: str
    session_id: int
    client_ip: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def get_permissions_for_role(role: str) -> list[str]:
    if role == "admin":
        return ADMIN_PERMISSIONS.copy()
    if role == "teacher":
        return TEACHER_PERMISSIONS.copy()
    return []


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def _teacher_class_scope_ids(session: Session, user: AppUser) -> list[int]:
    if user.role != "teacher" or user.teacher_id is None:
        return []
    class_ids: set[int] = set()
    class_ids.update(
        session.scalars(
            select(SchoolClass.id).where(
                SchoolClass.head_teacher_id == user.teacher_id,
                SchoolClass.is_active.is_(True),
            )
        ).all()
    )
    class_ids.update(
        session.scalars(
            select(TeachingAssignment.class_id).where(
                TeachingAssignment.teacher_id == user.teacher_id,
                TeachingAssignment.class_id.is_not(None),
                TeachingAssignment.is_active.is_(True),
            )
        ).all()
    )
    class_ids.update(
        session.scalars(
            select(AppUserClassScope.class_id).where(
                AppUserClassScope.user_id == user.id,
                AppUserClassScope.is_active.is_(True),
            )
        ).all()
    )
    return sorted(class_id for class_id in class_ids if class_id is not None)


def _extra_class_scope_ids(user: AppUser) -> list[int]:
    return sorted(scope.class_id for scope in user.class_scopes if scope.is_active)


def serialize_user(session: Session, user: AppUser) -> AppUserRead:
    teacher_name = user.teacher.name if user.teacher else None
    return AppUserRead(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,  # type: ignore[arg-type]
        teacher_id=user.teacher_id,
        teacher_name=teacher_name,
        must_change_password=user.must_change_password,
        failed_login_count=user.failed_login_count,
        locked_until=user.locked_until,
        last_login_at=user.last_login_at,
        extra_class_ids=_extra_class_scope_ids(user),
        effective_class_ids=_teacher_class_scope_ids(session, user),
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _load_user_by_username(session: Session, username: str) -> AppUser | None:
    return session.scalar(
        select(AppUser)
        .options(selectinload(AppUser.teacher), selectinload(AppUser.class_scopes))
        .where(AppUser.username == _normalize_username(username))
    )


def authenticate_user(session: Session, payload: LoginPayload) -> AppUser:
    user = _load_user_by_username(session, payload.username)
    generic_error = HTTPException(status_code=401, detail="账号或密码错误")
    if user is None:
        verify_password(payload.password, None)
        raise generic_error
    now = datetime.now()
    if not user.is_active or (user.locked_until and user.locked_until > now):
        verify_password(payload.password, user.password_hash)
        raise generic_error
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= 5:
            user.locked_until = now + timedelta(minutes=15)
        raise generic_error
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    session.flush()
    return user


def create_session(session: Session, settings: Settings, user: AppUser, request: Request) -> tuple[str, AppSession]:
    token = generate_session_token()
    session_row = AppSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        csrf_token=generate_csrf_token(),
        expires_at=datetime.now() + timedelta(hours=settings.auth_session_expire_hours),
        last_seen_at=datetime.now(),
        client_ip=_client_ip(request),
        user_agent=request.headers.get("user-agent", "")[:255] or None,
    )
    session.add(session_row)
    session.flush()
    return token, session_row


def login(session: Session, settings: Settings, payload: LoginPayload, request: Request) -> tuple[str, AuthResponse]:
    user = authenticate_user(session, payload)
    token, session_row = create_session(session, settings, user, request)
    write_audit_log(
        session,
        module="auth",
        action="login",
        target_type="app_user",
        target_id=str(user.id),
        actor_user_id=user.id,
        actor_username=user.username,
        client_ip=_client_ip(request),
        detail_json={"role": user.role},
    )
    return (
        token,
        AuthResponse(
            user=serialize_user(session, user),
            permissions=get_permissions_for_role(user.role),
            csrf_token=session_row.csrf_token,
        ),
    )


def build_context_from_token(session: Session, token: str, client_ip: str | None = None) -> AuthContext | None:
    token_hash = hash_session_token(token)
    now = datetime.now()
    session_row = session.scalar(
        select(AppSession)
        .options(
            selectinload(AppSession.user).selectinload(AppUser.teacher),
            selectinload(AppSession.user).selectinload(AppUser.class_scopes),
        )
        .where(
            AppSession.token_hash == token_hash,
            AppSession.revoked_at.is_(None),
            AppSession.expires_at > now,
        )
    )
    if not session_row or not session_row.user or not session_row.user.is_active:
        return None
    user = session_row.user
    session_row.last_seen_at = now
    return AuthContext(
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        teacher_id=user.teacher_id,
        permissions=tuple(get_permissions_for_role(user.role)),
        class_scope_ids=tuple(_teacher_class_scope_ids(session, user)),
        csrf_token=session_row.csrf_token,
        session_id=session_row.id,
        client_ip=client_ip,
    )


def current_user_response(session: Session, context: AuthContext) -> CurrentUserResponse:
    user = session.scalar(
        select(AppUser)
        .options(selectinload(AppUser.teacher), selectinload(AppUser.class_scopes))
        .where(AppUser.id == context.user_id)
    )
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效")
    return CurrentUserResponse(
        user=serialize_user(session, user),
        permissions=list(context.permissions),
        csrf_token=context.csrf_token,
    )


def logout(session: Session, token: str | None) -> None:
    if not token:
        return
    session.execute(
        update(AppSession)
        .where(AppSession.token_hash == hash_session_token(token), AppSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now())
    )


def revoke_user_sessions(session: Session, user_id: int, *, except_session_id: int | None = None) -> None:
    stmt = update(AppSession).where(AppSession.user_id == user_id, AppSession.revoked_at.is_(None))
    if except_session_id is not None:
        stmt = stmt.where(AppSession.id != except_session_id)
    session.execute(stmt.values(revoked_at=datetime.now()))


def change_password(
    session: Session,
    payload: ChangePasswordPayload,
    context: AuthContext,
) -> CurrentUserResponse:
    user = session.get(AppUser, context.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效")
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.failed_login_count = 0
    user.locked_until = None
    revoke_user_sessions(session, user.id, except_session_id=context.session_id)
    write_audit_log(
        session,
        module="auth",
        action="change_password",
        target_type="app_user",
        target_id=str(user.id),
        actor_user_id=context.user_id,
        actor_username=context.username,
        client_ip=context.client_ip,
    )
    session.flush()
    return current_user_response(session, context)


def _validate_teacher_role(session: Session, role: str, teacher_id: int | None) -> None:
    if role not in {"admin", "teacher"}:
        raise HTTPException(status_code=400, detail="账号角色不支持")
    if role == "teacher":
        if teacher_id is None:
            raise HTTPException(status_code=400, detail="教师账号必须关联教师档案")
        if not session.get(Teacher, teacher_id):
            raise HTTPException(status_code=404, detail="教师档案不存在")


def _replace_extra_class_scopes(session: Session, user: AppUser, class_ids: list[int]) -> None:
    unique_ids = sorted(set(class_ids))
    if unique_ids:
        existing_count = len(
            session.scalars(
                select(SchoolClass.id).where(SchoolClass.id.in_(unique_ids), SchoolClass.is_active.is_(True))
            ).all()
        )
        if existing_count != len(unique_ids):
            raise HTTPException(status_code=404, detail="可访问班级不存在或已停用")
    user.class_scopes.clear()
    for class_id in unique_ids:
        user.class_scopes.append(AppUserClassScope(class_id=class_id))
    session.flush()


def list_users(session: Session) -> list[AppUserRead]:
    users = session.scalars(
        select(AppUser)
        .options(selectinload(AppUser.teacher), selectinload(AppUser.class_scopes))
        .order_by(AppUser.role, AppUser.username)
    ).all()
    return [serialize_user(session, user) for user in users]


def create_user(
    session: Session,
    payload: AdminUserCreatePayload,
    context: AuthContext,
) -> AdminUserCreateResponse:
    if _load_user_by_username(session, payload.username):
        raise HTTPException(status_code=400, detail="账号已存在")
    _validate_teacher_role(session, payload.role, payload.teacher_id)
    temp_password = generate_temporary_password()
    user = AppUser(
        username=_normalize_username(payload.username),
        display_name=payload.display_name,
        role=payload.role,
        teacher_id=payload.teacher_id,
        password_hash=hash_password(temp_password),
        must_change_password=True,
    )
    session.add(user)
    session.flush()
    _replace_extra_class_scopes(session, user, payload.extra_class_ids)
    write_audit_log(
        session,
        module="admin_users",
        action="create",
        target_type="app_user",
        target_id=str(user.id),
        actor_user_id=context.user_id,
        actor_username=context.username,
        client_ip=context.client_ip,
        detail_json={"username": user.username, "role": user.role},
    )
    return AdminUserCreateResponse(user=serialize_user(session, user), temporary_password=temp_password)


def update_user(
    session: Session,
    user_id: int,
    payload: AdminUserUpdatePayload,
    context: AuthContext,
) -> AppUserRead:
    user = session.scalar(
        select(AppUser)
        .options(selectinload(AppUser.teacher), selectinload(AppUser.class_scopes))
        .where(AppUser.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    _validate_teacher_role(session, payload.role, payload.teacher_id)
    user.display_name = payload.display_name
    user.role = payload.role
    user.teacher_id = payload.teacher_id
    user.is_active = payload.is_active
    _replace_extra_class_scopes(session, user, payload.extra_class_ids)
    if not user.is_active:
        revoke_user_sessions(session, user.id)
    write_audit_log(
        session,
        module="admin_users",
        action="update",
        target_type="app_user",
        target_id=str(user.id),
        actor_user_id=context.user_id,
        actor_username=context.username,
        client_ip=context.client_ip,
        detail_json={"username": user.username, "role": user.role, "is_active": user.is_active},
    )
    return serialize_user(session, user)


def reset_password(
    session: Session,
    user_id: int,
    context: AuthContext,
) -> AdminUserResetPasswordResponse:
    user = session.scalar(
        select(AppUser)
        .options(selectinload(AppUser.teacher), selectinload(AppUser.class_scopes))
        .where(AppUser.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    temp_password = generate_temporary_password()
    user.password_hash = hash_password(temp_password)
    user.must_change_password = True
    user.failed_login_count = 0
    user.locked_until = None
    revoke_user_sessions(session, user.id)
    write_audit_log(
        session,
        module="admin_users",
        action="reset_password",
        target_type="app_user",
        target_id=str(user.id),
        actor_user_id=context.user_id,
        actor_username=context.username,
        client_ip=context.client_ip,
        detail_json={"username": user.username},
    )
    return AdminUserResetPasswordResponse(user=serialize_user(session, user), temporary_password=temp_password)


def set_user_active(
    session: Session,
    user_id: int,
    *,
    is_active: bool,
    context: AuthContext,
) -> AppUserRead:
    user = session.scalar(
        select(AppUser)
        .options(selectinload(AppUser.teacher), selectinload(AppUser.class_scopes))
        .where(AppUser.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    if user.id == context.user_id and not is_active:
        raise HTTPException(status_code=400, detail="不能停用当前登录账号")
    user.is_active = is_active
    if not is_active:
        revoke_user_sessions(session, user.id)
    write_audit_log(
        session,
        module="admin_users",
        action="enable" if is_active else "disable",
        target_type="app_user",
        target_id=str(user.id),
        actor_user_id=context.user_id,
        actor_username=context.username,
        client_ip=context.client_ip,
        detail_json={"username": user.username},
    )
    return serialize_user(session, user)
