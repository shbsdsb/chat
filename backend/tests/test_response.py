import json
import os
from app.utils.response import ok, fail


class TestOk:
    def test_ok_no_data(self, app):
        with app.test_request_context():
            resp = ok()
            body = json.loads(resp.get_data(as_text=True))
            assert body["code"] == 0
            assert body["message"] == "ok"
            assert body["data"] is None

    def test_ok_with_data(self, app):
        with app.test_request_context():
            resp = ok(data={"id": "abc"})
            body = json.loads(resp.get_data(as_text=True))
            assert body["code"] == 0
            assert body["data"] == {"id": "abc"}

    def test_ok_custom_message(self, app):
        with app.test_request_context():
            resp = ok(message="created")
            body = json.loads(resp.get_data(as_text=True))
            assert body["message"] == "created"


class TestFail:
    def test_fail_returns_code_in_body(self, app):
        with app.test_request_context():
            resp = fail(404, "not found")
            body = json.loads(resp.get_data(as_text=True))
            assert body["code"] == 404
            assert body["message"] == "not found"
            assert body["data"] is None

    def test_fail_writes_error_log(self, app, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)

        import app.utils.response as mod
        monkeypatch.setattr(mod, "LOG_DIR", str(log_dir))

        with app.test_request_context():
            fail(500, "server error")

        log_file = log_dir / "error.log"
        assert log_file.exists()
        entry = json.loads(log_file.read_text(encoding="utf-8"))
        assert entry["code"] == 500
        assert entry["message"] == "server error"
        assert "timestamp" in entry

    def test_fail_logs_request_info(self, app, tmp_path, monkeypatch):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)

        import app.utils.response as mod
        monkeypatch.setattr(mod, "LOG_DIR", str(log_dir))

        with app.test_request_context(
            path="/api/test",
            method="POST",
            json={"api_key": "secret123", "name": "test"},
        ):
            fail(400, "bad request")

        entry = json.loads(
            (log_dir / "error.log").read_text(encoding="utf-8")
        )
        assert entry["path"] == "/api/test"
        assert entry["method"] == "POST"
        assert entry["body"]["api_key"] == "***"
        assert entry["body"]["name"] == "test"
