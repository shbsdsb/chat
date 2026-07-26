# backend/app/routes/extensions.py
import os
import json
import shutil
import tempfile
from datetime import datetime, timezone

from flask import request, Response
from app.routes import api_bp
from app.utils.response import ok, fail
from app.extensions import get_extension_manager
import app.extensions.registry as _reg
import app.extensions.installer as _installer
from app.extensions.installer import (
    install_from_git,
    install_from_zip,
    uninstall_extension,
    update_extension,
)
from app.extensions.registry import (
    read_registry,
    add_extension,
    remove_extension,
    get_extension,
    set_extension_state,
)
from app.extensions.permissions import validate_permissions
from app.extensions.loader import unload_extension as _unload


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


@api_bp.route("/extensions")
def list_extensions():
    data = read_registry()
    exts = data.get("extensions", {})
    result = []
    for ext_id, info in exts.items():
        entry = {"id": ext_id, **info}
        manifest_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "manifest.json")
        if os.path.isfile(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                m = json.load(f)
                entry["name"] = m.get("name", ext_id)
                entry["description"] = m.get("description", "")
                entry["frontend"] = bool(m.get("ext_points", {}).get("frontend"))
        else:
            entry["name"] = ext_id
            entry["description"] = ""
            entry["frontend"] = False
        result.append(entry)
    return ok(data=result)


@api_bp.route("/extensions/install", methods=["POST"])
def install_extension():
    install_method = request.form.get("install_method", "zip")

    try:
        if install_method == "git":
            git_url = (request.form.get("git_url") or "").strip()
            git_branch = (request.form.get("git_branch") or "main").strip()
            if not git_url:
                return fail(400, "缺少 git_url")
            ext_id, name = install_from_git(git_url, git_branch)
        elif install_method == "zip":
            uploaded = request.files.get("file")
            if not uploaded:
                return fail(400, "缺少 zip 文件")
            tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            tmp.close()  # Windows: 必须先关闭才能被 save() 重新打开
            try:
                uploaded.save(tmp.name)
                ext_id, name = install_from_zip(tmp.name)
            finally:
                os.unlink(tmp.name)
        else:
            return fail(400, "不支持的安装方式")

        manifest_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        return ok(data={
            "id": ext_id,
            "name": name,
            "manifest": manifest,
            "permissions": manifest.get("permissions", []),
            "pending_approval": True,
        })
    except Exception as e:
        return fail(400, str(e))


@api_bp.route("/extensions/<ext_id>/confirm", methods=["POST"])
def confirm_extension(ext_id):
    """用户审批权限后确认安装"""
    body = request.get_json(silent=True) or {}
    approved_permissions = body.get("permissions", [])

    manifest_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "manifest.json")
    if not os.path.isfile(manifest_path):
        return fail(404, "扩展不存在")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid = validate_permissions(approved_permissions)
    now = datetime.now(timezone.utc).isoformat()
    update_info = manifest.get("update", {})
    install_method = "git" if update_info.get("type") == "git" else "zip"

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
    result = mgr.reload_extension(ext_id)  # api_bp=None: 运行时安装不注册 API 路由（需重启生效）

    return ok(data={
        "id": ext_id,
        "status": result["status"],
        "registered_hooks": result.get("registered_hooks", []),
    })


@api_bp.route("/extensions/<ext_id>/uninstall", methods=["POST"])
def uninstall_extension_route(ext_id):
    if not get_extension(ext_id):
        return fail(404, "扩展不存在")

    mgr = get_extension_manager()
    _unload(ext_id, mgr.dispatcher, mgr._loaded)

    uninstall_extension(ext_id)
    remove_extension(ext_id)

    return ok(message=f"扩展 {ext_id} 已卸载")


@api_bp.route("/extensions/<ext_id>/update", methods=["POST"])
def update_extension_route(ext_id):
    ext = get_extension(ext_id)
    if not ext:
        return fail(404, "扩展不存在")
    if ext.get("install_method") != "git":
        return fail(400, "仅 Git 安装的扩展支持在线更新")

    try:
        new_version = update_extension(ext_id)
        ext["version"] = new_version
        ext["last_updated"] = datetime.now(timezone.utc).isoformat()
        add_extension(ext_id, ext)

        mgr = get_extension_manager()
        result = mgr.reload_extension(ext_id)  # api_bp=None: 运行时安装不注册 API 路由（需重启生效）

        return ok(data={"version": new_version, "status": result["status"]})
    except Exception as e:
        return fail(400, str(e))


@api_bp.route("/extensions/<ext_id>/toggle", methods=["POST"])
def toggle_extension_route(ext_id):
    ext = get_extension(ext_id)
    if not ext:
        return fail(404, "扩展不存在")

    body = request.get_json(silent=True) or {}
    enabled = bool(body.get("enabled", not ext.get("enabled")))
    set_extension_state(ext_id, enabled)

    mgr = get_extension_manager()
    if enabled:
        result = mgr.reload_extension(ext_id)  # api_bp=None: 运行时安装不注册 API 路由（需重启生效）
        return ok(data={"enabled": True, "status": result["status"]})
    else:
        _unload(ext_id, mgr.dispatcher, mgr._loaded)
        return ok(data={"enabled": False})


@api_bp.route("/extensions/install/cancel", methods=["POST"])
def cancel_install():
    """取消未确认的安装，清理扩展目录。"""
    body = request.get_json(silent=True) or {}
    ext_id = (body.get("ext_id") or "").strip()
    if not ext_id:
        # 不带 ext_id 时无操作
        return ok(message="无待取消的安装")
    ext_dir = os.path.join(_reg.EXTENSIONS_DIR, ext_id)
    if os.path.isdir(ext_dir):
        shutil.rmtree(ext_dir, ignore_errors=True)
    return ok(message=f"已取消扩展 {ext_id} 的安装")


@api_bp.route("/extensions/<ext_id>/frontend")
def get_extension_frontend(ext_id):
    """返回扩展前端入口 JS（组件代码 + index.js 合并）。"""
    ext = get_extension(ext_id)
    if not ext:
        return fail(404, "扩展不存在")
    if not ext.get("enabled"):
        return fail(403, "扩展已禁用")

    frontend_dir = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "frontend")
    if not os.path.isdir(frontend_dir):
        return fail(404, "frontend 目录不存在")

    # 收集所有 .js 文件：先 components/ 再 index.js
    scripts = []
    comp_dir = os.path.join(frontend_dir, "components")
    if os.path.isdir(comp_dir):
        for fname in sorted(os.listdir(comp_dir)):
            if fname.endswith(".js"):
                with open(os.path.join(comp_dir, fname), "r", encoding="utf-8") as f:
                    scripts.append(f.read())

    index_path = os.path.join(frontend_dir, "index.js")
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            scripts.append(f.read())

    if not scripts:
        return fail(404, "无前端脚本文件")

    return Response("\n;\n".join(scripts), mimetype="application/javascript")


@api_bp.route("/extensions/<ext_id>/manifest")
def get_extension_manifest(ext_id):
    ext = get_extension(ext_id)
    if not ext:
        return fail(404, "扩展不存在")

    manifest_path = os.path.join(_reg.EXTENSIONS_DIR, ext_id, "manifest.json")
    if not os.path.isfile(manifest_path):
        return fail(404, "manifest.json 不存在")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    return ok(data=manifest)


@api_bp.route("/extensions/<ext_id>/settings")
def get_extension_settings(ext_id):
    ext = get_extension(ext_id)
    if not ext:
        return fail(404, "扩展不存在")
    settings = _read_extension_settings(ext_id)
    return ok(data=settings)


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
