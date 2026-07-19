# 前端待后端联调 API 清单

> 日期：2026-07-19 | 前端版本：v1.0.0 | 状态：待后端实现

---

## 通用约定

- 基础路径：`/api`
- 非 SSE 接口统一响应：`{ "code": 0, "message": "ok", "data": {} }`
- SSE 接口 Content-Type：`text/event-stream`
- SSE 数据格式：`data: {"delta": "...", "done": false}`

---

## 1. 会话管理

| 方法 | 路径 | 请求体 | 说明 | 前端调用位置 |
|------|------|--------|------|-------------|
| `GET` | `/conversations` | — | 获取对话列表，按 updated_at 倒序 | `chat.js → loadConversations()` |
| `POST` | `/conversations` | `{ "title"?: string }` | 新建对话，title 可选 | `chat.js → sendMessage()` 首次发送时 |
| `GET` | `/conversations/:id` | — | 获取对话详情，data 中需含 messages 数组 | `chat.js → selectConversation()` |
| `PUT` | `/conversations/:id` | `{ "title": string }` | 重命名对话 | `chat.js → renameConversation()` |
| `DELETE` | `/conversations/:id` | — | 删除对话（级联删除消息） | `chat.js → deleteConversation()` |

---

## 2. 消息与对话（SSE）

| 方法 | 路径 | 请求体 | 说明 | 前端调用位置 |
|------|------|--------|------|-------------|
| `POST` | `/conversations/:id/chat` | `{ "content": string }` | **SSE 流式**。保存 user 消息，拼接上下文调 AI，逐 chunk 推送 | `sse.js → chat.js → sendMessage()` |
| `POST` | `/conversations/:id/regenerate` | `{}` | **SSE 流式**。删除最后一条 assistant 消息，重新生成 | `sse.js → chat.js → replayMessage()` |
| `PUT` | `/conversations/:id/messages/:msgId` | `{ "content": string }` | 编辑消息，截断该消息之后的所有消息 | `chat.js → editMessage()` |
| `POST` | `/conversations/:id/stop` | — | 终止当前 SSE 生成，已输出部分保留 | `chat.js → stopStreaming()` |

### SSE 事件协议

```
data: {"delta": "你好"}      → 增量文本，前端追加渲染
data: {"delta": ""}          → 可能为空包
data: {"done": true}         → 生成完成，前端关闭 EventSource
data: {"stopped": true}      → 被 /stop 中断
```

---

## 3. API 配置管理

| 方法 | 路径 | 请求体 | 说明 | 前端调用位置 |
|------|------|--------|------|-------------|
| `GET` | `/settings` | — | 获取所有预设，api_key 脱敏返回 | `settings.js → loadPresets()` |
| `POST` | `/settings` | `{ name, api_url, api_key, model, response_format, temperature, max_tokens }` | 新建预设 | `settings.js → createPreset()` |
| `PUT` | `/settings/:id` | 同上，api_key 传 "" 不覆盖 | 更新预设 | `settings.js → savePreset()` |
| `DELETE` | `/settings/:id` | — | 删除预设 | `settings.js → deletePreset()` |
| `POST` | `/settings/:id/test` | — | 测试连通性 | `settings.js (预留)` |
| `PUT` | `/settings/:id/default` | — | 设为默认 | `settings.js (预留)` |
| `GET` | `/settings/models` | query: `api_url`, `api_key` | 调用 AI API `/models` 返回可用模型列表 | `settings.js → fetchModels()` |

---

## 4. 优先级

| 优先级 | 接口 | 原因 |
|--------|------|------|
| 🔴 P0 | `POST /conversations/:id/chat` (SSE) | **核心对话流程**，无此接口无法对话 |
| 🔴 P0 | `GET /settings` + `POST /settings` | 配置 API 后才能调用 AI |
| 🟡 P1 | `GET /conversations` + `POST /conversations` | 对话创建和列表 |
| 🟡 P1 | `GET /conversations/:id` | 切换对话加载历史 |
| 🟡 P1 | `POST /conversations/:id/stop` | 暂停 AI 输出 |
| 🟢 P2 | `PUT /conversations/:id` | 对话重命名 |
| 🟢 P2 | `DELETE /conversations/:id` | 删除对话 |
| 🟢 P2 | `PUT /conversations/:id/messages/:msgId` | 编辑消息 |
| 🟢 P2 | `POST /conversations/:id/regenerate` (SSE) | AI 重放 |
| 🟢 P2 | `GET /settings/models` | 拉取模型列表 |
| 🟢 P3 | `PUT /settings/:id` + `DELETE /settings/:id` | 预设更新/删除 |
| 🟢 P3 | `POST /settings/:id/test` + `PUT /settings/:id/default` | 测试和默认设置 |

---

## 5. 对接检查清单

- [ ] 所有接口统一返回 `{ code, message, data }` 格式
- [ ] SSE 流按 `data: {...}\n\n` 格式推送
- [ ] api_key 数据库 Fernet 加密存储，读取时解密，对外脱敏
- [ ] CORS 允许跨域（前端 Vite dev server 端口 5173 → 后端 5000）
- [ ] 错误日志写入 `user_data/logs/error.log`
