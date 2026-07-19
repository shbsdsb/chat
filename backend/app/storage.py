"""
JSON 文件存储 — 替代 SQLite

文件结构：
    user_data/
    ├── conversations.json          # 会话索引 [{id, title, created_at, updated_at}, ...]
    ├── messages/<conv_id>.json     # 每个会话的消息 [{id, role, content, reasoning_content, created_at}, ...]
    └── settings.json               # 预设 [{id, name, api_url, api_key, ...}, ...]
"""
import json
import os
import threading

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "user_data")
CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

_lock = threading.Lock()


# ── 底层 JSON 读写 ──────────────────────────────────

def _read_json(path, default=None):
    if default is None:
        default = []
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 初始化 ──────────────────────────────────────────

def init_storage():
    """确保数据目录和初始文件存在（幂等）。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MESSAGES_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)

    if not os.path.exists(CONVERSATIONS_FILE):
        _write_json(CONVERSATIONS_FILE, [])
    if not os.path.exists(SETTINGS_FILE):
        _write_json(SETTINGS_FILE, [])


# ── 会话 (conversations) ────────────────────────────

def list_conversations():
    """返回 [{id, title, created_at, updated_at}, ...]，按 updated_at 降序。"""
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
    items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return items


def get_conversation(conv_id):
    """返回会话 dict，不存在返回 None。"""
    items = list_conversations()
    for item in items:
        if item["id"] == conv_id:
            return item
    return None


def create_conversation(conv):
    """conv: {id, title, created_at, updated_at}。"""
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
        items.append(conv)
        _write_json(CONVERSATIONS_FILE, items)
    # 同时创建空消息文件
    msg_path = _msg_path(conv["id"])
    if not os.path.exists(msg_path):
        _write_json(msg_path, [])


def update_conversation(conv_id, updates):
    """updates: dict，只更新提供的字段。"""
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
        for item in items:
            if item["id"] == conv_id:
                item.update(updates)
                break
        _write_json(CONVERSATIONS_FILE, items)


def delete_conversation(conv_id):
    """删除会话及其消息文件。"""
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
        items = [i for i in items if i["id"] != conv_id]
        _write_json(CONVERSATIONS_FILE, items)
    msg_path = _msg_path(conv_id)
    if os.path.exists(msg_path):
        os.remove(msg_path)


# ── 消息 (messages) ─────────────────────────────────

def _msg_path(conv_id):
    return os.path.join(MESSAGES_DIR, f"{conv_id}.json")


def get_messages(conv_id):
    """返回 [{id, conversation_id, role, content, reasoning_content, created_at}, ...]，按 created_at 升序。"""
    items = _read_json(_msg_path(conv_id))
    items.sort(key=lambda x: x.get("created_at", ""))
    return items


def add_message(msg):
    """msg: {id, conversation_id, role, content, reasoning_content, created_at}。"""
    path = _msg_path(msg["conversation_id"])
    with _lock:
        items = _read_json(path)
        items.append(msg)
        _write_json(path, items)


def get_message(msg_id, conv_id=None):
    """按 ID 查找消息，可选限定会话。"""
    if conv_id:
        items = get_messages(conv_id)
        for m in items:
            if m["id"] == msg_id:
                return m
        return None
    # 不带 conv_id 则遍历所有消息文件（较少用）
    if not os.path.isdir(MESSAGES_DIR):
        return None
    for fname in os.listdir(MESSAGES_DIR):
        if not fname.endswith(".json"):
            continue
        items = _read_json(os.path.join(MESSAGES_DIR, fname))
        for m in items:
            if m["id"] == msg_id:
                return m
    return None


def update_message(msg_id, updates):
    """updates: dict，只更新提供的字段。需要通过 conv_id 定位文件。"""
    conv_id = updates.get("conversation_id")
    if not conv_id:
        # 回退：遍历查找
        m = get_message(msg_id)
        if m:
            conv_id = m["conversation_id"]
        else:
            return
    path = _msg_path(conv_id)
    with _lock:
        items = _read_json(path)
        for item in items:
            if item["id"] == msg_id:
                item.update(updates)
                break
        _write_json(path, items)


def delete_messages_after(conv_id, created_at):
    """删除指定会话中 created_at 大于指定时间的消息（编辑时截断后续）。"""
    path = _msg_path(conv_id)
    with _lock:
        items = _read_json(path)
        items = [m for m in items if m.get("created_at", "") <= created_at]
        _write_json(path, items)


def delete_message(msg_id, conv_id):
    """删除指定消息。"""
    path = _msg_path(conv_id)
    with _lock:
        items = _read_json(path)
        items = [m for m in items if m["id"] != msg_id]
        _write_json(path, items)


def get_last_assistant_message_id(conv_id):
    """获取会话中最后一条 assistant 消息的 id。"""
    items = get_messages(conv_id)
    for m in reversed(items):
        if m.get("role") == "assistant":
            return m["id"]
    return None


def get_messages_for_chat(conv_id):
    """获取用于发送给 AI 的消息列表 [{role, content}, ...]。"""
    items = get_messages(conv_id)
    return [{"role": m["role"], "content": m["content"]} for m in items]


# ── 设置 (settings) ─────────────────────────────────

def _read_settings():
    return _read_json(SETTINGS_FILE)


def _write_settings(data):
    _write_json(SETTINGS_FILE, data)


def list_settings_raw():
    """返回 [{...}, ...]，按 created_at 降序。is_default 为 bool 类型。"""
    with _lock:
        items = _read_settings()
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def get_setting(setting_id):
    """返回设置 dict，不存在返回 None。"""
    items = list_settings_raw()
    for item in items:
        if item["id"] == setting_id:
            return item
    return None


def create_setting(s):
    """s 包含所有字段。"""
    with _lock:
        items = _read_settings()
        items.append(s)
        _write_settings(items)


def update_setting(setting_id, updates):
    """updates: dict，只更新提供的字段。"""
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
    """返回默认设置，无则返回 None。"""
    items = list_settings_raw()
    for item in items:
        if item.get("is_default"):
            return item
    return None


def set_default_setting(setting_id):
    """将指定设置设为默认，取消其他默认。"""
    with _lock:
        items = _read_settings()
        for item in items:
            item["is_default"] = (item["id"] == setting_id)
        _write_settings(items)
