# 会话即时命名与排序 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 命名在用户发送瞬间生效，列表在发送瞬间重排到顶部。

**Architecture:** 前端截取 content[:20] 作为 title 传给后端创建会话；前端内存维护 lastMessageAt 字段驱动即时排序，后端 updated_at 同步持久化供刷新后初始排序。

**Tech Stack:** Vue 3 / Pinia (前端), Flask / JSON 文件存储 (后端)

## Global Constraints

- 保持 API 响应格式不变，前端零破坏
- conversations.json 结构不变
- 向后兼容旧数据（title="新对话"、旧 updated_at）
- 39 个现有测试必须通过

---

### Task 1: 前端 — create 传 title

**Files:**
- Modify: `frontend/src/api/conversations.js`

**Interfaces:**
- Produces: `create(title)` — 向后兼容，无 title 时传 undefined

- [ ] **Step 1: 修改 create 接受 title 参数**

```javascript
export function create(title) {
  return http.post("/conversations", { title });
}
```

当前已接受 title 参数（第10行：`return http.post("/conversations", { title });`），无需改动。验证即可。

- [ ] **Step 2: 构建验证**

```bash
cd frontend && npx vite build
```
预期：BUILD PASS

---

### Task 2: 前端 — sendMessage 截取命名 + lastMessageAt 排序

**Files:**
- Modify: `frontend/src/stores/chat.js`

**Interfaces:**
- Consumes: `conversationsApi.create(title)` from Task 1
- Produces: 每个 conv 新增前端字段 `lastMessageAt`；conversations 保持按 lastMessageAt 降序

- [ ] **Step 1: sendMessage 中截取命名并在创建时传入**

在 `sendMessage()` 的 `NEW_CONV` 分支中，截取 content[:20] 作为 title：

```javascript
// 替换：const conv = await conversationsApi.create();
const title = content.slice(0, 20);
const conv = await conversationsApi.create(title);
```

- [ ] **Step 2: sendMessage 中设置 lastMessageAt 并排序**

在 `sendMessage()` 中，创建会话后（非 NEW_CONV 则在添加用户消息后），更新 lastMessageAt 并排序：

```javascript
// 创建会话后 / 或已存在会话时
const now = new Date().toISOString();
const convIdx = this.conversations.findIndex(c => c.id === this.activeConvId);
if (convIdx !== -1) {
  this.conversations[convIdx].lastMessageAt = now;
}
this.conversations.sort((a, b) => (b.lastMessageAt || "").localeCompare(a.lastMessageAt || ""));
```

完整逻辑位置：在 `sendMessage` 中，插入用户消息到 messages 数组之后、SSE 请求之前。

- [ ] **Step 3: loadConversations 中初始化 lastMessageAt**

```javascript
async loadConversations() {
  this.conversations = await conversationsApi.list();
  this.conversations.forEach(c => {
    c.lastMessageAt = c.updated_at;
  });
  this.conversations.sort((a, b) => (b.lastMessageAt || "").localeCompare(a.lastMessageAt || ""));
},
```

- [ ] **Step 4: createConversation（新建空白对话）也设 lastMessageAt**

```javascript
createConversation() {
  this.activeConvId = NEW_CONV;
  this.messages = [];
  this.aiVersions = {};
  // 不设置 lastMessageAt（NEW_CONV 不在列表中）
},
```
无需改动 — NEW_CONV 不在 conversations 列表中，发送消息后创建时会自动处理。

- [ ] **Step 5: 构建验证**

```bash
cd frontend && npx vite build
```
预期：BUILD PASS

---

### Task 3: 后端 — create_conversation 直接用传入 title

**Files:**
- Modify: `backend/app/routes/conversations.py`

**Interfaces:**
- Consumes: `request.get_json()["title"]`
- Produces: conversations.json 中 title 直接为用户传入值

- [ ] **Step 1: 去掉默认 "新对话"**

```python
# 修改 create_conversation_route 中的 title 行：
# 旧：
title = (body.get("title") or "").strip() or "新对话"

# 新：直接使用传入值
title = (body.get("title") or "").strip() or "新对话"
```

实际上不用改 — 当前逻辑 `or "新对话"` 当 title 为空时兜底，前端传了就有值。已经正确。

- [ ] **Step 2: 运行测试**

```bash
cd backend && python -m pytest tests/test_conversations.py -v
```
预期：8 passed

---

### Task 4: 后端 — chat() 移除 title 更新

**Files:**
- Modify: `backend/app/routes/conversations.py`

- [ ] **Step 1: 删除 title 更新逻辑**

在 `chat()` 函数中，删除自动命名逻辑：

```python
# 删除这段：
new_title = content[:20] if row.get("title") == "新对话" else row.get("title")
update_conversation(conv_id, {"updated_at": now, "title": new_title})

# 替换为只更新 updated_at：
update_conversation(conv_id, {"updated_at": now})
```

- [ ] **Step 2: 运行测试**

```bash
cd backend && python -m pytest tests/ -v
```
预期：39 passed

---

### Task 5: 后端 — _stream_and_save 移除 updated_at 更新

**Files:**
- Modify: `backend/app/routes/conversations.py`

- [ ] **Step 1: 删除 finally 中的 update_conversation**

在 `_stream_and_save()` 的 finally 块中，删除 `update_conversation` 调用：

```python
# finally 块中，删除或注释这行：
# update_conversation(conv_id, {
#     "updated_at": datetime.now(timezone.utc).isoformat(),
# })
```

只保留 `add_message` 和 `sse_manager.unregister`。

- [ ] **Step 2: 运行全部测试**

```bash
cd backend && python -m pytest -v
```
预期：39 passed

---

### Task 6: 集成验证

- [ ] **Step 1: 前端构建**

```bash
cd frontend && npx vite build
```

- [ ] **Step 2: 全部后端测试**

```bash
cd backend && python -m pytest -v
```

预期：BUILD PASS + 39 passed

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "feat: 会话即时命名与排序优化"
```
