#!/usr/bin/env python
from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import DatabaseManager
from app.models import AppUser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="初始化或重置本地教务工具管理员账号。")
    parser.add_argument("--username", default="admin", help="管理员账号，默认 admin。")
    parser.add_argument("--display-name", default="系统管理员", help="管理员显示名称。")
    parser.add_argument("--password", help="管理员密码；不传时会安全输入。")
    parser.add_argument("--reset-password", action="store_true", help="账号已存在时重置密码。")
    return parser.parse_args()


def read_password(args: argparse.Namespace) -> str:
    if args.password:
        return args.password
    password = getpass.getpass("请输入管理员密码：")
    confirm = getpass.getpass("请再次输入管理员密码：")
    if password != confirm:
        print("两次密码不一致。", file=sys.stderr)
        raise SystemExit(1)
    return password


def validate_password(password: str) -> None:
    if len(password) < 8:
        print("密码至少 8 位。", file=sys.stderr)
        raise SystemExit(1)
    if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        print("密码至少包含字母和数字。", file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    args = parse_args()
    username = args.username.strip().lower()
    display_name = args.display_name.strip() or username
    if not username:
        print("账号不能为空。", file=sys.stderr)
        raise SystemExit(1)
    password = read_password(args)
    validate_password(password)

    settings = get_settings()
    db = DatabaseManager(settings.database_url, settings.debug)
    with db.session_scope() as session:
        user = session.scalar(select(AppUser).where(AppUser.username == username))
        if user and not args.reset_password:
            print(f"管理员账号已存在：{username}。如需重置密码，请追加 --reset-password。")
            return
        if user:
            user.display_name = display_name
            user.role = "admin"
            user.password_hash = hash_password(password)
            user.must_change_password = False
            user.is_active = True
            user.failed_login_count = 0
            user.locked_until = None
            print(f"已重置管理员账号：{username}")
            return
        session.add(
            AppUser(
                username=username,
                display_name=display_name,
                role="admin",
                password_hash=hash_password(password),
                must_change_password=False,
            )
        )
        print(f"已创建管理员账号：{username}")
    db.dispose()


if __name__ == "__main__":
    main()
