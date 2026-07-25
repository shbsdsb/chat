import json
import os
import threading

_lock = threading.Lock()

_PACKAGE_DIR = os.path.dirname(__file__)
EXTENSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(_PACKAGE_DIR)),
    "user_data", "extensions"
)


def get_registry_path():
    return os.path.join(EXTENSIONS_DIR, ".registry.json")


def _read_registry_unsafe():
    """不加锁的读取，调用者必须持有 _lock。"""
    path = get_registry_path()
    if not os.path.exists(path):
        return {"extensions": {}}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"extensions": {}}


def _write_registry_unsafe(data):
    """不加锁的写入，调用者必须持有 _lock。"""
    path = get_registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_registry():
    with _lock:
        return _read_registry_unsafe()


def write_registry(data):
    with _lock:
        _write_registry_unsafe(data)


def get_extension(ext_id):
    data = read_registry()
    return data.get("extensions", {}).get(ext_id)


def add_extension(ext_id, info):
    with _lock:
        data = _read_registry_unsafe()
        data.setdefault("extensions", {})[ext_id] = info
        _write_registry_unsafe(data)


def remove_extension(ext_id):
    with _lock:
        data = _read_registry_unsafe()
        data.get("extensions", {}).pop(ext_id, None)
        _write_registry_unsafe(data)


def set_extension_state(ext_id, enabled):
    with _lock:
        data = _read_registry_unsafe()
        if ext_id in data.get("extensions", {}):
            data["extensions"][ext_id]["enabled"] = enabled
            _write_registry_unsafe(data)
