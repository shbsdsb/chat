# Message Inspector 扩展 — 设计规格

> 日期：2026-07-29 | 状态：草稿 | 依赖：chat.pre_send 钩子（需新增 dispatch 调用点）

## 概述

开发 `message-inspector` 扩展：在消息发送给 AI 之前，将组装后的完整 `messages` 数组以格式化 JSON 打印到后端终端。带前端开关控制是否打印。

## 动机

- 用户无法直观看到前端组装后的 messages（含 prompt entries + 对话历史）实际内容
- 调试提示词组合效果需要透明化发送给 AI 的完整输入

---

## 1. 扩展结构

```
test_expand/message-inspector/
├── manifest.json
├── backend.py
└── frontend/
    └── index.js
```

---

## 2. manifest.json

```json
{
  "id": "message-inspector",
  "name": "Message Inspector",
  "version": "1.0.0",
  "permissions": ["hook:chat"],
  "ext_points": {
    "backend": ["chat.pre_send"],
    "frontend": ["panel"]
  },
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

- `chat.pre_send`：后端钩子，在 messages 发送给 AI 之前触发
- `panel`：前端扩展点，在扩展管理面板中显示
- `features[0]`：前端开关，控制是否打印

---

## 3. backend.py

### `on_chat_pre_send(ctx)`

```python
import json


def on_chat_pre_send(ctx):
    # 读取扩展 settings 中的开关
    ext_settings = ctx.get("_extension_settings", {})
    if not ext_settings.get("print_messages", True):
        return

    messages = ctx.get("messages", [])
    conv_id = ctx.get("conversation_id", "?")

    print(f"\n{'=' * 60}")
    print(f"  [Message Inspector] conversation: {conv_id}")
    print(f"  messages count: {len(messages)}")
    print(f"{'=' * 60}")
    print(json.dumps(messages, indent=2, ensure_ascii=False))
    print(f"{'=' * 60}\n")
```

### ctx 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `conversation_id` | str | 会话 ID |
| `messages` | list | 组装后的完整消息数组 `[{role, content}]` |
| `settings` | dict | API 设置 |
| `_extension_settings` | dict | 扩展自身的 settings（由 dispatch 时注入） |

---

## 4. frontend/index.js

纯前端面板注册，让扩展在管理面板中可见并支持开关：

```javascript
// 向扩展管理面板注册自身（panel 扩展点）
export function panel() {
  // 无需自定义 UI，扩展管理面板自动根据 manifest.features 渲染开关
  return null;
}
```

`manifest.features` 会被扩展管理面板自动解析为开关。

---

## 5. 后端改动：新增 chat.pre_send dispatch

### 文件：`backend/app/routes/conversations.py`

在 `/chat` 端点（`_stream_and_save` 调用前）和 `/regenerate` 端点分别新增：

```python
# dispatch chat.pre_send 钩子（扩展可在发送前检查和打印 messages）
ext_mgr = current_app.extensions.get("extension_manager")
if ext_mgr:
    ext_settings = {}
    try:
        ext_settings = ext_mgr.get_settings("message-inspector")
    except Exception:
        pass
    ext_mgr.dispatcher.dispatch("chat.pre_send", {
        "conversation_id": conv_id,
        "messages": messages,
        "settings": settings,
        "_extension_settings": ext_settings,
    })
```

### 注入点

- `/chat`：在 `messages` 构建后、`sse_manager.register` 之前（约第 185 行）
- `/regenerate`：同上位置

### 获取 ExtensionManager

使用 `flask.current_app.extensions`，与 `_stream_and_save` 中已有的 `mgr = current_app.extensions.get("extension_manager")` 模式一致（见 conversations.py:76-78）。

---

## 6. 边界情况

| 场景 | 行为 |
|---|---|
| 扩展未安装 | ext_mgr.get_settings 抛异常 → 静默跳过 dispatch |
| 扩展已安装但未启用 | loader 不会加载 backend.py，dispatch 无 handler → 无输出 |
| 开关关闭 | on_chat_pre_send 检查 settings → return 不打印 |
| messages 为空 | 正常打印空数组 `[]` |
| JSON 序列化失败 | try/except 包裹，fallback 打印 repr |

---

## 7. 实现步骤概览

1. 后端：`conversations.py` 新增 `chat.pre_send` dispatch（/chat + /regenerate）
2. 创建扩展目录和 `manifest.json`
3. 创建 `backend.py`（`on_chat_pre_send` 实现）
4. 创建 `frontend/index.js`
5. 安装扩展到扩展系统
6. 构建 + 测试验证

---

## 参考

- `Plugin_Development_Guide.md` — 扩展开发指南
- `test_expand/dashboard/` — 扩展示例
- `backend/app/extensions/hooks.py` — HookDispatcher
- `backend/app/extensions/loader.py` — 扩展加载器
