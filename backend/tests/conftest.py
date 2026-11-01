import os
import tempfile

_tmp = tempfile.mkdtemp()
# Set TEST_DATABASE_URL to run against Postgres; defaults to a throwaway SQLite file.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["MELA_PASSCODE"] = "1234"
os.environ["SESSION_SECRET"] = "test-secret-at-least-16"
os.environ["COOKIE_SECURE"] = "false"
os.environ.pop("YOUTUBE_API_KEY", None)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

HERE = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(scope="session", autouse=True)
def migrate():
    cfg = Config(os.path.join(HERE, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(HERE, "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture
def db():
    from app.db import SessionLocal
    from app.models import CookLog, GroceryItem, Photo, Recipe

    s = SessionLocal()
    for model in (GroceryItem, CookLog, Recipe, Photo):
        s.query(model).delete()
    s.commit()
    yield s
    s.close()


@pytest.fixture
def client(db):
    from app.main import app

    c = TestClient(app)
    r = c.post("/api/auth/login", json={"member": "Mei", "passcode": "1234"})
    assert r.status_code == 200
    return c
