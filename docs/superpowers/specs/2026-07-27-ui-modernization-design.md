# UI 现代化重设计 — 设计规格

> 日期：2026-07-27 | 状态：已确认 | 方案：视觉重构 + 微交互（方案 2）

## 一、目标与范围

对 Chat 应用前端进行全面视觉现代化，采用**现代 SaaS 风格**（类似 Linear/Notion/ChatGPT），纯 CSS 增强，零新增依赖，兼容现有自定义 CSS 预设体系。

### 范围

| 层面 | 内容 |
|------|------|
| Token 体系 | 升级色彩/阴影/圆角，新增玻璃态 Token |
| 聊天气泡 | user 靛蓝渐变 / assistant 灰底，非对称圆角，角色标签 |
| 输入栏 | 玻璃态 wrapper、光晕按钮、脉冲停止态、ModelSelector 徽章行 |
| 欢迎页 | 渐变标题、实心按钮、几何背景、快捷卡片 |
| 顶栏 | 微阴影浮起、渐变色标题、纯图标按钮、指示线 |
| 会话列表 | 靛蓝左侧指示线、淡底 active、hover 优化、时间戳 |
| 微交互 | 消息滑入、打字光标、发送动效、涟漪、折叠过渡、按钮微抬 |

### 不变

- BEM class 命名体系保持（`.bubble-row`, `.bubble`, `.bubble-text`, `.conv-item`, `.input-bar` 等）
- Vue 组件结构保持（少量增强如角色标签，不破坏现有 props/events）
- 自定义 CSS 预设兼容（用户通过 `_injectCss()` 覆盖的样式依然有效）
- 不引入 Tailwind 或任何新 npm 依赖

---

## 二、Token 升级

### 2.1 色彩

| Token | 旧值 | 新值 | 说明 |
|-------|------|------|------|
| `color-bg-primary` | `#fff` | `#fff` | 不变 |
| `color-bg-secondary` | `#fafafa` | `#f8f9fb` | 微冷 |
| `color-bg-tertiary` | `#f5f5f5` | `#f0f1f5` | 蓝灰底色 |
| `color-text-primary` | `#333` | `#1a1a2e` | 更深蓝黑 |
| `color-text-secondary` | `#555` | `#5b5b7a` | 冷调 |
| `color-text-muted` | `#888` | `#8e8ea0` | 冷灰 |
| `color-border` | `#e0e0e0` | `#e2e4eb` | 蓝灰 |
| `color-border-light` | `#d5d5d5` | `#d8dae2` | 统一 |
| `color-accent` | `#4a90d9` | `#4f6ef6` | 靛蓝 |
| `color-danger` | `#e53935` | `#ef4444` | 微调 |
| `color-bg-edit` | `#1e1e1e` | 不变 |  |
| `color-bg-edit-text` | `#d4d4d4` | 不变 |  |

### 2.2 新增：阴影

| Token | 值 | 用途 |
|-------|-----|------|
| `shadow-xs` | `0 1px 2px rgba(0,0,0,0.04)` | 面板轻微浮起 |
| `shadow-sm` | `0 2px 8px rgba(0,0,0,0.06)` | 消息气泡悬停 |
| `shadow-md` | `0 4px 16px rgba(0,0,0,0.08)` | 抽屉面板、弹窗 |
| `shadow-lg` | `0 8px 32px rgba(0,0,0,0.10)` | 模态弹窗 |

### 2.3 圆角

| Token | 旧值 | 新值 |
|-------|------|------|
| `radius-sm` | `6px` | `8px` |
| `radius-md` | `8px` | `10px` |
| `radius-lg` | `12px` | `16px` |
| `radius-xl` | `24px` | `28px` |

### 2.4 新增：玻璃态

```css
--glass-bg: rgba(255,255,255,0.7);
--glass-border: rgba(0,0,0,0.06);
--glass-blur: 12px;
```

### 2.5 新增：动画

| Token | 值 | 用途 |
|-------|-----|------|
| `msg-enter-duration` | `0.25s` | 消息入场 |
| `msg-enter-easing` | `ease-out` | 消息入场缓动 |
| `cursor-blink-duration` | `0.8s` | 打字光标闪烁 |
| `ripple-duration` | `0.5s` | 按钮涟漪 |
| `pulse-duration` | `1.2s` | 停止按钮脉冲 |
| `reasoning-collapse-duration` | `0.3s` | 推理块折叠 |

---

## 三、组件规格

### 3.1 MessageBubble

#### 视觉

- **User 气泡**：`linear-gradient(135deg, #4f6ef6, #6c8cfc)` 底 + `#fff` 字，右对齐，圆角 `16px 4px 16px 16px`，`shadow-sm`
- **Assistant 气泡**：`#f8f9fb` 底 + `#1a1a2e` 字，左对齐，圆角 `4px 16px 16px 16px`，`shadow-xs`
- **角色标签**：气泡上方 `12px` muted 色文字 `你` / `Chat`
- 无边框

#### 编辑模式

- `border: 1.5px solid #4f6ef6` + `shadow-md`，过渡 `0.2s ease`

#### 推理块

- 左侧边框 `3px solid #4f6ef6`（旧：`2px #d0d0d0`）
- 折叠 `max-height` 过渡 `0.3s ease`

#### 兼容

- BEM class 保持：`.bubble-row`, `.bubble`, `.bubble-text`, `.reasoning-block`
- 新增：`.bubble-role-label`（角色标签）、`.bubble-row.entering`（入场态）

---

### 3.2 InputBar

#### 视觉

- **Wrapper**：`background: rgba(255,255,255,0.7)` + `backdrop-filter: blur(12px)` + `shadow-sm` + `radius: 28px`
- **发送按钮**：靛蓝 `#4f6ef6` 实心圆，hover 缩放 1.08 + 光晕 `0 0 16px rgba(79,110,246,0.35)`
- **停止按钮**：红底 + 脉冲 `box-shadow` 呼吸动画

#### 结构增强

- 输入栏上方新增 `.input-toolbar` 行（28px 高），含 ModelSelector 徽章（当前模型名小标签，点击切换）
- 工具栏默认可见，可配置隐藏

#### 兼容

- BEM class 保持：`.input-bar`, `.input-wrapper`, `.input-field`, `.btn-send`
- 新增：`.input-toolbar`, `.model-badge`

---

### 3.3 WelcomeBanner

#### 视觉

- 标题：靛蓝→紫色渐变文字 `background: linear-gradient(135deg, #4f6ef6, #8b5cf6); -webkit-background-clip: text`
- 副标题：`15px` muted
- 主按钮：靛蓝实心 `#4f6ef6`（白字），`shadow-sm`，hover 阴影抬升
- 背景：极淡径向渐变几何图案

#### 结构增强

- 底部快捷操作卡片行（最多 2 张卡片）："开始新对话"、"导入设置"
- 卡片：白底 + `shadow-xs` + `radius-md`，hover 微微抬升

#### 兼容

- BEM class 保持：`.welcome`, `.btn-start`
- 新增：`.welcome-bg`, `.welcome-subtitle`, `.welcome-cards`

---

### 3.4 Top Bar

#### 视觉

- 高度 `48px`，底 `#f8f9fb` + `shadow-xs`
- 标题改为渐变色文字
- 右侧按钮：无边框纯图标，hover `translateY(-1px)` + 底部 2px 靛蓝指示线

#### 结构调整

- "会话记录"按钮移到左侧，改为 ☰ 汉堡图标 + 文字
- Logo/标题使用渐变色

#### 兼容

- BEM class 保持：`.top-bar`, `.top-btn`, `.top-nav`
- 新增：`.top-brand`, `.top-btn-indicator`

---

### 3.5 ConversationItem

#### 视觉

- 圆角 `10px`
- **active**：`background: rgba(79,110,246,0.08)` + 左侧 `3px solid #4f6ef6` 竖条（伪元素 `::before`）
- **hover**：`background: rgba(0,0,0,0.03)`
- 编辑/删除按钮 hover：微圆背景 `rgba(0,0,0,0.06)`

#### 结构增强

- 右侧新增 `.conv-time`：最后更新时间，`12px` muted，右对齐

#### 兼容

- BEM class 保持：`.conv-item`, `.conv-title`, `.conv-actions`
- 新增：`.conv-time`, `.conv-item.active::before`

---

## 四、微交互动效规格

### 4.1 消息入场

```css
@keyframes message-enter {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
```
- 仅对新到达的消息（非历史加载）应用
- 通过 `.bubble-row.entering` class 控制，动画结束后移除 class

### 4.2 流式打字光标

- AI 回复中最后一条 assistant 气泡的 `.bubble-text` 末尾 `::after`
- 内容 `|`，颜色 `#4f6ef6`
- `animation: blink-cursor 0.8s step-end infinite`

### 4.3 发送按钮动效

- **hover**：`scale(1.08)` + 光晕
- **active**：`scale(0.92)`，`0.1s` 回弹
- **流式中（`.is-streaming`）**：脉冲呼吸

```css
@keyframes stop-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
  100% { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
}
```

### 4.4 按钮涟漪

- 仅 `.btn-ripple` class 元素（发送按钮、欢迎页主按钮、保存按钮）
- JS 事件委托：`mousedown` → 创建 `<span class="ripple">` → CSS 动画 → 动画结束移除
- 使用 `getBoundingClientRect()` 计算涟漪原点

```css
@keyframes ripple {
  from { transform: scale(0); opacity: 0.3; }
  to   { transform: scale(4); opacity: 0; }
}
.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  pointer-events: none;
}
```

### 4.5 推理块折叠

- `max-height: 200px` → `0`，`transition: max-height 0.3s ease`
- 箭头图标 `▶` / `▼` 旋转 `transition: transform 0.2s`

### 4.6 顶栏按钮微抬

- hover：`transform: translateY(-1px)` + `::after` 底部 2px 靛蓝指示线
- `transition: all 0.15s ease`

---

## 五、兼容策略

### 5.1 现有 CSS 预设兼容

- 所有 BEM class 名称保持不变
- 新增 class 使用独立命名空间（如 `.model-badge`, `.bubble-role-label`, `.ripple`）
- User CSS 通过 `_injectCss()` + `!important` 覆盖原有样式依然生效
- 新增的伪元素（`::before` 指示线、`::after` 光标）可在用户 CSS 中通过 `display: none` 关闭

### 5.2 主题预设适配

四套主题预设（默认/暗夜护眼/日间暖阳/小清新）需要验证：
- 暗夜护眼：需要调整靛蓝强调色在深色背景上的对比度
- 日间暖阳：靛蓝与暖色背景的协调
- 小清新：靛蓝与薄荷绿的搭配
- 可在实施中微调预设 CSS

### 5.3 不兼容变更

- 无。所有变更均为增量。

---

## 六、实施顺序

1. `UI_token.md` 更新（Token 定义）
2. `App.vue` 全局样式刷新（顶栏、背景色、动画定义）
3. `MessageBubble.vue` 重构
4. `InputBar.vue` 重构
5. `WelcomeBanner.vue` 重构
6. `ConversationItem.vue` 重构
7. 微交互注入（`main.js` 中全局 ripple + 消息入场逻辑）
8. 主题预设 CSS 适配验证

---

## 七、自检清单

- [x] 无 "TBD"、"TODO" 或未完成段落
- [x] 组件规格与 Token 定义一致
- [x] BEM class 兼容策略明确
- [x] 无新增 npm 依赖
- [x] 微交互实现方式（CSS 动画 + 轻量 JS）可落地
