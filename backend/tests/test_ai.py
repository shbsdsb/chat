import json
import threading
from unittest.mock import patch, Mock, MagicMock
from app.services.ai import stream_chat


def make_mock_response(chunks):
    resp = Mock()
    resp.raise_for_status = Mock()
    lines = []
    for chunk in chunks:
        if chunk == "[DONE]":
            lines.append(b"data: [DONE]")
        else:
            lines.append(
                b"data: " + json.dumps({
                    "choices": [{"delta": {"content": chunk}}]
                }).encode()
            )
    resp.iter_lines.return_value = [b""] + lines
    return resp


class TestStreamChat:
    def test_yields_deltas(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["你好", "世界"])

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert {"delta": "你好"} in results
        assert {"delta": "世界"} in results
        assert {"done": True} in results

    def test_yields_done_at_end(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["ok"])

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert results[-1] == {"done": True}

    def test_stops_on_cancel(self):
        cancel = threading.Event()

        def set_cancel_then_iter():
            cancel.set()
            return iter([b'data: {"choices":[{"delta":{"content":"partial"}}]}'])

        with patch("app.services.ai.requests.post") as mock_post:
            mock_resp = Mock()
            mock_resp.raise_for_status = Mock()
            mock_resp.iter_lines.side_effect = set_cancel_then_iter
            mock_resp.close = Mock()
            mock_post.return_value = mock_resp

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert {"stopped": True} in results

    def test_request_error(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert len(results) == 1
        assert "error" in results[0]

    def test_includes_response_format_when_set(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["{}"])

            list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "json_object",
                cancel,
            ))

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["response_format"] == {"type": "json_object"}
