# Chat 扩展开发文档

> 版本：1.2.0 | 适用于 Chat 扩展系统 MVP

---

## 一、概述

Chat 扩展系统允许开发者为 Chat 桌面应用添加自定义功能。扩展以**本地文件夹**形式存在，通过 `manifest.json` 声明能力，可同时包含**后端钩子**（Python）和**前端组件**（Vue 3）。

### 扩展能做什么

| 能力 | 说明 | 示例 |
|------|------|------|
| 后端钩子 | 介入聊天请求/响应流程，读写上下文 | 分析命中率、注入系统提示词 |
| 前端组件 | 在消息气泡旁注入自定义 UI | 命中率标签、快捷回复按钮 |
| 自定义 API | 注册新的 HTTP 端点 | 扩展专属配置接口 |
| Provider 适配器 | 接入新的 LLM 后端 | Anthropic、Ollama 适配器（规划中） |

### 一个最小的扩展

```
my-extension/
├── manifest.json      # 必需：扩展身份证
├── backend.py         # 可选：后端钩子
└── frontend/          # 可选：前端组件
    └── index.js       # 前端入口，注册组件到全局注册表
```

---

## 二、manifest.json

扩展根目录必须包含 `manifest.json`，定义扩展的元数据、权限和扩展点。

### 完整字段

```jsonc
{
  // ── 必填 ──
  "id": "my-awesome-extension",      // 唯一标识，即文件夹名
  "name": "我的扩展",                  // 显示名称
  "version": "1.0.0",                // 语义化版本
  "permissions": [                   // 权限声明（安装时展示给用户审批）
    "read:conversations",
    "hook:chat"
  ],
  "ext_points": {                    // 注册的扩展点
    "backend": ["chat.post_receive"],
    "frontend": ["message_decorator"]
  },
  "min_app_version": "1.2.0",        // 最低核心版本

  // ── 可选 ──
  "author": "Your Name",
  "description": "扩展功能简述",
  "icon": "icon.png",                // 暂未使用

  // ── Git 安装专属 ──
  "update": {
    "type": "git",
    "url": "https://github.com/user/my-extension.git",
    "branch": "main"
  }
}
```

### 权限列表

| 权限 | 含义 |
|------|------|
| `read:conversations` | 读取会话消息列表 |
| `read:world_info` | 读取 World Info 配置 |
| `write:conversations` | 修改会话内容（规划中） |
| `hook:chat` | 注册聊天前后处理钩子 |
| `register:provider` | 注册 LLM Provider 适配器（规划中） |
| `network` | 发起外部网络请求（规划中） |

---

## 三、后端钩子

### 扩展点：`chat.post_receive`

在 AI 回复完成后触发。后端 `backend.py` 导出函数：

```python
def on_chat_post_receive(ctx):
    """
    ctx 是 ChatContext 字典，包含以下字段：

    conversation_id  : str     — 会话 ID
    messages         : list    — 本轮消息列表（含 system prompt）
    request_body     : dict    — 发往 LLM 的请求体
                                  { model, messages }
    response_body    : dict    — LLM 响应体
                                  { content, reasoning_content }
    world_info_entries : list  — 注入的 World Info 条目（当前为空列表）
    settings         : dict    — 当前 API 预设配置
                                  { api_url, api_key, model, ... }
    """
    # 你的逻辑...

    # 返回 ChatResult 或 None
    return {
        "hit_rate": 0.75,
        "hit": 3,
        "total": 4,
        "details": [...]
    }
```

### 返回值

函数可返回 `None`（纯观察者，不做修改）或一个 `dict`。返回的 dict 会被自动包装为：

```python
{
    "extension_id": "my-extension-id",
    "message_meta": { ... }   # 你返回的 dict 内容
}
```

其中 `message_meta` 会存入消息的 `extensions` 字段，供前端组件读取。

也可以显式返回标准格式：

```python
return {
    "extension_id": "my-ext",
    "message_meta": { "key": "value" }
}
```

### 执行约束

- 钩子在 30 秒超时后会被强制终止
- 钩子抛出的异常**不会影响主流程或其它扩展**
- 钩子在消息保存到磁盘**之前**执行
- 多个扩展的钩子按安装顺序依次执行

---

## 四、前端扩展

### 扩展点：`message_decorator`

在每条消息气泡下方注入自定义组件。组件通过**全局注册表**注册：

```javascript
// frontend/index.js
import MyBadge from './components/MyBadge.js';

if (!window.__EXTENSION_REGISTRY__) {
  window.__EXTENSION_REGISTRY__ = {};
}

window.__EXTENSION_REGISTRY__['my-extension-id'] = {
  message_decorator: [MyBadge],
};
```

### 组件 Props

注册的组件会收到以下 props：

| Prop | 类型 | 说明 |
|------|------|------|
| `message` | `Object` | 当前消息对象，包含 `id`、`role`、`content`、`extensions` |
| `conversation` | `Object` | 当前会话对象 |
| `api` | `Object` | 受限的 Core API（见下节） |

### 读取后端数据

后端钩子写入的数据在 `message.extensions` 中：

```javascript
// 在组件中
const extData = props.message?.extensions?.['my-extension-id'];
// extData 即 backend.py 返回的 message_meta 内容
```

### 组件示例（渲染函数）

使用 Vue 3 的 `h()` 渲染函数（推荐，无需编译）：

```javascript
// frontend/components/MyBadge.js
import { h, ref } from 'vue';

export default {
  name: 'MyBadge',
  props: {
    message: Object,
    conversation: Object,
    api: Object,
  },
  setup(props) {
    const extData = props.message?.extensions?.['my-extension-id'];
    if (!extData) return () => null;

    return () => h('div', { class: 'my-badge' }, [
      h('span', null, `扩展数据: ${JSON.stringify(extData)}`),
    ]);
  },
};
```

### 样式

扩展组件使用 Shadow DOM 之外的普通 CSS，建议使用 scoped 样式或命名空间 class 避免冲突：

```css
/* 在组件的 <style> 中或通过内联 style 属性 */
.my-extension-badge {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}
```

---

## 五、Core API（useExtensionApi）

扩展组件可通过 `props.api` 调用受限的核心 API：

```javascript
const api = props.api;

// 获取当前会话
const conv = api.getCurrentConversation();

// 获取指定会话
const conv = api.getConversation(conversationId);

// 获取会话消息列表
const messages = api.getMessages();           // 当前会话
const messages = api.getMessages(convId);     // 指定会话

// 获取当前 API 预设配置
const settings = api.getSettings();
// → { api_url, model, api_key: "...", ... }

// 获取 World Info（当前返回空数组）
const worldInfo = api.getWorldInfo();
```

> 权限不足时 API 返回 `null`，不抛出异常。

---

## 六、安装与分发

### 方式一：ZIP 导入

1. 将扩展文件夹打包为 `.zip`（根目录直接包含 `manifest.json`）
2. 在 Chat 中打开"扩展管理"抽屉 → 点击"导入 ZIP" → 选择文件
3. 审批权限 → 确认安装

### 方式二：Git 安装

1. 将扩展代码托管到 Git 仓库（GitHub / Gitee 等）
2. 在 Chat 中打开"扩展管理"抽屉 → 点击"Git 安装"
3. 输入仓库 URL 和分支 → 审批权限 → 确认安装
4. 后续可通过"更新"按钮执行 `git pull` 拉取最新版本

### 版本更新

- **Git 安装**：点击扩展卡片上的"更新"按钮自动 `git pull`
- **ZIP 安装**：重新导入新版 ZIP 覆盖旧版本

---

## 七、完整示例：上下文命中率分析器

此扩展分析 AI 回复中 World Info 条目的命中情况，在每条助手消息旁显示命中率标签。

### manifest.json

```json
{
  "id": "hit-rate-analyzer",
  "name": "上下文命中率分析",
  "version": "1.0.0",
  "author": "Chat Team",
  "description": "分析 AI 回复中 World Info 条目的命中情况",
  "permissions": ["read:conversations", "read:world_info", "hook:chat"],
  "ext_points": {
    "backend": ["chat.post_receive"],
    "frontend": ["message_decorator"]
  },
  "min_app_version": "1.2.0"
}
```

### backend.py

```python
def on_chat_post_receive(ctx):
    world_info_entries = ctx.get("world_info_entries", [])
    if not world_info_entries:
        return None

    response_body = ctx.get("response_body", {})
    ai_content = response_body.get("content", "").lower()

    hit_count = 0
    details = []
    for entry in world_info_entries:
        key = entry.get("key", "").lower()
        content = entry.get("content", "").lower()
        matched = (key and key in ai_content) or (content and content in ai_content)
        if matched:
            hit_count += 1
        details.append({
            "key": entry.get("key", ""),
            "content_preview": entry.get("content", "")[:100],
            "matched": matched,
        })

    total = len(world_info_entries)
    hit_rate = hit_count / total if total > 0 else 0.0

    return {
        "hit_rate": round(hit_rate, 2),
        "hit": hit_count,
        "total": total,
        "details": details,
    }
```

### frontend/index.js

```javascript
import HitRateBadge from './components/HitRateBadge.js';

if (!window.__EXTENSION_REGISTRY__) {
  window.__EXTENSION_REGISTRY__ = {};
}
window.__EXTENSION_REGISTRY__['hit-rate-analyzer'] = {
  message_decorator: [HitRateBadge],
};
```

### frontend/components/HitRateBadge.js

```javascript
import { h, ref } from 'vue';

export default {
  name: 'HitRateBadge',
  props: { message: Object, api: Object },
  setup(props) {
    const expanded = ref(false);
    const extData = props.message?.extensions?.['hit-rate-analyzer'];
    if (!extData) return () => null;

    const pct = Math.round(extData.hit_rate * 100);
    const color = pct >= 60 ? '#4caf50' : pct >= 30 ? '#ff9800' : '#f44336';

    return () => h('div', {
      onClick: () => expanded.value = !expanded.value,
      style: { display:'inline-flex', alignItems:'center', gap:'4px',
               marginTop:'6px', fontSize:'12px', cursor:'pointer', color:'#666' },
    }, [
      h('span', { style: { width:'8px', height:'8px', borderRadius:'50%',
                           backgroundColor: color, display:'inline-block' }}),
      h('span', null, `WOI 命中 ${extData.hit}/${extData.total} · ${pct}%`),
      expanded.value && h('div', {
        style: { marginTop:'4px', padding:'8px', background:'#f5f5f5',
                 borderRadius:'4px', fontSize:'11px' },
      }, extData.details.map(d =>
        h('div', { style: { marginBottom:'2px' } }, [
          h('span', { style: { color: d.matched ? '#4caf50' : '#ccc' } },
            d.matched ? '✓' : '✗'),
          h('span', null, ` ${d.key || d.content_preview || '(空)'}`),
        ])
      )),
    ]);
  },
};
```

---

## 八、调试

### 后端调试

1. 在后端控制台查看扩展加载日志（搜索 "扩展" 关键词）
2. 检查 `user_data/logs/error.log` 查看异常
3. 钩子异常不会中断主流程，但会记录完整 traceback

### 前端调试

1. 打开浏览器 DevTools → Console
2. 检查 `window.__EXTENSION_REGISTRY__` 确认组件已注册
3. 查看 `[ExtensionSlot]` 前缀的 console.warn 消息

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 扩展不显示 | 未启用 | 检查扩展管理中开关状态 |
| 前端组件不渲染 | 未注册到全局注册表 | 检查 `index.js` 中 `window.__EXTENSION_REGISTRY__` 赋值 |
| 后端钩子不触发 | `ext_points.backend` 未声明 | 检查 `manifest.json` 中是否包含 `chat.post_receive` |
| 安装失败"版本不兼容" | `min_app_version` 高于核心版本 | 降低版本要求或升级 Chat |
| 权限不足 API 返回 null | 未声明对应权限 | 在 manifest.json 中添加权限，重新安装 |

---

## 九、最佳实践

1. **最小权限原则** — 只声明扩展实际需要的权限
2. **钩子快速返回** — 后端钩子有 30 秒超时，避免耗时操作
3. **组件按需渲染** — 无数据时返回 `null` 避免空白占位
4. **使用渲染函数** — `h()` 无需编译，兼容性好
5. **版本语义化** — 遵循 `MAJOR.MINOR.PATCH` 便于更新管理
6. **GitHub 分发** — 推荐用 Git 安装方式，用户可一键更新
