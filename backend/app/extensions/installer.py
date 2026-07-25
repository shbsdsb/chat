import json
import os
import shutil
import subprocess
import tempfile
import zipfile

_PACKAGE_DIR = os.path.dirname(__file__)
EXTENSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(_PACKAGE_DIR)),
    "user_data", "extensions"
)


def get_extensions_dir():
    return EXTENSIONS_DIR


def _read_manifest(ext_dir):
    path = os.path.join(ext_dir, "manifest.json")
    if not os.path.isfile(path):
        raise ValueError("扩展缺少 manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_app_version():
    """从项目根 config.json 读取当前应用版本。"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config.json"
    )
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def _parse_version(v):
    """将 '1.2.3' 转换为 (1,2,3) 元组，非法值返回空元组。"""
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return ()


def _validate_manifest(manifest):
    required = ["id", "name", "version", "permissions", "ext_points", "min_app_version"]
    for key in required:
        if key not in manifest:
            raise ValueError(f"manifest.json 缺少必填字段: {key}")
    if not isinstance(manifest["permissions"], list):
        raise ValueError("permissions 必须是数组")
    if not isinstance(manifest["ext_points"], dict):
        raise ValueError("ext_points 必须是对象")
    # 检查 min_app_version 兼容性
    app_ver = _parse_version(_read_app_version())
    min_ver = _parse_version(manifest["min_app_version"])
    if app_ver and min_ver and app_ver < min_ver:
        raise ValueError(
            f"扩展要求最低应用版本 {manifest['min_app_version']}，"
            f"当前版本 {_read_app_version()}"
        )


def install_from_git(url, branch="main"):
    os.makedirs(EXTENSIONS_DIR, exist_ok=True)
    ext_id = None
    clone_dir = tempfile.mkdtemp(dir=EXTENSIONS_DIR)
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, url, clone_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git clone 失败: {result.stderr}")

        manifest = _read_manifest(clone_dir)
        _validate_manifest(manifest)
        ext_id = manifest["id"]

        target_dir = os.path.join(EXTENSIONS_DIR, ext_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.rename(clone_dir, target_dir)

        return ext_id, manifest["name"]
    finally:
        if os.path.exists(clone_dir) and ext_id is None:
            shutil.rmtree(clone_dir, ignore_errors=True)


def install_from_zip(zip_path):
    os.makedirs(EXTENSIONS_DIR, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(dir=EXTENSIONS_DIR)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        # 处理 zip 内可能含有一层目录的情况
        entries = os.listdir(tmp_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(tmp_dir, entries[0])):
            inner_dir = os.path.join(tmp_dir, entries[0])
        else:
            inner_dir = tmp_dir

        manifest = _read_manifest(inner_dir)
        _validate_manifest(manifest)
        ext_id = manifest["id"]

        target_dir = os.path.join(EXTENSIONS_DIR, ext_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.move(inner_dir, target_dir)

        return ext_id, manifest["name"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def uninstall_extension(ext_id):
    ext_dir = os.path.join(EXTENSIONS_DIR, ext_id)
    if os.path.isdir(ext_dir):
        shutil.rmtree(ext_dir, ignore_errors=True)


def update_extension(ext_id):
    ext_dir = os.path.join(EXTENSIONS_DIR, ext_id)
    if not os.path.isdir(ext_dir):
        raise FileNotFoundError(f"扩展 {ext_id} 未安装")

    result = subprocess.run(
        ["git", "-C", ext_dir, "pull", "--ff-only"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git pull 失败: {result.stderr}")

    manifest = _read_manifest(ext_dir)
    return manifest["version"]
