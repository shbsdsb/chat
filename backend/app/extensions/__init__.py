# backend/app/extensions/__init__.py
import logging
import threading

from .hooks import HookDispatcher
from .registry import read_registry, add_extension, remove_extension, set_extension_state
from .installer import install_from_git, install_from_zip, uninstall_extension, update_extension
from .loader import load_extension, unload_extension, load_all_enabled
from .permissions import check_permission, validate_permissions

logger = logging.getLogger(__name__)

_manager = None
_manager_lock = threading.Lock()


class ExtensionManager:
    def __init__(self):
        self.dispatcher = HookDispatcher()
        self._loaded = {}

    def init(self):
        """启动时初始化：加载所有已启用扩展"""
        self._loaded = load_all_enabled(self.dispatcher)
        logger.info(f"扩展初始化完成: {self._loaded}")

    def reload_extension(self, ext_id):
        """重新加载单个扩展（安装/更新后调用）"""
        unload_extension(ext_id, self.dispatcher, self._loaded)
        result = load_extension(ext_id, self.dispatcher)
        self._loaded[ext_id] = result
        return result

    def list_loaded(self):
        return dict(self._loaded)


def get_extension_manager():
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = ExtensionManager()
    return _manager
