import json
from app.database import init_db, get_db


def _setup_db(app):
    with app.app_context():
        init_db()
        db = get_db()
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")
        db.execute("DELETE FROM settings")
        db.commit()

def _create_setting(client):
    resp = client.post("/api/settings", json={
        "name": "Test", "api_url": "https://api.openai.com/v1", "api_key": "sk-test"
    })
    data = json.loads(resp.get_data(as_text=True))["data"]
    client.put(f"/api/settings/{data['id']}/default")
    return data


class TestConversationsList:
    def test_empty(self, client, app):
        _setup_db(app)
        resp = client.get("/api/conversations")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"] == []

    def test_returns_sorted(self, client, app):
        _setup_db(app)
        client.post("/api/conversations", json={"title": "B"})
        client.post("/api/conversations", json={"title": "A"})

        resp = client.get("/api/conversations")
        items = json.loads(resp.get_data(as_text=True))["data"]
        assert len(items) == 2
        assert items[0]["title"] == "A"
        assert items[1]["title"] == "B"


class TestConversationsCreate:
    def test_create_default_title(self, client, app):
        _setup_db(app)
        resp = client.post("/api/conversations", json={})
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["title"] == "新对话"


class TestConversationsDetail:
    def test_detail_with_messages(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={"title": "Test"})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.get(f"/api/conversations/{cid}")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["title"] == "Test"
        assert body["data"]["messages"] == []

    def test_detail_not_found(self, client, app):
        _setup_db(app)
        resp = client.get("/api/conversations/no-such-id")
        assert json.loads(resp.get_data(as_text=True))["code"] == 404


class TestConversationsDelete:
    def test_delete_success(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.delete(f"/api/conversations/{cid}")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0

        list_resp = client.get("/api/conversations")
        assert json.loads(list_resp.get_data(as_text=True))["data"] == []


class TestEditMessage:
    def test_edit_user_message(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        with app.app_context():
            db = get_db()
            import uuid
            mid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'user', ?, ?)",
                (mid, cid, "original", "2026-01-01T00:00:00Z"),
            )
            db.commit()

        resp = client.put(f"/api/conversations/{cid}/messages/{mid}", json={
            "content": "edited"
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["content"] == "edited"


class TestStop:
    def test_stop_returns_ok(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.post(f"/api/conversations/{cid}/stop")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0
