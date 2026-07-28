# 提示词条目编辑 Modal — 设计规格

> 日期：2026-07-29 | 状态：草稿 | 依赖：Phase 1 条目列表管理

## 概述

为提示词条目增加编辑功能。点击条目的 ✏️ 按钮弹出 Modal，可编辑条目名称、消息归属角色和提示词内容，支持保存和删除。

## 数据结构扩展

在现有 `{id, name, enabled, order}` 基础上增加两个字段：

```json
{
  "id": "uuid-1",
  "name": "双人成行",
  "content": "你现在扮演一个角色...",
  "role": null,
  "enabled": true,
  "order": 0
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `content` | string | `""` | 提示词文本内容 |
| `role` | string\|null | `null` | 消息归属：`null`=无，`"system"`=系统，`"user"`=用户，`"assistant"`=AI消息 |

## 组件设计

### PromptEntryModal.vue（新建）

基于 `BaseDialog` 的 Modal 组件。

**Props：**
- `visible: Boolean` — 是否显示
- `entry: Object` — 当前编辑的条目（含 id, name, content, role）

**Emits：**
- `close` — 关闭 Modal
- `save(formData)` — 保存，携带 `{name, content, role}`
- `delete(entryId)` — 删除

**布局：**

```
┌─────────────────────────────────┐
│  名称         [输入框]          │
│  消息归属     [下拉选择]        │
│                                 │
│  提示词内容                     │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │   (大文本输入框)          │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
│  [✕ 取消]    [删除]  [保存]    │
└─────────────────────────────────┘
```

- 名称输入框：普通 `<input>`，绑定 `name`
- 消息归属：`<select>` 下拉，选项为 `无(null)` / `系统(system)` / `用户(user)` / `AI消息(assistant)`
- 提示词内容：`<textarea>`（≥6 行），绑定 `content`
- 按钮：取消（左侧，dialog-btn-cancel）、删除（中间，dialog-btn-danger）、保存（右侧，dialog-btn-ok）

**内部状态：**
- 用 `reactive({ name, content, role })` 副本编辑，保存时才写回
- `watch(visible)` 在打开时从 `entry` prop 初始化表单

**删除确认：**
- 点击删除 → 弹出第二个 BaseDialog（无标题，危险样式）
- 文案："确定要删除条目「{name}」吗？此操作不可撤销。"
- 确认后 emit `delete`，取消则回到编辑 Modal

### PromptEntryCard.vue 改动

- 新增 `editingEntry` ref（当前编辑的条目对象）
- 监听 `PromptEntryItem` 的 `@edit` 事件 → 设置 `editingEntry` + 打开 Modal
- `@save` → 调用 `store.updateEntry(id, {name, content, role})` + 关闭 Modal
- `@delete` → 调用 `store.deleteEntry(id)` + 关闭 Modal

### PromptEntryItem.vue

- 无需改动，edit emit 已有

## 后端改动

### storage/prompt_entries.py

- `create_entry()` 新增默认字段 `content: ""`, `role: null`
- `update_entry()` 已透传 `data` 字典，无需改动

### routes/prompt_entries.py

- 无需改动（PUT 路由已透传 body 到 update_entry）

## 实现步骤

1. 后端：`create_entry` 添加 content/role 默认值
2. 后端测试：更新测试验证新字段
3. 前端：创建 `PromptEntryModal.vue`
4. 前端：`PromptEntryCard.vue` 集成 Modal
5. 构建验证
