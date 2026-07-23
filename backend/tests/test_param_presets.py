import os
import pytest
import json


@pytest.fixture(autouse=True)
def _isolate_param_presets(monkeypatch):
    """确保 PARAM_PRESETS_FILE 也指向临时目录（conftest 只 monkeypatch 了 storage 顶层属性）"""
    import app.storage.param_presets as pp_mod
    from app.storage import DATA_DIR as test_data_dir
    monkeypatch.setattr(pp_mod, "PARAM_PRESETS_FILE", os.path.join(test_data_dir, "param_presets.json"))


def test_list_empty_returns_default(client):
    """首次无文件时应自动创建默认预设"""
    resp = client.get("/api/param-presets")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    assert len(data["data"]) >= 1
    default = [p for p in data["data"] if p.get("is_default")]
    assert len(default) == 1
    assert default[0]["temperature"] == 0.7
    assert default[0]["max_tokens"] == 4096
    assert default[0]["top_p"] == 1.0


def test_create_param_preset(client):
    resp = client.post("/api/param-presets", json={
        "name": "创意模式",
        "temperature": 0.9,
        "max_tokens": 2048,
        "top_p": 0.95,
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    preset = data["data"]
    assert preset["name"] == "创意模式"
    assert preset["temperature"] == 0.9
    assert preset["max_tokens"] == 2048
    assert preset["top_p"] == 0.95
    assert "id" in preset


def test_create_param_preset_validation(client):
    """测试参数范围校验"""
    # 空名称
    resp = client.post("/api/param-presets", json={"name": "", "temperature": 0.7, "max_tokens": 4096, "top_p": 1.0})
    assert resp.get_json()["code"] != 0

    # temperature 超出范围
    resp = client.post("/api/param-presets", json={"name": "test", "temperature": 3.0, "max_tokens": 4096, "top_p": 1.0})
    assert resp.get_json()["code"] != 0

    # top_p 超出范围
    resp = client.post("/api/param-presets", json={"name": "test", "temperature": 0.7, "max_tokens": 4096, "top_p": 2.0})
    assert resp.get_json()["code"] != 0


def test_delete_default_blocked(client):
    """不能删除默认预设"""
    resp = client.get("/api/param-presets")
    default_id = [p["id"] for p in resp.get_json()["data"] if p["is_default"]][0]
    resp = client.delete(f"/api/param-presets/{default_id}")
    assert resp.get_json()["code"] == 409


def test_set_default(client):
    """设为默认"""
    # 创建一条非默认
    resp = client.post("/api/param-presets", json={
        "name": "测试",
        "temperature": 0.5,
        "max_tokens": 100,
        "top_p": 0.8,
    })
    preset_id = resp.get_json()["data"]["id"]

    # 设为默认
    resp = client.put(f"/api/param-presets/{preset_id}/default")
    assert resp.status_code == 200
    assert resp.get_json()["code"] == 0

    # 验证只有它是默认
    resp = client.get("/api/param-presets")
    defaults = [p for p in resp.get_json()["data"] if p["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == preset_id
