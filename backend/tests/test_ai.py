import json
import threading
import requests
from unittest.mock import patch, Mock
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
            mock_post.side_effect = requests.ConnectionError("Connection refused")

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


def make_mock_response_with_reasoning(reasoning_chunks, content_chunks):
    resp = Mock()
    resp.raise_for_status = Mock()
    lines = []
    for chunk in reasoning_chunks:
        lines.append(
            b"data: " + json.dumps({
                "choices": [{"delta": {"reasoning_content": chunk, "content": ""}}]
            }).encode()
        )
    for chunk in content_chunks:
        lines.append(
            b"data: " + json.dumps({
                "choices": [{"delta": {"content": chunk}}]
            }).encode()
        )
    lines.append(b"data: [DONE]")
    resp.iter_lines.return_value = [b""] + lines
    return resp


class TestStreamChatReasoning:
    def test_yields_reasoning_delta(self):
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response_with_reasoning(
                ["让我想想", "用户的问题是"],
                ["你好！"]
            )

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert {"reasoning_delta": "让我想想"} in results
        assert {"reasoning_delta": "用户的问题是"} in results
        assert {"delta": "你好！"} in results
        assert {"done": True} in results

    def test_no_reasoning_for_plain_models(self):
        """没有 reasoning_content 的模型不产生 reasoning_delta"""
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response(["hello"])

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        # 不应包含 reasoning_delta
        assert not any("reasoning_delta" in r for r in results)
        assert {"delta": "hello"} in results

    def test_reasoning_only_chunk(self):
        """只有 reasoning_content 没有 content 的 chunk"""
        cancel = threading.Event()
        with patch("app.services.ai.requests.post") as mock_post:
            mock_post.return_value = make_mock_response_with_reasoning(
                ["纯思考"],
                ["答案"]
            )

            results = list(stream_chat(
                "https://api.openai.com/v1",
                "sk-test",
                "gpt-4o",
                [{"role": "user", "content": "hi"}],
                "text",
                cancel,
            ))

        assert {"reasoning_delta": "纯思考"} in results
        assert {"delta": "答案"} in results
