# Chat — Vue 3 + Flask + Electron 桌面聊天应用

## Project
前后端分离的 AI 聊天桌面应用。前端 Vue 3 SPA 经 Vite 构建、Electron 打包；后端 Flask REST API，通过 SSE 流式转发 OpenAI 兼容的 chat completions。数据以 JSON 文件存储在 `user_data/` 下（conversations.json 索引 + messages/<id>.json 消息 + settings.json 预设）。

## Commands
```bash
# 后端
cd backend
pip install -r requirements.txt
python run.py                              # Flask @ 127.0.0.1:5000

# 前端 (仅浏览器)
cd frontend
npm install
npm run dev                                # Vite @ 127.0.0.1:5173

# 前端 (Electron 桌面窗口)
npm run electron:dev                       # 同时启动 Vite + Electron
npm run electron:build                     # 生产构建（vite build + electron-builder）

# 后端测试
cd backend
python -m pytest                           # 自动使用 tmp_path 隔离数据，9 个测试文件 + conftest.py
```

## Architecture

```
chat/
├── run.bat                                # Windows 一键启动脚本
├── Plugin_Development_Guide.md             # 扩展开发指南（manifest/backend/frontend）
├── UI_token.md                             # UI 设计 Token 与组件约定
├── docs/                                   # 设计文档（API/前端/存储设计 + api/前端/重构规格/superpowers 子目录）
├── Goal/                                    # 产品目标与竞品差距分析（chatbox-gap, sillytavern-gap）
├── test_expand/                            # 扩展（插件）开发目录
│   └── dashboard/                          # 内置 Dashboard 扩展示例
├── backend/
│   ├── run.py                             # 入口：create_app() → app.run()
│   ├── config.json                        # Flask 配置（DEBUG/HOST/PORT/SECRET_KEY）
│   ├── requirements.txt                   # flask, flask-cors, requests
│   ├── app/
│   │   ├── __init__.py                    # create_app() 工厂：加载配置、CORS、注册蓝图、初始化扩展管理器
│   │   ├── storage/                       # JSON 文件存储（拆分自原 storage.py）
│   │   │   ├── __init__.py                # 统一导出 + init_storage()
│   │   │   ├── conversations.py           # 会话索引 CRUD（conversations.json）
│   │   │   ├── messages.py                # 消息 CRUD（messages/<conv_id>.json）
│   │   │   ├── settings.py                # API 预设 CRUD（settings.json）
│   │   │   ├── css_presets.py             # CSS 预设（主题皮肤）CRUD
│   │   │   └── param_presets.py           # 参数预设（temperature 等）CRUD
│   │   ├── extensions/                    # 扩展系统（插件框架）
│   │   │   ├── __init__.py                # ExtensionManager — 生命周期、钩子调度
│   │   │   ├── registry.py                # .registry.json 读写、启用/禁用
│   │   │   ├── loader.py                  # 动态 import backend.py + 注册路由/钩子
│   │   │   ├── installer.py               # ZIP/Git 安装、卸载、更新
│   │   │   ├── hooks.py                   # 钩子模型（chat.post_receive 等）
│   │   │   └── permissions.py             # 权限声明与校验
│   │   ├── models/                        # 遗留目录（原 SQLite 模型定义，现数据模型见 docs/STORAGE.md）
│   │   ├── routes/
│   │   │   ├── __init__.py                # Blueprint("api", __name__)
│   │   │   ├── _helpers.py                # 路由共享辅助函数
│   │   │   ├── conversations.py           # CRUD + SSE 流式 chat、/stop、/regenerate、消息编辑
│   │   │   ├── settings.py                # CRUD + /test（连通性）、/models（模型列表）、/default
│   │   │   ├── css_presets.py             # CSS 预设（主题皮肤）CRUD
│   │   │   ├── param_presets.py           # 参数预设（temperature 等）CRUD
│   │   │   ├── extensions.py              # 扩展管理 API（安装/卸载/启用/禁用/列表/前端 JS 分发）
│   │   │   └── example.py                 # /api/hello 示例
│   │   ├── services/
│   │   │   ├── ai.py                      # stream_chat() — 调用 OpenAI 兼容 API，SSE 逐 token 产出
│   │   │   ├── http_client.py             # 带重试/超时的 HTTP 客户端封装
│   │   │   └── sse_manager.py             # SSEManager — {conv_id: threading.Event}，支持 /stop 取消流
│   │   └── utils/
│   │       ├── __init__.py                # 空文件（包标记）
│   │       └── response.py                # ok() / fail() 统一响应 + 错误日志（脱敏 api_key）
│   └── tests/                             # pytest（conftest.py monkeypatch DATA_DIR），9 个测试文件 + conftest.py
├── frontend/
│   ├── .npmrc                             # 淘宝 npm 镜像（国内加速）
│   ├── vite.config.js                     # 读取 vite.config.json，配置代理 /api → 127.0.0.1:5000
│   ├── vite.config.json                   # Vite host/port/proxy 配置
│   ├── electron/
│   │   ├── main.cjs                       # Electron 主进程（CommonJS），从 JSON 构建菜单，支持中英文
│   │   ├── preload.cjs                    # 预加载脚本（contextIsolation: true）
│   │   ├── menu.json                      # 英文菜单模板
│   │   └── menu_zn_cn.json                # 中文菜单模板
│   └── src/
│       ├── main.js                        # Vue 入口：createApp → Pinia → Router，import highlight.js GitHub 主题
│       ├── assets/
│       │   └── drawer.css                 # 抽屉（侧边栏）动画/过渡样式
│       ├── api/
│       │   ├── index.js                   # 统一出口：http, sse, conversationsApi, settingsApi, extensionsApi
│       │   ├── request.js                 # Axios 封装：拦截器解包 {code,message,data}，HTTP 错误弹 Alert
│       │   ├── sse.js                     # SSE 客户端（fetch + ReadableStream，非 EventSource）
│       │   ├── conversations.js           # 会话 API
│       │   ├── settings.js                # 设置 API
│       │   ├── extensions.js              # 扩展管理 API（安装/卸载/启用/禁用/列表）
│       │   ├── cssPresets.js              # CSS 预设 API
│       │   ├── paramPresets.js            # 参数预设 API
│       │   └── constants.js               # 前端常量（扩展点 ID、事件名等）
│       ├── composables/
│       │   ├── useMarkdown.js              # MD 流式渲染入口（组合 markdown/ 子模块）
│       │   ├── useResizableDrawer.js       # 可拖拽调整宽度的侧边栏 composable
│       │   └── markdown/                    # MD 渲染子模块
│       │       ├── engine.js               # markdown-it + DOMPurify + hljs 渲染引擎
│       │       ├── htmlDetector.js          # HTML 代码块自动检测
│       │       └── splitter.js              # 按 \n\n 分段冻结策略
│       ├── extensions/                      # 前端扩展运行时
│       │   ├── ExtensionSlot.vue            # 扩展点插槽 — 动态注入扩展 UI
│       │   └── useExtensionApi.js           # 扩展内可用的 API（Pinia stores 等）
│       ├── stores/
│       │   ├── chat.js                    # Pinia — 会话/消息/流式状态、lastMessageAt 即时排序
│       │   ├── settings.js                # Pinia — API 预设（多配置切换）
│       │   ├── alert.js                   # Pinia — 全局弹窗提示
│       │   ├── cssPresets.js              # Pinia — CSS 预设（主题皮肤）
│       │   ├── paramPresets.js            # Pinia — 参数预设（temperature 等）
│       │   └── extensions.js             # Pinia — 扩展安装状态、启用/禁用
│       ├── components/                    # BaseDialog(通用弹窗基类), ConversationItem(编辑/删除按钮+弹窗),
│       │                                  #   ConversationsDrawer(左→右可拖拽), InputBar, MessageBubble(MD渲染+代码块复制),
│       │                                  #   MessageList, AlertDialog, ModelSelector, PresetSelector,
│       │                                  #   ParamPresetSelector(参数预设选择器), CssPresetSelector(主题皮肤选择器),
│       │                                  #   CssPresetEditor(主题皮肤编辑器), SettingsDrawer(右→左可拖拽),
│       │                                  #   MessageActions, HtmlPreview(HTML 代码/预览切换),
│       │                                  #   ResponseFormatInput, WelcomeBanner,
│       │                                  #   ExtensionManager(扩展安装/卸载/启用/禁用管理面板),
│       │                                  #   ExtensionDetailDrawer(扩展详情抽屉)
│       ├── views/
│       │   ├── Home.vue                   # 聊天主页面（MessageList + InputBar）
│       │   └── SettingsView.vue           # 设置页面
│       └── router/index.js               # / 和 /settings 两个路由（懒加载）
└── user_data/                             # 运行时数据（conversations.json, messages/, settings.json, extensions/, logs/）
```

## Conventions

### 后端 (Python/Flask)
- **工厂模式**：`create_app()` 创建 Flask 实例，不在模块顶层持有 app 引用。
- **存储**：JSON 文件存储，`storage/` 包提供全部 CRUD 函数，`threading.Lock` 保护并发写入。数据分多个层级：`conversations.json`（会话索引）、`messages/<conv_id>.json`（每个会话的消息）、`settings.json`（预设配置）、CSS/参数预设各有独立文件。
- **API 响应**：统一使用 `ok(data, message)` / `fail(code, message)` 返回 `{code, message, data}` 结构。code=0 成功，非 0 失败。`fail()` 自动写 error.log 并脱敏敏感字段。
- **API Key**：明文存储在 settings.json 的 api_key 字段中。
- **蓝图注册**：先在 `routes/__init__.py` 中建 `api_bp`，再 import 各子模块触发 `@api_bp.route()` 装饰器，最后 `register_blueprint(api_bp, url_prefix="/api")`。注意扩展管理器必须在 `register_blueprint` 之前 `init()`，以便扩展注册自定义 API 路由。
- **SSE 流**：`stream_with_context()` + `Response(mimetype="text/event-stream")`，`SSEManager` 用 `threading.Event` 支持 `/stop` 取消。
- **扩展系统**：`app/extensions/` — ExtensionManager 管理生命周期，manifest.json 声明权限和扩展点，`loader.py` 动态 import backend.py，`installer.py` 支持 ZIP/Git 安装。后端钩子（如 `chat.post_receive`）通过 `hooks.py` 调度。
- **测试**：pytest，`conftest.py` 用 `monkeypatch` 将 DATA_DIR/MESSAGES_DIR 等路径指向 tmp_path，防止污染真实数据。

### 前端 (Vue 3 / JS)
- **组合式 API**：Vue 3 SFC 使用 `<script setup>`。
- **状态管理**：Pinia `defineStore`，options API 风格（state/actions）。
- **路由懒加载**：`() => import("@/views/...")`。
- **API 层**：`@/api/request.js` 封装 Axios，拦截器自动解包 `{code,message,data}` → 成功返回 `data`，失败 throw Error。HTTP 错误弹 AlertDialog。
- **SSE 客户端**：基于 `fetch` + `ReadableStream`（非 `EventSource`），支持 `close()` 中止。
- **Markdown 渲染**：`useMarkdown.js` composable — 按 `\n\n` 分段冻结策略，markdown-it 渲染 + DOMPurify 清洗，highlight.js 代码高亮。复制按钮通过 `renderer.rules.fence` 注入，事件委托在硬编码 `.bubble-text` 容器上处理。
- **路径别名**：`@` → `frontend/src`（vite.config.js 中配置）。
- **扩展系统**：`extensions/ExtensionSlot.vue` 根据扩展点 ID 动态拉取并注入扩展 JS，`useExtensionApi.js` 向扩展暴露 Pinia stores 等 API。`ExtensionManager.vue` 提供安装/卸载/启用/禁用 UI。`api/constants.js` 定义扩展点 ID 和事件名常量。
- **Electron**：主进程在 `electron/main.cjs`（CommonJS），预加载脚本 `preload.cjs`，`contextIsolation: true`。菜单根据系统语言自动选择中/英文。

## Branch Rules
- **禁止直接在 `main` 分支提交** — `.git/hooks/pre-commit` 已配置阻止 hook。
- 所有开发在 `develop` 分支进行，`main` 仅通过 PR/MR 合并进入。
- 当没有`develop`分支时，但需要进行提交时，需要向用户确认是否创建。

## Notes
- 无 CI/CD 配置，无 linter 配置。
- `.npmrc` 配置了淘宝镜像，CI 或非中文环境可能需要移除。
- 根目录 `run.bat` 可一键启动前后端（Windows）。
- `database.py` 已删除；`models/` 为遗留目录，数据模型见 `docs/STORAGE.md`。新代码全部使用 `storage/` 包。残留的 `user_data/chat.db` 可安全忽略。
- 会话命名从前端即时截取前 20 字符，排序用前端 `lastMessageAt` 字段实现发送瞬间重排。
- v1.1.0 新增内联 HTML 渲染：`HtmlPreview.vue` 自动检测 Markdown 输出中的 HTML 代码块，提供代码/预览切换。
- v1.2.0（backend）新增 CSS 预设（主题皮肤）、参数预设（temperature/top_p 等）、扩展系统（插件框架）。前端 package.json 版本为 1.1.0。
- `Plugin_Development_Guide.md` 是扩展开发的完整指南（manifest.json 规范、backend.py 钩子、frontend 渲染函数）。
- `UI_token.md` 定义了 UI 设计 Token（颜色、间距、圆角等）和组件约定，新 UI 代码应遵循。
- `docs/` 下包含各功能的设计规格和实现计划，新功能开发前建议先查阅。
- `Goal/` 下包含产品目标与竞品差距分析文档。
- `temp_check.js` 是临时检查脚本，不参与构建。
- `.reasonix/` 和 `.superpowers/` 是 AI 辅助开发工具目录，不参与应用运行。
