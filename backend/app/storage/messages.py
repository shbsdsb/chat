import os
from .conversations import _read_json, _write_json, _lock, MESSAGES_DIR


def _msg_path(conv_id):
    return os.path.join(MESSAGES_DIR, f"{conv_id}.json")


def get_messages(conv_id):
    items = _read_json(_msg_path(conv_id))
    items.sort(key=lambda x: x.get("created_at", ""))
    return items


def add_message(msg):
    path = _msg_path(msg["conversation_id"])
    with _lock:
        items = _read_json(path)
        items.append(msg)
        _write_json(path, items)


def get_message(msg_id, conv_id=None):
    if conv_id:
        items = get_messages(conv_id)
        for m in items:
            if m["id"] == msg_id:
                return m
        return None
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
    conv_id = updates.get("conversation_id")
    if not conv_id:
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
    path = _msg_path(conv_id)
    with _lock:
        items = _read_json(path)
        items = [m for m in items if m.get("created_at", "") <= created_at]
        _write_json(path, items)


def delete_message(msg_id, conv_id):
    path = _msg_path(conv_id)
    with _lock:
        items = _read_json(path)
        items = [m for m in items if m["id"] != msg_id]
        _write_json(path, items)


def get_last_assistant_message_id(conv_id):
    items = get_messages(conv_id)
    for m in reversed(items):
        if m.get("role") == "assistant":
            return m["id"]
    return None


def get_messages_for_chat(conv_id):
    items = get_messages(conv_id)
    return [{"role": m["role"], "content": m["content"]} for m in items]
