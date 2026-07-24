# Custom CSS 预设系统 — 设计规格

> **日期**: 2026-07-24
> **状态**: 待实现

---

## 一、功能概述

允许用户编写自定义 CSS，以多预设模式管理（创建/切换/删除），实时预览，全局生效。"多预设模式"指与现有 settings、param-presets 相同的 CRUD + default 架构。

---

## 二、数据模型

### css_presets.json

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "暗夜主题",
    "content": "body { background: #1a1a2e; color: #e0e0e0; }",
    "is_default": true,
    "created_at": "2026-07-24T10:00:00",
    "updated_at": "2026-07-24T10:00:00"
  }
]
```

**字段：**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | 自动 | — | 唯一标识 |
| `name` | string | 是 | — | 预设名称 |
| `content` | string | 否 | `""` | CSS 内容，空串 = 不注入任何样式 |
| `is_default` | bool | 否 | `false` | 是否为默认预设 |
| `created_at` | ISO8601 | 自动 | — | 创建时间 |
| `updated_at` | ISO8601 | 自动 | — | 更新时间 |

### 存储

- 文件：`user_data/css_presets.json`
- 锁：复用 `storage.py` 的 `threading.Lock`
- **首次启动自动创建**：如果文件不存在或无数据，自动创建一个默认预设 `{ name: "默认", content: "", is_default: true }`

---

## 三、API 设计

Base: `/api/css-presets`

| 方法 | 端点 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/css-presets` | 列出所有预设 | — | `[{...}]` |
| POST | `/api/css-presets` | 创建预设 | `{name, content}` | `{...}` |
| PUT | `/api/css-presets/<id>` | 更新预设 | `{name?, content?}` | `{...}` |
| DELETE | `/api/css-presets/<id>` | 删除预设 | — | `{...}` |
| PUT | `/api/css-presets/<id>/default` | 设为默认 | — | `{...}` |

### 行为约束

- **删除保护**：`is_default=true` 的预设不可删除，返回 `fail(400, "不能删除默认预设")`
- **默认唯一**：设为新默认时，旧的 `is_default` 自动清除
- **创建**：新预设默认 `content: ""`，`is_default: false`
- **更新**：`name` 和 `content` 均可单独更新

### 路由注册

在 `backend/app/routes/` 下新建 `css_presets.py`，使用 Blueprint `api_bp`，遵循现有模式：

```python
@api_bp.route("/css-presets", methods=["GET", "POST"])
@api_bp.route("/css-presets/<preset_id>", methods=["PUT", "DELETE"])
@api_bp.route("/css-presets/<preset_id>/default", methods=["PUT"])
```

---

## 四、前端设计

### 4.1 Store — `stores/cssPresets.js`

```js
// 状态
presets: []           // 预设列表
activeId: null        // 当前激活的预设 ID
loading: false

// 计算属性
activePreset          // 当前预设对象
activeContent         // 当前预设的 CSS 内容（"" 表示无样式）

// Actions
fetchPresets()        // GET /api/css-presets
createPreset(name)    // POST
updatePreset(id, data)// PUT
deletePreset(id)      // DELETE
setDefault(id)        // PUT /<id>/default
switchPreset(id)      // 切换激活预设 + 更新 <style> 节点
saveContent(id, css)  // 保存单次调用 PUT，但 v-model 不触发此
```

### 4.2 组件 — `CustomCssDrawer.vue`

右侧可拖拽抽屉（复用 `useResizableDrawer`），从右向左展开。

**布局：**
```
┌─────────────────────────────────┐
│ 自定义 CSS                  [✕] │  ← 标题栏
├─────────────────────────────────┤
│ 预设: [暗夜主题 ▾] [新建][删除] │  ← 预设选择器
├─────────────────────────────────┤
│                                 │
│  /* CSS 代码 */                 │  ← textarea（等宽字体、暗色背景）
│                                 │
│                                 │
│                                 │
├─────────────────────────────────┤
│                    [重置] [保存] │  ← 操作按钮
└─────────────────────────────────┘
```

**行为：**
- 预设下拉框：切换时立即加载对应 CSS 到 `<style>` 节点
- 预设名称：可选的内联编辑（双击或编辑图标触发）
- textarea：`@input` → `activePreset.content` 更新 → `<style id="custom-css">` textContent 直接替换，实现**实时预览**
- 保存按钮：调用后端 `PUT /api/css-presets/<id>` 持久化
- 重置按钮：清空 textarea 为当前已保存的内容（撤销未保存的修改）
- 新建按钮：创建名为"未命名"的预设，切换过去
- 删除按钮：删当前预设，自动切换到默认预设

### 4.3 组件 — `CssPresetSelector.vue`

工具栏中的下拉选择器，显示当前激活预设名称。

**尺寸与位置**：紧凑型，放在 `PresetSelector` 左侧。

```
[🎨 暗夜主题 ▾] [⚙️ 预设 ▾] [模型 ▾] ...
```

- 切换即生效
- 不包含编辑/管理功能（点击选择器本身或旁边的🎨图标打开 `CustomCssDrawer`）

### 4.4 DOM 注入

`App.vue` onMounted：

```js
// 加载 CSS 预设 → 选取默认预设 → 注入 <style id="custom-css">
const cssPresetsStore = useCssPresetsStore()
await cssPresetsStore.fetchPresets()
const defaultPreset = cssPresetsStore.presets.find(p => p.is_default)
if (defaultPreset) {
  cssPresetsStore.switchPreset(defaultPreset.id)
}
```

`switchPreset()` 内部：
```js
let styleEl = document.getElementById("custom-css")
if (!styleEl) {
  styleEl = document.createElement("style")
  styleEl.id = "custom-css"
  document.head.appendChild(styleEl)
}
styleEl.textContent = preset.content
```

textarea @input 同步更新 `styleEl.textContent`，无需经过 store action，保证实时性。

---

## 五、错误处理

| 场景 | 处理 |
|------|------|
| 删除默认预设 | 后端返回 400，前端 AlertDialog 提示"不能删除默认预设" |
| 保存失败 | AlertDialog 提示错误信息 |
| 首次启动无预设 | 后端 storage 自动创建默认预设 |
| CSS 语法错误 | 不校验——用户自行调试，浏览器自然忽略无效 CSS |

---

## 六、非功能需求

- **性能**：自定义 CSS 直接注入 `<style>` 节点，零额外运行时开销
- **安全**：用户自行编写 CSS，不存在注入风险（CSS 只能控制样式）
- **兼容性**：依赖浏览器 CSS 引擎，无平台限制
- **文件大小**：`user_data/css_presets.json` 预计 < 100KB（CSS 文本为主）
