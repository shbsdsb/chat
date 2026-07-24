# Custom CSS 预设系统 — 实现计划

> **日期**: 2026-07-24
> **基于**: `docs/superpowers/specs/2026-07-24-custom-css-presets-design.md`

---

## 计划总览

共 7 个步骤，依序执行。后端完全镜像 `param_presets` 模式，前端增加 DOM 注入和实时预览逻辑。

---

## Step 1: 后端 — 存储层

**新建** `backend/app/storage/css_presets.py`

以 `param_presets.py` 为模板，差异仅：
- 文件名：`css_presets.json`
- 默认预设字段：`name` + `content:""`（无 temperature/max_tokens/top_p）
- 函数名：`*_css_preset*` 替代 `*_param_preset*`

```python
# 需要实现的函数（完全对应 param_presets.py 的导出）：
init_css_presets()          # 首次自动创建默认预设
list_css_presets_raw()      # 列出所有
get_css_preset(preset_id)   # 按 ID 获取
create_css_preset(p)        # 创建
update_css_preset(id, data) # 更新
delete_css_preset(id)       # 删除（不检查 is_default，由路由层处理）
get_default_css_preset()    # 获取默认
set_default_css_preset(id)  # 设默认
```

**修改** `backend/app/storage/__init__.py`

从新模块导入全部公共函数，遵循现有模式。

---

## Step 2: 后端 — 路由层

**新建** `backend/app/routes/css_presets.py`

以 `param_presets.py` 路由为模板，差异仅：
- 端点前缀：`/css-presets` 替代 `/param-presets`
- 创建/更新时只处理 `name` + `content` 字段（无 temperature/max_tokens/top_p 校验）
- 删除保护文案："不能删除默认CSS预设，请先切换默认预设"

```python
# 路由清单：
GET    /api/css-presets                       # 列表
POST   /api/css-presets                       # 创建 {name, content?}
PUT    /api/css-presets/<preset_id>           # 更新 {name?, content?}
DELETE /api/css-presets/<preset_id>            # 删除（保护 is_default）
PUT    /api/css-presets/<preset_id>/default    # 设默认
```

**修改** `backend/app/__init__.py`

在 `create_app()` 中：
- `import app.routes.css_presets`（在 blueprint 注册前）
- `from app.storage.css_presets import init_css_presets` + `init_css_presets()`（在 `init_param_presets()` 之后）

---

## Step 3: 后端 — 测试

**新建** `backend/tests/test_css_presets.py`

以 `tests/test_param_presets.py` 为模板，覆盖：
- 首次启动自动创建默认预设
- CRUD 全流程
- 删除默认预设被拒绝
- 设默认 → 旧默认自动取消
- 切换默认后删除原默认

---

## Step 4: 前端 — API 模块

**新建** `frontend/src/api/cssPresets.js`

```js
import http from "./request.js";

export function list()     { return http.get("/css-presets"); }
export function create(d)  { return http.post("/css-presets", d); }
export function update(id,d){ return http.put(`/css-presets/${id}`, d); }
export function remove(id) { return http.delete(`/css-presets/${id}`); }
export function setDefault(id) { return http.put(`/css-presets/${id}/default`); }
```

（完全遵循 `paramPresets.js` 模式）

---

## Step 5: 前端 — Pinia Store

**新建** `frontend/src/stores/cssPresets.js`

架构镜像 `paramPresets.js`，但额外承担 DOM 注入职责：

```js
// 状态
presets: []          // 预设列表
activeId: null       // 当前激活的预设 ID
loading: false

// 计算属性
activePreset          // 当前预设对象
activeContent         // activePreset?.content || ""

// Actions（镜像 paramPresets）
loadPresets()         // GET → 选择默认 → 调用 injectCss()
selectPreset(id)      // 切换 → 调用 injectCss()
createPreset(name)    // POST
savePreset(name, content)  // PUT
deletePreset(id)      // DELETE，删后自动切到默认

// CSS 注入 Actions（新增，非标准 Pinia action，更贴近副作用管理）
injectCss(content)    // 创建/更新 <style id="custom-css"> textContent
removeCss()           // 移除 <style id="custom-css"> 节点
```

`injectCss()` 实现（store 内部函数）：
```js
let styleEl = document.getElementById("custom-css");
if (!styleEl) {
  styleEl = document.createElement("style");
  styleEl.id = "custom-css";
  document.head.appendChild(styleEl);
}
styleEl.textContent = content;
```

`loadPresets()` 中自动调用：找到默认预设 → `this.activeId = ...` → `this.injectCss(activePreset.content)`。

---

## Step 6: 前端 — 组件

### 6a. `CssPresetSelector.vue`（工具栏下拉）

**新建** `frontend/src/components/CssPresetSelector.vue`

- 紧凑型的 `<select>`，列出所有预设名称
- 默认选中 `activeId` 对应的预设
- `@change` → `store.selectPreset(val)`（切换即时生效）
- 可选：旁边 🎨 图标按钮 → `$emit('open-drawer')`

```html
<template>
  <div class="css-preset-selector">
    <button class="icon-btn" @click="$emit('open-drawer')" title="自定义 CSS">🎨</button>
    <select :value="store.activeId || ''" @change="store.selectPreset($event.target.value)">
      <option v-for="p in store.presets" :key="p.id" :value="p.id">{{ p.name }}</option>
    </select>
  </div>
</template>
```

### 6b. `CustomCssDrawer.vue`（编辑抽屉）

**新建** `frontend/src/components/CustomCssDrawer.vue`

复用 `SettingsDrawer` 组件的结构模式（`useResizableDrawer` + slot 布局），但直接内联内容而非通过 slot。

**布局：**
```
┌───────────────────────────────────┐
│ 自定义 CSS                    [✕] │
├───────────────────────────────────┤
│ [预设下拉 ▾]  [🖊 重命名] [+ 新建] [🗑 删除] │
├───────────────────────────────────┤
│ <textarea>                        │
│   /* CSS 代码 */                  │
│                                   │
│                                   │
├───────────────────────────────────┤
│                      [↺ 重置] [💾 保存] │
└───────────────────────────────────┘
```

**核心行为：**
- `textarea @input` → 直接更新 `<style id="custom-css">` textContent（不经过 store 持久化）
- 保存按钮 → `store.savePreset(name, content)` — 持久化到后端
- 重置按钮 → textarea 恢复为 `store.activePreset.content`
- 预设切换 → `<select @change>` → `store.selectPreset(id)` — 替换 CSS + 更新 textarea
- 新建 → `store.createPreset("未命名")`
- 删除 → `store.deletePreset(activeId)`，失败时 AlertDialog
- 重命名 → 点击 🖊 或双击名称 → 出现输入框 → Enter 确认 → `store.savePreset(newName, currentContent)`

**Props / Emits：**
```js
defineProps({ visible: Boolean })
defineEmits(["close"])
```

### 6c. 路由注册

不需要新路由。`CssPresetSelector` 直接在 `App.vue` 中引用，`CustomCssDrawer` 在 `App.vue` 中作为抽屉渲染。

---

## Step 7: 前端 — App.vue 集成

**修改** `frontend/src/App.vue`

1. 导入：
```js
import CssPresetSelector from "@/components/CssPresetSelector.vue";
import CustomCssDrawer from "@/components/CustomCssDrawer.vue";
import { useCssPresetsStore } from "@/stores/cssPresets";
```

2. state：`const showCssDrawer = ref(false);`

3. template — 工具栏，放在 `"预设"` 按钮左边：
```html
<nav class="top-nav">
  <CssPresetSelector @open-drawer="showCssDrawer = true" />
  <button class="top-btn" @click="showParamPresets = !showParamPresets">预设</button>
  <button class="top-btn" @click="showSettings = !showSettings">API 设置</button>
</nav>
```

4. template — 抽屉：
```html
<CustomCssDrawer :visible="showCssDrawer" @close="showCssDrawer = false" />
```

5. onMounted 中加载：
```js
const cssPresetsStore = useCssPresetsStore();
// 在现有 onMounted 中加一行：
cssPresetsStore.loadPresets();
```

---

## 验证方法

```bash
# 后端测试
cd backend
python -m pytest tests/test_css_presets.py -v

# 前端手动验证
# 1. 启动前后端
# 2. 点击工具栏 🎨 → CSS 下拉出现
# 3. 选 "默认" → 抽屉打开 → textarea 为空
# 4. 输入 body { background: red; } → 页面背景即时变红
# 5. 删除 textarea 内容 → 背景恢复
# 6. 点击保存 → 刷新页面 → 默认 CSS 仍加载
# 7. 新建预设 "暗夜主题" → 写入 CSS → 保存 → 切换回默认 → 样式正确切换
# 8. 尝试删除 "默认" 预设 → 弹窗提示"不能删除默认CSS预设"
# 9. 切换默认 → 页面上显示的默认预设样式立即生效
```

---

## 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/storage/css_presets.py` | 存储层 |
| 修改 | `backend/app/storage/__init__.py` | 导出新函数 |
| 新建 | `backend/app/routes/css_presets.py` | API 路由 |
| 修改 | `backend/app/__init__.py` | 注册路由+初始化 |
| 新建 | `backend/tests/test_css_presets.py` | 后端测试 |
| 新建 | `frontend/src/api/cssPresets.js` | API 封装 |
| 新建 | `frontend/src/stores/cssPresets.js` | Store + DOM注入 |
| 新建 | `frontend/src/components/CssPresetSelector.vue` | 工具栏下拉 |
| 新建 | `frontend/src/components/CustomCssDrawer.vue` | 编辑抽屉 |
| 修改 | `frontend/src/App.vue` | 集成 |

共 6 个新建文件、4 个修改文件。
