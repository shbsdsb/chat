# 参数预设 — 设计规格

**日期**: 2026-07-23
**状态**: 待实现

---

## 背景

当前系统只有一套"连接预设"（`settings.json`），管理 API URL、API Key、Model。
`temperature` 和 `max_tokens` 虽然已存在于后端字段中，但前端 UI 未暴露；
`top_p` 后端未透传。用户需要独立的参数预设体系，与连接预设分开管理、自由组合。

## 目标

- 新增独立的"参数预设"体系，管理 `temperature`、`max_tokens`、`top_p`
- 参数预设与连接预设互不依赖，可独立切换
- 工具栏新增"预设"按钮，与"API设置"平级

---

## 数据模型

### 新建 `user_data/param_presets.json`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "默认",
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0,
    "is_default": true,
    "created_at": "2026-07-23T00:00:00+00:00",
    "updated_at": "2026-07-23T00:00:00+00:00"
  }
]
```

- `id` — UUID 字符串
- `name` — 预设名称
- `temperature` — 0~2，默认 0.7
- `max_tokens` — 正整数，默认 4096
- `top_p` — 0~1，默认 1.0
- `is_default` — 是否默认预设，首次启动时自动创建一个，不可删除
- `created_at` / `updated_at` — ISO 时间戳

### 与连接预设的关系

```
连接预设 (settings.json)          参数预设 (param_presets.json)
┌──────────────────────┐         ┌──────────────────────────┐
│ api_url              │         │ temperature              │
│ api_key              │  独立   │ max_tokens               │
│ model                │  切换   │ top_p                    │
│ response_format      │         │                          │
└──────────────────────┘         └──────────────────────────┘
         ↓                                ↓
         └────────── 合并 → 发送消息 ──────┘
```

发送消息时，前端从两个 store 分别取当前选中值，直接传值给后端。

---

## API 设计

### 新增端点 `backend/app/routes/param_presets.py`

注册蓝图：`/api/param-presets`

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/param-presets` | 返回所有参数预设列表 |
| `POST` | `/param-presets` | 创建参数预设 |
| `PUT` | `/param-presets/<id>` | 更新参数预设 |
| `DELETE` | `/param-presets/<id>` | 删除参数预设（is_default 不可删） |
| `PUT` | `/param-presets/<id>/default` | 设为默认 |

**POST/PUT 请求体**：
```json
{
  "name": "创意模式",
  "temperature": 0.9,
  "max_tokens": 4096,
  "top_p": 0.95
}
```
所有字段必填（`name` 非空，`temperature` 0~2，`max_tokens` >0，`top_p` 0~1）。

**响应格式**：统一 `{code, message, data}`，code=0 成功。

### 已有代码改动

**`backend/app/services/ai.py`**：
- `stream_chat()` 签名增加 `top_p=None` 参数
- 在 payload 中补充 `top_p` 透传

**`backend/app/routes/conversations.py`**：
- `_stream_and_save()` 不再从连接预设读取 `temperature`/`max_tokens`
- 改为从请求体接收 `temperature`、`max_tokens`、`top_p`（由前端直接传值）
- SSE 流式端点接受新增的三个请求体字段

**`backend/app/routes/__init__.py`**：
- import 新的 `param_presets.py` 以触发 `@api_bp.route()` 装饰器注册

---

## 前端设计

### 新建 `frontend/src/stores/paramPresets.js`

```
State:
  presets: []           // 所有参数预设列表
  activePresetId: null  // 当前选中预设 ID
  loading: false

Getters:
  activePreset           // 当前选中预设的完整对象
  temperature            // 当前选中预设的 temperature
  maxTokens              // 当前选中预设的 max_tokens
  topP                   // 当前选中预设的 top_p

Actions:
  loadPresets()          // GET /param-presets，自动选中 default
  selectPreset(id)       // 切换 activePresetId
  createPreset(name)     // POST，用当前输入值创建
  savePreset()           // PUT，更新当前选中预设
  deletePreset(id)       // DELETE，自动切换到下一个
```

### 新建 `frontend/src/api/paramPresets.js`

封装 HTTP 方法：`list()` / `create(data)` / `update(id, data)` / `remove(id)` / `setDefault(id)`

### UI 改动

**`App.vue` — 工具栏**：

在 `<nav class="top-nav">` 中，"API设置"按钮前新增：
```html
<button class="top-btn" @click="showParamPresets = !showParamPresets">预设</button>
```
点击后打开 SettingsDrawer 内嵌参数预设面板。

**新建 `frontend/src/components/ParamPresetSelector.vue`**：

在 SettingsDrawer 内使用，包含：
- 预设下拉框（复用 PresetSelector 模式）
- `+` 新建按钮、`−` 删除按钮
- Temperature 输入框（type="number"，step=0.1，min=0，max=2）
- Max Tokens 输入框（type="number"，step=1，min=1）
- Top P 输入框（type="number"，step=0.01，min=0，max=1）
- 保存按钮

**`App.vue` 模板变更**：

新增第二个 SettingsDrawer 实例（复用组件）：
```html
<SettingsDrawer :visible="showParamPresets" @close="showParamPresets = false">
  <template #title>预设</template>
  <ParamPresetSelector @saved="showParamPresets = false" />
</SettingsDrawer>
```

### 发送消息改动

**`frontend/src/stores/chat.js`** — 发送消息方法中：

```js
import { useParamPresetsStore } from "@/stores/paramPresets";

// 发消息时附加参数
const paramStore = useParamPresetsStore();
const requestBody = {
  conversation_id: convId,
  message: content,
  temperature: paramStore.temperature,
  max_tokens: paramStore.maxTokens,
  top_p: paramStore.topP,
};
```

## 文件清单

| 操作 | 文件 |
|------|------|
| **新建** | `backend/app/routes/param_presets.py` |
| **新建** | `backend/app/storage/param_presets.py`（或扩展 storage.py） |
| **修改** | `backend/app/routes/__init__.py` |
| **修改** | `backend/app/services/ai.py` |
| **修改** | `backend/app/routes/conversations.py` |
| **新建** | `frontend/src/api/paramPresets.js` |
| **新建** | `frontend/src/stores/paramPresets.js` |
| **新建** | `frontend/src/components/ParamPresetSelector.vue` |
| **修改** | `frontend/src/App.vue` |
| **修改** | `frontend/src/stores/chat.js` |
| **新建** | `backend/tests/test_param_presets.py` |

---

## 边界与约束

- 默认预设（`is_default=true`）不可删除，始终至少保留一个
- 首次启动时若 `param_presets.json` 不存在或为空，自动创建名为"默认"的预设
- 参数预设名称不必全局唯一（允许同名）
- Temperature 范围 0~2，Top P 范围 0~1，Max Tokens >0
