import importlib.util
import json
import logging
import os
import sys

from .registry import get_extension, read_registry
from .permissions import check_permission

logger = logging.getLogger(__name__)

_PACKAGE_DIR = os.path.dirname(__file__)
EXTENSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(_PACKAGE_DIR)),
    "user_data", "extensions"
)

EXT_POINT_TO_FUNC = {
    "chat.post_receive": "on_chat_post_receive",
    "chat.pre_send": "on_chat_pre_send",
}


def _load_backend_module(ext_id, ext_dir):
    """用 importlib 加载 backend.py 为独立模块"""
    backend_path = os.path.join(ext_dir, "backend.py")
    if not os.path.isfile(backend_path):
        return None
    module_name = f"_ext_{ext_id.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, backend_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        logger.exception(f"加载扩展 {ext_id} 的后端模块失败")
        sys.modules.pop(module_name, None)
        return None
    return module


def load_extension(ext_id, dispatcher):
    ext = get_extension(ext_id)
    if not ext:
        return {"status": "error", "message": f"扩展 {ext_id} 未在注册表中找到"}
    if not ext.get("enabled"):
        return {"status": "error", "message": f"扩展 {ext_id} 已禁用"}

    ext_dir = os.path.join(EXTENSIONS_DIR, ext_id)
    if not os.path.isdir(ext_dir):
        return {"status": "error", "message": f"扩展目录不存在: {ext_dir}"}

    # 读取 manifest 获取声明的扩展点
    manifest_path = os.path.join(ext_dir, "manifest.json")
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        return {"status": "error", "message": "manifest.json 不存在"}

    # 加载后端模块
    module = _load_backend_module(ext_id, ext_dir)
    if module is None:
        # 纯前端扩展，不注册后端钩子
        return {"status": "loaded", "frontend_only": True}

    backend_points = manifest.get("ext_points", {}).get("backend", [])
    registered = []

    for ext_point in backend_points:
        if ext_point not in EXT_POINT_TO_FUNC:
            continue
        func_name = EXT_POINT_TO_FUNC[ext_point]
        handler = getattr(module, func_name, None)
        if handler is None:
            continue
        dispatcher.register_hook(ext_id, ext_point, handler)
        registered.append(ext_point)

    return {
        "status": "loaded",
        "registered_hooks": registered,
        "manifest": manifest,
    }


def unload_extension(ext_id, dispatcher, _loaded=None):
    dispatcher.unregister_extension(ext_id)
    # 清理 sys.modules 中的模块缓存
    module_name = f"_ext_{ext_id.replace('-', '_')}"
    sys.modules.pop(module_name, None)
    # 清理 ExtensionManager 的 _loaded 记录
    if _loaded is not None:
        _loaded.pop(ext_id, None)


def load_all_enabled(dispatcher):
    """启动时加载所有已启用的扩展"""
    data = read_registry()
    results = {}
    for ext_id, info in data.get("extensions", {}).items():
        if info.get("enabled"):
            try:
                results[ext_id] = load_extension(ext_id, dispatcher)
            except Exception:
                logger.exception(f"加载扩展 {ext_id} 失败")
                results[ext_id] = {"status": "error", "message": "加载异常"}
    return results
