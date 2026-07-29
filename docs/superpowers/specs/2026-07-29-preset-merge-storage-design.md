# 参数预设与提示词条目合并存储 — 设计规格

> 日期：2026-07-29 | 状态：草稿 | 依赖：Phase 1/2 提示词条目系统

## 概述

将参数预设（param_presets）和提示词条目（prompt_entries）从两个独立存储合并为单一 JSON 文件，同时调整前端交互：移除 ParamPresetSelector 卡片内的保存/删除按钮，改为在预设下拉菜单旁放置保存按钮，删除和新建按钮保留。

## 动机

- 当前 `chat_history` 位置持久化需要额外 API（`/chat-history-order`），且与条目分属两个文件，增加了不一致风险
- 用户修改参数 + 条目后需要分别保存，操作繁琐
- `提示词条目` 使用 JSON 对象（键值对）天然保持插入顺序，chat_history 作为键自然持久化

---

## 1. 数据模型

### 文件位置

```
user_data/presets/<preset_id>.json
```

替代旧的：
- `user_data/param_presets.json`（列表）
- `user_data/prompt_entries/<preset_id>.json`（列表）

### 预设列表索引

```
user_data/presets/_index.json
```

```json
[
  {"id": "36fc3fe4-...", "name": "默认", "is_default": true},
  {"id": "abc123-...", "name": "我的预设", "is_default": false}
]
```

轻量索引，只存 id/name/is_default，方便列表查询。

### 预设文件格式

```json
{
  "name": "我的预设",
  "is_default": false,
  "created_at": "2026-07-29T00:00:00+00:00",
  "updated_at": "2026-07-29T00:00:00+00:00",
  "params": {
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0
  },
  "entries": {
    "abc-123": {
      "name": "系统设定",
      "role": "system",
      "content": "你是助手",
      "enabled": true
    },
    "__chat_history__": "chat_history",
    "def-456": {
      "name": "尾部",
      "role": "assistant",
      "content": "喵",
      "enabled": true
    }
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 预设显示名称（中英文均可） |
| `is_default` | bool | 是否默认预设 |
| `created_at` | string | 创建时间 ISO 格式 |
| `updated_at` | string | 更新时间 ISO 格式 |
| `params` | object | temperature / max_tokens / top_p |
| `params.temperature` | float | 0~2 |
| `params.max_tokens` | int | >0 |
| `params.top_p` | float | 0~1 |
| `entries` | object | 键值对，插入顺序即排序 |
| `entries.<id>` | object | 普通条目：{name, role, content, enabled} |
| `entries.__chat_history__` | string `"chat_history"` | 特殊占位符，值为固定字符串 |

### 条目排序

JSON 对象在 Python 3.7+ / 现代 JS 中保持键的插入顺序。条目列表按 `entries` 对象中键的出现顺序排列。`__chat_history__` 出现在哪个键之间，它就排在哪个位置。键名为英文字符串（变量名），值内容允许中文。

---

## 2. 后端设计

### 存储层 `backend/app/storage/presets.py`（新建，替代 param_presets + prompt_entries）

```
presets/
├── __init__.py           # 导出
├── presets.py            # CRUD + 索引管理
└── （删除 param_presets.py 和 prompt_entries.py）
```

#### 函数清单

| 函数 | 说明 |
|---|---|
| `_get_file_path(preset_id)` | 返回 `user_data/presets/<id>.json` |
| `_read_index()` | 读 `_index.json` |
| `_write_index(data)` | 写 `_index.json` |
| `list_presets()` | 从索引返回列表 |
| `get_preset(preset_id)` | 读完整预设文件 |
| `create_preset(data)` | 创建新预设文件 + 更新索引 |
| `update_preset(preset_id, data)` | 写整个预设文件（覆盖） |
| `delete_preset(preset_id)` | 删文件 + 更新索引 |
| `get_default_preset()` | 返回 is_default=true 的预设 |
| `set_default_preset(preset_id)` | 更新索引中的 is_default |
| `get_entries(preset_id)` | 从 `提示词条目` 对象中提取条目数组，保持键顺序，分配 order 字段 |

### API 路由 `backend/app/routes/presets.py`（新建）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/presets` | 列出所有预设（从索引） |
| GET | `/api/presets/<id>` | 获取单个预设完整数据 |
| POST | `/api/presets` | 创建预设 `{name, temperature, max_tokens, top_p}` |
| PUT | `/api/presets/<id>` | **保存整个预设**（参数 + 条目） |
| DELETE | `/api/presets/<id>` | 删除预设 |
| PUT | `/api/presets/<id>/default` | 设为默认 |

### 入口改动的路由

- `backend/app/routes/prompt_entries.py` — **删除整个文件**
- `backend/app/routes/param_presets.py` — **删除整个文件**
- `backend/app/__init__.py` — 修改 import

### 迁移逻辑

首次访问时自动从旧格式迁移：
1. 读 `param_presets.json` → 创建 `presets/_index.json`
2. 读 `prompt_entries/<id>.json` → 合并入 `presets/<id>.json`
3. 迁移完成后保留旧文件（后续手动删除）

或者直接提供迁移脚本 `backend/migrate_presets.py`。

---

## 3. 前端设计

### ParamPresetSelector 改动

**移除：** 卡片内的"保存"按钮和"删除"按钮

**保留：** `<select>` 下拉 + "+" 新建按钮

**新增：** 下拉选择器旁边加保存按钮 + 删除按钮（小图标）

布局变为：
```
[参数预设 ▾]  [+ 新建]  [保存]  [删除]
```

保存按钮调用 `store.savePreset()`，将当前参数 + 所有条目一次性 PUT 到后端。

### PromptEntryCard 改动

- 条目增删改不再立即调 API
- 只修改本地 `store.entries`（新 store：`presetsStore`）
- 等用户点击顶部"保存"按钮时一起提交

### 新 Store `frontend/src/stores/presets.js`

合并当前的 `paramPresets` + `promptEntries` store：
- `state.presets` — 预设列表
- `state.activePresetId`
- `state.entries` — 当前预设的条目（对象格式，保持插入顺序）
- `actions.savePreset()` — 一次性 PUT 参数 + 条目

### 前端 API `frontend/src/api/presets.js`

```js
list()          → GET  /api/presets
get(id)         → GET  /api/presets/<id>
create(data)    → POST /api/presets
update(id, data)→ PUT  /api/presets/<id>
remove(id)      → DELETE /api/presets/<id>
setDefault(id)  → PUT  /api/presets/<id>/default
```

---

## 4. 兼容性

- 参数预设 API (`/api/param-presets`) 和提示词条目 API (`/api/prompt-entries`) 废除
- 依赖这些 API 的旧前端需要同步更新
- chat.js 中的 `useParamPresetsStore` → `usePresetsStore`
- chat.js 中的 `usePromptEntriesStore` → `usePresetsStore`

---

## 5. 实现步骤概览

1. 新建 `backend/app/storage/presets.py`
2. 新建 `backend/app/routes/presets.py`
3. 修改 `backend/app/__init__.py`（注册新路由，移除旧 import）
4. 删除旧路由文件：`prompt_entries.py`、`param_presets.py`
5. 新建 `frontend/src/api/presets.js`
6. 新建 `frontend/src/stores/presets.js`
7. 改造 `ParamPresetSelector.vue`
8. 改造 `PromptEntryCard.vue` / `PromptEntryItem.vue` / `PromptEntryModal.vue`
9. 改造 `chat.js`（用 presetsStore 替代两个旧 store）
10. 改造 `SettingsView.vue`（如有引用）
11. 数据迁移 + 测试
12. 构建验证

---

## 参考

- 当前 `param_presets.py` + `prompt_entries.py` 存储层
- 当前 `ParamPresetSelector.vue` + `PromptEntryCard.vue` 组件
- `docs/superpowers/specs/2026-07-28-prompt-entries-design.md`
- `docs/superpowers/specs/2026-07-29-prompt-entries-compose-design.md`
