# 扩展功能分组开关 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** features 支持 `type: "group"` 模块嵌套——模块可折叠卡片、级联开关、settings.json 扁平点号键持久化。

**Architecture:** 后端扩展 `_read_extension_settings` 默认值生成和 PUT 校验接受 `模块id.子功能id` 格式；前端抽屉分支渲染 group 卡片（可折叠+模块开关+子开关）；store `toggleFeature` 增加模块级联逻辑；Dashboard 组件适配子功能 key。

**Tech Stack:** Python/Flask + pytest（后端）、Vue 3 SFC + Pinia（前端）

## Global Constraints

- 向后兼容：无 `type` 的扁平 features 继续正常工作
- 一级嵌套：`children` 内不再含 `type: "group"`
- settings.json 扁平点号键：模块关时子功能写 `false` 但保留键（记忆）
- 模块 ON 时不主动覆盖已有子功能值
- 遵循现有代码风格：后端 ok()/fail()、前端组合式 API + Pinia options API

---

### Task 1: 后端 — `_read_extension_settings` 默认值生成扩展

**Files:**
- Modify: `backend/app/routes/extensions.py:54-58`

**Interfaces:**
- Consumes: `manifest["features"]` 数组（现含 `type: "group"` 项）
- Produces: `defaults` dict 包含 `模块id.子功能id` 格式的键

- [ ] **Step 1: 修改默认值生成循环**

找到 `_read_extension_settings` 函数中的循环：

```python
    defaults = {}
    for feat in features_declared:
        if isinstance(feat, dict) and "id" in feat:
            defaults[feat["id"]] = feat.get("default", False)
```

改为：

```python
    defaults = {}
    for feat in features_declared:
        if not isinstance(feat, dict) or "id" not in feat:
            continue
        if feat.get("type") == "group":
            defaults[feat["id"]] = feat.get("default", False)
            for child in feat.get("children", []):
                if isinstance(child, dict) and "id" in child:
                    defaults[f"{feat['id']}.{child['id']}"] = child.get("default", False)
        else:
            defaults[feat["id"]] = feat.get("default", False)
```

- [ ] **Step 2: 运行现有测试确认无回归**

```bash
cd backend && python -m pytest tests/test_extensions.py::TestGetSettings -v --tb=short
```
预期：4 tests PASS（现有扁平 features 测试不受影响）

- [ ] **Step 3: 提交**

```bash
git add backend/app/routes/extensions.py
git commit -m "feat: _read_extension_settings generates default values for type:group children"
```

---

### Task 2: 后端 — PUT /settings 校验扩展 + confirm 初始化

**Files:**
- Modify: `backend/app/routes/extensions.py:319-325`（PUT 校验 known_ids 收集）
- Modify: `backend/app/routes/extensions.py:160-168`（confirm 初始化 settings）
- Modify: `backend/tests/test_extensions.py`（新增 group tests）

**Interfaces:**
- Consumes: `_read_extension_settings()`、`_write_extension_settings()`
- Changes: PUT 校验接受 `模块id.子功能id`；confirm 初始化时写入子功能默认值

- [ ] **Step 1: 新增 group 相关测试**

在 `backend/tests/test_extensions.py` 末尾追加：

```python
# ============================================================
# group (type:group) 测试
# ============================================================

class TestGroupFeatures:
    def test_get_settings_with_group_defaults(self, api_client, tmp_path, monkeypatch):
        """manifest 有 group 时 GET 返回模块 + 子功能点号键"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "group-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "group-ext", "name": "Group Ext", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.2.0",
            "features": [
                {"id": "simple-feat", "label": "Simple", "description": "", "default": True},
                {"id": "my-group", "label": "My Group", "type": "group", "default": True,
                 "children": [
                     {"id": "child-a", "label": "A", "description": "", "default": True},
                     {"id": "child-b", "label": "B", "description": "", "default": False},
                 ]},
            ]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("group-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.get("/api/extensions/group-ext/settings")
        data = resp.get_json()
        assert data["code"] == 0
        f = data["data"]["features"]
        assert f["simple-feat"] is True
        assert f["my-group"] is True
        assert f["my-group.child-a"] is True
        assert f["my-group.child-b"] is False

    def test_put_group_child_key_accepted(self, api_client, tmp_path, monkeypatch):
        """PUT 点号键应被接受"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "group-put"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "group-put", "name": "Group Put", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.2.0",
            "features": [
                {"id": "my-group", "label": "G", "type": "group", "default": True,
                 "children": [{"id": "child-a", "label": "A", "description": "", "default": True}]},
            ]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("group-put", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.put("/api/extensions/group-put/settings",
                              json={"features": {"my-group": True, "my-group.child-a": False}})
        data = resp.get_json()
        assert data["code"] == 0

    def test_put_unknown_child_key_rejected(self, api_client, tmp_path, monkeypatch):
        """未声明的点号键应被拒绝"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "group-reject"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "group-reject", "name": "Group Reject", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.2.0",
            "features": [
                {"id": "my-group", "label": "G", "type": "group", "default": True,
                 "children": [{"id": "child-a", "label": "A", "description": "", "default": True}]},
            ]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("group-reject", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.put("/api/extensions/group-reject/settings",
                              json={"features": {"my-group.unknown-child": True}})
        data = resp.get_json()
        assert data["code"] == 400

    def test_confirm_initializes_group_settings(self, api_client, tmp_path, monkeypatch):
        """confirm 时应生成子功能默认值点号键"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "group-confirm"
        ext_path.mkdir(parents=True)
        manifest = {
            "id": "group-confirm", "name": "GC", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.2.0",
            "features": [
                {"id": "my-group", "label": "G", "type": "group", "default": True,
                 "children": [{"id": "ca", "label": "CA", "description": "", "default": True}]},
            ]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        from app.extensions.registry import write_registry
        write_registry({"extensions": {}})

        resp = api_client.post("/api/extensions/group-confirm/confirm",
                               json={"permissions": []})
        assert resp.get_json()["code"] == 0

        settings_path = ext_path / "settings.json"
        saved = json.loads(settings_path.read_text(encoding="utf-8"))
        assert saved["features"]["my-group"] is True
        assert saved["features"]["my-group.ca"] is True
```

- [ ] **Step 2: 运行新测试 — 预期 FAIL**

```bash
cd backend && python -m pytest tests/test_extensions.py::TestGroupFeatures -v --tb=line
```
预期：4 个测试 FAIL（group 逻辑未实现）

- [ ] **Step 3: 修改 PUT 校验的 known_ids 收集**

在 `put_extension_settings` 中，将：

```python
            for feat in m.get("features", []):
                if isinstance(feat, dict) and "id" in feat:
                    known_ids.add(feat["id"])
```

改为：

```python
            for feat in m.get("features", []):
                if not isinstance(feat, dict) or "id" not in feat:
                    continue
                if feat.get("type") == "group":
                    known_ids.add(feat["id"])
                    for child in feat.get("children", []):
                        if isinstance(child, dict) and "id" in child:
                            known_ids.add(f"{feat['id']}.{child['id']}")
                else:
                    known_ids.add(feat["id"])
```

- [ ] **Step 4: 修改 confirm_extension 的初始化逻辑**

在 `confirm_extension` 中，将：

```python
    features_declared = manifest.get("features", [])
    if features_declared:
        defaults = {}
        for feat in features_declared:
            if isinstance(feat, dict) and "id" in feat:
                defaults[feat["id"]] = feat.get("default", False)
        _write_extension_settings(ext_id, {"features": defaults})
```

改为：

```python
    features_declared = manifest.get("features", [])
    if features_declared:
        defaults = {}
        for feat in features_declared:
            if not isinstance(feat, dict) or "id" not in feat:
                continue
            if feat.get("type") == "group":
                defaults[feat["id"]] = feat.get("default", False)
                for child in feat.get("children", []):
                    if isinstance(child, dict) and "id" in child:
                        defaults[f"{feat['id']}.{child['id']}"] = child.get("default", False)
            else:
                defaults[feat["id"]] = feat.get("default", False)
        _write_extension_settings(ext_id, {"features": defaults})
```

- [ ] **Step 5: 运行测试 — 预期全部 PASS**

```bash
cd backend && python -m pytest tests/test_extensions.py -v --tb=line
```
预期：所有原有 + 新增测试 PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/routes/extensions.py backend/tests/test_extensions.py
git commit -m "feat: PUT validation and confirm init support type:group children dot-keys"
```

---

### Task 3: 前端 — ExtensionDetailDrawer group 卡片渲染

**Files:**
- Modify: `frontend/src/components/ExtensionDetailDrawer.vue`

**Interfaces:**
- Consumes: `manifest.features`（含 `type: "group"` 项）、`store.detailSettings`
- Produces: group 可折叠卡片 + 子功能 toggle

- [ ] **Step 1: 替换功能开关区域的 template 和新增 computed**

**template** — 将功能开关 section（第 70-91 行）替换为：

```html
        <!-- 功能开关 -->
        <section class="detail-section" v-if="features.length">
          <h4 class="detail-section-title">功能开关</h4>
          <template v-for="feat in features" :key="feat.id">
            <!-- 模块（type: group） -->
            <div v-if="feat.type === 'group'" class="feature-group">
              <div
                class="feature-group-header"
                @click="onGroupToggle(feat)"
              >
                <span class="group-arrow" :class="{ expanded: groupExpanded[feat.id] }">▶</span>
                <div class="feature-info">
                  <span class="feature-label">{{ feat.label }}</span>
                </div>
                <label class="feature-toggle" @click.stop>
                  <input
                    type="checkbox"
                    :checked="!!settings.features[feat.id]"
                    @change="onGroupSwitch(feat, $event.target.checked)"
                  />
                  <span class="toggle-slider" />
                </label>
              </div>
              <div v-if="groupExpanded[feat.id] && settings.features[feat.id]" class="feature-group-children">
                <div
                  v-for="child in feat.children"
                  :key="child.id"
                  class="feature-item feature-child"
                >
                  <div class="feature-info">
                    <span class="feature-label">{{ child.label }}</span>
                    <span class="feature-desc" v-if="child.description">{{ child.description }}</span>
                  </div>
                  <label class="feature-toggle">
                    <input
                      type="checkbox"
                      :checked="!!settings.features[feat.id + '.' + child.id]"
                      :disabled="!settings.features[feat.id]"
                      @change="onFeatureChange(feat.id + '.' + child.id, $event.target.checked)"
                    />
                    <span class="toggle-slider" />
                  </label>
                </div>
              </div>
            </div>

            <!-- 叶子功能 -->
            <div v-else class="feature-item">
              <div class="feature-info">
                <span class="feature-label">{{ feat.label }}</span>
                <span class="feature-desc" v-if="feat.description">{{ feat.description }}</span>
              </div>
              <label class="feature-toggle">
                <input
                  type="checkbox"
                  :checked="!!settings.features[feat.id]"
                  @change="onFeatureChange(feat.id, $event.target.checked)"
                />
                <span class="toggle-slider" />
              </label>
            </div>
          </template>
        </section>
```

**script** — 在 `const features = computed(...)` 之后添加：

```javascript
const groupExpanded = ref({});

function onGroupToggle(feat) {
  if (!settings.value.features[feat.id]) return;
  groupExpanded.value[feat.id] = !groupExpanded.value[feat.id];
}

async function onGroupSwitch(feat, value) {
  await store.toggleFeature(store.detailExt.id, feat.id, value);
  if (value) {
    groupExpanded.value[feat.id] = true;
  } else {
    groupExpanded.value[feat.id] = false;
  }
}
```

- [ ] **Step 2: 添加 group 相关 CSS**

在 `</style>` 之前追加：

```css
/* 模块 (group) */
.feature-group {
  margin-bottom: 8px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}

.feature-group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}
.feature-group-header:hover {
  background: #fafafa;
}

.group-arrow {
  font-size: 10px;
  color: #999;
  transition: transform 0.2s;
  flex-shrink: 0;
}
.group-arrow.expanded {
  transform: rotate(90deg);
}

.feature-group-children {
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.feature-child {
  padding-left: 28px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 0;
}
.feature-child:last-child {
  border-bottom: none;
}
```

- [ ] **Step 3: 验证编译**

```bash
cd frontend && npx vite build --logLevel error
```
预期：无错误输出

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/ExtensionDetailDrawer.vue
git commit -m "feat: ExtensionDetailDrawer renders type:group as collapsible cards with child toggles"
```

---

### Task 4: 前端 — stores/extensions.js toggleFeature 级联逻辑

**Files:**
- Modify: `frontend/src/stores/extensions.js:85-98`

**Interfaces:**
- Consumes: `extensionsApi.getManifest()`、`extensionsApi.saveSettings()`
- Changes: `toggleFeature()` 检测 group，级联设置子功能

- [ ] **Step 1: 替换 toggleFeature 实现**

将现有的 `toggleFeature` 方法替换为：

```javascript
    async toggleFeature(extId, featureId, value) {
      const prevFeatures = { ...this.detailSettings?.features || {} };

      // 乐观更新
      if (this.detailSettings?.features) {
        this.detailSettings.features[featureId] = value;
      }

      // 检查是否为 group 开关 → 级联子功能
      try {
        const manifest = await extensionsApi.getManifest(extId);
        const allFeatures = manifest?.features || [];
        const group = allFeatures.find(
          f => f.id === featureId && f.type === 'group'
        );
        if (group && this.detailSettings?.features) {
          for (const child of group.children || []) {
            const ck = `${featureId}.${child.id}`;
            if (!value) {
              this.detailSettings.features[ck] = false;
            }
            // value=true 时保持已有值不变
          }
        }
      } catch {
        // manifest 获取失败时仅操作 featureId 本身
      }

      try {
        await extensionsApi.saveSettings(extId, this.detailSettings);
        this.settingsVersion++;
      } catch (e) {
        if (this.detailSettings?.features) {
          this.detailSettings.features = prevFeatures;
        }
        throw e;
      }
    },
```

- [ ] **Step 2: 验证编译**

```bash
cd frontend && npx vite build --logLevel error
```
预期：无错误输出

- [ ] **Step 3: 提交**

```bash
git add frontend/src/stores/extensions.js
git commit -m "feat: toggleFeature cascades group switch to child features with memory"
```

---

### Task 5: Dashboard — manifest 拆分 + 组件适配

**Files:**
- Modify: `user_data/extensions/dashboard/manifest.json`
- Modify: `test_expand/dashboard/manifest.json`
- Modify: `user_data/extensions/dashboard/frontend/components/DashboardFloating.js`
- Modify: `test_expand/dashboard/frontend/components/DashboardFloating.js`

**Interfaces:**
- Changes: `show-token-count` 叶子 → `session-metrics` group + 3 children；组件读取子功能 key

- [ ] **Step 1: 更新 manifest.json（两个目录）**

将两个 `manifest.json` 中的 features 数组替换为：

```json
  "features": [
    {
      "id": "show-context-usage",
      "label": "显示上下文用量",
      "description": "显示当前会话的上下文窗口使用百分比",
      "default": true
    },
    {
      "id": "auto-refresh",
      "label": "自动刷新指标",
      "description": "每 30 秒自动刷新面板中的统计数据",
      "default": false
    },
    {
      "id": "session-metrics",
      "label": "会话指标",
      "type": "group",
      "default": true,
      "children": [
        { "id": "hit-rate", "label": "命中率", "description": "显示 AI 回复的缓存命中率", "default": true },
        { "id": "request-count", "label": "请求次数", "description": "显示当前会话的 API 请求次数", "default": true },
        { "id": "completion-tokens", "label": "累计 AI Token", "description": "显示累计 AI 输出的 Token 总量", "default": true }
      ]
    }
  ]
```

- [ ] **Step 2: 更新 settings.json（仅 user_data）**

```bash
# 直接用内容覆盖
cat > user_data/extensions/dashboard/settings.json << 'EOF'
{
  "features": {
    "show-context-usage": true,
    "auto-refresh": false,
    "session-metrics": true,
    "session-metrics.hit-rate": true,
    "session-metrics.request-count": true,
    "session-metrics.completion-tokens": true
  }
}
EOF
```

- [ ] **Step 3: 适配 DashboardFloating.js（两个目录）**

找到 `return () => {` 中渲染面板的代码，将会话指标区域（从 `// 会话指标` 注释开始的 h 调用块）替换为按子功能 key 独立控制：

```javascript
        // 会话指标（受 session-metrics group 控制）
        ...(feat['session-metrics'] !== false ? [
        ...(feat['session-metrics.hit-rate'] !== false || feat['session-metrics.request-count'] !== false || feat['session-metrics.completion-tokens'] !== false ? [
        h('div', { style: divider }),
        h('div', { style: sectionTitle }, '📈 会话指标'),
        ] : []),
        ...(feat['session-metrics.hit-rate'] !== false ? [
        h('div', { style: row }, [
          h('span', null, '命中率'),
          h('span', { style: { color: hitColor.value, fontWeight: 600 } },
            `${Math.round((m.last_hit_rate || 0) * 100)}%`),
        ]),
        ] : []),
        ...(feat['session-metrics.request-count'] !== false ? [
        h('div', { style: row }, [
          h('span', null, '请求次数'),
          h('span', { style: { fontWeight: 600 } }, String(m.request_count || 0)),
        ]),
        ] : []),
        ...(feat['session-metrics.completion-tokens'] !== false ? [
        h('div', { style: row }, [
          h('span', null, '累计 AI token'),
          h('span', { style: { fontWeight: 600 } }, formatTokens(m.total_completion_tokens)),
        ]),
        ] : []),
        ] : []),
```

- [ ] **Step 4: 验证编译**

```bash
cd frontend && npx vite build --logLevel error
```
预期：无错误输出

- [ ] **Step 5: 提交**

```bash
git add test_expand/dashboard/manifest.json test_expand/dashboard/frontend/components/DashboardFloating.js
git commit -m "feat: split show-token-count into session-metrics group with 3 child features"
```

---

### Task 6: Plugin_Development_Guide.md 文档同步 + 集成验证

**Files:**
- Modify: `Plugin_Development_Guide.md`（features 规范章节）

- [ ] **Step 1: 更新 features 规范文档**

找到 `#### features 规范 — 可配置功能开关` 章节，在字段说明表后、示例之前插入 group 说明：

```markdown
#### 模块（group）嵌套

`features` 支持 `type: "group"` 声明模块，将相关功能归类到一个可折叠的父级开关下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | `"group"` 表示模块，省略表示叶子功能 |
| `children` | array | 子功能数组，结构与叶子功能相同 |

**约束：**
- 仅支持一级嵌套（`children` 内不再含 `type: "group"`）
- 模块 `id` 与子功能 `id` 在 settings 中以点号连接：`模块id.子功能id`
- 模块开关关闭时子功能全部关闭但保留记忆
- 模块开关重新开启时不覆盖已有子功能状态

**group 示例：**
```

并在现有示例 JSON 之后追加 group 示例：

````markdown
```json
{
  "features": [
    { "id": "simple-toggle", "label": "简单开关", "default": true },
    {
      "id": "advanced-group",
      "label": "高级功能",
      "type": "group",
      "default": true,
      "children": [
        { "id": "feat-a", "label": "功能 A", "default": true },
        { "id": "feat-b", "label": "功能 B", "default": false }
      ]
    }
  ]
}
```
````

- [ ] **Step 2: 更新常见错误表**

在 `### 3.5 manifest.json 常见错误` 表中追加：

```markdown
| group 的 `children` 内使用 `type: "group"` | 加载时忽略嵌套 group | 仅一级嵌套，子功能为叶子 |
| settings 中 `模块id.子功能id` 键不存在 | 按 default 生成 | 确保 manifest 声明了对应的 children |
```

- [ ] **Step 3: 后端全量测试**

```bash
cd backend && python -m pytest -q --tb=line
```
预期：所有测试 PASS（含新增 group 测试）

- [ ] **Step 4: 前端编译验证**

```bash
cd frontend && npx vite build --logLevel error
```
预期：无错误输出

- [ ] **Step 5: 提交**

```bash
git add Plugin_Development_Guide.md
git commit -m "docs: document type:group nested features and cascade behavior in plugin dev guide"
```
