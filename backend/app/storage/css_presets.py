import os
from .conversations import _read_json, _write_json, _lock, DATA_DIR

CSS_PRESETS_FILE = os.path.join(DATA_DIR, "css_presets.json")

# 默认预设模板
_DEFAULT_PRESET = {
    "name": "默认",
    "content": "",
    "is_default": True,
}


def _read_css_presets():
    return _read_json(CSS_PRESETS_FILE)


def _write_css_presets(data):
    _write_json(CSS_PRESETS_FILE, data)


def init_css_presets():
    """首次启动：文件不存在或为空时自动创建默认预设"""
    import uuid
    from datetime import datetime, timezone

    if not os.path.exists(CSS_PRESETS_FILE):
        now = datetime.now(timezone.utc).isoformat()
        default = {**_DEFAULT_PRESET, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        _write_css_presets([default])
        return

    items = _read_css_presets()
    if not items:
        now = datetime.now(timezone.utc).isoformat()
        default = {**_DEFAULT_PRESET, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        _write_css_presets([default])


def list_css_presets_raw():
    with _lock:
        items = _read_css_presets()
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def get_css_preset(preset_id):
    items = list_css_presets_raw()
    for item in items:
        if item["id"] == preset_id:
            return item
    return None


def create_css_preset(p):
    with _lock:
        items = _read_css_presets()
        items.append(p)
        _write_css_presets(items)


def update_css_preset(preset_id, updates):
    with _lock:
        items = _read_css_presets()
        for item in items:
            if item["id"] == preset_id:
                item.update(updates)
                break
        _write_css_presets(items)


def delete_css_preset(preset_id):
    with _lock:
        items = _read_css_presets()
        items = [i for i in items if i["id"] != preset_id]
        _write_css_presets(items)


def get_default_css_preset():
    items = list_css_presets_raw()
    for item in items:
        if item.get("is_default"):
            return item
    return None


def set_default_css_preset(preset_id):
    with _lock:
        items = _read_css_presets()
        for item in items:
            item["is_default"] = (item["id"] == preset_id)
        _write_css_presets(items)
