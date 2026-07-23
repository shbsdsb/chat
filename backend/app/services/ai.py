import json
import requests


def stream_chat(api_url, api_key, model, messages, response_format, cancel_event,
               temperature=None, max_tokens=None, top_p=None):
    url = api_url.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    if response_format and response_format != "text":
        payload["response_format"] = {"type": response_format}
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p

    try:
        resp = requests.post(
            url, headers=headers, json=payload, stream=True, timeout=120
        )
        resp.raise_for_status()

        for line in resp.iter_lines():
            if cancel_event.is_set():
                yield {"stopped": True}
                resp.close()
                return

            if not line:
                continue

            line_str = line.decode("utf-8") if isinstance(line, bytes) else line
            if not line_str.startswith("data: "):
                continue

            data_str = line_str[6:]
            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"]
                reasoning = delta.get("reasoning_content", "")
                content = delta.get("content", "")
                if reasoning:
                    yield {"reasoning_delta": reasoning}
                if content:
                    yield {"delta": content}
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        yield {"done": True}

    except requests.RequestException as e:
        yield {"error": str(e)}
