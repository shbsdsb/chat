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
                        # 规范化：handler 返回的 "meta" 重命名为 "message_meta"
                        if "meta" in result and "message_meta" not in result:
                            result["message_meta"] = result.pop("meta")
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
