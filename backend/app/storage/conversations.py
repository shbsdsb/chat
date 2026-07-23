import json
import os
import threading

_PACKAGE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(_PACKAGE_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "user_data")
CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")

_lock = threading.Lock()


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


def init_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MESSAGES_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    if not os.path.exists(CONVERSATIONS_FILE):
        _write_json(CONVERSATIONS_FILE, [])
    if not os.path.exists(os.path.join(DATA_DIR, "settings.json")):
        _write_json(os.path.join(DATA_DIR, "settings.json"), [])


def list_conversations():
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
    items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return items


def get_conversation(conv_id):
    items = list_conversations()
    for item in items:
        if item["id"] == conv_id:
            return item
    return None


def create_conversation(conv):
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
        items.append(conv)
        _write_json(CONVERSATIONS_FILE, items)
    msg_path = os.path.join(MESSAGES_DIR, f"{conv['id']}.json")
    if not os.path.exists(msg_path):
        _write_json(msg_path, [])


def update_conversation(conv_id, updates):
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
        for item in items:
            if item["id"] == conv_id:
                item.update(updates)
                break
        _write_json(CONVERSATIONS_FILE, items)


def delete_conversation(conv_id):
    with _lock:
        items = _read_json(CONVERSATIONS_FILE)
        items = [i for i in items if i["id"] != conv_id]
        _write_json(CONVERSATIONS_FILE, items)
    msg_path = os.path.join(MESSAGES_DIR, f"{conv_id}.json")
    if os.path.exists(msg_path):
        os.remove(msg_path)
