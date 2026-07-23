# 参数预设 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增独立的参数预设体系（temperature / max_tokens / top_p），与 API 连接预设解耦，工具栏新增"预设"按钮。

**Architecture:** 后端新增 `param_presets.json` 存储 + `/api/param-presets` CRUD 端点；前端新增 `ParamPresetSelector` 组件 + `useParamPresetsStore`；发送消息时两个 store 各取值合并传参。

**Tech Stack:** Python/Flask（后端存储 + API），Vue 3/Pinia（前端状态 + UI）

## Global Constraints

- 参数预设与连接预设完全独立，互不依赖
- 默认预设（`is_default=true`）不可删除，至少保留一个
- 首次启动时若文件不存在或为空，自动创建"默认"预设（temperature=0.7, max_tokens=4096, top_p=1.0）
- 参数值范围：temperature 0~2, top_p 0~1, max_tokens > 0
- 命名不改现有"API设置"，工具栏新增按钮叫"预设"，两套共存

---

### Task 1: 后端存储层 — `param_presets.json` CRUD

**Files:**
- Create: `backend/app/storage/param_presets.py`
- Modify: `backend/app/storage/__init__.py`

**Interfaces:**
- Produces: `list_param_presets_raw()`, `get_param_preset(id)`, `create_param_preset(p)`, `update_param_preset(id, updates)`, `delete_param_preset(id)`, `get_default_param_preset()`, `set_default_param_preset(id)`, `init_param_presets()`

- [ ] **Step 1: 创建 `backend/app/storage/param_presets.py`**

```python
import os
from .conversations import _read_json, _write_json, _lock, DATA_DIR

PARAM_PRESETS_FILE = os.path.join(DATA_DIR, "param_presets.json")

# 默认预设模板
_DEFAULT_PRESET = {
    "name": "默认",
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0,
    "is_default": True,
}


def _read_param_presets():
    return _read_json(PARAM_PRESETS_FILE)


def _write_param_presets(data):
    _write_json(PARAM_PRESETS_FILE, data)


def init_param_presets():
    """首次启动：文件不存在或为空时自动创建默认预设"""
    import uuid
    from datetime import datetime, timezone

    if not os.path.exists(PARAM_PRESETS_FILE):
        now = datetime.now(timezone.utc).isoformat()
        default = {**_DEFAULT_PRESET, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        _write_param_presets([default])
        return

    items = _read_param_presets()
    if not items:
        now = datetime.now(timezone.utc).isoformat()
        default = {**_DEFAULT_PRESET, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        _write_param_presets([default])


def list_param_presets_raw():
    with _lock:
        items = _read_param_presets()
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def get_param_preset(preset_id):
    items = list_param_presets_raw()
    for item in items:
        if item["id"] == preset_id:
            return item
    return None


def create_param_preset(p):
    with _lock:
        items = _read_param_presets()
        items.append(p)
        _write_param_presets(items)


def update_param_preset(preset_id, updates):
    with _lock:
        items = _read_param_presets()
        for item in items:
            if item["id"] == preset_id:
                item.update(updates)
                break
        _write_param_presets(items)


def delete_param_preset(preset_id):
    with _lock:
        items = _read_param_presets()
        items = [i for i in items if i["id"] != preset_id]
        _write_param_presets(items)


def get_default_param_preset():
    items = list_param_presets_raw()
    for item in items:
        if item.get("is_default"):
            return item
    return None


def set_default_param_preset(preset_id):
    with _lock:
        items = _read_param_presets()
        for item in items:
            item["is_default"] = (item["id"] == preset_id)
        _write_param_presets(items)
```

- [ ] **Step 2: 在 `backend/app/storage/__init__.py` 中导出新函数**

在文件末尾追加：

```python
from .param_presets import (
    PARAM_PRESETS_FILE,
    list_param_presets_raw,
    get_param_preset,
    create_param_preset,
    update_param_preset,
    delete_param_preset,
    get_default_param_preset,
    set_default_param_preset,
    init_param_presets,
)
```

- [ ] **Step 3: 在 `backend/app/__init__.py` 中调用 `init_param_presets()`**

在 `init_storage()` 调用之后（第 40 行附近），`init_storage()` 后加入：

```python
    from app.storage.param_presets import init_param_presets
    init_param_presets()
```

完整上下文：
```python
    init_storage()  # 初始化 JSON 存储（幂等）
    from app.storage.param_presets import init_param_presets
    init_param_presets()  # 初始化参数预设存储（幂等）
```

- [ ] **Step 4: 验证存储层**

```bash
cd D:/UsersProject/chat/backend && python -c "from app.storage.param_presets import list_param_presets_raw, init_param_presets; init_param_presets(); print(list_param_presets_raw())"
```
Expected: 输出包含一条默认预设记录。

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/param_presets.py backend/app/storage/__init__.py backend/app/__init__.py
git commit -m "feat: add param_presets storage layer with default preset"
```

---

### Task 2: 后端路由层 — `/api/param-presets` CRUD

**Files:**
- Create: `backend/app/routes/param_presets.py`
- Modify: `backend/app/__init__.py`

**Interfaces:**
- Consumes: `list_param_presets_raw`, `get_param_preset`, `create_param_preset`, `update_param_preset`, `delete_param_preset`, `get_default_param_preset`, `set_default_param_preset` from storage
- Produces: 5 个路由端点注册在 `@api_bp`

- [ ] **Step 1: 创建 `backend/app/routes/param_presets.py`**

```python
import uuid
from datetime import datetime, timezone
from flask import request
from app.routes import api_bp
from app.storage import (
    list_param_presets_raw, get_param_preset, create_param_preset,
    update_param_preset, delete_param_preset,
    get_default_param_preset, set_default_param_preset,
)
from app.utils.response import ok, fail


def _row_to_dict(row):
    d = dict(row)
    d["is_default"] = bool(d.get("is_default"))
    return d


def _get_or_404(preset_id):
    return get_param_preset(preset_id)


@api_bp.route("/param-presets")
def list_param_presets_route():
    return ok(data=[_row_to_dict(r) for r in list_param_presets_raw()])


@api_bp.route("/param-presets", methods=["POST"])
def create_param_preset_route():
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

    pid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    p = {
        "id": pid,
        "name": name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "is_default": False,
        "created_at": now,
        "updated_at": now,
    }
    create_param_preset(p)

    return ok(data=_row_to_dict(p))


@api_bp.route("/param-presets/<preset_id>", methods=["PUT"])
def update_param_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or row["name"]).strip()

    try:
        temperature = float(body.get("temperature", row["temperature"]))
        max_tokens = int(body.get("max_tokens", row["max_tokens"]))
        top_p = float(body.get("top_p", row["top_p"]))
    except (ValueError, TypeError):
        return fail(400, "参数格式错误", request)

    if not 0 <= temperature <= 2:
        return fail(400, "temperature 范围 0~2", request)
    if max_tokens < 1:
        return fail(400, "max_tokens 必须 > 0", request)
    if not 0 <= top_p <= 1:
        return fail(400, "top_p 范围 0~1", request)

    now = datetime.now(timezone.utc).isoformat()

    updates = {
        "name": name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "updated_at": now,
    }
    update_param_preset(preset_id, updates)

    updated = _get_or_404(preset_id)
    return ok(data=_row_to_dict(updated))


@api_bp.route("/param-presets/<preset_id>", methods=["DELETE"])
def delete_param_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)
    if row.get("is_default"):
        return fail(409, "不能删除默认参数预设，请先切换默认预设", request)

    delete_param_preset(preset_id)
    return ok()


@api_bp.route("/param-presets/<preset_id>/default", methods=["PUT"])
def set_default_param_preset_route(preset_id):
    row = _get_or_404(preset_id)
    if not row:
        return fail(404, "参数预设不存在", request)

    set_default_param_preset(preset_id)
    return ok(data={"is_default": True})
```

- [ ] **Step 2: 在 `backend/app/__init__.py` 中注册路由**

在 `create_app()` 的蓝图注册区域，`import app.routes.conversations` 下一行添加：

```python
    import app.routes.param_presets  # noqa — 注册 /api/param-presets 系列路由
```

- [ ] **Step 3: 手动验证 API**

```bash
cd D:/UsersProject/chat/backend && python run.py &
sleep 2
# 测试列表
curl -s http://127.0.0.1:5000/api/param-presets | python -m json.tool
# 测试创建
curl -s -X POST http://127.0.0.1:5000/api/param-presets -H "Content-Type: application/json" -d '{"name":"创意模式","temperature":0.9,"max_tokens":4096,"top_p":0.95}' | python -m json.tool
# 清理
kill %1 2>/dev/null
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/param_presets.py backend/app/__init__.py
git commit -m "feat: add /api/param-presets CRUD endpoints"
```

---

### Task 3: 后端 — `ai.py` 增加 `top_p` 透传 + `conversations.py` 接受参数

**Files:**
- Modify: `backend/app/services/ai.py`
- Modify: `backend/app/routes/conversations.py`

**Interfaces:**
- Consumes: `stream_chat()` 新增 `top_p` 参数
- Produces: `_stream_and_save()` 接受 `temperature`, `max_tokens`, `top_p`；`chat()` 和 `regenerate()` 从请求体读取参数值

- [ ] **Step 1: 修改 `backend/app/services/ai.py` — 增加 `top_p` 参数**

修改 `stream_chat` 函数签名和 payload 构建：

```python
def stream_chat(api_url, api_key, model, messages, response_format, cancel_event,
               temperature=None, max_tokens=None, top_p=None):
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
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p
```

实际改动：签名第 6 行 `temperature=None, max_tokens=None):` → `temperature=None, max_tokens=None, top_p=None):`，并在 `max_tokens` 块后加 `top_p` 块。

- [ ] **Step 2: 修改 `backend/app/routes/conversations.py` — `_stream_and_save` 接受参数**

```python
def _stream_and_save(settings, messages, conv_id, cancel_event,
                     temperature=None, max_tokens=None, top_p=None):
    """Shared SSE generator: stream AI response, save assistant message, unregister."""

    full_content = ""
    full_reasoning = ""
    assistant_msg_id = str(uuid.uuid4())
    assistant_created = datetime.now(timezone.utc).isoformat()

    try:
        for chunk in stream_chat(
            settings["api_url"],
            settings["api_key"],
            settings["model"],
            messages,
            settings.get("response_format", ""),
            cancel_event,
            temperature,
            max_tokens,
            top_p,
        ):
```

关键改动：
- 函数签名增加 `temperature=None, max_tokens=None, top_p=None`
- `stream_chat()` 调用中，`settings.get("temperature")` → `temperature`，`settings.get("max_tokens")` → `max_tokens`，新增 `top_p`

- [ ] **Step 3: 修改 `chat()` 端点 — 从请求体读取参数**

在 `chat()` 函数中，`body` 解析处补充三个字段：

```python
    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    # 新增：从请求体读取参数预设值
    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    top_p = body.get("top_p")
```

然后修改 `_stream_and_save` 调用，传入新参数：

```python
    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event,
                                             temperature=temperature, max_tokens=max_tokens, top_p=top_p)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 4: 修改 `regenerate()` 端点 — 同样接受参数**

在 `regenerate()` 函数中同样从 `body` 提取：

```python
    body = request.get_json(silent=True) or {}
    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    top_p = body.get("top_p")

    # ... existing code ...

    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event,
                                             temperature=temperature, max_tokens=max_tokens, top_p=top_p)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 5: 验证后端改动**

```bash
cd D:/UsersProject/chat/backend && python -c "
from app.services.ai import stream_chat
import inspect
sig = inspect.signature(stream_chat)
assert 'top_p' in sig.parameters, 'top_p not in stream_chat signature'
print('OK: top_p accepted')
"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ai.py backend/app/routes/conversations.py
git commit -m "feat: pass temperature/max_tokens/top_p from request body to stream_chat"
```

---

### Task 4: 前端 API 封装 + Store

**Files:**
- Create: `frontend/src/api/paramPresets.js`
- Create: `frontend/src/stores/paramPresets.js`

**Interfaces:**
- Consumes: `http` from `request.js`
- Produces: `paramPresetsApi` (list/create/update/remove/setDefault), `useParamPresetsStore` (presets, activePresetId, temperature/maxTokens/topP getters, loadPresets/selectPreset/createPreset/savePreset/deletePreset actions)

- [ ] **Step 1: 创建 `frontend/src/api/paramPresets.js`**

```js
/**
 * 参数预设 API
 */
import http from "./request.js";

export function list() {
  return http.get("/param-presets");
}

export function create(data) {
  return http.post("/param-presets", data);
}

export function update(id, data) {
  return http.put(`/param-presets/${id}`, data);
}

export function remove(id) {
  return http.delete(`/param-presets/${id}`);
}

export function setDefault(id) {
  return http.put(`/param-presets/${id}/default`);
}
```

- [ ] **Step 2: 创建 `frontend/src/stores/paramPresets.js`**

```js
import { defineStore } from "pinia";
import * as paramPresetsApi from "@/api/paramPresets";

export const useParamPresetsStore = defineStore("paramPresets", {
  state: () => ({
    presets: [],
    activePresetId: null,
    loading: false,
  }),

  getters: {
    activePreset() {
      return this.presets.find((p) => p.id === this.activePresetId) || null;
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
  },

  actions: {
    async loadPresets() {
      this.loading = true;
      try {
        this.presets = await paramPresetsApi.list();
        if (!this.presets || !Array.isArray(this.presets)) {
          this.presets = [];
        }
        if (!this.activePresetId && this.presets.length > 0) {
          const def = this.presets.find((p) => p.is_default) || this.presets[0];
          if (def && def.id) {
            this.activePresetId = def.id;
          }
        }
        if (this.activePresetId && !this.presets.some((p) => p.id === this.activePresetId)) {
          if (this.presets.length > 0) {
            this.activePresetId = this.presets[0].id;
          } else {
            this.activePresetId = null;
          }
        }
      } catch (e) {
        this.presets = [];
        console.error("加载参数预设列表失败:", e);
        throw e;
      } finally {
        this.loading = false;
      }
    },

    selectPreset(id) {
      if (id == null) {
        this.activePresetId = null;
        return;
      }
      if (this.presets.find((p) => p.id === id)) {
        this.activePresetId = id;
      }
    },

    async createPreset(name, temperature, maxTokens, topP) {
      if (!name || !name.trim()) throw new Error("预设名称不能为空");
      const preset = await paramPresetsApi.create({
        name: name.trim(),
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
      });
      if (!preset || !preset.id) throw new Error("创建预设失败：服务器返回异常");
      this.presets.push(preset);
      this.activePresetId = preset.id;
    },

    async savePreset(temperature, maxTokens, topP) {
      if (!this.activePresetId) throw new Error("未选中任何预设");
      const preset = this.activePreset;
      if (!preset) throw new Error("未选中任何预设");
      const updated = await paramPresetsApi.update(this.activePresetId, {
        name: preset.name,
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
      });
      if (!updated || !updated.id) throw new Error("保存失败：服务器返回异常");
      const idx = this.presets.findIndex((p) => p.id === this.activePresetId);
      if (idx !== -1) this.presets[idx] = updated;
    },

    async deletePreset(id) {
      if (!id) throw new Error("未指定要删除的预设");
      await paramPresetsApi.remove(id);
      this.presets = this.presets.filter((p) => p.id !== id);
      if (this.activePresetId === id) {
        this.activePresetId = null;
        if (this.presets.length > 0) {
          this.activePresetId = this.presets[0].id;
        }
      }
    },
  },
});
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/paramPresets.js frontend/src/stores/paramPresets.js
git commit -m "feat: add paramPresets API layer and Pinia store"
```

---

### Task 5: 前端组件 — ParamPresetSelector

**Files:**
- Create: `frontend/src/components/ParamPresetSelector.vue`

**Interfaces:**
- Consumes: `useParamPresetsStore`, `useAlertStore`, `BaseDialog`
- Produces: 自包含的参数预设管理面板组件

- [ ] **Step 1: 创建 `frontend/src/components/ParamPresetSelector.vue`**

```vue
<template>
  <div class="pp-area">
    <!-- 预设选择行 -->
    <div class="pp-row">
      <select v-model="store.activePresetId" class="pp-select" @change="onSelect">
        <option :value="null" disabled>请选择预设</option>
        <option v-for="p in store.presets" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>
      <button class="pp-btn" title="新建" @click="clearForm">+</button>
      <button
        class="pp-btn"
        title="删除"
        @click="handleDelete"
        :disabled="!store.activePresetId"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
      </button>
    </div>

    <!-- 参数表单 -->
    <div class="pp-fields">
      <label class="pp-label">
        Temperature
        <input
          v-model.number="form.temperature"
          type="number"
          class="pp-input"
          step="0.1"
          min="0"
          max="2"
        />
      </label>
      <label class="pp-label">
        Max Tokens
        <input
          v-model.number="form.maxTokens"
          type="number"
          class="pp-input"
          step="1"
          min="1"
        />
      </label>
      <label class="pp-label">
        Top P
        <input
          v-model.number="form.topP"
          type="number"
          class="pp-input"
          step="0.01"
          min="0"
          max="1"
        />
      </label>
    </div>

    <button class="pp-save-btn" @click="handleSave" :disabled="!store.activePresetId">保存</button>

    <!-- Toast -->
    <transition name="fade">
      <span v-if="toastMsg" class="pp-toast">{{ toastMsg }}</span>
    </transition>

    <!-- 删除确认弹窗 -->
    <BaseDialog :visible="showDeleteDialog" title=" " @close="cancelDelete">
      <div class="dialog-danger">
        <div class="dialog-danger-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef5350" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <p class="dialog-danger-msg">确定要删除预设「{{ deletingPresetName }}」吗？此操作不可撤销。</p>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelDelete">取消</button>
        <button class="dialog-btn dialog-btn-danger" @click="confirmDelete">确定删除</button>
      </template>
    </BaseDialog>

    <!-- 命名弹窗 -->
    <BaseDialog :visible="showNameDialog" title="新建预设" @close="cancelNameDialog">
      <input
        ref="nameInput"
        v-model="dialogName"
        class="dialog-input"
        placeholder="输入预设名称"
        @keydown.enter="confirmNameDialog"
        @keydown.escape="cancelNameDialog"
      />
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelNameDialog">取消</button>
        <button class="dialog-btn dialog-btn-ok" @click="confirmNameDialog" :disabled="!dialogName.trim()">确认</button>
      </template>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from "vue";
import { useParamPresetsStore } from "@/stores/paramPresets";
import { useAlertStore } from "@/stores/alert";
import BaseDialog from "@/components/BaseDialog.vue";

const store = useParamPresetsStore();
const alert = useAlertStore();

const emit = defineEmits(["saved"]);

const toastMsg = ref("");
let toastTimer = null;

const form = reactive({
  temperature: 0.7,
  maxTokens: 4096,
  topP: 1.0,
});

// 切换预设时同步表单
watch(() => store.activePresetId, (id) => {
  const p = store.presets.find((p) => p.id === id);
  if (p) {
    form.temperature = p.temperature;
    form.maxTokens = p.max_tokens;
    form.topP = p.top_p;
  }
});

function onSelect() {
  // activePresetId 已由 v-model 更新，watch 自动同步表单
}

// 新建
const showNameDialog = ref(false);
const dialogName = ref("");
const nameInput = ref(null);

function clearForm() {
  store.activePresetId = null;
  form.temperature = 0.7;
  form.maxTokens = 4096;
  form.topP = 1.0;

  let base = "新预设";
  let candidate = base;
  let n = 1;
  while (store.presets.some((p) => p.name === candidate)) {
    candidate = `${base} (${n})`;
    n++;
  }
  dialogName.value = candidate;
  showNameDialog.value = true;
  nextTick(() => {
    nameInput.value?.focus();
    nameInput.value?.select();
  });
}

async function confirmNameDialog() {
  const name = dialogName.value.trim();
  if (!name) return;
  showNameDialog.value = false;
  try {
    await store.createPreset(name, form.temperature, form.maxTokens, form.topP);
    showToast("预设已创建");
    emit("saved");
  } catch (e) {
    alert.error("创建失败", e.message || "未知错误");
  }
}

function cancelNameDialog() {
  showNameDialog.value = false;
  dialogName.value = "";
}

// 保存
async function handleSave() {
  if (!store.activePresetId) return;
  try {
    await store.savePreset(form.temperature, form.maxTokens, form.topP);
    showToast("保存成功");
  } catch (e) {
    alert.error("保存失败", e.message || "未知错误");
  }
}

// 删除
const showDeleteDialog = ref(false);
const deletingPresetName = ref("");

function handleDelete() {
  const p = store.presets.find((p) => p.id === store.activePresetId);
  deletingPresetName.value = p?.name || "未命名";
  showDeleteDialog.value = true;
}

async function confirmDelete() {
  showDeleteDialog.value = false;
  try {
    await store.deletePreset(store.activePresetId);
    showToast("已删除");
  } catch (e) {
    alert.error("删除失败", e.message || "未知错误");
  }
}

function cancelDelete() {
  showDeleteDialog.value = false;
}

function showToast(msg) {
  toastMsg.value = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastMsg.value = ""; }, 2000);
}
</script>

<style scoped>
.pp-area {
  position: relative;
  padding: 8px 0;
}

.pp-row {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 16px;
}

.pp-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  font-family: inherit;
}

.pp-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.pp-btn:hover:not(:disabled) {
  background: #f0f0f0;
  color: #333;
}
.pp-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.pp-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.pp-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #888;
  font-weight: 500;
}

.pp-input {
  padding: 10px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
  width: 100%;
  box-sizing: border-box;
}
.pp-input:focus {
  border-color: #4a90d9;
  box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.15);
}

.pp-save-btn {
  width: 100%;
  padding: 10px 0;
  border: none;
  border-radius: 8px;
  background: #4a90d9;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}
.pp-save-btn:hover:not(:disabled) {
  background: #357abd;
}
.pp-save-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.pp-toast {
  position: absolute;
  top: -6px;
  left: 0;
  font-size: 12px;
  color: #555;
  background: #f5f5f5;
  padding: 3px 10px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ParamPresetSelector.vue
git commit -m "feat: add ParamPresetSelector component"
```

---

### Task 6: 前端集成 — App.vue 工具栏 + chat.js 发送参数

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/stores/chat.js`

**Interfaces:**
- Consumes: `ParamPresetSelector`, `useParamPresetsStore`
- Produces: 工具栏"预设"按钮 + SettingsDrawer 实例；`sendMessage()` 携带参数预设值

- [ ] **Step 1: 修改 `frontend/src/App.vue` — 工具栏加按钮 + 第二个抽屉**

模板部分：

```vue
<template>
  <div id="app" class="app-shell">
    <header class="top-bar">
      <div class="top-left">
        <button class="top-btn" @click="showConversations = !showConversations">会话记录</button>
        <span class="top-title">Chat</span>
      </div>
      <nav class="top-nav">
        <button class="top-btn" @click="showParamPresets = !showParamPresets">预设</button>
        <button class="top-btn" @click="showSettings = !showSettings">API 设置</button>
      </nav>
    </header>
    <div class="app-body">
      <ConversationsDrawer :visible="showConversations" @close="showConversations = false" />
      <main class="main-area">
        <router-view />
      </main>
      <SettingsDrawer :visible="showParamPresets" @close="showParamPresets = false">
        <template #title>预设</template>
        <ParamPresetSelector @saved="showParamPresets = false" />
      </SettingsDrawer>
      <SettingsDrawer :visible="showSettings" @close="showSettings = false">
        <template #title>API 设置</template>
        <SettingsView @saved="showSettings = false" />
      </SettingsDrawer>
    </div>
    <AlertDialog />
  </div>
</template>
```

Script 部分：

```js
<script setup>
import { ref, onMounted } from "vue";
import ConversationsDrawer from "@/components/ConversationsDrawer.vue";
import SettingsDrawer from "@/components/SettingsDrawer.vue";
import SettingsView from "@/views/SettingsView.vue";
import ParamPresetSelector from "@/components/ParamPresetSelector.vue";
import AlertDialog from "@/components/AlertDialog.vue";
import { useChatStore } from "@/stores/chat";
import { useParamPresetsStore } from "@/stores/paramPresets";

const chatStore = useChatStore();
const paramPresetsStore = useParamPresetsStore();
const showConversations = ref(false);
const showSettings = ref(false);
const showParamPresets = ref(false);

onMounted(() => {
  chatStore.loadConversations();
  paramPresetsStore.loadPresets();
});
</script>
```

- [ ] **Step 2: 修改 `frontend/src/stores/chat.js` — 发送时携带参数预设值**

在 `sendMessage()` 方法中，修改 SSE 请求的 body：

找到：
```js
      const es = sse(`/conversations/${this.activeConvId}/chat`, {
        method: "POST",
        body: JSON.stringify({ content }),
```

改为：
```js
      const es = sse(`/conversations/${this.activeConvId}/chat`, {
        method: "POST",
        body: JSON.stringify({
          content,
          temperature: paramPresetsStore.temperature,
          max_tokens: paramPresetsStore.maxTokens,
          top_p: paramPresetsStore.topP,
        }),
```

需要在文件顶部添加 import：

```js
import { useParamPresetsStore } from "@/stores/paramPresets";
```

并在 `sendMessage` 方法中获取 store 实例：

```js
    async sendMessage(content) {
      if (this.isStreaming) return;

      const paramPresetsStore = useParamPresetsStore();

      // ... rest of the method
```

- [ ] **Step 3: 构建验证**

```bash
cd D:/UsersProject/chat/frontend && npm run build
```
Expected: 构建成功，无错误。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue frontend/src/stores/chat.js
git commit -m "feat: integrate param presets into toolbar and chat send flow"
```

---

### Task 7: 端到端验证 + 测试

**Files:**
- Create: `backend/tests/test_param_presets.py`

- [ ] **Step 1: 创建后端测试 `backend/tests/test_param_presets.py`**

```python
import pytest
import json


def test_list_empty_returns_default(app_client, monkeypatch, tmp_path):
    """首次无文件时应自动创建默认预设"""
    from app import create_app
    resp = app_client.get("/api/param-presets")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    assert len(data["data"]) >= 1
    default = [p for p in data["data"] if p.get("is_default")]
    assert len(default) == 1
    assert default[0]["temperature"] == 0.7
    assert default[0]["max_tokens"] == 4096
    assert default[0]["top_p"] == 1.0


def test_create_param_preset(app_client):
    resp = app_client.post("/api/param-presets", json={
        "name": "创意模式",
        "temperature": 0.9,
        "max_tokens": 2048,
        "top_p": 0.95,
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    preset = data["data"]
    assert preset["name"] == "创意模式"
    assert preset["temperature"] == 0.9
    assert preset["max_tokens"] == 2048
    assert preset["top_p"] == 0.95
    assert "id" in preset


def test_create_param_preset_validation(app_client):
    """测试参数范围校验"""
    # 空名称
    resp = app_client.post("/api/param-presets", json={"name": "", "temperature": 0.7, "max_tokens": 4096, "top_p": 1.0})
    assert resp.get_json()["code"] != 0

    # temperature 超出范围
    resp = app_client.post("/api/param-presets", json={"name": "test", "temperature": 3.0, "max_tokens": 4096, "top_p": 1.0})
    assert resp.get_json()["code"] != 0

    # top_p 超出范围
    resp = app_client.post("/api/param-presets", json={"name": "test", "temperature": 0.7, "max_tokens": 4096, "top_p": 2.0})
    assert resp.get_json()["code"] != 0


def test_delete_default_blocked(app_client):
    """不能删除默认预设"""
    resp = app_client.get("/api/param-presets")
    default_id = [p["id"] for p in resp.get_json()["data"] if p["is_default"]][0]
    resp = app_client.delete(f"/api/param-presets/{default_id}")
    assert resp.get_json()["code"] == 409


def test_set_default(app_client):
    """设为默认"""
    # 创建一条非默认
    resp = app_client.post("/api/param-presets", json={
        "name": "测试",
        "temperature": 0.5,
        "max_tokens": 100,
        "top_p": 0.8,
    })
    preset_id = resp.get_json()["data"]["id"]

    # 设为默认
    resp = app_client.put(f"/api/param-presets/{preset_id}/default")
    assert resp.status_code == 200
    assert resp.get_json()["code"] == 0

    # 验证只有它是默认
    resp = app_client.get("/api/param-presets")
    defaults = [p for p in resp.get_json()["data"] if p["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == preset_id
```

- [ ] **Step 2: 运行测试**

```bash
cd D:/UsersProject/chat/backend && python -m pytest tests/test_param_presets.py -v
```
Expected: 所有测试通过。

- [ ] **Step 3: 运行已有测试确保无回归**

```bash
cd D:/UsersProject/chat/backend && python -m pytest -v
```
Expected: 全部 39+ 个测试通过。

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_param_presets.py
git commit -m "test: add param_presets API tests"
```
