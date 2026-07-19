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

# 后端测试
cd backend
python -m pytest                           # 自动使用 tmp_path 隔离 DB
```

## Architecture

```
chat/
├── backend/
│   ├── run.py                             # 入口：create_app() → app.run()
│   ├── config.json                        # Flask 配置（DEBUG/HOST/PORT/SECRET_KEY）
│   ├── app/
│   │   ├── __init__.py                    # create_app() 工厂：加载配置、CORS、注册蓝图、init_db
│   │   ├── database.py                    # SQLite 连接管理 (g-based)、建表
│   │   ├── routes/
│   │   │   ├── __init__.py                # Blueprint("api", __name__)
│   │   │   ├── conversations.py           # /api/conversations + SSE 流式 chat
│   │   │   ├── settings.py                # /api/settings CRUD
│   │   │   └── example.py                 # /api/hello 示例
│   │   ├── services/
│   │   │   ├── ai.py                      # stream_chat() — 调用 OpenAI 兼容 API，SSE 逐 token 产出
│   │   │   └── sse_manager.py             # SSEManager — {conv_id: threading.Event}，支持 /stop 取消流
│   │   └── utils/
│   │       ├── response.py                # ok() / fail() 统一响应 + 错误日志
│   └── tests/                             # pytest，conftest.py 用 monkeypatch 隔离 DB
├── frontend/
│   ├── vite.config.js                     # Vite 配置，/api → 127.0.0.1:5000 代理
│   ├── electron/main.cjs                  # Electron 主进程，从 JSON 构建菜单
│   └── src/
│       ├── main.js                        # Vue 入口：createApp → Pinia → Router
│       ├── api/
│       │   ├── request.js                 # Axios 封装：拦截器解包 {code,message,data}
│       │   ├── sse.js                     # SSE 客户端
│       │   ├── conversations.js           # 会话 API
│       │   └── settings.js                # 设置 API
│       ├── stores/
│       │   ├── chat.js                    # Pinia — 会话/消息/流式状态
│       │   └── settings.js                # Pinia — API 配置
│       ├── components/                    # ConversationItem, InputBar, MessageBubble, Sidebar 等
│       ├── views/
│       │   ├── Home.vue                   # 聊天主页面
│       │   └── SettingsView.vue           # 设置页面
│       └── router/index.js               # / 和 /settings 两个路由
└── user_data/                             # 运行时数据（chat.db, logs/）
```

## Conventions

### 后端 (Python/Flask)
- **工厂模式**：`create_app()` 创建 Flask 实例，不在模块顶层持有 app 引用。
- **数据库**：直接用 `sqlite3` 原生 SQL，无 ORM。连接通过 `g.db` 绑定到请求生命周期，teardown 时关闭。
- **API 响应**：统一使用 `ok(data, message)` / `fail(code, message)` 返回 `{code, message, data}` 结构。code=0 成功，非 0 失败。
- **API Key**：明文存储在 settings 表的 api_key 字段中。
- **蓝图注册**：先在 `routes/__init__.py` 中建 `api_bp`，再 import 各子模块触发 `@api_bp.route()` 装饰器，最后 `register_blueprint(api_bp, url_prefix="/api")`。
- **测试**：pytest，`conftest.py` 用 `monkeypatch` 将 DB_PATH 指向 tmp_path，防止污染真实数据。无 mock 框架依赖。

### 前端 (Vue 3 / JS)
- **组合式 API**：Vue 3 SFC 使用 `<script setup>`。
- **状态管理**：Pinia `defineStore`，options API 风格（state/actions）。
- **路由懒加载**：`() => import("@/views/...")`。
- **API 层**：`@/api/request.js` 封装 Axios，拦截器自动解包 `{code,message,data}` → 成功返回 `data`，失败 throw Error。
- **路径别名**：`@` → `frontend/src`（vite.config.js 中配置）。
- **Electron**：主进程在 `electron/main.cjs`（CommonJS），预加载脚本 `preload.cjs`，`contextIsolation: true`。

## Notes
- 无 CI/CD 配置，无 linter 配置。
