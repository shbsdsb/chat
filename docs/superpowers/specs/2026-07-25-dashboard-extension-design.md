# Dashboard 悬浮面板扩展 + 扩展系统增强

> 状态：设计已确认，待实现
> 日期：2026-07-25

---

## 一、目标

1. **扩展系统增强：** 新增 `panel`（前端全局浮层）和 `api_route`（后端自定义 API）两个扩展点
2. **Dashboard 扩展：** 可拖动的悬浮圆纽，展开为 9:20 面板，显示当前对话的上下文用量和会话指标

---

## 二、扩展系统增强

### 2.1 前端：`panel` 扩展点

在 `App.vue` 的 `app-shell` 内渲染 `<ExtensionSlot name="panel" />`。

扩展注册方式（`frontend/index.js`）：
```javascript
window.__EXTENSION_REGISTRY__['my-ext-id'] = {
  panel: [MyFloatingWidget],
};
```

manifest 声明：
```json
"ext_points": { "frontend": ["panel"] }
```

ExtensionSlot 已有支持多 slot 的注册表遍历逻辑，只需在 App.vue 添加一个 `<ExtensionSlot name="panel" />` 即可。

### 2.2 后端：`api_route` 扩展点

扩展的 `backend.py` 导出 `register_api_routes(api_bp)` 函数：

```python
def register_api_routes(api_bp):
    @api_bp.route("/ext/<ext_id>/metrics")
    def get_metrics():
        ...
```

`loader.py` 改动：
- `EXT_POINT_TO_FUNC` 新增 `"api_route": "register_api_routes"`
- `load_extension` 中检测到 `api_route` 时调用 `module.register_api_routes(api_bp)`
- 需将 `api_bp` 传入 loader

manifest 声明：
```json
"ext_points": { "backend": ["chat.post_receive", "api_route"] }
```

---

## 三、Dashboard 扩展结构

```
test_expand/dashboard/
├── manifest.json
├── backend.py
└── frontend/
    ├── index.js
    └── components/
        └── DashboardFloating.vue
```

### 3.1 manifest.json

```json
{
  "id": "dashboard",
  "name": "Dashboard 悬浮面板",
  "version": "1.0.0",
  "permissions": ["read:conversations", "hook:chat"],
  "ext_points": {
    "backend": ["chat.post_receive", "api_route"],
    "frontend": ["panel"]
  },
  "min_app_version": "1.2.0"
}
```

### 3.2 后端存储

文件：`user_data/extensions/dashboard/<conv_id>.json`

```json
{
  "request_count": 12,
  "total_completion_tokens": 45200,
  "total_prompt_tokens": 188000,
  "last_hit_rate": 0.65,
  "updated_at": "2026-07-25T10:00:00Z"
}
```

- 每字段仅限当前对话，不跨对话累加
- 命中率：对比 `world_info_entries` 的 key/content 是否出现在 AI 响应文本中

### 3.3 chat.post_receive 钩子

```python
def on_chat_post_receive(ctx):
    conv_id = ctx["conversation_id"]
    # 读取现有指标
    metrics = _read_metrics(conv_id)
    # 累加请求次数
    metrics["request_count"] = metrics.get("request_count", 0) + 1
    # 累加 token（从 response_body 的 usage 字段，如有）
    # 否则用 content 长度 / 4 估算
    # 计算命中率
    # 写回
    _write_metrics(conv_id, metrics)
    return None
```

### 3.4 API 端点

`GET /api/ext/dashboard/<conv_id>/metrics` → 返回指标 JSON

### 3.5 前端 UI

**收起态：** 40×40px 圆形，右下角默认位置（距右 20px，距底 80px），📊 图标，可拖拽移动，位置存 localStorage。

**展开态：** 宽 180px × 高 400px（9:20），border-radius: 12px，白底 + 阴影 + backdrop-filter blur。

上半部 — 上下文窗口：
- 显示 `total_prompt_tokens` 为已用上下文
- 进度条距 100M token 上限（100,000,000）
- 格式：`68.2M / 100M`

下半部 — 会话指标：
- 命中率：`last_hit_rate` × 100，带颜色圆点
- 请求次数：`request_count`
- 累计 AI token：`total_completion_tokens`，自动格式化（K/M）

**交互：**
- 圆纽左键点击 → 展开
- 点击面板外部 → 收起
- 面板内点击不收起
- 展开时不可拖动
- 每 3 秒轮询 metrics API 刷新数据

---

## 四、实现阶段

| 阶段 | 内容 | 涉及文件 |
|------|------|---------|
| A | panel 扩展点 + api_route 扩展点 | App.vue, loader.py, ExtensionSlot.vue |
| B | Dashboard 扩展开发 | test_expand/dashboard/ 下全部文件 |
| C | 集成验证 | 安装扩展、端到端测试 |
