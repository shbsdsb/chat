# AI 思考过程展示 — 设计文档

## 概述

在聊天对话页面中显示 AI 模型的推理/思考过程（reasoning_content）。支持 DeepSeek R1 及兼容 API（如硅基流动、通义千问 QwQ）。思考过程持久化到数据库但不纳入历史上下文。

## 数据流

```
DeepSeek API SSE chunk
  → delta.reasoning_content  → ai.py yield {"reasoning_delta": "…"}
    → _stream_and_save → SSE → 前端 reasoning_content 累积
  → delta.content            → ai.py yield {"delta": "…"}
    → _stream_and_save → SSE → 前端 content 累积
  → done
    → 存储: INSERT INTO messages (reasoning_content, content)
    → 构建上下文: 只用 role + content，不含 reasoning_content
```

## 改动范围

### 1. 数据库 — `backend/app/database.py`

- `messages` 表新增 `reasoning_content TEXT NOT NULL DEFAULT ''`
- `init_db()` 的 `CREATE TABLE IF NOT EXISTS` 同步更新
- **兼容性**：已有数据库需执行 `ALTER TABLE messages ADD COLUMN reasoning_content TEXT NOT NULL DEFAULT ''`（幂等，在 `init_db` 中 try/except 处理）

### 2. 后端 SSE 解析 — `backend/app/services/ai.py`

`stream_chat()` 解析 delta 时额外提取 `reasoning_content`：

```python
delta = chunk["choices"][0]["delta"]
reasoning = delta.get("reasoning_content", "")
content = delta.get("content", "")
if reasoning:
    yield {"reasoning_delta": reasoning}
if content:
    yield {"delta": content}
```

不影响现有行为 — 没有 reasoning 的模型不会触发新路径。

### 3. 后端 SSE 转发 & 存储 — `backend/app/routes/conversations.py`

`_stream_and_save()`：

- 新增 `full_reasoning` 变量累积思考内容
- 收到 `reasoning_delta` 时转发给 SSE 客户端：`{"reasoning_delta": "…"}`
- finally 块写入 messages 表时带上 `reasoning_content` 列
- `/chat` 和 `/regenerate` 构建历史上下文时**只取 role + content**，显式排除 reasoning_content

### 4. 前端 Store — `frontend/src/stores/chat.js`

`sendMessage()` 中：

- `assistantMsg` 新增 `reasoning_content: ""` 属性
- 处理 `chunk.reasoning_delta`：累加到 `assistantMsg.reasoning_content`
- 处理 `chunk.delta`：累加到 `assistantMsg.content`（逻辑不变）
- `replayMessage()` 同理

### 5. 前端组件 — `frontend/src/components/MessageBubble.vue`

当 `message.reasoning_content` 不为空时，在消息内容上方渲染可折叠区块：

- 标题行："🤔 思考过程" + 展开/收起箭头
- 默认展开
- 样式：浅色字体、左侧竖线标识、比正文略小的字号
- 用本地 `ref(false)` 控制折叠状态（不要全局状态 — 各消息独立）

## 不纳入范围

- 不做 OpenAI o1 系列的 reasoning_tokens 支持（API 不暴露原文）
- 不做其他 LLM 的思考字段适配（后续按需扩展）
- 不修改消息编辑逻辑（编辑仅针对用户消息，不涉及 AI 思考）

## 风险 & 边界

- **数据库兼容**：旧数据库无 reasoning_content 列，`init_db` 需 try/except ALTER TABLE
- **空字符串默认值**：无思考过程的模型，字段为空，前端不渲染
- **大文本**：思考过程可能很长（几百 token），需确保前端容器不撑爆布局（max-height + overflow-y: auto）
