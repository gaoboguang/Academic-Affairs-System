from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.core.bootstrap import ensure_runtime_directories
from app.core.config import Settings
from app.exporters.templates import generate_import_templates
from app.main import create_app
from app.models import AppUser, Base
from app.services.bootstrap import seed_demo_data, seed_reference_data


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / "data"
    return Settings(
        data_dir=data_dir,
        db_path=data_dir / "test.db",
        allowed_origins=["http://127.0.0.1:5173"],
        debug=False,
    )


@pytest.fixture()
def app(test_settings: Settings):
    app = create_app(test_settings)
    ensure_runtime_directories(test_settings)
    Base.metadata.create_all(app.state.db.engine)
    generate_import_templates(test_settings)
    with app.state.db.session_scope() as session:
        seed_reference_data(session)
        seed_demo_data(session)
        session.add(
            AppUser(
                username="admin",
                display_name="测试管理员",
                role="admin",
                password_hash=hash_password("AdminPass123!"),
                must_change_password=False,
            )
        )
    yield app
    app.state.db.dispose()


@pytest.fixture()
def anonymous_client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def auth_client(app) -> TestClient:
    client = TestClient(app)
    response = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert response.status_code == 200
    client.headers.update({"X-CSRF-Token": response.json()["csrf_token"]})
    return client


@pytest.fixture()
def client(auth_client) -> TestClient:
    return auth_client
