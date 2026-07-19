# 会话记录优化 — 即时命名与排序

日期：2026-07-19

## 背景

当前会话命名在 AI 回复完成后才更新，排序按 AI 回复时间，体验滞后。优化为前端即时命名+排序。

## 设计

### 1. 命名时机前移

**当前：** 后端 chat() 中判断 title=="新对话" 后用 content[:20] 改名，等 AI 回复完前端才看到。

**优化后：** 前端 sendMessage 时截取 content[:20] 作为 title，创建会话时传给后端。

```
用户点击发送
  → chat.js sendMessage()
    → title = content.slice(0, 20)
    → conversationsApi.create(title)
      → 后端 create_conversation 直接用 title
      → conversations.json: { title: "用户输入的前20字" }
    → 前端 conv.title = title → 侧边栏瞬间显示
```

**改动：**
- `conversationsApi.create(title)` — 加参数
- 后端 `create_conversation_route` — 直接使用 title，去掉默认"新对话"
- 后端 `chat()` — 移除 UPDATE title 逻辑

### 2. 排序即时化

**当前：** conversations 按 updated_at DESC，updated_at 在 AI 回复完成时更新。

**优化后：** 前端维护 `lastMessageAt`（内存），发送瞬间排序；后端 updated_at 在用户消息时更新（持久化）。

```
用户点击发送
  → conv.lastMessageAt = new Date().toISOString()
  → conversations.sort((a,b) => b.lastMessageAt.localeCompare(a.lastMessageAt))
  → 后端 chat() 用户消息入库 → update_conversation(updated_at=now)

首次加载：
  → loadConversations()
    → conv.lastMessageAt = conv.updated_at  // 用后端时间戳初始化
```

**改动：**
- `chat.js` — 每个 conv 增加前端字段 lastMessageAt
- `sendMessage()` — 发送后立即设 lastMessageAt 并排序
- `loadConversations()` — 用 updated_at 初始化 lastMessageAt
- 后端 `_stream_and_save()` — 移除 finally 中的 update_conversation(updated_at)

### 3. 数据格式

conversations.json 结构不变：
```json
{ "id": "...", "title": "...", "created_at": "...", "updated_at": "最后用户消息时间" }
```
- `updated_at` 语义改为"最后一条用户消息时间"
- `lastMessageAt` 纯前端内存，不持久化

### 4. 向后兼容

- 旧 title="新对话" → 用户可手动编辑
- 旧 updated_at 可能为 AI 回复时间 → 加载后用作初始排序，不影响功能
