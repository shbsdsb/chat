# Chat 后端 API 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 14 个后端 API 接口（会话管理 8 个 + 配置管理 6 个），对接前端 MVP。

**Architecture:** Flask Blueprint 路由 → 两个路由文件（conversations/settings）→ 共享 services（AI 流式调用 + SSE 取消管理）→ 共享 utils（统一响应）。使用 `requests` 直连 OpenAI 兼容 API，`threading.Event` 实现 `/stop` 取消。

**Tech Stack:** Python 3, Flask 3, SQLite, requests, cryptography (Fernet)

## Global Constraints

- 所有非 SSE 响应格式：`{"code": 0, "message": "ok", "data": {...}}`
- SSE 响应格式：`data: {"delta": "...", "done": false}\n\n`
- api_key 数据库存储必须 Fernet 加密，对外返回脱敏（前 4 位 + `****`）
- 错误日志写入 `user_data/logs/error.log`
- 不引入 Flask / cryptography / flask-cors 之外的第三方依赖（`requests` 例外）
- 接口路径严格对齐 `docs/API.md`

---

## 文件结构

| 操作 | 路径 | 职责 |
|------|------|------|
| 创建 | `backend/app/utils/response.py` | `ok()` / `fail()` 统一响应 + 错误日志 |
| 创建 | `backend/app/services/sse_manager.py` | `SSEManager` 类 — 维护 `{conv_id: Event}` 映射 |
| 创建 | `backend/app/services/ai.py` | `stream_chat()` 生成器 — 调 AI API，检查 cancel_event |
| 创建 | `backend/app/routes/settings.py` | 6 个配置管理接口 |
| 创建 | `backend/app/routes/conversations.py` | 8 个会话/消息接口 |
| 修改 | `backend/app/__init__.py` | 注册新路由模块 |
| 修改 | `backend/requirements.txt` | 添加 `requests` |
| 创建 | `backend/tests/conftest.py` | 测试夹具（Flask test client） |
| 创建 | `backend/tests/test_settings.py` | settings 路由测试 |
| 创建 | `backend/tests/test_conversations.py` | conversations 路由测试 |

---

### Task 1: 统一响应工具 `utils/response.py`

**Files:**
- Create: `backend/app/utils/response.py`
- Create: `backend/app/utils/__init__.py`
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Produces: `ok(data=None, message="ok")` → Flask Response (HTTP 200, JSON body)
- Produces: `fail(code, message, request=None)` → Flask Response (HTTP 200, JSON body; 写 error.log)

- [ ] **Step 1: 创建 utils 包和 conftest**

```bash
mkdir -p backend/app/utils
mkdir -p backend/tests
```

创建 `backend/app/utils/__init__.py`（空文件）。

创建 `backend/tests/conftest.py`：

```python
import sys
import os
import pytest

# 将 backend 加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()
```

- [ ] **Step 2: 编写测试**

创建 `backend/tests/test_response.py`：

```python
import json
import os
from app.utils.response import ok, fail


class TestOk:
    def test_ok_no_data(self, app):
        with app.test_request_context():
            resp = ok()
            body = json.loads(resp.get_data(as_text=True))
            assert body["code"] == 0
            assert body["message"] == "ok"
            assert body["data"] is None

    def test_ok_with_data(self, app):
        with app.test_request_context():
            resp = ok(data={"id": "abc"})
            body = json.loads(resp.get_data(as_text=True))
            assert body["code"] == 0
            assert body["data"] == {"id": "abc"}

    def test_ok_custom_message(self, app):
        with app.test_request_context():
            resp = ok(message="created")
            body = json.loads(resp.get_data(as_text=True))
            assert body["message"] == "created"


class TestFail:
    def test_fail_returns_code_in_body(self, app):
        with app.test_request_context():
            resp = fail(404, "not found")
            body = json.loads(resp.get_data(as_text=True))
            assert body["code"] == 404
            assert body["message"] == "not found"
            assert body["data"] is None

    def test_fail_writes_error_log(self, app, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)

        import app.utils.response as mod
        monkeypatch.setattr(mod, "LOG_DIR", str(log_dir))

        with app.test_request_context():
            fail(500, "server error")

        log_file = log_dir / "error.log"
        assert log_file.exists()
        entry = json.loads(log_file.read_text(encoding="utf-8"))
        assert entry["code"] == 500
        assert entry["message"] == "server error"
        assert "timestamp" in entry

    def test_fail_logs_request_info(self, app, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)

        import app.utils.response as mod
        monkeypatch.setattr(mod, "LOG_DIR", str(log_dir))

        with app.test_request_context(
            path="/api/test",
            method="POST",
            json={"api_key": "secret123", "name": "test"},
        ):
            fail(400, "bad request")

        entry = json.loads(
            (log_dir / "error.log").read_text(encoding="utf-8")
        )
        assert entry["path"] == "/api/test"
        assert entry["method"] == "POST"
        assert entry["body"]["api_key"] == "***"   # 脱敏
        assert entry["body"]["name"] == "test"      # 非敏感字段保留
```

- [ ] **Step 3: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_response.py -v
```

预期：全部 FAIL（模块不存在）

- [ ] **Step 4: 实现 `response.py`**

创建 `backend/app/utils/response.py`：

```python
import json
import os
import logging
from datetime import datetime, timezone
from flask import jsonify, request as flask_request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, "user_data", "logs")


def ok(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data})


def fail(code, message, request=None):
    req = request or flask_request
    os.makedirs(LOG_DIR, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code": code,
        "message": message,
    }

    if req:
        log_entry["method"] = req.method
        log_entry["path"] = req.path
        if req.is_json:
            body = req.get_json(silent=True) or {}
            masked = {}
            for key, val in body.items():
                if key in ("api_key", "password", "secret"):
                    masked[key] = "***"
                else:
                    masked[key] = val
            log_entry["body"] = masked

    with open(os.path.join(LOG_DIR, "error.log"), "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return jsonify({"code": code, "message": message, "data": None})
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_response.py -v
```

预期：全部 PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/utils/__init__.py backend/app/utils/response.py backend/tests/conftest.py backend/tests/test_response.py
git commit -m "feat: add unified response helpers ok()/fail() with error logging"
```

---

### Task 2: SSE 会话管理器 `services/sse_manager.py`

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/sse_manager.py`
- Create: `backend/tests/test_sse_manager.py`

**Interfaces:**
- Produces: `sse_manager.register(conv_id: str) → threading.Event`
- Produces: `sse_manager.cancel(conv_id: str) → bool`
- Produces: `sse_manager.unregister(conv_id: str) → None`

- [ ] **Step 1: 编写测试**

创建 `backend/tests/test_sse_manager.py`：

```python
import threading
from app.services.sse_manager import sse_manager


class TestSSEManager:
    def test_register_returns_event(self):
        event = sse_manager.register("conv-1")
        assert isinstance(event, threading.Event)
        assert not event.is_set()

    def test_cancel_sets_event(self):
        sse_manager.register("conv-2")
        result = sse_manager.cancel("conv-2")
        assert result is True

    def test_cancel_nonexistent(self):
        result = sse_manager.cancel("no-such-id")
        assert result is False

    def test_unregister_removes(self):
        sse_manager.register("conv-3")
        sse_manager.unregister("conv-3")
        result = sse_manager.cancel("conv-3")  # 已移除，应找不到
        assert result is False

    def test_thread_safe(self):
        """多个线程同时 register/cancel 不抛异常"""
        errors = []

        def worker(i):
            try:
                cid = f"conv-t{i}"
                sse_manager.register(cid)
                sse_manager.cancel(cid)
                sse_manager.unregister(cid)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_sse_manager.py -v
```

- [ ] **Step 3: 实现 `sse_manager.py`**

创建 `backend/app/services/__init__.py`（空文件）。

创建 `backend/app/services/sse_manager.py`：

```python
import threading


class SSEManager:
    """维护 {conversation_id: threading.Event} 映射，支持 /stop 取消 SSE 流。"""

    def __init__(self):
        self._events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def register(self, conv_id: str) -> threading.Event:
        """注册一个对话，返回取消用 Event。"""
        event = threading.Event()
        with self._lock:
            self._events[conv_id] = event
        return event

    def cancel(self, conv_id: str) -> bool:
        """发送取消信号。返回 True 表示成功找到并取消。"""
        with self._lock:
            event = self._events.get(conv_id)
        if event:
            event.set()
            return True
        return False

    def unregister(self, conv_id: str) -> None:
        """对话结束，清理映射。"""
        with self._lock:
            self._events.pop(conv_id, None)


# 模块级单例
sse_manager = SSEManager()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_sse_manager.py -v
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/__init__.py backend/app/services/sse_manager.py backend/tests/test_sse_manager.py
git commit -m "feat: add SSE manager for /stop cancellation"
```

---

### Task 3: AI 流式客户端 `services/ai.py`

**Files:**
- Create: `backend/app/services/ai.py`
- Create: `backend/tests/test_ai.py`

**Interfaces:**
- Produces: `stream_chat(api_url, api_key, model, messages, response_format, cancel_event) → generator[dict]`
  - yield `{"delta": str}` — 增量文本
  - yield `{"done": True}` — 正常结束
  - yield `{"stopped": True}` — 被取消
  - yield `{"error": str}` — 请求失败

- [ ] **Step 1: 编写测试**

创建 `backend/tests/test_ai.py`：

```python
import json
import threading
from unittest.mock import patch, Mock, MagicMock
from app.services.ai import stream_chat


def make_mock_response(chunks):
    """构造模拟的 requests.Response，iter_lines 返回指定 chunks。"""
    resp = Mock()
    resp.raise_for_status = Mock()
    lines = []
    for chunk in chunks:
        if chunk == "[DONE]":
            lines.append(b"data: [DONE]")
        else:
            lines.append(
                json.dumps({
                    "choices": [{"delta": {"content": chunk}}]
                }).encode()
            )
    resp.iter_lines.return_value = [b""] + lines  # SSE 有空行前缀
    return resp


class TestStreamChat:
    def test_yields_deltas(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["你好", "世界"])

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert {"delta": "你好"} in results
        assert {"delta": "世界"} in results
        assert {"done": True} in results

    def test_yields_done_at_end(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["ok"])

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert results[-1] == {"done": True}

    def test_stops_on_cancel(self):
        cancel = threading.Event()
        # 在 iter_lines 被调用时设置 cancel 信号
        orig_iter_lines = Mock()

        def set_cancel_then_iter():
            cancel.set()
            return iter([b'data: {"choices":[{"delta":{"content":"partial"}}]}'])

        with patch("app.services.ai.requests.post") as mock_post:
            mock_resp = Mock()
            mock_resp.raise_for_status = Mock()
            mock_resp.iter_lines.side_effect = set_cancel_then_iter
            mock_resp.close = Mock()
            mock_post.return_value = mock_resp

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        # cancel 后第一条 delta 应产出的同时检测到取消
        assert {"stopped": True} in results

    def test_request_error(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert len(results) == 1
        assert "error" in results[0]

    def test_includes_response_format_when_set(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["{}"])

            list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "json_object",
                cancel,
            ))

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["response_format"] == {"type": "json_object"}
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_ai.py -v
```

- [ ] **Step 3: 实现 `ai.py`**

创建 `backend/app/services/ai.py`：

```python
import json
import requests


def stream_chat(api_url, api_key, model, messages, response_format, cancel_event):
    """调用 OpenAI 兼容 API，逐 chunk yield 增量内容。

    参数:
        api_url:        API 地址（如 https://api.openai.com/v1）
        api_key:        API Key（明文）
        model:          模型名
        messages:       消息列表 [{"role": "user", "content": "..."}, ...]
        response_format: "text" | "json_object"
        cancel_event:   threading.Event，外部 set() 后停止生成

    Yields:
        {"delta": str}      增量文本
        {"done": True}      生成结束
        {"stopped": True}   被 /stop 中断
        {"error": str}      请求错误
    """
    url = api_url.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if response_format and response_format != "text":
        payload["response_format"] = {"type": response_format}

    try:
        resp = requests.post(
            url, headers=headers, json=payload, stream=True, timeout=120
        )
        resp.raise_for_status()

        for line in resp.iter_lines():
            # 检查取消信号 — 在循环的每一次迭代都检查
            if cancel_event.is_set():
                yield {"stopped": True}
                resp.close()
                return

            if not line:
                continue

            line_str = line.decode("utf-8") if isinstance(line, bytes) else line
            if not line_str.startswith("data: "):
                continue

            data_str = line_str[6:]
            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield {"delta": delta}
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        yield {"done": True}

    except requests.RequestException as e:
        yield {"error": str(e)}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_ai.py -v
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/ai.py backend/tests/test_ai.py
git commit -m "feat: add AI streaming client with cancel support"
```

---

### Task 4: 配置管理路由 `routes/settings.py`

**Files:**
- Create: `backend/app/routes/settings.py`
- Create: `backend/tests/test_settings.py`

**Interfaces:**
- Consumes: `app.routes.api_bp` (Flask Blueprint), `app.database.get_db`, `app.database.encrypt`, `app.database.decrypt`, `app.utils.response.ok`, `app.utils.response.fail`
- Produces: 6 个注册在 `api_bp` 上的路由处理器

- [ ] **Step 1: 编写测试**

创建 `backend/tests/test_settings.py`：

```python
import json
import uuid
from app.database import init_db, get_db


def _setup_db(app):
    """每个测试前清空并重建表。"""
    with app.app_context():
        init_db()
        db = get_db()
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")
        db.execute("DELETE FROM settings")
        db.commit()


class TestSettingsList:
    def test_empty_list(self, client, app):
        _setup_db(app)
        resp = client.get("/api/settings")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"] == []

    def test_returns_presets(self, client, app):
        _setup_db(app)
        # 先创建两条
        client.post("/api/settings", json={
            "name": "OpenAI", "api_url": "https://api.openai.com/v1", "api_key": "sk-abc"
        })
        client.post("/api/settings", json={
            "name": "Ollama", "api_url": "http://localhost:11434/v1", "api_key": ""
        })

        resp = client.get("/api/settings")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert len(body["data"]) == 2
        # api_key 脱敏
        for item in body["data"]:
            assert "****" in item["api_key"] or item["api_key"] == ""


class TestSettingsCreate:
    def test_create_success(self, client, app):
        _setup_db(app)
        resp = client.post("/api/settings", json={
            "name": "OpenAI",
            "api_url": "https://api.openai.com/v1",
            "api_key": "sk-abc123",
            "model": "gpt-4o",
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["name"] == "OpenAI"
        assert body["data"]["api_key"] == "sk-a****"

    def test_create_missing_name(self, client, app):
        _setup_db(app)
        resp = client.post("/api/settings", json={
            "api_url": "https://api.openai.com/v1",
            "api_key": "sk-abc",
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 400


class TestSettingsUpdate:
    def test_update_success(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/settings", json={
            "name": "Old", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        sid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.put(f"/api/settings/{sid}", json={
            "name": "New", "api_url": "https://b.com", "api_key": "", "model": "gpt-4o"
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["name"] == "New"
        assert body["data"]["api_url"] == "https://b.com"
        # api_key 为空字符串时保留原值
        assert "****" in body["data"]["api_key"]

    def test_update_nonexistent(self, client, app):
        _setup_db(app)
        resp = client.put("/api/settings/no-such-id", json={
            "name": "X", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        assert json.loads(resp.get_data(as_text=True))["code"] == 404


class TestSettingsDelete:
    def test_delete_success(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/settings", json={
            "name": "X", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        sid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.delete(f"/api/settings/{sid}")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0

        # 验证已删除
        list_resp = client.get("/api/settings")
        assert len(json.loads(list_resp.get_data(as_text=True))["data"]) == 0

    def test_cannot_delete_default(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/settings", json={
            "name": "Default", "api_url": "https://a.com", "api_key": "sk-abc"
        })
        sid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]
        # 设为默认
        client.put(f"/api/settings/{sid}/default")

        resp = client.delete(f"/api/settings/{sid}")
        assert json.loads(resp.get_data(as_text=True))["code"] == 409


class TestSettingsSetDefault:
    def test_set_default(self, client, app):
        _setup_db(app)
        r1 = client.post("/api/settings", json={
            "name": "A", "api_url": "https://a.com", "api_key": "sk-a"
        })
        r2 = client.post("/api/settings", json={
            "name": "B", "api_url": "https://b.com", "api_key": "sk-b"
        })
        id_a = json.loads(r1.get_data(as_text=True))["data"]["id"]
        id_b = json.loads(r2.get_data(as_text=True))["data"]["id"]

        # 先设 A 为默认
        client.put(f"/api/settings/{id_a}/default")
        # 再设 B 为默认
        resp = client.put(f"/api/settings/{id_b}/default")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0

        # 验证只有 B 是默认
        items = json.loads(client.get("/api/settings").get_data(as_text=True))["data"]
        defaults = [i for i in items if i["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["id"] == id_b
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_settings.py -v
```

- [ ] **Step 3: 实现 `routes/settings.py`**

创建 `backend/app/routes/settings.py`：

```python
import uuid
from datetime import datetime, timezone
from flask import request
from app.routes import api_bp
from app.database import get_db, encrypt, decrypt
from app.utils.response import ok, fail
import requests


def _row_to_dict(row):
    """sqlite3.Row → dict，api_key 脱敏。"""
    d = dict(row)
    if d.get("api_key"):
        key = d["api_key"]
        # 尝试解密（可能是明文也可能是密文）
        try:
            key = decrypt(key)
        except Exception:
            pass
        d["api_key"] = key[:4] + "****" if len(key) >= 4 else "****"
    d["is_default"] = bool(d.get("is_default"))
    return d


def _get_setting_or_404(setting_id):
    db = get_db()
    row = db.execute("SELECT * FROM settings WHERE id = ?", (setting_id,)).fetchone()
    return row


# ── GET /settings ──────────────────────────────────

@api_bp.route("/settings")
def list_settings():
    db = get_db()
    rows = db.execute("SELECT * FROM settings ORDER BY created_at DESC").fetchall()
    return ok(data=[_row_to_dict(r) for r in rows])


# ── POST /settings ─────────────────────────────────

@api_bp.route("/settings", methods=["POST"])
def create_setting():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    api_url = (body.get("api_url") or "").strip()
    api_key = body.get("api_key", "")

    if not name:
        return fail(400, "name 不能为空", request)
    if not api_url:
        return fail(400, "api_url 不能为空", request)

    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    encrypted_key = encrypt(api_key) if api_key else ""
    model = body.get("model", "gpt-4o")
    response_format = body.get("response_format", "text")
    temperature = body.get("temperature", 0.7)
    max_tokens = body.get("max_tokens", 4096)

    db = get_db()
    db.execute("""
        INSERT INTO settings (id, name, api_url, api_key, model, response_format,
                              temperature, max_tokens, is_default, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (sid, name, api_url, encrypted_key, model, response_format,
          temperature, max_tokens, now, now))
    db.commit()

    row = _get_setting_or_404(sid)
    return ok(data=_row_to_dict(row))


# ── PUT /settings/:id ──────────────────────────────

@api_bp.route("/settings/<setting_id>", methods=["PUT"])
def update_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or row["name"]).strip()
    api_url = (body.get("api_url") or row["api_url"]).strip()
    model = body.get("model", row["model"])
    response_format = body.get("response_format", row["response_format"])
    temperature = body.get("temperature", row["temperature"])
    max_tokens = body.get("max_tokens", row["max_tokens"])

    # api_key: 空字符串保留原值，否则加密新值
    api_key = body.get("api_key", "")
    if api_key == "":
        encrypted_key = row["api_key"]
    else:
        encrypted_key = encrypt(api_key)

    now = datetime.now(timezone.utc).isoformat()

    db = get_db()
    db.execute("""
        UPDATE settings
        SET name = ?, api_url = ?, api_key = ?, model = ?, response_format = ?,
            temperature = ?, max_tokens = ?, updated_at = ?
        WHERE id = ?
    """, (name, api_url, encrypted_key, model, response_format,
          temperature, max_tokens, now, setting_id))
    db.commit()

    updated = _get_setting_or_404(setting_id)
    return ok(data=_row_to_dict(updated))


# ── DELETE /settings/:id ───────────────────────────

@api_bp.route("/settings/<setting_id>", methods=["DELETE"])
def delete_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)
    if row["is_default"]:
        return fail(409, "不能删除默认配置，请先切换默认配置", request)

    db = get_db()
    db.execute("DELETE FROM settings WHERE id = ?", (setting_id,))
    db.commit()
    return ok()


# ── POST /settings/:id/test ────────────────────────

@api_bp.route("/settings/<setting_id>/test", methods=["POST"])
def test_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    api_key = row["api_key"]
    try:
        api_key = decrypt(api_key)
    except Exception:
        pass

    url = row["api_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": row["model"],
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
        "stream": False,
    }

    import time
    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        latency_ms = int((time.time() - start) * 1000)
        data = resp.json()
        model_used = data.get("model", row["model"])
        return ok(data={
            "success": True,
            "latency_ms": latency_ms,
            "model": model_used,
        })
    except requests.RequestException as e:
        latency_ms = int((time.time() - start) * 1000)
        return ok(data={
            "success": False,
            "latency_ms": latency_ms,
            "error": str(e),
        })


# ── PUT /settings/:id/default ──────────────────────

@api_bp.route("/settings/<setting_id>/default", methods=["PUT"])
def set_default_setting(setting_id):
    row = _get_setting_or_404(setting_id)
    if not row:
        return fail(404, "配置不存在", request)

    db = get_db()
    db.execute("UPDATE settings SET is_default = 0")
    db.execute("UPDATE settings SET is_default = 1 WHERE id = ?", (setting_id,))
    db.commit()

    return ok(data={"is_default": True})
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_settings.py -v
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/routes/settings.py backend/tests/test_settings.py
git commit -m "feat: add settings CRUD routes (6 endpoints)"
```

---

### Task 5: 会话与消息路由 `routes/conversations.py`

**Files:**
- Create: `backend/app/routes/conversations.py`
- Create: `backend/tests/test_conversations.py`

**Interfaces:**
- Consumes: `api_bp`, `get_db`, `ok`, `fail`, `sse_manager`, `stream_chat`, `decrypt`
- Produces: 8 个注册在 `api_bp` 上的路由处理器

- [ ] **Step 1: 编写测试**

创建 `backend/tests/test_conversations.py`：

```python
import json
from app.database import init_db, get_db


def _setup_db(app):
    with app.app_context():
        init_db()
        db = get_db()
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")
        db.execute("DELETE FROM settings")
        db.commit()

def _create_setting(client):
    """创建一个默认设置，返回其 api_url/api_key/model。"""
    resp = client.post("/api/settings", json={
        "name": "Test", "api_url": "https://api.openai.com/v1", "api_key": "sk-test"
    })
    data = json.loads(resp.get_data(as_text=True))["data"]
    client.put(f"/api/settings/{data['id']}/default")
    return data


class TestConversationsList:
    def test_empty(self, client, app):
        _setup_db(app)
        resp = client.get("/api/conversations")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"] == []

    def test_returns_sorted(self, client, app):
        _setup_db(app)
        client.post("/api/conversations", json={"title": "B"})
        client.post("/api/conversations", json={"title": "A"})

        resp = client.get("/api/conversations")
        items = json.loads(resp.get_data(as_text=True))["data"]
        assert len(items) == 2
        # 按 updated_at DESC
        assert items[0]["title"] == "A"
        assert items[1]["title"] == "B"


class TestConversationsCreate:
    def test_create_default_title(self, client, app):
        _setup_db(app)
        resp = client.post("/api/conversations", json={})
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["title"] == "新对话"


class TestConversationsDetail:
    def test_detail_with_messages(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={"title": "Test"})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.get(f"/api/conversations/{cid}")
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["title"] == "Test"
        assert body["data"]["messages"] == []

    def test_detail_not_found(self, client, app):
        _setup_db(app)
        resp = client.get("/api/conversations/no-such-id")
        assert json.loads(resp.get_data(as_text=True))["code"] == 404


class TestConversationsDelete:
    def test_delete_success(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.delete(f"/api/conversations/{cid}")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0

        # 验证删除
        list_resp = client.get("/api/conversations")
        assert json.loads(list_resp.get_data(as_text=True))["data"] == []


class TestEditMessage:
    def test_edit_user_message(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        # 直接插入一条 user 消息
        with app.app_context():
            db = get_db()
            import uuid
            mid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'user', ?, ?)",
                (mid, cid, "original", "2026-01-01T00:00:00Z"),
            )
            db.commit()

        resp = client.put(f"/api/conversations/{cid}/messages/{mid}", json={
            "content": "edited"
        })
        body = json.loads(resp.get_data(as_text=True))
        assert body["code"] == 0
        assert body["data"]["content"] == "edited"


class TestStop:
    def test_stop_returns_ok(self, client, app):
        _setup_db(app)
        create_resp = client.post("/api/conversations", json={})
        cid = json.loads(create_resp.get_data(as_text=True))["data"]["id"]

        resp = client.post(f"/api/conversations/{cid}/stop")
        assert json.loads(resp.get_data(as_text=True))["code"] == 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_conversations.py -v
```

- [ ] **Step 3: 实现 `routes/conversations.py`**

创建 `backend/app/routes/conversations.py`：

```python
import uuid
from datetime import datetime, timezone
from flask import request, Response, stream_with_context
from app.routes import api_bp
from app.database import get_db, decrypt
from app.utils.response import ok, fail
from app.services.sse_manager import sse_manager
from app.services.ai import stream_chat


def _get_conv_or_404(conv_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM conversations WHERE id = ?", (conv_id,)
    ).fetchone()


def _conv_to_dict(row):
    return dict(row)


def _get_default_settings():
    """获取当前默认 API 配置。"""
    db = get_db()
    row = db.execute(
        "SELECT * FROM settings WHERE is_default = 1 LIMIT 1"
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    # 解密 api_key
    if d.get("api_key"):
        try:
            d["api_key"] = decrypt(d["api_key"])
        except Exception:
            pass
    return d


# ── GET /conversations ─────────────────────────────

@api_bp.route("/conversations")
def list_conversations():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    return ok(data=[_conv_to_dict(r) for r in rows])


# ── POST /conversations ────────────────────────────

@api_bp.route("/conversations", methods=["POST"])
def create_conversation():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip() or "新对话"

    cid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db = get_db()
    db.execute(
        "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (cid, title, now, now),
    )
    db.commit()

    row = _get_conv_or_404(cid)
    return ok(data=_conv_to_dict(row))


# ── GET /conversations/:id ─────────────────────────

@api_bp.route("/conversations/<conv_id>")
def get_conversation(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    db = get_db()
    msgs = db.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()

    data = _conv_to_dict(row)
    data["messages"] = [dict(m) for m in msgs]
    return ok(data=data)


# ── DELETE /conversations/:id ──────────────────────

@api_bp.route("/conversations/<conv_id>", methods=["DELETE"])
def delete_conversation(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    db = get_db()
    db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    db.commit()
    return ok()


# ── POST /conversations/:id/chat (SSE) ─────────────

@api_bp.route("/conversations/<conv_id>/chat", methods=["POST"])
def chat(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = _get_default_settings()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    # 1. 保存 user 消息
    user_msg_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'user', ?, ?)",
        (user_msg_id, conv_id, content, now),
    )
    # 更新会话时间
    db.execute(
        "UPDATE conversations SET updated_at = ?, title = ? WHERE id = ?",
        (now, content[:30], conv_id),
    )
    db.commit()

    # 2. 获取历史消息
    rows = db.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()
    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    # 3. 注册取消信号
    cancel_event = sse_manager.register(conv_id)

    def generate():
        full_content = ""
        assistant_msg_id = str(uuid.uuid4())
        assistant_created = datetime.now(timezone.utc).isoformat()

        try:
            for chunk in stream_chat(
                settings["api_url"],
                settings["api_key"],
                settings["model"],
                messages,
                settings.get("response_format", "text"),
                cancel_event,
            ):
                if "error" in chunk:
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                    break
                if chunk.get("stopped"):
                    yield f"data: {json.dumps({'stopped': True})}\n\n"
                    break
                if chunk.get("delta"):
                    full_content += chunk["delta"]
                    yield f"data: {json.dumps({'delta': chunk['delta'], 'done': False})}\n\n"
                if chunk.get("done"):
                    yield f"data: {json.dumps({'done': True})}\n\n"
        finally:
            # 4. 保存 assistant 消息（即使是部分内容）
            if full_content:
                db2 = get_db()
                db2.execute(
                    "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'assistant', ?, ?)",
                    (assistant_msg_id, conv_id, full_content, assistant_created),
                )
                db2.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), conv_id),
                )
                db2.commit()
            sse_manager.unregister(conv_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── PUT /conversations/:id/messages/:msgId ─────────

@api_bp.route("/conversations/<conv_id>/messages/<msg_id>", methods=["PUT"])
def edit_message(conv_id, msg_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    db = get_db()
    msg = db.execute(
        "SELECT * FROM messages WHERE id = ? AND conversation_id = ?",
        (msg_id, conv_id),
    ).fetchone()
    if not msg:
        return fail(404, "消息不存在", request)
    if msg["role"] != "user":
        return fail(400, "只能编辑用户消息", request)

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    # 更新消息内容
    db.execute("UPDATE messages SET content = ? WHERE id = ?", (content, msg_id))
    # 删除该消息之后的所有消息
    db.execute(
        "DELETE FROM messages WHERE conversation_id = ? AND created_at > ?",
        (conv_id, msg["created_at"]),
    )
    db.commit()

    updated = db.execute("SELECT * FROM messages WHERE id = ?", (msg_id,)).fetchone()
    return ok(data=dict(updated))


# ── POST /conversations/:id/regenerate (SSE) ───────

@api_bp.route("/conversations/<conv_id>/regenerate", methods=["POST"])
def regenerate(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = _get_default_settings()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    db = get_db()
    # 删除最后一条 assistant 消息
    last_assistant = db.execute(
        "SELECT id FROM messages WHERE conversation_id = ? AND role = 'assistant' ORDER BY created_at DESC LIMIT 1",
        (conv_id,),
    ).fetchone()
    if not last_assistant:
        return fail(400, "没有可重新生成的 AI 回复", request)
    db.execute("DELETE FROM messages WHERE id = ?", (last_assistant["id"],))
    db.commit()

    # 获取当前历史消息
    rows = db.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()
    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    cancel_event = sse_manager.register(conv_id)

    def generate():
        full_content = ""
        assistant_msg_id = str(uuid.uuid4())
        assistant_created = datetime.now(timezone.utc).isoformat()
        try:
            for chunk in stream_chat(
                settings["api_url"],
                settings["api_key"],
                settings["model"],
                messages,
                settings.get("response_format", "text"),
                cancel_event,
            ):
                if "error" in chunk:
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                    break
                if chunk.get("stopped"):
                    yield f"data: {json.dumps({'stopped': True})}\n\n"
                    break
                if chunk.get("delta"):
                    full_content += chunk["delta"]
                    yield f"data: {json.dumps({'delta': chunk['delta'], 'done': False})}\n\n"
                if chunk.get("done"):
                    yield f"data: {json.dumps({'done': True})}\n\n"
        finally:
            if full_content:
                db2 = get_db()
                db2.execute(
                    "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'assistant', ?, ?)",
                    (assistant_msg_id, conv_id, full_content, assistant_created),
                )
                db2.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), conv_id),
                )
                db2.commit()
            sse_manager.unregister(conv_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── POST /conversations/:id/stop ───────────────────

@api_bp.route("/conversations/<conv_id>/stop", methods=["POST"])
def stop_generation(conv_id):
    cancelled = sse_manager.cancel(conv_id)
    if cancelled:
        return ok(message="已发送停止信号")
    return ok(message="没有正在进行的生成")
```

_（注意：SSE 路由中使用了 `json` 模块，需要在文件顶部添加 `import json`）_

- [ ] **Step 4: 在文件顶部添加缺失的 import**

确认 `backend/app/routes/conversations.py` 顶部包含：

```python
import uuid
import json
from datetime import datetime, timezone
from flask import request, Response, stream_with_context
from app.routes import api_bp
from app.database import get_db, decrypt
from app.utils.response import ok, fail
from app.services.sse_manager import sse_manager
from app.services.ai import stream_chat
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_conversations.py -v
```

- [ ] **Step 6: 提交**

```bash
git add backend/app/routes/conversations.py backend/tests/test_conversations.py
git commit -m "feat: add conversation & message routes (8 endpoints)"
```

---

### Task 6: 路由注册与依赖更新

**Files:**
- Modify: `backend/app/__init__.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 注册新路由模块**

编辑 `backend/app/__init__.py`，在 `import app.routes.example` 之后添加新路由导入：

找到：
```python
    from app.routes import api_bp
    import app.routes.example  # noqa — 必须在 register 前导入，注册 /api/hello
```

替换为：
```python
    from app.routes import api_bp
    import app.routes.example        # noqa — 必须在 register 前导入，注册 /api/hello
    import app.routes.settings       # noqa — 注册 /api/settings 路由
    import app.routes.conversations  # noqa — 注册 /api/conversations 路由
```

- [ ] **Step 2: 添加 requests 依赖**

编辑 `backend/requirements.txt`，追加一行：

```
flask>=3.0
flask-cors>=4.0
cryptography>=41.0
requests>=2.31
```

- [ ] **Step 3: 安装依赖并启动验证**

```bash
cd backend && pip install -r requirements.txt -q
python run.py
```

另一个终端测试：

```bash
curl http://127.0.0.1:5000/api/hello
# 预期：{"code":0,"data":{"message":"Hello from Flask!"},"message":"ok"}

curl http://127.0.0.1:5000/api/settings
# 预期：{"code":0,"data":[],"message":"ok"}

curl http://127.0.0.1:5000/api/conversations
# 预期：{"code":0,"data":[],"message":"ok"}
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/__init__.py backend/requirements.txt
git commit -m "feat: register settings & conversations routes, add requests dep"
```

---

### Task 7: 端到端集成测试

**Files:**
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: 编写集成测试**

创建 `backend/tests/test_integration.py`：

```python
"""
端到端测试：预设创建 → 会话创建 → 消息编辑 → 删除
不涉及真实 AI 调用（chat/regenerate 使用 mock）。
"""
import json
from unittest.mock import patch
from app.database import init_db, get_db


def _setup_db(app):
    with app.app_context():
        init_db()
        db = get_db()
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM conversations")
        db.execute("DELETE FROM settings")
        db.commit()


class TestFullWorkflow:
    def test_settings_crud_workflow(self, client, app):
        """完整预设管理流程。"""
        _setup_db(app)

        # 1. 创建预设
        r = client.post("/api/settings", json={
            "name": "OpenAI", "api_url": "https://api.openai.com/v1", "api_key": "sk-test"
        })
        assert json.loads(r.get_data(as_text=True))["code"] == 0
        sid = json.loads(r.get_data(as_text=True))["data"]["id"]

        # 2. 设为默认
        r = client.put(f"/api/settings/{sid}/default")
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 3. 更新预设
        r = client.put(f"/api/settings/{sid}", json={
            "name": "OpenAI Updated", "api_url": "https://api.openai.com/v1",
            "api_key": "", "model": "gpt-4o",
        })
        body = json.loads(r.get_data(as_text=True))
        assert body["data"]["name"] == "OpenAI Updated"

        # 4. 创建第二个预设
        r = client.post("/api/settings", json={
            "name": "Ollama", "api_url": "http://localhost:11434/v1", "api_key": ""
        })
        sid2 = json.loads(r.get_data(as_text=True))["data"]["id"]

        # 5. 删除非默认预设
        r = client.delete(f"/api/settings/{sid2}")
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 6. 列表应剩 1 个
        r = client.get("/api/settings")
        assert len(json.loads(r.get_data(as_text=True))["data"]) == 1

    def test_conversations_workflow(self, client, app):
        """完整对话 CRUD 流程（不涉及 AI）。"""
        _setup_db(app)

        # 创建两个对话
        r1 = client.post("/api/conversations", json={"title": "测试对话"})
        cid = json.loads(r1.get_data(as_text=True))["data"]["id"]
        client.post("/api/conversations", json={"title": "另一个对话"})

        # 列表应有 2 个
        r = client.get("/api/conversations")
        assert len(json.loads(r.get_data(as_text=True))["data"]) == 2

        # 查看详情
        r = client.get(f"/api/conversations/{cid}")
        body = json.loads(r.get_data(as_text=True))
        assert body["data"]["title"] == "测试对话"
        assert body["data"]["messages"] == []

        # 删除
        r = client.delete(f"/api/conversations/{cid}")
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 列表应剩 1 个
        r = client.get("/api/conversations")
        assert len(json.loads(r.get_data(as_text=True))["data"]) == 1

    def test_edit_message_truncates_following(self, client, app):
        """编辑消息后，后续消息应被删除。"""
        _setup_db(app)

        # 创建会话并插入多条消息
        r = client.post("/api/conversations", json={"title": "Test"})
        cid = json.loads(r.get_data(as_text=True))["data"]["id"]

        import uuid
        with app.app_context():
            db = get_db()
            m1 = str(uuid.uuid4())
            m2 = str(uuid.uuid4())
            m3 = str(uuid.uuid4())
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'user', ?, '2026-01-01T00:00:01Z')",
                (m1, cid, "问题1"),
            )
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'assistant', ?, '2026-01-01T00:00:02Z')",
                (m2, cid, "回答1"),
            )
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'user', ?, '2026-01-01T00:00:03Z')",
                (m3, cid, "问题2"),
            )
            db.commit()

        # 编辑第一条消息
        r = client.put(f"/api/conversations/{cid}/messages/{m1}", json={
            "content": "修改后的问题"
        })
        assert json.loads(r.get_data(as_text=True))["code"] == 0

        # 详情应只剩 1 条（编辑后的 m1，m2 和 m3 被截断删除）
        r = client.get(f"/api/conversations/{cid}")
        body = json.loads(r.get_data(as_text=True))
        assert len(body["data"]["messages"]) == 1
        assert body["data"]["messages"][0]["content"] == "修改后的问题"
```

- [ ] **Step 2: 运行集成测试**

```bash
cd backend && python -m pytest tests/test_integration.py -v
```

- [ ] **Step 3: 运行全部测试**

```bash
cd backend && python -m pytest tests/ -v
```

预期：所有测试 PASS（共约 25+ 个测试）

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add end-to-end integration tests"
```

---

## 验收清单

- [ ] `GET /api/hello` 仍正常（不破坏已有路由）
- [ ] `GET /api/settings` 返回空列表
- [ ] `POST /api/settings` → 创建预设，api_key 加密存储
- [ ] `PUT /api/settings/:id` → 更新预设，空 api_key 保留原值
- [ ] `DELETE /api/settings/:id` → 拒绝删除默认预设（409）
- [ ] `PUT /api/settings/:id/default` → 切换默认，同类互斥
- [ ] `GET/POST/DELETE /api/conversations` → 基本 CRUD
- [ ] `GET /api/conversations/:id` → 详情含 messages 数组
- [ ] `PUT /api/conversations/:id/messages/:msgId` → 编辑截断后续
- [ ] `POST /api/conversations/:id/stop` → 取消信号正常
- [ ] `POST /api/conversations/:id/chat` → SSE 格式正确（需 mock AI）
- [ ] `POST /api/conversations/:id/regenerate` → 删除最后 assistant 后重生成
- [ ] 所有错误响应 `code ≠ 0`，正常响应 `code === 0`
- [ ] 错误写入 `user_data/logs/error.log`
