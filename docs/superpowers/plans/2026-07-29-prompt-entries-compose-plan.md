# Prompt Entries 组合逻辑 — 实现计划

> **For agentic workers:** 使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 按任务逐个实现。步骤使用 checkbox (`- [ ]`) 语法追踪。

**目标：** 实现提示词条目组合逻辑，让用户通过 `__chat_history__` 占位符控制提示词条目与对话历史的排列顺序，前端组装完整 messages 后发给 AI。

**架构：** 后端 `get_entries()` 动态追加 `__chat_history__` 占位符；前端 `useMessageAssembler` 按 order 排序、过滤、同 role 合并、替换占位符后产出 messages；后端 `/chat` 和 `/regenerate` 接受可选 `messages` 覆盖字段。

**技术栈：** Python/Flask（后端）、Vue 3 Composition API（前端）、Pinia（状态管理）

## 全局约束

- `__chat_history__` id 为硬编码常量 `"__chat_history__"`
- `__chat_history__` 不存入 JSON 文件，由 `get_entries()` 动态追加
- `__chat_history__` 在前端不可删除、不可禁用、不可编辑
- role=null 的条目跳过不发送（开发测试条目）
- chat_history 是硬边界，不跨边界合并
- 前端 reorder 时过滤掉 `__chat_history__` 再发后端
- 遵循现有代码风格（`ok()`/`fail()` 响应、Pinia options API、CSS 变量）

---

## 文件结构

| 文件 | 操作 | 职责 |
|---|---|---|
| `backend/app/storage/prompt_entries.py` | 修改 | `get_entries()` 追加 `__chat_history__` |
| `backend/app/routes/conversations.py` | 修改 | `/chat` 和 `/regenerate` 接受可选 `messages` 覆盖 |
| `backend/tests/test_prompt_entries.py` | 修改 | 新增 `__chat_history__` 相关测试 |
| `frontend/src/composables/useMessageAssembler.js` | **新建** | 消息组装核心逻辑 |
| `frontend/src/components/PromptEntryItem.vue` | 修改 | 适配 `__chat_history__` 表现 |
| `frontend/src/components/PromptEntryCard.vue` | 修改 | reorder 过滤 `__chat_history__` |
| `frontend/src/stores/chat.js` | 修改 | `sendMessage()` / `replayMessage()` 集成组装器 |

---

### Task 1: 后端 — get_entries() 追加 __chat_history__

**文件：**
- 修改：`backend/app/storage/prompt_entries.py:16-24`

**接口：**
- 产出：`get_entries(preset_id)` 返回值末尾自动追加 `__chat_history__` 条目

- [ ] **Step 1: 修改 get_entries()**

将 `get_entries()` 函数末尾追加 `__chat_history__`：

```python
def get_entries(preset_id):
    """返回指定预设的所有提示词条目，按 order 排序。文件不存在返回 []。末尾自动追加 chat_history 占位符。"""
    _ensure_dir()
    filepath = _get_file_path(preset_id)
    if not os.path.exists(filepath):
        entries = []
    else:
        entries = _read_json(filepath)
        entries.sort(key=lambda e: e.get("order", 0))

    # 自动追加 chat_history 占位符（不存文件，动态生成）
    chat_history = {
        "id": "__chat_history__",
        "name": "对话历史",
        "role": "system",
        "content": "",
        "enabled": True,
        "order": len(entries),
    }
    return entries + [chat_history]
```

- [ ] **Step 2: 运行现有测试验证兼容性**

```bash
cd backend && python -m pytest tests/test_prompt_entries.py -v
```

预期：`test_list_empty` 现在会返回 `[__chat_history__]` 而非 `[]`，所以该测试需失败。其他测试可能也因为返回多了一个条目而受影响。

- [ ] **Step 3: 更新受影响的测试**

`test_list_empty` 和 `test_list_ordered` 的断言需调整，过滤掉 `__chat_history__`：

修改 `backend/tests/test_prompt_entries.py`：

**`test_list_empty` (L39-46)** — 修改断言，过滤掉占位符：

```python
def test_list_empty(self, test_app):
    """空列表返回仅含 chat_history 占位符。"""
    preset_id = _create_preset(test_app)
    resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 0
    entries = data["data"]
    # 过滤掉 __chat_history__，仅验证真实条目
    real_entries = [e for e in entries if e["id"] != "__chat_history__"]
    assert real_entries == []
    # 验证占位符存在
    chat = next((e for e in entries if e["id"] == "__chat_history__"), None)
    assert chat is not None
    assert chat["name"] == "对话历史"
    assert chat["enabled"] is True
```

**`test_list_ordered` (L85-96)** — 过滤后再验证顺序：

```python
def test_list_ordered(self, test_app):
    """列表按 order 排序返回（chat_history 在末尾）。"""
    preset_id = _create_preset(test_app)
    test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "B"})
    test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "A"})
    test_app.post("/api/prompt-entries", json={"preset_id": preset_id, "name": "C"})

    resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
    entries = resp.get_json()["data"]
    # 最后一个是 chat_history
    assert entries[-1]["id"] == "__chat_history__"
    real_entries = entries[:-1]
    names = [e["name"] for e in real_entries]
    assert names == ["B", "A", "C"]
```

**`test_reorder` (L141-160)** — 断言末尾有 chat_history：

```python
def test_reorder(self, test_app):
    """批量排序（末尾有 chat_history）。"""
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

    # 验证顺序（末尾有 chat_history）
    resp = test_app.get(f"/api/prompt-entries?preset_id={preset_id}")
    entries = resp.get_json()["data"]
    assert entries[-1]["id"] == "__chat_history__"
    real_ids = [e["id"] for e in entries[:-1]]
    assert real_ids == reversed_ids
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_prompt_entries.py -v
```

预期：全部 PASS（含修改后的测试）

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/prompt_entries.py backend/tests/test_prompt_entries.py
git commit -m "feat: get_entries() 追加 __chat_history__ 占位符"
```

---

### Task 2: 后端 — /chat 和 /regenerate 接受可选 messages 覆盖

**文件：**
- 修改：`backend/app/routes/conversations.py:145-193`（chat 端点）
- 修改：`backend/app/routes/conversations.py:220-254`（regenerate 端点）

**接口：**
- 消费：请求体新增可选字段 `messages: [{role, content}]`
- 产出：当 `messages` 存在时，跳过 `get_messages_for_chat()`，直接使用传入的 messages

- [ ] **Step 1: 修改 chat 端点**

在 `chat()` 函数中，第 180 行的 `messages = get_messages_for_chat(conv_id)` 替换为：

```python
@api_bp.route("/conversations/<conv_id>/chat", methods=["POST"])
def chat(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = get_default_setting()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return fail(400, "消息内容不能为空", request)

    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    top_p = body.get("top_p")

    now = datetime.now(timezone.utc).isoformat()

    user_msg_id = str(uuid.uuid4())
    add_message({
        "id": user_msg_id,
        "conversation_id": conv_id,
        "role": "user",
        "content": content,
        "reasoning_content": "",
        "created_at": now,
    })

    update_conversation(conv_id, {"updated_at": now})

    # 优先使用前端组装的 messages，否则从存储读取
    assembled = body.get("messages")
    if assembled and isinstance(assembled, list) and len(assembled) > 0:
        messages = assembled
    else:
        messages = get_messages_for_chat(conv_id)

    cancel_event = sse_manager.register(conv_id)

    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event,
                                             temperature=temperature, max_tokens=max_tokens, top_p=top_p,
                                             request_body=body, user_msg_id=user_msg_id)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: 修改 regenerate 端点**

在 `regenerate()` 函数中，第 241 行同样处理：

```python
@api_bp.route("/conversations/<conv_id>/regenerate", methods=["POST"])
def regenerate(conv_id):
    row = _get_conv_or_404(conv_id)
    if not row:
        return fail(404, "会话不存在", request)

    settings = get_default_setting()
    if not settings:
        return fail(400, "请先在设置中配置 API", request)

    last_assistant_id = get_last_assistant_message_id(conv_id)
    if not last_assistant_id:
        return fail(400, "没有可重新生成的 AI 回复", request)

    body = request.get_json(silent=True) or {}
    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    top_p = body.get("top_p")

    delete_message(last_assistant_id, conv_id)

    # 优先使用前端组装的 messages，否则从存储读取
    assembled = body.get("messages")
    if assembled and isinstance(assembled, list) and len(assembled) > 0:
        messages = assembled
    else:
        messages = get_messages_for_chat(conv_id)

    cancel_event = sse_manager.register(conv_id)

    return Response(
        stream_with_context(_stream_and_save(settings, messages, conv_id, cancel_event,
                                             temperature=temperature, max_tokens=max_tokens, top_p=top_p,
                                             request_body=body)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 3: 运行后端测试确认兼容**

```bash
cd backend && python -m pytest -v
```

预期：全部 PASS（chat 端点有相关测试吗？检查 conversations 相关测试）

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/conversations.py
git commit -m "feat: /chat 和 /regenerate 接受可选 messages 覆盖字段"
```

---

### Task 3: 前端 — 新建 useMessageAssembler.js

**文件：**
- 创建：`frontend/src/composables/useMessageAssembler.js`

**接口：**
- 产出：`function assembleMessages(entries, conversationMessages) → messages[]`
  - 参数 `entries`: prompt entries 数组（含 `__chat_history__`），每个条目 `{id, role, content, enabled, order}`
  - 参数 `conversationMessages`: 对话历史消息数组，每个消息 `{role, content}`
  - 返回：组装后的 messages 数组 `[{role, content}]`

- [ ] **Step 1: 创建 useMessageAssembler.js**

```javascript
// frontend/src/composables/useMessageAssembler.js

/**
 * 组装提示词条目和对话历史为完整 messages 数组。
 *
 * 规则：
 * 1. entries 按 order 排序
 * 2. 过滤 enabled=false 和 role=null 的条目
 * 3. 遍历 → 相邻同 role 合并（content 用 \n\n 分隔）
 * 4. 遇到 __chat_history__ → 展开为 conversationMessages
 * 5. __chat_history__ 是硬边界，不跨边界合并
 *
 * @param {Array} entries - 提示词条目（含 __chat_history__）
 * @param {Array} conversationMessages - 对话历史 [{role, content}]
 * @returns {Array} 组装后的 messages [{role, content}]
 */
export function assembleMessages(entries, conversationMessages) {
  if (!entries || entries.length === 0) {
    return conversationMessages ? [...conversationMessages] : [];
  }

  // 按 order 排序
  const sorted = [...entries].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  const result = [];

  let pendingRole = null;
  let pendingContents = [];

  /**
   * 刷新缓冲：将当前积累的同 role 内容合并为一条 message 写入 result
   */
  function flushPending() {
    if (pendingContents.length > 0) {
      result.push({
        role: pendingRole,
        content: pendingContents.join("\n\n"),
      });
      pendingRole = null;
      pendingContents = [];
    }
  }

  let chatHistoryInserted = false;

  for (const entry of sorted) {
    // --- chat_history 占位符 ---
    if (entry.id === "__chat_history__") {
      if (chatHistoryInserted) continue; // 防御：重复出现跳过
      chatHistoryInserted = true;

      flushPending(); // 先刷新边界前的缓冲区

      // 展开对话历史（保持原有 role，不合并）
      if (conversationMessages && conversationMessages.length > 0) {
        for (const msg of conversationMessages) {
          result.push({ role: msg.role, content: msg.content });
        }
      }
      continue;
    }

    // --- 跳过条件 ---
    if (entry.enabled === false) continue;
    if (entry.role === null || entry.role === undefined) continue;

    // --- 同 role 合并 ---
    if (entry.role === pendingRole) {
      pendingContents.push(entry.content || "");
    } else {
      flushPending();
      pendingRole = entry.role;
      pendingContents = [entry.content || ""];
    }
  }

  // 处理 chat_history 之后的缓冲区
  flushPending();

  return result;
}

/**
 * Vue composable 入口（便于在组件中使用）。
 * 直接返回 assembleMessages 函数引用。
 */
export function useMessageAssembler() {
  return { assembleMessages };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/composables/useMessageAssembler.js
git commit -m "feat: 新增 useMessageAssembler 消息组装器"
```

---

### Task 4: 前端 — PromptEntryItem.vue 适配 chat_history

**文件：**
- 修改：`frontend/src/components/PromptEntryItem.vue:1-39`

**接口：**
- 消费：`entry.id === "__chat_history__"` 时隐藏 Toggle 和编辑按钮
- 产出：视觉上不可编辑、不可禁用，但保留拖拽手柄

- [ ] **Step 1: 修改模板和脚本**

```vue
<template>
  <div
    class="pe-item"
    :class="{
      'pe-item--dragging': dragging,
      'pe-item--chat-history': entry.id === '__chat_history__',
    }"
  >
    <span class="pe-item__handle" title="拖拽排序" @mousedown.prevent="$emit('drag-start', $event)">
      <svg width="18" height="18" viewBox="0 0 100 100">
        <g stroke="currentColor" stroke-width="14" stroke-linecap="round" stroke-linejoin="round">
          <line x1="50" y1="16" x2="50" y2="84"/>
          <line x1="20" y1="32" x2="80" y2="68"/>
          <line x1="80" y1="32" x2="20" y2="68"/>
        </g>
      </svg>
    </span>
    <span class="pe-item__name">{{ entry.name }}</span>
    <span class="pe-item__token">{{ entry.id === '__chat_history__' ? '' : '-' }}</span>
    <button
      v-if="entry.id !== '__chat_history__'"
      class="pe-item__edit"
      title="编辑"
      @click="$emit('edit', entry)"
    >
      <Pencil :size="14" />
    </button>
    <div
      v-if="entry.id !== '__chat_history__'"
      class="pe-item__toggle toggle-switch"
      :class="{ active: entry.enabled }"
      @click="$emit('toggle', entry)"
    >
      <div class="toggle-switch__slider"></div>
    </div>
  </div>
</template>

<script setup>
import { Pencil } from "lucide-vue-next";

defineProps({
  entry: { type: Object, required: true },
  dragging: { type: Boolean, default: false },
});

defineEmits(["toggle", "edit", "drag-start"]);
</script>
```

在 `<style scoped>` 末尾新增 chat_history 样式：

```css
.pe-item--chat-history {
  color: var(--text-muted, #9ca3af);
  font-style: italic;
  opacity: 0.8;
}
.pe-item--chat-history .pe-item__name::before {
  content: "💬 ";
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PromptEntryItem.vue
git commit -m "feat: PromptEntryItem 适配 __chat_history__ 不可编辑/不可禁用"
```

---

### Task 5: 前端 — PromptEntryCard.vue reorder 过滤 chat_history

**文件：**
- 修改：`frontend/src/components/PromptEntryCard.vue:145-175`（onMouseUp 中的 reorder 调用）
- 修改：`frontend/src/components/PromptEntryCard.vue:229-231`（openEditModal 加防护）

**接口：**
- 消费：拖拽排序后 ID 列表含 `__chat_history__`
- 产出：发给后端的 ID 列表不含 `__chat_history__`

- [ ] **Step 1: 修改 onMouseUp 中的 reorder 调用**

在 `onMouseUp()` 函数中（第 170-174 行），修改 reorder 调用：

```javascript
if (di !== ti && di >= 0 && ti >= 0) {
    const data = [...store.entries];
    const [moved] = data.splice(di, 1);
    data.splice(ti, 0, moved);
    // 过滤掉 __chat_history__ 再发给后端
    const realIds = data
      .filter(e => e.id !== "__chat_history__")
      .map(e => e.id);
    store.reorderEntries(realIds);
}
```

- [ ] **Step 2: 修改 openEditModal 加兜底**

在 `openEditModal(entry)` 函数中（第 229-231 行），加防护：

```javascript
function openEditModal(entry) {
  // 防御：chat_history 不可编辑（编辑按钮已隐藏，兜底）
  if (entry.id === "__chat_history__") return;
  editingEntry.value = { ...entry };
  showEditModal.value = true;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PromptEntryCard.vue
git commit -m "feat: PromptEntryCard reorder 过滤 __chat_history__"
```

---

### Task 6: 前端 — chat.js 集成消息组装器

**文件：**
- 修改：`frontend/src/stores/chat.js:76-169`（sendMessage 方法）
- 修改：`frontend/src/stores/chat.js:198-259`（replayMessage 方法）

**接口：**
- 消费：`assembleMessages(entries, conversationMessages)` from `@/composables/useMessageAssembler`
- 消费：`usePromptEntriesStore().entries` from `@/stores/promptEntries`
- 产出：发送请求时 body 包含 `messages` 字段

- [ ] **Step 1: 修改 sendMessage()**

在 `sendMessage()` 中，构建 userMsg 后、发起 SSE 请求前，加入组装逻辑。完整修改后的 `sendMessage()` 方法：

```javascript
import { assembleMessages } from "@/composables/useMessageAssembler";
import { usePromptEntriesStore } from "@/stores/promptEntries";

// ... 在 actions 中 ...

async sendMessage(content) {
  if (this.isStreaming) return;

  const paramPresetsStore = useParamPresetsStore();
  const promptEntriesStore = usePromptEntriesStore();

  // 无活跃会话 → 视为新对话
  if (!this.activeConvId) {
    this.activeConvId = NEW_CONV;
  }

  // 首次发送 → 先创建后端对话记录
  if (this.activeConvId === NEW_CONV) {
    const title = content.slice(0, 20);
    const conv = await conversationsApi.create(title);
    conv.lastMessageAt = new Date().toISOString();
    this.activeConvId = conv.id;
    this.conversations.unshift(conv);
    sortByLastMessage(this.conversations);
  } else {
    const now = new Date().toISOString();
    const idx = this.conversations.findIndex((c) => c.id === this.activeConvId);
    if (idx !== -1) {
      this.conversations[idx].lastMessageAt = now;
    }
    sortByLastMessage(this.conversations);
  }

  const userMsg = {
    id: "temp-" + Date.now(),
    role: "user",
    content,
    created_at: new Date().toISOString(),
  };
  this.messages.push(userMsg);

  // ── 组装消息 ──
  // 对话历史 = 当前 this.messages（含刚加入的用户消息）
  const conversationMessages = this.messages.map(m => ({
    role: m.role,
    content: m.content,
  }));
  const assembledMessages = assembleMessages(
    promptEntriesStore.entries,
    conversationMessages
  );

  const assistantMsg = {
    id: "temp-" + (Date.now() + 1),
    role: "assistant",
    content: "",
    reasoning_content: "",
    created_at: new Date().toISOString(),
  };
  this.messages.push(assistantMsg);
  this.isStreaming = true;

  const es = sse(`/conversations/${this.activeConvId}/chat`, {
    method: "POST",
    body: JSON.stringify({
      content,
      messages: assembledMessages,
      temperature: paramPresetsStore.temperature,
      max_tokens: paramPresetsStore.maxTokens,
      top_p: paramPresetsStore.topP,
    }),
    // ... 其余 onMessage/onError/onDone 保持不变 ...
    onMessage: (chunk) => {
      if (chunk.stopped) {
        this.isStreaming = false;
        return;
      }
      const last = this.messages[this.messages.length - 1];
      if (last && last.role === "assistant") {
        applyChunk(last, chunk);
      }
      if (chunk.done) {
        this.isStreaming = false;
        if (chunk.user_msg_id) {
          for (let i = this.messages.length - 1; i >= 0; i--) {
            if (this.messages[i].role === "user") {
              this.messages[i].id = chunk.user_msg_id;
              break;
            }
          }
        }
        if (chunk.assistant_msg_id && last && last.role === "assistant") {
          const oldId = last.id;
          last.id = chunk.assistant_msg_id;
          if (this.aiVersions[oldId]) {
            this.aiVersions[chunk.assistant_msg_id] = this.aiVersions[oldId];
            delete this.aiVersions[oldId];
          }
        }
      }
    },
    onError: (err) => {
      this.isStreaming = false;
      console.error("SSE error:", err);
    },
    onDone: () => {
      this.isStreaming = false;
    },
  });

  this.abortController = es;
},
```

- [ ] **Step 2: 修改 replayMessage()**

在 `replayMessage()` 中，同样加入组装逻辑。找到 body 构建部分（约 221-226 行），修改为：

```javascript
async replayMessage(id) {
  const assistantMsg = this.messages.find((m) => m.id === id && m.role === "assistant");
  if (!assistantMsg || this.isStreaming) return;

  if (!this.aiVersions[id]) {
    this.aiVersions[id] = [{
      content: assistantMsg.content,
      reasoning_content: assistantMsg.reasoning_content,
    }];
    this.aiVersionIndex = 0;
  }

  assistantMsg.content = "";
  assistantMsg.reasoning_content = "";

  this.isStreaming = true;
  const newContent = { value: "" };
  const newReasoning = { value: "" };

  const paramPresetsStore = useParamPresetsStore();
  const promptEntriesStore = usePromptEntriesStore();

  // ── 组装消息 ──
  // 排除正在重新生成的 assistant 消息（content 已清空，不参与组装）
  const conversationMessages = this.messages
    .filter(m => m.id !== id)
    .map(m => ({ role: m.role, content: m.content }));
  const assembledMessages = assembleMessages(
    promptEntriesStore.entries,
    conversationMessages
  );

  const es = sse(`/conversations/${this.activeConvId}/regenerate`, {
    method: "POST",
    body: JSON.stringify({
      messages: assembledMessages,
      temperature: paramPresetsStore.temperature,
      max_tokens: paramPresetsStore.maxTokens,
      top_p: paramPresetsStore.topP,
    }),
    // ... 其余 onMessage/onError/onDone 保持不变 ...
```

- [ ] **Step 3: 在文件顶部新增 import**

在 `chat.js` 顶部（第 4 行后）添加：

```javascript
import { assembleMessages } from "@/composables/useMessageAssembler";
import { usePromptEntriesStore } from "@/stores/promptEntries";
```

`useParamPresetsStore` 已经 import 了（第 4 行），无需重复。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/chat.js
git commit -m "feat: chat.js 集成消息组装器（sendMessage + replayMessage）"
```

---

### Task 7: 构建验证

- [ ] **Step 1: 构建前端**

```bash
cd frontend && npm run build
```

预期：构建成功，无错误。

- [ ] **Step 2: 运行全量后端测试**

```bash
cd backend && python -m pytest -v
```

预期：全部 PASS。

- [ ] **Step 3: Commit（如有未提交变更）**

```bash
git status
git add -A
git commit -m "chore: 构建验证通过"
```
