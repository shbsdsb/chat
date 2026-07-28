# UI Token v2 — 设计规范（工具栏 & API 设置页面改造后）

> **最后更新**：2026-07-29  
> **基于**：`UI_token.md`（v1）+ 工具栏图标化 + API 设置页面重设计  
> **Token 文件**：`frontend/src/assets/tokens.css`

---

## 一、改造总览

| 改造 | 范围 | 核心思路 |
|------|------|---------|
| **工具栏图标化** | `App.vue` 顶部 5 个按钮 | 纯文字 → Lucide SVG 图标，激活态底部 accent 下划线 |
| **API 设置页面重设计** | `SettingsView.vue` + 3 个子组件 + store | 单面板 → 分组卡片式，CSS 变量统一管理 |

两项改造围绕同一设计哲学：**极简、克制、变量驱动**。

---

## 二、工具栏图标化

### 设计思路

原先 5 个按钮（"会话记录"、"预设"、"API 设置"、"扩展" + 地球 SVG）共用 `.top-btn` 透明背景 + `::after` 悬停下划线动画。文字按钮缺乏桌面应用应有的精致感。

改造后全部替换为 **Lucide 纯 SVG 图标**，保留原有 `::after` 下划线交互模式，新增 `.active` 激活态。

### 图标映射

| 按钮 | Lucide 图标 | Vue 组件 | 激活条件 |
|------|------------|---------|----------|
| 会话记录 | `sidebar` | `<Sidebar>` | `showConversations` |
| CSS 预设 | `palette` | `<Palette>` | `activeDrawer === 'css'` |
| 参数预设 | `sliders-horizontal` | `<SlidersHorizontal>` | `activeDrawer === 'presets'` |
| API 设置 | `plug` | `<Plug>` | `activeDrawer === 'api'` |
| 扩展管理 | `blocks` | `<Blocks>` | `activeDrawer === 'extensions'` |

### 核心 CSS（`.top-btn`）

```css
.top-btn {
  width: 36px; height: 36px;           /* 正方形触控区 */
  display: flex; align-items: center;
  justify-content: center;
  border: none; border-radius: 8px;    /* var(--radius-sm) */
  background: transparent;
  color: var(--text-secondary);        /* #5b5b7a */
  position: relative;
  transition: all 0.15s ease;
}
/* hover：图标变色 + 上浮 + 下划线展开至 60% */
.top-btn:hover {
  color: var(--text-primary);          /* #1a1a2e */
  transform: translateY(-1px);
}
.top-btn::after {
  content: ""; position: absolute;
  bottom: 0; left: 50%; transform: translateX(-50%);
  width: 0; height: 2px;
  background: var(--accent);           /* #4f6ef6 */
  border-radius: 2px;
  transition: width 0.15s ease;
}
.top-btn:hover::after { width: 60%; }

/* 激活态：下划线常驻 100% */
.top-btn.active { color: var(--text-primary); }
.top-btn.active::after { width: 100%; }
```

### 交互约定

- 原生 `<button>` + `title` 属性（无自定义 tooltip）
- 左侧"会话记录"独立状态，可与右侧面板同时激活
- 图标 `size="18"`，依赖 `lucide-vue-next`

---

## 三、API 设置页面重设计

### 设计思路

原先单面板布局、全硬编码颜色（`#d5d5d5`、`#4a90d9`、`#888` 等 20+ 种）、border-radius 混用（4/6/8/12px）、反馈机制混用（AlertDialog / 内联 toast / 结果段落三种方式）。

改造后：
1. **分组卡片式布局** — 4 张卡片（预设 / 连接信息 / 模型 / 响应格式）+ 状态指示行 + 测试按钮
2. **CSS 变量集中管理** — 新建 `tokens.css`，全部 50+ Token 统一在此
3. **新增交互组件** — 连接状态指示灯、自动连接开关
4. **测试按钮重设计** — 全宽大色块 → 紧凑型 `inline-flex` 图标按钮

### 布局结构

```
┌─────────────────────────────────────┐
│ ┌─────────────────────────────────┐ │
│ │ ⚙ 预设                          │ │  卡片1
│ │ [下拉▾] [💾] [+] [🗑]           │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🔌 连接信息                      │ │  卡片2
│ │ API URL   [________________]    │ │
│ │ API Key   [________________]    │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 💬 模型                          │ │  卡片3
│ │ [下拉▾]  [🔄 拉取]              │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 📝 响应格式                      │ │  卡片4
│ │ [__________________________]    │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ ● 已连接 · 8 个模型    [✓] 自动  │ │  状态行
│ └─────────────────────────────────┘ │
│ [🔌 测试连接]                       │  按钮
└─────────────────────────────────────┘
```

### 卡片规格

```css
.card {
  background: var(--bg-primary);       /* #fff */
  border: 1px solid var(--border);     /* #e2e4eb */
  border-radius: var(--radius-lg);     /* 16px */
  box-shadow: var(--shadow-sm);        /* 0 2px 8px rgba(0,0,0,0.06) */
  padding: 16px 18px;
}
.card-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px;
}
.card-icon { color: var(--card-icon-color); }   /* = var(--accent) */
.card-label {
  font-size: 13px; font-weight: 600;
  color: var(--text-secondary);
}
```

### 表单控件统一规格

| 元素 | 规则 |
|------|------|
| `input` / `select` / `textarea` | `bg: #fafbfc`, `border: 1px solid #d8dae2`, `radius: 8px` |
| focus 态 | `border: var(--accent)` + `box-shadow: 0 0 0 3px rgba(79,110,246,0.1)` |
| 标签 | `11px`, `text-transform: uppercase`, `letter-spacing: 0.3px` |
| 图标按钮 | `32×32px`, `bg: #fafbfc`, `border: 1px solid #d8dae2` |
| disabled | 统一 `opacity: 0.45`（原来混用 0.3/0.4/0.5） |

### 状态指示行

```
┌──────────────────────────────────────┐
│ ● 已连接 · 8 个模型可用    [✓] 自动连接 │
└──────────────────────────────────────┘
```

| 状态 | 圆点颜色 | 文字 | 动画 |
|------|---------|------|------|
| 未连接 | `#aaa` | "未连接" | — |
| 测试中 | `#4f6ef6`（accent） | "正在测试连接..." | `pulse-dot` 1s 循环 |
| 已连接 | `#22c55e` | "已连接 · N 个模型可用" | — |

- 圆点 `8×8px`，`border-radius: 50%`
- 脉冲动画：50% opacity:1 scale:1 → 0% opacity:0.4 scale:0.7

### 自动连接开关

- `18×18px`，`border-radius: 4px`
- 关闭：`border: 2px solid var(--border)` + 浅灰底
- 开启：`background: var(--accent)` + 白色 ✓ SVG
- 数据：`settingsStore.autoConnect`（per-preset 持久化）
- 行为：已有预设时切换即自动保存；新建预设等手动保存时写入

### 测试按钮重设计

```css
.test-btn {
  display: inline-flex;         /* 不拉伸全宽 */
  align-items: center; gap: 7px;
  padding: 8px 18px;
  border: none; border-radius: 8px;
  background: var(--accent);    /* #4f6ef6 */
  color: #fff; font-size: 13px;
  box-shadow: 0 1px 3px rgba(79,110,246,0.2);
  transition: all 0.15s;
}
.test-btn:hover:not(:disabled) {
  background: var(--accent-light);  /* #6c8cfc */
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(79,110,246,0.3);
}
.test-btn:disabled {
  opacity: 0.45; box-shadow: none; transform: none;
}
```

文案：默认 "测试连接" → 测试中 spinner + "测试中..." → 成功后 "重新测试"。

---

## 四、设计 Token（`tokens.css`）

全部 Token 集中在 `frontend/src/assets/tokens.css`，`App.vue` 通过 `@import` 引用。CSS 预设系统可通过覆盖 `:root` 变量实现换肤。

### 色彩

| Token | 值 | 用途 |
|------|-----|------|
| `--bg-primary` | `#fff` | 主背景 |
| `--bg-secondary` | `#f8f9fb` | 次背景（top-bar） |
| `--bg-tertiary` | `#f0f1f5` | 三级背景（左侧抽屉） |
| `--bg-input` | `#fafbfc` | 输入框背景 |
| `--bg-input-hover` | `#f0f1f5` | 按钮 hover |
| `--text-primary` | `#1a1a2e` | 主文字 |
| `--text-secondary` | `#5b5b7a` | 次文字（按钮、标签） |
| `--text-muted` | `#8e8ea0` | 弱化文字 |
| `--border` | `#e2e4eb` | 分割线、面板边框 |
| `--border-light` | `#d8dae2` | 输入框边框 |
| `--accent` | `#4f6ef6` | 强调色 |
| `--accent-light` | `#6c8cfc` | 强调色 hover |
| `--accent-bg` | `rgba(79,110,246,0.08)` | 强调色浅底 |
| `--danger` | `#ef4444` | 危险操作 |
| `--danger-bg` | `#fef2f2` | 危险操作浅底 |
| `--success` | `#2e7d32` | 成功文字 |
| `--success-bg` | `#f0faf0` | 成功浅底 |
| `--success-border` | `#c8e6c9` | 成功边框 |

### 阴影

| Token | 值 | 用途 |
|------|-----|------|
| `--shadow-xs` | `0 1px 2px rgba(0,0,0,0.04)` | 面板微弱浮起 |
| `--shadow-sm` | `0 2px 8px rgba(0,0,0,0.06)` | 卡片（API 设置页）、消息气泡 |
| `--shadow-md` | `0 4px 16px rgba(0,0,0,0.08)` | 抽屉面板、弹窗 |
| `--shadow-lg` | `0 8px 32px rgba(0,0,0,0.10)` | 模态弹窗 |

### 圆角

| Token | 值 | 用途 |
|------|-----|------|
| `--radius-sm` | `8px` | 按钮、输入框、标签 |
| `--radius-md` | `10px` | 卡片、面板、会话项 |
| `--radius-lg` | `16px` | 消息气泡、API 设置卡片 |
| `--radius-xl` | `28px` | 输入框 wrapper |

### 已使用图标（Lucide）

项目统一使用 Lucide（`lucide-vue-next`）图标，`size` 统一为 `18`（工具栏/卡片头）或 `14`（条目行内按钮）或 `16`（Modal 按钮）。

<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;padding:8px 0;">

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
<code>Sidebar</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><circle cx="13.5" cy="6.5" r="2.5"/><circle cx="18.5" cy="10.5" r="2.5"/><circle cx="9.5" cy="14.5" r="2.5"/><circle cx="14.5" cy="18.5" r="2.5"/><path d="M10.5 6.5a6 6 0 0 0-5 5"/></svg>
<code>Palette</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>
<code>SlidersHorizontal</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v-.5a3 3 0 0 0-3-3H9a3 3 0 0 0-3 3V8"/><path d="M5 8h14a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 1 2-2z"/></svg>
<code>Plug</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
<code>Blocks</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
<code>List</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>
<code>Pencil</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
<code>X</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
<code>Trash2</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#4f6ef6;border-radius:8px;padding:6px 12px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
<code>Save</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
<code>Settings</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
<code>MessageSquare</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
<code>Code</code>
</div>

<div style="display:flex;align-items:center;gap:6px;background:#f8f9fb;border-radius:8px;padding:6px 12px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5b5b7a" stroke-width="2" stroke-linecap="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
<code>RefreshCw</code>
</div>

</div>

**新增图标约定：**
- 优先从已使用列表中选择，保持项目图标语言一致
- 工具栏/卡片头 `size=18`，行内按钮 `size=14`，Modal 按钮 `size=16`
- 拖拽手柄使用自定义 SVG（`viewBox="0 0 100 100"` 三线星号），非 Lucide
- Save 图标按钮背景为 `var(--accent)` + 白色 SVG（其它图标为 `#5b5b7a`）

### 聚焦环

| Token | 值 | 用途 |
|------|-----|------|
| `--focus-ring` | `0 0 0 3px rgba(79,110,246,0.1)` | 所有 input/select/textarea 统一 focus 态 |

### API 设置页专用

| Token | 值 | 用途 |
|------|-----|------|
| `--card-icon-color` | `var(--accent)` | 卡片头部图标色 |
| `--test-btn-bg` | `var(--accent)` | 测试按钮背景 |
| `--test-btn-text` | `#fff` | 测试按钮文字 |
| `--status-dot-disconnected` | `#aaa` | 未连接指示灯 |
| `--status-dot-connected` | `#22c55e` | 已连接指示灯 |
| `--toggle-bg-off` | `#e2e4eb` | 自动连接开关关闭态 |
| `--toggle-bg-on` | `var(--accent)` | 自动连接开关开启态 |

### 动画

| Token | 值 | 用途 |
|------|-----|------|
| `btn-hover-duration` | `0.15s` | 按钮 hover |
| `drawer-width-duration` | `0.2s` | 抽屉展开 |
| `drawer-slide-duration` | `0.2s` | 抽屉内容切换 |
| `pulse-dot` | `1s ease-in-out infinite` | 状态指示圆点脉冲 |

### 字体

| Token | 值 | 用途 |
|------|-----|------|
| `font-family` | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | 全局 |
| `font-mono` | `"Consolas", "Monaco", monospace` | 代码输入（API Key、response_format） |
| `font-size-xs` | `12px` | 辅助文字 |
| `font-size-sm` | `13px` | 表单、按钮 |
| `font-size-md` | `14px` | 列表项 |
| `font-size-lg` | `15px` | 正文 |
| `font-size-xl` | `16px` | 标题 |

---

## 五、关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 图标库 | Lucide（`lucide-vue-next`） | Vue 3 Tree-shakable，MIT 协议，风格统一 |
| 工具栏交互 | 纯图标 + `::after` 下划线激活 | 极简，与原有交互一脉相承 |
| Token 管理 | 独立 `tokens.css` + `@import` | 集中管理，CSS 预设可覆盖 |
| API 页面布局 | 分组卡片式 | 信息层次清晰，与工具栏卡片语言一致 |
| 反馈机制 | 内联状态行 + AlertDialog 弹窗 | 高频操作用内联（不打断），错误用弹窗（必须关注） |
| 自动连接持久化 | per-preset（`auto_connect` 字段） | 与 API 配置强相关，切换预设自动切换偏好 |
| 颜色体系 | 全 CSS 变量，零硬编码 | 深色主题/CSS 预设自动适配 |

---

## 六、新增依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `lucide-vue-next` | latest | 工具栏 5 个 SVG 图标 + API 设置卡片头部 4 个图标 |

---

## 七、与原 UI_token.md 的关系

`UI_token.md`（v1）定义了初始 Token 和组件约定。本次两项改造后：

- **Token 已迁移**：`:root` 变量从 `App.vue` 移至 `tokens.css`，并新增 15+ Token（`--bg-input`、`--focus-ring`、`--status-dot-*` 等）
- **组件约定不变**：BEM 命名、非 scoped 暴露 class、抽屉统一架构等规则仍然有效
- **本文件为当前权威参考**：后续开发以本文件和 `tokens.css` 为准
