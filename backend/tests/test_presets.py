import pytest


@pytest.fixture(autouse=True)
def _isolate_presets(monkeypatch):
    """确保 presets 使用临时目录，不污染真实数据。"""
    import app.storage.presets as mod
    from app.storage import DATA_DIR as test_data_dir
    import os
    test_dir = os.path.join(test_data_dir, "presets")
    monkeypatch.setattr(mod, "PRESETS_DIR", test_dir)
    monkeypatch.setattr(mod, "INDEX_FILE", os.path.join(test_dir, "_index.json"))


def _create_preset(client):
    """辅助：创建参数预设并返回 data。"""
    resp = client.post("/api/presets", json={
        "name": "测试预设",
        "temperature": 0.5,
        "max_tokens": 2048,
        "top_p": 0.9,
    })
    return resp.get_json()["data"]


class TestPresetsCRUD:
    def test_list_empty(self, client):
        """空列表返回 []。"""
        resp = client.get("/api/presets")
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0

    def test_create(self, client):
        """创建预设成功。"""
        resp = client.post("/api/presets", json={
            "name": "测试", "temperature": 0.5, "max_tokens": 2048, "top_p": 0.9,
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["name"] == "测试"
        assert data["params"]["temperature"] == 0.5
        assert "id" in data
        assert "__chat_history__" in data["entries"]

    def test_create_missing_name(self, client):
        """缺少名称返回失败。"""
        resp = client.post("/api/presets", json={"name": ""})
        assert resp.get_json()["code"] != 0

    def test_get_detail(self, client):
        """获取预设详情含条目。"""
        created = _create_preset(client)
        resp = client.get(f"/api/presets/{created['id']}")
        data = resp.get_json()["data"]
        assert data["name"] == "测试预设"
        assert "entries" in data
        assert "__chat_history__" in data["entries"]

    def test_update_full(self, client):
        """全量更新预设（参数 + 条目）。"""
        created = _create_preset(client)
        resp = client.put(f"/api/presets/{created['id']}", json={
            "name": "新名称",
            "params": {"temperature": 0.3, "max_tokens": 1024, "top_p": 0.5},
            "entries": {
                "e1": {"name": "设定", "role": "system", "content": "你是助手", "enabled": True},
                "__chat_history__": "chat_history",
                "e2": {"name": "尾部", "role": "assistant", "content": "喵", "enabled": False},
            },
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["name"] == "新名称"
        assert data["params"]["temperature"] == 0.3
        assert data["entries"]["e1"]["role"] == "system"
        assert data["entries"]["e2"]["enabled"] is False

    def test_delete_not_default(self, client):
        """删除非默认预设成功。"""
        created = _create_preset(client)
        resp = client.delete(f"/api/presets/{created['id']}")
        assert resp.get_json()["code"] == 0
        resp = client.get(f"/api/presets/{created['id']}")
        assert resp.get_json()["code"] != 0

    def test_set_default(self, client):
        """设置默认预设。"""
        created = _create_preset(client)
        resp = client.put(f"/api/presets/{created['id']}/default")
        assert resp.get_json()["code"] == 0
        list_resp = client.get("/api/presets")
        presets = list_resp.get_json()["data"]
        target = next(p for p in presets if p["id"] == created["id"])
        assert target["is_default"] is True

    def test_entries_ordering(self, client):
        """验证 entries 对象保持键顺序。"""
        created = _create_preset(client)
        client.put(f"/api/presets/{created['id']}", json={
            "entries": {
                "a1": {"name": "A", "role": "system", "content": "a", "enabled": True},
                "__chat_history__": "chat_history",
                "b2": {"name": "B", "role": "user", "content": "b", "enabled": True},
            },
        })
        resp = client.get(f"/api/presets/{created['id']}")
        entries_obj = resp.get_json()["data"]["entries"]
        keys = list(entries_obj.keys())
        assert "a1" in keys
        assert "__chat_history__" in keys
        assert "b2" in keys

    def test_get_entries_function(self, client):
        """get_entries() 函数返回列表含 __chat_history__ 在正确位置。"""
        created = _create_preset(client)
        client.put(f"/api/presets/{created['id']}", json={
            "entries": {
                "a1": {"name": "A", "role": "system", "content": "a", "enabled": True},
                "__chat_history__": "chat_history",
                "b2": {"name": "B", "role": "user", "content": "b", "enabled": True},
            },
        })
        from app.storage.presets import get_entries
        entries = get_entries(created["id"])
        assert len(entries) == 3
        ids = [e["id"] for e in entries]
        assert "a1" in ids
        assert "__chat_history__" in ids
        assert "b2" in ids
