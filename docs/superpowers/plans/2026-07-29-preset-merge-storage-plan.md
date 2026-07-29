# 参数预设与提示词条目合并存储 — 实现计划

> **For agentic workers:** 使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 按任务逐个实现。

**目标：** 将参数预设和提示词条目从两个独立 JSON 文件合并为单一 `presets/<id>.json`，前端合并为一个 store，一次性保存。

**架构：** 后端 `storage/presets.py` 替代 `param_presets.py` + `prompt_entries.py`，`routes/presets.py` 替代两个旧路由；前端 `stores/presets.js` 合并 `paramPresets.js` + `promptEntries.js`。条目用 `entries` 对象（键值对）保持插入顺序，`__chat_history__` 自然持久化。

**技术栈：** Python/Flask（storage + routes）、Vue 3 + Pinia（前端）

---

## 全局约束

- 键名全部英文：`name`、`params`、`entries`，值允许中文
- 条目排序靠 `entries` 对象键的插入顺序
- `__chat_history__` 值为固定字符串 `"chat_history"`
- 前端 `ParamPresetSelector` 移除卡片内保存/删除按钮，改为下拉旁图标按钮
- 条目操作改为本地修改，点击顶部"保存"按钮一次性提交
- 所有文件禁止 emoji

---

### Task 1: 后端 — 新建 storage/presets.py

**文件：**
- 创建：`backend/app/storage/presets.py`
- 修改：`backend/app/storage/__init__.py`

**接口：**
- 产出：`list_presets()`, `get_preset(id)`, `create_preset(data)`, `update_preset(id, data)`, `delete_preset(id)`, `get_default_preset()`, `set_default_preset(id)`, `init_presets()`, `get_entries(id)`

- [ ] **Step 1: 创建 storage/presets.py**

```python
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
```

- [ ] **Step 2: 更新 storage/__init__.py 导出**

替换旧的 param_presets + prompt_entries 导出：

```python
from .presets import (
    list_presets,
    get_preset,
    create_preset,
    update_preset,
    delete_preset,
    get_default_preset,
    set_default_preset,
    init_presets,
    get_entries,
)
```

删除旧的 `from .param_presets import (...)` 和 `from .prompt_entries import (...)` 块。

- [ ] **Step 3: 运行测试确认存储层**

```bash
cd backend && python -c "from app.storage.presets import init_presets; init_presets(); print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/storage/presets.py backend/app/storage/__init__.py
git commit -m "feat: 新建 presets 合并存储层（替代 param_presets + prompt_entries）"
```

---

### Task 2: 后端 — 新建 routes/presets.py + 更新 __init__.py

**文件：**
- 创建：`backend/app/routes/presets.py`
- 修改：`backend/app/__init__.py`
- 修改：`backend/app/routes/conversations.py`（改 settings 获取方式）

**接口：**
- 产出：所有 `/api/presets` 路由
- 消费：`get_preset`, `list_presets` 等 from `app.storage.presets`
- 修改：conversations.py 中 `get_default_setting()` 改为读 presets

- [ ] **Step 1: 创建 routes/presets.py**

```python
import uuid
from datetime import datetime, timezone
from flask import request
from app.routes import api_bp
from app.storage.presets import (
    list_presets, get_preset, create_preset, update_preset,
    delete_preset, get_default_preset, set_default_preset, get_entries,
)
from app.utils.response import ok, fail


def _get_or_404(preset_id):
    return get_preset(preset_id)


@api_bp.route("/presets")
def list_presets_route():
    return ok(data=list_presets())


@api_bp.route("/presets/<preset_id>")
def get_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    return ok(data=row)


@api_bp.route("/presets", methods=["POST"])
def create_preset_route():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "name 不能为空", request)
    try:
        temperature = float(body.get("temperature", 0.7))
        max_tokens = int(body.get("max_tokens", 4096))
        top_p = float(body.get("top_p", 1.0))
    except (ValueError, TypeError):
        return fail(400, "参数格式错误", request)
    if not 0 <= temperature <= 2:
        return fail(400, "temperature 范围 0~2", request)
    if max_tokens < 1:
        return fail(400, "max_tokens 必须 > 0", request)
    if not 0 <= top_p <= 1:
        return fail(400, "top_p 范围 0~1", request)
    preset = create_preset({
        "name": name, "temperature": temperature,
        "max_tokens": max_tokens, "top_p": top_p,
    })
    return ok(data=preset)


@api_bp.route("/presets/<preset_id>", methods=["PUT"])
def update_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    body = request.get_json(silent=True) or {}
    updated = update_preset(preset_id, body)
    return ok(data=updated)


@api_bp.route("/presets/<preset_id>", methods=["DELETE"])
def delete_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    if row.get("is_default"):
        return fail(409, "不能删除默认参数预设，请先切换默认预设", request)
    delete_preset(preset_id)
    return ok()


@api_bp.route("/presets/<preset_id>/default", methods=["PUT"])
def set_default_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    set_default_preset(preset_id)
    return ok(data={"is_default": True})
```

- [ ] **Step 2: 更新后端 __init__.py**

```python
# 替换
# import app.routes.param_presets  # noqa
# import app.routes.prompt_entries  # noqa
# 为：
import app.routes.presets  # noqa: F401 — 注册 /api/presets 系列路由
```

```python
# 替换
# from app.storage.param_presets import init_param_presets
# init_param_presets()
# os.makedirs(os.path.join(DATA_DIR, "prompt_entries"), exist_ok=True)
# 为：
from app.storage.presets import init_presets
init_presets()
os.makedirs(os.path.join(DATA_DIR, "presets"), exist_ok=True)
```

- [ ] **Step 3: 修改 conversations.py 中 settings 获取**

conversations.py 当前通过 `get_default_setting()` 获取 API URL/Key/Model。这个函数来自 `app.storage.settings`，不受 param_presets 影响。确认 conversations.py 对 param_presets 没有依赖即可。

> 确认：conversations.py 不 import param_presets。温度参数从 body 获取，不依赖预设。

- [ ] **Step 4: 运行后端测试**

```bash
cd backend && python -m pytest -v
```

此时旧测试会失败（因为路由已换），预期看到 param_presets 和 prompt_entries 相关测试 FAIL。

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/presets.py backend/app/__init__.py
git commit -m "feat: 新建 /api/presets 路由（替代 param-presets + prompt-entries）"
```

---

### Task 3: 后端 — 删除旧文件 + 更新测试

**文件：**
- 删除：`backend/app/storage/param_presets.py`
- 删除：`backend/app/storage/prompt_entries.py`
- 删除：`backend/app/routes/param_presets.py`
- 删除：`backend/app/routes/prompt_entries.py`
- 重写：`backend/tests/test_presets.py`
- 删除：`backend/tests/test_param_presets.py`
- 删除：`backend/tests/test_prompt_entries.py`

- [ ] **Step 1: 删除旧文件**

```bash
rm backend/app/storage/param_presets.py
rm backend/app/storage/prompt_entries.py
rm backend/app/routes/param_presets.py
rm backend/app/routes/prompt_entries.py
rm backend/tests/test_param_presets.py
rm backend/tests/test_prompt_entries.py
```

- [ ] **Step 2: 新建 tests/test_presets.py**

```python
import pytest


@pytest.fixture(autouse=True)
def _isolate_presets(monkeypatch, tmp_path):
    """确保 presets 使用临时目录。"""
    import app.storage.presets as mod
    test_dir = str(tmp_path / "presets")
    monkeypatch.setattr(mod, "PRESETS_DIR", test_dir)
    monkeypatch.setattr(mod, "INDEX_FILE", mod.INDEX_FILE.replace(mod.PRESETS_DIR, test_dir))
    # 重新设置 INDEX_FILE 路径
    import os
    monkeypatch.setattr(mod, "INDEX_FILE", os.path.join(test_dir, "_index.json"))
    # 对 _init__.py 中的 DATA_DIR 也做 monkeypatch
    from app.storage.conversations import DATA_DIR as orig_data_dir
    # 重置模块级变量
    mod.PRESETS_DIR = test_dir
    mod.INDEX_FILE = os.path.join(test_dir, "_index.json")


def _create_preset(client):
    """创建预设辅助函数。"""
    resp = client.post("/api/presets", json={
        "name": "测试预设",
        "temperature": 0.5,
        "max_tokens": 2048,
        "top_p": 0.9,
    })
    return resp.get_json()["data"]


class TestPresetsCRUD:
    def test_list_empty(self, client):
        """空列表返回 []。"""
        resp = client.get("/api/presets")
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0

    def test_create(self, client):
        """创建预设成功。"""
        resp = client.post("/api/presets", json={
            "name": "测试", "temperature": 0.5, "max_tokens": 2048, "top_p": 0.9,
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["name"] == "测试"
        assert data["params"]["temperature"] == 0.5
        assert "id" in data
        # 验证默认含 __chat_history__
        assert "__chat_history__" in data["entries"]

    def test_create_missing_name(self, client):
        """缺少名称返回失败。"""
        resp = client.post("/api/presets", json={"name": ""})
        assert resp.get_json()["code"] != 0

    def test_get_detail(self, client):
        """获取预设详情含条目。"""
        created = _create_preset(client)
        resp = client.get(f"/api/presets/{created['id']}")
        data = resp.get_json()["data"]
        assert data["name"] == "测试预设"
        assert "entries" in data
        assert "__chat_history__" in data["entries"]

    def test_update_full(self, client):
        """全量更新预设（参数 + 条目）。"""
        created = _create_preset(client)
        resp = client.put(f"/api/presets/{created['id']}", json={
            "name": "新名称",
            "params": {"temperature": 0.3, "max_tokens": 1024, "top_p": 0.5},
            "entries": {
                "e1": {"name": "设定", "role": "system", "content": "你是助手", "enabled": True},
                "__chat_history__": "chat_history",
                "e2": {"name": "尾部", "role": "assistant", "content": "喵", "enabled": False},
            },
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["name"] == "新名称"
        assert data["params"]["temperature"] == 0.3
        assert data["entries"]["e1"]["role"] == "system"
        assert data["entries"]["e2"]["enabled"] is False

    def test_delete_not_default(self, client):
        """删除非默认预设成功。"""
        created = _create_preset(client)
        resp = client.delete(f"/api/presets/{created['id']}")
        assert resp.get_json()["code"] == 0
        resp = client.get(f"/api/presets/{created['id']}")
        assert resp.get_json()["code"] != 0

    def test_cannot_delete_default(self, client):
        """不能删除默认预设。"""
        # 先找到默认（列表第一个或创建第一个）
        list_resp = client.get("/api/presets")
        presets = list_resp.get_json()["data"]
        default = next((p for p in presets if p.get("is_default")), presets[0]) if presets else None
        if default:
            resp = client.delete(f"/api/presets/{default['id']}")
            assert resp.get_json()["code"] != 0

    def test_set_default(self, client):
        """设置默认预设。"""
        created = _create_preset(client)
        resp = client.put(f"/api/presets/{created['id']}/default")
        assert resp.get_json()["code"] == 0
        # 验证
        list_resp = client.get("/api/presets")
        presets = list_resp.get_json()["data"]
        target = next(p for p in presets if p["id"] == created["id"])
        assert target["is_default"] is True

    def test_get_entries_ordering(self, client):
        """get_entries 返回的条目数组保持 entries 对象键顺序。"""
        created = _create_preset(client)
        client.put(f"/api/presets/{created['id']}", json={
            "entries": {
                "a1": {"name": "A", "role": "system", "content": "a", "enabled": True},
                "__chat_history__": "chat_history",
                "b2": {"name": "B", "role": "user", "content": "b", "enabled": True},
            },
        })
        # 通过 get_preset_route 验证 entries 对象顺序
        resp = client.get(f"/api/presets/{created['id']}")
        entries_obj = resp.get_json()["data"]["entries"]
        keys = list(entries_obj.keys())
        assert keys == ["a1", "__chat_history__", "b2"]

    def test_get_entries_cross_module(self, client):
        """get_entries() 函数返回的列表含 __chat_history__ 在正确位置。"""
        created = _create_preset(client)
        client.put(f"/api/presets/{created['id']}", json={
            "entries": {
                "a1": {"name": "A", "role": "system", "content": "a", "enabled": True},
                "__chat_history__": "chat_history",
                "b2": {"name": "B", "role": "user", "content": "b", "enabled": True},
            },
        })
        from app.storage.presets import get_entries
        entries = get_entries(created["id"])
        assert len(entries) == 3
        assert entries[0]["id"] == "a1"
        assert entries[1]["id"] == "__chat_history__"
        assert entries[2]["id"] == "b2"
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/test_presets.py -v
```

预期：新建的测试应通过。其他旧测试可能因依赖 param_presets/prompt_entries 而失败，在 Task 4 中处理。

- [ ] **Step 4: Commit**

```bash
git add -A backend/
git commit -m "feat: 删除旧 param_presets/prompt_entries，新增 presets 测试"
```

---

### Task 4: 修复受影响的测试和引用

**文件：**
- 修改：`backend/tests/test_integration.py`（如有引用）
- 修改：`backend/app/storage/__init__.py`（确保无残留引用）
- 修改：`backend/app/__init__.py`（确保无残留引用）

- [ ] **Step 1: 运行全量测试看哪些失败**

```bash
cd backend && python -m pytest -v 2>&1 | head -50
```

- [ ] **Step 2: 逐个修复失败测试**

预期影响：`test_integration.py` 中如果有调用 `/api/param-presets` 的测试会失败。需改为 `/api/presets`。

- [ ] **Step 3: 确认全量测试通过**

```bash
cd backend && python -m pytest -v
```

- [ ] **Step 4: Commit**

```bash
git add -A backend/
git commit -m "fix: 修复合并存储后受影响的测试"
```

---

### Task 5: 前端 — 新建 API 和 Store

**文件：**
- 创建：`frontend/src/api/presets.js`
- 创建：`frontend/src/stores/presets.js`

- [ ] **Step 1: 创建 api/presets.js**

```javascript
/**
 * 预设 API（合并参数预设 + 提示词条目）
 */
import http from "./request.js";

export function list() {
  return http.get("/presets");
}

export function get(id) {
  return http.get(`/presets/${id}`);
}

export function create(data) {
  return http.post("/presets", data);
}

export function update(id, data) {
  return http.put(`/presets/${id}`, data);
}

export function remove(id) {
  return http.delete(`/presets/${id}`);
}

export function setDefault(id) {
  return http.put(`/presets/${id}/default`);
}
```

- [ ] **Step 2: 创建 stores/presets.js**

```javascript
import { defineStore } from "pinia";
import * as presetsApi from "@/api/presets";

export const usePresetsStore = defineStore("presets", {
  state: () => ({
    presets: [],
    activePresetId: null,
    loading: false,
    entries: {},  // 当前预设的 entries 对象（保持键顺序）
  }),

  getters: {
    activePreset(state) {
      return state.presets.find((p) => p.id === state.activePresetId) || null;
    },
    temperature() {
      const p = this.activePreset;
      return p ? p.temperature : 0.7;
    },
    maxTokens() {
      const p = this.activePreset;
      return p ? p.max_tokens : 4096;
    },
    topP() {
      const p = this.activePreset;
      return p ? p.top_p : 1.0;
    },
    /** 条目数组（含 __chat_history__），保持键顺序，带 order 字段 */
    entriesList(state) {
      const result = [];
      let idx = 0;
      for (const [key, value] of Object.entries(state.entries)) {
        if (key === "__chat_history__") {
          result.push({
            id: "__chat_history__",
            name: "对话历史",
            role: "system",
            content: "",
            enabled: true,
            order: idx,
          });
        } else if (typeof value === "object" && value !== null) {
          result.push({
            id: key,
            name: value.name || "",
            role: value.role,
            content: value.content || "",
            enabled: value.enabled !== false,
            order: idx,
          });
        }
        idx++;
      }
      return result;
    },
  },

  actions: {
    async loadPresets() {
      this.loading = true;
      try {
        this.presets = await presetsApi.list();
        if (!this.activePresetId && this.presets.length > 0) {
          const def = this.presets.find((p) => p.is_default) || this.presets[0];
          if (def && def.id) await this.selectPreset(def.id);
        }
      } catch (e) {
        this.presets = [];
        console.error("加载预设列表失败:", e);
      } finally {
        this.loading = false;
      }
    },

    async selectPreset(id) {
      if (!id) return;
      const preset = this.presets.find((p) => p.id === id);
      if (!preset) return;
      this.activePresetId = id;
      // 加载完整预设（含 entries）
      try {
        const detail = await presetsApi.get(id);
        this.entries = detail.entries || {};
      } catch (e) {
        this.entries = {};
      }
    },

    async createPreset(name, temperature, maxTokens, topP) {
      if (!name || !name.trim()) throw new Error("预设名称不能为空");
      const preset = await presetsApi.create({
        name: name.trim(), temperature, max_tokens: maxTokens, top_p: topP,
      });
      this.presets.push({ id: preset.id, name: preset.name, is_default: false });
      this.activePresetId = preset.id;
      this.entries = preset.entries || {};
    },

    /** 一次性保存整个预设（参数 + 条目） */
    async savePreset() {
      if (!this.activePresetId) throw new Error("未选中任何预设");
      const preset = this.activePreset;
      if (!preset) throw new Error("未选中任何预设");
      const updated = await presetsApi.update(this.activePresetId, {
        name: preset.name,
        params: {
          temperature: this.temperature,
          max_tokens: this.maxTokens,
          top_p: this.topP,
        },
        entries: this.entries,
      });
      const idx = this.presets.findIndex((p) => p.id === this.activePresetId);
      if (idx !== -1) {
        this.presets[idx] = { id: updated.id, name: updated.name, is_default: updated.is_default };
      }
      return updated;
    },

    async deletePreset(id) {
      if (!id) throw new Error("未指定要删除的预设");
      await presetsApi.remove(id);
      this.presets = this.presets.filter((p) => p.id !== id);
      if (this.activePresetId === id) {
        this.activePresetId = null;
        this.entries = {};
        if (this.presets.length > 0) {
          await this.selectPreset(this.presets[0].id);
        }
      }
    },

    // ── 条目本地操作（不即时调 API）──
    addEntry(name) {
      const id = "temp-" + Date.now();
      const entry = { name, role: null, content: "", enabled: true };
      const newEntries = { ...this.entries };
      newEntries[id] = entry;
      this.entries = newEntries;
      return id;
    },

    updateEntry(id, data) {
      const newEntries = { ...this.entries };
      if (newEntries[id] && typeof newEntries[id] === "object") {
        Object.assign(newEntries[id], data);
        this.entries = newEntries;
      }
    },

    removeEntry(id) {
      const newEntries = {};
      for (const [key, value] of Object.entries(this.entries)) {
        if (key !== id) newEntries[key] = value;
      }
      this.entries = newEntries;
    },

    /** 拖拽重排：按 id 顺序重建 entries 对象 */
    reorderEntries(orderedIds) {
      const newEntries = {};
      for (const id of orderedIds) {
        if (id === "__chat_history__") {
          newEntries["__chat_history__"] = "chat_history";
        } else if (this.entries[id]) {
          newEntries[id] = this.entries[id];
        }
      }
      this.entries = newEntries;
    },
  },
});
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/presets.js frontend/src/stores/presets.js
git commit -m "feat: 新建 presets API + Pinia store（合并 paramPresets + promptEntries）"
```

---

### Task 6: 前端 — 改造组件 + 清理旧引用

**文件：**
- 修改：`frontend/src/components/ParamPresetSelector.vue`
- 修改：`frontend/src/components/PromptEntryCard.vue`
- 修改：`frontend/src/stores/chat.js`
- 修改：`frontend/src/App.vue`

- [ ] **Step 1: 改造 ParamPresetSelector.vue**

模板改为：下拉旁放保存/删除/+ 按钮（移除卡片内旧按钮）：

```vue
<template>
  <div class="param-preset-selector">
    <div class="pps-row">
      <select v-model="selectedId" class="pps-select" @change="handleSelect">
        <option v-for="p in store.presets" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <button class="pps-icon-btn" title="新建预设" @click="handleCreate">+</button>
      <button class="pps-icon-btn" title="保存" @click="handleSave" :disabled="!canSave">
        <Save :size="14" />
      </button>
      <button class="pps-icon-btn pps-icon-btn--danger" title="删除" @click="handleDelete" :disabled="!canDelete">
        <Trash2 :size="14" />
      </button>
    </div>
    <!-- 命名弹窗（新建时） -->
    <BaseDialog v-if="showNameDialog" :visible="true" title="新建预设" @close="showNameDialog = false">
      <input v-model="newName" placeholder="预设名称" @keydown.enter="confirmCreate" />
      <button @click="confirmCreate">确认</button>
    </BaseDialog>
    <!-- 删除确认弹窗 -->
    <BaseDialog v-if="showDeleteConfirm" :visible="true" @close="showDeleteConfirm = false">
      <p>确定删除「{{ activePreset?.name }}」？</p>
      <button class="danger" @click="confirmDelete">删除</button>
    </BaseDialog>
    <!-- Toast -->
    <div v-if="toast" class="pps-toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { Save, Trash2 } from "lucide-vue-next";
import { usePresetsStore } from "@/stores/presets";
import BaseDialog from "@/components/BaseDialog.vue";

const store = usePresetsStore();
const emit = defineEmits(["saved"]);

const selectedId = ref(store.activePresetId);
const newName = ref("");
const showNameDialog = ref(false);
const showDeleteConfirm = ref(false);
const toast = ref("");

const activePreset = computed(() => store.activePreset);
const canSave = computed(() => !!store.activePresetId);
const canDelete = computed(() => {
  return store.activePresetId && !activePreset.value?.is_default;
});

watch(() => store.activePresetId, (v) => { selectedId.value = v; });

function handleSelect() {
  store.selectPreset(selectedId.value);
}

function handleCreate() {
  newName.value = "";
  showNameDialog.value = true;
}

async function confirmCreate() {
  const name = newName.value.trim();
  if (!name) return;
  showNameDialog.value = false;
  await store.createPreset(name, 0.7, 4096, 1.0);
  toast.value = "预设已创建";
  setTimeout(() => { toast.value = ""; }, 2000);
  emit("saved");
}

async function handleSave() {
  try {
    await store.savePreset();
    toast.value = "已保存";
    setTimeout(() => { toast.value = ""; }, 2000);
  } catch (e) {
    toast.value = "保存失败: " + (e.message || "未知错误");
  }
}

function handleDelete() {
  showDeleteConfirm.value = true;
}

async function confirmDelete() {
  showDeleteConfirm.value = false;
  await store.deletePreset(store.activePresetId);
}
</script>
```

样式略（保留现有 CSS 变量风格）。

- [ ] **Step 2: 改造 PromptEntryCard.vue**

改用 `usePresetsStore`，所有操作本地修改 entries 对象：

```vue
<script setup>
import { ref, watch, nextTick, computed, onBeforeUnmount } from "vue";
import { List } from "lucide-vue-next";
import { usePresetsStore } from "@/stores/presets";
import PromptEntryItem from "@/components/PromptEntryItem.vue";
import PromptEntryModal from "@/components/PromptEntryModal.vue";

const store = usePresetsStore();
const entries = computed(() => store.entriesList);

// ... 拖拽逻辑不变，但 onMouseUp 中改用 store.reorderEntries
// ... handleToggle / handleEditSave / handleEditDelete 改用 store.updateEntry / store.removeEntry
// ... handleAdd 改用 store.addEntry
</script>
```

关键修改点：
- 移除 `import * as promptEntriesApi` / `import * as paramPresetsApi`
- 移除 `import { usePromptEntriesStore }` / `import { useParamPresetsStore }`
- `store.entries` → `store.entriesList`（getter）
- `handleToggle(entry)` → `store.updateEntry(entry.id, { enabled: !entry.enabled })`
- `handleEditSave({ name, content, role })` → `store.updateEntry(id, { name, content, role })`
- `handleEditDelete(id)` → `store.removeEntry(id)`
- `handleAdd` → `store.addEntry(name)`
- `onMouseUp` reorder → `store.reorderEntries(orderedIds)`（含 `__chat_history__`）
- 移除 `watch paramStore.activePresetId → store.loadEntries`（由 presetsStore.selectPreset 处理）

- [ ] **Step 3: 改造 chat.js**

```javascript
// 替换
// import { useParamPresetsStore } from "@/stores/paramPresets";
// import { usePromptEntriesStore } from "@/stores/promptEntries";
// 为：
import { usePresetsStore } from "@/stores/presets";
import { assembleMessages } from "@/composables/useMessageAssembler";

// sendMessage 中：
// const paramPresetsStore = useParamPresetsStore();
// const promptEntriesStore = usePromptEntriesStore();
// 改为：
const presetsStore = usePresetsStore();

// 所有 paramPresetsStore.temperature → presetsStore.temperature
// 所有 paramPresetsStore.maxTokens → presetsStore.maxTokens
// 所有 paramPresetsStore.topP → presetsStore.topP
// 所有 promptEntriesStore.entries → presetsStore.entriesList
```

- [ ] **Step 4: 改造 App.vue**

```javascript
// 替换
// import { useParamPresetsStore } from "@/stores/paramPresets";
// 为：
import { usePresetsStore } from "@/stores/presets";

// const paramPresetsStore = useParamPresetsStore();
// paramPresetsStore.loadPresets();
// 改为：
// const presetsStore = usePresetsStore();
// presetsStore.loadPresets();
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ParamPresetSelector.vue frontend/src/components/PromptEntryCard.vue frontend/src/stores/chat.js frontend/src/App.vue
git commit -m "feat: 改造组件使用 presetsStore，ParamPresetSelector 布局重构"
```

---

### Task 7: 清理旧前端文件 + 构建验证

**文件：**
- 删除：`frontend/src/api/paramPresets.js`
- 删除：`frontend/src/api/promptEntries.js`
- 删除：`frontend/src/stores/paramPresets.js`
- 删除：`frontend/src/stores/promptEntries.js`

- [ ] **Step 1: 删除旧文件**

```bash
rm frontend/src/api/paramPresets.js
rm frontend/src/api/promptEntries.js
rm frontend/src/stores/paramPresets.js
rm frontend/src/stores/promptEntries.js
```

- [ ] **Step 2: 构建前端**

```bash
cd frontend && npm run build
```

修复构建错误（如有遗漏的 import）。

- [ ] **Step 3: 运行全量后端测试**

```bash
cd backend && python -m pytest -v
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: 删除旧 paramPresets/promptEntries API + Store，构建验证通过"
```
