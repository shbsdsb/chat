# Chat — Vue 3 + Flask + Electron 桌面聊天应用

## Project
前后端分离的 AI 聊天桌面应用。前端 Vue 3 SPA 经 Vite 构建、Electron 打包；后端 Flask REST API，通过 SSE 流式转发 OpenAI 兼容的 chat completions。数据存储在项目根 `user_data/` 下的 SQLite（chat.db）中。

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
python -m pytest                           # 自动使用 tmp_path 隔离 DB，36 tests
```

## Architecture

```
chat/
├── run.bat                                # Windows 一键启动脚本
├── backend/
│   ├── run.py                             # 入口：create_app() → app.run()
│   ├── config.json                        # Flask 配置（DEBUG/HOST/PORT/SECRET_KEY）
│   ├── requirements.txt                   # flask, flask-cors, requests
│   ├── app/
│   │   ├── __init__.py                    # create_app() 工厂：加载配置、CORS、注册蓝图、init_db
│   │   ├── database.py                    # SQLite 连接管理 (g-based)、建表（conversations/messages/settings）
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
│   └── tests/                             # pytest（conftest.py monkeypatch DB_PATH），6 个测试文件
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
│       ├── main.js                        # Vue 入口：createApp → Pinia → Router
│       ├── api/
│       │   ├── request.js                 # Axios 封装：拦截器解包 {code,message,data}，HTTP 错误弹 Alert
│       │   ├── sse.js                     # SSE 客户端（fetch + ReadableStream，非 EventSource）
│       │   ├── conversations.js           # 会话 API
│       │   └── settings.js                # 设置 API
│       ├── stores/
│       │   ├── chat.js                    # Pinia — 会话/消息/流式状态、AI 版本切换
│       │   ├── settings.js                # Pinia — API 预设（多配置切换）
│       │   └── alert.js                   # Pinia — 全局弹窗提示
│       ├── components/                    # ConversationItem, InputBar, MessageBubble, MessageList,
│       │                                  #   Sidebar, AlertDialog, ModelSelector, PresetSelector,
│       │                                  #   SettingsDrawer, MessageActions, WelcomeBanner 等
│       ├── views/
│       │   ├── Home.vue                   # 聊天主页面
│       │   └── SettingsView.vue           # 设置页面
│       └── router/index.js               # / 和 /settings 两个路由（懒加载）
└── user_data/                             # 运行时数据（chat.db, logs/）
```

## Conventions

### 后端 (Python/Flask)
- **工厂模式**：`create_app()` 创建 Flask 实例，不在模块顶层持有 app 引用。
- **数据库**：直接用 `sqlite3` 原生 SQL，无 ORM。连接通过 `g.db` 绑定到请求生命周期，teardown 时关闭。WAL 模式 + 外键约束。
- **API 响应**：统一使用 `ok(data, message)` / `fail(code, message)` 返回 `{code, message, data}` 结构。code=0 成功，非 0 失败。`fail()` 自动写 error.log 并脱敏敏感字段。
- **API Key**：明文存储在 settings 表的 api_key 字段中。
- **蓝图注册**：先在 `routes/__init__.py` 中建 `api_bp`，再 import 各子模块触发 `@api_bp.route()` 装饰器，最后 `register_blueprint(api_bp, url_prefix="/api")`。
- **SSE 流**：`stream_with_context()` + `Response(mimetype="text/event-stream")`，`SSEManager` 用 `threading.Event` 支持 `/stop` 取消。
- **测试**：pytest，`conftest.py` 用 `monkeypatch` 将 DB_PATH 指向 tmp_path，防止污染真实数据。无 mock 框架依赖。

### 前端 (Vue 3 / JS)
- **组合式 API**：Vue 3 SFC 使用 `<script setup>`。
- **状态管理**：Pinia `defineStore`，options API 风格（state/actions）。
- **路由懒加载**：`() => import("@/views/...")`。
- **API 层**：`@/api/request.js` 封装 Axios，拦截器自动解包 `{code,message,data}` → 成功返回 `data`，失败 throw Error。HTTP 错误弹 AlertDialog。
- **SSE 客户端**：基于 `fetch` + `ReadableStream`（非 `EventSource`），支持 `close()` 中止。
- **路径别名**：`@` → `frontend/src`（vite.config.js 中配置）。
- **Electron**：主进程在 `electron/main.cjs`（CommonJS），预加载脚本 `preload.cjs`，`contextIsolation: true`。菜单根据系统语言自动选择中/英文。

## Notes
- 无 CI/CD 配置，无 linter 配置。
- `.npmrc` 配置了淘宝镜像，CI 或非中文环境可能需要移除。
- 根目录 `run.bat` 可一键启动前后端（Windows）。
