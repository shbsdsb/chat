# 顶部工具栏图标化 — 设计规格

> **日期**：2026-07-27  
> **状态**：已确认  
> **范围**：`frontend/src/App.vue` · 安装 `lucide-vue-next`

---

## 1. 问题

顶部工具栏 5 个按钮目前使用纯文字（"会话记录""预设"等）和简单 SVG（地球图标），共用 `.top-btn` 透明背景 + 悬停下划线动画，缺乏精致感，与桌面应用应有的品质不匹配。

## 2. 目标

将 5 个按钮统一改为 **纯 SVG 图标按钮**，引入 Lucide 图标库，保持极简视觉风格，激活态通过底部 accent 色下划线指示。

## 3. 图标映射

| 按钮 | Lucide 图标 | `lucide-vue-next` 组件 | 激活条件 |
|------|------------|----------------------|----------|
| 会话记录 | `sidebar` | `<Sidebar>` | `showConversations === true` |
| CSS 预设 | `palette` | `<Palette>` | `activeDrawer === 'css'` |
| 参数预设 | `sliders-horizontal` | `<SlidersHorizontal>` | `activeDrawer === 'presets'` |
| API 设置 | `plug` | `<Plug>` | `activeDrawer === 'api'` |
| 扩展管理 | `blocks` | `<Blocks>` | `activeDrawer === 'extensions'` |

## 4. 视觉规格

```
布局不变，top-nav 内 5 个纯图标按钮水平排列，gap 保持 4px。

┌──────────────────────────────────────────────────────┐
│ [💬]  Chat                    [🎨] [⚙] [🔌] [🧩]    │
│  top-left                      top-nav                │
└──────────────────────────────────────────────────────┘
```

| 属性 | 值 |
|------|-----|
| 按钮尺寸 | 36 × 36px（正方形触控区） |
| 图标尺寸 | 18 × 18px（`size="18"`） |
| 默认颜色 | `var(--text-secondary)` = `#5b5b7a` |
| hover 颜色 | `var(--text-primary)` = `#1a1a2e` |
| hover 动画 | 底部 2px accent 色下划线从中间展开至 60% 宽度 |
| 激活态颜色 | `var(--text-primary)` |
| 激活态下划线 | 底部 2px accent 色，`width: 100%` 常驻 |
| 背景 | 始终透明 |
| 圆角 | `var(--radius-sm)` = 8px |
| 过渡 | `all 0.15s ease` |

### 交互

- 无自定义 tooltip；使用浏览器原生 `title` 属性
- 点击即 `toggleDrawer(name)`，再次点击关闭（现有逻辑不变）
- 左侧"会话记录"独立状态 `showConversations`，可与右侧面板同时激活
- 支持键盘 Tab 聚焦 + Enter/Space

## 5. 实现

### 5.1 依赖

```bash
cd frontend
npm install lucide-vue-next
```

### 5.2 改动范围

**仅 `frontend/src/App.vue`**：

- 引入 5 个图标组件：`Sidebar, Palette, SlidersHorizontal, Plug, Blocks`
- 替换 `<CssPresetSelector>` 为内联 `<button class="top-btn">`（删除组件引用）
- 4 个文字 `<button>` 改为图标 `<button>`
- 每个按钮加 `:class="{ active: ... }"` 和 `title="..."` 属性
- 新增 `.top-btn.active` 样式规则
- 调整 `.top-btn` 尺寸为 36×36px

### 5.3 样式

```css
.top-btn {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}
.top-btn:hover {
  color: var(--text-primary);
  transform: translateY(-1px);
}
.top-btn::after {
  content: "";
  position: absolute; bottom: 0; left: 50%;
  transform: translateX(-50%);
  width: 0; height: 2px;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.15s ease;
}
.top-btn:hover::after { width: 60%; }

/* 激活态 */
.top-btn.active { color: var(--text-primary); }
.top-btn.active::after { width: 100%; }
```

### 5.4 模板变更

```diff
- <button class="top-btn" @click="showConversations = !showConversations">会话记录</button>
+ <button class="top-btn" :class="{ active: showConversations }"
+   @click="showConversations = !showConversations" title="会话记录">
+   <Sidebar :size="18" />
+ </button>

- <CssPresetSelector @open-drawer="toggleDrawer('css')" />
+ <button class="top-btn" :class="{ active: activeDrawer === 'css' }"
+   @click="toggleDrawer('css')" title="CSS 预设">
+   <Palette :size="18" />
+ </button>

- <button class="top-btn" @click="toggleDrawer('presets')">预设</button>
+ <button class="top-btn" :class="{ active: activeDrawer === 'presets' }"
+   @click="toggleDrawer('presets')" title="参数预设">
+   <SlidersHorizontal :size="18" />
+ </button>

- <button class="top-btn" @click="toggleDrawer('api')">API 设置</button>
+ <button class="top-btn" :class="{ active: activeDrawer === 'api' }"
+   @click="toggleDrawer('api')" title="API 设置">
+   <Plug :size="18" />
+ </button>

- <button class="top-btn" @click="toggleDrawer('extensions')">扩展</button>
+ <button class="top-btn" :class="{ active: activeDrawer === 'extensions' }"
+   @click="toggleDrawer('extensions')" title="扩展管理">
+   <Blocks :size="18" />
+ </button>
```

### 5.5 清理

- 从 `App.vue` 移除 `CssPresetSelector` 的 import 和 components 注册
- 可删除 `frontend/src/components/CssPresetSelector.vue`（不再被引用）

## 6. 边界与兼容

### 深色主题

所有颜色走 CSS 变量（`--text-secondary`、`--text-primary`、`--accent`），现有"暗夜护眼"主题自动适配，无需额外处理。

### 自定义 CSS 覆盖

`.top-btn` 是非 scoped 样式，遵循 BEM 约定。用户可用 `#custom-css` 注入覆盖。Lucide 渲染的 SVG 自带 `.lucide` 类可精准选中。

### 响应式

5 个按钮 × 36px + 4 个 gap × 4px = 196px，极紧凑，不会溢出。

### 键盘可访问性

原生 `<button>` 支持 Tab 聚焦和 Enter/Space 触发。聚焦环使用浏览器默认 outline。

## 7. 审查记录

| 日期 | 审查者 | 结果 |
|------|--------|------|
| 2026-07-27 | 用户 | ✅ 全部确认 |
