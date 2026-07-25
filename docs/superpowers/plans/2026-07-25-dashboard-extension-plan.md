# Dashboard 悬浮面板 + 扩展系统增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task.

**Goal:** 为扩展系统新增 `panel`（前端浮层）和 `api_route`（后端自定义 API）两个扩展点，并基于此开发 Dashboard 悬浮面板扩展。

**Architecture:** 修改 loader.py 支持 api_route 调用；App.vue 添加 panel slot；Dashboard 扩展后端写会话级指标 JSON，前端渲染可拖动悬浮面板。

**Tech Stack:** Python 3 + Flask（后端），Vue 3（前端组件使用 `h()` 渲染函数），现有 JSON 存储模式。

## Global Constraints

- 所有扩展代码在 `user_data/extensions/` 下（内置示例）或 `test_expand/` 下（此扩展）
- Dashboard 指标按会话隔离，存储于 `user_data/extensions/dashboard/<conv_id>.json`
- 前端组件使用 `h()` 渲染函数，无需编译
- 悬浮面板收起态 40×40px 圆形，展开态 180×400px（9:20）
- 位置持久化到 localStorage key `dashboard-position`
- 每 3 秒轮询 metrics API

---

## File Structure

```
Modify:
  backend/app/extensions/loader.py          # + api_route 扩展点处理
  backend/app/extensions/__init__.py        # init() 传入 api_bp
  backend/app/__init__.py                   # create_app() 传入 api_bp
  frontend/src/App.vue                      # + <ExtensionSlot name="panel" />

Create:
  test_expand/dashboard/manifest.json
  test_expand/dashboard/backend.py
  test_expand/dashboard/frontend/index.js
  test_expand/dashboard/frontend/components/DashboardFloating.js
```

---

### Task 1: api_route 扩展点（loader + init 改造）

**Files:**
- Modify: `backend/app/extensions/loader.py:18-21,42,98` — EXT_POINT_TO_FUNC + load_extension 签名
- Modify: `backend/app/extensions/__init__.py:14,15,27` — init + reload_extension 传入 api_bp
- Modify: `backend/app/__init__.py:49` — create_app 传入 api_bp

**Interfaces:**
- Consumes: `api_bp` from `app.routes`
- Produces: `load_extension(ext_id, dispatcher, api_bp=None)`, `load_all_enabled(dispatcher, api_bp=None)`, `ExtensionManager.init(api_bp)`, `ExtensionManager.reload_extension(ext_id, api_bp=None)`

- [ ] **Step 1: 修改 loader.py**

`EXT_POINT_TO_FUNC` 添加 `api_route`：
```python
EXT_POINT_TO_FUNC = {
    "chat.post_receive": "on_chat_post_receive",
    "chat.pre_send": "on_chat_pre_send",
    "api_route": "register_api_routes",
}
```

`load_extension` 签名改为 `def load_extension(ext_id, dispatcher, api_bp=None)`，在钩子注册之后、return 之前添加：
```python
    # api_route 扩展点：调用 register_api_routes(api_bp)
    if "api_route" in backend_points and api_bp is not None:
        register_fn = getattr(module, "register_api_routes", None)
        if register_fn:
            try:
                register_fn(api_bp)
                registered.append("api_route")
            except Exception:
                logger.exception(f"扩展 {ext_id} 注册 API 路由失败")
```

`load_all_enabled` 签名改为 `def load_all_enabled(dispatcher, api_bp=None)`，内部调用 `load_extension(ext_id, dispatcher, api_bp)`。

- [ ] **Step 2: 修改 ExtensionManager**

`__init__.py` 中 `init` 签名：`def init(self, api_bp=None)`，内部 `self._loaded = load_all_enabled(self.dispatcher, api_bp)`。

`reload_extension` 签名：`def reload_extension(self, ext_id, api_bp=None)`，内部 `unload_extension(...)` 后 `result = load_extension(ext_id, self.dispatcher, api_bp)`。

- [ ] **Step 3: 修改 create_app()**

`backend/app/__init__.py` 中，`import app.routes.extensions` 之后获取 `api_bp` 并传入：
```python
from app.extensions import get_extension_manager
from app.routes import api_bp as _ext_api_bp
os.makedirs(os.path.join(...), exist_ok=True)
get_extension_manager().init(api_bp=_ext_api_bp)
```

需要调整：`api_bp` 来自 `app.routes` 模块的 `from app.routes import api_bp`，已在 create_app 顶部导入。

- [ ] **Step 4: 运行测试**

```bash
cd backend && python -m pytest -v
```
预期：89 passed（无回归）

- [ ] **Step 5: 提交**

```bash
git add backend/app/extensions/loader.py backend/app/extensions/__init__.py backend/app/__init__.py
git commit -m "feat: add api_route extension point (register_api_routes callback)"
```

---

### Task 2: panel 前端扩展点

**Files:**
- Modify: `frontend/src/App.vue` — 在 app-shell 内添加 `<ExtensionSlot name="panel" />`

- [ ] **Step 1: 在 App.vue 添加 panel slot**

在 `<AlertDialog />` 之前添加：
```vue
    <ExtensionSlot name="panel" />
    <AlertDialog />
```

导入已在 Task 14（之前的 message_decorator 集成）中添加，无需重复。

- [ ] **Step 2: 构建验证**

```bash
cd frontend && npx vite build
```
预期：build success

- [ ] **Step 3: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: add panel extension slot for global floating components"
```

---

### Task 3: Dashboard 扩展 — manifest + backend

**Files:**
- Create: `test_expand/dashboard/manifest.json`
- Create: `test_expand/dashboard/backend.py`

- [ ] **Step 1: 创建 manifest.json**

```json
{
  "id": "dashboard",
  "name": "Dashboard 悬浮面板",
  "version": "1.0.0",
  "author": "Chat Team",
  "description": "可拖动的悬浮面板，显示上下文用量和会话指标",
  "permissions": ["read:conversations", "hook:chat"],
  "ext_points": {
    "backend": ["chat.post_receive", "api_route"],
    "frontend": ["panel"]
  },
  "min_app_version": "1.2.0"
}
```

- [ ] **Step 2: 创建 backend.py**

```python
import json
import os
import threading

_lock = threading.Lock()

# 存储目录：user_data/extensions/dashboard/
_STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))),
    "user_data", "extensions", "dashboard"
)


def _metrics_path(conv_id):
    return os.path.join(_STORAGE_DIR, f"{conv_id}.json")


def _read_metrics(conv_id):
    path = _metrics_path(conv_id)
    if not os.path.exists(path):
        return {
            "request_count": 0,
            "total_completion_tokens": 0,
            "total_prompt_tokens": 0,
            "last_hit_rate": 0.0,
            "updated_at": "",
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_metrics(conv_id, metrics):
    os.makedirs(_STORAGE_DIR, exist_ok=True)
    with _lock:
        with open(_metrics_path(conv_id), "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)


def _estimate_tokens(text):
    """简易 token 估算：中文 ~1.5 char/token，英文 ~4 char/token"""
    return max(1, len(text) // 3)


def on_chat_post_receive(ctx):
    conv_id = ctx.get("conversation_id")
    if not conv_id:
        return None

    metrics = _read_metrics(conv_id)
    metrics["request_count"] = metrics.get("request_count", 0) + 1

    # 累加 token
    response_body = ctx.get("response_body", {})
    content = response_body.get("content", "")
    reasoning = response_body.get("reasoning_content", "")
    metrics["total_completion_tokens"] += _estimate_tokens(content + reasoning)

    # 估算 prompt tokens
    messages = ctx.get("messages", [])
    prompt_text = "".join(m.get("content", "") for m in messages)
    metrics["total_prompt_tokens"] = _estimate_tokens(prompt_text)

    # 上下文命中率
    world_info_entries = ctx.get("world_info_entries", [])
    if world_info_entries:
        ai_content = content.lower()
        hit_count = sum(
            1 for e in world_info_entries
            if (e.get("key", "").lower() in ai_content or
                e.get("content", "").lower()[:50] in ai_content)
        )
        metrics["last_hit_rate"] = round(hit_count / len(world_info_entries), 2)

    from datetime import datetime, timezone
    metrics["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_metrics(conv_id, metrics)
    return None


def register_api_routes(api_bp):
    @api_bp.route("/ext/dashboard/<conv_id>/metrics")
    def dashboard_metrics(conv_id):
        from flask import jsonify
        metrics = _read_metrics(conv_id)
        return jsonify({
            "code": 0,
            "message": "ok",
            "data": metrics,
        })
```

- [ ] **Step 3: 提交**

```bash
git add test_expand/dashboard/manifest.json test_expand/dashboard/backend.py
git commit -m "feat: dashboard extension — manifest + backend (metrics storage + API)"
```

---

### Task 4: Dashboard 扩展 — 前端悬浮面板组件

**Files:**
- Create: `test_expand/dashboard/frontend/index.js`
- Create: `test_expand/dashboard/frontend/components/DashboardFloating.js`

- [ ] **Step 1: 创建 frontend/index.js**

```javascript
import DashboardFloating from './components/DashboardFloating.js';

if (!window.__EXTENSION_REGISTRY__) {
  window.__EXTENSION_REGISTRY__ = {};
}
window.__EXTENSION_REGISTRY__['dashboard'] = {
  panel: [DashboardFloating],
};
```

- [ ] **Step 2: 创建 DashboardFloating.js**

```javascript
import { h, ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';

const MAX_TOKENS = 100_000_000;  // 100M

function formatTokens(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}

export default {
  name: 'DashboardFloating',
  props: { api: Object },
  setup(props) {
    const expanded = ref(false);
    const metrics = ref(null);
    const position = ref({ x: null, y: null });
    const dragging = ref(false);
    const dragStart = ref({ x: 0, y: 0 });
    let pollTimer = null;

    // 读 localStorage 恢复位置
    const saved = localStorage.getItem('dashboard-position');
    if (saved) {
      try { position.value = JSON.parse(saved); } catch(e) {}
    }

    // 默认位置：右下角
    const x = computed(() => position.value.x ?? window.innerWidth - 60);
    const y = computed(() => position.value.y ?? window.innerHeight - 140);

    const ratio = computed(() => {
      const t = metrics.value?.total_prompt_tokens || 0;
      return Math.min(100, Math.round((t / MAX_TOKENS) * 100));
    });

    const hitColor = computed(() => {
      const r = metrics.value?.last_hit_rate || 0;
      return r >= 0.6 ? '#4caf50' : r >= 0.3 ? '#ff9800' : '#f44336';
    });

    async function fetchMetrics() {
      const conv = props.api?.getCurrentConversation?.();
      if (!conv?.id) return;
      try {
        const resp = await fetch(`/api/ext/dashboard/${conv.id}/metrics`);
        const json = await resp.json();
        if (json.code === 0) metrics.value = json.data;
      } catch(e) {}
    }

    function onMouseDown(e) {
      if (expanded.value) return;
      dragging.value = true;
      dragStart.value = {
        x: e.clientX - x.value,
        y: e.clientY - y.value,
      };
      e.preventDefault();
    }
    function onMouseMove(e) {
      if (!dragging.value) return;
      position.value = {
        x: e.clientX - dragStart.value.x,
        y: e.clientY - dragStart.value.y,
      };
    }
    function onMouseUp() {
      if (dragging.value) {
        localStorage.setItem('dashboard-position', JSON.stringify(position.value));
      }
      dragging.value = false;
    }

    function onClick() {
      if (!dragging.value) expanded.value = !expanded.value;
    }

    function onOutsideClick(e) {
      // 简易外部点击检测
    }

    onMounted(() => {
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
      fetchMetrics();
      pollTimer = setInterval(fetchMetrics, 3000);
    });
    onBeforeUnmount(() => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      clearInterval(pollTimer);
    });

    return () => {
      const btn = h('div', {
        onMousedown: onMouseDown,
        onClick: onClick,
        style: {
          position: 'fixed', left: x.value+'px', top: y.value+'px',
          width: '40px', height: '40px', borderRadius: '50%',
          background: '#4a90d9', color: '#fff', display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          cursor: dragging.value ? 'grabbing' : 'grab',
          fontSize: '18px', zIndex: 9999,
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          userSelect: 'none',
          transition: expanded.value ? 'all 0.2s' : 'none',
        }
      }, '📊');

      if (!expanded.value || !metrics.value) return btn;

      const pct = ratio.value;
      const barColor = pct > 80 ? '#f44336' : pct > 50 ? '#ff9800' : '#4caf50';

      const panel = h('div', {
        style: {
          position: 'fixed', left: x.value+'px', top: y.value+'px',
          width: '180px', height: '400px', borderRadius: '12px',
          background: '#fff', boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
          backdropFilter: 'blur(8px)', zIndex: 9998, padding: '12px',
          display: 'flex', flexDirection: 'column', gap: '10px',
          fontSize: '12px', color: '#333', overflow: 'hidden',
        }
      }, [
        // 上下文窗口
        h('div', { style: { fontWeight: 600, fontSize: '13px' } }, '📊 上下文窗口'),
        h('div', { style: { marginTop: '4px' } }, [
          h('div', { style: { display:'flex', justifyContent:'space-between' } }, [
            h('span', null, `${formatTokens(metrics.value.total_prompt_tokens)} / 100M`),
            h('span', { style: { color: barColor } }, `${pct}%`),
          ]),
          h('div', {
            style: {
              marginTop: '4px', height: '6px', borderRadius: '3px',
              background: '#eee', overflow: 'hidden',
            }
          }, [
            h('div', {
              style: {
                width: pct+'%', height: '100%', borderRadius: '3px',
                background: barColor, transition: 'width 0.3s',
              }
            }),
          ]),
        ]),

        h('div', { style: { borderTop:'1px solid #eee', margin:'6px 0' } }),

        // 会话指标
        h('div', { style: { fontWeight: 600, fontSize: '13px' } }, '📈 会话指标'),
        h('div', { style: { display:'flex', flexDirection:'column', gap:'8px', marginTop:'4px' } }, [
          h('div', { style: { display:'flex', justifyContent:'space-between' } }, [
            h('span', null, '命中率'),
            h('span', { style: { color: hitColor.value, fontWeight: 600 } },
              `${Math.round((metrics.value.last_hit_rate||0)*100)}%`),
          ]),
          h('div', { style: { display:'flex', justifyContent:'space-between' } }, [
            h('span', null, '请求次数'),
            h('span', { style: { fontWeight: 600 } }, String(metrics.value.request_count)),
          ]),
          h('div', { style: { display:'flex', justifyContent:'space-between' } }, [
            h('span', null, '累计 AI token'),
            h('span', { style: { fontWeight: 600 } },
              formatTokens(metrics.value.total_completion_tokens)),
          ]),
        ]),
      ]);

      return h('div', null, [panel, btn]);
    };
  },
};
```

- [ ] **Step 3: 提交**

```bash
git add test_expand/dashboard/frontend/
git commit -m "feat: dashboard extension — frontend floating panel component"
```

---

### Task 5: 安装验证

- [ ] **Step 1: 复制扩展到安装目录**

```bash
cp -r test_expand/dashboard user_data/extensions/dashboard
```

- [ ] **Step 2: 通过 API 注册并启用**

```bash
# 手动写入注册表（模拟安装→审批流程）
cd backend && python -c "
from app.extensions.registry import add_extension, write_registry
write_registry({'extensions': {}})
add_extension('dashboard', {
    'version': '1.0.0', 'enabled': True,
    'installed_at': '2026-07-25T00:00:00Z',
    'install_method': 'zip',
    'permissions_granted': ['read:conversations', 'hook:chat']
})
"
```

- [ ] **Step 3: 启动应用验证**

```bash
# 终端1
cd backend && python run.py
# 终端2
cd frontend && npm run dev
```

预期：页面右下角出现蓝色 📊 圆纽，点击展开面板。

- [ ] **Step 4: 运行全部测试**

```bash
cd backend && python -m pytest -v
```
预期：89 passed

---

## Execution Order

Task 1 → Task 2 → Task 3 → Task 4 → Task 5

Tasks 1-2 是扩展系统增强（必须先行），Tasks 3-5 是 Dashboard 扩展开发与验证。
