# 扩展功能分组开关 — 设计规格

> **日期**：2026-07-25
> **状态**：设计完成，待实施
> **依赖**：`2026-07-25-extension-feature-toggles-design.md`（功能开关基础）

## 1. 概述

### 1.1 问题

当前 features 是扁平数组，所有功能开关平铺展示。用户希望将相关功能归类到"模块"下，模块作为一个整体可开关，子功能在模块内独立控制。

### 1.2 目标

- manifest features 支持 `type: "group"` 声明模块，内含 `children` 子功能数组
- 抽屉 UI 中模块以可折叠卡片展示，含模块级开关 + 子功能独立开关
- 模块关 → 所有子功能自动关闭；模块开 → 子功能恢复关闭前的状态（记忆模式）
- settings.json 以扁平点号键 (`module.child`) 持久化，向后兼容现有扁平项

---

## 2. manifest.json 扩展

### 2.1 features 嵌套格式

在现有 features 数组基础上扩展，**向后兼容**——无 `type` 的项仍为叶子功能。

```json
"features": [
  {
    "id": "show-context-usage",
    "label": "显示上下文用量",
    "default": true
  },
  {
    "id": "session-metrics",
    "label": "会话指标",
    "type": "group",
    "default": true,
    "children": [
      { "id": "hit-rate", "label": "命中率", "default": true },
      { "id": "request-count", "label": "请求次数", "default": true },
      { "id": "completion-tokens", "label": "累计 AI Token", "default": true }
    ]
  }
]
```

**字段约定的增量：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | `"group"` 表示模块，省略表示叶子功能 |
| `children` | array | 仅 `type: "group"` 时有，结构与叶子功能相同 |
| `children[].id` | string | 子功能标识，在模块内唯一 |
| `children[].default` | boolean | 子功能初始状态 |

**约束：**
- 仅支持一级嵌套（`children` 内不再含 `type: "group"`）
- 模块的 `default` 控制模块开关初始状态
- `id` 在 features 数组内全局唯一（叶子 id 和模块 id 不冲突）

---

## 3. settings.json 持久化

### 3.1 扁平点号键

```json
{
  "features": {
    "show-context-usage": true,
    "auto-refresh": false,
    "session-metrics": true,
    "session-metrics.hit-rate": true,
    "session-metrics.request-count": false,
    "session-metrics.completion-tokens": true
  }
}
```

**规则：**
- 叶子功能的 key 就是其 `id`
- 子功能的 key 为 `模块id.子功能id`
- 模块关闭时子功能值写为 `false`，但**保留键**（记忆）
- 模块重新开启时不覆盖已存在的子功能键（保留之前的开关状态）

### 3.2 GET /settings 兼容

`_read_extension_settings()` 按 manifest 的 `features`（含 children）生成默认值时，对子功能生成 `模块id.子功能id` 格式的键。

---

## 4. 抽屉 UI

### 4.1 模块卡片

修改 `ExtensionDetailDrawer.vue` 的功能开关区域，遍历 features 时分两种渲染：

**叶子功能（无 type）：** 现有 toggle 样式不变。

**模块（`type: "group"`）：**
```
┌──────────────────────────────────────────┐
│ ▶ 会话指标                         [ON]  │  ← 标题行可点击折叠/展开
├──────────────────────────────────────────┤
│   命中率                           [ON]  │  ← 缩进子功能
│   显示 AI 回复的缓存命中率                 │
│   请求次数                          [ON]  │
│   显示当前会话的 API 请求次数              │
│   累计 AI Token                     [ON]  │
│   显示累计 AI 输出的 Token 总量            │
└──────────────────────────────────────────┘
```

### 4.2 交互逻辑

| 操作 | 行为 |
|------|------|
| 点击模块开关 OFF | 所有子功能 → false，保存，卡片折叠 |
| 模块 OFF 时点击标题行 | 不展开 |
| 点击模块开关 ON | 子功能保留现有值，保存，卡片展开 |
| 模块 ON 时拨动子功能 | 独立开关，不影响模块开关 |
| 点击标题行/箭头 | 折叠/展开切换（仅 ON 时有效） |
| 模块 ON 时点击展开 | 显示子功能区域 |

### 4.3 级联逻辑（Store）

`toggleFeature()` 增加 group 检测：

```javascript
// 查找 manifest 中该 feature 是否为 group
const group = allFeatures.find(f => f.id === featureId && f.type === 'group');
if (group) {
  this.detailSettings.features[featureId] = value;
  for (const child of group.children) {
    const ck = `${featureId}.${child.id}`;
    if (!value) this.detailSettings.features[ck] = false;
    // value=true 时保持 settings 中已有值不变
  }
}
```

模块 ON 时不主动写入子功能值——已有值的保持不变，缺值的由后端 GET /settings 补 default。

---

## 5. 后端 API

### 5.1 PUT /settings 校验扩展

现有校验逻辑按 manifest 的 `features` 收集合法 key。需扩展为：当 features 中含有 `type: "group"` 项时，将 `模块id.子功能id` 也加入合法 key 集合。

```python
known_ids = set()
for feat in manifest.get("features", []):
    if feat.get("type") == "group":
        known_ids.add(feat["id"])
        for child in feat.get("children", []):
            known_ids.add(f"{feat['id']}.{child['id']}")
    else:
        known_ids.add(feat["id"])
```

### 5.2 _read_extension_settings 默认值生成

生成默认值时对 group 额外生成子功能的点号键：

```python
defaults = {}
for feat in features_declared:
    if feat.get("type") == "group":
        defaults[feat["id"]] = feat.get("default", False)
        for child in feat.get("children", []):
            defaults[f"{feat['id']}.{child['id']}"] = child.get("default", False)
    else:
        defaults[feat["id"]] = feat.get("default", False)
```

---

## 6. Dashboard 组件适配

`DashboardFloating.js` 中，原来 `show-token-count` 控制整个会话指标区域。现在拆分为三个子功能 key：

```javascript
const feat = props.settings?.features || {};

// 会话指标模块开关
if (feat['session-metrics'] !== false) {
  // 子功能分别控制
  if (feat['session-metrics.hit-rate'] !== false) { /* 渲染命中率 */ }
  if (feat['session-metrics.request-count'] !== false) { /* 渲染请求次数 */ }
  if (feat['session-metrics.completion-tokens'] !== false) { /* 渲染累计 token */ }
}
```

---

## 7. 改动范围

| 文件 | 操作 | 说明 |
|------|------|------|
| `user_data/extensions/dashboard/manifest.json` | 修改 | `show-token-count` → `session-metrics` group + 3 children |
| `test_expand/dashboard/manifest.json` | 修改 | 同上 |
| `user_data/extensions/dashboard/frontend/components/DashboardFloating.js` | 修改 | 三个子功能独立读取 |
| `test_expand/dashboard/frontend/components/DashboardFloating.js` | 修改 | 同上 |
| `frontend/src/components/ExtensionDetailDrawer.vue` | 修改 | 叶子/group 分支渲染 + group 卡片样式 |
| `frontend/src/stores/extensions.js` | 修改 | `toggleFeature()` 级联逻辑 |
| `backend/app/routes/extensions.py` | 修改 | `_read_extension_settings` 默认值 + PUT 校验扩展 |
| `backend/tests/test_extensions.py` | 修改 | group 相关测试用例 |
| `Plugin_Development_Guide.md` | 修改 | features 嵌套格式文档 + 级联规则 |
