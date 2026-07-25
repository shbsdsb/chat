import logging
import threading

logger = logging.getLogger(__name__)


class HookDispatcher:
    def __init__(self):
        self._handlers = {}   # {ext_point: [(ext_id, handler), ...]}
        self._lock = threading.Lock()

    def register_hook(self, ext_id, ext_point, handler):
        with self._lock:
            self._handlers.setdefault(ext_point, []).append(
                (ext_id, handler)
            )

    def unregister_extension(self, ext_id):
        with self._lock:
            for ext_point in list(self._handlers):
                self._handlers[ext_point] = [
                    (eid, h) for eid, h in self._handlers[ext_point]
                    if eid != ext_id
                ]

    def dispatch(self, ext_point, ctx):
        results = []
        handlers = list(self._handlers.get(ext_point, []))
        for ext_id, handler in handlers:
            try:
                result = handler(ctx)
                if result is not None:
                    if isinstance(result, dict):
                        result.setdefault("extension_id", ext_id)
                        # 规范化：统一转换为 {extension_id, message_meta} 格式
                        if "meta" in result and "message_meta" not in result:
                            result["message_meta"] = result.pop("meta")
                        if "message_meta" not in result:
                            # 非标准格式：整体包装为 message_meta
                            ext_id_val = result.pop("extension_id")
                            result = {
                                "extension_id": ext_id_val,
                                "message_meta": result,
                            }
                        results.append(result)
                    else:
                        results.append({
                            "extension_id": ext_id,
                            "message_meta": result,
                        })
            except Exception:
                logger.exception(
                    f"扩展 {ext_id} 的钩子 {ext_point} 执行异常"
                )
        return results
