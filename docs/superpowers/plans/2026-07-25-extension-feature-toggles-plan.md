# 扩展功能开关 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为扩展系统新增功能开关能力：manifest 声明 features、详情抽屉展示、settings.json 持久化、ExtensionSlot 运行时传入。

**Architecture:** 后端新增 GET/PUT `/api/extensions/<id>/settings` 端点 + confirm 时初始化 settings.json；前端新建 ExtensionDetailDrawer.vue 右侧抽屉组件，修改 ExtensionManager/Store/API/ExtensionSlot 串联数据流。

**Tech Stack:** Python/Flask（后端）、Vue 3 SFC + Pinia（前端）、pytest（测试）

## Global Constraints

- manifest.json `features` 为可选字段，省略时详情页不显示功能开关区域
- settings.json 不存在时按 manifest default 自动生成
- PUT settings 时校验 feature id 必须在 manifest 的 features 数组中声明
- 值必须是 boolean 类型
- 扩展作者通过 `props.settings` 读取开关状态
- 遵循现有代码风格：后端工厂模式、蓝图装饰器、ok()/fail()；前端组合式 API、Pinia options API

---

### Task 1: 后端 — settings 读写辅助函数

**Files:**
- Modify: `backend/app/routes/extensions.py`（在文件顶部新增两个辅助函数）

**Interfaces:**
- Produces: `_read_extension_settings(ext_id)` → `dict`（读 settings.json，不存在则按 manifest default 生成）
- Produces: `_write_extension_settings(ext_id, data)` → None（写 settings.json）
- Consumes: 无（纯文件 IO，不依赖其他 task）

这两个函数独立于路由，可被 Task 2（路由）和 Task 3（confirm 初始化）复用。

- [ ] **Step 1: 在 `extensions.py` 顶部新增辅助函数**

在现有 import 之后、第一个路由之前插入以下代码：

```python
# backend/app/routes/extensions.py
# 在现有 import 块之后、第一个 @api_bp.route 之前插入：

# ── settings.json 读写辅助 ──────────────────────

def _read_extension_settings(ext_id):
    """读取扩展 settings.json，不存在时按 manifest features.default 生成。

    返回: {"features": {"feat-a": true, "feat-b": false}}
    """
    settings_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "settings.json")
    if os.path.isfile(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass  # 文件损坏，fall through 生成默认值

    # 不存在或损坏 → 按 manifest default 生成
    manifest_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "manifest.json")
    features_declared = []
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
            features_declared = m.get("features", [])

    defaults = {}
    for feat in features_declared:
        if isinstance(feat, dict) and "id" in feat:
            defaults[feat["id"]] = feat.get("default", False)

    return {"features": defaults}


def _write_extension_settings(ext_id, data):
    """写入扩展 settings.json。"""
    settings_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "settings.json")
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/routes/extensions.py
git commit -m "feat: add _read/write_extension_settings helpers for per-extension settings.json"
```

---

### Task 2: 后端 — GET/PUT /api/extensions/\<id\>/settings 路由 + 测试

**Files:**
- Modify: `backend/app/routes/extensions.py`（在 `/manifest` 路由之后新增两个端点）
- Modify: `backend/tests/test_extensions.py`（新增两个测试类）

**Interfaces:**
- Consumes: `_read_extension_settings()`、`_write_extension_settings()`（来自 Task 1）
- Produces: `GET /api/extensions/<ext_id>/settings` → `{code: 0, data: {features: {...}}}`
- Produces: `PUT /api/extensions/<ext_id>/settings` → `{code: 0, message: "..."}` 或 `{code: 400/404, message: "..."}`

- [ ] **Step 1: 写后端测试（先写失败的测试）**

在 `backend/tests/test_extensions.py` 末尾追加两个测试类：

```python
# ============================================================
# Task 2: /api/extensions/<id>/settings 测试
# ============================================================

class TestGetSettings:
    def test_settings_not_found_ext(self, api_client):
        resp = api_client.get("/api/extensions/nonexistent/settings")
        data = resp.get_json()
        assert data["code"] == 404

    def test_settings_no_features_in_manifest(self, api_client, tmp_path, monkeypatch):
        """manifest 无 features 声明时返回空 features"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "no-settings-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {"id": "no-settings-ext", "name": "No Settings", "version": "1.0.0",
                         "permissions": [], "ext_points": {"backend": [], "frontend": []},
                         "min_app_version": "1.0.0"}
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("no-settings-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.get("/api/extensions/no-settings-ext/settings")
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["features"] == {}

    def test_settings_with_features_defaults(self, api_client, tmp_path, monkeypatch):
        """manifest 有 features 声明 + 无 settings.json → 返回 default 值"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "feat-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "feat-ext", "name": "Feature Ext", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.0.0",
            "features": [
                {"id": "auto-save", "label": "自动保存", "description": "...", "default": True},
                {"id": "dark-mode", "label": "暗色模式", "description": "...", "default": False},
            ]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("feat-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.get("/api/extensions/feat-ext/settings")
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["features"]["auto-save"] is True
        assert data["data"]["features"]["dark-mode"] is False

    def test_settings_existing_file(self, api_client, tmp_path, monkeypatch):
        """已有 settings.json → 返回其内容"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "cached-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "cached-ext", "name": "Cached", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.0.0",
            "features": [{"id": "feat-1", "label": "F1", "description": "", "default": True}]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        # 写入一个已修改过的 settings.json（用户关掉了 feat-1）
        (ext_path / "settings.json").write_text(
            '{"features": {"feat-1": false}}', encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("cached-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.get("/api/extensions/cached-ext/settings")
        data = resp.get_json()
        assert data["code"] == 0
        # 应返回用户修改后的值，不是 default
        assert data["data"]["features"]["feat-1"] is False


class TestPutSettings:
    def test_put_settings_not_found(self, api_client):
        resp = api_client.put("/api/extensions/nonexistent/settings",
                              json={"features": {"x": True}})
        data = resp.get_json()
        assert data["code"] == 404

    def test_put_settings_unknown_feature_id(self, api_client, tmp_path, monkeypatch):
        """传入 manifest 中未声明的 feature id 应被拒绝"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "strict-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "strict-ext", "name": "Strict", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.0.0",
            "features": [{"id": "allowed-feat", "label": "OK", "description": "", "default": True}]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("strict-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.put("/api/extensions/strict-ext/settings",
                              json={"features": {"unknown-feat": True}})
        data = resp.get_json()
        assert data["code"] == 400  # 未声明的 feature id
        assert "unknown-feat" in data["message"]

    def test_put_settings_non_boolean_value(self, api_client, tmp_path, monkeypatch):
        """非 boolean 值应被拒绝"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "type-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "type-ext", "name": "Type", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.0.0",
            "features": [{"id": "feat-1", "label": "F1", "description": "", "default": True}]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("type-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        resp = api_client.put("/api/extensions/type-ext/settings",
                              json={"features": {"feat-1": "not-a-bool"}})
        data = resp.get_json()
        assert data["code"] == 400

    def test_put_settings_success(self, api_client, tmp_path, monkeypatch):
        """成功保存并持久化"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "save-ext"
        ext_path.mkdir(parents=True)
        manifest_data = {
            "id": "save-ext", "name": "Save", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.0.0",
            "features": [
                {"id": "feat-a", "label": "A", "description": "", "default": True},
                {"id": "feat-b", "label": "B", "description": "", "default": False},
            ]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        from app.extensions.registry import add_extension, write_registry
        write_registry({"extensions": {}})
        add_extension("save-ext", {
            "version": "1.0.0", "enabled": True,
            "installed_at": "2026-01-01T00:00:00Z",
            "install_method": "zip",
            "permissions_granted": []
        })

        # 先 PUT 修改
        resp = api_client.put("/api/extensions/save-ext/settings",
                              json={"features": {"feat-a": False, "feat-b": True}})
        data = resp.get_json()
        assert data["code"] == 0

        # 验证文件已写入
        settings_path = ext_path / "settings.json"
        assert settings_path.is_file()
        saved = json.loads(settings_path.read_text(encoding="utf-8"))
        assert saved["features"]["feat-a"] is False
        assert saved["features"]["feat-b"] is True

        # GET 再次验证
        resp = api_client.get("/api/extensions/save-ext/settings")
        data = resp.get_json()
        assert data["data"]["features"]["feat-a"] is False
        assert data["data"]["features"]["feat-b"] is True
```

- [ ] **Step 2: 运行测试 — 确认全部 FAIL**

```bash
cd backend && python -m pytest tests/test_extensions.py::TestGetSettings tests/test_extensions.py::TestPutSettings -v
```
预期：所有 7 个测试 FAIL（路由不存在，返回 404）

- [ ] **Step 3: 实现 GET /api/extensions/\<ext_id\>/settings 路由**

在 `backend/app/routes/extensions.py` 的 `get_extension_manifest()` 函数之后追加：

```python
@api_bp.route("/extensions/<ext_id>/settings")
def get_extension_settings(ext_id):
    ext = get_extension(ext_id)
    if not ext:
        return fail(404, "扩展不存在")
    settings = _read_extension_settings(ext_id)
    return ok(data=settings)
```

- [ ] **Step 4: 实现 PUT /api/extensions/\<ext_id\>/settings 路由**

紧接着追加：

```python
@api_bp.route("/extensions/<ext_id>/settings", methods=["PUT"])
def put_extension_settings(ext_id):
    ext = get_extension(ext_id)
    if not ext:
        return fail(404, "扩展不存在")

    body = request.get_json(silent=True) or {}
    new_features = body.get("features")
    if not isinstance(new_features, dict):
        return fail(400, "请求体必须包含 features 字段，且为对象类型")

    # 读取 manifest 获取合法的 feature id 列表
    manifest_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "manifest.json")
    known_ids = set()
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
            for feat in m.get("features", []):
                if isinstance(feat, dict) and "id" in feat:
                    known_ids.add(feat["id"])

    # 校验：未知 feature id
    for fid in new_features:
        if fid not in known_ids:
            return fail(400, f"未知的功能 ID：{fid}")

    # 校验：值必须是 boolean
    for fid, val in new_features.items():
        if not isinstance(val, bool):
            return fail(400, f"功能 {fid} 的值必须是布尔类型")

    # 保存
    _write_extension_settings(ext_id, {"features": new_features})
    return ok(message="设置已保存")
```

- [ ] **Step 5: 运行测试 — 确认全部 PASS**

```bash
cd backend && python -m pytest tests/test_extensions.py::TestGetSettings tests/test_extensions.py::TestPutSettings -v
```
预期：7 tests PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/routes/extensions.py backend/tests/test_extensions.py
git commit -m "feat: add GET/PUT /api/extensions/<id>/settings endpoints with validation"
```

---

### Task 3: 后端 — confirm_extension 初始化 settings.json

**Files:**
- Modify: `backend/app/routes/extensions.py`（`confirm_extension()` 函数内部，`add_extension()` 之后）
- Modify: `backend/tests/test_extensions.py`（在 `TestConfirmExtension` 类中新增一个测试）

**Interfaces:**
- Consumes: `_write_extension_settings()`（来自 Task 1）
- Changes: `confirm_extension()` 在确认安装后，根据 manifest features.default 写入初始 settings.json

- [ ] **Step 1: 新增 confirm 初始化 settings 的测试**

在 `backend/tests/test_extensions.py` 的 `TestConfirmExtension` 类中追加：

```python
    def test_confirm_initializes_settings(self, api_client, tmp_path, monkeypatch):
        """确认安装后应自动按 manifest features.default 创建 settings.json"""
        ext_dir = tmp_path / "extensions"
        monkeypatch.setattr("app.extensions.installer.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.loader.EXTENSIONS_DIR", str(ext_dir))
        monkeypatch.setattr("app.extensions.registry.EXTENSIONS_DIR", str(ext_dir))

        ext_path = ext_dir / "feat-confirm"
        ext_path.mkdir(parents=True)
        manifest = {
            "id": "feat-confirm", "name": "Feat Confirm", "version": "1.0.0",
            "permissions": [], "ext_points": {"backend": [], "frontend": []},
            "min_app_version": "1.0.0",
            "features": [
                {"id": "feat-x", "label": "X", "description": "", "default": True},
                {"id": "feat-y", "label": "Y", "description": "", "default": False},
            ]
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        from app.extensions.registry import write_registry
        write_registry({"extensions": {}})

        resp = api_client.post("/api/extensions/feat-confirm/confirm",
                               json={"permissions": []})
        data = resp.get_json()
        assert data["code"] == 0

        # 验证 settings.json 已生成
        settings_path = ext_path / "settings.json"
        assert settings_path.is_file()
        saved = json.loads(settings_path.read_text(encoding="utf-8"))
        assert saved["features"]["feat-x"] is True
        assert saved["features"]["feat-y"] is False
```

- [ ] **Step 2: 运行新测试 — 确认 FAIL**

```bash
cd backend && python -m pytest tests/test_extensions.py::TestConfirmExtension::test_confirm_initializes_settings -v
```
预期：FAIL（settings.json 未生成）

- [ ] **Step 3: 修改 `confirm_extension()` 函数**

在 `backend/app/routes/extensions.py` 的 `confirm_extension()` 函数中，`add_extension()` 之后、`mgr.reload_extension()` 之前，插入初始化逻辑：

找到这段代码：
```python
    add_extension(ext_id, {
        "version": manifest["version"],
        "enabled": True,
        "installed_at": now,
        "install_method": install_method,
        "git_url": update_info.get("url", ""),
        "git_branch": update_info.get("branch", "main"),
        "last_updated": now,
        "permissions_granted": valid,
    })

    mgr = get_extension_manager()
    result = mgr.reload_extension(ext_id)
```

改为：
```python
    add_extension(ext_id, {
        "version": manifest["version"],
        "enabled": True,
        "installed_at": now,
        "install_method": install_method,
        "git_url": update_info.get("url", ""),
        "git_branch": update_info.get("branch", "main"),
        "last_updated": now,
        "permissions_granted": valid,
    })

    # 初始化 settings.json（按 manifest features.default）
    features_declared = manifest.get("features", [])
    if features_declared:
        defaults = {}
        for feat in features_declared:
            if isinstance(feat, dict) and "id" in feat:
                defaults[feat["id"]] = feat.get("default", False)
        _write_extension_settings(ext_id, {"features": defaults})

    mgr = get_extension_manager()
    result = mgr.reload_extension(ext_id)
```

- [ ] **Step 4: 运行测试 — 确认 PASS**

```bash
cd backend && python -m pytest tests/test_extensions.py::TestConfirmExtension -v
```
预期：3 tests PASS（原有 2 个 + 新增 1 个）

- [ ] **Step 5: 提交**

```bash
git add backend/app/routes/extensions.py backend/tests/test_extensions.py
git commit -m "feat: initialize settings.json on extension confirm with manifest feature defaults"
```

---

### Task 4: 前端 — api/extensions.js 新增 settings 方法

**Files:**
- Modify: `frontend/src/api/extensions.js`

**Interfaces:**
- Produces: `extensionsApi.getSettings(extId)` → Promise\<`{features: {...}}`\>
- Produces: `extensionsApi.saveSettings(extId, settings)` → Promise\<void\>

- [ ] **Step 1: 在返回对象末尾添加两个方法**

在 `frontend/src/api/extensions.js` 的 `toggle()` 方法之后、`};` 闭合之前追加：

```javascript
  getSettings(extId) {
    return http.get(`/extensions/${extId}/settings`);
  },
  saveSettings(extId, settings) {
    return http.put(`/extensions/${extId}/settings`, settings);
  },
```

完整 closing `};` 之后不变。

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/extensions.js
git commit -m "feat: add getSettings/saveSettings to extensions API"
```

---

### Task 5: 前端 — stores/extensions.js 新增详情状态和操作

**Files:**
- Modify: `frontend/src/stores/extensions.js`

**Interfaces:**
- Produces: `state.detailExt`, `state.detailSettings`, `state.detailLoading`
- Produces: `actions.openDetail(ext)`, `actions.closeDetail()`, `actions.toggleFeature(extId, featureId, value)`

- [ ] **Step 1: 修改 store 的 state 和 actions**

修改 `frontend/src/stores/extensions.js`，在 `state()` 中新增三个字段：

```javascript
// state: () => ({
//   原有字段保持不变 ...
//   在 items, pendingApproval, loading 之后追加:

    detailExt: null,        // 当前查看详情的扩展对象
    detailSettings: null,   // { features: {...} }
    detailLoading: false,
```

在 `actions` 中，`toggle()` 方法之后、`};` 闭合之前追加三个 action：

```javascript
    async openDetail(ext) {
      this.detailExt = ext;
      this.detailLoading = true;
      try {
        this.detailSettings = await extensionsApi.getSettings(ext.id);
      } catch {
        this.detailSettings = { features: {} };
      } finally {
        this.detailLoading = false;
      }
    },

    closeDetail() {
      this.detailExt = null;
      this.detailSettings = null;
    },

    async toggleFeature(extId, featureId, value) {
      const previous = this.detailSettings?.features?.[featureId];
      if (this.detailSettings?.features) {
        this.detailSettings.features[featureId] = value;
      }
      try {
        await extensionsApi.saveSettings(extId, this.detailSettings);
      } catch (e) {
        // 回滚
        if (this.detailSettings?.features) {
          this.detailSettings.features[featureId] = previous;
        }
        throw e;
      }
    },
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/stores/extensions.js
git commit -m "feat: add detailExt/detailSettings/toggleFeature to extensions store"
```

---

### Task 6: 前端 — ExtensionDetailDrawer.vue 新建

**Files:**
- Create: `frontend/src/components/ExtensionDetailDrawer.vue`

**Interfaces:**
- Consumes: `useExtensionsStore`（来自 Task 5）
- Consumes: `useResizableDrawer` composable
- Produces: 右侧可拖拽抽屉，展示扩展全部信息 + 功能开关

- [ ] **Step 1: 创建组件文件**

```vue
<!-- frontend/src/components/ExtensionDetailDrawer.vue -->
<template>
  <div
    class="drawer-panel"
    :class="{ open: !!store.detailExt, resizing: resizing }"
    :style="{ width: !!store.detailExt ? drawerWidth + 'px' : '0' }"
  >
    <div class="drawer-resize-handle" @mousedown.prevent="onResizeStart" />
    <div v-if="store.detailExt" class="drawer-body">
      <!-- 标题栏 -->
      <div class="detail-header">
        <div class="detail-title-row">
          <h3 class="detail-name">{{ store.detailExt.name || store.detailExt.id }}</h3>
          <button class="detail-close" @click="store.closeDetail()">✕</button>
        </div>
        <div class="detail-meta">
          <span class="detail-version">v{{ store.detailExt.version || '0.0.0' }}</span>
          <span v-if="manifest?.author" class="detail-author">by {{ manifest.author }}</span>
        </div>
      </div>

      <div v-if="detailLoading" class="detail-loading">加载中…</div>

      <template v-else>
        <!-- 基本信息 -->
        <section class="detail-section">
          <h4 class="detail-section-title">基本信息</h4>
          <div class="detail-row" v-if="manifest?.description">
            <span class="detail-label">描述</span>
            <span class="detail-value">{{ manifest.description }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">ID</span>
            <span class="detail-value detail-mono">{{ store.detailExt.id }}</span>
          </div>
          <div class="detail-row" v-if="store.detailExt.installed_at">
            <span class="detail-label">安装时间</span>
            <span class="detail-value">{{ formatDate(store.detailExt.installed_at) }}</span>
          </div>
          <div class="detail-row" v-if="store.detailExt.install_method">
            <span class="detail-label">安装方式</span>
            <span class="detail-value">{{ store.detailExt.install_method === 'git' ? 'Git' : 'ZIP' }}</span>
          </div>
        </section>

        <!-- 权限 -->
        <section class="detail-section" v-if="manifest?.permissions?.length">
          <h4 class="detail-section-title">权限</h4>
          <ul class="detail-list">
            <li v-for="p in manifest.permissions" :key="p" class="detail-list-item">{{ p }}</li>
          </ul>
        </section>

        <!-- 扩展点 -->
        <section class="detail-section" v-if="hasExtPoints">
          <h4 class="detail-section-title">扩展点</h4>
          <div v-if="manifest.ext_points?.backend?.length" class="detail-row">
            <span class="detail-label">后端钩子</span>
            <span class="detail-value">
              <code v-for="bp in manifest.ext_points.backend" :key="bp" class="detail-code">{{ bp }}</code>
            </span>
          </div>
          <div v-if="manifest.ext_points?.frontend?.length" class="detail-row">
            <span class="detail-label">前端面板</span>
            <span class="detail-value">
              <code v-for="fp in manifest.ext_points.frontend" :key="fp" class="detail-code">{{ fp }}</code>
            </span>
          </div>
        </section>

        <!-- 功能开关 -->
        <section class="detail-section" v-if="features.length">
          <h4 class="detail-section-title">功能开关</h4>
          <div
            v-for="feat in features"
            :key="feat.id"
            class="feature-item"
          >
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
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useExtensionsStore } from '@/stores/extensions';
import { useResizableDrawer } from '@/composables/useResizableDrawer';
import { extensionsApi } from '@/api/extensions';
import { useAlertStore } from '@/stores/alert';

const store = useExtensionsStore();
const alert = useAlertStore();
const { drawerWidth, resizing, onResizeStart } = useResizableDrawer('detail', { defaultWidth: 360 });
const detailLoading = ref(false);
const manifest = ref(null);

// 当 detailExt 变化时拉取 manifest
watch(() => store.detailExt, async (ext) => {
  if (!ext) {
    manifest.value = null;
    detailLoading.value = false;
    return;
  }
  detailLoading.value = true;
  try {
    manifest.value = await extensionsApi.getManifest(ext.id);
  } catch {
    manifest.value = null;
  } finally {
    detailLoading.value = false;
  }
}, { immediate: true });

const features = computed(() => manifest.value?.features || []);
const settings = computed(() => store.detailSettings || { features: {} });
const hasExtPoints = computed(() => {
  return (manifest.value?.ext_points?.backend?.length ||
          manifest.value?.ext_points?.frontend?.length);
});

async function onFeatureChange(featureId, value) {
  try {
    await store.toggleFeature(store.detailExt.id, featureId, value);
  } catch (e) {
    alert.show('保存设置失败：' + (e?.message || '未知错误'));
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '-';
  try {
    const d = new Date(isoStr);
    return d.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return isoStr;
  }
}
</script>

<style scoped>
.drawer-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 0;
  background: #fff;
  border-left: 1px solid #e5e5e5;
  overflow: hidden;
  transition: width 0.2s ease;
  z-index: 100;
}

.drawer-panel.open {
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.08);
}

.drawer-resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  z-index: 10;
}
.drawer-resize-handle:hover {
  background: rgba(74, 144, 217, 0.3);
}

.drawer-body {
  padding: 20px 24px 40px;
  height: 100%;
  overflow-y: auto;
}

/* 标题 */
.detail-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.detail-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.detail-close:hover {
  background: #f5f5f5;
  color: #333;
}

.detail-meta {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 13px;
  color: #888;
}

/* 分区 */
.detail-section {
  margin-bottom: 20px;
}

.detail-section-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-row {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.6;
}

.detail-label {
  color: #888;
  flex-shrink: 0;
  min-width: 60px;
}

.detail-value {
  color: #555;
}

.detail-mono {
  font-family: monospace;
  font-size: 12px;
}

.detail-list {
  margin: 0;
  padding: 0 0 0 16px;
  list-style: disc;
}

.detail-list-item {
  font-size: 13px;
  color: #555;
  padding: 2px 0;
  font-family: monospace;
}

.detail-code {
  display: inline-block;
  background: #f5f5f5;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  color: #555;
  margin: 1px 2px;
}

/* 功能开关 */
.feature-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}
.feature-item:last-child {
  border-bottom: none;
}

.feature-info {
  flex: 1;
  min-width: 0;
}

.feature-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.feature-desc {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.feature-toggle {
  position: relative;
  width: 40px;
  height: 22px;
  flex-shrink: 0;
  cursor: pointer;
}

.feature-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: #ccc;
  border-radius: 11px;
  transition: background 0.2s;
}
.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}

.feature-toggle input:checked + .toggle-slider {
  background: #4a90d9;
}
.feature-toggle input:checked + .toggle-slider::after {
  transform: translateX(18px);
}

.detail-loading {
  text-align: center;
  color: #999;
  padding: 32px 0;
  font-size: 14px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/ExtensionDetailDrawer.vue
git commit -m "feat: add ExtensionDetailDrawer with full manifest info and feature toggles"
```

---

### Task 7: 前端 — ExtensionManager.vue 集成详情按钮和抽屉

**Files:**
- Modify: `frontend/src/components/ExtensionManager.vue`

**Interfaces:**
- Consumes: `ExtensionDetailDrawer`（来自 Task 6）、`useExtensionsStore`（来自 Task 5）
- Produces: 每张扩展卡片新增"详情"按钮，点击打开抽屉

- [ ] **Step 1: 修改模板和 script**

两处修改：

**① template — 在 `.ext-controls` 中新增"详情"按钮：**

找到：
```html
          <button class="ext-btn ext-btn-update" @click="onUpdate(ext)">更新</button>
          <button class="ext-btn ext-btn-uninstall" @click="confirmUninstall(ext)">卸载</button>
```

改为：
```html
          <button class="ext-btn ext-btn-update" @click="onUpdate(ext)">更新</button>
          <button class="ext-btn ext-btn-uninstall" @click="confirmUninstall(ext)">卸载</button>
          <button class="ext-btn ext-btn-detail" @click="store.openDetail(ext)">详情</button>
```

**② template — 在 `</div>` 根元素闭合前引入抽屉：**

在 `</BaseDialog>`（卸载确认弹窗的闭合标签）之后、`</div>`（根 `.ext-manager` 闭合标签）之前：
```html
    <ExtensionDetailDrawer />
```

**③ script — 导入抽屉组件：**

在 `<script setup>` 的 import 块中追加：
```javascript
import ExtensionDetailDrawer from '@/components/ExtensionDetailDrawer.vue';
```

**④ style — 新增详情按钮样式：**

在 `.ext-btn-uninstall:hover` 规则之后追加：
```css
.ext-btn-detail {
  background: #fff;
  color: #666;
  border-color: #ddd;
}
.ext-btn-detail:hover {
  background: #f5f5f5;
  color: #333;
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/ExtensionManager.vue
git commit -m "feat: add detail button to ExtensionManager cards, wire ExtensionDetailDrawer"
```

---

### Task 8: 前端 — ExtensionSlot.vue 传入 settings props

**Files:**
- Modify: `frontend/src/extensions/ExtensionSlot.vue`

**Interfaces:**
- Consumes: `extensionsApi.getSettings()`（来自 Task 4）
- Produces: 每个扩展组件额外接收 `settings` prop（`{features: {...}}`）

- [ ] **Step 1: 修改 ExtensionSlot.vue**

**① import 追加：**

在 `<script setup>` 的 import 块中追加：
```javascript
import { extensionsApi } from '@/api/extensions';
```

**② 新增 settings 加载逻辑：**

在 `loadComponents()` 函数之前，新增一个 `settingsMap` ref 和加载函数：

```javascript
const settingsMap = ref({});

async function loadSettings() {
  const map = {};
  await Promise.all(
    extensionsStore.enabledExtensions.map(async (ext) => {
      try {
        const s = await extensionsApi.getSettings(ext.id);
        map[ext.id] = s;
      } catch {
        map[ext.id] = { features: {} };
      }
    })
  );
  settingsMap.value = map;
}
```

**③ 修改 `loadComponents()` 函数：**

找到：
```javascript
        props: {
          message: props.message,
          conversation: props.conversation,
          api: createExtensionApi(ext.id),
        },
```

改为：
```javascript
        props: {
          message: props.message,
          conversation: props.conversation,
          api: createExtensionApi(ext.id),
          settings: settingsMap.value[ext.id] || { features: {} },
        },
```

**④ 修改 `loadAllAndRender()` 函数：**

找到：
```javascript
async function loadAllAndRender() {
  await Promise.all(
    extensionsStore.enabledExtensions.map(e => loadExtensionFrontend(e))
  );
  loadComponents();
}
```

改为：
```javascript
async function loadAllAndRender() {
  await Promise.all(
    extensionsStore.enabledExtensions.map(e => loadExtensionFrontend(e))
  );
  await loadSettings();
  loadComponents();
}
```

**⑤ 移除旧的 `computed` 未使用的 import（如果有的话）** — 确保 import 块中有 `ref`：
```javascript
import { shallowRef, ref, watch, onMounted, markRaw } from 'vue';
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/extensions/ExtensionSlot.vue
git commit -m "feat: load and pass extension settings as props to extension components"
```

---

### Task 9: 集成验证

**Files:**
- 无新建文件

**操作：**
- [ ] **Step 1: 启动后端**

```bash
cd backend && python run.py
```
预期：Flask 启动在 127.0.0.1:5000，无报错。

- [ ] **Step 2: 启动前端**

```bash
cd frontend && npm run dev
```
预期：Vite 启动在 127.0.0.1:5173，无编译错误。

- [ ] **Step 3: 手动验证**

1. 打开浏览器访问 http://127.0.0.1:5173
2. 进入设置页 → 扩展管理
3. 确认安装的扩展（如有 dashboard 扩展）卡片右侧出现"详情"按钮
4. 点击"详情"→ 右侧滑出抽屉，展示基本信息、权限、扩展点
5. 如果扩展有 features 声明，展示功能开关区域
6. 拨动一个开关 → 刷新页面 → 确认开关状态持久化
7. 验证 manifest 无 features 的扩展不显示开关区域

- [ ] **Step 4: 后端测试全体通过**

```bash
cd backend && python -m pytest tests/test_extensions.py -v
```
预期：所有测试 PASS（含 Task 2 新增的 7 个 + Task 3 新增的 1 个）。

---

### Task 10: 更新 dashboard 扩展 manifest（可选）

**Files:**
- Modify: `test_expand/dashboard/manifest.json`

为 dashboard 扩展示例添加 features 声明，供开发和测试参考：

- [ ] **Step 1: 在 manifest.json 中添加 features**

在 `test_expand/dashboard/manifest.json` 中，`"min_app_version"` 之后插入：

```json
  "features": [
    {
      "id": "show-token-count",
      "label": "显示 Token 计数",
      "description": "在面板中显示每次对话的 Token 消耗量",
      "default": true
    },
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
    }
  ],
```

注意 JSON 逗号 — `min_app_version` 行末尾加逗号。

- [ ] **Step 2: 提交**

```bash
git add test_expand/dashboard/manifest.json
git commit -m "docs: add features declaration to dashboard extension example"
```
