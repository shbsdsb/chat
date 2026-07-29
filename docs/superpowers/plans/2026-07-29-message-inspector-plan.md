# Message Inspector 扩展 — 实现计划

> **For agentic workers:** 使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 按任务逐个实现。

**目标：** 开发 message-inspector 扩展，在消息发送给 AI 之前在终端打印组装后的完整 messages 数组（格式化 JSON），带前端开关控制。

**架构：** 后端 `conversations.py` 新增 `chat.pre_send` dispatch 调用点 → 扩展 `on_chat_pre_send(ctx)` 读取自身 settings.json 检查开关 → print JSON。前端仅面板注册，开关由扩展管理面板渲染。

**技术栈：** Python/Flask（dispatch + backend.py）、JSON（manifest/settings）、Vue（扩展管理面板自动渲染 features 开关）

---

## 全局约束

- 所有文件禁止 emoji
- 扩展存放在 `test_expand/message-inspector/`
- `chat.pre_send` dispatch 必须在 `/chat` 和 `/regenerate` 两处都加
- 扩展 settings 由 `on_chat_pre_send` 自行读取，dispatch 不需要注入
- 参考 `test_expand/dashboard/` 的结构和模式

---

### Task 1: conversations.py 新增 chat.pre_send dispatch

**文件：**
- 修改：`backend/app/routes/conversations.py:145-193`（chat 端点）
- 修改：`backend/app/routes/conversations.py:226-260`（regenerate 端点）

**接口：**
- 消费：已构建的 `messages` 变量、`conv_id`、`settings`
- 产出：`dispatcher.dispatch("chat.pre_send", ctx)` 调用，ctx 含 `conversation_id`、`messages`、`settings`

- [ ] **Step 1: 在 chat 端点新增 dispatch**

在 `chat()` 函数中，`messages` 构建完成后、`sse_manager.register` 之前（约第 189 行），新增：

```python
    # ── 扩展钩子：chat.pre_send ──
    from app.extensions import get_extension_manager
    mgr = get_extension_manager()
    mgr.dispatcher.dispatch("chat.pre_send", {
        "conversation_id": conv_id,
        "messages": messages,
        "settings": settings,
    })

    cancel_event = sse_manager.register(conv_id)
```

完整上下文（修改后的 chat 端点关键段）：

```python
    update_conversation(conv_id, {"updated_at": now})

    # 优先使用前端组装的 messages，否则从存储读取
    assembled = body.get("messages")
    if assembled and isinstance(assembled, list) and len(assembled) > 0:
        messages = assembled
    else:
        messages = get_messages_for_chat(conv_id)

    # ── 扩展钩子：chat.pre_send ──
    from app.extensions import get_extension_manager
    mgr = get_extension_manager()
    mgr.dispatcher.dispatch("chat.pre_send", {
        "conversation_id": conv_id,
        "messages": messages,
        "settings": settings,
    })

    cancel_event = sse_manager.register(conv_id)
```

- [ ] **Step 2: 在 regenerate 端点新增 dispatch**

在 `regenerate()` 函数中，`messages` 构建完成后、`sse_manager.register` 之前，新增同样的 dispatch 代码块：

```python
    delete_message(last_assistant_id, conv_id)

    # 优先使用前端组装的 messages，否则从存储读取
    assembled = body.get("messages")
    if assembled and isinstance(assembled, list) and len(assembled) > 0:
        messages = assembled
    else:
        messages = get_messages_for_chat(conv_id)

    # ── 扩展钩子：chat.pre_send ──
    from app.extensions import get_extension_manager
    mgr = get_extension_manager()
    mgr.dispatcher.dispatch("chat.pre_send", {
        "conversation_id": conv_id,
        "messages": messages,
        "settings": settings,
    })

    cancel_event = sse_manager.register(conv_id)
```

- [ ] **Step 3: 运行后端测试验证兼容性**

```bash
cd backend && python -m pytest -v
```

预期：112 PASS（chat.pre_send 尚无 handler 注册，dispatch 空跑，不影响现有行为）

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/conversations.py
git commit -m "feat: /chat 和 /regenerate 新增 chat.pre_send dispatch 调用点"
```

---

### Task 2: 创建扩展文件

**文件：**
- 创建：`test_expand/message-inspector/manifest.json`
- 创建：`test_expand/message-inspector/backend.py`
- 创建：`test_expand/message-inspector/frontend/index.js`

**接口：**
- 产出：`on_chat_pre_send(ctx)` — 扩展钩子 handler
- 产出：`panel()` — 前端面板注册（返回 null，由扩展管理面板根据 manifest.features 自动渲染开关）

- [ ] **Step 1: 创建 manifest.json**

```json
{
  "id": "message-inspector",
  "name": "Message Inspector",
  "version": "1.0.0",
  "description": "在终端打印发送给 AI 的完整 messages 数组",
  "permissions": ["hook:chat"],
  "ext_points": {
    "backend": ["chat.pre_send"],
    "frontend": ["panel"]
  },
  "min_app_version": "1.2.0",
  "features": [
    {
      "id": "print_messages",
      "label": "消息打印",
      "description": "将发送给 AI 的完整 messages 数组以格式化 JSON 输出到后端终端",
      "type": "boolean",
      "default": true
    }
  ]
}
```

写入：`test_expand/message-inspector/manifest.json`

- [ ] **Step 2: 创建 backend.py**

```python
"""
Message Inspector — 后端扩展
在消息发送给 AI 之前，将完整 messages 数组以格式化 JSON 打印到终端。
"""
import json
import os


def on_chat_pre_send(ctx):
    # 读取扩展 settings，检查 print_messages 开关
    try:
        ext_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(ext_dir, "settings.json")
        if os.path.isfile(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            features = settings.get("features", {})
            if not features.get("print_messages", True):
                return
    except Exception:
        pass  # settings 不可用时默认打印

    messages = ctx.get("messages", [])
    conv_id = ctx.get("conversation_id", "?")

    print(f"\n{'=' * 60}")
    print(f"  [Message Inspector] conversation: {conv_id}")
    print(f"  messages count: {len(messages)}")
    print(f"{'=' * 60}")
    print(json.dumps(messages, indent=2, ensure_ascii=False))
    print(f"{'=' * 60}\n")
```

写入：`test_expand/message-inspector/backend.py`

- [ ] **Step 3: 创建 frontend/index.js**

```javascript
/**
 * Message Inspector — 前端扩展
 * 仅注册面板，开关由扩展管理面板根据 manifest.features 自动渲染。
 */
export function panel() {
  return null;
}
```

写入：`test_expand/message-inspector/frontend/index.js`

- [ ] **Step 4: Commit**

```bash
git add test_expand/message-inspector/
git commit -m "feat: 创建 message-inspector 扩展（manifest + backend + frontend）"
```

---

### Task 3: 安装扩展 + 构建验证

- [ ] **Step 1: 通过 API 安装扩展**

扩展系统通过 ZIP 安装或直接复制目录后调用 `/api/extensions/confirm`。对于 `test_expand/` 目录下的扩展，需要先将目录复制到 `user_data/extensions/` 或通过安装 API 注册。

最简单方式：直接复制目录：

```bash
cp -r test_expand/message-inspector user_data/extensions/message-inspector
```

然后通过 API 注册或手动编辑 `.registry.json`：

```bash
cd backend && python -c "
from app.extensions.registry import read_registry, write_registry
reg = read_registry()
reg['message-inspector'] = {'id': 'message-inspector', 'enabled': True}
write_registry(reg)
print('extension registered')
"
```

- [ ] **Step 2: 运行后端测试**

```bash
cd backend && python -m pytest -v
```

预期：112 PASS

- [ ] **Step 3: 构建前端**

```bash
cd frontend && npm run build
```

预期：构建成功

- [ ] **Step 4: 验证扩展已加载**

启动后端后检查日志：

```bash
cd backend && python run.py
# 观察终端输出：
# 扩展初始化完成: {'message-inspector': ...}
```

发送一条消息后，终端应打印格式化 JSON。

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: 安装 message-inspector 扩展 + 构建验证通过"
```
