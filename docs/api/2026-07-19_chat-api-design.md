# Chat 后端 API 设计文档

> 日期：2025-07-16 | 版本：v1.0 | 状态：设计阶段（待实现）

---

## 1. 概述

后端基于 Flask，使用 SQLite 存储，Fernet 加密 API Key。所有接口返回统一 JSON 结构，SSE 接口使用 `text/event-stream`。

### 基础信息

| 项 | 值 |
|----|-----|
| 基础路径 | `http://127.0.0.1:5000/api` |
| 数据格式 | JSON（SSE 除外） |
| 字符编码 | UTF-8 |

---

## 2. 通用约定

### 2.1 响应格式

所有非 SSE 接口统一返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | **0 = 成功**，非零 = 失败 |
| message | string | 可读的描述信息 |
| data | object/array/null | 业务数据负载 |

### 2.2 SSE 流式格式

```
Content-Type: text/event-stream

data: {"delta": "你好", "done": false}

data: {"delta": "，世界", "done": false}

data: {"delta": "", "done": true}
```

- `done: true` → 生成结束，前端关闭 EventSource
- 被 `/stop` 中断时，额外收到 `{"stopped": true}`

---

## 3. 接口列表

### 3.1 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/conversations` | 获取会话列表 |
| `POST` | `/conversations` | 新建会话 |
| `GET` | `/conversations/:id` | 获取会话详情（含消息） |
| `DELETE` | `/conversations/:id` | 删除会话（级联删除消息） |
| `PUT` | `/conversations/:id` | 重命名会话 |

#### GET /conversations

**响应：**
```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": "uuid",
      "title": "新对话",
      "created_at": "2025-07-16T10:30:00Z",
      "updated_at": "2025-07-16T11:20:00Z"
    }
  ]
}
```

#### POST /conversations

**请求：**
```json
{ "title": "新对话" }
```
`title` 可选，不传自动生成。

#### GET /conversations/:id

**响应 data 中包含 messages 数组：**
```json
{
  "id": "uuid",
  "title": "...",
  "created_at": "...",
  "updated_at": "...",
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "...",
      "created_at": "..."
    },
    {
      "id": "msg-uuid",
      "role": "assistant",
      "content": "...",
      "created_at": "..."
    }
  ]
}
```

#### PUT /conversations/:id

**请求：**
```json
{ "title": "新标题" }
```

---

### 3.2 消息与对话

| 方法 | 路径 | 说明 | 响应类型 |
|------|------|------|----------|
| `POST` | `/conversations/:id/chat` | 发送消息 | **SSE** |
| `PUT` | `/conversations/:id/messages/:msgId` | 编辑消息 | JSON |
| `POST` | `/conversations/:id/regenerate` | 重新生成 | **SSE** |
| `POST` | `/conversations/:id/stop` | 停止生成 | JSON |

#### POST /conversations/:id/chat（SSE）

**请求：** `{ "content": "你好" }`

**流程：**
1. 保存 user 消息到 DB
2. 取出会话全部历史，组装上下文
3. 调用 AI API，逐 chunk 通过 SSE 推送
4. 流结束后，完整 assistant 消息写入 DB

#### PUT /conversations/:id/messages/:msgId

**规则：** 只能编辑 `role: "user"` 的消息。编辑后，该消息之后的所有消息（含 assistant 回复）自动删除。

**请求：** `{ "content": "修改后的内容" }`

#### POST /conversations/:id/regenerate（SSE）

**行为：** 删除最后一条 `role: "assistant"` 的消息，用当前上下文重新生成。

**异常：**
| 情况 | 返回 |
|------|------|
| 会话无消息 | 400 |
| 最后一条不是 assistant | 400 |

#### POST /conversations/:id/stop

**行为：** 终止当前 SSE 流。已产出的部分消息保留。

**时序：**
```
前端                           后端
 ├── POST /chat ───────────────→ SSE 开始
 │←── data: chunk1 ─────────────┤
 │←── data: chunk2 ─────────────┤
 ├── POST /stop ───────────────→ 设置 cancel 标志
 │←── { code: 0 } ──────────────┤
 │←── data: {"stopped":true} ───┤ SSE 关闭
```

---

### 3.3 API 配置管理

所有 `api_key` 以 Fernet 加密存储，对外返回脱敏形式（前 4 位 + `****`）。

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/settings` | 获取配置列表 |
| `POST` | `/settings` | 新增配置 |
| `PUT` | `/settings/:id` | 更新配置 |
| `DELETE` | `/settings/:id` | 删除配置 |
| `POST` | `/settings/:id/test` | 测试连通性 |
| `PUT` | `/settings/:id/default` | 设为默认配置 |
| `GET` | `/settings/models` | 拉取可用模型列表 |

#### GET /settings

`api_key` 脱敏返回：`sk-a****`

#### POST /settings

**请求：**
```json
{
  "name": "OpenAI 官方",
  "api_url": "https://api.openai.com/v1",
  "api_key": "sk-xxx",
  "model": "gpt-4o",
  "response_format": "text",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

| 参数 | 类型 | 必填 | 默认值 |
|------|------|------|--------|
| name | string | 是 | — |
| api_url | string | 是 | — |
| api_key | string | 是 | — |
| model | string | 否 | `gpt-4o` |
| response_format | string | 否 | `text` |
| temperature | float | 否 | `0.7` |
| max_tokens | int | 否 | `4096` |

#### PUT /settings/:id

`api_key` 传空字符串 `""` 时不覆盖原密钥。

#### DELETE /settings/:id

不能删除当前默认配置。

#### GET /settings/models

使用指定 `apiUrl` + `apiKey` 调用 AI API 的 `/models` 端点，返回可用模型列表。

**请求参数：** `?api_url=...&api_key=...`

---

## 4. 数据模型

### conversations

| 列 | 类型 | 说明 |
|----|------|------|
| id | TEXT PK | UUID |
| title | TEXT | 会话标题 |
| created_at | TEXT | ISO 8601 |
| updated_at | TEXT | ISO 8601 |

### messages

| 列 | 类型 | 说明 |
|----|------|------|
| id | TEXT PK | UUID |
| conversation_id | TEXT FK | 所属会话 |
| role | TEXT | `user` / `assistant` |
| content | TEXT | 消息内容 |
| created_at | TEXT | ISO 8601 |

外键 CASCADE 删除。

### settings

| 列 | 类型 | 说明 |
|----|------|------|
| id | TEXT PK | UUID |
| name | TEXT | 配置名称 |
| api_url | TEXT | API 地址 |
| api_key | TEXT | Fernet 加密 |
| model | TEXT | 默认模型 |
| response_format | TEXT | `text` / `json_object` |
| temperature | REAL | 0~2 |
| max_tokens | INTEGER | token 上限 |
| is_default | INTEGER | 0/1 |
| created_at | TEXT | ISO 8601 |
| updated_at | TEXT | ISO 8601 |

---

## 5. 实现状态

| 接口 | 路由文件 | 状态 |
|------|----------|------|
| `/hello` | `routes/example.py` | ✅ 已实现（测试） |
| `/conversations` CRUD | 待创建 | ❌ 待实现 |
| `/conversations/:id/chat` | 待创建 | ❌ 待实现 |
| `/conversations/:id/regenerate` | 待创建 | ❌ 待实现 |
| `/conversations/:id/stop` | 待创建 | ❌ 待实现 |
| `/settings` CRUD | 待创建 | ❌ 待实现 |
| `/settings/models` | 待创建 | ❌ 待实现 |
| 数据库 | `database.py` | ✅ 已建表 |
| Fernet 加密 | `database.py` | ✅ 已实现 |
