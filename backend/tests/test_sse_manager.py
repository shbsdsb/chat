import threading
from app.services.sse_manager import sse_manager


class TestSSEManager:
    def test_register_returns_event(self):
        event = sse_manager.register("conv-1")
        assert isinstance(event, threading.Event)
        assert not event.is_set()

    def test_cancel_sets_event(self):
        sse_manager.register("conv-2")
        result = sse_manager.cancel("conv-2")
        assert result is True

    def test_cancel_nonexistent(self):
        result = sse_manager.cancel("no-such-id")
        assert result is False

    def test_unregister_removes(self):
        sse_manager.register("conv-3")
        sse_manager.unregister("conv-3")
        result = sse_manager.cancel("conv-3")
        assert result is False

    def test_thread_safe(self):
        errors = []

        def worker(i):
            try:
                cid = f"conv-t{i}"
                sse_manager.register(cid)
                sse_manager.cancel(cid)
                sse_manager.unregister(cid)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
