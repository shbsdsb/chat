# 插件（扩展）开发指南

> 本文档教你如何为 Chat 应用开发扩展。扩展是运行在应用内的独立功能模块，可以注入 UI 面板、监听 AI 响应、注册自定义 API 路由。
>
> **前置要求：** 熟悉 Vue 3（组合式 API、Pinia、h 渲染函数）和 Flask（Blueprint、路由装饰器）。未接触过本项目的扩展系统没关系，本文档从头讲起。

---

## 第一部分：快速入门

### 1.1 什么是扩展系统

扩展系统是 Chat 应用的内置插件框架。一个扩展由三个部分组成：

- **manifest.json** — 声明文件，定义扩展的 ID、版本、权限和使用的扩展点
- **backend.py** — 后端逻辑（可选），注册生命周期钩子或自定义 API 路由
- **frontend/** — 前端 UI（可选），使用 Vue 3 渲染函数编写界面组件

#### 扩展能做什么？

| 能力 | 说明 |
|------|------|
| 注入面板 | 在应用界面的指定位置渲染自定义 UI（如悬浮窗、侧边栏） |
| 监听 AI 响应 | 在 AI 回复完成后执行自定义逻辑（如统计 token、记录日志） |
| 注册 API 路由 | 添加自定义后端接口，供前端扩展调用 |
| 读写数据 | 在自己的存储目录中持久化 JSON 数据 |

#### 加载流程一图胜千言

```
开发者编写扩展 → 放入 test_expand/ 或通过 ZIP/Git 安装
     ↓
.registry.json 注册（enabled: true 驱动加载）
     ↓
Flask 启动时：ExtensionManager 遍历注册表 → import backend.py → 注册钩子/路由
Vue 启动时：ExtensionSlot 拉取 frontend/ JS → 注入 <script> → 组件渲染
```

> 接下来用 5 分钟创建一个 Hello World 扩展，你会直观理解整个流程。

---

### 1.2 5 分钟 Hello World

创建一个最小可运行的扩展，在应用界面上显示 "Hello World!" 面板。

#### Step 1：创建目录和 manifest.json

在 `test_expand/hello-world/` 下创建：

```json
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
```

| 字段 | 这里的含义 |
|------|-----------|
| `id` | 唯一标识，必须与目录名一致 |
| `permissions` | 空数组——因为没有后端逻辑，无需权限 |
| `ext_points.frontend` | `["panel"]` 表示要在全局面板插槽渲染 |
| `ext_points.backend` | `[]` 表示不使用后端钩子 |

#### Step 2：创建占位 backend.py

即使不使用后端逻辑，也需要创建一个空的 `backend.py`（扩展加载器要求此文件存在）：

```python
# test_expand/hello-world/backend.py
# 本扩展无后端逻辑，仅需此文件满足加载要求
```

> **为什么需要空文件？** 扩展加载器 `load_extension()` 通过 `importlib` 加载 `backend.py`，如果文件不存在会报错。即使不需要后端功能，也必须保留此占位文件。

#### Step 3：编写前端组件 frontend/index.js

```javascript
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
```

**关键点解释：**

| 要点 | 说明 |
|------|------|
| IIFE 包裹 | `(function() { ... })()` 隔离作用域，避免污染全局 |
| `window.__EXT_VUE__` | 应用注入的 Vue API，包含 `{ h, ref, computed, watch, onMounted, onBeforeUnmount }` |
| `props: ['api']` | 接收 ExtensionSlot 传入的 `api` 对象，用于访问应用 Store |
| `h()` 渲染函数 | Vue 3 渲染函数，等价于 `<template>` 的编译结果 |
| 注册表 key | `'hello-world'` 必须与 `manifest.json` 中的 `id` 完全一致 |
| 插槽 key | `panel` 对应 `ext_points.frontend` 中声明的扩展点 |

#### Step 4：同步到运行时目录

扩展开发在 `test_expand/` 下进行，运行时从 `user_data/extensions/` 加载。需要将扩展复制过去：

```bash
# Windows PowerShell
Copy-Item -Recurse test_expand/hello-world user_data/extensions/hello-world

# macOS / Linux
cp -r test_expand/hello-world user_data/extensions/hello-world
```

#### Step 5：注册到 .registry.json

编辑 `user_data/extensions/.registry.json`，添加：

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

> 如果 `.registry.json` 中已有其他扩展，在 JSON 对象中追加即可——不要覆盖整个文件。

#### Step 6：验证

重启应用（或刷新前端页面），你应该看到蓝色边框的 "Hello World!" 面板。

**如果没出现，依次检查：**

1. DevTools Console 是否有报错
2. `.registry.json` 中 `enabled` 是否为 `true`
3. `App.vue` 是否 import 了 `<ExtensionSlot name="panel" />`
4. 浏览器 DevTools Network 面板：`/api/extensions/hello-world/frontend` 是否返回 200

---

> 🎉 恭喜！你已完成第一个扩展。下面深入了解每个模块的细节。

---

### 1.3 目录结构速览

```
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
```

| 目录 | 用途 |
|------|------|
| `test_expand/` | 开发目录，你在这里写代码和调试 |
| `user_data/extensions/` | 运行时目录，Flask 和前端只从这里加载扩展 |
| `.registry.json` | 注册表，记录了所有扩展的启用状态和授权权限 |

> ⚠️ 两个目录各自独立。修改 `test_expand/` 后必须手动同步到 `user_data/extensions/`，否则不会生效。
