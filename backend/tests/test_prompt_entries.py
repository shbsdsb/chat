import json
import os
import pytest


# ── isolation fixtures ──────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_prompt_entries(monkeypatch):
    """Ensure prompt_entries uses the temp data directory."""
    import app.storage.prompt_entries as pe_mod
    from app.storage import DATA_DIR as test_data_dir
    monkeypatch.setattr(
        pe_mod, "PROMPT_ENTRIES_DIR",
        os.path.join(test_data_dir, "prompt_entries"),
    )


@pytest.fixture
def test_app(client):
    """Alias for the Flask test client — matches the brief's convention."""
    return client


# ── helpers ─────────────────────────────────────────────────────────

def _create_preset(test_app, name="测试预设"):
    """辅助：创建一个参数预设并返回其 id。"""
    resp = test_app.post(
        "/api/param-presets",
        json={"name": name, "temperature": 0.5, "max_tokens": 2048, "top_p": 0.9},
    )
    return resp.get_json()["data"]["id"]


# ── tests ───────────────────────────────────────────────────────────

class TestPromptEntriesCRUD:
    def test_list_empty(self, test_app):
        """空列表返回 []。"""
        preset_id = _create_preset(test_app)
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"] == []

    def test_create_entry(self, test_app):
        """创建条目成功。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post(
            "/api/prompt-entries",
            json={"preset_id": preset_id, "name": "🏃 测试角色"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == 0
        entry = data["data"]
        assert entry["name"] == "🏃 测试角色"
        assert entry["enabled"] is True
        assert entry["content"] == ""
        assert entry["role"] is None
        assert "id" in entry
        assert "order" in entry

    def test_create_entry_missing_name(self, test_app):
        """缺少名称返回 400。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post(
            "/api/prompt-entries",
            json={"preset_id": preset_id, "name": ""},
        )
        assert resp.status_code == 200
        assert resp.get_json()["code"] != 0

    def test_create_entry_invalid_preset(self, test_app):
        """无效的 preset_id 返回 404。"""
        resp = test_app.post(
            "/api/prompt-entries",
            json={"preset_id": "nonexistent", "name": "测试"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["code"] != 0

    def test_list_ordered(self, test_app):
        """列表按 order 排序返回。"""
        preset_id = _create_preset(test_app)
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "B"})
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "A"})
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "C"})

        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        entries = resp.get_json()["data"]
        names = [e["name"] for e in entries]
        assert names == ["B", "A", "C"]

    def test_update_entry(self, test_app):
        """更新条目名称和开关。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "原始名称"})
        entry_id = resp.get_json()["data"]["id"]

        resp = test_app.put(
            f"/api/prompt-entries/{entry_id}",
            json={"preset_id": preset_id, "name": "新名称", "enabled": False},
        )
        assert resp.status_code == 200
        entry = resp.get_json()["data"]
        assert entry["name"] == "新名称"
        assert entry["enabled"] is False

    def test_update_content_role(self, test_app):
        """更新条目内容与角色。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "测试"})
        entry_id = resp.get_json()["data"]["id"]

        resp = test_app.put(
            f"/api/prompt-entries/{entry_id}",
            json={"preset_id": preset_id, "content": "你是助手", "role": "system"},
        )
        assert resp.status_code == 200
        entry = resp.get_json()["data"]
        assert entry["content"] == "你是助手"
        assert entry["role"] == "system"

    def test_delete_entry(self, test_app):
        """删除条目成功。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "待删除"})
        entry_id = resp.get_json()["data"]["id"]

        resp = test_app.delete(f"/api/prompt-entries/{entry_id}?preset_id={preset_id}")
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0

        # 验证已删除
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        assert resp.get_json()["data"] == []

    def test_reorder(self, test_app):
        """批量排序。"""
        preset_id = _create_preset(test_app)
        ids = []
        for name in ["A", "B", "C"]:
            resp = test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": name})
            ids.append(resp.get_json()["data"]["id"])

        # 反序
        reversed_ids = list(reversed(ids))
        resp = test_app.put(
            "/api/prompt-entries/reorder",
            json={"preset_id": preset_id, "ids": reversed_ids},
        )
        assert resp.status_code == 200

        # 验证顺序
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        entries = resp.get_json()["data"]
        assert [e["id"] for e in entries] == reversed_ids

    def test_cascade_delete_with_preset(self, test_app):
        """删除参数预设时联动清理提示词条目。"""
        preset_id = _create_preset(test_app)
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "测试"})

        # 删除参数预设
        test_app.delete(f"/api/param-presets/{preset_id}")

        # 条目文件应该不存在或返回空
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        # preset 不存在了，应返回 404
        assert resp.get_json()["code"] != 0
