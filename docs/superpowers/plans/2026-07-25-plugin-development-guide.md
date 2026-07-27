# Plugin Development Guide 文档重构 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Plugin_Development_Guide.md 重构为三部分混合模式文档（Quick Start + 主题参考 + 注意事项），供熟悉 Vue 3/Flask 的开发者快速上手扩展开发。

**Architecture:** 单文件 Markdown 文档，内容全部内嵌，引用现有 `test_expand/dashboard/` 为参考。原文档内容精简整合到第三部分。

**Tech Stack:** Markdown，无代码依赖。

## Global Constraints

- 目标读者：熟悉 Vue 3（组合式 API、h 渲染函数、Pinia）和 Flask（Blueprint），但未接触过本项目的扩展系统
- 代码全部内嵌在文档中，不创建新的示例扩展目录
- 原 `Plugin_Development_Guide.md` 内容整合到第三部分，不丢失任何检查项
- 所有 API 名称、文件路径、属性名必须与源码一致
- 预计总行数：1800-2500 行 Markdown

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `Plugin_Development_Guide.md` | 覆盖重写 | 完整的三部分扩展开发文档 |
| `docs/superpowers/specs/2026-07-25-plugin-development-guide-design.md` | 只读参考 | 设计规格 |

## Key Source Files to Reference

| 文件 | 用途 |
|------|------|
| `test_expand/dashboard/manifest.json` | 确认 manifest 真实字段 |
| `test_expand/dashboard/backend.py` | 确认钩子 ctx 结构、路由注册模式 |
| `test_expand/dashboard/frontend/index.js` | 确认组件注册模式 |
| `test_expand/dashboard/frontend/components/DashboardFloating.js` | 确认 h() 渲染函数写法 |
| `backend/app/extensions/loader.py` | 确认 EXT_POINT_TO_FUNC 映射和 load_extension 流程 |
| `backend/app/extensions/permissions.py` | 确认权限常量列表 |
| `frontend/src/extensions/useExtensionApi.js` | 确认 API 方法签名 |
| `frontend/src/main.js` | 确认 __EXT_VUE__ 注入的准确 API 列表 |
| `backend/app/extensions/hooks.py` | 确认 HookDispatcher 超时和行为 |

---

### Task 1: 撰写 Part 1 — Quick Start（约 500 行）

**Files:**
- Modify: `Plugin_Development_Guide.md`（新建/覆盖）

**Interfaces:**
- Produces: 文档 1.1 ~ 1.3 节，引入扩展系统概念并完成 Hello World

- [ ] **Step 1: 撰写 1.1 什么是扩展系统**

在文件开头写入标题和简介部分：

```markdown
# 插件（扩展）开发指南

> 本文档教你如何为 Chat 应用开发扩展。扩展是运行在应用内的独立功能模块，可以注入 UI 面板、监听 AI 响应、注册自定义 API 路由。

## 第一部分：快速入门

### 1.1 什么是扩展系统

扩展系统是 Chat 应用的内置插件框架。一个扩展由三个部分组成：

- **manifest.json** — 声明文件，定义扩展的 ID、版本、权限和使用的扩展点
- **backend.py** — 后端逻辑（可选），注册生命周期钩子或自定义 API 路由
- **frontend/** — 前端 UI（可选），使用 Vue 3 渲染函数编写界面组件

扩展能做什么？
| 能力 | 说明 |
|------|------|
| 注入面板 | 在应用界面的指定位置渲染自定义 UI（如悬浮窗、侧边栏） |
| 监听 AI 响应 | 在 AI 回复完成后执行自定义逻辑（如统计 token、记录日志） |
| 注册 API 路由 | 添加自定义后端接口，供前端扩展调用 |
| 读写数据 | 在自己的存储目录中持久化 JSON 数据 |

**加载流程一图胜千言：**

\`\`\`
开发者编写扩展 → 放入 test_expand/ 或通过 ZIP/Git 安装
     ↓
.registry.json 注册（enabled: true 驱动加载）
     ↓
Flask 启动时：ExtensionManager 遍历注册表 → import backend.py → 注册钩子/路由
Vue 启动时：ExtensionSlot 拉取 frontend/ JS → 注入 <script> → 组件渲染
\`\`\`

> 接下来用 5 分钟创建一个 Hello World 扩展，你会直观理解整个流程。
```

- [ ] **Step 2: 验证 1.1 节**

检查：概念准确（三部分结构）、加载流程图正确、无与源码矛盾的描述。

- [ ] **Step 3: 撰写 1.2 5 分钟 Hello World**

```markdown
### 1.2 5 分钟 Hello World

创建一个最小可运行的扩展，在应用界面上显示 "Hello World!" 面板。

#### Step 1：创建目录和 manifest.json

在 `test_expand/hello-world/` 下创建：

\`\`\`json
// test_expand/hello-world/manifest.json
{
  "id": "hello-world",
  "name": "Hello World",
  "version": "1.0.0",
  "description": "我的第一个扩展",
  "permissions": [],
  "ext_points": {
    "backend": [],
    "frontend": ["panel"]
  },
  "min_app_version": "1.2.0"
}
\`\`\`

| 字段 | 这里的含义 |
|------|-----------|
| `id` | 唯一标识，必须与目录名一致 |
| `permissions` | 因为没有后端逻辑，无需权限 |
| `ext_points.frontend` | `["panel"]` 表示要在全局面板插槽渲染 |
| `ext_points.backend` | `[]` 表示不使用后端钩子 |

#### Step 2：创建占位 backend.py

即使不使用后端逻辑，也需要创建一个空的 `backend.py`（扩展加载器要求此文件存在）：

\`\`\`python
# test_expand/hello-world/backend.py
# 本扩展无后端逻辑，仅需此文件满足加载要求
\`\`\`

#### Step 3：编写前端组件 frontend/index.js

\`\`\`javascript
// test_expand/hello-world/frontend/index.js
(function() {
  const { h, ref, onMounted } = window.__EXT_VUE__;

  const HelloPanel = {
    props: ['api'],
    setup(props) {
      const count = ref(0);

      onMounted(() => {
        console.log('[hello-world] 面板已挂载');
      });

      return () => h('div', {
        style: {
          padding: '16px',
          background: '#f0f9ff',
          border: '2px solid #0ea5e9',
          borderRadius: '8px',
          margin: '8px'
        }
      }, [
        h('h3', { style: { margin: '0 0 8px' } }, 'Hello World! 🎉'),
        h('p', { style: { margin: '0 0 8px' } }, '我的第一个扩展运行成功！'),
        h('button', {
          onClick: () => count.value++,
          style: {
            padding: '4px 12px',
            background: '#0ea5e9',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }
        }, `点击了 ${count.value} 次`)
      ]);
    }
  };

  // 注册到全局注册表
  if (!window.__EXTENSION_REGISTRY__) {
    window.__EXTENSION_REGISTRY__ = {};
  }
  window.__EXTENSION_REGISTRY__['hello-world'] = {
    panel: [HelloPanel]
  };
})();
\`\`\`

**关键点解释：**

| 要点 | 说明 |
|------|------|
| IIFE 包裹 | `(function() { ... })()` 隔离作用域，避免污染全局 |
| `window.__EXT_VUE__` | 应用注入的 Vue API，包含 `h, ref, computed, watch, onMounted, onBeforeUnmount` |
| `props: ['api']` | 接收 ExtensionSlot 传入的 `api` 对象，用于访问应用 Store |
| `h()` 渲染函数 | Vue 3 渲染函数，等价于 `<template>` 的编译结果 |
| 注册表 key | `'hello-world'` 必须与 `manifest.json` 中的 `id` 完全一致 |
| 插槽 key | `panel` 对应 `ext_points.frontend` 中声明的扩展点 |

#### Step 4：同步到运行时目录

扩展开发在 `test_expand/` 下进行，运行时从 `user_data/extensions/` 加载。需要将扩展复制过去：

\`\`\`bash
# Windows (PowerShell)
Copy-Item -Recurse test_expand/hello-world user_data/extensions/hello-world

# macOS / Linux
cp -r test_expand/hello-world user_data/extensions/hello-world
\`\`\`

#### Step 5：注册到 .registry.json

编辑 `user_data/extensions/.registry.json`，添加：

\`\`\`json
{
  "hello-world": {
    "id": "hello-world",
    "enabled": true,
    "installed_at": "2026-07-25T00:00:00",
    "permissions_granted": []
  }
}
\`\`\`

> 如果 `.registry.json` 中已有其他扩展，在 JSON 对象中追加即可（不要覆盖整个文件）。

#### Step 6：验证

重启应用（或刷新前端页面），你应该看到蓝色边框的 "Hello World!" 面板。

**如果没出现，依次检查：**

1. DevTools Console 是否有报错
2. `.registry.json` 中 `enabled` 是否为 `true`
3. `App.vue` 是否 import 了 `<ExtensionSlot name="panel" />`
4. 浏览器 DevTools Network 面板：`/api/extensions/hello-world/frontend` 是否返回 200

---

> 🎉 恭喜！你已完成第一个扩展。下面深入了解每个模块的细节。
```

- [ ] **Step 4: 验证 1.2 节**

检查：所有代码与实际 API 一致、manifest 字段与 installer/loader 校验逻辑吻合、file 路径正确。

- [ ] **Step 5: 撰写 1.3 目录结构速览**

```markdown
### 1.3 目录结构速览

\`\`\`
chat/
├── test_expand/                    ← 📝 开发工作目录（你在这里写代码）
│   └── <extension_id>/
│       ├── manifest.json           ← 声明：ID、版本、扩展点、权限
│       ├── backend.py              ← 后端：钩子 + 自定义 API 路由
│       └── frontend/
│           ├── index.js            ← 入口：将组件注册到全局注册表
│           └── components/         ← 组件目录（可选）
│               └── *.js
│
├── user_data/extensions/           ← 🏃 运行时目录（应用实际加载）
│   ├── .registry.json              ← 注册表：enabled: true 才会被加载
│   └── <extension_id>/
│       └── ...（与 test_expand 内结构相同）
\`\`\`

| 目录 | 用途 |
|------|------|
| `test_expand/` | 开发目录，你在这里写代码和调试 |
| `user_data/extensions/` | 运行时目录，Flask 和前端只从这里加载扩展 |
| `.registry.json` | 注册表，记录了所有扩展的启用状态和授权权限 |

> ⚠️ 两个目录各自独立。修改 `test_expand/` 后必须手动同步到 `user_data/extensions/`，否则不会生效。
```

- [ ] **Step 6: 验证 1.3 节**

检查：目录结构与实际项目一致。

- [ ] **Step 7: Commit Part 1**

\`\`\`bash
git add Plugin_Development_Guide.md
git commit -m "docs: add Part 1 — Quick Start for plugin development guide"
\`\`\`

---

### Task 2: 撰写 Part 2.1-2.2 — 架构总览 + manifest.json 规范（约 350 行）

**Files:**
- Modify: `Plugin_Development_Guide.md`（追加 Part 2 开头）

**Interfaces:**
- Consumes: Part 1 建立的文档结构和术语
- Produces: 2.1 节（全链路架构图）和 2.2 节（manifest.json 完整字段表）

- [ ] **Step 1: 撰写 2.1 架构总览**

在 Part 1 之后追加：

```markdown
---

## 第二部分：主题参考

### 2.1 架构总览

在深入每个模块之前，先看一张全链路图——了解扩展从注册到运行的全过程。

#### 后端加载流程

\`\`\`
Flask 启动 (create_app)
  └→ ExtensionManager.init(api_bp)
       └→ load_all_enabled()
            └→ 遍历 .registry.json 中 enabled 为 true 的扩展
                 └→ load_extension(ext_id, dispatcher, api_bp)
                      ├→ importlib 动态加载 backend.py
                      ├→ 读取 manifest.json 的 ext_points.backend
                      ├→ 若含 api_route → 调用 register_api_routes(api_bp)
                      └→ 若含 chat.post_receive → dispatcher.register_hook()
\`\`\`

#### 前端加载流程

\`\`\`
Vue 应用启动 (main.js)
  └→ App.vue 中的 <ExtensionSlot name="panel" />
       └→ onMounted：遍历扩展列表
            ├→ fetch(/api/extensions/<id>/frontend) → 获取 JS 代码
            ├→ 以 <script> 标签注入 DOM
            │    └→ index.js 执行 → 写入 window.__EXTENSION_REGISTRY__
            └→ 从注册表取出匹配 slot 的组件
                 └→ markRaw() 防止深度反应化
                 └→ shallowRef() 浅层引用
                 └→ <component :is> 渲染，传入 props.api
\`\`\`

#### 钩子触发流程

\`\`\`
AI 响应完成 (conversations.py)
  └→ 构造 hook_ctx = { conv_id, messages, last_message, settings }
       └→ dispatcher.dispatch("chat.post_receive", hook_ctx)
            └→ 线程池执行每个扩展的 on_chat_post_receive(ctx)
                 ├→ 超时限制：30 秒
                 ├→ 异常隔离：单个扩展报错不影响其他
                 └→ 返回值合并到消息的 extensions 字段
\`\`\`

#### 核心模块一览

| 模块 | 文件位置 | 作用 |
|------|----------|------|
| ExtensionManager | `backend/app/extensions/__init__.py` | 单例管理器，init() 驱动全量加载，reload_extension() 热重载 |
| loader | `backend/app/extensions/loader.py` | 读取 manifest，动态加载 backend.py，按映射注册扩展点 |
| HookDispatcher | `backend/app/extensions/hooks.py` | 钩子调度器，dispatch() 用线程池并发执行，30s 超时 |
| registry | `backend/app/extensions/registry.py` | .registry.json 的 CRUD，线程安全（threading.Lock） |
| installer | `backend/app/extensions/installer.py` | ZIP/Git 安装，manifest 校验，权限验证 |
| permissions | `backend/app/extensions/permissions.py` | 权限常量定义与验证 |
| ExtensionSlot | `frontend/src/extensions/ExtensionSlot.vue` | Vue 插槽组件，动态加载 JS 并渲染扩展组件 |
| useExtensionApi | `frontend/src/extensions/useExtensionApi.js` | 扩展安全访问 Pinia Store 的封装 |
| extensions Store | `frontend/src/stores/extensions.js` | 扩展列表、安装/卸载/启停等操作的状态管理 |
| extensions API | `frontend/src/api/extensions.js` | 前端对 /api/extensions 的 HTTP 请求封装 |
| ExtensionManager 组件 | `frontend/src/components/ExtensionManager.vue` | 扩展管理面板 UI |
```

- [ ] **Step 2: 验证 2.1 节**

对照以下源文件确认流程图和模块描述准确：
- `backend/app/extensions/loader.py` — EXT_POINT_TO_FUNC 映射
- `backend/app/extensions/hooks.py` — dispatch 超时
- `frontend/src/extensions/ExtensionSlot.vue` — markRaw/shallowRef 逻辑

- [ ] **Step 3: 撰写 2.2 manifest.json 完整规范**

```markdown
### 2.2 manifest.json 完整规范

manifest.json 是扩展的声明文件，应用通过它了解扩展的身份、需求和能力。

#### 必填字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | 字母数字下划线连字符，1-64 字符，与目录名一致 | 扩展唯一标识 |
| `name` | string | 任意 | 扩展显示名称 |
| `version` | string | 语义化版本（如 `"1.0.0"`） | 版本号 |
| `permissions` | string[] | 见下方权限表 | 声明扩展所需权限 |
| `ext_points` | object | `{ backend: string[], frontend: string[] }` | 声明使用的扩展点 |
| `min_app_version` | string | 语义化版本 | 最低兼容的应用版本 |

#### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | 简要描述，在扩展管理面板中展示 |
| `author` | string | 作者名 |
| `homepage` | string | 项目主页 URL |

#### 扩展点 (ext_points)

##### ext_points.backend — 后端扩展点

| 扩展点 | 需实现的函数 | 触发时机 |
|--------|-------------|----------|
| `chat.post_receive` | `on_chat_post_receive(ctx)` | AI 回复完成后 |
| `chat.pre_send` | `on_chat_pre_send(ctx)` | 消息发送前（已注册映射，暂未 dispatch） |
| `api_route` | `register_api_routes(app)` | Flask 启动时，传入 Blueprint 对象 |

##### ext_points.frontend — 前端扩展点

| 扩展点 | 插槽名 | 渲染位置 | 说明 |
|--------|--------|----------|------|
| `panel` | `"panel"` | App.vue 中 `<ExtensionSlot name="panel" />` | 全局面板（如 Dashboard 悬浮窗） |
| `message_decorator` | `"message_decorator"` | 每条消息下方（预留） | 消息装饰器 |

#### 权限列表

| 权限 | 说明 | 典型场景 |
|------|------|----------|
| `read:conversations` | 读取会话列表 | 统计分析、会话管理 |
| `read:messages` | 读取消息内容 | Token 统计、内容分析 |
| `write:messages` | 写入/修改消息 | 消息增强、自动回复 |
| `hook:chat` | 注册聊天钩子 | 使用 `chat.post_receive` / `chat.pre_send` 时必需 |
| `api:route` | 注册自定义 API 路由 | 使用 `api_route` 扩展点时必需 |
| `storage:read` | 读取扩展存储 | 读取持久化数据 |
| `storage:write` | 写入扩展存储 | 保存统计数据、配置等 |

#### 完整示例

以 Dashboard 扩展为例，展示一个使用全部扩展点的 manifest：

\`\`\`json
{
  "id": "dashboard",
  "name": "Dashboard",
  "version": "1.0.0",
  "description": "悬浮面板，统计 token 用量",
  "permissions": ["read:conversations", "hook:chat"],
  "ext_points": {
    "backend": ["chat.post_receive", "api_route"],
    "frontend": ["panel"]
  },
  "min_app_version": "1.2.0"
}
\`\`\`

> 权限必须与 `.registry.json` 中的 `permissions_granted` 一致，否则安装时校验不通过。
```

- [ ] **Step 4: 验证 2.2 节**

对照以下文件确认字段和权限：
- `backend/app/extensions/permissions.py` — 权限常量
- `backend/app/extensions/installer.py` — `_validate_manifest()` 校验逻辑
- `backend/app/extensions/loader.py` — `EXT_POINT_TO_FUNC` 映射

- [ ] **Step 5: Commit Part 2.1-2.2**

\`\`\`bash
git add Plugin_Development_Guide.md
git commit -m "docs: add Part 2.1-2.2 — architecture overview and manifest.json spec"
\`\`\`

---

### Task 3: 撰写 Part 2.3 — 后端开发（约 450 行）

**Files:**
- Modify: `Plugin_Development_Guide.md`（追加 2.3 节）

**Interfaces:**
- Consumes: 2.1 架构中的术语（HookDispatcher, Blueprint），2.2 中的扩展点声明
- Produces: 2.3.1 ~ 2.3.4 节

- [ ] **Step 1: 查阅源码确认钩子 ctx 结构**

阅读以下文件并记录准确的 ctx 字段：
- `backend/app/routes/conversations.py` — 搜索 `hook_ctx` 构造处
- `test_expand/dashboard/backend.py` — 看 `on_chat_post_receive` 如何使用 ctx

- [ ] **Step 2: 撰写 2.3.1 生命周期钩子详解**

```markdown
### 2.3 后端开发

#### 2.3.1 生命周期钩子详解

钩子是扩展介入应用行为的入口。实现对应的函数即可。

##### chat.post_receive — AI 响应完成后触发

在 manifest 中声明 `ext_points.backend: ["chat.post_receive"]`，然后在 backend.py 中实现：

\`\`\`python
# backend.py
def on_chat_post_receive(ctx):
    """
    AI 回复完成后调用。每个扩展独立执行，互不影响。

    ctx 结构（dict）：
    {
        "conv_id": str,          # 会话 ID
        "messages": [            # 完整消息历史
            {
                "role": "user" | "assistant",
                "content": str,
                "id": str,
                "timestamp": str
            },
            ...
        ],
        "last_message": {        # 刚完成的 AI 回复（messages 的最后一条）
            "role": "assistant",
            "content": "...",
            "id": str,
            "timestamp": str
        },
        "settings": {            # 当前使用的预设配置
            "api_key": "sk-...",
            "base_url": "https://...",
            "model": "gpt-4",
            ...
        }
    }

    返回值（可选）：dict，会合并到前端消息对象的 extensions 数组中
    """
    conv_id = ctx["conv_id"]
    last_msg = ctx["last_message"]

    # 示例：统计 token 数量
    token_count = len(last_msg.get("content", "").split())

    # 写入自己的数据文件（见 2.3.3 数据持久化）
    _save_stats(conv_id, {"tokens": token_count})

    # 返回值会出现在前端消息中
    return {"token_count": token_count}
\`\`\`

**行为规范：**

| 行为 | 说明 |
|------|------|
| 超时 | 30 秒，超时后强制中断 |
| 异常处理 | 单个扩展报错不影响其他扩展，错误会写入日志 |
| 返回值 | 可选，若返回 dict，会以 `{ extension_id: {...} }` 格式合并到消息的 `extensions` 字段 |
| 线程安全 | 使用 threading.Lock 保护文件写入（参考 2.3.3） |

> ⚠️ 不要在钩子中执行耗时操作（如调用外部 API 且不设超时）。30 秒超时后会中断，且可能影响后续扩展的执行调度。

##### chat.pre_send — 消息发送前触发

在 manifest 中声明 `ext_points.backend: ["chat.pre_send"]`：

\`\`\`python
def on_chat_pre_send(ctx):
    """
    消息发送给 AI 前调用。

    ctx 结构：
    {
        "conv_id": str,
        "messages": [...],        # 当前消息历史
        "pending_message": {...}, # 即将发送的消息
        "settings": {...},
    }

    返回值可修改 pending_message 的内容。
    """
    # 示例：在发送前添加系统提示
    pending = ctx["pending_message"]
    pending["content"] = "[系统提示：请用中文回答]\n" + pending["content"]
    return {"modified": True}
\`\`\`

> ⚠️ 此钩子已定义映射但暂未在代码中 dispatch，当前不会触发。后续版本将启用。
```

- [ ] **Step 3: 查阅源码确认路由注册模式**

阅读 `test_expand/dashboard/backend.py` 中 `register_api_routes` 的实现。

- [ ] **Step 4: 撰写 2.3.2 自定义 API 路由**

```markdown
#### 2.3.2 自定义 API 路由

在 manifest 中声明 `ext_points.backend: ["api_route"]`，实现 `register_api_routes(app)`：

\`\`\`python
# backend.py
import re
from flask import request, jsonify

# 输入校验正则（白名单）
_CONV_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')

def _validate_conv_id(conv_id):
    return bool(_CONV_ID_PATTERN.match(conv_id))

def register_api_routes(app):
    """app 是 Blueprint 对象，不是 Flask 实例"""

    @app.route("/ext/<ext_id>/metrics", methods=["GET"])
    def get_metrics(ext_id):
        conv_id = request.args.get("conv_id", "")
        if not _validate_conv_id(conv_id):
            return jsonify({"code": 400, "message": "invalid conv_id"}), 400

        data = _read_metrics(conv_id)
        return jsonify({"code": 0, "data": data})

    @app.route("/ext/<ext_id>/metrics", methods=["POST"])
    def save_metrics(ext_id):
        body = request.get_json(silent=True) or {}
        conv_id = body.get("conv_id", "")
        if not _validate_conv_id(conv_id):
            return jsonify({"code": 400, "message": "invalid conv_id"}), 400

        _write_metrics(conv_id, body.get("data", {}))
        return jsonify({"code": 0})
\`\`\`

**路由注册四要诀：**

| 要诀 | 说明 | 错误示例 |
|------|------|----------|
| **路由不加 `/api` 前缀** | Blueprint 已有 `url_prefix="/api"`，最终路径自动拼接为 `/api/ext/...` | `@app.route("/api/ext/...")` |
| **校验动态参数** | 所有来自 URL 或请求体的参数，必须用正则白名单校验 | 直接 `open(path + conv_id)` |
| **统一响应格式** | 成功 `{"code": 0, "data": ...}`，失败 `{"code": 非0, "message": "..."}` | 直接 return dict |
| **异常兜底** | JSON 解析和文件读写必须 try/except（见 2.3.3） | 裸 `json.load()` |
\`\`\`
```

- [ ] **Step 5: 撰写 2.3.3 数据持久化**

```markdown
#### 2.3.3 数据持久化

扩展有自己的存储目录：`user_data/ext_data/<ext_id>/`。以下是推荐的数据读写封装：

\`\`\`python
import json
import os
import threading

# 存储根目录
_STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "user_data", "ext_data"
)

# 每个扩展一个专属子目录
def _get_ext_dir(ext_id):
    dir_path = os.path.join(_STORAGE_DIR, ext_id)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def _get_file_path(ext_id, filename):
    return os.path.join(_get_ext_dir(ext_id), filename)

# 线程安全的 JSON 读写
_lock = threading.Lock()

def _read_json(ext_id, filename, default=None):
    path = _get_file_path(ext_id, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, FileNotFoundError):
        return default

def _write_json(ext_id, filename, data):
    path = _get_file_path(ext_id, filename)
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
\`\`\`

**文件命名建议：** 以会话 ID 为文件名，如 `<conv_id>_stats.json`，便于按会话隔离数据。
```

- [ ] **Step 6: 撰写 2.3.4 后端 API 参考**

查阅 `backend/app/storage.py` 确认准确的函数签名后写入：

```markdown
#### 2.3.4 后端 API 参考

扩展的 backend.py 中可直接 import 以下应用内部函数：

| 函数 | 来源 | 签名 | 用途 |
|------|------|------|------|
| `get_conversation(conv_id)` | `app.storage` | `str -> dict \| None` | 读取会话元数据（标题、创建时间等） |
| `get_messages(conv_id)` | `app.storage` | `str -> list[dict]` | 读取会话的完整消息列表 |
| `get_all_settings()` | `app.storage` | `() -> list[dict]` | 读取所有预设配置列表 |
| `get_setting(preset_id)` | `app.storage` | `str -> dict \| None` | 读取单个预设配置 |
| `save_setting(preset_id, data)` | `app.storage` | `(str, dict) -> None` | 保存预设配置 |

\`\`\`python
# 用法示例
from app.storage import get_messages, get_conversation

def on_chat_post_receive(ctx):
    conv = get_conversation(ctx["conv_id"])
    msgs = get_messages(ctx["conv_id"])
    # ...
\`\`\`

> 前端 Store 访问请参见 2.4.3 useExtensionApi。
```

- [ ] **Step 7: 验证 2.3 节**

确认：ctx 结构与 conversations.py 中构造一致、路由注册模式与 dashboard/backend.py 一致、storage.py 函数签名准确。

- [ ] **Step 8: Commit Part 2.3**

\`\`\`bash
git add Plugin_Development_Guide.md
git commit -m "docs: add Part 2.3 — backend development (hooks, routes, persistence, API ref)"
\`\`\`

---

### Task 4: 撰写 Part 2.4 — 前端开发（约 500 行）

**Files:**
- Modify: `Plugin_Development_Guide.md`（追加 2.4 节）

**Interfaces:**
- Consumes: Part 1 中的 __EXT_VUE__ 概念，2.2 中的前端扩展点
- Produces: 2.4.1 ~ 2.4.5 节

- [ ] **Step 1: 查阅源码确认前端 API**

阅读以下文件确认准确 API：
- `frontend/src/main.js` — __EXT_VUE__ 注入的具体 API 列表
- `frontend/src/extensions/useExtensionApi.js` — 所有方法签名和返回值
- `frontend/src/extensions/ExtensionSlot.vue` — 组件加载和 props 传递

- [ ] **Step 2: 撰写 2.4.1 技术栈说明**

```markdown
### 2.4 前端开发

#### 2.4.1 技术栈说明

扩展前端使用**纯 JavaScript**编写（非 Vue SFC），通过 Vue 3 渲染函数构建界面。

| 层 | 技术 | 说明 |
|----|------|------|
| 渲染 | Vue 3 `h()` 函数 | 创建 VNode，等价于 `<template>` 的编译结果 |
| 响应式 | `window.__EXT_VUE__` | 应用注入的 Vue API 子集 |
| 状态 | Pinia（通过 `props.api`） | 不直接 import store，通过 ExtensionSlot 传入的 api 对象访问 |
| 样式 | 内联 `style` 对象 | 写在 JS 中，无构建步骤 |
| 注册 | `window.__EXTENSION_REGISTRY__` | 全局组件注册表，按 ext_id 和 slot 名组织 |

**`window.__EXT_VUE__` 包含的 API：**

\`\`\`javascript
// 由 main.js 在应用启动时注入
window.__EXT_VUE__ = {
  h,                // Vue 渲染函数
  ref,              // 响应式引用
  computed,         // 计算属性
  watch,            // 侦听器
  onMounted,        // 挂载钩子
  onBeforeUnmount   // 卸载前钩子
};
\`\`\`

**为什么用 h() 函数而不是 .vue SFC？**

扩展组件以纯 `.js` 文件运行，不经过 Vite 编译。`h()` 函数是 Vue 3 的底层渲染 API，可以在运行时直接创建组件，无需编译步骤。

**参考模板：** `test_expand/dashboard/frontend/components/DashboardFloating.js`
```

- [ ] **Step 3: 撰写 2.4.2 组件注册机制**

```markdown
#### 2.4.2 组件注册机制

扩展组件通过写入全局注册表来声明自己的存在：

\`\`\`
扩展 JS 文件执行（由 ExtensionSlot 以 <script> 注入）
  └→ 写入 window.__EXTENSION_REGISTRY__["<ext_id>"] = {
       "panel": [ComponentA, ComponentB],
       "message_decorator": [...]
     }
  └→ ExtensionSlot 读取匹配当前 slot name 的组件列表
       └→ markRaw(comp) — 防止 Vue 深度反应化破坏组件闭包
       └→ shallowRef 推入 — 浅层引用，只追踪数组本身的变化
       └→ <component :is="comp" :api="createExtensionApi()" />
\`\`\`

**完整 index.js 模板：**

\`\`\`javascript
// frontend/index.js
(function() {
  const V = window.__EXT_VUE__;
  if (!V || typeof V.ref !== 'function') {
    console.error('[my-extension] window.__EXT_VUE__ 不可用');
    return;
  }
  const { h, ref, computed, watch, onMounted, onBeforeUnmount } = V;

  const MyPanel = {
    props: ['api'],
    setup(props) {
      // 从 props.api 获取应用状态
      const conv = props.api.getCurrentConversation();
      const messages = props.api.getMessages();

      const count = ref(0);

      return () => h('div', { class: 'ext-my-panel' }, [
        h('h3', `当前会话: ${conv?.id || '无'}`),
        h('p', `消息数: ${messages.length}`),
        h('button', { onClick: () => count.value++ }, `计数: ${count.value}`)
      ]);
    }
  };

  // 注册到全局注册表
  const REG = window.__EXTENSION_REGISTRY__ || {};
  REG['my-extension'] = {
    panel: [MyPanel]  // 可注册多个组件
  };
  window.__EXTENSION_REGISTRY__ = REG;
})();
\`\`\`

**关键约定：**

| 约定 | 说明 |
|------|------|
| IIFE 包裹 | 隔离作用域，不污染全局 |
| ID 一致性 | `REG['my-extension']` 的 key 必须与 `manifest.json` 的 `id` 一致 |
| slot 名匹配 | `panel` / `message_decorator` 对应 `ext_points.frontend` 中声明的扩展点 |
| props.api | ExtensionSlot 自动传入，无需手动绑定 |
| setup() 内实时读取 | 在 `setup()` 中从 `window.__EXT_VUE__` 读取 API（非 IIFE 顶层闭包），参见第三部分注意事项 |
```

- [ ] **Step 4: 撰写 2.4.3 useExtensionApi**

```markdown
#### 2.4.3 useExtensionApi — 扩展安全 API

扩展通过 `props.api` 访问应用状态，而非直接 import Pinia Store。这提供了安全层——扩展只能调用明确暴露的方法。

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `getConversation(convId)` | `{ id, title, ... } \| null` | 根据会话 ID 查找会话 |
| `getCurrentConversation()` | `{ id } \| null` | 获取当前活跃会话（只有 id 可用） |
| `getMessages()` | `Message[]` | 获取当前会话的消息列表 |
| `getSettings()` | `Settings` | 获取当前预设配置 |
| `getWorldInfo()` | — | 预留接口 |

**使用示例：**

\`\`\`javascript
setup(props) {
  const conv = props.api.getCurrentConversation();
  const messages = props.api.getMessages();

  // 用 conv.id 调用自己的后端 API
  async function fetchMyData() {
    if (!conv?.id) return;
    const res = await fetch(`/api/ext/my-ext/stats?conv_id=${conv.id}`);
    const json = await res.json();
    // ...
  }

  return () => h('div', ...);
}
\`\`\`

> ⚠️ `getCurrentConversation()` 返回的是 `{ id }` 而非完整的 conversation 对象。需要其他字段时用 `getConversation(convId)`。
```

- [ ] **Step 5: 撰写 2.4.4 前端扩展点 + 2.4.5 CSS 样式**

```markdown
#### 2.4.4 前端扩展点

| 扩展点 | 插槽名 | App.vue 中的位置 | 用途 |
|--------|--------|-----------------|------|
| `panel` | `"panel"` | 聊天界面全局区域 | 全局面板，适合悬浮窗、侧边栏等常驻 UI |
| `message_decorator` | `"message_decorator"` | 每条消息下方（预留） | 为消息添加操作按钮、标注等 |

> 要让扩展面板可见，`App.vue` 中必须有对应的 `<ExtensionSlot name="panel" />`。如果面板不显示，首先检查 App.vue 是否 import 了 ExtensionSlot 组件。

#### 2.4.5 CSS 样式最佳实践

由于扩展组件不经过构建工具，CSS 使用有以下方式：

**方式 1：内联 `style` 对象（推荐用于简单样式）**

\`\`\`javascript
h('div', {
  style: {
    padding: '12px',
    background: '#fff',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  }
}, [...])
\`\`\`

**方式 2：注入 `<style>` 标签（推荐用于复杂样式）**

\`\`\`javascript
(function() {
  // 注入样式（只执行一次）
  if (!document.getElementById('ext-my-styles')) {
    const style = document.createElement('style');
    style.id = 'ext-my-styles';
    style.textContent = `
      .ext-my-panel { padding: 12px; background: #fff; }
      .ext-my-button { padding: 4px 12px; cursor: pointer; }
    `;
    document.head.appendChild(style);
  }
  // ...组件定义
})();
\`\`\`

**命名规范：**

| 规则 | 示例 |
|------|------|
| 所有类名加 `ext-<id>-` 前缀 | `.ext-dashboard-panel` |
| 避免使用全局 CSS 变量 | 除非应用明确提供了稳定的主题变量表 |
| 不依赖外部 CSS 框架 | 除非扩展明确声明依赖 |
```

- [ ] **Step 6: 验证 2.4 节**

对照以下文件确认 API 和方法签名：
- `frontend/src/main.js` — __EXT_VUE__ 注入列表
- `frontend/src/extensions/useExtensionApi.js` — 所有方法
- `frontend/src/extensions/ExtensionSlot.vue` — props 传递

- [ ] **Step 7: Commit Part 2.4**

\`\`\`bash
git add Plugin_Development_Guide.md
git commit -m "docs: add Part 2.4 — frontend development (tech stack, registration, API, styling)"
\`\`\`

---

### Task 5: 撰写 Part 2.5-2.6 — 安装分发 + 调试排查（约 300 行）

**Files:**
- Modify: `Plugin_Development_Guide.md`（追加 2.5 和 2.6 节）

**Interfaces:**
- Consumes: 2.2 中的权限列表，1.3 中的目录结构
- Produces: 2.5.1 ~ 2.5.3（安装分发），2.6（调试排查）

- [ ] **Step 1: 撰写 2.5 安装与分发**

```markdown
### 2.5 安装与分发

#### 2.5.1 ZIP 打包规范

\`\`\`
my-extension.zip
└── my-extension/              ← 必须有一层目录包裹（目录名 = 扩展 id）
    ├── manifest.json
    ├── backend.py
    └── frontend/
        ├── index.js
        └── components/
            └── *.js
\`\`\`

打包命令：

\`\`\`bash
# Windows PowerShell
Compress-Archive -Path test_expand/my-extension/* -DestinationPath my-extension.zip

# macOS / Linux（注意进入目录打包，保证内部有一层包裹）
cd test_expand
zip -r ../../my-extension.zip my-extension/
\`\`\`

#### 2.5.2 Git 仓库发布

- 仓库根目录直接放 `manifest.json`、`backend.py`、`frontend/`
- **不要额外嵌套**（不要 `repo/my-extension/manifest.json`）
- 建议写 README.md 说明功能和用法
- 建议打 Git tag 标记版本号（如 `v1.0.0`）

\`\`\`bash
git tag v1.0.0
git push origin v1.0.0
\`\`\`

#### 2.5.3 安装流程与权限审批

\`\`\`
用户在扩展管理面板操作
  ├→ "从 ZIP 安装" → 选择 .zip 文件
  │    └→ 后端解压 → 校验 manifest → 返回所需权限列表
  └→ "从 Git 安装" → 输入仓库 URL
       └→ 后端 git clone → 校验 manifest → 返回所需权限列表

用户确认权限 → 写入 .registry.json + permissions_granted
  └→ 加载扩展
       ├→ 前端扩展：立即生效（刷新页面即可）
       └→ api_route 扩展：需重启应用生效（路由在 Flask 启动时注册）
\`\`\`

> ⚠️ **api_route 启动限制：** 通过 ZIP/Git 安装的扩展，如果在运行中，`api_bp=None`，自定义路由不会生效。需要重启应用使路由注册到 Blueprint。
```

- [ ] **Step 2: 撰写 2.6 调试与排查**

```markdown
### 2.6 调试与排查

#### 前端调试

| 现象 | 检查点 |
|------|--------|
| 扩展完全不显示 | ① `App.vue` 是否 `import ExtensionSlot`；② `.registry.json` 中 `enabled: true`；③ Network 面板 `/api/extensions/<id>/frontend` 是否 200 |
| `ref is not a function` | ① `window.__EXT_VUE__` 是否被覆盖（检查是否误用了 `__VUE__`）；② ExtensionSlot 是否使用了 `shallowRef` + `markRaw` |
| 面板渲染但数据不更新 | ① `props.api.getCurrentConversation()` 是否返回正确的 `id`；② 加 `console.log` 诊断 `setup()` 中的 ref 值 |
| 脚本未执行 | Network 面板检查 `/api/extensions/<id>/frontend` 是否 200；Console 是否有 JS 错误 |
| 组件注册了但没渲染 | 检查 `window.__EXTENSION_REGISTRY__[id][slotname]` 是否存在；slot 名是否与 manifest 中声明的一致 |

#### 后端调试

| 现象 | 检查点 |
|------|--------|
| `/api/ext/...` 返回 404 | ① `ExtensionManager.init()` 是否传了 `api_bp` 而非 `flask_app`；② 路由路径是否多加了 `/api` 前缀 |
| 钩子不触发 | ① `manifest.json` 中 `ext_points.backend` 是否包含对应扩展点；② 函数名是否与 `EXT_POINT_TO_FUNC` 映射一致 |
| 数据写入失败 | ① 存储目录是否存在；② `os.makedirs(exist_ok=True)` 是否调用；③ 是否有文件权限问题 |

#### 通用诊断命令

\`\`\`bash
# 查看注册表
cat user_data/extensions/.registry.json

# 确认扩展目录结构
ls -R user_data/extensions/<ext_id>/

# 查看后端日志中的扩展加载信息
# 搜索 "扩展初始化完成" 或 "加载扩展" 日志行
\`\`\`
```

- [ ] **Step 3: 验证 2.5-2.6 节**

确认安装流程与 `backend/app/routes/extensions.py` 和 `frontend/src/components/ExtensionManager.vue` 一致。

- [ ] **Step 4: Commit Part 2.5-2.6**

\`\`\`bash
git add Plugin_Development_Guide.md
git commit -m "docs: add Part 2.5-2.6 — distribution, installation, and debugging"
\`\`\`

---

### Task 6: 整合 Part 3 — 保留原有注意事项（约 250 行）

**Files:**
- Modify: `Plugin_Development_Guide.md`（追加第三部分）

**Interfaces:**
- Consumes: 原 `Plugin_Development_Guide.md` 的全部内容
- Produces: 第三部分，精简整合的注意事项

- [ ] **Step 1: 提取原文档内容并去重**

扫描原文档，标记与 Part 1 / Part 2 重复的内容：

| 原文档节 | 处理方式 |
|----------|----------|
| §1 目录结构与同步 | 保留，与 1.3 互补（1.3 讲"是什么"，这里讲"怎么小心"） |
| §2.1 必须 import ExtensionSlot | 保留，强调原因 |
| §2.2 __VUE__ vs __EXT_VUE__ | 保留，经典踩坑 |
| §2.3 markRaw + shallowRef | 保留，解释为什么 |
| §2.4 setup() 内实时读取 | 保留 |
| §3.1 init() 必须传 Blueprint | 保留 |
| §3.2 路由不加 /api 前缀 | 保留 |
| §3.3 安全校验 | 保留 |
| §3.4 JSON 异常处理 | 保留 |
| §4.1 Store 属性名 | 保留 |
| §5 manifest.json 规范 | **与 2.2 重复，改写为"常见错误"视角** |
| §6 调试技巧 | **与 2.6 重复，改写为速查清单** |
| §7 排查清单 | **保留为终极速查表** |

- [ ] **Step 2: 撰写第三部分**

```markdown
---

## 第三部分：开发注意事项

> 以下内容基于 Dashboard 扩展的实际调试经验。**正文教你"怎么做"，这里告诉你"为什么容易出错"。** 开发新扩展前务必阅读。

### 3.1 目录结构与同步

（保留原 §1，略作精简）

### 3.2 前端开发避坑

#### 3.2.1 必须 import ExtensionSlot

（保留原 §2.1）

#### 3.2.2 永远不要用 `__VUE__`，用 `__EXT_VUE__`

（保留原 §2.2）

#### 3.2.3 组件对象必须 markRaw + shallowRef

（保留原 §2.3）

#### 3.2.4 setup() 内实时读取 window.__EXT_VUE__

（保留原 §2.4）

### 3.3 后端开发避坑

#### 3.3.1 init() 传 Blueprint，不是 Flask app

（保留原 §3.1）

#### 3.3.2 扩展路由不加 /api 前缀

（保留原 §3.2）

#### 3.3.3 安全：校验动态路径参数

（保留原 §3.3）

#### 3.3.4 JSON 文件读写加异常处理

（保留原 §3.4）

### 3.4 useExtensionApi 注意事项

（保留原 §4.1，属性名对照）

### 3.5 manifest.json 常见错误

（原 §5 改写为常见错误视角，与 2.2 互补而非重复）

### 3.6 常见错误排查清单

（保留原 §7 作为终极速查表）
```

- [ ] **Step 3: 实际整合原文档内容**

逐节提取原文档内容，精简冗余表述，保留核心教训和代码示例。注意：
- 去重已在 Part 1/2 详细讲解的内容
- 保留"教训"、"根因"、"现象" 等实践性表述
- 代码示例保留正确/错误对照

- [ ] **Step 4: 验证 Part 3**

确认原文档所有检查项都被保留（无丢失），与 Part 1/2 无明显重复。

- [ ] **Step 5: Commit Part 3**

\`\`\`bash
git add Plugin_Development_Guide.md
git commit -m "docs: add Part 3 — development notes and pitfalls from original guide"
\`\`\`

---

### Task 7: 最终审查与润色

**Files:**
- Modify: `Plugin_Development_Guide.md`（全文件审查）

- [ ] **Step 1: 全文通读**

从头到尾通读一遍，检查：
- 术语一致性（如 extension/扩展/插件 统一使用）
- 交叉引用正确（如 "参见 2.4.3" 确实指向那一节）
- Markdown 格式无错误（表格对齐、代码块闭合）

- [ ] **Step 2: 对照设计规格逐项确认**

| 设计要求 | 完成情况 |
|----------|----------|
| Part 1: Quick Start + Hello World | 确认 |
| Part 2.1: 架构总览 | 确认 |
| Part 2.2: manifest.json 规范 | 确认 |
| Part 2.3: 后端开发（钩子/路由/持久化/API参考） | 确认 |
| Part 2.4: 前端开发（技术栈/注册/API/扩展点/CSS） | 确认 |
| Part 2.5: 安装与分发 | 确认 |
| Part 2.6: 调试与排查 | 确认 |
| Part 3: 原注意事项保留 | 确认 |
| 代码全部内嵌，无外部示例目录 | 确认 |
| 文件路径与源码一致 | 确认 |

- [ ] **Step 3: 行数检查**

确认总行数在 1800-2500 范围内。

- [ ] **Step 4: 最终 Commit**

\`\`\`bash
git add Plugin_Development_Guide.md
git commit -m "docs: finalize Plugin Development Guide — three-part hybrid document"
\`\`\`
```

---

## Self-Review

### 1. Spec coverage

逐个检查设计规格的章节是否都有对应任务：

| 规格章节 | 对应任务 |
|----------|----------|
| Part 1: 1.1 What | Task 1 Step 1 |
| Part 1: 1.2 Hello World | Task 1 Step 3 |
| Part 1: 1.3 目录结构 | Task 1 Step 5 |
| Part 2: 2.1 架构总览 | Task 2 Step 1 |
| Part 2: 2.2 manifest 规范 | Task 2 Step 3 |
| Part 2: 2.3.1 钩子 | Task 3 Step 2 |
| Part 2: 2.3.2 自定义路由 | Task 3 Step 4 |
| Part 2: 2.3.3 数据持久化 | Task 3 Step 5 |
| Part 2: 2.3.4 后端 API 参考 | Task 3 Step 6 |
| Part 2: 2.4.1 技术栈 | Task 4 Step 2 |
| Part 2: 2.4.2 注册机制 | Task 4 Step 3 |
| Part 2: 2.4.3 useExtensionApi | Task 4 Step 4 |
| Part 2: 2.4.4 扩展点 | Task 4 Step 5 |
| Part 2: 2.4.5 CSS | Task 4 Step 5 |
| Part 2: 2.5 安装分发 | Task 5 Step 1 |
| Part 2: 2.6 调试排查 | Task 5 Step 2 |
| Part 3: 注意事项 | Task 6 Step 2-3 |

所有设计规格章节都有覆盖。✅

### 2. Placeholder scan

搜索 "TBD"、"TODO"、"fill in"、"类似" — 无占位符。所有步骤都包含具体内容或指向明确的源码文件。✅

### 3. Type consistency

- `__EXT_VUE__` API 列表在 Task 4 Step 2 定义，后续步骤使用一致
- `props.api` 方法列表在 Task 4 Step 4 定义，与 useExtensionApi.js 一致
- ctx 结构在 Task 3 Step 2 定义，与 conversations.py 一致
- manifest 字段在 Task 2 Step 3 定义，后续任务引用一致 ✅

### 4. Issues found

- 无遗漏的规格需求
- 无矛盾或类型不一致
- 前方任务定义的术语在后续任务中使用一致
