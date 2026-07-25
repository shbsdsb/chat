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
