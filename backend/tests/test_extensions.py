import json
import os
import zipfile

import pytest
from app.extensions.registry import (
    get_registry_path, read_registry, write_registry,
    get_extension, add_extension, remove_extension, set_extension_state,
)
from app.extensions.installer import (
    install_from_zip, uninstall_extension,
)


def test_registry_path_under_extensions_dir():
    path = get_registry_path()
    assert path.endswith(os.path.join("user_data", "extensions", ".registry.json"))


def test_read_registry_returns_empty_when_no_file(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    data = read_registry()
    assert data == {"extensions": {}}


def test_read_registry_returns_empty_on_json_decode_error(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    # Write invalid JSON to the registry file
    reg_file.write_text("{invalid json", encoding="utf-8")
    data = read_registry()
    assert data == {"extensions": {}}


def test_write_and_read_registry(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    write_registry({"extensions": {"test-ext": {"enabled": True, "version": "1.0.0"}}})
    data = read_registry()
    assert data["extensions"]["test-ext"]["enabled"] is True


def test_add_extension(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {"version": "1.0.0", "enabled": True, "installed_at": "2026-01-01T00:00:00Z", "install_method": "zip", "permissions_granted": ["hook:chat"]})
    ext = get_extension("test-ext")
    assert ext["version"] == "1.0.0"
    assert ext["enabled"] is True


def test_remove_extension(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {"version": "1.0.0", "enabled": True, "installed_at": "2026-01-01T00:00:00Z", "install_method": "zip", "permissions_granted": []})
    remove_extension("test-ext")
    assert get_extension("test-ext") is None


def test_set_extension_state(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {"version": "1.0.0", "enabled": True, "installed_at": "2026-01-01T00:00:00Z", "install_method": "zip", "permissions_granted": []})
    set_extension_state("test-ext", False)
    assert get_extension("test-ext")["enabled"] is False


# --- Task 2: installer tests ---

def test_install_from_zip(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    os.makedirs(ext_dir)

    # 创建测试 zip
    zip_path = tmp_path / "test-ext.zip"
    manifest = {"id": "test-ext", "name": "Test", "version": "1.0.0",
                "permissions": [], "ext_points": {"backend": [], "frontend": []},
                "min_app_version": "1.0.0"}
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("backend.py", "def on_chat_post_receive(ctx): return None\n")

    result = install_from_zip(str(zip_path))
    assert result[0] == "test-ext"  # (ext_id, name)
    assert os.path.isfile(os.path.join(ext_dir, "test-ext", "manifest.json"))
    assert os.path.isfile(os.path.join(ext_dir, "test-ext", "backend.py"))


def test_install_from_zip_invalid_no_manifest(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("readme.txt", "no manifest here")
    with pytest.raises(ValueError, match="manifest.json"):
        install_from_zip(str(zip_path))


def test_uninstall_extension(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    ext_path = os.path.join(ext_dir, "to-remove")
    os.makedirs(ext_path)
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        f.write("{}")
    uninstall_extension("to-remove")
    assert not os.path.exists(ext_path)


# --- Task 3: permission tests ---

from app.extensions.permissions import check_permission, validate_permissions, VALID_PERMISSIONS


def test_validate_permissions_filters_invalid():
    result = validate_permissions(["hook:chat", "read:conversations", "invalid:perm"])
    assert "hook:chat" in result
    assert "read:conversations" in result
    assert "invalid:perm" not in result


def test_check_permission_granted(tmp_path, monkeypatch):
    from app.extensions.registry import add_extension
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat", "read:conversations"]
    })
    assert check_permission("test-ext", "hook:chat") is True
    assert check_permission("test-ext", "read:world_info") is False


def test_check_permission_disabled_extension(tmp_path, monkeypatch):
    from app.extensions.registry import add_extension
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("disabled-ext", {
        "version": "1.0.0", "enabled": False,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat"]
    })
    assert check_permission("disabled-ext", "hook:chat") is False


# --- Task 4: hook dispatcher tests ---

from app.extensions.hooks import HookDispatcher


class TestHookDispatcher:
    def test_dispatch_calls_registered_handler(self):
        dispatcher = HookDispatcher()
        results = []
        def handler(ctx):
            results.append(ctx["value"])
            return {"meta": {"hit": ctx["value"]}}
        dispatcher.register_hook("test-ext", "chat.post_receive", handler)
        output = dispatcher.dispatch("chat.post_receive", {"value": 42})
        assert results == [42]
        assert output == [{"extension_id": "test-ext", "message_meta": {"hit": 42}}]

    def test_dispatch_multiple_extensions(self):
        dispatcher = HookDispatcher()
        calls = []
        dispatcher.register_hook("ext-a", "chat.post_receive", lambda ctx: calls.append("a"))
        dispatcher.register_hook("ext-b", "chat.post_receive", lambda ctx: calls.append("b"))
        dispatcher.dispatch("chat.post_receive", {})
        assert calls == ["a", "b"]

    def test_dispatch_handler_exception_does_not_block_others(self):
        dispatcher = HookDispatcher()
        calls = []
        def bad_handler(ctx):
            raise RuntimeError("boom")
        dispatcher.register_hook("bad-ext", "chat.post_receive", bad_handler)
        dispatcher.register_hook("good-ext", "chat.post_receive", lambda ctx: calls.append("good"))
        dispatcher.dispatch("chat.post_receive", {})
        assert calls == ["good"]

    def test_unregister_extension_removes_handlers(self):
        dispatcher = HookDispatcher()
        dispatcher.register_hook("test-ext", "chat.post_receive", lambda ctx: None)
        dispatcher.unregister_extension("test-ext")
        output = dispatcher.dispatch("chat.post_receive", {})
        assert output == []

    def test_dispatch_unknown_ext_point(self):
        dispatcher = HookDispatcher()
        output = dispatcher.dispatch("nonexistent", {})
        assert output == []


# --- Task 5: loader tests ---

from app.extensions.loader import load_extension, unload_extension, load_all_enabled


def test_load_extension_registers_hooks(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))

    # 创建扩展目录
    ext_path = os.path.join(ext_dir, "test-loader")
    os.makedirs(ext_path)
    manifest = {"id": "test-loader", "name": "Loader Test", "version": "1.0.0",
                "permissions": ["hook:chat"], "ext_points": {"backend": ["chat.post_receive"]},
                "min_app_version": "1.0.0"}
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        json.dump(manifest, f)
    with open(os.path.join(ext_path, "backend.py"), "w") as f:
        f.write("def on_chat_post_receive(ctx): return {'hit': len(ctx.get('messages', []))}\n")

    # 注册到注册表
    from app.extensions.registry import add_extension, write_registry
    write_registry({"extensions": {}})
    add_extension("test-loader", {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat"]
    })

    from app.extensions.hooks import HookDispatcher
    dispatcher = HookDispatcher()
    result = load_extension("test-loader", dispatcher)
    assert result["status"] == "loaded"

    output = dispatcher.dispatch("chat.post_receive", {"messages": [1, 2, 3]})
    assert len(output) == 1
    assert output[0]["message_meta"]["hit"] == 3


def test_load_extension_missing_backend_py(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))

    ext_path = os.path.join(ext_dir, "no-backend")
    os.makedirs(ext_path)
    manifest = {"id": "no-backend", "name": "No Backend", "version": "1.0.0",
                "permissions": [], "ext_points": {"frontend": ["message_decorator"]},
                "min_app_version": "1.0.0"}
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        json.dump(manifest, f)

    from app.extensions.registry import add_extension, write_registry
    write_registry({"extensions": {}})
    add_extension("no-backend", {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": []
    })

    from app.extensions.hooks import HookDispatcher
    dispatcher = HookDispatcher()
    result = load_extension("no-backend", dispatcher)
    # 纯前端扩展加载应该成功
    assert result["status"] == "loaded"


def test_unload_extension_removes_from_dispatcher(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))

    ext_path = os.path.join(ext_dir, "to-unload")
    os.makedirs(ext_path)
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        json.dump({"id": "to-unload", "name": "X", "version": "1.0.0",
                   "permissions": ["hook:chat"], "ext_points": {"backend": ["chat.post_receive"]},
                   "min_app_version": "1.0.0"}, f)
    with open(os.path.join(ext_path, "backend.py"), "w") as f:
        f.write("def on_chat_post_receive(ctx): return None\n")

    # 注册到注册表
    from app.extensions.registry import add_extension, write_registry
    write_registry({"extensions": {}})
    add_extension("to-unload", {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat"]
    })

    from app.extensions.hooks import HookDispatcher
    dispatcher = HookDispatcher()
    load_extension("to-unload", dispatcher)
    unload_extension("to-unload", dispatcher)
    output = dispatcher.dispatch("chat.post_receive", {})
    assert output == []


# ============================================================
# Task 7: /api/extensions 路由集成测试
# ============================================================

import zipfile
import app.extensions
from app import create_app


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """创建带隔离扩展目录的测试客户端"""
    ext_dir = tmp_path / "extensions"
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    # 重置 ExtensionManager 单例
    import app.extensions
    app.extensions._manager = app.extensions.ExtensionManager()
    app_mock = create_app()
    app_mock.config["TESTING"] = True
    return app_mock.test_client()


class TestListExtensions:
    def test_empty(self, api_client):
        resp = api_client.get("/api/extensions")
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"] == []

    def test_with_installed_extension(self, api_client, tmp_path, monkeypatch):
        # 先通过直接注册表注入一个扩展
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "my-ext"
        ext_path.mkdir(parents=True)
        manifest = {"id": "my-ext", "name": "My Extension", "version": "1.0.0",
                     "description": "A test ext",
                     "permissions": [], "ext_points": {"backend": [], "frontend": ["message_decorator"]},
                     "min_app_version": "1.0.0"}
        (ext_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("my-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.get("/api/extensions")
        data = resp.get_json()
        assert data["code"] == 0
        assert len(data["data"]) == 1
        ext = data["data"][0]
        assert ext["id"] == "my-ext"
        assert ext["name"] == "My Extension"
        assert ext["description"] == "A test ext"
        assert ext["frontend"] is True


class TestInstallExtension:
    def test_install_from_zip_requires_file(self, api_client):
        resp = api_client.post("/api/extensions/install",
                               data={"install_method": "zip"},
                               content_type="multipart/form-data")
        data = resp.get_json()
        assert data["code"] == 400

    def test_install_from_zip_success(self, api_client, tmp_path, monkeypatch):
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        # 创建 zip 文件
        zip_path = tmp_path / "test-ext.zip"
        manifest = {"id": "api-test-ext", "name": "API Test Ext", "version": "1.0.0",
                    "permissions": ["hook:chat"], "ext_points": {"backend": [], "frontend": []},
                    "min_app_version": "1.0.0"}
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("backend.py", "")

        with open(zip_path, "rb") as fh:
            resp = api_client.post("/api/extensions/install",
                                   data={"install_method": "zip", "file": (fh, "test-ext.zip")},
                                   content_type="multipart/form-data")
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["id"] == "api-test-ext"
        assert data["data"]["pending_approval"] is True
        assert "hook:chat" in data["data"]["permissions"]


class TestConfirmExtension:
    def test_confirm_not_found(self, api_client):
        resp = api_client.post("/api/extensions/nonexistent/confirm",
                               json={"permissions": []})
        data = resp.get_json()
        assert data["code"] == 404

    def test_confirm_and_load(self, api_client, tmp_path, monkeypatch):
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        # 准备扩展目录（模拟 install 后的状态）
        ext_path = ext_dir / "confirm-ext"
        ext_path.mkdir(parents=True)
        manifest = {"id": "confirm-ext", "name": "Confirm Test", "version": "1.0.0",
                    "permissions": ["hook:chat"], "ext_points": {"backend": ["chat.post_receive"]},
                    "min_app_version": "1.0.0"}
        (ext_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (ext_path / "backend.py").write_text(
            "def on_chat_post_receive(ctx): return {'handled': True}\n", encoding="utf-8")

        from app.extensions.registry import write_registry
        write_registry({"extensions": {}})

        resp = api_client.post("/api/extensions/confirm-ext/confirm",
                               json={"permissions": ["hook:chat"]})
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["id"] == "confirm-ext"
        assert data["data"]["status"] == "loaded"
        assert "chat.post_receive" in data["data"]["registered_hooks"]


class TestUninstallExtension:
    def test_uninstall_not_found(self, api_client):
        resp = api_client.post("/api/extensions/nonexistent/uninstall")
        data = resp.get_json()
        assert data["code"] == 404

    def test_uninstall_success(self, api_client, tmp_path, monkeypatch):
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        # 准备扩展
        ext_path = ext_dir / "to-uninstall"
        ext_path.mkdir(parents=True)
        (ext_path / "manifest.json").write_text(json.dumps(
            {"id": "to-uninstall", "name": "X", "version": "1.0.0",
             "permissions": [], "ext_points": {"backend": [], "frontend": []},
             "min_app_version": "1.0.0"}), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("to-uninstall", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.post("/api/extensions/to-uninstall/uninstall")
        data = resp.get_json()
        assert data["code"] == 0
        assert "已卸载" in data["message"]

        # 确认注册表已移除
        from app.extensions.registry import get_extension
        assert get_extension("to-uninstall") is None


class TestUpdateExtension:
    def test_update_not_found(self, api_client):
        resp = api_client.post("/api/extensions/nonexistent/update")
        data = resp.get_json()
        assert data["code"] == 404

    def test_update_non_git_rejected(self, api_client, tmp_path, monkeypatch):
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("zip-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.post("/api/extensions/zip-ext/update")
        data = resp.get_json()
        assert data["code"] == 400
        assert "Git" in data["message"]


class TestToggleExtension:
    def test_toggle_not_found(self, api_client):
        resp = api_client.post("/api/extensions/nonexistent/toggle")
        data = resp.get_json()
        assert data["code"] == 404

    def test_toggle_disable(self, api_client, tmp_path, monkeypatch):
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "toggle-ext"
        ext_path.mkdir(parents=True)
        (ext_path / "manifest.json").write_text(json.dumps(
            {"id": "toggle-ext", "name": "Toggle", "version": "1.0.0",
             "permissions": [], "ext_points": {"backend": [], "frontend": []},
             "min_app_version": "1.0.0"}), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("toggle-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.post("/api/extensions/toggle-ext/toggle",
                               json={"enabled": False})
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["enabled"] is False

    def test_toggle_enable(self, api_client, tmp_path, monkeypatch):
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "toggle-on"
        ext_path.mkdir(parents=True)
        (ext_path / "manifest.json").write_text(json.dumps(
            {"id": "toggle-on", "name": "Toggle On", "version": "1.0.0",
             "permissions": [], "ext_points": {"backend": [], "frontend": []},
             "min_app_version": "1.0.0"}), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("toggle-on", {
            "version": "1.0.0", "enabled": False,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.post("/api/extensions/toggle-on/toggle",
                               json={"enabled": True})
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["enabled"] is True


class TestGetManifest:
    def test_manifest_not_found(self, api_client):
        resp = api_client.get("/api/extensions/nonexistent/manifest")
        data = resp.get_json()
        assert data["code"] == 404

    def test_manifest_success(self, api_client, tmp_path, monkeypatch):
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "manifest-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {"id": "manifest-ext", "name": "Manifest Ext", "version": "2.0.0",
                         "permissions": ["read:conversations"], "ext_points": {"backend": [], "frontend": []},
                         "min_app_version": "1.0.0"}
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("manifest-ext", {
            "version": "2.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": ["read:conversations"]
        })

        resp = api_client.get("/api/extensions/manifest-ext/manifest")
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["id"] == "manifest-ext"
        assert data["data"]["name"] == "Manifest Ext"
        assert data["data"]["version"] == "2.0.0"
