# 扩展系统设计

> 状态：设计已确认，待实现
> 日期：2026-07-25

---

## 一、目标

为 Chat 实现前后端可扩展的插件系统。核心只做 RP 基础能力，长尾功能通过扩展生态覆盖。MVP 阶段交付扩展加载基础设施 + 一个"上下文命中率分析"示例扩展跑通全流程。

---

## 二、整体架构

```
chat/
├── user_data/
│   └── extensions/                        # 扩展安装目录
│       ├── .registry.json                 # 扩展注册表（已安装扩展清单+状态）
│       └── <extension-id>/                # 每个扩展一个文件夹
│           ├── manifest.json              # 声明：id/name/version/permissions/ext_points
│           ├── backend.py                 # 后端扩展入口（可选）
│           └── frontend/                  # 前端扩展（可选）
│               ├── index.js               # 导出 { ext_points, components }
│               └── components/
│
├── backend/app/
│   ├── extensions/                        # 扩展管理核心
│   │   ├── __init__.py                    # ExtensionManager 单例
│   │   ├── registry.py                    # 注册表读写（.registry.json）
│   │   ├── loader.py                      # 加载/卸载扩展，导入 backend.py 模块
│   │   ├── installer.py                   # git clone / zip 解压 / 删除
│   │   ├── permissions.py                 # 权限检查装饰器
│   │   └── hooks.py                       # 钩子调度器（chat.pre_send / chat.post_receive）
│   └── routes/
│       └── extensions.py                  # /api/extensions CRUD + install/uninstall/update
│
├── frontend/src/
│   ├── api/
│   │   └── extensions.js                  # 扩展管理 API 调用
│   ├── stores/
│   │   └── extensions.js                  # Pinia — 已安装扩展状态
│   ├── extensions/                        # 扩展运行时核心
│   │   ├── ExtensionSlot.vue              # 扩展点插槽组件
│   │   └── useExtensionApi.js             # 暴露给扩展的 Core API composable
│   └── components/
│       └── ExtensionManager.vue           # 扩展管理 UI（安装/卸载/启用/禁用）
```

### 核心流程

1. 用户通过 UI 或 API 安装扩展（git clone 或 zip 导入）
2. 后端解析 manifest.json，提取权限声明和扩展点注册
3. 用户审批权限 → 注册到 `.registry.json`，状态变为 `enabled`
4. 后端加载 `backend.py`，注册钩子；前端动态加载 `frontend/index.js`
5. 运行时：核心触发钩子 → 扩展响应；核心渲染 ExtensionSlot → 扩展组件填入

---

## 三、Manifest 结构

`manifest.json` 是扩展的身份证和合同，核心只加载声明过的能力：

```jsonc
{
  "id": "hit-rate-analyzer",          // 唯一标识，文件夹名
  "name": "上下文命中率分析",
  "version": "1.0.0",
  "author": "…",
  "description": "分析 AI 回复中 World Info 条目的命中情况",
  "icon": "icon.png",                 // 可选

  "permissions": [                    // 必须声明，安装时逐条展示给用户
    "read:conversations",             // 读取会话消息
    "read:world_info",                // 读取 World Info 配置
    "hook:chat"                       // 注册 chat 前后钩子
  ],

  "ext_points": {                     // 注册的扩展点
    "backend": [
      "chat.post_receive"            // 收到 AI 响应后触发
    ],
    "frontend": [
      "message_decorator"            // 消息气泡旁注入 UI
    ]
  },

  "min_app_version": "1.2.0",        // 最低核心版本要求
  "update": {                         // Git 安装才有
    "type": "git",
    "url": "https://github.com/…",
    "branch": "main"
  }
}
```

### 权限粒度

| 权限 | 说明 | MVP |
|------|------|-----|
| `read:conversations` | 读取当前会话消息列表 | ✅ |
| `read:world_info` | 读取 World Info 配置和条目 | ✅ |
| `write:conversations` | 修改会话（如注入系统消息） | 🔮 |
| `hook:chat` | 注册 chat 前后处理钩子 | ✅ |
| `register:provider` | 注册 LLM Provider Adapter | 🔮 |
| `network` | 发起外部网络请求 | 🔮 |

---

## 四、扩展点接口

### 后端扩展点

| 扩展点 | 用途 | MVP |
|--------|------|-----|
| `chat.pre_send` | 发送前修改 messages/context | 🔮 |
| `chat.post_receive` | 收到响应后分析/附加元数据 | ✅ |
| `provider` | 注册 LLM Provider Adapter | 🔮 |
| `api_route` | 注册自定义 API 端点 | 🔮 |
| `tool` | 注册 Agent 可调用工具 | 🔮 |

### 前端扩展点

| 扩展点 | 用途 | MVP |
|--------|------|-----|
| `message_decorator` | 消息气泡旁注入 UI | ✅ |
| `panel` | 侧边栏/底栏面板 | 🔮 |
| `toolbar_button` | 工具栏按钮 | 🔮 |
| `settings_tab` | 设置页新标签 | 🔮 |

### 后端钩子签名：`chat.post_receive`

```python
# 扩展的 backend.py
def on_chat_post_receive(ctx: ChatContext) -> ChatResult | None:
    """
    ctx:
      - conversation_id       # 会话 ID
      - messages              # 本轮消息列表
      - request_body          # LLM 请求体
      - response_body         # LLM 响应体（含 usage）
      - world_info_entries    # 注入的 WOI 条目 [{key, content, ...}]
      - settings              # 当前 API 预设
    """
    ...

class ChatResult:
    extension_id: str
    message_meta: dict       # 附加到消息的 extensions 字段
```

MVP 阶段 `ctx` 只读，返回的 `ChatResult` 仅带 `message_meta`。

### 前端扩展点：`message_decorator`

核心在每条消息旁渲染 `<ExtensionSlot name="message_decorator" :message="msg" />`。

扩展组件接收 props：
```js
{
  message: {             // 消息对象
    id, role, content,
    extensions: {        // 后端注入的元数据
      "hit-rate-analyzer": { hitRate: 0.6, details: [...] }
    }
  },
  conversation: {...},
  api: {                 // useExtensionApi() 受限 API
    getWorldInfo,
    getSettings,
  }
}
```

### 前端 Core API：`useExtensionApi()`

```js
import { useExtensionApi } from '@/extensions/useExtensionApi'

const api = useExtensionApi()
// api.getConversation(id)
// api.getWorldInfo(convId)
// api.getSettings()
// 权限不足时返回 null，不抛异常
```

### 消息存储扩展

`messages/<id>.json` 新增 `extensions` 字段：
```json
{
  "messages": [
    { "id": "msg-1", "role": "user", "content": "…" },
    { "id": "msg-2", "role": "assistant", "content": "…",
      "extensions": {
        "hit-rate-analyzer": { "hitRate": 0.6, "hit": 3, "total": 5 }
      }
    }
  ]
}
```

---

## 五、扩展管理

### API 端点

```
POST   /api/extensions/install          # 安装（git clone 或 zip 上传）
POST   /api/extensions/<id>/uninstall   # 卸载（删除文件夹 + 注销）
POST   /api/extensions/<id>/update      # git pull 拉取最新
POST   /api/extensions/<id>/toggle      # { enabled: true/false }
GET    /api/extensions                  # 列出已安装扩展 + 状态
GET    /api/extensions/<id>/manifest    # 读取扩展 manifest
```

### 安装流程

```
用户操作                    后端处理                         前端
─────────                  ────────                         ────
拖入 .zip 文件         →   解压到 extensions/<id>/
粘贴 Git URL           →   git clone 到 extensions/<id>/
                       ↓
                       读取 manifest.json
                       检查 min_app_version 兼容性
                       ↓
                       返回 manifest + 权限列表给前端
                                                           ← 弹出审批弹窗
用户确认                 →
                       ↓
                       写入 .registry.json
                       状态设为 "enabled"
                       加载 backend.py
                       ↓
                       返回成功
                                                           ← 扩展卡片变绿
                                                           ← 通知前端加载扩展组件
```

### `.registry.json` 结构

```jsonc
{
  "extensions": {
    "hit-rate-analyzer": {
      "version": "1.0.0",
      "enabled": true,
      "installed_at": "2026-07-25T10:00:00Z",
      "install_method": "git",
      "git_url": "https://github.com/…",
      "git_branch": "main",
      "last_updated": "2026-07-25T10:00:00Z",
      "permissions_granted": ["read:conversations", "read:world_info", "hook:chat"]
    }
  }
}
```

### 禁用行为

- `enabled: false` → 后端不调用钩子，前端不渲染组件
- 已存储 `extensions` 元数据保留不删（重新启用后恢复）
- 卸载才删除文件夹和注册表条目

---

## 六、异常与边界处理

| 场景 | 处理策略 |
|------|---------|
| manifest.json 缺失/格式错误 | 安装失败，返回具体错误，不写注册表 |
| 版本不兼容 | 安装前校验，提示"需要升级核心版本" |
| backend.py import 异常 | 标记 `error` 状态，不影响其他扩展 |
| 钩子执行超时 | 30s 超时，打日志跳过，不阻塞主流程 |
| Git pull 失败 | 返回错误，保留当前版本 |
| 同名扩展重复安装 | 提示"已存在"，询问覆盖更新 |
| 卸载时文件夹删除失败 | 注册表先删，文件删除失败仅打日志 |
| 前端扩展组件加载失败 | ExtensionSlot 渲染空节点 + console.warn |
| 权限不足调用 Core API | useExtensionApi() 返回 undefined |
| 多扩展注册同一扩展点 | 按安装顺序依次调用，任意报错不影响后续 |

---

## 七、MVP 示例扩展：上下文命中率

### 功能

用户发送消息后，在 AI 回复旁显示 World Info 命中率标签（如 "WOI 命中 3/5 · 60%"），点击展开详情。

### 实现要点

1. **后端 `backend.py`：** 注册 `chat.post_receive`，对比 `world_info_entries` 中每条目的 key/content 是否出现在 AI 响应文本中，计算命中率，写入 `message_meta`
2. **前端 `HitRateBadge.vue`：** 注册 `message_decorator`，读取 `message.extensions["hit-rate-analyzer"]`，渲染小标签，点击弹窗显示详情
3. **Manifest：** 声明 `read:conversations`、`read:world_info`、`hook:chat` 权限

---

## 八、安全模型（MVP 轻隔离）

- 扩展通过 manifest 声明所需权限
- 安装时逐条展示给用户审批
- 扩展与核心同进程运行，权限通过代码层面约束（非进程级沙箱）
- 后续迭代可升级为子进程/iframe 硬隔离
