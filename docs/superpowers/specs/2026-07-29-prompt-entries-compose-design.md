# 提示词条目组合逻辑 — 设计规格

> 日期：2026-07-29 | 状态：草稿 | 依赖：Phase 1 条目 CRUD + Modal 编辑

## 概述

为提示词条目系统实现**消息组装逻辑**，通过新增 `__chat_history__` 特殊占位符条目，让用户可以自由控制提示词条目与对话历史的排列顺序，实现类似 SillyTavern 的灵活提示词组合能力。

## 动机

- Prompt entries 的 CRUD 已完整实现（Phase 1 + Modal），但从未参与消息发送流程
- 用户需要在提示词条目列表中摆放"对话历史"的位置
- 相邻同 role 条目应合并，减少冗余 message 数量

---

## 1. chat_history 特殊条目

| 属性 | 值 | 说明 |
|---|---|---|
| id | `"__chat_history__"` | 硬编码常量，前端通过 id 识别 |
| name | `"对话历史"` | 展示名称 |
| role | 任意值（不影响组装） | 不作为消息 role，仅占位 |
| 存储 | **不存入 JSON 文件** | `get_entries()` 返回时后端自动追加到末尾 |
| 前端表现 | 不可删除、不可禁用、可拖拽排序 | 隐藏 Toggle 和 ✏️ 按钮 |
| reorder | 前端传给后端前过滤掉 | 只传真实条目 ID |

### 后端改动

`storage/prompt_entries.py` 的 `get_entries()`：

```python
def get_entries(preset_id):
    entries = _read_entries(preset_id)
    entries.sort(key=lambda e: e.get("order", 0))
    # 自动追加 chat_history 占位符
    chat_history = {
        "id": "__chat_history__",
        "name": "对话历史",
        "role": "system",
        "content": "",
        "enabled": True,
        "order": len(entries)
    }
    return entries + [chat_history]
```

- 不存文件，每次读取时动态追加
- order 设为当前最大 + 1（即末尾）

---

## 2. 消息组装器（前端）

新增 `frontend/src/composables/useMessageAssembler.js`：

### 接口

```js
function assembleMessages(entries, conversationMessages) → messages[]
```

### 规则

1. entries 按 `order` 排序
2. 过滤 `enabled === false` 的条目
3. 过滤 `role === null` 的条目（开发测试条目，不参与发送）
4. 遍历条目：
   - 遇到 `id === "__chat_history__"` → 展开为 `conversationMessages`
   - 其他条目：相邻同 role 合并（content 用 `\n\n` 分隔）
5. `__chat_history__` 是硬边界：不跨边界合并

### 示例

```
条目列表（排序后）：
  [0] {role:"system", content:"你是助手"}   ─┐
  [1] {role:"system", content:"请用中文"}    ─┘ 合并为一条 system
  [2] __chat_history__                        → 替换为对话历史
  [3] {role:"user",   content:"继续"}         → 独立 user message

最终 messages：
  [{role:"system", content:"你是助手\n\n请用中文"},
   ...对话历史...,
   {role:"user", content:"继续"}]
```

---

## 3. 前端组件改动

### PromptEntryItem.vue

检测 `entry.id === "__chat_history__"`：
- 隐藏 Toggle 开关
- 隐藏 ✏️ 编辑按钮
- 保留拖拽手柄（`:drag-enabled="entry.id !== '__chat_history__'"` 中仍可拖拽）
- 名称前加特殊图标（如 💬）以示区别

### PromptEntryCard.vue

- 卡片中渲染 chat_history 条目时，传入 `isChatHistory` prop 或由 PromptEntryItem 自行判断
- reorder 发送给后端前过滤掉 `__chat_history__`：

```js
const realIds = orderedIds.filter(id => id !== "__chat_history__")
await store.reorderEntries(realIds)
```

### PromptEntryModal.vue

- 打开 Modal 前判断：如果 `entry.id === "__chat_history__"` 则不打开（因编辑按钮已隐藏，兜底）

---

## 4. 发送消息流程集成

在 `InputBar.vue` 或 `ChatStore` 中，发送消息前调用组装器：

```js
import { useMessageAssembler } from "@/composables/useMessageAssembler"
import { usePromptEntriesStore } from "@/stores/promptEntries"

// 组装消息
const promptStore = usePromptEntriesStore()
const assembledMessages = useMessageAssembler(
  promptStore.entries,      // 含 __chat_history__
  conversationMessages       // 当前对话历史
)

// 发送
await chatStore.sendMessage(assembledMessages)
```

---

## 5. 边界情况

| 场景 | 行为 |
|---|---|
| 没有 prompt entries（空预设） | `entries` 只有 `__chat_history__` → 等价于仅发送对话历史 |
| 所有条目都 disabled | 过滤后只剩 `__chat_history__` → 仅发送对话历史 |
| chat_history 在开头 | 对话历史在最前面 |
| chat_history 在末尾 | 对话历史在最后面 |
| chat_history 在中间 | 条目 + 对话历史 + 条目 |
| 两个 chat_history（异常） | 防御：遇到第一个替换，后续再遇到跳过 |

---

## 6. 实现步骤概览

1. 后端：`get_entries()` 追加 `__chat_history__`
2. 前端：新建 `useMessageAssembler.js`
3. 前端：`PromptEntryItem.vue` 适配 chat_history 表现
4. 前端：`PromptEntryCard.vue` reorder 过滤
5. 前端：发送流程集成组装器
6. 后端测试：验证 get_entries 返回含 chat_history
7. 构建验证

---

## 参考

- `docs/superpowers/specs/2026-07-28-prompt-entries-design.md` — Phase 1 设计
- `docs/superpowers/specs/2026-07-29-prompt-entry-modal-design.md` — Modal 编辑设计
- SillyTavern 提示词系统（需求来源）
