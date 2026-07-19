# Chat 后端 API 实现设计

> 日期：2026-07-19 · 分支：`develop` · 依赖：[Chat MVP 前端设计](./2026-07-19-chat-mvp-design.md)

---

## 1. 技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| AI 模型调用 | `requests` 库直连 OpenAI 兼容 API | 轻量、零额外依赖、兼容所有兼容接口 |
| SSE 取消机制 | `threading.Event` + `queue.Queue` | 支持 `/stop` 优雅中断，不引入新依赖 |
| 路由拆分 | 两个文件：`conversations.py` + `settings.py` | 职责清晰，对齐前端 Store 拆分风格 |

---

## 2. 文件结构

```
backend/app/
├── __init__.py              # 已有：create_app()
├── database.py              # 已有：init_db, get_db, encrypt/decrypt
├── models/
│   └── __init__.py          # 已有
├── routes/
│   ├── __init__.py          # 已有：Blueprint 定义
│   ├── conversations.py     # 新增：会话 + 消息 8 个接口
│   └── settings.py          # 新增：配置管理 6 个接口
├── services/                # 新增目录
│   ├── ai.py                # AI 调用 + 流式生成器
│   └── sse_manager.py       # SSE 会话管理（/stop 取消）
└── utils/
    └── response.py          # 新增：统一响应 + 错误日志 helper
```

---

## 3. 路由详情

### 3.1 conversations.py

| 方法 | 路径 | 核心逻辑 |
|------|------|----------|
| `GET` | `/conversations` | `SELECT * FROM conversations ORDER BY updated_at DESC` |
| `POST` | `/conversations` | `INSERT` 新行 → 返回完整对象 |
| `GET` | `/conversations/:id` | 联表查询 conversation + messages，按 created_at 升序 |
| `DELETE` | `/conversations/:id` | `DELETE` 对话（CASCADE 删消息） |
| `POST` | `/conversations/:id/chat` | ①保存 user msg ②注册 cancel ③流式 SSE ④保存 assistant msg ⑤注销 cancel |
| `PUT` | `/conversations/:id/messages/:msgId` | ①校验 role=user ②更新 content ③删除该消息之后的所有消息 |
| `POST` | `/conversations/:id/regenerate` | ①删除最后一条 assistant 消息 ②同 chat 流程 |
| `POST` | `/conversations/:id/stop` | 调用 `sse_manager.cancel(id)`，返回成功 |

### 3.2 settings.py

| 方法 | 路径 | 核心逻辑 |
|------|------|----------|
| `GET` | `/settings` | `SELECT *`，api_key 脱敏返回 `sk-a****` 格式 |
| `POST` | `/settings` | 校验 name/api_url/api_key 必填，Fernet 加密 api_key，INSERT |
| `PUT` | `/settings/:id` | UPDATE；api_key 为空字符串时保留原值 |
| `DELETE` | `/settings/:id` | 禁止删除 `is_default=1` 的配置，校验后 DELETE |
| `POST` | `/settings/:id/test` | 解密 api_key → 发一个简短的非流式请求 → 返回 `{success, latency_ms, model}` |
| `PUT` | `/settings/:id/default` | ①清空其他 `is_default` ②设置目标 `is_default=1` |

### 3.3 统一响应格式

```python
# utils/response.py
def ok(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data})

def fail(code, message, log_data=None):
    # 写入 user_data/logs/error.log
    return jsonify({"code": code, "message": message, "data": None})
```

---

## 4. 服务模块

### 4.1 ai.py — AI 调用 + 流式生成器

```
stream_chat(url, key, model, messages, response_format, cancel_event) → generator
```

- 用 `requests.post(url, stream=True)` 发送 OpenAI 兼容请求
- 逐行解析 `data: {"choices":[{"delta":{"content":"..."}}]}` 
- 每 yield 前检查 `cancel_event.is_set()`
- 被取消时 yield `{"stopped": true}`
- 流结束时 yield `{"done": true}`

### 4.2 sse_manager.py — SSE 会话管理

```
{conv_id: threading.Event} 映射表，用 threading.Lock 保护

register(conv_id)   → 创建 Event，存入映射
cancel(conv_id)     → 设置 Event，中断流
unregister(conv_id) → 从映射移除
```

---

## 5. 数据流

### 发送消息（POST /conversations/:id/chat）

```
前端 POST {content}
  → 校验 conversation 存在
  → 获取当前默认 settings（api_url, api_key, model, response_format）
  → 保存 user message 到 DB
  → sse_manager.register(conv_id)
  → Response(stream_generator(), mimetype='text/event-stream')
    → 组装 messages 历史数组
    → ai.stream_chat(url, key, model, messages, format, cancel_event)
      → 逐 chunk yield "data: {delta}\n\n" 给前端
    → 流正常结束：保存 assistant message 到 DB
    → 流被取消：保留已产出的部分内容，保存到 DB
  → sse_manager.unregister(conv_id)
```

### 停止生成（POST /conversations/:id/stop）

```
前端 POST（空 body）
  → sse_manager.cancel(conv_id)   # 设置 cancel_event
  → 返回 {code: 0}
  → AI 线程检测到 cancel_event → yield {stopped: true} → 退出
```

---

## 6. 错误码约定

| code | 含义 |
|------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在（会话/配置/消息） |
| 409 | 业务冲突（删除默认配置） |
| 500 | 服务端/外部 API 错误 |

---

## 7. 依赖

- `requests` — HTTP 调用 AI API（需添加到 `requirements.txt`）
- `threading` — 标准库
- `queue` — 标准库
- `uuid` — 标准库，生成 ID
- `datetime` — 标准库，时间戳

---

## 8. 相关文档

| 文档 | 路径 |
|------|------|
| API 接口规范 | `docs/API.md` |
| 数据存储方案 | `docs/STORAGE.md` |
| 前端 MVP 设计 | `docs/superpowers/specs/2026-07-19-chat-mvp-design.md` |
| 前端设计 | `docs/frontend/2026-07-19_chat-mvp-design.md` |
