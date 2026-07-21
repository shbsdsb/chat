# AI 思考过程展示 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在聊天页面显示 AI 模型的 reasoning_content（思考过程），持久化到 DB 但不纳入历史上下文。

**Architecture:** 后端 `ai.py` 解析 DeepSeek 风格 SSE chunk 中的 `reasoning_content` 字段，`_stream_and_save` 通过 SSE 转发到前端并持久化到 `messages.reasoning_content` 列；前端 `MessageBubble` 渲染可折叠思考区块（默认展开）。

**Tech Stack:** Python/Flask + sqlite3（后端），Vue 3 + Pinia（前端），无新依赖。

## 全局约束

- 数据库兼容：已有 DB 需 ALTER TABLE 新增列（幂等 try/except）
- reasoning_content 默认空字符串，无思考的模型不触发新路径
- 构建 API 请求上下文时只用 role + content，不含 reasoning
- 消息编辑逻辑不改动（仅编辑用户消息）
- 样式保持现有简洁风格，思考区块用浅色标识

---

### Task 1: 数据库 — messages 表新增 reasoning_content 列

**文件:**
- 修改: `backend/app/database.py:35-76`（init_db 方法）
- 测试: `backend/tests/test_conversations.py`（已有测试覆盖，无需新增 — 仅需确认不破坏现有测试）

**接口:**
- 产出: `messages.reasoning_content TEXT NOT NULL DEFAULT ''` 列（被 Task 3 INSERT 使用）

- [ ] **Step 1: 修改 init_db 的 CREATE TABLE 和添加 ALTER TABLE 迁移**

在 `database.py` 的 `init_db()` 中：

**1a. 更新 CREATE TABLE：**

将 messages 建表语句从：
```sql
CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE
);
```

改为：
```sql
CREATE TABLE IF NOT EXISTS messages (
    id                TEXT PRIMARY KEY,
    conversation_id   TEXT NOT NULL,
    role              TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content           TEXT NOT NULL,
    reasoning_content TEXT NOT NULL DEFAULT '',
    created_at        TEXT NOT NULL,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE
);
```

**1b. 在 `conn.executescript(...)` 之后、`conn.commit()` 之前添加迁移：**

```python
    # 兼容旧数据库：新增 reasoning_content 列
    try:
        conn.execute(
            "ALTER TABLE messages ADD COLUMN reasoning_content TEXT NOT NULL DEFAULT ''"
        )
    except sqlite3.OperationalError:
        pass  # 列已存在（新数据库已在 CREATE TABLE 中包含）
```

完整修改后的 `init_db()` 核心部分：
```python
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL DEFAULT '新对话',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id                TEXT PRIMARY KEY,
            conversation_id   TEXT NOT NULL,
            role              TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content           TEXT NOT NULL,
            reasoning_content TEXT NOT NULL DEFAULT '',
            created_at        TEXT NOT NULL,
            FOREIGN KEY (conversation_id)
                REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conv
            ON messages(conversation_id, created_at);

        CREATE TABLE IF NOT EXISTS settings (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            api_url         TEXT NOT NULL,
            api_key         TEXT NOT NULL,
            model           TEXT NOT NULL DEFAULT 'gpt-4o',
            response_format TEXT NOT NULL DEFAULT '',
            temperature     REAL NOT NULL DEFAULT 0.7,
            max_tokens      INTEGER NOT NULL DEFAULT 4096,
            is_default      INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
    """)

    # 兼容旧数据库：新增 reasoning_content 列
    try:
        conn.execute(
            "ALTER TABLE messages ADD COLUMN reasoning_content TEXT NOT NULL DEFAULT ''"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
```

- [ ] **Step 2: 运行现有测试确认不破坏**

```bash
cd backend && python -m pytest --tb=short
```

预期：36 passed（测试用 tmp_path 创建新 DB，CREATE TABLE 已含新列，ALTER TABLE 被 skip）

- [ ] **Step 3: 提交**

```bash
git add backend/app/database.py
git commit -m "feat: messages 表新增 reasoning_content 列"
```

---

### Task 2: ai.py — 解析 reasoning_content

**文件:**
- 修改: `backend/app/services/ai.py:47-53`
- 测试: `backend/tests/test_ai.py`（新增一个测试）

**接口:**
- 消耗: （无，这是最底层）
- 产出: `stream_chat()` 新增产出类型 `{"reasoning_delta": str}`，保持原有 `{"delta": str}`, `{"done": True}`, `{"error": str}`, `{"stopped": True}`

- [ ] **Step 1: 添加 reasoning_content 解析的测试**

在 `backend/tests/test_ai.py` 末尾添加新的 mock 辅助函数和测试：

```python
def make_mock_response_with_reasoning(reasoning_chunks, content_chunks):
    resp = Mock()
    resp.raise_for_status = Mock()
    lines = []
    for chunk in reasoning_chunks:
        lines.append(
            b"data: " + json.dumps({
                "choices": [{"delta": {"reasoning_content": chunk, "content": ""}}]
            }).encode()
        )
    for chunk in content_chunks:
        lines.append(
            b"data: " + json.dumps({
                "choices": [{"delta": {"content": chunk}}]
            }).encode()
        )
    lines.append(b"data: [DONE]")
    resp.iter_lines.return_value = [b""] + lines
    return resp


class TestStreamChatReasoning:
    def test_yields_reasoning_delta(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response_with_reasoning(
                ["让我想想", "用户的问题是"],
                ["你好！"]
            )

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert {"reasoning_delta": "让我想想"} in results
        assert {"reasoning_delta": "用户的问题是"} in results
        assert {"delta": "你好！"} in results
        assert {"done": True} in results

    def test_no_reasoning_for_plain_models(self):
        """没有 reasoning_content 的模型不产生 reasoning_delta"""
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["hello"])

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        # 不应包含 reasoning_delta
        assert not any("reasoning_delta" in r for r in results)
        assert {"delta": "hello"} in results

    def test_reasoning_only_chunk(self):
        """只有 reasoning_content 没有 content 的 chunk"""
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response_with_reasoning(
                ["纯思考"],
                ["答案"]
            )

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert {"reasoning_delta": "纯思考"} in results
        assert {"delta": "答案"} in results
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_ai.py::TestStreamChatReasoning -v
```

预期：3 个新测试 FAIL（reasoning_delta 尚未实现）

- [ ] **Step 3: 修改 ai.py 解析 reasoning_content**

修改 `backend/app/services/ai.py` 第 47-53 行：

原代码：
```python
            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield {"delta": delta}
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
```

改为：
```python
            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"]
                reasoning = delta.get("reasoning_content", "")
                content = delta.get("content", "")
                if reasoning:
                    yield {"reasoning_delta": reasoning}
                if content:
                    yield {"delta": content}
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
```

- [ ] **Step 4: 运行全部测试确认通过**

```bash
cd backend && python -m pytest --tb=short
```

预期：39 passed（36 旧 + 3 新）

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/ai.py backend/tests/test_ai.py
git commit -m "feat: stream_chat 解析 reasoning_content 字段"
```

---

### Task 3: conversations.py — SSE 转发 + 存储 + 上下文构建

**文件:**
- 修改: `backend/app/routes/conversations.py`（`_stream_and_save`, `chat`, `regenerate`）

**接口:**
- 消耗: `stream_chat()` 产出的 `{"reasoning_delta": str}`（Task 2 产出）
- 产出: SSE 事件 `{"reasoning_delta": str}` 发送给前端；messages 表 INSERT 包含 `reasoning_content` 列（被 Task 4 前端消费）

- [ ] **Step 1: 修改 _stream_and_save — SSE 转发 reasoning_delta 并存储**

修改 `backend/app/routes/conversations.py` 的 `_stream_and_save` 函数：

**1a. 在 `full_content = ""` 后添加：**

```python
    full_reasoning = ""
```

**1b. 在 `chunk.get("delta")` 处理之前，添加 `reasoning_delta` 处理：**

在 `if chunk.get("delta"):` 之前插入：
```python
            if chunk.get("reasoning_delta"):
                full_reasoning += chunk["reasoning_delta"]
                yield f"data: {json.dumps({'reasoning_delta': chunk['reasoning_delta']})}\n\n"
```

**1c. 修改 finally 块中的 INSERT 语句：**

原代码：
```python
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'assistant', ?, ?)",
                (assistant_msg_id, conv_id, full_content, assistant_created),
            )
```

改为：
```python
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, reasoning_content, created_at) VALUES (?, ?, 'assistant', ?, ?, ?)",
                (assistant_msg_id, conv_id, full_content, full_reasoning, assistant_created),
            )
```

**1d. 修改 finally 条件，当只有 reasoning 没有 content 时也保存：**

原条件 `if full_content:` 改为 `if full_content or full_reasoning:`：
```python
    finally:
        if full_content or full_reasoning:
            db = get_db()
            ...
```

完整修改后的 `_stream_and_save`：
```python
def _stream_and_save(settings, messages, conv_id, cancel_event):
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
            settings.get("temperature"),
            settings.get("max_tokens"),
        ):
            if "error" in chunk:
                yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                break
            if chunk.get("stopped"):
                yield f"data: {json.dumps({'stopped': True})}\n\n"
                break
            if chunk.get("reasoning_delta"):
                full_reasoning += chunk["reasoning_delta"]
                yield f"data: {json.dumps({'reasoning_delta': chunk['reasoning_delta']})}\n\n"
            if chunk.get("delta"):
                full_content += chunk["delta"]
                yield f"data: {json.dumps({'delta': chunk['delta'], 'done': False})}\n\n"
            if chunk.get("done"):
                yield f"data: {json.dumps({'done': True})}\n\n"
    finally:
        if full_content or full_reasoning:
            db = get_db()
            db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, reasoning_content, created_at) VALUES (?, ?, 'assistant', ?, ?, ?)",
                (assistant_msg_id, conv_id, full_content, full_reasoning, assistant_created),
            )
            db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), conv_id),
            )
            db.commit()
        sse_manager.unregister(conv_id)
```

- [ ] **Step 2: 验证上下文构建不变 — chat 和 regenerate 路由**

检查 `/chat`（第 166-170 行）和 `/regenerate`（第 236-240 行）的上下文构建 SQL：

```python
rows = db.execute(
    "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
    (conv_id,),
).fetchall()
messages = [{"role": r["role"], "content": r["content"]} for r in rows]
```

**不需要修改** — SQL 已经只选 `role, content`，`reasoning_content` 不会被纳入上下文。

- [ ] **Step 3: 运行全部测试**

```bash
cd backend && python -m pytest --tb=short
```

预期：39 passed

- [ ] **Step 4: 提交**

```bash
git add backend/app/routes/conversations.py
git commit -m "feat: SSE 转发 reasoning_delta 并持久化到 messages 表"
```

---

### Task 4: 前端 Store — chat.js 处理 reasoning_delta

**文件:**
- 修改: `frontend/src/stores/chat.js`（`sendMessage` 和 `replayMessage` 方法）

**接口:**
- 消耗: SSE 事件 `{"reasoning_delta": str}`（Task 3 产出）
- 产出: `assistantMsg.reasoning_content` 字段（被 Task 5 渲染使用）

- [ ] **Step 1: 修改 sendMessage — 初始化 reasoning_content 并处理 reasoning_delta**

**1a. 在 `assistantMsg` 对象中添加 `reasoning_content`：**

原代码（第 74-79 行）：
```javascript
      const assistantMsg = {
        id: "temp-" + (Date.now() + 1),
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
      };
```

改为：
```javascript
      const assistantMsg = {
        id: "temp-" + (Date.now() + 1),
        role: "assistant",
        content: "",
        reasoning_content: "",
        created_at: new Date().toISOString(),
      };
```

**1b. 在 onMessage 回调中添加 reasoning_delta 处理：**

在 `if (chunk.delta) {` 之前插入：
```javascript
          if (chunk.reasoning_delta) {
            const last = this.messages[this.messages.length - 1];
            if (last && last.role === "assistant") {
              last.reasoning_content += chunk.reasoning_delta;
            }
          }
```

- [ ] **Step 2: 修改 replayMessage — 同样处理 reasoning_delta**

**2a. 清空旧的 reasoning_content（重新生成时重置）：**

在 `this.isStreaming = true;` 之后、`const newContent = { value: "" };` 之后添加：
```javascript
      const newReasoning = { value: "" };
```

**2b. 在 replayMessage 的 onMessage 回调中添加 reasoning_delta 处理：**

在 `if (chunk.delta) {` 之前插入：
```javascript
          if (chunk.reasoning_delta) {
            newReasoning.value += chunk.reasoning_delta;
            assistantMsg.reasoning_content = newReasoning.value;
          }
```

**2c. done 时也设置 reasoning_content：**

在 `if (chunk.done)` 块内，`assistantMsg.content = newContent.value;` 之后、`this.aiVersions[id].push(...)` 之前添加：
```javascript
            assistantMsg.reasoning_content = newReasoning.value;
```

完整修改后的 `replayMessage` 方法（仅显示 onMessage 部分）：
```javascript
        onMessage: (chunk) => {
          if (chunk.stopped) {
            this.isStreaming = false;
            return;
          }
          if (chunk.reasoning_delta) {
            newReasoning.value += chunk.reasoning_delta;
            assistantMsg.reasoning_content = newReasoning.value;
          }
          if (chunk.delta) {
            newContent.value += chunk.delta;
            assistantMsg.content = newContent.value;
          }
          if (chunk.done) {
            assistantMsg.reasoning_content = newReasoning.value;
            this.aiVersions[id].push(newContent.value);
            this.aiVersionIndex = this.aiVersions[id].length - 1;
            this.isStreaming = false;
          }
        },
```

- [ ] **Step 3: 验证 selectConversation 中最新 assistant 消息包含 reasoning_content**

`selectConversation` 从 API 获取消息详情。后端 `/api/conversations/<id>` 返回的 `messages` 列表中，每个 message 已是 `SELECT *` 的 `dict()` 结果，自动包含 `reasoning_content` 列。无需修改 store。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/stores/chat.js
git commit -m "feat: chat store 处理 reasoning_delta SSE 事件"
```

---

### Task 5: 前端组件 — MessageBubble.vue 渲染思考区块

**文件:**
- 修改: `frontend/src/components/MessageBubble.vue`

**接口:**
- 消耗: `message.reasoning_content`（Task 4 产出）
- 产出: 用户可见的可折叠思考区块

- [ ] **Step 1: 修改 template — 添加思考区块**

替换整个 `<template>` 块：

```html
<template>
  <div class="bubble-row" :class="message.role">
    <div class="bubble">
      <div
        v-if="message.role === 'assistant' && message.reasoning_content"
        class="reasoning-block"
      >
        <div class="reasoning-header" @click="reasoningOpen = !reasoningOpen">
          <span class="reasoning-icon">{{ reasoningOpen ? '▼' : '▶' }}</span>
          <span>🤔 思考过程</span>
        </div>
        <div v-show="reasoningOpen" class="reasoning-content">
          {{ message.reasoning_content }}
        </div>
      </div>
      <div class="bubble-text">{{ message.content }}</div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 修改 script — 添加 reasoningOpen 状态**

替换 `<script setup>` 块：

```html
<script setup>
import { ref } from "vue";

defineProps({
  message: { type: Object, required: true },
});

const reasoningOpen = ref(true);
</script>
```

- [ ] **Step 3: 修改 style — 添加思考区块样式**

在现有 `<style scoped>` 末尾追加：

```css
.reasoning-block {
  margin-bottom: 10px;
  border-left: 2px solid #d0d0d0;
  padding-left: 10px;
}

.reasoning-header {
  cursor: pointer;
  font-size: 13px;
  color: #888;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.reasoning-header:hover {
  color: #666;
}

.reasoning-icon {
  font-size: 10px;
  width: 12px;
}

.reasoning-content {
  font-size: 13px;
  color: #999;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}
```

- [ ] **Step 4: 验证前端构建不报错**

```bash
cd frontend && npx vite build
```

预期：build 成功，无报错。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/MessageBubble.vue
git commit -m "feat: MessageBubble 渲染可折叠 AI 思考过程"
```

---

## 任务依赖图

```
Task 1 (database.py) ──┐
                        ├──> Task 3 (conversations.py) ──> Task 4 (chat.js) ──> Task 5 (MessageBubble.vue)
Task 2 (ai.py) ────────┘
```

Task 1 和 Task 2 互不依赖，可并行。Task 3 依赖 Task 1 + Task 2。Task 4 依赖 Task 3。Task 5 依赖 Task 4。
