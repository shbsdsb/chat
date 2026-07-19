import threading


class SSEManager:
    """维护 {conversation_id: threading.Event} 映射，支持 /stop 取消 SSE 流。"""

    def __init__(self):
        self._events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def register(self, conv_id: str) -> threading.Event:
        event = threading.Event()
        with self._lock:
            if conv_id in self._events:
                # Cancel the old stream before replacing
                self._events[conv_id].set()
            self._events[conv_id] = event
        return event

    def cancel(self, conv_id: str) -> bool:
        with self._lock:
            event = self._events.get(conv_id)
        if event:
            event.set()
            return True
        return False

    def unregister(self, conv_id: str) -> None:
        with self._lock:
            self._events.pop(conv_id, None)


sse_manager = SSEManager()
