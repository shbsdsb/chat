import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
import app.storage as storage_module


@pytest.fixture(autouse=True)
def setup_test_storage(monkeypatch, tmp_path):
    """Use a temp data directory for testing so production data is never touched."""
    test_dir = str(tmp_path / "user_data")
    monkeypatch.setattr(storage_module, "DATA_DIR", test_dir)
    monkeypatch.setattr(storage_module, "CONVERSATIONS_FILE", os.path.join(test_dir, "conversations.json"))
    monkeypatch.setattr(storage_module, "MESSAGES_DIR", os.path.join(test_dir, "messages"))
    monkeypatch.setattr(storage_module, "SETTINGS_FILE", os.path.join(test_dir, "settings.json"))


@pytest.fixture
def app(setup_test_storage):
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()
