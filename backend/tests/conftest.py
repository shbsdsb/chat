import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
import app.database as db_module


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Use a temp database for testing so production data is never touched."""
    test_db = str(tmp_path / "test_chat.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db)


@pytest.fixture
def app(setup_test_db):
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()
