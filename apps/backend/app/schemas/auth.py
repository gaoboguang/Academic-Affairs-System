from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel

UserRole = Literal["admin", "teacher"]


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("请输入账号")
        return normalized


class ChangePasswordPayload(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("密码首尾不能包含空格")
        if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("密码至少包含字母和数字")
        return value


class AppUserRead(ORMModel):
    id: int
    username: str
    display_name: str
    role: UserRole
    teacher_id: int | None = None
    teacher_name: str | None = None
    must_change_password: bool
    failed_login_count: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    extra_class_ids: list[int] = Field(default_factory=list)
    effective_class_ids: list[int] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    user: AppUserRead
    permissions: list[str] = Field(default_factory=list)
    csrf_token: str


class CurrentUserResponse(BaseModel):
    user: AppUserRead
    permissions: list[str] = Field(default_factory=list)
    csrf_token: str


class AdminUserCreatePayload(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=100)
    role: UserRole
    teacher_id: int | None = None
    extra_class_ids: list[int] = Field(default_factory=list)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("请输入账号")
        return normalized

    @field_validator("display_name")
    @classmethod
    def trim_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("请输入姓名")
        return normalized


class AdminUserUpdatePayload(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    role: UserRole
    teacher_id: int | None = None
    extra_class_ids: list[int] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("display_name")
    @classmethod
    def trim_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("请输入姓名")
        return normalized


class AdminUserCreateResponse(BaseModel):
    user: AppUserRead
    temporary_password: str


class AdminUserResetPasswordResponse(BaseModel):
    user: AppUserRead
    temporary_password: str
