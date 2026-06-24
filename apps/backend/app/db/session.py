from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseManager:
    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        *,
        attach_databases: Mapping[str, Path] | None = None,
    ) -> None:
        self.database_url = database_url
        self.attach_databases: dict[str, Path] = {
            alias: Path(path) for alias, path in (attach_databases or {}).items()
        }
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=echo,
            future=True,
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        self._configure_sqlite()

    def _configure_sqlite(self) -> None:
        if not self.database_url.startswith("sqlite"):
            return

        attach_databases = self.attach_databases

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            for alias, path in attach_databases.items():
                cursor.execute(
                    f"ATTACH DATABASE '{str(path).replace(chr(39), chr(39) * 2)}' AS {alias}"
                )
            cursor.close()

    def initialize(self) -> None:
        with self.engine.connect():
            return

    @contextmanager
    def session_scope(self) -> Session:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()


def get_request_db(request) -> DatabaseManager:  # type: ignore[no-untyped-def]
    return request.app.state.db

