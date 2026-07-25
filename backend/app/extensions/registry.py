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


def read_registry():
    path = get_registry_path()
    if not os.path.exists(path):
        return {"extensions": {}}
    with _lock:
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"extensions": {}}


def write_registry(data):
    path = get_registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_extension(ext_id):
    data = read_registry()
    return data.get("extensions", {}).get(ext_id)


def add_extension(ext_id, info):
    data = read_registry()
    data.setdefault("extensions", {})[ext_id] = info
    write_registry(data)


def remove_extension(ext_id):
    data = read_registry()
    data.get("extensions", {}).pop(ext_id, None)
    write_registry(data)


def set_extension_state(ext_id, enabled):
    data = read_registry()
    if ext_id in data.get("extensions", {}):
        data["extensions"][ext_id]["enabled"] = enabled
        write_registry(data)
