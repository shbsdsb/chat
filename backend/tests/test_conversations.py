import json
import uuid
from app.storage import init_storage, add_message, CONVERSATIONS_FILE, SETTINGS_FILE


def _setup_storage(app):
    with app.app_context():
        init_storage()
        # 清空：直接覆盖为空列表
        import app.storage as storage_module
        storage_module._write_json(CONVERSATIONS_FILE, [])
        storage_module._write_json(SETTINGS_FILE, [])
        # 清空消息目录
        import os, glob
        msg_dir = storage_module.MESSAGES_DIR
        for f in glob.glob(os.path.join(msg_dir, "*.json")):
            os.remove(f)


def _create_setting(client):
    resp = client.post("/api/settings", json={
        "name": "Test", "api_url": "https://api.openai.com/v1", "api_key": "sk-test"
    })
    data = json.loads(resp.get_data(as_text=True))["data"]
    client.put(f"/api/settings/{data['id']}/default")
    return data


class TestConversationsList:
    def test_empty(self, client, app):
        _setup_storage(app)
        resp = client.get("/api/conversations")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"] == []

    def test_returns_sorted(self, client, app):
        _setup_storage(app)
        client.post("/api/conversations", json={"title": "B"})
        client.post("/api/conversations", json={"title": "A"})

        resp = client.get("/api/conversations")
        items = json.loads(resp.get_data(as_text=True))["data"]
        assert len(items) == 2
        assert items[0]["title"] == "A"
        assert items[1]["title"] == "B"


class TestConversationsCreate:
    def test_create_default_title(self, client, app):
        _setup_storage(app)
        resp = client.post("/api/conversations", json={})
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["title"] == "新对话"


class TestConversationsDetail:
    def test_detail_with_messages(self, client, app):
        _setup_storage(app)
        create_resp = client.post("/api/conversations", json={"title": "Test"})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.get(f"/api/conversations/{cid}")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["title"] == "Test"
        assert body["data"]["messages"] == []

    def test_detail_not_found(self, client, app):
        _setup_storage(app)
        resp = client.get("/api/conversations/no-such-id")
        assert json.loads(resp.get_data(as_text=True))["code"] == 404


class TestConversationsDelete:
    def test_delete_success(self, client, app):
        _setup_storage(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.delete(f"/api/conversations/{cid}")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0

        list_resp = client.get("/api/conversations")
        assert json.loads(list_resp.get_data(as_text=True))["data"] == []


class TestEditMessage:
    def test_edit_user_message(self, client, app):
        _setup_storage(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        mid = str(uuid.uuid4())
        add_message({
            "id": mid,
            "conversation_id": cid,
            "role": "user",
            "content": "original",
            "reasoning_content": "",
            "created_at": "2026-01-01T00:00:00Z",
        })

        resp = client.put(f"/api/conversations/{cid}/messages/{mid}", json={
            "content": "edited"
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["content"] == "edited"


class TestStop:
    def test_stop_returns_ok(self, client, app):
        _setup_storage(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.post(f"/api/conversations/{cid}/stop")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0
