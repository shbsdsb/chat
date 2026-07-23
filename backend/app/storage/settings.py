import os
from .conversations import _read_json, _write_json, _lock, DATA_DIR

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def _read_settings():
    return _read_json(SETTINGS_FILE)


def _write_settings(data):
    _write_json(SETTINGS_FILE, data)


def list_settings_raw():
    with _lock:
        items = _read_settings()
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def get_setting(setting_id):
    items = list_settings_raw()
    for item in items:
        if item["id"] == setting_id:
            return item
    return None


def create_setting(s):
    with _lock:
        items = _read_settings()
        items.append(s)
        _write_settings(items)


def update_setting(setting_id, updates):
    with _lock:
        items = _read_settings()
        for item in items:
            if item["id"] == setting_id:
                item.update(updates)
                break
        _write_settings(items)


def delete_setting(setting_id):
    with _lock:
        items = _read_settings()
        items = [i for i in items if i["id"] != setting_id]
        _write_settings(items)


def get_default_setting():
    items = list_settings_raw()
    for item in items:
        if item.get("is_default"):
            return item
    return None


def set_default_setting(setting_id):
    with _lock:
        items = _read_settings()
        for item in items:
            item["is_default"] = (item["id"] == setting_id)
        _write_settings(items)
