import os
import uuid
from datetime import datetime, timezone
from .conversations import _read_json, _write_json, _lock, DATA_DIR

PRESETS_DIR = os.path.join(DATA_DIR, "presets")
INDEX_FILE = os.path.join(PRESETS_DIR, "_index.json")

_DEFAULT_PARAMS = {"temperature": 0.7, "max_tokens": 4096, "top_p": 1.0}


def _ensure_dir():
    os.makedirs(PRESETS_DIR, exist_ok=True)


def _get_file_path(preset_id):
    return os.path.join(PRESETS_DIR, f"{preset_id}.json")


def _read_index():
    _ensure_dir()
    if not os.path.exists(INDEX_FILE):
        return []
    return _read_json(INDEX_FILE)


def _write_index(data):
    _ensure_dir()
    _write_json(INDEX_FILE, data)


def _read_preset(preset_id):
    filepath = _get_file_path(preset_id)
    if not os.path.exists(filepath):
        return None
    return _read_json(filepath)


def _write_preset(preset_id, data):
    _ensure_dir()
    _write_json(_get_file_path(preset_id), data)


def init_presets():
    """首次启动：索引为空时创建默认预设（幂等）。"""
    with _lock:
        index = _read_index()
        if index:
            return
        now = datetime.now(timezone.utc).isoformat()
        pid = str(uuid.uuid4())
        preset = {
            "name": "默认",
            "is_default": True,
            "created_at": now,
            "updated_at": now,
            "params": dict(_DEFAULT_PARAMS),
            "entries": {"__chat_history__": "chat_history"},
        }
        _write_preset(pid, preset)
        _write_index([{"id": pid, "name": "默认", "is_default": True}])


def list_presets():
    """返回预设索引列表 [{id, name, is_default}]。"""
    return _read_index()


def get_preset(preset_id):
    """返回完整预设对象。"""
    data = _read_preset(preset_id)
    if data is None:
        return None
    data["id"] = preset_id
    return data


def create_preset(data):
    """创建新预设。data: {name, temperature, max_tokens, top_p}。"""
    with _lock:
        pid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        preset = {
            "name": (data.get("name") or "").strip(),
            "is_default": False,
            "created_at": now,
            "updated_at": now,
            "params": {
                "temperature": float(data.get("temperature", 0.7)),
                "max_tokens": int(data.get("max_tokens", 4096)),
                "top_p": float(data.get("top_p", 1.0)),
            },
            "entries": {"__chat_history__": "chat_history"},
        }
        _write_preset(pid, preset)
        index = _read_index()
        index.append({"id": pid, "name": preset["name"], "is_default": False})
        _write_index(index)
        result = dict(preset)
        result["id"] = pid
        return result


def update_preset(preset_id, data):
    """全量覆盖预设。data: {name, params, entries}。"""
    with _lock:
        existing = _read_preset(preset_id)
        if existing is None:
            return None
        now = datetime.now(timezone.utc).isoformat()
        existing["name"] = (data.get("name") or existing["name"]).strip()
        existing["updated_at"] = now
        if "params" in data and isinstance(data["params"], dict):
            p = data["params"]
            existing["params"]["temperature"] = float(p.get("temperature", existing["params"]["temperature"]))
            existing["params"]["max_tokens"] = int(p.get("max_tokens", existing["params"]["max_tokens"]))
            existing["params"]["top_p"] = float(p.get("top_p", existing["params"]["top_p"]))
        if "entries" in data and isinstance(data["entries"], dict):
            existing["entries"] = data["entries"]
        _write_preset(preset_id, existing)
        # 更新索引中的 name
        index = _read_index()
        for item in index:
            if item["id"] == preset_id:
                item["name"] = existing["name"]
                break
        _write_index(index)
        result = dict(existing)
        result["id"] = preset_id
        return result


def delete_preset(preset_id):
    """删除预设文件和索引条目。"""
    with _lock:
        filepath = _get_file_path(preset_id)
        if os.path.exists(filepath):
            os.remove(filepath)
        index = _read_index()
        index = [item for item in index if item["id"] != preset_id]
        _write_index(index)
        return True


def get_default_preset():
    """返回默认预设的完整数据。"""
    index = _read_index()
    for item in index:
        if item.get("is_default"):
            return get_preset(item["id"])
    # fallback: 返回第一个
    if index:
        return get_preset(index[0]["id"])
    return None


def set_default_preset(preset_id):
    """设置默认预设。"""
    with _lock:
        index = _read_index()
        for item in index:
            item["is_default"] = (item["id"] == preset_id)
        _write_index(index)


def get_entries(preset_id):
    """从预设的 entries 对象提取条目数组，保持键顺序。返回含 __chat_history__ 占位符的列表。"""
    preset = _read_preset(preset_id)
    if preset is None:
        return []
    entries_obj = preset.get("entries", {})
    result = []
    for idx, (key, value) in enumerate(entries_obj.items()):
        if key == "__chat_history__":
            result.append({
                "id": "__chat_history__",
                "name": "对话历史",
                "role": "system",
                "content": "",
                "enabled": True,
                "order": idx,
            })
        elif isinstance(value, dict):
            result.append({
                "id": key,
                "name": value.get("name", ""),
                "role": value.get("role"),
                "content": value.get("content", ""),
                "enabled": value.get("enabled", True),
                "order": idx,
            })
    return result
