# Chat API 接口文档

> 基础路径: `http://127.0.0.1:5000/api`

---

## 目录

- [1. 会话管理](#1-会话管理)
- [2. 消息与对话](#2-消息与对话)
- [3. API 配置管理](#3-api-配置管理)
- [通用约定](#通用约定)

---

## 通用约定

### 请求规范

- 所有接口的请求体和响应体均使用 **JSON** 格式
- 请求头 `Content-Type: application/json`（SSE 接口除外）
- 路径参数使用 URL 路径段（如 `/:id`），查询参数仅用于分页/筛选等可选场景

### 响应规范

所有非 SSE 接口统一返回以下 JSON 结构：

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
| data | object / array / null | 业务数据负载 |

### 错误码与日志

```
code = 0   →  成功，不记录日志
code ≠ 0   →  失败，后端自动写入日志文件 user_data/logs/error.log
```

所有 `code ≠ 0` 的响应均视为失败，服务端在返回前自动记录一条日志，包含：

- 时间戳
- 请求方法 + 路径
- 错误码
- 错误信息（message）
- 请求体（如有，敏感字段自动脱敏）

**客户端对接约定：** 前端统一判断 `code === 0`，非零一律进入错误处理分支。

### SSE 流式格式

流式接口使用 Server-Sent Events，Content-Type 为 `text/event-stream`。每条数据格式：

```
data: {"delta": "你好", "done": false}

data: {"delta": "，我", "done": false}

data: {"delta": "", "done": true}
```

当 `done: true` 时表示生成结束，前端关闭 EventSource。若被 `/stop` 中断，会额外收到一条：

```
data: {"stopped": true}
```

---

## 1. 会话管理

### 1.1 获取会话列表

```
GET /conversations
```

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": "c0a8b1c2-...",
      "title": "今天天气怎么样",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T11:20:00Z"
    }
  ]
}
```

---

### 1.2 新建会话

```
POST /conversations
```

**请求体：**

```json
{
  "title": "新对话"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 会话标题，不传则自动生成 |

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "c0a8b1c2-...",
    "title": "新对话",
    "created_at": "2026-01-15T12:00:00Z",
    "updated_at": "2026-01-15T12:00:00Z"
  }
}
```

---

### 1.3 获取会话详情

```
GET /conversations/:id
```

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "c0a8b1c2-...",
    "title": "今天天气怎么样",
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T11:20:00Z",
    "messages": [
      {
        "id": "msg-001",
        "role": "user",
        "content": "今天北京天气怎么样？",
        "created_at": "2026-01-15T10:30:00Z"
      },
      {
        "id": "msg-002",
        "role": "assistant",
        "content": "今天北京晴，最高温度 5°C……",
        "created_at": "2026-01-15T10:30:05Z"
      }
    ]
  }
}
```

---

### 1.4 删除会话

```
DELETE /conversations/:id
```

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": null
}
```

---

## 2. 消息与对话

### 2.1 发送消息（SSE 流式）

```
POST /conversations/:id/chat
```

**请求体：**

```json
{
  "content": "你好，请帮我……"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 用户消息内容 |

**响应：** SSE 流式，格式见 [通用约定 → SSE 流式格式](#sse-流式格式)。

**流程：**
1. 服务端保存 user 消息到数据库
2. 取出会话全部历史消息，组装上下文发给 AI 模型
3. 逐 chunk 通过 SSE 推送，前端实时渲染
4. 流结束后，完整 assistant 消息写入数据库

---

### 2.2 编辑消息

```
PUT /conversations/:id/messages/:msgId
```

**规则：** 只能编辑 `role: "user"` 的消息。编辑成功后，**该消息之后的所有消息（包括 assistant 回复）将被自动删除**，前端可调用 regenerate 重新生成。

**请求体：**

```json
{
  "content": "修改后的内容"
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "msg-001",
    "role": "user",
    "content": "修改后的内容",
    "created_at": "2026-01-15T10:30:00Z"
  }
}
```

> 注意：编辑不会自动触发 AI 回复，前端根据业务需要决定是否调用 regenerate。

---

### 2.3 重新生成（SSE 流式）

```
POST /conversations/:id/regenerate
```

**行为：** 删除会话中最后一条 `role: "assistant"` 的消息，用当前上下文重新调用 AI 模型，SSE 流式返回新回复。

**请求体：** 无（空 body）。

**响应：** SSE 流式，同 `/chat`。

**异常情况：**

| 情况 | 返回 |
|------|------|
| 会话无消息 | 400 |
| 最后一条不是 assistant | 400（无法 regene rate） |

---

### 2.4 停止生成

```
POST /conversations/:id/stop
```

**行为：** 终止该会话当前正在进行的 SSE 生成任务。服务端设置取消信号，SSE 循环检测到后退出，已产出的部分消息保留。

**请求体：** 无（空 body）。

**响应示例：**

```json
{
  "code": 0,
  "message": "已发送停止信号",
  "data": null
}
```

**时序说明：**
```
前端                           后端
 │                              │
 ├── POST /chat ───────────────→│ SSE 开始推送
 │←── data: chunk1 ─────────────┤
 │←── data: chunk2 ─────────────┤
 │                              │
 ├── POST /stop ───────────────→│ 设置 cancel 标志
 │←── { code: 0 } ──────────────┤
 │←── data: {"stopped":true} ───┤ SSE 优雅关闭
 │                              │
```

---

## 3. API 配置管理

支持多组 API 配置，前端设置页面自由切换。所有 `api_key` 在数据库中以 **Fernet 加密** 存储，对外仅返回脱敏形式。

### 3.1 获取配置列表

```
GET /settings
```

> `api_key` 脱敏返回：`sk-a****`（前 4 位 + `****`）。

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": "set-001",
      "name": "OpenAI 官方",
      "api_url": "https://api.openai.com/v1",
      "api_key": "sk-p****",
      "model": "gpt-4o",
      "response_format": "text",
      "temperature": 0.7,
      "max_tokens": 4096,
      "is_default": true,
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z"
    },
    {
      "id": "set-002",
      "name": "本地 Ollama",
      "api_url": "http://localhost:11434/v1",
      "api_key": "",
      "model": "qwen2.5:7b",
      "response_format": "text",
      "temperature": 0.7,
      "max_tokens": 2048,
      "is_default": false,
      "created_at": "2026-01-15T11:00:00Z",
      "updated_at": "2026-01-15T11:00:00Z"
    }
  ]
}
```

---

### 3.2 新增配置

```
POST /settings
```

**请求体：**

```json
{
  "name": "Azure OpenAI",
  "api_url": "https://xxx.openai.azure.com",
  "api_key": "sk-azure-key",
  "model": "gpt-4o",
  "response_format": "text",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 配置名称 |
| api_url | string | 是 | API 地址 |
| api_key | string | 是 | API 密钥（明文传入，后端加密存储） |
| model | string | 否 | 默认 `gpt-4o` |
| response_format | string | 否 | `text` / `json_object`，默认 `text` |
| temperature | float | 否 | 0~2，默认 0.7 |
| max_tokens | int | 否 | 默认 4096 |

---

### 3.3 更新配置

```
PUT /settings/:id
```

**规则：** `api_key` 为空字符串 `""` 时不覆盖原密钥。

**请求体：**

```json
{
  "name": "Azure 改个名字",
  "api_url": "https://xxx.openai.azure.com",
  "api_key": "",
  "model": "gpt-4o",
  "temperature": 0.5,
  "max_tokens": 8192
}
```

---

### 3.4 删除配置

```
DELETE /settings/:id
```

> 不能删除当前默认配置。需先通过 `/settings/:otherId/default` 切换默认后再删除。

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": null
}
```

---

### 3.5 测试连通性

```
POST /settings/:id/test
```

**行为：** 使用指定配置向 AI API 发送简短测试。`api_key` 在服务端解密后发起请求，全程不暴露明文。

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "success": true,
    "latency_ms": 320,
    "model": "gpt-4o"
  }
}
```

---

### 3.6 设为默认

```
PUT /settings/:id/default
```

**行为：** 将该配置设为默认，同时取消其他配置的默认标记。发送消息时若未指定配置则使用默认。

**响应示例：**

```json
{
  "code": 0,
  "message": "ok",
  "data": { "is_default": true }
}
```

---

## 接口汇总

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/conversations` | 会话列表 |
| `POST` | `/conversations` | 新建会话 |
| `GET` | `/conversations/:id` | 会话详情 + 历史消息 |
| `DELETE` | `/conversations/:id` | 删除会话（级联删除消息） |
| `POST` | `/conversations/:id/chat` | 发送消息 → **SSE** |
| `PUT` | `/conversations/:id/messages/:msgId` | 编辑消息（截断后续） |
| `POST` | `/conversations/:id/regenerate` | 重新生成 → **SSE** |
| `POST` | `/conversations/:id/stop` | 停止当前 SSE 生成 |
| `GET` | `/settings` | 获取配置列表 |
| `POST` | `/settings` | 新增配置 |
| `PUT` | `/settings/:id` | 更新配置 |
| `DELETE` | `/settings/:id` | 删除配置 |
| `POST` | `/settings/:id/test` | 测试连通性 |
| `PUT` | `/settings/:id/default` | 设为默认配置 |