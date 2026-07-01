from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from fastapi import HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import Settings
from app.core.security import (
    generate_csrf_token,
    generate_session_token,
    generate_temporary_password,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.importers.base import (
    RowError,
    build_error_preview,
    build_row_error,
    read_template_rows,
    resolve_import_status,
    save_error_report,
)
from app.models import AppSession, AppUser, AppUserClassScope, SchoolClass, Teacher, TeachingAssignment
from app.repositories.system import write_audit_log
from app.schemas.auth import (
    AdminUserBatchImportCreatedAccount,
    AdminUserBatchImportResponse,
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
from app.utils.parsers import clean_text

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

TEACHER_ACCOUNT_IMPORT_HEADERS = ["账号", "显示名称", "教师工号", "教师姓名", "额外可访问班级"]


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


def _clean_import_text(value: object) -> str | None:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return clean_text(value)


def _exception_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    return str(exc)


def _split_import_values(value: object) -> list[str]:
    text = _clean_import_text(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r"[、,，;；|\n\r]+", text) if item.strip()]


def _resolve_teacher_for_account_import(session: Session, row: dict[str, object]) -> Teacher:
    teacher_no = _clean_import_text(row.get("教师工号"))
    teacher_name = _clean_import_text(row.get("教师姓名"))
    if not teacher_no and not teacher_name:
        raise ValueError("教师工号或教师姓名不能为空")

    if teacher_no:
        teacher = session.scalar(select(Teacher).where(Teacher.teacher_no == teacher_no))
        if not teacher:
            raise ValueError(f"教师工号不存在: {teacher_no}")
        if teacher_name and teacher.name != teacher_name:
            raise ValueError(f"教师工号与姓名不匹配: {teacher_no} / {teacher_name}")
        return teacher

    matches = session.scalars(select(Teacher).where(Teacher.name == teacher_name)).all()
    if not matches:
        raise ValueError(f"教师姓名不存在: {teacher_name}")
    if len(matches) > 1:
        raise ValueError(f"教师姓名不唯一: {teacher_name}，请填写教师工号")
    return matches[0]


def _build_class_lookup(session: Session) -> dict[str, list[int]]:
    lookup: dict[str, list[int]] = {}
    classes = session.scalars(
        select(SchoolClass)
        .options(joinedload(SchoolClass.grade))
        .where(SchoolClass.is_active.is_(True))
    ).all()
    for school_class in classes:
        grade_name = school_class.grade.name if school_class.grade else ""
        keys = {
            str(school_class.id),
            school_class.name,
            f"{grade_name}{school_class.name}",
            f"{grade_name} {school_class.name}",
        }
        for key in keys:
            if key:
                lookup.setdefault(key, []).append(school_class.id)
    return lookup


def _resolve_import_class_ids(class_lookup: dict[str, list[int]], value: object) -> list[int]:
    class_ids: list[int] = []
    for item in _split_import_values(value):
        matched_ids = class_lookup.get(item, [])
        if not matched_ids:
            raise ValueError(f"额外可访问班级不存在: {item}")
        unique_ids = sorted(set(matched_ids))
        if len(unique_ids) > 1:
            raise ValueError(f"额外可访问班级不唯一: {item}，请填写年级+班级或班级ID")
        class_ids.append(unique_ids[0])
    return sorted(set(class_ids))


def import_teacher_accounts(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
    strategy: str,
    context: AuthContext,
) -> AdminUserBatchImportResponse:
    if strategy not in {"skip_existing", "create"}:
        raise HTTPException(status_code=400, detail="账号导入策略不支持")

    headers, rows = read_template_rows(content)
    if headers[: len(TEACHER_ACCOUNT_IMPORT_HEADERS)] != TEACHER_ACCOUNT_IMPORT_HEADERS:
        raise HTTPException(status_code=400, detail="教师账号导入模板表头不匹配，请先下载系统模板。")

    success_rows = 0
    failed_rows = 0
    skipped_rows = 0
    created_rows = 0
    row_errors: list[RowError] = []
    created_accounts: list[AdminUserBatchImportCreatedAccount] = []
    class_lookup = _build_class_lookup(session)

    for row_number, row_values in rows:
        savepoint = session.begin_nested()
        try:
            username = _clean_import_text(row_values.get("账号"))
            if not username:
                raise ValueError("账号不能为空")
            teacher = _resolve_teacher_for_account_import(session, row_values)
            display_name = _clean_import_text(row_values.get("显示名称")) or teacher.name
            extra_class_ids = _resolve_import_class_ids(class_lookup, row_values.get("额外可访问班级"))
            if _load_user_by_username(session, username):
                if strategy == "skip_existing":
                    savepoint.rollback()
                    skipped_rows += 1
                    continue
                raise ValueError(f"账号已存在: {username}")

            response = create_user(
                session,
                AdminUserCreatePayload(
                    username=username,
                    display_name=display_name,
                    role="teacher",
                    teacher_id=teacher.id,
                    extra_class_ids=extra_class_ids,
                ),
                context,
            )
            savepoint.commit()
            created_rows += 1
            success_rows += 1
            created_accounts.append(
                AdminUserBatchImportCreatedAccount(
                    username=response.user.username,
                    display_name=response.user.display_name,
                    teacher_no=teacher.teacher_no,
                    teacher_name=teacher.name,
                    temporary_password=response.temporary_password,
                )
            )
        except Exception as exc:
            if savepoint.is_active:
                savepoint.rollback()
            failed_rows += 1
            row_errors.append(
                build_row_error(
                    row_number=row_number,
                    values=row_values,
                    message=_exception_message(exc),
                )
            )

    error_report_path = save_error_report(
        settings=settings,
        prefix="teacher_account_import_errors",
        headers=TEACHER_ACCOUNT_IMPORT_HEADERS,
        errors=row_errors,
    )
    return AdminUserBatchImportResponse(
        status=resolve_import_status(
            total_rows=len(rows),
            success_rows=success_rows,
            failed_rows=failed_rows,
        ),
        total_rows=len(rows),
        success_rows=success_rows,
        failed_rows=failed_rows,
        skipped_rows=skipped_rows,
        created_rows=created_rows,
        updated_rows=0,
        error_report_path=error_report_path,
        error_preview=build_error_preview(row_errors),
        notice_preview=["临时密码只在本次导入结果中显示，请及时记录。"] if created_accounts else [],
        message=f"教师账号导入完成，成功 {success_rows} 条，失败 {failed_rows} 条，跳过 {skipped_rows} 条。",
        created_accounts=created_accounts,
    )


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
