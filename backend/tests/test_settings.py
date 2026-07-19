import json
import uuid
from app.database import init_db, get_db


def _setup_db(app):
    with app.app_context():
        init_db()
        db = get_db()
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")
        db.execute("DELETE FROM settings")
        db.commit()


class TestSettingsList:
    def test_empty_list(self, client, app):
        _setup_db(app)
        resp = client.get("/api/settings")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"] == []

    def test_returns_presets(self, client, app):
        _setup_db(app)
        client.post("/api/settings", json={
            "name": "OpenAI", "api_url": "https://api.openai.com/v1", "api_key": "sk-abc"
        })
        client.post("/api/settings", json={
            "name": "Ollama", "api_url": "http://localhost:11434/v1", "api_key": ""
        })

        resp = client.get("/api/settings")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert len(body["data"]) == 2
        for item in body["data"]:
            assert "****" in item["api_key"] or item["api_key"] == ""


class TestSettingsCreate:
    def test_create_success(self, client, app):
        _setup_db(app)
        resp = client.post("/api/settings", json={
            "name": "OpenAI",
            "api_url": "https://api.openai.com/v1",
            "api_key": "sk-abc123",
            "model": "gpt-4o",
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["name"] == "OpenAI"
        assert body["data"]["api_key"] == "sk-a****"

    def test_create_missing_name(self, client, app):
        _setup_db(app)
        resp = client.post("/api/settings", json={
            "api_url": "https://api.openai.com/v1",
            "api_key": "sk-abc",
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 400


class TestSettingsUpdate:
    def test_update_success(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/settings", json={
            "name": "Old", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        sid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.put(f"/api/settings/{sid}", json={
            "name": "New", "api_url": "https://b.com", "api_key": "", "model": "gpt-4o"
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["name"] == "New"
        assert body["data"]["api_url"] == "https://b.com"
        assert "****" in body["data"]["api_key"]

    def test_update_nonexistent(self, client, app):
        _setup_db(app)
        resp = client.put("/api/settings/no-such-id", json={
            "name": "X", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        assert json.loads(resp.get_data(as_text=True))["code"] == 404


class TestSettingsDelete:
    def test_delete_success(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/settings", json={
            "name": "X", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        sid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.delete(f"/api/settings/{sid}")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0

        list_resp = client.get("/api/settings")
        assert len(json.loads(list_resp.get_data(as_text=True))["data"]) == 0

    def test_cannot_delete_default(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/settings", json={
            "name": "Default", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        sid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]
        client.put(f"/api/settings/{sid}/default")

        resp = client.delete(f"/api/settings/{sid}")
        assert json.loads(resp.get_data(as_text=True))["code"] == 409


class TestSettingsSetDefault:
    def test_set_default(self, client, app):
        _setup_db(app)
        r1 = client.post("/api/settings", json={
            "name": "A", "api_url": "https://a.com", "api_key": "sk-a"
        })
        r2 = client.post("/api/settings", json={
            "name": "B", "api_url": "https://b.com", "api_key": "sk-b"
        })
        id_a = json.loads(r1.get_data(as_text=True))["data"]["id"]
        id_b = json.loads(r2.get_data(as_text=True))["data"]["id"]

        client.put(f"/api/settings/{id_a}/default")
        resp = client.put(f"/api/settings/{id_b}/default")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0

        items = json.loads(client.get("/api/settings").get_data(as_text=True))["data"]
        defaults = [i for i in items if i["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["id"] == id_b
