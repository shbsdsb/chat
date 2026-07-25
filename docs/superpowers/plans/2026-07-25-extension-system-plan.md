# 扩展系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Chat 构建前后端扩展系统 MVP，支持扩展的安装/卸载/启停，提供 `chat.post_receive` 后端钩子和 `message_decorator` 前端扩展点，并用"上下文命中率分析"示例扩展验证全流程。

**Architecture:** 后端 ExtensionManager 单例管理扩展生命周期（注册表/安装/加载/钩子调度），前端 ExtensionSlot 组件动态加载扩展的 Vue 组件。扩展以本地文件夹形式存放在 `user_data/extensions/<id>/`，通过 `manifest.json` 声明权限和扩展点。

**Tech Stack:** Python 3 + Flask（后端扩展加载），Vue 3 + Pinia（前端扩展运行时），现有 JSON 文件存储保持不变。

## Global Constraints

- 所有扩展代码在 `user_data/extensions/` 下，注册表 `.registry.json` 同目录
- 后端扩展入口文件固定命名为 `backend.py`，导出命名函数匹配扩展点
- 前端扩展入口固定为 `frontend/index.js`，导出 `{ ext_points, components }`
- Manifest 必须包含 id/name/version/permissions/ext_points 字段
- MVP 安全模型：manifest 声明权限 + 安装审批，同进程运行

---

## File Structure

```
Create:
  backend/app/extensions/__init__.py          # ExtensionManager 单例
  backend/app/extensions/registry.py          # .registry.json 读写
  backend/app/extensions/installer.py         # git clone / zip 解压 / 删除
  backend/app/extensions/loader.py            # 加载/卸载 backend.py 模块
  backend/app/extensions/permissions.py       # 权限检查工具函数
  backend/app/extensions/hooks.py             # 钩子调度器
  backend/app/routes/extensions.py            # /api/extensions CRUD 路由
  backend/tests/test_extensions.py            # 扩展系统测试
  frontend/src/api/extensions.js              # 扩展管理 API 调用
  frontend/src/stores/extensions.js           # Pinia 扩展状态
  frontend/src/extensions/ExtensionSlot.vue   # 扩展点插槽组件
  frontend/src/extensions/useExtensionApi.js  # 扩展可用的 Core API
  frontend/src/components/ExtensionManager.vue # 扩展管理 UI
  user_data/extensions/hit-rate-analyzer/manifest.json  # 示例扩展 manifest
  user_data/extensions/hit-rate-analyzer/backend.py     # 示例扩展后端
  user_data/extensions/hit-rate-analyzer/frontend/index.js      # 示例扩展前端入口
  user_data/extensions/hit-rate-analyzer/frontend/components/HitRateBadge.js

Modify:
  backend/app/__init__.py                     # 注册扩展蓝图 + 加载扩展
  backend/app/routes/conversations.py         # 在 _stream_and_save 中调用钩子
  frontend/src/components/MessageBubble.vue   # 渲染 ExtensionSlot
  frontend/src/components/SettingsDrawer.vue  # 添加扩展管理入口
```

---

### Task 1: 扩展注册表存储（registry.py）

**Files:**
- Create: `backend/app/extensions/registry.py`
- Create: `backend/tests/test_extensions.py` (第一条测试)

**Interfaces:**
- Produces: `get_registry_path() -> str`, `read_registry() -> dict`, `write_registry(data: dict) -> None`, `get_extension(ext_id: str) -> dict | None`, `add_extension(ext_id: str, info: dict) -> None`, `remove_extension(ext_id: str) -> None`, `set_extension_state(ext_id: str, enabled: bool) -> None`

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_extensions.py
import os
import pytest
from app.extensions.registry import (
    get_registry_path, read_registry, write_registry,
    get_extension, add_extension, remove_extension, set_extension_state,
)

def test_registry_path_under_extensions_dir():
    path = get_registry_path()
    assert path.endswith(os.path.join("user_data", "extensions", ".registry.json"))

def test_read_registry_returns_empty_when_no_file():
    data = read_registry()
    assert data == {"extensions": {}}

def test_write_and_read_registry(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    write_registry({"extensions": {"test-ext": {"enabled": True, "version": "1.0.0"}}})
    data = read_registry()
    assert data["extensions"]["test-ext"]["enabled"] is True

def test_add_extension(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {"version": "1.0.0", "enabled": True, "installed_at": "2026-01-01T00:00:00Z", "install_method": "zip", "permissions_granted": ["hook:chat"]})
    ext = get_extension("test-ext")
    assert ext["version"] == "1.0.0"
    assert ext["enabled"] is True

def test_remove_extension(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {"version": "1.0.0", "enabled": True, "installed_at": "2026-01-01T00:00:00Z", "install_method": "zip", "permissions_granted": []})
    remove_extension("test-ext")
    assert get_extension("test-ext") is None

def test_set_extension_state(tmp_path, monkeypatch):
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {"version": "1.0.0", "enabled": True, "installed_at": "2026-01-01T00:00:00Z", "install_method": "zip", "permissions_granted": []})
    set_extension_state("test-ext", False)
    assert get_extension("test-ext")["enabled"] is False
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_extensions.py -v
```
Expected: 全部 FAIL（模块尚未创建）

- [ ] **Step 3: 实现 registry.py**

```python
# backend/app/extensions/registry.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_extensions.py -v
```
Expected: 6 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/extensions/__init__.py backend/app/extensions/registry.py backend/tests/test_extensions.py
git commit -m "feat: add extension registry storage (.registry.json)"
```

---

### Task 2: 扩展安装器（installer.py）

**Files:**
- Create: `backend/app/extensions/installer.py`

**Interfaces:**
- Consumes: `get_registry_path()` (Task 1 中的 EXTENSIONS_DIR 路径)
- Produces: `install_from_git(url: str, branch: str) -> tuple[str, str]`, `install_from_zip(zip_path: str) -> tuple[str, str]`, `uninstall_extension(ext_id: str) -> None`, `update_extension(ext_id: str) -> str`

- [ ] **Step 1: 编写测试**

```python
# 追加到 backend/tests/test_extensions.py

import os
import zipfile
import subprocess
from app.extensions.installer import (
    install_from_zip, uninstall_extension, get_extensions_dir
)

def test_install_from_zip(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    os.makedirs(ext_dir)

    # 创建测试 zip
    zip_path = tmp_path / "test-ext.zip"
    manifest = {"id": "test-ext", "name": "Test", "version": "1.0.0",
                "permissions": [], "ext_points": {"backend": [], "frontend": []},
                "min_app_version": "1.0.0"}
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("backend.py", "def on_chat_post_receive(ctx): return None\n")

    result = install_from_zip(str(zip_path))
    assert result[0] == "test-ext"  # (ext_id, name)
    assert os.path.isfile(os.path.join(ext_dir, "test-ext", "manifest.json"))
    assert os.path.isfile(os.path.join(ext_dir, "test-ext", "backend.py"))

def test_install_from_zip_invalid_no_manifest(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("readme.txt", "no manifest here")
    with pytest.raises(ValueError, match="manifest.json"):
        install_from_zip(str(zip_path))

def test_uninstall_extension(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    ext_path = os.path.join(ext_dir, "to-remove")
    os.makedirs(ext_path)
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        f.write("{}")
    uninstall_extension("to-remove")
    assert not os.path.exists(ext_path)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_extensions.py::test_install_from_zip tests/test_extensions.py::test_install_from_zip_invalid_no_manifest tests/test_extensions.py::test_uninstall_extension -v
```
Expected: FAIL

- [ ] **Step 3: 实现 installer.py**

```python
# backend/app/extensions/installer.py
import json
import os
import shutil
import subprocess
import tempfile
import zipfile

_PACKAGE_DIR = os.path.dirname(__file__)
EXTENSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(_PACKAGE_DIR)),
    "user_data", "extensions"
)


def get_extensions_dir():
    return EXTENSIONS_DIR


def _read_manifest(ext_dir):
    path = os.path.join(ext_dir, "manifest.json")
    if not os.path.isfile(path):
        raise ValueError("扩展缺少 manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_manifest(manifest):
    required = ["id", "name", "version", "permissions", "ext_points", "min_app_version"]
    for key in required:
        if key not in manifest:
            raise ValueError(f"manifest.json 缺少必填字段: {key}")
    if not isinstance(manifest["permissions"], list):
        raise ValueError("permissions 必须是数组")
    if not isinstance(manifest["ext_points"], dict):
        raise ValueError("ext_points 必须是对象")


def install_from_git(url, branch="main"):
    os.makedirs(EXTENSIONS_DIR, exist_ok=True)
    ext_id = None
    clone_dir = tempfile.mkdtemp(dir=EXTENSIONS_DIR)
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, url, clone_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git clone 失败: {result.stderr}")

        manifest = _read_manifest(clone_dir)
        _validate_manifest(manifest)
        ext_id = manifest["id"]

        target_dir = os.path.join(EXTENSIONS_DIR, ext_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.rename(clone_dir, target_dir)

        return ext_id, manifest["name"]
    finally:
        if os.path.exists(clone_dir) and ext_id is None:
            shutil.rmtree(clone_dir, ignore_errors=True)


def install_from_zip(zip_path):
    os.makedirs(EXTENSIONS_DIR, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(dir=EXTENSIONS_DIR)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        # 处理 zip 内可能含有一层目录的情况
        entries = os.listdir(tmp_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(tmp_dir, entries[0])):
            inner_dir = os.path.join(tmp_dir, entries[0])
        else:
            inner_dir = tmp_dir

        manifest = _read_manifest(inner_dir)
        _validate_manifest(manifest)
        ext_id = manifest["id"]

        target_dir = os.path.join(EXTENSIONS_DIR, ext_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.move(inner_dir, target_dir)

        return ext_id, manifest["name"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def uninstall_extension(ext_id):
    ext_dir = os.path.join(EXTENSIONS_DIR, ext_id)
    if os.path.isdir(ext_dir):
        shutil.rmtree(ext_dir, ignore_errors=True)


def update_extension(ext_id):
    ext_dir = os.path.join(EXTENSIONS_DIR, ext_id)
    if not os.path.isdir(ext_dir):
        raise FileNotFoundError(f"扩展 {ext_id} 未安装")

    result = subprocess.run(
        ["git", "-C", ext_dir, "pull", "--ff-only"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git pull 失败: {result.stderr}")

    manifest = _read_manifest(ext_dir)
    return manifest["version"]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_extensions.py -v -k "install or uninstall"
```
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/extensions/installer.py backend/tests/test_extensions.py
git commit -m "feat: add extension installer (git clone / zip extract / delete)"
```

---

### Task 3: 权限检查（permissions.py）

**Files:**
- Create: `backend/app/extensions/permissions.py`

**Interfaces:**
- Produces: `check_permission(ext_id: str, permission: str) -> bool`, `validate_permissions(declared: list) -> list`

- [ ] **Step 1: 编写测试**

```python
# 追加到 backend/tests/test_extensions.py

from app.extensions.permissions import check_permission, validate_permissions, VALID_PERMISSIONS

def test_validate_permissions_filters_invalid():
    result = validate_permissions(["hook:chat", "read:conversations", "invalid:perm"])
    assert "hook:chat" in result
    assert "read:conversations" in result
    assert "invalid:perm" not in result

def test_check_permission_granted(tmp_path, monkeypatch):
    from app.extensions.registry import add_extension
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    monkeypatch.setattr("app.extensions.permissions.get_registry_path", lambda: str(reg_file))
    add_extension("test-ext", {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat", "read:conversations"]
    })
    assert check_permission("test-ext", "hook:chat") is True
    assert check_permission("test-ext", "read:world_info") is False

def test_check_permission_disabled_extension(tmp_path, monkeypatch):
    from app.extensions.registry import add_extension
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    monkeypatch.setattr("app.extensions.permissions.get_registry_path", lambda: str(reg_file))
    add_extension("disabled-ext", {
        "version": "1.0.0", "enabled": False,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat"]
    })
    assert check_permission("disabled-ext", "hook:chat") is False
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_extensions.py -v -k "permission"
```
Expected: FAIL

- [ ] **Step 3: 实现 permissions.py**

```python
# backend/app/extensions/permissions.py
from .registry import get_extension

VALID_PERMISSIONS = {
    "read:conversations",
    "read:world_info",
    "write:conversations",
    "hook:chat",
    "register:provider",
    "network",
}


def validate_permissions(declared):
    return [p for p in declared if p in VALID_PERMISSIONS]


def check_permission(ext_id, permission):
    ext = get_extension(ext_id)
    if not ext or not ext.get("enabled", False):
        return False
    return permission in ext.get("permissions_granted", [])
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_extensions.py -v -k "permission"
```
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/extensions/permissions.py backend/tests/test_extensions.py
git commit -m "feat: add extension permission check utilities"
```

---

### Task 4: 钩子调度器（hooks.py）

**Files:**
- Create: `backend/app/extensions/hooks.py`

**Interfaces:**
- Produces: `HookDispatcher` class with `dispatch(ext_point: str, ctx: dict) -> list[dict]`, `register_hook(ext_id: str, ext_point: str, handler: callable)`, `unregister_extension(ext_id: str)`

- [ ] **Step 1: 编写测试**

```python
# 追加到 backend/tests/test_extensions.py

from app.extensions.hooks import HookDispatcher

class TestHookDispatcher:
    def test_dispatch_calls_registered_handler(self):
        dispatcher = HookDispatcher()
        results = []
        def handler(ctx):
            results.append(ctx["value"])
            return {"meta": {"hit": ctx["value"]}}
        dispatcher.register_hook("test-ext", "chat.post_receive", handler)
        output = dispatcher.dispatch("chat.post_receive", {"value": 42})
        assert results == [42]
        assert output == [{"extension_id": "test-ext", "message_meta": {"hit": 42}}]

    def test_dispatch_multiple_extensions(self):
        dispatcher = HookDispatcher()
        calls = []
        dispatcher.register_hook("ext-a", "chat.post_receive", lambda ctx: calls.append("a"))
        dispatcher.register_hook("ext-b", "chat.post_receive", lambda ctx: calls.append("b"))
        dispatcher.dispatch("chat.post_receive", {})
        assert calls == ["a", "b"]

    def test_dispatch_handler_exception_does_not_block_others(self):
        dispatcher = HookDispatcher()
        calls = []
        def bad_handler(ctx):
            raise RuntimeError("boom")
        dispatcher.register_hook("bad-ext", "chat.post_receive", bad_handler)
        dispatcher.register_hook("good-ext", "chat.post_receive", lambda ctx: calls.append("good"))
        dispatcher.dispatch("chat.post_receive", {})
        assert calls == ["good"]

    def test_unregister_extension_removes_handlers(self):
        dispatcher = HookDispatcher()
        dispatcher.register_hook("test-ext", "chat.post_receive", lambda ctx: None)
        dispatcher.unregister_extension("test-ext")
        output = dispatcher.dispatch("chat.post_receive", {})
        assert output == []

    def test_dispatch_unknown_ext_point(self):
        dispatcher = HookDispatcher()
        output = dispatcher.dispatch("nonexistent", {})
        assert output == []
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_extensions.py -v -k "HookDispatcher"
```
Expected: FAIL

- [ ] **Step 3: 实现 hooks.py**

```python
# backend/app/extensions/hooks.py
import logging
import threading

logger = logging.getLogger(__name__)


class HookDispatcher:
    def __init__(self):
        self._handlers = {}   # {ext_point: [(ext_id, handler), ...]}
        self._lock = threading.Lock()

    def register_hook(self, ext_id, ext_point, handler):
        with self._lock:
            self._handlers.setdefault(ext_point, []).append(
                (ext_id, handler)
            )

    def unregister_extension(self, ext_id):
        with self._lock:
            for ext_point in list(self._handlers):
                self._handlers[ext_point] = [
                    (eid, h) for eid, h in self._handlers[ext_point]
                    if eid != ext_id
                ]

    def dispatch(self, ext_point, ctx):
        results = []
        handlers = list(self._handlers.get(ext_point, []))
        for ext_id, handler in handlers:
            try:
                result = handler(ctx)
                if result is not None:
                    if isinstance(result, dict):
                        result.setdefault("extension_id", ext_id)
                        results.append(result)
                    else:
                        results.append({
                            "extension_id": ext_id,
                            "message_meta": result,
                        })
            except Exception:
                logger.exception(
                    f"扩展 {ext_id} 的钩子 {ext_point} 执行异常"
                )
        return results
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_extensions.py -v -k "HookDispatcher"
```
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/extensions/hooks.py backend/tests/test_extensions.py
git commit -m "feat: add hook dispatcher for extension points"
```

---

### Task 5: 扩展加载器（loader.py）

**Files:**
- Create: `backend/app/extensions/loader.py`

**Interfaces:**
- Consumes: `HookDispatcher` (Task 4), `check_permission` (Task 3), `get_extension` (Task 1), `read_registry` (Task 1)
- Produces: `load_extension(ext_id: str, dispatcher: HookDispatcher) -> dict`, `unload_extension(ext_id: str, dispatcher: HookDispatcher) -> None`, `load_all_enabled(dispatcher: HookDispatcher) -> dict`

- [ ] **Step 1: 编写测试**

```python
# 追加到 backend/tests/test_extensions.py

import os
import json
import sys
from app.extensions.loader import load_extension, unload_extension, load_all_enabled

def test_load_extension_registers_hooks(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))

    # 创建扩展目录
    ext_path = os.path.join(ext_dir, "test-loader")
    os.makedirs(ext_path)
    manifest = {"id": "test-loader", "name": "Loader Test", "version": "1.0.0",
                "permissions": ["hook:chat"], "ext_points": {"backend": ["chat.post_receive"]},
                "min_app_version": "1.0.0"}
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        json.dump(manifest, f)
    with open(os.path.join(ext_path, "backend.py"), "w") as f:
        f.write("def on_chat_post_receive(ctx): return {'hit': len(ctx.get('messages', []))}\n")

    # 注册到注册表
    from app.extensions.registry import add_extension, write_registry
    write_registry({"extensions": {}})
    add_extension("test-loader", {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat"]
    })

    from app.extensions.hooks import HookDispatcher
    dispatcher = HookDispatcher()
    result = load_extension("test-loader", dispatcher)
    assert result["status"] == "loaded"

    output = dispatcher.dispatch("chat.post_receive", {"messages": [1, 2, 3]})
    assert len(output) == 1
    assert output[0]["message_meta"]["hit"] == 3

def test_load_extension_missing_backend_py(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))

    ext_path = os.path.join(ext_dir, "no-backend")
    os.makedirs(ext_path)
    manifest = {"id": "no-backend", "name": "No Backend", "version": "1.0.0",
                "permissions": [], "ext_points": {"frontend": ["message_decorator"]},
                "min_app_version": "1.0.0"}
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        json.dump(manifest, f)

    from app.extensions.registry import add_extension, write_registry
    write_registry({"extensions": {}})
    add_extension("no-backend", {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": []
    })

    from app.extensions.hooks import HookDispatcher
    dispatcher = HookDispatcher()
    result = load_extension("no-backend", dispatcher)
    # 纯前端扩展加载应该成功
    assert result["status"] == "loaded"

def test_unload_extension_removes_from_dispatcher(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))

    ext_path = os.path.join(ext_dir, "to-unload")
    os.makedirs(ext_path)
    with open(os.path.join(ext_path, "manifest.json"), "w") as f:
        json.dump({"id": "to-unload", "name": "X", "version": "1.0.0",
                   "permissions": ["hook:chat"], "ext_points": {"backend": ["chat.post_receive"]},
                   "min_app_version": "1.0.0"}, f)
    with open(os.path.join(ext_path, "backend.py"), "w") as f:
        f.write("def on_chat_post_receive(ctx): return None\n")

    from app.extensions.hooks import HookDispatcher
    dispatcher = HookDispatcher()
    load_extension("to-unload", dispatcher)
    unload_extension("to-unload", dispatcher)
    output = dispatcher.dispatch("chat.post_receive", {})
    assert output == []
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/test_extensions.py -v -k "load"
```
Expected: FAIL

- [ ] **Step 3: 实现 loader.py**

```python
# backend/app/extensions/loader.py
import importlib.util
import json
import logging
import os
import sys

from .registry import get_extension, read_registry
from .permissions import check_permission

logger = logging.getLogger(__name__)

_PACKAGE_DIR = os.path.dirname(__file__)
EXTENSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(_PACKAGE_DIR)),
    "user_data", "extensions"
)

EXT_POINT_TO_FUNC = {
    "chat.post_receive": "on_chat_post_receive",
    "chat.pre_send": "on_chat_pre_send",
}


def _load_backend_module(ext_id, ext_dir):
    """用 importlib 加载 backend.py 为独立模块"""
    backend_path = os.path.join(ext_dir, "backend.py")
    if not os.path.isfile(backend_path):
        return None
    module_name = f"_ext_{ext_id.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, backend_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_extension(ext_id, dispatcher):
    ext = get_extension(ext_id)
    if not ext:
        return {"status": "error", "message": f"扩展 {ext_id} 未在注册表中找到"}
    if not ext.get("enabled"):
        return {"status": "error", "message": f"扩展 {ext_id} 已禁用"}

    ext_dir = os.path.join(EXTENSIONS_DIR, ext_id)
    if not os.path.isdir(ext_dir):
        return {"status": "error", "message": f"扩展目录不存在: {ext_dir}"}

    # 读取 manifest 获取声明的扩展点
    manifest_path = os.path.join(ext_dir, "manifest.json")
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        return {"status": "error", "message": "manifest.json 不存在"}

    # 加载后端模块
    module = _load_backend_module(ext_id, ext_dir)
    if module is None:
        # 纯前端扩展，不注册后端钩子
        return {"status": "loaded", "frontend_only": True}

    backend_points = manifest.get("ext_points", {}).get("backend", [])
    registered = []

    for ext_point in backend_points:
        if ext_point not in EXT_POINT_TO_FUNC:
            continue
        func_name = EXT_POINT_TO_FUNC[ext_point]
        handler = getattr(module, func_name, None)
        if handler is None:
            continue
        dispatcher.register_hook(ext_id, ext_point, handler)
        registered.append(ext_point)

    return {
        "status": "loaded",
        "registered_hooks": registered,
        "manifest": manifest,
    }


def unload_extension(ext_id, dispatcher):
    dispatcher.unregister_extension(ext_id)
    # 清理 sys.modules 中的模块缓存
    module_name = f"_ext_{ext_id.replace('-', '_')}"
    sys.modules.pop(module_name, None)


def load_all_enabled(dispatcher):
    """启动时加载所有已启用的扩展"""
    data = read_registry()
    results = {}
    for ext_id, info in data.get("extensions", {}).items():
        if info.get("enabled"):
            try:
                results[ext_id] = load_extension(ext_id, dispatcher)
            except Exception:
                logger.exception(f"加载扩展 {ext_id} 失败")
                results[ext_id] = {"status": "error", "message": "加载异常"}
    return results
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/test_extensions.py -v -k "load"
```
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/extensions/loader.py backend/tests/test_extensions.py
git commit -m "feat: add extension loader (import backend.py, register hooks)"
```

---

### Task 6: ExtensionManager 单例（`__init__.py`）

**Files:**
- Create: `backend/app/extensions/__init__.py`

**Interfaces:**
- Consumes: 所有 Task 1-5 的模块
- Produces: `ExtensionManager` 单例（封装 `dispatcher` + `load_all_enabled` + `reload_extension`）, `get_extension_manager() -> ExtensionManager`

- [ ] **Step 1: 实现 `__init__.py`**

```python
# backend/app/extensions/__init__.py
import logging

from .hooks import HookDispatcher
from .registry import read_registry, add_extension, remove_extension, set_extension_state
from .installer import install_from_git, install_from_zip, uninstall_extension, update_extension
from .loader import load_extension, unload_extension, load_all_enabled
from .permissions import check_permission, validate_permissions

logger = logging.getLogger(__name__)

_manager = None


class ExtensionManager:
    def __init__(self):
        self.dispatcher = HookDispatcher()
        self._loaded = {}

    def init(self):
        """启动时初始化：加载所有已启用扩展"""
        self._loaded = load_all_enabled(self.dispatcher)
        logger.info(f"扩展初始化完成: {self._loaded}")

    def reload_extension(self, ext_id):
        """重新加载单个扩展（安装/更新后调用）"""
        unload_extension(ext_id, self.dispatcher)
        result = load_extension(ext_id, self.dispatcher)
        self._loaded[ext_id] = result
        return result

    def list_loaded(self):
        return dict(self._loaded)


def get_extension_manager():
    global _manager
    if _manager is None:
        _manager = ExtensionManager()
    return _manager
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/extensions/__init__.py
git commit -m "feat: add ExtensionManager singleton"
```

---

### Task 7: `/api/extensions` 路由

**Files:**
- Create: `backend/app/routes/extensions.py`

**Interfaces:**
- Consumes: `ExtensionManager` (Task 6), `api_bp` (已有), `ok`/`fail` (已有)
- Produces: 6 个 API 端点（list/install/uninstall/update/toggle/manifest）

- [ ] **Step 1: 编写测试**

```python
# 追加到 backend/tests/test_extensions.py

import io
import zipfile
from app import create_app

@pytest.fixture
def client_with_ext_dir(tmp_path, monkeypatch):
    """创建带隔离扩展目录的测试客户端"""
    ext_dir = tmp_path / "extensions"
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    # 重置 ExtensionManager
    import app.extensions
    app.extensions._manager = app.extensions.ExtensionManager()
    app_mock = create_app()
    app_mock.config["TESTING"] = True
    return app_mock.test_client(), tmp_path

def test_list_extensions_empty(client_with_ext_dir):
    client, _ = client_with_ext_dir
    resp = client.get("/api/extensions")
    data = resp.get_json()
    assert data["code"] == 0
    assert data["data"] == []

def test_install_from_zip(client_with_ext_dir):
    client, tmp_path = client_with_ext_dir
    zip_path = tmp_path / "test.zip"
    manifest = {"id": "api-test-ext", "name": "API Test", "version": "1.0.0",
                "permissions": [], "ext_points": {"backend": [], "frontend": []},
                "min_app_version": "1.0.0"}
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("backend.py", "")

    data = {"install_method": "zip"}
    resp = client.post("/api/extensions/install",
                       data={"install_method": "zip", "git_url": ""},
                       content_type="multipart/form-data",
                       buffered=True,
                       data_content={"file": (open(zip_path, "rb"), "test.zip")})

# 注：Flask 测试客户端处理文件上传较复杂，此处用直接导入函数测试
def test_api_install_via_zip_integration(tmp_path, monkeypatch):
    ext_dir = tmp_path / "extensions"
    reg_file = tmp_path / ".registry.json"
    monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
    monkeypatch.setattr("app.extensions.registry.get_registry_path", lambda: str(reg_file))
    monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))

    from app.extensions.registry import write_registry
    write_registry({"extensions": {}})

    from app.extensions import ExtensionManager
    mgr = ExtensionManager()

    from app.extensions.installer import install_from_zip
    zip_path = tmp_path / "test.zip"
    manifest = {"id": "api-integration", "name": "Integration Test", "version": "1.0.0",
                "permissions": ["hook:chat"], "ext_points": {"backend": ["chat.post_receive"]},
                "min_app_version": "1.0.0"}
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("backend.py", "def on_chat_post_receive(ctx): return None\n")

    ext_id, name = install_from_zip(str(zip_path))

    from app.extensions.registry import add_extension
    add_extension(ext_id, {
        "version": "1.0.0", "enabled": True,
        "installed_at": "2026-01-01T00:00:00Z",
        "install_method": "zip",
        "permissions_granted": ["hook:chat"]
    })

    result = mgr.reload_extension(ext_id)
    assert result["status"] == "loaded"

    from app.extensions.registry import get_extension
    ext = get_extension(ext_id)
    assert ext["enabled"] is True

    mgr.dispatcher.dispatch("chat.post_receive", {})
```

- [ ] **Step 2: 实现 routes/extensions.py**

```python
# backend/app/routes/extensions.py
import os
import json
from datetime import datetime, timezone

from flask import request
from app.routes import api_bp
from app.utils.response import ok, fail
from app.extensions import get_extension_manager
from app.extensions.installer import (
    install_from_git, install_from_zip, uninstall_extension, update_extension,
)
from app.extensions.registry import (
    read_registry, add_extension, remove_extension,
    get_extension, set_extension_state,
)
from app.extensions.permissions import validate_permissions


def _check_ext_exists(ext_id):
    ext = get_extension(ext_id)
    if not ext:
        return None
    return ext


@api_bp.route("/extensions")
def list_extensions():
    data = read_registry()
    exts = data.get("extensions", {})
    result = []
    for ext_id, info in exts.items():
        entry = {"id": ext_id, **info}
        # 尝试读取 manifest 获取扩展名
        from app.extensions.installer import EXTENSIONS_DIR
        manifest_path = os.path.join(EXTENSIONS_DIR, ext_id, "manifest.json")
        if os.path.isfile(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                m = json.load(f)
                entry["name"] = m.get("name", ext_id)
                entry["description"] = m.get("description", "")
                entry["frontend"] = bool(m.get("ext_points", {}).get("frontend"))
        else:
            entry["name"] = ext_id
            entry["description"] = ""
            entry["frontend"] = False
        result.append(entry)
    return ok(data=result)


@api_bp.route("/extensions/install", methods=["POST"])
def install_extension():
    install_method = request.form.get("install_method", "zip")

    try:
        if install_method == "git":
            git_url = (request.form.get("git_url") or "").strip()
            git_branch = (request.form.get("git_branch") or "main").strip()
            if not git_url:
                return fail(400, "缺少 git_url")
            ext_id, name = install_from_git(git_url, git_branch)
        elif install_method == "zip":
            uploaded = request.files.get("file")
            if not uploaded:
                return fail(400, "缺少 zip 文件")
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            try:
                uploaded.save(tmp.name)
                ext_id, name = install_from_zip(tmp.name)
            finally:
                os.unlink(tmp.name)
        else:
            return fail(400, "不支持的安装方式")

        # 读取 manifest 获取权限列表用于前端审批
        from app.extensions.installer import EXTENSIONS_DIR
        manifest_path = os.path.join(EXTENSIONS_DIR, ext_id, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        return ok(data={
            "id": ext_id,
            "name": name,
            "manifest": manifest,
            "permissions": manifest.get("permissions", []),
            "pending_approval": True,
        })
    except Exception as e:
        return fail(400, str(e))


@api_bp.route("/extensions/<ext_id>/confirm", methods=["POST"])
def confirm_extension(ext_id):
    """用户审批权限后确认安装"""
    body = request.get_json(silent=True) or {}
    approved_permissions = body.get("permissions", [])

    from app.extensions.installer import EXTENSIONS_DIR
    manifest_path = os.path.join(EXTENSIONS_DIR, ext_id, "manifest.json")
    if not os.path.isfile(manifest_path):
        return fail(404, "扩展不存在")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid = validate_permissions(approved_permissions)
    now = datetime.now(timezone.utc).isoformat()
    update_info = manifest.get("update", {})
    install_method = "git" if update_info.get("type") == "git" else "zip"

    add_extension(ext_id, {
        "version": manifest["version"],
        "enabled": True,
        "installed_at": now,
        "install_method": install_method,
        "git_url": update_info.get("url", ""),
        "git_branch": update_info.get("branch", "main"),
        "last_updated": now,
        "permissions_granted": valid,
    })

    mgr = get_extension_manager()
    result = mgr.reload_extension(ext_id)

    return ok(data={
        "id": ext_id,
        "status": result["status"],
        "registered_hooks": result.get("registered_hooks", []),
    })


@api_bp.route("/extensions/<ext_id>/uninstall", methods=["POST"])
def uninstall_extension_route(ext_id):
    if not _check_ext_exists(ext_id):
        return fail(404, "扩展不存在")

    mgr = get_extension_manager()
    from app.extensions.loader import unload_extension
    unload_extension(ext_id, mgr.dispatcher)

    uninstall_extension(ext_id)
    remove_extension(ext_id)

    return ok(message=f"扩展 {ext_id} 已卸载")


@api_bp.route("/extensions/<ext_id>/update", methods=["POST"])
def update_extension_route(ext_id):
    ext = _check_ext_exists(ext_id)
    if not ext:
        return fail(404, "扩展不存在")
    if ext.get("install_method") != "git":
        return fail(400, "仅 Git 安装的扩展支持在线更新")

    try:
        new_version = update_extension(ext_id)
        # 更新注册表版本
        from app.extensions.registry import add_extension
        ext["version"] = new_version
        ext["last_updated"] = datetime.now(timezone.utc).isoformat()
        add_extension(ext_id, ext)

        mgr = get_extension_manager()
        result = mgr.reload_extension(ext_id)

        return ok(data={"version": new_version, "status": result["status"]})
    except Exception as e:
        return fail(400, str(e))


@api_bp.route("/extensions/<ext_id>/toggle", methods=["POST"])
def toggle_extension_route(ext_id):
    ext = _check_ext_exists(ext_id)
    if not ext:
        return fail(404, "扩展不存在")

    body = request.get_json(silent=True) or {}
    enabled = bool(body.get("enabled", not ext.get("enabled")))
    set_extension_state(ext_id, enabled)

    mgr = get_extension_manager()
    if enabled:
        result = mgr.reload_extension(ext_id)
        return ok(data={"enabled": True, "status": result["status"]})
    else:
        from app.extensions.loader import unload_extension
        unload_extension(ext_id, mgr.dispatcher)
        return ok(data={"enabled": False})


@api_bp.route("/extensions/<ext_id>/manifest")
def get_extension_manifest(ext_id):
    ext = _check_ext_exists(ext_id)
    if not ext:
        return fail(404, "扩展不存在")

    from app.extensions.installer import EXTENSIONS_DIR
    manifest_path = os.path.join(EXTENSIONS_DIR, ext_id, "manifest.json")
    if not os.path.isfile(manifest_path):
        return fail(404, "manifest.json 不存在")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    return ok(data=manifest)
```

- [ ] **Step 3: 运行集成测试**

```bash
cd backend && python -m pytest tests/test_extensions.py::test_api_install_via_zip_integration -v
```
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add backend/app/routes/extensions.py backend/tests/test_extensions.py
git commit -m "feat: add /api/extensions CRUD endpoints"
```

---

### Task 8: 将扩展钩子接入聊天流程

**Files:**
- Modify: `backend/app/routes/conversations.py`
- Modify: `backend/app/__init__.py`

**Interfaces:**
- Consumes: `ExtensionManager` (Task 6)
- Produces: 修改后的 `_stream_and_save` 在消息保存后调用钩子

- [ ] **Step 1: 修改 `_stream_and_save`**

```python
# backend/app/routes/conversations.py — 在 _stream_and_save 的 finally 块中修改

# 原代码（第 62-72 行）替换为：

    finally:
        if full_content or full_reasoning:
            msg_data = {
                "id": assistant_msg_id,
                "conversation_id": conv_id,
                "role": "assistant",
                "content": full_content,
                "reasoning_content": full_reasoning,
                "created_at": assistant_created,
            }
            # ── 扩展钩子：chat.post_receive ──
            from app.extensions import get_extension_manager
            mgr = get_extension_manager()
            # 收集 World Info 条目（当前阶段传空列表，后续 World Info 实现后替换）
            world_info_entries = body.get("_world_info_entries", []) if isinstance(body, dict) else []
            hook_ctx = {
                "conversation_id": conv_id,
                "messages": messages + [{"role": "assistant", "content": full_content}],
                "request_body": {"model": settings.get("model"), "messages": messages},
                "response_body": {"content": full_content, "reasoning_content": full_reasoning},
                "world_info_entries": world_info_entries,
                "settings": settings,
            }
            ext_results = mgr.dispatcher.dispatch("chat.post_receive", hook_ctx)
            # 合并扩展返回的 message_meta
            ext_data = {}
            for result in ext_results:
                eid = result.get("extension_id", "")
                meta = result.get("message_meta", {})
                if meta:
                    ext_data[eid] = meta
            if ext_data:
                msg_data["extensions"] = ext_data

            add_message(msg_data)
        sse_manager.unregister(conv_id)
```

- [ ] **Step 2: 修改 `chat` 路由传递 body 信息**

在 `chat()` 函数的 `cancel_event = sse_manager.register(conv_id)` 之前添加 body 引用，使 `_stream_and_save` 能访问原始请求体中的额外字段：

```python
# 在 call to _stream_and_save 之前，确保 body 可被 _stream_and_save 访问
# 将 body 作为隐藏参数传入 settings（通过扩展字段）
settings["_request_body"] = body  # 仅用于扩展钩子上下文传递
```

实际上更简洁的做法：直接把原始请求体传入 `_stream_and_save`。修改 `_stream_and_save` 签名添加 `request_body` 参数：

```python
# 修改函数签名
def _stream_and_save(settings, messages, conv_id, cancel_event,
                     temperature=None, max_tokens=None, top_p=None, request_body=None):
    # ... 原有逻辑 ...
    # finally 块中使用 request_body 替代 body 变量

# 修改调用处
return Response(
    stream_with_context(_stream_and_save(
        settings, messages, conv_id, cancel_event,
        temperature=temperature, max_tokens=max_tokens, top_p=top_p,
        request_body=body,
    )),
    ...
)
```

- [ ] **Step 3: 注册扩展蓝图并初始化 ExtensionManager**

修改 `backend/app/__init__.py`，在 `create_app()` 中：

```python
# 在现有 import 块后添加
import app.routes.extensions   # noqa — 注册 /api/extensions 系列路由

# 在 register_blueprint 之后、return flask_app 之前添加
from app.extensions import get_extension_manager
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_data", "extensions"), exist_ok=True)
get_extension_manager().init()
```

- [ ] **Step 4: 运行全部扩展测试验证集成**

```bash
cd backend && python -m pytest tests/test_extensions.py -v
```
Expected: 全部 PASS

- [ ] **Step 5: 运行已有测试确保无回归**

```bash
cd backend && python -m pytest -v
```
Expected: 53 tests PASS（无回归）

- [ ] **Step 6: 提交**

```bash
git add backend/app/__init__.py backend/app/routes/conversations.py
git commit -m "feat: wire extension hooks into chat flow"
```

---

### Task 9: 前端扩展 API 层（`api/extensions.js`）

**Files:**
- Create: `frontend/src/api/extensions.js`

**Interfaces:**
- Consumes: `http` (已有的 Axios 实例)
- Produces: `extensionsApi` 对象

- [ ] **Step 1: 实现**

```javascript
// frontend/src/api/extensions.js
import { http } from './request.js';

export const extensionsApi = {
  list() {
    return http.get('/extensions');
  },
  getManifest(extId) {
    return http.get(`/extensions/${extId}/manifest`);
  },
  installZip(file) {
    const formData = new FormData();
    formData.append('install_method', 'zip');
    formData.append('file', file);
    return http.post('/extensions/install', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  installGit(gitUrl, branch = 'main') {
    const formData = new FormData();
    formData.append('install_method', 'git');
    formData.append('git_url', gitUrl);
    formData.append('git_branch', branch);
    return http.post('/extensions/install', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  confirm(extId, permissions) {
    return http.post(`/extensions/${extId}/confirm`, { permissions });
  },
  uninstall(extId) {
    return http.post(`/extensions/${extId}/uninstall`);
  },
  update(extId) {
    return http.post(`/extensions/${extId}/update`);
  },
  toggle(extId, enabled) {
    return http.post(`/extensions/${extId}/toggle`, { enabled });
  },
};
```

- [ ] **Step 2: 注册到 api/index.js**

修改 `frontend/src/api/index.js`，追加导出：
```javascript
export { extensionsApi } from './extensions.js';
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/extensions.js frontend/src/api/index.js
git commit -m "feat: add frontend extensions API layer"
```

---

### Task 10: 前端扩展 Pinia Store（`stores/extensions.js`）

**Files:**
- Create: `frontend/src/stores/extensions.js`

**Interfaces:**
- Consumes: `extensionsApi` (Task 9)
- Produces: `useExtensionsStore` Pinia store

- [ ] **Step 1: 实现**

```javascript
// frontend/src/stores/extensions.js
import { defineStore } from 'pinia';
import { extensionsApi } from '@/api/extensions';

export const useExtensionsStore = defineStore('extensions', {
  state: () => ({
    items: [],               // [{ id, name, description, version, enabled, ... }]
    pendingApproval: null,   // 待审批的扩展信息
    loading: false,
  }),

  getters: {
    enabledExtensions: (state) => state.items.filter(e => e.enabled),
    enabledIds: (state) => state.items.filter(e => e.enabled).map(e => e.id),
  },

  actions: {
    async fetchExtensions() {
      this.loading = true;
      try {
        this.items = await extensionsApi.list();
      } finally {
        this.loading = false;
      }
    },

    async installZip(file) {
      const result = await extensionsApi.installZip(file);
      this.pendingApproval = result;
      return result;
    },

    async installGit(url, branch) {
      const result = await extensionsApi.installGit(url, branch);
      this.pendingApproval = result;
      return result;
    },

    async confirmInstall(permissions) {
      const extId = this.pendingApproval.id;
      await extensionsApi.confirm(extId, permissions);
      this.pendingApproval = null;
      await this.fetchExtensions();
    },

    cancelInstall() {
      this.pendingApproval = null;
    },

    async uninstall(extId) {
      await extensionsApi.uninstall(extId);
      await this.fetchExtensions();
    },

    async update(extId) {
      await extensionsApi.update(extId);
      await this.fetchExtensions();
    },

    async toggle(extId, enabled) {
      await extensionsApi.toggle(extId, enabled);
      await this.fetchExtensions();
    },
  },
});
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/stores/extensions.js
git commit -m "feat: add extensions Pinia store"
```

---

### Task 11: Core API Composable（`useExtensionApi.js`）

**Files:**
- Create: `frontend/src/extensions/useExtensionApi.js`

**Interfaces:**
- Consumes: `useChatStore`, `useSettingsStore`（已有 stores）
- Produces: `useExtensionApi()` composable，返回受限的 Core API

- [ ] **Step 1: 实现**

```javascript
// frontend/src/extensions/useExtensionApi.js
import { useChatStore } from '@/stores/chat';
import { useSettingsStore } from '@/stores/settings';

/**
 * 扩展可用的核心 API。
 * 扩展组件通过 props.api 调用，而非直接 import。
 * 未来可在此处添加权限校验。
 */
export function createExtensionApi(extensionId) {
  return {
    getConversation(id) {
      const chatStore = useChatStore();
      return chatStore.conversations.find(c => c.id === id) || null;
    },
    getCurrentConversation() {
      const chatStore = useChatStore();
      return chatStore.activeConversation;
    },
    getMessages(convId) {
      const chatStore = useChatStore();
      if (convId) {
        const conv = chatStore.conversations.find(c => c.id === convId);
        return conv?.messages || [];
      }
      return chatStore.activeConversation?.messages || [];
    },
    getSettings() {
      const settingsStore = useSettingsStore();
      return settingsStore.activePreset || settingsStore.presets[0] || null;
    },
    getWorldInfo() {
      // MVP 阶段 World Info 暂未实现，返回空
      return [];
    },
  };
}

export function useExtensionApi(extensionId) {
  return createExtensionApi(extensionId);
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/extensions/useExtensionApi.js
git commit -m "feat: add useExtensionApi composable for extensions"
```

---

### Task 12: ExtensionSlot 组件

**Files:**
- Create: `frontend/src/extensions/ExtensionSlot.vue`

**Interfaces:**
- Consumes: `useExtensionsStore` (Task 10)
- Produces: `<ExtensionSlot name="..." :message="..." />` 组件

- [ ] **Step 1: 实现**

采用全局注册表模式（`window.__EXTENSION_REGISTRY__`），扩展前端入口通过注册表注册组件，ExtensionSlot 按需消费：

```vue
<!-- frontend/src/extensions/ExtensionSlot.vue -->
<template>
  <div v-if="components.length" class="extension-slot" :data-slot="name">
    <component
      v-for="(item, idx) in components"
      :is="item.comp"
      :key="idx"
      v-bind="item.props || {}"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useExtensionsStore } from '@/stores/extensions';
import { createExtensionApi } from './useExtensionApi';

const props = defineProps({
  name: { type: String, required: true },
  message: { type: Object, default: null },
  conversation: { type: Object, default: null },
});

const extensionsStore = useExtensionsStore();
const components = ref([]);

onMounted(() => {
  const registry = window.__EXTENSION_REGISTRY__ || {};
  const result = [];
  for (const ext of extensionsStore.enabledExtensions) {
    const extRegistry = registry[ext.id];
    if (!extRegistry) continue;
    for (const [slotName, comps] of Object.entries(extRegistry)) {
      if (slotName !== props.name) continue;
      for (const Comp of comps) {
        result.push({
          comp: Comp,
          props: {
            message: props.message,
            conversation: props.conversation,
            api: createExtensionApi(ext.id),
          },
        });
      }
    }
  }
  components.value = result;
});
</script>

<style scoped>
.extension-slot {
  /* 插槽容器无默认样式，扩展自行控制 */
}
</style>
```

扩展前端入口（如 `frontend/index.js`）注册方式：
```javascript
// 扩展在初始化时自行注册
if (!window.__EXTENSION_REGISTRY__) {
  window.__EXTENSION_REGISTRY__ = {};
}
window.__EXTENSION_REGISTRY__['my-extension-id'] = {
  message_decorator: [MyComponent],
};

- [ ] **Step 2: 提交**

```bash
git add frontend/src/extensions/ExtensionSlot.vue
git commit -m "feat: add ExtensionSlot component for dynamic extension UI"
```

---

### Task 13: ExtensionManager.vue 管理 UI

**Files:**
- Create: `frontend/src/components/ExtensionManager.vue`

**Interfaces:**
- Consumes: `useExtensionsStore` (Task 10), `BaseDialog` (已有)
- Produces: 扩展管理面板（列表、安装按钮、开关、卸载）

- [ ] **Step 1: 实现**

```vue
<template>
  <BaseDialog :visible="visible" title="扩展管理" @close="$emit('close')">
    <div class="ext-manager">
      <!-- 安装区域 -->
      <div class="install-section">
        <div class="install-row">
          <button class="btn-install" @click="triggerZipInput">📦 导入 ZIP</button>
          <input ref="zipInputRef" type="file" accept=".zip" hidden @change="handleZipSelect" />
        </div>
        <div class="install-row">
          <input v-model="gitUrl" type="text" placeholder="Git 仓库 URL（如 https://github.com/...）" class="git-input" />
          <button class="btn-install" @click="installFromGit" :disabled="!gitUrl.trim() || installing">🔽 Git 安装</button>
        </div>
        <p v-if="installError" class="error-msg">{{ installError }}</p>
      </div>

      <!-- 已安装列表 -->
      <div class="ext-list">
        <div v-if="extensions.length === 0" class="empty">暂无已安装扩展</div>
        <div v-for="ext in extensions" :key="ext.id" class="ext-card">
          <div class="ext-info">
            <span class="ext-name">{{ ext.name }}</span>
            <span class="ext-version">v{{ ext.version }}</span>
            <span v-if="ext.description" class="ext-desc">{{ ext.description }}</span>
          </div>
          <div class="ext-actions">
            <button
              class="btn-toggle"
              :class="{ on: ext.enabled }"
              @click="toggleExtension(ext)"
            >{{ ext.enabled ? '已启用' : '已禁用' }}</button>
            <button v-if="ext.install_method === 'git'" class="btn-update" @click="updateExtension(ext)">🔄 更新</button>
            <button class="btn-remove" @click="removeExtension(ext)">🗑</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 权限审批弹窗 -->
    <BaseDialog v-if="pendingApproval" :visible="true" title="权限审批" @close="cancelInstall">
      <div class="approval">
        <p><strong>{{ pendingApproval.name }}</strong> 请求以下权限：</p>
        <ul>
          <li v-for="perm in pendingApproval.permissions" :key="perm">{{ perm }}</li>
        </ul>
        <div class="approval-actions">
          <button class="btn-confirm" @click="confirmInstall">✅ 批准</button>
          <button class="btn-cancel" @click="cancelInstall">❌ 拒绝</button>
        </div>
      </div>
    </BaseDialog>
  </BaseDialog>
</template>

<script setup>
import { ref } from 'vue';
import { useExtensionsStore } from '@/stores/extensions';
import { storeToRefs } from 'pinia';
import BaseDialog from './BaseDialog.vue';

defineProps({ visible: { type: Boolean, default: false } });
defineEmits(['close']);

const store = useExtensionsStore();
const { items: extensions, pendingApproval } = storeToRefs(store);
const zipInputRef = ref(null);
const gitUrl = ref('');
const installing = ref(false);
const installError = ref('');

function triggerZipInput() {
  zipInputRef.value?.click();
}

async function handleZipSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  try {
    installing.value = true;
    installError.value = '';
    await store.installZip(file);
  } catch (err) {
    installError.value = err.message || '安装失败';
  } finally {
    installing.value = false;
  }
}

async function installFromGit() {
  try {
    installing.value = true;
    installError.value = '';
    await store.installGit(gitUrl.value.trim());
    gitUrl.value = '';
  } catch (err) {
    installError.value = err.message || '安装失败';
  } finally {
    installing.value = false;
  }
}

async function confirmInstall() {
  await store.confirmInstall(pendingApproval.value.permissions);
}

function cancelInstall() {
  store.cancelInstall();
}

async function toggleExtension(ext) {
  await store.toggle(ext.id, !ext.enabled);
}

async function updateExtension(ext) {
  await store.update(ext.id);
}

async function removeExtension(ext) {
  if (confirm(`确定卸载 "${ext.name}"？`)) {
    await store.uninstall(ext.id);
  }
}
</script>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/ExtensionManager.vue
git commit -m "feat: add ExtensionManager UI component"
```

---

### Task 14: 前端集成 — 接入 MessageBubble 和设置页

**Files:**
- Modify: `frontend/src/components/MessageBubble.vue`
- Modify: `frontend/src/components/SettingsDrawer.vue`

- [ ] **Step 1: 在 MessageBubble 中渲染 ExtensionSlot**

在 `MessageBubble.vue` 模板的消息内容区域（`bubble-text` 之后、`</div>` 之前）添加：

```vue
<!-- 在 MessageBubble.vue 的模板中，bubble div 的关闭标签前添加 -->
<ExtensionSlot name="message_decorator" :message="message" :conversation="conversation" />
```

在 `<script setup>` 中添加导入：

```javascript
import ExtensionSlot from '@/extensions/ExtensionSlot.vue';
```

需要从 store 获取 conversation 对象。在 `MessageBubble.vue` 中已有 `const props = defineProps({ message: … })`，需添加 conversation prop 或从 store 获取：

```javascript
// 在 script setup 中添加
const conversation = computed(() => chatStore.activeConversation);
```

- [ ] **Step 2: 在设置页添加扩展管理入口**

在 `SettingsDrawer.vue` 中添加"扩展管理"标签或按钮：

```vue
<!-- 在设置导航列表中添加 -->
<div class="settings-nav-item" @click="showExtensions = true; $emit('tab', 'extensions')">
  🧩 扩展管理
</div>
```

以及 `ExtensionManager` 的引用：

```javascript
import ExtensionManager from '@/components/ExtensionManager.vue';
```

同时在 `Home.vue` 或合适位置挂载 `<ExtensionManager>`：

```vue
<ExtensionManager :visible="showExtensionManager" @close="showExtensionManager = false" />
```

- [ ] **Step 3: 在 main.js 中初始化扩展注册表**

```javascript
// frontend/src/main.js — 在 createApp 前添加
window.__EXTENSION_REGISTRY__ = {};
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/MessageBubble.vue frontend/src/components/SettingsDrawer.vue frontend/src/main.js
git commit -m "feat: wire ExtensionSlot into MessageBubble, add extension manager entry"
```

---

### Task 15: 示例扩展 — 上下文命中率分析器

**Files:**
- Create: `user_data/extensions/hit-rate-analyzer/manifest.json`
- Create: `user_data/extensions/hit-rate-analyzer/backend.py`
- Create: `user_data/extensions/hit-rate-analyzer/frontend/index.js`
- Create: `user_data/extensions/hit-rate-analyzer/frontend/components/HitRateBadge.js`

- [ ] **Step 1: 创建 manifest.json**

```json
{
  "id": "hit-rate-analyzer",
  "name": "上下文命中率分析",
  "version": "1.0.0",
  "author": "Chat Team",
  "description": "分析 AI 回复中 World Info 条目的命中情况",
  "permissions": ["read:conversations", "read:world_info", "hook:chat"],
  "ext_points": {
    "backend": ["chat.post_receive"],
    "frontend": ["message_decorator"]
  },
  "min_app_version": "1.2.0"
}
```

- [ ] **Step 2: 创建 backend.py**

```python
def on_chat_post_receive(ctx):
    """分析 World Info 条目在 AI 回复中的命中率"""
    world_info_entries = ctx.get("world_info_entries", [])
    if not world_info_entries:
        # 没有 WOI 条目就不计算
        return None

    response_body = ctx.get("response_body", {})
    ai_content = response_body.get("content", "").lower()

    hit_count = 0
    details = []
    for entry in world_info_entries:
        key = entry.get("key", "").lower()
        content = entry.get("content", "").lower()
        # 简单字符串匹配：检查条目的 key 或 content 是否出现在 AI 回复中
        matched = (key and key in ai_content) or (content and content in ai_content)
        if matched:
            hit_count += 1
        details.append({
            "key": entry.get("key", ""),
            "content_preview": entry.get("content", "")[:100],
            "matched": matched,
        })

    total = len(world_info_entries)
    hit_rate = hit_count / total if total > 0 else 0.0

    return {
        "hit_rate": round(hit_rate, 2),
        "hit": hit_count,
        "total": total,
        "details": details,
    }
```

- [ ] **Step 3: 创建 frontend/index.js**

```javascript
// 扩展前端入口 — 通过全局注册表注册组件
import HitRateBadge from './components/HitRateBadge.js';

if (!window.__EXTENSION_REGISTRY__) {
  window.__EXTENSION_REGISTRY__ = {};
}
window.__EXTENSION_REGISTRY__['hit-rate-analyzer'] = {
  message_decorator: [HitRateBadge],
};
```

- [ ] **Step 4: 创建 HitRateBadge 组件（使用 JS 渲染函数，避免 .vue 需编译）**

```javascript
// frontend/components/HitRateBadge.js
import { h, ref } from 'vue';

export default {
  name: 'HitRateBadge',
  props: {
    message: Object,
    api: Object,
  },
  setup(props) {
    const expanded = ref(false);
    const extData = props.message?.extensions?.['hit-rate-analyzer'];

    if (!extData) {
      return () => null;  // 没有命中率数据时不渲染
    }

    const percentage = Math.round(extData.hit_rate * 100);
    const color = percentage >= 60 ? '#4caf50' : percentage >= 30 ? '#ff9800' : '#f44336';

    function toggleExpand() {
      expanded.value = !expanded.value;
    }

    return () => h('div', {
      class: 'hit-rate-badge',
      style: {
        display: 'inline-flex', alignItems: 'center', gap: '4px',
        marginTop: '6px', fontSize: '12px', cursor: 'pointer',
        color: '#666',
      },
      onClick: toggleExpand,
    }, [
      h('span', {
        style: {
          display: 'inline-block', width: '8px', height: '8px',
          borderRadius: '50%', backgroundColor: color,
        },
      }),
      h('span', null, `WOI 命中 ${extData.hit}/${extData.total} · ${percentage}%`),
      expanded.value && h('div', {
        style: {
          marginTop: '4px', padding: '8px', background: '#f5f5f5',
          borderRadius: '4px', fontSize: '11px',
        },
      }, extData.details.map(d =>
        h('div', { style: { marginBottom: '2px' } }, [
          h('span', { style: { color: d.matched ? '#4caf50' : '#ccc' } }, d.matched ? '✓' : '✗'),
          h('span', null, ` ${d.key || d.content_preview || '(空)'}`),
        ])
      )),
    ]);
  },
};
```

- [ ] **Step 5: 在 App 初始化时注册示例扩展**

修改 `frontend/src/main.js`，在 `window.__EXTENSION_REGISTRY__ = {};` 之后添加：

```javascript
// 注册内置示例扩展（开发阶段手动注册，后续由 ExtensionSlot 自动加载）
import HitRateBadge from '@/../user_data/extensions/hit-rate-analyzer/frontend/components/HitRateBadge.js';

window.__EXTENSION_REGISTRY__['hit-rate-analyzer'] = {
  message_decorator: [HitRateBadge],
};
```

- [ ] **Step 6: 提交**

```bash
git add user_data/extensions/hit-rate-analyzer/ frontend/src/main.js
git commit -m "feat: add hit-rate-analyzer example extension"
```

---

### Task 16: 创建 `__init__.py` 占位文件 + 最终测试

**Files:**
- Create: `backend/app/extensions/__pycache__/` 不需要手动创建
- Verify: 所有测试通过

- [ ] **Step 1: 运行全部测试**

```bash
cd backend && python -m pytest -v
```
Expected: 全部 PASS（原有 53 + 新增扩展系统测试）

- [ ] **Step 2: 提交**

```bash
git add backend/app/extensions/
git commit -m "feat: extension system MVP complete"
```

---

## Execution Order

任务必须严格按顺序执行（每个 Task 依赖前一个 Task 的接口）：
1 → 2 → 3 → 4 → 5 → 6 → **7 → 8**（后端核心完成）→ 9 → 10 → 11 → 12 → 13 → **14**（前端集成完成）→ **15**（示例扩展）→ **16**（最终验证）
