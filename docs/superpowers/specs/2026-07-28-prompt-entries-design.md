# 提示词条目系统 — 设计规格

> 日期：2026-07-28 | 状态：草稿 | 阶段：Phase 1（条目列表管理）

## 概述

为 Chat 项目增加提示词条目（Prompt Entries）系统。用户可在每个参数预设下创建多个提示词条目，通过开关控制启用/禁用，通过拖拽调整排序。这是完整提示词系统的第一阶段，后续将在此基础上叠加条目内容编辑和组合（System Prompt 拼接）逻辑。

## 动机

- 当前项目完全没有 System Prompt 能力，`ai.py` 直接透传 messages，无 `role: "system"` 注入
- 参数预设只管理 temperature/top_p/max_tokens，缺少对提示词的管控
- 用户希望像 SillyTavern 一样按条目管理提示词片段，最终组合成 System Prompt

## Phase 1 范围

| 包含 | 不包含 |
|---|---|
| 条目 CRUD（名称 + 开关） | 条目内容编辑（Prompt 文本） |
| 拖拽排序 | 组合拼接逻辑 |
| 数据归属参数预设 | 心形收藏功能 |
| Toggle 启用/禁用 | Token 实际计算（显示 `-`） |

## 架构决策

选择**独立存储 + 独立 API**（方案 B），而非嵌入 param_presets：

- **理由**：后续组合系统需要独立扩展空间；与现有 `param_presets` / `css_presets` 架构模式一致
- **关联方式**：通过 `preset_id` 关联参数预设，切换预设时前端带参请求

---

## 后端设计

### 存储层 (`backend/app/storage/prompt_entries.py`)

存储路径：`user_data/prompt_entries/<preset_id>.json`

数据格式：

```json
[
  { "id": "uuid-1", "name": "🏃 双人成行",   "enabled": true,  "order": 0 },
  { "id": "uuid-2", "name": "📜 上帝小说模式", "enabled": false, "order": 1 },
  { "id": "uuid-3", "name": "前置说明点",     "enabled": true,  "order": 2 }
]
```

函数清单：

| 函数 | 说明 |
|---|---|
| `get_entries(preset_id) → list` | 读取文件，按 order 排序返回；文件不存在返回 `[]` |
| `create_entry(preset_id, name) → entry` | 生成 UUID，order = 当前最大 + 1，enabled 默认 true |
| `update_entry(preset_id, entry_id, data) → entry` | 更新 name / enabled 字段 |
| `delete_entry(preset_id, entry_id)` | 删除并重整剩余条目的 order（连续化） |
| `reorder_entries(preset_id, id_order_list)` | 按传入的 id 列表批量重写 order |
| `delete_preset_entries(preset_id)` | 删除整个预设的条目文件（预设删除时调用） |

线程安全：使用 `threading.Lock`（参考 `param_presets.py` 模式）。

### 路由层 (`backend/app/routes/prompt_entries.py`)

注册于 `api_bp` Blueprint，URL 前缀 `/api`。

| 方法 | 路径 | Body / Query | 返回 |
|---|---|---|---|
| `GET` | `/prompt-entries` | `?preset_id=` | `ok(entries)` |
| `POST` | `/prompt-entries` | `{preset_id, name}` | `ok(entry)` |
| `PUT` | `/prompt-entries/<id>` | `{preset_id, name?, enabled?}` | `ok(entry)` |
| `DELETE` | `/prompt-entries/<id>` | `?preset_id=` | `ok()` |
| `PUT` | `/prompt-entries/reorder` | `{preset_id, ids: [...]}` | `ok()` |

参数校验：
- `preset_id` 必填，需验证对应参数预设存在
- `name` 必填（创建时），非空字符串
- `ids` 必为数组，长度与当前条目数一致

错误响应统一使用 `fail(code, message)`。

### 与 param_presets 的联动

删除参数预设时，需同步清理对应提示词条目。在 `param_presets.py` 路由的删除逻辑中增加调用 `delete_preset_entries(preset_id)`。

### 注册到应用

在 `backend/app/__init__.py` 的 `create_app()` 中 `register_blueprint` 之前 import `prompt_entries` 路由，触发 `@api_bp.route()` 装饰器。

---

## 前端设计

### API 层 (`frontend/src/api/promptEntries.js`)

```js
getEntries(presetId)          // GET  /api/prompt-entries?preset_id=
createEntry(presetId, name)   // POST /api/prompt-entries
updateEntry(id, presetId, data)  // PUT  /api/prompt-entries/<id>
deleteEntry(id, presetId)     // DELETE /api/prompt-entries/<id>
reorderEntries(presetId, ids) // PUT  /api/prompt-entries/reorder
```

使用 `request.js` 封装，自动解包 `{code, message, data}`。

### Pinia Store (`frontend/src/stores/promptEntries.js`)

```js
// state
entries: []        // 当前预设的条目列表
loading: false

// getters
enabledEntries      // entries.filter(e => e.enabled) — 预留，组合系统使用

// actions
loadEntries(presetId)
createEntry(name)       // 自动使用 paramPresetsStore.activePresetId
updateEntry(id, data)   // data: { name?, enabled? }
deleteEntry(id)
reorderEntries(ids)
```

**与 paramPresets 联动**：在 `ParamPresetSelector` 切换预设的 watch 中，新增调用 `promptEntriesStore.loadEntries(newPresetId)`。也要在 `App.vue` 或 `SettingsView.vue` 初始化时加载。

### 组件结构

```
SettingsView.vue
├── PresetSelector           ← 已有
├── ParamPresetSelector      ← 已有
└── PromptEntryCard.vue      ← 新增
    └── PromptEntryItem.vue  ← 新增（×N，v-for entries）
```

### PromptEntryCard.vue

- 卡片容器，遵循 `UI_token.md` 约定的卡片样式
- 标题栏：**"提示词条目"** + `[+]` 按钮（创建新条目）
- 点击 `[+]` → 弹出轻量输入框（或 inline input），填写名称后回车创建
- 列表为空时显示占位提示："暂无条目，点击 + 创建"

### PromptEntryItem.vue

单行条目，布局（从左到右）：

```
[*]  名称文本（含 emoji）    -    ✏️   [Toggle]
```

- `*` — 拖拽手柄，`draggable="true"`，实现 dragstart/dragover/drop
- 名称 — 纯文本展示，未编辑状态
- `-` — Token 计数占位，灰色小字
- `✏️` — 编辑按钮，Phase 1 为占位入口，点击不触发任何操作（后续实现编辑页面）
- Toggle — 控制 `enabled` 状态，切换时调用 `updateEntry(id, {enabled})`

### 拖拽排序

使用原生 HTML5 Drag & Drop API（零依赖）：

1. `dragstart` — 在拖拽手柄 `*` 上触发，`event.dataTransfer` 存条目 id
2. `dragover` — 在条目行上触发，阻止默认行为以允许 drop，显示插入位置指示（border-top 高亮）
3. `drop` — 获取源和目标 index，重新排列本地 `entries` 数组，调用 `reorderEntries(presetId, ids)`
4. `dragend` — 清除所有视觉指示

### 样式

遵循 `UI_token.md` 约定，使用项目 CSS 变量（`--color-*`, `--radius-*`, `--spacing-*`）。暗色主题适配。

---

## 实现步骤概览

1. **后端 Storage** — `prompt_entries.py`（CRUD + reorder）
2. **后端 Routes** — `prompt_entries.py`（5 个端点）
3. **集成** — `__init__.py` 注册路由，param_presets 删除时联动
4. **前端 API** — `promptEntries.js`
5. **前端 Store** — `promptEntries.js`（Pinia）
6. **前端组件** — `PromptEntryCard.vue` + `PromptEntryItem.vue`（含拖拽）
7. **集成** — 放入 `SettingsView.vue`，与 `ParamPresetSelector` 联动
8. **测试** — 后端 pytest（CRUD + reorder + 预设删除联动）

---

## 参考

- SillyTavern 提示词系统（需求来源）
- 现有 `param_presets` / `css_presets` 存储 + 路由模式（架构参考）
- `UI_token.md`（样式约定）
