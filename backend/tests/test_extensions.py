import os
import pytest
from app.extensions.registry import (
    get_registry_path, read_registry, write_registry,
    get_extension, add_extension, remove_extension, set_extension_state,
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
