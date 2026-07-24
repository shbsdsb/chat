import os
import pytest
import json


@pytest.fixture(autouse=True)
def _isolate_css_presets(monkeypatch):
    """确保 CSS_PRESETS_FILE 指向临时目录"""
    import app.storage.css_presets as cp_mod
    from app.storage import DATA_DIR as test_data_dir
    monkeypatch.setattr(cp_mod, "CSS_PRESETS_FILE", os.path.join(test_data_dir, "css_presets.json"))


def test_list_empty_returns_default(client):
    """首次无文件时应自动创建默认预设"""
    resp = client.get("/api/css-presets")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    assert len(data["data"]) >= 1
    default = [p for p in data["data"] if p.get("is_default")]
    assert len(default) == 1
    assert default[0]["name"] == "默认"
    assert default[0]["content"] == ""


def test_create_css_preset(client):
    resp = client.post("/api/css-presets", json={
        "name": "暗夜主题",
        "content": "body { background: #1a1a2e; }",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    preset = data["data"]
    assert preset["name"] == "暗夜主题"
    assert preset["content"] == "body { background: #1a1a2e; }"
    assert "id" in preset


def test_create_css_preset_validation(client):
    """空名称应被拒绝"""
    resp = client.post("/api/css-presets", json={"name": "", "content": ""})
    assert resp.get_json()["code"] != 0


def test_update_css_preset(client):
    """更新名称和内容"""
    resp = client.post("/api/css-presets", json={"name": "测试", "content": ""})
    preset_id = resp.get_json()["data"]["id"]

    resp = client.put(f"/api/css-presets/{preset_id}", json={
        "name": "改名",
        "content": "h1 { color: red; }",
    })
    assert resp.status_code == 200
    updated = resp.get_json()["data"]
    assert updated["name"] == "改名"
    assert updated["content"] == "h1 { color: red; }"


def test_update_partial(client):
    """只更新名称，内容保持不变"""
    resp = client.post("/api/css-presets", json={"name": "测试", "content": "original"})
    preset_id = resp.get_json()["data"]["id"]

    resp = client.put(f"/api/css-presets/{preset_id}", json={"name": "改名"})
    updated = resp.get_json()["data"]
    assert updated["name"] == "改名"
    assert updated["content"] == "original"


def test_delete_default_blocked(client):
    """不能删除默认预设"""
    resp = client.get("/api/css-presets")
    default_id = [p["id"] for p in resp.get_json()["data"] if p["is_default"]][0]
    resp = client.delete(f"/api/css-presets/{default_id}")
    assert resp.get_json()["code"] == 409


def test_delete_non_default_success(client):
    """非默认预设可正常删除"""
    resp = client.post("/api/css-presets", json={"name": "可删除"})
    preset_id = resp.get_json()["data"]["id"]

    resp = client.delete(f"/api/css-presets/{preset_id}")
    assert resp.get_json()["code"] == 0

    # 确认已删除
    resp = client.get("/api/css-presets")
    ids = [p["id"] for p in resp.get_json()["data"]]
    assert preset_id not in ids


def test_set_default(client):
    """设为默认"""
    resp = client.post("/api/css-presets", json={"name": "新默认", "content": "test"})
    preset_id = resp.get_json()["data"]["id"]

    resp = client.put(f"/api/css-presets/{preset_id}/default")
    assert resp.status_code == 200
    assert resp.get_json()["code"] == 0

    # 验证只有它一个默认
    resp = client.get("/api/css-presets")
    defaults = [p for p in resp.get_json()["data"] if p["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == preset_id


def test_delete_after_switch_default(client):
    """切换默认后，原默认可删除"""
    # 获取当前默认
    resp = client.get("/api/css-presets")
    old_default = [p for p in resp.get_json()["data"] if p["is_default"]][0]

    # 创建新预设并设为默认
    resp = client.post("/api/css-presets", json={"name": "新默认"})
    new_id = resp.get_json()["data"]["id"]
    client.put(f"/api/css-presets/{new_id}/default")

    # 旧默认现在可以删除
    resp = client.delete(f"/api/css-presets/{old_default['id']}")
    assert resp.get_json()["code"] == 0
