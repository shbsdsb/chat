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
python -m pytest                           # 自动使用 tmp_path 隔离数据，44 tests
```

## Architecture

```
chat/
├── run.bat                                # Windows 一键启动脚本
├── docs/                                   # 设计文档（API/前端/存储设计 + api/前端/重构规格子目录）
├── backend/
│   ├── run.py                             # 入口：create_app() → app.run()
│   ├── config.json                        # Flask 配置（DEBUG/HOST/PORT/SECRET_KEY）
│   ├── requirements.txt                   # flask, flask-cors, requests
│   ├── app/
│   │   ├── __init__.py                    # create_app() 工厂：加载配置、CORS、注册蓝图、init_storage
│   │   ├── storage.py                     # JSON 文件存储（conversations/messages/settings CRUD），threading.Lock 保护
│   │   ├── database.py                    # 旧 SQLite 模块（已废弃，被 storage.py 替代）
│   │   ├── routes/
│   │   │   ├── __init__.py                # Blueprint("api", __name__)
│   │   │   ├── conversations.py           # CRUD + SSE 流式 chat、/stop、/regenerate、消息编辑
│   │   │   ├── settings.py                # CRUD + /test（连通性）、/models（模型列表）、/default
│   │   │   └── example.py                 # /api/hello 示例
│   │   ├── services/
│   │   │   ├── ai.py                      # stream_chat() — 调用 OpenAI 兼容 API，SSE 逐 token 产出
│   │   │   └── sse_manager.py             # SSEManager — {conv_id: threading.Event}，支持 /stop 取消流
│   │   └── utils/
│   │       └── response.py                # ok() / fail() 统一响应 + 错误日志（脱敏 api_key）
│   └── tests/                             # pytest（conftest.py monkeypatch DATA_DIR），7 个测试文件
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
│       ├── api/
│       │   ├── index.js                   # 统一出口：http, sse, conversationsApi, settingsApi
│       │   ├── request.js                 # Axios 封装：拦截器解包 {code,message,data}，HTTP 错误弹 Alert
│       │   ├── sse.js                     # SSE 客户端（fetch + ReadableStream，非 EventSource）
│       │   ├── conversations.js           # 会话 API
│       │   └── settings.js                # 设置 API
│       ├── composables/
│       │   ├── useMarkdown.js              # MD 流式渲染入口（组合 markdown/ 子模块）
│       │   ├── useResizableDrawer.js       # 可拖拽调整宽度的侧边栏 composable
│       │   └── markdown/                    # MD 渲染子模块
│       │       ├── engine.js               # markdown-it + DOMPurify + hljs 渲染引擎
│       │       ├── htmlDetector.js          # HTML 代码块自动检测
│       │       └── splitter.js              # 按 \n\n 分段冻结策略
│       ├── stores/
│       │   ├── chat.js                    # Pinia — 会话/消息/流式状态、lastMessageAt 即时排序
│       │   ├── settings.js                # Pinia — API 预设（多配置切换）
│       │   └── alert.js                   # Pinia — 全局弹窗提示
│       ├── components/                    # BaseDialog(通用弹窗基类), ConversationItem(编辑/删除按钮+弹窗),
│       │                                  #   ConversationsDrawer(左→右可拖拽), InputBar, MessageBubble(MD渲染+代码块复制),
│       │                                  #   MessageList, AlertDialog, ModelSelector, PresetSelector,
│       │                                  #   ParamPresetSelector(参数预设选择器), SettingsDrawer(右→左可拖拽),
│       │                                  #   MessageActions, HtmlPreview(HTML 代码/预览切换),
│       │                                  #   ResponseFormatInput, WelcomeBanner
│       ├── views/
│       │   ├── Home.vue                   # 聊天主页面（MessageList + InputBar）
│       │   └── SettingsView.vue           # 设置页面
│       └── router/index.js               # / 和 /settings 两个路由（懒加载）
└── user_data/                             # 运行时数据（conversations.json, messages/, settings.json, logs/）
```

## Conventions

### 后端 (Python/Flask)
- **工厂模式**：`create_app()` 创建 Flask 实例，不在模块顶层持有 app 引用。
- **存储**：JSON 文件存储，`storage.py` 提供全部 CRUD 函数，`threading.Lock` 保护并发写入。数据分三个层级：`conversations.json`（会话索引）、`messages/<conv_id>.json`（每个会话的消息）、`settings.json`（预设配置）。
- **API 响应**：统一使用 `ok(data, message)` / `fail(code, message)` 返回 `{code, message, data}` 结构。code=0 成功，非 0 失败。`fail()` 自动写 error.log 并脱敏敏感字段。
- **API Key**：明文存储在 settings.json 的 api_key 字段中。
- **蓝图注册**：先在 `routes/__init__.py` 中建 `api_bp`，再 import 各子模块触发 `@api_bp.route()` 装饰器，最后 `register_blueprint(api_bp, url_prefix="/api")`。
- **SSE 流**：`stream_with_context()` + `Response(mimetype="text/event-stream")`，`SSEManager` 用 `threading.Event` 支持 `/stop` 取消。
- **测试**：pytest，`conftest.py` 用 `monkeypatch` 将 DATA_DIR/MESSAGES_DIR 等路径指向 tmp_path，防止污染真实数据。

### 前端 (Vue 3 / JS)
- **组合式 API**：Vue 3 SFC 使用 `<script setup>`。
- **状态管理**：Pinia `defineStore`，options API 风格（state/actions）。
- **路由懒加载**：`() => import("@/views/...")`。
- **API 层**：`@/api/request.js` 封装 Axios，拦截器自动解包 `{code,message,data}` → 成功返回 `data`，失败 throw Error。HTTP 错误弹 AlertDialog。
- **SSE 客户端**：基于 `fetch` + `ReadableStream`（非 `EventSource`），支持 `close()` 中止。
- **Markdown 渲染**：`useMarkdown.js` composable — 按 `\n\n` 分段冻结策略，markdown-it 渲染 + DOMPurify 清洗，highlight.js 代码高亮。复制按钮通过 `renderer.rules.fence` 注入，事件委托在硬编码 `.bubble-text` 容器上处理。
- **路径别名**：`@` → `frontend/src`（vite.config.js 中配置）。
- **Electron**：主进程在 `electron/main.cjs`（CommonJS），预加载脚本 `preload.cjs`，`contextIsolation: true`。菜单根据系统语言自动选择中/英文。

## Branch Rules
- **禁止直接在 `main` 分支提交** — `.git/hooks/pre-commit` 已配置阻止 hook。
- 所有开发在 `develop` 分支进行，`main` 仅通过 PR/MR 合并进入。
- 当没有`develop`分支时，但需要进行提交时，需要向用户确认是否创建。

## Notes
- 无 CI/CD 配置，无 linter 配置。
- `.npmrc` 配置了淘宝镜像，CI 或非中文环境可能需要移除。
- 根目录 `run.bat` 可一键启动前后端（Windows）。
- `database.py` 已废弃，新代码全部使用 `storage.py`。残留的 `user_data/chat.db` 可安全忽略。
- 会话命名从前端即时截取前 20 字符，排序用前端 `lastMessageAt` 字段实现发送瞬间重排。
- v1.1.0 新增内联 HTML 渲染：`HtmlPreview.vue` 自动检测 Markdown 输出中的 HTML 代码块，提供代码/预览切换。
- `docs/` 下包含各功能的设计规格和实现计划，新功能开发前建议先查阅。
