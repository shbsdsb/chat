"""
端到端测试：预设创建 → 会话创建 → 消息编辑 → 删除
不涉及真实 AI 调用（chat/regenerate 使用 mock）。
"""
import json
import uuid
import os
import glob
from app.storage import init_storage, add_message, CONVERSATIONS_FILE, SETTINGS_FILE


def _setup_storage(app):
    with app.app_context():
        init_storage()
        import app.storage as storage_module
        storage_module._write_json(CONVERSATIONS_FILE, [])
        storage_module._write_json(SETTINGS_FILE, [])
        msg_dir = storage_module.MESSAGES_DIR
        for f in glob.glob(os.path.join(msg_dir, "*.json")):
            os.remove(f)


class TestFullWorkflow:
    def test_settings_crud_workflow(self, client, app):
        """完整预设管理流程。"""
        _setup_storage(app)

        # 1. 创建预设
        r = client.post("/api/settings", json={
            "name": "OpenAI", "api_url": "https://api.openai.com/v1", "api_key": "sk-test"
        })
        assert json.loads(r.get_data(as_text=True))["code"] == 0
        sid = json.loads(r.get_data(as_text=True))["data"]["id"]

        # 2. 设为默认
        r = client.put(f"/api/settings/{sid}/default")
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 3. 更新预设
        r = client.put(f"/api/settings/{sid}", json={
            "name": "OpenAI Updated", "api_url": "https://api.openai.com/v1",
            "api_key": "", "model": "gpt-4o",
        })
        body = json.loads(r.get_data(as_text=True))
        assert body["data"]["name"] == "OpenAI Updated"

        # 4. 创建第二个预设
        r = client.post("/api/settings", json={
            "name": "Ollama", "api_url": "http://localhost:11434/v1", "api_key": ""
        })
        sid2 = json.loads(r.get_data(as_text=True))["data"]["id"]

        # 5. 删除非默认预设
        r = client.delete(f"/api/settings/{sid2}")
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 6. 列表应剩 1 个
        r = client.get("/api/settings")
        assert len(json.loads(r.get_data(as_text=True))["data"]) == 1

    def test_conversations_workflow(self, client, app):
        """完整对话 CRUD 流程（不涉及 AI）。"""
        _setup_storage(app)

        # 创建两个对话
        r1 = client.post("/api/conversations", json={"title": "测试对话"})
        cid = json.loads(r1.get_data(as_text=True))["data"]["id"]
        client.post("/api/conversations", json={"title": "另一个对话"})

        # 列表应有 2 个
        r = client.get("/api/conversations")
        assert len(json.loads(r.get_data(as_text=True))["data"]) == 2

        # 查看详情
        r = client.get(f"/api/conversations/{cid}")
        body = json.loads(r.get_data(as_text=True))
        assert body["data"]["title"] == "测试对话"
        assert body["data"]["messages"] == []

        # 删除
        r = client.delete(f"/api/conversations/{cid}")
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 列表应剩 1 个
        r = client.get("/api/conversations")
        assert len(json.loads(r.get_data(as_text=True))["data"]) == 1

    def test_edit_message_truncates_following(self, client, app):
        """编辑消息后，后续消息应被删除。"""
        _setup_storage(app)

        # 创建会话并插入多条消息
        r = client.post("/api/conversations", json={"title": "Test"})
        cid = json.loads(r.get_data(as_text=True))["data"]["id"]

        m1 = str(uuid.uuid4())
        m2 = str(uuid.uuid4())
        m3 = str(uuid.uuid4())

        add_message({
            "id": m1, "conversation_id": cid, "role": "user",
            "content": "问题1", "reasoning_content": "", "created_at": "2026-01-01T00:00:01Z",
        })
        add_message({
            "id": m2, "conversation_id": cid, "role": "assistant",
            "content": "回答1", "reasoning_content": "", "created_at": "2026-01-01T00:00:02Z",
        })
        add_message({
            "id": m3, "conversation_id": cid, "role": "user",
            "content": "问题2", "reasoning_content": "", "created_at": "2026-01-01T00:00:03Z",
        })

        # 编辑第一条消息
        r = client.put(f"/api/conversations/{cid}/messages/{m1}", json={
            "content": "修改后的问题"
        })
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 详情应只剩 1 条（编辑后的 m1，m2 和 m3 被截断删除）
        r = client.get(f"/api/conversations/{cid}")
        body = json.loads(r.get_data(as_text=True))
        assert len(body["data"]["messages"]) == 1
        assert body["data"]["messages"][0]["content"] == "修改后的问题"
