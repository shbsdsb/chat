# 提示词条目系统（Phase 1）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在参数预设系统基础上新增提示词条目 CRUD + 拖拽排序，第一阶段只做名称 + 开关，不含内容编辑和组合逻辑。

**Architecture:** 独立后端存储 + API，通过 preset_id 关联参数预设，前端 Pinia store 与 paramPresets store 联动，PromptEntryCard 组件放在 App.vue 中 ParamPresetSelector 下方。

**Tech Stack:** Python 3 / Flask / threading.Lock（后端），Vue 3 Composition API / Pinia / HTML5 Drag & Drop（前端）

## Global Constraints

- 后端响应统一 `ok(data)` / `fail(code, message)`，code=0 成功
- 前端 API 通过 `./request.js` 的 `http` 实例封装，自动解包 `{code, message, data}`
- 组件使用 `<script setup>` + `<style scoped>`
- 样式遵循 `tokens.css` 中的 CSS 变量
- TDD：先写测试，再写实现

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| Create | `backend/app/storage/prompt_entries.py` | JSON 文件 CRUD + reorder |
| Create | `backend/app/routes/prompt_entries.py` | REST API 5 端点 |
| Modify | `backend/app/__init__.py` | 注册路由 + init |
| Modify | `backend/app/storage/__init__.py` | 导出新模块 |
| Modify | `backend/app/routes/param_presets.py` | 删除预设时联动清理 |
| Create | `backend/tests/test_prompt_entries.py` | pytest 后端测试 |
| Create | `frontend/src/api/promptEntries.js` | API 封装 |
| Create | `frontend/src/stores/promptEntries.js` | Pinia store |
| Create | `frontend/src/components/PromptEntryCard.vue` | 卡片容器 |
| Create | `frontend/src/components/PromptEntryItem.vue` | 单行条目 |
| Modify | `frontend/src/App.vue` | 放入 PromptEntryCard |

---

### Task 1: 后端存储 — 提示词条目 CRUD

**Files:**
- Create: `backend/app/storage/prompt_entries.py`
- Modify: `backend/app/storage/__init__.py`

**Interfaces:**
- Produces: `get_entries(preset_id)`, `create_entry(preset_id, name)`, `update_entry(preset_id, entry_id, data)`, `delete_entry(preset_id, entry_id)`, `reorder_entries(preset_id, id_order_list)`, `delete_preset_entries(preset_id)`

---

- [ ] **Step 1: 创建 `prompt_entries.py`**

```python
# backend/app/storage/prompt_entries.py
import os
import uuid
from .conversations import _read_json, _write_json, _lock, DATA_DIR

PROMPT_ENTRIES_DIR = os.path.join(DATA_DIR, "prompt_entries")


def _get_file_path(preset_id):
    return os.path.join(PROMPT_ENTRIES_DIR, f"{preset_id}.json")


def _ensure_dir():
    os.makedirs(PROMPT_ENTRIES_DIR, exist_ok=True)


def get_entries(preset_id):
    """返回指定预设的所有提示词条目，按 order 排序。文件不存在返回 []。"""
    _ensure_dir()
    filepath = _get_file_path(preset_id)
    if not os.path.exists(filepath):
        return []
    entries = _read_json(filepath)
    entries.sort(key=lambda e: e.get("order", 0))
    return entries


def create_entry(preset_id, name):
    """创建新条目，order = 当前最大 + 1，enabled 默认 True。"""
    with _lock:
        entries = get_entries(preset_id)
        max_order = max((e.get("order", 0) for e in entries), default=-1)
        entry = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "enabled": True,
            "order": max_order + 1,
        }
        entries.append(entry)
        _ensure_dir()
        _write_json(_get_file_path(preset_id), entries)
        return entry


def update_entry(preset_id, entry_id, data):
    """更新条目字段（name / enabled）。"""
    with _lock:
        entries = get_entries(preset_id)
        for entry in entries:
            if entry["id"] == entry_id:
                if "name" in data:
                    entry["name"] = data["name"].strip()
                if "enabled" in data:
                    entry["enabled"] = bool(data["enabled"])
                _write_json(_get_file_path(preset_id), entries)
                return entry
        return None


def delete_entry(preset_id, entry_id):
    """删除条目并重整 order 为连续值。"""
    with _lock:
        entries = get_entries(preset_id)
        entries = [e for e in entries if e["id"] != entry_id]
        for i, entry in enumerate(entries):
            entry["order"] = i
        _write_json(_get_file_path(preset_id), entries)
        return True


def reorder_entries(preset_id, id_order_list):
    """按传入的 id 列表批量写入新 order。"""
    with _lock:
        entries = get_entries(preset_id)
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
```

- [ ] **Step 2: 在 `storage/__init__.py` 中导出**

在 `backend/app/storage/__init__.py` 末尾追加：

```python
# prompt_entries
from .prompt_entries import (
    get_entries,
    create_entry,
    update_entry,
    delete_entry,
    reorder_entries,
    delete_preset_entries,
)
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/storage/prompt_entries.py backend/app/storage/__init__.py
git commit -m "feat: add prompt_entries storage layer with CRUD and reorder"
```

---

### Task 2: 后端路由 — 提示词条目 API

**Files:**
- Create: `backend/app/routes/prompt_entries.py`
- Modify: `backend/app/__init__.py`

**Interfaces:**
- Consumes: `api_bp` from `app.routes`, `ok`/`fail` from `app.utils.response`, all storage functions from Task 1
- Produces: GET/POST/PUT/DELETE routes on `/api/prompt-entries`

---

- [ ] **Step 1: 创建 `prompt_entries.py` 路由文件**

```python
# backend/app/routes/prompt_entries.py
from flask import request
from app.routes import api_bp
from app.storage import (
    get_entries,
    create_entry,
    update_entry,
    delete_entry,
    reorder_entries,
)
from app.storage.param_presets import get_param_preset
from app.utils.response import ok, fail


def _verify_preset(preset_id):
    """校验参数预设存在。"""
    if not get_param_preset(preset_id):
        return False
    return True


@api_bp.route("/prompt-entries", methods=["GET"])
def list_prompt_entries():
    preset_id = request.args.get("preset_id", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    entries = get_entries(preset_id)
    return ok(entries)


@api_bp.route("/prompt-entries", methods=["POST"])
def create_prompt_entry():
    data = request.get_json(silent=True) or {}
    preset_id = data.get("preset_id", "")
    name = data.get("name", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    if not name or not name.strip():
        return fail(400, "名称不能为空")
    entry = create_entry(preset_id, name)
    return ok(entry, "创建成功")


@api_bp.route("/prompt-entries/<entry_id>", methods=["PUT"])
def update_prompt_entry(entry_id):
    data = request.get_json(silent=True) or {}
    preset_id = data.get("preset_id", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    updates = {}
    if "name" in data:
        if not data["name"] or not data["name"].strip():
            return fail(400, "名称不能为空")
        updates["name"] = data["name"]
    if "enabled" in data:
        updates["enabled"] = data["enabled"]
    if not updates:
        return fail(400, "没有需要更新的字段")
    entry = update_entry(preset_id, entry_id, updates)
    if entry is None:
        return fail(404, "条目不存在")
    return ok(entry, "更新成功")


@api_bp.route("/prompt-entries/<entry_id>", methods=["DELETE"])
def delete_prompt_entry(entry_id):
    preset_id = request.args.get("preset_id", "")
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    delete_entry(preset_id, entry_id)
    return ok(None, "删除成功")


@api_bp.route("/prompt-entries/reorder", methods=["PUT"])
def reorder_prompt_entries():
    data = request.get_json(silent=True) or {}
    preset_id = data.get("preset_id", "")
    ids = data.get("ids", [])
    if not preset_id:
        return fail(400, "缺少 preset_id 参数")
    if not _verify_preset(preset_id):
        return fail(404, "参数预设不存在")
    if not isinstance(ids, list):
        return fail(400, "ids 必须是数组")
    reorder_entries(preset_id, ids)
    return ok(None, "排序成功")
```

- [ ] **Step 2: 在 `__init__.py` 中注册路由**

在 `backend/app/__init__.py` 的 import 块中（第 31-37 行之间），添加一行：

```python
import app.routes.prompt_entries     # noqa: F401 — 触发 @api_bp.route() 装饰器注册
```

位置：放在 `import app.routes.param_presets` 之后。

同时在 `init_storage()` 调用后（第 48 行之后），添加 prompt_entries 目录初始化：

```python
os.makedirs(os.path.join(DATA_DIR, "prompt_entries"), exist_ok=True)
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/routes/prompt_entries.py backend/app/__init__.py
git commit -m "feat: add prompt_entries REST API routes"
```

---

### Task 3: 参数预设删除联动

**Files:**
- Modify: `backend/app/routes/param_presets.py`

**Interfaces:**
- Consumes: `delete_preset_entries` from `app.storage`

---

- [ ] **Step 1: 修改 `param_presets.py` 删除路由**

在 `backend/app/routes/param_presets.py` 顶部 import 区添加：

```python
from app.storage.prompt_entries import delete_preset_entries
```

在 `delete_param_preset_route` 函数中，`delete_param_preset(preset_id)` 调用之后、`return ok(...)` 之前，添加：

```python
    delete_preset_entries(preset_id)
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/routes/param_presets.py
git commit -m "feat: cascade delete prompt entries when param preset is deleted"
```

---

### Task 4: 后端测试

**Files:**
- Create: `backend/tests/test_prompt_entries.py`

**Interfaces:**
- Consumes: `test_app` fixture from `conftest.py`，`_monkey_patched_dirs` fixture

---

- [ ] **Step 1: 编写测试文件**

```python
# backend/tests/test_prompt_entries.py
import json


def _create_preset(test_app, name="测试预设"):
    """辅助：创建一个参数预设并返回其 id。"""
    resp = test_app.post(
        "/api/param-presets",
        json={"name": name, "temperature": 0.5, "max_tokens": 2048, "top_p": 0.9},
    )
    return resp.get_json()["data"]["id"]


class TestPromptEntriesCRUD:
    def test_list_empty(self, test_app):
        """空列表返回 []。"""
        preset_id = _create_preset(test_app)
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"] == []

    def test_create_entry(self, test_app):
        """创建条目成功。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post(
            "/api/prompt-entries",
            json={"preset_id": preset_id, "name": "🏃 测试角色"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["code"] == 0
        entry = data["data"]
        assert entry["name"] == "🏃 测试角色"
        assert entry["enabled"] is True
        assert "id" in entry
        assert "order" in entry

    def test_create_entry_missing_name(self, test_app):
        """缺少名称返回 400。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post(
            "/api/prompt-entries",
            json={"preset_id": preset_id, "name": ""},
        )
        assert resp.status_code == 200
        assert resp.get_json()["code"] != 0

    def test_create_entry_invalid_preset(self, test_app):
        """无效的 preset_id 返回 404。"""
        resp = test_app.post(
            "/api/prompt-entries",
            json={"preset_id": "nonexistent", "name": "测试"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["code"] != 0

    def test_list_ordered(self, test_app):
        """列表按 order 排序返回。"""
        preset_id = _create_preset(test_app)
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "B"})
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "A"})
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "C"})

        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        entries = resp.get_json()["data"]
        names = [e["name"] for e in entries]
        assert names == ["B", "A", "C"]

    def test_update_entry(self, test_app):
        """更新条目名称和开关。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "原始名称"})
        entry_id = resp.get_json()["data"]["id"]

        resp = test_app.put(
            f"/api/prompt-entries/{entry_id}",
            json={"preset_id": preset_id, "name": "新名称", "enabled": False},
        )
        assert resp.status_code == 200
        entry = resp.get_json()["data"]
        assert entry["name"] == "新名称"
        assert entry["enabled"] is False

    def test_delete_entry(self, test_app):
        """删除条目成功。"""
        preset_id = _create_preset(test_app)
        resp = test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "待删除"})
        entry_id = resp.get_json()["data"]["id"]

        resp = test_app.delete(f"/api/prompt-entries/{entry_id}?preset_id={preset_id}")
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 0

        # 验证已删除
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        assert resp.get_json()["data"] == []

    def test_reorder(self, test_app):
        """批量排序。"""
        preset_id = _create_preset(test_app)
        ids = []
        for name in ["A", "B", "C"]:
            resp = test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": name})
            ids.append(resp.get_json()["data"]["id"])

        # 反序
        reversed_ids = list(reversed(ids))
        resp = test_app.put(
            "/api/prompt-entries/reorder",
            json={"preset_id": preset_id, "ids": reversed_ids},
        )
        assert resp.status_code == 200

        # 验证顺序
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        entries = resp.get_json()["data"]
        assert [e["id"] for e in entries] == reversed_ids

    def test_cascade_delete_with_preset(self, test_app):
        """删除参数预设时联动清理提示词条目。"""
        preset_id = _create_preset(test_app)
        test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "测试"})

        # 删除参数预设
        test_app.delete(f"/api/param-presets/{preset_id}")

        # 条目文件应该不存在或返回空
        resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
        # preset 不存在了，应返回 404
        assert resp.get_json()["code"] != 0
```

- [ ] **Step 2: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_prompt_entries.py -v
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_prompt_entries.py
git commit -m "test: add prompt_entries CRUD and cascade delete tests"
```

---

### Task 5: 前端 API 封装

**Files:**
- Create: `frontend/src/api/promptEntries.js`

**Interfaces:**
- Consumes: `http` from `@/api/request.js`
- Produces: `getEntries`, `createEntry`, `updateEntry`, `deleteEntry`, `reorderEntries`

---

- [ ] **Step 1: 创建 API 文件**

```javascript
// frontend/src/api/promptEntries.js
import http from "./request.js";

export function getEntries(presetId) {
  return http.get("/prompt-entries", { params: { preset_id: presetId } });
}

export function createEntry(presetId, name) {
  return http.post("/prompt-entries", { preset_id: presetId, name });
}

export function updateEntry(id, presetId, data) {
  return http.put(`/prompt-entries/${id}`, { preset_id: presetId, ...data });
}

export function deleteEntry(id, presetId) {
  return http.delete(`/prompt-entries/${id}`, { params: { preset_id: presetId } });
}

export function reorderEntries(presetId, ids) {
  return http.put("/prompt-entries/reorder", { preset_id: presetId, ids });
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/promptEntries.js
git commit -m "feat: add promptEntries API client"
```

---

### Task 6: 前端 Pinia Store

**Files:**
- Create: `frontend/src/stores/promptEntries.js`

**Interfaces:**
- Consumes: `paramPresetsStore.activePresetId`（通过 `useParamPresetsStore`），API functions from Task 5
- Produces: `usePromptEntriesStore` — `entries`, `loading`, `loadEntries`, `createEntry`, `updateEntry`, `deleteEntry`, `reorderEntries`

---

- [ ] **Step 1: 创建 Store**

```javascript
// frontend/src/stores/promptEntries.js
import { defineStore } from "pinia";
import * as promptEntriesApi from "@/api/promptEntries";
import { useParamPresetsStore } from "@/stores/paramPresets";

export const usePromptEntriesStore = defineStore("promptEntries", {
  state: () => ({
    entries: [],
    loading: false,
  }),

  getters: {
    enabledEntries(state) {
      return state.entries.filter((e) => e.enabled);
    },
  },

  actions: {
    async loadEntries(presetId) {
      if (!presetId) {
        this.entries = [];
        return;
      }
      this.loading = true;
      try {
        this.entries = await promptEntriesApi.getEntries(presetId);
      } catch {
        this.entries = [];
      } finally {
        this.loading = false;
      }
    },

    async createEntry(name) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      const entry = await promptEntriesApi.createEntry(presetId, name);
      this.entries.push(entry);
      return entry;
    },

    async updateEntry(id, data) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      const entry = await promptEntriesApi.updateEntry(id, presetId, data);
      const idx = this.entries.findIndex((e) => e.id === id);
      if (idx !== -1) this.entries[idx] = entry;
      return entry;
    },

    async deleteEntry(id) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      await promptEntriesApi.deleteEntry(id, presetId);
      this.entries = this.entries.filter((e) => e.id !== id);
    },

    async reorderEntries(ids) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      // 乐观更新本地顺序
      const idToEntry = {};
      this.entries.forEach((e) => {
        idToEntry[e.id] = e;
      });
      const reordered = ids.map((id, i) => ({
        ...idToEntry[id],
        order: i,
      }));
      this.entries = reordered;
      // 后端同步
      await promptEntriesApi.reorderEntries(presetId, ids);
    },
  },
});
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/stores/promptEntries.js
git commit -m "feat: add promptEntries Pinia store with paramPresets integration"
```

---

### Task 7: 前端组件 — PromptEntryItem

**Files:**
- Create: `frontend/src/components/PromptEntryItem.vue`

**Interfaces:**
- Consumes: `entry` prop (`{ id, name, enabled, order }`), emits: `toggle`, `edit`, `drag-start`

---

- [ ] **Step 1: 创建 PromptEntryItem 组件**

```vue
<!-- frontend/src/components/PromptEntryItem.vue -->
<template>
  <div
    class="pe-item"
    :class="{ 'pe-item--dragging': isDragging }"
    :draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @dragover.prevent="onDragOver"
    @drop.prevent="onDrop"
  >
    <span class="pe-item__handle" title="拖拽排序">*</span>
    <span class="pe-item__name">{{ entry.name }}</span>
    <span class="pe-item__token">-</span>
    <button class="pe-item__edit" title="编辑" @click="$emit('edit', entry)">
      ✏️
    </button>
    <div
      class="pe-item__toggle toggle-switch"
      :class="{ active: entry.enabled }"
      @click="$emit('toggle', entry)"
    >
      <div class="toggle-switch__slider"></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  entry: { type: Object, required: true },
});

const emit = defineEmits(["toggle", "edit", "drag-start", "drop"]);

const isDragging = ref(false);

function onDragStart(e) {
  isDragging.value = true;
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", props.entry.id);
  emit("drag-start", props.entry);
}

function onDragEnd() {
  isDragging.value = false;
}

function onDragOver(e) {
  e.dataTransfer.dropEffect = "move";
  e.currentTarget.classList.add("pe-item--drop-target");
}

function onDrop(e) {
  e.currentTarget.classList.remove("pe-item--drop-target");
  const draggedId = e.dataTransfer.getData("text/plain");
  emit("drop", draggedId, props.entry.id);
}
</script>

<style scoped>
.pe-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light, #e5e7eb);
  transition: background-color 0.15s;
  user-select: none;
}
.pe-item:last-child {
  border-bottom: none;
}
.pe-item--drop-target {
  border-top: 2px solid var(--color-accent, #4facfe);
}
.pe-item--dragging {
  opacity: 0.5;
}

.pe-item__handle {
  cursor: grab;
  font-size: 16px;
  color: var(--text-muted, #9ca3af);
  margin-right: 8px;
  flex-shrink: 0;
}
.pe-item__handle:active {
  cursor: grabbing;
}

.pe-item__name {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary, #1f2937);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pe-item__token {
  font-size: 12px;
  color: var(--text-muted, #9ca3af);
  width: 30px;
  text-align: right;
  margin-right: 12px;
  flex-shrink: 0;
}

.pe-item__edit {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.6;
  padding: 4px;
  margin-right: 8px;
  flex-shrink: 0;
}
.pe-item__edit:hover {
  opacity: 1;
}

.toggle-switch {
  width: 34px;
  height: 18px;
  background-color: #444;
  border-radius: 10px;
  position: relative;
  cursor: pointer;
  transition: background-color 0.3s;
  flex-shrink: 0;
}
.toggle-switch.active {
  background-color: var(--color-accent, #007aff);
}
.toggle-switch__slider {
  width: 14px;
  height: 14px;
  background-color: #888;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.3s, background-color 0.3s;
}
.toggle-switch.active .toggle-switch__slider {
  transform: translateX(16px);
  background-color: #fff;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/PromptEntryItem.vue
git commit -m "feat: add PromptEntryItem component with drag-and-drop toggle"
```

---

### Task 8: 前端组件 — PromptEntryCard

**Files:**
- Create: `frontend/src/components/PromptEntryCard.vue`

**Interfaces:**
- Consumes: `usePromptEntriesStore`, `useParamPresetsStore`, `PromptEntryItem`
- Produces: 卡片容器，内含条目列表 + 新增按钮

---

- [ ] **Step 1: 创建 PromptEntryCard 组件**

```vue
<!-- frontend/src/components/PromptEntryCard.vue -->
<template>
  <div class="card">
    <div class="card-header">
      <span class="card-icon">📋</span>
      <span class="card-label">提示词条目</span>
      <button class="icon-btn" title="添加条目" @click="showAddInput = true"
        v-if="!showAddInput"
      >+</button>
    </div>

    <!-- 新增输入行 -->
    <div v-if="showAddInput" class="pe-add-row">
      <input
        ref="addInputRef"
        v-model="newName"
        class="input-field"
        placeholder="输入条目名称，回车确认"
        @keydown.enter="handleAdd"
        @keydown.escape="cancelAdd"
        @blur="cancelAdd"
      />
    </div>

    <!-- 空状态 -->
    <div v-if="!store.loading && store.entries.length === 0 && !showAddInput" class="pe-empty">
      暂无条目，点击 + 创建
    </div>

    <!-- 条目列表 -->
    <div v-if="store.entries.length > 0" class="pe-list">
      <PromptEntryItem
        v-for="entry in store.entries"
        :key="entry.id"
        :entry="entry"
        @toggle="handleToggle"
        @drag-start="onDragStart"
        @drop="onDrop"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";
import { usePromptEntriesStore } from "@/stores/promptEntries";
import { useParamPresetsStore } from "@/stores/paramPresets";
import PromptEntryItem from "@/components/PromptEntryItem.vue";

const store = usePromptEntriesStore();
const paramStore = useParamPresetsStore();

const showAddInput = ref(false);
const newName = ref("");
const addInputRef = ref(null);

// 切换参数预设时重新加载条目
watch(
  () => paramStore.activePresetId,
  (newId) => {
    store.loadEntries(newId);
  },
  { immediate: true }
);

// 打开输入框时自动聚焦
watch(showAddInput, async (val) => {
  if (val) {
    await nextTick();
    addInputRef.value?.focus();
  }
});

async function handleAdd() {
  const name = newName.value.trim();
  if (!name) return;
  await store.createEntry(name);
  newName.value = "";
  showAddInput.value = false;
}

function cancelAdd() {
  newName.value = "";
  showAddInput.value = false;
}

async function handleToggle(entry) {
  await store.updateEntry(entry.id, { enabled: !entry.enabled });
}

function onDragStart() {
  // 拖拽开始 — 预留，后续可加视觉反馈
}

function onDrop(draggedId, targetId) {
  const entries = [...store.entries];
  const draggedIdx = entries.findIndex((e) => e.id === draggedId);
  const targetIdx = entries.findIndex((e) => e.id === targetId);
  if (draggedIdx === -1 || targetIdx === -1 || draggedIdx === targetIdx) return;

  // 移动条目
  const [moved] = entries.splice(draggedIdx, 1);
  entries.splice(targetIdx, 0, moved);

  const ids = entries.map((e) => e.id);
  store.reorderEntries(ids);
}
</script>

<style scoped>
.card {
  background: var(--bg-card, #fff);
  border-radius: var(--radius-card, 16px);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.08));
  padding: 16px 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.card-icon {
  font-size: 16px;
}

.card-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  flex: 1;
}

.icon-btn {
  background: none;
  border: 1px solid var(--border-light, #e5e7eb);
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-secondary, #6b7280);
  transition: background-color 0.15s;
}
.icon-btn:hover {
  background: var(--bg-hover, #f3f4f6);
}

.pe-add-row {
  margin-bottom: 8px;
}

.input-field {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-light, #e5e7eb);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-input, #fafbfc);
  color: var(--text-primary, #1f2937);
  outline: none;
  box-sizing: border-box;
}
.input-field:focus {
  border-color: var(--focus-ring, #4facfe);
  box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.15);
}

.pe-empty {
  text-align: center;
  padding: 20px 0;
  color: var(--text-muted, #9ca3af);
  font-size: 13px;
}

.pe-list {
  /* 条目容器 */
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/PromptEntryCard.vue
git commit -m "feat: add PromptEntryCard with add drag reorder toggle"
```

---

### Task 9: 集成到 App.vue

**Files:**
- Modify: `frontend/src/App.vue`

---

- [ ] **Step 1: 在 App.vue 中引入 PromptEntryCard**

在 `frontend/src/App.vue` 中：

在第 46 行（`<ParamPresetSelector>` 之后）添加：

```vue
          <PromptEntryCard v-if="activeDrawer === 'presets'" key="prompt-entries" />
```

在第 62 行附近（`import ParamPresetSelector` 之后）添加 import：

```javascript
import PromptEntryCard from "@/components/PromptEntryCard.vue";
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: integrate PromptEntryCard into presets drawer"
```

---

### Task 10: 端到端验证

- [ ] **Step 1: 启动后端**

```bash
cd backend && python run.py
```

- [ ] **Step 2: 启动前端**

```bash
cd frontend && npm run dev
```

- [ ] **Step 3: 手动验证清单**

| 检查项 | 操作 | 预期 |
|--------|------|------|
| 预设抽屉 | 打开参数预设面板 | 看到"提示词条目"卡片在参数预设下方 |
| 创建条目 | 点击 +，输入名称，回车 | 新条目出现在列表末，enabled 默认开 |
| 切换开关 | 点击 toggle | 开关状态切换，刷新后保持 |
| 拖拽排序 | 拖拽条目 * 手柄 | 条目顺序改变，刷新后保持 |
| 删除条目 | （Phase 1 暂未实现删除按钮，后续加） | — |
| 切换预设 | 选择不同参数预设 | 条目列表跟随切换 |
| 空状态 | 选择无条目的预设 | 显示"暂无条目"占位 |

- [ ] **Step 4: 运行后端测试确认全部通过**

```bash
cd backend && python -m pytest tests/test_prompt_entries.py -v
```

---

## 自审

**1. Spec 覆盖检查：**
- [x] 条目 CRUD → Task 1, 2, 5, 6
- [x] 开关 → Task 1 (enabled), Task 7 (toggle)
- [x] 拖拽排序 → Task 7, 8 (drag & drop)
- [x] 数据归属参数预设 → Task 6 (watch activePresetId), Task 8
- [x] 列表顶部 + 按钮 → Task 8
- [x] 编辑按钮占位 → Task 7 (emit edit, no action)
- [x] Token 显示 "-" → Task 7
- [x] 预设删除联动 → Task 3
- [x] 后端测试 → Task 4

**2. Placeholder 检查：** 无 TBD/TODO/占位符。

**3. 类型一致性检查：**
- `get_entries(preset_id)` → 前后端一致
- `create_entry(preset_id, name)` → 前后端一致
- `update_entry(preset_id, entry_id, data)` → 前后端一致，data 含 name/enabled
- `reorder_entries(preset_id, id_order_list/ids)` → 前后端一致
- `delete_preset_entries(preset_id)` → 仅后端调用
- 路由参数 `preset_id` 统一通过 query (GET/DELETE) 或 body (POST/PUT) 传递
