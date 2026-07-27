# 扩展功能开关 — 设计规格

> **日期**：2026-07-25
> **状态**：设计完成，待实施

## 1. 概述

### 1.1 问题

当前扩展管理页面（ExtensionManager.vue）仅支持整体启用/禁用扩展。用户无法：
- 查看扩展的详细信息（权限、扩展点、安装信息）
- 按功能粒度开关扩展内的各项子功能

### 1.2 目标

- 新增扩展详情抽屉，展示 manifest 全部信息
- 扩展作者通过 manifest.json 声明可配置的功能开关
- 用户可在详情页按需开关每个功能
- 开关状态持久化到独立 settings.json

---

## 2. manifest.json 扩展

### 2.1 `features` 字段

扩展作者在 manifest.json 中新增可选字段 `features`：

```json
{
  "features": [
    {
      "id": "show-token-count",
      "label": "显示 Token 计数",
      "description": "在面板中显示每次对话的 Token 消耗量",
      "default": true
    }
  ]
}
```

**字段约定：**
- `features` 可选 — 省略时详情页不显示功能开关区域
- `id` 在扩展内唯一，用于 key 和持久化
- `default` 决定首次安装时的初始状态
- `label` 展示给用户的功能名称
- `description` 辅助说明文本

### 2.2 settings.json

用户修改后的开关状态持久化到 `user_data/extensions/<ext_id>/settings.json`：

```json
{
  "features": {
    "show-token-count": true,
    "show-context-usage": false
  }
}
```

**读取策略：**
- 文件不存在时，根据 manifest 的 `default` 值自动生成
- 如果 manifest 也没有 `features` 声明，返回空对象 `{}`

---

## 3. 后端 API

在 `backend/app/routes/extensions.py` 中新增两个端点。

### 3.1 GET /api/extensions/\<ext_id\>/settings

读取扩展 settings，不存在时按 manifest features.default 生成默认值。

**响应：**
```json
{
  "code": 0,
  "data": {
    "features": {
      "show-token-count": true,
      "show-context-usage": true,
      "auto-refresh": false
    }
  }
}
```

### 3.2 PUT /api/extensions/\<ext_id\>/settings

保存功能开关状态。

**请求体：**
```json
{
  "features": {
    "show-token-count": false
  }
}
```

**校验规则：**
- ext_id 必须存在于 registry 中
- 请求中的 feature id 必须在 manifest 的 `features` 数组中声明（防止注入）
- 值必须是 boolean 类型
- 写入 `user_data/extensions/<ext_id>/settings.json`

### 3.3 首次安装初始化

在 `confirm_extension()` 路由中，安装确认后根据 manifest 的 `features` 字段的 `default` 值写入初始 `settings.json`。这确保 settings.json 在扩展安装时就存在。

---

## 4. 前端

### 4.1 ExtensionManager.vue（修改）

每个扩展卡片右侧新增 **"详情" 按钮**：

```
[已启用 ☑] [更新] [卸载] [详情 ▸]
```

点击触发 `store.openDetail(ext)`。改动约 3 行。

### 4.2 ExtensionDetailDrawer.vue（新建）

右侧滑出抽屉，复用 `useResizableDrawer` composable。默认宽度 360px，可拖拽调整。

**布局（五个区域）：**

1. **标题栏**：扩展名 + 版本 + 作者 + 关闭按钮
2. **基本信息**：描述、ID、安装时间、安装方式
3. **权限列表**：permissions 数组逐条展示
4. **扩展点**：后端钩子 + 前端面板列表
5. **功能开关**（条件渲染）：每个 feature 一个 toggle switch（checkbox），含 label + description

**交互细节：**
- 切换开关即时调用 `PUT /settings` 保存
- 加载中显示占位状态
- 保存失败回滚开关状态 + 弹出错误提示

### 4.3 stores/extensions.js（修改）

新增状态和动作：

```javascript
state: () => ({
  detailExt: null,        // 当前查看详情的扩展
  detailSettings: null,   // { features: {...} }
  detailLoading: false,
}),

actions: {
  async openDetail(ext) {
    this.detailExt = ext;
    this.detailLoading = true;
    try {
      this.detailSettings = await extensionsApi.getSettings(ext.id);
    } finally {
      this.detailLoading = false;
    }
  },
  closeDetail() {
    this.detailExt = null;
    this.detailSettings = null;
  },
  async toggleFeature(extId, featureId, value) {
    // 乐观更新
    const previous = this.detailSettings.features[featureId];
    this.detailSettings.features[featureId] = value;
    try {
      await extensionsApi.saveSettings(extId, this.detailSettings);
    } catch (e) {
      // 回滚
      this.detailSettings.features[featureId] = previous;
      throw e;
    }
  },
}
```

### 4.4 api/extensions.js（修改）

新增两个方法：

```javascript
getSettings(extId) {
  return http.get(`/extensions/${extId}/settings`);
},
saveSettings(extId, settings) {
  return http.put(`/extensions/${extId}/settings`, settings);
},
```

### 4.5 ExtensionSlot 运行时传入

ExtensionSlot 渲染扩展组件时 props 中新增 `settings` 对象：

```javascript
// ExtensionSlot.vue 修改
result.push({
  comp: markRaw(Comp),
  props: {
    message: props.message,
    conversation: props.conversation,
    api: createExtensionApi(ext.id),
    settings: settingsMap[ext.id] || {},   // 新增
  },
});
```

扩展作者在组件中读取：
```javascript
props: ['api', 'settings'],
setup(props) {
  // 根据开关决定是否渲染某功能
  const showTokenCount = computed(() => props.settings.features?.['show-token-count']);
}
```

ExtensionSlot 需要在渲染前批量拉取所有已启用扩展的 settings（可合并为一个批量请求，或逐个拉取后缓存）。

---

## 5. 数据流

```
manifest.json (features 声明)
       │
       ▼
confirm API (首次安装) → 按 default 生成 settings.json
       │
       ├── GET /settings ← ExtensionDetailDrawer (读取展示)
       │
       ├── PUT /settings ← 用户拨动开关 → settings.json 更新
       │
       └── ExtensionSlot 渲染时 → props.settings → 扩展组件按需渲染
```

---

## 6. 约束与边界情况

| 场景 | 行为 |
|------|------|
| manifest 无 `features` 字段 | 详情页正常展示信息，不显示功能开关区域 |
| settings.json 不存在 | GET 时按 manifest default 自动生成后返回 |
| 用户传入未知 feature id | PUT 时服务器校验，拒绝并返回 400 |
| 扩展有 features 但 settings.json 为空 | 按 default 初始化展示 |
| ExtensionSlot 加载时 settings 未就绪 | 扩展收到空 `{}`，视为全部默认关闭，加载完成后更新 |

---

## 7. 改动范围

| 文件 | 操作 | 行数估算 |
|------|------|---------|
| `backend/app/routes/extensions.py` | 修改 | +45（新增 2 个端点 + confirm 初始化） |
| `frontend/src/components/ExtensionManager.vue` | 修改 | +5（详情按钮 + 抽屉引入） |
| `frontend/src/components/ExtensionDetailDrawer.vue` | 新建 | ~200 |
| `frontend/src/stores/extensions.js` | 修改 | +25 |
| `frontend/src/api/extensions.js` | 修改 | +5 |
| `frontend/src/extensions/ExtensionSlot.vue` | 修改 | +10 |

**总估算**：~290 行新增/修改代码，1 个新文件 + 5 个已有文件修改。
