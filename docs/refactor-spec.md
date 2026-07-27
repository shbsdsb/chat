# 代码库重构规格文档

> 状态：设计已确认 | 日期：2026-07-23 | 方案：适度重构（方案B）

## 一、背景与目标

基于代码库臃肿审查报告，识别出 P0/P1/P2 共 10 项重构点。目标是在**不改变 API 契约、不破坏现有功能**的前提下，消除死代码、抽象重复模式、拆分臃肿文件，提升代码可维护性。

### 不可破坏的契约

| 层面 | 契约 |
|------|------|
| API | `{code, message, data}` 格式不变；所有路由端点签名不变 |
| 存储 | `user_data/` 下 JSON 文件格式不变 |
| 组件 | 所有 Vue 组件的 props/emits/slots 签名不变 |
| 测试 | 39 个 pytest 全部保持通过 |

### 总览

```
阶段  PR#  内容                                  预计净减代码  风险
──────────────────────────────────────────────────────────────────
P0    #1   死代码删除 + BaseDialog 提取           ~160 行      极低
P1    #2   useMarkdown拆分 + 常量提取 + Drawer    ~65 行重复   低
P2    #3   storage拆分 + stream_handler + CRUD    ~130 行重复  中低
          + http_client + chat.js优化
```

### 依赖关系

```
P0 ──────► P1 ──────► P2
(无依赖)   (P1-1 依赖 P0 的 BaseDialog 可选)  (依赖前面稳定结构)
```

- P0 是基础，`BaseDialog.vue` 可被后续阶段复用
- P1 三个子任务完全独立，可并行开发
- P2 依赖 P0/P1 稳定后的代码结构

---

## 二、阶段一：P0（PR #1）

### P0-1: 删除 `database.py` 死代码

**问题**：`backend/app/database.py`（76行）是旧 SQLite 模块，包含 `init_db`/`get_db`/`close_db`，`storage.py` 已完全替代，无任何代码 import 它。

**方案**：

```
删除：
  backend/app/database.py                    （-76 行）
  user_data/chat.db                          （0 字节空文件）
  backend/tests/user_data/chat.db            （32KB 遗留）

验证：
  grep -r "from.*database\|import.*database" backend/app/  # 确认零引用
  cd backend && python -m pytest                          # 39 tests 通过
```

**涉及文件**：`backend/app/database.py`（删除）、`user_data/chat.db`（删除）、`backend/tests/user_data/chat.db`（删除）

**向后兼容**：零风险 — 无 import、无引用、无 API 影响。

---

### P0-2: 提取 `BaseDialog.vue` 通用弹窗组件

**问题**：`ConversationItem.vue`、`PresetSelector.vue`、`AlertDialog.vue` 各自完整复制了弹窗的 template + style（~90 行 CSS 完全一致）。

**目标组件 API**：

```vue
<BaseDialog
  :visible="show"
  :title="'标题'"
  @close="show = false"
>
  <template #default> 弹窗内容 </template>
  <template #footer>  底部按钮区 </template>
</BaseDialog>
```

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | Boolean | 显示/隐藏 |
| `title` | String | 弹窗标题 |

| Emit | 说明 |
|------|------|
| `close` | 点击遮罩或关闭按钮时触发 |

| Slot | 说明 |
|------|------|
| `default` | 弹窗主体内容 |
| `footer` | 底部操作按钮区 |

**改造对比**：

| 文件 | 改造内容 | 删除量 |
|------|---------|--------|
| `ConversationItem.vue` | 用 `<BaseDialog>` 替换内置弹窗模板 | ~90行CSS + ~15行模板 |
| `PresetSelector.vue` | 用 `<BaseDialog>` 替换内置弹窗模板 | ~110行CSS + ~15行模板 |
| `AlertDialog.vue` | 用 `<BaseDialog>` 替换简化版 overlay | ~30行CSS |
| **新增** `BaseDialog.vue` | 通用弹窗组件（~90行） | — |
| **净减少** | | **~160 行** |

**涉及文件**：
- 新增：`frontend/src/components/BaseDialog.vue`
- 修改：`ConversationItem.vue`、`PresetSelector.vue`、`AlertDialog.vue`

**验证**：手动验证创建/重命名/删除会话弹窗、预设保存/删除弹窗、全局 Alert 弹窗样式与交互行为一致。

---

## 三、阶段二：P1（PR #2）

三个子任务完全独立，可并行开发。

### P1-1: `useMarkdown.js` 拆分为 4 模块

**问题**：`useMarkdown.js`（~411行）单一 composable 承载了 markdown-it 配置、highlight.js 集成、HTML 文档检测、分段算法、代码块范围计算等 6+ 个独立关注点。

**拆分方案**：

```
composables/markdown/
├── engine.js               # markdown-it 实例化、highlight.js 配置、DOMPurify
│   export: md, sanitize(html)
│
├── htmlDetector.js         # detectHtmlType, findEmbeddedHtmlDoc, extractHtmlFragments
│   export: { detectHtmlType, findEmbeddedHtmlDoc, extractHtmlFragments }
│
├── splitter.js             # splitParagraphs, splitMixed, 代码块范围计算
│   export: { splitParagraphs, splitMixed, computeCodeBlockRanges }
│
└── useMarkdown.js          # 仅 composable + watch，组合以上模块
    import { md, sanitize } from './engine'
    import { extractHtmlFragments } from './htmlDetector'
    import { splitMixed } from './splitter'
```

**涉及文件**：
- 新增：`composables/markdown/engine.js`、`htmlDetector.js`、`splitter.js`
- 修改：`composables/useMarkdown.js`（精简为组合入口）

**向后兼容**：`useMarkdown.js` 的 export（composable 返回值）完全不变，消费者零改动。

---

### P1-2: `HTTP_STATUS_MSG` 提取到 `api/constants.js`

**问题**：`api/request.js` 和 `api/sse.js` 完全复制了 15 行 HTTP 状态码映射表 + `_alert()` 懒加载函数。

**方案**：

```js
// api/constants.js（新文件）
export const HTTP_STATUS_MSG = {
  400: '请求参数有误', 401: 'API Key 无效或未设置',
  403: '无权访问', 404: '资源未找到',
  429: '请求过于频繁', 500: '服务器内部错误',
  502: '网关错误', 503: '服务暂不可用',
}

let _alertFn = null
export function getAlert() {
  if (!_alertFn) {
    const { useAlertStore } = require('@/stores/alert')
    _alertFn = useAlertStore()
  }
  return _alertFn
}
```

**涉及文件**：
- 新增：`frontend/src/api/constants.js`
- 修改：`api/request.js`、`api/sse.js`（各 -18 行，改为 import）

---

### P1-3: `useResizableDrawer.js` 抽取共享拖拽

**问题**：`ConversationsDrawer.vue` 和 `SettingsDrawer.vue` 的 `startResize` 逻辑几乎相同，仅方向相反（左 drawer `+delta`，右 drawer `-delta`）。

**方案**：

```js
// composables/useResizableDrawer.js（新文件）
export function useResizableDrawer(options = {}) {
  const { direction = 'left', minWidth = 280, maxWidth = 500, defaultWidth = 320 } = options
  const width = ref(defaultWidth)
  const isResizing = ref(false)

  const startResize = (e) => {
    isResizing.value = true
    const startX = e.clientX
    const startWidth = width.value
    const onMove = (e) => {
      const delta = direction === 'left' ? e.clientX - startX : startX - e.clientX
      width.value = Math.max(minWidth, Math.min(maxWidth, startWidth + delta))
    }
    const onUp = () => {
      isResizing.value = false
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }

  return { width, isResizing, startResize }
}
```

**使用**：

```js
// ConversationsDrawer.vue
const { width, isResizing, startResize } = useResizableDrawer({ direction: 'left' })

// SettingsDrawer.vue
const { width, isResizing, startResize } = useResizableDrawer({ direction: 'right' })
```

**CSS 复用**：`.drawer-panel`、`.drawer-resizer`、`.drawer-close` 公共样式提取到 `assets/drawer.css`。

**涉及文件**：
- 新增：`composables/useResizableDrawer.js`、`assets/drawer.css`
- 修改：`ConversationsDrawer.vue`、`SettingsDrawer.vue`（各 -25 行拖拽逻辑 + -30 行 CSS）

---

## 四、阶段三：P2（PR #3）

### P2-1: `storage.py` 按域拆分

**问题**：conversations、messages、settings 三个域的 CRUD 混在一个文件（274 行）。

**方案**：保持导出兼容，外部 import 路径不变。

```
backend/app/storage/
├── __init__.py           # 重新导出所有公开函数 + _read_json / _write_json
├── conversations.py      # list_conversations, get_conversation, create_conversation,
│                         #   update_conversation, delete_conversation
├── messages.py           # get_messages, add_message, update_message, delete_message
└── settings.py           # list_settings, get_setting, create_setting,
                          #   update_setting, delete_setting, get_default_setting
```

**兼容策略**：

```python
# storage/__init__.py
from .conversations import (
    list_conversations, get_conversation, create_conversation,
    update_conversation, delete_conversation,
)
from .messages import get_messages, add_message, update_message, delete_message
from .settings import (
    list_settings, get_setting, create_setting,
    update_setting, delete_setting, get_default_setting,
)

# 原有 import 不变：
# from app.storage import get_conversation  ← 仍然有效
```

**涉及文件**：
- 新增：`storage/__init__.py`、`storage/conversations.py`、`storage/messages.py`、`storage/settings.py`
- 删除：`storage.py`（原文件）
- 测试适配：`conftest.py` 的 monkeypatch 路径按需调整

---

### P2-2: `_stream_and_save` → `services/stream_handler.py`

**问题**：`routes/conversations.py` 中 `_stream_and_save` 在路由层直接操作消息持久化和 SSE 管理，违反分层原则。

**方案**：

```python
# services/stream_handler.py（新文件）
def stream_and_save(conv_id, messages, setting, sse_manager):
    """生成器：逐 token yield SSE chunk，完成后持久化消息"""
    full_content = ""
    reasoning_content = ""
    try:
        for chunk in stream_chat(messages, setting):
            if sse_manager.is_cancelled(conv_id):
                yield {"stopped": True}
                break
            # 累加 content/reasoning，yield chunk
        # 持久化
        add_message(conv_id, "user", user_content)
        add_message(conv_id, "assistant", full_content, reasoning=reasoning_content)
    finally:
        sse_manager.unregister(conv_id)
```

**路由层精简为**：

```python
# routes/conversations.py
@api_bp.route('/conversations/<conv_id>/chat', methods=['POST'])
def chat(conv_id):
    return Response(
        stream_with_context(stream_and_save(conv_id, messages, setting, sse_manager)),
        mimetype='text/event-stream'
    )
```

**涉及文件**：
- 新增：`services/stream_handler.py`
- 修改：`routes/conversations.py`（-40 行）

---

### P2-3: 路由 CRUD 公共函数提取

**问题**：`conversations.py` 和 `settings.py` 中每个路由重复 `not row → fail(404)` 守卫。

**方案**：提取轻量级辅助函数（不引入 mixin/装饰器）。

```python
# routes/_helpers.py（新文件）
def get_or_404(fetcher, id, name="资源"):
    """通用「取或404」守卫。返回 (row, error)"""
    row = fetcher(id)
    if not row:
        return None, fail(404, f"{name}不存在")
    return row, None
```

路由中使用：
```python
conv, err = get_or_404(get_conversation, conv_id, "会话")
if err: return err
```

**涉及文件**：
- 新增：`routes/_helpers.py`
- 修改：`routes/conversations.py`、`routes/settings.py`（各 -15 行）

---

### P2-4: `services/http_client.py` 统一 API 调用

**问题**：`settings.py` 和 `ai.py` 中重复的 `try: requests.xxx → except RequestException → fail(502)` 模式。

**方案**：

```python
# services/http_client.py（新文件）
import requests

def api_post(url, headers, json, timeout=30):
    """统一的 OpenAI-compatible POST，返回 (data, error)"""
    try:
        resp = requests.post(url, headers=headers, json=json, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)

def api_get(url, headers, timeout=10):
    """统一的 GET"""
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)
```

**涉及文件**：
- 新增：`services/http_client.py`
- 修改：`routes/settings.py`（`test_setting`、`fetch_models`）、`services/ai.py`（`stream_chat`）

---

### P2-5: `chat.js` store 瘦身

**排序去重**：`conversations.sort(...)` 比较器出现 3 次 → 提取 getter：

```js
// stores/chat.js
getters: {
  sortedConversations: (state) =>
    [...state.conversations].sort((a, b) =>
      new Date(b.lastMessageAt || b.createdAt) - new Date(a.lastMessageAt || a.createdAt)
    )
}
```

**SSE chunk 处理去重**：`sendMessage` 和 `replayMessage` 中 ~40 行重复：

```js
// stores/chat.js 内部辅助函数
function applyChunk(msg, chunk) {
  if (chunk.reasoning_delta) msg.reasoning = (msg.reasoning || '') + chunk.reasoning_delta
  if (chunk.delta) msg.content = (msg.content || '') + chunk.delta
  if (chunk.done || chunk.stopped) msg.streaming = false
}
```

**涉及文件**：`frontend/src/stores/chat.js`（-40 行重复）

---

## 五、向后兼容保证

| 层面 | 措施 |
|------|------|
| API | 所有路由端点 URL、方法、请求/响应格式不变 |
| 存储 | `user_data/` 下 JSON schema 不变，重构前后数据完全互通 |
| 前端组件 | 所有组件 props/emits/slots 签名不变，仅内部实现改变 |
| 导入路径 | `storage.py` → `storage/__init__.py` 重新导出，外部 import 无需改动 |
| 测试 | 39 个 pytest 在每阶段 PR 中全量运行，必须全部通过 |

---

## 六、测试策略

### 自动化测试

```bash
cd backend && python -m pytest    # 39 tests，每阶段 PR 必须全绿
```

`conftest.py` 使用 `tmp_path` 隔离数据，重构不产生副作用。

### 手动验证清单

| 阶段 | 验证项 |
|------|--------|
| P0 | 创建/重命名/删除会话弹窗、预设保存/删除弹窗、全局 Alert 弹窗样式一致 |
| P1 | Markdown 渲染（代码高亮、HTML 检测、流式渲染）正常；Drawer 拖拽行为不变 |
| P2 | 会话 CRUD、消息发送/流式/停止/重生成、设置 CRUD/连通性测试/模型列表均正常 |

### 回归测试

- P0 合入后运行一次完整手动回归
- P1 合入后运行一次完整手动回归
- P2 合入后运行一次完整手动回归 + `npm run electron:build` 构建验证

---

## 七、执行清单

### PR #1 — P0 阶段

- [ ] 删除 `backend/app/database.py`
- [ ] 删除 `user_data/chat.db` 和 `backend/tests/user_data/chat.db`
- [ ] `grep` 验证零引用
- [ ] 创建 `frontend/src/components/BaseDialog.vue`
- [ ] 改造 `ConversationItem.vue` 使用 `BaseDialog`
- [ ] 改造 `PresetSelector.vue` 使用 `BaseDialog`
- [ ] 改造 `AlertDialog.vue` 使用 `BaseDialog`
- [ ] `cd backend && python -m pytest` 通过
- [ ] 手动验证弹窗交互

### PR #2 — P1 阶段

- [ ] 创建 `composables/markdown/engine.js`
- [ ] 创建 `composables/markdown/htmlDetector.js`
- [ ] 创建 `composables/markdown/splitter.js`
- [ ] 精简 `composables/useMarkdown.js` 为组合入口
- [ ] 创建 `api/constants.js`，提取 `HTTP_STATUS_MSG` + `getAlert`
- [ ] 修改 `api/request.js` 和 `api/sse.js` 改为 import
- [ ] 创建 `composables/useResizableDrawer.js`
- [ ] 创建 `assets/drawer.css`
- [ ] 改造 `ConversationsDrawer.vue` 和 `SettingsDrawer.vue`
- [ ] `cd backend && python -m pytest` 通过
- [ ] 手动验证 Markdown 渲染和 Drawer 拖拽

### PR #3 — P2 阶段

- [ ] 创建 `backend/app/storage/__init__.py` + 3 域文件，删除原 `storage.py`
- [ ] 创建 `backend/app/services/stream_handler.py`
- [ ] 精简 `routes/conversations.py` 路由层
- [ ] 创建 `routes/_helpers.py`，改造 `conversations.py` 和 `settings.py`
- [ ] 创建 `services/http_client.py`，改造 `settings.py` 和 `ai.py`
- [ ] 优化 `stores/chat.js`（getter + `applyChunk` 辅助函数）
- [ ] `cd backend && python -m pytest` 全量通过
- [ ] 手动验证完整功能 + `npm run electron:build`

---

## 八、预估数据

| 指标 | 数值 |
|------|------|
| 总涉及文件 | ~25 个（新增/修改/删除） |
| 预计净减少代码 | ~350 行 |
| 预计新增文件 | 12 个 |
| 预计删除文件 | 4 个（含 2 个遗留 .db） |
| 每阶段 PR diff 规模 | P0 ~200 行、P1 ~250 行、P2 ~350 行 |
| 总工作量估算 | 2-3 天（含手动验证） |
