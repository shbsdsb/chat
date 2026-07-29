import os
import uuid
from .conversations import _read_json, _write_json, _lock, DATA_DIR

PROMPT_ENTRIES_DIR = os.path.join(DATA_DIR, "prompt_entries")


def _get_file_path(preset_id):
    return os.path.join(PROMPT_ENTRIES_DIR, f"{preset_id}.json")


def _ensure_dir():
    os.makedirs(PROMPT_ENTRIES_DIR, exist_ok=True)


def _read_real_entries(preset_id):
    """读取真实条目（不含 __chat_history__），按 order 排序。内部使用。"""
    _ensure_dir()
    filepath = _get_file_path(preset_id)
    if not os.path.exists(filepath):
        return []
    entries = _read_json(filepath)
    entries.sort(key=lambda e: e.get("order", 0))
    return entries


def get_entries(preset_id):
    """返回所有条目（含 chat_history 占位符，按 chat_history_order 插入）。"""
    entries = _read_real_entries(preset_id)

    # 从参数预设中读取 chat_history 的插入位置
    from .param_presets import get_param_preset
    preset = get_param_preset(preset_id)
    chat_order = (preset or {}).get("chat_history_order")

    if chat_order is not None:
        chat_order = max(0, min(chat_order, len(entries)))
    else:
        chat_order = len(entries)  # 默认末尾

    chat_history = {
        "id": "__chat_history__",
        "name": "对话历史",
        "role": "system",
        "content": "",
        "enabled": True,
        "order": chat_order - 0.5,  # 插入到 chat_order 索引前
    }

    all_entries = entries + [chat_history]
    all_entries.sort(key=lambda e: e.get("order", 0))

    # 重新分配连续 order
    for i, entry in enumerate(all_entries):
        entry["order"] = i

    return all_entries


def create_entry(preset_id, name):
    """创建新条目，order = 当前最大 + 1，enabled 默认 True。"""
    with _lock:
        entries = _read_real_entries(preset_id)
        max_order = max((e.get("order", 0) for e in entries), default=-1)
        entry = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "content": "",
            "role": None,
            "enabled": True,
            "order": max_order + 1,
        }
        entries.append(entry)
        _ensure_dir()
        _write_json(_get_file_path(preset_id), entries)
        return entry


def update_entry(preset_id, entry_id, data):
    """更新条目字段。"""
    with _lock:
        entries = _read_real_entries(preset_id)
        for entry in entries:
            if entry["id"] == entry_id:
                if "name" in data:
                    entry["name"] = data["name"].strip()
                if "enabled" in data:
                    entry["enabled"] = bool(data["enabled"])
                if "content" in data:
                    entry["content"] = data["content"]
                if "role" in data:
                    entry["role"] = data["role"]
                _write_json(_get_file_path(preset_id), entries)
                return entry
        return None


def delete_entry(preset_id, entry_id):
    """删除条目并重整 order 为连续值。"""
    with _lock:
        entries = _read_real_entries(preset_id)
        entries = [e for e in entries if e["id"] != entry_id]
        for i, entry in enumerate(entries):
            entry["order"] = i
        _write_json(_get_file_path(preset_id), entries)
        return True


def reorder_entries(preset_id, id_order_list):
    """按传入的 id 列表批量写入新 order。"""
    with _lock:
        entries = _read_real_entries(preset_id)
        id_to_entry = {e["id"]: e for e in entries}
        for new_order, entry_id in enumerate(id_order_list):
            if entry_id in id_to_entry:
                id_to_entry[entry_id]["order"] = new_order
        entries.sort(key=lambda e: e.get("order", 0))
        _write_json(_get_file_path(preset_id), entries)


def delete_preset_entries(preset_id):
    """删除整个预设的条目文件。"""
    filepath = _get_file_path(preset_id)
    if os.path.exists(filepath):
        os.remove(filepath)
