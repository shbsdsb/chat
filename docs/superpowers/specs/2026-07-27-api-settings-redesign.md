# API 设置页面重设计 — 设计规格

> **日期**：2026-07-27  
> **状态**：已确认  
> **视觉参考**：`temp_api_preview/index.html`（分组卡片式 v2）

---

## 1. 问题

API 设置页面（`SettingsView.vue`）存在 13 个具体问题：零设计 token、border-radius 混用（4/6/8/12px）、反馈机制混用、无字段验证、无 loading 态、focus 样式不一致等。工具栏已升级为精美 Lucide 图标，内部页面需匹配。

## 2. 目标

将 API 设置页面改为**轻量卡片式**布局，统一使用 CSS 变量，新增连接状态指示器和自动连接开关，重设计测试按钮。

## 3. 整体布局

```
┌─────────────────────────────────────┐
│ API 设置                             │
│ 配置 AI 模型的连接信息和参数          │
├─────────────────────────────────────┤
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

| 属性 | 值 |
|------|-----|
| 背景 | `var(--bg-primary)` |
| 边框 | `1px solid var(--border)` |
| 圆角 | `var(--radius-lg)` = 16px |
| 阴影 | `var(--shadow-xs)` |
| 内边距 | 16px 18px |
| 间距 | 16px（gap） |
| 头部 | icon（accent 色, 18px）+ label（13px, text-secondary） |

## 4. 表单控件统一规格

| 元素 | 样式 |
|------|------|
| `input` / `select` / `textarea` | `bg: var(--bg-input)=#fafbfc`, `border: 1px solid var(--border-light)`, `radius: var(--radius-sm)=8px`, `padding: 8px 12px`, `font-size: 13px` |
| 所有控件 focus | `border-color: var(--accent)` + `box-shadow: var(--focus-ring)` = `0 0 0 3px rgba(79,110,246,0.1)` |
| 标签 | `font-size: 11px`, `color: var(--text-muted)`, `text-transform: uppercase` |
| `textarea` | `font-family: monospace`, `min-height: 90px`, `resize: vertical` |
| 图标按钮 | `32×32px`, `bg: var(--bg-input)`, `border: 1px solid var(--border-light)` |
| disabled | 统一 `opacity: 0.45` |

**关键修正**：select 新增 focus 样式（原来无）、所有 border-radius 统一 8px、输入框浅灰底区分可编辑区。

## 5. 状态指示行（新增）

位于响应格式卡片与测试按钮之间。

```
┌──────────────────────────────────────┐
│ ● 已连接 · 8 个模型可用    [✓] 自动连接 │
└──────────────────────────────────────┘
```

### 左侧：连接状态

| 状态 | 圆点 | 文字 |
|------|------|------|
| 未连接 | `var(--status-dot-disconnected)` = `#ccc` | "未连接" |
| 测试中 | `var(--accent)` + `pulse-dot` 动画 | "正在测试连接..." |
| 已连接 | `var(--status-dot-connected)` = `#22c55e` | "已连接 · N 个模型可用" |

- 圆点：`8×8px`, `border-radius: 50%`
- 脉冲动画：1s 循环缩放透明度（50% → 1.0, 0% → 0.4）

### 右侧：自动连接开关

- `18×18px` 圆角正方形（`border-radius: 4px`）
- 关闭：浅灰框 + 浅灰底
- 开启：accent 色底 + 白色 SVG 对号 ✓
- 右侧文字 "自动连接"，`12px`, `var(--text-muted)`
- 数据：`settingsStore.autoConnect` 布尔值

## 6. 测试按钮重设计

从全宽大色块改为紧凑型图标按钮。

| 属性 | 值 |
|------|-----|
| 类型 | `inline-flex`（不拉伸） |
| 尺寸 | `padding: 8px 18px`, `font-size: 13px` |
| 背景 | `var(--test-btn-bg)` = `var(--accent)` |
| 阴影 | `0 1px 3px rgba(79,110,246,0.2)` |
| hover | 背景 `--accent-light` + 上浮 1px + 阴影加深 |
| disabled | `opacity: 0.45` |

按钮文案：默认 "测试连接"，已连接变为 "重新测试"，测试中显示 spinner + "测试中..."。

## 7. CSS Token 文件（新增）

**新建** `frontend/src/assets/tokens.css`：

```css
:root {
  --bg-primary: #fff;
  --bg-secondary: #f8f9fb;
  --bg-input: #fafbfc;
  --bg-input-hover: #f0f1f5;
  --text-primary: #1a1a2e;
  --text-secondary: #5b5b7a;
  --text-muted: #8e8ea0;
  --border: #e2e4eb;
  --border-light: #d8dae2;
  --accent: #4f6ef6;
  --accent-light: #6c8cfc;
  --accent-bg: rgba(79,110,246,0.08);
  --danger: #ef4444;
  --danger-bg: #fef2f2;
  --success: #2e7d32;
  --success-bg: #f0faf0;
  --success-border: #c8e6c9;
  --error-text: #991b1b;
  --error-bg: #fef2f2;
  --error-border: #fecaca;
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 28px;
  --focus-ring: 0 0 0 3px rgba(79,110,246,0.1);

  /* API 设置页面专用 */
  --card-icon-color: var(--accent);
  --test-btn-bg: var(--accent);
  --test-btn-text: #fff;
  --status-dot-disconnected: #ccc;
  --status-dot-connected: #22c55e;
  --toggle-bg-off: #e2e4eb;
  --toggle-bg-on: var(--accent);
}
```

`App.vue` 现有 `:root` 变量迁移到此文件，改为 `@import "@/assets/tokens.css";`。

## 8. 反馈机制

| 场景 | 方式 | 说明 |
|------|------|------|
| 测试连接成功 | 状态指示行绿点 + 内联绿色提示 | 持续可见 |
| 测试连接失败 | AlertDialog 弹窗 | 重要错误 |
| 保存/删除成功 | 全局 AlertDialog（现有） | 保持现有方案 |
| 表单不完整 | AlertDialog warning | 保持现有方案 |

## 9. 实施范围

| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | `frontend/src/assets/tokens.css` | CSS 变量集中管理 |
| **修改** | `frontend/src/App.vue` | `:root` → `@import tokens.css` + API 专用变量 |
| **重写** | `frontend/src/views/SettingsView.vue` | 卡片布局 + 状态行 + 自动连接 + 测试按钮 |
| **修改** | `frontend/src/components/PresetSelector.vue` | 变量化样式 |
| **修改** | `frontend/src/components/ModelSelector.vue` | 变量化样式 |
| **修改** | `frontend/src/components/ResponseFormatInput.vue` | 变量化样式 |
| **修改** | `frontend/src/stores/settings.js` | 新增 `autoConnect` + `connectionStatus` |

**不在此范围**：`BaseDialog.vue`（弹窗）、后端 API、CSS 预设系统。

## 10. 审查记录

| 日期 | 审查者 | 结果 |
|------|--------|------|
| 2026-07-27 | 用户（可视化预览 v2） | ✅ 全部确认 |
