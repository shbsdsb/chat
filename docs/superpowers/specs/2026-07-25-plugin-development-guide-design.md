# Plugin Development Guide 文档重构 — 设计规格

> 日期：2026-07-25 | 状态：设计完成，待审阅

## 1. 动机

现有的 `Plugin_Development_Guide.md` 是一份优秀的**踩坑笔记**——它记录了 Dashboard 扩展开发中实际遇到的问题和解决方案。但它是自底向上写的：全部是"注意事项"和"检查清单"，缺乏一条从零到一的**开发主线**。

一个熟悉 Vue 3 + Flask 但未接触过本系统的开发者，打开这份文档会感到困惑：
- 我该从哪里开始？
- manifest.json 有哪些字段？每个扩展点做什么？
- 后端钩子和自定义路由怎么注册？能调用哪些内部 API？
- 前端怎么拿到 Vue API？怎么访问 Store？怎么注册组件？
- 开发完怎么打包分发？

这些问题的答案分散在 AGENTS.md、源码、以及旧文档的零星片段中，没有统一入口。

## 2. 目标

将 `Plugin_Development_Guide.md` 重构为一份**混合模式开发文档**：

- **第一部分 Quick Start**：线性流程，5 分钟做出 Hello World
- **第二部分主题参考**：按模块分类，随时查阅
- **第三部分注意事项**：保留原有踩坑记录，精简整合

### 边界

| 范围 | 说明 |
|------|------|
| **包含** | 扩展开发全流程：manifest → 后端 → 前端 → 安装分发 → 调试 |
| **包含** | 所有可用的扩展点、API、权限的完整参考 |
| **包含** | 前端技术栈说明（Vue h 函数、__EXT_VUE__、markRaw/shallowRef） |
| **包含** | 原有注意事项保留整合 |
| **不包含** | 扩展系统内部实现原理（那是源码注释的职责） |
| **不包含** | 扩展系统架构设计决策（那是 `docs/superpowers/specs/2026-07-25-extension-system-design.md` 的职责） |

## 3. 目标读者

**有经验的 Web 开发者，但未接触过本项目的扩展系统。**

- 假设读者熟悉 Vue 3（组合式 API、Pinia、h 渲染函数）和 Flask（Blueprint、路由装饰器）
- 假设读者了解 JSON 和基本的 HTTP 概念
- 不假设读者了解本项目的扩展注册机制、__EXT_VUE__ 注入、HookDispatcher 等

## 4. 文档大纲（详细版）

### 第一部分：快速入门（Quick Start）

#### 1.1 什么是扩展系统
- 一句话定位：扩展是运行在 Chat 应用内的独立功能模块
- 能做什么：注入面板、监听 AI 响应、注册 API 路由
- 核心概念速览：manifest.json（声明）→ backend.py（后端逻辑）→ frontend/（UI 组件）
- 一张架构全景图（文字描述 + ASCII 图）

#### 1.2 5 分钟 Hello World
以一个最小可运行扩展为线索，逐步讲解：

**Step 1：创建目录和 manifest.json**
```json
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
```

**Step 2：写前端组件 `frontend/index.js`**
```js
(function() {
  const { h, ref } = window.__EXT_VUE__;
  const HelloPanel = {
    setup(props) {
      return () => h('div', { class: 'hello-panel' }, 'Hello World!');
    }
  };
  // 注册到全局注册表
  if (!window.__EXTENSION_REGISTRY__) window.__EXTENSION_REGISTRY__ = {};
  window.__EXTENSION_REGISTRY__['hello-world'] = { panel: [HelloPanel] };
})();
```

**Step 3：注册到 .registry.json**
```json
{
  "hello-world": {
    "id": "hello-world",
    "enabled": true,
    "installed_at": "2026-07-25T00:00:00",
    "permissions_granted": []
  }
}
```

**Step 4：验证**
- 重启应用，看到"Hello World!"面板出现
- 如果没出现：检查 DevTools Console、确认 enabled: true、确认 App.vue 有 ExtensionSlot

> 注意：Hello World 不需要后端，但仍需创建一个占位 `backend.py`（说明原因）

#### 1.3 目录结构速览
```
你的扩展源码（放在 test_expand/ 开发）
test_expand/<ext_id>/
├── manifest.json          ← 声明文件（ID、版本、扩展点、权限）
├── backend.py            ← 后端：钩子 + 自定义路由
└── frontend/
    ├── index.js          ← 入口：注册组件到全局注册表
    └── components/       ← 组件目录（可选）
        └── *.js

运行时加载目录（应用实际读取）
user_data/extensions/
├── .registry.json        ← 注册表（驱动加载）
└── <ext_id>/             ← 与上方结构相同
```

### 第二部分：主题参考

#### 2.1 架构总览

**一张全链路图（ASCII）：**
```
Flask 启动
  └→ ExtensionManager.init(api_bp)
       └→ load_all_enabled()  遍历 registry 中 enabled 扩展
            └→ load_extension()
                 ├→ importlib 加载 backend.py
                 ├→ api_route → 调用 register_api_routes(api_bp)
                 └→ chat.post_receive → dispatcher.register_hook()

Vue 启动
  └→ App.vue: ExtensionSlot
       └→ fetch /api/extensions/<id>/frontend
            └→ 注入 <script> → index.js 执行
                 └→ 写入 window.__EXTENSION_REGISTRY__
       └→ <component :is> 渲染，props.api = createExtensionApi()

AI 响应完成
  └→ dispatcher.dispatch("chat.post_receive", ctx)
       └→ 每个扩展的 on_chat_post_receive(ctx) 执行
```

**各模块职责表**（简表，不必展开实现细节）：

| 模块 | 位置 | 开发者需要知道什么 |
|------|------|-------------------|
| ExtensionManager | `backend/app/extensions/__init__.py` | 单例，init(api_bp) 驱动加载 |
| loader | `backend/app/extensions/loader.py` | 按 EXT_POINT_TO_FUNC 映射注册钩子 |
| HookDispatcher | `backend/app/extensions/hooks.py` | dispatch() 用线程池执行（30s 超时） |
| registry | `backend/app/extensions/registry.py` | .registry.json 的 CRUD |
| ExtensionSlot | `frontend/src/extensions/ExtensionSlot.vue` | 动态加载 JS + 渲染组件 |
| useExtensionApi | `frontend/src/extensions/useExtensionApi.js` | 扩展访问 Store 的安全接口 |

#### 2.2 manifest.json 完整规范

**必填字段：**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一标识，字母数字下划线连字符，1-64 字符 |
| name | string | 显示名称 |
| version | string | 语义化版本 |
| permissions | string[] | 声明所需权限（见权限表） |
| ext_points | object | 声明使用的扩展点（见下方） |
| min_app_version | string | 最低兼容的应用版本 |

**可选字段：**
| 字段 | 类型 | 说明 |
|------|------|------|
| description | string | 简要描述 |
| author | string | 作者 |
| homepage | string | 项目主页 URL |

**扩展点 ext_points：**

| 扩展点 | 位置 | 说明 |
|--------|------|------|
| `backend: chat.post_receive` | ext_points.backend | AI 响应完成后触发，需实现 `on_chat_post_receive(ctx)` |
| `backend: chat.pre_send` | ext_points.backend | 消息发送前触发（已注册，暂未 dispatch），需实现 `on_chat_pre_send(ctx)` |
| `backend: api_route` | ext_points.backend | 注册自定义 API 路由，需实现 `register_api_routes(app)` |
| `frontend: panel` | ext_points.frontend | 全局面板，在 ExtensionSlot name="panel" 处渲染 |
| `frontend: message_decorator` | ext_points.frontend | 消息装饰器（预留） |

**权限列表：**

| 权限 | 说明 |
|------|------|
| `read:conversations` | 读取会话列表 |
| `read:messages` | 读取消息内容 |
| `write:messages` | 写入/修改消息 |
| `hook:chat` | 注册聊天钩子（chat.post_receive / chat.pre_send） |
| `api:route` | 注册自定义 API 路由 |
| `storage:read` | 读取扩展存储 |
| `storage:write` | 写入扩展存储 |

#### 2.3 后端开发

##### 2.3.1 生命周期钩子详解

**chat.post_receive — AI 响应完成触发**

```python
# backend.py
def on_chat_post_receive(ctx):
    """
    ctx 结构：
    {
        "conv_id": str,       # 会话 ID
        "messages": [...],    # 完整消息历史
        "last_message": {...},# 刚完成的 AI 回复
        "settings": {...},    # 当前预设配置
    }
    """
    conv_id = ctx["conv_id"]
    last_msg = ctx["last_message"]
    token_count = len(last_msg.get("content", "").split())

    # 可以写入自己的数据文件
    _save_stats(conv_id, {"tokens": token_count})

    # 返回值（可选）会合并到消息的 extensions 字段
    return {"token_count": token_count}
```

- 超时：30 秒
- 异常：会被捕获，不影响其他扩展
- 返回值：可选，会出现在前端消息对象的 `extensions` 数组中

**chat.pre_send — 消息发送前触发（已注册映射，暂未 dispatch）**

```python
def on_chat_pre_send(ctx):
    """
    ctx 结构：
    {
        "conv_id": str,
        "messages": [...],   # 当前消息历史
        "pending_message": {...},  # 即将发送的消息
        "settings": {...},
    }
    返回值可修改 pending_message
    """
    pass
```

##### 2.3.2 自定义 API 路由

```python
# backend.py
from flask import request, jsonify

def register_api_routes(app):
    @app.route("/ext/<ext_id>/my-endpoint", methods=["GET"])
    def my_endpoint():
        conv_id = request.args.get("conv_id", "")
        # 安全校验
        if not _validate_conv_id(conv_id):
            return jsonify({"code": 400, "message": "invalid id"}), 400
        # 业务逻辑
        return jsonify({"code": 0, "data": {...}})

    @app.route("/ext/<ext_id>/stats", methods=["POST"])
    def save_stats():
        data = request.get_json()
        # ...
        return jsonify({"code": 0})
```

要点：
- **路由不加 `/api` 前缀**：Blueprint 已有 `url_prefix="/api"`，最终路径为 `/api/ext/<id>/...`
- **必须校验输入**：动态路径参数用正则白名单
- **必须 try/except**：JSON 文件读写要有异常兜底
- **统一响应格式**：`{"code": 0, "data": ...}` 或 `{"code": 非0, "message": "..."}`

##### 2.3.3 数据持久化

```python
import json, os

_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "user_data", "ext_data")

def _get_storage_path(ext_id, filename):
    dir_path = os.path.join(_STORAGE_DIR, ext_id)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, filename)

def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

##### 2.3.4 后端 API 参考（速查表）

列出可供扩展调用的后端内部接口（来自 storage.py），注明：在 backend.py 中直接 import 使用。

| 函数 | 来源 | 用途 |
|------|------|------|
| `get_conversation(conv_id)` | `app/storage.py` | 读取会话元数据（索引信息） |
| `get_messages(conv_id)` | `app/storage.py` | 读取会话的完整消息列表 |
| `get_all_settings()` | `app/storage.py` | 读取所有预设配置列表 |
| `get_setting(preset_id)` | `app/storage.py` | 读取单个预设配置 |
| `save_setting(preset_id, data)` | `app/storage.py` | 保存预设配置 |

> 前端 Store 访问请参见 2.4.3 useExtensionApi。 |

#### 2.4 前端开发

##### 2.4.1 技术栈说明

| 层 | 技术 | 说明 |
|----|------|------|
| 渲染 | Vue 3 `h()` 函数 | 扩展组件使用渲染函数编写（.js 文件，非 .vue SFC） |
| 响应式 | `window.__EXT_VUE__` | main.js 注入的 Vue API：`{ h, ref, computed, watch, onMounted, onBeforeUnmount }` |
| 状态 | Pinia（通过 useExtensionApi） | 不直接 import store，通过 `props.api` 访问 |
| 样式 | 内联 style / CSS 类 | .js 文件中用 `style` 属性或引用全局 CSS 类 |
| 注册 | `window.__EXTENSION_REGISTRY__` | 全局组件注册表 |

**为什么用 h() 函数而不是 .vue SFC：**
- 扩展组件以纯 .js 文件运行，不经过 Vite 编译
- `h()` 是 Vue 3 的渲染函数，等价于 `<template>` 的编译结果
- 参考 `test_expand/dashboard/frontend/components/DashboardFloating.js` 作为模板

##### 2.4.2 组件注册机制

```
扩展前端 JS 文件执行
  └→ 写入 window.__EXTENSION_REGISTRY__["ext_id"] = { "panel": [组件], "message_decorator": [...] }
  └→ ExtensionSlot 读取匹配的 slot → markRaw(组件) → shallowRef 推入
  └→ <component :is="comp" :api="createExtensionApi()" />
```

**index.js 模板：**
```js
(function() {
  const { h, ref, computed, watch, onMounted, onBeforeUnmount } = window.__EXT_VUE__;

  const MyComponent = {
    props: ['api'],
    setup(props) {
      const count = ref(0);
      return () => h('div', { class: 'my-extension' }, [
        h('p', `Count: ${count.value}`),
        h('button', { onClick: () => count.value++ }, '+1'),
      ]);
    }
  };

  const REG = window.__EXTENSION_REGISTRY__ || {};
  REG['hello-world'] = { panel: [MyComponent] };
  window.__EXTENSION_REGISTRY__ = REG;
})();
```

##### 2.4.3 useExtensionApi — 扩展安全 API

完整列出 `useExtensionApi.js` 中所有可用的方法：

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `getConversation(convId)` | Conversation \| null | 根据 ID 获取会话 |
| `getCurrentConversation()` | { id } \| null | 获取当前活跃会话 |
| `getMessages()` | Message[] | 获取当前会话消息列表 |
| `getSettings()` | Settings | 获取当前预设配置 |
| `getWorldInfo()` | — | 预留 |

扩展组件通过 `props.api` 调用：
```js
setup(props) {
  const conv = props.api.getCurrentConversation();
  // conv.id → 可以用这个 ID 调后端 /api/ext/.../<conv.id>/...
}
```

##### 2.4.4 扩展点（前端）

| 扩展点 | 插槽名 | 渲染位置 | 说明 |
|--------|--------|----------|------|
| panel | `"panel"` | App.vue 全局区域 | 全局面板（如 Dashboard 悬浮窗） |
| message_decorator | `"message_decorator"` | 每条消息下方（预留） | 消息装饰器 |

##### 2.4.5 CSS 样式最佳实践

- 使用**唯一前缀**避免冲突：所有类名加 `ext-<id>-` 前缀
- 优先使用内联 `style` 属性（与组件逻辑紧密耦合）
- 如需复杂样式，在 `index.js` 中用 JS 注入 `<style>` 标签
- 避免依赖全局 CSS 变量（除非应用明确提供了主题变量）

#### 2.5 安装与分发

##### 2.5.1 ZIP 打包规范
```
<ext_id>.zip
└── <ext_id>/                  ← 必须有一层目录包裹
    ├── manifest.json
    ├── backend.py
    └── frontend/
        ├── index.js
        └── components/
```

打包命令：
```bash
# 在 test_expand/ 下
cd test_expand
zip -r ../hello-world.zip hello-world/
```

##### 2.5.2 Git 仓库发布
- 仓库根目录直接放 manifest.json、backend.py、frontend/
- 不要额外嵌套一层目录
- README.md 说明扩展功能和使用方法
- 建议打 Git tag 标记版本号

##### 2.5.3 权限审批流程
```
用户打开扩展管理面板
  └→ 点击"从 ZIP 安装" / "从 Git 安装"
       └→ 后端读取 manifest.json，展示所需权限
       └→ 用户确认 → 写入 .registry.json + 热加载
       └→ 如果 ext_points.backend 有 api_route：需重启应用生效
```

#### 2.6 调试与排查

##### 前端
| 现象 | 检查点 |
|------|--------|
| 扩展完全不显示 | App.vue 是否 import ExtensionSlot；registry enabled: true；/api/extensions 返回的 frontend 为 true |
| ref is not a function | window.__EXT_VUE__ 是否被覆盖；ExtensionSlot 是否用 shallowRef+markRaw |
| 组件渲染但数据不更新 | props.api 调用是否返回正确数据；加 console.log 诊断 |
| 脚本未执行 | Network 面板检查 /api/extensions/<id>/frontend 是否 200 |

##### 后端
| 现象 | 检查点 |
|------|--------|
| /api/ext/... 404 | init() 是否传 api_bp 而非 flask_app；路由是否多了 /api 前缀 |
| 钩子不触发 | manifest ext_points.backend 是否包含对应扩展点；函数名是否匹配 |
| 数据写入失败 | 存储目录是否存在；os.makedirs(exist_ok=True) 是否调用 |

##### 通用命令
```bash
cat user_data/extensions/.registry.json    # 查看注册表
ls user_data/extensions/<ext_id>/          # 确认目录结构
```

### 第三部分：开发注意事项

> 以下内容基于 Dashboard 扩展的实际调试经验，开发新扩展前务必阅读。

（保留原有 Plugin_Development_Guide.md 核心内容，按以下方式精简整合：）

- 3.1 目录结构与同步（保留原 1 节）
- 3.2 前端开发规范（合并原 2.1-2.4，去重重复内容）
- 3.3 后端开发规范（合并原 3.1-3.4）
- 3.4 useExtensionApi 注意事项（保留原 4.1）
- 3.5 manifest.json 常见错误（保留原 5 节核心）
- 3.6 常见错误排查清单（保留原 7 节，作为终极速查表）

> ⚠️ 注意事项与正文的关系：正文是"怎么做"，注意事项是"为什么容易出错"。两者不重复，相互引用。

## 5. 与现有文档的关系

| 已有文档 | 关系 |
|----------|------|
| 原 `Plugin_Development_Guide.md` | 内容整合入新文档第三部分 |
| `AGENTS.md` | 保持独立，新文档通过链接引用 |
| `docs/superpowers/specs/2026-07-25-extension-system-design.md` | 保持独立（架构设计），新文档聚焦开发教程 |
| `docs/superpowers/specs/2026-07-25-dashboard-extension-design.md` | 保持独立（Dashboard 示例的设计），新文档引用为参考 |

## 6. 非目标

- 不重构扩展系统的代码实现
- 不修改 AGENTS.md
- 不创建新的示例扩展目录（代码全部内嵌在文档中）
- 不在新文档中解释扩展系统的设计决策（那是架构设计文档的职责）

## 7. 交付物

单一文件：`Plugin_Development_Guide.md`（覆盖原文件）

- 估计行数：1800-2500 行 Markdown
- 代码示例：~15 个内嵌片段（Python + JS）
- 表格：~10 张参考速查表
